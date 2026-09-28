# PointCloud Identity Inspector
Uno strumento Python modulare ed avanzato, dotato di **interfaccia grafica desktop Qt** e CLI, per l'analisi approfondita e la caratterizzazione di nuvole di punti in formato **LAS, LAZ, E57 e PLY**. Estrae automaticamente la "carta d'identità" del rilievo: software di generazione, sensore hardware (TLS, ALS, Mobile, Fotogrammetria UAV), coordinate, CRS/EPSG, statistiche dei punti e tracce di post-processing.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GUI: PyQt5](https://img.shields.io/badge/GUI-PyQt5-orange.svg)](https://riverbankcomputing.com/software/pyqt/) 
[![Formats](https://img.shields.io/badge/formats-LAS%20%7C%20LAZ%20%7C%20E57%20%7C%20PLY-blueviolet.svg)](#supporto-multi-formato)

## Funzionalità Principali

- **Interfaccia Grafica Desktop Qt**: GUI moderna con Drag & Drop di file e intere cartelle, tabella di avanzamento in tempo reale, ispettore parametri chiave e visualizzatore JSON interattivo.
- **Supporto Multi-Formato**:
  - **LAS / LAZ**: Analisi completa di header, formati punto, classi, scale, VLR e tempo GPS con decompressione parallela (`lazrs`).
  - **E57 (ASTM E57)**: Supporto per scansioni multiple e singole, estrazione pose matriciali, bounds cartesiani e sferici, metadati dei sensori TLS (Faro, Leica, Trimble, Riegl).
  - **PLY (Polygon File Format)**: Analisi header ASCII/binario, proprietà, campi scalari, conteggio vertici/facce, estrazione commenti software e inferenza fotogrammetria.
- **Analisi della Natura della Nuvola**: Returns, classi di classificazione ASPRS, spettro di riflettanza/intensità, colori RGB e normali.
- **Sistema di Coordinate & Georeferenziazione**: Offset, scale, bounding box 3D, CRS/EPSG e WKT proiettato.
- **Rilevamento Software & Provenienza**: Identifica il software generatore o di post-processing (CloudCompare, FARO Scene, Leica Cyclone, Metashape, RealityCapture, LAStools, PDAL, ecc.).
- **Inferenza Hardware del Sensore**: Classifica il tipo di sensore (TLS, ALS, Mobile LiDAR, Fotogrammetria UAV) con indice di confidenza.
- **Report HTML Interattivi**: Generazione automatica di report visivi per singoli file e raggruppamenti automatici di scansioni correlate.

## Struttura del Progetto

```s
PointCloud-Identity-Inspector/
├── gui.py                       # Launcher interfaccia grafica desktop Qt
├── main.py                      # Entry point CLI e GUI
├── config/                      # Database configurazioni e firme
│   ├── sensor_db.json               # Database sensori LiDAR / Fotogrammetria
│   ├── sw_sign.json                 # Firme software e sensori
│   ├── class_map.json               # Mappa classificazioni ASPRS
│   └── post_proc_sign.json          # Firme di post-processing
├── src/                         # Moduli principali
│   ├── extractor.py                 # PointCloudMetadataExtractor principale
│   ├── extractors/                  # Estrattori specifici per formato
│   │   ├── e57_extr.py                  # Estrattore ASTM E57
│   │   ├── ply_extr.py                  # Estrattore PLY
│   │   ├── metadata_extr.py             # Header & metadati base
│   │   ├── crs_extr.py                  # Sistemi di coordinate & CRS
│   │   ├── intensity_extr.py            # Analisi intensità
│   │   ├── class_extr.py                # Classificazioni
│   │   └── timestamp_extr.py            # Tempo GPS e date
│   ├── detectors/                   # Motori di inferenza
│   │   ├── sw_detect.py                 # Rilevamento software
│   │   ├── sensor_detect.py             # Classificazione sensore hardware
│   │   └── process_detect.py            # Rilevamento post-processing
│   ├── gui/                         # Interfaccia Grafica Qt
│   │   ├── main_window.py               # Finestra principale, drag&drop, tabelle
│   │   └── worker.py                    # Worker asincrono multi-thread (QThread)
│   └── utils/
│       ├── directory_handler.py         # Scansione batch directory
│       ├── file_grouper.py              # Raggruppamento nuvole correlate
│       ├── html_generator.py            # Generatore report HTML interattivi
│       ├── config_load.py               # Loader configurazioni JSON
│       └── file_handler.py              # Gestione I/O
├── requirements.txt
├── LICENSE
└── README.md
```

## Installazione

Clona il repository e installa le dipendenze richieste:

```bash
git clone https://github.com/ndree97/PC_identity.git
cd PC_identity
pip install -r requirements.txt
```

## Utilizzo

### 🖥️ Interfaccia Grafica Desktop (Qt)
Puoi avviare l'interfaccia grafica semplicemente eseguendo:

```bash
python gui.py
# oppure
python main.py
```
* Trascina direttamente file `.las`, `.laz`, `.e57` o `.ply` (o intere cartelle) nell'area di rilascio.
* Seleziona le opzioni desiderate e premi **Avvia Analisi**.
* Clicca su ogni riga per visualizzare la carta d'identità, il JSON formattato e aprire il report HTML nel browser.

### ⌨️ Riga di Comando (CLI)

#### Analisi Singolo File
```bash
python main.py -i input.las
# Supporta anche altri formati:
python main.py -i input.laz
python main.py -i scan.e57
python main.py -i mesh.ply
```
Salva automaticamente i risultati in `output/<filename>/<filename>_metadata.json` e genera il report `output/<filename>/<filename>_report.html`.

#### Analisi Directory in Batch
```bash
python main.py -d /percorso/directory
```
Scansiona ricorsivamente tutti i file supportati (`.las`, `.laz`, `.e57`, `.ply`), raggruppando i file correlati e generando statistiche aggregate e report HTML.

#### Con Stampa Dettagliata a Console
```bash
python main.py -i input.e57 -p
```

#### Specifica Directory di Configurazione
```bash
python main.py -i input.las -c config -p
```

#### Help CLI
```bash
python main.py -h
```

## Struttura Output JSON

Lo script produce un file JSON strutturato con le seguenti sezioni:

### `file_info`
Informazioni generali sul file fisico.

```json
{
  "filename": "sample_pointcloud.las",
  "filepath": "/path/to/data/sample_pointcloud.las",
  "file_size_mb": 125.50
}
```

### `header_info`
Versione LAS e formato dei punti.

```json
{
  "las_version": "1.2",
  "point_format": 3,
  "point_count": 8536817
}
```

**Cosa significano:**
- `las_version`: Versione dello standard LAS (1.0, 1.2, 1.4). Letto da `header.version`
- `point_format`: ID del formato punto (0-10). Formato 3 = GPS time + RGB color
- `point_count`: Numero totale di punti nella nuvola

### `point_cloud_nature`
Caratteristiche intrinseche della nuvola di punti.

```json
{
  "num_points": 8536817,
  "return_types": {
    "return_1": 8499494,
    "return_2": 37323
  },
  "classification": {
    "Unclassified": 8536817
  },
  "intensity_range": {
    "min": 0,
    "max": 65280,
    "mean": 24156.78,
    "std": 18932.45
  },
  "scan_angle_info": null
}
```

**Cosa significano:**
- `return_types`: Quanti punti sono first return, second return, ecc. (punti che rimbalzano una o più volte)
- `classification`: Distribuzione punti per classe (Ground=terreno, Building=edificio, Vegetation=vegetazione). Se tutti "Unclassified" = no processing
- `intensity_range`: Valore di riflessività laser (0-65535). Range ampio = buona qualità sensore. `mean` e `std` sono media e deviazione standard

### `coordinate_system`
Sistema di coordinate e georeferenziazione.

```json
{
  "scale": [0.001, 0.001, 0.001],
  "offset": [500000.0, 4600000.0, 100.0],
  "bounds": {
    "x": {"min": 500000.0, "max": 500150.0},
    "y": {"min": 4600000.0, "max": 4600120.0},
    "z": {"min": 100.0, "max": 135.0}
  },
  "spatial_extent": {
    "x_range": 150.0,
    "y_range": 120.0,
    "z_range": 35.0
  }
}
```

**Cosa significano:**
- `scale`: Moltiplicatore per convertire coordinate intere in float. Valori piccoli (0.0001) = maggiore precisione. Formula reale: `valore_float = valore_grezzo * scale + offset`
- `offset`: Base per le coordinate. Esempi: 431364.69 è probabilmente in UTM (geografico)
- `bounds`: Limiti geografici della nuvola (bounding box). I valori X, Y sono coordinate geografiche (UTM), Z è altezza
- `spatial_extent`: Dimensioni nuvola in metri sui tre assi (72m × 73m × 10.8m)

### `temporal_info`
Informazioni temporali.

```json
{
  "gps_time_range": {
    "min": 1234567890.123,
    "max": 1234567920.456
  },
  "file_creation_date": "2025-021"
}
```

**Cosa significano:**
- `gps_time_range`: Istante GPS (in secondi della settimana GPS). Se presente = acquisizione GNSS sincronizzata
- `file_creation_date`: Data creazione file. Formato `YYYY-DDD` (anno e giorno dell'anno)

### `software_metadata`
Tracce di software generatore.

```json
{
  "system_identifier": "LASzip",
  "generating_software": "LASzip DLL 3.4 r3 (191111)",
  "detected_software": null
}
```

**Cosa significano:**
- `system_identifier`: Identifica il sistema/hardware che ha creato il file. Letto da `header.system_identifier`
- `generating_software`: **Software che ha generato/modificato il file**. "LASzip DLL" significa che il file è stato **compresso con l'algoritmo LASzip** (perdita o no di dati)
  - Se fosse "CloudCompare v2.11" → file elaborato con CloudCompare
  - Se fosse "DJI" → drone DJI
  - Se fosse "FARO" → scanner terrestre FARO
- `detected_software`: Nome decodificato del software (es. "CloudCompare", "FARO", "DJI")

### `georeferencing`
Informazioni sul sistema di coordinate e georeferenziazione.

```json
{
  "georeferenced": true,
  "has_gps_time": true,
  "gps_time_type": "GPS Week Time",
  "has_geo_keys": true,
  "epsg_code": "EPSG:32633",
  "crs_wkt": "PROJCS[\"WGS 84 / UTM zone 33N\",GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223...]"
}
```

**Cosa significano:**
- `georeferenced`: `true` se il file contiene informazioni di georeferenziazione (non solo coordinate relative)
- `has_gps_time`: `true` se i punti hanno timestamp GPS (sincronizzazione temporale)
- `gps_time_type`: "GPS Week Time" (secondi dalla settimana GPS) o "GPS Standard Time (UTC)"
- `has_geo_keys`: `true` se contiene GeoKey records (metadati geografici)
- `epsg_code`: **Codice EPSG del sistema di coordinate**. Es:
  - `EPSG:32633` = WGS 84 / UTM zone 33N (vedi sopra)
    - `EPSG:7030` = Definisce i parametri dell'Ellissoide utilizzato (non delle coordinate, ne delle proiezioni).
  - `EPSG:4326` = WGS 84 lat/lon
  - `EPSG:3857` = Web Mercator
- `crs_wkt`: **Well-Known Text (WKT) - Descrizione completa del sistema di coordinate in formato testuale standardizzato**
  - `PROJCS` = Projected Coordinate System
  - `GEOGCS` = Geographic Coordinate System
  - `DATUM` = Datum (es. WGS_1984)
  - `SPHEROID` = Ellissoide (es. WGS 84 con semiasse 6378137m e eccentricità 298.257223)
  - `UTM zone 33N` = Proiezione UTM fascia 33 emisfero Nord

### `processing_history` (Post-processing Detection)

```json
{
  "is_post_processed": true,
  "detected_software_chain": [
    {
      "software": "CloudCompare",
      "field": "generating_software",
      "typical_operations": ["merge", "subsample", "classification", "registration"]
    }
  ],
  "processing_indicators": [
    "Non-standard scale factors",
    "Multiple classification classes (5) - likely classified",
    "Custom VLR found (ID: 2048)"
  ],
  "anomalies": [
    "High precision offset in X: 431364.6939545541",
    "File Source ID is 0 (often reset during processing)"
  ],
  "primary_processor": "CloudCompare"
}
```

**Cosa significano:**

- **`is_post_processed`**: `true` se il file è stato elaborato **dopo la scansione iniziale**. Indica modifiche, merge, classificazione automatica, ecc.

- **`detected_software_chain`**: Lista di software che hanno toccato il file in sequenza
  - Campo `field`: Dove è stata trovata l'informazione (header.system_identifier o header.generating_software)
  - `typical_operations`: Cosa tipicamente fa quel software (merge = fusione nuvole, subsample = decimazione, classification = classificazione automatica)

- **`processing_indicators`**: Indizi di elaborazione rilevati
  - "Non-standard scale factors" = Scale/offset irregolari (tipico CloudCompare)
  - "Multiple classification classes (5) - likely classified" = Punti sono stati classificati (Ground, Building, Vegetation, ecc.)
  - "Custom VLR found (ID: 2048)" = Record personalizzato aggiunto (Variable Length Record)

- **`anomalies`**: Anomalie nel file che suggeriscono modifiche
  - "High precision offset in X: 431364.69..." = Offset con molti decimali (CloudCompare spesso fa questo)
  - "File Source ID is 0" = ID sorgente azzerato (common when re-exporting)

- **`primary_processor`**: Il software che probabilmente ha **POST-PROCESSATO** il file (es. CloudCompare, LAStools, PDAL)

### `sensor_type`
Tipo di sensore inferito.

```json
{
  "characteristics": [
    "high_intensity_resolution",
    "rgb_data_present"
  ],
  "detected_sensor": null,
  "inferred_sensor_types": [
    {
      "sensor_type": "Terrestrial Laser Scanner (TLS)",
      "confidence": 82.5,
      "examples": ["Leica BLK360", "FARO Focus", "Riegl VZ-400"]
    },
    {
      "sensor_type": "Mobile LiDAR (MLS)",
      "confidence": 65.3,
      "examples": ["Velodyne HDL-64E", "Ouster OS1-128"]
    }
  ]
}
```

**Cosa significano:**

- **`characteristics`**: Proprietà rilevate nei dati
  - `high_intensity_resolution` = Range intensità > 1000 (buon sensore)
  - `rgb_data_present` = Punti contengono colore RGB
  - `multi-return_capable` = Sensore può rilevare multipli rimbalzi
  - `nir_data_present` = Canale Near Infrared presente

- **`detected_sensor`**: Se esplicitamente scritto nel metadata (es. "DJI", "Leica"). `null` se non trovato

- **`inferred_sensor_types`**: **Lista ordinata per confidenza del tipo di sensore probabile**, basata su:
  - Densità punti (punti/m³)
  - Accuratezza stimata (dalla scala)
  - Range massimo (dalle dimensioni bounding box)
  - Presenza RGB/NIR
  - Numero di returns

  Ogni voce contiene:
  - `sensor_type`: Categoria di sensore
  - `confidence`: Percentuale di compatibilità (0-100%)
  - `examples`: Modelli reali di quel sensore


<!-- ### revit_rotation_shift (NUOVO)

Calcolo dello shift rotazionale necessario per allineare la nuvola al nord reale in Revit.

```json
{
  "revit_rotation_shift": {
    "shift_degrees": 45.23,
    "description": "Ruota di 45.23 gradi in Revit per allineare a 0 gradi",
    "direction": "clockwise"
  },
  "bounding_box_analysis": {
    "center": {
      "x": 431351.075,
      "y": 4552358.244
    },
    "dimensions": {
      "width_x": 72.24,
      "height_y": 73.21
    },
    "aspect_ratio": 0.99,
    "orientation": "portrait"
  },
  "azimuth_analysis": {
    "azimut_degrees": 45.23,
    "azimut_radians": 0.789,
    "diagonal_angle_degrees": 44.5,
    "description": "La nuvola e' orientata a 45.23 gradi dal nord reale"
  },
  "georeferencing_info": {
    "epsg_code": "EPSG:32633",
    "georeferenced": true,
    "has_gps_time": true
  }
}
```

**Cosa significano:**

- `shift_degrees`: Angolo di rotazione (in gradi) da applicare in Revit. Valore positivo = rotazione oraria (clockwise), negativo = rotazione antioraria (counter-clockwise)
- `description`: Descrizione testuale dell'azione da compiere in Revit
- `direction`: Direzione della rotazione necessaria
- `bounding_box_analysis`: Analisi della bounding box della nuvola
  - `center`: Centroide della nuvola nei coordinate geografiche
  - `dimensions`: Larghezza e altezza della bounding box in metri
  - `aspect_ratio`: Rapporto aspetto (larghezza/altezza). Valori < 1 indicano nuvola piu' alta che larga (portrait)
  - `orientation`: "landscape" se piu' larga che alta, "portrait" altrimenti
- `azimuth_analysis`: Analisi dell'orientamento geografico
  - `azimut_degrees`: Angolo di orientamento della nuvola dal nord reale (0-360 gradi)
  - `azimut_radians`: Stesso valore in radianti
  - `diagonal_angle_degrees`: Angolo della diagonale principale della bounding box
  - `description`: Descrizione dell'orientamento relativo al nord
- `georeferencing_info`: Informazioni geografiche utilizzate nel calcolo

**Come usarlo in Revit:**

1. Leggi il file JSON generato dallo script
2. Estrai il valore di `shift_degrees` dalla sezione revit_rotation_shift
3. In Revit, ruota la nuvola di punti del valore `shift_degrees` attorno all'asse Z (asse verticale)
4. Se `shift_degrees` e' positivo, ruota in senso orario (direzione clockwise)
5. Se `shift_degrees` e' negativo, ruota in senso antiorario (direzione counter-clockwise)
6. La nuvola risultante sara' allineata al nord reale (0 gradi di sfasamento)

**Esempio di utilizzo in Revit:**

```c#
// Leggi il JSON
JObject metadata = JObject.Parse(File.ReadAllText("metadata.json"));
double shiftDegrees = (double)metadata["revit_rotation_shift"]["revit_rotation_shift"]["shift_degrees"];
string direction = (string)metadata["revit_rotation_shift"]["revit_rotation_shift"]["direction"];

// Applica la rotazione
XYZ rotationAxis = new XYZ(0, 0, 1); // Asse Z
double angleRadians = UnitUtils.ConvertToInternalUnits(shiftDegrees, DisplayUnitType.DUT_DEGREES);
Transform rotation = Transform.CreateRotationAroundAxis(rotationAxis, angleRadians);

// Applica alle coordinate della nuvola di punti...
``` -->

---

## Spiegazione Chiavi Specifiche

### `vlr_records` (Variable Length Records)

```json
"vlr_records": [
  {
    "record_id": 34735,
    "user_id": "TIFF",
    "description": "GeoKeyDirectoryTag"
  },
  {
    "record_id": 2112,
    "user_id": "LASF_Projection",
    "description": "OGC Well Known Text (WKT)"
  },
  {
    "record_id": 2048,
    "user_id": "CloudCompare",
    "description": "Custom metadata"
  }
]
```

**Cosa sono:** Record metadati extra aggiuntivi nel file LAS. Si trovano dopo l'header standard.

| ID | Significato |
|:---:|:---|
| **34735** | GeoKeyDirectoryTag - Contiene chiavi di georeferenziazione |
| **34736** | GeoDoubleParamsTag - Parametri georeferenziazione double-precision |
| **2112** | OGC Well-Known Text - Descrizione CRS in formato WKT |
| **2048+** | Custom/Privati - Aggiunti da software (es. CloudCompare) |

**Importanza:** VLR personalizzati (ID > 100) indicano che il file è stato **POST-PROCESSATO**

### `anomalies` (Anomalie rilevate)

```json
"anomalies": [
  "Unusual scale values (> 1.0)",
  "Non-uniform scales: [0.1, 0.1, 0.001]",
  "High precision offset in X: 431364.6939545541",
  "File Source ID is 0 (often reset during processing)"
]
```

**Significato:** Indicatori che il file è stato **modificato** dopo la scansione originale.

- **Scale anomale** = CloudCompare spesso crea scale strane
- **Offset alta precisione** = Non standard, suggerisce post-processing
- **File Source ID = 0** = Resettato durante re-export

### `processing_indicators` (Indicatori di processing)

```json
"processing_indicators": [
  "Custom VLR found (ID: 2048)",
  "All points classified as Ground",
  "Multiple classification classes (5) - likely classified",
  "GPS time removed or zeroed"
]
```

**Significato:** Azioni di processing rilevate sulla nuvola.

- Custom VLR = Software ha aggiunto dati personalizzati
- Uniform classification = Filtro applicato (es. solo terreno estratto)
- Molte classi = File è stato **classificato** (automated o manuale)
- GPS time zeroed = Timestamp rimosso

### `crs_wkt` - Well-Known Text (WKT)

```json
PROJCS["WGS 84 / UTM zone 33N",
  GEOGCS["WGS 84",
    DATUM["WGS_1984",
      SPHEROID["WGS 84",6378137,298.257223563]
    ],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433]
  ],
  PROJECTION["Transverse_Mercator"],
  PARAMETER["latitude_of_origin",0],
  PARAMETER["central_meridian",15],
  PARAMETER["false_easting",500000],
  PARAMETER["false_northing",0],
  UNIT["metre",1]
]
```

**Cosa è:** Standard testuale per descrivere qualsiasi sistema di coordinate geografico.

**Componenti:**
- **PROJCS** = Projected Coordinate System (coordinate piane, non geografiche)
- **GEOGCS** = Geographic Coordinate System base (lat/lon)
- **DATUM** = Modello della terra (WGS_1984 è lo standard GPS)
- **SPHEROID** = Ellissoide (forma della terra)
  - `6378137` = semiasse maggiore (6378.137 km, raggio all'equatore)
  - `298.257223563` = inverse flattening (eccentricità)
- **PROJECTION** = Tipo proiezione (Transverse_Mercator per UTM)
- **PARAMETERS** = Parametri proiezione
  - `central_meridian=15` = meridiano centrale fascia 33
- **UTM zone 33N** = Fascia 33, emisfero Nord

**In pratica:** "Le coordinate sono in UTM (proiezione piana), fascia 33N, basate su WGS84"

### `generating_software` - Interpretazione

```bash
"generating_software": "LASzip DLL 3.4 r3 (191111)"
```

**Cosa significa:**
- **LASzip** = Software/libreria di **compressione LAS**
- **DLL** = Dynamic Link Library (è una libreria, non l'applicazione principale)
- **3.4** = Versione
- **r3** = Revision 3
- **(191111)** = Data di build (2019-11-11)

**Interpretazione:**
- ❌ NON significa "generato da LASzip"
- ✅ Significa "il file è stato **compresso/decompresso** con LASzip"
- Il vero generatore potrebbe essere CloudCompare, PDAL, o altro software che usa LASzip internamente
- Assieme a `system_identifier` aiuta a ricostruire la catena di processing

**Altri esempi comuni:**
- `"CloudCompare v2.11.3"` = Elaborato con CloudCompare
- `"FARO LS 2023"` = Scanner terrestre FARO
- `"DJI Zenmuse L1"` = Drone DJI con sensore Zenmuse L1
- `"LAStools by rapidlasso"` = Elaborato con LAStools
- `"PDAL 2.4"` = Elaborato con PDAL

---

## Esempio Completo Annotato

```json
{
  "file_info": {
    "filename": "sample_pointcloud.las",
    "filepath": "/path/to/data/sample_pointcloud.las",
    "file_size_mb": 125.50
  },
  "header_info": {
    "las_version": "1.2",
    "point_format": 3,
    "point_count": 8536817
  },
  "punto_cloud_nature": {
    "num_points": 8536817,
    "return_types": {
      "return_1": 8499494,
      "return_2": 37323
    },
    "classification": {
      "Unclassified": 8536817
    },
    "intensity_range": {
      "min": 0,
      "max": 65280,
      "mean": 24156.78,
      "std": 18932.45
    },
    "scan_angle_info": null
  },
  "coordinate_system": {
    "scale": [0.001, 0.001, 0.001],
    "offset": [500000.0, 4600000.0, 100.0],
    "bounds": {
      "x": {"min": 500000.0, "max": 500150.0},
      "y": {"min": 4600000.0, "max": 4600120.0},
      "z": {"min": 100.0, "max": 135.0}
    },
    "spatial_extent": {
      "x_range": 150.0,
      "y_range": 120.0,
      "z_range": 35.0
    }
  },
  "temporal_info": {
    "gps_time_range": {
      "min": 1234567890.123,
      "max": 1234567920.456
    },
    "file_creation_date": "2025-021"
  },
  "software_metadata": {
    "system_identifier": "LASzip",
    "generating_software": "LASzip DLL 3.4 r3 (191111)",
    "detected_software": null
  },
  "georeferencing": {
    "georeferenced": true,
    "coordinate_reference_system": null,
    "epsg_code": "EPSG:32633",
    "has_gps_time": true,
    "gps_time_type": "GPS Week Time",
    "has_geo_keys": true,
    "crs_wkt": "PROJCS[\"WGS 84 / UTM zone 33N\",GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223...]"
  },
  "processing_history": {
    "is_post_processed": false,
    "detected_software_chain": [],
    "processing_indicators": [],
    "anomalies": [
      "File Source ID is 0 (often reset during processing)"
    ]
  },
  "sensor_type": {
    "detected_sensor": null,
    "characteristics": ["multi-return_capable", "high_intensity_resolution", "rgb_data_present"],
    "inferred_sensor_types": [
      {
        "sensor_type": "Terrestrial Laser Scanner (TLS)",
        "confidence": 78.5,
        "examples": ["Leica BLK360", "FARO Focus", "Riegl VZ-400"]
      },
      {
        "sensor_type": "Mobile LiDAR (MLS)",
        "confidence": 65.3,
        "examples": ["Velodyne HDL-64E", "Ouster OS1-128"]
      }
    ]
  }
}
```

---

## Configurazione

### `config/sensor_database.json`
Modifica questo file per aggiungere o modificare i profili di sensori LiDAR.

### `config/software_signatures.json`
Aggiungi nuove firme software per rilevare ulteriori strumenti di processing.

### `config/classification_map.json`
Personalizza la mappa delle classificazioni LAS.

---

## Workflow Tipico

1. **Acquisizione**: Sensore LiDAR acquisisce nuvola di punti
2. **Export iniziale**: Software sensore esporta in LAS
   - Header contiene `generating_software` = "DJI" o "Leica" o "Riegl"
3. **Post-processing** (opzionale): Utente elabora con CloudCompare
   - Header `generating_software` ora = "CloudCompare v2.11"
   - Vengono aggiunti VLR personalizzati
   - Punti potrebbero essere classificati, filtrati, merged
4. **Export finale**: File salvato
   - Se compresso, `generating_software` = "LASzip DLL"
   - `processing_history` mostra la catena di elaborazioni

Questo script **ricostruisce** questa storia leggendo il file!
