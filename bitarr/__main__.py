"""
Main entry point for Bitarr application.
"""
import argparse
import sys

def main():
    """
    Main entry point for Bitarr.
    """
    parser = argparse.ArgumentParser(description="Bitarr - File Integrity Scanner")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Web command
    web_parser = subparsers.add_parser("web", help="Run the web interface")
    web_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    web_parser.add_argument('--port', type=int, default=8286, help='Port to bind to')
    web_parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    # Core command
    core_parser = subparsers.add_parser("core", help="Run core scanner functions")
    core_subparsers = core_parser.add_subparsers(dest="core_command", help="Core command")

    # Scan command
    scan_parser = core_subparsers.add_parser("scan", help="Scan a directory")
    scan_parser.add_argument("path", help="Directory path to scan")
    scan_parser.add_argument("--name", help="Name for the scan")
    scan_parser.add_argument("--algorithm", default="sha256", help="Checksum algorithm to use")
    scan_parser.add_argument("--threads", type=int, default=4, help="Number of threads to use")
    scan_parser.add_argument("--exclude", help="Comma-separated list of directories to exclude")

    # Algorithms command
    algorithms_parser = core_subparsers.add_parser("algorithms", help="List available checksum algorithms")

    # Devices command
    devices_parser = core_subparsers.add_parser("devices", help="Detect storage devices")

    # DB command
    db_parser = subparsers.add_parser("db", help="Database management")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="Database command")

    # Init command
    init_parser = db_subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--path", type=str, help="Path to database file", default=None)

    # Info command
    info_parser = db_subparsers.add_parser("info", help="Show database information")
    info_parser.add_argument("--path", type=str, help="Path to database file", default=None)

    # Parse arguments
    args = parser.parse_args()

    if args.command == "web":
        # Import web module and run
        from bitarr.web import create_app, socketio
        from bitarr.db.init_db import init_db
        from bitarr.db.db_manager import DatabaseManager

        # Check if database exists, initialize if needed
        try:
            db = DatabaseManager()
            db.get_all_configuration()
        except Exception:
            print("Database not found or incomplete. Initializing...")
            init_db()

        # Create app and run
        app = create_app()
        socketio.run(app, host=args.host, port=args.port, debug=args.debug)

    elif args.command == "core":
        if args.core_command == "scan":
            # Import core module and run scan
            from bitarr.core.scanner import FileScanner, ScannerError
            from bitarr.db.db_manager import DatabaseManager

            # Parse exclude dirs
            exclude_dirs = None
            if args.exclude:
                exclude_dirs = [d.strip() for d in args.exclude.split(',')]

            try:
                # Create scanner
                db = DatabaseManager()
                scanner = FileScanner(db)

                # Define progress callback
                def progress_callback(progress_data):
                    """Callback function to display scan progress."""
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
                        short_path = current_path.split('/')[-1] if current_path else ''
                        print(f"\rScanning: {files_processed}/{total_files} ({percent:.1f}%) - {short_path}", end="")
                    elif status == "completed":
                        print(f"\nScan completed: {files_processed} files processed")
                    elif status == "failed":
                        print(f"\nScan failed: {progress_data.get('error', 'Unknown error')}")

                # Add progress callback
                scanner.add_progress_callback(progress_callback)

                # Run scan
                scan_id = scanner.scan(
                    top_level_path=args.path,
                    name=args.name,
                    checksum_method=args.algorithm,
                    threads=args.threads,
                    exclude_dirs=exclude_dirs
                )

                # Get scan results
                scan_summary = scanner.get_scan_summary(scan_id)

                # Print results
                print("\nScan complete!")
                print(f"Scan ID: {scan_id}")
                print(f"Files scanned: {scan_summary['files_scanned']}")
                print(f"Files unchanged: {scan_summary['files_unchanged']}")
                print(f"Files modified: {scan_summary['files_modified']}")
                print(f"Files corrupted: {scan_summary['files_corrupted']}")
                print(f"Files missing: {scan_summary['files_missing']}")
                print(f"Files new: {scan_summary['files_new']}")

            except ScannerError as e:
                print(f"Error: {str(e)}")
                sys.exit(1)
            except KeyboardInterrupt:
                print("\nScan interrupted.")
                sys.exit(1)

        elif args.core_command == "algorithms":
            # Import core module and list algorithms
            from bitarr.core.scanner import ChecksumCalculator

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

        elif args.core_command == "devices":
            # Import core module and detect devices
            from bitarr.core.scanner import DeviceDetector

            detector = DeviceDetector()
            devices = detector.detect_devices()

            print(f"Detected {len(devices)} storage devices:")
            for i, device in enumerate(devices, 1):
                print(f"  {i}. {device['name']} ({device['mount_point']})")
                print(f"     Type: {device['device_type']}")
                if 'total_size' in device and device['total_size'] > 0:
                    size_gb = device['total_size'] / (1024**3)
                    print(f"     Size: {size_gb:.1f} GB")
                    print(f"     Used: {device['usage_percent']:.1f}%")
                print(f"     Device ID: {device['device_id']}")
                print()

        else:
            core_parser.print_help()

    elif args.command == "db":
        if args.db_command == "init":
            # Import db module and initialize
            from bitarr.db.init_db import init_db

            db_path = init_db(args.path)
            print(f"Database initialized at: {db_path}")

        elif args.db_command == "info":
            # Import db module and show info
            from bitarr.db.db_manager import DatabaseManager

            db = DatabaseManager(args.path)
            info = db.get_database_info()

            print("\nDatabase Information:")
            print(f"Path: {db.db_path}")
            size_mb = info['database_size'] / (1024*1024) if 'database_size' in info else 0
            print(f"Size: {size_mb:.2f} MB")

            print("\nCounts:")
            print(f"  Storage Devices: {info.get('storage_devices_count', 0)}")
            print(f"  Files: {info.get('files_count', 0)}")
            print(f"  Scans: {info.get('scans_count', 0)}")
            print(f"  Checksums: {info.get('checksums_count', 0)}")
            print(f"  Scheduled Scans: {info.get('scheduled_scans_count', 0)}")
            print(f"  Scan Errors: {info.get('scan_errors_count', 0)}")
            print(f"  Configuration Items: {info.get('configuration_count', 0)}")

            if info.get('first_scan'):
                print(f"\nFirst Scan: {info['first_scan']}")
            if info.get('last_scan'):
                print(f"Last Scan: {info['last_scan']}")

        else:
            db_parser.print_help()

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
