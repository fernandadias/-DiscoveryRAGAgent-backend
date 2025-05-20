"""
Script para testar a integração com Weaviate

Este script testa a conexão com o Weaviate, cria o esquema e indexa documentos processados.
"""

import os
import sys
import logging
from pathlib import Path
import json

# Adicionar o diretório raiz ao path para importação de módulos
sys.path.append('/home/ubuntu/DiscoveryRAGAgent')

# Importar módulos do projeto
from src.rag.weaviate_integration import WeaviateClient, load_processed_documents

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_weaviate_integration():
    """
    Testa a integração com o Weaviate.
    """
    # Configurações do Weaviate
    weaviate_rest_url = "https://zcdif5ntgkmtsrvwx507g.c0.us-west3.gcp.weaviate.cloud"
    admin_api_key = "VISmUEcKgStFN4x1wgqhTsampZzBkwl9di6m"
    readonly_api_key = "r3EJo6ulTPyv7hhhnFxMQvvthgjyyJWOTwzL"
    
    # Diretório de documentos processados
    processed_dir = "/home/ubuntu/DiscoveryRAGAgent/data/processed"
    
    # Conectar ao Weaviate
    logger.info(f"Conectando ao Weaviate: {weaviate_rest_url}")
    client = WeaviateClient(weaviate_rest_url, admin_api_key)
    
    if not client.is_connected():
        logger.error("Falha ao conectar com o Weaviate")
        return False
    
    # Criar esquema
    logger.info("Criando esquema no Weaviate")
    schema_created = client.create_schema()
    
    if not schema_created:
        logger.error("Falha ao criar esquema no Weaviate")
        return False
    
    # Carregar documentos processados
    logger.info(f"Carregando documentos processados de: {processed_dir}")
    documents = load_processed_documents(processed_dir)
    
    if not documents:
        logger.error("Nenhum documento processado encontrado")
        return False
    
    # Adicionar documentos ao Weaviate
    logger.info(f"Indexando {len(documents)} documentos no Weaviate")
    added_count = client.batch_add_documents(documents)
    
    if added_count == 0:
        logger.error("Falha ao indexar documentos no Weaviate")
        return False
    
    logger.info(f"Integração com Weaviate concluída: {added_count} documentos indexados")
    return True

if __name__ == "__main__":
    success = test_weaviate_integration()
    if success:
        print("Teste de integração com Weaviate concluído com sucesso!")
    else:
        print("Teste de integração com Weaviate falhou.")
