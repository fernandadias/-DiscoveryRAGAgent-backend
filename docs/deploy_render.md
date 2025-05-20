# Configuração de Deploy no Render

Este documento descreve os passos necessários para configurar o deploy da aplicação no Render.

## Estrutura de Arquivos para Deploy

Para garantir um deploy bem-sucedido no Render, os seguintes arquivos são necessários:

1. `requirements.txt` - Lista de dependências Python
2. `render.yaml` - Configuração do serviço Render
3. `.render-buildpacks.json` - Configuração de buildpacks (opcional)

## Arquivo requirements.txt

```
streamlit==1.32.0
weaviate-client==4.4.0
openai==1.12.0
pandas==2.1.0
python-dotenv==1.0.0
```

## Arquivo render.yaml

```yaml
services:
  - type: web
    name: discovery-rag-agent
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run src/ui/app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: WEAVIATE_URL
        value: $WEAVIATE_URL
      - key: WEAVIATE_API_KEY
        value: $WEAVIATE_API_KEY
      - key: OPENAI_API_KEY
        value: $OPENAI_API_KEY
    healthCheckPath: /_stcore/health
    autoDeploy: true
```

## Configuração de CI/CD com GitHub Actions

Para configurar CI/CD com GitHub Actions, crie o arquivo `.github/workflows/main.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          python -m unittest discover -s tests
      
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/v1/services/srv-$RENDER_SERVICE_ID/deploys \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            -H "Content-Type: application/json"
```

## Passos para Deploy Manual no Render

1. Crie uma conta no Render (https://render.com)
2. Conecte sua conta GitHub ao Render
3. Crie um novo Web Service
4. Selecione o repositório GitHub `DiscoveryRAGAgent`
5. Configure as seguintes opções:
   - **Nome**: discovery-rag-agent
   - **Ambiente**: Python
   - **Região**: Escolha a mais próxima (ex: US West)
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run src/ui/app.py --server.port $PORT --server.address 0.0.0.0`
6. Configure as variáveis de ambiente:
   - `WEAVIATE_URL`: $WEAVIATE_URL
   - `WEAVIATE_API_KEY`: $WEAVIATE_API_KEY
   - `OPENAI_API_KEY`: $OPENAI_API_KEY
7. Clique em "Create Web Service"

## Considerações de Segurança

Para um ambiente de produção, recomenda-se:

1. Não armazenar chaves de API diretamente no código ou arquivos de configuração
2. Utilizar variáveis de ambiente ou serviços de gerenciamento de segredos
3. Configurar políticas de acesso restritivas para o Weaviate e OpenAI
4. Implementar autenticação para a aplicação Streamlit

## Monitoramento e Manutenção

Após o deploy, é importante:

1. Configurar alertas para falhas no serviço
2. Monitorar o uso de recursos (CPU, memória)
3. Acompanhar logs para identificar problemas
4. Configurar backups regulares dos dados de feedback

## Próximos Passos

1. Configurar domínio personalizado (opcional)
2. Implementar HTTPS com certificado SSL
3. Configurar escalabilidade automática conforme necessidade
4. Implementar sistema de monitoramento de desempenho
