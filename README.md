# Bitarr - File Integrity Monitoring

Bitarr is a web-based application designed to scan file systems for integrity issues by tracking and comparing file checksums over time. The system enables users to detect file corruption, unauthorized modifications, and missing files across multiple storage devices.

## 🚀 Current Status (v1.1.1 - June 14, 2025)

**FULLY WORKING FEATURES:**

✅ **Core Scanning Engine (CLI)**
- Complete file system scanning with multiple checksum algorithms (SHA-256, SHA-512, BLAKE3, xxHash64, MD5, SHA-1, BLAKE2b)
- Multi-threaded scanning with thread-safe size calculation
- SQLite database storage and management
- Storage device detection and tracking
- Comprehensive scan summaries with total size reporting

✅ **Web Interface**
- Modern, responsive web dashboard with technical scan details page
- Real-time scan progress with Socket.IO integration
- New scan modal with configurable parameters
- Scan history with proper file counts and total sizes
- Interactive scan results with error categorization
- Database management interface

✅ **Multi-Host Architecture (v1.1.0)**
- Host relationship tracking for distributed environments
- Storage device associations with host information
- Centralized monitoring across multiple machines

✅ **Enhanced Data Display (v1.1.1)**
- Total file size calculation and display
- Proper file count reporting (actual files processed)
- Scan name display in dashboard and history tables
- Error categorization (Permission Denied vs I/O Errors)
- Timezone-aware datetime display
- Optimized table fonts for better space utilization

## 🔧 Recently Fixed Issues

**v1.1.1 Production Release Fixes:**
- 🐛 **FIXED**: Total size calculation now working correctly with thread-safe accumulation
- 🐛 **FIXED**: File count display showing actual processed files instead of 0
- 🐛 **FIXED**: Scan details page with technical layout and proper data display
- 🐛 **FIXED**: Template filters for datetime formatting and timezone conversion
- 🐛 **FIXED**: Database update_scan method to properly save total_size field
- 🐛 **FIXED**: Thread-safe size accumulation during multi-threaded scanning
- 🐛 **FIXED**: Error categorization with prominent display and user guidance
- 🐛 **FIXED**: Dashboard font sizing for better space utilization
- 🐛 **FIXED**: Scan name columns added to Recent Scans and Scan History tables

## 🚧 Work in Progress / Planned Features

**HIGH PRIORITY:**
- 📋 File listing with pagination in scan details
- 📊 Category filtering functionality (click to filter by file status)
- 🔍 Dashboard status integration (show errors properly)
- 📧 Email notifications for corruption detection

**MEDIUM PRIORITY:**
- 🏥 Storage device health monitoring integration
- 📈 Trend analysis and corruption patterns
- 📅 Scheduled scan automation
- 🔐 User authentication and access control

**LOW PRIORITY:**
- 🌐 Multi-user support and client/server architecture
- 📱 Mobile-responsive enhancements
- 🔌 Plugin system for custom checks
- ☁️ Cloud storage integration

## 🏗️ Technical Architecture

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Socket.IO
- **Database**: SQLite with v1.1.0 host relationship schema
- **Checksums**: Multiple algorithms via xxhash, blake3, and hashlib
- **Multi-threading**: Thread-safe file processing and size calculation

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/douginoz/bitarr.git
   cd bitarr
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python -m bitarr db init
   ```

5. **Run web interface**
   ```bash
   python -m bitarr web --host 0.0.0.0 --port 8286
   ```

6. **Access the application**
   - Web Interface: `http://localhost:8286`

### CLI Usage

**Scan a directory:**
```bash
python -m bitarr core scan /path/to/directory --name "My Scan" --algorithm sha256 --threads 4
```

**Database management:**
```bash
python -m bitarr db info          # Show database statistics
python -m bitarr db backup        # Create database backup
```

## 🧪 Testing Status

**Environment Tested:**
- Ubuntu Linux with Python 3.11.4
- 25+ production scans completed with v1.1.1 features
- Multi-host architecture validated
- Total size calculation verified across different file sets
- Error handling tested with permission denied and I/O errors
- Thread-safe operations validated under concurrent load

**Performance:**
- Multi-threaded scanning with thread-safe size tracking
- Real-time progress updates via web interface
- Efficient SQLite database operations with v1.1.0 schema
- Memory usage optimized for large file sets

## 🎯 Use Cases Validated

**Technical User Focus:**
- ✅ Homelab administrators monitoring 2-4 storage devices
- ✅ Data integrity verification with clear technical reporting
- ✅ Hardware failure detection (I/O errors, permission issues)
- ✅ Bitrot detection through checksum comparison
- ✅ Multi-machine file integrity monitoring
- ✅ Real hardware corruption detection (validated with actual drive failures)

## 🤝 Contributing

This project is currently in active development. The core v1.1.1 functionality is stable and ready for production use in homelab environments.

**Current Focus Areas:**
1. File listing implementation with pagination
2. Enhanced error diagnostics and recovery guidance
3. Storage health monitoring integration
4. Email notification system
5. Client/server architecture for distributed scanning

## 📝 License

MIT License - See LICENSE.md for details

## 🐛 Known Issues

- ⚠️ File listing in scan details shows placeholder (implementation in progress)
- ⚠️ Category filtering not yet implemented (UI ready)
- ⚠️ Dashboard may not reflect scan error status correctly in some edge cases
- ⚠️ Some edge cases in very large directory scans (>100K files) need optimization

## 📞 Support

For issues, suggestions, or contributions, please use the GitHub issue tracker.

---
