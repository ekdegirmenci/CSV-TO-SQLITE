#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UNIVERSAL CSV TO SQLITE CONVERTER
Herhangi bir CSV dosyasını SQLite database'ine dönüştür
"""

import pandas as pd
import sqlite3
import os
import sys
import re
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class CSVtoSQLite:
    """CSV to SQLite converter class"""
    
    @staticmethod
    def _validate_table_name(table_name):
        """
        Validate table name to prevent SQL injection
        
        Args:
            table_name (str): Table name to validate
            
        Raises:
            ValueError: If table name contains invalid characters
        """
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
            raise ValueError(f"Invalid table name: {table_name!r}. Must start with letter or underscore, "
                           f"contain only alphanumeric and underscores")
    
    def __init__(self, csv_file, db_file=None, table_name='data', verbose=True):
        """
        Initialize converter
        
        Args:
            csv_file (str): Path to input CSV file
            db_file (str): Output SQLite database file (auto-generated if None)
            table_name (str): Name of table in database
            verbose (bool): Print progress messages
            
        Raises:
            ValueError: If table_name is invalid
        """
        # Validate table name before any operations (KRITIK-2 FIX)
        self._validate_table_name(table_name)
        
        self.csv_file = csv_file
        self.verbose = verbose
        self.table_name = table_name
        
        # Auto-generate database filename if not provided
        if db_file is None:
            base_name = Path(csv_file).stem
            db_file = f"{base_name}.db"
        
        self.db_file = db_file
        self.df = None
        self.conn = None
        self.cursor = None
    
    def _print(self, message):
        """Print if verbose mode enabled"""
        if self.verbose:
            print(message)
    
    def load_csv(self):
        """Load CSV file into pandas DataFrame with intelligent encoding detection"""
        self._print(f"[1] Loading CSV: {self.csv_file}")
        
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        # Try encoding chain with proper nested exception handling (KRİTİK-1 FIX)
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-9', 'cp1252', 'windows-1254']
        
        last_error = None
        for encoding in encodings:
            try:
                self._print(f"    Trying encoding: {encoding}...")
                self.df = pd.read_csv(self.csv_file, encoding=encoding, low_memory=False)
                self._print(f"    ✓ Successfully loaded with {encoding}")
                break
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                continue
        
        if self.df is None:
            raise UnicodeDecodeError('unknown', b'', 0, 1, 
                                    f"Could not decode CSV with any encoding. Last error: {last_error}")
        
        file_size = os.path.getsize(self.csv_file) / 1024 / 1024
        self._print(f"[OK] Loaded: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
        self._print(f"     File size: {file_size:.1f} MB")
        
        return self
    
    def create_database(self):
        """Create SQLite database and import data"""
        self._print(f"\n[2] Creating SQLite Database: {self.db_file}")
        
        # Remove old database if exists
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
            self._print("     Removed old database")
        
        # Create connection
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        
        self._print("[OK] Database created")
        
        return self
    
    def import_data(self, chunksize=10000):
        """
        Import CSV data into SQLite table with chunked processing
        
        Args:
            chunksize (int): Number of rows per batch insert (default: 10000)
                           Reduces memory usage for large files
        """
        self._print(f"\n[3] Importing Data...")
        
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        if self.conn is None:
            raise ValueError("No database connection. Call create_database() first.")
        
        self._print(f"     Creating table '{self.table_name}'...")
        
        # Import with chunksize for memory efficiency (MAJOR-3 FIX)
        row_count = len(self.df)
        self.df.to_sql(self.table_name, self.conn, if_exists='replace', 
                      index=False, chunksize=chunksize)
        
        self.conn.commit()
        
        # Verify import
        if self.cursor is None:
            self.cursor = self.conn.cursor()
        
        self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
        count = self.cursor.fetchone()[0]
        
        self._print(f"[OK] Data imported: {count:,} records")
        
        return self
    
    def create_indexes(self):
        """Create indexes on columns for faster queries"""
        self._print(f"\n[4] Creating Indexes...")
        
        # Check if cursor exists (MAJOR-1 FIX)
        if self.cursor is None:
            raise ValueError("Database not initialized. Call create_database() first.")
        
        # Find numeric and string columns suitable for indexing
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()[:5]
        string_cols = self.df.select_dtypes(include=['object']).columns.tolist()[:8]
        
        index_count = 0
        created_indexes = set()
        
        # Create indexes on key columns with better naming (MİNOR-1, MİNOR-4 FIX)
        for i, col in enumerate(string_cols):
            try:
                # Better index naming to avoid collisions
                safe_col_name = col.replace(' ', '_').replace('-', '_').replace('.', '_')[:20]
                index_name = f"idx_str_{i}_{safe_col_name}"
                
                # Prevent duplicate index names
                if index_name in created_indexes:
                    continue
                
                self.cursor.execute(f'CREATE INDEX [{index_name}] ON [{self.table_name}] ([{col}])')
                created_indexes.add(index_name)
                index_count += 1
            except sqlite3.OperationalError as e:
                # Silently skip problematic columns
                continue
        
        # Create indexes on numeric columns if they exist
        for i, col in enumerate(numeric_cols):
            try:
                safe_col_name = col.replace(' ', '_').replace('-', '_').replace('.', '_')[:20]
                index_name = f"idx_num_{i}_{safe_col_name}"
                
                if index_name in created_indexes:
                    continue
                
                self.cursor.execute(f'CREATE INDEX [{index_name}] ON [{self.table_name}] ([{col}])')
                created_indexes.add(index_name)
                index_count += 1
            except sqlite3.OperationalError as e:
                continue
        
        self.conn.commit()
        
        self._print(f"[OK] Created {index_count} indexes")
        
        return self
    
    def create_metadata_table(self):
        """Create metadata table documenting column information"""
        self._print(f"\n[5] Creating Metadata Table...")
        
        # Check prerequisites (MAJOR-1 FIX)
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        if self.conn is None:
            raise ValueError("No database connection. Call create_database() first.")
        
        metadata = pd.DataFrame({
            'column_name': self.df.columns,
            'data_type': self.df.dtypes.astype(str),
            'non_null_count': self.df.count().values,
            'null_count': self.df.isna().sum().values,
            'null_percentage': (self.df.isna().sum().values / len(self.df) * 100).round(2),
            'unique_values': [self.df[col].nunique() for col in self.df.columns]
        })
        
        metadata.to_sql('_metadata', self.conn, if_exists='replace', index=False)
        self.conn.commit()
        
        self._print(f"[OK] Metadata table created ({len(metadata)} columns)")
        
        return self
    
    def get_statistics(self):
        """Get database statistics"""
        self._print(f"\n[6] Database Statistics...")
        
        # Check prerequisites (MAJOR-1 FIX)
        if self.cursor is None:
            raise ValueError("Database not initialized. Call create_database() first.")
        if self.conn is None:
            raise ValueError("Database connection closed.")
        
        self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
        total_records = self.cursor.fetchone()[0]
        
        self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
        columns = self.cursor.fetchall()
        total_columns = len(columns)
        
        db_size = os.path.getsize(self.db_file) / 1024 / 1024
        
        self._print(f"  Total Records: {total_records:,}")
        self._print(f"  Total Columns: {total_columns}")
        self._print(f"  Database Size: {db_size:.1f} MB")
        
        return {
            'records': total_records,
            'columns': total_columns,
            'size_mb': db_size
        }
    
    def get_schema(self):
        """Display database schema"""
        self._print(f"\n[7] Database Schema...")
        
        # Check prerequisites (MAJOR-1 FIX)
        if self.cursor is None:
            raise ValueError("Database not initialized. Call create_database() first.")
        
        self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
        columns = self.cursor.fetchall()
        
        self._print(f"\n  Table: {self.table_name}")
        for col_id, col_name, col_type, notnull, default, pk in columns[:10]:
            nullable = "NOT NULL" if notnull else "NULL"
            self._print(f"    {col_id+1}. {col_name:30s} {col_type:10s} {nullable}")
        
        if len(columns) > 10:
            self._print(f"    ... and {len(columns)-10} more columns")
        
        return columns
    
    def create_documentation(self, doc_file=None):
        """Create database documentation file"""
        if doc_file is None:
            doc_file = f"{Path(self.db_file).stem}_DOCUMENTATION.txt"
        
        self._print(f"\n[8] Creating Documentation: {doc_file}")
        
        # Check prerequisites (MAJOR-1 FIX)
        if self.cursor is None:
            raise ValueError("Database not initialized. Call create_database() first.")
        if self.conn is None:
            raise ValueError("Database connection closed.")
        
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
            total_records = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
            columns = self.cursor.fetchall()
            
            db_size = os.path.getsize(self.db_file) / 1024 / 1024
            
            doc_content = f"""
