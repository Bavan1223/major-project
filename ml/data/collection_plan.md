# Data Collection Plan — ML Module v0.1

**Document Version:** 0.1  
**Feature Version:** 1.0  
**Date:** 2026-08-20  
**Status:** IN PROGRESS  
**Milestone:** M2.1  

---

## 1. Objective and Scope

### 1.1 What This Dataset Represents

This dataset captures **behavioral telemetry** from a controlled Ubuntu lab environment, aggregated into 10-second observation windows. Each observation window produces a feature vector describing system activity (file operations, process activity, network connections) during that window.

### 1.2 What the Labels Mean

| Label | Value | Meaning |
|-------|-------|---------|
| NORMAL | 0 | The observation window was generated during a **controlled normal activity scenario**. The system was performing legitimate operations (editing, browsing, building, etc.) |
| RANSOMWARE_LIKE | 1 | The observation window was generated during a **controlled ransomware-like behavioral simulation**. The system was executing safe, non-destructive operations that mimic ransomware behavioral patterns (rapid file modification, bulk renaming, etc.) |

### 1.3 What the Model Should Learn

The model should learn to distinguish **behavioral patterns associated with ransomware-like activity** from **legitimate system behavior** based on the combination and intensity of file, process, and network features within a 10-second window.

The model is NOT learning to:
- Identify specific malware families
- Detect specific file signatures
- Analyze file content or entropy
- Replace the rule-based detection engine

### 1.4 Important Terminology

- **RANSOMWARE_LIKE** — NOT real ransomware. Safe controlled simulation that mimics behavioral patterns.
- **Label source** — The experimental condition (what scenario we deliberately ran), NOT the rule engine output.
- **Observation** — One 10-second feature vector.
- **Session** — One complete controlled experiment run (may produce multiple observations).

---

## 2. Terminology Definitions

| Term | Definition |
|------|------------|
| **Session** | One complete controlled experiment run. Has a unique ID, a defined scenario, and a known label. |
| **Window** | A 10-second observation period within a session. Features are aggregated over this period. |
| **Scenario** | A defined behavioral pattern to execute (e.g., "edit 3 files slowly" or "modify 20 files rapidly"). |
| **Feature vector** | The 10 integer values extracted from one window, matching the ML feature contract v1.0. |
| **Label** | The ground truth class (0 or 1) assigned from the experimental design, not from model output or rules. |
| **Common Event** | The standardized event format produced by all monitors in the existing project. |

---

## 3. Observation Window Specification

### 3.1 Window Duration

```
WINDOW_SECONDS = 10
```

This matches the existing rule-based detection window (10 unique files modified in 10 seconds → HIGH risk), enabling direct comparison between rule-based and ML-based detection.

### 3.2 Window Boundaries

- **Start:** Aligned to session start time.
- **Boundaries:** Non-overlapping, adjacent.
  - Window 1: `[session_start, session_start + 10s)`
  - Window 2: `[session_start + 10s, session_start + 20s)`
  - Window N: `[session_start + (N-1)*10s, session_start + N*10s)`
- **Inclusive start, exclusive end:** An event at exactly `session_start + 10.000s` belongs to Window 2, not Window 1.

### 3.3 Event Assignment Rule

An event with timestamp `T` belongs to Window `W` if:

```
window_start <= T < window_end
```

Where:
```
window_start = session_start + (W - 1) * WINDOW_SECONDS
window_end   = session_start + W * WINDOW_SECONDS
```

### 3.4 Partial Windows

If a session ends before a window completes (remaining time < 10 seconds), that partial window is **DISCARDED**. Reason: Features aggregated over a shorter period are not comparable to full 10-second windows without rate normalization, which is not in the v1.0 feature set.

### 3.5 Minimum Session Duration

Every scenario must run for at least 10 seconds to guarantee at least 1 valid window.

### 3.6 No Overlapping Windows

Windows do NOT overlap. Overlapping windows would create highly correlated samples that inflate dataset size without adding independent information, and would complicate session-based splitting.

### 3.7 Future Work

Experimentation with 5-second, 30-second, and 60-second windows is deferred until the primary 10-second model is operational.

---

## 4. Session Schema

Each session is recorded with the following metadata:

