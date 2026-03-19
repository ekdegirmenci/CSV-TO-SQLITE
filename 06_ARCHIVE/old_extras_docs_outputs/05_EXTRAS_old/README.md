# 05_EXTRAS - Ek Kaynaklar & İleri Konular

**Bu klasör:** Converter'ın gelişmiş kullanımı, customization ve integration örnekleri içerir.

## 📚 İçerik Kategorileri

### **1️⃣ Veritabanı Analiz Araçları**

#### **database_analysis.py**
SQLite veritabanını analiz eden Python scripti.

**Kullanım:**
```powershell
python database_analysis.py path/to/database.db
```

**Çıktı:**
- Tüm tabloları listeler
- Kolon özeti
- Row count'ları
- Data type'ları
- NULL değer istatistikleri

---

#### **db_explorer.html**
SQL sorgularını çalıştırmak için interaktif web arayüzü.

**Açmak:**
```
1. Dosyayı web tarayıcında aç
2. Database path'ini gir
3. SQL sorgusu yaz
4. "Execute" butonuna tıkla
5. Sonuçları gör
```

**Özellikleri:**
- ✅ Join/Query desteği
- ✅ Export to CSV
- ✅ Query history
- ✅ Auto-complete

---

### **2️⃣ Excel/CSV İşleme Scriptleri**

#### **csv_column_analyzer.py**
CSV kolonları önceden analiz et, sorunları bul.

**Kullanım:**
```powershell
python csv_column_analyzer.py data.csv
```

**Bulur:**
- Boş kolonlar
- Yükü az kolonlar
- Tutarsız data types
- Encoding sorunları
- Öneriler

---

#### **merge_multiple_csvs.py**
Birden fazla CSV'yi birleştir.

**Kullanım:**
```powershell
python merge_multiple_csvs.py --input folder/ --output merged.csv
```

**Özellikler:**
- Otomatik header alignment
- Duplicate row kaldırma
- Boş satır temizleme
- Before/after istatistik

---

#### **validate_csv_format.py**
CSV'nin converter'a hazır olup olmadığını kontrol et.

**Kullanım:**
```powershell
python validate_csv_format.py data.csv
```

**Kontrol eder:**
- Encoding ✓
- Header var mı?
- Veri tutarlılığı
- Satır sayısı
- Sütun alignment

---

### **3️⃣ İleri SQL Kaynakları**

#### **advanced_queries.sql**
Yaygın veri analizi sorguları kütüphanesi.

**İçerir:**
```sql
-- 1. Duplicate Records
SELECT COUNT(*), [column] FROM table
GROUP BY [column] HAVING COUNT(*) > 1

-- 2. NULL Pattern
SELECT * FROM table WHERE [column] IS NULL

-- 3. Data Quality Score
SELECT (non_null_count / total_count) * 100 AS quality_pct

-- ... ve çok daha fazla
```

**Kullanım:**
1. db_explorer.html'i aç
2. advanced_queries.sql'den sorgu kopyala
3. Yapıştır ve çalıştır

---

#### **performance_tuning.sql**
Büyük veritabanlar için index ve optimization.

**Öneriler:**
- Primary key index stratejisi
- Foreign key index'leri
- Query optimization tipsler
- VACUUM vs ANALYZE

---

### **4️⃣ Customization Örnekleri**

#### **custom_transformations.py**
Converter'ı özelleştirmek için Python template'i.

**Örnek transformations:**
```python
def cleanup_phone_numbers(data):
    # +1-555-1234 → 5551234
    
def standardize_dates(data):
    # 3/15/2024 → 2024-03-15
    
def remove_special_chars(data):
    # Ö → O, ç → c
```

**Nasıl kullanılır:**
1. Kendi transformation fonksiyonlarını ekle
2. Converter'a integrate et
3. Kendi custom pipeline'ını oluştur

---

#### **batch_conversion_template.py**
Birden fazla CSV'yi otomatik olarak konvert et.

**Örnek:**
```powershell
python batch_conversion_template.py --folder data/ --output-folder results/
```

**Özellikleri:**
- Klasör taraması
- Parallel processing
- Hata yönetimi
- Rapor oluşturma

---

### **5️⃣ Integration Örnekleri**

#### **excel_to_sqlite_direct.py**
Excel dosyasını doğrudan SQLite'ye yükle (CSV aşamasını atla).

**Kullanım:**
```powershell
python excel_to_sqlite_direct.py data.xlsx output.db
```

**Avantajı:**
- ✅ Formülleri korur
- ✅ Multiple sheets support
- ✅ Daha hızlı

---

#### **sqlite_to_powerbi_export.py**
SQLite'den PowerBI-ready format exporte et.

**Çıktılar:**
- `tables.csv` (normalized)
- `relationships.json` (for model)
- `metadata.yaml` (descriptions)

**Kullanım:**
```powershell
python sqlite_to_powerbi_export.py database.db
```

---

### **6️⃣ Monitoring & Reporting**

#### **conversion_monitoring.py**
Gerçek zamanlı dönüştürme durumunu izle.

**Gösterir:**
- Processed rows
- Current speed (rows/sec)
- Estimated time remaining
- Error counter

---

#### **generate_conversion_report.py**
Dönüştürmeden sonra detaylı rapor.

