"""
Görsel eşleştirme sonuç modeli.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class MatchResult:
    """
    Görsel eşleştirme işleminin sonucunu temsil eder.
    
    Attributes:
        total_rows: Toplam kart sayısı
        front_matched: Ön yüz eşleşme sayısı
        back_matched: Arka yüz eşleşme sayısı
        front_unmatched: Eşleşmeyen ön yüz sayısı
        back_unmatched: Eşleşmeyen arka yüz sayısı
        errors: Hata listesi
        warnings: Uyarı listesi
        info: Bilgi mesajları
        duplicate_backs: Çakışan arka yüzler
        skipped_images: Atlanan görseller (_s_, vb.)
        match_log: Detaylı eşleştirme logu
    """
    total_rows: int = 0
    front_matched: int = 0
    back_matched: int = 0
    front_unmatched: int = 0
    back_unmatched: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    info: List[Dict[str, Any]] = field(default_factory=list)
    duplicate_backs: List[str] = field(default_factory=list)
    skipped_images: List[str] = field(default_factory=list)
    match_log: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_error(self, message: str, row_number: int = None, details: str = ""):
        """Hata ekle."""
        self.errors.append({
            'message': message,
            'row': row_number,
            'details': details
        })
    
    def add_warning(self, message: str, row_number: int = None, details: str = ""):
        """Uyarı ekle."""
        self.warnings.append({
            'message': message,
            'row': row_number,
            'details': details
        })
    
    def add_info(self, message: str, details: str = ""):
        """Bilgi ekle."""
        self.info.append({
            'message': message,
            'details': details
        })
    
    def add_match_log(self, row: int, front: str = "", back: str = "", 
                      status: str = "", fuzzy_score: int = 0):
        """Eşleştirme log kaydı ekle."""
        self.match_log.append({
            'row': row,
            'front': front,
            'back': back,
            'status': status,
            'fuzzy_score': fuzzy_score
        })
    
    def get_front_match_rate(self) -> float:
        """Ön yüz eşleşme oranı (%)."""
        if self.total_rows == 0:
            return 0.0
        return (self.front_matched / self.total_rows) * 100
    
    def get_back_match_rate(self) -> float:
        """Arka yüz eşleşme oranı (%)."""
        if self.total_rows == 0:
            return 0.0
        return (self.back_matched / self.total_rows) * 100
    
    def generate_summary(self) -> str:
        """Özet rapor oluştur."""
        front_rate = self.get_front_match_rate()
        back_rate = self.get_back_match_rate()
        
        summary = (
            f"Ön Yüz: %{front_rate:.1f} ({self.front_matched}/{self.total_rows}) | "
            f"Arka Yüz: %{back_rate:.1f} ({self.back_matched}/{self.total_rows}) | "
            f"Hata: {len(self.errors)}"
        )
        
        return summary