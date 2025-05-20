# Design da Interface Streamlit - Agente de Discovery e Ideação de Produto

## Visão Geral

A interface Streamlit para o Agente de Discovery e Ideação de Produto será projetada para ser intuitiva, eficiente e alinhada com a identidade visual da Stone. O objetivo é criar uma experiência que permita aos usuários obter insights valiosos dos dados de discovery de forma rápida e contextualizada.

## Estrutura da Interface

### 1. Layout Principal

```
+-------------------------------------------------------+
|                                                       |
|  [LOGO] Agente de Discovery e Ideação de Produto      |
|                                                       |
+-------------------------------------------------------+
|                   |                                   |
|                   |                                   |
|                   |                                   |
|                   |                                   |
|   BARRA LATERAL   |        ÁREA PRINCIPAL            |
|                   |                                   |
|                   |                                   |
|                   |                                   |
|                   |                                   |
+-------------------+-----------------------------------+
```

### 2. Componentes da Barra Lateral

- **Filtros de Documentos**
  - Checkbox para tipos de documentos (Discovery, Entrevistas, Pesquisas)
  - Slider para relevância mínima
  
- **Configurações**
  - Seletor de modelo LLM (GPT-4o, outros modelos futuros)
  - Toggle para modo escuro/claro
  
- **Histórico de Consultas**
  - Lista das últimas 5-10 consultas realizadas
  - Opção para limpar histórico

- **Informações do Projeto**
  - Versão do agente
  - Links para documentação
  - Créditos

### 3. Componentes da Área Principal

- **Área de Consulta**
  ```
  +-------------------------------------------------------+
  |                                                       |
  |  Digite sua pergunta:                                 |
  |  +---------------------------------------------------+|
  |  |                                                   ||
  |  |                                                   ||
  |  +---------------------------------------------------+|
  |                                                       |
  |  [Enviar Consulta]                                    |
  |                                                       |
  +-------------------------------------------------------+
  ```

- **Área de Resposta**
  ```
  +-------------------------------------------------------+
  |                                                       |
  |  Resposta:                                            |
  |  +---------------------------------------------------+|
  |  |                                                   ||
  |  |                                                   ||
  |  |                                                   ||
  |  +---------------------------------------------------+|
  |                                                       |
  |  Esta resposta foi útil?  [👍]  [👎]                  |
  |                                                       |
  |  Comentários: [                                    ]  |
  |                                                       |
  +-------------------------------------------------------+
  ```

- **Painel de Fontes**
  ```
  +-------------------------------------------------------+
  |                                                       |
  |  Fontes Utilizadas:                                   |
  |  +---------------------------------------------------+|
  |  | Documento 1 (relevância: 85%)                     ||
  |  | "Trecho do documento que foi utilizado..."        ||
  |  |                                                   ||
  |  | Documento 2 (relevância: 72%)                     ||
  |  | "Trecho do documento que foi utilizado..."        ||
  |  +---------------------------------------------------+|
  |                                                       |
  +-------------------------------------------------------+
  ```

- **Ações Adicionais**
  ```
  +-------------------------------------------------------+
  |                                                       |
  |  [Exportar como PDF]  [Copiar]  [Nova Consulta]       |
  |                                                       |
  +-------------------------------------------------------+
  ```

## Fluxo de Usuário

### 1. Tela Inicial
- Apresentação do agente com breve descrição
- Campo de consulta em destaque
- Instruções simples de uso

### 2. Fluxo de Consulta
1. Usuário digita uma pergunta no campo de consulta
2. Usuário clica em "Enviar Consulta"
3. Exibição de indicador de carregamento durante o processamento
4. Apresentação da resposta formatada
5. Exibição das fontes utilizadas
6. Opções de feedback e ações adicionais

### 3. Interações Secundárias
- Filtrar tipos de documentos na barra lateral
- Ajustar configurações de modelo
- Visualizar e reutilizar consultas do histórico
- Exportar ou copiar respostas

## Elementos Visuais

### Cores
- Paleta principal: Verde Stone (#00A868), Branco (#FFFFFF), Cinza Escuro (#333333)
- Elementos de destaque: Azul (#007BFF), Vermelho (#DC3545)
- Modo escuro: Fundo escuro (#121212), Texto claro (#E0E0E0)

### Tipografia
- Fonte principal: Inter (sans-serif)
- Tamanhos:
  - Títulos: 24px
  - Subtítulos: 18px
  - Texto normal: 16px
  - Texto secundário: 14px

### Ícones
- Ícones simples e reconhecíveis
- Consistentes com a identidade visual da Stone

## Responsividade

A interface será responsiva, adaptando-se a diferentes tamanhos de tela:

- **Desktop**: Layout completo com barra lateral e área principal
- **Tablet**: Barra lateral colapsável, foco na área de consulta e resposta
- **Mobile**: Layout simplificado, componentes empilhados verticalmente

## Implementação Técnica

### Estrutura de Arquivos
```
streamlit_app/
├── app.py                # Ponto de entrada principal
├── components/           # Componentes reutilizáveis
│   ├── sidebar.py        # Componentes da barra lateral
│   ├── query_input.py    # Componente de entrada de consulta
│   └── results_display.py # Componente de exibição de resultados
├── utils/                # Funções utilitárias
│   ├── rag_connector.py  # Conexão com o pipeline RAG
│   └── formatting.py     # Formatação de respostas
├── assets/               # Recursos estáticos
│   ├── logo.png          # Logo da Stone
│   └── styles.css        # Estilos personalizados
└── config.py             # Configurações da aplicação
```

### Dependências
- streamlit
- streamlit-extras (para componentes adicionais)
- PyPDF2 (para exportação de PDF)
- requests (para comunicação com API)

## Próximos Passos

1. Implementar estrutura básica da aplicação Streamlit
2. Desenvolver componentes principais (consulta, resposta, fontes)
3. Integrar com o pipeline RAG existente
4. Adicionar funcionalidades de feedback
5. Implementar recursos adicionais (exportação, histórico)
6. Testar usabilidade e realizar ajustes
7. Preparar para deploy no Render
