"""
Loglama sistemi modülü.

Hem console'a hem de dosyaya log yazmayı destekler.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config.settings import LOG_DIR, LOG_FILE_MAX_SIZE


def setup_logger(name: str = 'MythosQR', level: int = logging.INFO) -> logging.Logger:
    """
    Logger'ı yapılandırır ve döndürür.
    
    Özellikler:
    - Console output (renkli)
    - Dosya output (rotating file handler)
    - Tarih-saat damgalı mesajlar
    
    Args:
        name: Logger adı
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Yapılandırılmış Logger
    """
    logger = logging.getLogger(name)
    
    # Zaten yapılandırılmışsa tekrar yapma
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Format
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    try:
        # Log klasörünü oluştur
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Log dosya adı: app_20251023.log
        log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
        log_file = LOG_DIR / log_filename
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_MAX_SIZE * 1024 * 1024,  # MB -> bytes
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning(f"Log dosyası oluşturulamadı: {e}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Mevcut logger'ı döndürür veya yeni oluşturur.
    
    Args:
        name: Logger adı (None ise root logger)
        
    Returns:
        Logger
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger('MythosQR')


def set_log_level(level: int) -> None:
    """
    Tüm handler'ların log seviyesini ayarlar.
    
    Args:
        level: Yeni log seviyesi
    """
    logger = get_logger()
    logger.setLevel(level)
    
    for handler in logger.handlers:
        handler.setLevel(level)