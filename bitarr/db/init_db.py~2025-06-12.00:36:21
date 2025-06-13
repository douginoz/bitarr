"""
Database initialization script for Bitarr.
"""
import sqlite3
import os
from pathlib import Path
from .schema import (
    PRAGMA_FOREIGN_KEYS, PRAGMA_JOURNAL_MODE,
    CREATE_STORAGE_DEVICES_TABLE, CREATE_FILES_TABLE,
    CREATE_SCHEDULED_SCANS_TABLE, CREATE_SCANS_TABLE,
    CREATE_CHECKSUMS_TABLE, CREATE_SCAN_ERRORS_TABLE,
    CREATE_CONFIGURATION_TABLE, CREATE_INDEXES,
    DEFAULT_CONFIG, get_default_db_path
)

def init_db(db_path=None):
    """
    Initialize the SQLite database with the schema.
    
    Args:
        db_path: Path to the database file. If None, uses the default path.
    
    Returns:
        str: Path to the initialized database
    """
    if db_path is None:
        db_path = get_default_db_path()
    
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys and WAL mode
    cursor.execute(PRAGMA_FOREIGN_KEYS)
    cursor.execute(PRAGMA_JOURNAL_MODE)
    
    # Create tables
    cursor.execute(CREATE_STORAGE_DEVICES_TABLE)
    cursor.execute(CREATE_FILES_TABLE)
    cursor.execute(CREATE_SCHEDULED_SCANS_TABLE)
    cursor.execute(CREATE_SCANS_TABLE)
    cursor.execute(CREATE_CHECKSUMS_TABLE)
    cursor.execute(CREATE_SCAN_ERRORS_TABLE)
    cursor.execute(CREATE_CONFIGURATION_TABLE)
    
    # Create indexes
    for index_sql in CREATE_INDEXES:
        cursor.execute(index_sql)
    
    # Insert default configuration values if they don't exist
    for key, value, type_str, description in DEFAULT_CONFIG:
        cursor.execute(
            """
            INSERT OR IGNORE INTO configuration 
            (key, value, type, description) 
            VALUES (?, ?, ?, ?)
            """, 
            (key, value, type_str, description)
        )
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()
    
    return str(db_path)

if __name__ == "__main__":
    db_path = init_db()
    print(f"Database initialized at: {db_path}")
