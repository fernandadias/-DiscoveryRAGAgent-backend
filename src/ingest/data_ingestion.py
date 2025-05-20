"""
Módulo de Ingestão de Dados

Este módulo contém funções para processar e preparar documentos para ingestão na base vetorial.
"""

import os
import logging
from pathlib import Path
import json
from datetime import datetime

# Importar o extrator de PDF
from .pdf_extractor import extract_text_with_metadata

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_document(file_path, output_dir=None, document_type=None):
    """
    Processa um documento para ingestão, extraindo texto e metadados.
    
    Args:
        file_path (str): Caminho para o arquivo
        output_dir (str, optional): Diretório para salvar o resultado processado
        document_type (str, optional): Tipo de documento (ex: 'research', 'interview')
        
    Returns:
        dict: Documento processado com texto e metadados
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Arquivo não encontrado: {file_path}")
        return None
    
    # Determinar o tipo de arquivo pela extensão
    file_extension = file_path.suffix.lower()
    
    # Processar com base no tipo de arquivo
    if file_extension == '.pdf':
        result = extract_text_with_metadata(str(file_path))
        text = result['text']
        metadata = result['metadata']
    else:
        logger.error(f"Tipo de arquivo não suportado: {file_extension}")
        return None
    
    # Adicionar metadados adicionais
    if document_type:
        metadata['tipo'] = document_type
    else:
        # Tentar inferir o tipo de documento pelo nome do arquivo
        filename = file_path.name.lower()
        if 'discovery' in filename:
            metadata['tipo'] = 'discovery'
        elif 'entrevista' in filename or 'interview' in filename:
            metadata['tipo'] = 'entrevista'
        elif 'pesquisa' in filename or 'research' in filename:
            metadata['tipo'] = 'pesquisa'
        else:
            metadata['tipo'] = 'documento'
    
    # Adicionar data de processamento
    metadata['data_processamento'] = datetime.now().isoformat()
    
    # Criar documento processado
    processed_document = {
        'text': text,
        'metadata': metadata
    }
    
    # Salvar o resultado se um diretório de saída for especificado
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar nome de arquivo para o documento processado
        output_filename = f"{file_path.stem}_processed.json"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_document, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Documento processado salvo em: {output_path}")
    
    return processed_document

def process_directory(input_dir, output_dir, file_types=None):
    """
    Processa todos os documentos em um diretório.
    
    Args:
        input_dir (str): Diretório contendo os documentos
        output_dir (str): Diretório para salvar os resultados processados
        file_types (list, optional): Lista de extensões de arquivo a processar
        
    Returns:
        list: Lista de documentos processados
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(f"Diretório de entrada não encontrado: {input_dir}")
        return []
    
    # Criar diretório de saída se não existir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Definir tipos de arquivo a processar
    if file_types is None:
        file_types = ['.pdf']
    
    # Encontrar todos os arquivos do tipo especificado
    files_to_process = []
    for file_type in file_types:
        files_to_process.extend(input_dir.glob(f"*{file_type}"))
    
    # Processar cada arquivo
    processed_documents = []
    for file_path in files_to_process:
        logger.info(f"Processando: {file_path}")
        processed_doc = process_document(file_path, output_dir)
        if processed_doc:
            processed_documents.append(processed_doc)
    
    logger.info(f"Processamento concluído. {len(processed_documents)} documentos processados.")
    return processed_documents

if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    if len(sys.argv) > 2:
        input_path = sys.argv[1]
        output_dir = sys.argv[2]
        
        if os.path.isdir(input_path):
            process_directory(input_path, output_dir)
        else:
            process_document(input_path, output_dir)
    else:
        print("Uso: python data_ingestion.py caminho/entrada caminho/saida")
