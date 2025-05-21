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

def test_weaviate_query():
    """
    Testa consultas diretas no Weaviate para verificar a recuperação de informações sobre perfis de usuários
    """
    # Configurar cliente Weaviate
    weaviate_url = os.getenv("WEAVIATE_URL", "https://xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s")
    
    # Criar conexão com autenticação
    auth_config = None
    if weaviate_api_key:
        auth_config = AuthApiKey(api_key=weaviate_api_key)
        
    client = weaviate.Client(
        url=weaviate_url,
        auth_client_secret=auth_config
    )
    
    # Verificar se o cliente está pronto
    try:
        is_ready = client.is_ready()
        logger.info(f"Weaviate está pronto: {is_ready}")
        if not is_ready:
            logger.error("Weaviate não está pronto. Verifique a conexão.")
            return
    except Exception as e:
        logger.error(f"Erro ao verificar status do Weaviate: {str(e)}")
        return
    
    # Testar consulta sobre perfis de usuários
    logger.info("Testando consulta sobre perfis de usuários...")
    
    # Consulta 1: Perfis de usuários (básica)
    query1 = "perfis de usuários"
    try:
        result1 = client.query.get(
            "Document", 
            ["content", "title", "metadata"]
        ).with_near_text({
            "concepts": [query1]
        }).with_limit(5).do()
        
        # Verificar se a resposta contém documentos
        docs1 = result1.get("data", {}).get("Get", {}).get("Document", [])
        if docs1 is None:
            docs1 = []
            logger.warning("Consulta 1 retornou None para documentos")
    except Exception as e:
        logger.error(f"Erro na consulta 1: {str(e)}")
        docs1 = []
    
    # Consulta 2: Perfis de usuários conhecidos (específica)
    query2 = "quais os perfis de usuários que conhecemos"
    try:
        result2 = client.query.get(
            "Document", 
            ["content", "title", "metadata"]
        ).with_near_text({
            "concepts": [query2]
        }).with_limit(5).do()
        
        # Verificar se a resposta contém documentos
        docs2 = result2.get("data", {}).get("Get", {}).get("Document", [])
        if docs2 is None:
            docs2 = []
            logger.warning("Consulta 2 retornou None para documentos")
    except Exception as e:
        logger.error(f"Erro na consulta 2: {str(e)}")
        docs2 = []
    
    # Consulta 3: Usando expansão semântica
    query3 = "perfis usuários personas segmentação público-alvo características comportamento necessidades"
    try:
        result3 = client.query.get(
            "Document", 
            ["content", "title", "metadata"]
        ).with_near_text({
            "concepts": [query3]
        }).with_limit(5).do()
        
        # Verificar se a resposta contém documentos
        docs3 = result3.get("data", {}).get("Get", {}).get("Document", [])
        if docs3 is None:
            docs3 = []
            logger.warning("Consulta 3 retornou None para documentos")
    except Exception as e:
        logger.error(f"Erro na consulta 3: {str(e)}")
        docs3 = []
    
    # Consulta 4: Busca por contexto semântico (se disponível)
    try:
        result4 = client.query.get(
            "Document", 
            ["content", "title", "metadata"]
        ).with_where({
            "path": ["semantic_context"],
            "operator": "Like",
            "valueText": "*perfis_usuarios*"
        }).with_limit(5).do()
        
        # Verificar se a resposta contém documentos
        docs4 = result4.get("data", {}).get("Get", {}).get("Document", [])
        if docs4 is None:
            docs4 = []
            logger.warning("Consulta 4 retornou None para documentos")
    except Exception as e:
        logger.error(f"Erro na consulta 4: {str(e)}")
        docs4 = []
    
    # Processar e exibir resultados
    logger.info(f"Consulta 1 (básica): {len(docs1)} documentos encontrados")
    logger.info(f"Consulta 2 (específica): {len(docs2)} documentos encontrados")
    logger.info(f"Consulta 3 (expandida): {len(docs3)} documentos encontrados")
    logger.info(f"Consulta 4 (contexto semântico): {len(docs4)} documentos encontrados")
    
    # Verificar se há documentos no Weaviate
    try:
        count_result = client.query.aggregate("Document").with_meta_count().do()
        total_docs = count_result.get("data", {}).get("Aggregate", {}).get("Document", [{}])[0].get("meta", {}).get("count", 0)
        logger.info(f"Total de documentos no Weaviate: {total_docs}")
        
        if total_docs == 0:
            logger.warning("Não há documentos indexados no Weaviate!")
    except Exception as e:
        logger.error(f"Erro ao contar documentos: {str(e)}")
    
    # Salvar resultados em arquivo para análise
    results = {
        "consulta_basica": {
            "query": query1,
            "documentos": [{"title": doc.get("title", ""), "snippet": doc.get("content", "")[:200] if doc.get("content") else ""} for doc in docs1]
        },
        "consulta_especifica": {
            "query": query2,
            "documentos": [{"title": doc.get("title", ""), "snippet": doc.get("content", "")[:200] if doc.get("content") else ""} for doc in docs2]
        },
        "consulta_expandida": {
            "query": query3,
            "documentos": [{"title": doc.get("title", ""), "snippet": doc.get("content", "")[:200] if doc.get("content") else ""} for doc in docs3]
        },
        "consulta_contexto_semantico": {
            "documentos": [{"title": doc.get("title", ""), "snippet": doc.get("content", "")[:200] if doc.get("content") else ""} for doc in docs4]
        }
    }
    
    # Salvar resultados em arquivo JSON
    with open("weaviate_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("Resultados salvos em weaviate_test_results.json")
    
    # Analisar resultados para verificar se há informações sobre perfis
    has_profile_info = False
    profile_terms = ["perfil", "perfis", "usuário", "usuários", "cliente", "clientes", "persona", "personas"]
    
    for docs in [docs1, docs2, docs3, docs4]:
        for doc in docs:
            content = doc.get("content", "").lower() if doc.get("content") else ""
            if any(term in content for term in profile_terms):
                has_profile_info = True
                break
        if has_profile_info:
            break
    
    if has_profile_info:
        logger.info("✅ Informações sobre perfis de usuários encontradas nos documentos recuperados")
    else:
        logger.warning("❌ Não foram encontradas informações sobre perfis de usuários nos documentos recuperados")
    
    # Retornar resumo dos resultados
    return {
        "consulta_basica": len(docs1),
        "consulta_especifica": len(docs2),
        "consulta_expandida": len(docs3),
        "consulta_contexto_semantico": len(docs4),
        "has_profile_info": has_profile_info
    }

if __name__ == "__main__":
    test_weaviate_query()
