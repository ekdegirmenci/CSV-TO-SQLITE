#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Raw Data CSV → SQLite Converter
This script converts the raw_data CSV file to SQLite format
"""

import os
import sys
from pathlib import Path

# Add production module to path
sys.path.insert(0, str(Path(__file__).parent / '01_PRODUCTION'))

from CSV_TO_SQLITE_UNIVERSAL_v2_PRODUCTION import CSVtoSQLite

def main():
    # Define paths
    raw_data_dir = Path(__file__).parent / 'raw_data'
    csv_file = list(raw_data_dir.glob('*.csv'))[0]  # Get first CSV
    
    db_file = raw_data_dir / f"{csv_file.stem}_converted.db"
    
    print(f"\n{'='*60}")
    print(f"  RAW DATA CSV → SQLite CONVERTER")
    print(f"{'='*60}")
    print(f"  Source CSV: {csv_file}")
    print(f"  Target DB:  {db_file}")
    print(f"{'='*60}\n")
    
    try:
        # Create converter instance
        converter = CSVtoSQLite(
            csv_file=str(csv_file),
            db_file=str(db_file),
            table_name='raw_data',
            verbose=True,
            backup=True
        )
        
        # Step 1: Load CSV
        print("\n[STEP 1] Loading CSV...")
        converter.load_csv()
        print(f"✓ Loaded {len(converter.df)} rows × {len(converter.df.columns)} columns")
        
        # Step 2: Convert to SQLite
        print("\n[STEP 2] Converting to SQLite...")
        converter.convert()
        print(f"✓ Successfully created: {db_file}")
        
        # Step 3: Display statistics
        print("\n[STEP 3] Conversion Statistics:")
        for key, value in converter.stats.items():
            print(f"  • {key}: {value}")
        
        # Step 4: Verify database
        print("\n[STEP 4] Verifying database...")
        converter.verify_database()
        print("✓ Database verification successful!")
        
        print(f"\n{'='*60}")
        print(f"  ✓ CONVERSION COMPLETED SUCCESSFULLY")
        print(f"{'='*60}\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
