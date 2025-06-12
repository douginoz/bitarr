#!/usr/bin/env python3
"""
Test script to verify the scanning functionality works via command line.
This helps isolate whether the issue is with the web UI or the core scanning.

Usage:
    python scan_test.py /path/to/test/directory
"""

import sys
import os
import time
from datetime import datetime

# Find the parent directory that contains the bitarr package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to the path so we can import bitarr
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print(f"Current directory: {current_dir}")
print(f"Parent directory: {parent_dir}")
print(f"Python path: {sys.path[:3]}...")

try:
    from db.db_manager import DatabaseManager
    from core.scanner import FileScanner, ChecksumCalculator, DeviceDetector
    print("✓ Successfully imported modules")
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Trying to run the existing command-line interface instead...")
    
    # Try using the existing CLI
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, '-m', 'bitarr', 'core', 'scan', 
            sys.argv[1] if len(sys.argv) > 1 else '/tmp',
            '--threads', '2'
        ], cwd=parent_dir, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Command-line scanning works!")
        else:
            print("❌ Command-line scanning failed")
        
        sys.exit(result.returncode)
        
    except Exception as e2:
        print(f"Could not run CLI either: {e2}")
        sys.exit(1)

def test_scanning():
    """Test the scanning functionality"""
    
    # Get test directory from command line or use a default
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        # Use a safe default test path
        test_path = os.path.expanduser("~/Documents")
        if not os.path.exists(test_path):
            test_path = os.path.expanduser("~")
            if not os.path.exists(test_path):
                test_path = "/tmp"
    
    print(f"Testing scan functionality with path: {test_path}")
    
    if not os.path.exists(test_path):
        print(f"Error: Test path {test_path} does not exist")
        return False
    
    if not os.path.isdir(test_path):
        print(f"Error: Test path {test_path} is not a directory")
        return False
    
    try:
        # Test database connection
        print("1. Testing database connection...")
        db = DatabaseManager()
        db_info = db.get_database_info()
        print(f"   ✓ Database connected. Total scans: {db_info.get('scans_count', 0)}")
        
        # Test device detection
        print("2. Testing device detection...")
        detector = DeviceDetector()
        devices = detector.detect_devices()
        print(f"   ✓ Detected {len(devices)} storage devices")
        for device in devices[:3]:  # Show first 3 devices
            print(f"     - {device.get('name', 'Unknown')} ({device.get('mount_point', 'Unknown')})")
        
        # Test checksum calculator
        print("3. Testing checksum calculator...")
        calculator = ChecksumCalculator()
        algorithms = calculator.get_supported_algorithms()
        print(f"   ✓ Available algorithms: {', '.join(algorithms)}")
        
        # Test scanner initialization
        print("4. Testing scanner initialization...")
        scanner = FileScanner(db)
        print("   ✓ Scanner initialized")
        
        # Test progress callback
        progress_data = []
        def test_progress_callback(data):
            progress_data.append(data)
            status = data.get('status', 'unknown')
            files_processed = data.get('files_processed', 0)
            total_files = data.get('total_files', 0)
            percent = data.get('percent_complete', 0)
            
            print(f"   Progress: {status} - {files_processed}/{total_files} ({percent:.1f}%)")
        
        scanner.add_progress_callback(test_progress_callback)
        
        # Perform a limited scan
        print(f"5. Performing test scan of {test_path}...")
        scan_name = f"Test scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        start_time = time.time()
        scan_id = scanner.scan(
            top_level_path=test_path,
            name=scan_name,
            checksum_method="sha256",
            threads=2,  # Use fewer threads for testing
            exclude_dirs=['.git', 'node_modules', '.venv', '__pycache__']
        )
        end_time = time.time()
        
        print(f"   ✓ Scan completed in {end_time - start_time:.2f} seconds")
        print(f"   ✓ Scan ID: {scan_id}")
        
        # Get scan summary
        print("6. Getting scan summary...")
        summary = scanner.get_scan_summary(scan_id)
        
        if summary:
            print(f"   ✓ Files scanned: {summary.get('files_scanned', 0)}")
            print(f"   ✓ Files unchanged: {summary.get('files_unchanged', 0)}")
            print(f"   ✓ Files modified: {summary.get('files_modified', 0)}")
            print(f"   ✓ Files corrupted: {summary.get('files_corrupted', 0)}")
            print(f"   ✓ Files missing: {summary.get('files_missing', 0)}")
            print(f"   ✓ Files new: {summary.get('files_new', 0)}")
            print(f"   ✓ Errors: {summary.get('error_count', 0)}")
        else:
            print("   ⚠ Could not retrieve scan summary")
        
        # Test progress callback data
        print("7. Checking progress callback data...")
        if progress_data:
            print(f"   ✓ Received {len(progress_data)} progress updates")
            
            # Check for datetime serialization issues
            for i, data in enumerate(progress_data):
                for key, value in data.items():
                    if isinstance(value, datetime):
                        print(f"   ⚠ Found non-serializable datetime in progress data[{i}][{key}]: {value}")
                        print("     This would cause JSON serialization errors in the web UI")
                        return False
            
            print("   ✓ All progress data is serializable")
        else:
            print("   ⚠ No progress updates received")
        
        print("\n✅ All tests passed! The scanning functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_json_serialization():
    """Test JSON serialization of progress data"""
    import json
    
    print("\n8. Testing JSON serialization...")
    
    # Create sample progress data that might be sent via Socket.IO
    sample_progress = {
        'status': 'scanning',
        'scan_id': 123,
        'files_processed': 50,
        'total_files': 100,
        'percent_complete': 50.0,
        'current_path': '/test/file.txt',
        'timestamp': datetime.now()  # This should cause an error
    }
    
    try:
        json.dumps(sample_progress)
        print("   ✓ JSON serialization test passed")
        return True
    except TypeError as e:
        print(f"   ❌ JSON serialization failed: {e}")
        print("   This confirms the datetime serialization issue in the web UI")
        
        # Test the fix
        print("   Testing serialization fix...")
        fixed_progress = {}
        for key, value in sample_progress.items():
            if isinstance(value, datetime):
                fixed_progress[key] = value.isoformat()
            else:
                fixed_progress[key] = value
        
        try:
            json.dumps(fixed_progress)
            print("   ✓ Serialization fix works correctly")
            return True
        except Exception as e2:
            print(f"   ❌ Fix failed: {e2}")
            return False

if __name__ == "__main__":
    print("Bitarr Scanning Test Script")
    print("=" * 40)
    
    success = test_scanning()
    test_json_serialization()
    
    if success:
        print("\n🎉 The core scanning functionality is working!")
        print("   The issue is likely in the web UI Socket.IO integration.")
        print("   Apply the provided fixes to resolve the web interface issues.")
    else:
        print("\n💥 Core scanning functionality has issues.")
        print("   Fix the core scanning problems before addressing web UI issues.")
    
    sys.exit(0 if success else 1)