```json
{
    "session_id": "S_0001",
    "scenario_id": "N1",
    "scenario_type": "NORMAL",
    "label": 0,
    "start_time": "2026-08-21T14:30:00.000Z",
    "end_time": "2026-08-21T14:30:35.000Z",
    "duration_seconds": 35,
    "window_count": 3,
    "environment": "ubuntu_lab",
    "parameters": {
        "file_count": 5,
        "delay_ms": 200,
        "operation_types": ["modify"],
        "target_directory": "~/ransomware-lab/test-files/"
    },
    "notes": ""
}
```

### 4.1 Session ID Format

```
S_NNNN
```

Sequential, zero-padded 4-digit number. Example: `S_0001`, `S_0042`.

### 4.2 Label Assignment Rule

**The label is determined by the scenario definition BEFORE execution.**

It is assigned based on WHAT WE INTENTIONALLY RAN, not based on:
- Rule engine output
- `suspicious_indicators` value
- ML model prediction
- Observed feature values
- Post-hoc analysis

This is the fundamental requirement for avoiding circular reasoning in the dataset.

---

## 5. Normal Scenario Catalog

### Design Principle

Normal scenarios must include varied activity levels, including HIGH legitimate activity. The model must learn that elevated feature values do not automatically indicate ransomware-like behavior.

---

### N1 — Idle System

| Field | Value |
|-------|-------|
| Description | No user activity. System at rest. |
| Operations | None |
| Expected duration | 15-20s |
| Expected windows | 1-2 |
| Parameter variation | None needed |
| Expected feature profile | All features at 0 or near 0 |
| Purpose | Establish the minimum baseline |

---

### N2 — Light File Editing

| Field | Value |
|-------|-------|
| Description | User edits 1-3 text files with natural pauses between edits |
| Operations | file_modified (1-3 files) |
| Expected duration | 15-30s |
| Expected windows | 1-3 |
| Parameter variation | file_count: 1, 2, or 3; delay: 1-4 seconds between edits |
| Expected feature profile | file_modified: 1-3, unique_files_modified: 1-3, total_events: 1-5 |
| Purpose | Common coding/editing behavior |

---

### N3 — Multi-File Editing Session

| Field | Value |
|-------|-------|
| Description | User works on 4-7 files in a coding session, editing multiple files |
| Operations | file_modified (4-7 files), possibly file_created (1-2) |
| Expected duration | 20-40s |
| Expected windows | 2-4 |
| Parameter variation | file_count: 4-7; delay: 500ms-2s; include occasional file_created |
| Expected feature profile | file_modified: 4-7, unique_files_modified: 4-7, total_events: 5-12 |
| Purpose | Moderate legitimate editing — overlaps with low-intensity ransomware |

---

### N4 — Directory Organization

| Field | Value |
|-------|-------|
| Description | User creates directories, renames files for organization, copies files |
| Operations | file_created (3-5), file_renamed (2-4), possibly file_deleted (1-2) |
| Expected duration | 20-30s |
| Expected windows | 2-3 |
| Parameter variation | create_count: 3-5; rename_count: 2-4; delete_count: 0-2 |
| Expected feature profile | file_created: 3-5, file_renamed: 2-4, file_deleted: 0-2 |
| Purpose | Legitimate rename/create activity to prevent model from treating ANY rename as suspicious |

---

### N5 — Build/Compilation Activity

| Field | Value |
|-------|-------|
| Description | Simulated build process: many files created (object files, outputs), process activity |
| Operations | file_created (8-15), process_events (5-10) |
| Expected duration | 20-30s |
| Expected windows | 2-3 |
| Parameter variation | file_count: 8-15; process_count: 5-10; delay: 50-200ms |
| Expected feature profile | file_created: 8-15, process_events: 5-10, total_events: 15-30 |
| Purpose | HIGH activity that is legitimately normal. Tests model's ability to distinguish creation-heavy vs. modification-heavy activity. |

---

### N6 — Network Browsing

| Field | Value |
|-------|-------|
| Description | Normal web browsing: multiple network connections to various IPs, minimal file activity |
| Operations | network connections (5-10), unique_remote_ips (3-6), minimal file_created (0-2) |
| Expected duration | 20-30s |
| Expected windows | 2-3 |
| Parameter variation | connection_count: 5-10; ip_count: 3-6; file_count: 0-2 |
| Expected feature profile | network_events: 5-10, unique_remote_ips: 3-6, established_connections: 4-8 |
| Purpose | High network without file modification — clearly different from ransomware pattern |

