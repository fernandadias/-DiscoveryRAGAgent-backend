import os
from typing import Dict, List

class GuidelinesManager:
    def __init__(self, guidelines_dir: str = "data/guidelines"):
        self.guidelines_dir = guidelines_dir
        self.guidelines = {}
        self.load_guidelines()
    
    def load_guidelines(self):
        """Carrega todas as diretrizes dos arquivos MD"""
        if not os.path.exists(self.guidelines_dir):
            os.makedirs(self.guidelines_dir, exist_ok=True)
            
        for filename in os.listdir(self.guidelines_dir):
            if filename.endswith(".md"):
                guideline_id = filename.replace(".md", "")
                file_path = os.path.join(self.guidelines_dir, filename)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Extrair título do arquivo MD (primeira linha com #)
                title = ""
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line.replace("# ", "").strip()
                        break
                
                self.guidelines[guideline_id] = {
                    "id": guideline_id,
                    "title": title,
                    "content": content
                }
    
    def get_all_guidelines_content(self) -> str:
        """Retorna o conteúdo de todas as diretrizes concatenado"""
        all_content = []
        
        # Ordenar por nome de arquivo para garantir ordem consistente
        sorted_guidelines = sorted(self.guidelines.items(), key=lambda x: x[0])
        
        for _, guideline in sorted_guidelines:
            all_content.append(guideline["content"])
            
        return "\n\n".join(all_content)
        
    def get_all_guidelines(self) -> List[Dict]:
        """Retorna lista de todas as diretrizes disponíveis"""
        return [
            {"id": guide_id, "title": guide["title"]} 
            for guide_id, guide in self.guidelines.items()
        ]
