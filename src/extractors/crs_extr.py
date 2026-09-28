from typing import Dict, Any, List

class CoordinateExtractor:
    """Estrae informazioni coordinate e sistema di riferimento."""
    
    @staticmethod
    def extract_coordinate_system(header) -> Dict[str, Any]:
        """Estrae scale, offset e bounds."""
        return {
            "scale": [
                float(header.scales[0]),
                float(header.scales[1]),
                float(header.scales[2])
            ],
            "offset": [
                float(header.offsets[0]),
                float(header.offsets[1]),
                float(header.offsets[2])
            ],
            "bounds": {
                "x": {"min": float(header.x_min), "max": float(header.x_max)},
                "y": {"min": float(header.y_min), "max": float(header.y_max)},
                "z": {"min": float(header.z_min), "max": float(header.z_max)},
            },
            "spatial_extent": {
                "x_range": float(header.x_max - header.x_min),
                "y_range": float(header.y_max - header.y_min),
                "z_range": float(header.z_max - header.z_min),
            }
        }
