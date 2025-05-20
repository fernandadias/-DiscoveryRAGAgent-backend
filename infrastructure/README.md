# Configuração de Infraestrutura do DiscoveryRAGAgent

Este documento contém as informações reais de infraestrutura utilizadas no projeto DiscoveryRAGAgent.

## Variáveis de Ambiente

As seguintes variáveis de ambiente são necessárias para o funcionamento do sistema:

```bash
# Weaviate (Base Vetorial)
WEAVIATE_URL=https://xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud
WEAVIATE_API_KEY=8ohYdBTciU1n6zTwA15nnsZYAA1I4S1nI17s

# OpenAI (LLM e Embeddings)
OPENAI_API_KEY=sua_chave_api_openai

# Configurações do Servidor
PORT=8000
HOST=0.0.0.0

# Autenticação
JWT_SECRET_KEY=discovery_rag_agent_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440  # 24 horas
```

## Serviços Utilizados

### Weaviate Cloud

- **Instância**: discoveryragagent-backend
- **REST Endpoint**: xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud
- **gRPC Endpoint**: grpc-xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud
- **Região**: us-west3 (GCP)
- **Modelo de Embeddings**: OpenAI (text-embedding-ada-002)
- **Plano Recomendado**: Starter ($7/mês) para evitar limitações do plano gratuito

### Render (Backend)

- **Tipo**: Web Service
- **Plano**: Starter ($7/mês) - Recomendado para evitar cold starts
- **Região**: Oregon (US West)
- **Branch**: main
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Vercel (Frontend)

- **Framework**: React + Vite
- **Região**: Auto (CDN Global)
- **Branch**: main
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Variáveis de Ambiente**: `VITE_API_URL=https://discoveryragagent-backend.onrender.com`

## Autenticação

O sistema utiliza autenticação JWT (JSON Web Token) com as seguintes credenciais hardcoded:

- **Usuário**: Mario
- **Senha**: Bros

Todas as rotas da API estão protegidas e requerem um token de acesso válido, que pode ser obtido através do endpoint `/api/login`.

## Estrutura de Arquivos

```
backend/
├── data/
│   ├── raw/                # Documentos PDF para ingestão
│   ├── processed/          # Documentos processados
│   ├── objectives/         # Arquivos MD de objetivos
│   ├── guidelines/         # Arquivos MD de diretrizes
│   └── feedback/           # Logs de feedback dos usuários
├── src/
│   ├── api/                # Rotas e modelos da API
│   ├── context/            # Gerenciadores de objetivos e diretrizes
│   ├── ingest/             # Pipeline de ingestão
│   ├── rag/                # Integração RAG
│   └── ui/                 # Utilitários de interface
├── infrastructure/         # Configurações de infraestrutura
└── main.py                 # Ponto de entrada da aplicação
```

## Configuração do Weaviate

O schema do Weaviate está configurado com a seguinte estrutura:

```json
{
  "class": "Document",
  "description": "Documentos para o DiscoveryRAGAgent",
  "vectorizer": "text2vec-openai",
  "moduleConfig": {
    "text2vec-openai": {
      "model": "ada",
      "modelVersion": "002",
      "type": "text"
    }
  },
  "properties": [
    {
      "name": "title",
      "description": "Título do documento",
      "dataType": ["text"]
    },
    {
      "name": "content",
      "description": "Conteúdo do documento",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": false,
          "vectorizePropertyName": false
        }
      }
    },
    {
      "name": "metadata",
      "description": "Metadados do documento",
      "dataType": ["text"]
    },
    {
      "name": "tipo",
      "description": "Tipo de documento",
      "dataType": ["text"]
    },
    {
      "name": "filename",
      "description": "Nome do arquivo original",
      "dataType": ["text"]
    },
    {
      "name": "file_path",
      "description": "Caminho do arquivo original",
      "dataType": ["text"]
    }
  ]
}
```

## Configuração do OpenAI

- **Modelo para Geração de Texto**: gpt-4o
- **Modelo para Embeddings**: text-embedding-ada-002
- **Temperatura**: 0.7
- **Max Tokens**: 1500
- **Versão da API**: 1.0.0+ (nova interface do cliente)

## Dependências Principais

- **FastAPI**: Framework web para API REST
- **Uvicorn**: Servidor ASGI para FastAPI
- **Weaviate Client**: v3.x (compatível com a API v3)
- **OpenAI**: v1.12.0+ (nova API)
- **PyJWT**: Para autenticação JWT
- **Python-Multipart**: Para upload de arquivos
- **Markdown**: Para processamento de arquivos MD

## Instruções de Deploy

### Backend (Render)

1. Faça login no Render Dashboard
2. Conecte o repositório GitHub
3. Configure as variáveis de ambiente listadas acima
4. Clique em "Deploy"

### Frontend (Vercel)

1. Faça login no Vercel Dashboard
2. Conecte o repositório GitHub
3. Configure a variável de ambiente `VITE_API_URL` apontando para o backend
4. Clique em "Deploy"

## Monitoramento e Logging

O sistema utiliza logging estruturado para facilitar o diagnóstico de problemas:
- Logs detalhados para inicialização do Weaviate
- Logs para carregamento de objetivos e diretrizes
- Logs para integração com OpenAI
- Logs para autenticação e acesso à API

## Backup e Recuperação

Os dados críticos estão armazenados no Weaviate Cloud, que possui seu próprio sistema de backup. Os arquivos de objetivos e diretrizes devem ser versionados no repositório Git para garantir recuperação em caso de falhas.

## Recomendações de Planos

Para um funcionamento ideal do sistema, recomendamos:
- **Render**: Plano Starter ($7/mês) para evitar cold starts
- **Weaviate**: Plano gratuito inicialmente, com upgrade para Starter ($80/mês) conforme o volume de dados aumentar
- **Vercel**: Plano gratuito é suficiente para a maioria dos casos de uso
