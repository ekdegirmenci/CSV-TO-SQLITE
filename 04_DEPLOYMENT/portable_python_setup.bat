@echo off
REM Portable Python + CSV to SQLite Setup
REM Windows 11 - Python olmayan bilgisayarlar için
REM Çalıştır: portable_python_setup.bat

setlocal enabledelayedexpansion
cd /d "%~dp0"

cls
echo.
echo ============================================
echo CSV to SQLite - Portable Python Setup
echo ============================================
echo.

REM Step 1: Python İndirilmiş mi?
set PYTHON_ZIP=WinPython-64bit-3.14.3.exe
set PYTHON_DIR=C:\WinPython

if exist "%PYTHON_DIR%" (
    echo [✓] Portable Python bulundu: %PYTHON_DIR%
    goto install_pandas
)

echo [!] Portable Python bulunamadı
echo.
echo Seçenekler:
echo 1. WinPython'u manuel indir: https://winpython.github.io/
echo    File: WinPython-64bit-3.14.3.exe
echo 2. Veya bu klasöre kopyala: %CD%
echo.
echo İndirdikten sonra bu batch dosyasını tekrar çalıştır
echo.
pause
exit /b 1

:install_pandas
echo [1/4] pandas yükleniyor...
"%PYTHON_DIR%\python.exe" -m pip install --quiet pandas

if %errorlevel% neq 0 (
    echo [!] pandas yükleme başarısız
    pause
    exit /b 1
)
echo [✓] pandas yüklendi

REM Step 2: Converter script kopyala
echo.
echo [2/4] Converter script kopyalanıyor...
if exist "CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py" (
    copy "CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py" "%PYTHON_DIR%\" >nul 2>&1
    echo [✓] Script kopyalandı
) else (
    echo [!] CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py bulunamadı
    pause
    exit /b 1
)

REM Step 3: Batch wrapper oluştur
echo.
echo [3/4] Wrapper batch dosyası oluşturuluyor...
(
    echo @echo off
    echo REM CSV to SQLite - Portable Python Wrapper
    echo "%PYTHON_DIR%\python.exe" "%PYTHON_DIR%\CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py" %%*
    echo pause
) > "%PYTHON_DIR%\csv_to_sqlite.bat"
echo [✓] Wrapper oluşturuldu

REM Step 4: README oluştur
echo.
echo [4/4] README.txt hazırlanıyor...
(
    echo CSV to SQLite - Portable Python
    echo ================================
    echo.
    echo Kurulum tamamlandı!
    echo.
    echo Kullanım:
    echo.
    echo   Cmd/PowerShell'de:
    echo   "%PYTHON_DIR%\python.exe" "%PYTHON_DIR%\CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py" your_data.csv
    echo.
    echo   VEYA
    echo.
    echo   "%PYTHON_DIR%\csv_to_sqlite.bat" your_data.csv
    echo.
    echo Örnekler:
    echo   csv_to_sqlite.bat data.csv
    echo   csv_to_sqlite.bat data.csv -o mydb.db -t employees
    echo.
    echo Portabilite:
    echo   C:\WinPython klasörünün tamamını başka bir konuma kopyalayabilirsiniz
    echo   Hepsi birlikte çalışacaktır
    echo.
    echo Özellikler:
    echo   ✓ Admin yetkisi GEREKMEZ
    echo   ✓ Python kurulu olması GEREKMEZ (Portable Python kullanıyor)
    echo   ✓ Tüm encoding'ler desteklenir
    echo   ✓ 50,000+ satırı destekler
    echo.
) > "%PYTHON_DIR%\CSV_to_SQLite_README.txt"
echo [✓] README oluşturuldu

REM Summary
echo.
echo.
echo ============================================
echo [✓] SETUP TAMAMLANDI!
echo ============================================
echo.
echo Dizin: %PYTHON_DIR%
echo.
echo Düzen:
echo   WinPython\python.exe (taşınabilir Python)
echo   WinPython\CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION.py
echo   WinPython\csv_to_sqlite.bat (shortcut)
echo.
echo Kullanım:
echo   "%PYTHON_DIR%\csv_to_sqlite.bat" your_data.csv
echo.
echo Paylaşma:
echo   C:\WinPython klasörünün tamamını ZIP'le
echo   İsteyen kişiye gönder
echo   Hiçbir Python kurulması GEREKMEZ!
echo.
pause
