#!/usr/bin/env python3
"""
Bitarr Database Migration v1.0.0 → v1.1.0
Storage-Device-Centric Architecture Migration

This script migrates the database from v1.0.0 single-machine architecture
to v1.1.0 distributed client-server architecture.
"""

import os
import sys
import sqlite3
import platform
import socket
from datetime import datetime
from pathlib import Path

def get_current_host_info():
    """Get current machine information for migration."""
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

def backup_database(db_path):
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return None

def get_database_version(conn):
    """Get current database version."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM configuration WHERE key = 'db_version'")
        result = cursor.fetchone()
        return result[0] if result else '1.0.0'
    except Exception:
        return '1.0.0'  # Assume v1.0.0 if no version found

def check_migration_needed(conn):
    """Check if migration is needed."""
    version = get_database_version(conn)
    
    if version == '1.1.0':
        print("✅ Database is already at v1.1.0")
        return False
    elif version == '1.0.0':
        print(f"📋 Migration needed: v{version} → v1.1.0")
        return True
    else:
        print(f"⚠️ Unknown database version: {version}")
        return False

def execute_sql_file(conn, sql_content):
    """Execute SQL statements from content."""
    cursor = conn.cursor()
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    for statement in statements:
        try:
            cursor.execute(statement)
            print(f"✅ Executed: {statement[:50]}...")
        except Exception as e:
            print(f"⚠️ SQL Warning: {e}")
            print(f"   Statement: {statement[:100]}...")
    
    conn.commit()

def migrate_database(db_path):
    """Perform the database migration."""
    print(f"🔄 Starting migration of {db_path}")
    
    # Create backup
    backup_path = backup_database(db_path)
    if not backup_path:
        print("❌ Cannot proceed without backup")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        # Check if migration needed
        if not check_migration_needed(conn):
            conn.close()
            return True
            
        print("🚀 Beginning migration...")
        
        # Get current host information
        host_info = get_current_host_info()
        print(f"📍 Current host: {host_info['host_display_name']}")
        
        # Read migration SQL
        migration_sql = """
        -- 1. Create scan_hosts table
        CREATE TABLE IF NOT EXISTS scan_hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_name TEXT NOT NULL,
            host_ip TEXT NOT NULL,
            host_display_name TEXT NOT NULL,
            host_type TEXT NOT NULL,
            client_version TEXT DEFAULT '1.1.0',
            connection_status TEXT DEFAULT 'online',
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            auth_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(host_name, host_ip)
        );
        
        -- 2. Add columns to storage_devices (ignore errors if already exist)
        ALTER TABLE storage_devices ADD COLUMN host_id INTEGER;
        ALTER TABLE storage_devices ADD COLUMN host_name TEXT;
        ALTER TABLE storage_devices ADD COLUMN host_ip TEXT;
        ALTER TABLE storage_devices ADD COLUMN host_display_name TEXT;
        ALTER TABLE storage_devices ADD COLUMN device_model TEXT;
        ALTER TABLE storage_devices ADD COLUMN device_serial TEXT;
        ALTER TABLE storage_devices ADD COLUMN connection_type TEXT DEFAULT 'unknown';
        ALTER TABLE storage_devices ADD COLUMN is_local BOOLEAN DEFAULT TRUE;
        ALTER TABLE storage_devices ADD COLUMN mount_points TEXT;
        ALTER TABLE storage_devices ADD COLUMN health_status TEXT DEFAULT 'unknown';
        ALTER TABLE storage_devices ADD COLUMN last_health_check TIMESTAMP;
        ALTER TABLE storage_devices ADD COLUMN performance_warning BOOLEAN DEFAULT FALSE;
        
        -- 3. Add columns to scans (ignore errors if already exist)
        ALTER TABLE scans ADD COLUMN host_id INTEGER;
        ALTER TABLE scans ADD COLUMN host_name TEXT;
        ALTER TABLE scans ADD COLUMN host_ip TEXT;
        ALTER TABLE scans ADD COLUMN host_display_name TEXT;
        ALTER TABLE scans ADD COLUMN storage_device_id INTEGER;
        ALTER TABLE scans ADD COLUMN scan_duration_seconds INTEGER;
        ALTER TABLE scans ADD COLUMN bitrot_clusters_detected INTEGER DEFAULT 0;
        ALTER TABLE scans ADD COLUMN total_size INTEGER DEFAULT 0;
        
        -- 4. Create bitrot_events table
        CREATE TABLE IF NOT EXISTS bitrot_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storage_device_id INTEGER NOT NULL,
            scan_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            event_date TIMESTAMP NOT NULL,
            affected_files_count INTEGER NOT NULL,
            file_paths TEXT NOT NULL,
            sector_ranges TEXT,
            cluster_analysis TEXT,
            severity TEXT NOT NULL,
            pattern_description TEXT,
            recommended_action TEXT,
            user_acknowledged BOOLEAN DEFAULT FALSE,
            acknowledgment_date TIMESTAMP,
            notes TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            resolution_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 5. Create device_health_history table
        CREATE TABLE IF NOT EXISTS device_health_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storage_device_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            check_date TIMESTAMP NOT NULL,
            temperature INTEGER,
            power_on_hours INTEGER,
            total_data_written INTEGER,
            bad_sectors_count INTEGER,
            wear_leveling_count INTEGER,
            health_score INTEGER,
            smart_status TEXT,
            smart_raw_data TEXT,
            predicted_failure_date DATE,
            data_source TEXT NOT NULL,
            requires_root BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Execute migration SQL (handle errors gracefully for ALTER TABLE)
        print("📋 Creating new tables and columns...")
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            try:
                conn.execute(statement)
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⚠️ Column already exists: {e}")
                else:
                    print(f"⚠️ SQL Error: {e}")
        
        conn.commit()
        
        # Insert current host
        print("📍 Adding current host...")
        conn.execute("""
            INSERT OR REPLACE INTO scan_hosts 
            (host_name, host_ip, host_display_name, host_type, client_version, connection_status, last_seen)
            VALUES (?, ?, ?, ?, '1.1.0', 'online', CURRENT_TIMESTAMP)
        """, (host_info['host_name'], host_info['host_ip'], host_info['host_display_name'], host_info['host_type']))
        
        # Get host ID
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM scan_hosts WHERE host_name = ? AND host_ip = ?", 
                      (host_info['host_name'], host_info['host_ip']))
        host_id = cursor.fetchone()[0]
        
        # Update existing storage devices
        print("💾 Updating storage devices...")
        conn.execute("""
            UPDATE storage_devices 
            SET host_id = ?, host_name = ?, host_ip = ?, host_display_name = ?
            WHERE host_id IS NULL
        """, (host_id, host_info['host_name'], host_info['host_ip'], host_info['host_display_name']))
        
        # Update existing scans
        print("🔍 Updating existing scans...")
        # First, ensure we have a storage device to link to
        cursor.execute("SELECT id FROM storage_devices ORDER BY id LIMIT 1")
        storage_device_result = cursor.fetchone()
        default_storage_device_id = storage_device_result[0] if storage_device_result else None
        
        if default_storage_device_id:
            conn.execute("""
                UPDATE scans 
                SET host_id = ?, host_name = ?, host_ip = ?, host_display_name = ?, storage_device_id = ?
                WHERE host_id IS NULL
            """, (host_id, host_info['host_name'], host_info['host_ip'], host_info['host_display_name'], default_storage_device_id))
        
        # Create indexes
        print("📊 Creating indexes...")
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_scan_hosts_status ON scan_hosts(connection_status, last_seen);
        CREATE INDEX IF NOT EXISTS idx_storage_devices_host ON storage_devices(host_id, is_local);
        CREATE INDEX IF NOT EXISTS idx_scans_host_device ON scans(host_id, storage_device_id, start_time);
        CREATE INDEX IF NOT EXISTS idx_bitrot_events_device ON bitrot_events(storage_device_id, event_date);
        CREATE INDEX IF NOT EXISTS idx_device_health_latest ON device_health_history(storage_device_id, check_date DESC);
        """
        
        for statement in [stmt.strip() for stmt in index_sql.split(';') if stmt.strip()]:
            conn.execute(statement)
        
        # Update database version
        print("🏷️ Updating database version...")
        conn.execute("""
            INSERT OR REPLACE INTO configuration (key, value, description, updated_at)
            VALUES ('db_version', '1.1.0', 'Database schema version', CURRENT_TIMESTAMP)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        print(f"📊 Database migrated to v1.1.0")
        print(f"📁 Backup saved: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"💡 You can restore from backup: {backup_path}")
        return False

def main():
    """Main migration function."""
    print("🚀 Bitarr Database Migration v1.0.0 → v1.1.0")
    print("=" * 50)
    
    # Find database path
    db_path = None
    possible_paths = [
        os.path.expanduser("~/.bitarr/bitarr.db"),
        "bitarr.db",
        "instance/bitarr.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Could not find bitarr.db database")
        print("💡 Tried these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        sys.exit(1)
    
    print(f"📁 Found database: {db_path}")
    
    # Confirm migration
    print("\n⚠️ This will modify your database structure.")
    print("📋 Changes include:")
    print("   • Add host tracking tables")
    print("   • Add bitrot clustering analysis")
    print("   • Add device health monitoring")
    print("   • Update existing scan data")
    print("   • Create automatic backup")
    
    response = input("\n🤔 Continue with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Migration cancelled")
        sys.exit(0)
    
    # Perform migration
    success = migrate_database(db_path)
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("🔧 Next steps:")
        print("   1. Restart Bitarr web server")
        print("   2. Verify dashboard shows host information")
        print("   3. Test scanning functionality")
        print("   4. Check storage device detection")
        
        print(f"\n📊 Database is now at v1.1.0")
        print("📚 See docs/v1.1.0/ for architecture details")
    else:
        print("\n❌ Migration failed!")
        print("💡 Check backup file and try manual recovery if needed")
        sys.exit(1)

if __name__ == "__main__":
    main()
