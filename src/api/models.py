from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    objective_id: Optional[str] = None

class SourceModel(BaseModel):
    id: str
    name: str
    snippet: str
    link: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    conversation_id: str
    sources: List[SourceModel]

class ConversationRequest(BaseModel):
    title: str
    messages: List[Any]

class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Any]

class DocumentListItem(BaseModel):
    id: str
    title: str
    type: str
    uploaded_at: datetime
    size: int

class ObjectiveListItem(BaseModel):
    id: str
    title: str

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
