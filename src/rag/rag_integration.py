"""
Módulo de integração RAG para o agente de IA

Este módulo contém funções para integrar o RAG (Retrieval Augmented Generation)
com o LLM, incluindo consulta à base vetorial e geração de respostas.
"""

import os
import logging
import json
from pathlib import Path
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import QueryReference

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGAgent:
    """Agente RAG para ideação e discovery de produto."""
    
    def __init__(self, weaviate_url, api_key=None, diretrizes_path=None):
        """
        Inicializa o agente RAG.
        
        Args:
            weaviate_url (str): URL do endpoint REST Weaviate
            api_key (str, optional): Chave de API para acesso ao Weaviate
            diretrizes_path (str, optional): Caminho para o arquivo de diretrizes
        """
        self.weaviate_url = weaviate_url
        self.api_key = api_key
        self.diretrizes_path = diretrizes_path
        self.client = None
        self.diretrizes = None
        
        # Conectar ao Weaviate
        self.connect()
        
        # Carregar diretrizes se o caminho for fornecido
        if diretrizes_path:
            self.load_diretrizes(diretrizes_path)
    
    def connect(self):
        """Estabelece conexão com o Weaviate."""
        try:
            # Configurar autenticação se a chave for fornecida
            auth_credentials = None
            if self.api_key:
                auth_credentials = Auth.api_key(self.api_key)
            
            # Conectar ao Weaviate usando o helper function oficial
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_url,
                auth_credentials=auth_credentials
            )
            
            # Verificar conexão
            if self.client.is_ready():
                logger.info(f"Conexão estabelecida com Weaviate: {self.weaviate_url}")
            else:
                logger.error(f"Falha ao conectar com Weaviate: {self.weaviate_url}")
                self.client = None
                
        except Exception as e:
            logger.error(f"Erro ao conectar com Weaviate: {e}")
            self.client = None
    
    def load_diretrizes(self, path):
        """
        Carrega as diretrizes de produto.
        
        Args:
            path (str): Caminho para o arquivo de diretrizes
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.diretrizes = f.read()
            logger.info(f"Diretrizes carregadas de: {path}")
        except Exception as e:
            logger.error(f"Erro ao carregar diretrizes: {e}")
            self.diretrizes = None
    
    def search_documents(self, query, collection_name="Document", limit=5):
        """
        Realiza uma busca semântica no Weaviate.
        
        Args:
            query (str): Consulta em linguagem natural
            collection_name (str): Nome da coleção no Weaviate
            limit (int): Número máximo de resultados
            
        Returns:
            list: Lista de documentos encontrados
        """
        if not self.client:
            logger.error("Cliente não está conectado ao Weaviate")
            return []
        
        try:
            # Realizar busca semântica
            collection = self.client.collections.get(collection_name)
            
            # Definir as propriedades a serem retornadas
            properties = ["content", "tipo", "filename", "file_path"]
            
            # Executar a consulta
            result = collection.query.near_text(
                query=query,
                limit=limit
            ).with_additional(["distance"]).with_fields(properties).do()
            
            # Extrair documentos do resultado
            documents = result.objects
            
            logger.info(f"Busca concluída: {len(documents)} documentos encontrados")
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao realizar busca no Weaviate: {e}")
            return []
    
    def generate_response(self, query, openai_api_key=None):
        """
        Gera uma resposta usando RAG (Retrieval Augmented Generation).
        
        Args:
            query (str): Consulta do usuário
            openai_api_key (str, optional): Chave de API da OpenAI
            
        Returns:
            dict: Resposta gerada e documentos recuperados
        """
        if not self.client:
            logger.error("Cliente não está conectado ao Weaviate")
            return {"response": "Erro: Não foi possível conectar à base de conhecimento.", "documents": []}
        
        if not openai_api_key:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                logger.error("Chave de API da OpenAI não fornecida")
                return {"response": "Erro: Chave de API da OpenAI não fornecida.", "documents": []}
        
        try:
            # Recuperar documentos relevantes
            documents = self.search_documents(query)
            
            if not documents:
                logger.warning("Nenhum documento relevante encontrado")
                return {"response": "Não encontrei informações específicas sobre isso na base de conhecimento.", "documents": []}
            
            # Preparar contexto para o LLM
            context = ""
            for doc in documents:
                context += f"\n\nDocumento: {doc.properties.get('filename', 'Sem nome')}\n"
                context += f"Conteúdo: {doc.properties.get('content', 'Sem conteúdo')}\n"
            
            # Adicionar diretrizes ao contexto se disponíveis
            if self.diretrizes:
                context += f"\n\nDiretrizes de Produto:\n{self.diretrizes}\n"
            
            # Construir prompt para o LLM
            prompt = f"""
            Você é um assistente especializado em ideação e discovery de produto para a Stone, 
            focado na personalização da Home do aplicativo.
            
            Use apenas as informações fornecidas no contexto abaixo para responder à pergunta.
            Se a informação não estiver no contexto, diga que não tem essa informação específica
            mas tente fornecer orientações gerais baseadas nas diretrizes de produto.
            
            Contexto:
            {context}
            
            Pergunta: {query}
            
            Resposta:
            """
            
            # Importar OpenAI apenas quando necessário
            import openai
            
            # Configurar cliente OpenAI
            client = openai.OpenAI(api_key=openai_api_key)
            
            # Gerar resposta
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em ideação e discovery de produto para a Stone."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extrair e retornar resposta
            answer = response.choices[0].message.content
            
            return {
                "response": answer,
                "documents": [
                    {
                        "filename": doc.properties.get("filename", ""),
                        "content_preview": doc.properties.get("content", "")[:200] + "..." if len(doc.properties.get("content", "")) > 200 else doc.properties.get("content", ""),
                        "distance": doc.metadata.distance
                    } for doc in documents
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return {"response": f"Erro ao gerar resposta: {str(e)}", "documents": []}

def test_rag_agent(weaviate_url, api_key, diretrizes_path, query, openai_api_key=None):
    """
    Testa o agente RAG com uma consulta.
    
    Args:
        weaviate_url (str): URL do endpoint REST Weaviate
        api_key (str): Chave de API para acesso ao Weaviate
        diretrizes_path (str): Caminho para o arquivo de diretrizes
        query (str): Consulta de teste
        openai_api_key (str, optional): Chave de API da OpenAI
    """
    # Inicializar agente
    agent = RAGAgent(weaviate_url, api_key, diretrizes_path)
    
    # Verificar conexão
    if not agent.client:
        logger.error("Falha ao conectar com o Weaviate")
        return
    
    # Verificar diretrizes
    if not agent.diretrizes:
        logger.error("Falha ao carregar diretrizes")
        return
    
    # Testar busca de documentos
    logger.info(f"Testando busca com a consulta: '{query}'")
    documents = agent.search_documents(query)
    
    if not documents:
        logger.warning("Nenhum documento relevante encontrado")
    else:
        logger.info(f"Encontrados {len(documents)} documentos relevantes")
        for i, doc in enumerate(documents):
            logger.info(f"Documento {i+1}: {doc.properties.get('filename', 'Sem nome')}")
            logger.info(f"Distância: {doc.metadata.distance}")
            logger.info(f"Conteúdo (primeiros 100 caracteres): {doc.properties.get('content', 'Sem conteúdo')[:100]}...")
    
    # Testar geração de resposta se a chave da OpenAI for fornecida
    if openai_api_key:
        logger.info("Testando geração de resposta...")
        result = agent.generate_response(query, openai_api_key)
        
        logger.info("Resposta gerada:")
        logger.info(result["response"])
        
        logger.info("Documentos utilizados:")
        for i, doc in enumerate(result["documents"]):
            logger.info(f"Documento {i+1}: {doc['filename']}")
            logger.info(f"Distância: {doc['distance']}")
            logger.info(f"Preview: {doc['content_preview']}")
    
    logger.info("Teste concluído")

if __name__ == "__main__":
    import sys
    import os
    
    # Verificar argumentos
    if len(sys.argv) < 4:
        print("Uso: python rag_integration.py <weaviate_url> <api_key> <diretrizes_path> [<query>] [<openai_api_key>]")
        sys.exit(1)
    
    # Obter argumentos
    weaviate_url = sys.argv[1]
    api_key = sys.argv[2]
    diretrizes_path = sys.argv[3]
    
    # Consulta padrão se não for fornecida
    query = sys.argv[4] if len(sys.argv) > 4 else "Quais são os principais desafios na personalização da Home?"
    
    # Chave da OpenAI do ambiente ou argumento
    openai_api_key = sys.argv[5] if len(sys.argv) > 5 else os.environ.get("OPENAI_API_KEY")
    
    # Testar agente
    test_rag_agent(weaviate_url, api_key, diretrizes_path, query, openai_api_key)
