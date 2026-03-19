#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL Detection & Installation Helper
"""

import subprocess
import sys
import os
from pathlib import Path
import psycopg2

def check_postgresql_installation():
    """Check if PostgreSQL is installed and running"""
    
    print("="*80)
    print("POSTGRESQL DETECTION & INSTALLATION STATUS")
    print("="*80)
    
    print("\n[1] PostgreSQL Binary Search:")
    
    # Common PostgreSQL paths on Windows
    possible_paths = [
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\13\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\14\bin\psql.exe",
        r"C:\PostgreSQL\bin\psql.exe",
    ]
    
    pg_found = False
    pg_path = None
    
    for path in possible_paths:
        if os.path.exists(path):
            pg_found = True
            pg_path = path
            print(f"     ✓ PostgreSQL found at: {path}")
            break
    
    if not pg_found:
        print(f"     ✗ PostgreSQL not found in default locations")
        print(f"\n[2] Alternative: Using Portable PostgreSQL")
        print(f"     - Download from: https://www.enterprisedb.com/download-postgresql-binaries")
        print(fr"     - Extract to: C:\PostgreSQL\\")
        print(f"     - No admin rights needed")
        print(f"\n[3] OR: Install via Windows Package Manager")
        print(f"     Command: winget install PostgreSQL.PostgreSQL")
        print(f"\n[4] OR: Install via Chocolatey (if available)")
        print(f"     Command: choco install postgresql")
        return pg_path
    
    # Test connection
    print(f"\n[2] Testing Connection:")
    try:
        # Try default connection
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"     ✓ Connected successfully")
        print(f"     ✓ Version: {version.split(',')[0]}")
        
        cursor.close()
        conn.close()
        
        print(f"\n[3] PostgreSQL Status: READY FOR USE")
        return pg_path
    
    except Exception as e:
        print(f"     ✗ Connection failed: {e}")
        print(f"\n[2] Troubleshooting:")
        print(f"     1. Verify PostgreSQL service is running")
        print(f"     2. Check connection parameters:")
        print(f"        - Host: localhost")
        print(f"        - Port: 5432")
        print(f"        - User: postgres")
        print(f"        - Password: (check during installation)")
        print(f"\n     3. Reset PostgreSQL password:")
        print(f"        - Open pgAdmin (if installed)")
        print(f"        - Or use command: psql -U postgres")
        print(f"\n     4. Portable PostgreSQL (NO ADMIN):")
        print(f"        - Download portable version")
        print(fr"        - Extract to: C:\PostgreSQL\\")
        print(fr"        - Initialize: initdb -D C:\PostgreSQL\data")
        print(fr"        - Start: pg_ctl -D C:\PostgreSQL\data start")
        
        return None


def try_portable_postgresql():
    """Attempt to setup portable PostgreSQL"""
    
    print("\n" + "="*80)
    print("PORTABLE POSTGRESQL SETUP (NO ADMIN RIGHTS)")
    print("="*80)
    
    portable_path = Path("C:/PostgreSQL")
    
    if portable_path.exists():
        print(f"\n✓ Portable PostgreSQL found at: {portable_path}")
        print(f"  See setup guide in: {portable_path}/README.txt")
        return True
    
    print(f"\n[SETUP GUIDE] Portable PostgreSQL")
    print(f"="*80)
    print(f"""
1. Download Portable PostgreSQL:
   - Visit: https://www.enterprisedb.com/download-postgresql-binaries
   - Select Windows x86-64
   - Download latest stable version (15+)

2. Extract to C:\\PostgreSQL\\
   - Create folder: C:\\PostgreSQL
   - Extract ZIP there
   - Should have: bin/, data/, include/, lib/, share/ folders

3. Initialize Database:
   - Open PowerShell as current user (no admin)
   - cd C:\\PostgreSQL
   - Run: .\\bin\\initdb.exe -D data -U postgres -A trust -E UTF8

4. Start PostgreSQL:
   - Run: .\\bin\\pg_ctl.exe -D data start
   - Should see: "server started"

5. Test Connection:
   - Run: .\\bin\\psql.exe -U postgres
   - Type: SELECT 1;
   - Should return: 1

6. Automatic Startup Script (Optional):
   - Create C:\\PostgreSQL\\start.bat:
     {portable_path}\\bin\\pg_ctl.exe -D {portable_path}\\data start
   - Run it at startup

7. For CSV-to-PostgreSQL Conversion:
   python CSV_TO_POSTGRESQL.py your_file.csv -H localhost -u postgres -P 5432 -o csv_data
""")
    
    return False


if __name__ == '__main__':
    print("[INFO] Checking Python PostgreSQL connection...")
    
    try:
        import psycopg2
        print("✓ psycopg2 module found")
    except ImportError:
        print("✗ psycopg2 not installed")
        print("  Install with: pip install psycopg2-binary")
        sys.exit(1)
    
    # Check installation
    pg_path = check_postgresql_installation()
    
    # Offer portable setup if not found
    if not pg_path:
        try_portable_postgresql()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print(f"""
1. If PostgreSQL is running:
   python CSV_TO_POSTGRESQL.py 'path/to/your.csv' -o csv_data -t your_table

2. If using portable PostgreSQL:
   - Start PostgreSQL first
   - Then run the converter command above

3. For Koç alumni data:
   python CSV_TO_POSTGRESQL.py '05_STAKEHOLDER_FOCUSED_VAKA\\01_RAW_DATA\\realdata1\\fd92876e-...csv' \\
     -o alumni_db -t alumni_raw -u postgres
""")
