from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class HTMLGenerator:
    """Genera report HTML con tabella riassuntiva dei parametri chiave."""

    def __init__(self):
        self.template_css = """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px solid #007acc;
                padding-bottom: 10px;
            }
            .summary {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
            }
            .summary-item {
                text-align: center;
                padding: 10px;
            }
            .summary-number {
                font-size: 24px;
                font-weight: bold;
                color: #007acc;
            }
            .summary-label {
                color: #666;
                font-size: 14px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th {
                background-color: #007acc;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                position: sticky;
                top: 0;
            }
            td {
                padding: 10px 12px;
                border-bottom: 1px solid #ddd;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .error {
                color: #dc3545;
                font-weight: bold;
            }
            .success {
                color: #28a745;
            }
            .filename {
                font-family: 'Courier New', monospace;
                font-size: 14px;
                max-width: 200px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .dim {
                text-align: center;
                font-family: 'Courier New', monospace;
            }
            .num-points {
                text-align: right;
                font-family: 'Courier New', monospace;
                font-weight: 600;
            }
            .epsg {
                text-align: center;
                font-weight: 600;
            }
            .crs {
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-size: 12px;
            }
            .source {
                max-width: 150px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .file-size {
                text-align: right;
                font-family: 'Courier New', monospace;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 14px;
            }
            .stats-bar {
                background-color: #e9ecef;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
            }

            /* Stili per gruppi */
            .group-section {
                margin-bottom: 40px;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                overflow: hidden;
            }
            .group-header {
                background-color: #6c757d;
                color: white;
                padding: 15px;
                font-size: 18px;
                font-weight: 600;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .group-header.split-cloud {
                background-color: #28a745;
            }
            .group-header.temporal-sequence {
                background-color: #fd7e14;
            }
            .group-header.related-files {
                background-color: #6f42c1;
            }
            .group-stats {
                display: flex;
                gap: 20px;
                font-size: 14px;
                font-weight: normal;
            }
            .group-stat {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .group-content {
                padding: 20px;
            }

            /* Stili per singolo file */
            .single-file-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }
            .file-details {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .detail-row {
                display: flex;
                padding: 8px 0;
                border-bottom: 1px solid #e9ecef;
            }
            .detail-row:last-child {
                border-bottom: none;
            }
            .detail-label {
                font-weight: 600;
                color: #495057;
                width: 150px;
                flex-shrink: 0;
            }
            .detail-value {
                color: #212529;
                flex-grow: 1;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .summary {
                    flex-direction: column;
                }
                .group-header {
                    flex-direction: column;
                    text-align: center;
                    gap: 10px;
                }
                .detail-row {
                    flex-direction: column;
                }
                .detail-label {
                    width: auto;
                }
            }
        </style>
        """

    def _generate_summary_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcola statistiche riassuntive."""
        total_files = len(results)
        successful_files = sum(1 for r in results if 'error' not in r['key_params'])
        error_files = total_files - successful_files

        # Total points
        total_points = 0
        successful_results = [r for r in results if 'error' not in r['key_params']]
        for result in successful_results:
            try:
                num_points_str = result['key_params']['num_points'].replace(' ', '')
                if num_points_str and num_points_str != 'N/D':
                    total_points += int(num_points_str)
            except:
                pass

        # Format total points
        if total_points > 0:
            total_points_str = f"{total_points:,}".replace(',', ' ')
        else:
            total_points_str = "N/D"

        # File extensions distribution
        extensions = {}
        for result in results:
            ext = Path(result['filename']).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'error_files': error_files,
            'total_points': total_points_str,
            'extensions': extensions
        }

    def generate_single_file_report(self, metadata: Dict[str, Any], output_path: Path, file_path: str):
        """Genera un report HTML completo per un singolo file con TUTTI i metadati."""

        if not metadata:
            print("Nessun metadato da visualizzare nel report HTML.")
            return

        # Estrai informazioni chiave
        key_params = self._extract_single_file_key_params(metadata, file_path)

        # Genera sezioni complete dei metadati
        metadata_sections = self._generate_metadata_sections(metadata)

        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Report Completo - {key_params['filename']}</title>
            {self.template_css}
            {self._get_complete_css()}
        </head>
        <body>
            <div class="container">
                <div class="single-file-header">
                    <h1>📁 Report Completo File LAS</h1>
                    <h2>{key_params['filename']}</h2>
                    <p>Report completo con tutti i metadati estratti</p>
                </div>

                <!-- Riepilogo Chiave -->
                <div class="key-summary">
                    <h3>📋 Riepilogo Parametri Chiave</h3>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <span class="label">File Size:</span>
                            <span class="value">{key_params.get('file_size', 'N/D')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Numero Punti:</span>
                            <span class="value">{key_params['num_points']}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">EPSG:</span>
                            <span class="value">{key_params['epsg']}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Source:</span>
                            <span class="value">{key_params.get('source', 'N/D')}</span>
                        </div>
                    </div>
                </div>

                <!-- Metadati Completi -->
                <div class="metadata-complete">
                    <h3>🔍 Tutti i Metadati</h3>
                    {metadata_sections}
                </div>

                <!-- JSON Grezzo -->
                <div class="json-section">
                    <button class="toggle-btn" onclick="toggleJson('json-content')">
                        📄 Mostra/Nascondi JSON Completo
                    </button>
                    <pre id="json-content" style="display: none;"><code>{self._format_json(metadata)}</code></pre>
                </div>

                <div class="footer">
                    <p>Report generato il {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p> creato con LAS Metadata Extractor</p>
                </div>
            </div>

            <script>
                function toggleJson(id) {{
                    var element = document.getElementById(id);
                    if (element.style.display === 'none' || element.style.display === '') {{
                        element.style.display = 'block';
                    }} else {{
                        element.style.display = 'none';
                    }}
                }}

                // Funzione per espandere/comprimere sezioni
                function toggleSection(sectionId) {{
                    var section = document.getElementById(sectionId);
                    var icon = document.getElementById('icon-' + sectionId);

                    // Gestisce sia il caso display:none che display:'' (valore iniziale)
                    if (section.style.display === 'none' || section.style.display === '') {{
                        section.style.display = 'block';
                        icon.textContent = '▼';
                    }} else {{
                        section.style.display = 'none';
                        icon.textContent = '▶';
                    }}
                }}

                // Inizializza tutte le icone correttamente al caricamento della pagina
                document.addEventListener('DOMContentLoaded', function() {{
                    // Assicura che tutte le sezioni siano nascoste e le icone siano ▶
                    var sections = document.querySelectorAll('.section-content');
                    sections.forEach(function(section) {{
                        section.style.display = 'none';
                    }});

                    var icons = document.querySelectorAll('.section-icon');
                    icons.forEach(function(icon) {{
                        icon.textContent = '▶';
                    }});
                }});
            </script>
        </body>
        </html>
        """

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Report HTML completo salvato in: {output_path}")

        # Mostra link cliccabile per aprire l'HTML
        import webbrowser
        import os

        # Converte path relativo in assoluto per Windows
        abs_path = os.path.abspath(output_path)
        # Per Windows: C:\path -> file:///C:/path
        file_url = f"file:///{abs_path.replace('\\', '/').replace(':', ':/').replace(' ', '%20')}"

        print(f"🌐 Link per aprire il report:")
        print(f"   {file_url}")

        # Tenta di aprire automaticamente il browser
        try:
            webbrowser.open(file_url)
            print(f"🚀 Report aperto nel browser predefinito")
        except Exception as e:
            print(f"⚠️ Impossibile aprire automaticamente: {e}")
            print(f"   Copia e incolla il link qui sopra nel tuo browser")

    def generate_report(self, results: List[Dict[str, Any]], output_path: Path, groups: Dict[str, List[Dict[str, Any]]] = None):
        """Genera il report HTML completo con supporto per gruppi."""

        if not results:
            print("Nessun risultato da visualizzare nel report HTML.")
            return

        stats = self._generate_summary_stats(results)

        # HTML content
        if groups:
            html_content = self._generate_grouped_html(results, groups, stats)
        else:
            html_content = self._generate_standard_html(results, stats)

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Report HTML salvato in: {output_path}")

    def _generate_grouped_html(self, results: List[Dict[str, Any]], groups: Dict[str, List[Dict[str, Any]]], stats: Dict[str, Any]) -> str:
        """Genera HTML con sezioni raggruppate."""

        groups_html = ""
        for group_name, group_results in groups.items():
            if not group_results:
                continue

            # Calcola statistiche del gruppo
            group_stats = self._calculate_group_stats(group_results)

            # Determina il tipo di gruppo
            group_type = self._determine_group_type(group_name, group_results)
            group_class = f"group-header {group_type.replace('_', '-')}"

            # Header del gruppo
            group_html = f"""
            <div class="group-section">
                <div class="{group_class}">
                    <span>{group_name}</span>
                    <div class="group-stats">
                        <div class="group-stat">📁 {len(group_results)} file</div>
                        <div class="group-stat">🔢 {group_stats['total_points']} punti totali</div>
                        <div class="group-stat">📏 {group_stats['combined_dim']}</div>
                    </div>
                </div>
                <div class="group-content">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Nome File</th>
                                <th>Dimensioni (X×Y×Z)</th>
                                <th>N. Punti</th>
                                <th>EPSG</th>
                                <th>CRS</th>
                                <th>Source</th>
                                <th>File Size</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(group_results)}
                        </tbody>
                    </table>
                </div>
            </div>
            """
            groups_html += group_html

        return f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Report Analisi File LAS</title>
            {self.template_css}
        </head>
        <body>
            <div class="container">
                <h1>📊 Report Analisi File LAS/LAZ/E57/PLY</h1>

                <div class="summary">
                    <div class="summary-item">
                        <div class="summary-number">{stats['total_files']}</div>
                        <div class="summary-label">File Totali</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{len(groups)}</div>
                        <div class="summary-label">Gruppi Identificati</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number success">{stats['successful_files']}</div>
                        <div class="summary-label">Elaborati con Successo</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{stats['total_points']}</div>
                        <div class="summary-label">Punti Totali</div>
                    </div>
                </div>

                <div class="stats-bar">
                    <strong>Distribuzione formati:</strong>
                    {', '.join([f"{ext} ({count})" for ext, count in stats['extensions'].items()])}
                </div>

                {groups_html}

                <div class="footer">
                    <p>Report generato il {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p> creato con LAS Metadata Extractor</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_standard_html(self, results: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Genera HTML standard senza raggruppamento."""
        return f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Report Analisi File LAS</title>
            {self.template_css}
        </head>
        <body>
            <div class="container">
                <h1>📊 Report Analisi File LAS/LAZ/E57/PLY</h1>

                <div class="summary">
                    <div class="summary-item">
                        <div class="summary-number">{stats['total_files']}</div>
                        <div class="summary-label">File Totali</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number success">{stats['successful_files']}</div>
                        <div class="summary-label">Elaborati con Successo</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number error">{stats['error_files']}</div>
                        <div class="summary-label">Errori</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number">{stats['total_points']}</div>
                        <div class="summary-label">Punti Totali</div>
                    </div>
                </div>

                <div class="stats-bar">
                    <strong>Distribuzione formati:</strong>
                    {', '.join([f"{ext} ({count})" for ext, count in stats['extensions'].items()])}
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Nome File</th>
                            <th>Dimensioni (X×Y×Z)</th>
                            <th>N. Punti</th>
                            <th>EPSG</th>
                            <th>CRS</th>
                            <th>Source</th>
                            <th>File Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_table_rows(results)}
                    </tbody>
                </table>

                <div class="footer">
                    <p>Report generato il {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p> creato con LAS Metadata Extractor</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_table_rows(self, results: List[Dict[str, Any]]) -> str:
        """Genera le righe della tabella HTML."""
        rows_html = ""

        for i, result in enumerate(results, 1):
            key_params = result['key_params']

            if 'error' in key_params:
                # Riga di errore
                rows_html += f"""
                <tr>
                    <td>{i}</td>
                    <td class="filename">{key_params['filename']}</td>
                    <td class="error" colspan="6">{key_params['error']}</td>
                </tr>
                """
            else:
                # Riga normale
                rows_html += f"""
                <tr>
                    <td>{i}</td>
                    <td class="filename" title="{key_params['filepath']}">{key_params['filename']}</td>
                    <td class="dim">{key_params['dim']}</td>
                    <td class="num-points">{key_params['num_points']}</td>
                    <td class="epsg">{key_params['epsg']}</td>
                    <td class="crs" title="{key_params.get('crs', 'N/D')}">{key_params.get('crs', 'N/D')}</td>
                    <td class="source" title="{key_params.get('source', 'N/D')}">{key_params.get('source', 'N/D')}</td>
                    <td class="file-size">{key_params.get('file_size', 'N/D')}</td>
                </tr>
                """

        return rows_html

    def _extract_single_file_key_params(self, metadata: Dict[str, Any], file_path: str) -> Dict[str, str]:
        """Estrae i parametri chiave per un singolo file."""
        from pathlib import Path

        file_path_obj = Path(file_path)

        # File size
        try:
            file_size = file_path_obj.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            elif file_size < 1024 * 1024 * 1024:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            else:
                size_str = f"{file_size/(1024*1024*1024):.1f} GB"
        except:
            size_str = "N/D"

        # Dimensioni
        dim = "N/D"
        try:
            coord_sys = metadata.get('coordinate_system', {})
            if 'spatial_extent' in coord_sys:
                extent = coord_sys['spatial_extent']
                x_dim = extent.get('x_range', 0)
                y_dim = extent.get('y_range', 0)
                z_dim = extent.get('z_range', 0)
                dim = f"{x_dim:.2f} × {y_dim:.2f} × {z_dim:.2f}"
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
                if 'EPSG' in epsg:
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
                if len(crs) > 100:
                    crs = crs[:100] + "..."
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

        return {
            'filename': file_path_obj.name,
            'dim': dim,
            'num_points': num_points,
            'epsg': epsg,
            'crs': crs,
            'source': source,
            'file_size': size_str
        }

    def _calculate_group_stats(self, group_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calcola statistiche aggregate per un gruppo."""
        total_points = 0
        combined_dims = []

        for result in group_results:
            if 'error' not in result['key_params']:
                try:
                    # Total points
                    num_points_str = result['key_params']['num_points'].replace(' ', '')
                    if num_points_str and num_points_str != 'N/D':
                        total_points += int(num_points_str)

                    # Dimensioni (semplice somma per ora)
                    dim_str = result['key_params']['dim']
                    if '×' in dim_str and dim_str != 'N/D':
                        parts = dim_str.split('×')
                        if len(parts) >= 3:
                            try:
                                x_dim = float(parts[0])
                                y_dim = float(parts[1])
                                z_dim = float(parts[2])
                                combined_dims.append((x_dim, y_dim, z_dim))
                            except:
                                pass
                except:
                    continue

        # Calcola dimensioni combinate (bounding box)
        if combined_dims:
            max_x = max(dim[0] for dim in combined_dims)
            max_y = max(dim[1] for dim in combined_dims)
            max_z = max(dim[2] for dim in combined_dims)
            combined_dim_str = f"{max_x:.1f}×{max_y:.1f}×{max_z:.1f}"
        else:
            combined_dim_str = "N/D"

        return {
            'total_points': f"{total_points:,}".replace(',', ' ') if total_points > 0 else "N/D",
            'combined_dim': combined_dim_str
        }

    def _determine_group_type(self, group_name: str, group_results: List[Dict[str, Any]]) -> str:
        """Determina il tipo di gruppo per lo stile CSS."""
        if len(group_results) == 1:
            return "single"

        # Se il nome del gruppo contiene "part", "chunk", "segment", etc.
        if any(keyword in group_name.lower() for keyword in ['part', 'chunk', 'segment', 'tile']):
            return "split_cloud"

        # Controlla se ci sono pattern numerici nel nome dei file
        import re
        has_numbers = any(bool(re.search(r'\d+', result['filename'])) for result in group_results)
        if has_numbers:
            return "temporal_sequence"

        return "related_files"

    def _get_complete_css(self) -> str:
        """CSS aggiuntivo per report completi."""
        return """
        <style>
            /* Stili aggiuntivi per report completi */
            .key-summary {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 30px;
            }
            .key-summary h3 {
                color: #495057;
                margin-bottom: 15px;
                text-align: center;
            }
            .summary-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .summary-item {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #e9ecef;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            .summary-item .label {
                font-weight: 600;
                color: #6c757d;
                margin-bottom: 5px;
                font-size: 14px;
            }
            .summary-item .value {
                font-size: 18px;
                font-weight: bold;
                color: #007acc;
            }

            .metadata-complete {
                margin-bottom: 30px;
            }
            .metadata-section {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-bottom: 20px;
                overflow: hidden;
            }
            .section-header {
                background-color: #f8f9fa;
                padding: 15px 20px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #dee2e6;
                font-weight: 600;
                color: #495057;
            }
            .section-header:hover {
                background-color: #e9ecef;
            }
            .section-icon {
                font-size: 12px;
                color: #6c757d;
                transition: transform 0.2s;
            }
            .section-content {
                padding: 20px;
                display: none;
            }
            .section-content.show {
                display: block;
            }

            .metadata-table {
                width: 100%;
                border-collapse: collapse;
            }
            .metadata-table td {
                padding: 8px 12px;
                border-bottom: 1px solid #f1f3f4;
                vertical-align: top;
            }
            .metadata-table td:first-child {
                font-weight: 600;
                color: #495057;
                width: 200px;
                background-color: #f8f9fa;
            }
            .metadata-table tr:last-child td {
                border-bottom: none;
            }

            .json-section {
                margin-top: 30px;
            }
            .toggle-btn {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: background-color 0.2s;
            }
            .toggle-btn:hover {
                background-color: #0056b3;
            }
            .json-section pre {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 20px;
                margin-top: 15px;
                overflow-x: auto;
                font-size: 12px;
                line-height: 1.4;
            }
            .json-section code {
                color: #495057;
            }

            @media (max-width: 768px) {
                .summary-grid {
                    grid-template-columns: 1fr;
                }
                .metadata-table td:first-child {
                    width: 120px;
                }
            }
        </style>
        """

    def _generate_metadata_sections(self, metadata: Dict[str, Any]) -> str:
        """Genera sezioni HTML per tutti i metadati."""
        sections = ""

        # Sezione File Info
        if 'file_info' in metadata:
            sections += self._generate_section("📁 Informazioni File", "file-info", metadata['file_info'])

        # Sezione Header Info
        if 'header_info' in metadata:
            sections += self._generate_section("📋 Header LAS", "header-info", metadata['header_info'])

        # Sezione Coordinate System
        if 'coordinate_system' in metadata:
            sections += self._generate_section("🌐 Sistema di Coordinate", "coordinate-system", metadata['coordinate_system'])

        # Sezione Punto Cloud Nature
        if 'punto_cloud_nature' in metadata:
            sections += self._generate_section("☁️ Natura Nuvola di Punti", "punto-cloud", metadata['punto_cloud_nature'])

        # Sezione Temporal Info
        if 'temporal_info' in metadata:
            sections += self._generate_section("⏰ Informazioni Temporali", "temporal-info", metadata['temporal_info'])

        # Sezione Software Metadata
        if 'software_metadata' in metadata:
            sections += self._generate_section("💻 Software Metadata", "software-metadata", metadata['software_metadata'])

        # Sezione Georeferencing
        if 'georeferencing' in metadata:
            sections += self._generate_section("🗺️ Georeferenziazione", "georeferencing", metadata['georeferencing'])

        # Sezione Sensor Type (se presente)
        if 'sensor_type' in metadata:
            sections += self._generate_section("📡 Tipo Sensore", "sensor-type", metadata['sensor_type'])

        # Sezione Processing History (se presente)
        if 'processing_history' in metadata:
            sections += self._generate_section("⚙️ Storia Processamento", "processing-history", metadata['processing_history'])

        return sections

    def _generate_section(self, title: str, section_id: str, data: Dict[str, Any]) -> str:
        """Genera una sezione HTML con tabella di metadati."""
        rows_html = self._generate_data_rows(data)

        return f"""
        <div class="metadata-section">
            <div class="section-header" onclick="toggleSection('{section_id}')">
                <span>{title}</span>
                <span id="icon-{section_id}" class="section-icon">▶</span>
            </div>
            <div id="{section_id}" class="section-content">
                <table class="metadata-table">
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_data_rows(self, data: Any, parent_key: str = "") -> str:
        """Genera righe HTML per dati strutturati."""
        if isinstance(data, dict):
            rows = ""
            for key, value in data.items():
                full_key = f"{parent_key}.{key}" if parent_key else key

                if isinstance(value, (dict, list)):
                    # Dati complessi - ricorsivo
                    if isinstance(value, dict) and value:
                        # Per dizionari non vuoti, crea sottosezione
                        sub_rows = self._generate_data_rows(value, full_key)
                        if sub_rows.strip():
                            rows += f"""
                            <tr>
                                <td colspan="2" style="padding: 0;">
                                    <div style="margin-left: 20px; margin-bottom: 10px;">
                                        <strong style="color: #007acc;">{key}:</strong>
                                        <table style="margin-top: 5px;">
                                            <tbody>
                                                {sub_rows}
                                            </tbody>
                                        </table>
                                    </div>
                                </td>
                            </tr>
                            """
                        else:
                            rows += f"<tr><td>{key}</td><td>Vuoto</td></tr>"
                    elif isinstance(value, list) and value:
                        # Per liste
                        if len(value) > 0 and isinstance(value[0], (dict, list)):
                            # Lista di oggetti complessi
                            rows += f"""
                            <tr>
                                <td>{key}</td>
                                <td>
                                    <details>
                                        <summary>{len(value)} elementi</summary>
                                        <div style="margin-left: 20px; margin-top: 10px;">
                                            {self._generate_list_items(value)}
                                        </div>
                                    </details>
                                </td>
                            </tr>
                            """
                        else:
                            # Lista semplice
                            list_str = ", ".join(str(v) for v in value[:10])  # Limita a 10 elementi
                            if len(value) > 10:
                                list_str += f" ... (+{len(value)-10} altri)"
                            rows += f"<tr><td>{key}</td><td>[{list_str}]</td></tr>"
                    else:
                        rows += f"<tr><td>{key}</td><td>{value}</td></tr>"
                else:
                    # Dati semplici
                    display_value = self._format_value(value)
                    rows += f"<tr><td>{key}</td><td>{display_value}</td></tr>"
            return rows
        elif isinstance(data, list):
            return self._generate_list_items(data)
        else:
            return f"<tr><td>{parent_key or 'value'}</td><td>{self._format_value(data)}</td></tr>"

    def _generate_list_items(self, items: list) -> str:
        """Genera HTML per liste di elementi."""
        if not items:
            return "Vuoto"

        items_html = ""
        for i, item in enumerate(items[:5]):  # Limita a 5 elementi per non appesantire
            if isinstance(item, (dict, list)):
                # Per dizionari, genera una tabella annidata valida
                sub_rows = self._generate_data_rows(item)
                if sub_rows.strip():
                    items_html += f"""
                    <div style="margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;">
                        <strong>Elemento {i+1}:</strong>
                        <table style="width: 100%; margin-top: 8px; border-collapse: collapse;">
                            <tbody>
                                {sub_rows}
                            </tbody>
                        </table>
                    </div>
                    """
                else:
                    items_html += f"""
                    <div style="margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;">
                        <strong>Elemento {i+1}:</strong> Vuoto
                    </div>
                    """
            else:
                items_html += f"<div style='margin-bottom: 5px;'>• {self._format_value(item)}</div>"

        if len(items) > 5:
            items_html += f"<div style='color: #6c757d; font-style: italic;'>... e altri {len(items)-5} elementi</div>"

        return items_html

    def _format_value(self, value: Any) -> str:
        """Formatta un valore per la visualizzazione HTML."""
        if value is None:
            return "N/D"
        elif isinstance(value, bool):
            return "✓ Sì" if value else "✗ No"
        elif isinstance(value, (int, float)):
            return f"{value:,}" if isinstance(value, int) else f"{value:.6f}"
        elif isinstance(value, str):
            # Gestisci stringhe lunghe
            if len(value) > 200:
                return f"{value[:200]}..."
            return value
        else:
            return str(value)

    def _format_number(self, num: int) -> str:
        """Formatta un numero con separatori delle migliaia usando spazi."""
        return f"{num:,}".replace(',', ' ') if isinstance(num, int) else str(num)

    def _format_json(self, metadata: Dict[str, Any]) -> str:
        """Formatta i metadati come JSON formattato."""
        import json
        try:
            return json.dumps(metadata, indent=2, ensure_ascii=False, default=str)
        except:
            return str(metadata)

    def generate_group_report(self, group_name: str, group_results: List[Dict[str, Any]], output_path: Path,
                             common_metadata: Dict[str, Any], total_points: int, total_size: str):
        """Genera un report HTML per un gruppo di file correlati."""

        if not group_results:
            print("Nessun risultato da visualizzare nel report HTML del gruppo.")
            return

        # Genera HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Report Gruppo - {group_name}</title>
            {self.template_css}
            {self._get_complete_css()}
        </head>
        <body>
            <div class="container">
                <div class="single-file-header">
                    <h1>🌩️ Report Gruppo File LAS</h1>
                    <h2>{group_name}</h2>
                    <p>Report consolidato per {len(group_results)} file correlati</p>
                </div>

                <!-- Riepilogo Gruppo -->
                <div class="key-summary">
                    <h3>📊 Statistiche Aggregate del Gruppo</h3>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <span class="label">File Totali:</span>
                            <span class="value">{len(group_results)}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Punti Totali:</span>
                            <span class="value">{self._format_number(total_points)}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Dimensione Totale:</span>
                            <span class="value">{total_size}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">EPSG:</span>
                            <span class="value">{common_metadata.get('epsg_code', 'N/D')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">Source:</span>
                            <span class="value">{common_metadata.get('source', 'N/D')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">LAS Version:</span>
                            <span class="value">{common_metadata.get('las_version', 'N/D')}</span>
                        </div>
                    </div>
                </div>

                <!-- Metadati Comuni -->
                <div class="metadata-complete">
                    <h3>🔧 Metadati Comuni (Identici per tutti i file)</h3>
                    {self._generate_common_metadata_section(common_metadata)}
                </div>

                <!-- Dettagli File Individuali -->
                <div class="metadata-complete">
                    <h3>📁 Dettagli File Individuali</h3>
                    {self._generate_individual_files_table(group_results)}
                </div>

                <div class="footer">
                    <p>Report gruppo generato il {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p> creato con LAS Metadata Extractor</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Report HTML gruppo salvato in: {output_path}")

        # Mostra link cliccabile per aprire l'HTML
        import webbrowser
        import os

        # Converte path relativo in assoluto per Windows
        abs_path = os.path.abspath(output_path)
        # Per Windows: C:\path -> file:///C:/path
        file_url = f"file:///{abs_path.replace('\\', '/').replace(':', ':/').replace(' ', '%20')}"

        print(f"🌐 Link per aprire il report gruppo:")
        print(f"   {file_url}")

        # Tenta di aprire automaticamente il browser
        try:
            webbrowser.open(file_url)
            print(f"🚀 Report gruppo aperto nel browser predefinito")
        except Exception as e:
            print(f"⚠️ Impossibile aprire automaticamente: {e}")
            print(f"   Copia e incolla il link qui sopra nel tuo browser")

    def _generate_common_metadata_section(self, common_metadata: Dict[str, Any]) -> str:
        """Genera sezione per metadati comuni."""
        rows_html = ""

        # EPSG
        epsg = common_metadata.get('epsg_code', 'N/D')
        rows_html += f"<tr><td>EPSG</td><td>{epsg}</td></tr>"

        # Source
        source = common_metadata.get('source', 'N/D')
        rows_html += f"<tr><td>Software</td><td>{source}</td></tr>"

        # LAS Version
        version = common_metadata.get('las_version', 'N/D')
        point_format = common_metadata.get('point_format', 'N/D')
        rows_html += f"<tr><td>LAS Version</td><td>{version} (Point Format: {point_format})</td></tr>"

        # CRS (troncato)
        crs = common_metadata.get('crs_wkt', 'N/D')
        if isinstance(crs, str) and len(crs) > 100:
            crs = crs[:100] + "..."
        rows_html += f"<tr><td>CRS</td><td>{crs}</td></tr>"

        # Software metadata aggiuntivi
        software_meta = common_metadata.get('software_metadata', {})
        if software_meta:
            rows_html += self._generate_data_rows({'software_details': software_meta})

        return f"""
        <div class="metadata-section">
            <div class="section-content" style="display: block;">
                <table class="metadata-table">
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_individual_files_table(self, group_results: List[Dict[str, Any]]) -> str:
        """Genera tabella con dettagli dei file individuali."""
        rows_html = ""

        for i, result in enumerate(group_results, 1):
            if 'error' not in result['key_params']:
                key_params = result['key_params']
                metadata = result['metadata']

                # Calcola dimensioni spaziali se disponibili
                spatial_info = ""
                try:
                    extent = metadata.get('coordinate_system', {}).get('spatial_extent', {})
                    if extent:
                        x_range = extent.get('x_range', 0)
                        y_range = extent.get('y_range', 0)
                        z_range = extent.get('z_range', 0)
                        spatial_info = f"{x_range:.1f}×{y_range:.1f}×{z_range:.1f}"
                except:
                    pass

                rows_html += f"""
                <tr>
                    <td>{i}</td>
                    <td style="font-family: 'Courier New', monospace;">{key_params['filename']}</td>
                    <td style="text-align: right; font-family: 'Courier New', monospace;">{key_params['dim']}</td>
                    <td style="text-align: right; font-family: 'Courier New', monospace; font-weight: 600;">{key_params['num_points']}</td>
                    <td style="text-align: center; font-family: 'Courier New', monospace;">{spatial_info if spatial_info else 'N/D'}</td>
                </tr>
                """

        return f"""
        <div class="metadata-section">
            <div class="section-content" style="display: block;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #007acc; color: white;">
                            <th style="padding: 12px; text-align: left;">#</th>
                            <th style="padding: 12px; text-align: left;">Nome File</th>
                            <th style="padding: 12px; text-align: right;">Dimensione File</th>
                            <th style="padding: 12px; text-align: right;">Numero Punti</th>
                            <th style="padding: 12px; text-align: center;">Estensione Spaziale</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """