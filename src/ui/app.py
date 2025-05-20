"""
Aplicação Streamlit para o Agente de Discovery e Ideação de Produto

Este é o ponto de entrada principal da aplicação Streamlit.
"""

import streamlit as st
import os
import sys
import json
import time

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.rag_connector import create_rag_connector
from ui.feedback_manager import create_feedback_manager
from ui.flow_visualization import display_flow_visualization

# Configuração da página
st.set_page_config(
    page_title="Agente de Discovery e Ideação de Produto",
    page_icon="🔍",
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
    .source-box {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .source-title {
        font-weight: bold;
    }
    .source-content {
        font-style: italic;
        color: #555;
    }
    .feedback-section {
        margin-top: 20px;
        padding: 10px;
        border-top: 1px solid #eee;
    }
    .feedback-success {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Inicializar o conector RAG
@st.cache_resource
def get_rag_connector():
    """
    Inicializa e retorna o conector RAG.
    
    Returns:
        RAGConnector: Instância do conector RAG
    """
    connector = create_rag_connector()
    if connector is None:
        st.error("Erro ao inicializar o conector RAG. Verifique as configurações.")
    return connector

# Inicializar o gerenciador de feedback
@st.cache_resource
def get_feedback_manager():
    """
    Inicializa e retorna o gerenciador de feedback.
    
    Returns:
        FeedbackManager: Instância do gerenciador de feedback
    """
    return create_feedback_manager()

# Função para consultar o sistema RAG
def query_rag_system(query, filters=None):
    """
    Consulta o sistema RAG.
    
    Args:
        query (str): A consulta do usuário
        filters (dict): Filtros opcionais
        
    Returns:
        dict: Resultados da consulta
    """
    connector = get_rag_connector()
    
    if connector is None:
        # Fallback para resultados de exemplo em caso de erro
        return fallback_results(query)
    
    try:
        # Processar a consulta usando o conector RAG
        results = connector.process_query(query, filters)
        return results
    except Exception as e:
        st.error(f"Erro ao processar consulta: {e}")
        return fallback_results(query)

# Função de fallback para resultados em caso de erro
def fallback_results(query):
    """
    Retorna resultados de exemplo em caso de erro.
    
    Args:
        query (str): A consulta do usuário
        
    Returns:
        dict: Resultados de exemplo
    """
    try:
        # Tentar carregar resultados de exemplo
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/processed/validation_results.json"), "r", encoding="utf-8") as f:
            all_results = json.load(f)
            
        # Tentar encontrar uma consulta similar nos resultados de exemplo
        for key, value in all_results.items():
            if any(word in key.lower() for word in query.lower().split()):
                return value
                
        # Se não encontrar, retornar o primeiro resultado
        return next(iter(all_results.values()))
    except Exception as e:
        # Retornar um resultado fictício em caso de erro
        return {
            "query": query,
            "results": [
                {
                    "content": "Conteúdo de exemplo para demonstração.",
                    "filename": "documento_exemplo.pdf",
                    "chunk_id": 1
                }
            ],
            "response": "Esta é uma resposta de exemplo para demonstrar a interface. O sistema RAG real não está disponível no momento."
        }

# Função para salvar feedback
def save_user_feedback(query, response, sources, is_helpful, comments):
    """
    Salva o feedback do usuário.
    
    Args:
        query (str): Consulta do usuário
        response (str): Resposta gerada
        sources (list): Fontes utilizadas
        is_helpful (bool): Se a resposta foi útil
        comments (str): Comentários adicionais
        
    Returns:
        bool: True se o feedback foi salvo com sucesso, False caso contrário
    """
    feedback_manager = get_feedback_manager()
    return feedback_manager.save_feedback(query, response, sources, is_helpful, comments)

# Barra lateral
def render_sidebar():
    st.sidebar.image("https://logodownload.org/wp-content/uploads/2017/11/stone-logo-1.png", width=150)
    st.sidebar.title("Configurações")
    
    # Navegação
    st.sidebar.subheader("Navegação")
    page = st.sidebar.radio(
        "Selecione uma página:",
        ["Consulta ao Agente", "Visualização do Fluxo"]
    )
    
    # Filtros
    st.sidebar.subheader("Filtros de Documentos")
    doc_types = st.sidebar.multiselect(
        "Tipos de Documentos",
        ["Discovery", "Entrevistas", "Pesquisas"],
        default=["Discovery"]
    )
    
    relevance = st.sidebar.slider(
        "Relevância Mínima",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1
    )
    
    # Configurações do modelo
    st.sidebar.subheader("Configurações do Modelo")
    model = st.sidebar.selectbox(
        "Modelo LLM",
        ["GPT-4o", "GPT-3.5 Turbo"],
        index=0
    )
    
    # Tema
    theme = st.sidebar.radio(
        "Tema",
        ["Claro", "Escuro"],
        index=0
    )
    
    # Estatísticas de feedback (se disponíveis)
    try:
        feedback_manager = get_feedback_manager()
        stats = feedback_manager.get_feedback_stats()
        
        if stats['total'] > 0:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Estatísticas de Feedback")
            st.sidebar.markdown(f"**Total de feedbacks:** {stats['total']}")
            st.sidebar.markdown(f"**Respostas úteis:** {stats['helpful_count']} ({stats['helpful_percentage']:.1f}%)")
            st.sidebar.markdown(f"**Respostas não úteis:** {stats['unhelpful_count']} ({stats['unhelpful_percentage']:.1f}%)")
    except Exception:
        pass
    
    # Informações do projeto
    st.sidebar.markdown("---")
    st.sidebar.subheader("Sobre o Projeto")
    st.sidebar.info(
        "Agente de IA para Ideação e Discovery de Produto\n\n"
        "Versão: 0.1.0\n\n"
        "Desenvolvido com Streamlit, Weaviate e OpenAI"
    )
    
    return {
        "page": page,
        "doc_types": doc_types,
        "relevance": relevance,
        "model": model,
        "theme": theme
    }

# Área de consulta ao agente
def render_query_area(sidebar_config):
    # Cabeçalho
    st.markdown("<h1 class='main-header'>Agente de Discovery e Ideação de Produto</h1>", unsafe_allow_html=True)
    
    st.markdown(
        "Este agente utiliza tecnologia RAG (Retrieval Augmented Generation) para responder "
        "perguntas sobre discovery e ideação de produto com base em documentos internos e "
        "diretrizes estratégicas."
    )
    
    # Formulário de consulta
    st.markdown("<h2 class='sub-header'>Nova Consulta</h2>", unsafe_allow_html=True)
    
    with st.form(key="query_form"):
        query = st.text_area(
            "Digite sua pergunta:",
            height=100,
            placeholder="Ex: Quais são os principais desafios na personalização da Home?"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            submit_button = st.form_submit_button(label="Enviar Consulta")
        with col2:
            st.markdown("<div class='info-text'>Pressione Ctrl+Enter para enviar</div>", unsafe_allow_html=True)
    
    # Processar consulta quando o botão for pressionado
    if submit_button and query:
        with st.spinner("Processando sua consulta..."):
            # Obter resultados do sistema RAG
            results = query_rag_system(query, sidebar_config)
            
            # Armazenar resultados na sessão para uso no feedback
            st.session_state.last_query = query
            st.session_state.last_response = results["response"]
            st.session_state.last_sources = results["results"]
            
            # Exibir resposta
            st.markdown("<h2 class='sub-header'>Resposta</h2>", unsafe_allow_html=True)
            st.markdown(results["response"])
            
            # Exibir fontes
            st.markdown("<h2 class='sub-header'>Fontes Utilizadas</h2>", unsafe_allow_html=True)
            
            for i, source in enumerate(results["results"]):
                with st.expander(f"Documento {i+1}: {source['filename']}"):
                    st.markdown(f"**Trecho:**")
                    st.markdown(f"_{source['content']}_")
            
            # Seção de feedback
            st.markdown("<div class='feedback-section'>", unsafe_allow_html=True)
            st.markdown("<h3>Esta resposta foi útil?</h3>", unsafe_allow_html=True)
            
            # Inicializar variáveis de estado para feedback se não existirem
            if 'feedback_submitted' not in st.session_state:
                st.session_state.feedback_submitted = False
            
            if 'feedback_comments' not in st.session_state:
                st.session_state.feedback_comments = ""
            
            # Função para processar feedback positivo
            def submit_positive_feedback():
                comments = st.session_state.feedback_comments
                success = save_user_feedback(
                    st.session_state.last_query,
                    st.session_state.last_response,
                    st.session_state.last_sources,
                    True,
                    comments
                )
                st.session_state.feedback_submitted = success
            
            # Função para processar feedback negativo
            def submit_negative_feedback():
                comments = st.session_state.feedback_comments
                success = save_user_feedback(
                    st.session_state.last_query,
                    st.session_state.last_response,
                    st.session_state.last_sources,
                    False,
                    comments
                )
                st.session_state.feedback_submitted = success
            
            # Exibir formulário de feedback se ainda não foi enviado
            if not st.session_state.feedback_submitted:
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    st.button("👍 Sim", key="feedback_yes", on_click=submit_positive_feedback)
                with col2:
                    st.button("👎 Não", key="feedback_no", on_click=submit_negative_feedback)
                with col3:
                    st.text_input("Comentários (opcional)", key="feedback_comments")
            else:
                st.markdown("<div class='feedback-success'>Obrigado pelo seu feedback!</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Botões de ação
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="Exportar como PDF",
                    data="Funcionalidade em desenvolvimento",
                    file_name="resposta.pdf",
                    mime="application/pdf",
                    disabled=True
                )
            with col2:
                st.button("Copiar Resposta", disabled=True)
            with col3:
                if st.button("Nova Consulta"):
                    # Limpar estado de feedback
                    st.session_state.feedback_submitted = False
                    st.session_state.feedback_comments = ""
                    st.experimental_rerun()

# Área de visualização do fluxo
def render_flow_area():
    # Exibir visualização do fluxo
    display_flow_visualization()
    
    # Adicionar botão para simular processamento
    if st.button("Simular Processamento", key="simulate_processing"):
        # Importar módulo de demonstração
        from ui.flow_visualization_demo import simulate_processing
        
        # Simular processamento
        simulate_processing()

# Função principal
def main():
    # Renderizar barra lateral
    sidebar_config = render_sidebar()
    
    # Renderizar página selecionada
    if sidebar_config["page"] == "Consulta ao Agente":
        render_query_area(sidebar_config)
    else:  # "Visualização do Fluxo"
        render_flow_area()

if __name__ == "__main__":
    main()
