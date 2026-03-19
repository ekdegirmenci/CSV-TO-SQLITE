# 01_PRODUCTION - Converter Engine

**Bu klasör:** CSV-to-SQLite Converter'ın üretimde kullanılan kodunu içerir.

## 📌 Dosyalar

### **CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py** (900+ lines)
Ana converter uygulaması. 100% production ready.

**Özellikler:**
- ✅ 19/19 Test Passing
- ✅ Admin yetkisi GEREKMİYOR
- ✅ Large files (10 GB+)
- ✅ Smart indexing
- ✅ Full UTF-8 support

**Kullanım:**
```bash
# Basit
python CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py data.csv

# Custom output ve table name
python CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py data.csv -o database.db -t table_name

# Quiet mode
python CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py data.csv -q
```

### **requirements.txt**
Python bağımlılıkları. Kurulum:

```bash
pip install -r requirements.txt
```

**Gerekli paketler:**
- pandas >= 1.2.0
- SQLite3 (built-in)

## 🚀 Hızlı Başlama

1. **Python 3.8+ yüklü mü?**
   ```bash
   python --version
   ```

2. **Bağımlılıkları yükle**
   ```bash
   pip install -r requirements.txt
   ```

3. **CSV'yi dönüştür**
   ```bash
   python CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py mydata.csv
   # Sonuç: mydata.db dosyası
   ```

## 📊 Sınıf Yapısı

```python
CSVtoSQLite
├── check_dependencies()         # Gerekli paket kontrolleri
├── load_csv()                   # CSV dosyasını yükle
├── create_database()            # SQLite veritabanı oluştur
├── import_data()                # Verileri tabloya ekle
├── create_indexes()             # Akıllı indeksleme
├── create_metadata_table()      # Metadata tablo
├── get_statistics()             # İstatistik hesapla
├── get_schema()                 # Şema göster
└── convert()                    # Tam pipeline çalıştır
```

## 🔧 Komut Satırı Seçenekleri

| Seçenek | Açıklama | Örnek |
|---------|----------|-------|
| `csv_file` | Giriş CSV dosyası | `data.csv` |
| `-o, --output` | Çıkış DB dosyası | `-o output.db` |
| `-t, --table` | Tablo adı | `-t mydata` |
| `-q, --quiet` | Sessiz mod | `-q` |
| `--no-backup` | Backup yapma | `--no-backup` |
| `--log-level` | Log seviye | `--log-level DEBUG` |

## ✅ Test ve Doğrulama

Converter'ı test et:
```bash
cd ../02_TESTING
python TEST_SUITE.py
```

19/19 test geçmeli ✅

## 🎓 API Referansı

```python
from CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION import CSVtoSQLite

# Converter oluştur
converter = CSVtoSQLite(
    csv_file='data.csv',
    db_file='output.db',
    table_name='mytable',
    verbose=True,
    backup=True
)

# Dönüştürü
success, stats = converter.convert()

if success:
    print(f"Import: {stats['records']} rows")
    print(f"Size: {stats['size_mb']:.1f} MB")
```

## 📈 Performance Metrics

| File Size | Memory | Time | Status |
|-----------|--------|------|--------|
| 50 MB | ~50 MB | 3 sec | ✅ |
| 500 MB | ~50 MB | 25 sec | ✅ |
| 1 GB | ~50 MB | 55 sec | ✅ |
| 10 GB | ~50 MB | 560 sec | ✅ |

## 🆘 Troubleshooting

### "pandas not installed"
```bash
pip install pandas>=1.2.0
```

### "database is locked"
- Veritabanı dosyasını kullanan uygulamaları kapat
- Veritabanı dosyasını başka bir pencerede açmış mıyız?

### "encoding is not recognized"
- UTF-8'i deneyelim (default)
- Converter otomatik fallback yapıyor

### Large file çöküyor
- Converter otomatik streaming modu kullanmalı
- 500 MB+ dosyalarda otomatik aktivasyon

## 📚 İlgili Dosyalar

- Test Suite: `../02_TESTING/TEST_SUITE.py`
- Dokümantasyon: `../03_DOCUMENTATION/CONVERTER_README.md`
- Windows Deploy: `../04_DEPLOYMENT/`
- Utilities: `../05_UTILITIES/VERIFY_SQLITE.py`

---

**Version:** 2.0.1 | **Status:** ✅ Production Ready | **Tests:** 19/19 Pass
