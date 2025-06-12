"""
API endpoints for Bitarr application.
"""
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from bitarr.db.db_manager import DatabaseManager
from bitarr.db.models import ScheduledScan, Configuration
from .routes import active_scans

# Create blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# Create blueprint
db_api = Blueprint('db_api', __name__, url_prefix='/api/db')

# Create database manager
db = DatabaseManager()

# === Scheduled Scans APIs ===

@bp.route('/scheduled_scans', methods=['GET'])
def get_scheduled_scans():
    """
    Get all scheduled scans.

    Returns:
        dict: List of scheduled scans
    """
    # Get scheduled scans
    scheduled_scans = db.get_all_scheduled_scans()

    return jsonify([scan.to_dict() for scan in scheduled_scans])

@bp.route('/scheduled_scans', methods=['POST'])
def create_scheduled_scan():
    """
    Create a new scheduled scan.

    Returns:
        dict: Created scheduled scan
    """
    # Get request data
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Validate input
    required_fields = ['name', 'paths', 'frequency', 'parameters']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    # Convert paths to JSON if it's a list
    paths = data['paths']
    if isinstance(paths, list):
        paths = json.dumps(paths)

    # Convert parameters to JSON if it's a dict
    parameters = data['parameters']
    if isinstance(parameters, dict):
        parameters = json.dumps(parameters)

    scheduled_scan = ScheduledScan(
        name=data['name'],
        paths=paths,
        frequency=data['frequency'],
        parameters=parameters,
        next_run=data.get('next_run'),
        status=data.get('status', 'active'),
        priority=data.get('priority', 0),
        max_runtime=data.get('max_runtime'),
        is_active=data.get('is_active', True)
    )

    # Add to database
    scheduled_scan.id = db.add_scheduled_scan(scheduled_scan)

    return jsonify({'success': True, 'scheduled_scan': scheduled_scan.to_dict()})

@bp.route('/scheduled_scans/<int:scheduled_scan_id>', methods=['GET'])
def get_scheduled_scan(scheduled_scan_id):
    """
    Get a scheduled scan.

    Args:
        scheduled_scan_id: ID of the scheduled scan

    Returns:
        dict: Scheduled scan details
    """
    # Get scheduled scan
    scheduled_scan = db.get_scheduled_scan(scheduled_scan_id)
    if not scheduled_scan:
        return jsonify({'success': False, 'error': 'Scheduled scan not found'}), 404

    return jsonify({'success': True, 'scheduled_scan': scheduled_scan.to_dict()})

@bp.route('/scheduled_scans/<int:scheduled_scan_id>', methods=['PUT'])
def update_scheduled_scan(scheduled_scan_id):
    """
    Update a scheduled scan.

    Args:
        scheduled_scan_id: ID of the scheduled scan

    Returns:
        dict: Updated scheduled scan
    """
    # Get request data
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Get scheduled scan
    scheduled_scan = db.get_scheduled_scan(scheduled_scan_id)
    if not scheduled_scan:
        return jsonify({'success': False, 'error': 'Scheduled scan not found'}), 404

    # Update fields
    if 'name' in data:
        scheduled_scan.name = data['name']

    if 'paths' in data:
        paths = data['paths']
        if isinstance(paths, list):
            paths = json.dumps(paths)
        scheduled_scan.paths = paths

    if 'frequency' in data:
        scheduled_scan.frequency = data['frequency']

    if 'parameters' in data:
        parameters = data['parameters']
        if isinstance(parameters, dict):
            parameters = json.dumps(parameters)
        scheduled_scan.parameters = parameters

    if 'next_run' in data:
        scheduled_scan.next_run = data['next_run']

    if 'status' in data:
        scheduled_scan.status = data['status']

    if 'priority' in data:
        scheduled_scan.priority = data['priority']

    if 'max_runtime' in data:
        scheduled_scan.max_runtime = data['max_runtime']

    if 'is_active' in data:
        scheduled_scan.is_active = data['is_active']

    # Update in database
    db.update_scheduled_scan(scheduled_scan)

    return jsonify({'success': True, 'scheduled_scan': scheduled_scan.to_dict()})

