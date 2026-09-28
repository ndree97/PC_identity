import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QCheckBox, QLineEdit, QTabWidget,
    QTextEdit, QSplitter, QMessageBox, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QColor, QDesktopServices

from src.gui.worker import ExtractionWorker


DARK_STYLESHEET = """
QMainWindow {
    background-color: #18191f;
}
QWidget {
    background-color: #18191f;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #21232d;
    border: 1px solid #2d313f;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px 0 6px;
}
QPushButton {
    background-color: #2e3447;
    border: 1px solid #3d455d;
    border-radius: 6px;
    padding: 7px 16px;
    color: #f8fafc;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3b425b;
    border-color: #38bdf8;
}
QPushButton:pressed {
    background-color: #1e2230;
}
QPushButton:disabled {
    background-color: #1a1c24;
    color: #64748b;
    border-color: #272a38;
}
QPushButton#btn_run {
    background-color: #059669;
    border-color: #10b981;
    color: #ffffff;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 24px;
}
QPushButton#btn_run:hover {
    background-color: #10b981;
    border-color: #34d399;
}
QPushButton#btn_cancel {
    background-color: #b91c1c;
    border-color: #ef4444;
    color: #ffffff;
}
QPushButton#btn_cancel:hover {
    background-color: #dc2626;
}
QTableWidget {
    background-color: #1e2029;
    border: 1px solid #2d313f;
    border-radius: 8px;
    gridline-color: #272a38;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #272a38;
    color: #94a3b8;
    font-weight: bold;
    padding: 6px;
    border: 1px solid #1e2029;
}
QLineEdit {
    background-color: #1e2029;
    border: 1px solid #2d313f;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}
QLineEdit:focus {
    border-color: #38bdf8;
}
QProgressBar {
    background-color: #1e2029;
    border: 1px solid #2d313f;
    border-radius: 6px;
    text-align: center;
    color: #f8fafc;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 5px;
}
QTabWidget::pane {
    border: 1px solid #2d313f;
    border-radius: 8px;
    background-color: #21232d;
}
QTabBar::tab {
    background-color: #1e2029;
    color: #94a3b8;
    border: 1px solid #2d313f;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #21232d;
    color: #38bdf8;
    border-bottom-color: #21232d;
    font-weight: bold;
}
QTextEdit {
    background-color: #1a1c24;
    border: 1px solid #2d313f;
    border-radius: 6px;
    color: #e2e8f0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3d455d;
    background-color: #1e2029;
}
QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}
"""