**Rapor içeriği:**
```
=== CONVERSION REPORT ===
Source CSV: data.csv
Target DB: data.db

📊 STATISTICS
├── Total Rows: 1,234,567
├── Processing Time: 45 seconds
├── Speed: 27,000 rows/sec
└── Status: ✅ SUCCESS

🔍 DATA QUALITY
├── Nulls Detected: 1,234 (0.1%)
├── Duplicates: 45
├── Data Type Mismatches: 0
└── Quality Score: 99.8%

⚠️  WARNINGS
(None)

✅ SUCCESS
```

---

### **7️⃣ Troubleshooting Araçları**

#### **diagnose_csv_issues.py**
CSV problemlerini otomatik olarak teşhis et.

**Bulur:**
- Encoding issues
- Line ending problems
- Quote escaping errors
- Character encoding mismatches

**Kullanım:**
```powershell
python diagnose_csv_issues.py data.csv
```

---

#### **test_sqlite_integrity.py**
Oluşturulan SQLite veritabanının bütünlüğünü kontrol et.

**Kontrol eder:**
- Tüm tabloların var olması
- Foreign keys
- Veri yüklemesinin başarılı olması
- Index'lerin doğru çalışması

---

## 📊 Hızlı Referans

### Yaygın Görevler

| Görev | Dosya | Komut |
|-------|-------|-------|
| CSV analiz et | `csv_column_analyzer.py` | `python csv_column_analyzer.py data.csv` |
| Multiple CSV'ler birleştir | `merge_multiple_csvs.py` | `python merge_multiple_csvs.py --input folder/` |
| DB analiz et | `database_analysis.py` | `python database_analysis.py db.sqlite` |
| DB'yi tamamen explore et | `db_explorer.html` | Tarayıcıda aç |
| Excel → SQLite direkt | `excel_to_sqlite_direct.py` | `python excel_to_sqlite_direct.py data.xlsx db.sqlite` |
| Rapor oluştur | `generate_conversion_report.py` | `python generate_conversion_report.py db.sqlite` |

---

## 🎯 İse Yarar Örnekler

### **Scenario 1: 50 dosyayı birleştir ve dönüştür**
```powershell
# 1. Tüm CSV'leri birleştir
python merge_multiple_csvs.py --input data/folder/ --output merged.csv

# 2. Kontrol et
python validate_csv_format.py merged.csv

# 3. Konvert et
python ../01_PRODUCTION/CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py merged.csv merged.db

# 4. Analiz et
python database_analysis.py merged.db
```

### **Scenario 2: Excel dosyalarını doğrudan SQLite'ye**
```powershell
# Excel → SQLite (tek adım, CSV'yi bir çarpar)
python excel_to_sqlite_direct.py sales_data.xlsx sales.db

# PowerBI'a hazırla
python sqlite_to_powerbi_export.py sales.db
```

### **Scenario 3: İleri data cleaning**
```powershell
# 1. Sorunları teşhis et
python diagnose_csv_issues.py data.csv

# 2. Özel transformations uygula
python custom_transformations.py data.csv output.csv

# 3. Kontrol et
python validate_csv_format.py output.csv

# 4. Konvert et
python ../01_PRODUCTION/CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py output.csv output.db
```

---

## 🔧 Customization İçin

**custom_transformations.py** dosyasını kopyala ve kendi transformationlarını ekle:

```python
# custom_my_data.py dosyası

from custom_transformations import BaseTransformer

class MyDataTransformer(BaseTransformer):
    def transform_phone(self, phone):
        # Kendi logic'in
        return phone.replace("-", "").replace("(", "k")
    
    def transform_date(self, date_str):
        # Tarih format'ını değiştir
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")

# Kullan
transformer = MyDataTransformer()
transformer.apply("data.csv", "output.csv")
```

---

## 📚 Hangi Dosya Ne Zaman?

```
CSV hazirligi
├─ Sorun teşhis et? → diagnose_csv_issues.py
├─ Format kontrol? → validate_csv_format.py
├─ Birleştir? → merge_multiple_csvs.py
└─ Analiz et? → csv_column_analyzer.py

Dönüştürme sonrası
├─ DB analiz et? → database_analysis.py
├─ Sorgu çalıştır? → db_explorer.html
├─ DB integrity? → test_sqlite_integrity.py
└─ Rapor oluştur? → generate_conversion_report.py

İleri işlemler
├─ PowerBI'a çıkar? → sqlite_to_powerbi_export.py
├─ Batch dönüştür? → batch_conversion_template.py
└─ Custom logic? → custom_transformations.py
```

---

## 🚀 QuickStart (En Sık Kullanılanlar)

```powershell
# 1. Önce kontrol et
python csv_column_analyzer.py data.csv

# 2. Birleştir (gerekirse)
python merge_multiple_csvs.py --input folder/ --output merged.csv

# 3. Konvert et
python ../01_PRODUCTION/CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py merged.csv output.db

# 4. Sonuçları gör
python database_analysis.py output.db

# 5. (Optional) PowerBI'a hazırla
python sqlite_to_powerbi_export.py output.db
```

---

## 📖 Diğer Dosyalar

- Ana Converter: `../01_PRODUCTION/CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py`
- Testler: `../02_TESTING/TEST_SUITE.py`
- Dağıtım: `../04_DEPLOYMENT/`

---

**Status:** ✅ Tüm araçlar çalışıyor | **Python Version:** 3.8+ | **Dependencies:** pandas, openpyxl (optional)