@bp.route('/scheduled_scans/<int:scheduled_scan_id>', methods=['DELETE'])
def delete_scheduled_scan(scheduled_scan_id):
    """
    Delete a scheduled scan.

    Args:
        scheduled_scan_id: ID of the scheduled scan

    Returns:
        dict: Success message
    """
    # Delete scheduled scan
    result = db.delete_scheduled_scan(scheduled_scan_id)

    if result:
        return jsonify({'success': True, 'message': 'Scheduled scan deleted'})

    return jsonify({'success': False, 'error': 'Scheduled scan not found'}), 404

@bp.route('/scheduled_scans/<int:scheduled_scan_id>/run', methods=['POST'])
def run_scheduled_scan(scheduled_scan_id):
    """
    Run a scheduled scan immediately.

    Args:
        scheduled_scan_id: ID of the scheduled scan

    Returns:
        dict: Success message
    """
    # Get scheduled scan
    scheduled_scan = db.get_scheduled_scan(scheduled_scan_id)
    if not scheduled_scan:
        return jsonify({'success': False, 'error': 'Scheduled scan not found'}), 404

    # TODO: Implement immediate execution of the scheduled scan
    # This would involve parsing the scheduled scan's paths and parameters,
    # then starting a scan similar to how it's done in the routes.py file.

    return jsonify({'success': False, 'error': 'Not implemented yet'}), 501

# === Configuration APIs ===

@bp.route('/configuration', methods=['GET'])
def get_configuration():
    """
    Get all configuration values.

    Returns:
        dict: Configuration values
    """
    # Get configuration
    config = db.get_all_configuration()

    return jsonify({'success': True, 'configuration': config})

@bp.route('/configuration/<key>', methods=['GET'])
def get_configuration_value(key):
    """
    Get a specific configuration value.

    Args:
        key: Configuration key

    Returns:
        dict: Configuration value
    """
    # Get configuration
    config = db.get_configuration(key)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration key not found'}), 404

    return jsonify({
        'success': True,
        'key': config.key,
        'value': config.get_typed_value(),
        'value_type': config.value_type,
        'description': config.description
    })

@bp.route('/configuration/<key>', methods=['PUT'])
def update_configuration(key):
    """
    Update a configuration value.

    Args:
        key: Configuration key

    Returns:
        dict: Updated configuration
    """
    # Get request data
    data = request.json
    if not data or 'value' not in data:
        return jsonify({'success': False, 'error': 'No value provided'}), 400

    # Update configuration
    value = data['value']
    value_type = data.get('value_type')
    description = data.get('description')

    result = db.set_configuration(key, value, value_type, description)

    if result:
        config = db.get_configuration(key)
        return jsonify({
            'success': True,
            'key': config.key,
            'value': config.get_typed_value(),
            'value_type': config.value_type,
            'description': config.description
        })

    return jsonify({'success': False, 'error': 'Failed to update configuration'}), 500

# === Database Management APIs ===

@bp.route('/database/info', methods=['GET'])
def get_database_info():
    """
    Get information about the database.

    Returns:
        dict: Database information
    """
    # Get database info
    info = db.get_database_info()

    return jsonify({'success': True, 'info': info})

@bp.route('/database/vacuum', methods=['POST'])
def vacuum_database():
    """
    Run VACUUM on the database.

    Returns:
        dict: Success message
    """
    # Run vacuum
    result = db.vacuum()

    if result:
        return jsonify({'success': True, 'message': 'Database vacuum completed'})

    return jsonify({'success': False, 'error': 'Failed to vacuum database'}), 500

