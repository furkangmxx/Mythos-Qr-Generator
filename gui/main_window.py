"""
Main Window.

Ana uygulama penceresi - tüm bileşenleri bir araya getirir.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from gui.styles import Styles
from gui.conversion_section import ConversionSection
from gui.matching_section import MatchingSection
from gui.mini_log_panel import MiniLogPanel
from gui import dialogs
from config.settings import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT


class MainWindow(QMainWindow):
    """
    Ana uygulama penceresi.
    
    Yapı:
    - Menu bar (Dosya, Araçlar, Yardım)
    - İki bölümlü ana alan (Conversion + Matching)
    - Mini log panel (alt)
    - Status bar
    """
    
    def __init__(self):
        """MainWindow başlatıcı."""
        super().__init__()
        
        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._connect_signals()
    
    def _init_ui(self):
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(Styles.MAIN_WINDOW)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Splitter (üst/alt bölünmüş)
        splitter = QSplitter(Qt.Vertical)
        
        # Üst kısım: Conversion + Matching sections
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)
        
        # Mini log panel (paylaşılan)
        self.log_panel = MiniLogPanel()
        
        # Conversion section
        self.conversion_section = ConversionSection(self.log_panel)
        top_layout.addWidget(self.conversion_section)
        
        # Matching section
        self.matching_section = MatchingSection(self.log_panel)
        top_layout.addWidget(self.matching_section)
        
        splitter.addWidget(top_widget)
        
        # Alt kısım: Log panel
        splitter.addWidget(self.log_panel)
        
        # Splitter oranları (70% üst, 30% alt)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        # Başlangıç log mesajı
        self.log_panel.add_log('SYSTEM', f'{APP_NAME} v{APP_VERSION} başlatıldı.')
        self.log_panel.add_log('INFO', 'Hazır! Excel dosyanızı seçerek başlayabilirsiniz.')
    
    def _create_menu_bar(self):
        """Menu bar oluşturur."""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("📁 Dosya")
        
        open_action = QAction("Excel Aç", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_menu_open)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Araçlar menüsü
        tools_menu = menubar.addMenu("🔧 Araçlar")
        
        clear_log_action = QAction("Logları Temizle", self)
        clear_log_action.triggered.connect(self.log_panel.clear_logs)
        tools_menu.addAction(clear_log_action)
        
        export_log_action = QAction("Logları Export Et", self)
        export_log_action.triggered.connect(self.log_panel.export_to_csv)
        tools_menu.addAction(export_log_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self._on_menu_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Status bar oluşturur."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hazır")
    
    def _connect_signals(self):
        """Section sinyallerini bağlar."""
        # Conversion tamamlandığında, matching section'a path gönder
        self.conversion_section.conversion_completed.connect(
            self.matching_section.set_output_path
        )
        
        # Status bar güncellemeleri
        self.conversion_section.validation_completed.connect(
            self._on_validation_completed
        )
        self.conversion_section.conversion_completed.connect(
            self._on_conversion_completed
        )
        self.matching_section.match_check_completed.connect(
            self._on_match_check_completed
        )
        self.matching_section.matching_completed.connect(
            self._on_matching_completed
        )
    
    def _on_menu_open(self):
        """Menu: Dosya → Aç."""
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Aç",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.conversion_section.input_path_edit.setText(file_path)
    
    def _on_menu_about(self):
        """Menu: Yardım → Hakkında."""
        about_text = f"""
        <h2>{APP_NAME}</h2>
        <p><b>Versiyon:</b> {APP_VERSION}</p>
        <p><b>Geliştirici:</b> Furkan Gümüş</p>
        <br>
        <p>Mythos Cards ürün verilerini otomatik olarak Excel formatına 
        dönüştüren ve görsellerle eşleştiren masaüstü uygulaması.</p>
        <br>
        <p><b>Özellikler:</b></p>
        <ul>
            <li>Excel veri dönüştürme ve doğrulama</li>
            <li>Fuzzy görsel eşleştirme</li>
            <li>Gerçek zamanlı loglama</li>
            <li>Otomatik yedekleme sistemi</li>
            <li>İptal edilebilir işlemler</li>
        </ul>
        """
        
        dialogs.show_info(self, "Hakkında", about_text)
    
    def _on_validation_completed(self, is_valid: bool):
        """Validation tamamlandı."""
        if is_valid:
            self.status_bar.showMessage("✅ Doğrulama başarılı")
        else:
            self.status_bar.showMessage("❌ Doğrulama başarısız")
    
    def _on_conversion_completed(self, output_path: str):
        """Conversion tamamlandı."""
        self.status_bar.showMessage(f"✅ Dönüştürme tamamlandı: {output_path}")
    
    def _on_match_check_completed(self):
        """Match check tamamlandı."""
        self.status_bar.showMessage("✅ Eşleşme kontrolü tamamlandı")
    
    def _on_matching_completed(self, excel_path: str):
        """Matching tamamlandı."""
        self.status_bar.showMessage(f"✅ Eşleştirme tamamlandı: {excel_path}")
    
    def closeEvent(self, event):
        """Pencere kapatılırken."""
        # Config otomatik kaydedilir
        self.log_panel.add_log('SYSTEM', 'Uygulama kapatılıyor...')
        event.accept()