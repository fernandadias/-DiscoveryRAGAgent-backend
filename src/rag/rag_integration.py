import os
from typing import Dict, List, Any
import weaviate
from weaviate.auth import AuthApiKey
from src.context.objectives_manager import ObjectivesManager
from src.context.guidelines_manager import GuidelinesManager
import json
import logging
import requests
import re
from datetime import datetime

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
        
        try:    
            self.client = weaviate.Client(
                url=weaviate_url,
                auth_client_secret=auth_config
            )
            # Verificar conexão imediatamente
            self.weaviate_connected = self.client.is_ready()
            if not self.weaviate_connected:
                logger.warning("Não foi possível conectar ao Weaviate durante a inicialização")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Weaviate: {str(e)}")
            self.client = None
            self.weaviate_connected = False
        
        # Inicializar gerenciadores de contexto
        self.objectives_manager = ObjectivesManager()
        self.guidelines_manager = GuidelinesManager()
        
        # Não inicializar OpenAI Client aqui, usar método direto
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Configurar variável de ambiente OPENAI_APIKEY para Weaviate
        if self.openai_api_key and not os.getenv("OPENAI_APIKEY"):
            os.environ["OPENAI_APIKEY"] = self.openai_api_key
        
        # Mapeamento de tópicos para expansão semântica
        self.topic_expansions = {
            "perfil": [
                "perfis de usuários", "personas", "segmentação de clientes", 
                "público-alvo", "comportamento do usuário", "necessidades do cliente",
                "características do usuário", "tipos de clientes", "segmentos de mercado",
                "usuários típicos", "clientes ideais", "target", "demografia"
            ],
            "usuário": [
                "cliente", "consumidor", "pessoa", "indivíduo", "utilizador",
                "comprador", "público", "audiência", "target", "prospect"
            ],
            "discovery": [
                "pesquisa", "investigação", "exploração", "análise", "estudo",
                "levantamento", "diagnóstico", "avaliação", "descoberta", "insights"
            ],
            "produto": [
                "serviço", "solução", "oferta", "aplicativo", "app", "plataforma",
                "ferramenta", "sistema", "funcionalidade", "recurso"
            ],
            "stone": [
                "ton", "pagar.me", "pagarme", "pagamentos", "maquininha",
                "adquirência", "gateway", "financeiro", "banking", "conta"
            ],
            "objetivo": [
                "meta", "propósito", "finalidade", "alvo", "intenção",
                "missão", "visão", "estratégia", "plano", "direção"
            ],
            "experiência": [
                "ux", "ui", "usabilidade", "interface", "interação",
                "jornada", "fluxo", "design", "layout", "navegação"
            ],
            "problema": [
                "dor", "dificuldade", "desafio", "obstáculo", "barreira",
                "limitação", "restrição", "impedimento", "complicação", "questão"
            ],
            "solução": [
                "resolução", "resposta", "abordagem", "estratégia", "tática",
                "método", "técnica", "prática", "implementação", "execução"
            ],
            "mercado": [
                "indústria", "setor", "nicho", "segmento", "área",
                "campo", "domínio", "espaço", "ambiente", "ecossistema"
            ]
        }
    
    def process_query(self, query: str, objective_id: str = None) -> Dict[str, Any]:
        """
        Processa uma consulta do usuário usando o pipeline RAG completo
        
        Args:
            query: A consulta do usuário
            objective_id: O ID do objetivo selecionado
            
        Returns:
            Dict contendo a resposta e as fontes utilizadas
        """
        try:
            # Se não houver objetivo especificado, usar o padrão
            if not objective_id:
                objective_id = self.objectives_manager.get_default_objective_id()
            
            # 1. Expandir a consulta para melhorar a recuperação
            expanded_query = self._expand_query(query)
            logger.info(f"Consulta expandida: {expanded_query}")
            
            # 2. Recuperar documentos relevantes usando busca híbrida
            relevant_docs = self.search_documents(query, expanded_query, limit=15)
            
            # 3. Verificar se há documentos específicos sobre o tema da consulta
            if len(relevant_docs) < 5:
                # Tentar busca por palavras-chave como fallback
                fallback_docs = self._keyword_search(query)
                # Combinar com os documentos já recuperados
                relevant_docs = self._merge_documents(relevant_docs, fallback_docs)
            
            # 4. Construir o contexto com os documentos recuperados
            rag_context = self._build_rag_context(relevant_docs, query)
            
            # 5. Obter o conteúdo do objetivo selecionado
            objective_content = self.objectives_manager.get_objective_content(objective_id)
            
            # 6. Obter todas as diretrizes
            guidelines_content = self.guidelines_manager.get_all_guidelines_content()
            
            # 7. Construir o prompt completo para a LLM
            prompt = self._build_prompt(query, rag_context, guidelines_content, objective_content)
            
            # 8. Gerar resposta usando a LLM (OpenAI GPT-4o)
            response = self._generate_response(prompt)
            
            # 9. Formatar e retornar o resultado
            return {
                "response": response,
                "sources": self._format_sources(relevant_docs)
            }
        except Exception as e:
            logger.error(f"Erro no processamento da consulta: {str(e)}")
            # Fallback para resposta de erro
            return {
                "response": f"Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente mais tarde.\n\nDetalhes técnicos: {str(e)}",
                "sources": []
            }
    
    def search_documents(self, query: str, expanded_query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca documentos relevantes para a consulta usando uma abordagem híbrida:
        1. Busca semântica (se vectorizer disponível)
        2. Busca por palavras-chave como fallback
        
        Args:
            query: Consulta do usuário
            expanded_query: Consulta expandida com termos relacionados (opcional)
            limit: Número máximo de documentos a retornar
            
        Returns:
            Lista de documentos relevantes
        """
        logger.info(f"Buscando documentos para: '{query}'")
        
        if not expanded_query:
            expanded_query = self._expand_query(query)
        
        try:
            # Verificar se o cliente está conectado
            if not self.client or not self.weaviate_connected:
                logger.error("Não foi possível conectar ao Weaviate")
                return self._keyword_search(query, limit)
            
            # Verificar conexão novamente
            try:
                self.weaviate_connected = self.client.is_ready()
                if not self.weaviate_connected:
                    logger.error("Weaviate não está pronto")
                    return self._keyword_search(query, limit)
            except Exception as e:
                logger.error(f"Erro ao verificar conexão com Weaviate: {str(e)}")
                return self._keyword_search(query, limit)
            
            # Verificar configuração do vectorizer
            try:
                schema = self.client.schema.get()
                document_class = None
                for class_obj in schema.get("classes", []):
                    if class_obj.get("class") == "Document":
                        document_class = class_obj
                        break
                
                vectorizer = document_class.get("vectorizer") if document_class else "none"
                logger.info(f"Vectorizer configurado: {vectorizer}")
            except Exception as e:
                logger.error(f"Erro ao obter schema do Weaviate: {str(e)}")
                vectorizer = "none"
            
            results = []
            
            # Tentar busca semântica se vectorizer não for 'none'
            if vectorizer != "none":
                try:
                    logger.info("Tentando busca semântica...")
                    semantic_results = self.client.query.get(
                        "Document", 
                        ["content", "title", "semantic_context", "keywords", "file_name", "file_path"]
                    ).with_near_text({
                        "concepts": [expanded_query]
                    }).with_limit(limit).do()
                    
                    documents = semantic_results.get("data", {}).get("Get", {}).get("Document", [])
                    logger.info(f"Busca semântica retornou {len(documents)} documentos")
                    
                    if documents:
                        results.extend(documents)
                except Exception as e:
                    logger.warning(f"Erro na busca semântica: {str(e)}")
            
            # Se não houver resultados ou vectorizer for 'none', usar busca por palavras-chave
            if not results:
                logger.info("Usando busca por palavras-chave como fallback...")
                keyword_results = self._keyword_search(query, limit)
                if keyword_results:
                    results.extend(keyword_results)
            
            # Reranking dos resultados para priorizar os mais relevantes
            if results:
                results = self._rerank_documents(results, query)
            
            logger.info(f"Busca híbrida retornou {len(results)} documentos relevantes")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {str(e)}")
            # Em caso de erro, tentar busca por palavras-chave como último recurso
            return self._keyword_search(query, limit)
    
    def _keyword_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Realiza busca por palavras-chave nos documentos
        
        Args:
            query: Consulta do usuário
            limit: Número máximo de documentos a retornar
            
        Returns:
            Lista de documentos relevantes
        """
        try:
            logger.info(f"Realizando busca por palavras-chave para: '{query}'")
            
            # Extrair palavras-chave da consulta (palavras com mais de 3 caracteres)
            query_words = [word.lower() for word in re.findall(r'\w+', query.lower()) if len(word) > 3]
            
            # Expandir com sinônimos e termos relacionados
            expanded_terms = set(query_words)
            
            # Mapeamento de sinônimos e termos relacionados para termos comuns
            synonyms = {
                "perfil": ["persona", "usuário", "cliente", "público", "segmento"],
                "usuário": ["cliente", "pessoa", "consumidor", "utilizador"],
                "cliente": ["usuário", "pessoa", "consumidor", "utilizador"],
                "segmento": ["grupo", "categoria", "classe", "tipo"],
                "comportamento": ["hábito", "costume", "prática", "ação"],
                "necessidade": ["demanda", "requisito", "exigência", "precisão"],
                "problema": ["dor", "dificuldade", "obstáculo", "desafio"],
                "objetivo": ["meta", "propósito", "finalidade", "alvo"],
                "discovery": ["pesquisa", "investigação", "exploração", "análise"],
                "experiência": ["ux", "ui", "usabilidade", "interface"],
                "produto": ["serviço", "solução", "oferta", "aplicativo"],
                "mercado": ["indústria", "setor", "nicho", "segmento"]
            }
            
            # Expandir cada termo da consulta
            for word in query_words:
                if word in synonyms:
                    expanded_terms.update(synonyms[word])
            
            logger.info(f"Termos expandidos: {expanded_terms}")
            
            # Obter todos os documentos para filtragem local
            try:
                if not self.client or not self.weaviate_connected:
                    # Fallback para busca local em arquivos
                    return self._local_file_search(query, expanded_terms, limit)
                
                all_docs = self.client.query.get(
                    "Document", 
                    ["content", "title", "semantic_context", "keywords", "file_name", "file_path"]
                ).with_limit(1000).do()
                
                documents = all_docs.get("data", {}).get("Get", {}).get("Document", [])
                logger.info(f"Recuperados {len(documents)} documentos para filtragem local")
                
                # Filtrar documentos que contêm os termos expandidos
                relevant_docs = []
                for doc in documents:
                    content = doc.get("content", "").lower()
                    title = doc.get("title", "").lower()
                    
                    # Calcular pontuação de relevância baseada na frequência dos termos
                    score = 0
                    for term in expanded_terms:
                        # Pontuação no título tem peso maior
                        title_count = title.count(term) * 3
                        content_count = content.count(term)
                        score += title_count + content_count
                    
                    # Adicionar documento se tiver alguma pontuação
                    if score > 0:
                        doc["score"] = score
                        relevant_docs.append(doc)
                
                # Ordenar por pontuação (mais relevantes primeiro)
                relevant_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
                
                # Limitar ao número solicitado
                top_docs = relevant_docs[:limit]
                
                logger.info(f"Busca por palavras-chave encontrou {len(relevant_docs)} documentos relevantes, retornando os {len(top_docs)} mais relevantes")
                
                return top_docs
            except Exception as e:
                logger.error(f"Erro na busca por palavras-chave no Weaviate: {str(e)}")
                # Fallback para busca local em arquivos
                return self._local_file_search(query, expanded_terms, limit)
                
        except Exception as e:
            logger.error(f"Erro na busca por palavras-chave: {str(e)}")
            return []
    
    def _local_file_search(self, query: str, expanded_terms: set, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca em arquivos locais quando o Weaviate não está disponível
        """
        try:
            logger.info("Realizando busca local em arquivos como fallback")
            
            # Diretório de dados
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw")
            
            if not os.path.exists(data_dir):
                logger.error(f"Diretório de dados não encontrado: {data_dir}")
                return []
            
            # Listar arquivos
            files = os.listdir(data_dir)
            logger.info(f"Encontrados {len(files)} arquivos para busca local")
            
            # Processar arquivos de texto
            relevant_docs = []
            
            for file_name in files:
                file_path = os.path.join(data_dir, file_name)
                
                if not os.path.isfile(file_path):
                    continue
                
                # Extrair extensão
                _, ext = os.path.splitext(file_name)
                ext = ext.lower()
                
                # Processar apenas arquivos de texto
                if ext in ['.txt', '.md', '.csv']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        logger.warning(f"Erro ao ler arquivo {file_name}: {str(e)}")
                        continue
                    
                    # Calcular pontuação
                    score = 0
                    content_lower = content.lower()
                    
                    for term in expanded_terms:
                        score += content_lower.count(term)
                    
                    if score > 0:
                        relevant_docs.append({
                            "title": file_name,
                            "content": content,
                            "file_name": file_name,
                            "file_path": file_path,
                            "score": score
                        })
            
            # Ordenar por pontuação
            relevant_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Limitar ao número solicitado
            top_docs = relevant_docs[:limit]
            
            logger.info(f"Busca local encontrou {len(relevant_docs)} documentos relevantes, retornando os {len(top_docs)} mais relevantes")
            
            return top_docs
            
        except Exception as e:
            logger.error(f"Erro na busca local em arquivos: {str(e)}")
            return []
    
    def _is_about_profiles(self, query: str) -> bool:
        """Verifica se a consulta é sobre perfis de usuários"""
        profile_terms = [
            "perfil", "perfis", "usuário", "usuários", "cliente", "clientes", 
            "persona", "personas", "segmentação", "público-alvo", "target"
        ]
        query_lower = query.lower()
        return any(term in query_lower for term in profile_terms)
    
    def _has_profile_documents(self, documents: List[Dict]) -> bool:
        """Verifica se há documentos específicos sobre perfis na lista"""
        if not documents:
            return False
            
        profile_terms = [
            "perfil", "perfis", "usuário", "usuários", "cliente", "clientes", 
            "persona", "personas", "segmentação", "público-alvo"
        ]
        
        for doc in documents[:5]:  # Verificar apenas os 5 primeiros documentos
            content = doc.get("content", "").lower()
            # Verificar se o documento tem uma concentração significativa de termos sobre perfis
            term_count = sum(content.count(term) for term in profile_terms)
            if term_count > 5:  # Limiar arbitrário para considerar um documento sobre perfis
                return True
                
        return False
    
    def _merge_documents(self, primary_docs: List[Dict], secondary_docs: List[Dict]) -> List[Dict]:
        """Combina duas listas de documentos, removendo duplicatas e priorizando os primários"""
        if not primary_docs:
            return secondary_docs
            
        if not secondary_docs:
            return primary_docs
            
        # Usar um conjunto para rastrear documentos já incluídos (pelo título)
        included_titles = set()
        merged_docs = []
        
        # Adicionar documentos primários primeiro
        for doc in primary_docs:
            title = doc.get("title", "")
            if title not in included_titles:
                included_titles.add(title)
                merged_docs.append(doc)
        
        # Adicionar documentos secundários que não são duplicatas
        for doc in secondary_docs:
            title = doc.get("title", "")
            if title not in included_titles:
                included_titles.add(title)
                merged_docs.append(doc)
        
        return merged_docs
    
    def _expand_query(self, query: str) -> str:
        """
        Expande a consulta com termos relacionados para melhorar a recuperação
        
        Args:
            query: Consulta original do usuário
            
        Returns:
            Consulta expandida com termos relacionados
        """
        # Extrair palavras-chave da consulta
        query_words = [word.lower() for word in re.findall(r'\w+', query.lower()) if len(word) > 3]
        
        # Expandir com termos relacionados
        expanded_terms = []
        
        # 1. Adicionar termos relacionados a cada palavra-chave
        for word in query_words:
            for topic, expansions in self.topic_expansions.items():
                if word in topic or topic in word:
                    expanded_terms.extend(expansions)
        
        # 2. Adicionar termos específicos para consultas sobre perfis
        if self._is_about_profiles(query):
            expanded_terms.extend([
                "quem são os usuários", "quais são os perfis", "tipos de usuários",
                "segmentos de clientes", "características dos usuários", "comportamento dos clientes",
                "necessidades dos usuários", "personas identificadas", "público-alvo definido",
                "segmentação de mercado", "perfil demográfico", "perfis já identificados",
                "usuários conhecidos", "personas existentes", "segmentos definidos",
                "clientes atuais", "base de usuários"
            ])
        
        if expanded_terms:
            # Remover duplicatas mantendo a ordem
            unique_expansions = []
            seen = set()
            for term in expanded_terms:
                if term not in seen:
                    seen.add(term)
                    unique_expansions.append(term)
            
            expanded_query = f"{query} {' '.join(unique_expansions)}"
            # Limitar o tamanho da consulta expandida
            if len(expanded_query) > 1000:
                expanded_query = expanded_query[:1000]
            return expanded_query
        
        return query
    
    def _rerank_documents(self, documents: List[Dict], query: str) -> List[Dict]:
        """
        Reordena os documentos com base na relevância para a consulta
        Implementa um algoritmo de reranking baseado em correspondência de termos e contexto semântico
        """
        if not documents:
            return []
        
        # Extrair termos importantes da consulta
        query_terms = set(query.lower().split())
        query_lower = query.lower()
        
        # Verificar se a consulta é sobre perfis de usuários
        is_profile_query = self._is_about_profiles(query)
        
        # Termos específicos para perfis de usuários
        profile_terms = [
            "perfil", "perfis", "usuário", "usuários", "cliente", "clientes", 
            "persona", "personas", "segmentação", "público-alvo", "target"
        ]
        
        # Calcular pontuação para cada documento
        scored_docs = []
        for doc in documents:
            score = 0
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            
            # 1. Correspondência de termos da consulta no título (peso alto)
            for term in query_terms:
                if term in title:
                    score += 10
            
            # 2. Correspondência de termos da consulta no conteúdo
            for term in query_terms:
                score += content.count(term) * 2
            
            # 3. Correspondência exata da consulta (peso muito alto)
            if query_lower in content:
                score += 50
            
            # 4. Pontuação adicional para documentos sobre perfis se a consulta for sobre perfis
            if is_profile_query:
                for term in profile_terms:
                    if term in content:
                        score += content.count(term)
            
            # 5. Pontuação baseada em contexto semântico
            semantic_context = doc.get("semantic_context", "")
            if semantic_context:
                if is_profile_query and "perfil" in semantic_context:
                    score += 30
                elif any(topic in semantic_context for topic in query_terms):
                    score += 20
            
            # 6. Pontuação baseada em palavras-chave
            keywords = doc.get("keywords", [])
            if keywords:
                for keyword in keywords:
                    if keyword.lower() in query_lower:
                        score += 15
            
            # Adicionar documento com sua pontuação
            scored_docs.append((doc, score))
        
        # Ordenar documentos por pontuação (maior para menor)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar apenas os documentos, sem as pontuações
        return [doc for doc, _ in scored_docs]
    
    def _build_rag_context(self, documents: List[Dict], query: str) -> str:
        """
        Constrói o contexto RAG a partir dos documentos recuperados
        
        Args:
            documents: Lista de documentos recuperados
            query: Consulta original do usuário
            
        Returns:
            String contendo o contexto RAG formatado
        """
        if not documents:
            return "Não foram encontrados documentos relevantes para a consulta."
        
        # Limitar o número de documentos para evitar contexto muito grande
        max_docs = min(10, len(documents))
        selected_docs = documents[:max_docs]
        
        # Construir o contexto
        context = f"Contexto baseado em {max_docs} documentos relevantes para a consulta: '{query}'\n\n"
        
        for i, doc in enumerate(selected_docs):
            title = doc.get("title", f"Documento {i+1}")
            content = doc.get("content", "")
            file_name = doc.get("file_name", "")
            
            # Limitar o tamanho do conteúdo para evitar contexto muito grande
            max_content_length = 1000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            # Adicionar informações do documento ao contexto
            context += f"--- Documento {i+1}: {title} ---\n"
            if file_name:
                context += f"Fonte: {file_name}\n"
            context += f"{content}\n\n"
        
        return context
    
    def _build_prompt(self, query: str, rag_context: str, guidelines: str, objective: str) -> str:
        """
        Constrói o prompt completo para a LLM
        
        Args:
            query: Consulta do usuário
            rag_context: Contexto RAG construído a partir dos documentos
            guidelines: Diretrizes para a resposta
            objective: Objetivo selecionado
            
        Returns:
            String contendo o prompt completo
        """
        # Construir o prompt
        prompt = f"""Você é um assistente especializado em responder perguntas com base em documentos fornecidos.

CONTEXTO:
{rag_context}

DIRETRIZES:
{guidelines}

OBJETIVO DA CONVERSA:
{objective}

PERGUNTA DO USUÁRIO:
{query}

Por favor, responda à pergunta do usuário com base apenas nas informações fornecidas no contexto acima. 
Se as informações no contexto não forem suficientes para responder completamente à pergunta, indique claramente o que não pode ser respondido.
Cite as fontes específicas (número do documento) ao fornecer informações.
Formate sua resposta em markdown para melhor legibilidade.
"""
        
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
        """
        Gera uma resposta usando a OpenAI API
        
        Args:
            prompt: Prompt completo para a LLM
            
        Returns:
            String contendo a resposta gerada
        """
        try:
            # Usar a API OpenAI v1.0.0+
            from openai import OpenAI
            
            # Inicializar cliente OpenAI - REMOVIDO PARÂMETRO PROXIES QUE CAUSAVA ERRO
            client = OpenAI(api_key=self.openai_api_key)
            
            # Chamar a API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em responder perguntas com base em documentos fornecidos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Extrair e retornar a resposta
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            
            # Fallback para resposta simples em caso de erro
            return f"""
# Resposta baseada nos documentos disponíveis

Desculpe, encontrei um problema técnico ao gerar a resposta completa. Aqui está um resumo baseado nos documentos encontrados:

## Informações Relevantes

Os documentos disponíveis contêm informações sobre a consulta realizada, mas não foi possível processar uma resposta detalhada devido a um erro técnico.

## Recomendação

Por favor, tente reformular sua pergunta ou entre em contato com o suporte técnico mencionando o seguinte erro:
"{str(e)}"

---
*Nota: Esta é uma resposta de fallback gerada devido a um erro no processamento da resposta completa.*
"""
    
    def _format_sources(self, documents: List[Dict]) -> List[Dict]:
        """
        Formata as fontes para inclusão na resposta
        
        Args:
            documents: Lista de documentos recuperados
            
        Returns:
            Lista de fontes formatadas
        """
        sources = []
        
        for i, doc in enumerate(documents[:5]):  # Limitar a 5 fontes
            title = doc.get("title", f"Documento {i+1}")
            content = doc.get("content", "")
            file_name = doc.get("file_name", "")
            
            # Extrair um snippet relevante (primeiros 200 caracteres)
            snippet = content[:200] + "..." if len(content) > 200 else content
            
            sources.append({
                "id": str(i+1),
                "name": title,
                "snippet": snippet,
                "link": file_name
            })
        
        return sources