@bp.route('/database/backup', methods=['POST'])
def backup_database():
    """
    Create a database backup.

    Returns:
        dict: Success message with backup path
    """
    # Create backup
    backup_path = db.backup()

    return jsonify({'success': True, 'message': 'Database backup created', 'backup_path': backup_path})

@bp.route('/database/prune', methods=['POST'])
def prune_database():
    """
    Prune old scans from the database.

    Returns:
        dict: Success message with number of scans pruned
    """
    # Get request data
    data = request.json
    if not data or 'days_old' not in data:
        return jsonify({'success': False, 'error': 'No days_old provided'}), 400

    days_old = int(data['days_old'])

    # Prune scans
    pruned = db.prune_old_scans(days_old)

    return jsonify({'success': True, 'message': f'Pruned {pruned} scans older than {days_old} days'})

# === Stats and Metrics APIs ===

@bp.route('/stats/overview', methods=['GET'])
def get_stats_overview():
    """
    Get overview statistics.

    Returns:
        dict: Overview statistics
    """
    # Get database info
    db_info = db.get_database_info()

    # Get active scans
    active_scan_count = len(active_scans)

    # Get last day's corruption stats
    # TODO: Implement query for corruption stats

    stats = {
        'files_count': db_info.get('files_count', 0),
        'scans_count': db_info.get('scans_count', 0),
        'storage_devices_count': db_info.get('storage_devices_count', 0),
        'active_scans': active_scan_count,
        'database_size': db_info.get('database_size', 0),
        'last_scan': db_info.get('last_scan'),
        'first_scan': db_info.get('first_scan')
    }

    return jsonify({'success': True, 'stats': stats})

@bp.route('/stats/storage_health', methods=['GET'])
def get_storage_health_stats():
    """
    Get storage health statistics.

    Returns:
        dict: Storage health statistics
    """
    # Get storage devices from database
    from bitarr.core.scanner import DeviceDetector

    detector = DeviceDetector()
    devices = detector.detect_devices()

    # Get corruption stats for each device
    device_stats = []

    for device in devices:
        device_id = device.get('device_id')

        # Skip devices without ID
        if not device_id:
            continue

        # Get storage device from database
        storage_device = db.get_storage_device(device_id=device_id)

        if not storage_device:
            continue

        # Get corruption stats
        query = """
            SELECT c.status, COUNT(*) as count
            FROM checksums c
            JOIN files f ON c.file_id = f.id
            WHERE f.storage_device_id = ?
            GROUP BY c.status
        """

        with db.lock:
            conn = db.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, (storage_device.id,))

                status_counts = {}
                for row in cursor.fetchall():
                    status_counts[row['status']] = row['count']

                # Calculate health score (simple calculation for now)
                total_files = sum(status_counts.values())
                corrupted = status_counts.get('corrupted', 0)
                missing = status_counts.get('missing', 0)

                health_score = 100.0
                if total_files > 0:
                    health_score = max(0, 100 - (corrupted + missing) * 100.0 / total_files)

                device_stats.append({
                    'device_id': device_id,
                    'name': device.get('name'),
                    'mount_point': device.get('mount_point'),
                    'device_type': device.get('device_type'),
                    'total_size': device.get('total_size'),
                    'used_size': device.get('used_size'),
                    'total_files': total_files,
                    'status_counts': status_counts,
                    'health_score': health_score
                })
            finally:
                conn.close()

    return jsonify({'success': True, 'device_stats': device_stats})

@bp.route('/stats/scan_trends', methods=['GET'])
def get_scan_trends():
    """
    Get scan trends over time.

    Returns:
        dict: Scan trends statistics
    """
    # Get request parameters
    days = request.args.get('days', 30, type=int)

    # TODO: Implement query for scan trends
    # This would track metrics like corrupted files over time

    return jsonify({'success': False, 'error': 'Not implemented yet'}), 501

