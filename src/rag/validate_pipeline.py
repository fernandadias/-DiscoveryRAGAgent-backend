"""
Script para validar o pipeline de ingestão e busca semântica com dados reais

Este script testa a ingestão de documentos PDF e a busca semântica no Weaviate.
"""

import os
import sys
import logging
import weaviate
from weaviate.classes.init import Auth
import json
import glob
import PyPDF2
from openai import OpenAI
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        pdf_path (str): Caminho para o arquivo PDF
        
    Returns:
        str: Texto extraído do PDF
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF {pdf_path}: {e}")
        return ""

def chunk_text(text, chunk_size=1000, overlap=100):
    """
    Divide um texto em chunks menores com sobreposição.
    
    Args:
        text (str): Texto a ser dividido
        chunk_size (int): Tamanho aproximado de cada chunk em caracteres
        overlap (int): Sobreposição entre chunks em caracteres
        
    Returns:
        list: Lista de chunks de texto
    """
    if not text:
        return []
    
    # Dividir o texto em parágrafos
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # Se o parágrafo for muito grande, dividi-lo em sentenças
        if len(paragraph) > chunk_size:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= chunk_size:
                    current_chunk += sentence + " "
                else:
                    chunks.append(current_chunk.strip())
                    # Manter alguma sobreposição
                    current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
                    current_chunk += sentence + " "
        else:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
    
    # Adicionar o último chunk se não estiver vazio
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def process_pdfs(pdf_dir, output_dir):
    """
    Processa todos os PDFs em um diretório e extrai o texto.
    
    Args:
        pdf_dir (str): Diretório contendo os PDFs
        output_dir (str): Diretório para salvar os textos extraídos
        
    Returns:
        list: Lista de dicionários com informações dos documentos processados
    """
    os.makedirs(output_dir, exist_ok=True)
    
    documents = []
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        logger.info(f"Processando PDF: {filename}")
        
        # Extrair texto do PDF
        text = extract_text_from_pdf(pdf_path)
        
        if text:
            # Salvar texto extraído
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Dividir o texto em chunks menores
            chunks = chunk_text(text, chunk_size=4000, overlap=200)
            logger.info(f"Documento dividido em {len(chunks)} chunks")
            
            # Adicionar cada chunk como um documento separado
            for i, chunk in enumerate(chunks):
                doc_info = {
                    "content": chunk,
                    "tipo": "discovery",
                    "filename": filename,
                    "file_path": pdf_path,
                    "chunk_id": i
                }
                documents.append(doc_info)
            
            logger.info(f"Texto extraído e salvo em: {output_path}")
        else:
            logger.warning(f"Não foi possível extrair texto de: {filename}")
    
    return documents

def ingest_documents(weaviate_url, api_key, openai_api_key, documents):
    """
    Ingere documentos no Weaviate.
    
    Args:
        weaviate_url (str): URL do endpoint REST Weaviate
        api_key (str): Chave de API para acesso ao Weaviate
        openai_api_key (str): Chave de API da OpenAI
        documents (list): Lista de documentos a serem ingeridos
        
    Returns:
        bool: True se a ingestão foi bem-sucedida, False caso contrário
    """
    try:
        # Configurar autenticação
        auth_credentials = None
        if api_key:
            auth_credentials = Auth.api_key(api_key)
        
        # Conectar ao Weaviate
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=auth_credentials,
            headers={"X-OpenAI-Api-Key": openai_api_key}
        )
        
        # Verificar conexão
        if not client.is_ready():
            logger.error(f"Falha ao conectar com Weaviate: {weaviate_url}")
            return False
        
        logger.info(f"Conexão estabelecida com Weaviate: {weaviate_url}")
        
        # Obter a coleção Document
        try:
            collection = client.collections.get("Document")
            logger.info("Coleção Document encontrada")
            
            # Ingerir documentos
            logger.info(f"Ingerindo {len(documents)} documentos...")
            
            # Usar batch para ingestão eficiente, mas processar em lotes menores
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                logger.info(f"Processando lote {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} ({len(batch_docs)} documentos)")
                
                with collection.batch.dynamic() as batch:
                    for doc in batch_docs:
                        batch.add_object(
                            properties=doc
                        )
                
                logger.info(f"Lote {i//batch_size + 1} processado")
            
            logger.info("Documentos ingeridos com sucesso")
            return True
            
        except Exception as collection_error:
            logger.error(f"Erro ao acessar coleção Document: {collection_error}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao ingerir documentos: {e}")
        return False
    finally:
        if 'client' in locals() and client:
            client.close()

