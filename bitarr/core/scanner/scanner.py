"""
Core scanner implementation for Bitarr.
"""
import os
import threading
import time
import queue
import socket
import platform

from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Tuple, Any
from pathlib import Path

from bitarr.db.db_manager import DatabaseManager
from bitarr.db.models import File, Scan, Checksum, StorageDevice, ScanError
from .checksum import ChecksumCalculator
from .device_detector import DeviceDetector
from .file_utils import get_file_metadata, walk_directory, split_path_components

class ScannerError(Exception):
    """Exception raised for scanner errors."""
    pass

class FileScanner:
    """
    Core file scanner for Bitarr.
    
    Handles file system scanning, checksum calculation, and change detection.
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the file scanner.
        
        Args:
            db_manager: Database manager instance, or None to create a new one
        """
        self.db = db_manager or DatabaseManager()
        self.device_detector = DeviceDetector()
        self.checksum_calculator = None  # Will be initialized in scan
        self.current_scan = None
        self.stop_event = threading.Event()
        self.queue = queue.Queue()
        self.threads = []
        self.files_processed = 0
        self.total_files = 0
        self.total_size = 0
        self.size_lock = threading.Lock()
        self.progress_callbacks = []
    
    def add_progress_callback(self, callback: Callable[[Dict], None]) -> None:
        """
        Add a callback to receive progress updates.
        
        Args:
            callback: Function that takes a dictionary with progress information
        """
        self.progress_callbacks.append(callback)
    
    def _report_progress(self, status: str, **kwargs) -> None:
        """
        Report progress to all registered callbacks.
        
        Args:
            status: Current status
            **kwargs: Additional information to include
        """
        progress_data = {
            "status": status,
            "scan_id": self.current_scan.id if self.current_scan else None,
            "files_processed": self.files_processed,
            "total_files": self.total_files,
            "percent_complete": (self.files_processed / self.total_files * 100) if self.total_files > 0 else 0,
            "timestamp": datetime.now(timezone.utc),
            **kwargs
        }
        
        for callback in self.progress_callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                print(f"Error in progress callback: {str(e)}")
    
    def scan(
        self, 
        top_level_path: str, 
        name: Optional[str] = None,
        checksum_method: str = "sha256", 
        threads: int = 4,
        exclude_dirs: List[str] = None,
        exclude_patterns: List[str] = None,
        scheduled_scan_id: Optional[int] = None
    ) -> int:
        """
        Scan a directory tree, calculate checksums, and detect changes.
        
        Args:
            top_level_path: Top-level directory to scan
            name: Name for the scan
            checksum_method: Checksum algorithm to use
            threads: Number of threads to use
            exclude_dirs: List of directory names to exclude
            exclude_patterns: List of glob patterns to exclude
            scheduled_scan_id: ID of the scheduled scan, if any
        
        Returns:
            int: ID of the created scan
        
        Raises:
            ScannerError: If the scan fails
        """
        # Validate input
        if not os.path.exists(top_level_path) or not os.path.isdir(top_level_path):
            raise ScannerError(f"Invalid top_level_path: {top_level_path}")
        
        # Normalize path
        top_level_path = os.path.abspath(top_level_path)
        
        # Initialize checksum calculator
        self.checksum_calculator = ChecksumCalculator(algorithm=checksum_method)
        
        # Default exclusions
        exclude_dirs = exclude_dirs or ['.git', 'node_modules', '.venv', 'venv', '__pycache__']
        exclude_patterns = exclude_patterns or ['*.tmp', '*.temp', '*.swp', '*.bak']
        
        # Create a new scan
        self.current_scan = Scan(
            name=name or f"Scan of {os.path.basename(top_level_path)}",
            top_level_path=top_level_path,
            status="running",
            checksum_method=checksum_method,
            scheduled_scan_id=scheduled_scan_id
        )
        
        # Add scan to database
        self.current_scan.id = self.db.add_scan(self.current_scan)
        
        # Detect the storage device
        device_info = self.device_detector.get_device_by_path(top_level_path)
        if not device_info:
            # If device not found, create a default one
            device_info = {
                "name": "Unknown Device",
                "mount_point": "/",
                "device_type": "unknown",
                "device_id": None,
                "total_size": 0,
                "used_size": 0
            }
        
        # Check if the device exists in the database
        storage_device = self.db.get_storage_device(
            device_id=device_info['device_id'], 
            mount_point=device_info['mount_point']
        )
        
        if not storage_device:
            # Create a new storage device
            storage_device = StorageDevice(
                name=device_info['name'],
                mount_point=device_info['mount_point'],
                device_type=device_info['device_type'],
                total_size=device_info['total_size'],
                used_size=device_info['used_size'],
                device_id=device_info['device_id']
            )
            storage_device.id = self.db.add_storage_device(storage_device)
        else:
            # Update the existing device
            storage_device.last_seen = datetime.now(timezone.utc)
            storage_device.is_connected = True
            storage_device.total_size = device_info['total_size']
            storage_device.used_size = device_info['used_size']
            self.db.update_storage_device(storage_device)
        
        # Reset counters
        self.files_processed = 0
        self.total_files = 0
        self.total_size = 0
        self.stop_event.clear()
        
        try:
            # Estimate total files
            self._report_progress("counting", current_path=top_level_path)
            self.total_files = self._count_files(top_level_path, exclude_dirs, exclude_patterns)
            self._report_progress("starting", storage_device_id=storage_device.id)
            
            # Use a thread pool to process files
            self.threads = []
            for _ in range(threads):
                thread = threading.Thread(target=self._worker, daemon=True)
                thread.start()
                self.threads.append(thread)
            
            # Enqueue all files
            for file_path in walk_directory(top_level_path, exclude_dirs, exclude_patterns):
                if self.stop_event.is_set():
                    break
                
                self.queue.put((file_path, storage_device.id))
            
            # Add sentinel values to signal worker threads to exit
            for _ in range(threads):
                self.queue.put(None)
            
            # Wait for all threads to finish
            for thread in self.threads:
                thread.join()
            
            # Update scan completion
            if self.stop_event.is_set():
                self.current_scan.status = "aborted"
            else:
                self.current_scan.status = "completed"
            
            self.current_scan.total_size = self.total_size
            self.current_scan.end_time = datetime.now(timezone.utc)
            self.current_scan.files_scanned = self.files_processed
            self.db.update_scan(self.current_scan)
            
            self._report_progress("completed", current_path=None)
            
            return self.current_scan.id
        
        except Exception as e:
            error_message = f"Scan failed: {str(e)}"
            print(error_message)
            
            # Update scan with error
            if self.current_scan:
                self.current_scan.status = "failed"
                self.current_scan.end_time = datetime.now(timezone.utc)
                self.current_scan.error_message = error_message
                self.db.update_scan(self.current_scan)
            
            self._report_progress("failed", error=error_message)
            
            raise ScannerError(error_message) from e
    
    def stop(self) -> None:
        """
        Stop the current scan.
        """
        self.stop_event.set()
    
    def _count_files(self, path: str, exclude_dirs: List[str], exclude_patterns: List[str]) -> int:
        """
        Count the number of files to be processed.
        
        Args:
            path: Directory path to count
            exclude_dirs: List of directory names to exclude
            exclude_patterns: List of glob patterns to exclude
        
        Returns:
            int: Number of files
        """
        count = 0
        for _ in walk_directory(path, exclude_dirs, exclude_patterns):
            count += 1
        return count
    
    def _worker(self) -> None:
        """
        Worker thread function to process files.
        """
        while not self.stop_event.is_set():
            # Get a file from the queue
            item = self.queue.get()
            if item is None:  # Sentinel value
                self.queue.task_done()
                break
            
            file_path, storage_device_id = item
            
            try:
                if self.stop_event.is_set():
                    self.queue.task_done()
                    break
                
                self._process_file(file_path, storage_device_id)
                
                self.files_processed += 1
                if self.files_processed % 10 == 0:  # Report progress every 10 files
                    self._report_progress("scanning", current_path=file_path)

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")

                # Record the error
                error = ScanError(
                    scan_id=self.current_scan.id,
                    file_path=file_path,
                    error_type="processing_error",
                    error_message=str(e)
                )
                self.db.add_scan_error(error)

            finally:
                self.queue.task_done()

    def _process_file(self, file_path: str, storage_device_id: int) -> None:
        """
        Process a single file.

        Args:
            file_path: Path to the file
            storage_device_id: ID of the storage device
        """
        # Get file metadata
        metadata = get_file_metadata(file_path)
        if not metadata["is_file"]:
            return  # Skip directories, symlinks, etc.

        # Split path components
        directory, filename, path = split_path_components(file_path)

        # Check if file exists in database
        db_file = self.db.get_file(path=path, storage_device_id=storage_device_id)

        if not db_file:
            # New file, add to database
            db_file = File(
                path=path,
                filename=filename,
                directory=directory,
                storage_device_id=storage_device_id,
                size=metadata["size"],
                last_modified=metadata["last_modified"],
                file_type=metadata["file_type"]
            )
            db_file.id = self.db.add_file(db_file)
            with self.size_lock:
                self.total_size += metadata["size"]
                print(f"DEBUG: Added {metadata['size']} bytes, total now: {self.total_size}")

            file_status = "new"
            prev_checksum_id = None
        else:
            # Update existing file
            db_file.last_seen = datetime.now(timezone.utc)
            db_file.size = metadata["size"]
            with self.size_lock:
                self.total_size += metadata["size"]  # ADD THIS LINE
                print(f"DEBUG: Added {metadata['size']} bytes, total now: {self.total_size}")
            db_file.last_modified = metadata["last_modified"]
            db_file.is_deleted = False
            self.db.update_file(db_file)

            # Get previous checksum to compare
            prev_checksums = self.db.get_file_checksums(db_file.id, limit=1)
            prev_checksum = prev_checksums[0] if prev_checksums else None
            prev_checksum_id = prev_checksum.id if prev_checksum else None

            # Initially mark as unchanged, will update after checksum calculation
            file_status = "unchanged"

        # Calculate checksum
        checksum_value = self.checksum_calculator.calculate_file_checksum(file_path)
        if not checksum_value:
            # Record error if checksum calculation failed
            error = ScanError(
                scan_id=self.current_scan.id,
                file_path=file_path,
                error_type="checksum_error",
                error_message="Failed to calculate checksum"
            )
            self.db.add_scan_error(error)
            return

        # Create checksum record
        checksum = Checksum(
            file_id=db_file.id,
            scan_id=self.current_scan.id,
            checksum_value=checksum_value,
            checksum_method=self.current_scan.checksum_method,
            status=file_status,
            previous_checksum_id=prev_checksum_id
        )

        # Check for changes if this is an existing file
        if file_status == "unchanged" and prev_checksum:
            if checksum_value != prev_checksum.checksum_value:
                # Check if modification or corruption
                if db_file.last_modified != prev_checksum.timestamp:
                    # File was modified
                    checksum.status = "modified"
                    self.current_scan.files_modified += 1
                else:
                    # File was likely corrupted
                    checksum.status = "corrupted"
                    self.current_scan.files_corrupted += 1
            else:
                # File is unchanged
                self.current_scan.files_unchanged += 1
        elif file_status == "new":
            # Count new files
            self.current_scan.files_new += 1

        # Add checksum to database
        checksum.id = self.db.add_checksum(checksum)

        # Update scan statistics
        self.db.update_scan(self.current_scan)

    def find_missing_files(self, top_level_path: str, storage_device_id: int) -> List[File]:
        """
        Find files that are in the database but no longer exist on disk.

        Args:
            top_level_path: Top-level directory path
            storage_device_id: ID of the storage device

        Returns:
            List[File]: List of missing files
        """
        # Get all files for this path and storage device
        query = """
            SELECT * FROM files
            WHERE directory LIKE ? AND storage_device_id = ? AND is_deleted = 0
        """
        params = (f"{top_level_path}%", storage_device_id)

        with self.db.lock:
            conn = self.db.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)

                # Check each file's existence
                missing_files = []
                for row in cursor.fetchall():
                    db_file = File(**dict(row))
                    if not os.path.exists(db_file.path):
                        db_file.is_deleted = True
                        self.db.update_file(db_file)
                        missing_files.append(db_file)

                return missing_files
            finally:
                conn.close()

    def update_missing_files_status(self, scan_id: int, missing_files: List[File]) -> int:
        """
        Update the status of missing files in a scan.

        Args:
            scan_id: ID of the scan
            missing_files: List of missing files

        Returns:
            int: Number of missing files
        """
        if not missing_files:
            return 0

        # Create checksums for missing files
        for file in missing_files:
            # Create a 'missing' checksum
            checksum = Checksum(
                file_id=file.id,
                scan_id=scan_id,
                checksum_value="",  # Empty for missing files
                checksum_method=self.current_scan.checksum_method,
                status="missing"
            )
            self.db.add_checksum(checksum)

        # Update scan statistics
        if self.current_scan and self.current_scan.id == scan_id:
            self.current_scan.files_missing = len(missing_files)
            self.db.update_scan(self.current_scan)

        return len(missing_files)

    def get_scan_summary(self, scan_id: int) -> Dict[str, Any]:
        """
        Get a summary of scan results.

        Args:
            scan_id: ID of the scan

        Returns:
            Dict: Summary of scan results
        """
        scan = self.db.get_scan(scan_id)
        if not scan:
            return {"error": "Scan not found"}

        # Get counts by status
        query = """
            SELECT status, COUNT(*) as count
            FROM checksums
            WHERE scan_id = ?
            GROUP BY status
        """
        params = (scan_id,)

        with self.db.lock:
            conn = self.db.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)

                status_counts = {}
                for row in cursor.fetchall():
                    status_counts[row['status']] = row['count']

                # Get storage device information
                storage_query = """
                    SELECT sd.id, sd.name, sd.mount_point, sd.device_type,
                           COUNT(DISTINCT f.id) as file_count
                    FROM storage_devices sd
                    JOIN files f ON sd.id = f.storage_device_id
                    JOIN checksums c ON f.id = c.file_id
                    WHERE c.scan_id = ?
                    GROUP BY sd.id
                """
                cursor.execute(storage_query, params)
                storage_devices = [dict(row) for row in cursor.fetchall()]

                # Get error count
                error_query = "SELECT COUNT(*) as count FROM scan_errors WHERE scan_id = ?"
                cursor.execute(error_query, params)
                error_count = cursor.fetchone()['count']

                return {
                    "scan_id": scan.id,
                    "name": scan.name,
                    "top_level_path": scan.top_level_path,
                    "start_time": scan.start_time,
                    "end_time": scan.end_time,
                    "status": scan.status,
                    "files_scanned": scan.files_scanned,
                    "files_unchanged": scan.files_unchanged,
                    "files_modified": scan.files_modified,
                    "files_corrupted": scan.files_corrupted,
                    "files_missing": scan.files_missing,
                    "files_new": scan.files_new,
                    "status_counts": status_counts,
                    "storage_devices": storage_devices,
                    "error_count": error_count,
                    "checksum_method": scan.checksum_method
                }
            finally:
                conn.close()

    def _get_current_host_info(self):
        """Get current host information for linking scans and storage devices."""
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

    def _get_or_create_current_host(self):
        """Get or create the current host in the database."""
        host_info = self._get_current_host_info()

        # Check if host exists
        query = "SELECT * FROM scan_hosts WHERE host_name = ? AND host_ip = ?"
        params = (host_info['host_name'], host_info['host_ip'])

        host_row = self.db.fetch_one(query, params)

        if host_row:
            # Update last_seen for existing host
            host_id = host_row['id']
            update_query = """
                UPDATE scan_hosts
                SET last_seen = ?, connection_status = 'online', updated_at = ?
                WHERE id = ?
            """
            update_params = (datetime.now(timezone.utc), datetime.now(timezone.utc), host_id)
            self.db.execute_query(update_query, update_params)

            return host_row
        else:
            # Create new host
            insert_query = """
                INSERT INTO scan_hosts
                (host_name, host_ip, host_display_name, host_type, client_version, connection_status, last_seen, created_at, updated_at)
                VALUES (?, ?, ?, ?, '1.1.0', 'online', ?, ?, ?)
            """
            now = datetime.now(timezone.utc)
            insert_params = (
                host_info['host_name'], host_info['host_ip'], host_info['host_display_name'],
                host_info['host_type'], now, now, now
            )
            cursor = self.db.execute_query(insert_query, insert_params)

            # Return the created host
            host_row = self.db.fetch_one("SELECT * FROM scan_hosts WHERE id = ?", (cursor.lastrowid,))
            return host_row

    # REPLACE the existing scan method with this updated version:
    def scan(
        self,
        top_level_path: str,
        name: Optional[str] = None,
        checksum_method: str = "sha256",
        threads: int = 4,
        exclude_dirs: List[str] = None,
        exclude_patterns: List[str] = None,
        scheduled_scan_id: Optional[int] = None
    ) -> int:
        """
        Scan a directory tree, calculate checksums, and detect changes.

        Args:
            top_level_path: Top-level directory to scan
            name: Name for the scan
            checksum_method: Checksum algorithm to use
            threads: Number of threads to use
            exclude_dirs: List of directory names to exclude
            exclude_patterns: List of glob patterns to exclude
            scheduled_scan_id: ID of the scheduled scan, if any

        Returns:
            int: Scan ID
        """
        # Validate path
        if not os.path.exists(top_level_path):
            raise ScannerError(f"Path does not exist: {top_level_path}")

        if not os.path.isdir(top_level_path):
            raise ScannerError(f"Path is not a directory: {top_level_path}")

        # Get or create current host
        current_host = self._get_or_create_current_host()

        # Initialize checksum calculator
        self.checksum_calculator = ChecksumCalculator(checksum_method)

        # Detect storage device for this path
        device_info = self.device_detector.get_device_by_path(top_level_path)
        if not device_info:
            device_info = {
                "device_id": f"unknown_{hash(top_level_path)}",
                "name": f"Unknown Device ({top_level_path})",
                "mount_point": "/",
                "device_type": "unknown",
                "total_size": 0,
                "used_size": 0
            }

        # Check if the device exists in the database
        storage_device = self.db.get_storage_device(
            device_id=device_info['device_id'],
            mount_point=device_info['mount_point']
        )

        if not storage_device:
            # Create a new storage device with host relationship
            storage_device = StorageDevice(
                name=device_info['name'],
                mount_point=device_info['mount_point'],
                device_type=device_info['device_type'],
                total_size=device_info['total_size'],
                used_size=device_info['used_size'],
                device_id=device_info['device_id'],
                # v1.1.0 host relationship fields
                host_id=current_host['id'],
                host_name=current_host['host_name'],
                host_ip=current_host['host_ip'],
                host_display_name=current_host['host_display_name']
            )
            storage_device.id = self.db.add_storage_device(storage_device)
        else:
            # Update the existing device with host relationship
            storage_device.last_seen = datetime.now(timezone.utc)
            storage_device.is_connected = True
            storage_device.total_size = device_info['total_size']
            storage_device.used_size = device_info['used_size']
            # Update host relationship if not already set
            if not storage_device.host_id:
                storage_device.host_id = current_host['id']
                storage_device.host_name = current_host['host_name']
                storage_device.host_ip = current_host['host_ip']
                storage_device.host_display_name = current_host['host_display_name']
            self.db.update_storage_device(storage_device)

        # Create scan record with host and storage device relationships
        self.current_scan = Scan(
            name=name,
            top_level_path=top_level_path,
            start_time=datetime.now(timezone.utc),
            status="running",
            checksum_method=checksum_method,
            scheduled_scan_id=scheduled_scan_id,
            # v1.1.0 relationship fields
            host_id=current_host['id'],
            host_name=current_host['host_name'],
            host_ip=current_host['host_ip'],
            host_display_name=current_host['host_display_name'],
            storage_device_id=storage_device.id
        )
        self.current_scan.id = self.db.add_scan(self.current_scan)

        # Reset counters
        self.files_processed = 0
        self.total_files = 0
        self.total_size = 0
        self.stop_event.clear()

        try:
            # Estimate total files
            self._report_progress("counting", current_path=top_level_path)
            self.total_files = self._count_files(top_level_path, exclude_dirs, exclude_patterns)
            self._report_progress("starting", storage_device_id=storage_device.id)

            # Use a thread pool to process files
            self.threads = []
            for _ in range(threads):
                thread = threading.Thread(target=self._worker, daemon=True)
                thread.start()
                self.threads.append(thread)

            # Enqueue all files
            for file_path in walk_directory(top_level_path, exclude_dirs, exclude_patterns):
                if self.stop_event.is_set():
                    break

                self.queue.put((file_path, storage_device.id))

            # Add sentinel values to signal worker threads to exit
            for _ in range(threads):
                self.queue.put(None)

            # Wait for all threads to finish
            for thread in self.threads:
                thread.join()

            # Update scan completion
            if self.stop_event.is_set():
                self.current_scan.status = "aborted"
            else:
                self.current_scan.status = "completed"

            self.current_scan.end_time = datetime.now(timezone.utc)
            self.current_scan.total_size = self.total_size
            print(f"DEBUG: About to save scan with total_size: {self.current_scan.total_size}")  # ADD THIS LINE

            # Calculate scan duration
            if self.current_scan.start_time and self.current_scan.end_time:
                duration = self.current_scan.end_time - self.current_scan.start_time
                self.current_scan.scan_duration_seconds = int(duration.total_seconds())

            # Find missing files
            missing_files = self.find_missing_files(top_level_path, storage_device.id)
            self.current_scan.files_missing = len(missing_files)

            # Final update of scan record
            self.db.update_scan(self.current_scan)

            # Report final progress
            self._report_progress("completed")

            return self.current_scan.id

        except Exception as e:
            # Handle scan errors
            self.current_scan.status = "failed"
            self.current_scan.error_message = str(e)
            self.current_scan.end_time = datetime.now(timezone.utc)
            self.db.update_scan(self.current_scan)

            self._report_progress("failed", error=str(e))
            raise ScannerError(f"Scan failed: {e}")

        finally:
            # Cleanup
            self.threads.clear()

            # Clear the queue
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except queue.Empty:
                    break