@db_api.route('/info', methods=['GET'])
def get_database_info():
    """
    Get information about the database.

    Returns:
        dict: Database information
    """
    # Get database info
    info = db.get_database_info()

    return jsonify({'success': True, 'info': info})

# === Reset Database Endpoints ===

@db_api.route('/reset/scan_history', methods=['POST'])
def reset_scan_history():
    """
    Reset scan history only, keeping schedules and configuration.

    Returns:
        dict: Status dictionary
    """
    # Verify confirmation code
    data = request.json
    if not data or data.get('confirmation') != 'RESET':
        return jsonify({
            'success': False,
            'error': 'Invalid confirmation code. Expected "RESET".'
        }), 400

    # Check for active scans
    active_scans_result = db.check_for_active_scans()
    if not active_scans_result['success']:
        return jsonify(active_scans_result), 500

    if active_scans_result['active_scan_count'] > 0:
        # Mark active scans as aborted
        db.mark_scans_as_aborted()

    # Perform reset
    result = db.reset_scan_history()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/reset/full', methods=['POST'])
def reset_full():
    """
    Reset database but keep configuration.

    Returns:
        dict: Status dictionary
    """
    # Verify confirmation code
    data = request.json
    if not data or data.get('confirmation') != 'RESET':
        return jsonify({
            'success': False,
            'error': 'Invalid confirmation code. Expected "RESET".'
        }), 400

    # Check for active scans
    active_scans_result = db.check_for_active_scans()
    if not active_scans_result['success']:
        return jsonify(active_scans_result), 500

    if active_scans_result['active_scan_count'] > 0:
        # Mark active scans as aborted
        db.mark_scans_as_aborted()

    # Perform reset
    result = db.reset_full()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/reset/complete', methods=['POST'])
def reset_complete():
    """
    Reset everything to default values.

    Returns:
        dict: Status dictionary
    """
    # Verify confirmation code
    data = request.json
    if not data or data.get('confirmation') != 'RESET':
        return jsonify({
            'success': False,
            'error': 'Invalid confirmation code. Expected "RESET".'
        }), 400

    # Check for active scans
    active_scans_result = db.check_for_active_scans()
    if not active_scans_result['success']:
        return jsonify(active_scans_result), 500

    if active_scans_result['active_scan_count'] > 0:
        # Mark active scans as aborted
        db.mark_scans_as_aborted()

    # Perform reset
    result = db.reset_complete()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

# === Maintenance Endpoints ===

@db_api.route('/vacuum', methods=['POST'])
def vacuum_database():
    """
    Run VACUUM on the database.

    Returns:
        dict: Success message
    """
    # Run vacuum
    result = db.vacuum()

    if result:
        return jsonify({'success': True, 'message': 'Database vacuum completed'})
    else:
        return jsonify({'success': False, 'error': 'Failed to vacuum database'}), 500

@db_api.route('/reindex', methods=['POST'])
def reindex_database():
    """
    Rebuild all database indexes.

    Returns:
        dict: Status dictionary
    """
    # Run reindex
    result = db.reindex()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/clear_old_scans', methods=['POST'])
def clear_old_scans():
    """
    Delete scans older than the specified number of days.

    Returns:
        dict: Status dictionary
    """
    # Get request data
    data = request.json
    if not data or 'days' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required parameter: days'
        }), 400

    days = int(data['days'])

    # Clear old scans
    result = db.clear_old_scans(days)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/purge_missing_files', methods=['POST'])
def purge_missing_files():
    """
    Delete files marked as missing for longer than the specified days.

    Returns:
        dict: Status dictionary
    """
    # Get request data
    data = request.json
    if not data or 'days' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required parameter: days'
        }), 400

    days = int(data['days'])

    # Purge missing files
    result = db.purge_missing_files(days)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/purge_orphaned_records', methods=['POST'])
def purge_orphaned_records():
    """
    Clean up orphaned records in the database.

    Returns:
        dict: Status dictionary
    """
    # Purge orphaned records
    result = db.purge_orphaned_records()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/integrity_check', methods=['GET'])
