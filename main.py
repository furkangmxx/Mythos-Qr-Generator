"""
Mythos Cards QR Generator - Ana Giriş Noktası

Uygulamayı başlatır ve GUI'yi gösterir.
"""

import sys
from pathlib import Path

# Proje kök dizinini Python path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from utils.logger import setup_logger
from gui.main_window import MainWindow


def main():
    """Ana uygulama fonksiyonu."""
    # Logger'ı ayarla
    logger = setup_logger('MythosQR')
    logger.info("=" * 60)
    logger.info("Mythos Cards QR Generator Başlatılıyor...")
    logger.info("=" * 60)
    
    try:
        # Qt Application oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("Mythos Cards QR Generator")
        app.setOrganizationName("Mythos Cards")
        
        # Ana pencereyi oluştur ve göster
        window = MainWindow()
        window.show()
        
        logger.info("GUI başarıyla başlatıldı!")
        
        # Event loop başlat
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Uygulama başlatma hatası: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()