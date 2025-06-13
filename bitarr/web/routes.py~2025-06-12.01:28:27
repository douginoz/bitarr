"""
Routes for the Bitarr web application.
"""
from datetime import datetime
import json
import os
import platform
import psutil
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, current_app, Response, stream_with_context
)
from werkzeug.exceptions import NotFound
import threading

from .app import socketio
from bitarr.db.db_manager import DatabaseManager
from bitarr.core.scanner import FileScanner, DeviceDetector
from bitarr.core.scanner.checksum import ChecksumCalculator

# Create blueprint
bp = Blueprint('routes', __name__)

# Create global objects
db = DatabaseManager()
device_detector = DeviceDetector()
active_scans = {}  # Store active scan threads

# Template filters
@bp.app_template_filter('format_size')
def format_size(size):
    """Format a size in bytes to a human-readable form."""
    if size is None:
        return "0 B"

    size = int(size)
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"

@bp.app_template_filter('thousands_separator')
def thousands_separator(value):
    """Add a thousands separator to a number."""
    if value is None:
        return "0"

    return f"{int(value):,}"

@bp.app_template_filter('from_json')
def from_json(value):
    """Convert a JSON string to a Python object."""
    if not value:
        return None

    try:
        return json.loads(value)
    except:
        return None

# Socket.IO progress handler
def handle_scan_progress(progress_data):
    """
    Handle scan progress updates.

    Args:
        progress_data: Progress data dictionary
    """
    # Convert datetime objects to ISO format strings for JSON serialization
    serializable_data = {}
    for key, value in progress_data.items():
        if isinstance(value, datetime):
            serializable_data[key] = value.isoformat()
        else:
            serializable_data[key] = value

    socketio.emit('scan_progress', serializable_data)

@bp.context_processor
def inject_now():
    """
    Inject the current datetime into all templates.
    """
    return {'now': datetime.now()}

@bp.route('/')
def index():
    """
    Home page / dashboard.
    """
    # Get recent scans
    recent_scans = db.get_recent_scans(limit=5)

    # Get storage devices
    devices = device_detector.detect_devices()

    # Get database info
    db_info = db.get_database_info()

    return render_template(
        'index.html',
        recent_scans=recent_scans,
        storage_devices=devices,
        active_scans=active_scans,
        db_info=db_info
    )

@bp.route('/scan_history')
def scan_history():
    """
    Scan history page.
    """
    # Get page parameters
    current_page = request.args.get('page', 1, type=int)
    page_size = 10

    # Get total count for pagination
    total_scans = db.count_scans()

    # Calculate offset
    offset = (current_page - 1) * page_size

    # Get paginated scans
    scans = db.get_recent_scans(limit=page_size, offset=offset)

    return render_template(
        'scan_history.html',
        scans=scans,
        total_scans=total_scans,
        current_page=current_page,
        page_size=page_size
    )

@bp.route('/scan_details/<int:scan_id>')
def scan_details(scan_id):
    """
    Scan detail page.

    Args:
        scan_id: ID of the scan
    """
    # Get scan details
    scan = db.get_scan(scan_id)
    if not scan:
        flash('Scan not found', 'error')
        return redirect(url_for('routes.scan_history'))

    # Get scan errors
    errors = db.get_scan_errors(scan_id)

    # Create scanner to get summary
    scanner = FileScanner(db)
    summary = scanner.get_scan_summary(scan_id)

    # DEBUG: Print scan object info
    print(f"DEBUG: scan.start_time type: {type(scan.start_time)}, value: {scan.start_time}")
    print(f"DEBUG: scan.end_time type: {type(scan.end_time)}, value: {scan.end_time}")

    return render_template(
        'scan_details.html',
        scan=scan,
        summary=summary,
        errors=errors
    )

@bp.route('/scheduled_scans')
def scheduled_scans():
    """
    Scheduled scans page.
    """
    # Get all scheduled scans
    schedules = db.get_all_scheduled_scans()

    return render_template(
        'scheduled_scans.html',
        schedules=schedules,
        active_scans=active_scans,
        now=datetime.now()
    )

