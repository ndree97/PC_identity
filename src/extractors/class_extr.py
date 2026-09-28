from typing import Dict, Optional
from src.utils.config_load import ConfigLoader


class ClassificationExtractor:
    """Estrae informazioni sulla classificazione."""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.classification_map = config_loader.get_classification_map()["classifications"]
    
    def extract_classification_info(self, las) -> Optional[Dict[str, int]]:
        """Estrae distribuzione classificazioni."""
        try:
            if hasattr(las, 'classification'):
                class_counts = {}
                unique_classes = set(las.classification)
                
                for cls in sorted(unique_classes):
                    count = (las.classification == cls).sum()
                    class_name = self.classification_map.get(
                        str(cls), f"Class_{cls}"
                    )
                    class_counts[class_name] = int(count)
                
                return class_counts if class_counts else None
        except:
            pass
        return None
