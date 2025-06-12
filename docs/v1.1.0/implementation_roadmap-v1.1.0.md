# Bitarr v1.1.0 Implementation Roadmap

## Phase 1: Storage-Device-Centric Foundation (Week 1)

### 1.1 Database Schema Migration
**Files to Modify:**
- `bitarr/db/schema.py` - Add new tables
- `bitarr/db/models.py` - New SQLAlchemy models
- `bitarr/db/migrations/` - Migration scripts

**Tasks:**
- [ ] Add `scan_hosts` table
- [ ] Enhance `storage_devices` table with host relationship
- [ ] Add `bitrot_events` table for clustering
- [ ] Add `device_health_history` table
- [ ] Create migration script for existing data
- [ ] Update existing scans to include host information

### 1.2 Enhanced Device Detection
**New Files:**
- `bitarr/core/device/device_detector_v2.py` - Enhanced detection
- `bitarr/core/device/linux_detector.py` - Linux-specific methods
- `bitarr/core/device/windows_detector.py` - Windows-specific methods
- `bitarr/core/device/sector_mapper.py` - File sector analysis

**Detection Methods:**
- [ ] Linux: `/proc/mounts`, `lsblk`, `findmnt`, `filefrag`
- [ ] Windows: WMI queries, PowerShell cmdlets, `fsutil`
- [ ] Network storage identification and warnings
- [ ] Permission-aware detection with fallbacks
- [ ] Device type classification (SSD/HDD/USB/Network)

### 1.3 UI Updates for Storage-Centric View
**Files to Modify:**
- `bitarr/web/templates/index.html` - Storage-focused dashboard
- `bitarr/web/templates/storage_health.html` - Enhanced device view
- `bitarr/web/routes.py` - New storage-centric endpoints

**UI Changes:**
- [ ] Dashboard: Group by Machine → Storage Device
- [ ] Add host display names ("192.168.1.25 (tiko)")
- [ ] Storage device health indicators
- [ ] Network storage warnings in UI

## Phase 2: Bitrot Clustering & Analysis (Week 2)

### 2.1 Sector Mapping Implementation
**New Files:**
- `bitarr/core/bitrot/cluster_analyzer.py` - Clustering algorithm
- `bitarr/core/bitrot/sector_mapper.py` - File-to-sector mapping
- `bitarr/core/bitrot/visualization.py` - Visual representation data

**Features:**
- [ ] File sector location detection (Linux `filefrag`, Windows APIs)
- [ ] Clustering algorithm for adjacent corrupted files
- [ ] Pattern analysis (sequential vs random corruption)
- [ ] Device map visualization data generation

### 2.2 Bitrot Event Management
**Files to Modify:**
- `bitarr/core/scanner/scanner.py` - Integrate clustering
- `bitarr/web/routes.py` - Bitrot event endpoints
- `bitarr/db/db_manager.py` - Bitrot event CRUD

**New Templates:**
- `bitarr/web/templates/bitrot_events.html` - Event dashboard
- `bitarr/web/templates/device_map.html` - Visual device map

**Features:**
- [ ] Automatic bitrot event creation during scans
- [ ] Severity assessment (minor/moderate/severe)
- [ ] Recommended actions based on patterns
- [ ] User acknowledgment and resolution tracking

### 2.3 Device Health Monitoring
**Features:**
- [ ] SMART data collection (when available)
- [ ] Health trend tracking
- [ ] Predictive failure warnings
- [ ] Health score calculation

## Phase 3: Client-Server Architecture (Week 3-4)

### 3.1 Client Management Infrastructure
**New Files:**
- `bitarr/client/` - Lightweight client package
- `bitarr/client/client_daemon.py` - Main client process
- `bitarr/client/api_client.py` - Server communication
- `bitarr/client/local_scanner.py` - Client-side scanning

**Server Enhancements:**
- `bitarr/web/api/client_api.py` - Client management endpoints
- `bitarr/web/socket_client.py` - WebSocket for client communication

