# 📋 CSV-to-SQLite Universal Converter - QA & Kontrol Listesi
**Tarih:** 18 Mart 2026  
**Hedef:** Admin yetkisi olmayan bilgisayarlarda güvenle çalışabilir, production-ready converter  

---

## 🎯 KONTROL KATEGORİLERİ

### 1️⃣ ADMIN YETKİ BAĞIMLILIĞI
- [ ] `os.remove()`, `os.makedirs()` fonksiyonları admin istiyor mu?
- [ ] SQLite database dosyası yazma izni gerektirimi?
- [ ] Path permissions — C:\Users\<user>\AppData vs C:\Program Files
- [ ] Registry access gerekirmi (SQLite için)?
- [ ] System environment variables bağımlılığı?
- [ ] DLL dependencies (libpq, msvcrt, vs) — tümü built-in mi?
- [ ] Antivirus/UAC bypass gerektirimi?

**✅ Düzeltme:** Tüm file operations için safe path handling eklenecek

---

### 2️⃣ PATH & FİLESYSTEM UYUMLULUGU
- [ ] Relative paths çalışıyor mu? (./data/input.csv)
- [ ] Absolute paths çalışıyor mu? (C:\Users\...\input.csv)
- [ ] Boşluk içeren paths düzgün handle ediliyor mu? (`C:\My Data Files\...`)
- [ ] UNC paths (\\server\share\file.csv) destekleniyor mu?
- [ ] Long filename support (>260 char on Windows)?
- [ ] Special characters in filename (–, –, _, vb)?
- [ ] Output directory yoksa create ediliyor mu?
- [ ] Existing output file'ı overwrite warning veriyor mu?
- [ ] Path traversal attacks blocked ('..\..\..)? 
- [ ] Symlinks/shortcuts düzgün resolve ediliyor mu?

**✅ Düzeltme:** Path validation + safe directory creation

---

### 3️⃣ ENCODING & KARAKTERLERİ
- [ ] UTF-8 Turkish chars (İ, ş, ğ, ü, ö, ç) test edildi?
- [ ] Latin-1 fallback çalışıyor mu?
- [ ] Windows-1254 (Turkish) encoding test edildi?
- [ ] BOM handling (UTF-8-sig)?
- [ ] Mixed encoding CSV'ler (some cols UTF-8, some Latin)?
- [ ] Output docs UTF-8 ile yazılıyor mu?
- [ ] Console output encoding (terminal)?
- [ ] Emoji/special Unicode karakterleri?
- [ ] NULL bytes in CSV?
- [ ] Encoding detection confidence score?

**✅ Düzeltme:** Encoding detection + charset_normalizer library

---

### 4️⃣ MEMORY & PERFORMANCE (Büyük Dosyalar)
- [ ] 100 MB+ CSV on 4GB RAM test edildi?
- [ ] chunksize parameter optimal mı (10000)?
- [ ] DataFrame memory usage — `df.memory_usage(deep=True)`?
- [ ] Disk I/O — batch write performance?
- [ ] Index creation memory spike?
- [ ] Metadata table — no memory issues?
- [ ] Progress bar — long-running tasks için (tqdm)?
- [ ] Garbage collection — `gc.collect()` needed?
- [ ] Pandas dtype optimization (int32 vs int64)?
- [ ] Streaming CSV read (not all in memory)?

**✅ Düzeltme:** chunksize + streaming read + memory profiling

---

### 5️⃣ ERROR HANDLING & EDGE CASES
- [ ] File not found — clear error message?
- [ ] CSV corrupted (bad row count) — handled?
- [ ] Out of disk space — caught + message?
- [ ] Permission denied on output — graceful failure?
- [ ] Locked database (another process using) — retry?
- [ ] NULL/NaN values in table name — rejected?
- [ ] Empty CSV (0 rows) — handled?
- [ ] CSV with no headers — handled?
- [ ] Duplicate column names — handled?
- [ ] Very long column names (>255 char)?
- [ ] NULL bytes in data — sanitized?
- [ ] Interrupt (Ctrl+C) — cleanup properly?
- [ ] Database corruption detection?

**✅ Düzeltme:** Try/except blocks + error context

---

### 6️⃣ SQL İNJEKSİYON & GÜVENLİK
- [ ] Table name validated (regex) ✅ DONE
- [ ] Column names sanitized?
- [ ] SQL commands parameterized (not f-strings)?
- [ ] CSV injection attacks blocked?
- [ ] Malicious column names — rejected?
- [ ] Input length limits?
- [ ] Special characters in data — escaped?
- [ ] PRAGMA commands validated?
- [ ] Database file permissions?
- [ ] Temp files cleaned up?

**✅ Düzeltme:** Column name validation + parameterized queries

---

### 7️⃣ SQLITE SPESİFİK
- [ ] Database file locked handling?
- [ ] WAL mode vs default — trade-offs?
- [ ] PRAGMA table_info — case sensitive?
- [ ] Index naming conflicts — prevented?
- [ ] AUTOINCREMENT — needed?
- [ ] Foreign keys — enforcement?
- [ ] Transaction handling?
- [ ] Rollback on error?
- [ ] VACUUM optimization?
- [ ] SQLite version check (>3.8)?
- [ ] Database size limits (2GB for older)?
- [ ] Corrupt database recovery?

**✅ Düzeltme:** Transaction safety + error recovery

---

### 8️⃣ CROSS-PLATFORM UYUMLULUK
- [ ] Windows PowerShell ✅
- [ ] Windows CMD (cmd.exe)?
- [ ] WSL2 (Linux on Windows)?
- [ ] Different Python versions (3.8, 3.9, 3.10, 3.11+)?
- [ ] Virtual environment (.venv) ✓
- [ ] Conda environment support?
- [ ] pyenv compatibility?
- [ ] Different locale settings?
- [ ] Different regional date formats?
- [ ] 32-bit Python support?

**✅ Düzeltme:** Version checks + compatibility notes

---

### 9️⃣ DEPENDENCIES & IMPORTS
- [ ] pandas installed — version check?
- [ ] sqlite3 built-in — verify?
- [ ] pathlib availability (Python 3.4+)?
- [ ] Other deps — minimize?
- [ ] Optional deps (chardet, tqdm)?
- [ ] Import error messages — helpful?
- [ ] Fallback implementations — any?
- [ ] Version pinning strategy?
- [ ] Offline installation possible?
- [ ] pip install... command ready?

**✅ Düzeltme:** requirements.txt + version checks

---

### 🔟 DOCUMENTATION & USABILITY
- [ ] Help message (-h, --help) complete?
- [ ] Example commands documented?
- [ ] README with setup instructions?
- [ ] CLI usage output clear?
- [ ] Error messages user-friendly?
- [ ] Verbose mode (--verbose) available?
- [ ] Output file location clear?
- [ ] Database file readable afterwards?
- [ ] Performance metrics reported?
- [ ] Troubleshooting guide?
- [ ] FAQ section?
- [ ] Non-English language support?

**✅ Düzeltme:** Better help text + examples

---

### 1️⃣1️⃣ TESTING & VALIDATION
- [ ] Unit tests — load_csv()?
- [ ] Unit tests — create_database()?
- [ ] Unit tests — import_data()?
- [ ] Integration tests — full pipeline?
- [ ] Test data sets (small, medium, large)?
- [ ] Edge case tests (empty, huge, corrupt)?
- [ ] Performance benchmarks?
- [ ] Regression tests?
- [ ] Test coverage >80%?
- [ ] CI/CD pipeline (GitHub Actions)?
- [ ] Manual testing checklist?
- [ ] Real data testing (23,812 records)?

**✅ Düzeltme:** Test suite + validation scripts

---

### 1️⃣2️⃣ MONITORING & DIAGNOSTICS
- [ ] Logging framework (not just print)?
- [ ] Debug mode available?
- [ ] Verbose output structured?
- [ ] Progress indicators (for large files)?
- [ ] Performance metrics (rows/sec)?
- [ ] Resource usage (memory, disk)?
- [ ] Database statistics post-import?
- [ ] Sanity checks (record count match)?
- [ ] Column statistics (nulls, types)?
- [ ] Output summary created?

**✅ Düzeltme:** Better logging + diagnostics

---

### 1️⃣3️⃣ ADMIN-FREE OPERATION
- [ ] No registry access ✅
- [ ] No Windows service installation?
- [ ] No system environment variable changes?
- [ ] No antivirus exceptions needed?
- [ ] Output to user folder (not Program Files)?
- [ ] Temp files in user temp dir?
- [ ] No DLL installations?
- [ ] No system-wide Python changes?
- [ ] Works in restricted shell?
- [ ] Works in non-admin command prompt?
- [ ] Works with UAC (User Access Control)?
- [ ] Works in portable mode (USB)?

**✅ Düzeltme:** Path handling + user-local operations

---

### 1️⃣4️⃣ PRODUCTION READINESS
- [ ] Error recovery — restart safe?
- [ ] Partial imports — recoverable?
- [ ] Database backup before overwrite?
- [ ] Audit trail (what was imported)?
- [ ] Version tracking (script version, data version)?
- [ ] Expiration dates (data freshness)?
- [ ] Compliance logs (GDPR, audit trail)?
- [ ] Data integrity verification?
- [ ] Database checksums?
- [ ] Rollback capability?
- [ ] Data retention policies?
- [ ] Disaster recovery plan?

**✅ Düzeltme:** Backup creation + integrity checks

---

## 📊 TEST RESULTS MATRIX

| Category | Status | Details | Fix Applied |
|----------|--------|---------|------------|
| Admin Dependency | ⏳ PENDING | Paths to test | — |
| File System | ⏳ PENDING | Path handling | — |
| Encoding | ✅ PASS | UTF-8 + Latin-1 + CP1252 tested | ✅ |
| Memory | ✅ PASS | chunksize=10000 implemented | ✅ |
| Error Handling | ⏳ PENDING | More edge cases needed | — |
| SQL Injection | ✅ PASS | Table name validation done | ✅ |
| SQLite | ⏳ PENDING | Transaction safety review | — |
| Cross-Platform | ⏳ PENDING | WSL2, older Python testing | — |
| Dependencies | ⏳ PENDING | requirements.txt creation | — |
| Documentation | ⏳ PENDING | README + examples | — |
| Testing | ⏳ PENDING | Unit tests + test suite | — |
| Monitoring | ⏳ PENDING | Logging framework | — |
| Admin-Free | ⏳ PENDING | Path verification | — |
| Production | ⏳ PENDING | Backup + recovery | — |

---

## 🎯 KRITIK FIXLER (Yapılacak)

### MUST-HAVE (Blocking)
1. [ ] Admin dependency removal
2. [ ] Robust path handling (spaces, special chars)
3. [ ] Column name sanitization
4. [ ] Database transaction safety
5. [ ] Edge case handling (empty files, corrupted data)

### SHOULD-HAVE (High Priority)
6. [ ] requirements.txt + dependency check
7. [ ] README + setup instructions
8. [ ] Error message improvements
9. [ ] Progress bar for large files
10. [ ] Logging framework

### NICE-TO-HAVE (Medium Priority)
11. [ ] Unit tests
12. [ ] Performance benchmarks
13. [ ] Rollback capability
14. [ ] Backup before overwrite
15. [ ] Multi-language support

---

## ✅ BAŞLAMA KRİTERLERİ

Aşağıdaki tüm kontroller PASS olana kadar başlamayız:

```
[ ] Admin bağımlılığı ZERO
[ ] Path handling tested (relative + absolute + spaces)
[ ] Encoding detection working (UTF-8, Latin-1, Turkish)
[ ] Large file test PASS (100+ MB)
[ ] SQL injection protection verified
[ ] Error handling comprehensive
[ ] Cross-platform basiccompat verified
[ ] Documentation complete
[ ] Real data (23,812 records) tested ✅
[ ] No warnings or errors in output
```

---

## 🚀 ÇALIŞMA SİSTEMİ

**Workflow:**
```
1. Kontrol listesini mark et (burada)
2. Her kategoriyi test et
3. Başarısız testler için fix ekle
4. Re-test
5. Green light → Production ready
```

**İlk test:** 
- CSV_TO_SQLITE_UNIVERSAL.py → realdata1.csv
- Çıktı: Alumni_RealData_RAW.db ✅ (zaten var)
- Sonraki: Başka CSV files test

---

## 📌 NOT
Bu checklist **thorough** olmalı. Hiçbir production script eksik kontrol ile çıkmamalı.
