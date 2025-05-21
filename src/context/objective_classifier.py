"""
Módulo para classificação automática de objetivos com base na pergunta do usuário.

Este módulo implementa um classificador que analisa o texto da pergunta do usuário
e identifica automaticamente o objetivo implícito (explorar, validar hipótese, pedir insight).
"""
import os
import logging
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import openai
from openai import OpenAI
from src.utils.openai_safe import create_safe_openai_client

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ObjectiveClassifier:
    """
    Classificador de objetivos baseado em embeddings e similaridade semântica.
    
    Este classificador utiliza a API OpenAI para gerar embeddings de texto e
    calcular a similaridade entre a pergunta do usuário e exemplos de cada objetivo.
    """
    
    # Constantes para os tipos de objetivos
    OBJECTIVE_EXPLORE = "explore"
    OBJECTIVE_VALIDATE = "validate"
    OBJECTIVE_INSIGHT = "insight"
    
    # Mapeamento de objetivos para IDs no sistema
    OBJECTIVE_MAPPING = {
        OBJECTIVE_EXPLORE: "obj_explore",
        OBJECTIVE_VALIDATE: "obj_validate",
        OBJECTIVE_INSIGHT: "obj_insight"
    }
    
    # Mapeamento inverso de IDs para objetivos
    OBJECTIVE_ID_MAPPING = {v: k for k, v in OBJECTIVE_MAPPING.items()}
    
    def __init__(self, api_key: Optional[str] = None, confidence_threshold: float = 0.75):
        """
        Inicializa o classificador de objetivos.
        
        Args:
            api_key: Chave da API OpenAI (opcional, usa variável de ambiente se não fornecida)
            confidence_threshold: Limiar de confiança para aceitação automática (0.0 a 1.0)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("API key não fornecida para o classificador de objetivos")
            
        # Usar o método seguro para criar o cliente OpenAI
        self.client = create_safe_openai_client(api_key=self.api_key)
        self.confidence_threshold = confidence_threshold
        self.examples = self._load_examples()
        self.example_embeddings = self._precompute_embeddings()
        
    def _load_examples(self) -> Dict[str, List[str]]:
        """
        Carrega exemplos de perguntas para cada objetivo.
        
        Returns:
            Dicionário com listas de exemplos para cada objetivo
        """
        # Exemplos de perguntas para cada objetivo
        examples = {
            self.OBJECTIVE_EXPLORE: [
                "Quais são os principais problemas que os usuários enfrentam com a home do app?",
                "O que descobrimos sobre o comportamento dos usuários na home?",
                "Quais foram as principais descobertas da pesquisa com usuários do mês passado sobre a home?",
                "Que informações temos sobre o tempo médio que os usuários passam na home do app?",
                "Quais são os principais pontos de atrito identificados no fluxo da home?",
                "O que sabemos sobre as preferências dos nossos usuários em relação à organização da home?",
                "Quais funcionalidades da home foram mais mencionadas nas entrevistas com usuários?",
                "Que dados temos sobre a taxa de interação com os elementos da home?",
                "Quais são os componentes mais utilizados pelos nossos usuários na home do app?",
                "O que descobrimos sobre as necessidades dos usuários de cada perfil ao acessar a home?"
            ],
            self.OBJECTIVE_VALIDATE: [
                "Nossa hipótese é que usuários preferem uma home com menos elementos. Os dados de uso confirmam isso?",
                "Acreditamos que o tempo de carregamento da home está afetando a retenção. Isso é verdade?",
                "Nossa suposição é que usuários de diferentes segmentos precisam de homes personalizadas. Os dados confirmam?",
                "Temos a hipótese que destacar ações recentes na home tem melhor conversão. Isso se confirma?",
                "Acreditamos que usuários mais jovens preferem uma home mais visual. Isso é verdade?",
                "Nossa hipótese é que o novo layout da home reduz o tempo de busca por informações. Os dados suportam isso?",
                "Suspeitamos que usuários premium interagem mais com a seção de análises na home. Isso se confirma?",
                "Temos a teoria que notificações personalizadas na home aumentam o engajamento. Os dados validam isso?",
                "Acreditamos que o tutorial interativo da home melhora a retenção. Isso é verdade?",
                "Nossa hipótese é que usuários passam mais tempo na home após a reorganização. Os dados confirmam?"
            ],
            self.OBJECTIVE_INSIGHT: [
                "Quais insights podemos extrair do comportamento dos usuários na nova home do app?",
                "O que os dados de uso nos dizem sobre como melhorar a experiência da home?",
                "Que padrões emergentes podemos identificar no comportamento dos usuários na home do app?",
                "Quais insights os dados de abandono a partir da home nos oferecem para otimização?",
                "O que podemos aprender com a forma como os usuários navegam entre as seções da home?",
                "Que conclusões podemos tirar sobre a eficácia da organização atual da home?",
                "Quais insights os dados de uso nos revelam sobre preferências de design da home?",
                "O que os padrões de busca dos usuários a partir da home nos dizem sobre suas necessidades?",
                "Que aprendizados podemos extrair da análise de jornada do usuário na home?",
                "Quais insights os dados de retenção nos oferecem para melhorar a home do app?"
            ]
        }
        
        return examples
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Obtém o embedding de um texto usando a API OpenAI.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding do texto
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erro ao obter embedding: {str(e)}")
            # Retornar um embedding vazio em caso de erro
            return [0.0] * 1536  # Dimensão padrão dos embeddings da OpenAI
    
    def _precompute_embeddings(self) -> Dict[str, List[List[float]]]:
        """
        Pré-computa embeddings para todos os exemplos.
        
        Returns:
            Dicionário com listas de embeddings para cada objetivo
        """
        embeddings = {}
        
        for objective, examples in self.examples.items():
            embeddings[objective] = []
            for example in examples:
                embedding = self._get_embedding(example)
                embeddings[objective].append(embedding)
        
        return embeddings
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        Calcula a similaridade de cosseno entre dois vetores.
        
        Args:
            a: Primeiro vetor
            b: Segundo vetor
            
        Returns:
            Similaridade de cosseno (entre -1 e 1)
        """
        a = np.array(a)
        b = np.array(b)
        
        # Evitar divisão por zero
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return np.dot(a, b) / (norm_a * norm_b)
    
    def classify_question(self, question: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Classifica uma pergunta para identificar o objetivo implícito.
        
        Args:
            question: Texto da pergunta do usuário
            
        Returns:
            Tupla com (objetivo_identificado, nível_de_confiança, scores_por_objetivo)
        """
        # Obter embedding da pergunta
        question_embedding = self._get_embedding(question)
        
        # Calcular similaridade com cada exemplo
        similarities = {}
        
        for objective, embeddings in self.example_embeddings.items():
            objective_similarities = []
            for embedding in embeddings:
                similarity = self._cosine_similarity(question_embedding, embedding)
                objective_similarities.append(similarity)
            
            # Usar a média das 3 maiores similaridades para cada objetivo
            objective_similarities.sort(reverse=True)
            top_similarities = objective_similarities[:3]
            similarities[objective] = sum(top_similarities) / len(top_similarities)
        
        # Identificar o objetivo com maior similaridade
        best_objective = max(similarities, key=similarities.get)
        confidence = similarities[best_objective]
        
        # Normalizar as similaridades para somar 1.0 (para interpretação como probabilidades)
        total = sum(similarities.values())
        normalized_similarities = {obj: sim/total for obj, sim in similarities.items()}
        
        logger.info(f"Pergunta classificada como '{best_objective}' com confiança {confidence:.4f}")
        
        return best_objective, confidence, normalized_similarities
    
    def get_objective_id(self, objective: str) -> str:
        """
        Converte o tipo de objetivo para o ID usado no sistema.
        
        Args:
            objective: Tipo de objetivo (explore, validate, insight)
            
        Returns:
            ID do objetivo no sistema
        """
        return self.OBJECTIVE_MAPPING.get(objective, self.OBJECTIVE_MAPPING[self.OBJECTIVE_EXPLORE])
    
    def get_objective_from_id(self, objective_id: str) -> str:
        """
        Converte o ID do objetivo para o tipo usado pelo classificador.
        
        Args:
            objective_id: ID do objetivo no sistema
            
        Returns:
            Tipo de objetivo (explore, validate, insight)
        """
        return self.OBJECTIVE_ID_MAPPING.get(objective_id, self.OBJECTIVE_EXPLORE)
    
    def get_confidence_threshold(self) -> float:
        """
        Retorna o limiar de confiança para aceitação automática.
        
        Returns:
            Valor do limiar de confiança (entre 0.0 e 1.0)
        """
        return self.confidence_threshold
    
    def should_accept_automatically(self, confidence: float) -> bool:
        """
        Verifica se o nível de confiança é suficiente para aceitação automática.
        
        Args:
            confidence: Nível de confiança da classificação
            
        Returns:
            True se a confiança for suficiente para aceitação automática
        """
        return confidence >= self.confidence_threshold
    
    def get_objective_description(self, objective: str) -> str:
        """
        Retorna uma descrição amigável do objetivo.
        
        Args:
            objective: Tipo de objetivo (explore, validate, insight)
            
        Returns:
            Descrição do objetivo
        """
        descriptions = {
            self.OBJECTIVE_EXPLORE: "Explorar o que já foi descoberto",
            self.OBJECTIVE_VALIDATE: "Validar hipótese",
            self.OBJECTIVE_INSIGHT: "Pedir insight"
        }
        
        return descriptions.get(objective, "Objetivo desconhecido")
