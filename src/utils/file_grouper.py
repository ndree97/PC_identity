from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import re
from collections import defaultdict


class FileGrouper:
    """Identifica e raggruppa file che potrebbero essere parti della stessa nuvola di punti."""

    def __init__(self):
        # Pattern comuni per file split
        self.split_patterns = [
            r'(.+?)_part_(\d+)(?:\..+)?$',           # basename_part_001.las
            r'(.+?)_chunk_(\d+)(?:\..+)?$',          # basename_chunk_1.las
            r'(.+?)_seg(?:ment)?_(\d+)(?:\..+)?$',    # basename_segment_1.las
            r'(.+?)_tile_(\d+)(?:\..+)?$',           # basename_tile_001.las
            r'(.+?)[_-](\d+)(?:\..+)?$',             # basename-001.las, basename_001.las
            r'(.+?)(?:\D+)?_?(\d{1,})(?:\..+)?$',   # basename001.las, basename_01.las, cloud0.las
            r'^(.+?)(\d+)(?:\..+)?$',                # cloud0.las, scan1.las (prefisso+numero)
        ]

    def identify_groups(self, files: List[Path]) -> Dict[str, List[Path]]:
        """
        Identifica gruppi di file correlati SOLO quando sono chiaramente parti della stessa nuvola.
        Restituisce: {group_name: [file_paths]}
        """
        if not files:
            return {}

        # Estrai patterns da tutti i file
        pattern_matches = []
        ungrouped_files = []

        for file_path in files:
            group_result = self._extract_base_pattern_strict(file_path.name)
            if group_result["is_grouped"]:
                pattern_matches.append((group_result["group_name"], file_path))
            else:
                ungrouped_files.append(file_path)

        # Raggruppa solo se ci sono almeno 2 file con lo stesso pattern
        temp_groups = defaultdict(list)
        for group_name, file_path in pattern_matches:
            temp_groups[group_name].append(file_path)

        # Filtra: mantieni solo gruppi con 2+ file
        groups = {}
        for group_name, file_paths in temp_groups.items():
            if len(file_paths) >= 2:  # SOLO gruppi veri
                groups[group_name] = file_paths
            else:
                # File singoli vanno negli ungrouped
                ungrouped_files.extend(file_paths)

        # Converti in dict normale e aggiungi file non raggruppati come singoli
        for file_path in ungrouped_files:
            groups[file_path.stem] = [file_path]

        return groups

    def _extract_base_pattern(self, filename: str) -> Optional[str]:
        """Estrae il pattern base dal nome del file."""
        # Rimuovi estensione per il pattern matching
        name_without_ext = Path(filename).stem

        for pattern in self.split_patterns:
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                base_name = match.group(1).strip('_-')
                # Caso speciale: se base_name è vuoto, estrai il prefisso numerico
                if not base_name:
                    # Per pattern come "cloud0", "scan1", estrai tutto tranne il numero finale
                    match_number = re.search(r'^(.+?)(\d+)$', name_without_ext)
                    if match_number:
                        base_name = match_number.group(1)
                    else:
                        base_name = name_without_ext

                # Rimuovi eventuali separatori finali
                base_name = base_name.rstrip('_-')

                # Normalizza il nome base
                return self._normalize_group_name(base_name)

        return None

    def _extract_base_pattern_strict(self, filename: str) -> Dict[str, Any]:
        """
        Estrae pattern base con logica più restrittiva.
        Restituisce: {"is_grouped": bool, "group_name": str}
        """
        # Rimuovi estensione per il pattern matching
        name_without_ext = Path(filename).stem

        # Pattern molto specifici per split di file
        split_patterns = [
            r'(.+?)_part_(\d+)(?:\..+)?$',           # basename_part_001.las
            r'(.+?)_chunk_(\d+)(?:\..+)?$',          # basename_chunk_1.las
            r'(.+?)_seg(?:ment)?_(\d+)(?:\..+)?$',    # basename_segment_1.las
            r'(.+?)_tile_(\d+)(?:\..+)?$',           # basename_tile_001.las
            r'^(.+?)(\d{2,})(?:\..+)?$',              # cloud00, cloud01 (con 2+ cifre)
            r'^(.+?)(\d+)(?:\..+)?$',                # cloud0, cloud1, scan1 (solo se prefisso è un nome comune)
        ]

        # Nomi comuni che INDICANO split
        common_split_names = ['cloud', 'scan', 'tile', 'chunk', 'part', 'segment', 'flight', 'mission']

        for pattern in split_patterns:
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                base_name = match.group(1).strip('_-')

                # Controllo più restrittivo
                if self._is_valid_split_pattern(base_name, name_without_ext):
                    normalized_name = self._normalize_group_name(base_name)
                    return {
                        "is_grouped": True,
                        "group_name": normalized_name
                    }

        return {"is_grouped": False, "group_name": name_without_ext}

    def _is_valid_split_pattern(self, base_name: str, full_name: str) -> bool:
        """
        Verifica se il pattern è un valido split di file.
        Restituisce True solo se è molto probabile che sia un split.
        """
        # Se base_name è vuoto, non è un pattern valido
        if not base_name or len(base_name) < 2:
            return False

        # Se base_name è un nome comune di split
        common_names = ['cloud', 'scan', 'tile', 'chunk', 'segment', 'flight', 'mission', 'acquisition']
        if base_name.lower() in common_names:
            return True

        # Se il nome completo ha un numero alla fine e il prefisso non contiene numeri
        if re.search(r'\d+$', full_name) and not re.search(r'\d', base_name):
            return True

        # Pattern con _part, _chunk, etc.
        if any(keyword in full_name.lower() for keyword in ['_part', '_chunk', '_segment', '_tile']):
            return True

        # Altrimenti, non è considerato un split valido
        return False

    def _normalize_group_name(self, name: str) -> str:
        """Normalizza il nome del gruppo per consistenza."""
        # Rimuovi caratteri non necessari e converto in minuscolo
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', name)
        # Rimuovi underscore multipli
        normalized = re.sub(r'_+', '_', normalized)
        # Rimuovi underscore finali
        normalized = normalized.strip('_')
        return normalized.lower() if normalized else "unknown_group"

    def get_group_statistics(self, groups: Dict[str, List[Path]]) -> Dict[str, Dict]:
        """Calcola statistiche di base per ogni gruppo."""
        stats = {}

        for group_name, files in groups.items():
            stats[group_name] = {
                'file_count': len(files),
                'files': [f.name for f in files],
                'total_size_mb': sum(f.stat().st_size for f in files if f.exists()) / (1024 * 1024),
                'extensions': list(set(f.suffix.lower() for f in files))
            }

        return stats

    def is_likely_same_cloud(self, group_name: str, files: List[Path]) -> bool:
        """
        Determina se un gruppo di file è probabilmente la stessa nuvola di punti divisa.
        Basato su euristiche:
        1. Stesso pattern di naming
        2. Numerazione sequenziale
        3. Stessa estensione
        """
        if len(files) <= 1:
            return False

        # Controlla se tutti hanno la stessa estensione
        extensions = [f.suffix.lower() for f in files]
        if len(set(extensions)) != 1:
            return False

        # Controlla se la numerazione è sequenziale
        numbers = []
        for file_path in files:
            name_without_ext = file_path.stem
            for pattern in self.split_patterns:
                match = re.match(pattern, name_without_ext, re.IGNORECASE)
                if match and len(match.groups()) >= 2:
                    try:
                        num = int(match.group(2))
                        numbers.append(num)
                        break
                    except ValueError:
                        continue

        if len(numbers) >= 2:
            numbers.sort()
            # Controlla se sono numeri consecutivi o quasi consecutivi
            return self._is_sequential(numbers)

        return False

    def _is_sequential(self, numbers: List[int]) -> bool:
        """Controlla se i numeri sono sequenziali."""
        if not numbers:
            return False

        numbers_sorted = sorted(numbers)
        for i in range(1, len(numbers_sorted)):
            if numbers_sorted[i] - numbers_sorted[i-1] > 2:  # Tolleranza di 2
                return False
        return True

    def get_group_type(self, group_name: str, files: List[Path]) -> str:
        """Determina il tipo di gruppo."""
        if len(files) == 1:
            return "single"

        if self.is_likely_same_cloud(group_name, files):
            return "split_cloud"

        # Controlla se sono file temporali (con date)
        has_dates = any(self._has_date_pattern(f.name) for f in files)
        if has_dates:
            return "temporal_sequence"

        return "related_files"

    def _has_date_pattern(self, filename: str) -> bool:
        """Controlla se il filename contiene un pattern di data."""
        date_patterns = [
            r'\d{4}[-_]\d{2}[-_]\d{2}',  # 2024-01-15, 2024_01_15
            r'\d{2}[-_]\d{2}[-_]\d{4}',  # 15-01-2024, 15_01_2024
            r'\d{8}',                    # 20240115
        ]
        return any(re.search(pattern, filename) for pattern in date_patterns)

    def suggest_group_display_name(self, group_name: str, files: List[Path]) -> str:
        """Suggerisce un nome visualizzato per il gruppo."""
        if len(files) == 1:
            return files[0].stem

        group_type = self.get_group_type(group_name, files)

        if group_type == "split_cloud":
            base_name = self._extract_base_name_from_files(files)
            return f"{base_name} (Nuvola Divisa: {len(files)} parti)"

        elif group_type == "temporal_sequence":
            base_name = self._extract_base_name_from_files(files)
            return f"{base_name} (Sequenza Temporale: {len(files)} file)"

        elif group_type == "related_files":
            base_name = self._extract_base_name_from_files(files)
            return f"{base_name} (File Correlati: {len(files)})"

        return f"Gruppo: {group_name} ({len(files)} file)"

    def _extract_base_name_from_files(self, files: List[Path]) -> str:
        """Estrae un nome base comune dai file del gruppo."""
        if not files:
            return "Sconosciuto"

        # Usa il primo file come riferimento
        first_file = files[0]
        base_pattern = self._extract_base_pattern(first_file.name)

        if base_pattern:
            # Converti dal nome normalizzato a qualcosa di più leggibile
            return base_pattern.replace('_', ' ').title()

        return first_file.stem