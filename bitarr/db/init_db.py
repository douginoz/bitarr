"""
Database initialization script for Bitarr v1.1.0
Storage-device-centric architecture with distributed client support
"""
import sqlite3
import os
import socket
import platform
from pathlib import Path
from datetime import datetime, timezone
from .schema import (
    PRAGMA_FOREIGN_KEYS, PRAGMA_JOURNAL_MODE,
    CREATE_SCAN_HOSTS_TABLE, CREATE_STORAGE_DEVICES_TABLE,
    CREATE_FILES_TABLE, CREATE_SCHEDULED_SCANS_TABLE,
    CREATE_SCANS_TABLE, CREATE_CHECKSUMS_TABLE,
    CREATE_SCAN_ERRORS_TABLE, CREATE_CONFIGURATION_TABLE,
    CREATE_BITROT_EVENTS_TABLE, CREATE_DEVICE_HEALTH_HISTORY_TABLE,
    CREATE_INDEXES, DEFAULT_CONFIG, get_default_db_path
)

def get_current_host_info():
    """Get current machine information for initial host setup."""
    try:
        hostname = socket.gethostname()

        # Try to get local IP (not 127.0.0.1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))  # Connect to Google DNS
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()

        host_type = 'linux' if platform.system().lower() == 'linux' else 'windows'
        display_name = f"{local_ip} ({hostname})"

        return {
            'host_name': hostname,
            'host_ip': local_ip,
            'host_display_name': display_name,
            'host_type': host_type
        }
    except Exception as e:
        print(f"Warning: Could not detect host info: {e}")
        return {
            'host_name': 'localhost',
            'host_ip': '127.0.0.1',
            'host_display_name': '127.0.0.1 (localhost)',
            'host_type': 'linux'
        }

def init_db(db_path=None):
    """
    Initialize the SQLite database with the v1.1.0 schema.

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

    try:
        # Enable foreign keys and WAL mode
        cursor.execute(PRAGMA_FOREIGN_KEYS)
        cursor.execute(PRAGMA_JOURNAL_MODE)

        # Create tables in dependency order
        print("Creating database tables...")

        # 1. Independent tables first
        cursor.execute(CREATE_CONFIGURATION_TABLE)
        cursor.execute(CREATE_SCAN_HOSTS_TABLE)
        cursor.execute(CREATE_SCHEDULED_SCANS_TABLE)

        # 2. Tables that depend on scan_hosts
        cursor.execute(CREATE_STORAGE_DEVICES_TABLE)

        # 3. Tables that depend on storage_devices
        cursor.execute(CREATE_FILES_TABLE)

        # 4. Tables that depend on multiple other tables
        cursor.execute(CREATE_SCANS_TABLE)
        cursor.execute(CREATE_CHECKSUMS_TABLE)
        cursor.execute(CREATE_SCAN_ERRORS_TABLE)

        # 5. v1.1.0 new tables
        cursor.execute(CREATE_BITROT_EVENTS_TABLE)
        cursor.execute(CREATE_DEVICE_HEALTH_HISTORY_TABLE)

        print("Creating database indexes...")

        # Create indexes
        for index_sql in CREATE_INDEXES:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError as e:
                print(f"Warning: Could not create index: {e}")

        print("Inserting default configuration...")

        # Insert default configuration values if they don't exist
        for key, value, type_str, description in DEFAULT_CONFIG:
            cursor.execute(
                """
                INSERT OR IGNORE INTO configuration
                (key, value, type, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, value, type_str, description, datetime.now(timezone.utc))
            )

        print("Setting up current host...")

        # Add current host information
        host_info = get_current_host_info()
        cursor.execute(
            """
            INSERT OR REPLACE INTO scan_hosts
            (host_name, host_ip, host_display_name, host_type, client_version, connection_status, last_seen, created_at, updated_at)
            VALUES (?, ?, ?, ?, '1.1.0', 'online', ?, ?, ?)
            """,
            (
                host_info['host_name'],
                host_info['host_ip'],
                host_info['host_display_name'],
                host_info['host_type'],
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            )
        )

        # Commit changes
        conn.commit()

        print(f"✅ Database initialized successfully at: {db_path}")
        print(f"🖥️ Host added: {host_info['host_display_name']}")
        print(f"📊 Schema version: 1.1.0")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    return str(db_path)

def reset_db(db_path=None):
    """
    Reset the database by deleting and recreating it.

    Args:
        db_path: Path to the database file. If None, uses the default path.

    Returns:
        str: Path to the reset database
    """
    if db_path is None:
        db_path = get_default_db_path()

    # Delete existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Deleted existing database: {db_path}")

    # Initialize fresh database
    return init_db(db_path)

