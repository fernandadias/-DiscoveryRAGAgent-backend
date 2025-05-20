"""
Demonstração da visualização do fluxo de processamento do agente RAG

Este módulo fornece uma aplicação Streamlit para demonstrar
a visualização do fluxo de processamento com dados mockados.
"""

import streamlit as st
import time
import random
from flow_visualization import display_flow_visualization

# Configuração da página
st.set_page_config(
    page_title="Visualização do Fluxo do Agente RAG",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar CSS personalizado
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        color: #00A868;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .info-text {
        font-size: 1rem;
        color: #666;
    }
    .node-active {
        background-color: #ffcc00;
        border-radius: 5px;
        padding: 5px;
        font-weight: bold;
    }
    .node-waiting {
        background-color: #cccccc;
        border-radius: 5px;
        padding: 5px;
    }
    .node-completed {
        background-color: #99ff99;
        border-radius: 5px;
        padding: 5px;
    }
    .flow-container {
        margin: 20px 0;
        padding: 15px;
        border: 1px solid #eee;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    .metrics-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 15px 0;
    }
    .metric-card {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        flex: 1;
        min-width: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Dados mockados para o fluxo
mock_data = {
    "pdf_docs": {"status": "waiting", "time": 0, "data": "2 documentos PDF"},
    "pdf_extractor": {"status": "waiting", "time": 0, "data": ""},
    "raw_text": {"status": "waiting", "time": 0, "data": ""},
    "metadata_extractor": {"status": "waiting", "time": 0, "data": ""},
    "diretrizes": {"status": "waiting", "time": 0, "data": "Diretrizes de produto carregadas"},
    "processed_docs": {"status": "waiting", "time": 0, "data": ""},
    "chunker": {"status": "waiting", "time": 0, "data": ""},
    "chunks": {"status": "waiting", "time": 0, "data": ""},
    "metadata_enricher": {"status": "waiting", "time": 0, "data": ""},
    "json_serializer": {"status": "waiting", "time": 0, "data": ""},
    "schema_creator": {"status": "waiting", "time": 0, "data": ""},
    "batch_indexer": {"status": "waiting", "time": 0, "data": ""},
    "openai_embeddings": {"status": "waiting", "time": 0, "data": ""},
    "weaviate_db": {"status": "waiting", "time": 0, "data": ""},
    "user_query": {"status": "waiting", "time": 0, "data": ""},
    "streamlit_form": {"status": "waiting", "time": 0, "data": ""},
    "semantic_search": {"status": "waiting", "time": 0, "data": ""},
    "relevant_docs": {"status": "waiting", "time": 0, "data": ""},
    "prompt_builder": {"status": "waiting", "time": 0, "data": ""},
    "openai_llm": {"status": "waiting", "time": 0, "data": ""},
    "generated_response": {"status": "waiting", "time": 0, "data": ""},
    "response_display": {"status": "waiting", "time": 0, "data": ""},
    "sources_display": {"status": "waiting", "time": 0, "data": ""},
    "feedback_system": {"status": "waiting", "time": 0, "data": ""}
}

# Sequência de processamento para simulação
processing_sequence = [
    "pdf_docs",
    "pdf_extractor",
    "raw_text",
    "metadata_extractor",
    "processed_docs",
    "chunker",
    "chunks",
    "metadata_enricher",
    "json_serializer",
    "processed_docs",
    "schema_creator",
    "batch_indexer",
    "openai_embeddings",
    "weaviate_db",
    "user_query",
    "streamlit_form",
    "semantic_search",
    "relevant_docs",
    "prompt_builder",
    "openai_llm",
    "generated_response",
    "response_display",
    "sources_display",
    "feedback_system"
]

# Dados mockados para métricas
mock_metrics = {
    "total_docs": 2,
    "total_chunks": 0,
    "tokens_used": 0,
    "processing_time": 0,
    "retrieval_time": 0,
    "generation_time": 0,
    "total_time": 0
}

# Função para simular o processamento
def simulate_processing():
    # Resetar dados
    for node in mock_data:
        mock_data[node]["status"] = "waiting"
        mock_data[node]["time"] = 0
    
    # Resetar métricas
    mock_metrics["total_chunks"] = 0
    mock_metrics["tokens_used"] = 0
    mock_metrics["processing_time"] = 0
    mock_metrics["retrieval_time"] = 0
    mock_metrics["generation_time"] = 0
    mock_metrics["total_time"] = 0
    
    # Placeholder para o status atual
    status_placeholder = st.empty()
    
    # Placeholder para métricas
    metrics_placeholder = st.empty()
    
    # Placeholder para detalhes do nó
    node_details_placeholder = st.empty()
    
    # Iniciar tempo total
    start_time = time.time()
    
    # Processar cada nó na sequência
    for i, node in enumerate(processing_sequence):
        # Atualizar status para ativo
        mock_data[node]["status"] = "active"
        
        # Exibir status atual
        status_html = generate_status_html()
        status_placeholder.markdown(status_html, unsafe_allow_html=True)
        
        # Simular tempo de processamento
        process_time = random.uniform(0.5, 2.0)
        time.sleep(process_time)
        
        # Atualizar tempo do nó
        mock_data[node]["time"] = process_time
        
        # Atualizar dados mockados com base no nó
        update_mock_data(node, process_time)
        
        # Atualizar métricas
        update_metrics(node, process_time)
        
        # Exibir métricas atualizadas
        metrics_html = generate_metrics_html()
        metrics_placeholder.markdown(metrics_html, unsafe_allow_html=True)
        
        # Exibir detalhes do nó atual
        node_details_html = generate_node_details_html(node)
        node_details_placeholder.markdown(node_details_html, unsafe_allow_html=True)
        
        # Atualizar status para concluído
        mock_data[node]["status"] = "completed"
        
        # Atualizar visualização de status
        status_html = generate_status_html()
        status_placeholder.markdown(status_html, unsafe_allow_html=True)
    
    # Atualizar tempo total
    mock_metrics["total_time"] = time.time() - start_time
    
    # Exibir métricas finais
    metrics_html = generate_metrics_html()
    metrics_placeholder.markdown(metrics_html, unsafe_allow_html=True)
    
    # Exibir mensagem de conclusão
    st.success("Processamento concluído com sucesso!")

# Função para atualizar dados mockados
def update_mock_data(node, process_time):
    if node == "pdf_extractor":
        mock_data[node]["data"] = "Extraindo texto de 2 PDFs"
    elif node == "raw_text":
        mock_data[node]["data"] = "15.432 caracteres extraídos"
    elif node == "metadata_extractor":
        mock_data[node]["data"] = "Metadados: autor, data, título"
    elif node == "processed_docs":
        mock_data[node]["data"] = "2 documentos processados"
    elif node == "chunker":
        mock_data[node]["data"] = "Dividindo em chunks de 500 tokens"
    elif node == "chunks":
        num_chunks = random.randint(20, 30)
        mock_data[node]["data"] = f"{num_chunks} chunks gerados"
        mock_metrics["total_chunks"] = num_chunks
    elif node == "metadata_enricher":
        mock_data[node]["data"] = "Adicionando metadados aos chunks"
    elif node == "json_serializer":
        mock_data[node]["data"] = "Serializando para JSON"
    elif node == "schema_creator":
        mock_data[node]["data"] = "Criando schema no Weaviate"
    elif node == "batch_indexer":
        mock_data[node]["data"] = f"Indexando {mock_metrics['total_chunks']} chunks"
    elif node == "openai_embeddings":
        tokens = mock_metrics["total_chunks"] * random.randint(400, 600)
        mock_data[node]["data"] = f"Gerando embeddings ({tokens} tokens)"
        mock_metrics["tokens_used"] += tokens
    elif node == "weaviate_db":
        mock_data[node]["data"] = f"{mock_metrics['total_chunks']} vetores armazenados"
    elif node == "user_query":
        mock_data[node]["data"] = "Consulta: 'Quais os perfis de usuários?'"
    elif node == "streamlit_form":
        mock_data[node]["data"] = "Processando formulário"
    elif node == "semantic_search":
        mock_data[node]["data"] = "Buscando documentos similares"
    elif node == "relevant_docs":
        mock_data[node]["data"] = "3 documentos relevantes encontrados"
    elif node == "prompt_builder":
        mock_data[node]["data"] = "Construindo prompt com contexto"
    elif node == "openai_llm":
        tokens_prompt = random.randint(1500, 2500)
        tokens_completion = random.randint(500, 1000)
        mock_data[node]["data"] = f"Gerando resposta ({tokens_prompt} tokens entrada, {tokens_completion} tokens saída)"
        mock_metrics["tokens_used"] += (tokens_prompt + tokens_completion)
    elif node == "generated_response":
        mock_data[node]["data"] = "Resposta gerada com 750 caracteres"
    elif node == "response_display":
        mock_data[node]["data"] = "Exibindo resposta formatada"
    elif node == "sources_display":
        mock_data[node]["data"] = "Exibindo 3 fontes utilizadas"
    elif node == "feedback_system":
        mock_data[node]["data"] = "Aguardando feedback do usuário"

# Função para atualizar métricas
def update_metrics(node, process_time):
    if node in ["pdf_extractor", "raw_text", "metadata_extractor", "chunker", "metadata_enricher", "json_serializer"]:
        mock_metrics["processing_time"] += process_time
    elif node in ["semantic_search", "relevant_docs"]:
        mock_metrics["retrieval_time"] += process_time
    elif node in ["prompt_builder", "openai_llm", "generated_response"]:
        mock_metrics["generation_time"] += process_time

# Função para gerar HTML do status atual
def generate_status_html():
    html = """
    <div class="flow-container">
        <h3>Status do Processamento</h3>
        <table style="width:100%">
    """
    
    # Agrupar nós por etapa
    node_groups = {
        "Ingestão de Dados": ["pdf_docs", "pdf_extractor", "raw_text", "metadata_extractor", "diretrizes"],
        "Chunking e Processamento": ["processed_docs", "chunker", "chunks", "metadata_enricher", "json_serializer"],
        "Indexação Vetorial": ["schema_creator", "batch_indexer", "openai_embeddings", "weaviate_db"],
        "Recuperação e Geração": ["user_query", "streamlit_form", "semantic_search", "relevant_docs", "prompt_builder", "openai_llm", "generated_response"],
        "Interface do Usuário": ["response_display", "sources_display", "feedback_system"]
    }
    
    # Adicionar cada grupo
    for group_name, nodes in node_groups.items():
        html += f"""
        <tr>
            <td colspan="2" style="background-color:#f0f0f0; padding:5px; font-weight:bold;">{group_name}</td>
        </tr>
        """
        
        for node in nodes:
            # Obter dados do nó
            node_data = mock_data[node]
            status = node_data["status"]
            
            # Determinar classe CSS com base no status
            if status == "active":
                status_class = "node-active"
            elif status == "completed":
                status_class = "node-completed"
            else:
                status_class = "node-waiting"
            
            # Obter nome legível do nó
            node_name = node.replace("_", " ").title()
            
            # Adicionar linha para o nó
            html += f"""
            <tr>
                <td style="padding:5px;"><span class="{status_class}">{node_name}</span></td>
                <td style="padding:5px;">{node_data["data"] if node_data["data"] else ""}</td>
            </tr>
            """
    
    html += """
        </table>
    </div>
    """
    
    return html

# Função para gerar HTML das métricas
def generate_metrics_html():
    html = """
    <div class="metrics-container">
    """
    
    # Adicionar cada métrica
    metrics = [
        {"name": "Documentos", "value": mock_metrics["total_docs"], "icon": "📄"},
        {"name": "Chunks", "value": mock_metrics["total_chunks"], "icon": "🧩"},
        {"name": "Tokens", "value": mock_metrics["tokens_used"], "icon": "🔤"},
        {"name": "Tempo de Processamento", "value": f"{mock_metrics['processing_time']:.2f}s", "icon": "⚙️"},
        {"name": "Tempo de Recuperação", "value": f"{mock_metrics['retrieval_time']:.2f}s", "icon": "🔍"},
        {"name": "Tempo de Geração", "value": f"{mock_metrics['generation_time']:.2f}s", "icon": "💬"},
        {"name": "Tempo Total", "value": f"{mock_metrics['total_time']:.2f}s", "icon": "⏱️"}
    ]
    
    for metric in metrics:
        html += f"""
        <div class="metric-card">
            <div style="font-size:24px;">{metric["icon"]}</div>
            <div style="font-weight:bold;">{metric["name"]}</div>
            <div style="font-size:18px;">{metric["value"]}</div>
        </div>
        """
    
    html += """
    </div>
    """
    
    return html

# Função para gerar HTML dos detalhes do nó atual
def generate_node_details_html(node):
    # Obter dados do nó
    node_data = mock_data[node]
    
    # Obter nome legível do nó
    node_name = node.replace("_", " ").title()
    
    html = f"""
    <div style="margin:20px 0; padding:15px; border:2px solid #ffcc00; border-radius:10px; background-color:#fffbf0;">
        <h3>Processando: {node_name}</h3>
        <p>Tempo estimado: {node_data["time"]:.2f}s</p>
        <p>{node_data["data"]}</p>
        <div style="width:100%; height:10px; background-color:#eee; border-radius:5px; margin-top:10px;">
            <div style="width:100%; height:10px; background-color:#ffcc00; border-radius:5px; animation: pulse 1s infinite;">
            </div>
        </div>
    </div>
    """
    
    return html

# Interface principal
def main():
    st.title("Visualização do Fluxo do Agente RAG")
    
    st.markdown("""
    Esta demonstração simula o fluxo de processamento do agente RAG com dados mockados,
    permitindo visualizar como os dados fluem através dos diferentes componentes do sistema.
    """)
    
    # Exibir visualização estática do fluxo
    display_flow_visualization()
    
    # Adicionar seção de simulação
    st.header("Simulação do Processamento")
    
    st.markdown("""
    Clique no botão abaixo para simular o processamento de uma consulta através do agente RAG.
    A simulação mostrará o fluxo de dados e atualizará as métricas em tempo real.
    """)
    
    # Botão para iniciar simulação
    if st.button("Iniciar Simulação", key="start_simulation"):
        simulate_processing()

if __name__ == "__main__":
    main()
