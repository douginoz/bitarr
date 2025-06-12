"""
Command-line interface for the Bitarr core scanner.
"""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from bitarr.db.db_manager import DatabaseManager
from bitarr.core.scanner import FileScanner, ChecksumCalculator, DeviceDetector

def progress_callback(progress_data):
    """
    Callback function to display scan progress.
    """
    status = progress_data["status"]
    files_processed = progress_data["files_processed"]
    total_files = progress_data["total_files"]
    percent = progress_data["percent_complete"]

    if status == "counting":
        print(f"Counting files in {progress_data.get('current_path', '')}")
    elif status == "starting":
        print(f"Starting scan, found {total_files} files to process")
    elif status == "scanning":
        current_path = progress_data.get('current_path', '')
        short_path = os.path.basename(current_path) if current_path else ''
        print(f"\rScanning: {files_processed}/{total_files} ({percent:.1f}%) - {short_path}", end="")
    elif status == "completed":
        print(f"\nScan completed: {files_processed} files processed")
    elif status == "failed":
        print(f"\nScan failed: {progress_data.get('error', 'Unknown error')}")
    else:
        print(f"\rStatus: {status} - {files_processed}/{total_files} ({percent:.1f}%)", end="")

def list_checksum_algorithms():
    """
    List available checksum algorithms.
    """
    calculator = ChecksumCalculator()
    algorithms = calculator.get_supported_algorithms()

    print("Available checksum algorithms:")
    for algorithm in algorithms:
        print(f"  - {algorithm}")

    print("\nAlgorithm details:")
    info = calculator.algorithm_info()
    for algorithm, details in info.items():
        print(f"  {algorithm}:")
        print(f"    Description: {details['description']}")
        print(f"    Speed: {details['speed']}")
        print(f"    Security: {details['security']}")
        print(f"    Recommendation: {details['recommendation']}")
        print()

def detect_devices():
    """
    Detect and display storage devices.
    """
    detector = DeviceDetector()
    devices = detector.detect_devices()

    print(f"Detected {len(devices)} storage devices:")
    for i, device in enumerate(devices, 1):
        print(f"  {i}. {device['name']} ({device['mount_point']})")
        print(f"     Type: {device['device_type']}")
        if 'total_size' in device and device['total_size'] > 0:
            print(f"     Size: {device['total_size'] / (1024**3):.1f} GB")
            print(f"     Used: {device['usage_percent']:.1f}%")
        print(f"     Device ID: {device['device_id']}")
        print()

def run_scan(path, name=None, algorithm="sha256", threads=4, exclude=None):
    """
    Run a scan on a directory.

    Args:
        path: Directory path to scan
        name: Name for the scan
        algorithm: Checksum algorithm to use
        threads: Number of threads to use
        exclude: Comma-separated list of directories to exclude
    """
    # Normalize path
    path = os.path.abspath(path)

    # Parse exclusions
    exclude_dirs = None
    if exclude:
        exclude_dirs = [d.strip() for d in exclude.split(',')]

    # Create a database manager
    db = DatabaseManager()

    # Create a scanner
    scanner = FileScanner(db)

    # Add progress callback
    scanner.add_progress_callback(progress_callback)

    print(f"Starting scan of {path}")
    print(f"Using {algorithm} algorithm with {threads} threads")

    if exclude_dirs:
        print(f"Excluding directories: {', '.join(exclude_dirs)}")

    try:
        # Start scan
        start_time = time.time()
        scan_id = scanner.scan(
            top_level_path=path,
            name=name,
            checksum_method=algorithm,
            threads=threads,
            exclude_dirs=exclude_dirs
        )
        end_time = time.time()

        # Get scan summary
        summary = scanner.get_scan_summary(scan_id)

        print("\nScan complete!")
        print(f"Scan ID: {scan_id}")
        print(f"Time: {end_time - start_time:.2f} seconds")
        print(f"Files scanned: {summary['files_scanned']}")
        print(f"Files unchanged: {summary['files_unchanged']}")
        print(f"Files modified: {summary['files_modified']}")
        print(f"Files corrupted: {summary['files_corrupted']}")
        print(f"Files missing: {summary['files_missing']}")
        print(f"Files new: {summary['files_new']}")
        print(f"Errors: {summary['error_count']}")

        # Show storage devices
        print("\nStorage devices:")
        for device in summary['storage_devices']:
            print(f"  {device['name']} ({device['mount_point']}): {device['file_count']} files")

    except KeyboardInterrupt:
        print("\nScan interrupted, stopping...")
        scanner.stop()
        sys.exit(1)

    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

def main():
    """
    Main entry point for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Bitarr core scanner")

    # Add subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan a directory")
    scan_parser.add_argument("path", help="Directory path to scan")
    scan_parser.add_argument("--name", help="Name for the scan")
    scan_parser.add_argument("--algorithm", default="sha256", help="Checksum algorithm to use")
    scan_parser.add_argument("--threads", type=int, default=4, help="Number of threads to use")
    scan_parser.add_argument("--exclude", help="Comma-separated list of directories to exclude")

    # List algorithms command
    algorithms_parser = subparsers.add_parser("algorithms", help="List available checksum algorithms")

    # Detect devices command
    devices_parser = subparsers.add_parser("devices", help="Detect storage devices")

    # Parse arguments
    args = parser.parse_args()

    if args.command == "scan":
        run_scan(args.path, args.name, args.algorithm, args.threads, args.exclude)
    elif args.command == "algorithms":
        list_checksum_algorithms()
    elif args.command == "devices":
        detect_devices()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
