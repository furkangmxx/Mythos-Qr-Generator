"""
Veri doğrulama modülü.

Input Excel dosyasının yapısını ve içeriğini doğrular.
Eksik kolonları, boş alanları ve hatalı verileri tespit eder.
"""

import pandas as pd
from typing import List, Set
import logging

from models.validation_result import ValidationResult
from config.settings import (
    INPUT_COLUMNS,
    DETERMINANT_KEYWORDS
)


class DataValidator:
    """
    Excel verilerini doğrular ve ValidationResult döndürür.
    
    Kontroller:
    - Gerekli kolonların varlığı
    - Zorunlu alanların doluluğu (Series Name, Player Name)
    - Determinant kolonlarının tespiti
    - Boş determinant sayısı
    - Veri tipi kontrolü
    """
    
    def __init__(self):
        """DataValidator başlatıcı."""
        self.logger = logging.getLogger(__name__)
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        DataFrame'i doğrular ve detaylı sonuç döndürür.
        
        Args:
            df: Doğrulanacak DataFrame
            
        Returns:
            ValidationResult objesi (hatalar, uyarılar, bilgiler içerir)
            
        Raises:
            ValueError: DataFrame boş ise
        """
        result = ValidationResult()
        
        # DataFrame boş kontrolü
        if df is None or df.empty:
            result.add_error("Excel dosyası boş veya okunamadı!")
            result.generate_summary()
            return result
        
        result.row_count = len(df)
        result.add_info(f"Toplam {result.row_count} satır bulundu.")
        
        # 1. Gerekli kolonları kontrol et
        missing_cols = self._check_required_columns(df, result)
        if missing_cols:
            result.generate_summary()
            return result  # Kritik hata, devam edilemez
        
        # 2. Determinant kolonlarını tespit et
        determinant_cols = self._find_determinant_columns(df)
        if not determinant_cols:
            result.add_error("Hiçbir determinant kolonu bulunamadı! (Base, Short Print, X, /, vb.)")
            result.generate_summary()
            return result
        
        result.add_info(f"Tespit edilen determinant kolonları: {', '.join(determinant_cols)}")
        
        # 3. Satır bazında doğrulamalar
        self._validate_rows(df, determinant_cols, result)
        
        # 4. Özet oluştur
        if len(result.errors) == 0:
            result.is_valid = True
            result.add_info("✅ Tüm doğrulamalar başarılı!")
        else:
            result.add_info(f"❌ {len(result.errors)} hata bulundu.")
        
        result.generate_summary()
        return result
    
    def _check_required_columns(self, df: pd.DataFrame, result: ValidationResult) -> List[str]:
        """
        Gerekli kolonların varlığını kontrol eder.
        
        Args:
            df: DataFrame
            result: ValidationResult (güncellenir)
            
        Returns:
            Eksik kolon listesi
        """
        required_columns = [
            INPUT_COLUMNS['SERIES_NAME'],
            INPUT_COLUMNS['PLAYER_NAME']
        ]
        
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
                result.add_error(f"Gerekli kolon eksik: '{col}'")
        
        result.missing_columns = missing_columns
        return missing_columns
    
    def _find_determinant_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Determinant kolonlarını tespit eder.
        
        KURAL: Seri Adı, Grup, Oyuncu Adı DIŞINDA kalan tüm kolonlar determinant'tır!
        """
        determinant_cols = []
        
        # Sabit kolonlar (bunlar determinant DEĞİL)
        fixed_columns = [
            INPUT_COLUMNS['SERIES_NAME'],   # Seri Adı
            INPUT_COLUMNS['GROUP'],          # Grup
            INPUT_COLUMNS['PLAYER_NAME']     # Oyuncu Adı
        ]
        
        for col in df.columns:
            # Eğer sabit kolon değilse → determinant!
            if col not in fixed_columns:
                determinant_cols.append(col)
        
        self.logger.info(f"Bulunan determinant kolonları: {determinant_cols}")
        
        return determinant_cols
    
    def _validate_rows(self, df: pd.DataFrame, determinant_cols: List[str], 
                       result: ValidationResult) -> None:
        """
        Her satırı doğrular.
        
        Kontroller:
        - Series Name boş mu?
        - Player Name boş mu?
        - En az bir determinant dolu mu?
        
        Args:
            df: DataFrame
            determinant_cols: Determinant kolon listesi
            result: ValidationResult (güncellenir)
        """
        series_col = INPUT_COLUMNS['SERIES_NAME']
        player_col = INPUT_COLUMNS['PLAYER_NAME']
        group_col = INPUT_COLUMNS.get('GROUP', 'Group')
        
        empty_determinant_count = 0
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel satır numarası (başlık + 1)
            
            # Series Name kontrolü
            series_name = row.get(series_col, '')
            if pd.isna(series_name) or str(series_name).strip() == '':
                result.add_error(
                    f"Satır {row_num}: 'Series Name' alanı boş!",
                    row_number=row_num,
                    details="Series Name zorunlu bir alandır."
                )
            
            # Player Name kontrolü
            player_name = row.get(player_col, '')
            if pd.isna(player_name) or str(player_name).strip() == '':
                result.add_error(
                    f"Satır {row_num}: 'Player Name' alanı boş!",
                    row_number=row_num,
                    details="Player Name zorunlu bir alandır."
                )
            
            # Determinant kontrolü: En az bir tane dolu olmalı
            has_determinant = False
            for det_col in determinant_cols:
                det_value = row.get(det_col, '')
                if not pd.isna(det_value) and str(det_value).strip() != '':
                    has_determinant = True
                    break
            
            if not has_determinant:
                empty_determinant_count += 1
                result.add_warning(
                    f"Satır {row_num}: Hiçbir determinant alanı dolu değil!",
                    row_number=row_num,
                    details=f"Kontrol edilen kolonlar: {', '.join(determinant_cols)}"
                )
        
        result.empty_determinants = empty_determinant_count
        
        if empty_determinant_count > 0:
            result.add_warning(
                f"Toplam {empty_determinant_count} satırda determinant alanı boş."
            )
    
    def get_determinant_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Sadece determinant kolonlarını döndürür (validation yapmadan).
        
        Args:
            df: DataFrame
            
        Returns:
            Determinant kolon listesi
        """
        return self._find_determinant_columns(df)
    
    def quick_validate(self, df: pd.DataFrame) -> bool:
        """
        Hızlı doğrulama (sadece True/False döner).
        
        Args:
            df: DataFrame
            
        Returns:
            Doğrulama başarılı mı?
        """
        result = self.validate(df)
        return result.is_valid