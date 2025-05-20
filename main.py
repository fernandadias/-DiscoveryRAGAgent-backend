from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.api.routes import router as main_router
from src.api.requirements_routes import router as requirements_router

# Criar a aplicação FastAPI
app = FastAPI(
    title="DiscoveryRAGAgent API",
    description="API REST para o agente de IA especializado em Ideação e Discovery de Produto",
    version="1.0.0"
)

# Configuração de CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir as rotas da API
app.include_router(main_router, prefix="/api")
app.include_router(requirements_router, prefix="/api")

# Rota raiz para verificação de status
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "DiscoveryRAGAgent API está funcionando",
        "docs": "/docs"
    }

# Iniciar o servidor se este arquivo for executado diretamente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
