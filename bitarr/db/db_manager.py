"""
Database manager for Bitarr.
"""
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3
import json
import threading
from typing import List, Dict, Any, Optional, Union, Tuple
from .models import (
    StorageDevice, File, Scan, Checksum, 
    ScheduledScan, ScanError, Configuration
)
from .schema import get_default_db_path

class DatabaseManager:
    """
    Manager for database operations.
    
    This class provides methods to interact with the SQLite database,
    handling connections, transactions, and CRUD operations for all entities.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the database file. If None, uses the default path.
        """
        self.db_path = db_path or get_default_db_path()
        self.lock = threading.RLock()  # Reentrant lock for thread safety
    
    def get_connection(self):
        """
        Get a connection to the database.
        
        Returns:
            sqlite3.Connection: A connection to the database.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access to rows
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        return conn
    
    def execute_query(self, query, params=None, commit=True):
        """
        Execute a SQL query.
        
        Args:
            query: SQL query to execute.
            params: Parameters for the query.
            commit: Whether to commit the transaction.
            
        Returns:
            cursor: SQLite cursor after execution.
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if commit:
                    conn.commit()
                
                return cursor
            finally:
                conn.close()
    
    def execute_many(self, query, params_list, commit=True):
        """
        Execute a SQL query with multiple parameter sets.
        
        Args:
            query: SQL query to execute.
            params_list: List of parameter sets.
            commit: Whether to commit the transaction.
            
        Returns:
            cursor: SQLite cursor after execution.
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                
                if commit:
                    conn.commit()
                
                return cursor
            finally:
                conn.close()
    
    def fetch_one(self, query, params=None):
        """
        Fetch a single row from the database.
        
        Args:
            query: SQL query to execute.
            params: Parameters for the query.
            
        Returns:
            row: The first row returned by the query, or None.
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()
    
    def fetch_all(self, query, params=None):
        """
        Fetch all rows from the database.
        
        Args:
            query: SQL query to execute.
            params: Parameters for the query.
            
        Returns:
            rows: List of rows returned by the query.
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()
    
    # ===== Storage Devices =====
    
    def get_storage_device(self, device_id=None, mount_point=None, id=None):
        """
        Get a storage device by ID, device_id, or mount point.
        
        Args:
            device_id: System device ID.
            mount_point: Mount point path.
            id: Database ID.
            
        Returns:
            StorageDevice: The storage device, or None if not found.
        """
        if id is not None:
            query = "SELECT * FROM storage_devices WHERE id = ?"
            params = (id,)
        elif device_id is not None:
            query = "SELECT * FROM storage_devices WHERE device_id = ?"
            params = (device_id,)
        elif mount_point is not None:
            query = "SELECT * FROM storage_devices WHERE mount_point = ?"
            params = (mount_point,)
        else:
            return None
        
        row = self.fetch_one(query, params)
        if row:
            return StorageDevice(**row)
        return None
    
    def get_all_storage_devices(self, connected_only=False):
        """
        Get all storage devices.
        
        Args:
            connected_only: Whether to only return connected devices.
            
        Returns:
            List[StorageDevice]: List of storage devices.
        """
        if connected_only:
            query = "SELECT * FROM storage_devices WHERE is_connected = 1"
        else:
            query = "SELECT * FROM storage_devices"
        
        rows = self.fetch_all(query)
        return [StorageDevice(**row) for row in rows]
    
    def add_storage_device(self, device):
        """
        Add a storage device to the database.

        Args:
            device: StorageDevice object to add.

        Returns:
            int: ID of the added storage device.
        """
        query = """
            INSERT INTO storage_devices (
                name, mount_point, device_type, total_size,
                used_size, first_seen, last_seen, is_connected, device_id,
                host_id, host_name, host_ip, host_display_name,
                device_model, device_serial, connection_type, is_local,
                mount_points, health_status, last_health_check, performance_warning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            device.name, device.mount_point, device.device_type,
            device.total_size, device.used_size, device.first_seen,
            device.last_seen, device.is_connected, device.device_id,
            # v1.1.0 fields
            getattr(device, 'host_id', None),
            getattr(device, 'host_name', None),
            getattr(device, 'host_ip', None),
            getattr(device, 'host_display_name', None),
            getattr(device, 'device_model', None),
            getattr(device, 'device_serial', None),
            getattr(device, 'connection_type', 'unknown'),
            getattr(device, 'is_local', True),
            getattr(device, 'mount_points', None),
            getattr(device, 'health_status', 'unknown'),
            getattr(device, 'last_health_check', None),
            getattr(device, 'performance_warning', False)
        )

        cursor = self.execute_query(query, params)
        return cursor.lastrowid
    
    def update_storage_device(self, device):
        """
        Update a storage device in the database.

        Args:
            device: StorageDevice object to update.

        Returns:
            bool: Whether the update was successful.
        """
        query = """
            UPDATE storage_devices SET
                name = ?, mount_point = ?, device_type = ?,
                total_size = ?, used_size = ?, last_seen = ?,
                is_connected = ?, device_id = ?,
                host_id = ?, host_name = ?, host_ip = ?, host_display_name = ?,
                device_model = ?, device_serial = ?, connection_type = ?,
                is_local = ?, mount_points = ?, health_status = ?,
                last_health_check = ?, performance_warning = ?
            WHERE id = ?
        """
        params = (
            device.name, device.mount_point, device.device_type,
            device.total_size, device.used_size, device.last_seen,
            device.is_connected, device.device_id,
            # v1.1.0 fields
            getattr(device, 'host_id', None),
            getattr(device, 'host_name', None),
            getattr(device, 'host_ip', None),
            getattr(device, 'host_display_name', None),
            getattr(device, 'device_model', None),
            getattr(device, 'device_serial', None),
            getattr(device, 'connection_type', 'unknown'),
            getattr(device, 'is_local', True),
            getattr(device, 'mount_points', None),
            getattr(device, 'health_status', 'unknown'),
            getattr(device, 'last_health_check', None),
            getattr(device, 'performance_warning', False),
            device.id
        )

        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    def delete_storage_device(self, device_id):
        """
        Delete a storage device from the database.
        
        Args:
            device_id: ID of the storage device to delete.
            
        Returns:
            bool: Whether the deletion was successful.
        """
        query = "DELETE FROM storage_devices WHERE id = ?"
        params = (device_id,)
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    # ===== Files =====
    
    def get_file(self, id=None, path=None, storage_device_id=None):
        """
        Get a file by ID or path and storage device.
        
        Args:
            id: Database ID.
            path: File path.
            storage_device_id: ID of the storage device.
            
        Returns:
            File: The file, or None if not found.
        """
        if id is not None:
            query = "SELECT * FROM files WHERE id = ?"
            params = (id,)
        elif path is not None and storage_device_id is not None:
            query = "SELECT * FROM files WHERE path = ? AND storage_device_id = ?"
            params = (path, storage_device_id)
        else:
            return None
        
        row = self.fetch_one(query, params)
        if row:
            return File(**row)
        return None
    
    def get_files_by_directory(self, directory, storage_device_id=None, include_deleted=False):
        """
        Get files in a directory.
        
        Args:
            directory: Directory path.
            storage_device_id: ID of the storage device.
            include_deleted: Whether to include deleted files.
            
        Returns:
            List[File]: List of files.
        """
        params = [directory]
        if storage_device_id is not None:
            query = "SELECT * FROM files WHERE directory = ? AND storage_device_id = ?"
            params.append(storage_device_id)
        else:
            query = "SELECT * FROM files WHERE directory = ?"
        
        if not include_deleted:
            query += " AND is_deleted = 0"
        
        rows = self.fetch_all(query, tuple(params))
        return [File(**row) for row in rows]
    
    def add_file(self, file):
        """
        Add a file to the database.
        
        Args:
            file: File object to add.
            
        Returns:
            int: ID of the added file.
        """
        query = """
            INSERT INTO files (
                path, filename, directory, storage_device_id,
                size, last_modified, file_type, first_seen, 
                last_seen, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            file.path, file.filename, file.directory, file.storage_device_id,
            file.size, file.last_modified, file.file_type, file.first_seen,
            file.last_seen, file.is_deleted
        )
        
        cursor = self.execute_query(query, params)
        return cursor.lastrowid
    
    def update_file(self, file):
        """
        Update a file in the database.
        
        Args:
            file: File object to update.
            
        Returns:
            bool: Whether the update was successful.
        """
        query = """
            UPDATE files SET
                path = ?, filename = ?, directory = ?, storage_device_id = ?,
                size = ?, last_modified = ?, file_type = ?, last_seen = ?,
                is_deleted = ?
            WHERE id = ?
        """
        params = (
            file.path, file.filename, file.directory, file.storage_device_id,
            file.size, file.last_modified, file.file_type, file.last_seen,
            file.is_deleted, file.id
        )
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    def mark_files_as_deleted(self, file_ids):
        """
        Mark files as deleted.
        
        Args:
            file_ids: List of file IDs to mark as deleted.
            
        Returns:
            int: Number of files marked as deleted.
        """
        if not file_ids:
            return 0
        
        placeholders = ", ".join(["?"] * len(file_ids))
        query = f"UPDATE files SET is_deleted = 1 WHERE id IN ({placeholders})"
        
        cursor = self.execute_query(query, file_ids)
        return cursor.rowcount
    
    # ===== Scans =====
    
    def get_scan(self, id):
        """
        Get a scan by ID.
        
        Args:
            id: Database ID.
            
        Returns:
            Scan: The scan, or None if not found.
        """
        query = "SELECT * FROM scans WHERE id = ?"
        params = (id,)
        
        row = self.fetch_one(query, params)
        if row:
            return Scan(**row)
        return None
    
    def get_scans_by_path(self, path, limit=10):
        """
        Get scans for a specific path.
        
        Args:
            path: Top-level path.
            limit: Maximum number of scans to return.
            
        Returns:
            List[Scan]: List of scans.
        """
        query = """
            SELECT * FROM scans 
            WHERE top_level_path = ? 
            ORDER BY start_time DESC 
            LIMIT ?
        """
        params = (path, limit)
        
        rows = self.fetch_all(query, params)
        return [Scan(**row) for row in rows]
    
    def get_recent_scansx(self, limit=10):
        """
        Get recent scans.
        
        Args:
            limit: Maximum number of scans to return.
            
        Returns:
            List[Scan]: List of scans.
        """
        query = """
            SELECT * FROM scans 
            ORDER BY start_time DESC 
            LIMIT ?
        """
        params = (limit,)
        
        rows = self.fetch_all(query, params)
        return [Scan(**row) for row in rows]

    def get_recent_scans(self, limit=10, offset=0):
        """
        Get recent scans with pagination.

        Args:
            limit: Maximum number of scans to return.
            offset: Number of scans to skip (for pagination).

        Returns:
            List[Scan]: List of scans.
        """
        query = """
            SELECT * FROM scans
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?
        """
        params = (limit, offset)

        rows = self.fetch_all(query, params)
        return [Scan(**row) for row in rows]

    
    def add_scan(self, scan):
        """
        Add a scan to the database.

        Args:
            scan: Scan object to add.

        Returns:
            int: ID of the added scan.
        """
        query = """
            INSERT INTO scans (
                name, top_level_path, start_time, end_time, status,
                files_scanned, files_unchanged, files_modified,
                files_corrupted, files_missing, files_new,
                checksum_method, scheduled_scan_id, error_message, notes,
                host_id, host_name, host_ip, host_display_name,
                storage_device_id, scan_duration_seconds, bitrot_clusters_detected, total_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            scan.name, scan.top_level_path, scan.start_time, scan.end_time, scan.status,
            scan.files_scanned, scan.files_unchanged, scan.files_modified,
            scan.files_corrupted, scan.files_missing, scan.files_new,
            scan.checksum_method, scan.scheduled_scan_id, scan.error_message, scan.notes,
            # v1.1.0 fields
            getattr(scan, 'host_id', None),
            getattr(scan, 'host_name', None),
            getattr(scan, 'host_ip', None),
            getattr(scan, 'host_display_name', None),
            getattr(scan, 'storage_device_id', None),
            getattr(scan, 'scan_duration_seconds', None),
            getattr(scan, 'bitrot_clusters_detected', 0),
            getattr(scan, 'total_size', 0)
        )

        cursor = self.execute_query(query, params)
        return cursor.lastrowid
    
    def update_scan(self, scan):
        """
        Update a scan in the database.
        
        Args:
            scan: Scan object to update.
            
        Returns:
            bool: Whether the update was successful.
        """
        query = """
            UPDATE scans SET
                name = ?, top_level_path = ?, end_time = ?, status = ?,
                files_scanned = ?, files_unchanged = ?, files_modified = ?,
                files_corrupted = ?, files_missing = ?, files_new = ?,
                error_message = ?, notes = ?, total_size = ?
            WHERE id = ?
        """
        params = (
            scan.name, scan.top_level_path, scan.end_time, scan.status,
            scan.files_scanned, scan.files_unchanged, scan.files_modified,
            scan.files_corrupted, scan.files_missing, scan.files_new,
            scan.error_message, scan.notes, scan.total_size, scan.id
        )
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    def delete_scan(self, scan_id):
        """
        Delete a scan from the database.
        
        Args:
            scan_id: ID of the scan to delete.
            
        Returns:
            bool: Whether the deletion was successful.
        """
        # This will cascade and delete associated checksums and scan errors
        query = "DELETE FROM scans WHERE id = ?"
        params = (scan_id,)
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    # ===== Checksums =====
    
    def get_checksum(self, id):
        """
        Get a checksum by ID.
        
        Args:
            id: Database ID.
            
        Returns:
            Checksum: The checksum, or None if not found.
        """
        query = "SELECT * FROM checksums WHERE id = ?"
        params = (id,)
        
        row = self.fetch_one(query, params)
        if row:
            return Checksum(**row)
        return None
    
    def get_file_checksums(self, file_id, limit=10):
        """
        Get checksums for a file.
        
        Args:
            file_id: ID of the file.
            limit: Maximum number of checksums to return.
            
        Returns:
            List[Checksum]: List of checksums.
        """
        query = """
            SELECT * FROM checksums 
            WHERE file_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        params = (file_id, limit)
        
        rows = self.fetch_all(query, params)
        return [Checksum(**row) for row in rows]
    
    def get_scan_checksums(self, scan_id, status=None, limit=100, offset=0):
        """
        Get checksums for a scan.
        
        Args:
            scan_id: ID of the scan.
            status: Filter by status.
            limit: Maximum number of checksums to return.
            offset: Offset for pagination.
            
        Returns:
            List[Checksum]: List of checksums.
        """
        if status:
            query = """
                SELECT * FROM checksums 
                WHERE scan_id = ? AND status = ?
                ORDER BY id 
                LIMIT ? OFFSET ?
            """
            params = (scan_id, status, limit, offset)
        else:
            query = """
                SELECT * FROM checksums 
                WHERE scan_id = ? 
                ORDER BY id 
                LIMIT ? OFFSET ?
            """
            params = (scan_id, limit, offset)
        
        rows = self.fetch_all(query, params)
        return [Checksum(**row) for row in rows]
    
    def add_checksum(self, checksum):
        """
        Add a checksum to the database.
        
        Args:
            checksum: Checksum object to add.
            
        Returns:
            int: ID of the added checksum.
        """
        query = """
            INSERT INTO checksums (
                file_id, scan_id, checksum_value, checksum_method,
                timestamp, status, previous_checksum_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            checksum.file_id, checksum.scan_id, checksum.checksum_value,
            checksum.checksum_method, checksum.timestamp, checksum.status,
            checksum.previous_checksum_id
        )
        
        cursor = self.execute_query(query, params)
        return cursor.lastrowid
    
    def update_checksum_status(self, checksum_id, status):
        """
        Update the status of a checksum.
        
        Args:
            checksum_id: ID of the checksum.
            status: New status.
            
        Returns:
            bool: Whether the update was successful.
        """
        query = "UPDATE checksums SET status = ? WHERE id = ?"
        params = (status, checksum_id)
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    # ===== Scheduled Scans =====
    
    def get_scheduled_scan(self, id):
        """
        Get a scheduled scan by ID.
        
        Args:
            id: Database ID.
            
        Returns:
            ScheduledScan: The scheduled scan, or None if not found.
        """
        query = "SELECT * FROM scheduled_scans WHERE id = ?"
        params = (id,)
        
        row = self.fetch_one(query, params)
        if row:
            return ScheduledScan(**row)
        return None
    
    def get_active_scheduled_scans(self):
        """
        Get all active scheduled scans.
        
        Returns:
            List[ScheduledScan]: List of scheduled scans.
        """
        query = "SELECT * FROM scheduled_scans WHERE is_active = 1"
        
        rows = self.fetch_all(query)
        return [ScheduledScan(**row) for row in rows]
    
    def get_all_scheduled_scans(self):
        """
        Get all scheduled scans.
        
        Returns:
            List[ScheduledScan]: List of scheduled scans.
        """
        query = "SELECT * FROM scheduled_scans ORDER BY name"
        
        rows = self.fetch_all(query)
        return [ScheduledScan(**row) for row in rows]
    
    def get_due_scheduled_scans(self, current_time=None):
        """
        Get scheduled scans that are due to run.
        
        Args:
            current_time: Current time.
            
        Returns:
            List[ScheduledScan]: List of scheduled scans.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        query = """
            SELECT * FROM scheduled_scans 
            WHERE is_active = 1 
            AND status = 'active' 
            AND next_run <= ?
            ORDER BY priority DESC
        """
        params = (current_time,)
        
        rows = self.fetch_all(query, params)
        return [ScheduledScan(**row) for row in rows]
    
    def add_scheduled_scan(self, scheduled_scan):
        """
        Add a scheduled scan to the database.
        
        Args:
            scheduled_scan: ScheduledScan object to add.
            
        Returns:
            int: ID of the added scheduled scan.
        """
        query = """
            INSERT INTO scheduled_scans (
                name, paths, frequency, parameters, last_run,
                next_run, status, priority, max_runtime, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            scheduled_scan.name, scheduled_scan.paths, scheduled_scan.frequency,
            scheduled_scan.parameters, scheduled_scan.last_run, scheduled_scan.next_run,
            scheduled_scan.status, scheduled_scan.priority, scheduled_scan.max_runtime,
            scheduled_scan.is_active
        )
        
        cursor = self.execute_query(query, params)
        return cursor.lastrowid
    
    def update_scheduled_scan(self, scheduled_scan):
        """
        Update a scheduled scan in the database.
        
        Args:
            scheduled_scan: ScheduledScan object to update.
            
        Returns:
            bool: Whether the update was successful.
        """
        query = """
            UPDATE scheduled_scans SET
                name = ?, paths = ?, frequency = ?, parameters = ?,
                last_run = ?, next_run = ?, status = ?, priority = ?,
                max_runtime = ?, is_active = ?
            WHERE id = ?
        """
        params = (
            scheduled_scan.name, scheduled_scan.paths, scheduled_scan.frequency,
            scheduled_scan.parameters, scheduled_scan.last_run, scheduled_scan.next_run,
            scheduled_scan.status, scheduled_scan.priority, scheduled_scan.max_runtime,
            scheduled_scan.is_active, scheduled_scan.id
        )
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    def delete_scheduled_scan(self, scheduled_scan_id):
        """
        Delete a scheduled scan from the database.
        
        Args:
            scheduled_scan_id: ID of the scheduled scan to delete.
            
        Returns:
            bool: Whether the deletion was successful.
        """
        query = "DELETE FROM scheduled_scans WHERE id = ?"
        params = (scheduled_scan_id,)
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    # ===== Scan Errors =====
    
    def add_scan_error(self, scan_error):
        """
        Add a scan error to the database.
        
        Args:
            scan_error: ScanError object to add.
            
        Returns:
            int: ID of the added scan error.
        """
        query = """
            INSERT INTO scan_errors (
                scan_id, file_path, error_type, error_message, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        """
        params = (
            scan_error.scan_id, scan_error.file_path, scan_error.error_type,
            scan_error.error_message, scan_error.timestamp
        )
        
        cursor = self.execute_query(query, params)
        return cursor.lastrowid
    
    def get_scan_errors(self, scan_id, limit=100, offset=0):
        """
        Get errors for a scan.
        
        Args:
            scan_id: ID of the scan.
            limit: Maximum number of errors to return.
            offset: Offset for pagination.
            
        Returns:
            List[ScanError]: List of scan errors.
        """
        query = """
            SELECT * FROM scan_errors 
            WHERE scan_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """
        params = (scan_id, limit, offset)
        
        rows = self.fetch_all(query, params)
        return [ScanError(**row) for row in rows]
    
    # ===== Configuration =====
    
    def get_configuration(self, key):
        """
        Get a configuration value.
        
        Args:
            key: Configuration key.
            
        Returns:
            Configuration: The configuration, or None if not found.
        """
        query = "SELECT key, value, type AS value_type, description, updated_at FROM configuration WHERE key = ?"
        params = (key,)
        
        row = self.fetch_one(query, params)
        if row:
            return Configuration(**row)
        return None
    
    def get_all_configuration(self):
        """
        Get all configuration values.
        
        Returns:
            dict: Dictionary of configuration values.
        """
        query = "SELECT key, value, type AS value_type, description, updated_at FROM configuration"
        
        rows = self.fetch_all(query)
        config_dict = {}
        for row in rows:
            config = Configuration(**row)
            config_dict[config.key] = config.get_typed_value()
        
        return config_dict
    
    def set_configuration(self, key, value, value_type=None, description=None):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key.
            value: Configuration value.
            value_type: Value type.
            description: Configuration description.
            
        Returns:
            bool: Whether the operation was successful.
        """
        # Get existing configuration to determine type if not provided
        if value_type is None or description is None:
            existing = self.get_configuration(key)
            if existing:
                value_type = value_type or existing.value_type
                description = description or existing.description
        
        # If value_type is still None, guess from the value
        if value_type is None:
            if isinstance(value, bool):
                value_type = "boolean"
                value = "true" if value else "false"
            elif isinstance(value, int):
                value_type = "integer"
                value = str(value)
            elif isinstance(value, float):
                value_type = "float"
                value = str(value)
            elif isinstance(value, (dict, list)):
                value_type = "json"
                value = json.dumps(value)
            else:
                value_type = "string"
                value = str(value)
        
        # Convert value to string if it's not already
        if not isinstance(value, str):
            if value_type == "json":
                value = json.dumps(value)
            else:
                value = str(value)
        
        # Update or insert
        query = """
            INSERT OR REPLACE INTO configuration 
            (key, value, type, description, updated_at) 
            VALUES (?, ?, ?, ?, ?)
        """
        params = (key, value, value_type, description, datetime.now(timezone.utc))
        
        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0
    
    # ===== Database Maintenance =====
    
    def vacuum(self):
        """
        Run VACUUM to reclaim space.
        
        Returns:
            bool: Whether the operation was successful.
        """
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute("VACUUM")
                conn.commit()
                return True
            except sqlite3.Error:
                return False
            finally:
                conn.close()
    
    def backup(self, backup_path=None):
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for the backup file.
            
        Returns:
            str: Path to the backup file.
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        with self.lock:
            source_conn = self.get_connection()
            try:
                dest_conn = sqlite3.connect(backup_path)
                source_conn.backup(dest_conn)
                dest_conn.close()
                return backup_path
            finally:
                source_conn.close()
    
    def get_database_info(self):
        """
        Get information about the database.
        
        Returns:
            dict: Database information.
        """
        result = {}
        
        # Get table counts
        tables = [
            "storage_devices", "files", "scans", "checksums",
            "scheduled_scans", "scan_errors", "configuration"
        ]
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            row = self.fetch_one(query)
            result[f"{table}_count"] = row["count"] if row else 0
        
        # Get database size
        try:
            result["database_size"] = Path(self.db_path).stat().st_size
        except OSError:
            result["database_size"] = 0
        
        # Get last scan date
        query = "SELECT MAX(start_time) as last_scan FROM scans"
        row = self.fetch_one(query)
        result["last_scan"] = row["last_scan"] if row and "last_scan" in row else None

        # Get first scan date
        query = "SELECT MIN(start_time) as first_scan FROM scans"
        row = self.fetch_one(query)
        result["first_scan"] = row["first_scan"] if row and "first_scan" in row else None

        return result

    def prune_old_scans(self, days_old):
        """
        Delete scans older than a specified number of days.

        Args:
            days_old: Number of days old.

        Returns:
            int: Number of scans deleted.
        """
        query = """
            DELETE FROM scans
            WHERE start_time < datetime('now', '-' || ? || ' days')
        """
        params = (days_old,)

        cursor = self.execute_query(query, params)
        return cursor.rowcount


    def reset(self):
        """Reset the database, keeping only configuration."""
        # Implementation needed
        return True

    def reset_scan_history(self):
        """
        Delete all scan history while preserving schedules and configuration.

        This deletes all checksums, scan errors, scans, and files, but keeps
        scheduled scans, configuration, and storage device information.

        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Count records to be deleted (for reporting)
                cursor.execute("SELECT COUNT(*) FROM checksums")
                checksum_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM scan_errors")
                error_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM scans")
                scan_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM files")
                file_count = cursor.fetchone()[0]

                # Delete all checksums (must be first due to foreign key constraints)
                cursor.execute("DELETE FROM checksums")

                # Delete all scan errors
                cursor.execute("DELETE FROM scan_errors")

                # Delete all scans
                cursor.execute("DELETE FROM scans")

                # Delete all files
                cursor.execute("DELETE FROM files")

                # Commit transaction
                conn.commit()

                return {
                    "success": True,
                    "checksums_deleted": checksum_count,
                    "errors_deleted": error_count,
                    "scans_deleted": scan_count,
                    "files_deleted": file_count
                }
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error resetting scan history: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def reset_full(self):
        """
        Reset database but keep configuration.

        This performs a scan history reset and additionally deletes all
        scheduled scans and storage devices. Only configuration is preserved.

        Returns:
            dict: Status dictionary with success flag and counts
        """
        # First, reset scan history
        result = self.reset_scan_history()
        if not result["success"]:
            return result

        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Count records to be deleted (for reporting)
                cursor.execute("SELECT COUNT(*) FROM scheduled_scans")
                scheduled_scan_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM storage_devices")
                device_count = cursor.fetchone()[0]

                # Delete all scheduled scans
                cursor.execute("DELETE FROM scheduled_scans")

                # Delete all storage devices
                cursor.execute("DELETE FROM storage_devices")

                # Commit transaction
                conn.commit()

                # Add the additional deletions to the result
                result.update({
                    "scheduled_scans_deleted": scheduled_scan_count,
                    "devices_deleted": device_count
                })

                return result
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error performing full reset: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def reset_complete(self):
        """
        Reset everything to default values.

        This completely resets the database, including configuration.
        Only schema and essential default values are preserved.

        Returns:
            dict: Status dictionary with success flag and counts
        """
        # First, backup configuration
        config_backup = {}
        try:
            # Get configuration to backup
            config_backup = self.get_all_configuration()
        except Exception as e:
            print(f"Warning: Could not backup configuration: {str(e)}")

        # Then perform full reset
        result = self.reset_full()
        if not result["success"]:
            return result

        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Get count of configuration items
                cursor.execute("SELECT COUNT(*) FROM configuration")
                config_count = cursor.fetchone()[0]

                # Delete all configuration (except schema_version)
                cursor.execute("DELETE FROM configuration WHERE key != 'schema_version'")

                # Re-initialize default configuration
                from .init_db import DEFAULT_CONFIG
                for key, value, type_str, description in DEFAULT_CONFIG:
                    # Skip schema_version as it was preserved
                    if key == 'schema_version':
                        continue

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO configuration
                        (key, value, type, description, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (key, value, type_str, description, datetime.now(timezone.utc))
                    )

                # Commit transaction
                conn.commit()

                # Add the additional deletions to the result
                result.update({
                    "configuration_reset": True,
                    "config_items_deleted": config_count
                })

                return result
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error performing complete reset: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def reindex(self):
        """
        Rebuild all database indexes.

        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Get a list of all indexes
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                """)

                indexes = [row[0] for row in cursor.fetchall()]
                reindexed_count = 0

                # Reindex each index
                for index in indexes:
                    cursor.execute(f"REINDEX {index}")
                    reindexed_count += 1

                conn.commit()
                return {
                    "success": True,
                    "indexes_reindexed": reindexed_count,
                    "index_names": indexes
                }
            except sqlite3.Error as e:
                print(f"Error reindexing database: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def clear_old_scans(self, days):
        """
        Delete scans older than the specified number of days.

        Args:
            days: Number of days old to delete

        Returns:
            dict: Status dictionary with success flag and count of deleted scans
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Find the cutoff date
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                cutoff_str = cutoff_date.isoformat()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Get list of scan IDs to delete
                cursor.execute("""
                    SELECT id FROM scans
                    WHERE start_time < ?
                """, (cutoff_str,))

                scan_ids = [row[0] for row in cursor.fetchall()]

                if not scan_ids:
                    # No scans to delete
                    return {
                        "success": True,
                        "scans_deleted": 0,
                        "message": f"No scans found older than {days} days"
                    }

                # Get counts for reporting
                cursor.execute("""
                    SELECT COUNT(*) FROM checksums
                    WHERE scan_id IN ({})
                """.format(','.join('?' * len(scan_ids))), scan_ids)
                checksum_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM scan_errors
                    WHERE scan_id IN ({})
                """.format(','.join('?' * len(scan_ids))), scan_ids)
                error_count = cursor.fetchone()[0]

                # Delete checksums for these scans
                cursor.execute("""
                    DELETE FROM checksums
                    WHERE scan_id IN ({})
                """.format(','.join('?' * len(scan_ids))), scan_ids)

                # Delete scan errors for these scans
                cursor.execute("""
                    DELETE FROM scan_errors
                    WHERE scan_id IN ({})
                """.format(','.join('?' * len(scan_ids))), scan_ids)

                # Delete the scans
                cursor.execute("""
                    DELETE FROM scans
                    WHERE id IN ({})
                """.format(','.join('?' * len(scan_ids))), scan_ids)

                # Commit transaction
                conn.commit()

                return {
                    "success": True,
                    "scans_deleted": len(scan_ids),
                    "checksums_deleted": checksum_count,
                    "errors_deleted": error_count
                }
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error clearing old scans: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def purge_missing_files(self, days):
        """
        Delete files marked as missing for longer than the specified days.

        Args:
            days: Number of days to consider a file as permanently missing

        Returns:
            dict: Status dictionary with success flag and count of purged files
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Find the cutoff date
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                cutoff_str = cutoff_date.isoformat()

                # Find files that have been marked as missing
                # and where the last_seen date is older than the cutoff
                cursor.execute("""
                    SELECT id FROM files
                    WHERE is_deleted = 1 AND last_seen < ?
                """, (cutoff_str,))

                file_ids = [row[0] for row in cursor.fetchall()]

                if not file_ids:
                    # No files to purge
                    return {
                        "success": True,
                        "files_purged": 0,
                        "message": f"No files found missing for more than {days} days"
                    }

                # Get counts for reporting
                cursor.execute("""
                    SELECT COUNT(*) FROM checksums
                    WHERE file_id IN ({})
                """.format(','.join('?' * len(file_ids))), file_ids)
                checksum_count = cursor.fetchone()[0]

                # Delete checksums for these files
                cursor.execute("""
                    DELETE FROM checksums
                    WHERE file_id IN ({})
                """.format(','.join('?' * len(file_ids))), file_ids)

                # Delete the files
                cursor.execute("""
                    DELETE FROM files
                    WHERE id IN ({})
                """.format(','.join('?' * len(file_ids))), file_ids)

                # Commit transaction
                conn.commit()

                return {
                    "success": True,
                    "files_purged": len(file_ids),
                    "checksums_deleted": checksum_count
                }
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error purging missing files: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def purge_orphaned_records(self):
        """
        Clean up orphaned records in the database.

        This removes:
        - Checksums without valid file or scan references
        - Scan errors without valid scan references

        Returns:
            dict: Status dictionary with success flag and counts
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Delete checksums with invalid file references
                cursor.execute("""
                    DELETE FROM checksums
                    WHERE file_id NOT IN (SELECT id FROM files)
                """)
                orphaned_checksums_file = cursor.rowcount

                # Delete checksums with invalid scan references
                cursor.execute("""
                    DELETE FROM checksums
                    WHERE scan_id NOT IN (SELECT id FROM scans)
                """)
                orphaned_checksums_scan = cursor.rowcount

                # Delete scan errors with invalid scan references
                cursor.execute("""
                    DELETE FROM scan_errors
                    WHERE scan_id NOT IN (SELECT id FROM scans)
                """)
                orphaned_errors = cursor.rowcount

                # Commit transaction
                conn.commit()

                return {
                    "success": True,
                    "orphaned_checksums_removed": orphaned_checksums_file + orphaned_checksums_scan,
                    "orphaned_errors_removed": orphaned_errors
                }
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error purging orphaned records: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def create_backup(self, name=None):
        """
        Create a named backup of the database.

        Args:
            name: Optional name for the backup

        Returns:
            dict: Status dictionary with backup information
        """
        # Create a backup directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        backup_dir = os.path.join(db_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # Generate a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create backup filename
        if name:
            # Sanitize name to be filesystem-safe
            name = ''.join(c for c in name if c.isalnum() or c in ' _-').strip()
            name = name.replace(' ', '_')
            backup_filename = f"{timestamp}_{name}.db"
        else:
            backup_filename = f"{timestamp}_backup.db"

        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            # Perform the backup
            with self.lock:
                source_conn = self.get_connection()
                try:
                    dest_conn = sqlite3.connect(backup_path)
                    source_conn.backup(dest_conn)
                    dest_conn.close()

                    # Get backup file size
                    backup_size = os.path.getsize(backup_path)

                    # Create a metadata record for this backup
                    metadata = {
                        "id": timestamp,  # Use timestamp as ID
                        "name": name or "Auto backup",
                        "date": timestamp,
                        "size": backup_size,
                        "path": backup_path,
                        "type": "manual" if name else "auto"
                    }

                    # Store metadata in backups registry
                    self._save_backup_metadata(metadata)

                    return {
                        "success": True,
                        "backup_id": timestamp,
                        "backup_name": name or "Auto backup",
                        "backup_date": timestamp,
                        "backup_size": backup_size,
                        "backup_path": backup_path
                    }
                finally:
                    source_conn.close()
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _save_backup_metadata(self, metadata):
        """
        Save backup metadata to the backup registry file.

        Args:
            metadata: Dictionary with backup metadata
        """
        # Get the backup registry file path
        db_dir = os.path.dirname(self.db_path)
        backup_dir = os.path.join(db_dir, "backups")
        registry_path = os.path.join(backup_dir, "backup_registry.json")

        # Load existing registry or create new one
        registry = []
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
            except json.JSONDecodeError:
                # If the file is corrupted, start with an empty registry
                registry = []

        # Add or update this backup in the registry
        existing_index = next((i for i, x in enumerate(registry) if x.get('id') == metadata['id']), None)
        if existing_index is not None:
            registry[existing_index] = metadata
        else:
            registry.append(metadata)

        # Write registry back to file
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

    def list_backups(self):
        """
        List all available backups.

        Returns:
            list: List of backup metadata dictionaries
        """
        # Get the backup registry file path
        db_dir = os.path.dirname(self.db_path)
        backup_dir = os.path.join(db_dir, "backups")
        registry_path = os.path.join(backup_dir, "backup_registry.json")

        # Load existing registry or return empty list
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)

                    # Sort by date (newest first)
                    registry.sort(key=lambda x: x.get('date', ''), reverse=True)

                    return {
                        "success": True,
                        "backups": registry
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Error reading backup registry: {str(e)}",
                    "backups": []
                }

        return {
            "success": True,
            "backups": []
        }

    def restore_backup(self, backup_id):
        """
        Restore database from a backup.

        Args:
            backup_id: ID of the backup to restore

        Returns:
            dict: Status dictionary
        """
        # Get backup metadata
        registry_result = self.list_backups()
        if not registry_result["success"]:
            return registry_result

        registry = registry_result["backups"]
        backup_metadata = next((x for x in registry if x.get('id') == backup_id), None)

        if not backup_metadata:
            return {
                "success": False,
                "error": f"Backup with ID {backup_id} not found"
            }

        backup_path = backup_metadata.get('path')

        if not backup_path or not os.path.exists(backup_path):
            return {
                "success": False,
                "error": f"Backup file not found at {backup_path}"
            }

        try:
            # Create a temporary file for the current database
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_file.close()
            temp_path = temp_file.name

            # Copy current database to temp file as a safety measure
            shutil.copy2(self.db_path, temp_path)

            # Replace current database with backup
            with self.lock:
                # Close any open connections
                # This is necessary to replace the file on Windows
                time.sleep(0.5)  # Brief pause to ensure connections are released

                # Copy backup to the database path
                shutil.copy2(backup_path, self.db_path)

                return {
                    "success": True,
                    "message": f"Database restored from backup {backup_metadata.get('name')}",
                    "temp_backup_path": temp_path
                }
        except Exception as e:
            # Try to restore from temporary backup if the restore failed
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    shutil.copy2(temp_path, self.db_path)
                    os.unlink(temp_path)
            except Exception as restore_error:
                print(f"Error restoring from temp backup: {str(restore_error)}")

            print(f"Error restoring backup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def delete_backup(self, backup_id):
        """
        Delete a backup.

        Args:
            backup_id: ID of the backup to delete

        Returns:
            dict: Status dictionary
        """
        # Get backup metadata
        registry_result = self.list_backups()
        if not registry_result["success"]:
            return registry_result

        registry = registry_result["backups"]
        backup_metadata = next((x for x in registry if x.get('id') == backup_id), None)

        if not backup_metadata:
            return {
                "success": False,
                "error": f"Backup with ID {backup_id} not found"
            }

        backup_path = backup_metadata.get('path')

        try:
            # Delete the backup file
            if backup_path and os.path.exists(backup_path):
                os.unlink(backup_path)

            # Get the backup registry file path
            db_dir = os.path.dirname(self.db_path)
            backup_dir = os.path.join(db_dir, "backups")
            registry_path = os.path.join(backup_dir, "backup_registry.json")

            # Update registry
            if os.path.exists(registry_path):
                with open(registry_path, 'r') as f:
                    registry = json.load(f)

                # Remove the backup from the registry
                registry = [x for x in registry if x.get('id') != backup_id]

                # Write updated registry
                with open(registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)

            return {
                "success": True,
                "message": f"Backup {backup_metadata.get('name')} deleted successfully"
            }
        except Exception as e:
            print(f"Error deleting backup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_backup_settings(self):
        """
        Get automatic backup settings.

        Returns:
            dict: Backup settings
        """
        config = self.get_all_configuration()

        return {
            "success": True,
            "enabled": config.get('db_auto_backup', True),
            "frequency": config.get('db_backup_frequency', 'weekly'),
            "retain_count": config.get('db_backup_retain', 10)
        }

    def set_backup_settings(self, enabled, frequency, retain_count):
        """
        Configure automatic backup settings.

        Args:
            enabled: Whether automatic backups are enabled
            frequency: Backup frequency (daily, weekly, monthly)
            retain_count: Number of backups to keep

        Returns:
            dict: Status dictionary
        """
        try:
            # Validate frequency
            valid_frequencies = ['daily', 'weekly', 'monthly']
            if frequency not in valid_frequencies:
                return {
                    "success": False,
                    "error": f"Invalid frequency. Must be one of {', '.join(valid_frequencies)}"
                }

            # Validate retain_count
            try:
                retain_count = int(retain_count)
                if retain_count < 1 or retain_count > 100:
                    return {
                        "success": False,
                        "error": "Retain count must be between 1 and 100"
                    }
            except ValueError:
                return {
                    "success": False,
                    "error": "Retain count must be an integer"
                }

            # Update settings
            self.set_configuration('db_auto_backup', str(bool(enabled)).lower(), 'boolean', 'Enable automatic database backups')
            self.set_configuration('db_backup_frequency', frequency, 'string', 'How often to perform database backups')
            self.set_configuration('db_backup_retain', str(retain_count), 'integer', 'Number of backup copies to retain')

            # Enforce retention policy
            self._enforce_backup_retention(retain_count)

            return {
                "success": True,
                "message": "Backup settings updated successfully",
                "enabled": enabled,
                "frequency": frequency,
                "retain_count": retain_count
            }
        except Exception as e:
            print(f"Error setting backup settings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _enforce_backup_retention(self, retain_count):
        """
        Enforce backup retention policy by deleting oldest backups.

        Args:
            retain_count: Number of backups to keep
        """
        # Get all backups
        registry_result = self.list_backups()
        if not registry_result["success"] or not registry_result["backups"]:
            return

        registry = registry_result["backups"]

        # If we have more backups than the retention count, delete the oldest ones
        if len(registry) > retain_count:
            # Sort by date (oldest first)
            registry.sort(key=lambda x: x.get('date', ''))

            # Delete the oldest backups
            for i in range(len(registry) - retain_count):
                self.delete_backup(registry[i].get('id'))

    def run_integrity_check(self):
        """
        Run an integrity check on the database.

        Returns:
            dict: Status dictionary with integrity check results
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()

                # Run integrity check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchall()

                # If the result is just ["ok"], the database is fine
                if len(result) == 1 and result[0][0] == "ok":
                    return {
                        "success": True,
                        "integrity_status": "ok",
                        "message": "Database integrity check passed"
                    }
                else:
                    # Collect error messages
                    errors = [row[0] for row in result]
                    return {
                        "success": True,
                        "integrity_status": "error",
                        "message": "Database integrity check failed",
                        "errors": errors
                    }
            except sqlite3.Error as e:
                print(f"Error running integrity check: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def repair_database(self):
        """
        Attempt to repair the database by dumping and recreating it.

        Returns:
            dict: Status dictionary
        """
        try:
            # Create a backup first
            backup_result = self.create_backup("pre_repair_backup")
            if not backup_result["success"]:
                return backup_result

            # Create temporary files for dump and new database
            temp_dump = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
            temp_dump.close()
            temp_dump_path = temp_dump.name

            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            temp_db_path = temp_db.name

            # Dump the database schema and contents
            with self.lock:
                conn = self.get_connection()
                try:
                    # Dump to SQL file
                    with open(temp_dump_path, 'w') as f:
                        for line in conn.iterdump():
                            f.write(f"{line}\n")
                finally:
                    conn.close()

            # Create a new database from the dump
            conn = sqlite3.connect(temp_db_path)
            try:
                with open(temp_dump_path, 'r') as f:
                    script = f.read()
                    conn.executescript(script)

                conn.close()

                # Replace the original database with the repaired one
                with self.lock:
                    # Close any open connections
                    time.sleep(0.5)  # Brief pause to ensure connections are released

                    # Copy repaired database to the database path
                    shutil.copy2(temp_db_path, self.db_path)

                return {
                    "success": True,
                    "message": "Database repair completed successfully",
                    "backup_id": backup_result.get("backup_id")
                }
            except Exception as e:
                # If repair fails, don't replace the original database
                print(f"Error repairing database: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "backup_id": backup_result.get("backup_id")
                }
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_dump_path)
                    os.unlink(temp_db_path)
                except Exception as e:
                    print(f"Error cleaning up temporary files: {str(e)}")
        except Exception as e:
            print(f"Error during database repair: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def export_schema(self):
        """
        Export the database schema to a SQL file.

        Returns:
            dict: Status dictionary with path to the exported schema
        """
        try:
            # Create export directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            export_dir = os.path.join(db_dir, "exports")
            os.makedirs(export_dir, exist_ok=True)

            # Generate a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create export filename
            export_path = os.path.join(export_dir, f"schema_export_{timestamp}.sql")

            with self.lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()

                    # Get all table definitions
                    cursor.execute("""
                        SELECT name, sql FROM sqlite_master
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)

                    tables = cursor.fetchall()

                    # Get all index definitions
                    cursor.execute("""
                        SELECT name, sql FROM sqlite_master
                        WHERE type='index' AND name NOT LIKE 'sqlite_%'
                    """)

                    indexes = cursor.fetchall()

                    # Get all trigger definitions
                    cursor.execute("""
                        SELECT name, sql FROM sqlite_master
                        WHERE type='trigger' AND name NOT LIKE 'sqlite_%'
                    """)

                    triggers = cursor.fetchall()

                    # Get all view definitions
                    cursor.execute("""
                        SELECT name, sql FROM sqlite_master
                        WHERE type='view' AND name NOT LIKE 'sqlite_%'
                    """)

                    views = cursor.fetchall()

                    # Write schema to file
                    with open(export_path, 'w') as f:
                        # Write header
                        f.write("-- SQLite schema export\n")
                        f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")

                        # Write PRAGMA statements
                        f.write("PRAGMA foreign_keys = ON;\n")
                        f.write("PRAGMA journal_mode = WAL;\n\n")

                        # Write tables
                        f.write("-- Tables\n")
                        for name, sql in tables:
                            if sql:
                                f.write(f"{sql};\n\n")

                        # Write views
                        if views:
                            f.write("-- Views\n")
                            for name, sql in views:
                                if sql:
                                    f.write(f"{sql};\n\n")

                        # Write indexes
                        if indexes:
                            f.write("-- Indexes\n")
                            for name, sql in indexes:
                                if sql:
                                    f.write(f"{sql};\n\n")

                        # Write triggers
                        if triggers:
                            f.write("-- Triggers\n")
                            for name, sql in triggers:
                                if sql:
                                    f.write(f"{sql};\n\n")

                    return {
                        "success": True,
                        "export_path": export_path,
                        "tables_count": len(tables),
                        "indexes_count": len(indexes),
                        "triggers_count": len(triggers),
                        "views_count": len(views)
                    }
                finally:
                    conn.close()
        except Exception as e:
            print(f"Error exporting schema: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def export_all_data(self):
        """
        Export all database data to a SQL file.

        Returns:
            dict: Status dictionary with path to the exported data
        """
        try:
            # Create export directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            export_dir = os.path.join(db_dir, "exports")
            os.makedirs(export_dir, exist_ok=True)

            # Generate a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create export filename
            export_path = os.path.join(export_dir, f"data_export_{timestamp}.sql")

            with self.lock:
                conn = self.get_connection()
                try:
                    # Dump entire database to SQL file
                    with open(export_path, 'w') as f:
                        for line in conn.iterdump():
                            f.write(f"{line}\n")

                    return {
                        "success": True,
                        "export_path": export_path,
                        "message": "All database data exported successfully"
                    }
                finally:
                    conn.close()
        except Exception as e:
            print(f"Error exporting data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def export_configuration(self):
        """
        Export database configuration to a JSON file.

        Returns:
            dict: Status dictionary with path to the exported configuration
        """
        try:
            # Create export directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            export_dir = os.path.join(db_dir, "exports")
            os.makedirs(export_dir, exist_ok=True)

            # Generate a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create export filename
            export_path = os.path.join(export_dir, f"config_export_{timestamp}.json")

            # Get configuration
            config = self.get_all_configuration()

            # Write to JSON file
            with open(export_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)

            return {
                "success": True,
                "export_path": export_path,
                "config_items": len(config),
                "message": "Configuration exported successfully"
            }
        except Exception as e:
            print(f"Error exporting configuration: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def count_scans(self):
        """
        Count the total number of scans in the database.

        Returns:
            int: Number of scans
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM scans")
                count = cursor.fetchone()[0]
                return count
            except sqlite3.Error as e:
                print(f"Error counting scans: {str(e)}")
                return 0
            finally:
                conn.close()

    def check_for_active_scans(self):
        """
        Check if there are any running scans.

        Returns:
            dict: Status dictionary with active scan info
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, top_level_path, start_time
                    FROM scans
                    WHERE status = 'running'
                """)
                active_scans = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "top_level_path": row[2],
                        "start_time": row[3]
                    }
                    for row in cursor.fetchall()
                ]

                return {
                    "success": True,
                    "active_scan_count": len(active_scans),
                    "active_scans": active_scans
                }
            except sqlite3.Error as e:
                print(f"Error checking for active scans: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    def mark_scans_as_aborted(self):
        """
        Mark all running scans as aborted.

        Returns:
            dict: Status dictionary with count of aborted scans
        """
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE scans
                    SET status = 'aborted', end_time = CURRENT_TIMESTAMP
                    WHERE status = 'running'
                """)

                conn.commit()
                return {
                    "success": True,
                    "scans_aborted": cursor.rowcount
                }
            except sqlite3.Error as e:
                print(f"Error marking scans as aborted: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                conn.close()

    # ===== Scan Hosts (v1.1.0) =====

    def get_scan_host(self, host_id=None, host_ip=None):
        """
        Get a scan host by ID or IP.

        Args:
            host_id: Database ID.
            host_ip: Host IP address.

        Returns:
            ScanHost: The scan host, or None if not found.
        """
        if host_id is not None:
            query = "SELECT * FROM scan_hosts WHERE id = ?"
            params = (host_id,)
        elif host_ip is not None:
            query = "SELECT * FROM scan_hosts WHERE host_ip = ?"
            params = (host_ip,)
        else:
            return None

        row = self.fetch_one(query, params)
        if row:
            from .models import ScanHost
            return ScanHost(**row)
        return None

    def get_all_scan_hosts(self):
        """
        Get all scan hosts with device and scan counts.

        Returns:
            List[dict]: List of scan hosts with additional statistics.
        """
        query = """
            SELECT
                sh.*,
                COUNT(DISTINCT sd.id) as device_count,
                COUNT(DISTINCT s.id) as scan_count,
                MAX(s.start_time) as last_scan_time
            FROM scan_hosts sh
            LEFT JOIN storage_devices sd ON sh.id = sd.host_id
            LEFT JOIN scans s ON sh.id = s.host_id
            GROUP BY sh.id
            ORDER BY sh.host_display_name
        """

        rows = self.fetch_all(query)
        return rows

    def add_scan_host(self, scan_host):
        """
        Add a scan host to the database.

        Args:
            scan_host: ScanHost object to add.

        Returns:
            int: ID of the added scan host.
        """
        query = """
            INSERT INTO scan_hosts (
                hostname, host_ip, display_name, first_seen, last_seen,
                os_type, os_version, architecture, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            scan_host.hostname, scan_host.host_ip, scan_host.display_name,
            scan_host.first_seen, scan_host.last_seen, scan_host.os_type,
            scan_host.os_version, scan_host.architecture, scan_host.is_active
        )

        cursor = self.execute_query(query, params)
        return cursor.lastrowid

    def update_scan_host(self, scan_host):
        """
        Update a scan host in the database.

        Args:
            scan_host: ScanHost object to update.

        Returns:
            bool: Whether the update was successful.
        """
        query = """
            UPDATE scan_hosts SET
                hostname = ?, host_ip = ?, display_name = ?,
                last_seen = ?, os_type = ?, os_version = ?,
                architecture = ?, is_active = ?
            WHERE id = ?
        """
        params = (
            scan_host.hostname, scan_host.host_ip, scan_host.display_name,
            scan_host.last_seen, scan_host.os_type, scan_host.os_version,
            scan_host.architecture, scan_host.is_active, scan_host.id
        )

        cursor = self.execute_query(query, params)
        return cursor.rowcount > 0

    # ===== Bitrot Events (v1.1.0) =====

    def get_bitrot_event(self, id):
        """
        Get a bitrot event by ID.

        Args:
            id: Database ID.

        Returns:
            BitrotEvent: The bitrot event, or None if not found.
        """
        query = "SELECT * FROM bitrot_events WHERE id = ?"
        params = (id,)

        row = self.fetch_one(query, params)
        if row:
            from .models import BitrotEvent
            return BitrotEvent(**row)
        return None

    def get_bitrot_events(self, scan_id=None, cluster_id=None, limit=100, offset=0):
        """
        Get bitrot events, optionally filtered by scan or cluster.

        Args:
            scan_id: Filter by scan ID.
            cluster_id: Filter by cluster ID.
            limit: Maximum number of events to return.
            offset: Offset for pagination.

        Returns:
            List[BitrotEvent]: List of bitrot events.
        """
        if scan_id is not None:
            query = """
                SELECT * FROM bitrot_events
                WHERE scan_id = ?
                ORDER BY detected_at DESC
                LIMIT ? OFFSET ?
            """
            params = (scan_id, limit, offset)
        elif cluster_id is not None:
            query = """
                SELECT * FROM bitrot_events
                WHERE cluster_id = ?
                ORDER BY detected_at DESC
                LIMIT ? OFFSET ?
            """
            params = (cluster_id, limit, offset)
        else:
            query = """
                SELECT * FROM bitrot_events
                ORDER BY detected_at DESC
                LIMIT ? OFFSET ?
            """
            params = (limit, offset)

        rows = self.fetch_all(query, params)
        from .models import BitrotEvent
        return [BitrotEvent(**row) for row in rows]

    def add_bitrot_event(self, bitrot_event):
        """
        Add a bitrot event to the database.

        Args:
            bitrot_event: BitrotEvent object to add.

        Returns:
            int: ID of the added bitrot event.
        """
        query = """
            INSERT INTO bitrot_events (
                scan_id, file_id, checksum_id, cluster_id,
                detected_at, event_type, severity, file_path,
                expected_checksum, actual_checksum, file_size,
                last_modified, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            bitrot_event.scan_id, bitrot_event.file_id, bitrot_event.checksum_id,
            bitrot_event.cluster_id, bitrot_event.detected_at, bitrot_event.event_type,
            bitrot_event.severity, bitrot_event.file_path, bitrot_event.expected_checksum,
            bitrot_event.actual_checksum, bitrot_event.file_size, bitrot_event.last_modified,
            bitrot_event.metadata
        )

        cursor = self.execute_query(query, params)
        return cursor.lastrowid

    # ===== Device Health History (v1.1.0) =====

    def get_device_health_history(self, storage_device_id, limit=100, offset=0):
        """
        Get health history for a storage device.

        Args:
            storage_device_id: ID of the storage device.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List[DeviceHealthHistory]: List of health history records.
        """
        query = """
            SELECT * FROM device_health_history
            WHERE storage_device_id = ?
            ORDER BY recorded_at DESC
            LIMIT ? OFFSET ?
        """
        params = (storage_device_id, limit, offset)

        rows = self.fetch_all(query, params)
        from .models import DeviceHealthHistory
        return [DeviceHealthHistory(**row) for row in rows]

    def add_device_health_history(self, health_record):
        """
        Add a device health history record.

        Args:
            health_record: DeviceHealthHistory object to add.

        Returns:
            int: ID of the added health record.
        """
        query = """
            INSERT INTO device_health_history (
                storage_device_id, recorded_at, health_status,
                total_files, corrupted_files, missing_files,
                read_errors, write_errors, temperature,
                disk_usage_percent, performance_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            health_record.storage_device_id, health_record.recorded_at,
            health_record.health_status, health_record.total_files,
            health_record.corrupted_files, health_record.missing_files,
            health_record.read_errors, health_record.write_errors,
            health_record.temperature, health_record.disk_usage_percent,
            health_record.performance_score, health_record.notes
        )

        cursor = self.execute_query(query, params)
        return cursor.lastrowid

    # ===== Enhanced Storage Device Queries (v1.1.0) =====

    def get_storage_devices_with_host_info(self):
        """
        Get all storage devices with host information.

        Returns:
            List[dict]: Storage devices with host details.
        """
        query = """
            SELECT
                sd.*,
                sh.host_name as hostname,
                sh.host_display_name,
                sh.host_type,
                sh.connection_status as host_is_active
            FROM storage_devices sd
            LEFT JOIN scan_hosts sh ON sd.host_id = sh.id
            ORDER BY sh.host_display_name, sd.name
        """

        rows = self.fetch_all(query)
        return rows

    # ===== Enhanced Scan Queries (v1.1.0) =====

    def get_scans_with_host_info(self, limit=10, offset=0):
        """
        Get scans with host information.

        Args:
            limit: Maximum number of scans to return.
            offset: Offset for pagination.

        Returns:
            List[dict]: Scans with host details.
        """
        query = """
            SELECT
                s.*,
                sh.host_name as hostname,
                sh.host_display_name,
                sh.host_type,
                sd.name as storage_device_name
            FROM scans s
            LEFT JOIN scan_hosts sh ON s.host_id = sh.id
            LEFT JOIN storage_devices sd ON s.storage_device_id = sd.id
            ORDER BY s.start_time DESC
            LIMIT ? OFFSET ?
        """
        params = (limit, offset)

        rows = self.fetch_all(query, params)
        return rows
