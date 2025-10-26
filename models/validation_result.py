"""
Doğrulama işlemi sonuç modeli.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ValidationResult:
    """
    Veri doğrulama işleminin sonucunu temsil eder.
    
    Attributes:
        is_valid: Doğrulama başarılı mı?
        row_count: Toplam satır sayısı
        errors: Hata listesi (log mesajı, satır no, detay)
        warnings: Uyarı listesi
        info: Bilgi mesajları
        missing_columns: Eksik kolonlar
        empty_determinants: Boş determinant sayısı
        summary: Özet bilgi
    """
    is_valid: bool = False
    row_count: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    info: List[Dict[str, Any]] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    empty_determinants: int = 0
    summary: str = ""
    
    def add_error(self, message: str, row_number: int = None, details: str = ""):
        """Hata ekle."""
        self.errors.append({
            'message': message,
            'row': row_number,
            'details': details
        })
        self.is_valid = False
    
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
    
    def get_total_issues(self) -> int:
        """Toplam sorun sayısı (hata + uyarı)."""
        return len(self.errors) + len(self.warnings)
    
    def generate_summary(self) -> str:
        """Özet rapor oluştur."""
        summary_parts = []
        summary_parts.append(f"Toplam Satır: {self.row_count}")
        summary_parts.append(f"Hata: {len(self.errors)}")
        summary_parts.append(f"Uyarı: {len(self.warnings)}")
        
        if self.empty_determinants > 0:
            summary_parts.append(f"Boş Determinant: {self.empty_determinants}")
        
        if self.is_valid:
            summary_parts.append("✅ Doğrulama Başarılı")
        else:
            summary_parts.append("❌ Doğrulama Başarısız")
        
        self.summary = " | ".join(summary_parts)
        return self.summary