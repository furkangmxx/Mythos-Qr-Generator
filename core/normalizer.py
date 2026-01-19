"""
Metin normalizasyonu modülü.

Türkçe karakterleri İngilizce'ye çevirir, boşlukları ve özel karakterleri düzenler.
Fuzzy matching için metinleri standart hale getirir.

v1.1 - Güncelleme:
- URL'de geçersiz tüm karakterler temizlendi (&, ', ", #, ?, vb.)
"""

import re
from typing import Dict
from unidecode import unidecode

from config.settings import (
    TURKISH_CHAR_MAP,
    EQUIVALENT_CHARS,
    IGNORE_PATTERNS,
    IMAGE_SIGNED_MARKER
)

# URL'de geçersiz karakterler listesi
URL_INVALID_CHARS = [
    # Kesme işaretleri ve tırnaklar
    "'", "'", "'", "`", "´",  # Kesme işaretleri
    '"', '"', '"', '„',        # Tırnaklar
    
    # Özel semboller
    '&',   # Ampersand (soruna neden olan karakter)
    '#',   # Hash
    '?',   # Soru işareti
    '@',   # At işareti
    '!',   # Ünlem
    '$',   # Dolar
    '%',   # Yüzde
    '^',   # Şapka
    '*',   # Yıldız
    '+',   # Artı
    '=',   # Eşittir
    '~',   # Tilde
    '|',   # Pipe
    '\\',  # Backslash
    
    # Parantezler
    '(', ')',   # Normal parantez
    '[', ']',   # Köşeli parantez
    '{', '}',   # Süslü parantez
    '<', '>',   # Açılı parantez
    
    # Noktalama işaretleri
    ':',   # İki nokta
    ';',   # Noktalı virgül
    ',',   # Virgül
    '.',   # Nokta
    
    # Para birimleri
    '€',   # Euro
    '£',   # Pound
    '¥',   # Yen
    '₺',   # TL
]


