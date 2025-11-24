"""
Dosya işlemleri yardımcı modülü.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict
import logging


class FileHandler:
    """Güvenli dosya okuma/yazma işlemleri."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def read_excel(self, file_path: str, sheet_name: str = None) -> Optional[pd.DataFrame]:
        """Excel dosyasını okur."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
        
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            self.logger.info(f"Excel okundu: {path.name} ({len(df)} satır)")
            return df
        except Exception as e:
            self.logger.error(f"Excel okuma hatası: {e}")
            raise
    
    def write_excel(self, df: pd.DataFrame, file_path: str, 
                   sheet_name: str = 'Sheet1', index: bool = False) -> bool:
        """DataFrame'i Excel'e yazar."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=index)
            
            self.logger.info(f"Excel oluşturuldu: {path.name}")
            return True
        except Exception as e:
            self.logger.error(f"Excel yazma hatası: {e}")
            return False
    
    def write_excel_multiple_sheets(self, file_path: str, 
                                     sheets_data: Dict[str, pd.DataFrame], 
                                     index: bool = False) -> bool:
        """
        Birden fazla sheet içeren Excel dosyası oluşturur.
        
        Args:
            file_path: Kaydedilecek dosya yolu
            sheets_data: {'SheetAdı': DataFrame, ...} formatında dict
            index: Index sütunu yazılsın mı
            
        Returns:
            Başarılı ise True
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in sheets_data.items():
                    if df is not None and not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=index)
            
            self.logger.info(f"Excel oluşturuldu: {path.name} ({len(sheets_data)} sheet)")
            return True
        except Exception as e:
            self.logger.error(f"Excel yazma hatası: {e}")
            return False