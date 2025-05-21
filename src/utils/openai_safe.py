"""
Módulo para criar um wrapper seguro para o cliente OpenAI
Este módulo fornece uma função para criar um cliente OpenAI que ignora
parâmetros problemáticos como 'proxies' que causam erros na versão atual da API.
"""
import os
import logging

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

# Nota: O monkey patch foi removido para evitar problemas de compatibilidade
# com a versão atual da biblioteca OpenAI