DATABASE DOCUMENTATION
======================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: {self.csv_file}

DATABASE INFORMATION
====================
Type: SQLite3
File: {self.db_file}
Size: {db_size:.1f} MB
Records: {total_records:,}
Columns: {len(columns)}

TABLE STRUCTURE
===============
Table Name: {self.table_name}

Columns:
"""
            
            for col_id, col_name, col_type, notnull, default, pk in columns:
                nullable = "NOT NULL" if notnull else "NULL"
                doc_content += f"\n  {col_id+1}. {col_name:40s} {col_type:10s} {nullable}"
            
            doc_content += f"""

METADATA TABLE
==============
Table: _metadata
Columns: column_name, data_type, non_null_count, null_count, null_percentage, unique_values
Purpose: Column information and data quality tracking

QUICK START QUERIES
===================

1. Count total records:
   SELECT COUNT(*) FROM [{self.table_name}];

2. Get column information:
   SELECT * FROM _metadata ORDER BY null_percentage DESC;

3. Export to CSV:
   .mode csv
   .output export.csv
   SELECT * FROM [{self.table_name}];
   .quit

PYTHON USAGE
============

import sqlite3
import pandas as pd

# Connect
conn = sqlite3.connect('{self.db_file}')

# Query data
df = pd.read_sql_query('SELECT * FROM [{self.table_name}] LIMIT 100', conn)

