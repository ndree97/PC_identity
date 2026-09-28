import json
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """Carica e gestisce file di configurazione JSON."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Directory configurazione non trovata: {config_dir}")
        
        self._configs = {}
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Carica un file di configurazione JSON."""
        if config_name in self._configs:
            return self._configs[config_name]
        
        config_path = self.config_dir / f"{config_name}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"File configurazione non trovato: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._configs[config_name] = config
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Errore parsing JSON {config_path}: {e}")
    
    def get_sensor_database(self) -> Dict[str, Any]:
        """Ritorna il database dei sensori."""
        return self.load_config("sensor_db")
    
    def get_software_signatures(self) -> Dict[str, Any]:
        """Ritorna le firme software."""
        return self.load_config("sw_sign")
    
    def get_classification_map(self) -> Dict[str, str]:
        """Ritorna la mappa classificazioni."""
        return self.load_config("class_map")
    
    def get_post_processing_signatures(self) -> Dict[str, Any]:
        """Ritorna le firme post-processing."""
        return self.load_config("post_proc_sign")