@bp.route('/storage_health')
def storage_health():
    """
    Storage health page.
    """
    # Get storage devices
    devices = device_detector.detect_devices()

    # Get database manager
    db_manager = DatabaseManager()

    # Get storage device health information
    device_health = {}
    for device in devices:
        device_id = device['device_id']
        storage_device = db_manager.get_storage_device(device_id=device_id)

        if storage_device:
            # Get file counts
            query = """
                SELECT c.status, COUNT(*) as count
                FROM checksums c
                JOIN files f ON c.file_id = f.id
                WHERE f.storage_device_id = ?
                GROUP BY c.status
            """
            params = (storage_device.id,)

            with db_manager.lock:
                conn = db_manager.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute(query, params)

                    status_counts = {}
                    for row in cursor.fetchall():
                        status_counts[row['status']] = row['count']

                    # Calculate corruption trend (dummy data for now)
                    trend = 0
                    if 'corrupted' in status_counts and status_counts['corrupted'] > 0:
                        # In a real implementation, we would compare with historical data
                        trend = 0.5  # Positive means increasing corruption

                    # Add corruption events (dummy data for now)
                    corruption_events = []
                    if 'corrupted' in status_counts and status_counts['corrupted'] > 0:
                        # In a real implementation, we would get actual corruption events
                        corruption_events = [
                            {
                                'date': '2025-05-15',
                                'corrupted_files': 3,
                                'path': device['mount_point'] + '/path/to/files',
                                'most_affected_directory': '/path/to/corruption',
                                'directory_corrupted_files': 2,
                                'scan_id': 1
                            }
                        ]

                    # Add to device health
                    device_health[device_id] = {
                        'storage_device': storage_device,
                        'status_counts': status_counts,
                        'trend': trend,
                        'corruption_events': corruption_events
                    }
                finally:
                    conn.close()

    return render_template(
        'storage_health.html',
        storage_devices=devices,
        device_health=device_health,
        now=datetime.now()
    )

@bp.route('/configuration')
def configuration():
    """
    Configuration page.
    """
    # Get all configuration values
    config = db.get_all_configuration()

    # Get available checksum algorithms
    calculator = ChecksumCalculator()
    algorithms = calculator.get_supported_algorithms()
    algo_info = calculator.algorithm_info()

    # Get system info
    system_info = {
        'os': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_cores': os.cpu_count(),
        'memory': f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
    }

    # App version and other metadata
    app_version = "1.0.0"  # Replace with actual version

    return render_template(
        'configuration.html',
        config=config,
        algorithms=algorithms,
        algo_info=algo_info,
        system_info=system_info,
        app_version=app_version,
        release_date="May 18, 2025",
        license="MIT"
    )

@bp.route('/database_management')
def database_management():
    """
    Database management page.
    """
    # Create database manager
    db_manager = DatabaseManager()

    # Get database info
    db_info = db_manager.get_database_info()

    # Get recent scans (for Manage Scans tab)
    scans = db_manager.get_recent_scans(limit=10)

    # Get total scan count
    total_scans = db_manager.count_scans()

    # Get storage devices
    from bitarr.core.scanner import DeviceDetector
    detector = DeviceDetector()
    storage_devices = detector.detect_devices()

    # Get active scans count
    active_scans_result = db_manager.check_for_active_scans()
    active_scan_count = 0
    active_scans = []
    if active_scans_result['success']:
        active_scan_count = active_scans_result['active_scan_count']
        active_scans = active_scans_result['active_scans']

    # Calculate storage statistics
    storage_stats = {}
    for device in storage_devices:
        device_id = device.get('device_id')

        # Skip devices without ID
        if not device_id:
            continue

        # Get storage device from database
        storage_device = db_manager.get_storage_device(device_id=device_id)

        if storage_device:
            # Calculate health and status
            health_score = 100  # Default to 100%
            health_status = "good"

            # In a real implementation, would query for corrupted files, etc.
            # For now, just use example data
            corrupted_files = 0
            missing_files = 0
            total_files = 0

            # Add to stats
            storage_stats[device_id] = {
                'health_score': health_score,
                'health_status': health_status,
                'corrupted_files': corrupted_files,
                'missing_files': missing_files,
                'total_files': total_files
            }

    # Get backup settings
    backup_settings = db_manager.get_backup_settings()

    # List backups
    backups_result = db_manager.list_backups()
    backups = []
    if backups_result['success']:
        backups = backups_result['backups']

    # Run integrity check
    integrity_result = db_manager.run_integrity_check()
    integrity_status = "unknown"
    if integrity_result['success']:
        integrity_status = integrity_result['integrity_status']

    # Check for disk space
    import shutil
    disk_space = {}
    try:
        db_path = db_manager.db_path
        disk_usage = shutil.disk_usage(os.path.dirname(db_path))
        disk_space = {
            'total': disk_usage.total,
            'used': disk_usage.used,
            'free': disk_usage.free,
            'percent_used': (disk_usage.used / disk_usage.total) * 100
        }
    except Exception as e:
        print(f"Error getting disk space: {str(e)}")

    # Get date of last vacuum
    last_vacuum = db_manager.get_configuration('last_vacuum_date')
    last_vacuum_date = None
    if last_vacuum and last_vacuum.value:
        last_vacuum_date = last_vacuum.value

    # Prepare database health metrics
    db_health = {
        'integrity_status': integrity_status,
        'integrity_check_date': db_manager.get_configuration('last_integrity_check_date'),
        'disk_usage_percent': disk_space.get('percent_used', 0),
        'disk_free': disk_space.get('free', 0),
        'disk_status': 'sufficient' if disk_space.get('percent_used', 0) < 80 else 'low',
        'vacuum_date': last_vacuum_date,
        'vacuum_status': 'recent' if last_vacuum_date else 'never',
        'missing_files': db_info.get('missing_files_count', 0),
        'missing_files_status': 'review_recommended' if db_info.get('missing_files_count', 0) > 0 else 'good'
    }

    # Calculate stats for tracked files
    file_stats = {
        'total': db_info.get('files_count', 0),
        'corrupted': db_info.get('corrupted_files_count', 0),
        'missing': db_info.get('missing_files_count', 0),
        'modified': db_info.get('modified_files_count', 0),
        'unchanged': db_info.get('unchanged_files_count', 0),
        'new': db_info.get('new_files_count', 0)
    }

    # Convert dates for better display
    from datetime import datetime, timezone
    if db_info.get('first_scan'):
        try:
            first_scan_date = datetime.fromisoformat(db_info['first_scan'].replace('Z', '+00:00'))
            db_info['first_scan_date'] = first_scan_date.strftime('%Y-%m-%d')
            # Calculate days since first scan
            days_since = (datetime.now(timezone.utc) - first_scan_date).days
            db_info['days_since_first_scan'] = days_since
        except Exception as e:
            print(f"Error formatting first scan date: {str(e)}")

    if db_info.get('last_scan'):
        try:
            last_scan_date = datetime.fromisoformat(db_info['last_scan'].replace('Z', '+00:00'))
            db_info['last_scan_date'] = last_scan_date.strftime('%Y-%m-%d')
            db_info['last_scan_time'] = last_scan_date.strftime('%H:%M')
        except Exception as e:
            print(f"Error formatting last scan date: {str(e)}")

    return render_template(
        'database_management.html',
        db_info=db_info,
        total_scans=total_scans,
        scans=scans,
        storage_devices=storage_devices,
        storage_stats=storage_stats,
        file_stats=file_stats,
        active_scan_count=active_scan_count,
        active_scans=active_scans,
        backup_settings=backup_settings,
        backups=backups,
        db_health=db_health
    )

