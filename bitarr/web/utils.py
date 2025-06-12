"""
Utility functions for the web application.
"""
import os
import json
from datetime import datetime, timedelta
from dateutil import parser

def format_size(size_bytes):
    """
    Format size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string
    """
    if size_bytes is None:
        return "Unknown"

    # Convert to integer
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "Unknown"

    # Format
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} EB"

def format_timestamp(timestamp):
    """
    Format timestamp to human-readable format.

    Args:
        timestamp: Timestamp string or datetime object

    Returns:
        str: Formatted timestamp string
    """
    if not timestamp:
        return "Unknown"

    # Convert to datetime if string
    if isinstance(timestamp, str):
        try:
            timestamp = parser.parse(timestamp)
        except ValueError:
            return timestamp

    # Format
    now = datetime.now()
    diff = now - timestamp

    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M")

def parse_schedule_parameters(parameters):
    """
    Parse schedule parameters from JSON.

    Args:
        parameters: JSON string or dict

    Returns:
        dict: Parsed parameters
    """
    if isinstance(parameters, str):
        try:
            return json.loads(parameters)
        except json.JSONDecodeError:
            return {}
    elif isinstance(parameters, dict):
        return parameters
    else:
        return {}

def get_next_run_time(frequency, parameters):
    """
    Calculate the next run time based on frequency and parameters.

    Args:
        frequency: Frequency string (daily, weekly, monthly, quarterly, custom)
        parameters: Parameters dict

    Returns:
        datetime: Next run time
    """
    now = datetime.now()
    params = parse_schedule_parameters(parameters)

    if frequency == 'daily':
        # Get hour and minute
        hour = int(params.get('hour', 0))
        minute = int(params.get('minute', 0))

        # Create next run time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If next run is in the past, add one day
        if next_run <= now:
            next_run += timedelta(days=1)

    elif frequency == 'weekly':
        # Get day of week, hour, and minute
        day_of_week = int(params.get('day_of_week', 0))  # 0 = Monday, 6 = Sunday
        hour = int(params.get('hour', 0))
        minute = int(params.get('minute', 0))

        # Create next run time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Adjust day of week
        current_day_of_week = now.weekday()
        days_to_add = (day_of_week - current_day_of_week) % 7

        # If next run is today but in the past, add a week
        if days_to_add == 0 and next_run <= now:
            days_to_add = 7

        next_run += timedelta(days=days_to_add)

    elif frequency == 'monthly':
        # Get day of month, hour, and minute
        day_of_month = int(params.get('day_of_month', 1))
        hour = int(params.get('hour', 0))
        minute = int(params.get('minute', 0))

        # Create next run time
        next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)

        # If next run is in the past, add one month
        if next_run <= now:
            # Add a month
            if now.month == 12:
                next_run = next_run.replace(year=now.year + 1, month=1)
            else:
                next_run = next_run.replace(month=now.month + 1)

    elif frequency == 'quarterly':
        # Get day of quarter, hour, and minute
        day_of_quarter = int(params.get('day_of_quarter', 1))
        hour = int(params.get('hour', 0))
        minute = int(params.get('minute', 0))

        # Calculate current quarter
        current_quarter = (now.month - 1) // 3 + 1

        # Calculate next quarter start
        next_quarter = current_quarter + 1 if current_quarter < 4 else 1
        next_quarter_year = now.year if next_quarter > current_quarter else now.year + 1
        next_quarter_month = (next_quarter - 1) * 3 + 1

        # Create next run time
        next_run = datetime(year=next_quarter_year, month=next_quarter_month, day=day_of_quarter,
                           hour=hour, minute=minute, second=0, microsecond=0)

    elif frequency == 'custom':
        # Get interval and unit
        interval = int(params.get('interval', 1))
        unit = params.get('unit', 'days')
        hour = int(params.get('hour', 0))
        minute = int(params.get('minute', 0))

        # Create next run time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If next run is in the past, add interval
        if next_run <= now:
            if unit == 'days':
                next_run += timedelta(days=interval)
            elif unit == 'weeks':
                next_run += timedelta(weeks=interval)
            elif unit == 'months':
                # Approximate months as 30 days
                next_run += timedelta(days=30 * interval)
            elif unit == 'years':
                # Approximate years as 365 days
                next_run += timedelta(days=365 * interval)

    else:
        # Default to daily at midnight
        next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    return next_run