class Normalizer:
    """
    Metin normalizasyonu için static metodlar sağlar.
    
    Kullanım:
        normalized_text = Normalizer.normalize("Galatasaray vs Liverpool")
        # "galatasaray-vs-liverpool"
    """
    
    @staticmethod
    def normalize(text: str, remove_signed: bool = True) -> str:
        """
        Metni fuzzy matching için normalize eder.
        
        İşlemler:
        1. Türkçe karakterleri İngilizce'ye çevir
        2. Küçük harfe çevir
        3. _s_ gibi işaretleyicileri kaldır (opsiyonel)
        4. _ ve boşlukları - yap
        5. URL'de geçersiz karakterleri kaldır (/, &, ', vb.)
        6. Tarih/sayı kalıplarını kaldır
        7. Çoklu tire/boşlukları tek yap
        8. Baş/sondaki boşlukları temizle
        
        Args:
            text: Normalize edilecek metin
            remove_signed: _s_ işaretleyicisini kaldır mı? (varsayılan: True)
            
        Returns:
            Normalize edilmiş metin
            
        Examples:
            >>> Normalizer.normalize("Galatasaray_vs_Liverpool")
            'galatasaray-vs-liverpool'
            
            >>> Normalizer.normalize("Arda_Güler_Base_s_2024")
            'arda-guler-base'
            
            >>> Normalizer.normalize("Matteo Guendouzi & Asensio & Edson")
            'matteo-guendouzi-asensio-edson'
            
            >>> Normalizer.normalize("Dorgeles' Nene")
            'dorgeles-nene'
        """
        if not text or not isinstance(text, str):
            return ""
        
        # 1. Türkçe karakterleri değiştir
        normalized = Normalizer._replace_turkish_chars(text)
        
        # 2. Küçük harfe çevir
        normalized = normalized.lower()
        
        # 3. _s_ işaretleyicisini kaldır
        if remove_signed:
            normalized = normalized.replace(IMAGE_SIGNED_MARKER, "")
        
        # 4. _ ve boşlukları - yap
        for old_char, new_char in EQUIVALENT_CHARS.items():
            normalized = normalized.replace(old_char, new_char)

        # 5. URL'de geçersiz karakterleri kaldır
        # ==============================================
        # Önce / karakterini kaldır (önceden de vardı)
        normalized = normalized.replace('/', '')
        
        # Tüm geçersiz karakterleri kaldır
        for char in URL_INVALID_CHARS:
            normalized = normalized.replace(char, '')
        # ==============================================

        # 6. Tarih/sayı kalıplarını kaldır
        normalized = Normalizer._remove_ignore_patterns(normalized)
        
        # 7. Çoklu tire/boşlukları tek yap
        normalized = re.sub(r'-+', '-', normalized)
        normalized = re.sub(r'\s+', '-', normalized)
        
        # 8. Baş/son tire ve boşlukları temizle
        normalized = normalized.strip('- ')
        
        return normalized
    
    @staticmethod
    def _replace_turkish_chars(text: str) -> str:
        """
        Türkçe karakterleri İngilizce eşdeğerleriyle değiştirir.
        
        Args:
            text: Değiştirilecek metin
            
        Returns:
            Dönüştürülmüş metin
        """
        result = text
        for turkish_char, english_char in TURKISH_CHAR_MAP.items():
            result = result.replace(turkish_char, english_char)
        return result
    
    @staticmethod
    def _remove_ignore_patterns(text: str) -> str:
        """
        Yok sayılacak kalıpları (tarihler vb.) metinden kaldırır.
        
        Args:
            text: Temizlenecek metin
            
        Returns:
            Temizlenmiş metin
        """
        result = text
        for pattern in IGNORE_PATTERNS:
            result = re.sub(pattern, '', result)
        return result
    
    @staticmethod
    def normalize_for_filename(text: str) -> str:
        """
        Dosya adı için güvenli metin üretir.
        
        Boşlukları ve özel karakterleri tire ile değiştirir.
        Dosya sisteminde geçersiz karakterleri kaldırır.
        
        Args:
            text: Dosya adı için normalize edilecek metin
            
        Returns:
            Dosya adı için güvenli metin
            
        Examples:
            >>> Normalizer.normalize_for_filename("Galatasaray vs Liverpool (Group A)")
            'galatasaray-vs-liverpool-group-a'
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Türkçe karakterleri değiştir
        normalized = Normalizer._replace_turkish_chars(text)
        
        # Küçük harfe çevir
        normalized = normalized.lower()
        
        # Geçersiz karakterleri kaldır (sadece harf, rakam, tire, alt çizgi)
        normalized = re.sub(r'[^a-z0-9\-_]', '-', normalized)
        
        # Çoklu tireleri tek yap
        normalized = re.sub(r'-+', '-', normalized)
        
        # Baş/son tire temizle
        normalized = normalized.strip('-')
        
        return normalized
    
    @staticmethod
    def extract_determinant(text: str) -> tuple[str, str]:
        """
        Metinden determinant değerini çıkarır.
        
        Determinant tipleri:
        - Sayısal: /25, /50, /99 vb. (Stock = sayı)
        - Yazılı: Base, X, Short Print vb. (Stock = 0)
        
        Args:
            text: Determinant içeren metin
            
        Returns:
            (determinant_value, determinant_type) tuple
            - determinant_value: Temiz determinant değeri
            - determinant_type: "numeric" veya "text"
            
        Examples:
            >>> Normalizer.extract_determinant("/25")
            ('/25', 'numeric')
            
            >>> Normalizer.extract_determinant("Base")
            ('Base', 'text')
        """
        if not text or not isinstance(text, str):
            return ("", "text")
        
        text = text.strip()
        
        # Sayısal determinant kontrolü: / ile başlıyorsa
        if text.startswith('/'):
            # Sayıyı çıkar
            match = re.search(r'/(\d+)', text)
            if match:
                return (text, "numeric")
        
        # Yazılı determinant
        return (text, "text")
    
    @staticmethod
    def clean_player_name(name: str) -> str:
        """
        Oyuncu adını temizler (fazla boşluklar, özel karakterler).
        
        Args:
            name: Temizlenecek oyuncu adı
            
        Returns:
            Temizlenmiş ad
        """
        if not name or not isinstance(name, str):
            return ""
        
        # Çoklu boşlukları tek yap
        cleaned = re.sub(r'\s+', ' ', name)
        
        # Baş/son boşlukları temizle
        cleaned = cleaned.strip()
        
        return cleaned
    
    @staticmethod
    def split_words(text: str) -> list[str]:
        """
        Metni kelimelere böler (fuzzy matching için).
        
        Tire, alt çizgi ve boşlukları ayırıcı kabul eder.
        
        Args:
            text: Bölünecek metin
            
        Returns:
            Kelime listesi
            
        Examples:
            >>> Normalizer.split_words("galatasaray-vs-liverpool")
            ['galatasaray', 'vs', 'liverpool']
        """
        if not text or not isinstance(text, str):
            return []
        
        # Tire, alt çizgi, boşlukla böl
        words = re.split(r'[-_\s]+', text)
        
        # Boş kelimeleri filtrele
        words = [w for w in words if w]
        
        return words
    
    @staticmethod
    def compare_normalized(text1: str, text2: str) -> bool:
        """
        İki metni normalize ederek karşılaştırır (tam eşitlik).
        
        Args:
            text1: İlk metin
            text2: İkinci metin
            
        Returns:
            Normalize edilmiş halleri eşit mi?
        """
        norm1 = Normalizer.normalize(text1)
        norm2 = Normalizer.normalize(text2)
        return norm1 == norm2
    
    @staticmethod
    def is_back_image(filename: str) -> bool:
        """
        Dosya adının arka yüz görseli olup olmadığını kontrol eder.
        
        Args:
            filename: Kontrol edilecek dosya adı
            
        Returns:
            _arka_ içeriyor mu?
        """
        if not filename:
            return False
        return IMAGE_SIGNED_MARKER.replace('_s_', '_arka_') in filename.lower()
    
    @staticmethod
    def is_signed_image(filename: str) -> bool:
        """
        Dosya adının imzalı görsel olup olmadığını kontrol eder.
        
        Args:
            filename: Kontrol edilecek dosya adı
            
        Returns:
            _s_ içeriyor mu?
        """
        if not filename:
            return False
        return IMAGE_SIGNED_MARKER in filename.lower()