def test_semantic_search(weaviate_url, api_key, openai_api_key, query, diretrizes_path):
    """
    Testa a busca semântica no Weaviate.
    
    Args:
        weaviate_url (str): URL do endpoint REST Weaviate
        api_key (str): Chave de API para acesso ao Weaviate
        openai_api_key (str): Chave de API da OpenAI
        query (str): Consulta para busca semântica
        diretrizes_path (str): Caminho para o arquivo de diretrizes
        
    Returns:
        dict: Resultados da busca semântica
    """
    try:
        # Configurar autenticação
        auth_credentials = None
        if api_key:
            auth_credentials = Auth.api_key(api_key)
        
        # Conectar ao Weaviate
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=auth_credentials,
            headers={"X-OpenAI-Api-Key": openai_api_key}
        )
        
        # Verificar conexão
        if not client.is_ready():
            logger.error(f"Falha ao conectar com Weaviate: {weaviate_url}")
            return {"error": "Falha na conexão com Weaviate"}
        
        logger.info(f"Conexão estabelecida com Weaviate: {weaviate_url}")
        
        # Obter a coleção Document
        try:
            collection = client.collections.get("Document")
            logger.info("Coleção Document encontrada")
            
            # Realizar busca semântica
            logger.info(f"Realizando busca semântica com a consulta: '{query}'")
            
            # Corrigido para API v4
            results = collection.query.near_text(
                query=query,
                limit=3
            ).objects
            
            logger.info(f"Busca semântica retornou {len(results)} resultados")
            
            # Carregar diretrizes
            with open(diretrizes_path, 'r', encoding='utf-8') as f:
                diretrizes = f.read()
            
            # Gerar resposta com OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            
            # Preparar contexto para o prompt
            context = ""
            for i, result in enumerate(results):
                context += f"\n\nDocumento {i+1}:\n{result.properties['content'][:1000]}...\n"
            
            # Criar prompt com diretrizes e contexto
            prompt = f"""
            Você é um assistente especializado em ideação e discovery de produto.
            
            DIRETRIZES:
            {diretrizes[:2000]}...
            
            CONTEXTO DOS DOCUMENTOS:
            {context}
            
            CONSULTA DO USUÁRIO:
            {query}
            
            Com base nas diretrizes e no contexto fornecido, responda à consulta do usuário de forma clara e concisa.
            """
            
            # Gerar resposta
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em ideação e discovery de produto."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Preparar resultados
            search_results = {
                "query": query,
                "results": [
                    {
                        "content": result.properties.get("content", "")[:500] + "...",
                        "filename": result.properties.get("filename", ""),
                        "chunk_id": result.properties.get("chunk_id", "")
                    } for result in results
                ],
                "response": response.choices[0].message.content
            }
            
            return search_results
            
        except Exception as collection_error:
            logger.error(f"Erro ao acessar coleção Document: {collection_error}")
            return {"error": f"Erro ao acessar coleção: {str(collection_error)}"}
            
    except Exception as e:
        logger.error(f"Erro ao realizar busca semântica: {e}")
        return {"error": f"Erro ao realizar busca: {str(e)}"}
    finally:
        if 'client' in locals() and client:
            client.close()

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 6:
        print("Uso: python validate_pipeline.py <weaviate_url> <api_key> <openai_api_key> <pdf_dir> <diretrizes_path>")
        sys.exit(1)
    
    # Obter argumentos
    weaviate_url = sys.argv[1]
    api_key = sys.argv[2]
    openai_api_key = sys.argv[3]
    pdf_dir = sys.argv[4]
    diretrizes_path = sys.argv[5]
    
    # Processar PDFs
    output_dir = os.path.join(os.path.dirname(pdf_dir), "processed")
    documents = process_pdfs(pdf_dir, output_dir)
    
    if not documents:
        logger.error("Nenhum documento processado")
        sys.exit(1)
    
    # Ingerir documentos
    success = ingest_documents(weaviate_url, api_key, openai_api_key, documents)
    
    if not success:
        logger.error("Falha ao ingerir documentos")
        sys.exit(1)
    
    # Testar busca semântica
    queries = [
        "Quais são os principais desafios na personalização da Home?",
        "Como podemos melhorar o engajamento dos usuários na Home?",
        "Quais são as necessidades dos diferentes perfis de usuários?"
    ]
    
    results = {}
    for query in queries:
        result = test_semantic_search(weaviate_url, api_key, openai_api_key, query, diretrizes_path)
        results[query] = result
    
    # Salvar resultados
    output_file = os.path.join(output_dir, "validation_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Resultados da validação salvos em: {output_file}")
    print("Pipeline validado com sucesso!")
