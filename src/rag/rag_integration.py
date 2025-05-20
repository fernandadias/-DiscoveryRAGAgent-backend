import os
from typing import Dict, List, Any
import weaviate
from src.context.objectives_manager import ObjectivesManager
from src.context.guidelines_manager import GuidelinesManager
import openai
import json

class RAGIntegration:
    def __init__(self):
        # Configurar cliente Weaviate usando variáveis de ambiente
        self.client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL", "https://xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud"),
            auth_client_secret=weaviate.AuthApiKey(os.getenv("WEAVIATE_API_KEY", "")),
        )
        
        # Configurar cliente OpenAI
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Inicializar gerenciadores de contexto
        self.objectives_manager = ObjectivesManager()
        self.guidelines_manager = GuidelinesManager()
    
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
            # Implementação da busca semântica no Weaviate
            result = self.client.query.get(
                "Document", 
                ["content", "title", "metadata"]
            ).with_near_text({
                "concepts": [query]
            }).with_limit(5).do()
            
            return result.get("data", {}).get("Get", {}).get("Document", [])
        except Exception as e:
            print(f"Erro ao recuperar documentos: {str(e)}")
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
"""
    
    def _generate_response(self, prompt: str) -> str:
        """Gera resposta usando a LLM (OpenAI GPT-4o)"""
        try:
            # Chamada real à API da OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em discovery de produto, que ajuda a responder consultas com base em documentos, diretrizes e objetivos específicos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extrair e retornar o texto da resposta
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro ao gerar resposta com OpenAI: {str(e)}")
            # Em caso de erro, retornar mensagem de erro
            return f"Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente mais tarde."
    
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
