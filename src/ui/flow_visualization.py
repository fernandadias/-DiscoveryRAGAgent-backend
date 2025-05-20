"""
Módulo de visualização do fluxo de processamento do agente RAG

Este módulo fornece componentes Streamlit para visualizar o fluxo
de processamento do agente RAG de forma semelhante ao n8n.
"""

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import io
import base64
from PIL import Image
import numpy as np

# Definir cores para os diferentes tipos de nós
NODE_COLORS = {
    'input': '#ffcc99',    # Laranja claro
    'process': '#99ccff',  # Azul claro
    'storage': '#ccff99',  # Verde claro
    'api': '#ff99cc',      # Rosa
    'output': '#cc99ff'    # Roxo claro
}

def create_rag_flow_graph():
    """
    Cria um grafo NetworkX representando o fluxo do agente RAG.
    
    Returns:
        G (nx.DiGraph): Grafo direcionado representando o fluxo
        pos (dict): Posições dos nós para visualização
        node_colors (list): Cores dos nós
        node_types (dict): Tipos de cada nó
    """
    # Criar grafo direcionado
    G = nx.DiGraph()
    
    # Definir nós e seus tipos
    nodes = {
        # Ingestão de Dados
        'pdf_docs': {'type': 'input', 'label': 'Documentos PDF'},
        'pdf_extractor': {'type': 'process', 'label': 'Extrator PDF\n(poppler-utils)'},
        'raw_text': {'type': 'storage', 'label': 'Texto Bruto'},
        'metadata_extractor': {'type': 'process', 'label': 'Extrator de\nMetadados'},
        'diretrizes': {'type': 'input', 'label': 'Diretrizes\nde Produto'},
        
        # Chunking e Processamento
        'chunker': {'type': 'process', 'label': 'Chunker\n(data_ingestion.py)'},
        'chunks': {'type': 'storage', 'label': 'Chunks\nde Texto'},
        'metadata_enricher': {'type': 'process', 'label': 'Enriquecedor\nde Metadados'},
        'json_serializer': {'type': 'process', 'label': 'Serializador\nJSON'},
        'processed_docs': {'type': 'storage', 'label': 'Documentos\nProcessados'},
        
        # Indexação Vetorial
        'schema_creator': {'type': 'process', 'label': 'Criador de\nSchema Weaviate'},
        'batch_indexer': {'type': 'process', 'label': 'Indexador\nem Lote'},
        'openai_embeddings': {'type': 'api', 'label': 'API de\nEmbeddings OpenAI'},
        'weaviate_db': {'type': 'storage', 'label': 'Base Vetorial\nWeaviate'},
        
        # Recuperação e Geração
        'user_query': {'type': 'input', 'label': 'Consulta\ndo Usuário'},
        'semantic_search': {'type': 'process', 'label': 'Busca\nSemântica'},
        'relevant_docs': {'type': 'storage', 'label': 'Documentos\nRelevantes'},
        'prompt_builder': {'type': 'process', 'label': 'Construtor\nde Prompt'},
        'openai_llm': {'type': 'api', 'label': 'LLM GPT-4o\n(OpenAI API)'},
        'generated_response': {'type': 'output', 'label': 'Resposta\nGerada'},
        
        # Interface do Usuário
        'streamlit_form': {'type': 'process', 'label': 'Formulário\nStreamlit'},
        'response_display': {'type': 'output', 'label': 'Exibição\nde Resposta'},
        'sources_display': {'type': 'output', 'label': 'Visualização\nde Fontes'},
        'feedback_system': {'type': 'process', 'label': 'Sistema de\nFeedback'}
    }
    
    # Adicionar nós ao grafo
    for node_id, attrs in nodes.items():
        G.add_node(node_id, **attrs)
    
    # Definir arestas (conexões entre nós)
    edges = [
        # Ingestão de Dados
        ('pdf_docs', 'pdf_extractor'),
        ('pdf_extractor', 'raw_text'),
        ('raw_text', 'metadata_extractor'),
        ('metadata_extractor', 'processed_docs'),
        ('diretrizes', 'prompt_builder'),
        
        # Chunking e Processamento
        ('processed_docs', 'chunker'),
        ('chunker', 'chunks'),
        ('chunks', 'metadata_enricher'),
        ('metadata_enricher', 'json_serializer'),
        ('json_serializer', 'processed_docs'),
        
        # Indexação Vetorial
        ('processed_docs', 'schema_creator'),
        ('schema_creator', 'batch_indexer'),
        ('batch_indexer', 'openai_embeddings'),
        ('openai_embeddings', 'weaviate_db'),
        
        # Recuperação e Geração
        ('user_query', 'streamlit_form'),
        ('streamlit_form', 'semantic_search'),
        ('weaviate_db', 'semantic_search'),
        ('semantic_search', 'relevant_docs'),
        ('relevant_docs', 'prompt_builder'),
        ('prompt_builder', 'openai_llm'),
        ('openai_llm', 'generated_response'),
        
        # Interface do Usuário
        ('generated_response', 'response_display'),
        ('relevant_docs', 'sources_display'),
        ('response_display', 'feedback_system')
    ]
    
    # Adicionar arestas ao grafo
    for source, target in edges:
        G.add_edge(source, target)
    
    # Definir layout em camadas para visualização semelhante ao n8n
    pos = {
        # Ingestão de Dados (Camada 1)
        'pdf_docs': (0, 10),
        'diretrizes': (0, 6),
        
        # Processamento Inicial (Camada 2)
        'pdf_extractor': (2, 10),
        
        # Resultados Iniciais (Camada 3)
        'raw_text': (4, 10),
        'metadata_extractor': (6, 10),
        
        # Processamento de Chunks (Camada 4)
        'processed_docs': (8, 10),
        'chunker': (10, 10),
        
        # Resultados de Chunks (Camada 5)
        'chunks': (12, 10),
        'metadata_enricher': (14, 10),
        'json_serializer': (16, 10),
        
        # Indexação (Camada 6)
        'schema_creator': (8, 8),
        'batch_indexer': (10, 8),
        'openai_embeddings': (12, 8),
        'weaviate_db': (14, 8),
        
        # Consulta do Usuário (Camada 7)
        'user_query': (0, 4),
        'streamlit_form': (2, 4),
        
        # Recuperação (Camada 8)
        'semantic_search': (14, 6),
        'relevant_docs': (16, 6),
        
        # Geração (Camada 9)
        'prompt_builder': (18, 6),
        'openai_llm': (20, 6),
        'generated_response': (22, 6),
        
        # Interface (Camada 10)
        'response_display': (22, 4),
        'sources_display': (22, 2),
        'feedback_system': (24, 3)
    }
    
    # Extrair cores dos nós com base em seus tipos
    node_colors = [NODE_COLORS[nodes[node]['type']] for node in G.nodes()]
    
    # Criar dicionário de tipos de nós
    node_types = {node: attrs['type'] for node, attrs in nodes.items()}
    
    return G, pos, node_colors, node_types

