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
      RESPONSE              PROTECTION
     CONTROLLER             CONTROLLER
           │                       │
           └───────────┬───────────┘
                       ↓
              INCIDENT MANAGER
                       ↓
              PREVENTION ENGINE
                       ↓
               FLASK API (5000)
                       ↓
            REACT SOC DASHBOARD (3000)
```

## Requirements

- Ubuntu Linux (VMware)
- Python 3.11+
- Node.js 18+
- Virtual environment with dependencies

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
cd ~/ransomware-lab
source .venv/bin/activate
python3 dashboard.py
# API at http://127.0.0.1:5000
```

### Frontend Dashboard
```bash
cd ~/ransomware-lab/frontend
npm run dev
# Dashboard at http://127.0.0.1:3000
```

### Monitors
```bash
# Terminal 1: File Monitor
python3 monitor/file_monitor.py

# Terminal 2: Process Monitor
python3 monitor/process_monitor.py

# Terminal 3: Network Monitor
python3 monitor/network_monitor.py
```

### Detection Pipeline
```bash
python3 detection_pipeline.py
# Live behavioral risk assessment every 1 second
```

### Safe Simulation
```bash
python3 simulator/safe_simulator.py
# Creates/modifies 30 test files in test-files/
# Triggers CRITICAL detection when pipeline is running
```

## Detection Logic

### Risk Levels
| Level | Condition |
|-------|-----------|
| NORMAL | No suspicious behavior |
| LOW | Minor file activity |
| MEDIUM | Elevated activity or ML-only detection |
| HIGH | Rule-based rapid mass file modification |
| CRITICAL | Rule HIGH + ML confident agreement |

### ML Policy
- ML is **advisory only**, never authoritative
- ML alone caps at MEDIUM (never CRITICAL alone)
- ML threshold: 0.7
- Rule HIGH + ML confident ransomware = CRITICAL
- ML unavailable = rule-only (graceful degradation)

### Detection Signals
- `rapid_mass_file_modification` — 10+ unique files modified rapidly
- `multiple_unique_files_modified` — 10+ distinct file paths
- `ml_ransomware_confirmed` — ML model confirms with high confidence

## Incident Lifecycle

```
OPEN → INVESTIGATING → CONTAINED → RESOLVED → CLOSED
```

Each incident tracks:
- Risk level, reason, signals
- ML probability and contribution
- File/process/network evidence
- Timeline of all actions
- Containment and recovery status

## Prevention & Containment (DRY_RUN)

All prevention operates safely within the lab:

| Action | Description |
|--------|-------------|
| Protect Lab Files | Backup test-files/ to recovery/snapshots/ |
| Process Isolation | Record isolation (no actual kill) |
| Network Isolation | Record recommendation (no firewall change) |
| Recovery Snapshot | Real file copy within lab directory |
| Restore Lab Files | Restore from latest snapshot |

## API Endpoints

### Status & Telemetry
- `GET /api/status` — System state, risk level, incident info
- `GET /api/events` — Event stream with counts
- `GET /api/risk` — Current behavioral risk assessment
- `GET /api/network` — Network connections
- `GET /api/processes` — Process activity
- `GET /api/files` — File activity
- `GET /api/health` — Real system health (CPU, memory, component status)

### Incidents
- `GET /api/incidents` — All incidents
- `GET /api/incidents/<id>` — Incident detail
- `POST /api/incidents/<id>/acknowledge` — Transition to INVESTIGATING
- `POST /api/incidents/<id>/contain` — Trigger safe containment
- `POST /api/incidents/<id>/resolve` — Mark resolved
- `POST /api/incidents/<id>/close` — Close incident

### Prevention & Recovery
- `POST /api/prevention/protect` — Protect lab files
- `POST /api/prevention/isolate-process` — Simulate process isolation
- `POST /api/prevention/isolate-network` — Simulate network isolation
- `POST /api/recovery/snapshot` — Create recovery snapshot
- `POST /api/recovery/restore` — Restore from snapshot
- `POST /api/simulation/run` — Run safe simulator

### Audit
- `GET /api/audit` — Complete audit trail

## Dashboard Pages

| Page | Description |
|------|-------------|
| Overview | Risk status, engine status, telemetry counters |
| Live Events | Real-time event stream with filters |
| File Activity | File operations, honeypot status |
| Network Activity | Connections, repeated endpoints |
| Process Activity | Process telemetry, inspector |
| Detection & Risk | Signals, ML confidence, incident state |
| Response | Containment controls, recovery actions |
| Prevention | Full prevention center, incident lifecycle, audit log |
| System Health | Real component status, host metrics |

## Demo Workflow

1. Start all monitors + backend + frontend + detection pipeline
2. Dashboard shows NORMAL state
3. Run `python3 simulator/safe_simulator.py`
4. File monitor detects rapid modifications
5. Rule engine triggers HIGH (rapid_mass_file_modification)
6. ML confirms ransomware-like pattern (probability ~0.99)
7. Risk escalates to CRITICAL
8. Incident created automatically
9. Dashboard shows CRITICAL with real signals
10. Use Prevention page: Acknowledge → Contain → Snapshot → Restore → Resolve → Close
11. System recovers to NORMAL
12. Audit log shows complete timeline

## Project Structure

```
ransomware-lab/
├── core/
│   ├── incident_manager.py    # Incident lifecycle management
│   ├── prevention_engine.py   # Safe containment, recovery, audit
│   ├── risk_engine.py         # Rule + ML risk scoring
│   ├── response_controller.py # Response recommendations
│   ├── protection_controller.py # Protection decisions
│   ├── feature_extractor.py   # Behavioral feature extraction
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
├── frontend/
│   └── src/                   # React + Vite SOC dashboard
├── logs/
│   └── events.jsonl           # Central telemetry log
├── test-files/                # Controlled lab test directory
├── recovery/                  # Recovery snapshots
├── dashboard.py               # Flask API backend
├── detection_pipeline.py      # Live detection loop
├── detection_engine.py        # Threshold detection
└── event_logger.py            # Event creation & persistence
```

## Testing

```bash
# Syntax validation
python3 -m py_compile detection_pipeline.py
python3 -m py_compile dashboard.py
python3 -m py_compile core/incident_manager.py
python3 -m py_compile core/prevention_engine.py

# Frontend build
cd frontend && npx vite build

# End-to-end: Run simulator then check detection pipeline output
python3 simulator/safe_simulator.py
# Expected: CRITICAL detection with ML probability ~0.99
```

## Key Design Decisions

1. **DRY_RUN everywhere** — No destructive actions in the lab
2. **Incident deduplication** — Same behavioral state = one incident, not repeated events
3. **ML is advisory** — Never escalates beyond MEDIUM alone
4. **Real telemetry only** — No fabricated evidence or fake forensic data
5. **Safe simulation** — Modifies plain text files, no encryption
6. **Timestamp consistency** — Local time throughout to avoid timezone bugs

## Technology Stack

- **Backend**: Python 3.11, Flask, psutil, watchdog
- **ML**: scikit-learn Random Forest classifier
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide icons
- **Monitoring**: inotify (files), psutil (processes), socket (network)
- **Storage**: JSONL event log, JSON incident persistence
