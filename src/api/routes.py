from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query
from typing import List, Optional
import uuid
import os
from datetime import datetime

from src.api.models import (
    QueryRequest, 
    QueryResponse, 
    ConversationRequest, 
    ConversationListItem,
    ConversationDetail,
    DocumentListItem,
    ObjectiveListItem,
    SourceModel,
    APIResponse
)

from src.rag.rag_integration import RAGIntegration
from src.context.objectives_manager import ObjectivesManager

router = APIRouter()
rag_integration = RAGIntegration()
objectives_manager = ObjectivesManager()

# Simulação de banco de dados em memória para desenvolvimento
conversations_db = {}
documents_db = {}

def generate_uuid():
    """Gera um UUID único para identificadores"""
    return str(uuid.uuid4())

@router.get("/objectives", response_model=List[ObjectiveListItem])
async def get_objectives():
    """
    Retorna a lista de todos os objetivos disponíveis
    """
    try:
        objectives = objectives_manager.get_all_objectives()
        return objectives
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/objectives/default", response_model=str)
async def get_default_objective():
    """
    Retorna o ID do objetivo padrão (Sobre a discovery)
    """
    try:
        default_objective_id = objectives_manager.get_default_objective_id()
        return default_objective_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Processa uma consulta do usuário e retorna a resposta do agente IA
    """
    try:
        # Processa a consulta usando o módulo RAG
        result = rag_integration.process_query(
            query=request.query,
            objective_id=request.objective_id
        )
        
        # Formata a resposta
        sources = [
            SourceModel(
                id=src.get("id", generate_uuid()),
                name=src.get("name", "Fonte desconhecida"),
                snippet=src.get("snippet", "")[:200],
                link=src.get("url")
            ) for src in result.get("sources", [])
        ]
        
        # Gera ou recupera ID da conversa
        conversation_id = request.conversation_id or generate_uuid()
        
        # Salva a conversa no histórico (simulado)
        if conversation_id not in conversations_db:
            conversations_db[conversation_id] = {
                "id": conversation_id,
                "title": f"Conversa {len(conversations_db) + 1}",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "messages": []
            }
        
        # Adiciona mensagens à conversa
        conversations_db[conversation_id]["messages"].append({
            "content": request.query,
            "isUser": True,
            "timestamp": datetime.now()
        })
        
        conversations_db[conversation_id]["messages"].append({
            "content": result["response"],
            "isUser": False,
            "timestamp": datetime.now(),
            "sources": sources
        })
        
        conversations_db[conversation_id]["updated_at"] = datetime.now()
        
        return {
            "response": result["response"],
            "conversation_id": conversation_id,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[ConversationListItem])
async def get_conversations():
    """
    Retorna a lista de todas as conversas salvas
    """
    try:
        return [
            ConversationListItem(
                id=conv_id,
                title=conv["title"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=len(conv["messages"])
            )
            for conv_id, conv in conversations_db.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """
    Retorna os detalhes de uma conversa específica
    """
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    try:
        return ConversationDetail(
            id=conversation_id,
            title=conversations_db[conversation_id]["title"],
            created_at=conversations_db[conversation_id]["created_at"],
            updated_at=conversations_db[conversation_id]["updated_at"],
            messages=conversations_db[conversation_id]["messages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations", response_model=APIResponse)
async def save_conversation(conversation: ConversationRequest):
    """
    Salva uma nova conversa ou atualiza uma existente
    """
    try:
        conversation_id = generate_uuid()
        
        conversations_db[conversation_id] = {
            "id": conversation_id,
            "title": conversation.title,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": conversation.messages
        }
        
        return APIResponse(
            success=True,
            message="Conversa salva com sucesso",
            data={"id": conversation_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload", response_model=APIResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Faz upload de um novo documento para a base de conhecimento
    """
    try:
        # Verificar se o diretório data/raw existe
        raw_dir = "data/raw"
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir, exist_ok=True)
        
        # Salvar o arquivo no diretório data/raw
        file_path = os.path.join(raw_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Registrar o documento no banco de dados simulado
        document_id = generate_uuid()
        documents_db[document_id] = {
            "id": document_id,
            "title": file.filename,
            "type": file.content_type,
            "uploaded_at": datetime.now(),
            "size": len(content),
            "path": file_path
        }
        
        return APIResponse(
            success=True,
            message="Documento enviado com sucesso",
            data={"id": document_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[DocumentListItem])
async def get_documents():
    """
    Retorna a lista de documentos na base de conhecimento
    """
    try:
        return [
            DocumentListItem(
                id=doc_id,
                title=doc["title"],
                type=doc["type"],
                uploaded_at=doc["uploaded_at"],
                size=doc["size"]
            )
            for doc_id, doc in documents_db.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}", response_model=APIResponse)
async def delete_document(document_id: str):
    """
    Remove um documento da base de conhecimento
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    try:
        # Remover o arquivo do sistema de arquivos
        file_path = documents_db[document_id].get("path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Remover do banco de dados simulado
        del documents_db[document_id]
        
        return APIResponse(
            success=True,
            message="Documento removido com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/reindex", response_model=APIResponse)
async def reindex_documents():
    """
    Trigger manual para reindexar todos os documentos
    """
    try:
        # Em uma implementação real, aqui seria chamado o processo de ingestão
        # para reindexar todos os documentos na pasta data/raw
        
        # Simulação para desenvolvimento
        return APIResponse(
            success=True,
            message="Reindexação de documentos iniciada com sucesso",
            data={"status": "processing"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
