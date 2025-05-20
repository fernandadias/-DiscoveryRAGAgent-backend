# Guia do Utilizador - Agente de Discovery e Ideação de Produto

## Introdução

O Agente de Discovery e Ideação de Produto é uma ferramenta de IA projetada para auxiliar equipas de produto na análise e extração de insights de documentos de pesquisa, entrevistas e outros materiais de discovery. Utilizando tecnologia RAG (Retrieval Augmented Generation), o agente consegue responder a perguntas específicas com base nos documentos indexados e nas diretrizes estratégicas da empresa.

## Acesso à Aplicação

A aplicação está disponível através do seguinte link:
[https://discovery-rag-agent.onrender.com](https://discovery-rag-agent.onrender.com)

## Funcionalidades Principais

### 1. Consulta Contextualizada
- Faça perguntas em linguagem natural sobre personalização da Home, engajamento de usuários e outros tópicos de produto
- Receba respostas baseadas nos documentos de discovery e nas diretrizes estratégicas da empresa
- Visualize as fontes utilizadas para cada resposta

### 2. Filtros e Configurações
- Filtre por tipos de documentos (Discovery, Entrevistas, Pesquisas)
- Ajuste a relevância mínima para resultados mais precisos
- Selecione o modelo LLM para diferentes necessidades

### 3. Feedback e Melhoria Contínua
- Avalie a utilidade das respostas
- Forneça comentários para melhorar o sistema
- Visualize estatísticas de feedback na barra lateral

## Como Utilizar

### Fazer uma Consulta

1. Acesse a aplicação através do link fornecido
2. Digite sua pergunta na caixa de texto principal
   - Exemplo: "Quais são os principais desafios na personalização da Home?"
   - Exemplo: "Como podemos melhorar o engajamento dos usuários?"
3. Clique no botão "Enviar Consulta" ou pressione Ctrl+Enter
4. Aguarde enquanto o sistema processa sua consulta

### Interpretar os Resultados

1. **Resposta**: A resposta principal aparecerá na seção "Resposta"
2. **Fontes**: Expanda os itens na seção "Fontes Utilizadas" para ver os trechos dos documentos que fundamentaram a resposta
3. **Feedback**: Indique se a resposta foi útil e forneça comentários adicionais se necessário

### Utilizar Filtros

1. Na barra lateral, selecione os tipos de documentos que deseja incluir na busca
2. Ajuste o controle deslizante de "Relevância Mínima" para refinar os resultados
3. Selecione o modelo LLM desejado (por padrão, GPT-4o é utilizado)

## Exemplos de Consultas Eficazes

- "Quais são as principais necessidades dos usuários MEI na Home?"
- "Como podemos personalizar a experiência para diferentes perfis de usuários?"
- "Quais métricas devemos monitorar para avaliar o sucesso da personalização?"
- "Quais são os principais pontos de atrito identificados nas pesquisas com usuários?"
- "Como equilibrar personalização e simplicidade na interface da Home?"

## Limitações Atuais

- O agente responde apenas com base nos documentos indexados
- Informações muito recentes podem não estar disponíveis se não foram incluídas na base de conhecimento
- Consultas muito específicas sobre tópicos não cobertos nos documentos podem resultar em respostas genéricas

## Resolução de Problemas

### A aplicação não carrega
- Verifique sua conexão com a internet
- Tente atualizar a página
- Se o problema persistir, entre em contato com o suporte

### Respostas imprecisas ou irrelevantes
- Tente reformular sua pergunta de forma mais específica
- Ajuste os filtros na barra lateral
- Forneça feedback negativo e comentários para melhorar o sistema

### Erro ao enviar feedback
- Verifique sua conexão com a internet
- Tente novamente após alguns segundos
- Se o problema persistir, entre em contato com o suporte

## Próximas Atualizações

Estamos constantemente melhorando o Agente de Discovery e Ideação de Produto. Algumas funcionalidades planejadas incluem:

- Exportação de respostas em formato PDF
- Histórico de consultas persistente
- Visualização de dados e gráficos
- Sugestões automáticas de consultas relacionadas

## Suporte

Para dúvidas, sugestões ou relatos de problemas, entre em contato através do email [suporte@exemplo.com](mailto:suporte@exemplo.com) ou abra uma issue no [repositório GitHub](https://github.com/fernandadias/DiscoveryRAGAgent).

---

Desenvolvido com Streamlit, Weaviate e OpenAI | Versão 0.1.0
