"""
GUI stilleri ve tema yönetimi.

PySide6 QSS (Qt Style Sheets) ile modern görünüm.
"""


class Styles:
    """
    Uygulama genelinde kullanılacak CSS stilleri.
    """
    
    # Ana pencere stili
    MAIN_WINDOW = """
        QMainWindow {
            background-color: #f5f5f5;
        }
    """
    
    # Section başlıkları
    SECTION_TITLE = """
        QLabel {
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
        }
    """
    
    # Butonlar
    PRIMARY_BUTTON = """
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #21618c;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
    """
    
    SUCCESS_BUTTON = """
        QPushButton {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #229954;
        }
        QPushButton:pressed {
            background-color: #1e8449;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
    """
    
    DANGER_BUTTON = """
        QPushButton {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }
        QPushButton:pressed {
            background-color: #a93226;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
    """
    
    SECONDARY_BUTTON = """
        QPushButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #7f8c8d;
        }
        QPushButton:pressed {
            background-color: #5d6d7e;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
    """
    
    # Dosya seçici
    FILE_PICKER = """
        QLineEdit {
            padding: 8px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 13px;
            background-color: white;
        }
        QLineEdit:focus {
            border: 2px solid #3498db;
        }
        QLineEdit:disabled {
            background-color: #ecf0f1;
            color: #7f8c8d;
        }
    """
    
    BROWSE_BUTTON = """
        QPushButton {
            background-color: #34495e;
            color: white;
            border: none;
            padding: 8px 15px;
            font-size: 13px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #2c3e50;
        }
        QPushButton:pressed {
            background-color: #1a252f;
        }
    """
    
    # Year spinner
    YEAR_SPINNER = """
        QSpinBox {
            padding: 8px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 13px;
            background-color: white;
        }
        QSpinBox:focus {
            border: 2px solid #3498db;
        }
    """
    
    # Progress bar
    PROGRESS_BAR = """
        QProgressBar {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
            background-color: #ecf0f1;
        }
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 4px;
        }
    """
    
    # Status badge
    STATUS_BADGE = """
        QLabel {
            padding: 5px 15px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
    """
    
    STATUS_READY = """
        QLabel {
            padding: 5px 15px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            background-color: #95a5a6;
        }
    """
    
    STATUS_PROCESSING = """
        QLabel {
            padding: 5px 15px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            background-color: #f39c12;
        }
    """
    
    STATUS_SUCCESS = """
        QLabel {
            padding: 5px 15px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            background-color: #27ae60;
        }
    """
    
    STATUS_ERROR = """
        QLabel {
            padding: 5px 15px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            background-color: #e74c3c;
        }
    """
    
    # Log panel
    LOG_PANEL = """
        QTextEdit {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            padding: 10px;
        }
    """
    
    # Tab widget
    TAB_WIDGET = """
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #ecf0f1;
            color: #2c3e50;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background-color: white;
            color: #3498db;
        }
        QTabBar::tab:hover:!selected {
            background-color: #d5dbdb;
        }
    """
    
    # Group box
    GROUP_BOX = """
        QGroupBox {
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """
    
    # Search box (log filter)
    SEARCH_BOX = """
        QLineEdit {
            padding: 6px;
            border: 1px solid #bdc3c7;
            border-radius: 15px;
            font-size: 12px;
            background-color: white;
            padding-left: 10px;
        }
        QLineEdit:focus {
            border: 2px solid #3498db;
        }
    """
    
    @staticmethod
    def get_log_color(level: str) -> str:
        """
        Log seviyesine göre renk döndürür.
        
        Args:
            level: Log seviyesi (INFO, WARNING, ERROR, SYSTEM)
            
        Returns:
            Hex renk kodu
        """
        colors = {
            'INFO': '#2ecc71',      # Yeşil
            'WARNING': '#f39c12',   # Turuncu
            'ERROR': '#e74c3c',     # Kırmızı
            'SYSTEM': '#3498db'     # Mavi
        }
        return colors.get(level.upper(), '#ecf0f1')