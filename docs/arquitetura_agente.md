```mermaid
graph TD
    subgraph "Ingestão de Dados"
        A[Documentos PDF] -->|Extração de Texto| B[Processador de PDF]
        B -->|Texto + Metadados| C[Documentos Processados]
        D[Diretrizes de Produto] -->|Contexto Estratégico| E[Base de Conhecimento]
    end

    subgraph "Base Vetorial (Weaviate)"
        C -->|Indexação| F[Coleção Document]
        F -->|Vectorização| G[Embeddings OpenAI]
        E -->|Contexto Fixo| H[Diretrizes Estratégicas]
    end

    subgraph "RAG (Retrieval Augmented Generation)"
        I[Query do Usuário] -->|Busca Semântica| J[Recuperação de Contexto]
        J -->|Documentos Relevantes| K[Construção de Prompt]
        H -->|Diretrizes| K
        K -->|Prompt Enriquecido| L[LLM (GPT-4o)]
        L -->|Resposta Gerada| M[Resposta Final]
    end

    subgraph "Interface do Usuário (Streamlit)"
        N[Formulário de Consulta] -->|Input| I
        M -->|Output| O[Exibição de Resposta]
        P[Visualização de Fontes] -->|Transparência| O
        Q[Feedback do Usuário] -->|Melhoria Contínua| R[Ajustes no Sistema]
    end

    style A fill:#f9d5e5,stroke:#333,stroke-width:2px
    style D fill:#f9d5e5,stroke:#333,stroke-width:2px
    style F fill:#eeeeee,stroke:#333,stroke-width:2px
    style G fill:#eeeeee,stroke:#333,stroke-width:2px
    style H fill:#eeeeee,stroke:#333,stroke-width:2px
    style L fill:#d5e8f9,stroke:#333,stroke-width:2px
    style M fill:#d5e8f9,stroke:#333,stroke-width:2px
    style N fill:#e2f0cb,stroke:#333,stroke-width:2px
    style O fill:#e2f0cb,stroke:#333,stroke-width:2px
```
