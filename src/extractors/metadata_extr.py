from pathlib import Path
from typing import Dict, Any, Optional
import laspy

class MetadataExtractor:
    """Estrae metadati generali dal file LAS."""
    
    @staticmethod
    def extract_file_info(las_path: Path) -> Dict[str, Any]:
        """Estrae informazioni sul file."""
        try:
            file_size = las_path.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            elif file_size < 1024 * 1024 * 1024:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            else:
                size_str = f"{file_size/(1024*1024*1024):.1f} GB"
        except:
            file_size = 0
            size_str = "N/D"

        return {
            "filename": las_path.name,
            "filepath": str(las_path.absolute()),
            "file_size_bytes": file_size,
            "file_size_formatted": size_str,
            "file_size_mb": round(file_size / (1024 * 1024), 2) if file_size > 0 else 0,
        }
    
    @staticmethod
    def extract_header_info(header) -> Dict[str, Any]:
        """Estrae informazioni dall'header LAS."""
        try:
            return {
                "las_version": f"{header.version.major}.{header.version.minor}",
                "point_format": header.point_format.id,
                "point_count": header.point_count,
            }
        except Exception as e:
            raise ValueError(f"Errore nell'estrazione header: {e}")