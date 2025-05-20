import os
import subprocess
import tempfile
import uuid
import json
from typing import Dict, List, Any, Optional
import weaviate
from PyPDF2 import PdfReader
import re

class DocumentIngestor:
    def __init__(self):
        # Configurar cliente Weaviate usando variáveis de ambiente
        self.client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL", "https://xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud"),
            auth_client_secret=weaviate.AuthApiKey(os.getenv("WEAVIATE_API_KEY", "")),
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
                print("Schema criado com sucesso.")
        except Exception as e:
            print(f"Erro ao verificar/criar schema: {str(e)}")
    
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
            print(f"Erro ao processar PDF {file_path}: {str(e)}")
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
                    text += page.extract_text() + "\n\n"
            return text
        except Exception as e:
            print(f"Erro ao extrair texto com PyPDF2: {str(e)}")
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
            print(f"Erro ao extrair texto com pdftotext: {str(e)}")
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
            print(f"Erro ao extrair metadados com pdfinfo: {str(e)}")
            return {"file_path": file_path, "error": str(e)}
    
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
            print(f"Erro ao indexar documento: {str(e)}")
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
                print(f"Arquivo não encontrado: {file_path}")
                return False
            
            # Verificar a extensão do arquivo
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
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
            else:
                print(f"Formato de arquivo não suportado: {ext}")
                return False
            
            # Indexar o documento
            return self.index_document(document)
        except Exception as e:
            print(f"Erro ao processar e indexar arquivo {file_path}: {str(e)}")
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
                print(f"Diretório não encontrado: {directory}")
                return stats
            
            # Listar todos os arquivos no diretório
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file_path)
                    ext = ext.lower()
                    
                    stats["total"] += 1
                    
                    # Verificar se é um formato suportado
                    if ext in ['.pdf', '.txt', '.md']:
                        # Processar e indexar o arquivo
                        success = self.process_and_index_file(file_path)
                        
                        if success:
                            stats["success"] += 1
                        else:
                            stats["failed"] += 1
                            stats["failed_files"].append(file_path)
                    else:
                        stats["skipped"] += 1
            
            return stats
        except Exception as e:
            print(f"Erro ao reindexar documentos: {str(e)}")
            stats["error"] = str(e)
            return stats
