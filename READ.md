# 🎯 Mythos Cards QR Generator

Mythos Cards ürün verilerini otomatik olarak Excel formatına dönüştüren ve görsellerle eşleştiren masaüstü uygulaması.

## 🚀 Kurulum

### Gereksinimler
- Python 3.10 veya üstü
- pip

### Bağımlılıkları Yükleme
```bash
pip install -r requirements.txt
```

## 📦 Bağımlılıklar

- **PySide6**: GUI framework
- **pandas**: Excel veri işleme
- **openpyxl**: Excel okuma/yazma
- **python-Levenshtein**: Fuzzy string matching
- **Unidecode**: Karakter normalizasyonu

## 🏃 Çalıştırma
```bash
python main.py
```

## 📁 Proje Yapısı
```
mythos_qr_generator/
├── main.py                 # Giriş noktası
├── config/                 # Ayarlar ve konfigürasyon
├── models/                 # Veri modelleri
├── core/                   # İş mantığı
├── workers/                # Arka plan işlemleri
├── gui/                    # Kullanıcı arayüzü
├── utils/                  # Yardımcı fonksiyonlar
└── tests/                  # Test dosyaları
```

## 📝 Özellikler

✅ Excel veri dönüştürme ve doğrulama
✅ Fuzzy görsel eşleştirme (Levenshtein ≤ 2)
✅ Gerçek zamanlı loglama ve filtreleme
✅ Otomatik yedekleme sistemi
✅ İptal edilebilir işlemler
✅ Türkçe karakter desteği

## 👨‍💻 Geliştirici

**Furkan Gümüş**

## 📄 Versiyon

1.0.0