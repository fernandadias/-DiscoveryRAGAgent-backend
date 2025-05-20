"""
Módulo de integração entre a interface Streamlit e o pipeline RAG

Este módulo fornece funções para conectar a interface Streamlit ao backend RAG.
"""

import os
import sys
import logging
import weaviate
from weaviate.auth import AuthApiKey
from openai import OpenAI
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGConnector:
    """
    Classe para conectar a interface Streamlit ao pipeline RAG.
    """
    
    def __init__(self, weaviate_url, api_key, openai_api_key, diretrizes_path):
        """
        Inicializa o conector RAG.
        
        Args:
            weaviate_url (str): URL do endpoint REST Weaviate
            api_key (str): Chave de API para acesso ao Weaviate
            openai_api_key (str): Chave de API da OpenAI
            diretrizes_path (str): Caminho para o arquivo de diretrizes
        """
        self.weaviate_url = weaviate_url
        self.api_key = api_key
        self.openai_api_key = openai_api_key
        self.diretrizes_path = diretrizes_path
        
        # Carregar diretrizes
        try:
            with open(diretrizes_path, 'r', encoding='utf-8') as f:
                self.diretrizes = f.read()
            logger.info(f"Diretrizes carregadas de {diretrizes_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar diretrizes: {e}")
            self.diretrizes = "Diretrizes não disponíveis."
    
    def connect_to_weaviate(self):
        """
        Conecta ao Weaviate.
        
        Returns:
            weaviate.Client: Cliente Weaviate conectado ou None em caso de erro
        """
        try:
            # Configurar autenticação usando a API compatível
            auth_config = None
            if self.api_key:
                auth_config = AuthApiKey(api_key=self.api_key)
            
            # Conectar ao Weaviate usando o construtor padrão (compatível com todas as versões)
            client = weaviate.Client(
                url=self.weaviate_url,
                auth_client_secret=auth_config,
                additional_headers={
                    "X-OpenAI-Api-Key": self.openai_api_key
                }
            )
            
            # Verificar conexão
            if not client.is_ready():
                logger.error(f"Falha ao conectar com Weaviate: {self.weaviate_url}")
                return None
            
            logger.info(f"Conexão estabelecida com Weaviate: {self.weaviate_url}")
            return client
            
        except Exception as e:
            logger.error(f"Erro ao conectar com Weaviate: {e}")
            return None
    
    def search_documents(self, query, filters=None, limit=3):
        """
        Realiza busca semântica no Weaviate.
        
        Args:
            query (str): Consulta para busca semântica
            filters (dict): Filtros opcionais
            limit (int): Número máximo de resultados
            
        Returns:
            list: Lista de documentos encontrados ou lista vazia em caso de erro
        """
        try:
            client = self.connect_to_weaviate()
            if not client:
                return []
            
            # Definir as propriedades a serem retornadas
            properties = ["content", "tipo", "filename", "file_path"]
            
            # Executar a consulta usando a API compatível
            result = (
                client.query
                .get("Document", properties)
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            # Extrair documentos do resultado
            documents = result['data']['Get']['Document'] if 'data' in result and 'Get' in result['data'] and 'Document' in result['data']['Get'] else []
            
            logger.info(f"Busca semântica retornou {len(documents)} resultados")
            
            # Formatar resultados
            formatted_results = []
            for doc in documents:
                formatted_results.append({
                    "content": doc.get("content", ""),
                    "filename": doc.get("filename", ""),
                    "chunk_id": doc.get("chunk_id", ""),
                    "tipo": doc.get("tipo", "")
                })
            
            return formatted_results
                
        except Exception as e:
            logger.error(f"Erro ao realizar busca semântica: {e}")
            return []
    
    def generate_response(self, query, results):
        """
        Gera resposta usando o OpenAI GPT-4o.
        
        Args:
            query (str): Consulta do usuário
            results (list): Resultados da busca semântica
            
        Returns:
            str: Resposta gerada ou mensagem de erro
        """
        try:
            # Inicializar cliente OpenAI
            openai_client = OpenAI(api_key=self.openai_api_key)
            
            # Preparar contexto para o prompt
            context = ""
            for i, result in enumerate(results):
                context += f"\n\nDocumento {i+1}:\n{result['content'][:1000]}...\n"
            
            # Criar prompt com diretrizes e contexto
            prompt = f"""
            Você é um assistente especializado em ideação e discovery de produto.
            
            DIRETRIZES:
            {self.diretrizes[:2000]}...
            
            CONTEXTO DOS DOCUMENTOS:
            {context}
            
            CONSULTA DO USUÁRIO:
            {query}
            
            Com base nas diretrizes e no contexto fornecido, responda à consulta do usuário de forma clara e concisa.
            """
            
            # Gerar resposta
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em ideação e discovery de produto."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"Erro ao gerar resposta: {str(e)}"
    
    def process_query(self, query, filters=None):
        """
        Processa uma consulta completa, realizando busca e gerando resposta.
        
        Args:
            query (str): Consulta do usuário
            filters (dict): Filtros opcionais
            
        Returns:
            dict: Resultados da consulta
        """
        try:
            # Realizar busca semântica
            results = self.search_documents(query, filters)
            
            if not results:
                return {
                    "query": query,
                    "results": [],
                    "response": "Não foi possível encontrar informações relevantes para sua consulta. Por favor, tente reformular ou entre em contato com a equipe de suporte."
                }
            
            # Gerar resposta
            response = self.generate_response(query, results)
            
            # Retornar resultados formatados
            return {
                "query": query,
                "results": results,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}")
            return {
                "query": query,
                "results": [],
                "response": f"Erro ao processar consulta: {str(e)}"
            }

# Função para criar uma instância do conector RAG
def create_rag_connector(config_path=None):
    """
    Cria uma instância do conector RAG com base em um arquivo de configuração ou variáveis de ambiente.
    
    Args:
        config_path (str): Caminho para o arquivo de configuração (opcional)
        
    Returns:
        RAGConnector: Instância do conector RAG
    """
    try:
        # Tentar carregar configuração do arquivo
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            weaviate_url = config.get('weaviate_url')
            api_key = config.get('api_key')
            openai_api_key = config.get('openai_api_key')
            diretrizes_path = config.get('diretrizes_path')
        else:
            # Usar variáveis de ambiente ou valores padrão
            weaviate_url = os.environ.get('WEAVIATE_URL', '$WEAVIATE_URL')
            api_key = os.environ.get('WEAVIATE_API_KEY', '$WEAVIATE_API_KEY')
            openai_api_key = os.environ.get('OPENAI_API_KEY', '$OPENAI_API_KEY')
            diretrizes_path = os.environ.get('DIRETRIZES_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'diretrizes_produto.md'))
        
        # Criar e retornar o conector
        return RAGConnector(weaviate_url, api_key, openai_api_key, diretrizes_path)
        
    except Exception as e:
        logger.error(f"Erro ao criar conector RAG: {e}")
        # Retornar um conector com valores padrão em caso de erro
        return None
