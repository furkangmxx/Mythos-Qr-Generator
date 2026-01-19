"""
Görsel eşleştirme modülü.

LinkUrlTR sütunundaki verilerle görselleri eşleştirir.
"arka" kelimesi içeren görseller BackSideImage, diğerleri FrontSideImage için kullanılır.

PRD v4.2 - BackSide 6 Seviyeli Eşleştirme:
- Seviye 1: Oyuncu + Seri + Grup + Determinant (en spesifik)
- Seviye 2: Oyuncu + Seri + Grup (determinant yok) ← YENİ!
- Seviye 3: Seri + Grup + Determinant
- Seviye 4: Seri + Grup (determinant yok)
- Seviye 5: Seri + Determinant (grup yok)
- Seviye 6: Seri (en genel)
- Her seviyede İmzalı/İmzalısız MUTLAK ayrımı
- Aynı back görsel birden fazla satır için kullanılabilir

v1.1 - Güncelleme:
- Text determinant için görselin sonundaki sayı yoksayılıyor
- Sayısal: ..._s_25 (sayı önemli, eşleşmeli)
- Text: ..._short_print_s (görseldeki _2 yoksay)
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import re
from datetime import datetime
import os


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
TRAILING_NUMBER_PATTERN = re.compile(r'_\d+$')  # Sondaki _sayı pattern'i


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


def remove_trailing_number(core_name: str) -> str:
    """
    Core name'den sondaki sayıyı kaldır.
    
    Örnekler:
        "xxx_short_print_s_2" → "xxx_short_print_s"
        "xxx_base_3" → "xxx_base"
        "xxx_s_25" → "xxx_s_25" (değişmez - bu sayısal determinant)
    """
    if not core_name:
        return ""
    return TRAILING_NUMBER_PATTERN.sub('', core_name)


def is_numeric_determinant(expected_core: str) -> bool:
    """
    Expected core name'in sayısal determinant olup olmadığını kontrol et.
    
    Sayısal: ..._s_25 veya ..._25 (sayı ile bitiyor)
    Text: ..._short_print_s veya ..._base (text ile bitiyor)
    """
    if not expected_core:
        return False
    
    _, variant = extract_variant(expected_core)
    return variant.isdigit()


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


def generate_back_expected_levels(player_name: str, series_name: str, group: str, 
                                   determinant: str, is_signed: bool) -> List[str]:
    """
    BackSide için 6 seviye expected core name üret.
    
    Args:
        player_name: Oyuncu adı (Örn: "Wilfred Ndidi")
        series_name: Seri adı (Örn: "Sezon Kartları")
        group: Grup adı (Örn: "Newcomers", boş olabilir)
        determinant: Determinant (Örn: "1", "5", "base")
        is_signed: İmzalı mı?
    
    Returns:
        6 seviye expected string listesi
    """
    # Normalize et
    player_norm = normalize_token(player_name) if player_name else ""
    series_norm = normalize_token(series_name) if series_name else ""
    group_norm = normalize_token(group) if group else ""
    det_norm = normalize_token(determinant) if determinant else ""
    
    # İmzalı suffix
    s_suffix = "_s" if is_signed else ""
    
    levels = []
    
    # Seviye 1: Oyuncu + Seri + Grup + Det (en spesifik)
    if player_norm and series_norm and group_norm and det_norm:
        level1 = f"{player_norm}_{series_norm}_{group_norm}{s_suffix}_{det_norm}"
        levels.append(level1)
    else:
        levels.append("")
    
    # Seviye 2: Oyuncu + Seri + Grup (Det YOK) ← YENİ VE KRİTİK!
    if player_norm and series_norm and group_norm:
        level2 = f"{player_norm}_{series_norm}_{group_norm}{s_suffix}"
        levels.append(level2)
    else:
        levels.append("")
    
    # Seviye 3: Seri + Grup + Det
    if series_norm and group_norm and det_norm:
        level3 = f"{series_norm}_{group_norm}{s_suffix}_{det_norm}"
        levels.append(level3)
    else:
        levels.append("")
    
    # Seviye 4: Seri + Grup (Det yok)
    if series_norm and group_norm:
        level4 = f"{series_norm}_{group_norm}{s_suffix}"
        levels.append(level4)
    else:
        levels.append("")
    
    # Seviye 5: Seri + Det (Grup yok)
    if series_norm and det_norm:
        level5 = f"{series_norm}{s_suffix}_{det_norm}"
        levels.append(level5)
    else:
        levels.append("")
    
    # Seviye 6: Seri (en genel)
    if series_norm:
        level6 = f"{series_norm}{s_suffix}"
        levels.append(level6)
    else:
        levels.append("")
    
    return levels


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


def parse_back_image_filename(filename: str) -> Tuple[str, bool]:
    """
    BackSide görsel dosya adını parse et.
    
    Returns:
        (core_name, has_s_marker) tuple
        
    Örnekler:
        arka_xxx_s_5.jpg     → (xxx_s_5, True)
        arka_xxx_5.jpg       → (xxx_5, False)
        arka_xxx_s.jpg       → (xxx_s, True)
        arka_xxx.jpg         → (xxx, False)
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
    
    return (core_name_raw, has_s)


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
        
        # FrontSide indexes - Sondaki sayı kaldırılmış versiyonlar (Text determinant için)
        self.front_map_no_trailing: Dict[str, str] = {}
        
        # BackSide indexes - 2 MAP (İmzalı/İmzalısız)
        self.back_map_signed: Dict[str, str] = {}
        self.back_map_unsigned: Dict[str, str] = {}
        
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
        self.front_map_no_trailing.clear()
        self.back_map_signed.clear()
        self.back_map_unsigned.clear()
        self.all_files.clear()
        
        image_dict = {}
        
        for ext in IMAGE_EXTENSIONS:
            for img_path in folder.rglob(f"*{ext}"):
                filename = img_path.name
                self.all_files.append(filename)
                
                # Parse et
                core_full, variant_full, is_back = parse_image_filename(filename, expected_variant=None)
                
                if is_back:
                    # BackSide için basit indexleme
                    back_core, has_s = parse_back_image_filename(filename)
                    
                    # İmzalı/İmzalısız ayrımı
                    if has_s:
                        self.back_map_signed[back_core] = filename
                    else:
                        self.back_map_unsigned[back_core] = filename
                else:
                    # FrontSide
                    core_text, variant_text, _ = parse_image_filename(filename, expected_variant="text")
                    self.front_map[core_full] = filename
                    self.front_map_text[core_text] = filename
                    
                    # Text determinant için: sondaki sayı kaldırılmış versiyon
                    core_no_trailing = remove_trailing_number(core_full)
                    self.front_map_no_trailing[core_no_trailing] = filename
                
                image_dict[core_full] = img_path
        
        self.logger.info(f"📂 Toplam: {len(self.all_files)} görsel indexlendi")
        self.logger.info(f"   ├─ Front: {len(self.front_map)}")
        self.logger.info(f"   ├─ Front (no trailing): {len(self.front_map_no_trailing)}")
        self.logger.info(f"   └─ Back: {len(self.back_map_signed) + len(self.back_map_unsigned)}")
        self.logger.info(f"      ├─ Signed: {len(self.back_map_signed)}")
        self.logger.info(f"      └─ Unsigned: {len(self.back_map_unsigned)}")
        
        return image_dict
    
    def _find_exact_match(self, expected_core: str, image_map: Dict[str, str]) -> Optional[str]:
        """Tam eşleşme ara."""
        return image_map.get(expected_core)
    
    def _find_fuzzy_match(self, expected_core: str, image_map: Dict[str, str], 
                          check_word_count: bool = True) -> Optional[str]:
        """
        Fuzzy eşleşme ara.
        
        Args:
            expected_core: Beklenen core name
            image_map: Görsel map'i
            check_word_count: True ise kelime sayısı aynı olmalı
        """
        expected_words = expected_core.split('_')
        
        best_match = None
        best_score = float('inf')
        
        for core_name, filename in image_map.items():
            file_words = core_name.split('_')
            
            # Kelime sayısı kontrolü (opsiyonel)
            if check_word_count and len(expected_words) != len(file_words):
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
            result.add_info(f"Front: {len(self.front_map)}, Back Signed: {len(self.back_map_signed)}, Back Unsigned: {len(self.back_map_unsigned)}")
        except Exception as e:
            result.add_error(f"Görsel klasörü tarama hatası: {e}")
            return df, result
        
        # DataFrame kopyası
        work_df = df.copy() if not dry_run else df
        
        # FrontSideImage ve BackSideImage sütunları yoksa ekle - STRING TİPİNDE!
        if 'FrontSideImage' not in work_df.columns:
            work_df['FrontSideImage'] = ""
        else:
            work_df['FrontSideImage'] = work_df['FrontSideImage'].astype(str).replace('nan', '')
            
        if 'BackSideImage' not in work_df.columns:
            work_df['BackSideImage'] = ""
        else:
            work_df['BackSideImage'] = work_df['BackSideImage'].astype(str).replace('nan', '')
        
        # BackSide için meta kolonlar var mı?
        has_meta_columns = all(col in df.columns for col in ['player_name', 'series_name', 'determinant'])
        
        if has_meta_columns:
            self.logger.info("✅ Meta kolonlar bulundu, 6 seviyeli BackSide sistemi kullanılacak")
        else:
            self.logger.warning("⚠️ Meta kolonlar bulunamadı, basit BackSide sistemi kullanılacak")
        
        # DEBUG: İlk birkaç back map içeriğini logla
        self.logger.info(f"🔍 DEBUG - Back Unsigned Map örnekleri (ilk 5):")
        for i, (k, v) in enumerate(list(self.back_map_unsigned.items())[:5]):
            self.logger.info(f"   {k} → {v}")
        
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
            
            # === FRONT SIDE ===
            # LinkUrlTR'den expected core name üret
            expected_core = generate_expected_from_link_url_tr(str(link_url_tr))
            
            # Determinant tipi kontrol (sayısal mı text mi)
            is_numeric = is_numeric_determinant(expected_core)
            
            # DEBUG: İlk birkaç satır için logla
            if row_num <= 3:
                self.logger.info(f"🔍 DEBUG FrontSide Satır {row_num}:")
                self.logger.info(f"   LinkUrlTR: {link_url_tr}")
                self.logger.info(f"   Expected: {expected_core}")
                self.logger.info(f"   is_numeric: {is_numeric}")
            
            front_match = None
            match_type_front = "not_found"
            
            if is_numeric:
                # SAYISAL DETERMINANT: Normal eşleştirme (sayı önemli)
                front_match = self._find_exact_match(expected_core, self.front_map)
                match_type_front = "exact"
                
                if not front_match:
                    front_match = self._find_fuzzy_match(expected_core, self.front_map)
                    match_type_front = "fuzzy" if front_match else "not_found"
            else:
                # TEXT DETERMINANT: Sondaki sayıyı yoksay
                # Önce normal dene
                front_match = self._find_exact_match(expected_core, self.front_map)
                match_type_front = "exact"
                
                if not front_match:
                    # Sondaki sayı kaldırılmış map'te ara
                    front_match = self._find_exact_match(expected_core, self.front_map_no_trailing)
                    match_type_front = "exact_no_trailing" if front_match else "not_found"
                
                if not front_match:
                    # Fuzzy dene (sondaki sayı kaldırılmış map'te)
                    front_match = self._find_fuzzy_match(expected_core, self.front_map_no_trailing)
                    match_type_front = "fuzzy_no_trailing" if front_match else "not_found"
            
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
            # İmzalı kontrolü (LinkUrlTR'den)
            expected_is_signed = "_s_" in expected_core or expected_core.endswith("_s") or "imzali" in str(link_url_tr).lower()
            
            # Doğru map'i seç
            back_map_to_use = self.back_map_signed if expected_is_signed else self.back_map_unsigned
            
            back_match = None
            match_type_back = "not_found"
            
            if has_meta_columns:
                # YENİ SİSTEM: 6 seviyeli eşleştirme
                player_name = str(row.get('player_name', '')) if pd.notna(row.get('player_name')) else ""
                series_name = str(row.get('series_name', '')) if pd.notna(row.get('series_name')) else ""
                group = str(row.get('group', '')) if pd.notna(row.get('group')) else ""
                determinant = str(row.get('determinant', '')) if pd.notna(row.get('determinant')) else ""
                
                # 6 seviye expected üret
                levels = generate_back_expected_levels(player_name, series_name, group, determinant, expected_is_signed)
                
                # DEBUG: İlk satır için seviyeleri logla
                if row_num <= 3:
                    self.logger.info(f"🔍 DEBUG BackSide Satır {row_num}:")
                    self.logger.info(f"   Player: {player_name}, Series: {series_name}, Group: {group}, Det: {determinant}")
                    self.logger.info(f"   is_signed: {expected_is_signed}")
                    for i, lvl in enumerate(levels, 1):
                        self.logger.info(f"   L{i}: {lvl}")
                
                # 6 Seviyeli arama (Exact + Fuzzy)
                for level_idx, level_expected in enumerate(levels, 1):
                    if not level_expected:
                        continue
                    
                    # Exact match dene
                    back_match = self._find_exact_match(level_expected, back_map_to_use)
                    if back_match:
                        match_type_back = f"exact_L{level_idx}"
                        break
                    
                    # Fuzzy match dene
                    back_match = self._find_fuzzy_match(level_expected, back_map_to_use)
                    if back_match:
                        match_type_back = f"fuzzy_L{level_idx}"
                        break
            else:
                # ESKİ SİSTEM: Basit eşleştirme (fallback)
                # Sadece exact + fuzzy (tek seviye)
                back_match = self._find_exact_match(expected_core, back_map_to_use)
                if back_match:
                    match_type_back = "exact"
                else:
                    back_match = self._find_fuzzy_match(expected_core, back_map_to_use)
                    if back_match:
                        match_type_back = "fuzzy"
            
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
    