---

### N7 — File Download and Save

| Field | Value |
|-------|-------|
| Description | Download files from network, save to disk |
| Operations | network connections (3-5), file_created (3-5) |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | download_count: 3-5; ips: 1-3 |
| Expected feature profile | network_events: 3-5, file_created: 3-5, unique_remote_ips: 1-3 |
| Purpose | Concurrent network + file creation (legitimate combined activity) |

---

### N8 — Log Rotation / Repeated Single-File Writes

| Field | Value |
|-------|-------|
| Description | A process writes to the same log file repeatedly (simulates logging, auto-save, database writes) |
| Operations | file_modified: 10-20 events, but unique_files_modified: 1-2 |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | write_count: 10-20; unique_files: 1-2; delay: 200-800ms |
| Expected feature profile | file_modified: 10-20, unique_files_modified: 1-2, total_events: 10-22 |
| Purpose | CRITICAL scenario — high file_modified count but LOW unique_files_modified. This is the key behavioral difference from ransomware (which modifies MANY unique files). Tests whether the model learns this distinction. |

---

### N9 — Mixed High-Activity Normal

| Field | Value |
|-------|-------|
| Description | Simultaneous legitimate activity: editing files, running processes, network connections |
| Operations | file_modified (3-6), file_created (2-4), process_events (4-8), network_events (3-6) |
| Expected duration | 20-35s |
| Expected windows | 2-3 |
| Parameter variation | All parameters varied independently within stated ranges |
| Expected feature profile | total_events: 15-30, moderate values across all categories |
| Purpose | Represents a busy developer workstation. High total activity that is legitimate. Forces model to evaluate PATTERNS not just total volume. |

---

### N10 — Batch File Creation (Archive Extract)

| Field | Value |
|-------|-------|
| Description | Legitimate extraction of an archive: many files created rapidly |
| Operations | file_created (10-20), minimal modification |
| Expected duration | 15-20s |
| Expected windows | 1-2 |
| Parameter variation | file_count: 10-20; delay: 20-100ms; file types: mixed |
| Expected feature profile | file_created: 10-20, file_modified: 0-2, unique_files_modified: 0-2 |
| Purpose | High file_created burst that is legitimate. Distinguishes from ransomware which MODIFIES existing files. |

---

## 6. Ransomware-Like Scenario Catalog

### Design Principle

Ransomware-like scenarios simulate behavioral patterns associated with ransomware — rapid modification of many unique files, bulk renaming, deletion of originals, etc. They must be VARIED to prevent the model from overfitting to one specific pattern.

**Safety:** All operations target only `~/ransomware-lab/test-files/`. No real encryption. No destruction of important files.

---

### R1 — Rapid Modification (Low Intensity)

| Field | Value |
|-------|-------|
| Description | Modify 8-12 unique files quickly within a window |
| Operations | file_modified (8-12 unique files) |
| Expected duration | 12-15s |
| Expected windows | 1 |
| Parameter variation | file_count: 8, 10, 12; delay: 100-500ms |
| Expected feature profile | file_modified: 8-12, unique_files_modified: 8-12 |
| Purpose | Low-end ransomware-like behavior. Overlaps with N3 (4-7 files). Tests sensitivity. |

---

### R2 — Rapid Modification (High Intensity)

| Field | Value |
|-------|-------|
| Description | Modify 20-30 unique files very quickly |
| Operations | file_modified (20-30 unique files) |
| Expected duration | 12-15s |
| Expected windows | 1 |
| Parameter variation | file_count: 20, 25, 30; delay: 10-100ms |
| Expected feature profile | file_modified: 20-30, unique_files_modified: 20-30, total_events: 20-35 |
| Purpose | Clear high-intensity ransomware pattern. Should be easily detectable. |

---

### R3 — Encrypt and Rename

| Field | Value |
|-------|-------|
| Description | Modify files (simulate encryption) then rename with new extension (.encrypted, .locked) |
| Operations | file_modified + file_renamed for each target file |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | file_count: 8-15; extensions: .encrypted, .locked, .cry, .enc; delay: 50-200ms |
| Expected feature profile | file_modified: 8-15, file_renamed: 8-15, unique_files_modified: 8-15 |
| Purpose | Classic ransomware behavioral signature: modify then rename. |

---

### R4 — Create Encrypted Copy, Delete Original

