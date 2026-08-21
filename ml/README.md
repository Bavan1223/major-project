# ML Module — Ransomware Behavioral Detection

## Purpose

This module provides machine learning-based behavioral classification for the Real-Time Ransomware Detection and Prevention system. It distinguishes normal system behavior from ransomware-like behavioral patterns based on system telemetry features extracted from monitored events.

**Status:** Baseline model (controlled 76-sample dataset). Not production-ready.

## Architecture Position

```
File Monitor ─┐
Process Monitor ─┤ → Common Events → Event Collector → Feature Extractor
Network Monitor ─┘                                            │
                                                              ↓
                                                     12-feature dict
                                                              │
                                                              ↓
                                              ┌───────────────────────────────┐
                                              │ ML Integration Adapter        │
                                              │  - Selects 10 ML features     │
                                              │  - Excludes file_events       │
                                              │  - Excludes suspicious_indicators │
                                              └───────────────┬───────────────┘
                                                              │
                                                              ↓
                                              ┌───────────────────────────────┐
                                              │ ML Predictor                  │
                                              │  - Validates features         │
                                              │  - Applies StandardScaler     │
                                              │  - Logistic Regression        │
                                              │  - Returns structured result  │
                                              └───────────────┬───────────────┘
                                                              │
                                                              ↓
                                                     ML Prediction Result
                                                              │
                                                              ↓
                                                   Central Risk Engine
                                              (combines ML + rules + other signals)
```

## What This Module Does

- Classifies 10-second behavioral observation windows as NORMAL or RANSOMWARE_LIKE
- Returns probability scores and feature-level explanations
- Validates input features against the v1.0 contract
- Loads and manages model artifacts

## What This Module Does NOT Do

- Monitor files, processes, or network
- Make final risk severity decisions (NORMAL/LOW/MEDIUM/HIGH/CRITICAL)
- Kill processes, block connections, or quarantine files
- Replace the rule-based detection engine
- Retrain during inference

## Directory Structure

```
ml/
├── __init__.py                  # Module definition (v0.1.0)
├── config.py                    # Central configuration and constants
├── README.md                    # This file
│
├── features/
│   ├── feature_definition.json  # Formal 10-feature contract (v1.0)
│   └── suspicious_indicators_decision.md  # Exclusion rationale
│
├── data/
│   ├── collection_plan.md       # Data collection methodology
│   ├── scenarios/
│   │   ├── normal_scenarios.json       # N1-N10 definitions
│   │   ├── ransomware_like_scenarios.json  # R1-R10 definitions
│   │   └── validate_scenarios.py       # Scenario validation tests
│   ├── collectors/
│   │   ├── collection_harness.py       # Dataset generation orchestrator
│   │   ├── collect_ubuntu.py           # Ubuntu lab collection script
│   │   ├── scenario_runner.py          # Scenario execution engine
│   │   └── window_extractor.py         # 10-second window processing
│   ├── processed/
│   │   └── dataset_v0.1.csv            # Training dataset (76 samples)
│   ├── metadata/
│   │   └── sessions.json               # Session-level metadata
│   ├── raw/                            # Raw event data per session
│   └── validate_dataset.py             # Dataset quality validation
│
├── models/
│   ├── ransomware_model.pkl     # Trained Logistic Regression
│   ├── preprocessor.pkl         # Fitted StandardScaler
│   └── model_metadata.json      # Version, params, metrics
│
├── training/
│   └── train.py                 # Complete training pipeline
│
├── inference/
│   ├── predictor.py             # RansomwarePredictor class
│   └── integration.py           # Core integration adapter
│
├── evaluation/                  # (reserved for future evaluation scripts)
│
├── tests/
│   ├── test_feature_contract.py            # M1 contract validation (26 tests)
│   ├── test_feature_extractor_compatibility.py  # M2.2 compatibility (18 tests)
│   └── test_inference.py                   # Inference + integration (44 tests)
│
└── docs/
    ├── MODEL_CARD.md            # Model documentation
    ├── INFERENCE_SPEC.md        # Input/output specification
    └── TRAINING_SPEC.md         # Training methodology
```

## Feature Contract (v1.0)

The ML model consumes exactly these 10 features, in this order:

| Index | Feature | Source |
|-------|---------|--------|
| 0 | total_events | all monitors |
| 1 | file_created | file_monitor |
| 2 | file_modified | file_monitor |
| 3 | file_deleted | file_monitor |
| 4 | file_renamed | file_monitor |
| 5 | unique_files_modified | file_monitor |
| 6 | process_events | process_monitor |
| 7 | network_events | network_monitor |
| 8 | established_connections | network_monitor |
| 9 | unique_remote_ips | network_monitor |

**Excluded:** `file_events` (redundant), `suspicious_indicators` (rule-derived, creates circular reasoning).

## Training Workflow

```bash
# On Ubuntu lab:
cd ~/ransomware-lab

# Collect dataset using real monitors
python3 -m ml.data.collectors.collect_ubuntu --mode full

# Validate dataset
python3 -m ml.data.validate_dataset ml/data/processed/dataset_v0.1.csv

# Train models
python3 -m ml.training.train
```

## Inference Workflow

```python
from ml.inference.integration import get_ml_prediction

# Input: 12-feature dict from core/feature_extractor.extract_features()
extractor_output = extract_features(events)

# Get ML prediction
result = get_ml_prediction(extractor_output)

# Result structure:
# {
#     "status": "success",
#     "prediction": 1,
#     "label": "RANSOMWARE_LIKE",
#     "probability": 0.9986,
#     "above_threshold": True,
#     "threshold": 0.7,
#     "model_version": "1.0.0",
#     "feature_version": "1.0",
#     "important_features": [...],
#     "inference_time_ms": 0.35
# }
```

## How to Run Tests

```bash
# All tests (114 total):
python -m ml.tests.test_feature_contract
python -m ml.tests.test_feature_extractor_compatibility
python -m ml.data.scenarios.validate_scenarios
python -m ml.tests.test_inference

# Individual test suites:
python ml/tests/test_feature_contract.py          # 26 tests
python ml/tests/test_feature_extractor_compatibility.py  # 18 tests
python ml/data/scenarios/validate_scenarios.py    # 26 tests
python ml/tests/test_inference.py                 # 44 tests
```

## How to Run Inference

```python
from ml.inference.predictor import RansomwarePredictor

# Direct predictor usage (10-feature dict):
predictor = RansomwarePredictor()
result = predictor.predict({
    "total_events": 25,
    "file_created": 0,
    "file_modified": 20,
    "file_deleted": 2,
    "file_renamed": 3,
    "unique_files_modified": 20,
    "process_events": 0,
    "network_events": 0,
    "established_connections": 0,
    "unique_remote_ips": 0,
})

# Integration adapter (12-feature dict from feature extractor):
from ml.inference.integration import get_ml_prediction
result = get_ml_prediction(extractor_output_dict)
```

## Versioning

| Version Type | Current | Changes When |
|-------------|---------|--------------|
| Feature version | 1.0 | Feature set changes (add/remove/reorder) |
| Model version | 1.0.0 | Model retrained or algorithm changed |
| Dataset version | 0.1 | Dataset regenerated or expanded |

## Dependencies

- Python 3.8+
- numpy
- scikit-learn
- joblib

## Limitations

- Baseline model trained on controlled 76-sample dataset
- Simulated feature extractor used (not actual Ubuntu lab telemetry for current artifacts)
- NOT production-ready — requires Ubuntu lab data collection and retraining
- 2 genuinely ambiguous cross-class samples exist (N3/R6 overlap)
- Model has never seen real ransomware
- Probability output is not calibrated
