import os
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
import weaviate
from weaviate.auth import AuthApiKey
from PyPDF2 import PdfReader
import subprocess
import tempfile
import uuid
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            
            if "Document" not in classes:
                # Criar a classe Document
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
                            "name": "metadata",
                            "description": "Metadados do documento",
                            "dataType": ["object"]
                        }
                    ]
                }
                
                self.client.schema.create_class(document_class)
                logger.info("Schema criado com sucesso.")
            else:
                logger.info("Schema já existe.")
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
            
            return {
                "title": title,
                "content": text,
                "metadata": metadata
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
            
            return {
                "title": os.path.basename(file_path),
                "content": text,
                "metadata": {
                    "file_path": file_path,
                    "file_type": "docx",
                    "processed_at": str(datetime.now())
                }
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
    
    def chunk_document(self, document: Dict[str, Any], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Divide o documento em chunks menores para melhor indexação
        
        Args:
            document: Documento a ser dividido
            chunk_size: Tamanho aproximado de cada chunk em caracteres
            overlap: Sobreposição entre chunks em caracteres
            
        Returns:
            Lista de chunks do documento
        """
        content = document["content"]
        title = document["title"]
        metadata = document["metadata"]
        
        # Se o conteúdo for menor que o chunk_size, retornar o documento inteiro
        if len(content) <= chunk_size:
            return [document]
        
        chunks = []
        start = 0
        
        while start < len(content):
            # Determinar o fim do chunk
            end = start + chunk_size
            
            # Ajustar o fim para não cortar no meio de uma palavra/frase
            if end < len(content):
                # Tentar encontrar um ponto final, quebra de linha ou espaço próximo
                for separator in ["\n\n", ".", "\n", " "]:
                    pos = content.find(separator, end - 30, end + 30)
                    if pos != -1:
                        end = pos + 1  # +1 para incluir o separador
                        break
            
            # Garantir que não ultrapasse o tamanho do conteúdo
            end = min(end, len(content))
            
            # Criar o chunk
            chunk = {
                "title": f"{title} (parte {len(chunks) + 1})",
                "content": content[start:end],
                "metadata": {
                    **metadata,
                    "chunk_index": len(chunks),
                    "original_title": title
                }
            }
            
            chunks.append(chunk)
            
            # Atualizar o início para o próximo chunk, considerando a sobreposição
            start = end - overlap
            
            # Garantir que o início não retroceda
            start = max(start, 0)
        
        return chunks
    
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
            # Dividir o documento em chunks
            chunks = self.chunk_document(document)
            
            logger.info(f"Indexando documento '{document['title']}' em {len(chunks)} chunks")
            
            # Criar um batch para indexação
            with self.client.batch as batch:
                batch.batch_size = batch_size
                
                for chunk in chunks:
                    # Gerar um UUID baseado no conteúdo para evitar duplicatas
                    content_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["content"]))
                    
                    # Adicionar o chunk ao batch
                    batch.add_data_object(
                        data_object={
                            "title": chunk["title"],
                            "content": chunk["content"],
                            "metadata": chunk["metadata"]
                        },
                        class_name="Document",
                        uuid=content_hash
                    )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao indexar documento: {str(e)}")
            return False
    
    def process_and_index_file(self, file_path: str) -> bool:
        """
        Processa e indexa um arquivo no Weaviate
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            True se o processamento e indexação foram bem-sucedidos, False caso contrário
        """
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(file_path):
                logger.warning(f"Arquivo não encontrado: {file_path}")
                return False
            
            # Verificar a extensão do arquivo
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            logger.info(f"Processando arquivo: {file_path} (tipo: {ext})")
            
            if ext == '.pdf':
                # Processar PDF
                document = self.process_pdf(file_path)
            elif ext in ['.txt', '.md']:
                # Processar arquivo de texto
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                document = {
                    "title": os.path.basename(file_path),
                    "content": content,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": ext[1:],  # Remover o ponto
                        "processed_at": str(datetime.now())
                    }
                }
            elif ext in ['.docx', '.doc']:
                # Processar arquivo Word
                document = self.process_docx(file_path)
            else:
                logger.warning(f"Formato de arquivo não suportado: {ext}")
                return False
            
            # Verificar se o conteúdo foi extraído com sucesso
            if not document["content"] or document["content"].startswith("Erro ao processar documento"):
                logger.warning(f"Não foi possível extrair conteúdo de {file_path}")
                return False
                
            # Indexar o documento
            success = self.index_document(document)
            if success:
                logger.info(f"Documento indexado com sucesso: {file_path}")
            else:
                logger.error(f"Falha ao indexar documento: {file_path}")
            
            return success
        except Exception as e:
            logger.error(f"Erro ao processar e indexar arquivo {file_path}: {str(e)}")
            return False
    
    def reindex_all_documents(self, directory: str = "data/raw") -> Dict[str, Any]:
        """
        Reindexar todos os documentos em um diretório
        
        Args:
            directory: Diretório contendo os documentos
            
        Returns:
            Dict com estatísticas do processo de reindexação
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "failed_files": []
        }
        
        try:
            # Verificar se o diretório existe
            if not os.path.exists(directory):
                logger.warning(f"Diretório não encontrado: {directory}")
                return stats
            
            logger.info(f"Iniciando reindexação de documentos em: {directory}")
            
            # Listar todos os arquivos no diretório
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file_path)
                    ext = ext.lower()
                    
                    stats["total"] += 1
                    
                    # Verificar se é um formato suportado
                    if ext in ['.pdf', '.txt', '.md', '.docx', '.doc']:
                        # Processar e indexar o arquivo
                        success = self.process_and_index_file(file_path)
                        
                        if success:
                            stats["success"] += 1
                            logger.info(f"Documento processado com sucesso: {file_path}")
                        else:
                            stats["failed"] += 1
                            stats["failed_files"].append(file_path)
                            logger.error(f"Falha ao processar documento: {file_path}")
                    else:
                        stats["skipped"] += 1
                        logger.warning(f"Documento ignorado (formato não suportado): {file_path}")
            
            logger.info(f"Reindexação concluída. Estatísticas: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Erro ao reindexar documentos: {str(e)}")
            stats["error"] = str(e)
            return stats