@bp.route('/api/scan/start', methods=['POST'])
def api_scan_start():
    """
    API endpoint to start a scan.
    """
    # Get parameters from request
    try:
        data = request.get_json()
        path = data.get('path')
        name = data.get('name')
        algorithm = data.get('algorithm', 'sha256')
        threads = int(data.get('threads', 4))
        exclude_dirs = data.get('exclude_dirs', '').split(',') if data.get('exclude_dirs') else None
        exclude_patterns = data.get('exclude_patterns', '').split(',') if data.get('exclude_patterns') else None
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    # Validate parameters
    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400
    if not os.path.exists(path):
        return jsonify({'success': False, 'error': f'Path does not exist: {path}'}), 400
    if not os.path.isdir(path):
        return jsonify({'success': False, 'error': f'Path is not a directory: {path}'}), 400

    # Create scanner
    scanner = FileScanner(db)

    # Create a temporary scan_id for tracking before the actual scan starts
    import time
    temp_scan_id = f"temp_{int(time.time() * 1000)}"

    # Add progress callback with scan_id
    def progress_callback_wrapper(progress_data):
        progress_data['scan_id'] = temp_scan_id
        handle_scan_progress(progress_data)

    scanner.add_progress_callback(progress_callback_wrapper)

    # Start scan in a background thread
    def run_scan():
        try:
            actual_scan_id = scanner.scan(
                top_level_path=path,
                name=name,
                checksum_method=algorithm,
                threads=threads,
                exclude_dirs=exclude_dirs,
                exclude_patterns=exclude_patterns
            )

            print(f"DEBUG: Scan completed. Temp ID: {temp_scan_id}, Actual ID: {actual_scan_id}")  # ADD THIS LINE

            # Update active_scans with actual ID
            if temp_scan_id in active_scans:
                active_scans[actual_scan_id] = active_scans.pop(temp_scan_id)
            # Remove from active scans when done
            if actual_scan_id in active_scans:
                del active_scans[actual_scan_id]

            # Emit completion event with BOTH IDs
            completion_data = {
                'scan_id': actual_scan_id,
                'temp_scan_id': temp_scan_id,
                'summary': scanner.get_scan_summary(actual_scan_id)
            }
            print(f"DEBUG: Emitting scan_complete: {completion_data}")  # ADD THIS LINE
            socketio.emit('scan_complete', completion_data)

        except Exception as e:
            print(f"Scan error: {str(e)}")
            # Clean up temp scan
            if temp_scan_id in active_scans:
                del active_scans[temp_scan_id]
            socketio.emit('scan_error', {
                'temp_scan_id': temp_scan_id,
                'error': str(e)
            })
    scan_thread = threading.Thread(target=run_scan)
    scan_thread.daemon = True
    scan_thread.start()
    # Store the thread for status checking using temp_scan_id
    active_scans[temp_scan_id] = {  # <- CHANGED to temp_scan_id
        'thread': scan_thread,
        'scanner': scanner,
        'start_time': datetime.now(),
        'path': path
    }
    return jsonify({
        'success': True,
        'scan_id': temp_scan_id,  # <- CHANGED to temp_scan_id
        'message': f'Scan started for {path}'
    })

