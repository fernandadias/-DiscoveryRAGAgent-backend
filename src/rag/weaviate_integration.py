"""
Módulo de integração com Weaviate

Este módulo contém funções para integrar com a base vetorial Weaviate,
incluindo configuração, indexação e consulta.
"""

import os
import logging
import json
import uuid
from pathlib import Path
import weaviate
from weaviate.auth import AuthApiKey

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeaviateClient:
    """Cliente para interagir com a base vetorial Weaviate."""
    
    def __init__(self, url, api_key=None, read_only_api_key=None):
        """
        Inicializa o cliente Weaviate.
        
        Args:
            url (str): URL do endpoint REST Weaviate
            api_key (str, optional): Chave de API para acesso administrativo
            read_only_api_key (str, optional): Chave de API para acesso somente leitura
        """
        self.url = url
        self.api_key = api_key
        self.read_only_api_key = read_only_api_key
        self.client = None
        self.connect()
    
    def connect(self):
        """Estabelece conexão com o Weaviate."""
        try:
            # Configurar autenticação
            auth_config = None
            if self.api_key:
                auth_config = AuthApiKey(api_key=self.api_key)
            
            # Conectar ao Weaviate usando o construtor padrão (compatível com todas as versões)
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config
            )
            
            # Verificar conexão
            if self.client.is_ready():
                logger.info(f"Conexão estabelecida com Weaviate: {self.url}")
            else:
                logger.error(f"Falha ao conectar com Weaviate: {self.url}")
                self.client = None
                
        except Exception as e:
            logger.error(f"Erro ao conectar com Weaviate: {e}")
            self.client = None
    
    def is_connected(self):
        """Verifica se o cliente está conectado ao Weaviate."""
        return self.client is not None and self.client.is_ready()
    
    def create_schema(self, class_name="Document", properties=None):
        """
        Cria o esquema para a classe de documentos no Weaviate.
        
        Args:
            class_name (str): Nome da classe no Weaviate
            properties (list): Lista de propriedades para a classe
        
        Returns:
            bool: True se o esquema foi criado com sucesso, False caso contrário
        """
        if not self.is_connected():
            logger.error("Cliente não está conectado ao Weaviate")
            return False
        
        # Definir propriedades padrão se não forem fornecidas
        if properties is None:
            properties = [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Conteúdo textual do documento"
                },
                {
                    "name": "tipo",
                    "dataType": ["text"],
                    "description": "Tipo de documento (ex: discovery, entrevista, pesquisa)"
                },
                {
                    "name": "autor",
                    "dataType": ["text"],
                    "description": "Autor do documento"
                },
                {
                    "name": "projeto",
                    "dataType": ["text"],
                    "description": "Projeto relacionado ao documento"
                },
                {
                    "name": "data",
                    "dataType": ["date"],
                    "description": "Data de criação do documento"
                },
                {
                    "name": "fonte",
                    "dataType": ["text"],
                    "description": "Fonte do documento"
                },
                {
                    "name": "nivel_confidencialidade",
                    "dataType": ["text"],
                    "description": "Nível de confidencialidade do documento"
                },
                {
                    "name": "filename",
                    "dataType": ["text"],
                    "description": "Nome do arquivo original"
                },
                {
                    "name": "file_path",
                    "dataType": ["text"],
                    "description": "Caminho do arquivo original"
                }
            ]
        
        try:
            # Verificar se a classe já existe
            schema = self.client.schema.get()
            classes = [c['class'] for c in schema['classes']] if 'classes' in schema else []
            
            if class_name in classes:
                logger.info(f"Classe '{class_name}' já existe no Weaviate")
                return True
            
            # Configurar o esquema da classe
            class_obj = {
                "class": class_name,
                "description": "Documentos para o agente de IA de ideação e discovery de produto",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "ada",
                        "modelVersion": "002",
                        "type": "text"
                    }
                },
                "properties": properties
            }
            
            # Criar a classe
            self.client.schema.create_class(class_obj)
            
            logger.info(f"Classe '{class_name}' criada com sucesso no Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar esquema no Weaviate: {e}")
            return False
    
    def add_document(self, document, class_name="Document"):
        """
        Adiciona um documento ao Weaviate.
        
        Args:
            document (dict): Documento a ser adicionado
            class_name (str): Nome da classe no Weaviate
            
        Returns:
            str: ID do documento adicionado, ou None em caso de erro
        """
        if not self.is_connected():
            logger.error("Cliente não está conectado ao Weaviate")
            return None
        
        try:
            # Extrair texto e metadados do documento
            text = document.get('text', '')
            metadata = document.get('metadata', {})
            
            # Preparar propriedades para o Weaviate
            properties = {
                "content": text,
                "tipo": metadata.get('tipo', 'documento'),
                "filename": metadata.get('filename', ''),
                "file_path": metadata.get('path', '')
            }
            
            # Adicionar outros metadados disponíveis
            for key, value in metadata.items():
                if key not in ['tipo', 'filename', 'path']:
                    properties[key] = value
            
            # Gerar UUID baseado no conteúdo para evitar duplicatas
            doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, text[:1000]))
            
            # Adicionar documento ao Weaviate
            self.client.data_object.create(
                properties,
                class_name,
                doc_uuid
            )
            
            logger.info(f"Documento adicionado ao Weaviate com ID: {doc_uuid}")
            return doc_uuid
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documento ao Weaviate: {e}")
            return None
    
    def batch_add_documents(self, documents, class_name="Document", batch_size=100):
        """
        Adiciona múltiplos documentos ao Weaviate em lote.
        
        Args:
            documents (list): Lista de documentos a serem adicionados
            class_name (str): Nome da classe no Weaviate
            batch_size (int): Tamanho do lote para processamento
            
        Returns:
            int: Número de documentos adicionados com sucesso
        """
        if not self.is_connected():
            logger.error("Cliente não está conectado ao Weaviate")
            return 0
        
        try:
            # Iniciar o lote
            with self.client.batch as batch:
                # Configurar o tamanho do lote
                batch.batch_size = batch_size
                
                # Contador de documentos adicionados
                added_count = 0
                
                for document in documents:
                    # Extrair texto e metadados do documento
                    text = document.get('text', '')
                    metadata = document.get('metadata', {})
                    
                    # Preparar propriedades para o Weaviate
                    properties = {
                        "content": text,
                        "tipo": metadata.get('tipo', 'documento'),
                        "filename": metadata.get('filename', ''),
                        "file_path": metadata.get('path', '')
                    }
                    
                    # Adicionar outros metadados disponíveis
                    for key, value in metadata.items():
                        if key not in ['tipo', 'filename', 'path']:
                            properties[key] = value
                    
                    # Gerar UUID baseado no conteúdo para evitar duplicatas
                    doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, text[:1000]))
                    
                    # Adicionar ao lote
                    batch.add_data_object(
                        properties,
                        class_name,
                        doc_uuid
                    )
                    
                    added_count += 1
            
            logger.info(f"{added_count} documentos adicionados ao Weaviate em lote")
            return added_count
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documentos em lote ao Weaviate: {e}")
            return 0
    
    def search_documents(self, query, class_name="Document", limit=5):
        """
        Realiza uma busca semântica no Weaviate.
        
        Args:
            query (str): Consulta em linguagem natural
            class_name (str): Nome da classe no Weaviate
            limit (int): Número máximo de resultados
            
        Returns:
            list: Lista de documentos encontrados
        """
        if not self.is_connected():
            logger.error("Cliente não está conectado ao Weaviate")
            return []
        
        try:
            # Definir as propriedades a serem retornadas
            properties = ["content", "tipo", "filename", "file_path"]
            
            # Executar a consulta
            result = (
                self.client.query
                .get(class_name, properties)
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            # Extrair documentos do resultado
            documents = result['data']['Get'][class_name]
            
            logger.info(f"Busca concluída: {len(documents)} documentos encontrados")
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao realizar busca no Weaviate: {e}")
            return []

def load_processed_documents(processed_dir):
    """
    Carrega documentos processados de um diretório.
    
    Args:
        processed_dir (str): Diretório contendo documentos processados
        
    Returns:
        list: Lista de documentos processados
    """
    processed_dir = Path(processed_dir)
    
    if not processed_dir.exists() or not processed_dir.is_dir():
        logger.error(f"Diretório não encontrado: {processed_dir}")
        return []
    
    # Encontrar todos os arquivos JSON
    json_files = list(processed_dir.glob("*.json"))
    
    # Carregar cada arquivo
    documents = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                document = json.load(f)
                documents.append(document)
            
            logger.info(f"Documento carregado: {json_file}")
        except Exception as e:
            logger.error(f"Erro ao carregar documento {json_file}: {e}")
    
    logger.info(f"{len(documents)} documentos carregados de {processed_dir}")
    return documents

if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    if len(sys.argv) > 3:
        weaviate_url = sys.argv[1]
        api_key = sys.argv[2]
        processed_dir = sys.argv[3]
        
        # Conectar ao Weaviate
        client = WeaviateClient(weaviate_url, api_key)
        
        if client.is_connected():
            # Criar esquema
            client.create_schema()
            
            # Carregar documentos processados
            documents = load_processed_documents(processed_dir)
            
            # Adicionar documentos ao Weaviate
            client.batch_add_documents(documents)
    else:
        print("Uso: python weaviate_integration.py weaviate_url api_key processed_dir")
