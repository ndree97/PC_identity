from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys

from src.extractor import LASMetadataExtractor


class DirectoryHandler:
    """Gestisce l'analisi di directory contenenti file LAS."""

    def __init__(self):
        self.supported_extensions = {'.las', '.laz', '.e57', '.ply'}

    def find_supported_files(self, directory: Path) -> List[Path]:
        """Trova tutti i file supportati nella directory."""
        supported_files = []

        try:
            # Cerca ricorsivamente file con estensioni supportate
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    supported_files.append(file_path)
        except Exception as e:
            print(f"Errore durante la scansione della directory: {e}", file=sys.stderr)

        return supported_files

    def _analyze_single_file(self, file_path: Path, extractor: LASMetadataExtractor) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Analizza un singolo file e restituisce metadati e parametri chiave."""
        try:
            # Estrai metadati completi
            metadata = extractor.extract(str(file_path))

            # Estrai parametri chiave
            key_params = self._extract_key_params(metadata, file_path)

            return metadata, key_params

        except Exception as e:
            print(f"Errore durante l'analisi di {file_path.name}: {e}", file=sys.stderr)
            # Restituisci dati di errore
            error_metadata = {
                'file_info': {
                    'filename': file_path.name,
                    'filepath': str(file_path),
                    'error': str(e)
                }
            }
            error_key_params = {
                'filename': file_path.name,
                'error': str(e),
                'dim': 'Errore',
                'num_points': 'Errore',
                'epsg': 'Errore',
                'crs': 'Errore',
                'source': 'Errore'
            }
            return error_metadata, error_key_params

    def _extract_key_params(self, metadata: Dict[str, Any], file_path: Path) -> Dict[str, str]:
        """Estrae solo i parametri chiave dai metadati."""
        try:
            # Nome file
            filename = metadata.get('file_info', {}).get('filename', file_path.name)

            # Dimensioni File (richiesta principale)
            dim = "N/D"
            try:
                # Prova prima a prenderlo dai metadati (se già calcolato)
                dim = metadata.get('file_info', {}).get('file_size_formatted', None)
                if not dim:
                    # Calcola la dimensione del file
                    file_size = file_path.stat().st_size
                    if file_size < 1024:
                        dim = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        dim = f"{file_size/1024:.1f} KB"
                    elif file_size < 1024 * 1024 * 1024:
                        dim = f"{file_size/(1024*1024):.1f} MB"
                    else:
                        dim = f"{file_size/(1024*1024*1024):.1f} GB"
            except:
                dim = "N/D"

            # Estensione Spaziale (informazione aggiuntiva)
            spatial_ext = "N/D"
            try:
                coord_sys = metadata.get('coordinate_system', {})
                if 'spatial_extent' in coord_sys:
                    extent = coord_sys['spatial_extent']
                    x_dim = extent.get('x_range', 0)
                    y_dim = extent.get('y_range', 0)
                    z_dim = extent.get('z_range', 0)
                    spatial_ext = f"{x_dim:.1f}×{y_dim:.1f}×{z_dim:.1f}"
            except:
                pass

            # Numero di punti
            num_points = "N/D"
            try:
                num_points_raw = metadata.get('punto_cloud_nature', {}).get('num_points', None)
                if num_points_raw is not None:
                    num_points = f"{num_points_raw:,}".replace(',', ' ')
            except:
                pass

            # EPSG
            epsg = "N/D"
            try:
                epsg_raw = metadata.get('georeferencing', {}).get('epsg_code', None)
                if epsg_raw:
                    epsg = str(epsg_raw)
                    # Pulisce l'EPSG da formato problematico
                    if 'EPSG' in epsg:
                        # Estrae solo il codice numerico
                        import re
                        epsg_match = re.search(r'(\d+)', epsg)
                        if epsg_match:
                            epsg = f"EPSG:{epsg_match.group(1)}"
                        else:
                            epsg = epsg.replace('"', '').replace(',', '')
            except:
                pass

            # CRS
            crs = "N/D"
            try:
                crs_raw = metadata.get('georeferencing', {}).get('crs_wkt', None)
                if crs_raw and len(str(crs_raw)) > 0:
                    crs = str(crs_raw)
                    # Tronca se troppo lungo
                    if len(crs) > 50:
                        crs = crs[:50] + "..."
            except:
                pass

            # Source
            source = "N/D"
            try:
                source_raw = metadata.get('software_metadata', {}).get('generating_software', None)
                if source_raw:
                    source = str(source_raw)
            except:
                pass

            # File size (separato per compatibilità)
            file_size = dim  # Usa la stessa variabile per consistenza

            return {
                'filename': filename,
                'dim': dim,
                'num_points': num_points,
                'epsg': epsg,
                'crs': crs,
                'source': source,
                'file_size': file_size,
                'filepath': str(file_path)
            }

        except Exception as e:
            return {
                'filename': file_path.name,
                'dim': 'Errore',
                'num_points': 'Errore',
                'epsg': 'Errore',
                'crs': 'Errore',
                'source': 'Errore',
                'file_size': 'Errore',
                'error': str(e),
                'filepath': str(file_path)
            }

    def analyze_directory(self, files: List[Path], extractor: LASMetadataExtractor,
                         show_key_params: bool = False, generate_html: bool = False) -> List[Dict[str, Any]]:
        """Analizza tutti i file in una directory e restituisce i risultati."""

        results = []
        total_files = len(files)

        print(f"\n{'='*60}")
        print(f"ANALISI DIRECTORY - {total_files} file trovati")
        print(f"{'='*60}")

        for i, file_path in enumerate(files, 1):
            # Progress indicator
            print(f"[{i}/{total_files}] Elaborazione: {file_path.name}", end=" ... ")

            # Analizza il file
            metadata, key_params = self._analyze_single_file(file_path, extractor)

            # Stampa parametri chiave se richiesto
            if show_key_params and 'error' not in key_params:
                print("✓")
                # Stampa compatta dei parametri chiave
                print(f"  Dim: {key_params['dim']} | Punti: {key_params['num_points']} | EPSG: {key_params['epsg']} | Source: {key_params['source']}")
            elif 'error' in key_params:
                print("✗ ERRORE")
                print(f"  Errore: {key_params['error']}")
            else:
                print("✓")

            # Salva i risultati
            result = {
                'filepath': str(file_path),
                'filename': file_path.name,
                'metadata': metadata,
                'key_params': key_params
            }
            results.append(result)

        print(f"{'='*60}")
        print(f"ANALISI COMPLETATA - Processati {total_files} file")
        print(f"{'='*60}\n")

        return results