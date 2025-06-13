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

[Continue with rest of roadmap...]
