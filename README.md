# Bitarr - File Integrity Monitoring

Bitarr is a web-based application designed to scan file systems for integrity issues by tracking and comparing file checksums over time. The system enables users to detect file corruption, unauthorized modifications, and missing files across multiple storage devices.

## 🚀 Current Status (v0.9.0 - June 2025)

**FULLY WORKING FEATURES:**

✅ **Core Scanning Engine (CLI)**
- Complete file system scanning with multiple checksum algorithms (SHA-256, SHA-512, BLAKE3, xxHash64, MD5, SHA-1, BLAKE2b)
- Multi-threaded scanning for performance
- SQLite database storage and management
- Storage device detection and tracking
- Comprehensive scan summaries and reporting

✅ **Web Interface**
- Modern, responsive web dashboard
- Real-time scan progress with Socket.IO integration
- New scan modal with configurable parameters
- Scan history and detailed results pages
- Interactive file status charts and visualizations
- Database management interface

✅ **Database Operations**
- Database initialization, backup, and maintenance
- Scan history tracking (17+ scans, 44K+ checksums tested)
- File integrity status tracking across multiple scans
- Storage device management

## 🔧 Recently Fixed Issues

**v0.9.0 Milestone Fixes:**
- 🐛 **FIXED**: Socket.IO scan completion redirect (was redirecting to temp URLs)
- 🐛 **FIXED**: Division by zero errors in scan results display
- 🐛 **FIXED**: Infinite Chart.js rendering loop causing browser CPU spikes
- 🐛 **FIXED**: DateTime serialization in Socket.IO events
- 🐛 **FIXED**: Checksum module dependency handling

## 🚧 Work in Progress / Planned Features

**HIGH PRIORITY:**
- 📋 File comparison and diff visualization
- 📅 Scheduled scan automation
- 📊 Advanced reporting and export functionality
- 🔍 File search and filtering improvements

**MEDIUM PRIORITY:**
- 📧 Email notifications for corruption detection
- 🏥 Storage device health monitoring
- 📈 Trend analysis and corruption patterns
- 🔐 User authentication and access control

**LOW PRIORITY:**
- 🌐 Multi-user support
- 📱 Mobile-responsive enhancements
- 🔌 Plugin system for custom checks
- ☁️ Cloud storage integration

## 🏗️ Technical Architecture

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js, Socket.IO
- **Database**: SQLite with configurable backup system
- **Checksums**: Multiple algorithms via xxhash, blake3, and hashlib

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
python -m bitarr core scan /path/to/directory --algorithm sha256 --threads 4
```

**Database management:**
```bash
python -m bitarr db info          # Show database statistics
python -m bitarr db backup        # Create database backup
```

## 🧪 Testing Status

**Environment Tested:**
- Ubuntu Linux with Python 3.11.4
- 17+ production scans completed
- 3,564 files tracked across 2 storage devices
- 44,345+ checksums calculated and stored

**Performance:**
- Multi-threaded scanning operational
- Real-time progress updates via web interface
- Efficient SQLite database operations
- Memory usage optimized for large file sets

## 🤝 Contributing

This project is currently in active development. The core functionality is stable and ready for testing.

**Current Focus Areas:**
1. Enhanced scan result analysis
2. Automated scheduling system
3. Advanced reporting features
4. Performance optimizations

## 📝 License

MIT License - See LICENSE.md for details

## 🐛 Known Issues

- ⚠️ Scheduled scans UI implemented but automation not yet functional
- ⚠️ Export functionality placeholders present but not implemented
- ⚠️ Some edge cases in very large directory scans (>100K files) need optimization

## 📞 Support

For issues, suggestions, or contributions, please use the GitHub issue tracker.
