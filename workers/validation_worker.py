"""
Validation Worker.

Excel verilerini arka planda doğrular.
GUI'yi dondurmadan validation işlemini gerçekleştirir.
"""

import pandas as pd
from pathlib import Path

from workers.base_worker import BaseWorker, WorkerCancelledException
from core.data_validator import DataValidator
from utils.file_handler import FileHandler
from models.validation_result import ValidationResult


class ValidationWorker(BaseWorker):
    """
    Excel doğrulama işlemini arka planda yapar.
    
    Input:
        - excel_path: Excel dosya yolu
        
    Output:
        - ValidationResult objesi
    """
    
    def __init__(self, excel_path: str):
        """
        ValidationWorker başlatıcı.
        
        Args:
            excel_path: Doğrulanacak Excel dosyası yolu
        """
        super().__init__()
        self.excel_path = excel_path
        self.validator = DataValidator()
        self.file_handler = FileHandler()
    
    def do_work(self) -> ValidationResult:
        """
        Doğrulama işlemini gerçekleştirir.
        
        Returns:
            ValidationResult objesi
            
        Raises:
            FileNotFoundError: Dosya bulunamazsa
            Exception: Diğer hatalar
        """
        # Adım 1: Dosya kontrolü
        self.update_status("Dosya kontrol ediliyor...")
        self.update_progress(0, 100)
        
        if not Path(self.excel_path).exists():
            self.log_error(f"Dosya bulunamadı: {self.excel_path}")
            raise FileNotFoundError(f"Dosya bulunamadı: {self.excel_path}")
        
        self.check_cancelled()
        
        # Adım 2: Excel okuma
        self.update_status("Excel dosyası okunuyor...")
        self.update_progress(20, 100)
        
        try:
            df = self.file_handler.read_excel(self.excel_path)
            self.log_info(f"{len(df)} satır okundu.")
        except Exception as e:
            self.log_error(f"Excel okuma hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 3: Doğrulama
        self.update_status("Veriler doğrulanıyor...")
        self.update_progress(50, 100)
        
        result = self.validator.validate(df)
        
        self.check_cancelled()
        
        # Adım 4: Sonuç analizi
        self.update_status("Sonuçlar analiz ediliyor...")
        self.update_progress(80, 100)
        
        # Log mesajlarını GUI'ye gönder
        for error in result.errors:
            self.log_error(error['message'])
        
        for warning in result.warnings:
            self.log_warning(warning['message'])
        
        for info in result.info:
            self.log_info(info['message'])
        
        self.check_cancelled()
        
        # Adım 5: Tamamlandı
        self.update_status("Doğrulama tamamlandı!")
        self.update_progress(100, 100)
        
        if result.is_valid:
            self.log_info(f"✅ Doğrulama başarılı: {result.summary}")
        else:
            self.log_error(f"❌ Doğrulama başarısız: {result.summary}")
        
        return result