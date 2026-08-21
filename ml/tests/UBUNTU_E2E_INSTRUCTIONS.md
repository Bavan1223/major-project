# Ubuntu End-to-End Validation — Deployment Instructions

## Overview

This document provides exact steps to validate the ML module against the REAL Ubuntu lab environment at `~/ransomware-lab/`.

## Prerequisites

- Ubuntu lab machine (192.168.74.131)
- Python 3.8+ with pip
- Project at `~/ransomware-lab/` with working monitors
- `~/ransomware-lab/test-files/` directory

## Step 1: Install Dependencies

```bash
cd ~/ransomware-lab
pip3 install scikit-learn joblib numpy
```

## Step 2: Copy ML Module to Ubuntu Lab

From your Windows machine, transfer the entire `ml/` directory to the Ubuntu lab:

**Option A: SCP from Windows**
```powershell
scp -r "C:\Users\sbava\OneDrive\Desktop\ml model\ml" bavan@192.168.74.131:~/ransomware-lab/
```

**Option B: Manual copy via shared folder or USB**
Copy the entire `ml/` folder to `~/ransomware-lab/ml/`

**Option C: Git (if using version control)**
```bash
cd ~/ransomware-lab
git pull  # if ml/ is tracked
```

## Step 3: Verify Directory Structure

```bash
cd ~/ransomware-lab
ls ml/
# Should show: __init__.py  config.py  README.md  data/  docs/  evaluation/
#              features/  inference/  models/  tests/  training/

ls ml/models/
# Should show: model_metadata.json  preprocessor.pkl  ransomware_model.pkl
```

## Step 4: Verify Core Compatibility

```bash
cd ~/ransomware-lab
python3 -c "from core.feature_extractor import extract_features; print('Core extractor: OK')"
python3 -c "from ml.inference.predictor import RansomwarePredictor; p = RansomwarePredictor(); print(f'ML model: OK (v{p.model_version})')"
```

Both should print OK without errors.

## Step 5: Run E2E Validation

```bash
cd ~/ransomware-lab
python3 -m ml.tests.e2e_ubuntu_validation
```

This will:
1. Generate normal file activity (create 3 files, modify 2)
2. Extract features using REAL `core/feature_extractor.py`
3. Run ML inference
4. Generate ransomware-like activity (rapidly modify 15 files)
5. Extract features again
6. Run ML inference
7. Measure latency (100 iterations)
8. Save report to `ml/tests/e2e_report.json`

## Step 6: Verify Output

The script should print:
- `Core extractor: AVAILABLE`
- Normal scenario → prediction=NORMAL, probability < 0.5
- Ransomware scenario → prediction=RANSOMWARE_LIKE, probability > 0.7
- `Pipeline verdict: COMPATIBLE`

## Step 7: Capture Results

After execution, collect:
```bash
cat ml/tests/e2e_report.json
```

Copy this JSON output — it contains the full validation results needed for Gate 6.

## Step 8: Run Full Test Suite (Optional but Recommended)

```bash
cd ~/ransomware-lab
python3 ml/tests/test_feature_contract.py
python3 ml/tests/test_feature_extractor_compatibility.py
python3 ml/tests/test_inference.py
```

All should report PASS.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: sklearn` | `pip3 install scikit-learn` |
| `ModuleNotFoundError: core.feature_extractor` | Ensure running from `~/ransomware-lab/` |
| `ModelNotLoadedError` | Check `ml/models/` contains .pkl files |
| `FileNotFoundError: test-files` | `mkdir -p ~/ransomware-lab/test-files/` |
| `Permission denied` | Check file permissions: `chmod -R 755 ml/` |

## Expected Output Format

On successful Ubuntu validation, the output should look like:

```
Core extractor: AVAILABLE (REAL core/feature_extractor.py)

Normal scenario:
  Features: total_events=5, file_created=3, file_modified=2, ...
  Prediction: NORMAL (probability=0.16)
  
Ransomware scenario:
  Features: total_events=15, file_modified=15, unique_files_modified=15, ...
  Prediction: RANSOMWARE_LIKE (probability=0.96)

Inference latency: ~0.3-1.0 ms (mean)
Pipeline verdict: COMPATIBLE
```

## What This Validates

- [x] Real core/feature_extractor.py produces output compatible with ML contract
- [x] 12-feature → 10-feature mapping works correctly
- [x] file_events and suspicious_indicators are properly excluded
- [x] Baseline model loads and predicts on Ubuntu
- [x] Preprocessing (StandardScaler) works on real feature values
- [x] Structured output format is correct
- [x] Inference latency is acceptable for real-time use
- [x] No core files need modification

## What This Does NOT Validate

- Real-time continuous monitoring (single observation only)
- Integration with Central Risk Engine (separate step)
- Model accuracy on real-world ransomware
- Production readiness