| Field | Value |
|-------|-------|
| Description | For each target file: create new file (encrypted copy), delete original |
| Operations | file_created + file_deleted for each target |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | file_count: 8-15; delay: 50-200ms |
| Expected feature profile | file_created: 8-15, file_deleted: 8-15, total_events: 20-35 |
| Purpose | Alternative ransomware pattern: create+delete rather than modify+rename. |

---

### R5 — Burst All Operations

| Field | Value |
|-------|-------|
| Description | Rapid mix of create, modify, delete, and rename operations |
| Operations | All file operation types in rapid succession |
| Expected duration | 12-20s |
| Expected windows | 1-2 |
| Parameter variation | total_ops: 15-30; op_mix: varied; delay: 20-100ms |
| Expected feature profile | Elevated across file_created, file_modified, file_deleted, file_renamed |
| Purpose | Chaotic ransomware behavior — all operation types active simultaneously. |

---

### R6 — Slow Encryption (Low Intensity)

| Field | Value |
|-------|-------|
| Description | Modify 5-8 unique files spread across the full 10s window (slower attack) |
| Operations | file_modified (5-8 files), spread with 1-2s delays |
| Expected duration | 12-15s |
| Expected windows | 1 |
| Parameter variation | file_count: 5, 6, 7, 8; delay: 1000-2000ms |
| Expected feature profile | file_modified: 5-8, unique_files_modified: 5-8 |
| Purpose | CRITICAL — overlaps with N3 (4-7 files). Model must use OTHER features or subtle patterns to distinguish. Represents stealthier ransomware. |

---

### R7 — Process Spawn + Encrypt

| Field | Value |
|-------|-------|
| Description | Spawn child processes that each modify multiple files |
| Operations | process_events (3-6) + file_modified (12-20) |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | process_count: 3-6; files_per_process: 3-5; delay: 50-150ms |
| Expected feature profile | process_events: 3-6, file_modified: 12-20, unique_files_modified: 12-20 |
| Purpose | Multi-process ransomware pattern with high file modification. |

---

### R8 — Network Exfiltration + Encrypt

| Field | Value |
|-------|-------|
| Description | Establish network connections (simulated C2/exfil) concurrent with file modifications |
| Operations | network connections (3-6) + file_modified (10-15) |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | connections: 3-6; ips: 2-4; file_count: 10-15; delay: 50-200ms |
| Expected feature profile | network_events: 3-6, unique_remote_ips: 2-4, file_modified: 10-15, unique_files_modified: 10-15 |
| Purpose | Multi-vector ransomware: file + network combined. Distinguishes from N6 (network-only) and N7 (network + create, not modify). |

---

### R9 — Multi-Vector Combined

| Field | Value |
|-------|-------|
| Description | File modification + process spawning + network activity all elevated simultaneously |
| Operations | file_modified (8-12), process_events (4-8), network_events (3-5), unique_remote_ips (2-3) |
| Expected duration | 15-25s |
| Expected windows | 1-2 |
| Parameter variation | All parameters varied within ranges |
| Expected feature profile | Elevated across all feature categories |
| Purpose | Full multi-dimensional ransomware pattern. Should be clearly distinguishable from any single-category normal behavior. |

---

### R10 — Rename-Only Burst

| Field | Value |
|-------|-------|
| Description | Rapid renaming of many files without modification (extension change attack) |
| Operations | file_renamed (12-20) |
| Expected duration | 12-15s |
| Expected windows | 1 |
| Parameter variation | file_count: 12, 15, 18, 20; delay: 20-100ms; extensions: varied |
| Expected feature profile | file_renamed: 12-20, file_modified: 0-2 |
| Purpose | Different ransomware signature — rename-heavy rather than modify-heavy. Forces model to recognize multiple attack patterns. |

---

## 7. Labeling Rules

### 7.1 Label Source

Labels come EXCLUSIVELY from the experimental design:

```
IF scenario_type == "NORMAL":
    label = 0
ELIF scenario_type == "RANSOMWARE_LIKE":
    label = 1
```

### 7.2 Label Prohibition

Labels are NEVER derived from:
- Rule engine output
- `suspicious_indicators` feature value
- ML model prediction (circular)
- Post-hoc feature analysis ("this window had high values, so label it 1")
- The `detection_engine.py` HIGH/CRITICAL risk level

