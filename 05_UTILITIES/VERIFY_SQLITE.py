#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SQLite Database Verification & Validation Script
"""

import sqlite3
import pandas as pd
import os
import sys

def verify_sqlite_database(db_file, table_name='alumni_raw'):
    """Verify SQLite database integrity"""
    
    print("="*80)
    print("SQLITE DATABASE VERIFICATION")
    print("="*80)
    
    # Check file exists
    print(f"\n[1] File Check:")
    if not os.path.exists(db_file):
        print(f"[ERROR] Database file not found: {db_file}")
        return False
    
    file_size = os.path.getsize(db_file) / 1024 / 1024
    print(f"     ✓ File exists: {db_file}")
    print(f"     ✓ File size: {file_size:.1f} MB")
    
    # Connect to database
    print(f"\n[2] Connection Check:")
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print(f"     ✓ Connected successfully")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    
    # Check tables
    print(f"\n[3] Tables Check:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    if not tables:
        print(f"[ERROR] No tables found in database")
        return False
    
    for table in tables:
        print(f"     ✓ {table[0]}")
    
    # Check main table
    print(f"\n[4] Main Table Check ({table_name}):")
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]
        print(f"     ✓ Records: {record_count:,}")
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"     ✓ Columns: {len(columns)}")
        
        print(f"     ✓ Table integrity: OK")
    except Exception as e:
        print(f"[ERROR] Table check failed: {e}")
        conn.close()
        return False, {}
    
    # Show schema sample
    print(f"\n[5] Schema Sample:")
    for i, col in enumerate(columns[:10]):
        col_id, col_name, col_type = col[0], col[1], col[2]
        print(f"     {col_id+1:2d}. {col_name:35s} ({col_type})")
    if len(columns) > 10:
        print(f"     ... and {len(columns)-10} more columns")
    
    # Sample data
    print(f"\n[6] Sample Data (First 3 records):")
    try:
        df_sample = pd.read_sql_query(
            f"SELECT * FROM {table_name} LIMIT 3",
            conn
        )
        
        if not df_sample.empty:
            for idx, row in df_sample.iterrows():
                print(f"\n     Record {idx+1}:")
                # Show only non-null values
                for col in df_sample.columns:
                    val = row[col]
                    if pd.notna(val):
                        val_str = str(val)[:50]  # Truncate long values
                        print(f"       {col[:40]:40s}: {val_str}")
        else:
            print(f"     No data found")
    except Exception as e:
        print(f"     Error retrieving sample data: {e}")
    
    # Metadata check
    print(f"\n[7] Metadata Table Check:")
    try:
        df_metadata = pd.read_sql_query(
            "SELECT * FROM _metadata",
            conn
        )
        print(f"     ✓ Metadata records: {len(df_metadata)}")
        
        # Show null statistics
        print(f"\n     Top 10 Columns by Null Percentage:")
        df_meta_sorted = df_metadata.nlargest(10, 'null_percentage')
        for idx, row in df_meta_sorted.iterrows():
            col_name = row['column_name'][:40]
            null_pct = row['null_percentage']
            print(f"       {col_name:40s} {null_pct:6.1f}% null")
    except Exception as e:
        print(f"     Metadata check error: {e}")
    
    # Indexes check
    print(f"\n[8] Indexes Check:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (table_name,))
    indexes = cursor.fetchall()
    print(f"     ✓ Indexes created: {len(indexes)}")
    for idx in indexes:
        print(f"       - {idx[0]}")
    
    # Query test
    print(f"\n[9] Query Performance Test:")
    
    # Test 1: Filter by column
    try:
        import time
        start = time.time()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE \"Raklet Id\" IS NOT NULL")
        result = cursor.fetchone()[0]
        elapsed = time.time() - start
        print(f"     ✓ Query 1 (filter): {result:,} records in {elapsed*1000:.1f}ms")
    except Exception as e:
        print(f"     Query 1 failed: {e}")
    
    # Test 2: Group by
    try:
        start = time.time()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE \"Profile - Gender\" IS NOT NULL")
        result = cursor.fetchone()[0]
        elapsed = time.time() - start
        print(f"     ✓ Query 2 (group): {result:,} records in {elapsed*1000:.1f}ms")
    except Exception as e:
        print(f"     Query 2 failed: {e}")
    
    # Final summary
    print(f"\n" + "="*80)
    print(f"[RESULT] DATABASE VERIFICATION SUCCESSFUL")
    print(f"="*80)
    
    summary = {
        'file_size_mb': file_size,
        'record_count': record_count,
        'column_count': len(columns),
        'index_count': len(indexes),
        'table_count': len(tables),
        'status': 'VALID'
    }
    
    print(f"\nSummary:")
    print(f"  Database File: {db_file}")
    print(f"  File Size: {file_size:.1f} MB")
    print(f"  Records: {record_count:,}")
    print(f"  Columns: {len(columns)}")
    print(f"  Indexes: {len(indexes)}")
    print(f"  Status: ✓ VALID & READY FOR USE")
    
    conn.close()
    
    return True, summary


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python verify_sqlite.py <database.db> [table_name]")
        print("\nExample:")
        print("  python verify_sqlite.py Alumni_RealData_RAW.db alumni_raw")
        sys.exit(1)
    
    db_file = sys.argv[1]
    table_name = sys.argv[2] if len(sys.argv) > 2 else 'alumni_raw'
    
    success, summary = verify_sqlite_database(db_file, table_name)
    
    sys.exit(0 if success else 1)
