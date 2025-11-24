"""
Matching Worker.

Görsel eşleştirmeyi gerçekleştirir ve Excel'i günceller.
Sheet2'ye log kaydı ekler.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

from workers.base_worker import BaseWorker, WorkerCancelledException
from core.image_matcher import ImageMatcher
from utils.file_handler import FileHandler
from models.match_result import MatchResult


class MatchingWorker(BaseWorker):
    """
    Görsel eşleştirme işlemini gerçekleştirir.
    
    İşlem adımları:
    1. Excel oku
    2. Görselleri tara
    3. Eşleştirme yap
    4. Excel'i güncelle (FrontSideImage, BackSideImage)
    5. Sheet2'ye log ekle
    6. Kaydet
    
    Input:
        - excel_path: Output Excel dosyası
        - image_folder: Görsel klasörü
        
    Output:
        - (updated_excel_path, match_result) tuple
    """
    
    def __init__(self, excel_path: str, image_folder: str):
        """
        MatchingWorker başlatıcı.
        
        Args:
            excel_path: Excel dosya yolu (output)
            image_folder: Görsel klasörü yolu
        """
        super().__init__()
        self.excel_path = excel_path
        self.image_folder = image_folder
        
        self.matcher = ImageMatcher()
        self.file_handler = FileHandler()
    
    def do_work(self) -> Tuple[str, MatchResult]:
        """
        Eşleştirme işlemini gerçekleştirir.
        
        Returns:
            (excel_path, match_result) tuple
            
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
        self.update_progress(5, 100)
        
        if not Path(self.image_folder).exists():
            self.log_error(f"Görsel klasörü bulunamadı: {self.image_folder}")
            raise FileNotFoundError(f"Görsel klasörü bulunamadı")
        
        self.check_cancelled()
        
        # Adım 3: Excel okuma
        self.update_status("Excel dosyası okunuyor...")
        self.update_progress(10, 100)
        
        try:
            df = self.file_handler.read_excel(self.excel_path)
            self.log_info(f"{len(df)} kart bulundu.")
        except Exception as e:
            self.log_error(f"Excel okuma hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 4: Görselleri tara
        self.update_status("Görseller taranıyor...")
        self.update_progress(20, 100)
        
        try:
            image_dict = self.matcher.scan_images(self.image_folder)
            self.log_info(f"{len(image_dict)} görsel bulundu.")
        except Exception as e:
            self.log_error(f"Görsel tarama hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 5: Eşleştirme
        self.update_status("Eşleştirme yapılıyor...")
        self.update_progress(40, 100)
        
        try:
            updated_df, result = self.matcher.match(
                df,
                self.image_folder,
                dry_run=False  # Gerçek eşleştirme
            )
            
            self.log_info(f"Eşleştirme tamamlandı.")
        except Exception as e:
            self.log_error(f"Eşleştirme hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 6: Sonuçları logla
        self.update_status("Sonuçlar analiz ediliyor...")
        self.update_progress(70, 100)
        
        # Log mesajlarını GUI'ye gönder
        for error in result.errors:
            self.log_error(error['message'])
        
        for warning in result.warnings:
            self.log_warning(warning['message'])
        
        for info in result.info:
            self.log_info(info['message'])
        
        self.check_cancelled()
        
        # Adım 7: Sheet2 log oluştur
        self.update_status("Log kaydı oluşturuluyor...")
        self.update_progress(80, 100)
        
        log_df = self._create_log_sheet(result)
        
        self.check_cancelled()
        
        # Adım 8: Excel'i kaydet (Sheet1 + Sheet2)
        self.update_status("Excel dosyası kaydediliyor...")
        self.update_progress(90, 100)
        
        try:
            sheets = {
                'Sheet1': updated_df,
                'Log': log_df
            }
            
            # DÜZELTME: Argüman sırası (önce path, sonra dict)
            success = self.file_handler.write_excel_multiple_sheets(
                self.excel_path,
                sheets
            )
            
            if not success:
                raise Exception("Excel kaydedilemedi")
            
            self.log_info(f"✅ Excel güncellendi: {Path(self.excel_path).name}")
        except Exception as e:
            self.log_error(f"Excel kaydetme hatası: {e}")
            raise
        
        self.check_cancelled()
        
        # Adım 9: Tamamlandı
        self.update_status("İşlem tamamlandı!")
        self.update_progress(100, 100)
        
        front_rate = result.get_front_match_rate()
        back_rate = result.get_back_match_rate()
        
        self.log_info("=" * 50)
        self.log_info(f"✅ EŞLEŞTİRME TAMAMLANDI")
        self.log_info(f"🖼️ Ön Yüz: %{front_rate:.1f} ({result.front_matched}/{result.total_rows})")
        self.log_info(f"🖼️ Arka Yüz: %{back_rate:.1f} ({result.back_matched}/{result.total_rows})")
        self.log_info(f"📄 Dosya: {self.excel_path}")
        self.log_info("=" * 50)
        
        return (self.excel_path, result)
    
    def _create_log_sheet(self, result: MatchResult) -> pd.DataFrame:
        """
        Sheet2 için log DataFrame'i oluşturur.
        
        Args:
            result: MatchResult objesi
            
        Returns:
            Log DataFrame
        """
        log_data = []
        
        # Özet bilgileri
        log_data.append({
            'Satır': 'ÖZET',
            'Ön Yüz': f'{result.front_matched}/{result.total_rows}',
            'Arka Yüz': f'{result.back_matched}/{result.total_rows}',
            'Durum': f'{len(result.errors)} Hata, {len(result.warnings)} Uyarı',
            'Detay': ''
        })
        
        log_data.append({
            'Satır': '',
            'Ön Yüz': '',
            'Arka Yüz': '',
            'Durum': '',
            'Detay': ''
        })
        
        # Eşleştirme detayları
        for log_entry in result.match_log:
            log_data.append({
                'Satır': log_entry.get('row', ''),
                'Ön Yüz': log_entry.get('front', ''),
                'Arka Yüz': log_entry.get('back', ''),
                'Durum': log_entry.get('status', ''),
                'Detay': f"Fuzzy: {log_entry.get('fuzzy_score', 0)}" if log_entry.get('fuzzy_score') else ''
            })
        
        log_data.append({
            'Satır': '',
            'Ön Yüz': '',
            'Arka Yüz': '',
            'Durum': '',
            'Detay': ''
        })
        
        # Hatalar
        if result.errors:
            log_data.append({
                'Satır': 'HATALAR',
                'Ön Yüz': '',
                'Arka Yüz': '',
                'Durum': '',
                'Detay': ''
            })
            
            for error in result.errors:
                log_data.append({
                    'Satır': error.get('row', ''),
                    'Ön Yüz': '',
                    'Arka Yüz': '',
                    'Durum': 'HATA',
                    'Detay': error.get('message', '')
                })
        
        return pd.DataFrame(log_data)