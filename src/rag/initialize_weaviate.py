import os
import weaviate
from weaviate.auth import AuthApiKey
import json
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_weaviate_schema():
    """
    Inicializa o schema do Weaviate para o DiscoveryRAGAgent
    """
    logger.info("Iniciando configuração do schema do Weaviate...")
    
    # Configurar cliente Weaviate
    weaviate_url = os.getenv("WEAVIATE_URL", "xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s")
    
    # Garantir que a URL tenha o prefixo https://
    if not weaviate_url.startswith("http://") and not weaviate_url.startswith("https://"):
        weaviate_url = f"https://{weaviate_url}"
    
    logger.info(f"Conectando ao Weaviate em: {weaviate_url}")
    
    # Criar conexão com autenticação
    auth_config = None
    if weaviate_api_key:
        auth_config = AuthApiKey(api_key=weaviate_api_key)
        
    client = weaviate.Client(
        url=weaviate_url,
        auth_client_secret=auth_config
    )
    
    # Verificar se o cliente está pronto
    try:
        is_ready = client.is_ready()
        logger.info(f"Weaviate está pronto: {is_ready}")
        if not is_ready:
            logger.error("Weaviate não está pronto. Verifique a conexão.")
            return False
    except Exception as e:
        logger.error(f"Erro ao verificar status do Weaviate: {str(e)}")
        return False
    
    # Definir o schema para a classe Document
    document_class = {
        "class": "Document",
        "description": "Documentos para o DiscoveryRAGAgent",
        "vectorizer": "text2vec-openai",  # Usando OpenAI para vetorização
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
                "dataType": ["text"]
            },
            {
                "name": "content",
                "description": "Conteúdo do documento",
                "dataType": ["text"],
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": False,
                        "vectorizePropertyName": False
                    }
                }
            },
            {
                "name": "metadata",
                "description": "Metadados do documento",
                "dataType": ["text"]
            },
            {
                "name": "tipo",
                "description": "Tipo de documento",
                "dataType": ["text"]
            },
            {
                "name": "filename",
                "description": "Nome do arquivo original",
                "dataType": ["text"]
            },
            {
                "name": "file_path",
                "description": "Caminho do arquivo original",
                "dataType": ["text"]
            }
        ]
    }
    
    # Verificar se a classe já existe
    try:
        schema = client.schema.get()
        existing_classes = [c["class"] for c in schema["classes"]] if "classes" in schema else []
        
        if "Document" not in existing_classes:
            # Criar a classe Document
            client.schema.create_class(document_class)
            logger.info("Schema do Weaviate inicializado com sucesso!")
        else:
            logger.info("Schema do Weaviate já existe.")
        
        # Adicionar alguns documentos de exemplo para teste
        add_sample_documents(client)
            
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar schema do Weaviate: {str(e)}")
        return False

def add_sample_documents(client):
    """
    Adiciona documentos de exemplo ao Weaviate para teste
    """
    logger.info("Verificando se existem documentos de exemplo...")
    
    # Verificar se já existem documentos
    try:
        result = client.query.get("Document", ["title"]).with_limit(1).do()
        documents = result.get("data", {}).get("Get", {}).get("Document", [])
        
        if documents:
            logger.info(f"Documentos já existem no Weaviate. Encontrado: {len(documents)}")
            return
    except Exception as e:
        logger.error(f"Erro ao verificar documentos existentes: {str(e)}")
    
    # Adicionar documentos de exemplo
    sample_documents = [
        {
            "title": "Introdução ao Product Discovery",
            "content": "Product Discovery é o processo de identificar oportunidades de produto que resolvam problemas reais dos usuários e tenham potencial de mercado. Envolve pesquisa, validação de hipóteses e experimentação.",
            "metadata": json.dumps({"type": "introduction", "tags": ["discovery", "product"]}),
            "tipo": "introduction",
            "filename": "intro_product_discovery.md",
            "file_path": "/data/documents/intro_product_discovery.md"
        },
        {
            "title": "Técnicas de Entrevista com Usuários",
            "content": "Entrevistas com usuários são fundamentais para entender necessidades, comportamentos e pontos de dor. Utilize perguntas abertas, evite induzir respostas e foque em experiências reais em vez de opiniões.",
            "metadata": json.dumps({"type": "technique", "tags": ["user research", "interviews"]}),
            "tipo": "technique",
            "filename": "user_interview_techniques.md",
            "file_path": "/data/documents/user_interview_techniques.md"
        },
        {
            "title": "Validação de Hipóteses",
            "content": "A validação de hipóteses é um processo sistemático para testar suposições sobre o produto. Defina hipóteses claras, métricas de sucesso e experimentos que possam falsificar suas suposições.",
            "metadata": json.dumps({"type": "methodology", "tags": ["validation", "experimentation"]}),
            "tipo": "methodology",
            "filename": "hypothesis_validation.md",
            "file_path": "/data/documents/hypothesis_validation.md"
        }
    ]
    
    logger.info(f"Adicionando {len(sample_documents)} documentos de exemplo ao Weaviate...")
    
    # Adicionar cada documento ao Weaviate
    for doc in sample_documents:
        try:
            client.data_object.create(
                data_object=doc,
                class_name="Document"
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar documento '{doc['title']}': {str(e)}")
    
    logger.info("Documentos de exemplo adicionados com sucesso!")

if __name__ == "__main__":
    initialize_weaviate_schema()
