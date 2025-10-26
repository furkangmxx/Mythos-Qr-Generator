"""
Görsel eşleştirme modülü.

Kart verilerini görsellerle eşleştirir (fuzzy matching).
Ön yüz ve arka yüz görselleri için ayrı kurallar uygular.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import Levenshtein

from models.match_result import MatchResult
from core.normalizer import Normalizer
from config.settings import (
    IMAGE_EXTENSIONS,
    IMAGE_BACK_MARKER,
    IMAGE_SIGNED_MARKER,
    FUZZY_TOLERANCE
)


class ImageMatcher:
    """
    Görsel eşleştirme işlemlerini yönetir.
    
    Özellikler:
    - Fuzzy matching (Levenshtein distance ≤ 2)
    - _arka_ işaretleyici ile arka yüz tespiti
    - _s_ işaretleyici ile imzalı görsellerin filtrelenmesi
    - Arka yüz için özel kurallar (player olmadan eşleştirme)
    """
    
    def __init__(self):
        """ImageMatcher başlatıcı."""
        self.logger = logging.getLogger(__name__)
        self.normalizer = Normalizer()
    
    def scan_images(self, folder_path: str) -> Dict[str, Path]:
        """
        Klasördeki tüm görselleri tarar ve indexler.
        
        Args:
            folder_path: Görsel klasörü yolu
            
        Returns:
            {normalized_filename: actual_path} dict
            
        Raises:
            FileNotFoundError: Klasör bulunamazsa
        """
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            raise FileNotFoundError(f"Klasör bulunamadı: {folder_path}")
        
        image_dict = {}
        skipped_signed = 0
        
        # Tüm görselleri tara
        for ext in IMAGE_EXTENSIONS:
            for img_path in folder.rglob(f"*{ext}"):
                filename = img_path.stem  # Uzantısız dosya adı
                
                # _s_ (signed) görselleri atla
                if self.normalizer.is_signed_image(filename):
                    skipped_signed += 1
                    continue
                
                # Normalize et ve kaydet
                normalized = self.normalizer.normalize(filename, remove_signed=True)
                image_dict[normalized] = img_path
        
        self.logger.info(
            f"{len(image_dict)} görsel indexlendi. "
            f"{skipped_signed} imzalı görsel atlandı (_s_)."
        )
        
        return image_dict
    
    def match(self, df: pd.DataFrame, image_folder: str, 
              dry_run: bool = False) -> Tuple[pd.DataFrame, MatchResult]:
        """
        DataFrame'deki kartları görsellerle eşleştirir.
        
        Args:
            df: Kart verileri (dönüştürülmüş output DataFrame)
            image_folder: Görsel klasörü yolu
            dry_run: True ise simülasyon (DataFrame değişmez)
            
        Returns:
            (updated_df, match_result) tuple
        """
        result = MatchResult()
        result.total_rows = len(df)
        
        # Görselleri tara
        try:
            image_dict = self.scan_images(image_folder)
            result.add_info(f"{len(image_dict)} görsel bulundu.")
        except Exception as e:
            result.add_error(f"Görsel klasörü tarama hatası: {e}")
            return df, result
        
        # DataFrame kopyası (dry_run için)
        work_df = df.copy() if not dry_run else df
        
        # Arka yüz görselleri ve ön yüz görselleri ayır
        back_images, front_images = self._separate_images(image_dict)
        
        result.add_info(f"Ön yüz: {len(front_images)}, Arka yüz: {len(back_images)}")
        
        # Arka yüz eşleştirme stratejisi için analiz
        back_strategy_map = self._analyze_back_strategy(work_df, back_images)
        
        # Her satır için eşleştirme yap
        for idx, row in work_df.iterrows():
            row_num = idx + 1
            
            # Ön yüz eşleştir
            front_match = self._match_front(row, front_images)
            if front_match:
                work_df.at[idx, 'FrontSideImage'] = front_match.name
                result.front_matched += 1
                result.add_match_log(
                    row=row_num,
                    front=front_match.name,
                    status="OK"
                )
            else:
                result.front_unmatched += 1
                result.add_warning(
                    f"Satır {row_num}: Ön yüz görseli bulunamadı",
                    row_number=row_num,
                    details=f"Name: {row.get('Name', '')}"
                )
            
            # Arka yüz eşleştir
            back_match = self._match_back(row, back_images, back_strategy_map)
            if back_match:
                work_df.at[idx, 'BackSideImage'] = back_match.name
                result.back_matched += 1
                result.add_match_log(
                    row=row_num,
                    back=back_match.name,
                    status="OK"
                )
            else:
                result.back_unmatched += 1
                result.add_warning(
                    f"Satır {row_num}: Arka yüz görseli bulunamadı",
                    row_number=row_num
                )
        
        # Özet
        result.add_info(
            f"Eşleştirme tamamlandı: "
            f"Ön %{result.get_front_match_rate():.1f}, "
            f"Arka %{result.get_back_match_rate():.1f}"
        )
        
        return work_df, result
    
    def _separate_images(self, image_dict: Dict[str, Path]) -> Tuple[Dict, Dict]:
        """
        Görselleri ön yüz ve arka yüz olarak ayırır.
        
        Args:
            image_dict: Tüm görseller
            
        Returns:
            (back_images, front_images) tuple
        """
        back_images = {}
        front_images = {}
        
        for normalized, path in image_dict.items():
            if IMAGE_BACK_MARKER in normalized:
                back_images[normalized] = path
            else:
                front_images[normalized] = path
        
        return back_images, front_images
    
    def _analyze_back_strategy(self, df: pd.DataFrame, 
                               back_images: Dict[str, Path]) -> Dict[str, str]:
        """
        Arka yüz eşleştirme stratejisi belirler.
        
        Bazı arka yüzler player adı içermez, bu durumda aynı determinant'a
        sahip tüm kartlara aynı arka yüz atanır.
        
        Args:
            df: Kart DataFrame'i
            back_images: Arka yüz görselleri
            
        Returns:
            {determinant_key: back_image_path} dict
        """
        # TODO: İleri seviye strateji implementasyonu
        # Şimdilik boş döndür, temel eşleştirme kullanılacak
        return {}
    
    def _match_front(self, row: pd.Series, front_images: Dict[str, Path]) -> Optional[Path]:
        """
        Tek bir satır için ön yüz görseli eşleştirir.
        
        Eşleştirme kuralı:
        Player + Series + (Group) + Determinant
        
        Args:
            row: DataFrame satırı
            front_images: Ön yüz görselleri
            
        Returns:
            Eşleşen görsel Path'i veya None
        """
        # Name alanından eşleştirme anahtarı oluştur
        name = row.get('Name', '')
        if not name:
            return None
        
        # Name formatı: <Year Range> <Player> <Series> <Group> <Det>
        # Year Range'i çıkar (ilk kelime)
        parts = name.split()
        if len(parts) < 2:
            return None
        
        # İlk kelimeyi (year range) atla
        search_parts = parts[1:]
        search_key = self.normalizer.normalize(' '.join(search_parts))
        
        # Tam eşleşme dene
        if search_key in front_images:
            return front_images[search_key]
        
        # Fuzzy eşleşme dene
        best_match = self._fuzzy_match(search_key, front_images.keys())
        if best_match:
            return front_images[best_match]
        
        return None
    
    def _match_back(self, row: pd.Series, back_images: Dict[str, Path],
                    strategy_map: Dict[str, str]) -> Optional[Path]:
        """
        Tek bir satır için arka yüz görseli eşleştirir.
        
        Eşleştirme kuralları:
        1. _arka_ + player name + series (öncelikli)
        2. _arka_ + series + (group) + determinant (player olmadan)
        
        Args:
            row: DataFrame satırı
            back_images: Arka yüz görselleri
            strategy_map: Strateji haritası
            
        Returns:
            Eşleşen görsel Path'i veya None
        """
        # Kural 1: Player + Series
        player = row.get('CustomProductName', '')
        description = row.get('Description', '')  # Series + Group
        
        if player and description:
            search_key = self.normalizer.normalize(f"{IMAGE_BACK_MARKER}{player} {description}")
            
            # Tam eşleşme
            if search_key in back_images:
                return back_images[search_key]
            
            # Fuzzy eşleşme
            best_match = self._fuzzy_match(search_key, back_images.keys())
            if best_match:
                return back_images[best_match]
        
        # Kural 2: Series + Group + Determinant (player olmadan)
        # TODO: İleri seviye implementasyon
        
        return None
    
    def _fuzzy_match(self, search_key: str, candidates: List[str]) -> Optional[str]:
        """
        Fuzzy matching ile en uygun adayı bulur.
        
        Kurallar:
        - Her kelime için Levenshtein distance ≤ FUZZY_TOLERANCE
        - En düşük toplam mesafeye sahip aday seçilir
        
        Args:
            search_key: Aranan anahtar (normalize edilmiş)
            candidates: Aday liste (normalize edilmiş)
            
        Returns:
            En uygun aday veya None
        """
        search_words = self.normalizer.split_words(search_key)
        
        if not search_words:
            return None
        
        best_candidate = None
        best_score = float('inf')
        
        for candidate in candidates:
            candidate_words = self.normalizer.split_words(candidate)
            
            # Kelime sayısı farkı çok fazlaysa atla
            if abs(len(search_words) - len(candidate_words)) > 2:
                continue
            
            # Her kelime için en yakın eşleşmeyi bul
            total_distance = 0
            matched_words = 0
            
            for search_word in search_words:
                min_distance = float('inf')
                
                for cand_word in candidate_words:
                    distance = Levenshtein.distance(search_word, cand_word)
                    if distance < min_distance:
                        min_distance = distance
                
                if min_distance <= FUZZY_TOLERANCE:
                    matched_words += 1
                    total_distance += min_distance
                else:
                    # Tolerance aşıldı, bu aday uygun değil
                    total_distance = float('inf')
                    break
            
            # Tüm kelimeler eşleştiyse ve skor daha iyiyse
            if matched_words == len(search_words) and total_distance < best_score:
                best_score = total_distance
                best_candidate = candidate
        
        return best_candidate
    
    def check_matches(self, df: pd.DataFrame, image_folder: str) -> MatchResult:
        """
        Eşleştirme simülasyonu yapar (DataFrame değiştirmez).
        
        Args:
            df: Kart DataFrame'i
            image_folder: Görsel klasörü
            
        Returns:
            MatchResult
        """
        _, result = self.match(df, image_folder, dry_run=True)
        return result