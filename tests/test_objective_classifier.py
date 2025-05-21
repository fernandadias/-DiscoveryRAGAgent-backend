"""
Módulo para testes do classificador de objetivos.

Este módulo implementa testes unitários para o classificador de objetivos,
verificando a precisão da classificação em diferentes cenários.
"""
import unittest
import os
from src.context.objective_classifier import ObjectiveClassifier

class TestObjectiveClassifier(unittest.TestCase):
    """Testes para o classificador de objetivos."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Usar uma chave de API de teste ou mock
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.classifier = ObjectiveClassifier(api_key=self.api_key)
    
    def test_explore_classification(self):
        """Testa a classificação de perguntas de exploração."""
        questions = [
            "Quais são os principais problemas que os usuários enfrentam com a home do app?",
            "O que descobrimos sobre o comportamento dos usuários na home?",
            "Que informações temos sobre o tempo médio que os usuários passam na home do app?"
        ]
        
        for question in questions:
            objective, confidence, _ = self.classifier.classify_question(question)
            self.assertEqual(objective, ObjectiveClassifier.OBJECTIVE_EXPLORE)
            self.assertGreaterEqual(confidence, 0.5)
    
    def test_validate_classification(self):
        """Testa a classificação de perguntas de validação de hipótese."""
        questions = [
            "Nossa hipótese é que usuários preferem uma home com menos elementos. Os dados de uso confirmam isso?",
            "Acreditamos que o tempo de carregamento da home está afetando a retenção. Isso é verdade?",
            "Temos a hipótese que destacar ações recentes na home tem melhor conversão. Isso se confirma?"
        ]
        
        for question in questions:
            objective, confidence, _ = self.classifier.classify_question(question)
            self.assertEqual(objective, ObjectiveClassifier.OBJECTIVE_VALIDATE)
            self.assertGreaterEqual(confidence, 0.5)
    
    def test_insight_classification(self):
        """Testa a classificação de perguntas de pedido de insight."""
        questions = [
            "Quais insights podemos extrair do comportamento dos usuários na nova home do app?",
            "O que os dados de uso nos dizem sobre como melhorar a experiência da home?",
            "Que padrões emergentes podemos identificar no comportamento dos usuários na home do app?"
        ]
        
        for question in questions:
            objective, confidence, _ = self.classifier.classify_question(question)
            self.assertEqual(objective, ObjectiveClassifier.OBJECTIVE_INSIGHT)
            self.assertGreaterEqual(confidence, 0.5)
    
    def test_ambiguous_questions(self):
        """Testa a classificação de perguntas ambíguas."""
        questions = [
            "Como está a home do app?",
            "Preciso de informações sobre a home",
            "A home do app está funcionando bem?"
        ]
        
        for question in questions:
            objective, confidence, _ = self.classifier.classify_question(question)
            # Não testamos qual objetivo foi escolhido, apenas que a confiança é menor
            self.assertLessEqual(confidence, 0.8)
    
    def test_confidence_threshold(self):
        """Testa o limiar de confiança para aceitação automática."""
        threshold = self.classifier.get_confidence_threshold()
        self.assertGreaterEqual(threshold, 0.0)
        self.assertLessEqual(threshold, 1.0)
        
        # Teste com confiança alta
        self.assertTrue(self.classifier.should_accept_automatically(threshold + 0.1))
        
        # Teste com confiança baixa
        self.assertFalse(self.classifier.should_accept_automatically(threshold - 0.1))
    
    def test_objective_mapping(self):
        """Testa o mapeamento entre tipos de objetivo e IDs do sistema."""
        for objective in [
            ObjectiveClassifier.OBJECTIVE_EXPLORE,
            ObjectiveClassifier.OBJECTIVE_VALIDATE,
            ObjectiveClassifier.OBJECTIVE_INSIGHT
        ]:
            objective_id = self.classifier.get_objective_id(objective)
            self.assertIsNotNone(objective_id)
            
            # Teste de conversão bidirecional
            converted_objective = self.classifier.get_objective_from_id(objective_id)
            self.assertEqual(converted_objective, objective)
    
    def test_objective_description(self):
        """Testa as descrições dos objetivos."""
        for objective in [
            ObjectiveClassifier.OBJECTIVE_EXPLORE,
            ObjectiveClassifier.OBJECTIVE_VALIDATE,
            ObjectiveClassifier.OBJECTIVE_INSIGHT
        ]:
            description = self.classifier.get_objective_description(objective)
            self.assertIsNotNone(description)
            self.assertNotEqual(description, "Objetivo desconhecido")

if __name__ == "__main__":
    unittest.main()
