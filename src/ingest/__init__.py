"""
Inicializador do módulo de ingestão

Este script inicializa o módulo de ingestão e cria o arquivo __init__.py
"""

# Importar funções principais para facilitar o acesso
from .pdf_extractor import extract_text_from_pdf, extract_text_with_metadata
from .data_ingestion import process_document, process_directory

__all__ = [
    'extract_text_from_pdf',
    'extract_text_with_metadata',
    'process_document',
    'process_directory'
]
