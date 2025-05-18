# Bitarr - File Integrity Monitoring

Bitarr is a web-based application designed to scan file systems for integrity issues by tracking and comparing file checksums over time. The system enables users to detect file corruption, unauthorized modifications, and missing files across multiple storage devices.

## Features

- File system scanning with configurable checksums
- Change detection and integrity verification
- Tracking of files across multiple storage devices
- Scheduled automatic scanning
- Detailed reporting and visualization
- Database management for scan history

## Development Setup

1. Clone the repository
git clone https://github.com/douginoz/bitarr.git
cd bitarr

2. Set up a virtual environment
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Initialize the database
python -m bitarr.db.init_db

5. Run the development server
python -m bitarr.web.app

## License

[Specify your license here]