### 7.3 All Windows in a Session Share the Same Label

A RANSOMWARE_LIKE session does not contain NORMAL windows. The entire session represents one controlled experimental condition.

### 7.4 Edge Cases

If a RANSOMWARE_LIKE scenario produces a window with very low activity (e.g., the burst happened in Window 1 but Window 2 was quiet because the scenario completed), that window is STILL labeled RANSOMWARE_LIKE because it came from a ransomware-like session. This is a known limitation — partial-activity windows may add noise. Mitigation: keep scenarios compact (minimize quiet trailing time).

---

## 8. Feature Extraction Pipeline

### 8.1 Pipeline Flow

```
Scenario execution generates Common Events
        ↓
Events collected (in memory or events.jsonl)
        ↓
Events assigned to 10-second windows by timestamp
        ↓
Each window's events passed to core/feature_extractor.py
        ↓
Feature extractor returns 12 features
        ↓
ML feature selection: pick 10 features per ML_FEATURE_COLUMNS
        ↓
Attach session_id, window_id, label
        ↓
Save record
```

### 8.2 Feature Extractor Interface

The collection harness will call the EXISTING `core/feature_extractor.py`.

**Expected interface** (to be confirmed in M2.2):
```python
from core.feature_extractor import extract_features

features = extract_features(events_in_window)
# Returns dict with 12 keys
```

### 8.3 ML Feature Selection

After receiving 12 features from the extractor:
```python
from ml.config import ML_FEATURE_COLUMNS

ml_features = {col: features[col] for col in ML_FEATURE_COLUMNS}
```

This excludes `file_events` and `suspicious_indicators`.

### 8.4 No Independent Feature Calculation

Features are NOT independently recalculated by the ML module. They come from the existing verified feature extractor. This ensures consistency between training and real-time inference.

---

## 9. Dataset Record Format

### 9.1 Storage Format

**CSV** — simple, portable, inspectable, directly loadable by pandas.

Filename: `ml/data/processed/dataset_v0.1.csv`

### 9.2 Column Schema

```csv
session_id,window_id,scenario_id,label,total_events,file_created,file_modified,file_deleted,file_renamed,unique_files_modified,process_events,network_events,established_connections,unique_remote_ips
```

| Column | Type | Role |
|--------|------|------|
| session_id | string | Metadata (for splitting) |
| window_id | string | Metadata (for traceability) |
| scenario_id | string | Metadata (for analysis) |
| label | int (0 or 1) | Target variable |
| total_events | int | ML feature [0] |
| file_created | int | ML feature [1] |
| file_modified | int | ML feature [2] |
| file_deleted | int | ML feature [3] |
| file_renamed | int | ML feature [4] |
| unique_files_modified | int | ML feature [5] |
| process_events | int | ML feature [6] |
| network_events | int | ML feature [7] |
| established_connections | int | ML feature [8] |
| unique_remote_ips | int | ML feature [9] |

### 9.3 Window ID Format

```
S_0001_W01, S_0001_W02, S_0001_W03, ...
```

Combines session_id + sequential window number within that session.

### 9.4 Metadata vs. Model Input

**Metadata columns** (session_id, window_id, scenario_id): Used for splitting, analysis, and traceability. NEVER used as model input features.

**Feature columns** (10 columns from total_events to unique_remote_ips): Used as model input. Must match `ML_FEATURE_COLUMNS` order exactly.

**Label column** (label): Target variable for training.

---

## 10. Session Metadata Format

### 10.1 Storage

File: `ml/data/metadata/sessions.json`

### 10.2 Schema

```json
{
    "dataset_version": "0.1",
    "feature_version": "1.0",
    "window_seconds": 10,
    "collection_environment": "ubuntu_lab",
    "sessions": [
        {
            "session_id": "S_0001",
            "scenario_id": "N1",
            "scenario_type": "NORMAL",
            "label": 0,
            "start_time": "...",
            "end_time": "...",
            "duration_seconds": 15,
            "window_count": 1,
            "parameters": {
                "file_count": 0,
                "delay_ms": 0,
                "operation_types": [],
                "target_directory": "~/ransomware-lab/test-files/"
            },
            "split": null
        }
    ]
}
```

The `split` field (train/validation/test) is assigned AFTER all data is collected.

### 10.3 What Metadata Must NOT Become

