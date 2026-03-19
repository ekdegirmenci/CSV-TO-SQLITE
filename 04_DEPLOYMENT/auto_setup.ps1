#!/usr/bin/env powershell
# CSV to SQLite - Auto Installer & Launcher
# Windows 11 - Python otomatik kuruluyor, converter çalışıyor
# Çalıştır: powershell -ExecutionPolicy Bypass -File auto_setup.ps1 -CsvFile data.csv

param(
    [string]$CsvFile = ""
)

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    switch ($Type) {
        "Success" { Write-Host "✓ $Message" -ForegroundColor $SuccessColor }
        "Error" { Write-Host "✗ $Message" -ForegroundColor $ErrorColor }
        "Warning" { Write-Host "⚠ $Message" -ForegroundColor $WarningColor }
        "Info" { Write-Host "  $Message" -ForegroundColor $InfoColor }
        default { Write-Host "• $Message" }
    }
}

function Check-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Header
Clear-Host
Write-Host "=====================================`n" -ForegroundColor Green
Write-Host "  CSV to SQLite - Auto Installer`n" -ForegroundColor Green
Write-Host "=====================================`n" -ForegroundColor Green

# Check if running as admin (recommended)
if (-not (Check-Admin)) {
    Write-Status "Not running as administrator (recommended but not required)" "Warning"
    Write-Host ""
}

# Step 1: Check Python
Write-Host "[1/4] Python kontrol ediliyor..." -ForegroundColor Cyan
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path

if ($pythonPath) {
    Write-Status "Python bulundu: $pythonPath" "Success"
    $python = "python"
} else {
    Write-Status "Python bulunamadı. Kurulması gerekiyor." "Warning"
    
    Write-Host ""
    Write-Host "[2/4] Python 3.14.3 indiriliyor..." -ForegroundColor Cyan
    
    # Download Python
    $pythonUrl = "https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe"
    $tempDir = [System.IO.Path]::GetTempPath()
    $installerPath = Join-Path $tempDir "python-3.14.3-amd64.exe"
    
    Write-Status "Hedef: $installerPath" "Info"
    
    try {
        # Download
        Write-Host "    İndiriliyor..." -ForegroundColor Gray
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -ErrorAction Stop
        Write-Status "İndirme tamamlandı (100 MB)" "Success"
        
        # Install
        Write-Host ""
        Write-Host "[3/4] Python kuruluyyor (2-3 dakika)..." -ForegroundColor Cyan
        
        $installArgs = @(
            "/quiet"
            "PrependPath=1"
            "InstallLauncherAllUsers=0"
            "Include_test=0"
            "Include_tcltk=0"
            "Include_doc=0"
        )
        
        $process = Start-Process -FilePath $installerPath `
                                 -ArgumentList $installArgs `
                                 -NoNewWindow `
                                 -PassThru `
                                 -Wait
        
        if ($process.ExitCode -ne 0) {
            Write-Status "Python kurulması başarısız (Kod: $($process.ExitCode))" "Error"
            Write-Host ""
            Write-Host "Çözüm:" -ForegroundColor Yellow
            Write-Host "1. https://www.python.org/downloads/ adresinden indiyin" -ForegroundColor Gray
            Write-Host "2. Kurulum sırasında 'Add Python to PATH' seçeneğini işaretleyin" -ForegroundColor Gray
            Write-Host "3. Bu script'i tekrar çalıştırın" -ForegroundColor Gray
            exit 1
        }
        
        Write-Status "Python kuruldu" "Success"
        
        # Clean up
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
    } catch {
        Write-Status "İndirme başarısız: $($_.Exception.Message)" "Error"
        Write-Host ""
        Write-Host "İnternet bağlantısını kontrol edin veya python.org'dan manuel edin" -ForegroundColor Yellow
        exit 1
    }
}

# Step 2: Install pandas
Write-Host ""
Write-Host "[4/4] pandas yükleniyor..." -ForegroundColor Cyan

try {
    Write-Host "    pip update ediliyor..." -ForegroundColor Gray
    python -m pip install --quiet --upgrade pip 2>$null
    
    Write-Host "    pandas kuruluyyor..." -ForegroundColor Gray
    python -m pip install --quiet pandas 2>$null
    
    # Verify installation
    python -c "import pandas; print(f'pandas {pandas.__version__}')" 2>$null
    
    Write-Status "pandas yüklendi" "Success"
} catch {
    Write-Status "pandas yükleme başarısız" "Error"
    exit 1
}

# Step 3: Run converter
Write-Host ""
Write-Host "=" * 37 -ForegroundColor Green
Write-Host "" -ForegroundColor Green

if ($CsvFile) {
    Write-Status "CSV dosyası: $CsvFile" "Info"
    Write-Host ""
    
    if (-not (Test-Path $CsvFile)) {
        Write-Status "Dosya bulunamadı: $CsvFile" "Error"
        exit 1
    }
    
    # Detect if converter script exists
    $converterScripts = @(
        "CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py",
        "./CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py",
        "$PSScriptRoot\CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py"
    )
    
    $converterPath = $null
    foreach ($script in $converterScripts) {
        if (Test-Path $script) {
            $converterPath = $script
            break
        }
    }
    
    if (-not $converterPath) {
        Write-Status "CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py bulunamadı" "Error"
        Write-Host ""
        Write-Host "Lütfen converter script'ini indirin:" -ForegroundColor Yellow
        Write-Host "https://github.com/.../CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py" -ForegroundColor Gray
        exit 1
    }
    
    # Run converter
    Write-Host "Converter çalıştırılıyor...`n" -ForegroundColor Cyan
    python $converterPath $CsvFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 37 -ForegroundColor Green
        Write-Status "Dönüştürme tamamlandı!" "Success"
        Write-Host "=" * 37 -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Status "Dönüştürme başarısız" "Error"
        exit 1
    }
} else {
    # Interactive mode
    Write-Host "Kullanım:" -ForegroundColor White
    Write-Host ""
    Write-Host "  powershell -ExecutionPolicy Bypass -File auto_setup.ps1 -CsvFile data.csv" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Veya:" -ForegroundColor White
    Write-Host ""
    Write-Host "  python CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py your_data.csv" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Seçenekler:" -ForegroundColor White
    Write-Host "  -o, --output DB_FILE        Çıkış veritabanı (varsayılan: <csv_name>.db)" -ForegroundColor Gray
    Write-Host "  -t, --table TABLE_NAME      Tablo adı (varsayılan: data)" -ForegroundColor Gray
    Write-Host "  -q, --quiet                 Sessiz mod" -ForegroundColor Gray
    Write-Host "  --log-level DEBUG|INFO      Verbosity seviyesi" -ForegroundColor Gray
}

Write-Host ""
