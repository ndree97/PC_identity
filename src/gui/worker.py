from pathlib import Path
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from src.extractor import PointCloudMetadataExtractor
from src.utils.html_generator import HTMLGenerator
from src.utils.file_grouper import FileGrouper


class ExtractionWorker(QThread):
    """
    Worker in background thread per l'analisi delle nuvole di punti.
    Evita il freeze dell'interfaccia utente durante il caricamento di file pesanti.
    """

    # Segnali di avanzamento e stato
    sig_progress = pyqtSignal(int, int)  # current, total
    sig_file_started = pyqtSignal(int, str)  # index, filepath
    sig_file_completed = pyqtSignal(int, str, dict, dict, str)  # index, filepath, metadata, key_params, html_path
    sig_file_error = pyqtSignal(int, str, str)  # index, filepath, error_message
    sig_log = pyqtSignal(str)  # log message
    sig_all_finished = pyqtSignal(list)  # list of all results

    def __init__(
        self,
        file_paths: List[Path],
        output_dir: Path,
        generate_html: bool = True,
        group_files: bool = True,
        config_dir: str = "config",
        parent=None,
    ):
        super().__init__(parent)
        self.file_paths = file_paths
        self.output_dir = Path(output_dir)
        self.generate_html = generate_html
        self.group_files = group_files
        self.config_dir = config_dir
        self._is_cancelled = False

    def cancel(self):
        """Richiede l'interruzione dell'elaborazione."""
        self._is_cancelled = True
        self.sig_log.emit("⚠️ Richiesta di interruzione in corso...")

    def run(self):
        total = len(self.file_paths)
        self.sig_log.emit(f"🚀 Inizio elaborazione di {total} file...")
        self.sig_progress.emit(0, total)

        extractor = PointCloudMetadataExtractor(config_dir=self.config_dir)
        html_gen = HTMLGenerator() if self.generate_html else None

        all_results = []

        for idx, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                self.sig_log.emit("⏹️ Elaborazione interrotta dall'utente.")
                break

            self.sig_file_started.emit(idx, str(file_path))
            self.sig_log.emit(f"[{idx + 1}/{total}] Analisi: {file_path.name}...")

            try:
                # Estrazione metadati unificata (.las, .laz, .e57, .ply)
                metadata = extractor.extract(str(file_path))

                # Estrai parametri chiave per la vista tabella
                key_params = self._extract_key_summary(metadata, file_path)

                # Cartella di output per il singolo file
                file_output_dir = self.output_dir / file_path.stem
                file_output_dir.mkdir(parents=True, exist_ok=True)

                # Salva JSON
                json_path = file_output_dir / f"{file_path.stem}_metadata.json"
                extractor.save(metadata, str(json_path))

                # Genera HTML se abilitato
                html_path_str = ""
                if html_gen:
                    html_path = file_output_dir / f"{file_path.stem}_report.html"
                    try:
                        html_gen.generate_single_file_report(metadata, html_path, str(file_path))
                        html_path_str = str(html_path)
                    except Exception as html_err:
                        self.sig_log.emit(f"  ⚠️ Errore report HTML per {file_path.name}: {html_err}")

                result_entry = {
                    "filepath": str(file_path),
                    "filename": file_path.name,
                    "metadata": metadata,
                    "key_params": key_params,
                    "json_path": str(json_path),
                    "html_path": html_path_str,
                }
                all_results.append(result_entry)

                self.sig_file_completed.emit(idx, str(file_path), metadata, key_params, html_path_str)
                self.sig_log.emit(f"  ✓ {file_path.name} completato con successo.")

            except Exception as e:
                err_msg = str(e)
                self.sig_file_error.emit(idx, str(file_path), err_msg)
                self.sig_log.emit(f"  ✗ Errore su {file_path.name}: {err_msg}")

            self.sig_progress.emit(idx + 1, total)

        # Gestione raggruppamento se abilitato e ci sono almeno 2 file analizzati
        if self.group_files and len(all_results) > 1 and not self._is_cancelled:
            self.sig_log.emit("🔍 Analisi raggruppamenti file correlati...")
            try:
                grouper = FileGrouper()
                file_objs = [Path(r["filepath"]) for r in all_results]
                groups = grouper.identify_groups(file_objs)

                # Se ci sono gruppi con più di 1 file, genera report aggregato
                multi_groups = {k: v for k, v in groups.items() if len(v) > 1}
                if multi_groups and html_gen:
                    for gname, gfiles in multi_groups.items():
                        g_results = [r for r in all_results if Path(r["filepath"]) in gfiles]
                        if len(g_results) > 1:
                            safe_gname = gname.replace(' ', '_').replace('(', '').replace(')', '').replace(':', '').lower()
                            grp_out = self.output_dir / safe_gname
                            grp_out.mkdir(parents=True, exist_ok=True)
                            grp_html = grp_out / f"{safe_gname}_group_report.html"

                            total_pts = sum(
                                r["metadata"].get("punto_cloud_nature", {}).get("num_points", 0)
                                for r in g_results
                            )
                            total_bytes = sum(
                                r["metadata"].get("file_info", {}).get("file_size_bytes", 0)
                                for r in g_results
                            )
                            size_str = (
                                f"{total_bytes / (1024*1024*1024):.2f} GB"
                                if total_bytes >= 1024*1024*1024
                                else f"{total_bytes / (1024*1024):.1f} MB"
                            )
                            first_meta = g_results[0]["metadata"]
                            common_meta = {
                                "epsg_code": first_meta.get("georeferencing", {}).get("epsg_code"),
                                "source": first_meta.get("software_metadata", {}).get("generating_software"),
                                "crs_wkt": first_meta.get("georeferencing", {}).get("crs_wkt"),
                            }
                            html_gen.generate_group_report(gname, g_results, grp_html, common_meta, total_pts, size_str)
                            self.sig_log.emit(f"  ✓ Report gruppo creato: {gname} ({len(g_results)} file)")
            except Exception as grp_err:
                self.sig_log.emit(f"⚠️ Errore nel raggruppamento: {grp_err}")

        self.sig_log.emit("✨ Processo completato!")
        self.sig_all_finished.emit(all_results)

    def _extract_key_summary(self, metadata: Dict[str, Any], file_path: Path) -> Dict[str, str]:
        """Estrae un dizionario con i parametri chiave formattati per la tabella della GUI."""
        file_info = metadata.get("file_info", {})
        nature = metadata.get("punto_cloud_nature", {})
        georef = metadata.get("georeferencing", {})
        software = metadata.get("software_metadata", {})
        sensor = metadata.get("sensor_type", {})

        # Punti
        num_pts = nature.get("num_points", 0)
        num_pts_str = f"{num_pts:,}".replace(",", " ") if num_pts else "N/D"

        # Dimensione
        dim_str = file_info.get("file_size_formatted")
        if not dim_str:
            bytes_val = file_path.stat().st_size
            dim_str = f"{bytes_val / (1024 * 1024):.1f} MB"

        # EPSG
        epsg = georef.get("epsg_code") or "Non definito"

        # Software / Sensore
        sw = software.get("generating_software") or software.get("detected_software") or "N/D"
        sensor_name = sensor.get("detected_sensor") or "N/D"

        return {
            "filename": file_path.name,
            "format": file_info.get("format", file_path.suffix.upper().replace(".", "")),
            "dim": dim_str,
            "num_points": num_pts_str,
            "epsg": epsg,
            "source": sw,
            "sensor": sensor_name,
        }
