# Bitarr Project File Descriptions

## Core Package (`bitarr/`)

### Main Module
- `bitarr/__init__.py` - Package initialization file (standard Python package marker)
- `bitarr/__main__.py` - CLI entry point for `python -m bitarr` commands, handles argument parsing and command routing

### Core Scanning Engine (`bitarr/core/`)
- `bitarr/core/__init__.py` - Core package initialization
- `bitarr/core/__main__.py` - CLI entry point for core scanning commands
- `bitarr/core/scanner/checksum.py` - Checksum calculation engine supporting multiple algorithms (SHA-256, BLAKE3, xxHash, etc.)
- `bitarr/core/scanner/device_detector.py` - Storage device detection and analysis for Linux/Windows platforms
- `bitarr/core/scanner/file_utils.py` - File system utilities for metadata extraction and directory traversal
- `bitarr/core/scanner/__init__.py` - Scanner package initialization
- `bitarr/core/scanner/scanner.py` - **UPDATED v1.1.0** Main file scanning engine with host relationship support and multi-threaded processing

### Database Layer (`bitarr/db/`)
- `bitarr/db/db_manager.py` - **UPDATED v1.1.0** Database operations manager with CRUD methods for all tables including new host relationships
- `bitarr/db/init_db.py` - **UPDATED v1.1.0** Database initialization with v1.1.0 schema and host auto-detection
- `bitarr/db/__init__.py` - Database package initialization (empty file)
- `bitarr/db/__main__.py` - CLI entry point for database management commands
- `bitarr/db/models.py` - **UPDATED v1.1.0** SQLAlchemy model classes including new ScanHost, BitrotEvent, and DeviceHealthHistory
- `bitarr/db/schema.py` - **UPDATED v1.1.0** Complete database schema with storage-device-centric architecture and host tracking

### Web Interface (`bitarr/web/`)
- `bitarr/web/api.py` - REST API endpoints for web interface communication
- `bitarr/web/app.py` - Flask application factory and configuration
- `bitarr/web/filters.py` - Jinja2 template filters for data formatting
- `bitarr/web/forms.py` - Web form definitions and validation
- `bitarr/web/__init__.py` - Web package initialization
- `bitarr/web/__main__.py` - CLI entry point for web server commands
- `bitarr/web/routes.py` - **NEEDS UPDATE** Web routes and view functions (may not handle v1.1.0 host relationships yet)
- `bitarr/web/socket.py` - WebSocket integration for real-time scan progress updates
- `bitarr/web/utils.py` - Web utility functions and helpers

### Web Assets (`bitarr/web/static/`)
- `bitarr/web/static/css/style.css` - Main stylesheet for web interface
- `bitarr/web/static/js/main.js` - JavaScript for web interface functionality and real-time updates

### Web Templates (`bitarr/web/templates/`)
- `bitarr/web/templates/configuration.html` - Application configuration management page
- `bitarr/web/templates/database_management.html` - Database maintenance and administration interface
- `bitarr/web/templates/index.html` - **NEEDS UPDATE** Main dashboard (may not show v1.1.0 host relationships)
- `bitarr/web/templates/layout.html` - **UPDATED** Base template layout with fixed Socket.IO event handling
- `bitarr/web/templates/layouts/base.html` - Alternative base layout template
- `bitarr/web/templates/scan_details.html` - **UPDATED** Individual scan results page with fixed chart rendering
- `bitarr/web/templates/scan_history.html` - **NEEDS UPDATE** Scan history listing (may not show host relationships)
- `bitarr/web/templates/scheduled_scans.html` - Scheduled scan management interface
- `bitarr/web/templates/storage_health.html` - **NEEDS UPDATE** Storage device health monitoring dashboard

### Utilities (`bitarr/utils/`)
- `bitarr/utils/__init__.py` - Utilities package initialization (empty)

### Testing (`bitarr/tests/`)
- `bitarr/tests/scan_test.py` - Test cases for scanning functionality

### Miscellaneous (`bitarr/`)
- `bitarr/fullcode.txt` - Code consolidation file (purpose unclear, may be temporary)
- `bitarr/Progress_Report.md` - Development progress documentation

## Project Root Files

### Documentation
- `CLAUDE_SESSION_HANDOFF.md` - **NEW** Critical handoff document for Claude session continuity
- `docs/README.md` - Documentation index and versioning strategy
- `docs/v1.1.0/architecture-v1.1.0.md` - **NEW** v1.1.0 storage-device-centric architecture specification
- `docs/v1.1.0/implementation-roadmap-v1.1.0.md` - **NEW** Detailed implementation roadmap for v1.1.0 features
- `docs/v1.1.0/bitarr_session_handoff_v2.md` - Development session handoff documentation
- `docs/v1.1.0/claude_expertise_prompt.md` - Claude expertise context for optimal development output
- `docs/Optimal Storage Health Monitoring analysis.md` - Storage health monitoring design analysis

### Configuration & Setup
- `.gitignore` - Git ignore patterns for Python projects
- `LICENSE.md` - Project license file
- `README.md` - **UPDATED** Project overview with current v1.1.0 status and installation instructions
- `requirements.txt` - Python package dependencies
- `setup.py` - Python package setup and installation configuration

### Database & Migration
- `init_database.py` - **LEGACY** Original database initialization script (superseded by v1.1.0)
- `migrate_to_v1.1.0.py` - **UNUSED** Database migration script (created but not needed due to fresh database approach)

### Testing
- `tests/test_db.py` - Database functionality test cases

### Directories
- `instance/` - Flask instance-specific configuration directory
- `templates/` - Additional template directory (purpose unclear, may be legacy)