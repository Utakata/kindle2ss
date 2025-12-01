import sys
import os
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QFormLayout, QTabWidget,
                               QSpinBox, QCheckBox, QComboBox, QFileDialog, QGroupBox,
                               QTextEdit, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QImage

# Import modules
# Adjust paths if necessary based on your project structure
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.capture_engine import CaptureEngine
from src.core.ocr_processor import OCRProcessor
from src.gui.overlay import SelectionOverlay
from src.utils.window_detector import WindowDetector

class CaptureWorker(QThread):
    status_update = Signal(str, str) # type, message

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        # Callback wrapper to emit signals
        def callback(type, msg):
            self.status_update.emit(type, str(msg))

        self.engine.start_capture(callback_status=callback)
        # Thread stays alive while engine.running is true and loop is active in engine
        # However, engine.start_capture spawns its own thread.
        # Ideally, we should run the loop here or wait for it.
        # Let's adjust CaptureEngine to be blocking or handle it here.
        # Actually, CaptureEngine spawns a thread. We just need to wait for it to finish.
        while self.engine.running:
            time.sleep(0.5)

    def stop(self):
        self.engine.stop_capture()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kindle2PDF Automation Tool")
        self.resize(800, 600)

        # Init Core
        self.engine = CaptureEngine()
        self.ocr = OCRProcessor()
        self.detector = WindowDetector()

        # Init UI
        self.init_ui()

        # Worker
        self.worker = None

        # Timer for window detection
        self.check_window_timer = QThread() # Reuse thread logic or simple QTimer
        # Using simple QTimer for UI updates
        from PySide6.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_active_window)
        self.timer.start(2000) # Check every 2 seconds

    def check_active_window(self):
        title = self.detector.get_active_window_title()
        if title:
            self.lbl_active_window.setText(f"Active: {title}")
            # Optional: Warning color if not "Kindle"
            if "Kindle" not in title and self.worker and self.worker.isRunning():
                self.lbl_active_window.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.lbl_active_window.setStyleSheet("color: green;")
        else:
            self.lbl_active_window.setText("Active: Unknown")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Dashboard
        self.tab_dashboard = QWidget()
        self.setup_dashboard(self.tab_dashboard)
        self.tabs.addTab(self.tab_dashboard, "Dashboard")

        # Tab 2: Settings
        self.tab_settings = QWidget()
        self.setup_settings(self.tab_settings)
        self.tabs.addTab(self.tab_settings, "Settings")

        # Tab 3: OCR/PDF
        self.tab_ocr = QWidget()
        self.setup_ocr(self.tab_ocr)
        self.tabs.addTab(self.tab_ocr, "PDF & OCR")

        # Footer Status
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def setup_dashboard(self, parent):
        layout = QVBoxLayout(parent)

        # 1. Selection Area Info
        region_group = QGroupBox("Capture Region")
        region_layout = QHBoxLayout()
        self.lbl_region = QLabel("No region selected")
        self.btn_select_region = QPushButton("Select Area")
        self.btn_select_region.clicked.connect(self.launch_overlay)

        self.lbl_active_window = QLabel("Active: Checking...")

        region_layout.addWidget(self.lbl_region)
        region_layout.addWidget(self.btn_select_region)
        region_layout.addWidget(self.lbl_active_window)
        region_group.setLayout(region_layout)
        layout.addWidget(region_group)

        # 2. Preview & Status
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.lbl_preview = QLabel("Last captured image will appear here")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setStyleSheet("border: 1px dashed gray; min-height: 200px;")
        preview_layout.addWidget(self.lbl_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # 3. Controls
        control_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Capture")
        self.btn_start.clicked.connect(self.start_capture)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_capture)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        layout.addLayout(control_layout)

        # Log
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(100)
        layout.addWidget(self.txt_log)

    def setup_settings(self, parent):
        layout = QFormLayout(parent)

        self.input_output_dir = QLineEdit("output")
        layout.addRow("Output Directory:", self.input_output_dir)

        self.input_interval = QSpinBox()
        self.input_interval.setValue(1)
        self.input_interval.setSuffix(" sec")
        layout.addRow("Capture Interval:", self.input_interval)

        self.input_key = QComboBox()
        self.input_key.addItems(["left", "right", "down", "space"])
        layout.addRow("Page Turn Key:", self.input_key)

        self.input_crop_header = QSpinBox()
        self.input_crop_header.setRange(0, 500)
        self.input_crop_header.setValue(0)
        self.input_crop_header.setSuffix(" px")
        layout.addRow("Header Crop:", self.input_crop_header)

        self.input_crop_footer = QSpinBox()
        self.input_crop_footer.setRange(0, 500)
        self.input_crop_footer.setValue(0)
        self.input_crop_footer.setSuffix(" px")
        layout.addRow("Footer Crop:", self.input_crop_footer)

        self.input_duplicate_threshold = QSpinBox()
        self.input_duplicate_threshold.setValue(3)
        layout.addRow("Stop after duplicates:", self.input_duplicate_threshold)

    def setup_ocr(self, parent):
        layout = QVBoxLayout(parent)

        info_label = QLabel("Convert captured images to PDF using YomiToku (if available) or standard tools.")
        layout.addWidget(info_label)

        form = QFormLayout()

        self.chk_gpu = QCheckBox("Use GPU Acceleration")
        self.chk_gpu.setChecked(self.ocr.check_gpu())
        self.chk_gpu.setEnabled(self.ocr.check_gpu())
        form.addRow("GPU Status:", self.chk_gpu)

        self.chk_apply_crop = QCheckBox("Apply Header/Footer Crop to PDF")
        self.chk_apply_crop.setChecked(True)
        form.addRow("Cropping:", self.chk_apply_crop)

        layout.addLayout(form)

        self.btn_create_pdf = QPushButton("Create PDF from Output Folder")
        self.btn_create_pdf.clicked.connect(self.create_pdf)
        layout.addWidget(self.btn_create_pdf)

        self.btn_ocr_export = QPushButton("Export OCR (Markdown/Text) using YomiToku")
        self.btn_ocr_export.clicked.connect(self.run_ocr)
        self.btn_ocr_export.setEnabled(self.ocr.check_gpu() or True) # Allow CPU too but warn?
        layout.addWidget(self.btn_ocr_export)

        self.ocr_progress = QProgressBar()
        layout.addWidget(self.ocr_progress)

    # --- Slots ---

    def launch_overlay(self):
        self.overlay = SelectionOverlay()
        self.overlay.selection_confirmed.connect(self.on_selection_confirmed)
        self.overlay.show()

    def on_selection_confirmed(self, x, y, w, h):
        self.engine.set_region(x, y, w, h)
        self.lbl_region.setText(f"X: {x}, Y: {y}, W: {w}, H: {h}")
        self.log(f"Region selected: {x},{y} {w}x{h}")

    def start_capture(self):
        if not self.engine.capture_region:
            QMessageBox.warning(self, "Warning", "Please select a capture region first.")
            return

        # Apply settings
        self.engine.save_dir = self.input_output_dir.text()
        self.engine.interval = self.input_interval.value()
        self.engine.turn_key = self.input_key.currentText()
        self.engine.duplicate_threshold = self.input_duplicate_threshold.value()
        self.engine.set_crop_margins(self.input_crop_header.value(), self.input_crop_footer.value())

        # UI Update
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.tabs.setCurrentIndex(0) # Go to dashboard
        self.log("Starting capture...")

        # Worker
        self.worker = CaptureWorker(self.engine)
        self.worker.status_update.connect(self.on_capture_update)
        self.worker.finished.connect(self.on_capture_finished)
        self.worker.start()

    def stop_capture(self):
        if self.worker:
            self.worker.stop()
            self.log("Stopping...")

    def on_capture_update(self, type, msg):
        if type == "saved":
            self.log(f"Captured: {os.path.basename(msg)}")
            # Update preview
            pixmap = QPixmap(msg)
            if not pixmap.isNull():
                self.lbl_preview.setPixmap(pixmap.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif type == "duplicate":
            self.status_bar.showMessage(f"Duplicate detected ({msg})")
        elif type == "error":
            self.log(f"Error: {msg}")
        elif type == "finished":
            self.log(f"Finished: {msg}")

    def on_capture_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_bar.showMessage("Capture stopped")
        self.log("Capture process ended.")

    def create_pdf(self):
        self._process_images("pdf")

    def run_ocr(self):
        self._process_images("ocr")

    def _process_images(self, mode):
        # Gather images
        output_dir = self.input_output_dir.text()
        if not os.path.exists(output_dir):
             QMessageBox.warning(self, "Error", "Output directory does not exist.")
             return

        images = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".png")])
        if not images:
             QMessageBox.warning(self, "Error", "No images found in output directory.")
             return

        self.log(f"Found {len(images)} images. Starting {mode.upper()} process...")
        self.btn_create_pdf.setEnabled(False)
        self.btn_ocr_export.setEnabled(False)
        self.ocr_progress.setValue(0)

        crop_config = None
        if self.chk_apply_crop.isChecked():
            crop_config = {
                'top': self.input_crop_header.value(),
                'bottom': self.input_crop_footer.value()
            }

        def progress(curr, total, status):
            self.ocr_progress.setValue(int((curr/total)*100))
            self.status_bar.showMessage(status)
            QApplication.processEvents()

        if mode == "pdf":
            pdf_path = os.path.join(output_dir, "output.pdf")
            success, msg = self.ocr.images_to_pdf(images, pdf_path, crop_config, progress)
        else:
            success, msg = self.ocr.run_ocr_export(images, output_dir, "markdown", progress)

        self.btn_create_pdf.setEnabled(True)
        self.btn_ocr_export.setEnabled(True)
        self.ocr_progress.setValue(100)

        if success:
            QMessageBox.information(self, "Success", msg)
            self.log(msg)
        else:
            QMessageBox.critical(self, "Error", msg)
            self.log(f"{mode.upper()} Error: {msg}")

    def log(self, message):
        self.txt_log.append(message)
        # Scroll to bottom
        sb = self.txt_log.verticalScrollBar()
        sb.setValue(sb.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
