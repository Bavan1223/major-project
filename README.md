# Real-Time Ransomware Detection and Prevention System

**BE CSE Major Project** — System Behavior Monitoring and Artificial Intelligence

A controlled academic cybersecurity lab that detects, classifies, and responds to ransomware-like behavior in real time using behavioral monitoring, rule-based detection, machine learning, and a SOC-style dashboard.

## Safety Notice

This is a **controlled academic lab** running on an isolated Ubuntu VM. The system operates in **SAFE_LAB_MODE / DRY_RUN** at all times:

- No real ransomware is used
- No real files are encrypted or destroyed
- No real processes are killed
- No real firewall rules are modified
- No real network isolation occurs
- All containment/prevention is simulated within the controlled test environment

## Architecture

```
SAFE LAB SIMULATOR
       ↓
FILE MONITOR → PROCESS MONITOR → NETWORK MONITOR
       ↓               ↓                ↓
              EVENT LOGGER (events.jsonl)
                       ↓
              DETECTION PIPELINE (1s loop)
                       ↓
              FEATURE EXTRACTION
                       ↓
           ┌───────────┴───────────┐
           │                       │
      RULE ENGINE             ML MODEL
           │                       │
           └───────────┬───────────┘
                       ↓
                  RISK ENGINE
                       ↓
           ┌───────────┴───────────┐
           │                       │
      CANARY CHECK         CORRELATION
           │                       │
           └───────────┬───────────┘
                       ↓
              INCIDENT MANAGER
                       ↓
           ┌───────────┴───────────┐
           │           │           │
      RESPONSE    PREVENTION   RECOVERY
     CONTROLLER    ENGINE      ENGINE
           │           │           │
           └───────────┬───────────┘
                       ↓
                  AUDIT LOG
                       ↓
               FLASK API (5000)
                       ↓
            REACT SOC DASHBOARD (3000)
```

## Requirements

- Ubuntu Linux (VMware recommended)
- Python 3.11+
- Node.js 18+
- psutil, flask, flask-cors, scikit-learn, pandas, numpy, watchdog

## Installation

```bash
cd ~/ransomware-lab
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors psutil scikit-learn pandas numpy watchdog
cd frontend && npm install && cd ..
```

## Startup

### Backend API
```bash
source .venv/bin/activate
python3 dashboard.py
# API at http://127.0.0.1:5000
```

### Frontend Dashboard
```bash
cd frontend && npm run dev
# Dashboard at http://127.0.0.1:3000
```

### Monitors
```bash
python3 monitor/file_monitor.py       # File monitor (inotify)
python3 monitor/process_monitor.py    # Process monitor (psutil)
python3 monitor/network_monitor.py    # Network monitor (sockets)
```

### Detection Pipeline
```bash
python3 detection_pipeline.py
# Live behavioral risk assessment every 1 second
```

### Safe Simulation
```bash
python3 simulator/safe_simulator.py
# Modifies 30 test files → triggers CRITICAL detection
```

### Run Tests
```bash
python3 tests/test_system.py
# 21 automated tests covering all subsystems
```

## Detection Logic

### Risk Levels
| Level | Condition |
|-------|-----------|
| NORMAL | No suspicious behavior |
| LOW | Minor file activity |
| MEDIUM | Elevated activity or ML-only detection |
| HIGH | Rule-based rapid mass file modification OR canary triggered |
| CRITICAL | Rule HIGH + ML confident agreement |

### ML Policy
- ML is **advisory only**, never the sole authority
- ML alone caps at HIGH (escalates MEDIUM → HIGH)
- ML alone **never** reaches CRITICAL
- CRITICAL requires: `rapid_mass_file_modification` (rule) + ML confirmation
- ML threshold: 0.7

### Detection Signals
- `rapid_mass_file_modification` — 10+ unique files modified rapidly
- `multiple_unique_files_modified` — 10+ distinct file paths
- `ml_ransomware_confirmed` — ML confirms ransomware-like pattern
- `canary_file_triggered` — Protected decoy file was modified/deleted

