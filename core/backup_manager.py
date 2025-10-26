"""
Otomatik yedekleme yönetimi modülü.

Dönüştürme sonrası oluşturulan Excel dosyalarının
otomatik yedeğini Backup/ klasörüne alır.
"""

import shutil
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional

from config.settings import (
    BACKUP_DIR,
    BACKUP_FILE_PATTERN,
    BACKUP_FILE_PATTERN_NO_GROUP,
    DATE_FORMAT,
    DATETIME_FORMAT
)


class BackupManager:
    """
    Excel dosyalarının otomatik yedeğini yönetir.
    
    Özellikler:
    - Backup/ klasörünü otomatik oluşturur
    - İsim çakışmalarını timestamp ile çözer
    - Hata durumunda ana işlemi etkilemez
    """
    
    def __init__(self):
        """BackupManager başlatıcı."""
        self.logger = logging.getLogger(__name__)
        self.backup_dir = BACKUP_DIR
        
        # Backup klasörünü oluştur
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self) -> None:
        """
        Backup klasörünün varlığını garanti eder.
        Yoksa oluşturur.
        """
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Backup klasörü hazır: {self.backup_dir}")
        except Exception as e:
            self.logger.error(f"Backup klasörü oluşturulamadı: {e}")
            raise
    
    def create_backup(self, source_file: Path, series_name: str, 
                     group: Optional[str] = None) -> Optional[Path]:
        """
        Dosyanın yedeğini Backup/ klasörüne alır.
        
        Args:
            source_file: Yedeklenecek dosya path'i
            series_name: Seri adı (dosya adı için)
            group: Grup adı (opsiyonel)
            
        Returns:
            Backup dosyası path'i veya None (hata durumunda)
        """
        if not source_file.exists():
            self.logger.error(f"Kaynak dosya bulunamadı: {source_file}")
            return None
        
        try:
            # Backup dosya adını oluştur
            backup_filename = self._generate_backup_filename(series_name, group)
            backup_path = self.backup_dir / backup_filename
            
            # Çakışma varsa timestamp ekle
            if backup_path.exists():
                backup_path = self._resolve_conflict(backup_path)
            
            # Dosyayı kopyala
            shutil.copy2(source_file, backup_path)
            
            self.logger.info(f"✅ Backup oluşturuldu: {backup_path.name}")
            return backup_path
            
        except Exception as e:
            # Backup hatası ana işlemi etkilememeli
            self.logger.warning(f"⚠️ Backup oluşturulamadı: {e}")
            return None
    
    def _generate_backup_filename(self, series_name: str, 
                                  group: Optional[str] = None) -> str:
        """
        Backup dosya adını oluşturur.
        
        Format: <YYYYMMDD>_<series-name>_<group>_QR_Backup.xlsx
        
        Args:
            series_name: Seri adı
            group: Grup adı (opsiyonel)
            
        Returns:
            Dosya adı
        """
        from core.normalizer import Normalizer
        
        date_str = datetime.now().strftime(DATE_FORMAT)
        series_normalized = Normalizer.normalize_for_filename(series_name)
        
        if group:
            group_normalized = Normalizer.normalize_for_filename(group)
            filename = BACKUP_FILE_PATTERN.format(
                date=date_str,
                series=series_normalized,
                group=group_normalized
            )
        else:
            filename = BACKUP_FILE_PATTERN_NO_GROUP.format(
                date=date_str,
                series=series_normalized
            )
        
        return filename
    
    def _resolve_conflict(self, backup_path: Path) -> Path:
        """
        Dosya adı çakışmasını timestamp ekleyerek çözer.
        
        Args:
            backup_path: Çakışan dosya path'i
            
        Returns:
            Yeni (benzersiz) dosya path'i
        """
        # Timestamp ekle: 20251023-1515_...
        datetime_str = datetime.now().strftime(DATETIME_FORMAT)
        
        # Dosya adını parçala
        stem = backup_path.stem  # 20251023_series_group_QR_Backup
        suffix = backup_path.suffix  # .xlsx
        
        # Timestamp'i başa ekle
        new_stem = f"{datetime_str}_{stem}"
        new_path = backup_path.parent / f"{new_stem}{suffix}"
        
        self.logger.info(f"Dosya adı çakışması çözüldü: {new_path.name}")
        
        return new_path
    
    def list_backups(self, series_name: Optional[str] = None) -> list[Path]:
        """
        Backup klasöründeki dosyaları listeler.
        
        Args:
            series_name: Belirli bir seriye ait backupları filtrele (opsiyonel)
            
        Returns:
            Backup dosyaları listesi (yeniden eskiye)
        """
        try:
            if series_name:
                from core.normalizer import Normalizer
                series_normalized = Normalizer.normalize_for_filename(series_name)
                pattern = f"*{series_normalized}*_Backup.xlsx"
            else:
                pattern = "*_Backup.xlsx"
            
            backups = sorted(
                self.backup_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Backup listesi alınamadı: {e}")
            return []
    
    def delete_old_backups(self, keep_count: int = 10) -> int:
        """
        Eski backupları siler, sadece son N tanesini tutar.
        
        Args:
            keep_count: Tutulacak backup sayısı
            
        Returns:
            Silinen dosya sayısı
        """
        try:
            all_backups = self.list_backups()
            
            if len(all_backups) <= keep_count:
                return 0
            
            to_delete = all_backups[keep_count:]
            deleted_count = 0
            
            for backup in to_delete:
                try:
                    backup.unlink()
                    deleted_count += 1
                    self.logger.info(f"Eski backup silindi: {backup.name}")
                except Exception as e:
                    self.logger.warning(f"Backup silinemedi {backup.name}: {e}")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Eski backup temizleme hatası: {e}")
            return 0
    
    def get_backup_info(self) -> dict:
        """
        Backup klasörü hakkında bilgi döndürür.
        
        Returns:
            {
                'total_backups': int,
                'total_size_mb': float,
                'oldest': Path,
                'newest': Path
            }
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size_mb': 0.0,
                    'oldest': None,
                    'newest': None
                }
            
            total_size = sum(b.stat().st_size for b in backups)
            total_size_mb = total_size / (1024 * 1024)
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size_mb, 2),
                'oldest': backups[-1],
                'newest': backups[0]
            }
            
        except Exception as e:
            self.logger.error(f"Backup bilgisi alınamadı: {e}")
            return {
                'total_backups': 0,
                'total_size_mb': 0.0,
                'oldest': None,
                'newest': None
            }