def upgrade_db(db_path=None):
    """
    Upgrade existing database to v1.1.0 schema.
    Note: This is for development use only. Production should use proper migrations.

    Args:
        db_path: Path to the database file. If None, uses the default path.

    Returns:
        str: Path to the upgraded database
    """
    if db_path is None:
        db_path = get_default_db_path()

    if not os.path.exists(db_path):
        print("No existing database found. Creating new database...")
        return init_db(db_path)

    print("⚠️ Upgrading existing database to v1.1.0...")
    print("⚠️ This will modify the existing database structure!")

    # Create backup first
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"📁 Created backup: {backup_path}")

    # Connect and upgrade
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Enable foreign keys
        cursor.execute(PRAGMA_FOREIGN_KEYS)

        # Check current schema version
        try:
            cursor.execute("SELECT value FROM configuration WHERE key = 'schema_version'")
            current_version = cursor.fetchone()
            if current_version and current_version[0] == '1.1.0':
                print("✅ Database is already at v1.1.0")
                return str(db_path)
        except sqlite3.OperationalError:
            print("📊 No version info found, assuming v1.0.0")

        print("🔄 Adding v1.1.0 tables and columns...")

        # Add new tables
        cursor.execute(CREATE_SCAN_HOSTS_TABLE)
        cursor.execute(CREATE_BITROT_EVENTS_TABLE)
        cursor.execute(CREATE_DEVICE_HEALTH_HISTORY_TABLE)

        # Add new columns to existing tables (ignore errors if they already exist)
        v1_1_0_columns = [
            "ALTER TABLE storage_devices ADD COLUMN host_id INTEGER",
            "ALTER TABLE storage_devices ADD COLUMN host_name TEXT",
            "ALTER TABLE storage_devices ADD COLUMN host_ip TEXT",
            "ALTER TABLE storage_devices ADD COLUMN host_display_name TEXT",
            "ALTER TABLE storage_devices ADD COLUMN device_model TEXT",
            "ALTER TABLE storage_devices ADD COLUMN device_serial TEXT",
            "ALTER TABLE storage_devices ADD COLUMN connection_type TEXT DEFAULT 'unknown'",
            "ALTER TABLE storage_devices ADD COLUMN is_local BOOLEAN DEFAULT TRUE",
            "ALTER TABLE storage_devices ADD COLUMN mount_points TEXT",
            "ALTER TABLE storage_devices ADD COLUMN health_status TEXT DEFAULT 'unknown'",
            "ALTER TABLE storage_devices ADD COLUMN last_health_check TIMESTAMP",
            "ALTER TABLE storage_devices ADD COLUMN performance_warning BOOLEAN DEFAULT FALSE",

            "ALTER TABLE scans ADD COLUMN host_id INTEGER",
            "ALTER TABLE scans ADD COLUMN host_name TEXT",
            "ALTER TABLE scans ADD COLUMN host_ip TEXT",
            "ALTER TABLE scans ADD COLUMN host_display_name TEXT",
            "ALTER TABLE scans ADD COLUMN storage_device_id INTEGER",
            "ALTER TABLE scans ADD COLUMN scan_duration_seconds INTEGER",
            "ALTER TABLE scans ADD COLUMN bitrot_clusters_detected INTEGER DEFAULT 0",
            "ALTER TABLE scans ADD COLUMN total_size INTEGER DEFAULT 0"
        ]

        for alter_sql in v1_1_0_columns:
            try:
                cursor.execute(alter_sql)
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    print(f"Warning: {e}")

        # Add current host
        host_info = get_current_host_info()
        cursor.execute(
            """
            INSERT OR REPLACE INTO scan_hosts
            (host_name, host_ip, host_display_name, host_type, client_version, connection_status, last_seen)
            VALUES (?, ?, ?, ?, '1.1.0', 'online', ?)
            """,
            (
                host_info['host_name'],
                host_info['host_ip'],
                host_info['host_display_name'],
                host_info['host_type'],
                datetime.now(timezone.utc)
            )
        )

        # Get host ID for updating existing records
        cursor.execute("SELECT id FROM scan_hosts WHERE host_name = ? AND host_ip = ?",
                      (host_info['host_name'], host_info['host_ip']))
        host_id = cursor.fetchone()[0]

        # Update existing storage devices
        cursor.execute("""
            UPDATE storage_devices
            SET host_id = ?, host_name = ?, host_ip = ?, host_display_name = ?
            WHERE host_id IS NULL
        """, (host_id, host_info['host_name'], host_info['host_ip'], host_info['host_display_name']))

        # Update existing scans
        cursor.execute("SELECT id FROM storage_devices ORDER BY id LIMIT 1")
        storage_device_result = cursor.fetchone()
        default_storage_device_id = storage_device_result[0] if storage_device_result else None

        if default_storage_device_id:
            cursor.execute("""
                UPDATE scans
                SET host_id = ?, host_name = ?, host_ip = ?, host_display_name = ?, storage_device_id = ?
                WHERE host_id IS NULL
            """, (host_id, host_info['host_name'], host_info['host_ip'], host_info['host_display_name'], default_storage_device_id))

        # Update configuration version
        cursor.execute("""
            INSERT OR REPLACE INTO configuration (key, value, type, description, updated_at)
            VALUES ('schema_version', '1.1.0', 'string', 'Database schema version', ?)
        """, (datetime.now(timezone.utc),))

        # Create new indexes
        for index_sql in CREATE_INDEXES:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError:
                pass  # Index might already exist

        conn.commit()
        print("✅ Database upgraded to v1.1.0 successfully!")

    except Exception as e:
        print(f"❌ Error upgrading database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    return str(db_path)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "reset":
            db_path = reset_db()
            print(f"🆕 Database reset and initialized at: {db_path}")
        elif command == "upgrade":
            db_path = upgrade_db()
            print(f"⬆️ Database upgraded at: {db_path}")
        else:
            print("Usage: python init_db.py [reset|upgrade]")
    else:
        db_path = init_db()
        print(f"📊 Database initialized at: {db_path}")
