"""
Módulo para criar um wrapper seguro para o cliente OpenAI
Este módulo fornece uma função para criar um cliente OpenAI que ignora
parâmetros problemáticos como 'proxies' que causam erros na versão atual da API.
"""
import os
import logging
import inspect

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
        
        # Debug detalhado: registrar todos os kwargs recebidos
        logger.info(f"create_safe_openai_client recebeu os seguintes kwargs: {kwargs}")
        
        # Lista de parâmetros problemáticos conhecidos
        problematic_params = ['proxies', 'proxy', 'http_proxy', 'https_proxy', 'no_proxy']
        
        # Remover todos os parâmetros problemáticos conhecidos
        for param in problematic_params:
            if param in kwargs:
                logger.warning(f"Parâmetro '{param}' detectado e removido da inicialização do cliente OpenAI")
                del kwargs[param]
        
        # Usar a chave da API fornecida ou a variável de ambiente
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')
        
        # Verificar os parâmetros aceitos pelo construtor OpenAI
        valid_params = inspect.signature(OpenAI.__init__).parameters.keys()
        logger.info(f"Parâmetros válidos para OpenAI.__init__: {valid_params}")
        
        # Filtrar apenas os parâmetros válidos
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
        
        # Registrar os kwargs filtrados
        logger.info(f"Parâmetros filtrados para OpenAI.__init__: {filtered_kwargs}")
        
        # Criar o cliente apenas com parâmetros válidos
        # Não usar **kwargs para evitar parâmetros inesperados
        return OpenAI(api_key=api_key, **filtered_kwargs)
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente OpenAI seguro: {e}")
        raise

def create_minimal_openai_client(api_key=None):
    """
    Cria um cliente OpenAI com configuração mínima, sem usar kwargs.
    
    Args:
        api_key (str, optional): Chave da API OpenAI. Se não fornecida, usa a variável de ambiente.
        
    Returns:
        OpenAI: Cliente OpenAI com configuração mínima.
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
        logger.error(f"Erro ao criar cliente OpenAI mínimo: {e}")
        raise

# Nota: O monkey patch foi removido para evitar problemas de compatibilidade
# com a versão atual da biblioteca OpenAI
