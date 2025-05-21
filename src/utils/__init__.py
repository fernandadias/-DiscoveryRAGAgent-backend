"""
Arquivo de inicialização para o pacote utils

Este arquivo é necessário para que o diretório utils seja reconhecido como um pacote Python.
"""

# Importar o módulo openai_safe para garantir que o monkey patch seja aplicado
from .openai_safe import patch_openai, create_safe_openai_client

__all__ = ['patch_openai', 'create_safe_openai_client']