Session metadata (parameters, scenario_id, scenario_type) must NEVER leak into model features. The model sees only the 10 behavioral feature values. It does not know which scenario produced them.

---

## 11. Diversity and Overlap Strategy

### 11.1 Parameter Variation

Each scenario is executed multiple times with different parameters:

| Dimension | Variation Strategy |
|-----------|-------------------|
| File count | At least 3 different values per scenario |
| Timing/delay | At least 2 different speeds per scenario |
| File types | .txt, .doc, .pdf, .py, .csv, .log — varied across sessions |
| Operation order | Randomized within constraints |
| Target files | Different filenames each session (avoid "victim_1.txt" signature) |

### 11.2 Cross-Class Overlap (Critical)

The dataset is specifically designed so that some normal and ransomware-like windows produce overlapping feature ranges:

| Feature | Normal Range (max) | Ransomware Range (min) | Overlap Zone |
|---------|-------------------|----------------------|--------------|
| total_events | 15-30 (N5, N9) | 10-20 (R6) | 10-30 |
| file_modified | 10-20 (N8) | 5-8 (R6) | 5-20 |
| unique_files_modified | 4-7 (N3) | 5-8 (R6) | 4-8 |
| file_created | 10-20 (N10) | 8-15 (R4) | 8-15 |
| file_renamed | 2-4 (N4) | 12-20 (R10) | 2-4 (minimal) |

### 11.3 Why Overlap Matters

Without overlap, the model learns a trivial threshold (e.g., "unique_files_modified > 7 = ransomware"). This:
- Overfits to specific simulator parameters
- Adds no value beyond the existing rule (which already checks for 10 files)
- Is not defensible in a viva

With overlap, the model must learn **multi-dimensional patterns** — the COMBINATION of features, not just individual thresholds.

### 11.4 Key Distinguishing Patterns

Despite overlap in individual features, the COMBINATIONS differ:

| Pattern | Normal Example | Ransomware Example |
|---------|---------------|-------------------|
| High file_modified + LOW unique_files | N8 (log rotation) | — |
| High file_modified + HIGH unique_files | — | R1, R2, R6 |
| High file_created + LOW file_modified | N5, N10 | — |
| High file_created + HIGH file_deleted | — | R4 |
| High file_renamed + HIGH file_modified | — | R3 |
| High network + LOW file_modified | N6 | — |
| High network + HIGH file_modified | — | R8 |

This is the behavioral intelligence the model should capture.

---

## 12. Safety Controls

### 12.1 File System Safety

| Rule | Implementation |
|------|---------------|
| All file operations ONLY in `~/ransomware-lab/test-files/` | Path prefix check before every file operation |
| Never modify files outside the test directory | Absolute path validation |
| Test files are disposable | Regenerated fresh before each session |
| No real encryption | Write dummy content (random bytes or known string) to simulate modification |
| No irreversible operations on real data | Test directory contains only purpose-generated disposable files |

### 12.2 Process Safety

| Rule | Implementation |
|------|---------------|
| No real ransomware binaries executed | All simulation via Python scripts |
| No privilege escalation | Run as normal user |
| Process spawning is controlled | Known safe processes only (python, bash, cat, touch, mv, cp) |
| Maximum scenario duration | Timeout kills scenario after defined maximum |

### 12.3 Network Safety

| Rule | Implementation |
|------|---------------|
| No external exploitation | Only connect to controlled endpoints |
| Network targets: localhost, Kali machine (192.168.74.129), or benign external | Allowlist of safe targets |
| No data exfiltration | Only connection establishment matters, not actual data content |
| No port scanning of external systems | Network activity is controlled connections only |

### 12.4 Rollback

Before each session:
1. Delete all files in `~/ransomware-lab/test-files/`
2. Regenerate fresh test files appropriate for the scenario
3. Confirm clean state

After each session:
1. Clean up any residual files
2. Confirm no operations occurred outside test directory

---

## 13. Data Storage Format and Versioning

### 13.1 File Structure

```
ml/data/
├── collection_plan.md          # This document
├── scenarios/
│   ├── normal_scenarios.json   # Normal scenario definitions
│   └── ransomware_like_scenarios.json  # Ransomware-like scenario definitions
├── collectors/
│   ├── collection_harness.py   # Orchestrator
│   ├── scenario_runner.py      # Executes scenarios
│   └── window_extractor.py     # Divides events into windows
├── raw/                        # Raw session event data (JSONL per session)
├── processed/
│   └── dataset_v0.1.csv       # Final ML-ready dataset
├── metadata/
│   └── sessions.json          # Session registry with full metadata
└── validate_dataset.py        # Dataset validation script
```