def draw_rag_flow(G, pos, node_colors, node_types, figsize=(20, 10)):
    """
    Desenha o grafo do fluxo RAG em estilo n8n.
    
    Args:
        G (nx.DiGraph): Grafo direcionado representando o fluxo
        pos (dict): Posições dos nós para visualização
        node_colors (list): Cores dos nós
        node_types (dict): Tipos de cada nó
        figsize (tuple): Tamanho da figura
        
    Returns:
        bytes: Imagem em formato PNG como bytes
    """
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)
    
    # Desenhar nós com bordas arredondadas e cores específicas
    for node, (x, y) in pos.items():
        node_type = node_types[node]
        color = NODE_COLORS[node_type]
        
        # Criar retângulo arredondado
        rect = mpatches.FancyBboxPatch(
            (x - 1, y - 0.5), 2, 1, 
            boxstyle=mpatches.BoxStyle("Round", pad=0.3, rounding_size=0.2),
            facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.9
        )
        ax.add_patch(rect)
        
        # Adicionar texto do nó
        label = G.nodes[node]['label']
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Desenhar arestas com setas (versão simplificada compatível)
    for u, v in G.edges():
        # Obter posições dos nós
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        
        # Desenhar linha reta com seta
        ax.annotate("", 
                   xy=(x2, y2), 
                   xytext=(x1, y1),
                   arrowprops=dict(arrowstyle="->", color='#555555', 
                                  linewidth=1.5, alpha=0.7))
    
    # Criar legenda
    legend_elements = [
        mpatches.Patch(facecolor=NODE_COLORS['input'], edgecolor='black', label='Entrada'),
        mpatches.Patch(facecolor=NODE_COLORS['process'], edgecolor='black', label='Processamento'),
        mpatches.Patch(facecolor=NODE_COLORS['storage'], edgecolor='black', label='Armazenamento'),
        mpatches.Patch(facecolor=NODE_COLORS['api'], edgecolor='black', label='API Externa'),
        mpatches.Patch(facecolor=NODE_COLORS['output'], edgecolor='black', label='Saída')
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.05),
              ncol=5, fancybox=True, shadow=True)
    
    # Configurar limites e remover eixos
    ax.set_xlim(-1, 26)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Adicionar título
    plt.title('Fluxo de Processamento do Agente RAG', fontsize=16, pad=20)
    
    # Salvar figura em bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return buf