class DropAreaWidget(QFrame):
    """Area drag & drop per aggiungere facilmente file e cartelle."""

    def __init__(self, on_files_dropped, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3d455d;
                border-radius: 10px;
                background-color: #1e2029;
                padding: 15px;
            }
            QFrame:hover {
                border-color: #38bdf8;
                background-color: #232733;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label_icon = QLabel("📥")
        self.label_icon.setStyleSheet("font-size: 28px; background: transparent;")
        self.label_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_icon)

        self.label_text = QLabel("Trascina qui i tuoi file (.las, .laz, .e57, .ply) oppure cartelle di rilievo")
        self.label_text.setStyleSheet("font-weight: bold; color: #cbd5e1; background: transparent; font-size: 14px;")
        self.label_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_text)

        self.label_sub = QLabel("I formati supportati verranno rilevati e aggiunti automaticamente alla coda")
        self.label_sub.setStyleSheet("color: #64748b; background: transparent; font-size: 12px;")
        self.label_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_sub)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #10b981;
                    border-radius: 10px;
                    background-color: #1e2d27;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3d455d;
                border-radius: 10px;
                background-color: #1e2029;
            }
        """)

    def dropEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3d455d;
                border-radius: 10px;
                background-color: #1e2029;
            }
        """)
        paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path:
                paths.append(Path(local_path))
        if paths:
            self.on_files_dropped(paths)


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione Point Cloud Identity Inspector."""

    SUPPORTED_EXTS = {".las", ".laz", ".e57", ".ply"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PointCloud Identity Inspector — LAS · LAZ · E57 · PLY")
        self.resize(1150, 850)
        self.setStyleSheet(DARK_STYLESHEET)

        self.file_queue: List[Path] = []
        self.results_cache: Dict[int, Dict[str, Any]] = {}
        self.worker: Optional[ExtractionWorker] = None

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header con titolo e badge
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("☁️ PointCloud Identity Inspector")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")
        subtitle_lbl = QLabel("Analizzatore avanzato di metadati, sensori, software e provenienza per nuvole di punti 3D")
        subtitle_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        badge_lbl = QLabel("Supporto: .LAS · .LAZ · .E57 · .PLY")
        badge_lbl.setStyleSheet("""
            background-color: #1e293b;
            color: #38bdf8;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 15px;
            border: 1px solid #0284c7;
        """)
        header_layout.addWidget(badge_lbl)
        main_layout.addLayout(header_layout)

        # 2. Area Drag & Drop
        drop_area = DropAreaWidget(self.add_paths_to_queue)
        main_layout.addWidget(drop_area)

        # 3. Toolbar con pulsanti azione coda
        btn_toolbar = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ Aggiungi File...")
        self.btn_add_files.clicked.connect(self._on_add_files_clicked)
        btn_toolbar.addWidget(self.btn_add_files)

        self.btn_add_dir = QPushButton("📁 Aggiungi Cartella...")
        self.btn_add_dir.clicked.connect(self._on_add_dir_clicked)
        btn_toolbar.addWidget(self.btn_add_dir)

        self.btn_remove = QPushButton("🗑️ Rimuovi Selezionato")
        self.btn_remove.clicked.connect(self._on_remove_selected_clicked)
        btn_toolbar.addWidget(self.btn_remove)

        self.btn_clear = QPushButton("🧹 Svuota Lista")
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        btn_toolbar.addWidget(self.btn_clear)

        btn_toolbar.addStretch()

        self.lbl_file_count = QLabel("0 file in coda")
        self.lbl_file_count.setStyleSheet("color: #94a3b8; font-weight: bold;")
        btn_toolbar.addWidget(self.lbl_file_count)
        main_layout.addLayout(btn_toolbar)

        # 4. Splitter centrale: Tabella file sopra, Dettagli e Tab sotto
        splitter = QSplitter(Qt.Vertical)

        # Tabella coda
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Nome File", "Formato", "Dimensione", "Punti", "EPSG / CRS", "Software / Sensore", "Stato", "Azioni"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self._on_table_row_clicked)
        splitter.addWidget(self.table)

        # Tab inferiori per ispezione
        self.tabs = QTabWidget()
        
        # Tab 1: Parametri Chiave
        self.tab_key_params = QTextEdit()
        self.tab_key_params.setReadOnly(True)
        self.tab_key_params.setPlaceholderText("Seleziona una nuvola di punti dalla tabella per visualizzare i parametri chiave estratti...")
        self.tabs.addTab(self.tab_key_params, "📊 Parametri Chiave")

        # Tab 2: JSON Completo
        self.tab_json = QTextEdit()
        self.tab_json.setReadOnly(True)
        self.tab_json.setPlaceholderText("I metadati completi in formato JSON appariranno qui...")
        self.tabs.addTab(self.tab_json, "📄 JSON Completo")

        # Tab 3: Log Console
        self.tab_log = QTextEdit()
        self.tab_log.setReadOnly(True)
        self.tabs.addTab(self.tab_log, "📋 Log Operazioni")

        splitter.addWidget(self.tabs)
        splitter.setSizes([320, 280])
        main_layout.addWidget(splitter)

        # 5. Opzioni di configurazione
        opts_box = QGroupBox("Impostazioni di Output")
        opts_layout = QHBoxLayout(opts_box)
        opts_layout.setSpacing(16)

        opts_layout.addWidget(QLabel("Cartella di Output:"))
        self.edit_output_dir = QLineEdit(str(Path("output").resolve()))
        opts_layout.addWidget(self.edit_output_dir, stretch=1)

        self.btn_browse_out = QPushButton("Sfoglia...")
        self.btn_browse_out.clicked.connect(self._on_browse_output_clicked)
        opts_layout.addWidget(self.btn_browse_out)

        self.chk_html = QCheckBox("Genera Report HTML")
        self.chk_html.setChecked(True)
        opts_layout.addWidget(self.chk_html)

        self.chk_group = QCheckBox("Raggruppa File Correlati")
        self.chk_group.setChecked(True)
        opts_layout.addWidget(self.chk_group)

        self.chk_auto_open = QCheckBox("Apri HTML al termine")
        self.chk_auto_open.setChecked(False)
        opts_layout.addWidget(self.chk_auto_open)

        self.btn_open_out_folder = QPushButton("📂 Apri Cartella")
        self.btn_open_out_folder.clicked.connect(self._on_open_output_folder_clicked)
        opts_layout.addWidget(self.btn_open_out_folder)

        main_layout.addWidget(opts_box)

        # 6. Barra di progresso e pulsanti esecuzione
        action_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        action_layout.addWidget(self.progress_bar, stretch=1)

        self.btn_run = QPushButton("🚀 Avvia Analisi")
        self.btn_run.setObjectName("btn_run")
        self.btn_run.clicked.connect(self._on_run_clicked)
        action_layout.addWidget(self.btn_run)

        self.btn_cancel = QPushButton("⏹️ Interrompi")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        action_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(action_layout)

        # Status Bar info
        self.statusBar().showMessage("Pronto. Aggiungi file o cartelle per iniziare.")

    # --- Gestione file e code ---

    def add_paths_to_queue(self, paths: List[Path]):
        """Aggiunge una lista di percorsi (file o cartelle ricorsive) alla coda."""
        added_count = 0
        for p in paths:
            if p.is_file():
                if p.suffix.lower() in self.SUPPORTED_EXTS and p not in self.file_queue:
                    self.file_queue.append(p)
                    self._add_row_to_table(p)
                    added_count += 1
            elif p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file() and sub.suffix.lower() in self.SUPPORTED_EXTS and sub not in self.file_queue:
                        self.file_queue.append(sub)
                        self._add_row_to_table(sub)
                        added_count += 1

        self.lbl_file_count.setText(f"{len(self.file_queue)} file in coda")
        if added_count > 0:
            self.statusBar().showMessage(f"Aggiunti {added_count} file alla coda.")

    def _add_row_to_table(self, file_path: Path):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Dimensione formattata
        bytes_val = file_path.stat().st_size
        if bytes_val < 1024 * 1024:
            size_str = f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            size_str = f"{bytes_val / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"

        self.table.setItem(row, 0, QTableWidgetItem(file_path.name))
        self.table.setItem(row, 1, QTableWidgetItem(file_path.suffix.upper().replace(".", "")))
        self.table.setItem(row, 2, QTableWidgetItem(size_str))
        self.table.setItem(row, 3, QTableWidgetItem("In attesa..."))
        self.table.setItem(row, 4, QTableWidgetItem("-"))
        self.table.setItem(row, 5, QTableWidgetItem("-"))

        status_item = QTableWidgetItem("In attesa")
        status_item.setForeground(QColor("#94a3b8"))
        self.table.setItem(row, 6, status_item)

        btn_action = QPushButton("Report")
        btn_action.setEnabled(False)
        self.table.setCellWidget(row, 7, btn_action)

    def _on_add_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleziona nuvole di punti",
            "",
            "Point Cloud Files (*.las *.laz *.e57 *.ply);;LAS/LAZ Files (*.las *.laz);;E57 Files (*.e57);;PLY Files (*.ply);;Tutti i file (*.*)"
        )
        if files:
            self.add_paths_to_queue([Path(f) for f in files])

    def _on_add_dir_clicked(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleziona cartella con nuvole di punti")
        if directory:
            self.add_paths_to_queue([Path(directory)])

    def _on_remove_selected_clicked(self):
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in selected_rows:
            if r < len(self.file_queue):
                del self.file_queue[r]
            self.table.removeRow(r)
        self.lbl_file_count.setText(f"{len(self.file_queue)} file in coda")

    def _on_clear_clicked(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Attenzione", "Impossibile svuotare la lista durante l'elaborazione.")
            return
        self.file_queue.clear()
        self.results_cache.clear()
        self.table.setRowCount(0)
        self.tab_key_params.clear()
        self.tab_json.clear()
        self.lbl_file_count.setText("0 file in coda")
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Lista svuotata.")

    def _on_browse_output_clicked(self):
        d = QFileDialog.getExistingDirectory(self, "Seleziona cartella di output", self.edit_output_dir.text())
        if d:
            self.edit_output_dir.setText(d)

    def _on_open_output_folder_clicked(self):
        out_p = Path(self.edit_output_dir.text())
        out_p.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out_p)))

    # --- Esecuzione asincrona ---

    def _on_run_clicked(self):
        if not self.file_queue:
            QMessageBox.information(self, "Coda vuota", "Aggiungi prima almeno un file da analizzare.")
            return

        out_dir = Path(self.edit_output_dir.text())
        out_dir.mkdir(parents=True, exist_ok=True)

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_add_files.setEnabled(False)
        self.btn_add_dir.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_remove.setEnabled(False)

        self.progress_bar.setMaximum(len(self.file_queue))
        self.progress_bar.setValue(0)

        self.worker = ExtractionWorker(
            file_paths=list(self.file_queue),
            output_dir=out_dir,
            generate_html=self.chk_html.isChecked(),
            group_files=self.chk_group.isChecked(),
        )
        self.worker.sig_progress.connect(self._on_worker_progress)
        self.worker.sig_file_started.connect(self._on_worker_file_started)
        self.worker.sig_file_completed.connect(self._on_worker_file_completed)
        self.worker.sig_file_error.connect(self._on_worker_file_error)
        self.worker.sig_log.connect(self._append_log)
        self.worker.sig_all_finished.connect(self._on_worker_all_finished)
        self.worker.start()

    def _on_cancel_clicked(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.btn_cancel.setEnabled(False)

    def _on_worker_progress(self, current: int, total: int):
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"Elaborazione: {current} / {total} completati...")

    def _on_worker_file_started(self, idx: int, filepath: str):
        if idx < self.table.rowCount():
            status_item = self.table.item(idx, 6)
            if status_item:
                status_item.setText("⏳ In corso...")
                status_item.setForeground(QColor("#38bdf8"))

    def _on_worker_file_completed(self, idx: int, filepath: str, metadata: dict, key_params: dict, html_path: str):
        self.results_cache[idx] = {
            "metadata": metadata,
            "key_params": key_params,
            "html_path": html_path,
        }

        if idx < self.table.rowCount():
            self.table.setItem(idx, 3, QTableWidgetItem(key_params.get("num_points", "N/D")))
            self.table.setItem(idx, 4, QTableWidgetItem(key_params.get("epsg", "N/D")))
            source_lbl = f"{key_params.get('source', '')} / {key_params.get('sensor', '')}".strip(" /")
            self.table.setItem(idx, 5, QTableWidgetItem(source_lbl if source_lbl else "N/D"))

            status_item = self.table.item(idx, 6)
            if status_item:
                status_item.setText("✓ Completato")
                status_item.setForeground(QColor("#10b981"))

            if html_path:
                btn = QPushButton("🌐 Apri HTML")
                btn.setStyleSheet("background-color: #0284c7; color: white; padding: 4px 8px; font-size: 11px;")
                btn.clicked.connect(lambda _, hp=html_path: QDesktopServices.openUrl(QUrl.fromLocalFile(hp)))
                self.table.setCellWidget(idx, 7, btn)

        # Seleziona automaticamente il primo risultato per mostrare i parametri
        if idx == 0:
            self._display_file_details(metadata)

    def _on_worker_file_error(self, idx: int, filepath: str, error_msg: str):
        if idx < self.table.rowCount():
            status_item = self.table.item(idx, 6)
            if status_item:
                status_item.setText("✗ Errore")
                status_item.setForeground(QColor("#ef4444"))
                status_item.setToolTip(error_msg)

    def _on_worker_all_finished(self, all_results: list):
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_add_files.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_remove.setEnabled(True)

        self.statusBar().showMessage(f"✨ Elaborazione terminata: {len(all_results)} file analizzati.")

        # Se richiesto, apri il report HTML
        if self.chk_auto_open.isChecked() and all_results:
            first_html = all_results[0].get("html_path")
            if first_html:
                QDesktopServices.openUrl(QUrl.fromLocalFile(first_html))

    def _on_table_row_clicked(self, row: int, col: int):
        if row in self.results_cache:
            meta = self.results_cache[row]["metadata"]
            self._display_file_details(meta)

    def _display_file_details(self, metadata: dict):
        """Formatta i parametri chiave e il JSON nei tab inferiori."""
        # 1. JSON
        pretty_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        self.tab_json.setPlainText(pretty_json)

        # 2. Parametri Chiave Formattati
        f_info = metadata.get("file_info", {})
        nature = metadata.get("punto_cloud_nature", {})
        coords = metadata.get("coordinate_system", {})
        georef = metadata.get("georeferencing", {})
        software = metadata.get("software_metadata", {})
        sensor = metadata.get("sensor_type", {})
        proc = metadata.get("processing_history", {})

        extent = coords.get("spatial_extent", {})
        bounds = coords.get("bounds", {})

        summary_text = f"""================================================================================
                    CARTA D'IDENTITÀ DELLA NUVOLA DI PUNTI
