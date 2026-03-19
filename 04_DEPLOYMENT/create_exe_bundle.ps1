# CSV-to-SQLite Windows 11 EXE Bundle Creator
# Python yüklü olmayan bilgisayarlar için
# Çalıştır: powershell -ExecutionPolicy Bypass -File create_exe_bundle.ps1

Write-Host "CSV-to-SQLite Windows 11 EXE Bundle Creator" -ForegroundColor Green
Write-Host "=============================================`n" -ForegroundColor Green

# Step 1: Check if Python is available
Write-Host "[1/5] Python kontrol ediliyor..." -ForegroundColor Cyan
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
if ($pythonPath) {
    Write-Host "  ✓ Python bulundu: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python bulunamadı. Lütfen Python 3.8+ yükleyiniz." -ForegroundColor Red
    Write-Host "    İnternet bağlantısı varsa: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Step 2: Install PyInstaller
Write-Host "`n[2/5] PyInstaller yükleniyor..." -ForegroundColor Cyan
pip install pyinstaller --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ PyInstaller yüklendi" -ForegroundColor Green
} else {
    Write-Host "  ✗ PyInstaller yükleme başarısız" -ForegroundColor Red
    exit 1
}

# Step 3: Create build directory
Write-Host "`n[3/5] Build dizini hazırlanıyor..." -ForegroundColor Cyan
$buildDir = "csv_to_sqlite_exe"
if (Test-Path $buildDir) {
    Remove-Item $buildDir -Recurse -Force
    Write-Host "  ✓ Eski build temizlendi" -ForegroundColor Green
}
New-Item -ItemType Directory -Path $buildDir -ErrorAction SilentlyContinue | Out-Null
Write-Host "  ✓ Build dizini hazırlandı: $buildDir" -ForegroundColor Green

# Step 4: Build EXE with PyInstaller
Write-Host "`n[4/5] EXE dosyası oluşturuluyor (bu 1-2 dakika alabilir)..." -ForegroundColor Cyan
$scriptPath = "CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py"

if (-not (Test-Path $scriptPath)) {
    Write-Host "  ✗ Script bulunamadı: $scriptPath" -ForegroundColor Red
    exit 1
}

# Create spec file for optimization
pyinstaller `
    --onefile `
    --windowed `
    --name "csv_to_sqlite" `
    --icon=NONE `
    --distpath="$buildDir\dist" `
    --buildpath="$buildDir\build" `
    --specpath="$buildDir" `
    --add-data=".:." `
    --hidden-import=pandas `
    --hidden-import=sqlite3 `
    $scriptPath `
    2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ EXE başarıyla oluşturuldu" -ForegroundColor Green
} else {
    Write-Host "  ✗ EXE oluşturma başarısız" -ForegroundColor Red
    exit 1
}

# Step 5: Create standalone bundle
Write-Host "`n[5/5] Standalone bundle hazırlanıyor..." -ForegroundColor Cyan
$exePath = "$buildDir\dist\csv_to_sqlite.exe"
$bundleDir = "CSV_to_SQLite_Windows"

if (Test-Path $bundleDir) {
    Remove-Item $bundleDir -Recurse -Force
}
New-Item -ItemType Directory -Path $bundleDir | Out-Null

# Copy exe
Copy-Item $exePath "$bundleDir\csv_to_sqlite.exe" -Force
Write-Host "  ✓ EXE dosyası kopyalandı" -ForegroundColor Green

# Create README
$readmeContent = @"
# CSV to SQLite - Windows 11 Standalone Executable

## Hızlı Başlangıç

1. CSV dosyanızı bu klasöre kopyalayın
2. `csv_to_sqlite.exe` dosyasına sağ tıklayın → "Özellikler" → "İlişkili program seç"
3. **VEYA** terminalde çalıştırın:

```cmd
csv_to_sqlite.exe your_data.csv
```

## Komut Örnekleri

```cmd
# Basit kullanım
csv_to_sqlite.exe data.csv

# Özel çıktı dosyası
csv_to_sqlite.exe data.csv -o mydb.db -t employees

# Sessiz mod
csv_to_sqlite.exe data.csv --quiet

# Debug modu
csv_to_sqlite.exe data.csv --log-level DEBUG
```

## Özellikler

