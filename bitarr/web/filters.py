"""
Custom filters for the web templates.

This file contains Jinja2 filter functions that can be used in templates
to format values.
"""
from flask import Blueprint

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

def register_filters(app):
    """
    Register all custom filters with the Flask app.

    Args:
        app: Flask application instance
    """
    app.register_blueprint(filters_bp)