### False-Positive Protection
- Normal file editing (3 files): LOW — not CRITICAL
- Browser traffic (50 connections): NORMAL
- Git operations (4 files): LOW
- Package installation (8 files): HIGH maximum (ML advisory, not CRITICAL)
- CRITICAL is unreachable without `rapid_mass_file_modification`

## Incident Lifecycle

```
OPEN → INVESTIGATING → CONTAINED → RESOLVED → CLOSED
```

Features:
- Unique incident IDs (INC-XXXXXXXX)
- Deduplication (one continuous episode = one incident)
- Auto-resolve on NORMAL recovery
- Stale timeout (60s without update = auto-resolve)
- Timeline tracking for all state transitions
- Persistence to disk (survives restart)

## Canary/Honeypot System

5 defensive decoy files deployed in `canary-files/`:
- `canary_trap_passwords_backup.txt`
- `canary_trap_financial_records.xlsx`
- `canary_trap_private_keys.pem`
- `canary_trap_database_export.sql`
- `canary_trap_important_documents.docx`

SHA-256 hash integrity monitoring. Any modification = HIGH-confidence signal.

## Prevention & Containment (DRY_RUN)

| Action | Description | Mode |
|--------|-------------|------|
| Protect Lab Files | Backup test-files/ to recovery/snapshots/ | REAL |
| Process Isolation | Record isolation (no actual kill) | SIMULATED |
| Network Isolation | Record recommendation (no firewall) | SIMULATED |
| Recovery Snapshot | Real file copy within lab | REAL |
| Restore Lab Files | Restore from snapshot + hash verify | REAL |
| Containment | Orchestrates protect + isolate | DRY_RUN |

## Recovery

- Real `shutil.copytree` snapshots of test-files/
- Restore from latest snapshot
- SHA-256 hash verification of restored content
- Incident auto-resolves on successful recovery

## API Endpoints

### Status & Telemetry
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System state, risk, active incident |
| `/api/events` | GET | Event stream with counts |
| `/api/risk` | GET | Current behavioral risk + ML |
| `/api/network` | GET | Network connections |
| `/api/processes` | GET | Process activity |
| `/api/files` | GET | File activity |
| `/api/health` | GET | Real system health (CPU, mem, disk) |
| `/api/canary` | GET | Canary/honeypot status |
| `/api/correlation` | GET | Process-network correlations |
| `/api/audit` | GET | Audit trail |

### Incidents
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/incidents` | GET | All incidents |
| `/api/incidents/<id>` | GET | Incident detail |
| `/api/incidents/<id>/acknowledge` | POST | → INVESTIGATING |
| `/api/incidents/<id>/contain` | POST | → CONTAINED |
| `/api/incidents/<id>/resolve` | POST | → RESOLVED |
| `/api/incidents/<id>/close` | POST | → CLOSED |

### Prevention & Recovery
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prevention/protect` | POST | Protect lab files |
| `/api/prevention/isolate-process` | POST | Simulate process isolation |
| `/api/prevention/isolate-network` | POST | Simulate network isolation |
| `/api/recovery/snapshot` | POST | Create recovery snapshot |
| `/api/recovery/restore` | POST | Restore from snapshot |
| `/api/simulation/run` | POST | Run safe simulator |
| `/api/canary/reset` | POST | Redeploy canary files |

## Dashboard Pages

| Page | Description |
|------|-------------|
| Overview | Risk status, engine status, telemetry counters |
| Live Events | Real-time event stream with severity filters |
| File Activity | File operations, honeypot status |
| Network Activity | Connections, repeated endpoints |
| Process Activity | Process telemetry, inspector |
| Detection & Risk | Signals, ML confidence, incident state |
| Response | Containment controls, recovery actions |
| Prevention | Full prevention center, incident lifecycle, audit |
| System Health | Real component status, CPU/memory/disk metrics |

## End-to-End Demo Workflow

1. Start all monitors + backend + frontend + detection pipeline
2. Dashboard shows NORMAL state
3. Run `python3 simulator/safe_simulator.py`
4. File monitor detects 30 rapid modifications
5. Rule engine triggers: `rapid_mass_file_modification`
6. ML confirms: RANSOMWARE_LIKE (probability ~0.99)
7. Risk escalates to CRITICAL
8. Incident auto-created (INC-XXXXXXXX)
9. Use Prevention page: Acknowledge → Contain → Snapshot → Restore → Resolve → Close
10. System returns to NORMAL
11. Audit log shows complete timeline
12. Recovery verified with SHA-256 hash matching

