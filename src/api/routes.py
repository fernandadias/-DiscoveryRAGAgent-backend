from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import uuid
import os
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError
import logging

from src.api.models import (
    QueryRequest, 
    QueryResponse, 
    ConversationRequest, 
    ConversationListItem,
    ConversationDetail,
    DocumentListItem,
    ObjectiveListItem,
    SourceModel,
    APIResponse,
    LoginRequest,
    TokenResponse
)

from src.rag.rag_integration import RAGIntegration
from src.context.objectives_manager import ObjectivesManager

# Configuração de logging
logger = logging.getLogger(__name__)

router = APIRouter()
rag_integration = RAGIntegration()
objectives_manager = ObjectivesManager()

# Configuração de segurança
security = HTTPBearer()
SECRET_KEY = "discovery_rag_agent_secret_key"  # Em produção, usar variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Credenciais hardcoded
VALID_CREDENTIALS = {
    "Mario": "Bros"
}

# Simulação de banco de dados em memória para desenvolvimento
conversations_db = {}
documents_db = {}

# Inicializar alguns documentos de exemplo para garantir que a tela não fique vazia
def initialize_sample_documents():
    if not documents_db:
        sample_docs = [
            {
                "id": "doc1",
                "title": "Guia de Discovery de Produto.pdf",
                "type": "application/pdf",
                "uploaded_at": datetime.now(),
                "size": 1024 * 500,  # 500 KB
                "path": "data/raw/guia_discovery.pdf"
            },
            {
                "id": "doc2",
                "title": "Framework de Pesquisa.docx",
                "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "uploaded_at": datetime.now(),
                "size": 1024 * 350,  # 350 KB
                "path": "data/raw/framework_pesquisa.docx"
            },
            {
                "id": "doc3",
                "title": "Metodologia de Entrevistas.md",
                "type": "text/markdown",
                "uploaded_at": datetime.now(),
                "size": 1024 * 120,  # 120 KB
                "path": "data/raw/metodologia_entrevistas.md"
            }
        ]
        
        for doc in sample_docs:
            documents_db[doc["id"]] = doc
        
        logger.info(f"Inicializados {len(sample_docs)} documentos de exemplo")

# Inicializar documentos de exemplo
initialize_sample_documents()

