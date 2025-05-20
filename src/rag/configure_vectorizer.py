"""
Script para configurar o vectorizer na coleção Document no Weaviate

Este script verifica e configura o vectorizer na coleção Document para permitir buscas semânticas.
"""

import os
import sys
import logging
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_vectorizer(weaviate_url, api_key, openai_api_key):
    """
    Configura o vectorizer na coleção Document no Weaviate.
    
    Args:
        weaviate_url (str): URL do endpoint REST Weaviate
        api_key (str): Chave de API para acesso ao Weaviate
        openai_api_key (str): Chave de API da OpenAI para o vectorizer
        
    Returns:
        bool: True se a configuração foi bem-sucedida, False caso contrário
    """
    try:
        # Configurar autenticação
        auth_credentials = None
        if api_key:
            auth_credentials = Auth.api_key(api_key)
        
        # Conectar ao Weaviate
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=auth_credentials,
            headers={"X-OpenAI-Api-Key": openai_api_key}
        )
        
        # Verificar conexão
        if not client.is_ready():
            logger.error(f"Falha ao conectar com Weaviate: {weaviate_url}")
            return False
        
        logger.info(f"Conexão estabelecida com Weaviate: {weaviate_url}")
        
        # Verificar se a coleção Document existe
        try:
            collection = client.collections.get("Document")
            logger.info("Coleção Document encontrada")
            
            # Tentar deletar a coleção existente para recriar com vectorizer correto
            try:
                client.collections.delete("Document")
                logger.info("Coleção Document deletada para recriação com vectorizer correto")
            except Exception as delete_error:
                logger.error(f"Erro ao deletar coleção: {delete_error}")
                return False
            
            # Criar nova coleção com vectorizer correto
            return create_collection_with_vectorizer(client, openai_api_key)
            
        except Exception as collection_error:
            logger.info(f"Coleção Document não encontrada: {collection_error}")
            
            # Criar a coleção com o vectorizer configurado
            logger.info("Criando coleção Document com vectorizer text2vec-openai")
            return create_collection_with_vectorizer(client, openai_api_key)
            
    except Exception as e:
        logger.error(f"Erro ao configurar vectorizer: {e}")
        return False
    finally:
        if 'client' in locals() and client:
            client.close()

def create_collection_with_vectorizer(client, openai_api_key):
    """
    Cria uma nova coleção Document com vectorizer configurado.
    
    Args:
        client: Cliente Weaviate conectado
        openai_api_key (str): Chave de API da OpenAI
        
    Returns:
        bool: True se a criação foi bem-sucedida, False caso contrário
    """
    try:
        # Criar a coleção com vectorizer configurado usando a sintaxe correta
        # Definindo as propriedades diretamente na criação da coleção
        collection = client.collections.create(
            name="Document",
            description="Documentos para o agente de IA de ideação e discovery de produto",
            properties=[
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                    description="Conteúdo textual do documento"
                ),
                Property(
                    name="tipo",
                    data_type=DataType.TEXT,
                    description="Tipo de documento (ex: discovery, entrevista, pesquisa)"
                ),
                Property(
                    name="filename",
                    data_type=DataType.TEXT,
                    description="Nome do arquivo original"
                ),
                Property(
                    name="file_path",
                    data_type=DataType.TEXT,
                    description="Caminho do arquivo original"
                )
            ],
            vectorizer_config=[
                Configure.NamedVectors.text2vec_openai(
                    name="content_vector",
                    source_properties=["content"],
                    model="ada"  # Usando modelo suportado conforme erro
                )
            ]
        )
        
        logger.info("Coleção Document criada com sucesso com vectorizer text2vec-openai")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar coleção: {e}")
        return False

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 4:
        print("Uso: python configure_vectorizer.py <weaviate_url> <api_key> <openai_api_key>")
        sys.exit(1)
    
    # Obter argumentos
    weaviate_url = sys.argv[1]
    api_key = sys.argv[2]
    openai_api_key = sys.argv[3]
    
    # Configurar vectorizer
    success = configure_vectorizer(weaviate_url, api_key, openai_api_key)
    
    if success:
        print("Vectorizer configurado com sucesso!")
    else:
        print("Falha ao configurar vectorizer.")
        sys.exit(1)
