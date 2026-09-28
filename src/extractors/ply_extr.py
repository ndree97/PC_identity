from pathlib import Path
from typing import Dict, Any, Optional, List
import re
from datetime import datetime

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


class PLYMetadataExtractor:
    """
    Estrattore metadati per file Polygon File Format (.ply).
    Estrae proprietà dell'header, commenti software, conteggio vertici/facce,
    e calcola bounds/proprietà geometriche.
    """

    def __init__(self, config_loader=None, software_det=None, sensor_det=None, processing_det=None):
        self.config_loader = config_loader
        self.software_det = software_det
        self.sensor_det = sensor_det
        self.processing_det = processing_det

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """Estrae i metadati completi da un file .ply."""
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

        # 1. Parsing Header PLY
        header_info = self._parse_ply_header(file_path)

        vertex_count = header_info.get("vertex_count", 0)
        face_count = header_info.get("face_count", 0)
        properties = header_info.get("properties", [])
        comments = header_info.get("comments", [])
        ply_format = header_info.get("format", "unknown")

        prop_names = [p["name"] for p in properties]
        has_color = any(p in prop_names for p in ["red", "diffuse_red", "r"]) and any(p in prop_names for p in ["green", "diffuse_green", "g"])
        has_normals = any(p in prop_names for p in ["nx", "normal_x"])
        has_intensity = any(p in prop_names for p in ["intensity", "scalar_intensity", "reflectance", "confidence"])
        scalar_fields = [p for p in prop_names if p not in ["x", "y", "z", "nx", "ny", "nz", "red", "green", "blue", "alpha", "diffuse_red", "diffuse_green", "diffuse_blue"]]

        # 2. Bounding Box & Estensione (tramite Open3D se disponibile e file non eccessivamente enorme)
        bounds = {"x": {"min": 0.0, "max": 0.0}, "y": {"min": 0.0, "max": 0.0}, "z": {"min": 0.0, "max": 0.0}}
        spatial_extent = {"x_range": 0.0, "y_range": 0.0, "z_range": 0.0}
        offset = [0.0, 0.0, 0.0]

        if HAS_OPEN3D and vertex_count > 0 and file_size_mb < 300:
            try:
                pcd = o3d.io.read_point_cloud(str(file_path))
                if not pcd.is_empty():
                    min_b = pcd.get_min_bound()
                    max_b = pcd.get_max_bound()
                    x_min, y_min, z_min = float(min_b[0]), float(min_b[1]), float(min_b[2])
                    x_max, y_max, z_max = float(max_b[0]), float(max_b[1]), float(max_b[2])
                    bounds = {
                        "x": {"min": round(x_min, 4), "max": round(x_max, 4)},
                        "y": {"min": round(y_min, 4), "max": round(y_max, 4)},
                        "z": {"min": round(z_min, 4), "max": round(z_max, 4)},
                    }
                    spatial_extent = {
                        "x_range": round(x_max - x_min, 4),
                        "y_range": round(y_max - y_min, 4),
                        "z_range": round(z_max - z_min, 4),
                    }
                    offset = [round(x_min, 4), round(y_min, 4), round(z_min, 4)]
            except Exception:
                pass

        # 3. Software Detection dai commenti
        detected_software = None
        generating_software = "PLY Exporter"
        all_comments_str = " ".join(comments)

        software_signatures = [
            ("CloudCompare", "CloudCompare"),
            ("MeshLab", "MeshLab"),
            ("Agisoft", "Agisoft Metashape"),
            ("Metashape", "Agisoft Metashape"),
            ("RealityCapture", "RealityCapture"),
            ("Blender", "Blender"),
            ("Open3D", "Open3D"),
            ("Pix4D", "Pix4D"),
            ("FARO", "FARO Scene"),
            ("Leica", "Leica Cyclone"),
        ]

        for key, name in software_signatures:
            if key.lower() in all_comments_str.lower():
                detected_software = name
                generating_software = name
                break

        if not detected_software and comments:
            generating_software = comments[0]

        # 4. Georeferenziazione
        georeferenced = False
        if bounds["x"]["max"] > 10000 or bounds["y"]["max"] > 10000:
            georeferenced = True

        georeferencing = {
            "georeferenced": georeferenced,
            "epsg_code": None,
            "crs_wkt": None,
        }

        # 5. Sensor Inference
        characteristics = [f"ply_{ply_format}"]
        if has_color:
            characteristics.append("rgb_data_present")
        if has_normals:
            characteristics.append("normals_present")
        if has_intensity:
            characteristics.append("intensity_present")
        if face_count > 0:
            characteristics.append("polygonal_mesh")

        # Se ha RGB e normali ed è generato da Metashape/Pix4D/RealityCapture -> Fotogrammetria
        is_photogrammetry = (
            detected_software in ["Agisoft Metashape", "Pix4D", "RealityCapture", "MeshLab"]
            or (has_color and not has_intensity)
        )

        if is_photogrammetry:
            sensor_name = "Photogrammetry (UAV/Aerial or Terrestrial)"
            inferred = [
                {
                    "sensor_type": "UAV Photogrammetry",
                    "confidence": 85.0,
                    "examples": ["DJI Mavic / Matrice", "Wingtra", "SenseFly"],
                },
                {
                    "sensor_type": "Close-Range Photogrammetry",
                    "confidence": 75.0,
                    "examples": ["DSLR Camera", "Mirrorless", "Structured Light Scanner"],
                }
            ]
        else:
            sensor_name = "Laser Scanner (TLS/MLS)"
            inferred = [
                {
                    "sensor_type": "Terrestrial Laser Scanner (TLS)",
                    "confidence": 70.0,
                    "examples": ["FARO Focus", "Leica RTC360", "Riegl"],
                }
            ]

        sensor_type = {
            "detected_sensor": detected_software if detected_software else sensor_name,
            "characteristics": characteristics,
            "inferred_sensor_types": inferred,
        }

        point_cloud_nature = {
            "num_points": vertex_count,
            "face_count": face_count,
            "has_color": has_color,
            "has_normals": has_normals,
            "has_intensity": has_intensity,
            "scalar_fields": scalar_fields,
            "classification": {"Unclassified": vertex_count},
            "return_types": {"single_return": vertex_count},
            "intensity_range": None,
            "scan_angle_info": None,
        }

        metadata: Dict[str, Any] = {
            "file_info": {
                "filename": file_path.name,
                "filepath": str(file_path.absolute()),
                "file_size_bytes": file_size_bytes,
                "file_size_mb": file_size_mb,
                "file_size_formatted": file_size_formatted,
                "format": "PLY",
                "ply_format": ply_format,
            },
            "header_info": {
                "format": "PLY",
                "ply_format": ply_format,
                "point_count": vertex_count,
                "face_count": face_count,
                "properties": prop_names,
            },
            "punto_cloud_nature": point_cloud_nature,
            "point_cloud_nature": point_cloud_nature,
            "coordinate_system": {
                "scale": [0.001, 0.001, 0.001],
                "offset": offset,
                "bounds": bounds,
                "spatial_extent": spatial_extent,
            },
            "temporal_info": {
                "file_creation_date": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d"),
            },
            "georeferencing": georeferencing,
            "software_metadata": {
                "system_identifier": "PLY Format",
                "generating_software": generating_software,
                "detected_software": detected_software,
            },
            "processing_history": {
                "is_post_processed": bool(detected_software or comments or face_count > 0),
                "detected_software_chain": [detected_software] if detected_software else [],
                "processing_indicators": [f"Export comment: {c}" for c in comments[:3]],
                "anomalies": [],
            },
            "sensor_type": sensor_type,
        }

        return metadata

    def _parse_ply_header(self, file_path: Path) -> Dict[str, Any]:
        """Estrae i metadati leggendo solo l'header ASCII del file PLY."""
        header: Dict[str, Any] = {
            "format": "unknown",
            "vertex_count": 0,
            "face_count": 0,
            "properties": [],
            "comments": [],
            "obj_info": [],
        }

        current_element = None

        with open(file_path, "rb") as f:
            for line_bytes in f:
                try:
                    line = line_bytes.decode("ascii", errors="ignore").strip()
                except Exception:
                    continue

                if line == "end_header":
                    break

                parts = line.split()
                if not parts:
                    continue

                token = parts[0].lower()
                if token == "format" and len(parts) >= 2:
                    header["format"] = parts[1]
                elif token == "comment":
                    comment_text = " ".join(parts[1:]).strip()
                    if comment_text:
                        header["comments"].append(comment_text)
                elif token == "obj_info":
                    info_text = " ".join(parts[1:]).strip()
                    if info_text:
                        header["obj_info"].append(info_text)
                elif token == "element" and len(parts) >= 3:
                    elem_name = parts[1].lower()
                    try:
                        elem_count = int(parts[2])
                    except ValueError:
                        elem_count = 0
                    current_element = elem_name
                    if elem_name == "vertex":
                        header["vertex_count"] = elem_count
                    elif elem_name == "face":
                        header["face_count"] = elem_count
                elif token == "property" and len(parts) >= 3:
                    if current_element == "vertex":
                        # property <type> <name>
                        header["properties"].append({
                            "type": parts[1],
                            "name": parts[2],
                        })

        return header
