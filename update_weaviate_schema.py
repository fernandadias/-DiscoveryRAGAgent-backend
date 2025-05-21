import os
import logging
import weaviate
from weaviate.auth import AuthApiKey
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_weaviate_schema():
    """
    Script para atualizar o schema do Weaviate para usar vectorizer 'none'
    """
    try:
        # Configurar cliente Weaviate
        weaviate_url = os.getenv("WEAVIATE_URL", "xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s")
        
        # Garantir que a URL tenha o prefixo https://
        if not weaviate_url.startswith("http://") and not weaviate_url.startswith("https://"):
            weaviate_url = f"https://{weaviate_url}"
        
        # Criar conexão usando a API v3 com autenticação correta
        auth_config = None
        if weaviate_api_key:
            auth_config = AuthApiKey(api_key=weaviate_api_key)
            
        client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=auth_config
        )
        
        # Verificar se o cliente está conectado
        if not client.is_ready():
            logger.error("Não foi possível conectar ao Weaviate")
            return False
        
        # Verificar se a classe Document existe
        schema = client.schema.get()
        document_class = None
        for class_obj in schema.get("classes", []):
            if class_obj.get("class") == "Document":
                document_class = class_obj
                break
        
        if not document_class:
            logger.error("Classe Document não encontrada no schema")
            return False
        
        # Verificar o vectorizer atual
        current_vectorizer = document_class.get("vectorizer")
        logger.info(f"Vectorizer atual: {current_vectorizer}")
        
        # Se o vectorizer já for 'none', não é necessário atualizar
        if current_vectorizer == "none":
            logger.info("Vectorizer já está configurado como 'none'")
            return True
        
        # Deletar a classe Document para recriá-la com vectorizer 'none'
        logger.info("Deletando classe Document para recriá-la com vectorizer 'none'")
        client.schema.delete_class("Document")
        
        # Definir o schema da classe Document com vectorizer 'none'
        document_class_schema = {
            "class": "Document",
            "description": "Documento para RAG",
            "vectorizer": "none",  # Usar 'none' em vez de 'text2vec-openai'
            "properties": [
                {
                    "name": "content",
                    "description": "Conteúdo do documento",
                    "dataType": ["text"]
                },
                {
                    "name": "title",
                    "description": "Título do documento",
                    "dataType": ["text"]
                },
                {
                    "name": "file_name",
                    "description": "Nome do arquivo",
                    "dataType": ["text"]
                },
                {
                    "name": "file_path",
                    "description": "Caminho do arquivo",
                    "dataType": ["text"]
                },
                {
                    "name": "file_type",
                    "description": "Tipo do arquivo",
                    "dataType": ["text"]
                },
                {
                    "name": "semantic_context",
                    "description": "Contexto semântico do documento",
                    "dataType": ["text"]
                },
                {
                    "name": "keywords",
                    "description": "Palavras-chave do documento",
                    "dataType": ["text[]"]
                },
                {
                    "name": "created_at",
                    "description": "Data de criação",
                    "dataType": ["date"]
                }
            ]
        }
        
        # Criar a classe Document com o novo schema
        client.schema.create_class(document_class_schema)
        logger.info("Classe Document recriada com vectorizer 'none'")
        
        # Verificar se a classe foi criada corretamente
        schema = client.schema.get()
        for class_obj in schema.get("classes", []):
            if class_obj.get("class") == "Document":
                logger.info(f"Classe Document criada com vectorizer: {class_obj.get('vectorizer')}")
                return True
        
        logger.error("Falha ao verificar a criação da classe Document")
        return False
    except Exception as e:
        logger.error(f"Erro ao atualizar schema do Weaviate: {str(e)}")
        return False

if __name__ == "__main__":
    update_weaviate_schema()
