from typing import Dict, Any, List, Optional
from src.utils.config_load import ConfigLoader

class SensorDetector:
    """Rileva il tipo di sensore dalle caratteristiche."""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.sensor_db = config_loader.get_sensor_database()["sensor_types"]
    
    def extract_sensor_info(self, las, header) -> Optional[Dict[str, Any]]:
        """Estrae informazioni sensore."""
        sensor_info = {}
        characteristics = []
        characteristics_data = {}
        
        # Analizza returns
        try:
            if hasattr(las, 'return_num') and len(las.return_num) > 0:
                max_returns = int(las.return_num.max())
                characteristics_data["max_returns"] = max_returns

                # Aggiungi caratteristiche basate sui returns
                if max_returns == 1:
                    characteristics.append("single_return")
                elif max_returns == 2:
                    characteristics.append("dual_return")
                elif max_returns >= 3:
                    characteristics.append("multi_return")
                if max_returns >= 4:
                    characteristics.append("high_return_capability")
        except:
            pass

        # Analizza intensità
        try:
            if hasattr(las, 'intensity') and len(las.intensity) > 0:
                intensity_min = float(las.intensity.min())
                intensity_max = float(las.intensity.max())
                intensity_range = intensity_max - intensity_min
                characteristics_data["intensity_range"] = intensity_range
                characteristics_data["intensity_min"] = intensity_min
                characteristics_data["intensity_max"] = intensity_max

                # Aggiungi caratteristiche basate sull'intensità
                if intensity_range >= 50000:
                    characteristics.append("full_intensity_16bit")
                elif intensity_range >= 1000:
                    characteristics.append("high_intensity_resolution")
                elif intensity_range < 100:
                    characteristics.append("low_intensity_range")

                # Intensità tipica per droni (spesso limitata)
                if intensity_max <= 255 and intensity_range < 256:
                    characteristics.append("byte_intensity")
        except:
            pass

        # Analizza RGB
        try:
            if hasattr(las, 'red') and len(las.red) > 0:
                characteristics.append("rgb_data_present")
                characteristics_data["has_rgb"] = True

                # Controlla se RGB ha valori validi
                rgb_nonzero = (las.red > 0).sum()
                if rgb_nonzero > 0:
                    characteristics.append("active_rgb_channels")
        except:
            pass

        # Analizza NIR/NIR se presente
        try:
            if hasattr(las, 'nir') and len(las.nir) > 0:
                characteristics.append("nir_data_present")
                characteristics_data["has_nir"] = True
        except:
            pass

        # Analizza scan angle (tipico per scanner aerei/drone)
        try:
            if hasattr(las, 'scan_angle') and len(las.scan_angle) > 0:
                scan_angle_range = abs(float(las.scan_angle.max()) - float(las.scan_angle.min()))
                characteristics_data["scan_angle_range"] = scan_angle_range

                if scan_angle_range > 60:
                    characteristics.append("wide_scan_angle")
                elif scan_angle_range > 30:
                    characteristics.append("moderate_scan_angle")
                else:
                    characteristics.append("narrow_scan_angle")
        except:
            pass

        # Analizza GPS time
        try:
            if hasattr(las, 'gps_time') and len(las.gps_time) > 0:
                characteristics.append("gps_time_data")
                characteristics_data["has_gps_time"] = True
        except:
            pass

        # Analizza classification data
        try:
            if hasattr(las, 'classification') and len(las.classification) > 0:
                unique_classes = set(las.classification)
                characteristics_data["classification_classes"] = list(unique_classes)
                characteristics_data["classification_count"] = len(unique_classes)

                if len(unique_classes) > 5:
                    characteristics.append("detailed_classification")
                elif len(unique_classes) > 0:
                    characteristics.append("classification_present")
        except:
            pass
        
        sensor_info["characteristics"] = characteristics
        
        # Inferenza basata su specifiche
        inferred = self._infer_from_specs(characteristics_data, header)
        if inferred:
            sensor_info["inferred_sensor_types"] = inferred
        
        return sensor_info if sensor_info else None
    
    def _infer_from_specs(self, characteristics_data: Dict[str, Any], 
                        header) -> Optional[List[Dict[str, Any]]]:
        """Inferisce tipo sensore dalle specifiche."""
        possible_sensors = []
        
        point_density = characteristics_data.get("point_density", None)
        if point_density is None and header.point_count > 0:
            spatial_volume = (header.x_max - header.x_min) * \
                           (header.y_max - header.y_min) * \
                        (header.z_max - header.z_min)
            if spatial_volume > 0:
                point_density = header.point_count / spatial_volume
        
        for sensor_type, specs in self.sensor_db.items():
            score = self._calculate_sensor_score(
                characteristics_data, specs, point_density, header
            )
            
            if score > 30:
                possible_sensors.append({
                    "sensor_type": sensor_type,
                    "confidence": score,
                    "examples": specs["examples"]
                })
        
        possible_sensors.sort(key=lambda x: x["confidence"], reverse=True)
        return possible_sensors if possible_sensors else None
    
    def _calculate_sensor_score(self, data: Dict, specs: Dict,
                            density: Optional[float], header) -> float:
        """Calcola score compatibilità sensore."""
        score = 0

        try:
            # 1. Punteggio per returns (usa typical_returns dal database)
            max_returns = data.get("max_returns", 0)
            if "typical_returns" in specs:
                target_returns = specs["typical_returns"]
                if isinstance(target_returns, list) and len(target_returns) == 2:
                    # Range: [min, max]
                    if max_returns >= target_returns[0] and max_returns <= target_returns[1]:
                        score += 30
                    elif max_returns >= target_returns[0]:
                        score += 20
                elif target_returns == max_returns:
                    score += 25

            # 2. Punteggio per intensity bits
            intensity_bits = data.get("intensity_max", 0)
            max_intensity = data.get("intensity_max", 0)
            # Calcola bits necessari per il range di intensità
            if max_intensity > 0:
                bits_needed = max_intensity.bit_length()
            else:
                bits_needed = 0

            if "intensity_bits" in specs:
                target_bits = specs["intensity_bits"]
                if bits_needed <= target_bits + 2:  # Tolleranza di 2 bits
                    score += 20
                elif target_bits == 0:  # No intensity per photogrammetry
                    if bits_needed == 0:
                        score += 25

            # 3. Punteggio per RGB
            has_rgb = data.get("has_rgb", False)
            if "has_rgb" in specs:
                if specs["has_rgb"] and has_rgb:
                    score += 15
                elif not specs["has_rgb"] and not has_rgb:
                    score += 10

            # 4. Punteggio per densità punti
            if density and "point_density" in specs:
                target_density = specs["point_density"]
                if isinstance(target_density, list) and len(target_density) == 2:
                    # Range: [min, max]
                    if density >= target_density[0] and density <= target_density[1]:
                        score += 25
                    elif density >= target_density[0]:
                        score += 15

            # 5. Punteggio per range
            z_range = 0
            if hasattr(header, 'z_max') and hasattr(header, 'z_min'):
                z_range = header.z_max - header.z_min

            if "range" in specs and z_range > 0:
                target_range = specs["range"]
                if isinstance(target_range, list) and len(target_range) == 2:
                    # Range: [min, max] in metri
                    if z_range >= target_range[0] and z_range <= target_range[1]:
                        score += 20
                    elif z_range >= target_range[0]:
                        score += 10

            # 6. Punteggio per accuracy (usando scale come proxy)
            if hasattr(header, 'scales') and len(header.scales) >= 3:
                avg_scale = sum(abs(s) for s in header.scales[:3]) / 3
                if "accuracy" in specs:
                    target_accuracy = specs["accuracy"]
                    if isinstance(target_accuracy, list) and len(target_accuracy) == 2:
                        # Confronta scale con accuracy attesa
                        expected_scale = avg_scale
                        # Logica approssimativa: scale più piccolo = migliore accuracy
                        if expected_scale <= target_accuracy[1] and expected_scale >= target_accuracy[0]:
                            score += 15
                        elif expected_scale <= target_accuracy[1]:
                            score += 10

            # 7. Punteggio per examples matching
            if hasattr(header, 'generating_software'):
                software = str(header.generating_software).lower()
                if "examples" in specs:
                    for example in specs["examples"]:
                        if any(keyword.lower() in software for keyword in example.split()):
                            score += 25  # Forte indicatore
                            break

            # 8. Punteggio per scan pattern matching
            scan_patterns_detected = []
            if "scan_angle_range" in data:
                angle_range = data["scan_angle_range"]
                if angle_range < 10:
                    scan_patterns_detected.append("narrow")
                elif angle_range > 60:
                    scan_patterns_detected.append("wide")
                else:
                    scan_patterns_detected.append("moderate")

            if "scan_pattern" in specs:
                pattern = specs["scan_pattern"]
                if pattern in scan_patterns_detected:
                    score += 10
                elif pattern == "rotating" and "moderate" in scan_patterns_detected:
                    score += 8  # UAV tipicamente moderate

        except Exception as e:
            # Se c'è un errore nel calcolo, restituisci 0
            pass

        return score