## Project Structure

```
ransomware-lab/
├── core/
│   ├── config.py              # Unified configuration
│   ├── canary_manager.py      # Honeypot/canary system
│   ├── incident_manager.py    # Incident lifecycle
│   ├── prevention_engine.py   # Containment, recovery, audit
│   ├── risk_engine.py         # Rule + ML risk scoring
│   ├── response_controller.py # Response recommendations
│   ├── protection_controller.py # Protection decisions
│   ├── feature_extractor.py   # Behavioral features
│   ├── correlation_engine.py  # Process/network/file correlation
│   ├── audit_attributor.py    # Auditd-based attribution
│   ├── event_collector.py     # In-memory event buffer
│   └── event_schema.py        # Common Event validation
├── monitor/
│   ├── file_monitor.py        # inotify file watcher
│   ├── process_monitor.py     # psutil process scanner
│   └── network_monitor.py     # Network connection monitor
├── ml/
│   ├── inference/             # ML prediction (Random Forest)
│   ├── training/              # Model training pipeline
│   ├── models/                # Trained model artifacts
│   └── data/                  # Training datasets
├── simulator/
│   └── safe_simulator.py      # Safe ransomware behavior simulation
├── tests/
│   └── test_system.py         # Automated test suite (21 tests)
├── frontend/src/              # React + Vite SOC dashboard
├── logs/                      # Runtime event/incident logs
├── test-files/                # Controlled lab test directory
├── canary-files/              # Deployed canary/honeypot files
├── recovery/                  # Recovery snapshots
├── dashboard.py               # Flask API backend
├── detection_pipeline.py      # Live detection loop
├── detection_engine.py        # Threshold detection
├── event_logger.py            # Event creation & persistence
└── main.py                    # Entry point (runs tests)
```

## Testing

```bash
python3 tests/test_system.py    # 21 automated tests
python3 main.py                 # Same (runs test suite)
```

Test coverage:
- Risk engine levels (5 tests)
- ML integration (3 tests)
- Incident lifecycle (4 tests)
- Canary system (2 tests)
- Feature extraction (1 test)
- Recovery with hash verification (1 test)
- API state consistency (3 tests)
- False-positive resistance (2 tests)

## Architectural Decisions

1. **Incident Manager is the source of truth** for current risk. Historical events are history, not current state.
2. **Stale incident timeout** (60s) auto-resolves incidents when the pipeline stops.
3. **Orphan incident prevention** — `clear_active()` auto-resolves rather than leaving OPEN.
4. **DRY_RUN everywhere** — No destructive enforcement without explicit configuration.
5. **ML is advisory** — Never escalates beyond HIGH alone. CRITICAL requires rule confirmation.
6. **Real telemetry only** — No fabricated evidence, no fake forensic data.
7. **Honest attribution** — Reports "unavailable" when process attribution cannot be determined.
8. **Consistent timestamps** — Local time throughout to avoid timezone bugs.

## Known Limitations

| Limitation | Status | Notes |
|-----------|--------|-------|
| Process attribution for file events | LIMITED | inotify doesn't provide PID; auditd required |
| Network containment | SIMULATED | DRY_RUN only, no real firewall rules |
| Process containment | SIMULATED | DRY_RUN only, no actual kill |
| ML model training data | OFFLINE | Model trained on behavioral dataset, not live Ubuntu data |
| Canary monitoring | POLLING | Checked each pipeline cycle, not real-time inotify |

## Technology Stack

- **Backend**: Python 3.12, Flask, psutil, watchdog
- **ML**: scikit-learn Random Forest classifier
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide icons
- **Monitoring**: inotify (files), psutil (processes), socket (network)
- **Storage**: JSONL event log, JSON incident/audit persistence
- **Safety**: DRY_RUN default, SAFE_LAB_MODE, path validation
