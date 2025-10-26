"""
Konfigürasyon yönetimi modülü.

Kullanıcı tercihlerini ve son kullanılan yolları
JSON dosyasında saklar ve yükler.
"""

import json
from pathlib import Path
from typing import Any, Optional
import logging

from config.settings import (
    CONFIG_FILE,
    DEFAULT_CONFIG,
    BASE_DIR
)


class ConfigManager:
    """
    Uygulama konfigürasyonunu yönetir.
    
    Saklanan bilgiler:
    - Son kullanılan input dosya yolu
    - Son kullanılan output dosya yolu
    - Son kullanılan görsel klasörü
    - Varsayılan yıl
    - Tema tercihi
    """
    
    def __init__(self):
        """ConfigManager başlatıcı."""
        self.logger = logging.getLogger(__name__)
        self.config_file = CONFIG_FILE
        self.config = DEFAULT_CONFIG.copy()
        
        # Ana klasörü oluştur
        self._ensure_base_dir()
        
        # Config'i yükle
        self.load()
    
    def _ensure_base_dir(self) -> None:
        """Ana çalışma klasörünü oluşturur."""
        try:
            BASE_DIR.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Çalışma klasörü hazır: {BASE_DIR}")
        except Exception as e:
            self.logger.error(f"Çalışma klasörü oluşturulamadı: {e}")
            raise
    
    def load(self) -> None:
        """
        Config dosyasını yükler.
        Dosya yoksa varsayılan değerleri kullanır.
        """
        if not self.config_file.exists():
            self.logger.info("Config dosyası bulunamadı, varsayılan değerler kullanılıyor.")
            self.save()  # Varsayılan config'i kaydet
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            # Loaded config'i mevcut config'le birleştir (eksik keyler için varsayılan değer)
            for key, default_value in DEFAULT_CONFIG.items():
                if key in loaded_config:
                    self.config[key] = loaded_config[key]
                else:
                    self.config[key] = default_value
            
            self.logger.info("Config dosyası yüklendi.")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Config dosyası parse edilemedi: {e}")
            self.logger.info("Varsayılan değerler kullanılıyor.")
            self.config = DEFAULT_CONFIG.copy()
        except Exception as e:
            self.logger.error(f"Config yükleme hatası: {e}")
            self.config = DEFAULT_CONFIG.copy()
    
    def save(self) -> bool:
        """
        Mevcut config'i dosyaya kaydeder.
        
        Returns:
            Başarılı mı?
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.debug("Config dosyası kaydedildi.")
            return True
            
        except Exception as e:
            self.logger.error(f"Config kaydetme hatası: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Config değerini döndürür.
        
        Args:
            key: Config anahtarı
            default: Key bulunamazsa döndürülecek varsayılan değer
            
        Returns:
            Config değeri veya default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> None:
        """
        Config değerini ayarlar.
        
        Args:
            key: Config anahtarı
            value: Yeni değer
            save_immediately: Hemen dosyaya kaydet mi?
        """
        self.config[key] = value
        
        if save_immediately:
            self.save()
    
    def set_last_input_path(self, path: str) -> None:
        """Son kullanılan input dosya yolunu kaydet."""
        self.set('last_input_path', path)
    
    def get_last_input_path(self) -> str:
        """Son kullanılan input dosya yolunu getir."""
        return self.get('last_input_path', '')
    
    def set_last_output_path(self, path: str) -> None:
        """Son kullanılan output dosya yolunu kaydet."""
        self.set('last_output_path', path)
    
    def get_last_output_path(self) -> str:
        """Son kullanılan output dosya yolunu getir."""
        return self.get('last_output_path', '')
    
    def set_last_image_folder(self, path: str) -> None:
        """Son kullanılan görsel klasörünü kaydet."""
        self.set('last_image_folder', path)
    
    def get_last_image_folder(self) -> str:
        """Son kullanılan görsel klasörünü getir."""
        return self.get('last_image_folder', '')
    
    def set_default_year(self, year: int) -> None:
        """Varsayılan yılı kaydet."""
        self.set('default_year', year)
    
    def get_default_year(self) -> int:
        """Varsayılan yılı getir."""
        return self.get('default_year', DEFAULT_CONFIG['default_year'])
    
    def set_theme(self, theme: str) -> None:
        """Tema tercihini kaydet (light/dark)."""
        if theme not in ['light', 'dark']:
            self.logger.warning(f"Geçersiz tema: {theme}")
            return
        
        self.set('theme', theme)
    
    def get_theme(self) -> str:
        """Tema tercihini getir."""
        return self.get('theme', 'light')
    
    def reset_to_defaults(self) -> None:
        """Config'i varsayılan değerlere sıfırlar."""
        self.config = DEFAULT_CONFIG.copy()
        self.save()
        self.logger.info("Config varsayılan değerlere sıfırlandı.")
    
    def get_all(self) -> dict:
        """Tüm config'i döndürür."""
        return self.config.copy()
    
    def update_multiple(self, updates: dict, save_immediately: bool = True) -> None:
        """
        Birden fazla config değerini günceller.
        
        Args:
            updates: {key: value} dict
            save_immediately: Hemen kaydet mi?
        """
        for key, value in updates.items():
            self.config[key] = value
        
        if save_immediately:
            self.save()