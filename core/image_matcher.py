"""
Görsel eşleştirme modülü.

LinkUrlTR sütunundaki verilerle görselleri eşleştirir.
"arka" kelimesi içeren görseller BackSideImage, diğerleri FrontSideImage için kullanılır.

PRD v3.0 - BackSide Özel Kuralları:
- BackSide için determinant varsa TAM eşleştirme
- BackSide için determinant yoksa determinant atılarak eşleştirme
- İmzalı kontrolü MUTLAK (expected_is_signed == back_has_s)
- Aynı back görsel birden fazla satır için kullanılabilir
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import re

# Proje içinden import dene, yoksa standalone çalış
try:
    from models.match_result import MatchResult
    from config.settings import IMAGE_EXTENSIONS, FUZZY_TOLERANCE
except ImportError:
    # Standalone test için
    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp']
    FUZZY_TOLERANCE = 2
    
    class MatchResult:
        """Standalone test için basit MatchResult."""
        def __init__(self):
            self.total_rows = 0
            self.front_matched = 0
            self.front_unmatched = 0
            self.back_matched = 0
            self.back_unmatched = 0
            self.errors = []
            self.warnings = []
            self.infos = []
            self.match_logs = []
        
        def add_error(self, msg): self.errors.append(msg)
        def add_warning(self, msg, row_number=None, details=None): self.warnings.append(msg)
        def add_info(self, msg): self.infos.append(msg)
        def add_match_log(self, row, front=None, back=None, status=None): 
            self.match_logs.append({'row': row, 'front': front, 'back': back, 'status': status})
        
        def get_front_match_rate(self):
            if self.total_rows == 0: return 0
            return (self.front_matched / self.total_rows) * 100
        
        def get_back_match_rate(self):
            if self.total_rows == 0: return 0
            return (self.back_matched / self.total_rows) * 100


# ============================================================================
# CONFIGURATION
# ============================================================================

# Turkish character mapping
TR_CHAR_MAP = {
    'ç': 'c', 'Ç': 'c',
    'ğ': 'g', 'Ğ': 'g',
    'ı': 'i', 'I': 'i', 'İ': 'i',
    'ö': 'o', 'Ö': 'o',
    'ş': 's', 'Ş': 's',
    'ü': 'u', 'Ü': 'u',
}

# Patterns
DATE_PATTERN = re.compile(r'^\d{8}_')  # 20250911_ gibi
YEAR_PATTERN = re.compile(r'^\d{4}-\d{2}-')  # 2025-26- gibi
BACK_PREFIX = 'arka_'


# ============================================================================
# NORMALIZATION FUNCTIONS
# ============================================================================

def normalize_token(text: str) -> str:
    """
    Metin normalizasyonu - hem Excel hem görsel tarafı için ortak.
    
    Kurallar:
    - Türkçe karakterleri ASCII'ye dönüştür
    - Küçük harfe çevir
    - Harf ve rakam dışındaki her şeyi _ yap
    - Birden fazla _ → tek _
    - Baştaki ve sondaki _ sil
    """
    if not text:
        return ""
    
    # ÖNCELİKLE Türkçe karakterler (büyük/küçük harf dönüşümünden ÖNCE)
    for tr_char, ascii_char in TR_CHAR_MAP.items():
        text = text.replace(tr_char, ascii_char)
    
    # Sonra küçük harf
    text = text.lower()
    
    # Harf ve rakam dışındaki her şey → _
    text = re.sub(r'[^a-z0-9]', '_', text)
    
    # Birden fazla _ → tek _
    text = re.sub(r'_+', '_', text)
    
    # Baş ve sondaki _ sil
    text = text.strip('_')
    
    return text


def extract_variant(core_name: str) -> Tuple[str, str]:
    """
    Core name'den varyant kısmını ayır.
    
    Returns:
        (base_name, variant) tuple
    """
    if not core_name:
        return ("", "")
    
    parts = core_name.rsplit('_', 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    return (core_name, "")


# ============================================================================
# LINK URL TR PROCESSING
# ============================================================================

def generate_expected_from_link_url_tr(link_url_tr: str) -> str:
    """
    LinkUrlTR'den direkt expected core name üret.
    
    Args:
        link_url_tr: Ör: "2025-26-jhon-duran-youssef-en-nesyri-404-ultra-booklet-patch-imzali-1"
    
    Returns:
        Expected core name: "jhon_duran_youssef_en_nesyri_404_ultra_booklet_patch_s_1"
    """
    if not link_url_tr:
        return ""
    
    text = str(link_url_tr).strip().lower()
    
    # Baştaki yıl prefix'ini sil (2025-26- veya 2024-25- gibi)
    text = YEAR_PATTERN.sub('', text)
    
    # Tire → alt çizgi
    text = text.replace('-', '_')
    
    # Türkçe karakterler (normalde LinkUrlTR'de zaten ASCII olmalı ama garanti olsun)
    for tr_char, ascii_char in TR_CHAR_MAP.items():
        text = text.replace(tr_char, ascii_char)
    
    # "imzali" → "_s" dönüşümü (görsel formatına uyumlu)
    text = text.replace('_imzali_', '_s_')  # Ortada
    text = text.replace('_imzali', '_s')    # Sonda
    
    # Birden fazla _ → tek _
    text = re.sub(r'_+', '_', text)
    
    # Baş ve sondaki _ sil
    text = text.strip('_')
    
    return text


# ============================================================================
# IMAGE FILE PROCESSING
# ============================================================================

def parse_image_filename(filename: str, expected_variant: str = None) -> Tuple[str, str, bool]:
    """
    Görsel dosya adını parse et (FrontSide için).
    
    Args:
        filename: Dosya adı (uzantılı)
        expected_variant: LinkUrlTR'den gelen beklenen varyant (opsiyonel)
    
    Returns:
        (core_name, variant, is_back) tuple
    """
    # Uzantıyı ayır
    path = Path(filename)
    name = path.stem.lower()
    
    # 1. Başta tarih varsa sil (YYYYMMDD_)
    name = DATE_PATTERN.sub('', name)
    
    # 2. Back mi kontrol et
    is_back = False
    if name.startswith(BACK_PREFIX):
        is_back = True
        name = name[len(BACK_PREFIX):]
    
    # 3. Normalize et
    core_name_raw = normalize_token(name)
    
    # 4. _s_ işaretini KALDIRMA - olduğu gibi bırak (imzalı kontrolü için)
    core_name = core_name_raw
    
    # 5. Variant'ı çıkar
    parts = core_name.rsplit('_', 1)
    
    if len(parts) == 2:
        base_part, last_part = parts
        
        # Eğer son kısım sayı ise
        if last_part.isdigit():
            # expected_variant var mı ve TEXT mi kontrol et
            is_expected_text = expected_variant and not expected_variant.isdigit()
            
            if is_expected_text:
                # Text varyant bekleniyor, görseldeki son sayıyı atla
                inner_parts = base_part.rsplit('_', 1)
                
                if len(inner_parts) == 2:
                    inner_base, second_last = inner_parts
                    # İkinci son kısım text mi?
                    if not second_last.isdigit():
                        core_name = base_part
                        variant = second_last
                    else:
                        variant = last_part
                else:
                    if not inner_parts[0].isdigit():
                        core_name = base_part
                        variant = inner_parts[0] if inner_parts else last_part
                    else:
                        variant = last_part
            else:
                # Sayısal varyant bekleniyor
                variant = last_part
        else:
            # Son kısım zaten text
            variant = last_part
    else:
        variant = ""
    
    return (core_name, variant, is_back)


def parse_back_image_filename(filename: str) -> Tuple[str, bool, bool]:
    """
    BackSide görsel dosya adını parse et.
    
    Returns:
        (core_name, has_s_marker, has_determinant) tuple
        
    Örnekler:
        arka_xxx_s_5.jpg     → (xxx_s_5, True, True)
        arka_xxx_5.jpg       → (xxx_5, False, True)
        arka_xxx_s.jpg       → (xxx_s, True, False)
        arka_xxx.jpg         → (xxx, False, False)
    """
    # Uzantıyı ayır
    path = Path(filename)
    name = path.stem.lower()
    
    # 1. Başta tarih varsa sil
    name = DATE_PATTERN.sub('', name)
    
    # 2. "arka_" prefix'ini sil
    if name.startswith(BACK_PREFIX):
        name = name[len(BACK_PREFIX):]
    
    # 3. Normalize et
    core_name_raw = normalize_token(name)
    
    # 4. _s_ var mı kontrol et (SİLME!)
    has_s = "_s_" in core_name_raw or core_name_raw.endswith("_s")
    
    # 5. Son kısım sayı mı? (Determinant var mı?)
    parts = core_name_raw.rsplit('_', 1)
    
    has_determinant = False
    
    if len(parts) == 2:
        last_part = parts[1]
        
        # Son kısım sayı ise → Determinant VAR
        if last_part.isdigit():
            has_determinant = True
        # Son kısım "s" ise → bir öncekine bak
        elif last_part == "s":
            inner_parts = parts[0].rsplit('_', 1)
            if len(inner_parts) == 2 and inner_parts[1].isdigit():
                has_determinant = True
    
    return (core_name_raw, has_s, has_determinant)


def remove_determinant_from_back(core_name: str) -> str:
    """
    BackSide core name'den determinant'ı kaldır.
    
    Örnekler:
        xxx_s_5 → xxx_s
        xxx_5   → xxx
        xxx_s   → xxx_s (zaten yok)
        xxx     → xxx (zaten yok)
    """
    parts = core_name.rsplit('_', 1)
    
    if len(parts) == 2:
        last_part = parts[1]
        
        # Son kısım sayı ise → sil
        if last_part.isdigit():
            return parts[0]
        # Son kısım "s" ise → bir öncekine bak
        elif last_part == "s":
            inner_parts = parts[0].rsplit('_', 1)
            if len(inner_parts) == 2 and inner_parts[1].isdigit():
                # xxx_5_s → xxx_s
                return inner_parts[0] + "_s"
    
    return core_name


# ============================================================================
# IMAGE MATCHER CLASS
# ============================================================================

class ImageMatcher:
    """
    Görsel eşleştirme işlemlerini yönetir.
    """
    
    def __init__(self):
        """ImageMatcher başlatıcı."""
        self.logger = logging.getLogger(__name__)
        
        # FrontSide indexes
        self.front_map: Dict[str, str] = {}
        self.front_map_text: Dict[str, str] = {}
        
        # BackSide indexes - ÜÇ FARKLI MAP
        # 1. Determinant VAR, İmzalı VAR
        self.back_map_det_signed: Dict[str, str] = {}
        # 2. Determinant VAR, İmzalı YOK
        self.back_map_det_unsigned: Dict[str, str] = {}
        # 3. Determinant YOK, İmzalı VAR
        self.back_map_nodet_signed: Dict[str, str] = {}
        # 4. Determinant YOK, İmzalı YOK
        self.back_map_nodet_unsigned: Dict[str, str] = {}
        
        # Tüm dosya adları
        self.all_files: List[str] = []
    
    def scan_images(self, folder_path: str) -> Dict[str, Path]:
        """
        Klasördeki tüm görselleri tarar ve indexler.
        
        Args:
            folder_path: Görsel klasörü yolu
            
        Returns:
            {core_name: actual_path} dict
        """
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            raise FileNotFoundError(f"Klasör bulunamadı: {folder_path}")
        
        self.front_map.clear()
        self.front_map_text.clear()
        self.back_map_det_signed.clear()
        self.back_map_det_unsigned.clear()
        self.back_map_nodet_signed.clear()
        self.back_map_nodet_unsigned.clear()
        self.all_files.clear()
        
        image_dict = {}
        
        for ext in IMAGE_EXTENSIONS:
            for img_path in folder.rglob(f"*{ext}"):
                filename = img_path.name
                self.all_files.append(filename)
                
                # Parse et
                core_full, variant_full, is_back = parse_image_filename(filename, expected_variant=None)
                
                if is_back:
                    # BackSide için özel indexleme
                    back_core, has_s, has_det = parse_back_image_filename(filename)
                    
                    # Determinant yoksa → kaldır
                    if not has_det:
                        back_core_clean = back_core
                    else:
                        back_core_clean = back_core  # Olduğu gibi (determinant ile)
                    
                    # Doğru map'e ekle
                    if has_det and has_s:
                        self.back_map_det_signed[back_core_clean] = filename
                    elif has_det and not has_s:
                        self.back_map_det_unsigned[back_core_clean] = filename
                    elif not has_det and has_s:
                        self.back_map_nodet_signed[back_core_clean] = filename
                    else:  # not has_det and not has_s
                        self.back_map_nodet_unsigned[back_core_clean] = filename
                else:
                    # FrontSide
                    core_text, variant_text, _ = parse_image_filename(filename, expected_variant="text")
                    self.front_map[core_full] = filename
                    self.front_map_text[core_text] = filename
                
                image_dict[core_full] = img_path
        
        total_back = (len(self.back_map_det_signed) + len(self.back_map_det_unsigned) +
                     len(self.back_map_nodet_signed) + len(self.back_map_nodet_unsigned))
        
        self.logger.info(f"📂 Toplam: {len(self.all_files)} görsel indexlendi")
        self.logger.info(f"   ├─ Front: {len(self.front_map)}")
        self.logger.info(f"   └─ Back: {total_back}")
        self.logger.info(f"      ├─ Det+Signed: {len(self.back_map_det_signed)}")
        self.logger.info(f"      ├─ Det+Unsigned: {len(self.back_map_det_unsigned)}")
        self.logger.info(f"      ├─ NoDet+Signed: {len(self.back_map_nodet_signed)}")
        self.logger.info(f"      └─ NoDet+Unsigned: {len(self.back_map_nodet_unsigned)}")
        
        return image_dict
    
    def _find_exact_match(self, expected_core: str, image_map: Dict[str, str]) -> Optional[str]:
        """Tam eşleşme ara."""
        return image_map.get(expected_core)
    
    def _find_fuzzy_match(self, expected_core: str, image_map: Dict[str, str], check_variant: bool = True) -> Optional[str]:
        """
        Fuzzy eşleşme ara.
        
        Args:
            expected_core: Beklenen core name
            image_map: Görsel map'i
            check_variant: Varyant kontrolü yapılsın mı? (BackSide determinant YOK için False)
        """
        # check_variant=False ise variant ayırma, tüm kelimeyi kullan
        if check_variant:
            expected_base, expected_variant = extract_variant(expected_core)
            expected_words = expected_base.split('_')
        else:
            expected_base = expected_core
            expected_variant = ""
            expected_words = expected_core.split('_')
        
        best_match = None
        best_score = float('inf')
        
        for core_name, filename in image_map.items():
            # check_variant=False ise variant ayırma
            if check_variant:
                file_base, file_variant = extract_variant(core_name)
                
                # Varyant kontrolü
                if file_variant != expected_variant:
                    continue
                
                file_words = file_base.split('_')
            else:
                file_base = core_name
                file_variant = ""
                file_words = core_name.split('_')
            
            # Kelime sayısı AYNI OLMALI
            if len(expected_words) != len(file_words):
                continue
            
            # İKİ YÖNLÜ kelime eşleştirme
            total_distance = 0
            all_matched = True
            used_file_words = set()
            
            for exp_word in expected_words:
                found_match = False
                best_dist_for_word = float('inf')
                best_file_idx = -1
                
                for idx, file_word in enumerate(file_words):
                    if idx in used_file_words:
                        continue
                    
                    dist = self._levenshtein(exp_word, file_word)
                    
                    if dist <= FUZZY_TOLERANCE and dist < best_dist_for_word:
                        best_dist_for_word = dist
                        best_file_idx = idx
                        found_match = True
                
                if found_match:
                    used_file_words.add(best_file_idx)
                    total_distance += best_dist_for_word
                else:
                    all_matched = False
                    break
            
            if all_matched and total_distance < best_score:
                best_score = total_distance
                best_match = filename
        
        return best_match
    
    def _levenshtein(self, s1: str, s2: str) -> int:
        """Levenshtein mesafesi hesapla."""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def match(self, df: pd.DataFrame, image_folder: str, 
              dry_run: bool = False) -> Tuple[pd.DataFrame, MatchResult]:
        """
        DataFrame'deki kartları görsellerle eşleştirir.
        
        Args:
            df: Kart verileri (LinkUrlTR sütunu olmalı)
            image_folder: Görsel klasörü yolu
            dry_run: True ise simülasyon (DataFrame değişmez)
            
        Returns:
            (updated_df, match_result) tuple
        """
        result = MatchResult()
        result.total_rows = len(df)
        
        # LinkUrlTR sütunu kontrolü
        if 'LinkUrlTR' not in df.columns:
            result.add_error("LinkUrlTR sütunu bulunamadı!")
            return df, result
        
        # Görselleri tara
        try:
            self.scan_images(image_folder)
            result.add_info(f"Front: {len(self.front_map)}, Back: indexlendi.")
        except Exception as e:
            result.add_error(f"Görsel klasörü tarama hatası: {e}")
            return df, result
        
        # DataFrame kopyası
        work_df = df.copy() if not dry_run else df
        
        # FrontSideImage ve BackSideImage sütunları yoksa ekle
        if 'FrontSideImage' not in work_df.columns:
            work_df['FrontSideImage'] = ""
        if 'BackSideImage' not in work_df.columns:
            work_df['BackSideImage'] = ""
        
        # Her satır için eşleştirme yap
        for idx, row in work_df.iterrows():
            row_num = idx + 1 if isinstance(idx, int) else idx
            link_url_tr = row.get('LinkUrlTR', '')
            
            if not link_url_tr or pd.isna(link_url_tr):
                result.add_warning(
                    f"Satır {row_num}: LinkUrlTR boş",
                    row_number=row_num
                )
                result.front_unmatched += 1
                result.back_unmatched += 1
                continue
            
            # LinkUrlTR'den expected core name üret
            expected_core = generate_expected_from_link_url_tr(str(link_url_tr))
            
            # İmzalı mı?
            expected_is_signed = "_s_" in expected_core or expected_core.endswith("_s")
            
            # Expected varyantı belirle
            _, expected_variant = extract_variant(expected_core)
            
            # Varyant tipine göre doğru map'i seç (FrontSide için)
            is_text_variant = expected_variant and not expected_variant.isdigit() and expected_variant != "s"
            
            if is_text_variant:
                front_map_to_use = self.front_map_text
            else:
                front_map_to_use = self.front_map
            
            # === FRONT SIDE ===
            front_match = self._find_exact_match(expected_core, front_map_to_use)
            match_type_front = "exact"
            
            if not front_match:
                front_match = self._find_fuzzy_match(expected_core, front_map_to_use)
                match_type_front = "fuzzy" if front_match else "not_found"
            
            if front_match:
                work_df.at[idx, 'FrontSideImage'] = front_match
                result.front_matched += 1
                result.add_match_log(
                    row=row_num,
                    front=front_match,
                    status=f"OK ({match_type_front})"
                )
            else:
                result.front_unmatched += 1
                result.add_warning(
                    f"Satır {row_num}: Ön yüz görseli bulunamadı",
                    row_number=row_num,
                    details=f"LinkUrlTR: {link_url_tr}\nBeklenen: {expected_core}"
                )
            
            # === BACK SIDE ===
            # BackSide için doğru map'i seç
            # İlk olarak determinantlı map'lere bak
            back_match = None
            match_type_back = "not_found"
            
            # 1. Determinant VAR map'lerinde ara
            if expected_is_signed:
                back_match = self._find_exact_match(expected_core, self.back_map_det_signed)
                if back_match:
                    match_type_back = "exact_det"
            else:
                back_match = self._find_exact_match(expected_core, self.back_map_det_unsigned)
                if back_match:
                    match_type_back = "exact_det"
            
            # 2. Bulunamadıysa, Determinant YOK map'lerinde ara (determinant'ı silerek)
            if not back_match:
                expected_core_no_det = remove_determinant_from_back(expected_core)
                
                if expected_is_signed:
                    back_match = self._find_exact_match(expected_core_no_det, self.back_map_nodet_signed)
                    if back_match:
                        match_type_back = "exact_nodet"
                else:
                    back_match = self._find_exact_match(expected_core_no_det, self.back_map_nodet_unsigned)
                    if back_match:
                        match_type_back = "exact_nodet"
            
            # 3. Hala bulunamadıysa, Fuzzy dene (determinant VAR map'lerinde)
            if not back_match:
                if expected_is_signed:
                    back_match = self._find_fuzzy_match(expected_core, self.back_map_det_signed)
                else:
                    back_match = self._find_fuzzy_match(expected_core, self.back_map_det_unsigned)
                
                if back_match:
                    match_type_back = "fuzzy_det"
            
            # 4. Hala bulunamadıysa, Fuzzy dene (determinant YOK map'lerinde)
            # ÖNEMLİ: Determinant YOK için variant kontrolü KAPALI!
            if not back_match:
                expected_core_no_det = remove_determinant_from_back(expected_core)
                
                if expected_is_signed:
                    back_match = self._find_fuzzy_match(expected_core_no_det, self.back_map_nodet_signed, check_variant=False)
                else:
                    back_match = self._find_fuzzy_match(expected_core_no_det, self.back_map_nodet_unsigned, check_variant=False)
                
                if back_match:
                    match_type_back = "fuzzy_nodet"
            
            # BackSide sonucu yaz
            if back_match:
                work_df.at[idx, 'BackSideImage'] = back_match
                result.back_matched += 1
                result.add_match_log(
                    row=row_num,
                    back=back_match,
                    status=f"OK ({match_type_back})"
                )
            else:
                result.back_unmatched += 1
        
        # Özet
        result.add_info(
            f"Eşleştirme tamamlandı: "
            f"Ön %{result.get_front_match_rate():.1f}, "
            f"Arka %{result.get_back_match_rate():.1f}"
        )
        
        return work_df, result
    
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