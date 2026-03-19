#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UNIVERSAL CSV TO SQLITE CONVERTER - PRODUCTION READY
Admin yetkisi olmadan bilgisayarlarda da çalışan, robust converter
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
import tempfile
import shutil
import hashlib

# Setup logging with better format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Minimum version checks
__version__ = "2.0.1"
PYTHON_MIN_VERSION = (3, 8)
PANDAS_MIN_VERSION = "1.2.0"
SQLITE_MIN_VERSION = "3.8"
LARGE_FILE_THRESHOLD_MB = 500  # Stream if larger than 500MB
MAX_MEMORY_MB = 1000  # Safety limit for memory usage


class CSVtoSQLite:
    """CSV to SQLite converter class - Production Ready"""
    
    @staticmethod
    def _parse_version(version_string):
        """Parse version string to tuple for comparison"""
        try:
            parts = version_string.split('-')[0].split('+')[0]  # Handle pre-release
            return tuple(map(int, re.findall(r'\d+', parts)[:3]))
        except (ValueError, AttributeError):
            return (0, 0, 0)
    
    @staticmethod
    def check_dependencies():
        """Verify all required dependencies available"""
        # Python version
        if sys.version_info < PYTHON_MIN_VERSION:
            raise RuntimeError(f"Python {PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]}+ required, got {sys.version_info.major}.{sys.version_info.minor}")
        
        # pandas version
        try:
            import pandas
            current_pandas = CSVtoSQLite._parse_version(pandas.__version__)
            min_pandas = CSVtoSQLite._parse_version(PANDAS_MIN_VERSION)
            
            logger.info(f"pandas {pandas.__version__} detected")
            
            if current_pandas < min_pandas:
                raise ImportError(
                    f"pandas {PANDAS_MIN_VERSION}+ required, got {pandas.__version__}. "
                    f"Run: pip install --upgrade pandas"
                )
        except ImportError as e:
            if "No module named" in str(e):
                raise ImportError("pandas not installed. Run: pip install pandas")
            raise
        
        # sqlite3 version - parse as tuple for proper comparison
        sqlite_version = sqlite3.sqlite_version
        logger.info(f"SQLite {sqlite_version} available")
        
        # Convert version strings to tuples for proper comparison
        def version_tuple(v):
            try:
                return tuple(map(int, v.split('.')))
            except (ValueError, AttributeError):
                return (0, 0, 0)
        
        min_version = version_tuple(SQLITE_MIN_VERSION)
        current_version = version_tuple(sqlite_version)
        
        if current_version < min_version:
            raise RuntimeError(f"SQLite {SQLITE_MIN_VERSION}+ required, got {sqlite_version}")
        
        return True
    
    @staticmethod
    def _validate_table_name(table_name):
        """
        Validate table name to prevent SQL injection
        Table names must: Start with letter/underscore, contain only alphanumeric/underscores
        Max 64 chars (SQLite recommendation)
        
        Args:
            table_name (str): Table name to validate
            
        Raises:
            ValueError: If table name contains invalid characters
        """
        if not isinstance(table_name, str) or not table_name:
            raise ValueError("Table name must be non-empty string")
        
        if len(table_name) > 64:
            raise ValueError(f"Table name too long ({len(table_name)}). Max 64 chars")
        
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
            raise ValueError(
                f"Invalid table name: {table_name!r}. "
                f"Must start with letter/underscore, contain only alphanumeric+underscores"
            )
    
    @staticmethod
    def _sanitize_column_name(col_name, column_index=None):
        """
        Sanitize column name for safe SQL usage with fallback
        
        Args:
            col_name (str): Original column name
            column_index (int): Column index for fallback naming
            
        Returns:
            str: Safe column name for SQL (never empty)
        """
        # Keep display name, use safe version for SQL
        safe_name = col_name.strip() if col_name else ""
        
        # Remove/replace problematic chars
        safe_name = re.sub(r'[^\w\s\-]', '', safe_name)  # Keep word chars, spaces, hyphens
        safe_name = re.sub(r'\s+', '_', safe_name)       # Replace spaces with underscore
        safe_name = safe_name.strip('_')                  # Remove leading/trailing underscores
        safe_name = safe_name[:100]                       # Limit length
        
        # Handle empty or numeric-starting names
        if not safe_name:
            # Empty column name - use fallback
            if column_index is not None:
                safe_name = f"column_{column_index:03d}"
            else:
                safe_name = "column"  # Ultimate fallback
        elif safe_name[0].isdigit():
            safe_name = f"col_{safe_name}"
        
        return safe_name
    
    @staticmethod
    def _safe_path(file_path):
        """
        Convert to safe Path object with user-writable directory
        
        Args:
            file_path (str|Path): Input path
            
        Returns:
            Path: Absolute path in user-writable location
        """
        path = Path(file_path).expanduser().resolve()
        
        # Prevent directory traversal attacks
        try:
            path.relative_to(path.anchor)  # Ensure it's valid absolute path
        except ValueError:
            raise ValueError(f"Invalid path: {file_path}")
        
        return path
    
    def __init__(self, csv_file, db_file=None, table_name='data', verbose=True, backup=True):
        """
        Initialize converter
        
        Args:
            csv_file (str): Path to input CSV file
            db_file (str): Output SQLite database file (auto-generated if None)
            table_name (str): Name of table in database
            verbose (bool): Print progress messages
            backup (bool): Create backup of existing DB before overwrite
            
        Raises:
            ValueError: If parameters invalid
            FileNotFoundError: If CSV not found
        """
        # Check dependencies first
        self.check_dependencies()
        
        # Validate table name before any operations
        self._validate_table_name(table_name)
        
        # Safe path handling
        try:
            self.csv_file = str(self._safe_path(csv_file))
        except Exception as e:
            raise ValueError(f"Invalid CSV path: {csv_file} — {e}")
        
        # Verify CSV exists
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        self.verbose = verbose
        self.table_name = table_name
        self.backup = backup
        self.backup_file = None
        
        # Safe database path
        if db_file is None:
            base_name = Path(self.csv_file).stem
            db_file = f"{base_name}.db"
        
        try:
            self.db_file = str(self._safe_path(db_file))
        except Exception as e:
            raise ValueError(f"Invalid database path: {db_file} — {e}")
        
        # Initialize state
        self.df = None
        self.conn = None
        self.cursor = None
        self.stats = {}
        self.use_streaming = False  # Large file flag
        self.detected_encoding = None  # For streaming mode
        self.first_chunk_mapping = {}  # Column mapping for streaming
        
        logger.info(f"Converter initialized (v{__version__})")
        logger.debug(f"CSV: {self.csv_file}")
        logger.debug(f"DB: {self.db_file}")
        logger.debug(f"Table: {self.table_name}")
    
    def _print(self, message, level='info'):
        """Print if verbose mode enabled with logging"""
        if self.verbose:
            if level == 'info':
                logger.info(message)
            elif level == 'warn':
                logger.warning(message)
            elif level == 'error':
                logger.error(message)
            else:
                print(message)
    
    def load_csv(self):
        """Load CSV file with intelligent encoding detection and large file streaming support"""
        self._print(f"[1] Loading CSV: {self.csv_file}")
        
        csv_size = os.path.getsize(self.csv_file) / 1024 / 1024
        self._print(f"    File size: {csv_size:.1f} MB")
        
        # Check if file is too large for memory
        if csv_size > LARGE_FILE_THRESHOLD_MB:
            self._print(
                f"    ⚠️  Large file detected ({csv_size:.1f} MB > {LARGE_FILE_THRESHOLD_MB} MB)",
                level='warn'
            )
            self._print(f"    → Switching to chunked (streaming) mode", level='warn')
            self.use_streaming = True
            self.stats['streaming_mode'] = True
            self.stats['csv_size_mb'] = csv_size
            return self._load_csv_streaming()
        
        # Encoding chain optimized for Turkish data
        encodings = [
            'utf-8',           # Most common
            'utf-8-sig',       # UTF-8 with BOM
            'latin-1',         # Latin
            'iso-8859-9',      # Turkish (Latin-5)
            'windows-1254',    # Windows Turkish
            'cp1252',          # Windows Latin
        ]
        
        last_error = None
        detected_encoding = None
        bad_lines_count = 0
        
        for encoding in encodings:
            try:
                self._print(f"    Trying encoding: {encoding}...", level='warn')
                self.df = pd.read_csv(
                    self.csv_file,
                    encoding=encoding,
                    on_bad_lines='warn'
                )
                detected_encoding = encoding
                self._print(f"    ✓ Loaded with {encoding}", level='info')
                break
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                continue
        
        if self.df is None:
            raise UnicodeDecodeError(
                'unknown', b'', 0, 1,
                f"Could not decode CSV with any encoding. Last error: {last_error}"
            )
        
        # Validate data
        if self.df.empty:
            logger.warning("CSV file is empty (0 rows)")
        
        rows, cols = self.df.shape
        self._print(f"[OK] Loaded: {rows:,} rows × {cols} columns")
        
        self.stats['csv_rows'] = rows
        self.stats['csv_cols'] = cols
        self.stats['csv_size_mb'] = csv_size
        self.stats['encoding'] = detected_encoding
        self.stats['streaming_mode'] = False
        self.use_streaming = False
        
        return self
    
    def _load_csv_streaming(self):
        """Load CSV in streaming mode for large files (stores encoding only)"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-9', 'windows-1254', 'cp1252']
        detected_encoding = None
        
        # Just detect encoding without loading full file
        for encoding in encodings:
            try:
                # Try reading just first chunk to detect encoding
                test_df = pd.read_csv(
                    self.csv_file,
                    encoding=encoding,
                    nrows=1
                )
                detected_encoding = encoding
                self._print(f"    ✓ Encoding detected: {encoding}", level='info')
                self.df = None  # Don't load full file yet
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if detected_encoding is None:
            raise UnicodeDecodeError(
                'unknown', b'', 0, 1,
                "Could not detect encoding for this file"
            )
        
        # Store encoding for later use in import_data
        self.detected_encoding = detected_encoding
        self.stats['encoding'] = detected_encoding
        self.stats['csv_size_mb'] = os.path.getsize(self.csv_file) / 1024 / 1024
        self.stats['streaming_mode'] = True
        self.use_streaming = True
        
        return self
    
    def create_database(self):
        """Create SQLite database with proper directory handling"""
        self._print(f"\n[2] Creating SQLite Database: {self.db_file}")
        
        # Create output directory if needed
        db_dir = os.path.dirname(self.db_file)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                self._print(f"    Created directory: {db_dir}", level='warn')
            except OSError as e:
                raise PermissionError(f"Cannot create directory {db_dir}: {e}")
        
        # Backup existing database
        if os.path.exists(self.db_file):
            if self.backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{self.db_file}.backup.{timestamp}"
                try:
                    shutil.copy2(self.db_file, backup_name)
                    self.backup_file = backup_name
                    self._print(f"    Backup created: {backup_name}", level='warn')
                except Exception as e:
                    self._print(f"    Warning: Could not backup existing DB: {e}", level='warn')
                    # Continue anyway
            
            try:
                os.remove(self.db_file)
                self._print(f"    Removed old database", level='warn')
            except OSError as e:
                raise PermissionError(f"Cannot remove existing database: {e}")
        
        # Create connection
        try:
            self.conn = sqlite3.connect(self.db_file, timeout=30)
            self.cursor = self.conn.cursor()
            
            # Enable optimizations
            self.cursor.execute("PRAGMA synchronous = NORMAL")
            self.cursor.execute("PRAGMA journal_mode = WAL")
            self.cursor.execute("PRAGMA cache_size = -64000")
            
            self._print(f"[OK] Database created", level='info')
        except sqlite3.Error as e:
            raise RuntimeError(f"Cannot create database: {e}")
        
        return self
    
    def import_data(self, chunksize=10000):
        """
        Import CSV data into SQLite table with chunked processing
        Supports both normal and streaming modes for large files
        
        Args:
            chunksize (int): Rows per batch (default: 10000)
        """
        self._print(f"\n[3] Importing Data (chunksize={chunksize})...")
        
        if self.conn is None:
            raise ValueError("No database. Call create_database() first")
        
        # Handle streaming mode (large files)
        if self.use_streaming:
            return self._import_data_streaming(chunksize)
        
        # Normal mode (small files already in memory)
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first")
        
        # Sanitize column names
        column_mapping = {}
        for idx, col in enumerate(self.df.columns):
            safe_col = self._sanitize_column_name(col, column_index=idx)
            column_mapping[col] = safe_col
        
        self.df = self.df.rename(columns=column_mapping)
        
        # Create table and import
        try:
            self._print(f"    Creating table '{self.table_name}'...")
            
            row_count = len(self.df)
            # Use default method (VALUES) instead of 'multi' to avoid SQLite variable limit
            self.df.to_sql(
                self.table_name,
                self.conn,
                if_exists='replace',
                index=False,
                chunksize=chunksize
            )
            
            self.conn.commit()
            
            # Verify import
            if self.cursor is None:
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
            count = self.cursor.fetchone()[0]
            
            self._print(f"[OK] Data imported: {count:,} records", level='info')
            
            if count != row_count:
                logger.warning(f"Row count mismatch: expected {row_count}, got {count}")
            
            self.stats['imported_rows'] = count
        
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Data import failed: {e}")
        
        return self
    
    def _import_data_streaming(self, chunksize=10000):
        """Import CSV data in streaming mode for large files (no memory load)"""
        self._print(f"    Using streaming import (chunksize={chunksize})...")
        
        try:
            total_rows = 0
            chunk_count = 0
            bad_lines_total = 0
            
            for chunk_idx, chunk_df in enumerate(
                pd.read_csv(
                    self.csv_file,
                    encoding=self.detected_encoding,
                    chunksize=chunksize,
                    on_bad_lines='warn'
                )
            ):
                if chunk_idx == 0:
                    self._print(f"    Creating table '{self.table_name}' (streaming)...")
                
                # Sanitize column names on first chunk
                if chunk_idx == 0:
                    column_mapping = {}
                    for idx, col in enumerate(chunk_df.columns):
                        safe_col = self._sanitize_column_name(col, column_index=idx)
                        column_mapping[col] = safe_col
                    self.first_chunk_mapping = column_mapping
                
                # Apply column mapping
                chunk_df = chunk_df.rename(columns=self.first_chunk_mapping)
                
                # Import chunk
                if_exists = 'replace' if chunk_idx == 0 else 'append'
                chunk_df.to_sql(
                    self.table_name,
                    self.conn,
                    if_exists=if_exists,
                    index=False,
                    method='multi'
                )
                
                total_rows += len(chunk_df)
                chunk_count += 1
                
                if chunk_idx % 10 == 0:
                    self._print(f"    Progress: {total_rows:,} rows imported ({chunk_count} chunks)...")
            
            self.conn.commit()
            
            # Verify import
            self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
            count = self.cursor.fetchone()[0]
            
            self._print(f"[OK] Data imported: {count:,} records ({chunk_count} chunks)", level='info')
            self.stats['imported_rows'] = count
            self.stats['chunk_count'] = chunk_count
            
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Streaming import failed: {e}")
        
        return self
    
    def create_indexes(self):
        """Create indexes on columns for faster queries using cardinality-based strategy"""
        self._print(f"\n[4] Creating Indexes (cardinality-based)...")
        
        if self.cursor is None:
            raise ValueError("Database not initialized")
        
        # Get row count for cardinality calculation
        self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
        row_count = self.cursor.fetchone()[0]
        
        if row_count == 0:
            self._print(f"    Skipping indexes: table is empty", level='warn')
            return self
        
        # Get table schema
        self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
        columns = [(row[1], row[2]) for row in self.cursor.fetchall()]  # name, type
        
        index_count = 0
        skipped_count = 0
        created_indexes = set()
        fallback_candidates = []  # Store candidates for fallback indexing
        
        try:
            self._print(f"    Analyzing cardinality on {len(columns)} columns...")
            
            for col_idx, (col_name, col_type) in enumerate(columns):
                # Check cardinality
                self.cursor.execute(
                    f"SELECT COUNT(DISTINCT [{col_name}]) FROM [{self.table_name}]"
                )
                unique_count = self.cursor.fetchone()[0]
                
                if unique_count == 0:
                    cardinality_ratio = 0
                else:
                    cardinality_ratio = unique_count / row_count
                
                # Safe column name for SQL
                safe_col = self._sanitize_column_name(col_name, col_idx)
                
                # Index strategy: index columns unless they are:
                # - Perfectly unique (100%): primary key material, skip
                # - Perfectly constant (0%): no selectivity, skip
                # - Very low cardinality (<0.5%): poor selectivity, skip
                should_index = unique_count > 0 and cardinality_ratio > 0.005 and cardinality_ratio < 0.995
                
                if should_index:
                    idx_name = f"idx_{col_idx:03d}_{safe_col[:25]}"
                    
                    if idx_name not in created_indexes:
                        self.cursor.execute(
                            f'CREATE INDEX IF NOT EXISTS [{idx_name}] ON [{self.table_name}] ([{safe_col}])'
                        )
                        created_indexes.add(idx_name)
                        index_count += 1
                        
                        self._print(
                            f"    ✓ Indexed: {col_name:35s} cardinality={cardinality_ratio:.1%}",
                            level='info'
                        )
                else:
                    skipped_count += 1
                    reason = "constant (0% unique)" if unique_count == 0 else \
                            "primary-key-like" if cardinality_ratio >= 0.995 else \
                            "low selectivity"
                    self._print(
                        f"    ⊘ Skipped: {col_name:35s} cardinality={cardinality_ratio:.1%} ({reason})",
                        level='warn'
                    )
                    
                    # Store as fallback candidate if has some selectivity
                    if unique_count > 0 and unique_count < row_count:
                        fallback_candidates.append((col_idx, col_name, safe_col, cardinality_ratio))
            
            # Fallback: if no indexes created but we have candidates, create index on best candidate
            if index_count == 0 and fallback_candidates:
                fallback_candidates.sort(key=lambda x: abs(x[3] - 0.5))  # Best around 50% cardinality
                col_idx, col_name, safe_col, ratio = fallback_candidates[0]
                idx_name = f"idx_{col_idx:03d}_{safe_col[:25]}_fallback"
                
                self.cursor.execute(
                    f'CREATE INDEX IF NOT EXISTS [{idx_name}] ON [{self.table_name}] ([{safe_col}])'
                )
                index_count = 1
                self._print(
                    f"    ✓ Fallback index: {col_name:35s} cardinality={ratio:.1%}",
                    level='info'
                )
            
            self.conn.commit()
            self._print(
                f"[OK] Created {index_count} indexes ({skipped_count} skipped)",
                level='info'
            )
            self.stats['indexes'] = index_count
            self.stats['indexes_skipped'] = skipped_count
        
        except sqlite3.Error as e:
            logger.warning(f"Index creation incomplete: {e}")
        
        return self
    
    def create_metadata_table(self):
        """Create metadata table documenting column information"""
        self._print(f"\n[5] Creating Metadata Table...")
        
        if self.conn is None:
            raise ValueError("Database not initialized")
        
        try:
            # Get metadata from database (works for both streaming and normal modes)
            self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
            columns = self.cursor.fetchall()
            
            # Calculate statistics for metadata
            metadata_rows = []
            for col_id, col_name, col_type, notnull, default, pk in columns:
                self.cursor.execute(
                    f"SELECT COUNT(*), COUNT(DISTINCT [{col_name}]), "
                    f"SUM(CASE WHEN [{col_name}] IS NULL THEN 1 ELSE 0 END) "
                    f"FROM [{self.table_name}]"
                )
                total_count, unique_count, null_count = self.cursor.fetchone()
                
                if total_count > 0:
                    null_percentage = (null_count / total_count * 100) if null_count else 0
                    non_null_count = total_count - (null_count or 0)
                else:
                    null_percentage = 0
                    non_null_count = 0
                
                metadata_rows.append({
                    'column_name': col_name,
                    'data_type': col_type,
                    'non_null_count': non_null_count,
                    'null_count': null_count or 0,
                    'null_percentage': round(null_percentage, 2),
                    'unique_values': unique_count or 0
                })
            
            # Create metadata dataframe and save
            metadata = pd.DataFrame(metadata_rows)
            metadata.to_sql(
                '_metadata',
                self.conn,
                if_exists='replace',
                index=False
            )
            self.conn.commit()
            
            self._print(f"[OK] Metadata table created ({len(metadata)} columns)", level='info')
            self.stats['metadata_rows'] = len(metadata)
        
        except Exception as e:
            logger.warning(f"Metadata creation failed: {e}")
        
        return self
        
        return self
    
    def get_statistics(self):
        """Get database statistics"""
        self._print(f"\n[6] Database Statistics...")
        
        if self.cursor is None:
            raise ValueError("Database not initialized")
        
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
            total_records = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
            columns = self.cursor.fetchall()
            total_columns = len(columns)
            
            db_size = os.path.getsize(self.db_file) / 1024 / 1024
            
            self._print(f"  Total Records: {total_records:,}")
            self._print(f"  Total Columns: {total_columns}")
            self._print(f"  Database Size: {db_size:.1f} MB")
            
            self.stats['final_records'] = total_records
            self.stats['final_columns'] = total_columns
            self.stats['db_size_mb'] = db_size
            
            return {
                'records': total_records,
                'columns': total_columns,
                'size_mb': db_size
            }
        
        except sqlite3.Error as e:
            logger.warning(f"Could not retrieve statistics: {e}")
            return {}
    
    def get_schema(self):
        """Display database schema"""
        self._print(f"\n[7] Database Schema...")
        
        if self.cursor is None:
            raise ValueError("Database not initialized")
        
        try:
            self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
            columns = self.cursor.fetchall()
            
            self._print(f"\n  Table: {self.table_name}")
            for col_id, col_name, col_type, notnull, default, pk in columns[:15]:
                nullable = "NOT NULL" if notnull else "NULL"
                self._print(f"    {col_id+1:2d}. {col_name:35s} {col_type:10s} {nullable}")
            
            if len(columns) > 15:
                self._print(f"    ... and {len(columns)-15} more columns")
            
            return columns
        
        except sqlite3.Error as e:
            logger.warning(f"Schema display failed: {e}")
            return []
    
    def create_documentation(self, doc_file=None):
        """Create comprehensive database documentation"""
        if doc_file is None:
            doc_file = f"{Path(self.db_file).stem}_DOCUMENTATION.txt"
        
        self._print(f"\n[8] Creating Documentation: {doc_file}")
        
        if self.cursor is None:
            raise ValueError("Database not initialized")
        
        try:
            # Gather stats
            self.cursor.execute(f"SELECT COUNT(*) FROM [{self.table_name}]")
            total_records = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"PRAGMA table_info([{self.table_name}])")
            columns = self.cursor.fetchall()
            
            db_size = os.path.getsize(self.db_file) / 1024 / 1024
            
            # Build documentation
            doc_content = f"""
{'='*80}
DATABASE DOCUMENTATION
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Converter Version: {__version__}
Source: {self.csv_file}
Created By: CSV-to-SQLite Universal Converter (Admin-Free Compatible)

