from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class TemporalExtractor:
    """Estrae informazioni temporali."""
    
    @staticmethod
    def extract_gps_time(las) -> Optional[Dict[str, float]]:
        """Estrae range GPS time."""
        try:
            if hasattr(las, 'gps_time') and len(las.gps_time) > 0:
                return {
                    "min": float(las.gps_time.min()),
                    "max": float(las.gps_time.max()),
                }
        except:
            pass
        return None
    
    @staticmethod
    def extract_file_creation_date(header, las_file_path: Path) -> Optional[str]:
        """Estrae data creazione file."""
        try:
            if hasattr(header, 'creation_year') and hasattr(header, 'creation_day_of_year'):
                creation_year = header.creation_year
                creation_doy = header.creation_day_of_year
                if creation_year and creation_doy:
                    return f"{creation_year}-{str(creation_doy).zfill(3)}"
            elif hasattr(header, 'creation_datetime'):
                return str(header.creation_datetime)
        except:
            pass
        
        # Fallback: data modifica file
        try:
            mod_time = datetime.fromtimestamp(las_file_path.stat().st_mtime)
            return mod_time.isoformat()
        except:
            pass
        
        return None
