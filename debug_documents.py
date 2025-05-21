import os
import logging
import glob
import uuid
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simulação do banco de dados em memória
documents_db = {}

def load_real_documents():
    """Carrega os documentos reais do diretório data/raw para o banco de dados em memória"""
    try:
        raw_dir = "data/raw"
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir, exist_ok=True)
            logger.info(f"Diretório {raw_dir} criado")
            return
        
        # Listar todos os arquivos no diretório
        file_paths = []
        for ext in ['*.pdf', '*.txt', '*.md', '*.docx']:
            file_paths.extend(glob.glob(os.path.join(raw_dir, ext)))
        
        logger.info(f"Encontrados {len(file_paths)} arquivos no diretório {raw_dir}")
        
        # Adicionar cada arquivo ao banco de dados em memória
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = os.path.splitext(file_path)[1].lower()
            
            # Mapear extensão para tipo MIME
            mime_types = {
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            
            content_type = mime_types.get(file_type, 'application/octet-stream')
            
            # Gerar ID único para o documento
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path))
            
            # Adicionar ao banco de dados em memória
            documents_db[doc_id] = {
                "id": doc_id,
                "title": file_name,
                "type": content_type,
                "uploaded_at": datetime.fromtimestamp(os.path.getctime(file_path)),
                "size": file_size,
                "path": file_path
            }
            
            logger.info(f"Adicionado documento: {file_name}")
        
        logger.info(f"Total de documentos carregados: {len(documents_db)}")
    except Exception as e:
        logger.error(f"Erro ao carregar documentos reais: {str(e)}")

# Executar o carregamento
load_real_documents()

# Imprimir estatísticas
print(f"\nTotal de documentos carregados: {len(documents_db)}")
print("\nPrimeiros 5 documentos:")
for i, (doc_id, doc) in enumerate(list(documents_db.items())[:5]):
    print(f"{i+1}. {doc['title']} ({doc['size']} bytes)")

print("\nExtensões únicas:")
extensions = set([os.path.splitext(doc["title"])[1].lower() for doc in documents_db.values()])
print(extensions)

# Verificar duplicatas
titles = [doc["title"] for doc in documents_db.values()]
duplicates = set([title for title in titles if titles.count(title) > 1])
if duplicates:
    print("\nDocumentos duplicados encontrados:")
    for dup in duplicates:
        print(f"- {dup}")
else:
    print("\nNenhum documento duplicado encontrado.")
