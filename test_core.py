"""
Mythos QR Generator - Kapsamlı Test Scripti

Core logic modüllerinin tamamını test eder.
"""

import sys
from pathlib import Path
import pandas as pd

# Proje kök dizinini ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger
from core.normalizer import Normalizer
from core.data_validator import DataValidator
from core.data_converter import DataConverter
from core.backup_manager import BackupManager
from config.config_manager import ConfigManager
from utils.file_handler import FileHandler


def print_separator(title: str):
    """Test bölümü başlığı yazdır."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_normalizer():
    """Normalizer modülünü test eder."""
    print_separator("TEST 1: NORMALIZER")
    
    test_cases = [
        ("Galatasaray vs Liverpool", "galatasaray-vs-liverpool"),
        ("Arda_Güler_Base", "arda-guler-base"),
        ("Şampiyonlar_Ligi_2024", "sampiyonlar-ligi"),
        ("İstanbul_Başakşehir_/25", "istanbul-basaksehir-25"),
        ("Çağlar_Söyüncü_Short_Print", "caglar-soyuncu-short-print"),
    ]
    
    print("\n🧪 Normalizer Test Senaryoları:\n")
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = Normalizer.normalize(input_text)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Input: '{input_text}'")
        print(f"   Expected: '{expected}'")
        print(f"   Got:      '{result}'")
        print()
    
    print(f"\n📊 Sonuç: {passed} başarılı, {failed} başarısız")
    return failed == 0


def create_sample_excel():
    """Örnek test Excel dosyası oluşturur."""
    print_separator("TEST 2: ÖRNEK EXCEL OLUŞTURMA")
    
    data = {
        'Seri Adı': [
            'Galatasaray vs Liverpool',
            'Galatasaray vs Liverpool',
            'Galatasaray vs Liverpool',
            'Beşiktaş vs Fenerbahçe',
            'Beşiktaş vs Fenerbahçe',
        ],
        'Grup': [
            'UEFA Champions League',
            'UEFA Champions League',
            'UEFA Champions League',
            'Süper Lig',
            'Süper Lig',
        ],
        'Oyuncu Adı': [
            'Mauro Icardi',
            'Fernando Muslera',
            'Kerem Aktürkoğlu',
            'Cenk Tosun',
            'İrfan Can Kahveci',
        ],
        'Base': [
            'Base',
            '',
            'Base',
            'Base',
            '',
        ],
        'Short Print': [
            '',
            'Short Print',
            '',
            '',
            'Short Print',
        ],
        '/25': [
            '',
            '',
            '/25',
            '',
            '/25',
        ]
    }
    df = pd.DataFrame(data)
    
    # Test klasörünü oluştur
    test_dir = project_root / 'test_data'
    test_dir.mkdir(exist_ok=True)
    
    excel_path = test_dir / 'sample_input.xlsx'
    df.to_excel(excel_path, index=False)
    
    print(f"\n✅ Örnek Excel oluşturuldu: {excel_path}")
    print(f"📊 {len(df)} satır, {len(df.columns)} kolon")
    print("\n📋 Veri Önizlemesi:")
    print(df.to_string(index=False))
    
    return excel_path


def test_validator(excel_path: Path):
    """DataValidator modülünü test eder."""
    print_separator("TEST 3: DATA VALIDATOR")
    
    validator = DataValidator()
    file_handler = FileHandler()
    
    print("\n📂 Excel dosyası okunuyor...")
    df = file_handler.read_excel(str(excel_path))
    
    print("\n🔍 Doğrulama yapılıyor...")
    result = validator.validate(df)
    
    print(f"\n📊 Doğrulama Sonucu:")
    print(f"   Geçerli mi: {'✅ EVET' if result.is_valid else '❌ HAYIR'}")
    print(f"   Toplam Satır: {result.row_count}")
    print(f"   Hata Sayısı: {len(result.errors)}")
    print(f"   Uyarı Sayısı: {len(result.warnings)}")
    print(f"   Boş Determinant: {result.empty_determinants}")
    
    if result.errors:
        print("\n❌ Hatalar:")
        for error in result.errors:
            print(f"   - {error['message']}")
    
    if result.warnings:
        print("\n⚠️ Uyarılar:")
        for warning in result.warnings:
            print(f"   - {warning['message']}")
    
    if result.info:
        print("\n📋 Bilgiler:")
        for info in result.info:
            print(f"   - {info['message']}")
    
    print(f"\n📝 Özet: {result.summary}")
    
    return result.is_valid, df


def test_converter(df: pd.DataFrame):
    """DataConverter modülünü test eder."""
    print_separator("TEST 4: DATA CONVERTER")
    
    converter = DataConverter(year=2025)
    
    print("\n🔄 Dönüştürme yapılıyor...")
    
    try:
        output_df = converter.convert(df)
        
        print(f"\n✅ Dönüştürme başarılı!")
        print(f"📊 Input: {len(df)} satır → Output: {len(output_df)} satır")
        
        print("\n📋 Output Kolonları:")
        for col in output_df.columns:
            print(f"   - {col}")
        
        print("\n📄 İlk 3 Satır Önizlemesi:")
        print(output_df.head(3).to_string(index=False))
        
        # Test klasörüne kaydet
        test_dir = project_root / 'test_data'
        output_path = test_dir / 'sample_output.xlsx'
        
        file_handler = FileHandler()
        file_handler.write_excel(output_df, str(output_path))
        
        print(f"\n💾 Output kaydedildi: {output_path}")
        
        return True, output_df, output_path
        
    except Exception as e:
        print(f"\n❌ Dönüştürme hatası: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_backup_manager(source_file: Path):
    """BackupManager modülünü test eder."""
    print_separator("TEST 5: BACKUP MANAGER")
    
    backup_mgr = BackupManager()
    
    print("\n💾 Backup oluşturuluyor...")
    
    backup_path = backup_mgr.create_backup(
        source_file,
        series_name="galatasaray-vs-liverpool",
        group="uefa-champions-league"
    )
    
    if backup_path:
        print(f"✅ Backup başarılı: {backup_path}")
        
        # Backup bilgilerini göster
        info = backup_mgr.get_backup_info()
        print(f"\n📊 Backup Klasörü Bilgileri:")
        print(f"   Toplam Backup: {info['total_backups']}")
        print(f"   Toplam Boyut: {info['total_size_mb']} MB")
        if info['newest']:
            print(f"   En Yeni: {info['newest'].name}")
        
        return True
    else:
        print("❌ Backup oluşturulamadı!")
        return False


def test_config_manager():
    """ConfigManager modülünü test eder."""
    print_separator("TEST 6: CONFIG MANAGER")
    
    config = ConfigManager()
    
    print("\n⚙️ Config Test:")
    print(f"   Config Dosyası: {config.config_file}")
    print(f"   Varsayılan Yıl: {config.get_default_year()}")
    print(f"   Tema: {config.get_theme()}")
    
    # Test değeri kaydet
    config.set_last_input_path("C:/test/input.xlsx")
    saved_path = config.get_last_input_path()
    
    if saved_path == "C:/test/input.xlsx":
        print(f"\n✅ Config okuma/yazma çalışıyor!")
        return True
    else:
        print(f"\n❌ Config okuma/yazma hatası!")
        return False


def run_all_tests():
    """Tüm testleri çalıştırır."""
    logger = setup_logger('MythosQR_Test')
    
    print("\n" + "🚀" * 40)
    print("  MYTHOS CARDS QR GENERATOR - KAPSAMLI TEST")
    print("🚀" * 40)
    
    results = {}
    
    # Test 1: Normalizer
    results['normalizer'] = test_normalizer()
    
    # Test 2 & 3: Excel oluştur ve validate et
    excel_path = create_sample_excel()
    results['validator'], df = test_validator(excel_path)
    
    # Test 4: Converter
    if df is not None:
        results['converter'], output_df, output_path = test_converter(df)
        
        # Test 5: Backup Manager
        if output_path:
            results['backup'] = test_backup_manager(output_path)
        else:
            results['backup'] = False
    else:
        results['converter'] = False
        results['backup'] = False
    
    # Test 6: Config Manager
    results['config'] = test_config_manager()
    
    # Özet
    print_separator("TEST SONUÇLARI ÖZETİ")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n📊 Genel Sonuç:\n")
    for test_name, result in results.items():
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"   {test_name.upper():20} : {status}")
    
    print(f"\n{'=' * 80}")
    print(f"  TOPLAM: {passed}/{total} test başarılı")
    print(f"{'=' * 80}\n")
    
    if failed == 0:
        print("🎉 TÜM TESTLER BAŞARILI! Core Logic %100 çalışıyor!")
    else:
        print(f"⚠️ {failed} test başarısız oldu. Lütfen hataları kontrol edin.")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)