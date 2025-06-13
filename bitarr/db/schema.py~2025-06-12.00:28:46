"""
SQLite database schema for Bitarr.
"""
import sqlite3
from pathlib import Path
import os

# SQL for enabling foreign keys
PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON;"

# SQL for enabling WAL mode for better concurrency
PRAGMA_JOURNAL_MODE = "PRAGMA journal_mode = WAL;"

# Table creation SQL statements
CREATE_STORAGE_DEVICES_TABLE = """
CREATE TABLE IF NOT EXISTS storage_devices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    mount_point  TEXT NOT NULL,
    device_type  TEXT,
    total_size   INTEGER,
    used_size    INTEGER,
    first_seen   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_connected BOOLEAN NOT NULL DEFAULT 1,
    device_id    TEXT,
    UNIQUE (device_id)
);
"""

CREATE_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS files (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    path              TEXT NOT NULL,
    filename          TEXT NOT NULL,
    directory         TEXT NOT NULL,
    storage_device_id INTEGER NOT NULL,
    size              INTEGER,
    last_modified     TIMESTAMP,
    file_type         TEXT,
    first_seen        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted        BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (storage_device_id) REFERENCES storage_devices(id),
    UNIQUE (path, storage_device_id)
);
"""

CREATE_SCHEDULED_SCANS_TABLE = """
CREATE TABLE IF NOT EXISTS scheduled_scans (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    paths        TEXT NOT NULL,
    frequency    TEXT NOT NULL,
    parameters   TEXT NOT NULL,
    last_run     TIMESTAMP,
    next_run     TIMESTAMP,
    status       TEXT NOT NULL DEFAULT 'active',
    priority     INTEGER NOT NULL DEFAULT 0,
    max_runtime  INTEGER,
    is_active    BOOLEAN NOT NULL DEFAULT 1,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SCANS_TABLE = """
CREATE TABLE IF NOT EXISTS scans (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT,
    top_level_path    TEXT NOT NULL,
    start_time        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time          TIMESTAMP,
    status            TEXT NOT NULL,
    files_scanned     INTEGER DEFAULT 0,
    files_unchanged   INTEGER DEFAULT 0,
    files_modified    INTEGER DEFAULT 0,
    files_corrupted   INTEGER DEFAULT 0,
    files_missing     INTEGER DEFAULT 0,
    files_new         INTEGER DEFAULT 0,
    checksum_method   TEXT NOT NULL,
    scheduled_scan_id INTEGER,
    error_message     TEXT,
    notes             TEXT,
    FOREIGN KEY (scheduled_scan_id) REFERENCES scheduled_scans(id)
);
"""

CREATE_CHECKSUMS_TABLE = """
CREATE TABLE IF NOT EXISTS checksums (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id          INTEGER NOT NULL,
    scan_id          INTEGER NOT NULL,
    checksum_value   TEXT NOT NULL,
    checksum_method  TEXT NOT NULL,
    timestamp        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status           TEXT NOT NULL,
    previous_checksum_id INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (scan_id) REFERENCES scans(id),
    FOREIGN KEY (previous_checksum_id) REFERENCES checksums(id),
    UNIQUE (file_id, scan_id)
);
"""

CREATE_SCAN_ERRORS_TABLE = """
CREATE TABLE IF NOT EXISTS scan_errors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     INTEGER NOT NULL,
    file_path   TEXT,
    error_type  TEXT NOT NULL,
    error_message TEXT,
    timestamp   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);
"""

CREATE_CONFIGURATION_TABLE = """
CREATE TABLE IF NOT EXISTS configuration (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    type        TEXT NOT NULL,
    description TEXT,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# Create indexes
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);",
    "CREATE INDEX IF NOT EXISTS idx_files_storage_device ON files(storage_device_id);",
    "CREATE INDEX IF NOT EXISTS idx_files_directory ON files(directory);",
    "CREATE INDEX IF NOT EXISTS idx_files_is_deleted ON files(is_deleted);",
    
    "CREATE INDEX IF NOT EXISTS idx_checksums_file_id ON checksums(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_checksums_scan_id ON checksums(scan_id);",
    "CREATE INDEX IF NOT EXISTS idx_checksums_status ON checksums(status);",
    "CREATE INDEX IF NOT EXISTS idx_checksums_previous ON checksums(previous_checksum_id);",
    
    "CREATE INDEX IF NOT EXISTS idx_scans_path ON scans(top_level_path);",
    "CREATE INDEX IF NOT EXISTS idx_scans_time ON scans(start_time);",
    "CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);",
    "CREATE INDEX IF NOT EXISTS idx_scans_scheduled ON scans(scheduled_scan_id);",
    
    "CREATE INDEX IF NOT EXISTS idx_storage_devices_mount ON storage_devices(mount_point);",
    "CREATE INDEX IF NOT EXISTS idx_storage_devices_connected ON storage_devices(is_connected);",
    
    "CREATE INDEX IF NOT EXISTS idx_scheduled_scans_active ON scheduled_scans(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_scheduled_scans_next_run ON scheduled_scans(next_run);",
    
    "CREATE INDEX IF NOT EXISTS idx_scan_errors_scan ON scan_errors(scan_id);"
]

# Default configuration values
DEFAULT_CONFIG = [
    (
        'web_ui_port', '8286', 'integer', 
        'Port for the web interface'
    ),
    (
        'scan_threads', '4', 'integer', 
        'Number of threads to use for scanning'
    ),
    (
        'checksum_method', 'sha256', 'string', 
        'Default checksum method'
    ),
    (
        'checksum_block_size', '4', 'integer', 
        'Size of blocks read when calculating checksums (MB)'
    ),
    (
        'db_auto_vacuum', '1', 'integer', 
        'Enable auto-vacuum (0=none, 1=full, 2=incremental)'
    ),
    (
        'db_auto_backup', '1', 'boolean', 
        'Enable automatic database backups'
    ),
    (
        'db_backup_frequency', 'weekly', 'string', 
        'How often to perform database backups'
    ),
    (
        'db_backup_retain', '10', 'integer', 
        'Number of backup copies to retain'
    ),
    (
        'schema_version', '1', 'integer', 
        'Database schema version'
    )
]

def get_default_db_path():
    """Get the default database file path."""
    # Get the user's home directory
    home_dir = Path.home()
    app_dir = home_dir / ".bitarr"
    
    # Create the directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)
    
    return app_dir / "bitarr.db"
