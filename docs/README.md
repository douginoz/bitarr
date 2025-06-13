# Bitarr Documentation Index

## Current Version: v1.1.0 (In Development)
- [Architecture v1.1.0](v1.1.0/architecture-v1.1.0.md) - Storage-device-centric distributed design
- [Implementation Roadmap v1.1.0](v1.1.0/implementation-roadmap-v1.1.0.md) - Phase-by-phase development plan

## Previous Versions
- **v1.0.0**: Initial stable release (single-machine architecture)
  - Architecture documented in git history and README.md
  - Features: CLI scanning, web interface, basic storage device detection

## Documentation Versioning Strategy

### Version Types
- **Major versions** (v1.x.0): Significant architectural changes, breaking changes
- **Minor versions** (v1.1.x): Feature additions, API extensions, backward-compatible changes  
- **Patch versions** (v1.1.1): Bug fixes, documentation clarifications, performance improvements

### When to Create New Version Docs
- ✅ **New major/minor version**: Architectural changes, new features
- ✅ **Update existing version**: Clarifications, implementation details
- ✅ **Cross-reference**: Link related concepts between versions

### Documentation Maintenance
1. Copy current version docs to new version directory
2. Update version references and dates in new documents
3. Update this index with new version
4. Commit changes with descriptive message
5. Tag releases when stable

## Architecture Evolution

### v1.0.0 → v1.1.0 Key Changes
- **Single-machine** → **Distributed client-server architecture**
- **File-centric** → **Storage-device-centric design**
- **Basic device detection** → **Comprehensive non-root device analysis**
- **Simple corruption detection** → **Bitrot clustering and pattern analysis**
- **Local scanning only** → **Remote client scanning with performance monitoring**

### Future Roadmap
- **v1.2.0**: Scheduled scanning automation, advanced reporting
- **v1.3.0**: Native NAS support, enterprise features
- **v2.0.0**: Multi-tenant support, cloud integration
