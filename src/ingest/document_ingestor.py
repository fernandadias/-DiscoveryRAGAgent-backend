import os
import logging
import json
import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import weaviate
from weaviate.auth import AuthApiKey
from PyPDF2 import PdfReader
import subprocess
import tempfile

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definir padrões para perfis de usuários globalmente
perfil_patterns = [
    r'(?i)perfis?\s+de\s+usuários?',
    r'(?i)personas?',
    r'(?i)segmenta[çc][aã]o\s+de\s+(?:usuários?|clientes?)',
    r'(?i)públicos?[\s-]alvos?',
    r'(?i)tipos?\s+de\s+(?:usuários?|clientes?)',
    r'(?i)caracter[íi]sticas?\s+(?:dos?|das?)\s+(?:usuários?|clientes?)',
    r'(?i)comportamentos?\s+(?:dos?|das?)\s+(?:usuários?|clientes?)'
]

def sanitize_key(key):
    """Sanitiza uma chave para ser compatível com GraphQL"""
    if not isinstance(key, str):
        return "unknown_key"
    # Remover caracteres não alfanuméricos e substituir por underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', key)
    # Garantir que começa com letra ou underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = 'f_' + sanitized
    return sanitized

def sanitize_value(value):
    """Sanitiza um valor para ser compatível com JSON e UTF-8"""
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    elif isinstance(value, str):
        # Remover caracteres que causam problemas de encoding
        try:
            # Tentar codificar e decodificar para detectar problemas
            value.encode('utf-8').decode('utf-8')
            return value
        except UnicodeError:
            # Se falhar, substituir caracteres problemáticos
            return value.encode('utf-8', errors='replace').decode('utf-8')
    elif isinstance(value, dict):
        return sanitize_metadata(value)
    elif isinstance(value, list):
        return [sanitize_value(item) for item in value]
    else:
        # Converter outros tipos para string
        try:
            return str(value)
        except:
            return "unparseable_value"

def sanitize_metadata(metadata):
    """Sanitiza os metadados para serem compatíveis com GraphQL e JSON"""
    if not metadata:
        return {}
    
    if not isinstance(metadata, dict):
        try:
            return {"value": str(metadata)}
        except:
            return {"value": "unparseable_metadata"}
    
    sanitized = {}
    for key, value in metadata.items():
        if key is None or value is None:
            continue
            
        # Sanitizar a chave
        try:
            new_key = sanitize_key(key)
        except:
            new_key = "unknown_key"
            
        # Sanitizar o valor
        try:
            sanitized[new_key] = sanitize_value(value)
        except:
            sanitized[new_key] = "unparseable_value"
    
    return sanitized

