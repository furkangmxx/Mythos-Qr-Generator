"""
Yol (path) işlemleri yardımcı modülü.

Dosya yolu oluşturma, doğrulama ve yönetimi.
"""

from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import logging

from config.settings import (
    BASE_DIR,
    OUTPUT_FILE_PATTERN,
    OUTPUT_FILE_PATTERN_NO_GROUP,
    DATETIME_FORMAT
)
from core.normalizer import Normalizer


class PathUtils:
    """
    Dosya yolu işlemleri için static metodlar.
    """
    
    @staticmethod
    def generate_output_filename(year: int, series_name: str, 
                                 group: Optional[str] = None) -> str:
        """
        Output dosya adını oluşturur.
        
        Format: YYYY_series-name_group_QR.xlsx
        
        Args:
            year: Yıl
            series_name: Seri adı
            group: Grup adı (opsiyonel)
            
        Returns:
            Dosya adı
        """
        series_normalized = Normalizer.normalize_for_filename(series_name)
        
        if group:
            group_normalized = Normalizer.normalize_for_filename(group)
            filename = OUTPUT_FILE_PATTERN.format(
                year=year,
                series=series_normalized,
                group=group_normalized
            )
        else:
            filename = OUTPUT_FILE_PATTERN_NO_GROUP.format(
                year=year,
                series=series_normalized
            )
        
        return filename
    
    @staticmethod
    def generate_output_path(year: int, series_name: str,
                           group: Optional[str] = None) -> Path:
        """
        Tam output dosya yolunu oluşturur.
        
        Args:
            year: Yıl
            series_name: Seri adı
            group: Grup adı (opsiyonel)
            
        Returns:
            Tam dosya path'i
        """
        filename = PathUtils.generate_output_filename(year, series_name, group)
        return BASE_DIR / filename
    
    @staticmethod
    def resolve_conflict(file_path: Path) -> Tuple[Path, str]:
        """
        Dosya adı çakışmasını çözer.
        
        Args:
            file_path: Çakışan dosya path'i
            
        Returns:
            (new_path, conflict_type) tuple
            conflict_type: 'none', 'timestamp_added'
        """
        if not file_path.exists():
            return file_path, 'none'
        
        # Timestamp ekle
        datetime_str = datetime.now().strftime(DATETIME_FORMAT)
        stem = file_path.stem
        suffix = file_path.suffix
        
        new_name = f"{stem}_{datetime_str}{suffix}"
        new_path = file_path.parent / new_name
        
        return new_path, 'timestamp_added'
    
    @staticmethod
    def ensure_directory(dir_path: Path) -> bool:
        """
        Klasörün varlığını garanti eder, yoksa oluşturur.
        
        Args:
            dir_path: Klasör yolu
            
        Returns:
            Başarılı mı?
        """
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Klasör oluşturulamadı: {e}")
            return False
    
    @staticmethod
    def validate_input_file(file_path: str) -> Tuple[bool, str]:
        """
        Input dosyasının geçerliliğini kontrol eder.
        
        Args:
            file_path: Dosya yolu
            
        Returns:
            (is_valid, error_message) tuple
        """
        path = Path(file_path)
        
        if not path.exists():
            return False, "Dosya bulunamadı."
        
        if not path.is_file():
            return False, "Bu bir dosya değil."
        
        if path.suffix.lower() not in ['.xlsx', '.xls']:
            return False, "Geçersiz dosya formatı. Excel dosyası (.xlsx, .xls) bekleniyor."
        
        if path.stat().st_size == 0:
            return False, "Dosya boş."
        
        return True, ""
    
    @staticmethod
    def validate_image_folder(folder_path: str) -> Tuple[bool, str]:
        """
        Görsel klasörünün geçerliliğini kontrol eder.
        
        Args:
            folder_path: Klasör yolu
            
        Returns:
            (is_valid, error_message) tuple
        """
        path = Path(folder_path)
        
        if not path.exists():
            return False, "Klasör bulunamadı."
        
        if not path.is_dir():
            return False, "Bu bir klasör değil."
        
        # En az bir görsel dosyası var mı?
        from config.settings import IMAGE_EXTENSIONS
        has_images = False
        
        for ext in IMAGE_EXTENSIONS:
            if list(path.rglob(f"*{ext}")):
                has_images = True
                break
        
        if not has_images:
            return False, "Klasörde görsel dosyası bulunamadı."
        
        return True, ""
    
    @staticmethod
    def get_relative_path(full_path: Path, base_path: Path = BASE_DIR) -> str:
        """
        Tam yolu göreceli yola çevirir.
        
        Args:
            full_path: Tam yol
            base_path: Baz klasör
            
        Returns:
            Göreceli yol (string)
        """
        try:
            return str(full_path.relative_to(base_path))
        except ValueError:
            return str(full_path)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Dosya boyutunu okunabilir formata çevirir.
        
        Args:
            size_bytes: Byte cinsinden boyut
            
        Returns:
            Formatlanmış string (örn: "1.5 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.1f} GB"