================================================================================
📁 INFORMAZIONI FILE:
   • Nome File:          {f_info.get('filename', 'N/D')}
   • Formato:            {f_info.get('format', 'N/D')}
   • Dimensione:         {f_info.get('file_size_formatted', 'N/D')} ({f_info.get('file_size_bytes', 0):,} bytes)
   • Percorso:           {f_info.get('filepath', 'N/D')}

☁️ NATURA DELLA NUVOLA:
   • Numero Punti:       {nature.get('num_points', 0):,}
   • Presenza Colore:    {'Sì (RGB)' if nature.get('has_color') else 'No'}
   • Presenza Intensità: {'Sì' if nature.get('has_intensity', nature.get('intensity_range') is not None) else 'No'}
   • Scansioni E57:      {nature.get('scan_count', 1)}

📐 COORDINATE & BOUNDING BOX 3D:
   • Estensione X (W):   {extent.get('x_range', 0)} m  [min: {bounds.get('x', {}).get('min', '-')} | max: {bounds.get('x', {}).get('max', '-')}]
   • Estensione Y (L):   {extent.get('y_range', 0)} m  [min: {bounds.get('y', {}).get('min', '-')} | max: {bounds.get('y', {}).get('max', '-')}]
   • Estensione Z (H):   {extent.get('z_range', 0)} m  [min: {bounds.get('z', {}).get('min', '-')} | max: {bounds.get('z', {}).get('max', '-')}]

