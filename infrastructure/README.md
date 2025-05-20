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
```

## Serviços Utilizados

### Weaviate Cloud

- **Instância**: discoveryragagent-backend
- **REST Endpoint**: xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud
- **gRPC Endpoint**: grpc-xoplne4asfshde3fsprroq.c0.us-west3.gcp.weaviate.cloud
- **Região**: us-west3 (GCP)
- **Modelo de Embeddings**: OpenAI (text-embedding-ada-002)

### Render (Backend)

- **Tipo**: Web Service
- **Plano**: Starter
- **Região**: Oregon (US West)
- **Branch**: main
- **Runtime**: Python 3.9
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Vercel (Frontend)

- **Framework**: Next.js
- **Região**: Auto (CDN Global)
- **Branch**: main
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

## Estrutura de Arquivos

```
backend/
├── data/
│   ├── raw/                # Documentos PDF para ingestão
│   ├── processed/          # Documentos processados
│   ├── objectives/         # Arquivos MD de objetivos
│   └── guidelines/         # Arquivos MD de diretrizes
├── src/
│   ├── api/                # Rotas e modelos da API
│   ├── context/            # Gerenciadores de objetivos e diretrizes
│   ├── ingest/             # Pipeline de ingestão
│   ├── rag/                # Integração RAG
│   └── utils/              # Utilitários
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
      "dataType": ["string"]
    },
    {
      "name": "content",
      "description": "Conteúdo do documento",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": false,
          "vectorizePropertyName": true
        }
      }
    },
    {
      "name": "metadata",
      "description": "Metadados do documento",
      "dataType": ["object"]
    }
  ]
}
```

## Configuração do OpenAI

- **Modelo para Geração de Texto**: gpt-4o
- **Modelo para Embeddings**: text-embedding-ada-002
- **Temperatura**: 0.7
- **Max Tokens**: 1500

## Instruções de Deploy

### Backend (Render)

1. Faça login no Render Dashboard
2. Conecte o repositório GitHub
3. Configure as variáveis de ambiente listadas acima
4. Clique em "Deploy"

### Frontend (Vercel)

1. Faça login no Vercel Dashboard
2. Conecte o repositório GitHub
3. Configure a variável de ambiente `NEXT_PUBLIC_API_URL` apontando para o backend
4. Clique em "Deploy"

## Monitoramento

Atualmente, o monitoramento é feito através dos dashboards nativos do Render e Vercel. Logs detalhados são gerados no console do serviço Render.

## Backup e Recuperação

Os dados críticos estão armazenados no Weaviate Cloud, que possui seu próprio sistema de backup. Os arquivos de objetivos e diretrizes devem ser versionados no repositório Git para garantir recuperação em caso de falhas.
