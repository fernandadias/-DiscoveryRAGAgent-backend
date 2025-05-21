"""
Módulo para integração do classificador de objetivos ao fluxo de processamento de consultas.

Este módulo modifica o endpoint de chat para incluir a classificação automática
de objetivos com base na pergunta do usuário.
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import uuid
import os
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError
import logging
import glob

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
    TokenResponse,
    ObjectiveClassificationResponse
)

from src.rag.rag_integration import RAGIntegration
from src.context.objectives_manager import ObjectivesManager
from src.ingest.document_ingestor import DocumentIngestor
from src.context.objective_classifier import ObjectiveClassifier

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()
rag_integration = RAGIntegration()
objectives_manager = ObjectivesManager()
document_ingestor = DocumentIngestor()
objective_classifier = ObjectiveClassifier()

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

# Função para carregar documentos reais do diretório data/raw
def load_real_documents():
    """Carrega os documentos reais do diretório data/raw para o banco de dados em memória"""
    try:
        raw_dir = "data/raw"
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir, exist_ok=True)
            logger.info(f"Diretório {raw_dir} criado")
            return
        
        # Limpar o banco de dados em memória para evitar duplicatas
        documents_db.clear()
        
        # Listar todos os arquivos no diretório
        file_paths = []
        for ext in ['*.pdf', '*.txt', '*.md', '*.docx']:
            file_paths.extend(glob.glob(os.path.join(raw_dir, ext)))
        
        # Adicionar cada arquivo ao banco de dados em memória
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = os.path.splitext(file_path)[1].lower()
            
            # Mapear extensão para tipo MIME
            mime_types = {
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            
            content_type = mime_types.get(file_type, 'application/octet-stream')
            
            # Gerar ID único para o documento
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path))
            
            # Adicionar ao banco de dados em memória
            documents_db[doc_id] = {
                "id": doc_id,
                "title": file_name,
                "type": content_type,
                "uploaded_at": datetime.fromtimestamp(os.path.getctime(file_path)),
                "size": file_size,
                "path": file_path
            }
        
        logger.info(f"Carregados {len(file_paths)} documentos reais do diretório {raw_dir}")
    except Exception as e:
        logger.error(f"Erro ao carregar documentos reais: {str(e)}")

# Carregar documentos reais ao iniciar
load_real_documents()

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

@router.post("/objectives/classify", response_model=ObjectiveClassificationResponse)
async def classify_objective(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """
    Classifica automaticamente o objetivo de uma pergunta
    """
    try:
        logger.info(f"Classificando objetivo para pergunta: {request.query[:50]}...")
        
        # Classificar a pergunta usando o classificador de objetivos
        objective_type, confidence, scores = objective_classifier.classify_question(request.query)
        
        # Obter o ID do objetivo correspondente
        objective_id = objective_classifier.get_objective_id(objective_type)
        
        # Verificar se a confiança é suficiente para aceitação automática
        auto_accept = objective_classifier.should_accept_automatically(confidence)
        
        # Obter a descrição amigável do objetivo
        objective_description = objective_classifier.get_objective_description(objective_type)
        
        logger.info(f"Pergunta classificada como '{objective_type}' (ID: {objective_id}) com confiança {confidence:.4f}")
        
        return {
            "objective_id": objective_id,
            "objective_type": objective_type,
            "objective_description": objective_description,
            "confidence": confidence,
            "scores": scores,
            "auto_accept": auto_accept
        }
    except Exception as e:
        logger.error(f"Erro ao classificar objetivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=QueryResponse)
async def process_query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """
    Processa uma consulta do usuário e retorna a resposta do agente IA
    """
    try:
        logger.info(f"Processando consulta: {request.query[:50]}...")
        
        # Se não houver objetivo especificado, classificar automaticamente
        objective_id = request.objective_id
        auto_classified = False
        
        if not objective_id:
            try:
                # Classificar a pergunta usando o classificador de objetivos
                objective_type, confidence, _ = objective_classifier.classify_question(request.query)
                
                # Obter o ID do objetivo correspondente
                objective_id = objective_classifier.get_objective_id(objective_type)
                
                # Verificar se a confiança é suficiente para aceitação automática
                auto_accept = objective_classifier.should_accept_automatically(confidence)
                
                if auto_accept:
                    logger.info(f"Objetivo classificado automaticamente: {objective_type} (ID: {objective_id}) com confiança {confidence:.4f}")
                    auto_classified = True
                else:
                    # Se a confiança for baixa, usar o objetivo padrão
                    logger.info(f"Confiança baixa ({confidence:.4f}) para classificação automática, usando objetivo padrão")
                    objective_id = objectives_manager.get_default_objective_id()
            except Exception as e:
                logger.warning(f"Erro na classificação automática de objetivo: {str(e)}")
                # Em caso de erro, usar o objetivo padrão
                objective_id = objectives_manager.get_default_objective_id()
        
        logger.info(f"Processando consulta com objetivo: {objective_id} (auto-classificado: {auto_classified})")
        
        # Processa a consulta usando o módulo RAG
        result = rag_integration.process_query(
            query=request.query,
            objective_id=objective_id
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
        
        # Adicionar informação sobre classificação automática na resposta
        response_text = result["response"]
        if auto_classified:
            objective_description = objective_classifier.get_objective_description(
                objective_classifier.get_objective_from_id(objective_id)
            )
            response_prefix = f"[Objetivo identificado automaticamente: {objective_description}]\n\n"
            response_text = response_prefix + response_text
        
        conversations_db[conversation_id]["messages"].append({
            "content": response_text,
            "isUser": False,
            "timestamp": datetime.now(),
            "sources": sources,
            "objective_id": objective_id,
            "auto_classified": auto_classified
        })
        
        conversations_db[conversation_id]["updated_at"] = datetime.now()
        
        logger.info(f"Consulta processada com sucesso, {len(sources)} fontes encontradas")
        
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "sources": sources,
            "objective_id": objective_id,
            "auto_classified": auto_classified
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

@router.delete("/conversations/{conversation_id}", response_model=APIResponse)
async def delete_conversation(conversation_id: str, current_user: str = Depends(get_current_user)):
    """
    Remove uma conversa do histórico
    """
    if conversation_id not in conversations_db:
        logger.warning(f"Conversa não encontrada: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    try:
        # Remover do banco de dados simulado
        del conversations_db[conversation_id]
        
        logger.info(f"Conversa removida com sucesso: {conversation_id}")
        
        return APIResponse(
            success=True,
            message="Conversa removida com sucesso"
        )
    except Exception as e:
        logger.error(f"Erro ao remover conversa: {str(e)}")
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
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path))
        documents_db[document_id] = {
            "id": document_id,
            "title": file.filename,
            "type": file.content_type,
            "uploaded_at": datetime.now(),
            "size": len(content),
            "path": file_path
        }
        
        # Processar e indexar o documento no Weaviate
        success = document_ingestor.process_and_index_file(file_path)
        
        logger.info(f"Documento enviado e indexado com sucesso: {file.filename} (ID: {document_id})")
        
        return APIResponse(
            success=True,
            message="Documento enviado e indexado com sucesso",
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
        # Recarregar documentos reais para garantir que a lista esteja atualizada
        load_real_documents()
        
        # Ordenar documentos por data de upload (mais recentes primeiro)
        sorted_docs = sorted(
            documents_db.items(),
            key=lambda x: x[1]["uploaded_at"],
            reverse=True
        )
        
        documents = [
            DocumentListItem(
                id=doc_id,
                title=doc["title"],
                type=doc["type"],
                uploaded_at=doc["uploaded_at"],
                size=doc["size"]
            )
            for doc_id, doc in sorted_docs
        ]
        
        logger.info(f"Retornando {len(documents)} documentos")
        return documents
    except Exception as e:
        logger.error(f"Erro ao obter documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}/preview", response_model=dict)
async def get_document_preview(document_id: str, current_user: str = Depends(get_current_user)):
    """
    Retorna uma pré-visualização do conteúdo de um documento
    """
    if document_id not in documents_db:
        logger.warning(f"Documento não encontrado: {document_id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    try:
        document = documents_db[document_id]
        file_path = document["path"]
        
        # Extrair conteúdo do documento (implementação simplificada)
        content = "Conteúdo não disponível para pré-visualização"
        
        if file_path.endswith(".txt") or file_path.endswith(".md"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(2000)  # Limitar a 2000 caracteres
        
        logger.info(f"Retornando pré-visualização do documento: {document_id}")
        
        return {
            "id": document_id,
            "title": document["title"],
            "content": content,
            "type": document["type"]
        }
    except Exception as e:
        logger.error(f"Erro ao obter pré-visualização do documento: {str(e)}")
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
        document = documents_db[document_id]
        file_path = document["path"]
        
        # Remover arquivo físico
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remover do banco de dados simulado
        del documents_db[document_id]
        
        # Remover do índice Weaviate (implementação simplificada)
        try:
            if document_ingestor.client and document_ingestor.client.is_ready():
                document_ingestor.client.data_object.delete(
                    class_name="Document",
                    uuid=document_id
                )
        except Exception as e:
            logger.warning(f"Erro ao remover documento do Weaviate: {str(e)}")
        
        logger.info(f"Documento removido com sucesso: {document_id}")
        
        return APIResponse(
            success=True,
            message="Documento removido com sucesso"
        )
    except Exception as e:
        logger.error(f"Erro ao remover documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
