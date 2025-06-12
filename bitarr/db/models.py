"""
Database models for Bitarr.
"""
import json
import sqlite3
import time
from datetime import datetime, timezone

class StorageDevice:
    """Represents a storage device in the system."""
    
    def __init__(
        self, id=None, name=None, mount_point=None, 
        device_type=None, total_size=None, used_size=None,
        first_seen=None, last_seen=None, is_connected=True, 
        device_id=None
    ):
        self.id = id
        self.name = name
        self.mount_point = mount_point
        self.device_type = device_type
        self.total_size = total_size
        self.used_size = used_size
        self.first_seen = first_seen or datetime.now(timezone.utc)
        self.last_seen = last_seen or datetime.now(timezone.utc)
        self.is_connected = is_connected
        self.device_id = device_id
    
    @classmethod
    def from_row(cls, row):
        """Create a StorageDevice object from a database row."""
        if not row:
            return None
        
        return cls(
            id=row[0],
            name=row[1],
            mount_point=row[2],
            device_type=row[3],
            total_size=row[4],
            used_size=row[5],
            first_seen=row[6],
            last_seen=row[7],
            is_connected=bool(row[8]),
            device_id=row[9]
        )
    
    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "mount_point": self.mount_point,
            "device_type": self.device_type,
            "total_size": self.total_size,
            "used_size": self.used_size,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_connected": self.is_connected,
            "device_id": self.device_id
        }

class File:
    """Represents a file tracked in the system."""
    
    def __init__(
        self, id=None, path=None, filename=None, 
        directory=None, storage_device_id=None,
        size=None, last_modified=None, file_type=None,
        first_seen=None, last_seen=None, is_deleted=False
    ):
        self.id = id
        self.path = path
        self.filename = filename
        self.directory = directory
        self.storage_device_id = storage_device_id
        self.size = size
        self.last_modified = last_modified
        self.file_type = file_type
        self.first_seen = first_seen or datetime.now(timezone.utc)
        self.last_seen = last_seen or datetime.now(timezone.utc)
        self.is_deleted = is_deleted
    
    @classmethod
    def from_row(cls, row):
        """Create a File object from a database row."""
        if not row:
            return None
        
        return cls(
            id=row[0],
            path=row[1],
            filename=row[2],
            directory=row[3],
            storage_device_id=row[4],
            size=row[5],
            last_modified=row[6],
            file_type=row[7],
            first_seen=row[8],
            last_seen=row[9],
            is_deleted=bool(row[10])
        )
    
    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "path": self.path,
            "filename": self.filename,
            "directory": self.directory,
            "storage_device_id": self.storage_device_id,
            "size": self.size,
            "last_modified": self.last_modified,
            "file_type": self.file_type,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_deleted": self.is_deleted
        }

class Scan:
    """Represents a scan operation."""
    
    def __init__(
        self, id=None, name=None, top_level_path=None,
        start_time=None, end_time=None, status="running",
        files_scanned=0, files_unchanged=0, files_modified=0,
        files_corrupted=0, files_missing=0, files_new=0,
        checksum_method="sha256", scheduled_scan_id=None,
        error_message=None, notes=None
    ):
        self.id = id
        self.name = name
        self.top_level_path = top_level_path
        self.start_time = start_time or datetime.now(timezone.utc)
        self.end_time = end_time
        self.status = status
        self.files_scanned = files_scanned
        self.files_unchanged = files_unchanged
        self.files_modified = files_modified
        self.files_corrupted = files_corrupted
        self.files_missing = files_missing
        self.files_new = files_new
        self.checksum_method = checksum_method
        self.scheduled_scan_id = scheduled_scan_id
        self.error_message = error_message
        self.notes = notes
    
    @classmethod
    def from_row(cls, row):
        """Create a Scan object from a database row."""
        if not row:
            return None
        
        return cls(
            id=row[0],
            name=row[1],
            top_level_path=row[2],
            start_time=row[3],
            end_time=row[4],
            status=row[5],
            files_scanned=row[6],
            files_unchanged=row[7],
            files_modified=row[8],
            files_corrupted=row[9],
            files_missing=row[10],
            files_new=row[11],
            checksum_method=row[12],
            scheduled_scan_id=row[13],
            error_message=row[14],
            notes=row[15]
        )
    
    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "top_level_path": self.top_level_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "files_scanned": self.files_scanned,
            "files_unchanged": self.files_unchanged,
            "files_modified": self.files_modified,
            "files_corrupted": self.files_corrupted,
            "files_missing": self.files_missing,
            "files_new": self.files_new,
            "checksum_method": self.checksum_method,
            "scheduled_scan_id": self.scheduled_scan_id,
            "error_message": self.error_message,
            "notes": self.notes
        }

