"""
Mini Log Panel.

Tabbed log viewer (All/Info/Warning/Error) ve filtreleme.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QColor
from datetime import datetime

from gui.styles import Styles


class MiniLogPanel(QWidget):
    """
    Mini log paneli widget'ı.
    
    Özellikler:
    - Tab'lı görünüm (All/Info/Warning/Error)
    - Arama/filtreleme
    - Renkli log mesajları
    - CSV export
    - Otomatik scroll
    
    Signals:
        log_cleared: Log temizlendi
    """
    
    log_cleared = Signal()
    
    def __init__(self, parent=None):
        """MiniLogPanel başlatıcı."""
        super().__init__(parent)
        
        self.logs = []  # Tüm logları sakla
        
        self._init_ui()
    
    def _init_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Üst toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(Styles.TAB_WIDGET)
        
        # Tab'lar
        self.all_log = self._create_log_text_edit()
        self.info_log = self._create_log_text_edit()
        self.warning_log = self._create_log_text_edit()
        self.error_log = self._create_log_text_edit()
        
        self.tab_widget.addTab(self.all_log, "📋 All")
        self.tab_widget.addTab(self.info_log, "✅ Info")
        self.tab_widget.addTab(self.warning_log, "⚠️ Warning")
        self.tab_widget.addTab(self.error_log, "❌ Error")
        
        layout.addWidget(self.tab_widget)
    
    def _create_toolbar(self) -> QHBoxLayout:
        """Üst toolbar oluşturur."""
        toolbar = QHBoxLayout()
        
        # Arama kutusu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Ara...")
        self.search_box.setStyleSheet(Styles.SEARCH_BOX)
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_box)
        
        toolbar.addStretch()
        
        # Log sayısı
        self.log_count_label = QLabel("Toplam: 0")
        self.log_count_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        toolbar.addWidget(self.log_count_label)
        
        # Temizle butonu
        clear_btn = QPushButton("🗑️ Temizle")
        clear_btn.setStyleSheet(Styles.SECONDARY_BUTTON)
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.clear_logs)
        toolbar.addWidget(clear_btn)
        
        # Export butonu
        export_btn = QPushButton("💾 Export")
        export_btn.setStyleSheet(Styles.SECONDARY_BUTTON)
        export_btn.setMaximumWidth(100)
        export_btn.clicked.connect(self.export_to_csv)
        toolbar.addWidget(export_btn)
        
        return toolbar
    
    def _create_log_text_edit(self) -> QTextEdit:
        """Log text edit widget'ı oluşturur."""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(Styles.LOG_PANEL)
        return text_edit
    
    def add_log(self, level: str, message: str):
        """
        Log mesajı ekler.
        
        Args:
            level: Log seviyesi (INFO, WARNING, ERROR, SYSTEM)
            message: Log mesajı
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'level': level.upper(),
            'message': message
        }
        
        self.logs.append(log_entry)
        
        # Renkli mesaj oluştur
        color = Styles.get_log_color(level)
        formatted_message = f'<span style="color: #95a5a6;">[{timestamp}]</span> ' \
                          f'<span style="color: {color}; font-weight: bold;">[{level.upper()}]</span> ' \
                          f'<span style="color: #ecf0f1;">{message}</span>'
        
        # All tab'a ekle
        self.all_log.append(formatted_message)
        self._scroll_to_bottom(self.all_log)
        
        # İlgili tab'a ekle
        if level.upper() == 'INFO':
            self.info_log.append(formatted_message)
            self._scroll_to_bottom(self.info_log)
        elif level.upper() == 'WARNING':
            self.warning_log.append(formatted_message)
            self._scroll_to_bottom(self.warning_log)
        elif level.upper() == 'ERROR':
            self.error_log.append(formatted_message)
            self._scroll_to_bottom(self.error_log)
        
        # Sayaç güncelle
        self._update_count()
    
    def clear_logs(self):
        """Tüm logları temizler."""
        self.logs.clear()
        
        self.all_log.clear()
        self.info_log.clear()
        self.warning_log.clear()
        self.error_log.clear()
        
        self._update_count()
        self.log_cleared.emit()
    
    def export_to_csv(self):
        """Logları CSV dosyasına export eder."""
        from PySide6.QtWidgets import QFileDialog
        import csv
        
        if not self.logs:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Log Dosyasını Kaydet",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'level', 'message'])
                    writer.writeheader()
                    writer.writerows(self.logs)
                
                self.add_log('SYSTEM', f'✅ Loglar kaydedildi: {file_path}')
            except Exception as e:
                self.add_log('ERROR', f'Log kaydetme hatası: {e}')
    
    def _scroll_to_bottom(self, text_edit: QTextEdit):
        """Text edit'i en alta scroll eder."""
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        text_edit.setTextCursor(cursor)
    
    def _update_count(self):
        """Log sayacını günceller."""
        count = len(self.logs)
        self.log_count_label.setText(f"Toplam: {count}")
    
    def _on_search(self, text: str):
        """
        Arama işlemini gerçekleştirir.
        
        Args:
            text: Arama metni
        """
        # Şu an aktif olan tab'da ara
        current_widget = self.tab_widget.currentWidget()
        
        if not text:
            # Arama boşsa, highlighting'i kaldır
            cursor = current_widget.textCursor()
            cursor.clearSelection()
            current_widget.setTextCursor(cursor)
            return
        
        # Highlight yap (basit implementasyon)
        # Gelişmiş: tüm eşleşmeleri highlight yapabilir
        current_widget.find(text)
    
    def get_log_count(self) -> dict:
        """
        Log sayılarını döndürür.
        
        Returns:
            {'total': int, 'info': int, 'warning': int, 'error': int}
        """
        counts = {
            'total': len(self.logs),
            'info': sum(1 for log in self.logs if log['level'] == 'INFO'),
            'warning': sum(1 for log in self.logs if log['level'] == 'WARNING'),
            'error': sum(1 for log in self.logs if log['level'] == 'ERROR')
        }
        return counts