"""
Database models for Bitarr v1.1.0
Storage-device-centric architecture with distributed client support
"""
import json
import sqlite3
import time
from datetime import datetime, timezone

# v1.1.0 NEW: Scan host model for machine tracking
class ScanHost:
    """Represents a machine running Bitarr client."""

    def __init__(
        self, id=None, host_name=None, host_ip=None,
        host_display_name=None, host_type=None, client_version='1.1.0',
        connection_status='offline', last_seen=None, auth_token=None,
        created_at=None, updated_at=None
    ):
        self.id = id
        self.host_name = host_name
        self.host_ip = host_ip
        self.host_display_name = host_display_name
        self.host_type = host_type
        self.client_version = client_version
        self.connection_status = connection_status
        self.last_seen = last_seen
        self.auth_token = auth_token
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @classmethod
    def from_row(cls, row):
        """Create a ScanHost object from a database row."""
        if not row:
            return None

        return cls(
            id=row[0] if len(row) > 0 else None,
            host_name=row[1] if len(row) > 1 else None,
            host_ip=row[2] if len(row) > 2 else None,
            host_display_name=row[3] if len(row) > 3 else None,
            host_type=row[4] if len(row) > 4 else None,
            client_version=row[5] if len(row) > 5 else '1.1.0',
            connection_status=row[6] if len(row) > 6 else 'offline',
            last_seen=row[7] if len(row) > 7 else None,
            auth_token=row[8] if len(row) > 8 else None,
            created_at=row[9] if len(row) > 9 else None,
            updated_at=row[10] if len(row) > 10 else None
        )

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "host_name": self.host_name,
            "host_ip": self.host_ip,
            "host_display_name": self.host_display_name,
            "host_type": self.host_type,
            "client_version": self.client_version,
            "connection_status": self.connection_status,
            "last_seen": self.last_seen,
            "auth_token": self.auth_token,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class StorageDevice:
    """Represents a storage device in the system (enhanced for v1.1.0)."""

    def __init__(
        self, id=None, name=None, mount_point=None,
        device_type=None, total_size=None, used_size=None,
        first_seen=None, last_seen=None, is_connected=True,
        device_id=None,
        # v1.1.0 additions
        host_id=None, host_name=None, host_ip=None, host_display_name=None,
        device_model=None, device_serial=None, connection_type='unknown',
        is_local=True, mount_points=None, health_status='unknown',
        last_health_check=None, performance_warning=False
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
        # v1.1.0 additions
        self.host_id = host_id
        self.host_name = host_name
        self.host_ip = host_ip
        self.host_display_name = host_display_name
        self.device_model = device_model
        self.device_serial = device_serial
        self.connection_type = connection_type
        self.is_local = is_local
        self.mount_points = mount_points
        self.health_status = health_status
        self.last_health_check = last_health_check
        self.performance_warning = performance_warning

    @classmethod
    def from_row(cls, row):
        """Create a StorageDevice object from a database row."""
        if not row:
            return None

        return cls(
            id=row[0] if len(row) > 0 else None,
            name=row[1] if len(row) > 1 else None,
            mount_point=row[2] if len(row) > 2 else None,
            device_type=row[3] if len(row) > 3 else None,
            total_size=row[4] if len(row) > 4 else None,
            used_size=row[5] if len(row) > 5 else None,
            first_seen=row[6] if len(row) > 6 else None,
            last_seen=row[7] if len(row) > 7 else None,
            is_connected=bool(row[8]) if len(row) > 8 else True,
            device_id=row[9] if len(row) > 9 else None,
            # v1.1.0 fields
            host_id=row[10] if len(row) > 10 else None,
            host_name=row[11] if len(row) > 11 else None,
            host_ip=row[12] if len(row) > 12 else None,
            host_display_name=row[13] if len(row) > 13 else None,
            device_model=row[14] if len(row) > 14 else None,
            device_serial=row[15] if len(row) > 15 else None,
            connection_type=row[16] if len(row) > 16 else 'unknown',
            is_local=bool(row[17]) if len(row) > 17 else True,
            mount_points=row[18] if len(row) > 18 else None,
            health_status=row[19] if len(row) > 19 else 'unknown',
            last_health_check=row[20] if len(row) > 20 else None,
            performance_warning=bool(row[21]) if len(row) > 21 else False
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
            "device_id": self.device_id,
            # v1.1.0 fields
            "host_id": self.host_id,
            "host_name": self.host_name,
            "host_ip": self.host_ip,
            "host_display_name": self.host_display_name,
            "device_model": self.device_model,
            "device_serial": self.device_serial,
            "connection_type": self.connection_type,
            "is_local": self.is_local,
            "mount_points": self.mount_points,
            "health_status": self.health_status,
            "last_health_check": self.last_health_check,
            "performance_warning": self.performance_warning
        }

class File:
    """Represents a file tracked in the system (unchanged from v1.0.0)."""

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
    """Represents a scan operation (enhanced for v1.1.0)."""

    def __init__(
        self, id=None, name=None, top_level_path=None,
        start_time=None, end_time=None, status="running",
        files_scanned=0, files_unchanged=0, files_modified=0,
        files_corrupted=0, files_missing=0, files_new=0,
        checksum_method="sha256", scheduled_scan_id=None,
        error_message=None, notes=None,
        # v1.1.0 additions
        host_id=None, host_name=None, host_ip=None, host_display_name=None,
        storage_device_id=None, scan_duration_seconds=None,
        bitrot_clusters_detected=0, total_size=0
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
        # v1.1.0 additions
        self.host_id = host_id
        self.host_name = host_name
        self.host_ip = host_ip
        self.host_display_name = host_display_name
        self.storage_device_id = storage_device_id
        self.scan_duration_seconds = scan_duration_seconds
        self.bitrot_clusters_detected = bitrot_clusters_detected
        self.total_size = total_size

    @classmethod
    def from_row(cls, row):
        """Create a Scan object from a database row."""
        if not row:
            return None

        return cls(
            id=row[0] if len(row) > 0 else None,
            name=row[1] if len(row) > 1 else None,
            top_level_path=row[2] if len(row) > 2 else None,
            start_time=row[3] if len(row) > 3 else None,
            end_time=row[4] if len(row) > 4 else None,
            status=row[5] if len(row) > 5 else "running",
            files_scanned=row[6] if len(row) > 6 else 0,
            files_unchanged=row[7] if len(row) > 7 else 0,
            files_modified=row[8] if len(row) > 8 else 0,
            files_corrupted=row[9] if len(row) > 9 else 0,
            files_missing=row[10] if len(row) > 10 else 0,
            files_new=row[11] if len(row) > 11 else 0,
            checksum_method=row[12] if len(row) > 12 else "sha256",
            scheduled_scan_id=row[13] if len(row) > 13 else None,
            error_message=row[14] if len(row) > 14 else None,
            notes=row[15] if len(row) > 15 else None,
            # v1.1.0 fields
            host_id=row[16] if len(row) > 16 else None,
            host_name=row[17] if len(row) > 17 else None,
            host_ip=row[18] if len(row) > 18 else None,
            host_display_name=row[19] if len(row) > 19 else None,
            storage_device_id=row[20] if len(row) > 20 else None,
            scan_duration_seconds=row[21] if len(row) > 21 else None,
            bitrot_clusters_detected=row[22] if len(row) > 22 else 0,
            total_size=row[23] if len(row) > 23 else 0
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
            "notes": self.notes,
            # v1.1.0 fields
            "host_id": self.host_id,
            "host_name": self.host_name,
            "host_ip": self.host_ip,
            "host_display_name": self.host_display_name,
            "storage_device_id": self.storage_device_id,
            "scan_duration_seconds": self.scan_duration_seconds,
            "bitrot_clusters_detected": self.bitrot_clusters_detected,
            "total_size": self.total_size
        }

class Checksum:
    """Represents a file checksum (unchanged from v1.0.0)."""

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
    """Represents a scheduled scan configuration (unchanged from v1.0.0)."""

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
    """Represents an error that occurred during a scan (unchanged from v1.0.0)."""

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
    """Represents a configuration setting (unchanged from v1.0.0)."""

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

# v1.1.0 NEW: Bitrot event model for clustering analysis
class BitrotEvent:
    """Represents a bitrot event with clustering analysis."""

    def __init__(
        self, id=None, storage_device_id=None, scan_id=None, host_id=None,
        event_date=None, affected_files_count=0, file_paths=None,
        sector_ranges=None, cluster_analysis=None, severity='moderate',
        pattern_description=None, recommended_action=None,
        user_acknowledged=False, acknowledgment_date=None, notes=None,
        resolved=False, resolution_date=None, created_at=None
    ):
        self.id = id
        self.storage_device_id = storage_device_id
        self.scan_id = scan_id
        self.host_id = host_id
        self.event_date = event_date or datetime.now(timezone.utc)
        self.affected_files_count = affected_files_count
        self.file_paths = file_paths if isinstance(file_paths, str) else json.dumps(file_paths or [])
        self.sector_ranges = sector_ranges if isinstance(sector_ranges, str) else json.dumps(sector_ranges or [])
        self.cluster_analysis = cluster_analysis
        self.severity = severity
        self.pattern_description = pattern_description
        self.recommended_action = recommended_action
        self.user_acknowledged = user_acknowledged
        self.acknowledgment_date = acknowledgment_date
        self.notes = notes
        self.resolved = resolved
        self.resolution_date = resolution_date
        self.created_at = created_at or datetime.now(timezone.utc)

    @classmethod
    def from_row(cls, row):
        """Create a BitrotEvent object from a database row."""
        if not row:
            return None

        return cls(
            id=row[0] if len(row) > 0 else None,
            storage_device_id=row[1] if len(row) > 1 else None,
            scan_id=row[2] if len(row) > 2 else None,
            host_id=row[3] if len(row) > 3 else None,
            event_date=row[4] if len(row) > 4 else None,
            affected_files_count=row[5] if len(row) > 5 else 0,
            file_paths=row[6] if len(row) > 6 else None,
            sector_ranges=row[7] if len(row) > 7 else None,
            cluster_analysis=row[8] if len(row) > 8 else None,
            severity=row[9] if len(row) > 9 else 'moderate',
            pattern_description=row[10] if len(row) > 10 else None,
            recommended_action=row[11] if len(row) > 11 else None,
            user_acknowledged=bool(row[12]) if len(row) > 12 else False,
            acknowledgment_date=row[13] if len(row) > 13 else None,
            notes=row[14] if len(row) > 14 else None,
            resolved=bool(row[15]) if len(row) > 15 else False,
            resolution_date=row[16] if len(row) > 16 else None,
            created_at=row[17] if len(row) > 17 else None
        )

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "storage_device_id": self.storage_device_id,
            "scan_id": self.scan_id,
            "host_id": self.host_id,
            "event_date": self.event_date,
            "affected_files_count": self.affected_files_count,
            "file_paths": json.loads(self.file_paths) if isinstance(self.file_paths, str) else self.file_paths,
            "sector_ranges": json.loads(self.sector_ranges) if isinstance(self.sector_ranges, str) else self.sector_ranges,
            "cluster_analysis": self.cluster_analysis,
            "severity": self.severity,
            "pattern_description": self.pattern_description,
            "recommended_action": self.recommended_action,
            "user_acknowledged": self.user_acknowledged,
            "acknowledgment_date": self.acknowledgment_date,
            "notes": self.notes,
            "resolved": self.resolved,
            "resolution_date": self.resolution_date,
            "created_at": self.created_at
        }

# v1.1.0 NEW: Device health history model
class DeviceHealthHistory:
    """Represents a device health check record."""

    def __init__(
        self, id=None, storage_device_id=None, host_id=None, check_date=None,
        temperature=None, power_on_hours=None, total_data_written=None,
        bad_sectors_count=None, wear_leveling_count=None, health_score=None,
        smart_status=None, smart_raw_data=None, predicted_failure_date=None,
        data_source='calculated', requires_root=False, created_at=None
    ):
        self.id = id
        self.storage_device_id = storage_device_id
        self.host_id = host_id
        self.check_date = check_date or datetime.now(timezone.utc)
        self.temperature = temperature
        self.power_on_hours = power_on_hours
        self.total_data_written = total_data_written
        self.bad_sectors_count = bad_sectors_count
        self.wear_leveling_count = wear_leveling_count
        self.health_score = health_score
        self.smart_status = smart_status
        self.smart_raw_data = smart_raw_data if isinstance(smart_raw_data, str) else json.dumps(smart_raw_data or {})
        self.predicted_failure_date = predicted_failure_date
        self.data_source = data_source
        self.requires_root = requires_root
        self.created_at = created_at or datetime.now(timezone.utc)

    @classmethod
    def from_row(cls, row):
        """Create a DeviceHealthHistory object from a database row."""
        if not row:
            return None

        return cls(
            id=row[0] if len(row) > 0 else None,
            storage_device_id=row[1] if len(row) > 1 else None,
            host_id=row[2] if len(row) > 2 else None,
            check_date=row[3] if len(row) > 3 else None,
            temperature=row[4] if len(row) > 4 else None,
            power_on_hours=row[5] if len(row) > 5 else None,
            total_data_written=row[6] if len(row) > 6 else None,
            bad_sectors_count=row[7] if len(row) > 7 else None,
            wear_leveling_count=row[8] if len(row) > 8 else None,
            health_score=row[9] if len(row) > 9 else None,
            smart_status=row[10] if len(row) > 10 else None,
            smart_raw_data=row[11] if len(row) > 11 else None,
            predicted_failure_date=row[12] if len(row) > 12 else None,
            data_source=row[13] if len(row) > 13 else 'calculated',
            requires_root=bool(row[14]) if len(row) > 14 else False,
            created_at=row[15] if len(row) > 15 else None
        )

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "storage_device_id": self.storage_device_id,
            "host_id": self.host_id,
            "check_date": self.check_date,
            "temperature": self.temperature,
            "power_on_hours": self.power_on_hours,
            "total_data_written": self.total_data_written,
            "bad_sectors_count": self.bad_sectors_count,
            "wear_leveling_count": self.wear_leveling_count,
            "health_score": self.health_score,
            "smart_status": self.smart_status,
            "smart_raw_data": json.loads(self.smart_raw_data) if isinstance(self.smart_raw_data, str) else self.smart_raw_data,
            "predicted_failure_date": self.predicted_failure_date,
            "data_source": self.data_source,
            "requires_root": self.requires_root,
            "created_at": self.created_at
        }
