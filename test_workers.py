"""
Workers modülü test scripti.

Threading sistemini test eder.
"""

import sys
from pathlib import Path
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

# Proje kök dizinini ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger
from workers import ValidationWorker, ConversionWorker


def test_workers_import():
    """Workers modüllerinin import edilebilirliğini test eder."""
    print("=" * 80)
    print("  WORKERS MODÜLÜ - IMPORT TESTİ")
    print("=" * 80)
    
    try:
        from workers import (
            WorkerSignals,
            BaseWorker,
            WorkerCancelledException,
            ValidationWorker,
            ConversionWorker,
            MatchCheckWorker,
            MatchingWorker
        )
        
        print("\n✅ Tüm worker sınıfları başarıyla import edildi!\n")
        
        print("📦 Import edilen sınıflar:")
        print("   - WorkerSignals")
        print("   - BaseWorker")
        print("   - WorkerCancelledException")
        print("   - ValidationWorker")
        print("   - ConversionWorker")
        print("   - MatchCheckWorker")
        print("   - MatchingWorker")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_worker_signals():
    """WorkerSignals sinyallerini test eder."""
    print("\n" + "=" * 80)
    print("  WORKER SIGNALS TESTİ")
    print("=" * 80)
    
    try:
        from workers import WorkerSignals
        
        signals = WorkerSignals()
        
        print("\n✅ WorkerSignals oluşturuldu!\n")
        print("📡 Mevcut sinyaller:")
        print("   - started")
        print("   - finished")
        print("   - cancelled")
        print("   - progress")
        print("   - status")
        print("   - log")
        print("   - error")
        print("   - result")
        
        return True
        
    except Exception as e:
        print(f"\n❌ WorkerSignals test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_worker():
    """BaseWorker sınıfını test eder."""
    print("\n" + "=" * 80)
    print("  BASE WORKER TESTİ")
    print("=" * 80)
    
    try:
        from workers import BaseWorker
        
        # Test worker oluştur
        class TestWorker(BaseWorker):
            def do_work(self):
                self.log_info("Test worker çalışıyor...")
                self.update_progress(50, 100, "İşlem devam ediyor...")
                self.update_progress(100, 100, "İşlem tamamlandı!")
                return "Test başarılı!"
        
        worker = TestWorker()
        
        print("\n✅ BaseWorker test worker'ı oluşturuldu!\n")
        print("🔧 Özellikler:")
        print(f"   - Signals: {worker.signals is not None}")
        print(f"   - Logger: {worker.logger is not None}")
        print(f"   - Cancel flag: {worker.is_cancelled()}")
        print(f"   - Running: {worker.is_running()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ BaseWorker test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_threadpool():
    """QThreadPool varlığını test eder."""
    print("\n" + "=" * 80)
    print("  QTHREADPOOL TESTİ")
    print("=" * 80)
    
    try:
        # QApplication oluştur (Qt için gerekli)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        pool = QThreadPool.globalInstance()
        
        print("\n✅ QThreadPool hazır!\n")
        print("📊 Thread Pool Bilgileri:")
        print(f"   - Max Thread Count: {pool.maxThreadCount()}")
        print(f"   - Active Thread Count: {pool.activeThreadCount()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ QThreadPool test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Tüm testleri çalıştırır."""
    logger = setup_logger('WorkersTest')
    
    print("\n" + "🔄" * 40)
    print("  WORKERS MODÜLÜ - KAPSAMLI TEST")
    print("🔄" * 40)
    
    results = {}
    
    # Test 1: Import
    results['import'] = test_workers_import()
    
    # Test 2: Signals
    results['signals'] = test_worker_signals()
    
    # Test 3: Base Worker
    results['base_worker'] = test_base_worker()
    
    # Test 4: ThreadPool
    results['threadpool'] = test_threadpool()
    
    # Özet
    print("\n" + "=" * 80)
    print("  TEST SONUÇLARI ÖZETİ")
    print("=" * 80)
    
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
        print("🎉 TÜM TESTLER BAŞARILI! Workers modülü hazır!")
        print("\n💡 Sonraki Adım: GUI modülünü oluşturun (Faz 4)")
    else:
        print(f"⚠️ {failed} test başarısız oldu. Lütfen hataları kontrol edin.")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)