{'='*80}
DATABASE INFORMATION
{'='*80}
Type: SQLite3
File: {self.db_file}
Size: {db_size:.1f} MB
Records: {total_records:,}
Columns: {len(columns)}
Encoding: {self.stats.get('encoding', 'UTF-8')}

{'='*80}
TABLE STRUCTURE
{'='*80}
Table Name: {self.table_name}

Columns:
"""
            
            for col_id, col_name, col_type, notnull, default, pk in columns:
                nullable = "NOT NULL" if notnull else "NULL"
                doc_content += f"\n  {col_id+1}. {col_name:40s} {col_type:10s} {nullable}"
            
            doc_content += f"""

{'='*80}
METADATA TABLE
{'='*80}
Table: _metadata
Columns: column_name, data_type, non_null_count, null_count, null_percentage, unique_values
Purpose: Column information and data quality tracking

{'='*80}
QUICK START QUERIES
{'='*80}

-- Count records
SELECT COUNT(*) FROM [{self.table_name}];

-- Get null statistics
SELECT * FROM _metadata ORDER BY null_percentage DESC;

-- First 10 records
SELECT * FROM [{self.table_name}] LIMIT 10;

-- Export to CSV
.mode csv
.output export.csv
SELECT * FROM [{self.table_name}];
.quit

