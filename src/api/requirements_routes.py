from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os

from src.context.objectives_manager import ObjectivesManager
from src.context.guidelines_manager import GuidelinesManager

router = APIRouter()
objectives_manager = ObjectivesManager()
guidelines_manager = GuidelinesManager()

@router.get("/objectives/content", response_model=List[Dict[str, Any]])
async def get_objectives_content():
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
async def get_guidelines_content():
    """
    Retorna o conteúdo completo de todas as diretrizes
    """
    try:
        return guidelines_manager.get_all_guidelines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", response_model=Dict[str, Any])
async def submit_feedback(feedback: Dict[str, Any]):
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
