# Bitarr Architecture Documentation v1.1.0

## Overview

Bitarr is a **storage-device-centric** file integrity monitoring system designed to detect bitrot (data corruption) across distributed computing environments. The system uses a client-server architecture to enable scanning of locally-attached storage devices while maintaining centralized monitoring and reporting.

## Core Principles

### 1. Storage-Device-Centric Design
- **Primary Focus**: Detect bitrot on physical/logical storage devices
- **Hierarchy**: Machine → Storage Device → Mount Points → Files
- **Rationale**: Bitrot affects the storage medium, not individual files

### 2. Local-First Scanning
- **Performance**: Only scan locally-attached storage for optimal speed
- **Network Storage**: Allow but warn about performance impact
- **Client Distribution**: Deploy lightweight clients on each machine

### 3. Non-Root Operation
- **Accessibility**: Work without administrative privileges when possible
- **Fallback**: Use multiple detection methods, graceful degradation
- **Warnings**: Inform users when elevated permissions would provide more data

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Bitarr Server                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Web Interface │  │   Database      │  │   Client API    │ │
│  │   (Flask/JS)    │  │   (SQLite)      │  │   (REST/WS)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                           │                        │           │
└───────────────────────────┼────────────────────────┼───────────┘
                            │                        │
                    ┌───────▼───────┐        ┌───────▼───────┐
                    │  Scan History │        │ Client Manager│
                    │  Bitrot Events│        │ Communication │
                    │  Device Health│        └───────┬───────┘
                    └───────────────┘                │
                                                     │
        ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
        │                                            │                                            │
