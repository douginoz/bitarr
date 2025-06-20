"""
Custom filters for the web templates.
This file contains Jinja2 filter functions that can be used in templates
to format values.
"""
from flask import Blueprint
from datetime import datetime
import re

# Create a blueprint for the filters
filters_bp = Blueprint('filters', __name__)

@filters_bp.app_template_filter('thousands_separator')
def thousands_separator(value):
    """
    Format a number with thousands separators.
    Args:
        value: Number to format
    Returns:
        str: Formatted number with thousands separators
    """
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)

@filters_bp.app_template_filter('format_size')
def format_size(size_bytes):
    """
    Format a size in bytes to a human-readable format.
    Args:
        size_bytes: Size in bytes
    Returns:
        str: Human-readable size (e.g., "1.23 MB")
    """
    try:
        size_bytes = float(size_bytes)
    except (ValueError, TypeError):
        return "0 B"

    if size_bytes == 0:
        return "0 B"

    # Define size units and their scales
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    scale = 1024.0

    # Calculate the appropriate unit
    unit_index = 0
    while size_bytes >= scale and unit_index < len(units) - 1:
        size_bytes /= scale
        unit_index += 1

    # Format with appropriate precision
    if unit_index == 0:  # Bytes
        return f"{int(size_bytes)} {units[unit_index]}"
    else:
        # Use 2 decimal places for KB and higher
        return f"{size_bytes:.2f} {units[unit_index]}"

@filters_bp.app_template_filter('strftime')
def strftime_filter(date_value, format_string='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object or ISO string using strftime with local timezone conversion.
    Args:
        date_value: datetime object or ISO string
        format_string: strftime format string
    Returns:
        str: Formatted date string in local timezone
    """
    if not date_value:
        return ""

    # Handle string datetime values (ISO format)
    if isinstance(date_value, str):
        try:
            # Parse ISO format: "2025-06-13 06:29:14.708942+00:00"
            date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try parsing without timezone - assume UTC
                date_value = datetime.fromisoformat(date_value.split('+')[0].split('Z')[0])
                # If no timezone info, assume it's UTC
                from datetime import timezone
                date_value = date_value.replace(tzinfo=timezone.utc)
            except ValueError:
                return str(date_value)

    # Handle datetime objects - convert UTC to local time
    if isinstance(date_value, datetime):
        # If it has timezone info (likely UTC), convert to local time
        if date_value.tzinfo is not None:
            # Convert UTC to local time using the system's local timezone
            import time
            # Get local timezone offset in seconds
            if time.daylight:
                # Daylight saving time is in effect
                offset_seconds = -time.altzone
            else:
                # Standard time
                offset_seconds = -time.timezone

            # Create local timezone
            from datetime import timezone, timedelta
            local_tz = timezone(timedelta(seconds=offset_seconds))

            # Convert to local timezone
            date_value = date_value.astimezone(local_tz)

        return date_value.strftime(format_string)

    return str(date_value)

@filters_bp.app_template_filter('regex_replace')
def regex_replace(value, pattern, replacement=''):
    """
    Replace text using regular expressions.
    Args:
        value: Input string
        pattern: Regular expression pattern
        replacement: Replacement string
    Returns:
        str: String with replacements made
    """
    if not value:
        return ""

    try:
        return re.sub(pattern, replacement, str(value))
    except re.error:
        return str(value)

@filters_bp.app_template_filter('duration_seconds')
def duration_seconds(start_time, end_time):
    """
    Calculate duration in seconds between two datetime values.
    Args:
        start_time: Start datetime (string or datetime object)
        end_time: End datetime (string or datetime object)
    Returns:
        float: Duration in seconds, or None if calculation fails
    """
    if not start_time or not end_time:
        return None

    try:
        # Parse start time
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = start_time

        # Parse end time
        if isinstance(end_time, str):
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = end_time

        # Calculate duration
        duration = end_dt - start_dt
        return duration.total_seconds()

    except (ValueError, AttributeError):
        return None

def register_filters(app):
    """
    Register all custom filters with the Flask app.
    Args:
        app: Flask application instance
    """
    app.register_blueprint(filters_bp)