# Get metadata
metadata = pd.read_sql_query('SELECT * FROM _metadata', conn)

conn.close()

STATUS: ✅ READY FOR USE
"""
            
            # Ensure directory exists (MİNOR-3 FIX)
            doc_path = Path(doc_file)
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            self._print(f"[OK] Documentation created: {doc_file}")
        
        except (IOError, OSError) as e:
            self._print(f"[WARNING] Could not create documentation: {e}")
        
        return self
    
    def close(self):
        """
        Close database connection
        Idempotent - safe to call multiple times (MAJOR-2 FIX)
        """
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
            self._print(f"\n[OK] Database closed")
        except Exception as e:
            # Silently handle close errors
            pass
    
    def convert(self, create_docs=True):
        """Run complete conversion process"""
        try:
            self.load_csv()
            self.create_database()
            self.import_data()
            self.create_indexes()
            self.create_metadata_table()
            stats = self.get_statistics()
            self.get_schema()
            if create_docs:
                self.create_documentation()
            
            return True, stats
        
        except Exception as e:
            self._print(f"\n[ERROR] Conversion failed: {str(e)}")
            logging.error(f"Exception: {type(e).__name__}: {str(e)}")
            return False, None
        
        finally:
            # Always close connection, even on error (MAJOR-2 FIX)
            self.close()


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description='Convert CSV to SQLite database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python csv_to_sqlite.py mydata.csv
  python csv_to_sqlite.py data.csv -o mydb.db -t mytable
  python csv_to_sqlite.py data.csv --quiet
        '''
    )
    
    parser.add_argument('csv_file', help='Input CSV file')
    parser.add_argument('-o', '--output', help='Output SQLite database file')
    parser.add_argument('-t', '--table', default='data', help='Table name (default: data)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output messages')
    
    args = parser.parse_args()
    
    try:
        # Validate table name upfront (KRİTİK-2 FIX)
        CSVtoSQLite._validate_table_name(args.table)
        
        converter = CSVtoSQLite(
            csv_file=args.csv_file,
            db_file=args.output,
            table_name=args.table,
            verbose=not args.quiet
        )
        
        success, stats = converter.convert()
        
        if success:
            print(f"\n{'='*80}")
            print(f"[SUCCESS] CSV to SQLite conversion complete!")
            print(f"{'='*80}")
            print(f"\nDatabase: {converter.db_file}")
            if stats:
                print(f"Records: {stats['records']:,}")
                print(f"Columns: {stats['columns']}")
                print(f"Size: {stats['size_mb']:.1f} MB")
            
            sys.exit(0)  # MİNOR-6 FIX
        else:
            print(f"\n{'='*80}")
            print(f"[FAILED] Conversion failed. See errors above.")
            print(f"{'='*80}")
            
            sys.exit(1)  # MİNOR-6 FIX
    
    except ValueError as e:
        print(f"[ERROR] Invalid input: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n[INTERRUPTED] Conversion cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}", file=sys.stderr)
        logging.exception("Fatal error during conversion")
        sys.exit(1)


if __name__ == '__main__':
    main()
