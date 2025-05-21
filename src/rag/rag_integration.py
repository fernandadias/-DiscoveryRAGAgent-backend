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
            # Expandir a consulta para melhorar a recuperação semântica
            expanded_query = self._expand_query(query)
            logger.info(f"Consulta expandida: {expanded_query}")
            
            # Implementação da busca semântica no Weaviate usando a API v3
            result = self.client.query.get(
                "Document", 
                ["content", "title", "metadata"]
            ).with_near_text({
                "concepts": [expanded_query]
            }).with_limit(15).do()  # Aumentado para 15 resultados
            
            # Extrair documentos da resposta
            documents = result.get("data", {}).get("Get", {}).get("Document", [])
            
            # Verificar se documents é None e retornar lista vazia nesse caso
            if documents is None:
                logger.warning("Resultado da consulta ao Weaviate retornou None para documentos")
                return []
            
            # Reranking dos resultados para priorizar os mais relevantes
            reranked_docs = self._rerank_documents(documents, query)
                
            logger.info(f"Recuperados {len(reranked_docs)} documentos relevantes para a consulta: {query[:50]}...")
            return reranked_docs
        except Exception as e:
            logger.error(f"Erro ao recuperar documentos: {str(e)}")
            # Em caso de erro, tentar busca alternativa com termos específicos
            return self._fallback_retrieval(query)
    
    def _fallback_retrieval(self, query: str) -> List[Dict]:
        """Método alternativo de recuperação em caso de falha na busca principal"""
        try:
            logger.info("Usando método alternativo de recuperação")
            
            # Extrair palavras-chave da consulta
            keywords = [word.lower() for word in query.split() if len(word) > 3]
            
            # Se houver palavras-chave específicas relacionadas a perfis, adicionar termos específicos
            if any(kw in query.lower() for kw in ["perfil", "usuário", "cliente", "persona"]):
                keywords.extend(["perfil", "usuários", "clientes", "personas"])
            
            # Buscar documentos para cada palavra-chave
            all_docs = []
            for keyword in keywords[:5]:  # Limitar a 5 palavras-chave para evitar muitas consultas
                try:
                    result = self.client.query.get(
                        "Document", 
                        ["content", "title", "metadata"]
                    ).with_near_text({
                        "concepts": [keyword]
                    }).with_limit(5).do()
                    
                    docs = result.get("data", {}).get("Get", {}).get("Document", [])
                    if docs:
                        all_docs.extend(docs)
                except Exception:
                    continue
            
            # Remover duplicatas (baseado no título)
            unique_docs = []
            seen_titles = set()
            for doc in all_docs:
                title = doc.get("title", "")
                if title not in seen_titles:
                    seen_titles.add(title)
                    unique_docs.append(doc)
            
            return unique_docs[:10]  # Limitar a 10 documentos
        except Exception as e:
            logger.error(f"Erro no método alternativo de recuperação: {str(e)}")
            return []
    
    def _expand_query(self, query: str) -> str:
        """
        Expande a consulta para melhorar a recuperação semântica
        Adiciona termos relacionados e sinônimos para aumentar a chance de encontrar documentos relevantes
        """
        # Mapeamento de termos comuns para expansão
        expansions = {
            "perfil": ["perfis", "persona", "personas", "usuário", "usuários", "cliente", "clientes", "segmentação"],
            "usuário": ["usuários", "cliente", "clientes", "perfil", "perfis", "persona", "personas"],
            "cliente": ["clientes", "usuário", "usuários", "perfil", "perfis", "persona", "personas"],
            "discovery": ["descoberta", "pesquisa", "investigação", "análise"],
            "produto": ["produtos", "serviço", "serviços", "solução", "soluções", "aplicativo", "app"],
            "stone": ["ton", "pagar.me", "pagarme", "pagamentos", "maquininha"],
            "ton": ["stone", "pagar.me", "pagarme", "pagamentos", "maquininha"],
            "pagar.me": ["pagarme", "stone", "ton", "pagamentos", "gateway"],
            "pagarme": ["pagar.me", "stone", "ton", "pagamentos", "gateway"]
        }
        
        # Termos específicos para perfis de usuários
        if any(term in query.lower() for term in ["perfil", "usuário", "cliente", "persona"]):
            query = f"{query} perfis personas usuários clientes segmentação comportamento características público-alvo target"
        
        # Expandir a consulta com termos relacionados
        expanded_terms = []
        for word in query.lower().split():
            if word in expansions:
                expanded_terms.extend(expansions[word])
        
        # Combinar a consulta original com os termos expandidos
        if expanded_terms:
            expanded_query = f"{query} {' '.join(expanded_terms)}"
            # Limitar o tamanho da consulta expandida
            if len(expanded_query) > 500:
                expanded_query = expanded_query[:500]
            return expanded_query
        
        return query
    
    def _rerank_documents(self, documents: List[Dict], query: str) -> List[Dict]:
        """
        Reordena os documentos com base na relevância para a consulta
        Implementa um algoritmo simples de reranking baseado em correspondência de termos
        """
        if not documents:
            return []
        
        # Extrair termos importantes da consulta
        query_terms = set(query.lower().split())
        
        # Termos específicos para perfis de usuários
        if any(term in query.lower() for term in ["perfil", "usuário", "cliente", "persona"]):
            query_terms.update(["perfil", "perfis", "usuário", "usuários", "cliente", "clientes", "persona", "personas", "segmentação"])
        
        # Calcular pontuação para cada documento
        scored_docs = []
        for doc in documents:
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            
            # Pontuação baseada na frequência dos termos da consulta no documento
            score = 0
            for term in query_terms:
                # Termos no título têm peso maior
                title_count = title.count(term) * 3
                # Termos no conteúdo
                content_count = content.count(term)
                score += title_count + content_count
            
            # Bônus para documentos com "perfil" ou "usuário" no título quando a consulta é sobre perfis
            if any(term in query.lower() for term in ["perfil", "usuário", "cliente", "persona"]):
                if any(term in title for term in ["perfil", "usuário", "cliente", "persona"]):
                    score += 50
            
            # Adicionar documento com sua pontuação
            scored_docs.append((doc, score))
        
        # Ordenar documentos por pontuação (maior para menor)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar apenas os documentos, sem as pontuações
        return [doc for doc, _ in scored_docs]
    
    def _build_rag_context(self, documents: List[Dict]) -> str:
        """Constrói o contexto RAG a partir dos documentos recuperados"""
        if not documents:
            return "Não foram encontrados documentos relevantes para esta consulta."
            
        context_parts = []
        
        for i, doc in enumerate(documents):
            title = doc.get("title", "Documento sem título")
            content = doc.get("content", "")
            
            # Limitar o tamanho do conteúdo para evitar contextos muito grandes
            if len(content) > 2000:
                content = content[:2000] + "..."
                
            # Adicionar fonte numerada para facilitar citações
            context_parts.append(f"--- Fonte {i+1}: {title} ---\n{content}\n")
        
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

