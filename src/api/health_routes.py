"""
Módulo para endpoints de health check e diagnóstico do sistema.

Este módulo implementa endpoints robustos para verificação de saúde
e diagnóstico do sistema, permitindo monitoramento detalhado em produção.
"""
import os
import sys
import time
import logging
import platform
import psutil
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(tags=["health"])

class HealthStatus(BaseModel):
    """Modelo para resposta de status de saúde"""
    status: str
    version: str
    timestamp: float
    uptime: float
    environment: str
    python_version: str
    components: Dict[str, Dict[str, Any]]
    dependencies: Dict[str, str]
    memory_usage: Dict[str, Any]

class ComponentStatus(BaseModel):
    """Modelo para status de componente individual"""
    name: str
    status: str
    details: Dict[str, Any]

# Variáveis globais
start_time = time.time()
app_version = "1.0.0"

def get_memory_usage() -> Dict[str, Any]:
    """
    Obtém informações sobre uso de memória do processo.
    
    Returns:
        Dicionário com informações de uso de memória
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size em MB
        "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size em MB
        "percent": process.memory_percent(),
        "cpu_percent": process.cpu_percent(interval=0.1)
    }

def check_openai_status() -> Dict[str, Any]:
    """
    Verifica o status da integração com OpenAI.
    
    Returns:
        Dicionário com status da integração
    """
    from src.utils.openai_safe import create_safe_openai_client
    
    status = "ok"
    details = {"message": "OpenAI API disponível"}
    
    try:
        # Verificar se a chave da API está configurada
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            status = "warning"
            details = {"message": "Chave da API OpenAI não configurada"}
        else:
            # Tentar criar cliente (sem fazer chamadas reais à API)
            client = create_safe_openai_client()
            details["client_initialized"] = True
    except Exception as e:
        status = "error"
        details = {
            "message": "Erro ao inicializar cliente OpenAI",
            "error": str(e)
        }
    
    return {
        "status": status,
        "details": details
    }

def check_weaviate_status() -> Dict[str, Any]:
    """
    Verifica o status da integração com Weaviate.
    
    Returns:
        Dicionário com status da integração
    """
    status = "ok"
    details = {"message": "Weaviate disponível"}
    
    try:
        # Verificar se a URL do Weaviate está configurada
        weaviate_url = os.environ.get("WEAVIATE_URL")
        if not weaviate_url:
            status = "warning"
            details = {"message": "URL do Weaviate não configurada"}
        else:
            # Não fazer chamada real ao Weaviate para evitar sobrecarga
            details["url_configured"] = True
    except Exception as e:
        status = "error"
        details = {
            "message": "Erro ao verificar configuração do Weaviate",
            "error": str(e)
        }
    
    return {
        "status": status,
        "details": details
    }

def check_objective_classifier_status() -> Dict[str, Any]:
    """
    Verifica o status do classificador de objetivos.
    
    Returns:
        Dicionário com status do classificador
    """
    from src.context.objective_classifier import ObjectiveClassifier
    
    status = "ok"
    details = {"message": "Classificador de objetivos disponível"}
    
    try:
        # Tentar inicializar o classificador
        classifier = ObjectiveClassifier(use_fallback=True)
        
        # Verificar se o cliente OpenAI está disponível
        if classifier.client:
            details["openai_client"] = "disponível"
            details["using_embeddings"] = True
        else:
            status = "warning"
            details["openai_client"] = "indisponível"
            details["using_embeddings"] = False
            details["message"] = "Usando classificador local de fallback"
        
        # Testar classificação com uma pergunta de exemplo
        test_question = "Quais são os principais problemas que os usuários enfrentam com a home do app?"
        objective, confidence, scores = classifier.classify_question(test_question)
        
        details["test_classification"] = {
            "question": test_question,
            "objective": objective,
            "confidence": confidence,
            "scores": scores
        }
    except Exception as e:
        status = "error"
        details = {
            "message": "Erro ao inicializar classificador de objetivos",
            "error": str(e)
        }
    
    return {
        "status": status,
        "details": details
    }

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Endpoint para verificação detalhada de saúde do sistema.
    
    Returns:
        Objeto HealthStatus com informações detalhadas sobre o estado do sistema
    """
    # Verificar componentes principais
    components = {
        "openai": check_openai_status(),
        "weaviate": check_weaviate_status(),
        "objective_classifier": check_objective_classifier_status()
    }
    
    # Determinar status geral com base nos componentes
    overall_status = "ok"
    for component in components.values():
        if component["status"] == "error":
            overall_status = "error"
            break
        elif component["status"] == "warning" and overall_status != "error":
            overall_status = "warning"
    
    # Obter informações sobre dependências
    dependencies = {
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "fastapi": "0.104.1",  # Hardcoded para evitar import circular
        "openai": "1.81.0"      # Hardcoded para evitar import circular
    }
    
    # Obter ambiente de execução
    environment = os.environ.get("ENVIRONMENT", "production")
    
    # Construir resposta
    response = HealthStatus(
        status=overall_status,
        version=app_version,
        timestamp=time.time(),
        uptime=time.time() - start_time,
        environment=environment,
        python_version=platform.python_version(),
        components=components,
        dependencies=dependencies,
        memory_usage=get_memory_usage()
    )
    
    # Registrar verificação de saúde
    logger.info(f"Health check: status={overall_status}, components={len(components)}")
    
    return response

@router.get("/health/simple")
async def simple_health_check():
    """
    Endpoint simplificado para verificação de saúde do sistema.
    Útil para health checks de infraestrutura que não precisam de detalhes.
    
    Returns:
        Dicionário simples com status
    """
    return {"status": "ok", "message": "API está funcionando"}

@router.get("/health/objective-classifier")
async def objective_classifier_health():
    """
    Endpoint específico para verificar o status do classificador de objetivos.
    
    Returns:
        Dicionário com status detalhado do classificador
    """
    status = check_objective_classifier_status()
    
    # Se o status for erro, retornar código 500
    if status["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status["details"]
        )
    
    return status
