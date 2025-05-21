import os
import logging
import weaviate
from weaviate.auth import AuthApiKey
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_weaviate_chunks():
    """
    Script para validar os chunks indexados no Weaviate e testar buscas
    """
    try:
        # Configurar cliente Weaviate
        weaviate_url = os.getenv("WEAVIATE_URL", "xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s")
        
        # Garantir que a URL tenha o prefixo https://
        if not weaviate_url.startswith("http://") and not weaviate_url.startswith("https://"):
            weaviate_url = f"https://{weaviate_url}"
        
        # Criar conexão usando a API v3 com autenticação correta
        auth_config = None
        if weaviate_api_key:
            auth_config = AuthApiKey(api_key=weaviate_api_key)
            
        client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=auth_config
        )
        
        # Verificar se o cliente está conectado
        if not client.is_ready():
            logger.error("Não foi possível conectar ao Weaviate")
            return False
        
        # Verificar schema
        schema = client.schema.get()
        document_class = None
        for class_obj in schema.get("classes", []):
            if class_obj.get("class") == "Document":
                document_class = class_obj
                break
        
        if not document_class:
            logger.error("Classe Document não encontrada no schema")
            return False
        
        # Verificar o vectorizer atual
        current_vectorizer = document_class.get("vectorizer")
        logger.info(f"Vectorizer atual: {current_vectorizer}")
        
        # Contar documentos indexados
        try:
            count_result = client.query.aggregate("Document").with_meta_count().do()
            doc_count = count_result.get("data", {}).get("Aggregate", {}).get("Document", [{}])[0].get("meta", {}).get("count")
            logger.info(f"Total de documentos indexados: {doc_count}")
        except Exception as e:
            logger.error(f"Erro ao contar documentos: {str(e)}")
            doc_count = "desconhecido"
        
        # Testar busca por palavras-chave
        logger.info("Testando busca por palavras-chave...")
        
        # Lista de consultas de teste
        test_queries = [
            "perfis de usuários",
            "objetivos da discovery",
            "necessidades dos clientes",
            "home do aplicativo",
            "stone e ton"
        ]
        
        results = {}
        
        for query in test_queries:
            logger.info(f"Testando consulta: '{query}'")
            
            try:
                # Busca por palavras-chave (where filter)
                where_filter = {
                    "operator": "Or",
                    "operands": [
                        {
                            "path": ["content"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        },
                        {
                            "path": ["title"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        }
                    ]
                }
                
                where_results = client.query.get(
                    "Document", 
                    ["content", "title", "file_name"]
                ).with_where(where_filter).with_limit(5).do()
                
                docs = where_results.get("data", {}).get("Get", {}).get("Document", [])
                
                results[query] = {
                    "count": len(docs),
                    "titles": [doc.get("title") for doc in docs[:3]]
                }
                
                logger.info(f"Consulta '{query}' retornou {len(docs)} documentos")
                for i, doc in enumerate(docs[:3]):
                    logger.info(f"  {i+1}. {doc.get('title')}")
                    
            except Exception as e:
                logger.error(f"Erro na consulta '{query}': {str(e)}")
                results[query] = {"error": str(e)}
        
        # Salvar resultados em um arquivo
        results_file = "weaviate_validation_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": str(datetime.now()),
                "vectorizer": current_vectorizer,
                "document_count": doc_count,
                "test_queries": results
            }, f, indent=2)
        
        logger.info(f"Resultados salvos em: {results_file}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao validar chunks do Weaviate: {str(e)}")
        return False

if __name__ == "__main__":
    from datetime import datetime
    validate_weaviate_chunks()
