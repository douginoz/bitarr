"""
Command-line interface for database management.
"""
import sys
import argparse
from pathlib import Path
from .init_db import init_db
from .db_manager import DatabaseManager

def main():
    """Main entry point for database management CLI."""
    parser = argparse.ArgumentParser(description="Bitarr Database Management")
    
    # Add subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument(
        "--path", type=str, help="Path to database file", default=None
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show database information")
    info_parser.add_argument(
        "--path", type=str, help="Path to database file", default=None
    )
    
    # Vacuum command
    vacuum_parser = subparsers.add_parser("vacuum", help="Run VACUUM on database")
    vacuum_parser.add_argument(
        "--path", type=str, help="Path to database file", default=None
    )
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument(
        "--path", type=str, help="Path to database file", default=None
    )
    backup_parser.add_argument(
        "--backup-path", type=str, help="Path for backup file", default=None
    )
    
    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Prune old scans")
    prune_parser.add_argument(
        "--path", type=str, help="Path to database file", default=None
    )
    prune_parser.add_argument(
        "--days", type=int, help="Days old to prune", required=True
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "init":
        db_path = init_db(args.path)
        print(f"Database initialized at: {db_path}")
    
    elif args.command == "info":
        db = DatabaseManager(args.path)
        info = db.get_database_info()
        print("\nDatabase Information:")
        print(f"Path: {db.db_path}")
        print(f"Size: {info['database_size'] / (1024*1024):.2f} MB")
        print("\nCounts:")
        print(f"  Storage Devices: {info['storage_devices_count']}")
        print(f"  Files: {info['files_count']}")
        print(f"  Scans: {info['scans_count']}")
        print(f"  Checksums: {info['checksums_count']}")
        print(f"  Scheduled Scans: {info['scheduled_scans_count']}")
        print(f"  Scan Errors: {info['scan_errors_count']}")
        print(f"  Configuration Items: {info['configuration_count']}")
        
        if info["first_scan"]:
            print(f"\nFirst Scan: {info['first_scan']}")
        if info["last_scan"]:
            print(f"Last Scan: {info['last_scan']}")
    
    elif args.command == "vacuum":
        db = DatabaseManager(args.path)
        success = db.vacuum()
        if success:
            print("VACUUM completed successfully")
        else:
            print("VACUUM failed")
            sys.exit(1)
    
    elif args.command == "backup":
        db = DatabaseManager(args.path)
        backup_path = db.backup(args.backup_path)
        print(f"Backup created at: {backup_path}")
    
    elif args.command == "prune":
        db = DatabaseManager(args.path)
        pruned = db.prune_old_scans(args.days)
        print(f"Pruned {pruned} scans older than {args.days} days")
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
