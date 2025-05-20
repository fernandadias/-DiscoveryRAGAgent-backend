"""
PDF Extractor Module

Este módulo contém funções para extrair texto de documentos PDF utilizando poppler-utils.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    Extrai texto de um arquivo PDF utilizando pdftotext (poppler-utils).
    
    Args:
        pdf_path (str): Caminho para o arquivo PDF
        
    Returns:
        str: Texto extraído do PDF
    """
    if not os.path.exists(pdf_path):
        logger.error(f"Arquivo não encontrado: {pdf_path}")
        return ""
    
    logger.info(f"Extraindo texto de: {pdf_path}")
    
    # Criar um arquivo temporário para o texto extraído
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Executar pdftotext para extrair o texto
        subprocess.run(
            ['pdftotext', '-layout', pdf_path, temp_path],
            check=True,
            capture_output=True
        )
        
        # Ler o texto extraído
        with open(temp_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"Extração concluída: {len(text)} caracteres extraídos")
        return text
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao extrair texto do PDF: {e}")
        return ""
    
    finally:
        # Remover o arquivo temporário
        if os.path.exists(temp_path):
            os.remove(temp_path)

def extract_text_with_metadata(pdf_path):
    """
    Extrai texto e metadados básicos de um arquivo PDF.
    
    Args:
        pdf_path (str): Caminho para o arquivo PDF
        
    Returns:
        dict: Dicionário contendo texto e metadados
    """
    text = extract_text_from_pdf(pdf_path)
    
    # Extrair metadados básicos
    filename = os.path.basename(pdf_path)
    file_size = os.path.getsize(pdf_path)
    
    # Tentar extrair metadados adicionais com pdfinfo
    metadata = {
        'filename': filename,
        'file_size': file_size,
        'path': pdf_path,
        'char_count': len(text)
    }
    
    try:
        # Executar pdfinfo para obter metadados
        result = subprocess.run(
            ['pdfinfo', pdf_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Processar a saída do pdfinfo
        for line in result.stdout.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip().lower().replace(' ', '_')] = value.strip()
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"Não foi possível extrair metadados detalhados: {e}")
    
    return {
        'text': text,
        'metadata': metadata
    }

if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        result = extract_text_with_metadata(pdf_file)
        print(f"Metadados: {result['metadata']}")
        print(f"Primeiros 500 caracteres do texto:\n{result['text'][:500]}...")
    else:
        print("Uso: python pdf_extractor.py caminho/para/arquivo.pdf")