@bp.route('/api/scan/stop/<int:scan_id>', methods=['POST'])
def api_scan_stop(scan_id):
    """
    API endpoint to stop a scan.

    Args:
        scan_id: ID of the scan to stop
    """
    global active_scans

    if scan_id not in active_scans:
        return jsonify({'success': False, 'error': 'Scan not found or already completed'}), 404

    # Stop the scan
    scanner = active_scans[scan_id]['scanner']
    scanner.stop()

    # Wait for the thread to finish
    active_scans[scan_id]['thread'].join(timeout=5)

    # Remove from active scans
    del active_scans[scan_id]

    return jsonify({
        'success': True,
        'message': f'Scan {scan_id} stopped'
    })

@bp.route('/api/scan/status/<int:scan_id>')
def api_scan_status(scan_id):
    """
    API endpoint to get scan status.

    Args:
        scan_id: ID of the scan
    """
    global active_scans

    if scan_id in active_scans:
        # Scan is running
        scanner = active_scans[scan_id]['scanner']
        return jsonify({
            'status': 'running',
            'scan_id': scan_id,
            'files_processed': scanner.files_processed,
            'total_files': scanner.total_files,
            'percent_complete': (scanner.files_processed / scanner.total_files * 100) if scanner.total_files > 0 else 0,
            'start_time': active_scans[scan_id]['start_time'].isoformat(),
            'path': active_scans[scan_id]['path']
        })

    # Check if scan exists in database
    scan = db.get_scan(scan_id)
    if not scan:
        return jsonify({'status': 'not_found'}), 404

    return jsonify({
        'status': scan.status,
        'scan_id': scan.id,
        'files_scanned': scan.files_scanned,
        'start_time': scan.start_time.isoformat() if scan.start_time else None,
        'end_time': scan.end_time.isoformat() if scan.end_time else None,
        'path': scan.top_level_path
    })

@bp.route('/api/devices')
def api_devices():
    """
    API endpoint to get storage devices.
    """
    devices = device_detector.detect_devices()
    return jsonify({'devices': devices})

# Database management API endpoints
@bp.route('/api/db/vacuum', methods=['POST'])
def api_db_vacuum():
    """API endpoint to vacuum the database."""
    try:
        db.vacuum()
        return jsonify({'success': True, 'message': 'Database vacuum completed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/reindex', methods=['POST'])
def api_db_reindex():
    """API endpoint to reindex the database."""
    try:
        db.reindex()
        return jsonify({'success': True, 'message': 'Database reindex completed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/reset', methods=['POST'])
def api_db_reset():
    """API endpoint to reset the database."""
    try:
        # Verification code from request
        data = request.get_json()
        confirmation = data.get('confirmation')

        if confirmation != 'RESET':
            return jsonify({'success': False, 'error': 'Invalid confirmation code'}), 400

        db.reset()
        return jsonify({'success': True, 'message': 'Database reset completed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/clear_old_scans', methods=['POST'])
def api_db_clear_old_scans():
    """API endpoint to clear old scans."""
    try:
        data = request.get_json()
        days = int(data.get('days', 30))

        count = db.clear_old_scans(days)
        return jsonify({'success': True, 'message': f'Cleared {count} old scans'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/purge_missing_files', methods=['POST'])
def api_db_purge_missing_files():
    """API endpoint to purge missing files."""
    try:
        data = request.get_json()
        days = int(data.get('days', 30))

        count = db.purge_missing_files(days)
        return jsonify({'success': True, 'message': f'Purged {count} missing files'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/backup', methods=['POST'])
def api_db_backup():
    """API endpoint to create a database backup."""
    try:
        data = request.get_json()
        name = data.get('name')

        backup_id = db.create_backup(name)
        return jsonify({'success': True, 'backup_id': backup_id, 'message': 'Backup created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/backup/<int:backup_id>/restore', methods=['POST'])
def api_db_restore(backup_id):
    """API endpoint to restore a database backup."""
    try:
        db.restore_backup(backup_id)
        return jsonify({'success': True, 'message': 'Backup restored successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/db/backup/<int:backup_id>/delete', methods=['POST'])
def api_db_delete_backup(backup_id):
    """API endpoint to delete a database backup."""
    try:
        db.delete_backup(backup_id)
        return jsonify({'success': True, 'message': 'Backup deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