### 3.2 Client Management UI
**New Templates:**
- `bitarr/web/templates/client_management.html` - Client dashboard
- `bitarr/web/templates/add_client.html` - Client registration
- `bitarr/web/templates/client_details.html` - Individual client view

**Features:**
- [ ] Client registration and authentication
- [ ] Connection status monitoring
- [ ] Remote filesystem browsing
- [ ] Client performance monitoring
- [ ] Network storage detection and warnings

### 3.3 Distributed Scanning
**Features:**
- [ ] Remote scan initiation
- [ ] Real-time progress reporting
- [ ] Client resource monitoring (CPU, network speed)
- [ ] Scan abort capability
- [ ] Performance warning thresholds

## Phase 4: Advanced Features (Week 5-6)

### 4.1 Enhanced Network Storage Handling
**Features:**
- [ ] Dynamic performance monitoring during network scans
- [ ] Automatic speed detection and warnings
- [ ] User-configurable performance thresholds
- [ ] Intelligent scan scheduling for network storage

### 4.2 Advanced Visualization
**New Templates:**
- `bitarr/web/templates/device_visualization.html` - Interactive device maps
- `bitarr/web/templates/bitrot_trends.html` - Trend analysis

**Features:**
- [ ] Interactive device sector maps
- [ ] Bitrot pattern visualization
- [ ] Health trend charts
- [ ] Comparative analysis across devices

### 4.3 Automated Recommendations
**Features:**
- [ ] Intelligent remediation suggestions
- [ ] Backup urgency recommendations
- [ ] Device replacement predictions
- [ ] Scan frequency optimization

## Testing & Validation

### Test Environments
- [ ] Linux (Ubuntu, CentOS, Debian)
- [ ] Windows (10, 11, Server)
- [ ] Mixed storage types (SSD, HDD, USB, Network)
- [ ] Permission scenarios (root/non-root, admin/user)

### Performance Benchmarks
- [ ] Local storage scan speeds
- [ ] Network storage performance detection
- [ ] Client-server communication latency
- [ ] Resource usage under load

### Edge Cases
- [ ] Offline clients
- [ ] Network interruptions
- [ ] Permission changes mid-scan
- [ ] Device disconnection during scan

## Deployment Strategy

### v1.1.0-alpha
- Phase 1 complete: Storage-centric foundation
- Limited testing environment

### v1.1.0-beta  
- Phases 1-2 complete: Include bitrot clustering
- Extended testing across platforms

### v1.1.0-rc
- Phases 1-3 complete: Full client-server architecture
- Production readiness testing

### v1.1.0-stable
- All phases complete
- Comprehensive documentation
- Migration guides from v1.0.0

## Documentation Updates

### Technical Documentation
- [ ] API documentation for client-server communication
- [ ] Database schema migration guide
- [ ] Client installation instructions
- [ ] Network storage configuration guide

### User Documentation
- [ ] Updated user manual with storage-centric concepts
- [ ] Bitrot remediation guide
- [ ] Client management tutorial
- [ ] Performance optimization guide

## Backward Compatibility

### v1.0.0 Compatibility
- [ ] Automatic migration of existing scan data
- [ ] Host information backfill for existing scans
- [ ] Legacy API endpoint support (deprecated)
- [ ] Configuration migration utility

### Migration Path
1. Backup existing database
2. Run schema migration
3. Update client installations
4. Verify data integrity
5. Test core functionality
6. Enable new features gradually

## Success Metrics

### Functional Requirements
- [ ] All existing v1.0.0 functionality preserved
- [ ] Storage device detection accuracy >95%
- [ ] Bitrot clustering detection operational
- [ ] Client-server communication stable
- [ ] Network storage warnings functional

### Performance Requirements
- [ ] Local scan speeds maintain v1.0.0 performance
- [ ] Client-server overhead <5% performance impact
- [ ] UI response times <500ms for device operations
- [ ] Memory usage <1GB per client process

### User Experience
- [ ] Intuitive storage-centric navigation
- [ ] Clear bitrot event presentation
- [ ] Effective network storage warnings
- [ ] Simplified client management workflow
