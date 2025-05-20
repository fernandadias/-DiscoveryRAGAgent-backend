"""
Módulo para gerenciar o feedback do usuário na aplicação Streamlit

Este módulo fornece funções para coletar, armazenar e analisar feedback do usuário.
"""

import os
import json
import datetime
import pandas as pd
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeedbackManager:
    """
    Classe para gerenciar o feedback do usuário.
    """
    
    def __init__(self, feedback_dir=None):
        """
        Inicializa o gerenciador de feedback.
        
        Args:
            feedback_dir (str): Diretório para armazenar os feedbacks
        """
        if feedback_dir is None:
            # Usar diretório padrão se não for especificado
            self.feedback_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data',
                'feedback'
            )
        else:
            self.feedback_dir = feedback_dir
        
        # Garantir que o diretório exista
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        # Caminho para o arquivo de feedback
        self.feedback_file = os.path.join(self.feedback_dir, 'user_feedback.json')
        
        # Inicializar arquivo de feedback se não existir
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def save_feedback(self, query, response, sources, is_helpful, comments=None):
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
        try:
            # Criar objeto de feedback
            feedback = {
                'timestamp': datetime.datetime.now().isoformat(),
                'query': query,
                'response': response,
                'sources': sources,
                'is_helpful': is_helpful,
                'comments': comments or ''
            }
            
            # Carregar feedbacks existentes
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                feedbacks = []
            
            # Adicionar novo feedback
            feedbacks.append(feedback)
            
            # Salvar feedbacks atualizados
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Feedback salvo com sucesso: {is_helpful}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar feedback: {e}")
            return False
    
    def get_all_feedback(self):
        """
        Obtém todos os feedbacks.
        
        Returns:
            list: Lista de feedbacks
        """
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao obter feedbacks: {e}")
            return []
    
    def get_feedback_stats(self):
        """
        Obtém estatísticas de feedback.
        
        Returns:
            dict: Estatísticas de feedback
        """
        feedbacks = self.get_all_feedback()
        
        if not feedbacks:
            return {
                'total': 0,
                'helpful_count': 0,
                'helpful_percentage': 0,
                'unhelpful_count': 0,
                'unhelpful_percentage': 0,
                'with_comments_count': 0,
                'with_comments_percentage': 0
            }
        
        total = len(feedbacks)
        helpful_count = sum(1 for f in feedbacks if f.get('is_helpful', False))
        with_comments_count = sum(1 for f in feedbacks if f.get('comments', '').strip())
        
        return {
            'total': total,
            'helpful_count': helpful_count,
            'helpful_percentage': (helpful_count / total) * 100 if total > 0 else 0,
            'unhelpful_count': total - helpful_count,
            'unhelpful_percentage': ((total - helpful_count) / total) * 100 if total > 0 else 0,
            'with_comments_count': with_comments_count,
            'with_comments_percentage': (with_comments_count / total) * 100 if total > 0 else 0
        }
    
    def export_feedback_to_csv(self, output_path=None):
        """
        Exporta os feedbacks para um arquivo CSV.
        
        Args:
            output_path (str): Caminho para o arquivo CSV de saída
            
        Returns:
            str: Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        try:
            feedbacks = self.get_all_feedback()
            
            if not feedbacks:
                logger.warning("Nenhum feedback para exportar")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(feedbacks)
            
            # Definir caminho de saída se não for especificado
            if output_path is None:
                output_path = os.path.join(self.feedback_dir, f'feedback_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            
            # Exportar para CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Feedbacks exportados para {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao exportar feedbacks: {e}")
            return None

# Função para criar uma instância do gerenciador de feedback
def create_feedback_manager(feedback_dir=None):
    """
    Cria uma instância do gerenciador de feedback.
    
    Args:
        feedback_dir (str): Diretório para armazenar os feedbacks
        
    Returns:
        FeedbackManager: Instância do gerenciador de feedback
    """
    return FeedbackManager(feedback_dir)