def integrity_check():
    """
    Run an integrity check on the database.

    Returns:
        dict: Status dictionary
    """
    # Run integrity check
    result = db.run_integrity_check()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/repair', methods=['POST'])
def repair_database():
    """
    Attempt to repair the database.

    Returns:
        dict: Status dictionary
    """
    # Repair database
    result = db.repair_database()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

# === Backup Endpoints ===

@db_api.route('/backups', methods=['GET'])
def list_backups():
    """
    List all available backups.

    Returns:
        dict: List of backups
    """
    # List backups
    result = db.list_backups()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/backup', methods=['POST'])
def create_backup():
    """
    Create a database backup.

    Returns:
        dict: Status dictionary
    """
    # Get request data
    data = request.json or {}
    name = data.get('name')

    # Create backup
    result = db.create_backup(name)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/backup/settings', methods=['GET'])
def get_backup_settings():
    """
    Get automatic backup settings.

    Returns:
        dict: Backup settings
    """
    # Get settings
    result = db.get_backup_settings()

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/backup/settings', methods=['PUT'])
def set_backup_settings():
    """
    Configure automatic backup settings.

    Returns:
        dict: Status dictionary
    """
    # Get request data
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400

    # Validate input
    required_fields = ['enabled', 'frequency', 'retain_count']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400

    # Update settings
    result = db.set_backup_settings(
        data['enabled'],
        data['frequency'],
        data['retain_count']
    )

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/backup/<backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """
    Restore database from a backup.

    Args:
        backup_id: ID of the backup

    Returns:
        dict: Status dictionary
    """
    # Verify confirmation code
    data = request.json
    if not data or data.get('confirmation') != 'RESTORE':
        return jsonify({
            'success': False,
            'error': 'Invalid confirmation code. Expected "RESTORE".'
        }), 400

    # Check for active scans
    active_scans_result = db.check_for_active_scans()
    if not active_scans_result['success']:
        return jsonify(active_scans_result), 500

    if active_scans_result['active_scan_count'] > 0:
        # Mark active scans as aborted
        db.mark_scans_as_aborted()

    # Restore backup
    result = db.restore_backup(backup_id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@db_api.route('/backup/<backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """
    Delete a backup.

    Args:
        backup_id: ID of the backup

    Returns:
        dict: Status dictionary
    """
    # Delete backup
    result = db.delete_backup(backup_id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

# === Export Endpoints ===

@db_api.route('/export/schema', methods=['GET'])
def export_schema():
    """
    Export the database schema to a SQL file.

    Returns:
        file: Downloaded SQL file
    """
    # Export schema
    result = db.export_schema()

    if result['success']:
        # Return the file for download
        return send_file(
            result['export_path'],
            mimetype='text/plain',
            as_attachment=True,
            download_name=os.path.basename(result['export_path'])
        )
    else:
        return jsonify(result), 500

@db_api.route('/export/all_data', methods=['GET'])
def export_all_data():
    """
    Export all database data to a SQL file.

    Returns:
        file: Downloaded SQL file
    """
    # Export data
    result = db.export_all_data()

    if result['success']:
        # Return the file for download
        return send_file(
            result['export_path'],
            mimetype='text/plain',
            as_attachment=True,
            download_name=os.path.basename(result['export_path'])
        )
    else:
        return jsonify(result), 500

@db_api.route('/export/configuration', methods=['GET'])
def export_configuration():
    """
    Export database configuration to a JSON file.

    Returns:
        file: Downloaded JSON file
    """
    # Export configuration
    result = db.export_configuration()

    if result['success']:
        # Return the file for download
        return send_file(
            result['export_path'],
            mimetype='application/json',
            as_attachment=True,
            download_name=os.path.basename(result['export_path'])
        )
    else:
        return jsonify(result), 500
