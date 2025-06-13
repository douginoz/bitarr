"""
SQLite database schema for Bitarr v1.1.0
Storage-device-centric architecture with distributed client support
"""
import sqlite3
from pathlib import Path
import os

# SQL for enabling foreign keys
PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON;"

# SQL for enabling WAL mode for better concurrency
PRAGMA_JOURNAL_MODE = "PRAGMA journal_mode = WAL;"

# v1.1.0 - NEW: Scan hosts table for machine tracking
CREATE_SCAN_HOSTS_TABLE = """
CREATE TABLE IF NOT EXISTS scan_hosts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name    TEXT NOT NULL,
    host_ip      TEXT NOT NULL,
    host_display_name TEXT NOT NULL,
    host_type    TEXT NOT NULL,
    client_version TEXT DEFAULT '1.1.0',
    connection_status TEXT DEFAULT 'offline',
    last_seen    TIMESTAMP,
    auth_token   TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (host_name, host_ip)
);
"""

# Enhanced storage devices table with host relationship
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
    -- v1.1.0 additions for distributed architecture
    host_id      INTEGER,
    host_name    TEXT,
    host_ip      TEXT,
    host_display_name TEXT,
    device_model TEXT,
    device_serial TEXT,
    connection_type TEXT DEFAULT 'unknown',
    is_local     BOOLEAN DEFAULT TRUE,
    mount_points TEXT,
    health_status TEXT DEFAULT 'unknown',
    last_health_check TIMESTAMP,
    performance_warning BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (host_id) REFERENCES scan_hosts (id),
    UNIQUE (device_id)
);
"""

# Files table (unchanged structure, compatible with v1.0.0)
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

# Scheduled scans table (unchanged structure)
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

# Enhanced scans table with host and storage device relationships
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
    -- v1.1.0 additions for distributed architecture
    host_id           INTEGER,
    host_name         TEXT,
    host_ip           TEXT,
    host_display_name TEXT,
    storage_device_id INTEGER,
    scan_duration_seconds INTEGER,
    bitrot_clusters_detected INTEGER DEFAULT 0,
    total_size        INTEGER DEFAULT 0,
    FOREIGN KEY (scheduled_scan_id) REFERENCES scheduled_scans(id),
    FOREIGN KEY (host_id) REFERENCES scan_hosts(id),
    FOREIGN KEY (storage_device_id) REFERENCES storage_devices(id)
);
"""

# Checksums table (unchanged structure)
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

# Scan errors table (unchanged structure)
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

# Configuration table (unchanged structure)
CREATE_CONFIGURATION_TABLE = """
CREATE TABLE IF NOT EXISTS configuration (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    type        TEXT NOT NULL,
    description TEXT,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# v1.1.0 - NEW: Bitrot events table for clustering analysis
CREATE_BITROT_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS bitrot_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_device_id INTEGER NOT NULL,
    scan_id          INTEGER NOT NULL,
    host_id          INTEGER NOT NULL,
    event_date       TIMESTAMP NOT NULL,
    affected_files_count INTEGER NOT NULL,
    file_paths       TEXT NOT NULL,
    sector_ranges    TEXT,
    cluster_analysis TEXT,
    severity         TEXT NOT NULL,
    pattern_description TEXT,
    recommended_action TEXT,
    user_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledgment_date TIMESTAMP,
    notes            TEXT,
    resolved         BOOLEAN DEFAULT FALSE,
    resolution_date  TIMESTAMP,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (storage_device_id) REFERENCES storage_devices (id),
    FOREIGN KEY (scan_id) REFERENCES scans (id),
    FOREIGN KEY (host_id) REFERENCES scan_hosts (id)
);
"""

# v1.1.0 - NEW: Device health history for tracking device health over time
CREATE_DEVICE_HEALTH_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS device_health_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_device_id INTEGER NOT NULL,
    host_id          INTEGER NOT NULL,
    check_date       TIMESTAMP NOT NULL,
    temperature      INTEGER,
    power_on_hours   INTEGER,
    total_data_written INTEGER,
    bad_sectors_count INTEGER,
    wear_leveling_count INTEGER,
    health_score     INTEGER,
    smart_status     TEXT,
    smart_raw_data   TEXT,
    predicted_failure_date DATE,
    data_source      TEXT NOT NULL,
    requires_root    BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (storage_device_id) REFERENCES storage_devices (id),
    FOREIGN KEY (host_id) REFERENCES scan_hosts (id)
);
"""

# Create indexes for performance
CREATE_INDEXES = [
    # Existing indexes
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

    "CREATE INDEX IF NOT EXISTS idx_scan_errors_scan ON scan_errors(scan_id);",

    # v1.1.0 new indexes
    "CREATE INDEX IF NOT EXISTS idx_scan_hosts_status ON scan_hosts(connection_status, last_seen);",
    "CREATE INDEX IF NOT EXISTS idx_scan_hosts_name_ip ON scan_hosts(host_name, host_ip);",

    "CREATE INDEX IF NOT EXISTS idx_storage_devices_host ON storage_devices(host_id, is_local);",
    "CREATE INDEX IF NOT EXISTS idx_storage_devices_health ON storage_devices(health_status, last_health_check);",

    "CREATE INDEX IF NOT EXISTS idx_scans_host_device ON scans(host_id, storage_device_id, start_time);",

    "CREATE INDEX IF NOT EXISTS idx_bitrot_events_device ON bitrot_events(storage_device_id, event_date);",
    "CREATE INDEX IF NOT EXISTS idx_bitrot_events_unresolved ON bitrot_events(resolved, severity);",
    "CREATE INDEX IF NOT EXISTS idx_bitrot_events_host ON bitrot_events(host_id, event_date);",

    "CREATE INDEX IF NOT EXISTS idx_device_health_latest ON device_health_history(storage_device_id, check_date DESC);",
    "CREATE INDEX IF NOT EXISTS idx_device_health_host ON device_health_history(host_id, check_date);",
]

# Default configuration values (enhanced for v1.1.0)
DEFAULT_CONFIG = [
    # Existing v1.0.0 config
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
        'schema_version', '1.1.0', 'string',
        'Database schema version'
    ),
    # v1.1.0 new config
    (
        'app_version', '1.1.0', 'string',
        'Application version'
    ),
    (
        'bitrot_alert_threshold', 'moderate', 'string',
        'Minimum severity for bitrot alerts (minor, moderate, severe)'
    ),
    (
        'device_health_check_interval_hours', '24', 'integer',
        'Device health check frequency in hours'
    ),
    (
        'network_storage_warning_speed_mbps', '50', 'integer',
        'Speed threshold for network storage warnings in MB/s'
    ),
    (
        'client_timeout_seconds', '300', 'integer',
        'Timeout for client connections in seconds'
    ),
    (
        'auto_detect_local_storage', '1', 'boolean',
        'Automatically detect local vs network storage'
    ),
]

def get_default_db_path():
    """Get the default database file path."""
    # Get the user's home directory
    home_dir = Path.home()
    app_dir = home_dir / ".bitarr"

    # Create the directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)

    return app_dir / "bitarr.db"