def get_flow_image_html():
    """
    Gera o HTML para exibir a imagem do fluxo RAG.
    
    Returns:
        str: HTML para exibir a imagem
    """
    # Criar grafo
    G, pos, node_colors, node_types = create_rag_flow_graph()
    
    # Desenhar grafo
    img_bytes = draw_rag_flow(G, pos, node_colors, node_types)
    
    # Converter para base64
    img_str = base64.b64encode(img_bytes.read()).decode('utf-8')
    
    # Criar HTML
    html = f"""
    <div style="display: flex; justify-content: center; margin: 20px 0;">
        <img src="data:image/png;base64,{img_str}" 
             alt="Fluxo de Processamento do Agente RAG" 
             style="max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    </div>
    """
    
    return html

def display_flow_visualization():
    """
    Exibe a visualização do fluxo RAG no Streamlit.
    """
    st.title("Visualização do Fluxo de Processamento")
    
    st.markdown("""
    Esta visualização mostra o fluxo completo de processamento do agente RAG, 
    desde a ingestão de documentos até a geração de respostas, em um formato 
    semelhante ao n8n.
    """)
    
    # Exibir imagem do fluxo
    html = get_flow_image_html()
    st.markdown(html, unsafe_allow_html=True)
    
    # Adicionar explicação das etapas
    with st.expander("Explicação Detalhada das Etapas"):
        st.markdown("""
        ### 1. Ingestão de Dados
        - **Documentos PDF**: Entrada inicial de documentos
        - **Extrator PDF**: Utiliza poppler-utils para extrair texto
        - **Texto Bruto**: Armazena o texto extraído
        - **Extrator de Metadados**: Extrai informações como autor, data, etc.
        - **Diretrizes de Produto**: Contexto estratégico para o agente
        
        ### 2. Chunking e Processamento
        - **Chunker**: Divide o texto em segmentos menores
        - **Chunks de Texto**: Armazena os segmentos divididos
        - **Enriquecedor de Metadados**: Adiciona metadados a cada chunk
        - **Serializador JSON**: Converte para formato JSON
        - **Documentos Processados**: Armazena os documentos prontos para indexação
        
        ### 3. Indexação Vetorial
        - **Criador de Schema**: Configura a estrutura no Weaviate
        - **Indexador em Lote**: Processa documentos em batch
        - **API de Embeddings OpenAI**: Gera vetores para os chunks
        - **Base Vetorial Weaviate**: Armazena os vetores e metadados
        
        ### 4. Recuperação e Geração
        - **Consulta do Usuário**: Entrada da pergunta
        - **Busca Semântica**: Encontra documentos relevantes
        - **Documentos Relevantes**: Armazena os resultados da busca
        - **Construtor de Prompt**: Combina consulta, contexto e diretrizes
        - **LLM GPT-4o**: Gera resposta contextualizada
        - **Resposta Gerada**: Resultado final do processamento
        
        ### 5. Interface do Usuário
        - **Formulário Streamlit**: Captura a consulta do usuário
        - **Exibição de Resposta**: Mostra a resposta gerada
        - **Visualização de Fontes**: Exibe as fontes utilizadas
        - **Sistema de Feedback**: Coleta feedback do usuário
        """)
    
    # Adicionar informações sobre o fluxo de dados
    with st.expander("Fluxo de Dados"):
        st.markdown("""
        ### Caminho dos Dados
        1. Os documentos PDF são processados para extrair texto e metadados
        2. O texto é dividido em chunks e enriquecido com metadados
        3. Os chunks são convertidos em vetores e armazenados no Weaviate
        4. Quando uma consulta é recebida, o sistema busca chunks relevantes
        5. Os chunks relevantes são combinados com as diretrizes para criar um prompt
        6. O prompt é enviado ao GPT-4o para gerar uma resposta
        7. A resposta e as fontes são exibidas ao usuário
        8. O feedback do usuário é coletado para melhorias futuras
        """)

if __name__ == "__main__":
    # Testar visualização
    display_flow_visualization()
