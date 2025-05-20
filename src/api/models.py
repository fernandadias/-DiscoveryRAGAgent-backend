from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    """Modelo para requisição de consulta ao agente IA"""
    query: str
    conversation_id: Optional[str] = None

class MessageModel(BaseModel):
    """Modelo para mensagens individuais"""
    content: str
    isUser: bool
    timestamp: datetime

class ConversationRequest(BaseModel):
    """Modelo para salvar uma conversa"""
    title: str
    messages: List[MessageModel]

class SourceModel(BaseModel):
    """Modelo para fontes de informação usadas na resposta"""
    id: str
    name: str
    snippet: str
    link: Optional[str] = None

class QueryResponse(BaseModel):
    """Modelo para resposta de consulta ao agente IA"""
    response: str
    conversation_id: str
    sources: List[SourceModel]

class ConversationListItem(BaseModel):
    """Modelo para item na lista de conversas"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class ConversationDetail(BaseModel):
    """Modelo para detalhes de uma conversa"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]]

class DocumentListItem(BaseModel):
    """Modelo para item na lista de documentos"""
    id: str
    title: str
    type: str
    uploaded_at: datetime
    size: int

class APIResponse(BaseModel):
    """Modelo para respostas genéricas da API"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