class DocumentIngestor:
    def __init__(self):
        # Configurar cliente Weaviate usando variáveis de ambiente
        weaviate_url = os.getenv("WEAVIATE_URL", "https://xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s")
        
        # Garantir que a URL tenha o prefixo https://
        if not weaviate_url.startswith("http://") and not weaviate_url.startswith("https://"):
            weaviate_url = f"https://{weaviate_url}"
        
        # Criar conexão com autenticação correta
        auth_config = None
        if weaviate_api_key:
            auth_config = AuthApiKey(api_key=weaviate_api_key)
            
        self.client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=auth_config
        )
        
        # Verificar se o schema existe, caso contrário, criar
        self._ensure_schema_exists()
        
    def _ensure_schema_exists(self):
        """Garante que o schema do Weaviate existe"""
        try:
            # Verificar se a classe Document já existe
            schema = self.client.schema.get()
            classes = [c["class"] for c in schema["classes"]] if "classes" in schema else []
            
            # Verificar se a classe já existe antes de criar
            if "Document" not in classes:
                logger.info("Classe Document não existe, criando...")
                
                # Criar a classe Document com schema correto
                document_class = {
                    "class": "Document",
                    "description": "Documentos para o DiscoveryRAGAgent",
                    "vectorizer": "text2vec-openai",  # Usando OpenAI para vectorização
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "ada",
                            "modelVersion": "002",
                            "type": "text"
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "description": "Título do documento",
                            "dataType": ["string"]
                        },
                        {
                            "name": "content",
                            "description": "Conteúdo do documento",
                            "dataType": ["text"],
                            "moduleConfig": {
                                "text2vec-openai": {
                                    "skip": False,
                                    "vectorizePropertyName": True
                                }
                            }
                        },
                        {
                            "name": "metadata_json",
                            "description": "Metadados do documento em formato JSON",
                            "dataType": ["string"]
                        },
                        {
                            "name": "semantic_context",
                            "description": "Contexto semântico do chunk",
                            "dataType": ["string"]
                        },
                        {
                            "name": "keywords",
                            "description": "Palavras-chave extraídas do conteúdo",
                            "dataType": ["string[]"]
                        },
                        {
                            "name": "file_path",
                            "description": "Caminho do arquivo original",
                            "dataType": ["string"]
                        },
                        {
                            "name": "file_name",
                            "description": "Nome do arquivo original",
                            "dataType": ["string"]
                        }
                    ]
                }
                
                # Criar a classe
                self.client.schema.create_class(document_class)
                logger.info("Schema criado com sucesso.")
            else:
                logger.info("Schema já existe, mantendo-o para preservar os documentos indexados.")
        except Exception as e:
            logger.error(f"Erro ao verificar/criar schema: {str(e)}")
            raise
    
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Processa um arquivo PDF, extraindo texto e metadados
        
        Args:
            file_path: Caminho para o arquivo PDF
            
        Returns:
            Dict contendo título, conteúdo e metadados do documento
        """
        try:
            # Extrair texto usando PyPDF2
            text = self._extract_text_with_pypdf2(file_path)
            
            # Extrair metadados usando pdfinfo
            metadata = self._extract_metadata_with_pdfinfo(file_path)
            
            # Determinar título (do metadata ou do nome do arquivo)
            title = metadata.get("Title", os.path.basename(file_path))
            if not title or title.strip() == "":
                title = os.path.basename(file_path)
            
            # Sanitizar metadados
            sanitized_metadata = sanitize_metadata(metadata)
            
            return {
                "title": title,
                "content": text,
                "metadata": sanitized_metadata
            }
        except Exception as e:
            logger.error(f"Erro ao processar PDF {file_path}: {str(e)}")
            return {
                "title": os.path.basename(file_path),
                "content": f"Erro ao processar documento: {str(e)}",
                "metadata": {"error": str(e)}
            }
    
    def _extract_text_with_pypdf2(self, file_path: str) -> str:
        """Extrai texto de um PDF usando PyPDF2"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf = PdfReader(file)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            if not text.strip():
                logger.warning(f"PyPDF2 não extraiu texto de {file_path}, tentando método alternativo")
                return self._extract_text_with_pdftotext(file_path)
                
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto com PyPDF2: {str(e)}")
            # Tentar método alternativo se PyPDF2 falhar
            return self._extract_text_with_pdftotext(file_path)
    
    def _extract_text_with_pdftotext(self, file_path: str) -> str:
        """Extrai texto de um PDF usando pdftotext (poppler-utils)"""
        try:
            # Verificar se pdftotext está instalado
            subprocess.run(["which", "pdftotext"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Usar pdftotext para extrair o texto
            with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
                subprocess.run(["pdftotext", "-layout", file_path, temp_file.name], check=True)
                with open(temp_file.name, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Erro ao extrair texto com pdftotext: {str(e)}")
            return f"Não foi possível extrair o texto do documento. Erro: {str(e)}"
    
    def _extract_metadata_with_pdfinfo(self, file_path: str) -> Dict[str, Any]:
        """Extrai metadados de um PDF usando pdfinfo (poppler-utils)"""
        metadata = {}
        try:
            # Verificar se pdfinfo está instalado
            subprocess.run(["which", "pdfinfo"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Usar pdfinfo para extrair metadados
            result = subprocess.run(["pdfinfo", file_path], capture_output=True, text=True, check=True)
            
            # Processar a saída
            for line in result.stdout.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            
            # Adicionar caminho do arquivo e data de processamento
            metadata["file_path"] = file_path
            metadata["processed_at"] = str(datetime.now())
            
            return metadata
        except Exception as e:
            logger.error(f"Erro ao extrair metadados com pdfinfo: {str(e)}")
            return {"file_path": file_path, "error": str(e)}
    
    def process_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Processa um arquivo DOCX, extraindo texto
        
        Args:
            file_path: Caminho para o arquivo DOCX
            
        Returns:
            Dict contendo título, conteúdo e metadados do documento
        """
        try:
            # Tentar extrair texto usando docx2txt se disponível
            try:
                import docx2txt
                text = docx2txt.process(file_path)
            except ImportError:
                # Fallback para extração simples
                text = self._extract_text_with_textract(file_path)
            
            metadata = {
                "file_path": file_path,
                "file_type": "docx",
                "processed_at": str(datetime.now())
            }
            
            # Sanitizar metadados
            sanitized_metadata = sanitize_metadata(metadata)
            
            return {
                "title": os.path.basename(file_path),
                "content": text,
                "metadata": sanitized_metadata
            }
        except Exception as e:
            logger.error(f"Erro ao processar DOCX {file_path}: {str(e)}")
            return {
                "title": os.path.basename(file_path),
                "content": f"Erro ao processar documento: {str(e)}",
                "metadata": {"error": str(e)}
            }
    
    def _extract_text_with_textract(self, file_path: str) -> str:
        """Extrai texto usando textract se disponível"""
        try:
            import textract
            return textract.process(file_path, encoding='utf-8').decode('utf-8')
        except ImportError:
            logger.warning("textract não está instalado, usando método alternativo")
            # Tentar usar antiword para DOC ou unzip + grep para DOCX
            if file_path.lower().endswith('.docx'):
                return self._extract_text_from_docx_with_unzip(file_path)
            else:
                return f"Não foi possível extrair texto do documento {file_path}. Instale textract ou docx2txt."
    
    def _extract_text_from_docx_with_unzip(self, file_path: str) -> str:
        """Extrai texto de DOCX usando unzip e grep"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Descompactar o arquivo DOCX
                subprocess.run(["unzip", "-q", file_path, "word/document.xml", "-d", temp_dir], check=True)
                
                # Extrair texto do XML
                xml_path = os.path.join(temp_dir, "word/document.xml")
                if os.path.exists(xml_path):
                    with open(xml_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extrair texto entre tags w:t
                    import re
                    text_parts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', content)
                    return ' '.join(text_parts)
                
                return "Não foi possível extrair texto do documento DOCX."
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX com unzip: {str(e)}")
            return f"Erro ao extrair texto: {str(e)}"
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extrai palavras-chave relevantes do texto
        
        Args:
            text: Texto para extrair palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        # Lista de termos importantes para o domínio
        domain_terms = [
            "perfil", "perfis", "usuário", "usuários", "cliente", "clientes", 
            "persona", "personas", "segmentação", "segmento", "público-alvo",
            "comportamento", "necessidade", "necessidades", "dor", "dores",
            "jornada", "experiência", "discovery", "pesquisa", "entrevista",
            "validação", "hipótese", "métrica", "produto", "serviço",
            "stone", "ton", "pagar.me", "pagarme", "pagamento"
        ]
        
        # Normalizar texto
        text_lower = text.lower()
        
        # Encontrar termos do domínio no texto
        found_terms = []
        for term in domain_terms:
            if term in text_lower:
                found_terms.append(term)
        
        # Adicionar termos compostos específicos se presentes
        compound_terms = [
            "perfil de usuário", "perfis de usuários", "persona de cliente",
            "segmentação de clientes", "público-alvo", "jornada do usuário",
            "experiência do cliente", "pesquisa de usuário", "entrevista com usuário"
        ]
        
        for term in compound_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return list(set(found_terms))
    
    def detect_semantic_context(self, text: str) -> str:
        """
        Detecta o contexto semântico do texto
        
        Args:
            text: Texto para detectar contexto
            
        Returns:
            String descrevendo o contexto semântico
        """
        # Verificar se o texto contém informações sobre perfis de usuários
        for pattern in perfil_patterns:
            if re.search(pattern, text):
                return "perfil_usuario"
        
        # Outros contextos semânticos
        contexts = {
            "pesquisa": ["pesquisa", "entrevista", "survey", "questionário", "estudo"],
            "produto": ["produto", "feature", "funcionalidade", "recurso", "serviço"],
            "metricas": ["métrica", "kpi", "indicador", "performance", "desempenho"],
            "estrategia": ["estratégia", "objetivo", "meta", "visão", "missão"],
            "tecnologia": ["tecnologia", "sistema", "plataforma", "software", "aplicativo"]
        }
        
        # Verificar cada contexto
        detected_contexts = []
        for context, terms in contexts.items():
            for term in terms:
                if term in text.lower():
                    detected_contexts.append(context)
                    break
        
        if detected_contexts:
            return "_".join(detected_contexts)
        
        return "geral"
    
    def chunk_document(self, document: Dict[str, Any], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Divide um documento em chunks de tamanho fixo com sobreposição
        
        Args:
            document: Documento a ser dividido
            chunk_size: Tamanho máximo de cada chunk em caracteres
            overlap: Sobreposição entre chunks em caracteres
            
        Returns:
            Lista de chunks do documento
        """
        content = document.get("content", "")
        if not content:
            return [document]
        
        # Dividir o conteúdo em parágrafos
        paragraphs = content.split("\n\n")
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Se o parágrafo for maior que o chunk_size, dividi-lo
            if len(paragraph) > chunk_size:
                # Adicionar o chunk atual se não estiver vazio
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # Dividir o parágrafo grande em chunks menores
                for i in range(0, len(paragraph), chunk_size - overlap):
                    chunk = paragraph[i:i + chunk_size]
                    chunks.append(chunk)
            
            # Se adicionar o parágrafo exceder o tamanho do chunk, criar um novo chunk
            elif len(current_chunk) + len(paragraph) > chunk_size:
                chunks.append(current_chunk)
                current_chunk = paragraph
            
            # Caso contrário, adicionar o parágrafo ao chunk atual
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
        
        # Adicionar o último chunk se não estiver vazio
        if current_chunk:
            chunks.append(current_chunk)
        
        # Criar documentos para cada chunk
        chunk_docs = []
        for i, chunk_content in enumerate(chunks):
            # Extrair palavras-chave do chunk
            keywords = self.extract_keywords(chunk_content)
            
            # Detectar contexto semântico
            semantic_context = self.detect_semantic_context(chunk_content)
            
            # Criar metadados para o chunk
            chunk_metadata = document.get("metadata", {}).copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            
            # Criar documento para o chunk
            chunk_doc = {
                "title": f"{document.get('title', 'Sem título')} - Parte {i+1}",
                "content": chunk_content,
                "metadata": chunk_metadata,
                "keywords": keywords,
                "semantic_context": semantic_context
            }
            
            chunk_docs.append(chunk_doc)
        
        return chunk_docs
    
    def chunk_document_semantic(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Divide um documento em chunks semânticos baseados em parágrafos e seções
        
        Args:
            document: Documento a ser dividido
            
        Returns:
            Lista de chunks semânticos do documento
        """
        content = document.get("content", "")
        if not content:
            return [document]
        
        # Dividir o conteúdo em parágrafos
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        
        # Identificar possíveis cabeçalhos/títulos de seção
        section_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^(.+)\n[=\-]{3,}$',  # Underlined headers
            r'^(\d+\.?\s+.+)$',  # Numbered sections
            r'^([A-Z][A-Za-z\s]+:)$',  # Capitalized labels with colon
            r'^([A-Z][A-Za-z\s]+)$'  # All capitalized short lines
        ]
        
        # Função para verificar se um parágrafo é um cabeçalho
        def is_header(paragraph):
            paragraph = paragraph.strip()
            if len(paragraph) > 100:  # Cabeçalhos geralmente são curtos
                return False
                
            for pattern in section_patterns:
                if re.match(pattern, paragraph):
                    return True
            
            # Verificar se é todo em maiúsculas e curto
            if paragraph.isupper() and len(paragraph) < 50:
                return True
                
            return False
        
        # Agrupar parágrafos em seções semânticas
        sections = []
        current_section = {"header": "", "content": []}
        
        for paragraph in paragraphs:
            if is_header(paragraph):
                # Se já temos conteúdo na seção atual, salvá-la
                if current_section["content"]:
                    sections.append(current_section)
                    
                # Iniciar nova seção
                current_section = {"header": paragraph, "content": []}
            else:
                # Adicionar parágrafo à seção atual
                current_section["content"].append(paragraph)
        
        # Adicionar a última seção se tiver conteúdo
        if current_section["content"]:
            sections.append(current_section)
        
        # Se não encontramos seções (sem cabeçalhos), usar chunks de tamanho fixo
        if not sections:
            return self.chunk_document(document)
        
        # Criar documentos para cada seção semântica
        chunk_docs = []
        for i, section in enumerate(sections):
            # Juntar o conteúdo da seção
            section_content = section["header"]
            if section["content"]:
                section_content += "\n\n" + "\n\n".join(section["content"])
            
            # Extrair palavras-chave da seção
            keywords = self.extract_keywords(section_content)
            
            # Detectar contexto semântico
            semantic_context = self.detect_semantic_context(section_content)
            
            # Criar metadados para o chunk
            chunk_metadata = document.get("metadata", {}).copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(sections)
            chunk_metadata["section_header"] = section["header"]
            
            # Criar documento para o chunk
            chunk_doc = {
                "title": f"{document.get('title', 'Sem título')} - {section['header'][:50]}",
                "content": section_content,
                "metadata": chunk_metadata,
                "keywords": keywords,
                "semantic_context": semantic_context
            }
            
            chunk_docs.append(chunk_doc)
        
        return chunk_docs
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Processa um documento baseado em sua extensão
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            Dict contendo título, conteúdo e metadados do documento
        """
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return {
                "title": os.path.basename(file_path),
                "content": "Arquivo não encontrado",
                "metadata": {"error": "Arquivo não encontrado"}
            }
        
        # Determinar o tipo de arquivo pela extensão
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.pdf']:
            return self.process_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.process_docx(file_path)
        elif file_ext in ['.txt', '.md', '.csv']:
            # Processar arquivos de texto simples
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                metadata = {
                    "file_path": file_path,
                    "file_type": file_ext[1:],  # Remover o ponto
                    "processed_at": str(datetime.now())
                }
                
                return {
                    "title": os.path.basename(file_path),
                    "content": content,
                    "metadata": metadata
                }
            except Exception as e:
                logger.error(f"Erro ao processar arquivo de texto {file_path}: {str(e)}")
                return {
                    "title": os.path.basename(file_path),
                    "content": f"Erro ao processar documento: {str(e)}",
                    "metadata": {"error": str(e)}
                }
        else:
            logger.warning(f"Tipo de arquivo não suportado: {file_ext}")
            return {
                "title": os.path.basename(file_path),
                "content": f"Tipo de arquivo não suportado: {file_ext}",
                "metadata": {"error": f"Tipo de arquivo não suportado: {file_ext}"}
            }
    
    def index_document(self, document: Dict[str, Any], batch_size: int = 10) -> bool:
        """
        Indexa um documento no Weaviate
        
        Args:
            document: Documento a ser indexado
            batch_size: Tamanho do lote para indexação em batch
            
        Returns:
            True se a indexação foi bem-sucedida, False caso contrário
        """
        try:
            # Dividir o documento em chunks semânticos
            chunks = self.chunk_document_semantic(document)
            
            logger.info(f"Indexando documento '{document['title']}' em {len(chunks)} chunks semânticos")
            
            # Criar um batch para indexação
            with self.client.batch as batch:
                batch.batch_size = batch_size
                
                for chunk in chunks:
                    try:
                        # Sanitizar metadados
                        sanitized_metadata = {}
                        if "metadata" in chunk and chunk["metadata"]:
                            try:
                                # Usar apenas metadados básicos para evitar problemas
                                sanitized_metadata = {
                                    "file_path": str(chunk["metadata"].get("file_path", "")),
                                    "processed_at": str(chunk["metadata"].get("processed_at", ""))
                                }
                            except Exception as e:
                                logger.warning(f"Erro ao sanitizar metadados: {str(e)}. Usando metadados vazios.")
                        
                        # Serializar metadados para JSON, tratando erros de encoding
                        try:
                            metadata_json = json.dumps(sanitized_metadata, ensure_ascii=True)
                        except Exception as e:
                            logger.warning(f"Erro ao serializar metadados: {str(e)}. Usando metadados vazios.")
                            metadata_json = "{}"
                        
                        # Sanitizar conteúdo para remover caracteres problemáticos
                        content = chunk.get("content", "")
                        if content:
                            # Remover caracteres surrogates e outros caracteres problemáticos
                            content = re.sub(r'[\uD800-\uDFFF]', '', content)
                            # Garantir que o conteúdo seja codificável em UTF-8
                            content = content.encode('utf-8', errors='ignore').decode('utf-8')
                        
                        # Sanitizar título
                        title = chunk.get("title", "")
                        if title:
                            title = re.sub(r'[\uD800-\uDFFF]', '', title)
                            title = title.encode('utf-8', errors='ignore').decode('utf-8')
                        
                        # Gerar um UUID baseado no conteúdo para evitar duplicatas
                        content_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, content[:1000] if content else "empty"))
                        
                        # Preparar objeto para indexação - SEM INCLUIR METADATA COMO OBJETO
                        data_object = {
                            "title": title,
                            "content": content,
                            "metadata_json": metadata_json,
                            "file_path": sanitized_metadata.get("file_path", ""),
                            "file_name": os.path.basename(sanitized_metadata.get("file_path", ""))
                        }
                        
                        # Adicionar contexto semântico e palavras-chave se disponíveis
                        if "semantic_context" in chunk:
                            semantic_context = chunk["semantic_context"]
                            # Sanitizar contexto semântico
                            semantic_context = re.sub(r'[\uD800-\uDFFF]', '', semantic_context)
                            semantic_context = semantic_context.encode('utf-8', errors='ignore').decode('utf-8')
                            data_object["semantic_context"] = semantic_context
                        
                        if "keywords" in chunk:
                            # Garantir que keywords seja uma lista de strings sanitizadas
                            keywords = []
                            for kw in chunk["keywords"]:
                                if kw:
                                    # Sanitizar cada palavra-chave
                                    kw = re.sub(r'[\uD800-\uDFFF]', '', str(kw))
                                    kw = kw.encode('utf-8', errors='ignore').decode('utf-8')
                                    if kw:  # Adicionar apenas se não estiver vazio após sanitização
                                        keywords.append(kw)
                            
                            if keywords:  # Adicionar apenas se houver palavras-chave após sanitização
                                data_object["keywords"] = keywords
                        
                        # Adicionar o chunk ao batch
                        batch.add_data_object(
                            data_object=data_object,
                            class_name="Document",
                            uuid=content_hash
                        )
                    except Exception as chunk_error:
                        logger.error(f"Erro ao processar chunk: {str(chunk_error)}")
                        continue
            
            return True
        except Exception as e:
            logger.error(f"Erro ao indexar documento: {str(e)}")
            return False
    
    def reindex_all_documents(self, data_dir: str) -> Dict[str, int]:
        """
        Reindexar todos os documentos em um diretório
        
        Args:
            data_dir: Diretório contendo os documentos
            
        Returns:
            Dict com estatísticas de processamento
        """
        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Verificar se o diretório existe
        if not os.path.exists(data_dir):
            logger.error(f"Diretório não encontrado: {data_dir}")
            return stats
        
        # Listar arquivos no diretório
        for file_name in os.listdir(data_dir):
            file_path = os.path.join(data_dir, file_name)
            
            # Verificar se é um arquivo
            if not os.path.isfile(file_path):
                continue
                
            # Verificar extensão
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.pdf', '.docx', '.doc', '.txt', '.md', '.csv']:
                logger.info(f"Pulando arquivo não suportado: {file_path}")
                stats["skipped"] += 1
                continue
            
            logger.info(f"Processando arquivo: {file_path} (tipo: {file_ext})")
            
            try:
                # Processar o documento
                document = self.process_document(file_path)
                
                # Indexar o documento
                if self.index_document(document):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Erro ao processar/indexar arquivo {file_path}: {str(e)}")
                stats["failed"] += 1
        
        logger.info(f"Processamento concluído: {stats['success']} sucesso, {stats['failed']} falhas, {stats['skipped']} ignorados")
        return stats
