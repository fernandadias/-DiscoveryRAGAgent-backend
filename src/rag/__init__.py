"""
Inicializador do módulo RAG

Este script inicializa o módulo RAG e cria o arquivo __init__.py
"""

# Importar funções principais para facilitar o acesso
from .weaviate_integration import WeaviateClient, load_processed_documents

__all__ = [
    'WeaviateClient',
    'load_processed_documents'
]