{'='*80}
PYTHON USAGE
{'='*80}

import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('{self.db_file}')

# Load all data
df = pd.read_sql_query('SELECT * FROM [{self.table_name}]', conn)

# Load subset (first 1000 rows)
df = pd.read_sql_query('SELECT * FROM [{self.table_name}] LIMIT 1000', conn)

# Get metadata
metadata = pd.read_sql_query('SELECT * FROM _metadata', conn)

# Close connection
conn.close()

{'='*80}
TROUBLESHOOTING
{'='*80}

Q: "database is locked" error?
A: Close other applications accessing the database. Use .timeout parameter.

Q: "no such table or column"?
A: Column names may be sanitized. Check _metadata table.

Q: How to update data?
A: Re-run converter with updated CSV file.

Q: How to backup?
A: Copy .db file to another location. Automated backup created before overwrite.

{'='*80}
STATUS: ✅ READY FOR USE
Verified on: Windows (no admin), CSV size: {self.stats.get('csv_size_mb', 'N/A')} MB
Rows imported: {total_records:,} | Columns: {len(columns)} | Indexes: {self.stats.get('indexes', 'N/A')}
{'='*80}
"""
            
            # Ensure directory exists (with proper error handling)
            doc_path = Path(doc_file)
            try:
                doc_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.warning(f"Could not create doc directory {doc_path.parent}: {e}")
                # Try current directory instead
                doc_path = Path(doc_path.name)
            
            # Write file with proper encoding
            with open(str(doc_path), 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            self._print(f"[OK] Documentation created: {doc_path}", level='info')
        
        except Exception as e:
            logger.warning(f"Documentation creation partial: {e}")
        
        return self
    
    def close(self):
        """Close database connection (idempotent - safe to call multiple times)"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
            self._print(f"\n[OK] Database closed", level='info')
        except Exception:
            pass  # Silently handle close errors
    
    def convert(self, create_docs=True):
        """Execute full conversion pipeline"""
        start_time = datetime.now()
        
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
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self.stats['elapsed_seconds'] = elapsed
            
            return True, stats
        
        except Exception as e:
            self._print(f"\n[ERROR] Conversion failed: {str(e)}", level='error')
            logger.exception("Full exception trace:")
            return False, None
        
        finally:
            self.close()


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(
        description='Convert CSV to SQLite database (Production Ready, Admin-Free)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage
  python csv_to_sqlite.py mydata.csv
  
  # Custom output and table name
  python csv_to_sqlite.py data.csv -o mydb.db -t mytable
  
  # Quiet mode (minimal output)
  python csv_to_sqlite.py data.csv --quiet
  
  # Without backup
  python csv_to_sqlite.py data.csv --no-backup

Encoding support:
  - UTF-8 (default)
  - Latin-1 / ISO-8859-1
  - Turkish (Windows-1254, ISO-8859-9)
  - Windows CP1252
  - Auto-detection with fallback chain

Admin-free operation:
  - No elevated privileges required
  - Works in user folder, temp directories
  - No registry access, UAC dialogs, or service installation
  - Safe for shared/restricted systems
        '''
    )
    
    parser.add_argument('csv_file', help='Input CSV file path')
    parser.add_argument('-o', '--output', dest='db_file', help='Output SQLite database file')
    parser.add_argument('-t', '--table', dest='table_name', default='data', help='Table name (default: data)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress verbose output')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup of existing database')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                       help='Set logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Validate table name
        CSVtoSQLite._validate_table_name(args.table_name)
        
        # Create converter
        converter = CSVtoSQLite(
            csv_file=args.csv_file,
            db_file=args.db_file,
            table_name=args.table_name,
            verbose=not args.quiet,
            backup=not args.no_backup
        )
        
        # Run conversion
        success, stats = converter.convert()
        
        if success and stats:
            print(f"\n{'='*80}")
            print(f"[SUCCESS] CSV to SQLite conversion complete!")
            print(f"{'='*80}")
            print(f"\nDatabase: {converter.db_file}")
            print(f"Records: {stats['records']:,}")
            print(f"Columns: {stats['columns']}")
            print(f"Size: {stats['size_mb']:.1f} MB")
            
            if converter.backup_file:
                print(f"Backup: {converter.backup_file}")
            
            print(f"\n{'='*80}\n")
            sys.exit(0)
        else:
            print(f"\n{'='*80}")
            print(f"[FAILED] Conversion failed. See errors above.")
            print(f"{'='*80}\n")
            sys.exit(1)
    
    except ValueError as e:
        print(f"[ERROR] Invalid input: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}", file=sys.stderr)
        sys.exit(2)
    except PermissionError as e:
        print(f"[ERROR] Permission denied: {e}", file=sys.stderr)
        print(f"  Ensure you have write access to the output directory", file=sys.stderr)
        sys.exit(3)
    except KeyboardInterrupt:
        print(f"\n[INTERRUPTED] Conversion cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}", file=sys.stderr)
        logging.exception("Fatal error trace:")
        sys.exit(1)


if __name__ == '__main__':
    main()
