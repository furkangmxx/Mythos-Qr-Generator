"""
Uygulama genelinde kullanılacak sabit değerler ve ayarlar.
"""
from pathlib import Path
from datetime import datetime

# =============================================================================
# UYGULAMA BİLGİLERİ
# =============================================================================
APP_NAME = "Mythos Cards QR Generator"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Furkan Gümüş"

# =============================================================================
# KLASÖR AYARLARI
# =============================================================================
# Ana çalışma klasörü: Documents/Mythos Cards QR/
BASE_DIR = Path.home() / "Documents" / "Mythos Cards QR"
BACKUP_DIR = BASE_DIR / "Backup"
LOG_DIR = BASE_DIR / "app-logs"
CONFIG_FILE = BASE_DIR / "config.json"

# =============================================================================
# DOSYA İSİMLENDİRME
# =============================================================================
OUTPUT_FILE_PATTERN = "{year}_{series}_{group}_QR.xlsx"
OUTPUT_FILE_PATTERN_NO_GROUP = "{year}_{series}_QR.xlsx"
BACKUP_FILE_PATTERN = "{date}_{series}_{group}_QR_Backup.xlsx"
BACKUP_FILE_PATTERN_NO_GROUP = "{date}_{series}_QR_Backup.xlsx"

# Tarih formatı (20251023)
DATE_FORMAT = "%Y%m%d"
# Tarih-saat formatı (20251023-1515)
DATETIME_FORMAT = "%Y%m%d-%H%M"

# =============================================================================
# EXCEL KOLON İSİMLERİ
# =============================================================================
# Input Excel'de aranacak kolonlar
INPUT_COLUMNS = {
    'SERIES_NAME': 'Seri Adı',
    'GROUP': 'Grup',
    'PLAYER_NAME': 'Oyuncu Adı',
}

# Determinant kolonları (Base, Short Print, X, vb.)
DETERMINANT_KEYWORDS = ['Base', 'Short Print', 'X', 'Astim', 'Isto', '/']

# Output Excel kolonları
OUTPUT_COLUMNS = [
    'No',
    'Name',
    'Description',
    'CustomProductName',
    'ProductInformation',
    'CardPrintingYear',
    'LinkUrlTR',
    'FrontSideImage',
    'BackSideImage',
    'Price',
    'Stock',
    'player_name',      # BackSide eşleştirme için (Part 2)
    'series_name',      # BackSide eşleştirme için (Part 2)
    'group',            # BackSide eşleştirme için (Part 2)
    'determinant'       # BackSide eşleştirme için (Part 2)
]

# Sabit değerler
PRODUCT_INFORMATION_TEXT = "6.4 / 8.9 cm ebatlarında özel baskılı koleksiyon kartı"
DEFAULT_PRICE = 0

# =============================================================================
# GÖRSEL EŞLEŞTİRME KURALLARI
# =============================================================================
# Görsel dosya uzantıları
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Özel işaretleyiciler
IMAGE_BACK_MARKER = '_arka_'      # Arka yüz görseli
IMAGE_SIGNED_MARKER = '_s_'       # İmzalı (eşleştirmede yok sayılır)

# Fuzzy matching toleransı (Levenshtein distance)
FUZZY_TOLERANCE = 2

# =============================================================================
# LOG SİSTEMİ
# =============================================================================
# Log seviyeleri
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_SYSTEM = "SYSTEM"

# Log renkleri (hex)
LOG_COLORS = {
    LOG_LEVEL_INFO: "#28a745",      # Yeşil
    LOG_LEVEL_WARNING: "#ffc107",   # Turuncu
    LOG_LEVEL_ERROR: "#dc3545",     # Kırmızı
    LOG_LEVEL_SYSTEM: "#007bff"     # Mavi
}

# Log dosya boyutu limiti (MB)
LOG_FILE_MAX_SIZE = 10

# =============================================================================
# GUI AYARLARI
# =============================================================================
# Ana pencere boyutları
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700

# Durum rozet metinleri
STATUS_READY = "Hazır"
STATUS_VALIDATING = "Doğrulanıyor..."
STATUS_CONVERTING = "Dönüştürülüyor..."
STATUS_COMPLETED = "Tamamlandı"
STATUS_FAILED = "Başarısız"
STATUS_CANCELLED = "İptal Edildi"

# Progress bar
PROGRESS_UPDATE_INTERVAL = 100  # Her 100 satırda bir güncelle

# =============================================================================
# PERFORMANS AYARLARI
# =============================================================================
# Maksimum işlem süreleri (saniye)
MAX_CONVERSION_TIME = 30  # 10,000 satır için
MAX_IMAGE_SCAN_TIME = 10  # 100,000 görsel için

# Thread pool boyutu
MAX_THREAD_POOL_SIZE = 4

# =============================================================================
# NORMALİZASYON KURALLARI
# =============================================================================
# Türkçe karakter dönüşümleri
TURKISH_CHAR_MAP = {
    'ç': 'c', 'Ç': 'c',
    'ğ': 'g', 'Ğ': 'g',
    'ı': 'i', 'I': 'i', 'İ': 'i',
    'ö': 'o', 'Ö': 'o',
    'ş': 's', 'Ş': 's',
    'ü': 'u', 'Ü': 'u'
}

# Eşdeğer karakterler
EQUIVALENT_CHARS = {
    '_': '-',
    ' ': '-'
}

# Yok sayılacak kelimeler (tarihler vb.)
IGNORE_PATTERNS = [
    r'\d{4}',           # 4 haneli yıllar
    r'\d{2}-\d{2}',     # Tarih formatları
]

# =============================================================================
# VARSAYILAN DEGERLER
# =============================================================================
# Sistem yılı varsayılan olarak kullanılır
DEFAULT_YEAR = datetime.now().year

# Varsayılan config değerleri
DEFAULT_CONFIG = {
    'last_input_path': '',
    'last_output_path': '',
    'last_image_folder': '',
    'default_year': DEFAULT_YEAR,
    'theme': 'light'
}