### 13.2 Versioning

```
FEATURE_VERSION = "1.0"     # Changes when feature contract changes
DATASET_VERSION = "0.1"     # Changes when dataset is regenerated or expanded
MODEL_VERSION = None         # Set during training (M6)
```

**Version independence:**
- Feature version changes → dataset must be regenerated → model must be retrained
- Dataset version changes → model should be retrained
- Model version changes → no effect on dataset or features

### 13.3 No Heavy Infrastructure

Storage is plain files (CSV, JSON, JSONL). No databases, message queues, or external services required.

---

## 14. Target Dataset Size Estimation

### 14.1 Calculation

| Item | Count |
|------|-------|
| Normal scenarios | 10 types |
| Sessions per normal scenario | 3-4 (varied parameters) |
| Total normal sessions | 30-40 |
| Windows per normal session (avg) | 2 |
| **Total normal windows** | **60-80** |
| | |
| Ransomware-like scenarios | 10 types |
| Sessions per ransomware scenario | 3-4 (varied parameters) |
| Total ransomware-like sessions | 30-40 |
| Windows per ransomware session (avg) | 1.5 |
| **Total ransomware-like windows** | **45-60** |
| | |
| **TOTAL ESTIMATED OBSERVATIONS** | **105-140** |

### 14.2 Is This Enough?

This is a **small dataset** by general ML standards. However:

- We have only 10 features (low-dimensional)
- Binary classification (simple problem structure)
- Tree-based models (Random Forest, Gradient Boosting) handle small datasets well
- Features are clean (controlled generation, no noise from real-world chaos)
- Cross-validation can maximize use of limited data

### 14.3 Limitations to Acknowledge

- Small sample size limits statistical power
- May not capture all possible ransomware behavioral patterns
- Model generalization to truly unseen patterns is uncertain
- Reported metrics will have wide confidence intervals

### 14.4 Expansion Strategy

If initial results are promising but noisy:
1. Add more parameter variations to existing scenarios
2. Design additional scenario types
3. Increase session count per scenario

Do NOT artificially inflate by duplicating identical sessions or adding trivially different parameters.

---

## 15. Leakage Prevention and Splitting Strategy

### 15.1 Splitting Rule

**SPLIT BY SESSION. NEVER BY WINDOW.**

All windows from a single session go to the same split.

### 15.2 Split Ratios

```
TRAIN:      ~60% of sessions
VALIDATION: ~20% of sessions
TEST:       ~20% of sessions
```

Applied separately, then windows inherit their session's split assignment.

### 15.3 Stratification

Splits must be stratified by:
1. **Label** — each split must contain both NORMAL and RANSOMWARE_LIKE sessions
2. **Scenario diversity** — avoid putting all instances of one scenario type in the same split

### 15.4 Test Set Integrity

The test set should contain:
- Parameter combinations NOT seen during training
- At least one session from each scenario type (if possible)
- Represents "unseen" behavior for genuine generalization assessment

### 15.5 Implementation

Splitting is performed AFTER all data is collected (not during collection). The split assignment is recorded in `sessions.json` under the `split` field.

### 15.6 What This Prevents

| Leakage Type | How Prevention Works |
|--------------|---------------------|
| Temporal leakage | Adjacent windows from same session stay together |
| Parameter leakage | All windows from same parameters stay together |
| Session signature | Each session is fully in one split |

---

## 16. Validation Requirements

### 16.1 Per-Record Validation

| Check | Rule |
|-------|------|
| Missing values | No NaN/null in any feature or label column |
| Negative values | All 10 features must be >= 0 |
| Data types | All features must be integer; label must be 0 or 1 |
| Feature count | Exactly 10 feature columns |
| Feature order | Must match ML_FEATURE_COLUMNS |

### 16.2 Dataset-Level Validation

| Check | Rule |
|-------|------|
| Duplicate window IDs | No duplicates allowed |
| Duplicate rows | No identical feature vectors (indicates copy error) |
| Class distribution | Both classes present; report exact ratio |
| Session integrity | Every window's session_id exists in sessions.json |
| Label consistency | All windows from same session have same label |
| Feature ranges | Report min/max/mean for each feature |
| Empty sessions | No sessions with 0 windows (indicates execution failure) |

