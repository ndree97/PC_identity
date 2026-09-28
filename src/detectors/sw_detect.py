from typing import Dict, Any, Optional
from src.utils.config_load import ConfigLoader

class SoftwareDetector:
    """Rileva software di generazione e post-processing."""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.software_sigs = config_loader.get_software_signatures()
    
    def extract_software_info(self, header) -> Optional[Dict[str, Any]]:
        """Estrae metadati software."""
        software_info = {}
        
        try:
            if hasattr(header, 'system_identifier'):
                system_id = header.system_identifier
                if isinstance(system_id, bytes):
                    system_id = system_id.decode('utf-8', errors='ignore').strip()
                if system_id:
                    software_info["system_identifier"] = system_id
        except:
            pass
        
        try:
            if hasattr(header, 'generating_software'):
                gen_soft = header.generating_software
                if isinstance(gen_soft, bytes):
                    gen_soft = gen_soft.decode('utf-8', errors='ignore').strip()
                if gen_soft:
                    software_info["generating_software"] = gen_soft
        except:
            pass
        
        # Detect software
        detected = self._detect_software(software_info)
        if detected:
            software_info["detected_software"] = detected
        
        return software_info if software_info else None
    
    def _detect_software(self, software_info: Dict[str, str]) -> Optional[str]:
        """Rileva nome software dalla metadata."""
        combined_text = " ".join([
            software_info.get("system_identifier", ""),
            software_info.get("generating_software", "")
        ]).lower()
        
        sensor_mfg = self.software_sigs["sensor_manufacturers"]
        
        for software, signatures in sensor_mfg.items():
            if any(sig in combined_text for sig in signatures):
                return software
        
        return None
