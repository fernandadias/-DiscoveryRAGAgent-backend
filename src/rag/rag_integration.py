import os
from typing import Dict, List, Any
import weaviate
from weaviate.auth import AuthApiKey
from src.context.objectives_manager import ObjectivesManager
from src.context.guidelines_manager import GuidelinesManager
import json
import logging
import requests

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGIntegration:
    def __init__(self):
        # Configurar cliente Weaviate usando variáveis de ambiente usando a API v3
        weaviate_url = os.getenv("WEAVIATE_URL", "xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s")
        
        # Garantir que a URL tenha o prefixo https://
        if not weaviate_url.startswith("http://") and not weaviate_url.startswith("https://"):
            weaviate_url = f"https://{weaviate_url}"
        
        # Criar conexão usando a API v3 com autenticação correta
        auth_config = None
        if weaviate_api_key:
            auth_config = AuthApiKey(api_key=weaviate_api_key)
            
        self.client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=auth_config
        )
        
        # Inicializar gerenciadores de contexto
        self.objectives_manager = ObjectivesManager()
        self.guidelines_manager = GuidelinesManager()
        
        # Não inicializar OpenAI Client aqui, usar método direto
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    def process_query(self, query: str, objective_id: str = None) -> Dict[str, Any]:
        """
        Processa uma consulta do usuário usando o pipeline RAG completo
        
        Args:
            query: A consulta do usuário
            objective_id: O ID do objetivo selecionado
            
        Returns:
            Dict contendo a resposta e as fontes utilizadas
        """
        # Se não houver objetivo especificado, usar o padrão
        if not objective_id:
            objective_id = self.objectives_manager.get_default_objective_id()
        
        # 1. Recuperar documentos relevantes do Weaviate
        relevant_docs = self._retrieve_documents(query)
        
        # 2. Construir o contexto com os documentos recuperados
        rag_context = self._build_rag_context(relevant_docs)
        
        # 3. Obter o conteúdo do objetivo selecionado
        objective_content = self.objectives_manager.get_objective_content(objective_id)
        
        # 4. Obter todas as diretrizes
        guidelines_content = self.guidelines_manager.get_all_guidelines_content()
        
        # 5. Construir o prompt completo para a LLM
        prompt = self._build_prompt(query, rag_context, guidelines_content, objective_content)
        
        # 6. Gerar resposta usando a LLM (OpenAI GPT-4o)
        response = self._generate_response(prompt)
        
        # 7. Formatar e retornar o resultado
        return {
            "response": response,
            "sources": self._format_sources(relevant_docs)
        }
    
    def _retrieve_documents(self, query: str) -> List[Dict]:
        """Recupera documentos relevantes do Weaviate"""
        try:
            # Implementação da busca semântica no Weaviate usando a API v3
            result = self.client.query.get(
                "Document", 
                ["content", "title", "metadata"]
            ).with_near_text({
                "concepts": [query]
            }).with_limit(5).do()
            
            # Extrair documentos da resposta
            documents = result.get("data", {}).get("Get", {}).get("Document", [])
            
            # Verificar se documents é None e retornar lista vazia nesse caso
            if documents is None:
                logger.warning("Resultado da consulta ao Weaviate retornou None para documentos")
                return []
                
            logger.info(f"Recuperados {len(documents)} documentos relevantes para a consulta: {query[:50]}...")
            return documents
        except Exception as e:
            logger.error(f"Erro ao recuperar documentos: {str(e)}")
            # Em caso de erro, retornar lista vazia
            return []
    
    def _build_rag_context(self, documents: List[Dict]) -> str:
        """Constrói o contexto RAG a partir dos documentos recuperados"""
        if not documents:
            return "Não foram encontrados documentos relevantes para esta consulta."
            
        context_parts = []
        
        for doc in documents:
            title = doc.get("title", "Documento sem título")
            content = doc.get("content", "")
            context_parts.append(f"--- {title} ---\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, rag_context: str, guidelines: str, objective: str) -> str:
        """
        Constrói o prompt completo seguindo o fluxo:
        RAG > Diretrizes > Objetivo > Consulta
        """
        return f"""
# Contexto da Base de Conhecimento
{rag_context}

# Diretrizes Estratégicas
{guidelines}

# Objetivo da Conversa
{objective}

# Consulta do Usuário
{query}

Com base no contexto fornecido, nas diretrizes estratégicas e no objetivo da conversa, responda à consulta do usuário de forma clara, precisa e alinhada com o objetivo selecionado.
Inclua citações diretas das fontes quando relevante, indicando de qual documento a informação foi extraída.
"""
    
    def _generate_response(self, prompt: str) -> str:
        """Gera resposta usando a LLM (OpenAI GPT-4o) com chamada direta à API"""
        try:
            # Usar chamada direta à API OpenAI via requests em vez do cliente
            api_key = self.openai_api_key
            if not api_key:
                logger.error("API key da OpenAI não configurada")
                return "Erro: API key da OpenAI não configurada. Por favor, configure a variável de ambiente OPENAI_API_KEY."
            
            # Endpoint da API OpenAI
            url = "https://api.openai.com/v1/chat/completions"
            
            # Cabeçalhos da requisição
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # Corpo da requisição
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "Você é um assistente especializado em discovery de produto, que ajuda a responder consultas com base em documentos, diretrizes e objetivos específicos. Inclua citações diretas das fontes quando relevante."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            # Fazer a requisição
            logger.info("Enviando requisição para a API da OpenAI")
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                # Extrair e retornar o texto da resposta
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Erro na API da OpenAI: {response.status_code} - {response.text}")
                return f"Desculpe, ocorreu um erro ao processar sua consulta. Código: {response.status_code}. Por favor, tente novamente mais tarde."
                
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com OpenAI: {str(e)}")
            return f"Desculpe, ocorreu um erro ao processar sua consulta: {str(e)}. Por favor, tente novamente mais tarde."
    
    def _format_sources(self, documents: List[Dict]) -> List[Dict]:
        """Formata as fontes para retorno na API"""
        sources = []
        
        for i, doc in enumerate(documents):
            sources.append({
                "id": f"doc{i+1}",
                "name": doc.get("title", f"Documento {i+1}"),
                "snippet": doc.get("content", "")[:200] + "...",
                "url": None  # Pode ser implementado se os documentos tiverem URLs
            })
        
        return sources
