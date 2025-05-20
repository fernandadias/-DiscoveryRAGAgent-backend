"""
Script para testar o fluxo end-to-end da aplicação Streamlit

Este script executa testes para verificar se todos os componentes da aplicação
estão funcionando corretamente juntos.
"""

import os
import sys
import json
import logging
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Importar módulos a serem testados
from ui.rag_connector import RAGConnector, create_rag_connector
from ui.feedback_manager import FeedbackManager, create_feedback_manager

class TestEndToEndFlow(unittest.TestCase):
    """
    Testes end-to-end para a aplicação Streamlit
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes
        """
        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.feedback_dir = os.path.join(self.temp_dir, 'feedback')
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        # Definir caminhos para arquivos de teste
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_dir = os.path.join(self.base_dir, 'tests')
        self.data_dir = os.path.join(self.temp_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Configurar arquivo de feedback para testes
        self.test_feedback_file = os.path.join(self.feedback_dir, 'test_feedback.json')
        with open(self.test_feedback_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        # Inicializar gerenciador de feedback para testes
        self.feedback_manager = FeedbackManager(self.feedback_dir)
        
        # Configurar dados de teste
        self.test_query = "Quais são os principais desafios na personalização da Home?"
        self.test_response = "Os principais desafios incluem a segmentação de usuários, a relevância do conteúdo e a experiência do usuário."
        self.test_sources = [
            {
                "content": "A personalização da Home enfrenta desafios como segmentação de usuários e relevância de conteúdo.",
                "filename": "documento_teste.pdf",
                "chunk_id": 1
            }
        ]
    
    def tearDown(self):
        """
        Limpeza após os testes
        """
        # Remover diretório temporário
        shutil.rmtree(self.temp_dir)
    
    def test_feedback_manager(self):
        """
        Testa o fluxo de feedback do usuário
        """
        logger.info("Testando gerenciador de feedback...")
        
        # Testar salvamento de feedback positivo
        result_positive = self.feedback_manager.save_feedback(
            self.test_query,
            self.test_response,
            self.test_sources,
            True,
            "Resposta muito útil!"
        )
        self.assertTrue(result_positive, "Falha ao salvar feedback positivo")
        
        # Testar salvamento de feedback negativo
        result_negative = self.feedback_manager.save_feedback(
            "Como melhorar o engajamento?",
            "Resposta sobre engajamento",
            [],
            False,
            "Resposta incompleta"
        )
        self.assertTrue(result_negative, "Falha ao salvar feedback negativo")
        
        # Verificar se os feedbacks foram salvos
        all_feedback = self.feedback_manager.get_all_feedback()
        self.assertEqual(len(all_feedback), 2, "Número incorreto de feedbacks salvos")
        
        # Verificar estatísticas
        stats = self.feedback_manager.get_feedback_stats()
        self.assertEqual(stats['total'], 2, "Total de feedbacks incorreto")
        self.assertEqual(stats['helpful_count'], 1, "Contagem de feedbacks úteis incorreta")
        self.assertEqual(stats['unhelpful_count'], 1, "Contagem de feedbacks não úteis incorreta")
        
        logger.info("Teste de gerenciador de feedback concluído com sucesso")
    
    @patch('ui.rag_connector.weaviate')
    @patch('ui.rag_connector.OpenAI')
    def test_rag_connector(self, mock_openai, mock_weaviate):
        """
        Testa o fluxo do conector RAG
        """
        logger.info("Testando conector RAG...")
        
        # Configurar mocks
        mock_client = MagicMock()
        mock_weaviate.connect_to_weaviate_cloud.return_value = mock_client
        mock_client.is_ready.return_value = True
        
        mock_collection = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        
        mock_query = MagicMock()
        mock_collection.query.near_text.return_value = mock_query
        
        # Configurar resultados simulados
        mock_result = MagicMock()
        mock_result.properties = {
            "content": "Conteúdo de teste",
            "filename": "arquivo_teste.pdf",
            "chunk_id": 1,
            "tipo": "Discovery"
        }
        mock_query.objects = [mock_result]
        
        # Configurar mock do OpenAI
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Resposta gerada pelo GPT-4o"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        # Criar conector RAG com diretrizes de teste
        diretrizes_path = os.path.join(self.data_dir, 'test_diretrizes.md')
        with open(diretrizes_path, 'w', encoding='utf-8') as f:
            f.write("# Diretrizes de teste\n\nEstas são diretrizes para teste.")
        
        rag_connector = RAGConnector(
            "https://test-weaviate-url.com",
            "test-api-key",
            "test-openai-key",
            diretrizes_path
        )
        
        # Testar conexão com Weaviate
        client = rag_connector.connect_to_weaviate()
        self.assertIsNotNone(client, "Falha ao conectar com Weaviate")
        
        # Testar busca de documentos
        results = rag_connector.search_documents("teste")
        self.assertEqual(len(results), 1, "Número incorreto de resultados de busca")
        
        # Testar geração de resposta
        response = rag_connector.generate_response("teste", results)
        self.assertEqual(response, "Resposta gerada pelo GPT-4o", "Resposta gerada incorretamente")
        
        # Testar processamento completo de consulta
        query_results = rag_connector.process_query("teste")
        self.assertEqual(query_results['query'], "teste", "Consulta incorreta nos resultados")
        self.assertEqual(len(query_results['results']), 1, "Número incorreto de resultados")
        self.assertEqual(query_results['response'], "Resposta gerada pelo GPT-4o", "Resposta incorreta nos resultados")
        
        logger.info("Teste de conector RAG concluído com sucesso")
    
    def test_end_to_end_integration(self):
        """
        Testa a integração end-to-end entre RAG e feedback
        """
        logger.info("Testando integração end-to-end...")
        
        # Simular fluxo completo com dados mockados
        # 1. Usuário faz uma consulta
        query = "Como podemos melhorar o engajamento dos usuários na Home?"
        
        # 2. Sistema RAG processa a consulta (simulado)
        rag_results = {
            "query": query,
            "results": [
                {
                    "content": "O engajamento dos usuários pode ser melhorado através de personalização e conteúdo relevante.",
                    "filename": "engajamento_usuarios.pdf",
                    "chunk_id": 3
                }
            ],
            "response": "Para melhorar o engajamento dos usuários na Home, recomendamos: 1) Personalização baseada no perfil e comportamento, 2) Conteúdo relevante e atualizado, 3) Design intuitivo e acessível."
        }
        
        # 3. Usuário fornece feedback
        feedback_result = self.feedback_manager.save_feedback(
            rag_results["query"],
            rag_results["response"],
            rag_results["results"],
            True,
            "Excelente resposta, muito útil!"
        )
        
        self.assertTrue(feedback_result, "Falha ao salvar feedback na integração end-to-end")
        
        # 4. Verificar se o feedback foi registrado corretamente
        all_feedback = self.feedback_manager.get_all_feedback()
        latest_feedback = next((f for f in all_feedback if f["query"] == query), None)
        
        self.assertIsNotNone(latest_feedback, "Feedback não encontrado na integração end-to-end")
        self.assertEqual(latest_feedback["response"], rag_results["response"], "Resposta incorreta no feedback")
        self.assertTrue(latest_feedback["is_helpful"], "Status de utilidade incorreto no feedback")
        self.assertEqual(latest_feedback["comments"], "Excelente resposta, muito útil!", "Comentários incorretos no feedback")
        
        logger.info("Teste de integração end-to-end concluído com sucesso")

if __name__ == "__main__":
    unittest.main()
