"""
Módulo para criar um wrapper seguro para o cliente OpenAI
Este módulo fornece uma função para criar um cliente OpenAI de forma simples.
"""
import os
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_safe_openai_client(api_key=None):
    """
    Cria um cliente OpenAI de forma simples.
    
    Args:
        api_key (str, optional): Chave da API OpenAI. Se não fornecida, usa a variável de ambiente.
        
    Returns:
        OpenAI: Cliente OpenAI configurado.
    """
    try:
        # Importar dinamicamente para evitar problemas de importação
        from openai import OpenAI
        
        # Usar a chave da API fornecida ou a variável de ambiente
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
            
        # Criar o cliente com configuração mínima
        return OpenAI(api_key=api_key)
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente OpenAI: {e}")
        raise

# Função de compatibilidade para código existente
create_minimal_openai_client = create_safe_openai_client