🌐 GEOREFERENZIAZIONE:
   • Georeferenziato:    {'Sì' if georef.get('georeferenced') else 'No / Non certo'}
   • Codice EPSG:        {georef.get('epsg_code') or 'Non specificato'}
   • WKT / Coordinate:   {str(georef.get('crs_wkt') or georef.get('coordinate_metadata') or 'N/D')[:120]}

🛰️ SENSORE & SOFTWARE RILEVATI:
   • Software Origine:   {software.get('generating_software') or 'N/D'}
   • Software Rilevato:  {software.get('detected_software') or 'N/D'}
   • Sensore Stimato:    {sensor.get('detected_sensor') or 'N/D'}

🔬 POST-PROCESSING:
   • Elaborato:          {'Sì' if proc.get('is_post_processed') else 'No (Grezzo/Diretto)'}
   • Firme / Anomalie:   {', '.join(proc.get('processing_indicators', [])) or 'Nessuna anomalia evidente'}
================================================================================
"""
        self.tab_key_params.setPlainText(summary_text)

    def _append_log(self, text: str):
        self.tab_log.append(text)


def run_gui():
    """Avvia l'applicazione desktop Qt."""
    app = QApplication(sys.argv)
    app.setApplicationName("PointCloud Identity Inspector")
    app.setOrganizationName("OpenSource")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
