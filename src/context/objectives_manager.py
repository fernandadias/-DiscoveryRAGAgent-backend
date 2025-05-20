import os
import markdown
from typing import Dict, List, Optional

class ObjectivesManager:
    def __init__(self, objectives_dir: str = "data/objectives"):
        self.objectives_dir = objectives_dir
        self.objectives = {}
        self.load_objectives()
    
    def load_objectives(self):
        """Carrega todos os objetivos dos arquivos MD"""
        if not os.path.exists(self.objectives_dir):
            os.makedirs(self.objectives_dir, exist_ok=True)
            
        for filename in os.listdir(self.objectives_dir):
            if filename.endswith(".md"):
                objective_id = filename.replace(".md", "")
                file_path = os.path.join(self.objectives_dir, filename)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Extrair título do arquivo MD (primeira linha com #)
                title = ""
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line.replace("# ", "").strip()
                        break
                
                self.objectives[objective_id] = {
                    "id": objective_id,
                    "title": title,
                    "content": content
                }
    
    def get_all_objectives(self) -> List[Dict]:
        """Retorna lista de todos os objetivos disponíveis"""
        return [
            {"id": obj_id, "title": obj["title"]} 
            for obj_id, obj in self.objectives.items()
        ]
    
    def get_objective_content(self, objective_id: str) -> Optional[str]:
        """Retorna o conteúdo completo de um objetivo específico"""
        objective = self.objectives.get(objective_id)
        return objective["content"] if objective else None
    
    def get_default_objective_id(self) -> str:
        """Retorna o ID do objetivo padrão (Sobre a discovery)"""
        # Procura pelo objetivo com "discovery" no título
        for obj_id, obj in self.objectives.items():
            if "discovery" in obj["title"].lower():
                return obj_id
        
        # Fallback para o primeiro objetivo se não encontrar
        return list(self.objectives.keys())[0] if self.objectives else ""
