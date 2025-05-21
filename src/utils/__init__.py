"""
Arquivo de inicialização para o pacote utils
Este arquivo é necessário para que o diretório utils seja reconhecido como um pacote Python.
"""
# Importar o módulo openai_safe para garantir que as funções estejam disponíveis
from .openai_safe import create_safe_openai_client
__all__ = ['create_safe_openai_client']
