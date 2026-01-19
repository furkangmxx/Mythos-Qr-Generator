"""
Matching Section.

Alt bölüm - Görsel eşleştirme işlemleri.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar,
    QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, QThreadPool, Signal
from pathlib import Path

from gui.styles import Styles
from gui.mini_log_panel import MiniLogPanel
from gui import dialogs
from workers import MatchCheckWorker, MatchingWorker
from config.config_manager import ConfigManager
from utils.path_utils import PathUtils
from core.image_matcher import add_date_prefix_to_files



class MatchingSection(QWidget):
    """
    Matching section widget'ı.
    
    Özellikler:
    - Output Excel seçimi
    - Görsel klasörü seçimi
    - Check Matches butonu
    - Run Matching butonu
    - Cancel butonu
    - Progress bar
    - Status badge (Ön % | Arka % | Hata)
    
    Signals:
        match_check_completed: Kontrol tamamlandı
        matching_completed: Eşleştirme tamamlandı
    """
    
    match_check_completed = Signal()
    matching_completed = Signal(str)
    
    def __init__(self, log_panel: MiniLogPanel, parent=None):
        """
        MatchingSection başlatıcı.
        
        Args:
            log_panel: Mini log panel referansı
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.log_panel = log_panel
        self.config = ConfigManager()
        self.thread_pool = QThreadPool.globalInstance()
        
        self.current_worker = None
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("🟧 BÖLÜM 2: GÖRSEL EŞLEŞTİRME")
        title.setStyleSheet(Styles.SECTION_TITLE)
        layout.addWidget(title)
        
        # Group box
        group = QGroupBox()
        group.setStyleSheet(Styles.GROUP_BOX)
        group_layout = QVBoxLayout(group)
        
        # Output Excel seçimi
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Excel:"))
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Dönüştürülmüş Excel dosyası...")
        self.output_path_edit.setStyleSheet(Styles.FILE_PICKER)
        self.output_path_edit.setReadOnly(True)
        output_layout.addWidget(self.output_path_edit)
        
        browse_output_btn = QPushButton("📁 Gözat")
        browse_output_btn.setStyleSheet(Styles.BROWSE_BUTTON)
        browse_output_btn.clicked.connect(self._on_browse_output)
        output_layout.addWidget(browse_output_btn)
        
        group_layout.addLayout(output_layout)
        
        # Görsel klasörü seçimi
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("Görsel Klasörü:"))
        
        self.image_folder_edit = QLineEdit()
        self.image_folder_edit.setPlaceholderText("Görsellerin bulunduğu klasör...")
        self.image_folder_edit.setStyleSheet(Styles.FILE_PICKER)
        self.image_folder_edit.setReadOnly(True)
        image_layout.addWidget(self.image_folder_edit)
        
        browse_folder_btn = QPushButton("📂 Gözat")
        browse_folder_btn.setStyleSheet(Styles.BROWSE_BUTTON)
        browse_folder_btn.clicked.connect(self._on_browse_folder)
        image_layout.addWidget(browse_folder_btn)
        
        group_layout.addLayout(image_layout)
        
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
        
        self.check_btn = QPushButton("🔍 Check Matches")
        self.check_btn.setStyleSheet(Styles.PRIMARY_BUTTON)
        self.check_btn.clicked.connect(self._on_check_matches)
        status_button_layout.addWidget(self.check_btn)
        
        self.match_btn = QPushButton("⚙️ Run Matching")
        self.match_btn.setStyleSheet(Styles.SUCCESS_BUTTON)
        self.match_btn.clicked.connect(self._on_run_matching)
        status_button_layout.addWidget(self.match_btn)
        
        self.cancel_btn = QPushButton("⏹ Cancel")
        self.cancel_btn.setStyleSheet(Styles.DANGER_BUTTON)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        status_button_layout.addWidget(self.cancel_btn)

        self.date_prefix_btn = QPushButton("📅 Tarihleri Ekle")
        self.date_prefix_btn.setStyleSheet(Styles.PRIMARY_BUTTON)
        self.date_prefix_btn.clicked.connect(self._on_add_date_prefix)
        status_button_layout.addWidget(self.date_prefix_btn)
        
        group_layout.addLayout(status_button_layout)
        
        layout.addWidget(group)
    
    def _load_config(self):
        """Son kullanılan ayarları yükler."""
        last_output = self.config.get_last_output_path()
        if last_output and Path(last_output).exists():
            self.output_path_edit.setText(last_output)
        
        last_folder = self.config.get_last_image_folder()
        if last_folder and Path(last_folder).exists():
            self.image_folder_edit.setText(last_folder)
    
    def set_output_path(self, path: str):
        """
        Output path'i dışarıdan ayarlar.
        
        Args:
            path: Output Excel yolu
        """
        self.output_path_edit.setText(path)
    
    def _on_browse_output(self):
        """Output Excel dosyası seç."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Output Excel Dosyası Seç",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.output_path_edit.setText(file_path)
            self.config.set_last_output_path(file_path)
    
    def _on_browse_folder(self):
        """Görsel klasörü seç."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Görsel Klasörü Seç",
            str(Path.home())
        )
        
        if folder_path:
            self.image_folder_edit.setText(folder_path)
            self.config.set_last_image_folder(folder_path)

    def _on_add_date_prefix(self):
        """Tarihleri Ekle butonuna basıldı."""
        image_folder = self.image_folder_edit.text()
        
        if not image_folder:
            dialogs.show_warning(self, "Uyarı", "Lütfen görsel klasörünü seçin!")
            return
        
        # Klasör kontrolü
        is_valid, error_msg = PathUtils.validate_image_folder(image_folder)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        # Onay al
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Onay",
            "Görsellerin başına tarih prefix'i eklenecek.\nBu işlem geri alınamaz!\n\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # İşlemi yap
        self.log_panel.add_log('SYSTEM', "Tarih prefix'leri ekleniyor...")
        
        result = add_date_prefix_to_files(image_folder)
        
        # Sonuçları logla
        self.log_panel.add_log('INFO', f"✅ {result['renamed']} dosya yeniden adlandırıldı")
        self.log_panel.add_log('INFO', f"⏭️ {result['skipped']} dosya zaten tarihli (atlandı)")
        
        if result['conflicts']:
            self.log_panel.add_log('WARNING', f"⚠️ {len(result['conflicts'])} çakışma:")
            for conflict in result['conflicts']:
                self.log_panel.add_log('WARNING', f"   - {conflict}")
        
        if result['errors']:
            self.log_panel.add_log('ERROR', f"❌ {len(result['errors'])} hata:")
            for error in result['errors']:
                self.log_panel.add_log('ERROR', f"   - {error}")
        
        # Özet dialog
        summary = f"Yeniden adlandırılan: {result['renamed']}\nZaten tarihli: {result['skipped']}"
        if result['conflicts']:
            summary += f"\nÇakışma: {len(result['conflicts'])}"
        if result['errors']:
            summary += f"\nHata: {len(result['errors'])}"
        
        dialogs.show_info(self, "Tarih Ekleme Tamamlandı", summary)

    
    def _on_check_matches(self):
        """Check Matches butonuna basıldı."""
        output_path = self.output_path_edit.text()
        image_folder = self.image_folder_edit.text()
        
        if not output_path:
            dialogs.show_warning(self, "Uyarı", "Lütfen Output Excel dosyasını seçin!")
            return
        
        if not image_folder:
            dialogs.show_warning(self, "Uyarı", "Lütfen görsel klasörünü seçin!")
            return
        
        # Dosya/klasör kontrolü
        is_valid, error_msg = PathUtils.validate_input_file(output_path)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        is_valid, error_msg = PathUtils.validate_image_folder(image_folder)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        # Worker oluştur ve çalıştır
        self.current_worker = MatchCheckWorker(output_path, image_folder)
        self._connect_worker_signals(self.current_worker)
        
        self._set_processing_state(True)
        self.log_panel.add_log('SYSTEM', "Eşleşme kontrolü başlatıldı...")
        
        self.thread_pool.start(self.current_worker)
    
    def _on_run_matching(self):
        """Run Matching butonuna basıldı."""
        output_path = self.output_path_edit.text()
        image_folder = self.image_folder_edit.text()
        
        if not output_path:
            dialogs.show_warning(self, "Uyarı", "Lütfen Output Excel dosyasını seçin!")
            return
        
        if not image_folder:
            dialogs.show_warning(self, "Uyarı", "Lütfen görsel klasörünü seçin!")
            return
        
        # Dosya/klasör kontrolü
        is_valid, error_msg = PathUtils.validate_input_file(output_path)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        is_valid, error_msg = PathUtils.validate_image_folder(image_folder)
        if not is_valid:
            dialogs.show_error(self, "Hata", error_msg)
            return
        
        # Worker oluştur ve çalıştır
        self.current_worker = MatchingWorker(output_path, image_folder)
        self._connect_worker_signals(self.current_worker)
        
        self._set_processing_state(True)
        self.log_panel.add_log('SYSTEM', "Eşleştirme başlatıldı...")
        
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
        if isinstance(self.current_worker, MatchCheckWorker):
            # Match check result
            self.match_check_completed.emit()
            
            # Status badge güncelle
            front_rate = result.get_front_match_rate()
            back_rate = result.get_back_match_rate()
            error_count = len(result.errors)
            
            status_text = f"Ön %{front_rate:.0f} | Arka %{back_rate:.0f} | Hata {error_count}"
            self.status_badge.setText(status_text)
        
        elif isinstance(self.current_worker, MatchingWorker):
            # Matching result
            excel_path, match_result = result
            self.matching_completed.emit(excel_path)
            
            # Status badge güncelle
            front_rate = match_result.get_front_match_rate()
            back_rate = match_result.get_back_match_rate()
            
            status_text = f"Tamamlandı ✅ Ön %{front_rate:.0f} | Arka %{back_rate:.0f}"
            self.status_badge.setText(status_text)
            
            # Dosya oluşturuldu dialog'u
            if dialogs.show_file_created(self, excel_path):
                dialogs.open_file(excel_path)
    
    def _on_worker_cancelled(self):
        """Worker iptal edildi."""
        self.status_badge.setText("İptal Edildi ⏹")
        self.status_badge.setStyleSheet(Styles.STATUS_READY)
        self._set_processing_state(False)
    
    def _set_processing_state(self, is_processing: bool):
        """İşlem durumunu ayarlar."""
        if is_processing:
            self.check_btn.setEnabled(False)
            self.match_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.status_badge.setText("İşleniyor... ⏳")
            self.status_badge.setStyleSheet(Styles.STATUS_PROCESSING)
        else:
            self.check_btn.setEnabled(True)
            self.match_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.progress_bar.setVisible(False)