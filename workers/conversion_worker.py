"""
Conversion Worker.

Excel verilerini dönüştürür, kaydeder ve yedekler.
Tüm işlemi arka planda yapar.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

from workers.base_worker import BaseWorker, WorkerCancelledException
from core.data_validator import DataValidator
from core.data_converter import DataConverter
from core.backup_manager import BackupManager
from utils.file_handler import FileHandler
from utils.path_utils import PathUtils


class ConversionWorker(BaseWorker):
    """
    Excel dönüştürme işlemini arka planda yapar.
    
    İşlem adımları:
    1. Excel oku
    2. Validate et
    3. Dönüştür
    4. Kaydet
    5. Backup oluştur
    
    Input:
        - input_path: Input Excel yolu
        - year: Kart basım yılı
        
    Output:
        - (output_path, backup_path) tuple
    """
    
    def __init__(self, input_path: str, year: int):
        """
        ConversionWorker başlatıcı.
        
        Args:
            input_path: Input Excel dosya yolu
            year: Kart basım yılı
        """
        super().__init__()
        self.input_path = input_path
        self.year = year
        
        self.validator = DataValidator()
        self.converter = DataConverter(year=year)
        self.backup_manager = BackupManager()
        self.file_handler = FileHandler()
    
    def do_work(self) -> Tuple[str, str]:
        """
        Dönüştürme işlemini gerçekleştirir.
        
        Returns:
            (output_path, backup_path) tuple
            
        Raises:
            FileNotFoundError: Input dosyası bulunamazsa
            ValueError: Doğrulama başarısız olursa
            Exception: Diğer hatalar
        """
        # Adım 1: Input dosyası kontrolü
        self.update_status("Input dosyası kontrol ediliyor...")
        self.update_progress(0, 100)
        
        if not Path(self.input_path).exists():
            self.log_error(f"Input dosyası bulunamadı: {self.input_path}")
            raise FileNotFoundError(f"Dosya bulunamadı: {self.input_path}")
        
        self.check_cancelled()
        
        # Adım 2: Excel okuma
        self.update_status("Excel dosyası okunuyor...")
        self.update_progress(10, 100)
        
        try:
            df = self.file_handler.read_excel(self.input_path)
            self.log_info(f"{len(df)} satır okundu.")
        except Exception as e:
            self.log_error(f"Excel okuma hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 3: Doğrulama
        self.update_status("Veriler doğrulanıyor...")
        self.update_progress(20, 100)
        
        validation_result = self.validator.validate(df)
        
        if not validation_result.is_valid:
            error_count = len(validation_result.errors)
            self.log_error(f"Doğrulama başarısız: {error_count} hata bulundu.")
            
            # İlk birkaç hatayı logla
            for i, error in enumerate(validation_result.errors[:5]):
                self.log_error(f"  - {error['message']}")
            
            if error_count > 5:
                self.log_warning(f"  ... ve {error_count - 5} hata daha")
            
            raise ValueError(f"Doğrulama başarısız: {error_count} hata")
        
        self.log_info(f"✅ Doğrulama başarılı: {validation_result.summary}")
        
        self.check_cancelled()
        
        # Adım 4: Dönüştürme
        self.update_status("Veriler dönüştürülüyor...")
        self.update_progress(40, 100)
        
        try:
            output_df = self.converter.convert(df, validate=False)  # Zaten validate ettik
            self.log_info(f"{len(output_df)} kart oluşturuldu.")
        except Exception as e:
            self.log_error(f"Dönüştürme hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 5: Output yolu belirleme
        self.update_status("Output dosya yolu hazırlanıyor...")
        self.update_progress(60, 100)
        
        series_name, group = self.converter.get_series_and_group(df)
        output_path = PathUtils.generate_output_path(self.year, series_name, group)
        
        # Dosya çakışması varsa çöz
        if output_path.exists():
            new_path, conflict_type = PathUtils.resolve_conflict(output_path)
            self.log_warning(f"Dosya zaten mevcut, timestamp eklendi: {new_path.name}")
            output_path = new_path
        
        self.log_info(f"Output: {output_path.name}")
        
        self.check_cancelled()
        
        # Adım 6: Excel kaydetme
        self.update_status("Excel dosyası kaydediliyor...")
        self.update_progress(70, 100)
        
        try:
            success = self.file_handler.write_excel(
                output_df,
                str(output_path),
                sheet_name='Sheet1'
            )
            
            if not success:
                raise Exception("Excel kaydedilemedi")
            
            self.log_info(f"✅ Excel kaydedildi: {output_path.name}")
        except Exception as e:
            self.log_error(f"Excel kaydetme hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 7: Backup oluşturma
        self.update_status("Backup oluşturuluyor...")
        self.update_progress(85, 100)
        
        backup_path = None
        try:
            backup_path = self.backup_manager.create_backup(
                output_path,
                series_name=series_name,
                group=group
            )
            
            if backup_path:
                self.log_info(f"✅ Backup oluşturuldu: {backup_path.name}")
            else:
                self.log_warning("⚠️ Backup oluşturulamadı (ana işlem etkilenmedi)")
        except Exception as e:
            self.log_warning(f"⚠️ Backup hatası: {e} (ana işlem etkilenmedi)")
        
        self.check_cancelled()
        
        # Adım 8: Tamamlandı
        self.update_status("İşlem tamamlandı!")
        self.update_progress(100, 100)
        
        self.log_info("=" * 50)
        self.log_info(f"✅ DÖNÜŞTÜRME TAMAMLANDI")
        self.log_info(f"📄 Output: {output_path}")
        if backup_path:
            self.log_info(f"💾 Backup: {backup_path}")
        self.log_info("=" * 50)
        
        return (str(output_path), str(backup_path) if backup_path else "")