from typing import Dict, Any, Optional
import math

"""
Detector per calcolare lo shift rotazionale da applicare in Revit.
Calcola l'angolo di rotazione necessario per allineare la nuvola al nord reale.
"""

class RevitShiftDetector:
    """Rileva e calcola lo shift di rotazione per Revit."""
    
    def detect_rotation_shift(self, bounds: Dict[str, Any], 
                            georeferencing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calcola lo shift rotazionale da applicare in Revit.
        
        Args:
            bounds: Dizionario con bounds della nuvola (x, y, z con min/max)
            georeferencing: Dizionario con info georeferenziazione (EPSG, CRS, ecc.)
            
        Returns:
            Dizionario con info rotazione e shift da applicare in Revit
        """
        if not bounds or 'x' not in bounds or 'y' not in bounds:
            return None
        
        try:
            x_bounds = bounds['x']
            y_bounds = bounds['y']
            
            # Calcola i quattro vertici della bounding box nel piano X-Y
            x_min = x_bounds['min']
            x_max = x_bounds['max']
            y_min = y_bounds['min']
            y_max = y_bounds['max']
            
            # Centroide della bounding box
            center_x = (x_min + x_max) / 2
            center_y = (y_min + y_max) / 2
            
            # Dimensioni della bounding box
            width_x = x_max - x_min  # Estensione in X
            height_y = y_max - y_min  # Estensione in Y
            
            # Calcola l'azimut della bounding box (angolo rispetto al nord)
            # L'azimut è misurato da nord (0°) in senso orario
            azimut_rad = math.atan2(width_x, height_y)
            azimut_deg = math.degrees(azimut_rad)
            
            # Normalizza azimut a 0-360°
            azimut_normalized = azimut_deg % 360
            
            # Lo SHIFT per Revit è l'angolo che bisogna ruotare per arrivare a 0°
            # Se azimut = 45°, bisogna ruotare di -45° (rotazione in senso antiorario)
            rotation_shift = -azimut_normalized
            
            # Se il valore è negativo, convertilo a positivo (0-360)
            if rotation_shift < 0:
                rotation_shift += 360
            
            # Calcola l'angolo della diagonale principale
            diagonal_angle_rad = math.atan2(height_y, width_x)
            diagonal_angle_deg = math.degrees(diagonal_angle_rad)
            
            # Rapporto aspetto della bounding box
            aspect_ratio = width_x / height_y if height_y > 0 else 0
            
            # Determina se la nuvola è più larga che alta (landscape) o vice versa
            orientation = "landscape" if width_x > height_y else "portrait"
            
            return {
                "revit_rotation_shift": {
                    "shift_degrees": round(rotation_shift, 2),
                    "description": f"Ruota di {round(rotation_shift, 2)}° in Revit per allineare a 0°",
                    "direction": "clockwise" if rotation_shift >= 0 else "counter-clockwise"
                },
                "bounding_box_analysis": {
                    "center": {
                        "x": round(center_x, 4),
                        "y": round(center_y, 4)
                    },
                    "dimensions": {
                        "width_x": round(width_x, 2),
                        "height_y": round(height_y, 2)
                    },
                    "aspect_ratio": round(aspect_ratio, 2),
                    "orientation": orientation
                },
                "azimuth_analysis": {
                    "azimut_degrees": round(azimut_normalized, 2),
                    "azimut_radians": round(azimut_rad, 4),
                    "diagonal_angle_degrees": round(diagonal_angle_deg, 2),
                    "description": f"La nuvola è orientata a {round(azimut_normalized, 2)}° dal nord reale"
                },
                "georeferencing_info": {
                    "epsg_code": georeferencing.get("epsg_code"),
                    "georeferenced": georeferencing.get("georeferenced"),
                    "has_gps_time": georeferencing.get("has_gps_time")
                }
            }
        
        except Exception as e:
            return {
                "error": f"Errore nel calcolo dello shift: {str(e)}",
                "shift_degrees": None
            }
