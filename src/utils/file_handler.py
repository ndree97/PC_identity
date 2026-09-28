import json
from pathlib import Path
from typing import Dict, Any

class FileHandler:
    """Gestisce salvataggio e caricamento file."""
    
    @staticmethod
    def save_json(data: Dict[str, Any], output_path: str) -> Path:
        """Salva dati in JSON con creazione cartella."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Carica dati da JSON."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)