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
    SourceModel,
    APIResponse
)

# Importações simuladas dos módulos existentes
# Em uma implementação real, estas seriam importações reais dos módulos do DiscoveryRAGAgent
try:
    from src.rag.rag_integration import process_query as rag_process_query
except ImportError:
    # Função simulada para desenvolvimento
    def rag_process_query(query: str):
        return {
            "response": f"Resposta simulada para: {query}",
            "sources": [
                {
                    "id": "doc1",
                    "title": "Documento de Exemplo 1",
                    "content": "Este é um conteúdo de exemplo que seria retornado pelo sistema RAG.",
                    "url": None
                }
            ]
        }

router = APIRouter()

# Simulação de banco de dados em memória para desenvolvimento
conversations_db = {}
documents_db = {}

def generate_uuid():
    """Gera um UUID único para identificadores"""
    return str(uuid.uuid4())

@router.post("/chat", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Processa uma consulta do usuário e retorna a resposta do agente IA
    """
    try:
        # Processa a consulta usando o módulo RAG existente
        result = rag_process_query(request.query)
        
        # Formata a resposta
        sources = [
            SourceModel(
                id=src.get("id", generate_uuid()),
                name=src.get("title", "Fonte desconhecida"),
                snippet=src.get("content", "")[:200],
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
            "messages": [
                {
                    "content": msg.content,
                    "isUser": msg.isUser,
                    "timestamp": msg.timestamp
                }
                for msg in conversation.messages
            ]
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
        # Simulação de processamento de documento
        document_id = generate_uuid()
        
        # Em uma implementação real, aqui seria feito o processamento do documento
        # usando os módulos existentes de ingestão de dados
        
        documents_db[document_id] = {
            "id": document_id,
            "title": file.filename,
            "type": file.content_type,
            "uploaded_at": datetime.now(),
            "size": 0  # Em uma implementação real, seria o tamanho real do arquivo
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
        # Em uma implementação real, aqui seria feita a remoção do documento
        # da base de conhecimento e do sistema de arquivos
        
        del documents_db[document_id]
        
        return APIResponse(
            success=True,
            message="Documento removido com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