### 16.3 Contract Validation

| Check | Rule |
|-------|------|
| Feature version | Dataset metadata matches FEATURE_VERSION = "1.0" |
| Window size | All windows based on WINDOW_SECONDS = 10 |
| Excluded features | `file_events` and `suspicious_indicators` NOT present as columns |

---

## 17. Reproducibility Requirements

### 17.1 Per-Session Recording

Every session records:
- Session ID
- Scenario type and ID
- Exact parameters used
- Start/end timestamps
- Window count
- Environment identifier
- Label

### 17.2 Scenario Definitions

Scenarios are defined in JSON files with exact parameter specifications. Running the same scenario with the same parameters should produce similar (not identical, due to timing variability) results.

### 17.3 Random Seeds

If any randomization is used (e.g., random file selection, random delays):
- Record the seed in session metadata
- Allow replaying with the same seed

### 17.4 Environment Recording

Record the lab environment state:
- Ubuntu version
- Python version
- Project version/commit hash (if available)
- Date and time

---

## 18. Core Compatibility Verification Plan (M2.2)

Before building the full collection harness, verify compatibility by:

### 18.1 Steps

1. Inspect `core/feature_extractor.py` to confirm:
   - Input format (list of event dicts? event objects?)
   - Output format (dict with 12 keys?)
   - Whether it requires the event collector or can be called standalone
   - How `suspicious_indicators` is calculated

2. Inspect `core/event_schema.py` to confirm:
   - Exact Common Event fields
   - Required vs optional fields
   - Validation logic

3. Run a minimal test:
   - Generate 3-5 Common Events manually
   - Pass them to feature_extractor
   - Verify 12 features returned
   - Select 10 ML features
   - Validate against feature contract

### 18.2 If Incompatibility Found

STOP. Document:
- What is incompatible
- What would need to change
- Impact on existing tests
- Proposed solution

Request approval before modifying any core file.

---

## 19. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|-----------|
| Small dataset (100-140 observations) | Limited statistical power, wide confidence intervals | Use appropriate models, cross-validation, acknowledge in reporting |
| Lab environment only | May not represent real-world system noise | Document as limitation, focus on behavioral patterns not absolute values |
| Limited ransomware behavioral patterns | Only 10 scenario types designed | Clearly state what patterns are covered vs. not covered |
| Python-based simulation | Model may learn Python-specific artifacts | Vary execution methods, test with different process names if possible |
| Controlled timing | Real ransomware timing may differ | Vary delays significantly, acknowledge limitation |
| Single observation window (10s) | May miss attacks that span longer periods | Document as future work (5s/30s/60s experimentation) |
| Binary classification only | Cannot distinguish between different attack types | Start simple, multi-class can be explored later with more data |
| No real-world validation | Cannot test against actual ransomware | Use diverse simulated patterns, acknowledge this is a controlled study |

---

## 20. M2 Development Sequence

| Step | Task | Depends On | Status |
|------|------|-----------|--------|
| M2.1 | Create collection_plan.md | M1 complete | IN PROGRESS |
| M2.2 | Review feature extractor compatibility | M2.1 approved | PLANNED |
| M2.3 | Design scenario definitions (JSON) | M2.2 complete | PLANNED |
| M2.4 | Build minimal collection harness | M2.3 complete | PLANNED |
| M2.5 | Run one NORMAL session (smoke test) | M2.4 complete | PLANNED |
| M2.6 | Run one RANSOMWARE_LIKE session (smoke test) | M2.5 complete | PLANNED |
| M2.7 | Validate generated records | M2.6 complete | PLANNED |
| M2.8 | Expand scenario diversity (all sessions) | M2.7 complete | PLANNED |
| M2.9 | Collect final dataset | M2.8 complete | PLANNED |
| M2.10 | Validate final dataset | M2.9 complete | PLANNED |

---

## 21. Approval Gates

| Gate | What Needs Approval |
|------|-------------------|
| After M2.1 | This collection plan |
| After M2.2 | Any proposed core modifications (if needed) |
| After M2.7 | Initial validation results before full collection |
| After M2.10 | Final dataset before proceeding to M3 (EDA) |

---

*End of Collection Plan*
