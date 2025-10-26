"""
Temel worker sınıfı.

Tüm worker'ların miras alacağı base sınıf.
İptal mekanizması, sinyal yönetimi ve hata yakalama içerir.
"""

from PySide6.QtCore import QRunnable, QObject, Slot
import traceback
import logging
from typing import Optional

from workers.worker_signals import WorkerSignals


class BaseWorker(QRunnable):
    """
    Temel worker sınıfı.
    
    Özellikler:
    - İptal edilebilir (cancel flag)
    - Progress güncelleme
    - Log mesajları
    - Hata yönetimi
    - Sinyal sistemi
    
    Alt sınıflar do_work() metodunu implemente etmelidir.
    """
    
    def __init__(self):
        """BaseWorker başlatıcı."""
        super().__init__()
        
        self.signals = WorkerSignals()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # İptal flag'i
        self._cancel_requested = False
        self._is_running = False
    
    @Slot()
    def run(self):
        """
        Worker'ı çalıştırır.
        
        Bu metod QThreadPool tarafından otomatik çağrılır.
        Alt sınıflar bunu override ETMEMELİ, do_work() metodunu implemente etmelidir.
        """
        self._is_running = True
        self._cancel_requested = False
        
        try:
            # Başladı sinyali
            self.signals.started.emit()
            self.log_info("İşlem başladı...")
            
            # Asıl işi yap
            result = self.do_work()
            
            # İptal kontrolü
            if self._cancel_requested:
                self.log_warning("İşlem kullanıcı tarafından iptal edildi.")
                self.signals.cancelled.emit()
                self.signals.finished.emit(False)
            else:
                # Başarılı
                self.log_info("İşlem tamamlandı.")
                self.signals.result.emit(result)
                self.signals.finished.emit(True)
        
        except Exception as e:
            # Hata
            error_msg = f"Hata oluştu: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_error(error_msg)
            self.signals.error.emit(error_msg)
            self.signals.finished.emit(False)
        
        finally:
            self._is_running = False
    
    def do_work(self) -> any:
        """
        Asıl işin yapıldığı metod.
        
        Alt sınıflar bu metodu implemente ETMELİDİR.
        
        Returns:
            İşlem sonucu (herhangi bir tip)
            
        Raises:
            NotImplementedError: Alt sınıf implemente etmemişse
        """
        raise NotImplementedError("Alt sınıf do_work() metodunu implemente etmelidir!")
    
    def request_cancel(self):
        """
        İptal talebi gönderir.
        
        Worker güvenli bir noktada durmalıdır.
        """
        self.logger.info("İptal talebi alındı.")
        self._cancel_requested = True
    
    def is_cancelled(self) -> bool:
        """
        İptal edilip edilmediğini kontrol eder.
        
        Worker'lar döngülerde bu metodu düzenli kontrol etmelidir.
        
        Returns:
            İptal talebi var mı?
        """
        return self._cancel_requested
    
    def is_running(self) -> bool:
        """Worker çalışıyor mu?"""
        return self._is_running
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """
        İlerleme günceller.
        
        Args:
            current: Şu anki adım
            total: Toplam adım
            message: İsteğe bağlı mesaj
        """
        if total == 0:
            percentage = 0
        else:
            percentage = int((current / total) * 100)
        
        self.signals.progress.emit(percentage)
        
        if message:
            self.signals.status.emit(message)
    
    def update_status(self, message: str):
        """
        Durum mesajı günceller.
        
        Args:
            message: Durum mesajı
        """
        self.signals.status.emit(message)
    
    def log_info(self, message: str):
        """Info log mesajı gönderir."""
        self.logger.info(message)
        self.signals.log.emit("INFO", message)
    
    def log_warning(self, message: str):
        """Warning log mesajı gönderir."""
        self.logger.warning(message)
        self.signals.log.emit("WARNING", message)
    
    def log_error(self, message: str):
        """Error log mesajı gönderir."""
        self.logger.error(message)
        self.signals.log.emit("ERROR", message)
    
    def check_cancelled(self):
        """
        İptal kontrolü yapar ve iptal edildiyse exception fırlatır.
        
        Raises:
            WorkerCancelledException: İptal talebi varsa
        """
        if self.is_cancelled():
            raise WorkerCancelledException("İşlem iptal edildi")


class WorkerCancelledException(Exception):
    """Worker iptal edildiğinde fırlatılan exception."""
    pass