✓ Admin yetkisi GEREKMEZ
✓ Python yüklü olması GEREKMEZ
✓ Tek dosya - taşınabilir
✓ Tüm Encoding'ler desteklenir (UTF-8, Latin-1, Türkçe, vb.)
✓ Otomatik backup oluşturur
✓ SQL injection koruması
✓ 50,000+ satırı destekler

## Windows Güvenliği

Windows 11 bu dosyayı tanımadığı için uyarı gösterebilir:
1. "Weitere Informationen" / "More info" tıklayın
2. "Ausführen trotzdem" / "Run anyway" seçin
3. Dosya çalışacaktır

## Sorun Giderme

**"Virüs" uyarısı alıyorum?**
- PyInstaller oluşturulan dosyalar bazen antivirus tarafından flaglanır
- Dosya 100% güvenlidir (kaynak koda bakın)
- Whitelist'e ekleyin veya antivirus'ü geçici olarak devre dışı bırakın

**Çalışmıyor?**
- Windows Defender SmartScreen'i geçin
- Admin olarak çalıştırmayı deneyin
- Dosyayı farklı konuma kopyalayın

## İçerik

- `csv_to_sqlite.exe` - Ana uygulamak (500+ MB, tüm dependenciler dahil)

## Destek

Sorun varsa:
1. Terminal açın (cmd veya PowerShell)
2. `csv_to_sqlite.exe --help` yazın
3. Dosyayı debug modda çalıştırın: `csv_to_sqlite.exe data.csv --log-level DEBUG`

---
Oluşturma Tarihi: $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')
Python: 3.8+
Windows: 11/10
"@

$readmeContent | Out-File "$bundleDir\README.txt" -Encoding UTF8
Write-Host "  ✓ README hazırlandı" -ForegroundColor Green

# Create batch file for easy execution
$batchContent = @"
@echo off
REM CSV to SQLite - Windows 11 Standalone
REM Çift tıkla veya batch dosyasını çalıştır

if "%~1"=="" (
    echo.
    echo CSV to SQLite - Windows 11 Standalone
    echo ======================================
    echo.
    echo Kullanım:
    echo   1. CSV dosyasını bu klasöre kopyalayın
    echo   2. Terminalde çalıştırın:
    echo      csv_to_sqlite.exe your_data.csv
    echo.
    echo Örnekler:
    echo   csv_to_sqlite.exe data.csv
    echo   csv_to_sqlite.exe data.csv -o mydb.db -t employees
    echo.
    pause
) else (
    csv_to_sqlite.exe %*
)
"@

$batchContent | Out-File "$bundleDir\run.bat" -Encoding ASCII
Write-Host "  ✓ Batch dosyası hazırlandı" -ForegroundColor Green

# Get file sizes
$exeSize = "{0:F2}" -f ((Get-Item "$bundleDir\csv_to_sqlite.exe").Length / 1MB)
Write-Host "  ✓ EXE dosyası boyutu: ${exeSize} MB" -ForegroundColor Green

# Summary
Write-Host "`n" + ("="*50) -ForegroundColor Green
Write-Host "✓ BUNDLE BAŞARIYLA OLUŞTURULDU!" -ForegroundColor Green
Write-Host ("="*50) -ForegroundColor Green
Write-Host "`nKlasör: $bundleDir" -ForegroundColor Cyan
Write-Host "Dosyalar:" -ForegroundColor Cyan
Write-Host "  • csv_to_sqlite.exe (${exeSize} MB)" -ForegroundColor White
Write-Host "  • README.txt" -ForegroundColor White
Write-Host "  • run.bat" -ForegroundColor White

Write-Host "`nSonraki Adımlar:" -ForegroundColor Yellow
Write-Host "  1. '$bundleDir' klasörünü kapatıp aç" -ForegroundColor White
Write-Host "  2. 'csv_to_sqlite.exe' dosyasını sağ tıklayıp Özellikler'e bak" -ForegroundColor White
Write-Host "  3. Terminalde çalıştır: cd $bundleDir" -ForegroundColor White
Write-Host "  4. Komutu çalıştır: .\csv_to_sqlite.exe your_data.csv" -ForegroundColor White

Write-Host "`nPaylaşma:" -ForegroundColor Yellow
Write-Host "  $bundleDir klasörünün tamamını ZIP olarak kodla" -ForegroundColor White
Write-Host "  Windows 11 kullanıcılara gönder" -ForegroundColor White
Write-Host "  Hiçbir bağımlılık / Python yüklü olması GEREKMEZ!" -ForegroundColor Green

Write-Host "`n"
