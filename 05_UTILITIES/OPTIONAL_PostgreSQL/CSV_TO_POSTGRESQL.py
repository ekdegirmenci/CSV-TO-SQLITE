#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV to PostgreSQL Database Converter
Automatic encoding detection, metadata generation, and documentation
"""

import pandas as pd
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import time

try:
    import psycopg2
    from psycopg2 import sql, Error
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

class CSVtoPostgreSQL:
    """Convert CSV files to PostgreSQL database with auto-detection and metadata"""
    
    def __init__(self, csv_file, db_host='localhost', db_name='csv_data', 
                 db_user='postgres', db_password='postgres', db_port=5432, 
                 table_name=None, chunk_size=1000):
        """
        Initialize PostgreSQL converter
        
        Args:
            csv_file: Path to CSV file
            db_host: PostgreSQL host (default: localhost)
            db_name: Database name (default: csv_data)
            db_user: Database user (default: postgres)
            db_password: Database password (default: postgres)
            db_port: Database port (default: 5432)
            table_name: Target table name (auto-generated if None)
            chunk_size: Rows per batch insert (default: 1000)
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")
        
        self.csv_file = Path(csv_file)
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port
        self.chunk_size = chunk_size
        
        if table_name is None:
            table_name = self.csv_file.stem.lower().replace('-', '_').replace(' ', '_')
        self.table_name = table_name
        
        self.conn = None
        self.cursor = None
        self.df = None
        self.stats = {}
        self.start_time = None
        
        print(f"[INIT] PostgreSQL Converter initialized")
        print(f"       CSV File: {self.csv_file.name}")
        print(f"       Target Table: {self.table_name}")
        print(f"       Connection: {db_user}@{db_host}:{db_port}/{db_name}")
    
    def connect_to_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
                connect_timeout=5
            )
            self.cursor = self.conn.cursor()
            print(f"[DB] Connected to PostgreSQL successfully")
            return True
        except Error as e:
            print(f"[ERROR] PostgreSQL connection failed: {e}")
            return False
    
    def load_csv(self):
        """Load CSV with automatic encoding detection"""
        print(f"\n[CSV] Loading '{self.csv_file.name}'...")
        
        if not self.csv_file.exists():
            print(f"[ERROR] File not found: {self.csv_file}")
            return False
        
        file_size = self.csv_file.stat().st_size / 1024 / 1024
        print(f"       File size: {file_size:.1f} MB")
        
        # Try encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-9']
        
        for encoding in encodings:
            try:
                self.df = pd.read_csv(self.csv_file, encoding=encoding, low_memory=False)
                print(f"       ✓ Loaded with encoding: {encoding}")
                print(f"       ✓ Shape: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
                
                self.stats['rows'] = self.df.shape[0]
                self.stats['columns'] = self.df.shape[1]
                self.stats['encoding'] = encoding
                
                return True
            except Exception:
                continue
        
        print(f"[ERROR] Could not load CSV with any encoding")
        return False
    
    def create_table(self):
        """Create table in PostgreSQL with appropriate data types"""
        print(f"\n[SQL] Creating table '{self.table_name}'...")
        
        # Drop existing table
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {self.table_name} CASCADE;")
            self.conn.commit()
            print(f"       ✓ Dropped existing table if exists")
        except Error as e:
            print(f"       Warning: Could not drop existing table: {e}")
        
        # Generate column definitions with appropriate types
        col_defs = []
        for col in self.df.columns:
            # Sanitize column name
            safe_col = col.replace(' ', '_').replace('-', '_').replace('.', '_').lower()
            
            # Infer type
            if self.df[col].dtype == 'object':
                col_type = 'TEXT'
            elif self.df[col].dtype == 'int64':
                col_type = 'BIGINT'
            elif self.df[col].dtype == 'float64':
                col_type = 'NUMERIC'
            elif self.df[col].dtype == 'bool':
                col_type = 'BOOLEAN'
            else:
                col_type = 'TEXT'
            
            col_defs.append(f'"{safe_col}" {col_type}')
        
        # Create table
        create_sql = f"""
        CREATE TABLE {self.table_name} (
            id SERIAL PRIMARY KEY,
            {', '.join(col_defs)}
        );
        """
        
        try:
            self.cursor.execute(create_sql)
            self.conn.commit()
            print(f"       ✓ Table created with {len(col_defs)} columns")
            return True
        except Error as e:
            print(f"[ERROR] Table creation failed: {e}")
            return False
    
    def import_data(self):
        """Import CSV data into PostgreSQL"""
        print(f"\n[IMPORT] Importing {len(self.df):,} rows...")
        
        # Prepare data
        self.df = self.df.fillna('NULL')
        
        # Get columns
        cols = [col.replace(' ', '_').replace('-', '_').replace('.', '_').lower() 
                for col in self.df.columns]
        col_str = ', '.join([f'"{col}"' for col in cols])
        
        # Insert in chunks
        total_rows = len(self.df)
        imported = 0
        
        for i in range(0, total_rows, self.chunk_size):
            chunk = self.df.iloc[i:i + self.chunk_size]
            
            try:
                for _, row in chunk.iterrows():
                    values = [str(v) if v != 'NULL' else None for v in row]
                    placeholders = ', '.join(['%s'] * len(values))
                    
                    insert_sql = f"INSERT INTO {self.table_name} ({col_str}) VALUES ({placeholders})"
                    self.cursor.execute(insert_sql, values)
                
                self.conn.commit()
                imported += len(chunk)
                
                pct = (imported / total_rows) * 100
                print(f"\r       Progress: {imported:,}/{total_rows:,} ({pct:.1f}%)", end='')
            
            except Error as e:
                print(f"\n[ERROR] Import failed at row {i}: {e}")
                self.conn.rollback()
                return False
        
        print(f"\n       ✓ Imported {imported:,} rows successfully")
        self.stats['imported'] = imported
        return True
    
    def create_indexes(self):
        """Create indexes on key columns"""
        print(f"\n[INDEX] Creating indexes...")
        
        # Identify string and numeric columns for indexing
        string_cols = []
        numeric_cols = []
        
        for col in self.df.columns[:15]:  # First 15 columns
            safe_col = col.replace(' ', '_').replace('-', '_').replace('.', '_').lower()
            if self.df[col].dtype == 'object':
                string_cols.append(safe_col)
            else:
                numeric_cols.append(safe_col)
        
        # Create indexes
        indexes_created = 0
        
        try:
            # String column indexes
            for col in string_cols[:5]:
                idx_name = f"idx_{self.table_name}_{col[:20]}"
                self.cursor.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON {self.table_name} ("{col}");')
                indexes_created += 1
            
            # Numeric column indexes
            for col in numeric_cols[:3]:
                idx_name = f"idx_{self.table_name}_{col[:20]}"
                self.cursor.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON {self.table_name} ("{col}");')
                indexes_created += 1
            
            self.conn.commit()
            print(f"       ✓ Created {indexes_created} indexes")
            self.stats['indexes'] = indexes_created
            return True
        except Error as e:
            print(f"       Warning: Index creation incomplete: {e}")
            return True  # Don't fail if indexing fails
    
    def create_metadata_table(self):
        """Create metadata table with column statistics"""
        print(f"\n[META] Creating metadata table...")
        
        try:
            # Drop existing metadata table
            self.cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}_metadata CASCADE;")
            
            # Create metadata table
            create_meta_sql = f"""
            CREATE TABLE {self.table_name}_metadata (
                column_name TEXT,
                data_type TEXT,
                non_null_count INTEGER,
                null_count INTEGER,
                null_percentage NUMERIC,
                unique_values INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(create_meta_sql)
            
            # Insert metadata
            for col in self.df.columns:
                safe_col = col.replace(' ', '_').replace('-', '_').replace('.', '_').lower()
                
                non_null = self.df[col].notna().sum()
                null_count = self.df[col].isna().sum()
                null_pct = (null_count / len(self.df)) * 100
                unique_vals = self.df[col].nunique()
                dtype = str(self.df[col].dtype)
                
                insert_meta_sql = f"""
                INSERT INTO {self.table_name}_metadata 
                (column_name, data_type, non_null_count, null_count, null_percentage, unique_values)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                self.cursor.execute(insert_meta_sql, 
                    (col, dtype, int(non_null), int(null_count), float(null_pct), int(unique_vals)))
            
            self.conn.commit()
            print(f"       ✓ Metadata table created with {len(self.df.columns)} column definitions")
            self.stats['metadata_rows'] = len(self.df.columns)
            return True
        except Error as e:
            print(f"       Warning: Metadata creation failed: {e}")
            return True
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            # Table size
            self.cursor.execute(f"""
            SELECT pg_size_pretty(pg_total_relation_size('{self.table_name}'))
            """)
            size = self.cursor.fetchone()[0]
            
            # Record count
            self.cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = self.cursor.fetchone()[0]
            
            print(f"\n[STATS]")
            print(f"       Table Size: {size}")
            print(f"       Record Count: {count:,}")
            
            self.stats['table_size'] = size
            self.stats['final_count'] = count
            
        except Error as e:
            print(f"       Could not retrieve statistics: {e}")
    
    def create_documentation(self):
        """Generate documentation file"""
        doc_file = Path(f"{self.table_name}_DOCUMENTATION.txt")
        
        doc_content = f"""
PostgreSQL DATABASE DOCUMENTATION
Generated: {datetime.now().isoformat()}
Source File: {self.csv_file.name}
Target Table: {self.table_name}

{'='*80}
DATABASE CONNECTION
{'='*80}
Host: {self.db_host}
Port: {self.db_port}
Database: {self.db_name}
User: {self.db_user}

{'='*80}
TABLE INFORMATION
{'='*80}
Table Name: {self.table_name}
Records: {self.stats.get('imported', 'N/A'):,}
Columns: {self.stats.get('columns', 'N/A')}
Table Size: {self.stats.get('table_size', 'N/A')}

{'='*80}
IMPORT STATISTICS
{'='*80}
Source File Size: {self.csv_file.stat().st_size / 1024 / 1024:.1f} MB
Encoding Detected: {self.stats.get('encoding', 'utf-8')}
Rows Imported: {self.stats.get('imported', 'N/A'):,}
Indexes Created: {self.stats.get('indexes', 'N/A')}

{'='*80}
COLUMN DEFINITIONS
{'='*80}
"""
        
        # Add column info
        try:
            self.cursor.execute(f"SELECT * FROM {self.table_name}_metadata ORDER BY column_name")
            metadata = self.cursor.fetchall()
            
            doc_content += "\n"
            for row in metadata:
                col_name, dtype, non_null, null_count, null_pct, unique_vals = row[:6]
                doc_content += f"{col_name:40s} {dtype:15s} Nulls: {null_pct:5.1f}% Unique: {unique_vals:6d}\n"
        except:
            pass
        
        doc_content += f"""

{'='*80}
SAMPLE QUERIES
{'='*80}

-- Row count
SELECT COUNT(*) FROM {self.table_name};

-- First 10 records
SELECT * FROM {self.table_name} LIMIT 10;

-- Column statistics
SELECT column_name, non_null_count, null_percentage, unique_values 
FROM {self.table_name}_metadata 
ORDER BY null_percentage DESC LIMIT 10;

-- Distinct values in first column
SELECT COUNT(DISTINCT {list(self.df.columns)[0].replace('"', '')}), 
       COUNT(*) as total,
       COUNT({list(self.df.columns)[0].replace('"', '')}) as filled
FROM {self.table_name};

{'='*80}
PYTHON CONNECTION EXAMPLE
{'='*80}

import psycopg2

conn = psycopg2.connect(
    host="{self.db_host}",
    database="{self.db_name}",
    user="{self.db_user}",
    password="YOUR_PASSWORD",
    port={self.db_port}
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM {self.table_name} LIMIT 5")
results = cursor.fetchall()

for row in results:
    print(row)

cursor.close()
conn.close()

EOF
"""
        
        try:
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            print(f"\n[DOC] Documentation created: {doc_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Could not create documentation: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print(f"\n[CLOSE] Database connection closed")
    
    def convert(self):
        """Execute full conversion pipeline"""
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("CSV TO POSTGRESQL CONVERSION PIPELINE")
        print("="*80)
        
        # Step 1: Load CSV
        if not self.load_csv():
            return False, {}
        
        # Step 2: Connect to database
        if not self.connect_to_db():
            return False, self.stats
        
        # Step 3: Create table
        if not self.create_table():
            self.close()
            return False, self.stats
        
        # Step 4: Import data
        if not self.import_data():
            self.close()
            return False, self.stats
        
        # Step 5: Create indexes
        self.create_indexes()
        
        # Step 6: Create metadata
        self.create_metadata_table()
        
        # Step 7: Get statistics
        self.get_statistics()
        
        # Step 8: Create documentation
        self.create_documentation()
        
        # Cleanup
        self.close()
        
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("CONVERSION COMPLETE")
        print("="*80)
        print(f"\nElapsed Time: {elapsed:.1f} seconds")
        print(f"Speed: {(self.stats.get('imported', 0) / elapsed):.0f} rows/second")
        print(f"\nTarget Database: {self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}")
        print(f"Target Table: {self.table_name}")
        print(f"Records Imported: {self.stats.get('imported', 0):,}")
        
        return True, self.stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert CSV to PostgreSQL Database')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('-o', '--output', dest='db_name', default='csv_data', help='Database name (default: csv_data)')
    parser.add_argument('-t', '--table', dest='table_name', help='Table name (auto-generated if not provided)')
    parser.add_argument('-H', '--host', dest='db_host', default='localhost', help='PostgreSQL host (default: localhost)')
    parser.add_argument('-P', '--port', dest='db_port', type=int, default=5432, help='PostgreSQL port (default: 5432)')
    parser.add_argument('-u', '--user', dest='db_user', default='postgres', help='Database user (default: postgres)')
    parser.add_argument('-p', '--password', dest='db_password', default='postgres', help='Database password (default: postgres)')
    
    args = parser.parse_args()
    
    if not PSYCOPG2_AVAILABLE:
        print("ERROR: psycopg2 not installed")
        print("Install with: pip install psycopg2-binary")
        sys.exit(1)
    
    converter = CSVtoPostgreSQL(
        args.csv_file,
        db_host=args.db_host,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        db_port=args.db_port,
        table_name=args.table_name
    )
    
    success, stats = converter.convert()
    sys.exit(0 if success else 1)
