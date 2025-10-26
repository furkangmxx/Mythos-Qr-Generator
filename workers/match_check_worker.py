"""
Match Check Worker.

Görsel eşleştirme simülasyonu yapar (dry run).
Dosyaları değiştirmez, sadece eşleşme oranlarını gösterir.
"""

import pandas as pd
from pathlib import Path

from workers.base_worker import BaseWorker, WorkerCancelledException
from core.image_matcher import ImageMatcher
from utils.file_handler import FileHandler
from models.match_result import MatchResult


class MatchCheckWorker(BaseWorker):
    """
    Görsel eşleşme kontrolü (simülasyon).
    
    Dosyaları değiştirmez, sadece:
    - Kaç görsel bulundu?
    - Kaç ön yüz eşleşecek?
    - Kaç arka yüz eşleşecek?
    - Hangi görseller eksik?
    
    Input:
        - excel_path: Output Excel dosyası
        - image_folder: Görsel klasörü
        
    Output:
        - MatchResult objesi
    """
    
    def __init__(self, excel_path: str, image_folder: str):
        """
        MatchCheckWorker başlatıcı.
        
        Args:
            excel_path: Excel dosya yolu (output)
            image_folder: Görsel klasörü yolu
        """
        super().__init__()
        self.excel_path = excel_path
        self.image_folder = image_folder
        
        self.matcher = ImageMatcher()
        self.file_handler = FileHandler()
    
    def do_work(self) -> MatchResult:
        """
        Eşleşme kontrolü yapar (simülasyon).
        
        Returns:
            MatchResult objesi
            
        Raises:
            FileNotFoundError: Dosya/klasör bulunamazsa
            Exception: Diğer hatalar
        """
        # Adım 1: Excel kontrolü
        self.update_status("Excel dosyası kontrol ediliyor...")
        self.update_progress(0, 100)
        
        if not Path(self.excel_path).exists():
            self.log_error(f"Excel dosyası bulunamadı: {self.excel_path}")
            raise FileNotFoundError(f"Excel dosyası bulunamadı")
        
        self.check_cancelled()
        
        # Adım 2: Görsel klasörü kontrolü
        self.update_status("Görsel klasörü kontrol ediliyor...")
        self.update_progress(10, 100)
        
        if not Path(self.image_folder).exists():
            self.log_error(f"Görsel klasörü bulunamadı: {self.image_folder}")
            raise FileNotFoundError(f"Görsel klasörü bulunamadı")
        
        self.check_cancelled()
        
        # Adım 3: Excel okuma
        self.update_status("Excel dosyası okunuyor...")
        self.update_progress(20, 100)
        
        try:
            df = self.file_handler.read_excel(self.excel_path)
            self.log_info(f"{len(df)} kart bulundu.")
        except Exception as e:
            self.log_error(f"Excel okuma hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 4: Görselleri tara
        self.update_status("Görseller taranıyor...")
        self.update_progress(30, 100)
        
        try:
            image_dict = self.matcher.scan_images(self.image_folder)
            self.log_info(f"{len(image_dict)} görsel bulundu.")
        except Exception as e:
            self.log_error(f"Görsel tarama hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 5: Eşleşme simülasyonu
        self.update_status("Eşleşmeler kontrol ediliyor...")
        self.update_progress(50, 100)
        
        try:
            result = self.matcher.check_matches(df, self.image_folder)
        except Exception as e:
            self.log_error(f"Eşleşme kontrolü hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 6: Sonuçları analiz et
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
        
        # Adım 7: Özet
        self.update_status("Kontrol tamamlandı!")
        self.update_progress(100, 100)
        
        front_rate = result.get_front_match_rate()
        back_rate = result.get_back_match_rate()
        
        self.log_info("=" * 50)
        self.log_info(f"📊 EŞLEŞTİRME KONTROLÜ SONUÇLARI")
        self.log_info(f"🖼️ Ön Yüz: %{front_rate:.1f} ({result.front_matched}/{result.total_rows})")
        self.log_info(f"🖼️ Arka Yüz: %{back_rate:.1f} ({result.back_matched}/{result.total_rows})")
        self.log_info(f"⚠️ Hata: {len(result.errors)} | Uyarı: {len(result.warnings)}")
        self.log_info("=" * 50)
        
        return result