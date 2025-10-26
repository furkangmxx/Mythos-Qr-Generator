"""
Worker sinyal sistemi.

QRunnable worker'ların GUI ile iletişim kurması için
Qt sinyal sınıflarını içerir.
"""

from PySide6.QtCore import QObject, Signal
from typing import Any, Dict


class WorkerSignals(QObject):
    """
    Worker'ların GUI'ye mesaj göndermek için kullandığı sinyaller.
    
    Sinyaller:
        started: İşlem başladı
        finished: İşlem tamamlandı (başarılı/başarısız)
        progress: İlerleme güncellendi (0-100)
        status: Durum mesajı (string)
        log: Log mesajı (level, message)
        error: Hata oluştu (error_message)
        result: İşlem sonucu (data dict)
        cancelled: İşlem iptal edildi
    """
    
    # İşlem durumu sinyalleri
    started = Signal()
    finished = Signal(bool)  # success: bool
    cancelled = Signal()
    
    # İlerleme sinyalleri
    progress = Signal(int)  # percentage: 0-100
    status = Signal(str)    # status message
    
    # Log sinyalleri
    log = Signal(str, str)  # level, message
    
    # Hata sinyali
    error = Signal(str)     # error message
    
    # Sonuç sinyali
    result = Signal(object)  # result data (any type)