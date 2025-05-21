"""
Módulo para criar um wrapper seguro para o cliente OpenAI

Este módulo fornece uma função para criar um cliente OpenAI que ignora
parâmetros problemáticos como 'proxies' que causam erros na versão atual da API.
"""

import os
import logging
import importlib
import sys
from functools import wraps

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_safe_openai_client(api_key=None, **kwargs):
    """
    Cria um cliente OpenAI seguro que ignora parâmetros problemáticos.
    
    Args:
        api_key (str, optional): Chave da API OpenAI. Se não fornecida, usa a variável de ambiente.
        **kwargs: Argumentos adicionais para o cliente OpenAI.
        
    Returns:
        OpenAI: Cliente OpenAI configurado de forma segura.
    """
    try:
        # Importar dinamicamente para evitar problemas de importação
        from openai import OpenAI
        
        # Remover parâmetros problemáticos conhecidos
        if 'proxies' in kwargs:
            logger.warning("Parâmetro 'proxies' detectado e removido da inicialização do cliente OpenAI")
            del kwargs['proxies']
        
        # Usar a chave da API fornecida ou a variável de ambiente
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
            
        # Criar o cliente com os parâmetros seguros
        return OpenAI(api_key=api_key, **kwargs)
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente OpenAI seguro: {e}")
        raise

# Monkey patch para a classe OpenAI
def patch_openai():
    """
    Aplica um monkey patch na classe OpenAI para garantir que o parâmetro 'proxies' seja ignorado.
    """
    try:
        # Importar o módulo OpenAI
        from openai import OpenAI
        
        # Guardar o inicializador original
        original_init = OpenAI.__init__
        
        # Criar um novo inicializador que filtra o parâmetro 'proxies'
        @wraps(original_init)
        def safe_init(self, *args, **kwargs):
            if 'proxies' in kwargs:
                logger.warning("Monkey patch: Parâmetro 'proxies' detectado e removido da inicialização do cliente OpenAI")
                del kwargs['proxies']
            return original_init(self, *args, **kwargs)
        
        # Substituir o inicializador
        OpenAI.__init__ = safe_init
        
        logger.info("Monkey patch aplicado com sucesso na classe OpenAI")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao aplicar monkey patch na classe OpenAI: {e}")
        return False

# Aplicar o monkey patch automaticamente quando o módulo é importado
patch_applied = patch_openai()
