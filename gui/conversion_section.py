"""
Conversion Section.

Üst bölüm - Excel dönüştürme işlemleri.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QProgressBar,
    QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, QThreadPool, Signal
from pathlib import Path
from datetime import datetime

from gui.styles import Styles
from gui.mini_log_panel import MiniLogPanel
from gui import dialogs
from workers import ValidationWorker, ConversionWorker
from config.config_manager import ConfigManager
from utils.path_utils import PathUtils


class ConversionSection(QWidget):
    """
    Conversion section widget'ı.
    
    Özellikler:
    - Input Excel seçimi
    - Yıl seçimi
    - Validate butonu
    - Convert & Save butonu
    - Cancel butonu
    - Progress bar
    - Status badge
    
    Signals:
        validation_completed: Doğrulama tamamlandı (is_valid: bool)
        conversion_completed: Dönüştürme tamamlandı (output_path: str)
    """
    
    validation_completed = Signal(bool)
    conversion_completed = Signal(str)
    
    def __init__(self, log_panel: MiniLogPanel, parent=None):
        """
        ConversionSection başlatıcı.
        
        Args:
            log_panel: Mini log panel referansı
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.log_panel = log_panel
        self.config = ConfigManager()
        self.thread_pool = QThreadPool.globalInstance()
        
        self.current_worker = None
        self.last_output_path = None
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("🟦 BÖLÜM 1: VERİ DÖNÜŞTÜRME")
        title.setStyleSheet(Styles.SECTION_TITLE)
        layout.addWidget(title)
        
        # Group box
        group = QGroupBox()
        group.setStyleSheet(Styles.GROUP_BOX)
        group_layout = QVBoxLayout(group)
        
        # Input Excel seçimi
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Excel:"))
        
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Excel dosyası seçin...")
        self.input_path_edit.setStyleSheet(Styles.FILE_PICKER)
        self.input_path_edit.setReadOnly(True)
        input_layout.addWidget(self.input_path_edit)
        
        browse_btn = QPushButton("📁 Gözat")
        browse_btn.setStyleSheet(Styles.BROWSE_BUTTON)
        browse_btn.clicked.connect(self._on_browse_input)
        input_layout.addWidget(browse_btn)
        
        group_layout.addLayout(input_layout)
        
        # Yıl seçimi
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Kart Basım Yılı:"))
        
        self.year_spinner = QSpinBox()
        self.year_spinner.setRange(2000, 2100)
        self.year_spinner.setValue(datetime.now().year)
        self.year_spinner.setStyleSheet(Styles.YEAR_SPINNER)
        year_layout.addWidget(self.year_spinner)
        
        year_layout.addStretch()
        group_layout.addLayout(year_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(Styles.PROGRESS_BAR)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        # Status ve butonlar
        status_button_layout = QHBoxLayout()
        
        self.status_badge = QLabel("Hazır")
        self.status_badge.setStyleSheet(Styles.STATUS_READY)
        self.status_badge.setAlignment(Qt.AlignCenter)
        status_button_layout.addWidget(self.status_badge)
        
        status_button_layout.addStretch()
        
        self.validate_btn = QPushButton("✅ Validate")
        self.validate_btn.setStyleSheet(Styles.PRIMARY_BUTTON)
        self.validate_btn.clicked.connect(self._on_validate)
        status_button_layout.addWidget(self.validate_btn)
        
        self.convert_btn = QPushButton("💾 Convert & Save")
        self.convert_btn.setStyleSheet(Styles.SUCCESS_BUTTON)
        self.convert_btn.clicked.connect(self._on_convert)
        status_button_layout.addWidget(self.convert_btn)
        
        self.cancel_btn = QPushButton("⏹ Cancel")
        self.cancel_btn.setStyleSheet(Styles.DANGER_BUTTON)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        status_button_layout.addWidget(self.cancel_btn)
        
        group_layout.addLayout(status_button_layout)
        
        layout.addWidget(group)
    
    def _load_config(self):
        """Son kullanılan ayarları yükler."""
        last_input = self.config.get_last_input_path()
        if last_input and Path(last_input).exists():
            self.input_path_edit.setText(last_input)
        
        default_year = self.config.get_default_year()
        self.year_spinner.setValue(default_year)
    
    def _on_browse_input(self):
        """Input Excel dosyası seç."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Input Excel Dosyası Seç",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.input_path_edit.setText(file_path)
            self.config.set_last_input_path(file_path)
    
    def _on_validate(self):
        """Validate butonuna basıldı."""
        input_path = self.input_path_edit.text()
        
        if not input_path:
            dialogs.show_warning(self, "Uyarı", "Lütfen bir Excel dosyası seçin!")
            return
        
        # Dosya kontrolü
        is_valid, error_msg = PathUtils.validate_input_file(input_path)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        # Worker oluştur ve çalıştır
        self.current_worker = ValidationWorker(input_path)
        self._connect_worker_signals(self.current_worker)
        
        self._set_processing_state(True)
        self.log_panel.add_log('SYSTEM', "Doğrulama başlatıldı...")
        
        self.thread_pool.start(self.current_worker)
    
    def _on_convert(self):
        """Convert & Save butonuna basıldı."""
        input_path = self.input_path_edit.text()
        year = self.year_spinner.value()
        
        if not input_path:
            dialogs.show_warning(self, "Uyarı", "Lütfen bir Excel dosyası seçin!")
            return
        
        # Dosya kontrolü
        is_valid, error_msg = PathUtils.validate_input_file(input_path)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        # Worker oluştur ve çalıştır
        self.current_worker = ConversionWorker(input_path, year)
        self._connect_worker_signals(self.current_worker)
        
        self._set_processing_state(True)
        self.log_panel.add_log('SYSTEM', "Dönüştürme başlatıldı...")
        
        self.thread_pool.start(self.current_worker)
    
    def _on_cancel(self):
        """Cancel butonuna basıldı."""
        if self.current_worker:
            self.current_worker.request_cancel()
            self.log_panel.add_log('WARNING', "İptal talebi gönderildi...")
    
    def _connect_worker_signals(self, worker):
        """Worker sinyallerini bağlar."""
        worker.signals.started.connect(self._on_worker_started)
        worker.signals.finished.connect(self._on_worker_finished)
        worker.signals.progress.connect(self._on_worker_progress)
        worker.signals.status.connect(self._on_worker_status)
        worker.signals.log.connect(self.log_panel.add_log)
        worker.signals.error.connect(self._on_worker_error)
        worker.signals.result.connect(self._on_worker_result)
        worker.signals.cancelled.connect(self._on_worker_cancelled)
    
    def _on_worker_started(self):
        """Worker başladı."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
    
    def _on_worker_finished(self, success: bool):
        """Worker tamamlandı."""
        self._set_processing_state(False)
        
        if success:
            self.status_badge.setText("Tamamlandı ✅")
            self.status_badge.setStyleSheet(Styles.STATUS_SUCCESS)
        else:
            self.status_badge.setText("Başarısız ❌")
            self.status_badge.setStyleSheet(Styles.STATUS_ERROR)
    
    def _on_worker_progress(self, percentage: int):
        """Progress güncellendi."""
        self.progress_bar.setValue(percentage)
    
    def _on_worker_status(self, message: str):
        """Status mesajı."""
        self.status_badge.setText(message)
    
    def _on_worker_error(self, error_msg: str):
        """Hata oluştu."""
        dialogs.show_error(self, "Hata", error_msg)
    
    def _on_worker_result(self, result):
        """Worker sonucu."""
        if isinstance(self.current_worker, ValidationWorker):
            # Validation result
            self.validation_completed.emit(result.is_valid)
        
        elif isinstance(self.current_worker, ConversionWorker):
            # Conversion result
            output_path, backup_path = result
            self.last_output_path = output_path
            self.conversion_completed.emit(output_path)
            
            # Config'e kaydet
            self.config.set_last_output_path(output_path)
            
            # Dosya oluşturuldu dialog'u
            if dialogs.show_file_created(self, output_path):
                dialogs.open_file(output_path)
    
    def _on_worker_cancelled(self):
        """Worker iptal edildi."""
        self.status_badge.setText("İptal Edildi ⏹")
        self.status_badge.setStyleSheet(Styles.STATUS_READY)
        self._set_processing_state(False)
    
    def _set_processing_state(self, is_processing: bool):
        """İşlem durumunu ayarlar."""
        if is_processing:
            self.validate_btn.setEnabled(False)
            self.convert_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.status_badge.setText("İşleniyor... ⏳")
            self.status_badge.setStyleSheet(Styles.STATUS_PROCESSING)
        else:
            self.validate_btn.setEnabled(True)
            self.convert_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.progress_bar.setVisible(False)