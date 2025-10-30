"""
Kart veri modeli.
"""
from typing import Optional
from core.normalizer import Normalizer


class CardData:
    """
    Tek bir kartın tüm bilgilerini temsil eder.
    """
    
    def __init__(self,
                 series_name: str,
                 player_name: str,
                 determinant: str,
                 determinant_column: str,
                 card_printing_year: int,
                 product_information: str,
                 price: float,
                 group: Optional[str] = None):
        """CardData başlatıcı."""
        # Ana alanlar
        self.no = 0
        self.name = ""
        self.description = ""
        self.custom_product_name = ""
        self.product_information = product_information
        self.card_printing_year = card_printing_year
        self.link_url_tr = ""
        self.front_side_image = ""
        self.back_side_image = ""
        self.price = price
        self.stock = 0
        
        # İşleme alanları
        self.series_name = series_name
        self.group = group
        self.player_name = player_name
        self.determinant = determinant
        self.determinant_column = determinant_column
        
        # Normalizer
        self.normalizer = Normalizer()
    
    def generate_name(self) -> str:
        """Name alanını oluşturur."""
        year_str = f"{self.card_printing_year}-{str(self.card_printing_year + 1)[-2:]}"
        
        # Determinant formatı
        if '/' in self.determinant_column:
            det_display = f"(.../{self.determinant})"
        else:
            det_display = self.determinant
        
        # Name oluştur
        if self.group:
            self.name = f"{year_str} {self.player_name} {self.series_name} {self.group} {det_display}"
        else:
            self.name = f"{year_str} {self.player_name} {self.series_name} {det_display}"
        
        return self.name
    
    def generate_description(self) -> str:
        """Description alanını oluşturur."""
        if self.group:
            self.description = f"{self.series_name} {self.group}"
        else:
            self.description = f"{self.series_name}"
        
        return self.description
    
    def generate_link_url(self) -> str:
        """LinkUrlTR alanını oluşturur."""
        year_short = f"{self.card_printing_year}-{str(self.card_printing_year + 1)[-2:]}"
        
        # Her parçayı normalize et (YEAR HARİÇ!)
        parts = [
            year_short,  # ← Normalize YAPMA!
            self.normalizer.normalize(self.player_name),
            self.normalizer.normalize(self.series_name)
        ]
        
        if self.group:
            parts.append(self.normalizer.normalize(self.group))
        
        parts.append(self.normalizer.normalize(self.determinant))
        
        self.link_url_tr = "-".join(parts)
        return self.link_url_tr
    
    def calculate_stock(self) -> int:
        """
        Stock değerini belirler.
        
        KURAL: Kolon adına bakılır
        - Sayısal determinant (/25, /50, vb.) → Stock = değerdeki sayı
        - Yazılı determinant (Base, X İmzalı, vb.) → Stock = 0
        """
        if '/' in self.determinant_column:
            # Sayısal determinant
            try:
                number = int(''.join(filter(str.isdigit, self.determinant)))
                self.stock = number
                return number
            except:
                self.stock = 0
                return 0
        else:
            # Yazılı determinant
            self.stock = 0
            return 0