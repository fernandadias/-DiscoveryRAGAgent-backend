import os
import logging
import json
from datetime import datetime
from src.ingest.document_ingestor import DocumentIngestor

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reindex_all_documents():
    """
    Script para reindexar todos os documentos no Weaviate
    """
    try:
        # Inicializar o DocumentIngestor
        ingestor = DocumentIngestor()
        
        # Definir diretório de dados com caminho absoluto explícito
        data_dir = "/home/ubuntu/projects/backend/data/raw"
        
        # Verificar se o diretório existe
        if not os.path.exists(data_dir):
            logger.error(f"Diretório de dados não encontrado: {data_dir}")
            return False
        
        logger.info(f"Iniciando reindexação de documentos do diretório: {data_dir}")
        
        # Listar arquivos no diretório para verificação
        files = os.listdir(data_dir)
        logger.info(f"Encontrados {len(files)} arquivos no diretório: {', '.join(files[:5])}...")
        
        # Reindexar todos os documentos
        stats = ingestor.reindex_all_documents(data_dir)
        
        # Salvar estatísticas em um arquivo
        stats_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reindex_stats.json")
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": str(datetime.now()),
                "stats": stats
            }, f, indent=2)
        
        logger.info(f"Reindexação concluída. Estatísticas: {stats}")
        logger.info(f"Estatísticas salvas em: {stats_file}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao reindexar documentos: {str(e)}")
        return False

if __name__ == "__main__":
    reindex_all_documents()
