from pathlib import Path
from typing import Dict, Any, Optional, List
import re
from datetime import datetime

try:
    import pye57
    HAS_PYE57 = True
except ImportError:
    HAS_PYE57 = False


class E57MetadataExtractor:
    """
    Estrattore metadati per file ASTM E57 (.e57).
    Estrae metadati di scansioni multiple o singole senza caricare tutti i punti in memoria.
    """

    def __init__(self, config_loader=None, software_det=None, sensor_det=None, processing_det=None):
        self.config_loader = config_loader
        self.software_det = software_det
        self.sensor_det = sensor_det
        self.processing_det = processing_det

    def is_available(self) -> bool:
        return HAS_PYE57

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """Estrae i metadati completi da un file .e57."""
        if not HAS_PYE57:
            raise ImportError(
                "La libreria 'pye57' non è installata. "
                "Per analizzare file .e57 installala con: pip install pye57"
            )

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        file_size_bytes = file_path.stat().st_size
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        if file_size_bytes < 1024 * 1024:
            file_size_formatted = f"{file_size_bytes / 1024:.1f} KB"
        elif file_size_bytes < 1024 * 1024 * 1024:
            file_size_formatted = f"{file_size_mb:.1f} MB"
        else:
            file_size_formatted = f"{file_size_bytes / (1024 * 1024 * 1024):.2f} GB"

        e57 = pye57.E57(str(file_path))
        try:
            root = e57.root
            scan_count = e57.scan_count

            # Metadati root E57
            guid = str(root.get("guid", "")) if "guid" in root else ""
            format_version = str(root.get("formatVersion", "ASTM E57")) if "formatVersion" in root else "ASTM E57"
            coordinate_metadata = str(root.get("coordinateMetadata", "")) if "coordinateMetadata" in root else ""
            creation_date_raw = None
            if "creationDateTime" in root:
                try:
                    c_dt = root["creationDateTime"]
                    creation_date_raw = str(c_dt.get("dateTimeValue", "")) if hasattr(c_dt, "get") else str(c_dt)
                except Exception:
                    creation_date_raw = None

            # Dettaglio scansioni
            total_points = 0
            scans_details = []
            has_color = False
            has_intensity = False
            all_intensity_min = []
            all_intensity_max = []

            all_x_min, all_x_max = [], []
            all_y_min, all_y_max = [], []
            all_z_min, all_z_max = [], []

            sensor_hints = []

            for i in range(scan_count):
                scan_hdr = e57.get_header(i)
                pts = getattr(scan_hdr, "point_count", 0)
                total_points += pts

                scan_info: Dict[str, Any] = {
                    "scan_index": i + 1,
                    "point_count": pts,
                    "guid": getattr(scan_hdr, "guid", ""),
                    "has_pose": getattr(scan_hdr, "has_pose", False),
                }

                # Sensor info da scan header
                desc = getattr(scan_hdr, "description", None)
                if desc:
                    scan_info["description"] = str(desc)
                    sensor_hints.append(str(desc))

                name = getattr(scan_hdr, "name", None)
                if name:
                    scan_info["name"] = str(name)
                    sensor_hints.append(str(name))

                # Bounds cartesiani
                x_min = getattr(scan_hdr, "xMinimum", None)
                x_max = getattr(scan_hdr, "xMaximum", None)
                y_min = getattr(scan_hdr, "yMinimum", None)
                y_max = getattr(scan_hdr, "yMaximum", None)
                z_min = getattr(scan_hdr, "zMinimum", None)
                z_max = getattr(scan_hdr, "zMaximum", None)

                if None not in (x_min, x_max, y_min, y_max, z_min, z_max):
                    scan_info["bounds"] = {
                        "x": {"min": float(x_min), "max": float(x_max)},
                        "y": {"min": float(y_min), "max": float(y_max)},
                        "z": {"min": float(z_min), "max": float(z_max)},
                    }
                    all_x_min.append(float(x_min))
                    all_x_max.append(float(x_max))
                    all_y_min.append(float(y_min))
                    all_y_max.append(float(y_max))
                    all_z_min.append(float(z_min))
                    all_z_max.append(float(z_max))

                # Pose / translation
                if getattr(scan_hdr, "has_pose", False):
                    try:
                        trans = getattr(scan_hdr, "translation", None)
                        if trans is not None:
                            scan_info["translation"] = [float(v) for v in trans]
                    except Exception:
                        pass

                # Intensità
                int_min = getattr(scan_hdr, "intensityMinimum", None)
                int_max = getattr(scan_hdr, "intensityMaximum", None)
                if int_min is not None and int_max is not None:
                    has_intensity = True
                    scan_info["intensity_range"] = {"min": float(int_min), "max": float(int_max)}
                    all_intensity_min.append(float(int_min))
                    all_intensity_max.append(float(int_max))

                # Colore
                color_limits = getattr(scan_hdr, "colorLimits", None)
                if color_limits is not None:
                    has_color = True
                    scan_info["has_color"] = True

                scans_details.append(scan_info)

            # Bounding box aggregata
            if all_x_min and all_x_max:
                bbox_x_min = min(all_x_min)
                bbox_x_max = max(all_x_max)
                bbox_y_min = min(all_y_min)
                bbox_y_max = max(all_y_max)
                bbox_z_min = min(all_z_min)
                bbox_z_max = max(all_z_max)
                x_range = round(bbox_x_max - bbox_x_min, 4)
                y_range = round(bbox_y_max - bbox_y_min, 4)
                z_range = round(bbox_z_max - bbox_z_min, 4)
                bounds = {
                    "x": {"min": bbox_x_min, "max": bbox_x_max},
                    "y": {"min": bbox_y_min, "max": bbox_y_max},
                    "z": {"min": bbox_z_min, "max": bbox_z_max},
                }
                spatial_extent = {
                    "x_range": x_range,
                    "y_range": y_range,
                    "z_range": z_range,
                }
                offset = [round(bbox_x_min, 4), round(bbox_y_min, 4), round(bbox_z_min, 4)]
            else:
                bounds = {"x": {"min": 0.0, "max": 0.0}, "y": {"min": 0.0, "max": 0.0}, "z": {"min": 0.0, "max": 0.0}}
                spatial_extent = {"x_range": 0.0, "y_range": 0.0, "z_range": 0.0}
                offset = [0.0, 0.0, 0.0]

            # Coordinate system
            coordinate_system = {
                "scale": [0.001, 0.001, 0.001],
                "offset": offset,
                "bounds": bounds,
                "spatial_extent": spatial_extent,
            }

            # Intensità aggregata
            intensity_range = None
            if all_intensity_min and all_intensity_max:
                intensity_range = {
                    "min": min(all_intensity_min),
                    "max": max(all_intensity_max),
                }

            # Georeferencing
            epsg_code = None
            georeferenced = False
            if coordinate_metadata:
                georeferenced = True
                epsg_match = re.search(r"EPSG[:\s]+(\d+)", coordinate_metadata, re.IGNORECASE)
                if epsg_match:
                    epsg_code = f"EPSG:{epsg_match.group(1)}"
            elif bounds["x"]["max"] > 10000 or bounds["y"]["max"] > 10000:
                # Coordinate metriche proiettate
                georeferenced = True

            georeferencing = {
                "georeferenced": georeferenced,
                "epsg_code": epsg_code,
                "crs_wkt": coordinate_metadata if coordinate_metadata else None,
                "coordinate_metadata": coordinate_metadata if coordinate_metadata else None,
            }

            # Software detection
            software_signature = "ASTM E57 Reader/Exporter"
            detected_sw = None
            all_text_hints = f"{coordinate_metadata} {' '.join(sensor_hints)}"
            for brand in ["FARO", "Leica", "Trimble", "Riegl", "Z+F", "CloudCompare", "RealityCapture", "Agisoft"]:
                if brand.lower() in all_text_hints.lower():
                    detected_sw = brand
                    software_signature = f"{brand} (E57 Exporter)"
                    break

            software_metadata = {
                "system_identifier": "E57 Standard",
                "generating_software": software_signature,
                "detected_software": detected_sw,
            }

            # Sensor detection: E57 è quasi sempre TLS (Terrestrial Laser Scanner)
            sensor_type = {
                "detected_sensor": detected_sw if detected_sw else "Terrestrial Laser Scanner (TLS)",
                "characteristics": [
                    "terrestrial_laser_scanner",
                    f"scans_count_{scan_count}",
                ],
                "inferred_sensor_types": [
                    {
                        "sensor_type": "Terrestrial Laser Scanner (TLS)",
                        "confidence": 95.0,
                        "examples": ["FARO Focus", "Leica RTC360 / BLK360", "Trimble X7", "Z+F IMAGER"],
                    }
                ],
            }
            if has_color:
                sensor_type["characteristics"].append("rgb_data_present")
            if has_intensity:
                sensor_type["characteristics"].append("intensity_present")

            # Costruzione metadati unificati
            point_cloud_nature = {
                "num_points": total_points,
                "scan_count": scan_count,
                "scans_details": scans_details,
                "has_color": has_color,
                "has_intensity": has_intensity,
                "intensity_range": intensity_range,
                "classification": {"Unclassified": total_points},
                "return_types": {"single_return": total_points},
                "scan_angle_info": None,
            }

            metadata: Dict[str, Any] = {
                "file_info": {
                    "filename": file_path.name,
                    "filepath": str(file_path.absolute()),
                    "file_size_bytes": file_size_bytes,
                    "file_size_mb": file_size_mb,
                    "file_size_formatted": file_size_formatted,
                    "format": "E57",
                    "e57_version": format_version,
                    "guid": guid,
                },
                "header_info": {
                    "format": "E57",
                    "scan_count": scan_count,
                    "point_count": total_points,
                    "point_format": "E57 Multi-Scan",
                },
                "punto_cloud_nature": point_cloud_nature,
                "point_cloud_nature": point_cloud_nature,
                "coordinate_system": coordinate_system,
                "temporal_info": {
                    "file_creation_date": creation_date_raw if creation_date_raw else datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d"),
                },
                "georeferencing": georeferencing,
                "software_metadata": software_metadata,
                "processing_history": {
                    "is_post_processed": scan_count > 1 or detected_sw == "CloudCompare",
                    "detected_software_chain": [detected_sw] if detected_sw else [],
                    "processing_indicators": [f"Multi-scan E57 bundle ({scan_count} scans)"] if scan_count > 1 else [],
                    "anomalies": [],
                },
                "sensor_type": sensor_type,
            }

            return metadata

        finally:
            try:
                e57.close()
            except Exception:
                pass
