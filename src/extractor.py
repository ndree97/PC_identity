from pathlib import Path
from typing import Dict, Any, Optional
import re
import numpy as np
import laspy

from src.extractors.metadata_extr import MetadataExtractor
from src.extractors.intensity_extr import IntensityExtractor  # lasciato compatibile
from src.extractors.class_extr import ClassificationExtractor  # lasciato compatibile
from src.extractors.timestamp_extr import TemporalExtractor  # lasciato compatibile
from src.extractors.crs_extr import CoordinateExtractor  # lasciato compatibile
from src.detectors.sw_detect import SoftwareDetector
from src.detectors.sensor_detect import SensorDetector
from src.detectors.process_detect import ProcessingDetector
from src.utils.config_load import ConfigLoader
from src.utils.file_handler import FileHandler


class LASMetadataExtractor:
    """
    Estrattore metadati LAS/LAZ ottimizzato:
    - Lettura a chunk
    - Statistiche combinate in passata unica
    - Extent da header
    - Selezione backend LAZ
    """

    def __init__(
        self,
        config_dir: str = "config",
        chunk_size: int = 2_000_000,
        laz_backend: Optional[str] = "auto",  # "auto", "lazrs-parallel", "lazrs", "laszip", None
    ):
        self.config_loader = ConfigLoader(config_dir)
        self.file_handler = FileHandler()

        # Estrattori / detector esistenti
        self.metadata_ext = MetadataExtractor()
        self.intensity_ext = IntensityExtractor()
        self.classification_ext = ClassificationExtractor(self.config_loader)
        self.temporal_ext = TemporalExtractor()
        self.coordinate_ext = CoordinateExtractor()

        self.software_det = SoftwareDetector(self.config_loader)
        self.sensor_det = SensorDetector(self.config_loader)
        self.processing_det = ProcessingDetector(self.config_loader)

        # Inizializza estrattori per formati aggiuntivi (.e57, .ply)
        from src.extractors.e57_extr import E57MetadataExtractor
        from src.extractors.ply_extr import PLYMetadataExtractor

        self.e57_ext = E57MetadataExtractor(
            self.config_loader, self.software_det, self.sensor_det, self.processing_det
        )
        self.ply_ext = PLYMetadataExtractor(
            self.config_loader, self.software_det, self.sensor_det, self.processing_det
        )

        self.chunk_size = int(chunk_size)
        self._laz_backend = self._resolve_laz_backend(laz_backend)

    @staticmethod
    def _resolve_laz_backend(name: Optional[str]):
        # Rimappa stringhe in laspy.compression.LazBackend o None
        try:
            from laspy.compression import LazBackend
        except Exception:
            return None

        if name is None:
            return None
        if isinstance(name, LazBackend):
            return name

        mapping = {
            "auto": None,  # lascia autodetect di laspy
            "lazrs-parallel": LazBackend.LazrsParallel,
            "lazrs": LazBackend.Lazrs,
            "laszip": LazBackend.Laszip,
        }
        return mapping.get(str(name).lower(), None)

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Estrae TUTTI i metadati supportando file .las, .laz, .e57, .ply.
        """
        target_path = Path(file_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        ext = target_path.suffix.lower()
        if ext in [".las", ".laz"]:
            return self._extract_las_laz(target_path)
        elif ext == ".e57":
            return self.e57_ext.extract(target_path)
        elif ext == ".ply":
            return self.ply_ext.extract(target_path)
        else:
            raise ValueError(
                f"Formato non supportato '{ext}'. "
                f"Formati supportati: .las, .laz, .e57, .ply"
            )

    def _extract_las_laz(self, las_path: Path) -> Dict[str, Any]:
        """
        Estrae TUTTI i metadati LAS/LAZ usando lettura a chunk e passata unica.
        """
        # Apertura ottimizzata con backend LAZ opzionale
        # Nota: laspy autodetermina il backend se None; si può forzare Lazrs/LazrsParallel
        # per migliori performance su .laz quando disponibile.
        open_kwargs = {}
        if self._laz_backend is not None:
            open_kwargs["laz_backend"] = self._laz_backend

        with laspy.open(las_path, mode="r", **open_kwargs) as reader:
            header = reader.header

            # Coordinate system & extent: usare i limiti dall'header
            coordinate_system = self._extract_coordinate_system_from_header(header)

            # Georeferencing (EPSG, WKT, VLR)
            georeferencing = self._extract_georeferencing_from_header(header)

            # Software metadata dall'header
            software_metadata = self.software_det.extract_software_info(header)

            # Accumulatori per passata unica
            return_counts = None           # np.ndarray per conteggio returns
            class_counts = None            # np.ndarray per conteggio classificazioni
            intensity_min = None
            intensity_max = None
            scan_min = None
            scan_max = None
            gps_min = None
            gps_max = None

            # Iterazione a chunk
            for points in reader.chunk_iterator(self.chunk_size):
                # Conteggio returns
                if hasattr(points, "return_num"):
                    rn = points.return_num
                    if rn is not None and len(rn) > 0:
                        local = np.bincount(rn, minlength=int(rn.max()) + 1)
                        if return_counts is None:
                            return_counts = local
                        else:
                            # allinea lunghezze
                            if local.size > return_counts.size:
                                pad = local.size - return_counts.size
                                return_counts = np.pad(return_counts, (0, pad))
                            elif return_counts.size > local.size:
                                local = np.pad(local, (0, return_counts.size - local.size))
                            return_counts += local

                # Conteggio classificazioni
                if hasattr(points, "classification"):
                    cl = points.classification
                    if cl is not None and len(cl) > 0:
                        local = np.bincount(cl, minlength=int(cl.max()) + 1)
                        if class_counts is None:
                            class_counts = local
                        else:
                            if local.size > class_counts.size:
                                pad = local.size - class_counts.size
                                class_counts = np.pad(class_counts, (0, pad))
                            elif class_counts.size > local.size:
                                local = np.pad(local, (0, class_counts.size - local.size))
                            class_counts += local

                # Intensità min/max
                if hasattr(points, "intensity"):
                    inten = points.intensity
                    if inten is not None and len(inten) > 0:
                        pmin = int(np.min(inten))
                        pmax = int(np.max(inten))
                        intensity_min = pmin if intensity_min is None else min(intensity_min, pmin)
                        intensity_max = pmax if intensity_max is None else max(intensity_max, pmax)

                # Angolo di scansione min/max
                if hasattr(points, "scan_angle"):
                    sa = points.scan_angle
                    if sa is not None and len(sa) > 0:
                        smin = float(np.min(sa))
                        smax = float(np.max(sa))
                        scan_min = smin if scan_min is None else min(scan_min, smin)
                        scan_max = smax if scan_max is None else max(scan_max, smax)

                # Range tempo GPS
                if hasattr(points, "gps_time"):
                    gt = points.gps_time
                    if gt is not None and len(gt) > 0:
                        gmin = float(np.min(gt))
                        gmax = float(np.max(gt))
                        gps_min = gmin if gps_min is None else min(gps_min, gmin)
                        gps_max = gmax if gps_max is None else max(gps_max, gmax)

            # Confezione risultati
            return_dict = (
                {f"return_{i}": int(c) for i, c in enumerate(return_counts) if i > 0 and c > 0}
                if return_counts is not None else None
            )
            class_dict = (
                {str(i): int(c) for i, c in enumerate(class_counts) if c > 0}
                if class_counts is not None else None
            )

            # Num points dal solo header
            num_points = int(header.point_count)

            # Temporal info di alto livello
            gps_range = {"min": gps_min, "max": gps_max} if gps_min is not None else None
            gps_type = self._gps_time_type_from_header(header) if gps_range else None

            metadata = {
                "file_info": self.metadata_ext.extract_file_info(las_path),
                "header_info": self.metadata_ext.extract_header_info(header),

                "punto_cloud_nature": {
                    "num_points": num_points,
                    "return_types": return_dict,
                    "classification": class_dict,  # oppure mantenere l’API del vostro ClassificationExtractor
                    "intensity_range": (
                        {"min": intensity_min, "max": intensity_max}
                        if intensity_min is not None else None
                    ),
                    "scan_angle_info": (
                        {"min": scan_min, "max": scan_max}
                        if scan_min is not None else None
                    ),
                },

                "coordinate_system": coordinate_system,

                "temporal_info": {
                    "gps_time_range": gps_range,
                    "gps_time_type": gps_type,
                    "file_creation_date": self.temporal_ext.extract_file_creation_date(header, las_path),
                },

                "software_metadata": software_metadata,
                "georeferencing": georeferencing,
            }

            # Sensor info: adattare la vostra implementazione a header/reader se non serve l’intero cloud
            try:
                sensor_info = self.sensor_det.extract_sensor_info(None, header)
                if sensor_info:
                    metadata["sensor_type"] = sensor_info
            except Exception:
                pass

            # Post-processing history
            try:
                processing_info = self.processing_det.detect_post_processing(None, header)
                if processing_info:
                    metadata["processing_history"] = processing_info
            except Exception:
                pass

            # Duplica per compatibilità chiavi inglesi/italiane
            metadata["point_cloud_nature"] = metadata["punto_cloud_nature"]

        return metadata

    def save(self, metadata: Dict[str, Any], output_path: str) -> Path:
        return self.file_handler.save_json(metadata, output_path)

    def print_key_parameters(self, metadata: Dict[str, Any]):
        print("\n" + "="*80)
        print("PARAMETRI CHIAVE DEL FILE")
        print("="*80)

        # Nome file
        filename = metadata.get('file_info', {}).get('filename', 'N/A')
        print(f"File: {filename}")

        # Dimensione file (con fallback)
        try:
            file_size_formatted = metadata.get('file_info', {}).get('file_size_formatted', None)
            if file_size_formatted:
                print(f"Dim. File: {file_size_formatted}")
            else:
                file_path = metadata.get('file_info', {}).get('filepath', '')
                if file_path:
                    path_obj = Path(file_path)
                    if path_obj.exists():
                        file_size = path_obj.stat().st_size
                        if file_size < 1024:
                            dim_str = f"{file_size} B"
                        elif file_size < 1024 * 1024:
                            dim_str = f"{file_size/1024:.1f} KB"
                        elif file_size < 1024 * 1024 * 1024:
                            dim_str = f"{file_size/(1024*1024):.1f} MB"
                        else:
                            dim_str = f"{file_size/(1024*1024*1024):.1f} GB"
                        print(f"Dim. File: {dim_str}")
                    else:
                        print("Dim. File: Non disponibile")
                else:
                    print("Dim. File: Non disponibile")
        except Exception as e:
            print(f"Dim. File: Errore ({e})")

        # Estensione spaziale
        try:
            coord_sys = metadata.get('coordinate_system', {})
            if 'spatial_extent' in coord_sys:
                extent = coord_sys['spatial_extent']
                x_dim = extent.get('x_range', 0)
                y_dim = extent.get('y_range', 0)
                z_dim = extent.get('z_range', 0)
                print(f"Ext. Spaziale: {x_dim:.2f} × {y_dim:.2f} × {z_dim:.2f}")
            else:
                print("Ext. Spaziale: Non disponibili")
        except:
            print("Ext. Spaziale: Non disponibili")

        # Numero di punti
        try:
            num_points = metadata.get('punto_cloud_nature', {}).get('num_points', 'N/A')
            print(f"N. punti: {num_points:,}".replace(',', ' ') if isinstance(num_points, int) else f"N. punti: {num_points}")
        except:
            print("N. punti: Non disponibili")

        # EPSG
        try:
            epsg = metadata.get('georeferencing', {}).get('epsg_code', 'Non specificato')
            if isinstance(epsg, str):
                if 'EPSG' in epsg:
                    epsg_match = re.search(r'(\d+)', epsg)
                    if epsg_match:
                        epsg = f"EPSG:{epsg_match.group(1)}"
                    else:
                        epsg = epsg.replace('"', '').replace(',', '')
            print(f"EPSG: {epsg}")
        except:
            print("EPSG: Non disponibile")

        # CRS
        try:
            crs = metadata.get('georeferencing', {}).get('crs_wkt', 'Non specificato')
            if isinstance(crs, str) and len(crs) > 80:
                crs = crs[:80] + "..."
            print(f"CRS: {crs}")
        except:
            print("CRS: Non disponibile")

        # Source
        try:
            source = metadata.get('software_metadata', {}).get('generating_software', 'Sconosciuto')
            print(f"Source: {source}")
        except:
            print("Source: Non disponibile")

        print("="*80 + "\n")

    # ======= Helper ottimizzati =======

    @staticmethod
    def _extract_coordinate_system_from_header(header) -> Dict[str, Any]:
        mins = header.mins  # [minX, minY, minZ]
        maxs = header.maxs  # [maxX, maxY, maxZ]
        return {
            "spatial_extent": {
                "x_min": float(mins[0]),
                "x_max": float(maxs[0]),
                "y_min": float(mins[1]),
                "y_max": float(maxs[1]),
                "z_min": float(mins[2]),
                "z_max": float(maxs[2]),
                "x_range": float(maxs[0] - mins[0]),
                "y_range": float(maxs[1] - mins[1]),
                "z_range": float(maxs[2] - mins[2]),
            }
        }

    @staticmethod
    def _extract_georeferencing_from_header(header) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "georeferenced": False,
            "epsg_code": None,
            "crs_wkt": None,
            "has_gps_time": None,   # valorizzato in temporal_info
            "gps_time_type": None,  # valorizzato altrove
            "vlr_records": None,
            "has_geo_keys": False,
        }

        vlr_records = []
        try:
            for vlr in getattr(header, "vlrs", []):
                try:
                    rec = {
                        "record_id": getattr(vlr, "record_id", None),
                        "user_id": getattr(vlr, "user_id", None),
                    }
                    vlr_records.append(rec)

                    # GeoKeyDirectoryTag
                    if getattr(vlr, "record_id", None) == 34735:
                        info["georeferenced"] = True
                        info["has_geo_keys"] = True

                    # WKT VLR
                    if getattr(vlr, "record_id", None) == 2112:
                        try:
                            raw = getattr(vlr, "record_data", b"")
                            wkt = raw.decode("utf-8", errors="ignore")
                            info["crs_wkt"] = wkt if len(wkt) <= 100 else (wkt[:100] + "...")
                            # Estrai EPSG indicativo dal WKT
                            if "EPSG" in wkt:
                                m = re.search(r"EPSG[^0-9]*([0-9]{3,6})", wkt)
                                if m:
                                    info["epsg_code"] = f"EPSG:{m.group(1)}"
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        if vlr_records:
            info["vlr_records"] = vlr_records

        # Prova a serializzare eventuale CRS in header (se disponibile)
        try:
            # Non tutti gli header hanno .crs risolto, ma se presente
            crs_str = str(getattr(header, "crs", "")).strip()
            if crs_str:
                info["georeferenced"] = True
                if not info.get("epsg_code") and "EPSG" in crs_str:
                    info["epsg_code"] = crs_str
        except Exception:
            pass

        return info

    @staticmethod
    def _gps_time_type_from_header(header) -> Optional[str]:
        try:
            ge = getattr(header, "global_encoding", None)
            if ge is None:
                return None
            # Se il flag 'gps_standard_time' è esposto
            if hasattr(ge, "gps_standard_time") and ge.gps_standard_time:
                return "GPS Standard Time (UTC)"
            # fallback
            return "GPS Week Time"
        except Exception:
            return None


# Alias per terminologia generica
PointCloudMetadataExtractor = LASMetadataExtractor