class Checksum:
    """Represents a file checksum."""
    
    def __init__(
        self, id=None, file_id=None, scan_id=None,
        checksum_value=None, checksum_method="sha256",
        timestamp=None, status="new", previous_checksum_id=None
    ):
        self.id = id
        self.file_id = file_id
        self.scan_id = scan_id
        self.checksum_value = checksum_value
        self.checksum_method = checksum_method
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.status = status
        self.previous_checksum_id = previous_checksum_id
    
    @classmethod
    def from_row(cls, row):
        """Create a Checksum object from a database row."""
        if not row:
            return None
        
        return cls(
            id=row[0],
            file_id=row[1],
            scan_id=row[2],
            checksum_value=row[3],
            checksum_method=row[4],
            timestamp=row[5],
            status=row[6],
            previous_checksum_id=row[7]
        )
    
    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "scan_id": self.scan_id,
            "checksum_value": self.checksum_value,
            "checksum_method": self.checksum_method,
            "timestamp": self.timestamp,
            "status": self.status,
            "previous_checksum_id": self.previous_checksum_id
        }

class ScheduledScan:
    """Represents a scheduled scan configuration."""
    
    def __init__(
        self, id=None, name=None, paths=None,
        frequency=None, parameters=None, last_run=None,
        next_run=None, status="active", priority=0,
        max_runtime=None, is_active=True, created_at=None
    ):
        self.id = id
        self.name = name
        self.paths = paths if isinstance(paths, str) else json.dumps(paths or [])
        self.frequency = frequency
        self.parameters = parameters if isinstance(parameters, str) else json.dumps(parameters or {})
        self.last_run = last_run
        self.next_run = next_run
        self.status = status
        self.priority = priority
        self.max_runtime = max_runtime
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)
    
    @classmethod
    def from_row(cls, row):
        """Create a ScheduledScan object from a database row."""
        if not row:
            return None
        
        return cls(
            id=row[0],
            name=row[1],
            paths=row[2],
            frequency=row[3],
            parameters=row[4],
            last_run=row[5],
            next_run=row[6],
            status=row[7],
            priority=row[8],
            max_runtime=row[9],
            is_active=bool(row[10]),
            created_at=row[11]
        )

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "paths": json.loads(self.paths) if isinstance(self.paths, str) else self.paths,
            "frequency": self.frequency,
            "parameters": json.loads(self.parameters) if isinstance(self.parameters, str) else self.parameters,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "status": self.status,
            "priority": self.priority,
            "max_runtime": self.max_runtime,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

class ScanError:
    """Represents an error that occurred during a scan."""
    
    def __init__(
        self, id=None, scan_id=None, file_path=None,
        error_type=None, error_message=None, timestamp=None
    ):
        self.id = id
        self.scan_id = scan_id
        self.file_path = file_path
        self.error_type = error_type
        self.error_message = error_message
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    @classmethod
    def from_row(cls, row):
        """Create a ScanError object from a database row."""
        if not row:
            return None
        
        return cls(
            id=row[0],
            scan_id=row[1],
            file_path=row[2],
            error_type=row[3],
            error_message=row[4],
            timestamp=row[5]
        )
    
    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "file_path": self.file_path,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }

class Configuration:
    """Represents a configuration setting."""

    def __init__(
        self, key=None, value=None, value_type=None,
        description=None, updated_at=None
    ):
        self.key = key
        self.value = value
        self.value_type = value_type
        self.description = description
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @classmethod
    def from_row(cls, row):
        """Create a Configuration object from a database row."""
        if not row:
            return None

        return cls(
            key=row[0],
            value=row[1],
            value_type=row[2],
            description=row[3],
            updated_at=row[4]
        )

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "value_type": self.value_type,
            "description": self.description,
            "updated_at": self.updated_at
        }

    def get_typed_value(self):
        """Get the value converted to its appropriate type."""
        if self.value_type == "integer":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "boolean":
            return self.value.lower() in ("1", "true", "yes", "y", "t")
        elif self.value_type == "json":
            return json.loads(self.value)
        else:  # string or other
            return self.value