IMPORTANTE:
1. Inclua citações diretas das fontes quando relevante, indicando de qual fonte (número) a informação foi extraída.
2. Se a informação solicitada estiver presente no contexto, SEMPRE cite-a diretamente.
3. Utilize formatação rica para tornar a resposta mais legível:
   - Use títulos (# Título, ## Subtítulo) para organizar seções
   - Use listas (- item ou 1. item) para enumerar pontos
   - Use **negrito** para destacar informações importantes
   - Use > para criar callouts com informações destacadas
   - Use tabelas quando apropriado para organizar dados
4. Se não encontrar informações específicas sobre a consulta, indique claramente que não há dados suficientes.
5. Organize a resposta em seções lógicas para facilitar a compreensão.
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
                    {"role": "system", "content": "Você é um assistente especializado em discovery de produto, que ajuda a responder consultas com base em documentos, diretrizes e objetivos específicos. Inclua citações diretas das fontes quando relevante. Use formatação rica (markdown) para tornar suas respostas mais legíveis e estruturadas."},
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
            # Extrair metadados relevantes
            metadata = doc.get("metadata", {})
            file_path = metadata.get("file_path", "")
            
            # Determinar o nome do documento
            doc_name = doc.get("title", f"Documento {i+1}")
            
            # Extrair um snippet relevante do conteúdo
            content = doc.get("content", "")
            snippet = content[:300] + "..." if len(content) > 300 else content
            
            sources.append({
                "id": f"doc{i+1}",
                "name": doc_name,
                "snippet": snippet,
                "url": file_path  # Usar o caminho do arquivo como URL
            })
        
        return sources
