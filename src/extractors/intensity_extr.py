from typing import Dict, Any, Optional
import numpy as np

class IntensityExtractor:
    """Estrae informazioni sull'intensità."""
    
    @staticmethod
    def extract_intensity_range(las) -> Optional[Dict[str, int]]:
        """Estrae range di intensità."""
        try:
            if hasattr(las, 'intensity') and len(las.intensity) > 0:
                return {
                    "min": int(las.intensity.min()),
                    "max": int(las.intensity.max()),
                    "mean": round(float(las.intensity.mean()), 2),
                    "std": round(float(las.intensity.std()), 2),
                }
        except:
            pass
        return None