# ============================================================================
# DATE PREFIX UTILITIES
# ============================================================================

def add_date_prefix_to_files(folder_path: str) -> Dict[str, any]:
    """
    Klasördeki tarihsiz görsellere YYYYMMDD_ prefix'i ekler.
    
    Args:
        folder_path: Görsel klasörü yolu
        
    Returns:
        {
            'renamed': int,
            'skipped': int,
            'conflicts': List[str],
            'errors': List[str]
        }
    """
    from datetime import datetime
    
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        return {'renamed': 0, 'skipped': 0, 'conflicts': [], 'errors': [f"Klasör bulunamadı: {folder_path}"]}
    
    today_prefix = datetime.now().strftime('%Y%m%d') + '_'
    
    result = {
        'renamed': 0,
        'skipped': 0,
        'conflicts': [],
        'errors': []
    }
    
    for ext in IMAGE_EXTENSIONS:
        for img_path in folder.rglob(f"*{ext}"):
            filename = img_path.name
            
            # Zaten tarih var mı kontrol et (YYYYMMDD_ formatı)
            if DATE_PATTERN.match(filename):
                result['skipped'] += 1
                continue
            
            # Yeni isim oluştur
            new_filename = today_prefix + filename
            new_path = img_path.parent / new_filename
            
            # Çakışma kontrolü
            if new_path.exists():
                result['conflicts'].append(filename)
                continue
            
            # Rename yap
            try:
                img_path.rename(new_path)
                result['renamed'] += 1
            except Exception as e:
                result['errors'].append(f"{filename}: {str(e)}")
    
    return result