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

\`\`\`
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
\`\`\`

[Continue with rest of architecture document...]