def generate_uuid():
    """Gera um UUID único para identificadores"""
    return str(uuid.uuid4())

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Cria um token JWT de acesso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Endpoint de login com credenciais hardcoded
    """
    logger.info(f"Tentativa de login para usuário: {request.username}")
    
    # Verificar se as credenciais são válidas
    if request.username not in VALID_CREDENTIALS or VALID_CREDENTIALS[request.username] != request.password:
        logger.warning(f"Falha no login para usuário: {request.username}")
        raise HTTPException(
            status_code=401,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Criar token de acesso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"Login bem-sucedido para usuário: {request.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/objectives", response_model=List[ObjectiveListItem])
async def get_objectives(current_user: str = Depends(get_current_user)):
    """
    Retorna a lista de todos os objetivos disponíveis
    """
    try:
        objectives = objectives_manager.get_all_objectives()
        logger.info(f"Retornando {len(objectives)} objetivos")
        return objectives
    except Exception as e:
        logger.error(f"Erro ao obter objetivos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/objectives/default", response_model=str)
async def get_default_objective(current_user: str = Depends(get_current_user)):
    """
    Retorna o ID do objetivo padrão (Sobre a discovery)
    """
    try:
        default_objective_id = objectives_manager.get_default_objective_id()
        logger.info(f"Retornando objetivo padrão: {default_objective_id}")
        return default_objective_id
    except Exception as e:
        logger.error(f"Erro ao obter objetivo padrão: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=QueryResponse)
async def process_query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """
    Processa uma consulta do usuário e retorna a resposta do agente IA
    """
    try:
        logger.info(f"Processando consulta: {request.query[:50]}... (objetivo: {request.objective_id})")
        
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
        
        logger.info(f"Consulta processada com sucesso, {len(sources)} fontes encontradas")
        
        return {
            "response": result["response"],
            "conversation_id": conversation_id,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[ConversationListItem])
async def get_conversations(current_user: str = Depends(get_current_user)):
    """
    Retorna a lista de todas as conversas salvas
    """
    try:
        conversations = [
            ConversationListItem(
                id=conv_id,
                title=conv["title"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=len(conv["messages"])
            )
            for conv_id, conv in conversations_db.items()
        ]
        logger.info(f"Retornando {len(conversations)} conversas")
        return conversations
    except Exception as e:
        logger.error(f"Erro ao obter conversas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, current_user: str = Depends(get_current_user)):
    """
    Retorna os detalhes de uma conversa específica
    """
    if conversation_id not in conversations_db:
        logger.warning(f"Conversa não encontrada: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    try:
        logger.info(f"Retornando detalhes da conversa: {conversation_id}")
        return ConversationDetail(
            id=conversation_id,
            title=conversations_db[conversation_id]["title"],
            created_at=conversations_db[conversation_id]["created_at"],
            updated_at=conversations_db[conversation_id]["updated_at"],
            messages=conversations_db[conversation_id]["messages"]
        )
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da conversa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations", response_model=APIResponse)
async def save_conversation(conversation: ConversationRequest, current_user: str = Depends(get_current_user)):
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
        
        logger.info(f"Conversa salva com sucesso: {conversation_id}")
        
        return APIResponse(
            success=True,
            message="Conversa salva com sucesso",
            data={"id": conversation_id}
        )
    except Exception as e:
        logger.error(f"Erro ao salvar conversa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload", response_model=APIResponse)
async def upload_document(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
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
        
        logger.info(f"Documento enviado com sucesso: {file.filename} (ID: {document_id})")
        
        return APIResponse(
            success=True,
            message="Documento enviado com sucesso",
            data={"id": document_id}
        )
    except Exception as e:
        logger.error(f"Erro ao enviar documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[DocumentListItem])
async def get_documents(current_user: str = Depends(get_current_user)):
    """
    Retorna a lista de documentos na base de conhecimento
    """
    try:
        documents = [
            DocumentListItem(
                id=doc_id,
                title=doc["title"],
                type=doc["type"],
                uploaded_at=doc["uploaded_at"],
                size=doc["size"]
            )
            for doc_id, doc in documents_db.items()
        ]
        logger.info(f"Retornando {len(documents)} documentos")
        return documents
    except Exception as e:
        logger.error(f"Erro ao obter documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}", response_model=APIResponse)
async def delete_document(document_id: str, current_user: str = Depends(get_current_user)):
    """
    Remove um documento da base de conhecimento
    """
    if document_id not in documents_db:
        logger.warning(f"Documento não encontrado: {document_id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    try:
        # Remover o arquivo do sistema de arquivos
        file_path = documents_db[document_id].get("path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Remover do banco de dados simulado
        del documents_db[document_id]
        
        logger.info(f"Documento removido com sucesso: {document_id}")
        
        return APIResponse(
            success=True,
            message="Documento removido com sucesso"
        )
    except Exception as e:
        logger.error(f"Erro ao remover documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/reindex", response_model=APIResponse)
async def reindex_documents(current_user: str = Depends(get_current_user)):
    """
    Trigger manual para reindexar todos os documentos
    """
    try:
        # Em uma implementação real, aqui seria chamado o processo de ingestão
        # para reindexar todos os documentos na pasta data/raw
        
        logger.info("Reindexação de documentos iniciada")
        
        # Simulação para desenvolvimento
        return APIResponse(
            success=True,
            message="Reindexação de documentos iniciada com sucesso",
            data={"status": "processing"}
        )
    except Exception as e:
        logger.error(f"Erro ao reindexar documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
