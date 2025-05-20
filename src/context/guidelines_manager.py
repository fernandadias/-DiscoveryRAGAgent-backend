import os
from typing import Dict, List, Any
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GuidelinesManager:
    def __init__(self, guidelines_dir: str = "data/guidelines"):
        self.guidelines_dir = guidelines_dir
        self.guidelines = {}
        self.load_guidelines()
    
    def load_guidelines(self):
        """Carrega todas as diretrizes dos arquivos MD"""
        logger.info(f"Carregando diretrizes do diretório: {self.guidelines_dir}")
        
        if not os.path.exists(self.guidelines_dir):
            logger.warning(f"Diretório de diretrizes não encontrado. Criando: {self.guidelines_dir}")
            os.makedirs(self.guidelines_dir, exist_ok=True)
            
            # Criar arquivo de exemplo se o diretório estiver vazio
            example_file = os.path.join(self.guidelines_dir, "diretrizes_design.md")
            if not os.listdir(self.guidelines_dir):
                with open(example_file, "w", encoding="utf-8") as f:
                    f.write("# Diretrizes de Design\n\nEste é um arquivo de exemplo para diretrizes de design.")
        
        # Limpar diretrizes existentes antes de recarregar
        self.guidelines = {}
        
        # Verificar se há arquivos no diretório
        files = [f for f in os.listdir(self.guidelines_dir) if f.endswith(".md")]
        if not files:
            logger.warning(f"Nenhum arquivo .md encontrado no diretório: {self.guidelines_dir}")
            
            # Tentar carregar dos arquivos de upload como fallback
            upload_dir = "upload"
            if os.path.exists(upload_dir):
                logger.info(f"Tentando carregar diretrizes do diretório de upload: {upload_dir}")
                for filename in os.listdir(upload_dir):
                    if filename.endswith(".md") and "diretrizes" in filename.lower():
                        src_path = os.path.join(upload_dir, filename)
                        dst_path = os.path.join(self.guidelines_dir, filename)
                        
                        # Copiar arquivo para o diretório de diretrizes
                        with open(src_path, "r", encoding="utf-8") as src_file:
                            content = src_file.read()
                            
                        with open(dst_path, "w", encoding="utf-8") as dst_file:
                            dst_file.write(content)
                            
                        logger.info(f"Copiado arquivo de diretrizes: {filename}")
        
        # Carregar todos os arquivos .md do diretório
        for filename in os.listdir(self.guidelines_dir):
            if filename.endswith(".md"):
                guideline_id = filename.replace(".md", "")
                file_path = os.path.join(self.guidelines_dir, filename)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Extrair título do arquivo MD (primeira linha com #)
                    title = ""
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line.replace("# ", "").strip()
                            break
                    
                    if not title:
                        title = guideline_id.replace("_", " ").title()
                    
                    self.guidelines[guideline_id] = {
                        "id": guideline_id,
                        "title": title,
                        "content": content
                    }
                    
                    logger.info(f"Carregada diretriz: {title} (ID: {guideline_id})")
                except Exception as e:
                    logger.error(f"Erro ao carregar diretriz {filename}: {str(e)}")
        
        logger.info(f"Total de diretrizes carregadas: {len(self.guidelines)}")
    
    def get_all_guidelines_content(self) -> str:
        """Retorna o conteúdo de todas as diretrizes concatenado"""
        if not self.guidelines:
            logger.warning("Nenhuma diretriz encontrada. Tentando recarregar...")
            self.load_guidelines()
            
        all_content = []
        
        # Ordenar por nome de arquivo para garantir ordem consistente
        sorted_guidelines = sorted(self.guidelines.items(), key=lambda x: x[0])
        
        for _, guideline in sorted_guidelines:
            all_content.append(guideline["content"])
            
        return "\n\n".join(all_content)
        
    def get_all_guidelines(self) -> List[Dict[str, Any]]:
        """Retorna lista de todas as diretrizes disponíveis com conteúdo completo"""
        if not self.guidelines:
            logger.warning("Nenhuma diretriz encontrada. Tentando recarregar...")
            self.load_guidelines()
            
        return [
            {
                "id": guide_id, 
                "title": guide["title"],
                "content": guide["content"]
            } 
            for guide_id, guide in self.guidelines.items()
        ]
        
    def get_guideline_content(self, guideline_id: str) -> str:
        """Retorna o conteúdo de uma diretriz específica"""
        if guideline_id not in self.guidelines:
            logger.warning(f"Diretriz não encontrada: {guideline_id}. Tentando recarregar...")
            self.load_guidelines()
            
            if guideline_id not in self.guidelines:
                logger.error(f"Diretriz não encontrada após recarga: {guideline_id}")
                return ""
                
        return self.guidelines[guideline_id]["content"]
