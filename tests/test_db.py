"""
Tests for the database implementation.
"""
import json
import sys
import os
import unittest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bitarr.db.init_db import init_db
from bitarr.db.db_manager import DatabaseManager
from bitarr.db.models import (
    StorageDevice, File, Scan, Checksum, 
    ScheduledScan, ScanError, Configuration
)

class TestDatabase(unittest.TestCase):
    """Test the database implementation."""
    
    def setUp(self):
        """Set up a test database."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        init_db(self.db_path)
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up the test database."""
        self.temp_dir.cleanup()
    
    def test_storage_device_operations(self):
        """Test storage device CRUD operations."""
        # Create a storage device
        device = StorageDevice(
            name="Test Device",
            mount_point="/mnt/test",
            device_type="Test",
            total_size=1000,
            used_size=500,
            device_id="test123"
        )
        
        # Add storage device
        device_id = self.db.add_storage_device(device)
        self.assertIsNotNone(device_id)
        
        # Get storage device
        retrieved_device = self.db.get_storage_device(id=device_id)
        self.assertIsNotNone(retrieved_device)
        self.assertEqual(retrieved_device.name, "Test Device")
        self.assertEqual(retrieved_device.mount_point, "/mnt/test")
        
        # Update storage device
        retrieved_device.name = "Updated Device"
        self.db.update_storage_device(retrieved_device)
        
        # Get updated device
        updated_device = self.db.get_storage_device(id=device_id)
        self.assertEqual(updated_device.name, "Updated Device")
        
        # Get all storage devices
        devices = self.db.get_all_storage_devices()
        self.assertEqual(len(devices), 1)
        
        # Delete storage device
        self.db.delete_storage_device(device_id)
        
        # Verify deletion
        deleted_device = self.db.get_storage_device(id=device_id)
        self.assertIsNone(deleted_device)
    
    def test_file_operations(self):
        """Test file CRUD operations."""
        # Create a storage device first
        device = StorageDevice(
            name="Test Device",
            mount_point="/mnt/test",
            device_type="Test"
        )
        device_id = self.db.add_storage_device(device)
        
        # Create a file
        file = File(
            path="/mnt/test/file.txt",
            filename="file.txt",
            directory="/mnt/test",
            storage_device_id=device_id,
            size=100,
            file_type="text"
        )
        
        # Add file
        file_id = self.db.add_file(file)
        self.assertIsNotNone(file_id)
        
        # Get file
        retrieved_file = self.db.get_file(id=file_id)
        self.assertIsNotNone(retrieved_file)
        self.assertEqual(retrieved_file.path, "/mnt/test/file.txt")
        
        # Update file
        retrieved_file.size = 200
        self.db.update_file(retrieved_file)
        
        # Get updated file
        updated_file = self.db.get_file(id=file_id)
        self.assertEqual(updated_file.size, 200)
        
        # Get files by directory
        dir_files = self.db.get_files_by_directory("/mnt/test", device_id)
        self.assertEqual(len(dir_files), 1)
        
        # Mark file as deleted
        self.db.mark_files_as_deleted([file_id])
        
        # Verify deletion flag
        deleted_file = self.db.get_file(id=file_id)
        self.assertTrue(deleted_file.is_deleted)
    
    def test_scan_operations(self):
        """Test scan CRUD operations."""
        # Create a scan
        scan = Scan(
            name="Test Scan",
            top_level_path="/mnt/test",
            status="running",
            checksum_method="sha256"
        )
        
        # Add scan
        scan_id = self.db.add_scan(scan)
        self.assertIsNotNone(scan_id)
        
        # Get scan
        retrieved_scan = self.db.get_scan(scan_id)
        self.assertIsNotNone(retrieved_scan)
        self.assertEqual(retrieved_scan.name, "Test Scan")
        self.assertEqual(retrieved_scan.status, "running")
        
        # Update scan
        retrieved_scan.status = "completed"
        retrieved_scan.end_time = datetime.now(timezone.utc)
        self.db.update_scan(retrieved_scan)
        
        # Get updated scan
        updated_scan = self.db.get_scan(scan_id)
        self.assertEqual(updated_scan.status, "completed")
        
        # Get scans by path
        path_scans = self.db.get_scans_by_path("/mnt/test")
        self.assertEqual(len(path_scans), 1)
        
        # Get recent scans
        recent_scans = self.db.get_recent_scans()
        self.assertEqual(len(recent_scans), 1)
        
        # Delete scan
        self.db.delete_scan(scan_id)
        
        # Verify deletion
        deleted_scan = self.db.get_scan(scan_id)
        self.assertIsNone(deleted_scan)
    
    def test_configuration_operations(self):
        """Test configuration operations."""
        # Set configuration
        self.db.set_configuration("test_key", "test_value", "string", "Test description")

        # Get configuration
        config = self.db.get_configuration("test_key")
        self.assertIsNotNone(config)
        self.assertEqual(config.key, "test_key")
        self.assertEqual(config.value, "test_value")
        self.assertEqual(config.value_type, "string")  # Changed from config.type to config.value_type

        # Get all configuration
        all_config = self.db.get_all_configuration()
        self.assertIn("test_key", all_config)
        # Default configurations should also exist
        self.assertIn("web_ui_port", all_config)

        # Update configuration
        self.db.set_configuration("test_key", "updated_value")

        # Get updated configuration
        updated_config = self.db.get_configuration("test_key")
        self.assertEqual(updated_config.value, "updated_value")

        # Test different types
        self.db.set_configuration("int_key", 42)
        self.db.set_configuration("bool_key", True)
        self.db.set_configuration("json_key", {"test": "value"})

        all_config = self.db.get_all_configuration()
        self.assertEqual(all_config["int_key"], 42)
        self.assertEqual(all_config["bool_key"], True)
        self.assertEqual(all_config["json_key"], {"test": "value"})

    def test_checksum_operations(self):
        """Test checksum CRUD operations."""
        # Create prerequisites: storage device, file, and scan
        device = StorageDevice(name="Test Device", mount_point="/mnt/test")
        device_id = self.db.add_storage_device(device)
        
        file = File(
            path="/mnt/test/file.txt",
            filename="file.txt",
            directory="/mnt/test",
            storage_device_id=device_id
        )
        file_id = self.db.add_file(file)
        
        scan = Scan(
            name="Test Scan",
            top_level_path="/mnt/test",
            status="completed",
            checksum_method="sha256"
        )
        scan_id = self.db.add_scan(scan)
        
        # Create a checksum
        checksum = Checksum(
            file_id=file_id,
            scan_id=scan_id,
            checksum_value="123456789abcdef",
            checksum_method="sha256",
            status="unchanged"
        )
        
        # Add checksum
        checksum_id = self.db.add_checksum(checksum)
        self.assertIsNotNone(checksum_id)
        
        # Get checksum
        retrieved_checksum = self.db.get_checksum(checksum_id)
        self.assertIsNotNone(retrieved_checksum)
        self.assertEqual(retrieved_checksum.checksum_value, "123456789abcdef")
        
        # Update checksum status
        self.db.update_checksum_status(checksum_id, "modified")
        
        # Get updated checksum
        updated_checksum = self.db.get_checksum(checksum_id)
        self.assertEqual(updated_checksum.status, "modified")
        
        # Get file checksums
        file_checksums = self.db.get_file_checksums(file_id)
        self.assertEqual(len(file_checksums), 1)
        
        # Get scan checksums
        scan_checksums = self.db.get_scan_checksums(scan_id)
        self.assertEqual(len(scan_checksums), 1)
    
    def test_scheduled_scan_operations(self):
        """Test scheduled scan CRUD operations."""
        # Create a scheduled scan
        scheduled_scan = ScheduledScan(
            name="Test Schedule",
            paths=json.dumps(["/mnt/test"]),
            frequency="daily",
            parameters=json.dumps({"time": "03:00"}),
            next_run=datetime.now(timezone.utc) + timedelta(days=1),
            status="active",
            priority=0
        )
        
        # Add scheduled scan
        scheduled_scan_id = self.db.add_scheduled_scan(scheduled_scan)
        self.assertIsNotNone(scheduled_scan_id)
        
        # Get scheduled scan
        retrieved_scheduled_scan = self.db.get_scheduled_scan(scheduled_scan_id)
        self.assertIsNotNone(retrieved_scheduled_scan)
        self.assertEqual(retrieved_scheduled_scan.name, "Test Schedule")
        
        # Update scheduled scan
        retrieved_scheduled_scan.priority = 1
        self.db.update_scheduled_scan(retrieved_scheduled_scan)
        
        # Get updated scheduled scan
        updated_scheduled_scan = self.db.get_scheduled_scan(scheduled_scan_id)
        self.assertEqual(updated_scheduled_scan.priority, 1)
        
        # Get all scheduled scans
        all_scheduled_scans = self.db.get_all_scheduled_scans()
        self.assertEqual(len(all_scheduled_scans), 1)
        
        # Get active scheduled scans
        active_scheduled_scans = self.db.get_active_scheduled_scans()
        self.assertEqual(len(active_scheduled_scans), 1)
        
        # Set next_run to past date to test due functionality
        retrieved_scheduled_scan.next_run = datetime.now(timezone.utc) - timedelta(hours=1)
        self.db.update_scheduled_scan(retrieved_scheduled_scan)
        
        # Get due scheduled scans
        due_scheduled_scans = self.db.get_due_scheduled_scans()
        self.assertEqual(len(due_scheduled_scans), 1)
        
        # Delete scheduled scan
        self.db.delete_scheduled_scan(scheduled_scan_id)
        
        # Verify deletion
        deleted_scheduled_scan = self.db.get_scheduled_scan(scheduled_scan_id)
        self.assertIsNone(deleted_scheduled_scan)
    
    def test_scan_error_operations(self):
        """Test scan error operations."""
        # Create a scan first
        scan = Scan(
            name="Test Scan",
            top_level_path="/mnt/test",
            status="completed",
            checksum_method="sha256"
        )
        scan_id = self.db.add_scan(scan)
        
        # Create a scan error
        scan_error = ScanError(
            scan_id=scan_id,
            file_path="/mnt/test/error.txt",
            error_type="access_denied",
            error_message="Permission denied"
        )
        
        # Add scan error
        error_id = self.db.add_scan_error(scan_error)
        self.assertIsNotNone(error_id)
        
        # Get scan errors
        scan_errors = self.db.get_scan_errors(scan_id)
        self.assertEqual(len(scan_errors), 1)
        self.assertEqual(scan_errors[0].error_type, "access_denied")
    
    def test_database_maintenance(self):
        """Test database maintenance operations."""
        # Test vacuum
        result = self.db.vacuum()
        self.assertTrue(result)
        
        # Test backup
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            backup_path = temp_file.name
        
        backup_result = self.db.backup(backup_path)
        self.assertEqual(backup_result, backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # Clean up
        os.unlink(backup_path)
        
        # Test database info
        info = self.db.get_database_info()
        self.assertIn("database_size", info)
        self.assertIn("storage_devices_count", info)
        self.assertIn("files_count", info)
        self.assertIn("scans_count", info)
        
        # Add some test data for pruning
        past_date = datetime.now(timezone.utc) - timedelta(days=10)
        
        scan = Scan(
            name="Old Scan",
            top_level_path="/mnt/test",
            status="completed",
            checksum_method="sha256",
            start_time=past_date
        )
        scan_id = self.db.add_scan(scan)
        
        # Test pruning old scans
        pruned = self.db.prune_old_scans(5)  # Prune scans older than 5 days
        self.assertEqual(pruned, 1)
        
        # Verify the scan was pruned
        pruned_scan = self.db.get_scan(scan_id)
        self.assertIsNone(pruned_scan)


if __name__ == "__main__":
    unittest.main()
