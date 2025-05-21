"""
Módulo principal para inicialização da aplicação

Este módulo configura e inicializa a aplicação FastAPI.
"""

import os
import sys
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar rotas
from src.api.routes import router as api_router
from src.api.requirements_routes import router as requirements_router

# Criar aplicação FastAPI
app = FastAPI(
    title="DiscoveryRAGAgent API",
    description="API para o agente RAG de Discovery",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos
    allow_headers=["*"],  # Permitir todos os cabeçalhos
)

# Incluir rotas
app.include_router(api_router, prefix="/api")
app.include_router(requirements_router, prefix="/api")

# Rota de verificação de saúde
@app.get("/health")
async def health_check():
    """
    Verifica a saúde da aplicação.
    """
    return {"status": "ok", "message": "API está funcionando corretamente"}

# Manipulador de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Manipulador global de exceções.
    """
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Erro interno do servidor: {str(exc)}"}
    )

# Verificar variáveis de ambiente necessárias
required_env_vars = ["OPENAI_API_KEY", "WEAVIATE_URL"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

if missing_vars:
    logger.warning(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
    logger.warning("A aplicação pode não funcionar corretamente sem estas variáveis.")

# Inicialização da aplicação
logger.info("Aplicação inicializada com sucesso")
