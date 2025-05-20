from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any
import os
import jwt
from jwt.exceptions import PyJWTError

from src.context.objectives_manager import ObjectivesManager
from src.context.guidelines_manager import GuidelinesManager

router = APIRouter()
objectives_manager = ObjectivesManager()
guidelines_manager = GuidelinesManager()

# Configuração de segurança
security = HTTPBearer()
SECRET_KEY = "discovery_rag_agent_secret_key"  # Em produção, usar variável de ambiente
ALGORITHM = "HS256"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifica o token JWT e retorna o usuário atual"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    return username

@router.get("/objectives/content", response_model=List[Dict[str, Any]])
async def get_objectives_content(current_user: str = Depends(get_current_user)):
    """
    Retorna o conteúdo completo de todos os objetivos
    """
    try:
        objectives = []
        for obj in objectives_manager.get_all_objectives():
            obj_id = obj["id"]
            content = objectives_manager.get_objective_content(obj_id)
            objectives.append({
                "id": obj_id,
                "title": obj["title"],
                "content": content
            })
        return objectives
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guidelines/content", response_model=List[Dict[str, Any]])
async def get_guidelines_content(current_user: str = Depends(get_current_user)):
    """
    Retorna o conteúdo completo de todas as diretrizes
    """
    try:
        guidelines = guidelines_manager.get_all_guidelines()
        if not guidelines:
            # Caso não encontre diretrizes, tentar recarregar
            guidelines_manager.load_guidelines()
            guidelines = guidelines_manager.get_all_guidelines()
            
        return guidelines
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", response_model=Dict[str, Any])
async def submit_feedback(feedback: Dict[str, Any], current_user: str = Depends(get_current_user)):
    """
    Recebe e armazena feedback do usuário sobre respostas
    """
    try:
        # Em uma implementação real, armazenar o feedback em um banco de dados
        # Por enquanto, apenas registrar no console e em um arquivo de log
        
        feedback_dir = "data/feedback"
        os.makedirs(feedback_dir, exist_ok=True)
        
        feedback_file = os.path.join(feedback_dir, "feedback_log.txt")
        with open(feedback_file, "a") as f:
            f.write(f"Message ID: {feedback.get('message_id')}\n")
            f.write(f"Reasons: {', '.join(feedback.get('reasons', []))}\n")
            f.write(f"Details: {feedback.get('details', '')}\n")
            f.write("-" * 50 + "\n")
        
        return {"success": True, "message": "Feedback recebido com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
