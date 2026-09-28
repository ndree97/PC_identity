import argparse
import sys
from pathlib import Path

# Assicura supporto UTF-8 su console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.extractor import LASMetadataExtractor

def main():
    # Avvia la GUI se non vengono passati argomenti o con flag --gui / -g
    if len(sys.argv) == 1 or "--gui" in sys.argv or "-g" in sys.argv:
        try:
            from src.gui import run_gui
            run_gui()
            return
        except ImportError as e:
            print(f"Interfaccia grafica non disponibile ({e}). Uso modalità CLI.", file=sys.stderr)

    parser = argparse.ArgumentParser(
        description="PointCloud Identity Inspector - Analizza nuvole di punti (.las, .laz, .e57, .ply)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Esempi di utilizzo:
    python main.py                           # Avvia interfaccia grafica Qt
    python main.py --gui                     # Avvia interfaccia grafica Qt
    python main.py -i input.las              # analizza singolo file (parametri chiave + HTML)
    python main.py -i input.e57 -p           # stampa metadati completi + HTML
    python main.py -d /percorso/directory    # analizza directory (supporta .las, .laz, .e57, .ply)

    Output structure:
    output/
    |-- filename1/
    |   |-- filename1_metadata.json
    |   \\-- filename1_report.html
    \\-- filename2/
        |-- filename2_metadata.json
        \\-- filename2_report.html
            """
        )

    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        help="Avvia l'interfaccia grafica Qt Desktop"
    )

    # Gruppo esclusivo per input (file o directory)
    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "-i", "--input",
        type=str,
        help="Percorso del file da analizzare (.las, .laz, .e57, .ply)"
    )

    input_group.add_argument(
        "-d", "--directory",
        type=str,
        help="Percorso della directory da analizzare (cerca .las, .laz, .e57, .ply)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Percorso file JSON output (default: output/<filename>_metadata.json)"
    )
    
    parser.add_argument(
        "-p", "--print",
        action="store_true",
        help="Stampa metadati completi anche a console"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config",
        help="Directory configurazione (default: config)"
    )
    
    args = parser.parse_args()

    try:
        # Crea extractor
        extractor = LASMetadataExtractor(config_dir=args.config)

        # Gestione file singolo
        if args.input:
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Errore: File non trovato: {args.input}", file=sys.stderr)
                sys.exit(1)

            # Determina output path
            if args.output is None:
                output_path = Path("output") / f"{input_path.stem}_metadata.json"
            else:
                output_path = args.output

            print(f"Elaborazione: {input_path}")

            # Estrai metadati
            metadata = extractor.extract(str(input_path))

            # Stampa sempre parametri chiave
            extractor.print_key_parameters(metadata)

            # Stampa completa se richiesto
            if args.print:
                import json
                print("\n" + "="*60)
                print("METADATI ESTRATTI:")
                print("="*60)
                print(json.dumps(metadata, indent=2, ensure_ascii=False))
                print("="*60 + "\n")

            # Crea sottocartella per il file
            output_dir = Path("output") / input_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)

            # Salva JSON nella sottocartella
            json_path = output_dir / f"{input_path.stem}_metadata.json"
            saved_path = extractor.save(metadata, str(json_path))
            print(f"Metadati salvati in: {saved_path}")

            # Genera HTML nella sottocartella
            from src.utils.html_generator import HTMLGenerator
            html_gen = HTMLGenerator()
            html_path = output_dir / f"{input_path.stem}_report.html"
            html_gen.generate_single_file_report(metadata, html_path, str(input_path))
            print(f"Report HTML salvato in: {html_path}")

        # Gestione directory
        elif args.directory:
            from src.utils.directory_handler import DirectoryHandler
            import os

            dir_path = Path(args.directory)
            if not dir_path.exists():
                print(f"Errore: Directory non trovata: {args.directory}", file=sys.stderr)
                sys.exit(1)

            if not dir_path.is_dir():
                print(f"Errore: Il percorso non è una directory: {args.directory}", file=sys.stderr)
                sys.exit(1)

            # Crea directory handler
            dir_handler = DirectoryHandler()

            # Trova files supportati
            files = dir_handler.find_supported_files(dir_path)
            if not files:
                print(f"Nessun file supportato trovato in: {args.directory}")
                sys.exit(1)

            print(f"Trovati {len(files)} file da analizzare...")

            # Analizza i files e genera output raggruppati
            results = dir_handler.analyze_directory(files, extractor, True, True)

            # Identifica gruppi di file correlati
            from src.utils.html_generator import HTMLGenerator
            from src.utils.file_grouper import FileGrouper

            html_gen = HTMLGenerator()
            file_grouper = FileGrouper()

            print(f"\n{'='*60}")
            print(f"RAGGRUPPAMENTO FILE E GENERAZIONE OUTPUT")
            print(f"{'='*60}")

            # Raggruppa i file
            all_files = [Path(result['filepath']) for result in results]
            file_groups = file_grouper.identify_groups(all_files)

            # Organizza i risultati per gruppi
            grouped_results = {}
            for group_name, file_paths in file_groups.items():
                group_results = []
                for file_path in file_paths:
                    # Trova il risultato corrispondente
                    matching_result = next((r for r in results if Path(r['filepath']) == file_path), None)
                    if matching_result:
                        group_results.append(matching_result)

                if group_results:
                    grouped_results[group_name] = group_results

            # Genera output per ogni gruppo
            for group_name, group_results in grouped_results.items():
                try:
                    if len(group_results) == 1:
                        # GESTIONE SINGOLI FILE (comportamento originale)
                        result = group_results[0]
                        if 'error' not in result['key_params']:
                            input_path = Path(result['filepath'])
                            output_dir = Path("output") / input_path.stem
                            output_dir.mkdir(parents=True, exist_ok=True)

                            print(f"\n📁 File singolo: {input_path.stem}")

                            # Salva JSON come singolo
                            json_path = output_dir / f"{input_path.stem}_metadata.json"
                            extractor.save(result['metadata'], str(json_path))
                            print(f"   ✓ JSON: {json_path}")

                            # Genera HTML come singolo
                            html_path = output_dir / f"{input_path.stem}_report.html"
                            html_gen.generate_single_file_report(result['metadata'], html_path, result['filepath'])
                            print(f"   ✓ HTML: {html_path}")
                        else:
                            print(f"\n✗ Saltato {result['filename']} (errore nell'analisi)")

                    else:
                        # GESTIONE GRUPPI (2+ file)
                        # Nome cartella pulito per il gruppo
                        safe_group_name = group_name.replace(' ', '_').replace('(', '').replace(')', '').replace(':', '').lower()
                        output_dir = Path("output") / safe_group_name
                        output_dir.mkdir(parents=True, exist_ok=True)

                        print(f"\n🌩️ Gruppo: {group_name} ({len(group_results)} file)")

                        # Calcola statistiche aggregate
                        total_points = 0
                        total_size_bytes = 0
                        common_metadata = {}
                        variable_metadata = []

                        # Prendi il primo file come riferimento per metadati comuni
                        if group_results and 'error' not in group_results[0]['key_params']:
                            first_metadata = group_results[0]['metadata']

                            # Metadati comuni (uguali per tutti i file)
                            common_metadata = {
                                'epsg_code': first_metadata.get('georeferencing', {}).get('epsg_code'),
                                'source': first_metadata.get('software_metadata', {}).get('generating_software'),
                                'las_version': first_metadata.get('header_info', {}).get('las_version'),
                                'point_format': first_metadata.get('header_info', {}).get('point_format'),
                                'crs_wkt': first_metadata.get('georeferencing', {}).get('crs_wkt'),
                                'software_metadata': first_metadata.get('software_metadata', {}),
                                'temporal_info': first_metadata.get('temporal_info', {})
                            }

                        for result in group_results:
                            if 'error' not in result['key_params']:
                                # Aggiungi statistiche
                                try:
                                    num_points_str = result['key_params']['num_points'].replace(' ', '')
                                    if num_points_str and num_points_str != 'N/D':
                                        total_points += int(num_points_str)
                                except:
                                    pass

                                try:
                                    file_size = result['metadata']['file_info']['file_size_bytes']
                                    total_size_bytes += file_size
                                except:
                                    pass

                                # Metadati variabili per ogni file
                                variable_metadata.append({
                                    'filename': result['key_params']['filename'],
                                    'file_size_formatted': result['key_params']['dim'],
                                    'num_points': result['key_params']['num_points'],
                                    'spatial_extent': result['metadata'].get('coordinate_system', {}).get('spatial_extent', {}),
                                    'bounds': result['metadata'].get('coordinate_system', {}).get('bounds', {})
                                })

                        # Formatta dimensione totale
                        if total_size_bytes < 1024 * 1024:
                            total_size_str = f"{total_size_bytes/1024:.1f} KB"
                        elif total_size_bytes < 1024 * 1024 * 1024:
                            total_size_str = f"{total_size_bytes/(1024*1024):.1f} MB"
                        else:
                            total_size_str = f"{total_size_bytes/(1024*1024*1024):.1f} GB"

                        print(f"   📊 Statistiche aggregate:")
                        print(f"      • Punti totali: {total_points:,}".replace(',', ' '))
                        print(f"      • Dimensione totale: {total_size_str}")
                        print(f"      • File: {len(group_results)}")
                        print(f"      • EPSG: {common_metadata.get('epsg_code', 'N/D')}")
                        print(f"      • Source: {common_metadata.get('source', 'N/D')}")

                        # Genera JSON consolidato per il gruppo
                        group_metadata = {
                            "group_info": {
                                "group_name": group_name,
                                "total_files": len(group_results),
                                "total_points": total_points,
                                "total_size_bytes": total_size_bytes,
                                "total_size_formatted": total_size_str
                            },
                            "common_metadata": common_metadata,
                            "variable_metadata": variable_metadata,
                            "individual_files": [r['metadata'] for r in group_results if 'error' not in r['key_params']]
                        }

                        # Salva JSON del gruppo
                        json_path = output_dir / f"{safe_group_name}_group_metadata.json"
                        with open(json_path, 'w', encoding='utf-8') as f:
                            import json
                            json.dump(group_metadata, f, indent=2, ensure_ascii=False, default=str)
                        print(f"   ✓ JSON gruppo: {json_path}")

                        # Genera HTML consolidato per il gruppo
                        html_path = output_dir / f"{safe_group_name}_group_report.html"
                        html_gen.generate_group_report(group_name, group_results, html_path, common_metadata, total_points, total_size_str)
                        print(f"   ✓ HTML gruppo: {html_path}")

                except Exception as e:
                    print(f"✗ Errore nel gruppo {group_name}: {e}")

            print(f"\n{'='*60}")
            print(f"OUTPUT RAGGRUPPATI COMPLETATI")
            print(f"{'='*60}\n")

    except FileNotFoundError as e:
        print(f"Errore: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()