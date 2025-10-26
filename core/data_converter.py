"""
Veri dönüştürme modülü.

Input Excel'i output formatına dönüştürür.
Her satır için gerekli hesaplamaları yapar ve yeni DataFrame oluşturur.
"""

import pandas as pd
from typing import List, Optional
import logging

from models.card_data import CardData
from core.normalizer import Normalizer
from core.data_validator import DataValidator
from config.settings import (
    INPUT_COLUMNS,
    OUTPUT_COLUMNS,
    PRODUCT_INFORMATION_TEXT,
    DEFAULT_PRICE
)


class DataConverter:
    """
    Excel verilerini dönüştürür ve output DataFrame oluşturur.
    
    Dönüşüm kuralları:
    - Her satır bir CardData objesine dönüştürülür
    - Name, Description, LinkUrlTR otomatik oluşturulur
    - Stock determinant tipine göre hesaplanır
    - Boş alanlar uygun şekilde doldurulur
    """
    
    def __init__(self, year: int = None):
        """
        DataConverter başlatıcı.
        
        Args:
            year: Kart basım yılı (None ise sistem yılı kullanılır)
        """
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()
        self.year = year if year else pd.Timestamp.now().year
        self.normalizer = Normalizer()
    
    def convert(self, df: pd.DataFrame, validate: bool = True) -> pd.DataFrame:
        """
        Input DataFrame'i output formatına dönüştürür.
        
        Args:
            df: Input DataFrame
            validate: Önce doğrulama yap mı?
            
        Returns:
            Output DataFrame
            
        Raises:
            ValueError: Doğrulama başarısız ise
        """
        # Doğrulama
        if validate:
            validation_result = self.validator.validate(df)
            if not validation_result.is_valid:
                error_msg = f"Doğrulama başarısız: {len(validation_result.errors)} hata bulundu."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Determinant kolonlarını tespit et
        determinant_cols = self.validator.get_determinant_columns(df)
        
        if not determinant_cols:
            raise ValueError("Determinant kolonları bulunamadı!")
        
        self.logger.info(f"Dönüştürme başlıyor: {len(df)} satır, {len(determinant_cols)} determinant kolonu")
        
        # Her satır için CardData oluştur
        cards = []
        row_number = 0
        
        for idx, row in df.iterrows():
            row_number += 1
            
            # Her determinant kolonu için ayrı kart oluştur
            for det_col in determinant_cols:
                det_value = row.get(det_col, '')
                
                # Boş determinant atla
                if pd.isna(det_value) or str(det_value).strip() == '':
                    continue
                
                # CardData oluştur
                card = self._create_card_data(row, det_col, str(det_value).strip(), row_number)
                if card:
                    cards.append(card)
        
        self.logger.info(f"{len(cards)} kart oluşturuldu")
        
        # DataFrame'e dönüştür
        output_df = self._cards_to_dataframe(cards)
        
        return output_df
    
    def _clean_determinant_value(self, value: str) -> str:
        """
        Determinant değerini temizler (.0 gibi float kalıntılarını kaldırır).
        """
        try:
            num = float(value)
            if num.is_integer():
                return str(int(num))
            else:
                return str(num)
        except (ValueError, AttributeError):
            return str(value).strip()

    def _create_card_data(self, row: pd.Series, det_column: str,
                        det_value: str, row_number: int) -> Optional[CardData]:
        """
        Tek bir satırdan CardData objesi oluşturur.
        """
        try:
            series_name = str(row.get(INPUT_COLUMNS['SERIES_NAME'], '')).strip()
            player_name = str(row.get(INPUT_COLUMNS['PLAYER_NAME'], '')).strip()
            group = row.get(INPUT_COLUMNS['GROUP'], None)
            
            if pd.isna(group) or str(group).strip() == '':
                group = None
            else:
                group = str(group).strip()
            
            # Determinant değerini temizle
            det_value_clean = self._clean_determinant_value(det_value)
            
            # Determinant tipini belirle
            if '/' in det_column:
                det_display = det_value_clean
            else:
                det_display = det_column
            
            # Zorunlu alan kontrolü
            if not series_name or not player_name:
                self.logger.warning(
                    f"Satır {row_number}: Seri Adı veya Oyuncu Adı boş, atlanıyor."
                )
                return None
            
            # CardData oluştur
            card = CardData(
                series_name=series_name,
                player_name=self.normalizer.clean_player_name(player_name),
                group=group,
                determinant=det_display,
                determinant_column=det_column,
                card_printing_year=self.year,
                product_information=PRODUCT_INFORMATION_TEXT,
                price=DEFAULT_PRICE
            )
            
            card.generate_name()
            card.generate_description()
            card.generate_link_url()
            card.calculate_stock()
            card.custom_product_name = card.player_name
            
            return card
            
        except Exception as e:
            self.logger.error(f"Satır {row_number} işlenirken hata: {e}")
            return None
        
    def _cards_to_dataframe(self, cards: List[CardData]) -> pd.DataFrame:
        """CardData listesini DataFrame'e dönüştürür."""
        data = []
        
        for idx, card in enumerate(cards, start=1):
            card.no = idx
            
            row_data = {
                'No': card.no,
                'Name': card.name,
                'Description': card.description,
                'CustomProductName': card.custom_product_name,
                'ProductInformation': card.product_information,
                'CardPrintingYear': card.card_printing_year,
                'LinkUrlTR': card.link_url_tr,
                'FrontSideImage': card.front_side_image,
                'BackSideImage': card.back_side_image,
                'Price': card.price,
                'Stock': card.stock
            }
            
            data.append(row_data)
        
        df = pd.DataFrame(data, columns=OUTPUT_COLUMNS)
        return df
    
    def get_series_and_group(self, df: pd.DataFrame) -> tuple:
        """DataFrame'den Series ve Group değerlerini çıkarır."""
        if df.empty:
            return ("unknown", None)
        
        first_row = df.iloc[0]
        
        series_name = str(first_row.get(INPUT_COLUMNS['SERIES_NAME'], 'unknown')).strip()
        group = first_row.get(INPUT_COLUMNS.get('GROUP', 'Grup'), None)
        
        if pd.isna(group) or str(group).strip() == '':
            group = None
        else:
            group = str(group).strip()
        
        return (series_name, group)        