┌───────▼───────┐                            ┌───────▼───────┐                            ┌───────▼───────┐
│ Linux Client  │                            │Windows Client │                            │ Future Client │
│ 192.168.1.25  │                            │ 192.168.1.40  │                            │ (NAS/Docker)  │
│    (tiko)     │                            │   (work01)    │                            │               │
├───────────────┤                            ├───────────────┤                            ├───────────────┤
│ Local Storage:│                            │ Local Storage:│                            │ Local Storage:│
│ • NVMe SSD    │                            │ • SATA SSD    │                            │ • ZFS Pool    │
│ • SATA HDD    │                            │ • USB Drive   │                            │ • Network Vol │
│ • USB Flash   │                            │ • DVD-ROM     │                            │               │
├───────────────┤                            ├───────────────┤                            ├───────────────┤
│Network Storage│                            │Network Storage│                            │Network Storage│
│ • NFS Mount   │                            │ • SMB Share   │                            │ • iSCSI LUN   │
│ • SMB Mount   │                            │ • Mapped Drive│                            │               │
│ (⚠️ Slower)   │                            │ (⚠️ Slower)   │                            │               │
└───────────────┘                            └───────────────┘                            └───────────────┘
```

## Database Schema (v1.1.0)

### Core Tables

#### scan_hosts
- Tracks each machine running a Bitarr client
- Stores connection status and client metadata
- Key fields: host_name, host_ip, host_display_name, client_version

#### storage_devices
- Central table for all storage devices across all machines
- Distinguishes local vs network storage
- Tracks device health and performance characteristics
- Key fields: device_type, connection_type, is_local, performance_warning

#### scans
- Individual scan operations, always tied to a specific storage device
- Enhanced with bitrot clustering detection
- Key fields: storage_device_id, bitrot_clusters_detected

#### bitrot_events (NEW)
- Clusters of corruption detected during scans
- Enables pattern analysis and remediation planning
- Key fields: affected_files_count, cluster_analysis, severity

#### device_health_history (NEW)
- Historical tracking of storage device health metrics
- Enables trend analysis and predictive failure detection
- Key fields: health_score, smart_status, predicted_failure_date

## Storage Device Detection Strategy

### Detection Methods (Priority Order)

#### Linux (Non-Root)
1. `/proc/mounts` - filesystem types and mount points
2. `lsblk -f` - block device hierarchy with filesystems
3. `df -T` - mounted filesystem usage
4. `/sys/block/*/` - basic device information
5. `findmnt -D` - detailed mount tree
6. `udevadm info` - device metadata (when available)

**Fallback for Root-Only Data:**
- SMART data: Show "Requires root access for hardware health data"
- Serial numbers: Use available methods, warn if incomplete

#### Windows (Non-Admin)
1. `wmic logicaldisk get` - basic drive information
2. PowerShell `Get-WmiObject Win32_LogicalDisk`
3. `fsutil fsinfo drives` - available drives
4. Registry queries for mount points
5. `vol` command for volume information

**Fallback for Admin-Only Data:**
- Physical disk info: Show "Requires administrator access for hardware details"
- SMART data: Use `wmic diskdrive` where possible

### Storage Type Classification

```
Local Storage (Fast):
├── SSD (SATA/NVMe/M.2)
├── HDD (SATA/IDE/SCSI)
├── USB (Flash/External HDD)
├── Optical (CD/DVD/Blu-ray)
└── eMMC/SD (Embedded/Mobile)

Network Storage (Slow - Warn User):
├── NFS (Network File System)
├── SMB/CIFS (Windows Shares)
├── iSCSI (Network Block Device)
├── AFP (Apple Filing Protocol)
└── Cloud Mounts (S3FS/etc.)
```

## Bitrot Detection & Clustering

### Cluster Analysis Approach

#### File Sector Mapping (Non-Root)
```bash
# Linux: Get file block allocation
filefrag -v /path/to/corrupted/file

# Output analysis:
# Physical blocks: 1048576-1048640 (Cluster 1)
# Physical blocks: 2097152-2097280 (Cluster 2)
```

#### Clustering Algorithm
1. **Collect Corrupted Files**: During scan, gather all files with checksum mismatches
2. **Map Physical Locations**: Use `filefrag` (Linux) or filesystem APIs (Windows)
3. **Group by Proximity**: Files within adjacent sectors = same cluster
4. **Analyze Patterns**:
   - Sequential sectors → Hardware failure likely
   - Random distribution → Filesystem corruption likely
   - Single large files → Individual file corruption

#### Visualization Strategy
```
Device Map Representation:
[████████████████████████████████████████████████████]
 ^     ^                    ^                       ^
 0%   25%                  50%                    100%
      🔴🔴                  🔴
   Cluster 1            Cluster 2

Legend:
█ = Used space
░ = Free space  
🔴 = Bitrot detected
```

## Client-Server Communication

### API Endpoints

#### Client Registration
```
POST /api/client/register
{
  "host_name": "tiko",
  "host_ip": "192.168.1.25", 
  "client_version": "1.1.0",
  "storage_devices": [...],
  "auth_token": "..."
}
```

#### Scan Initiation
```
POST /api/client/scan/start
{
  "client_id": "tiko",
  "storage_device_id": "nvme0n1",
  "scan_path": "/home/moa/Documents",
  "checksum_method": "sha256",
  "scan_id": "temp_12345"
}
```

#### Progress Reporting
```
WebSocket: /api/client/scan/progress
{
  "scan_id": "temp_12345",
  "status": "scanning",
  "files_processed": 1234,
  "current_file": "/path/to/current/file",
  "cpu_usage": 15.2,
  "network_speed": "125 MB/s",  // For network storage
  "estimated_completion": "2024-06-12T15:30:00Z"
}
```

### Network Storage Handling

#### Detection & Warning
- Automatically detect network mounts during client setup
- Display prominent warnings about performance impact
- Show real-time performance metrics during network scans
- Provide abort capability for slow network operations

#### Performance Monitoring
```
Network Scan Metrics:
├── Transfer Speed: 45 MB/s (Expected: 100+ MB/s for local)
├── CPU Usage: 5% (Normal: scanning, 85%: network overhead)  
├── Network Utilization: 89%
├── Estimated Completion: 14 hours (vs 2 hours local)
└── Recommendation: Consider NAS-native client installation
```

## User Interface Design

### Storage-Centric Navigation
```
Dashboard
├── Storage Health Overview
│   ├── Devices by Machine
│   ├── Recent Bitrot Events  
│   └── Health Trends
├── Client Management
│   ├── Add New Client
│   ├── Client Status Grid
│   └── Network Storage Warnings
└── Scan Management
    ├── Initiate Scans (Device Selection)
    ├── Active Scan Monitoring
    └── Historical Scan Results
```

### Bitrot Event Display
```
Bitrot Alert: Samsung SSD 980 PRO on tiko
┌─────────────────────────────────────────────────┐
│ Severity: ⚠️ Moderate (12 files affected)        │
│ Pattern: Sequential sectors (Hardware failure)   │
│ Location: Sectors 1,048,576 - 1,048,640         │
│ Recommended: Backup immediately, monitor device  │
│                                                 │
│ Device Map:                                     │
│ [████████🔴🔴████████████████████████████████]   │
│  0%      25%    50%    75%              100%    │
│                                                 │
│ Affected Files:                                 │
│ • /home/moa/photos/vacation2023.jpg             │
│ • /home/moa/photos/wedding.mp4                  │
│ • /home/moa/documents/thesis_final.pdf          │
│                                                 │
│ [View Details] [Mark Resolved] [Schedule Rescan]│
└─────────────────────────────────────────────────┘
```

## Security Considerations

### Client Authentication
- API key-based authentication between client and server
- Optional TLS encryption for client-server communication
- Client registration workflow with manual approval

### Permission Model
- Clients run with minimal required privileges
- Clear warnings when additional permissions needed
- Graceful degradation of functionality

## Future Enhancements

### Native NAS Support
- Synology/QNAP package development
- Docker containers for containerized NAS systems
- Direct SMART data access on NAS devices

### Advanced Analytics
- Machine learning for bitrot pattern prediction
- Predictive failure analysis based on device health trends
- Automated remediation recommendations

### Enterprise Features
- Multi-tenant support
- LDAP/Active Directory integration
- Advanced reporting and compliance features

## Performance Specifications

### Local Storage Performance
- Target: 500+ MB/s scan speed (NVMe SSD)
- Baseline: 150+ MB/s scan speed (SATA SSD)  
- Minimum: 50+ MB/s scan speed (HDD)

### Network Storage Warnings
- Display warning if speed < 50 MB/s
- Suggest local client installation if speed < 25 MB/s
- Automatic abort recommendation if speed < 10 MB/s

### Resource Usage
- CPU: <20% average during local scans
- Memory: <1GB for client processes
- Network: Minimal overhead for coordination
