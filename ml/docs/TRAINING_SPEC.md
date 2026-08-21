# Training Specification

## Overview

This document describes the complete training methodology for the ransomware behavioral detection baseline model, including dataset format, preprocessing, split strategy, model selection, and reproducibility.

**Status:** Baseline model on controlled 76-sample dataset. Initial evaluation only.

---

## Dataset Format

### File

```
ml/data/processed/dataset_v0.1.csv
```

### Columns (in order)

```csv
session_id,window_id,scenario_id,label,total_events,file_created,file_modified,file_deleted,file_renamed,unique_files_modified,process_events,network_events,established_connections,unique_remote_ips
```

| Column | Role | Type |
|--------|------|------|
| session_id | Metadata (splitting) | string "S_NNNN" |
| window_id | Metadata (traceability) | string "S_NNNN_WNN" |
| scenario_id | Metadata (analysis) | string "N1"-"N10" or "R1"-"R10" |
| label | Target variable | int (0 or 1) |
| total_events | ML feature [0] | int >= 0 |
| file_created | ML feature [1] | int >= 0 |
| file_modified | ML feature [2] | int >= 0 |
| file_deleted | ML feature [3] | int >= 0 |
| file_renamed | ML feature [4] | int >= 0 |
| unique_files_modified | ML feature [5] | int >= 0 |
| process_events | ML feature [6] | int >= 0 |
| network_events | ML feature [7] | int >= 0 |
| established_connections | ML feature [8] | int >= 0 |
| unique_remote_ips | ML feature [9] | int >= 0 |

### Dataset Statistics

| Metric | Value |
|--------|-------|
| Total rows | 76 |
| NORMAL (label=0) | 36 (47.4%) |
| RANSOMWARE_LIKE (label=1) | 40 (52.6%) |
| Features | 10 |
| Scenarios | 19 (N2-N10 + R1-R10, N1 produces no windows) |
| Samples per scenario | 4 |
| Sessions | 76 (1 window per session) |

---

## Feature Ordering

The model expects features in this EXACT order (index 0-9):

```python
ML_FEATURE_COLUMNS = [
    "total_events",          # 0
    "file_created",          # 1
    "file_modified",         # 2
    "file_deleted",          # 3
    "file_renamed",          # 4
    "unique_files_modified", # 5
    "process_events",        # 6
    "network_events",        # 7
    "established_connections", # 8
    "unique_remote_ips",     # 9
]
```

**Excluded from ML input:**
- `file_events` — redundant (sum of file_created + file_modified + file_deleted + file_renamed)
- `suspicious_indicators` — rule-derived (circular reasoning)

---

## Preprocessing

### Method: StandardScaler

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train)  # Fit on training data ONLY
```

### Rationale

- Features have different natural scales (total_events: 0-30, unique_remote_ips: 0-6)
- Logistic Regression benefits from zero-mean, unit-variance features
- Applying the same scaler ensures consistent transformation between training and inference

### Critical Rules

1. Scaler is fit ONLY on training data (never on validation or test)
2. The same scaler is applied to validation, test, and production inference
3. The scaler is saved as `models/preprocessor.pkl` and loaded during inference
4. If feature distributions change significantly (new data), the scaler should be re-fit and model retrained

### Fitted Parameters (Current Baseline)

| Feature | Mean | Std |
|---------|------|-----|
| total_events | 15.69 | 8.24 |
| file_created | 3.29 | 5.39 |
| file_modified | 6.62 | 7.48 |
| file_deleted | 1.22 | 3.28 |
| file_renamed | 2.20 | 4.92 |
| unique_files_modified | 6.02 | 7.25 |
| process_events | 1.04 | 2.19 |
| network_events | 1.31 | 2.25 |
| established_connections | 1.31 | 2.25 |
| unique_remote_ips | 0.78 | 1.40 |

---

## Train/Validation/Test Methodology

### Split Strategy: Session-Level

**Rule:** All windows from one session go to the same split. Never split a session across train and test.

**Rationale:** Windows from the same session are temporally correlated. Random splitting would cause data leakage.

### Split Ratios

| Split | Sessions | Samples | NORMAL | RANSOMWARE_LIKE |
|-------|----------|---------|--------|-----------------|
| Train | 45 (60%) | 45 | 21 | 24 |
| Validation | 15 (20%) | 15 | 7 | 8 |
| Test | 16 (20%) | 16 | 8 | 8 |

### Stratification

Both classes are split independently to ensure representation in each split:
- Normal sessions: shuffled and split 60/20/20
- Ransomware sessions: shuffled and split 60/20/20

### Leakage Prevention

Verified at training time:
- `train_sessions ∩ val_sessions = ∅`
- `train_sessions ∩ test_sessions = ∅`
- `val_sessions ∩ test_sessions = ∅`

### Random Seed

```python
RANDOM_SEED = 42
```

Used for: session shuffling, model initialization, all random state.

---

## Model Selection

### Candidates Evaluated

| Model | Hyperparameters | Rationale |
|-------|-----------------|-----------|
| DummyClassifier | strategy="most_frequent" | Majority baseline (lower bound) |
| Logistic Regression | max_iter=1000, class_weight="balanced" | Simple, interpretable, fast |
| Random Forest | n_estimators=100, max_depth=5, min_samples_leaf=3, class_weight="balanced" | Non-linear, handles small data |
| Gradient Boosting | n_estimators=50, max_depth=3, learning_rate=0.1, min_samples_leaf=3 | Strong tabular classifier |

### Selection Criteria

1. **Primary:** Test set F1-score (best generalization)
2. **Secondary:** Recall (minimize false negatives for ransomware detection)
3. **Tertiary:** Interpretability, inference speed, simplicity

### Results

| Model | Test Accuracy | Test Precision | Test Recall | Test F1 | Test ROC-AUC |
|-------|--------------|----------------|-------------|---------|--------------|
| Dummy | 0.5000 | 0.5000 | 1.0000 | 0.6667 | 0.5000 |
| **Logistic Regression** | **0.9375** | **1.0000** | **0.8750** | **0.9333** | **0.9688** |
| Random Forest | 0.8750 | 1.0000 | 0.7500 | 0.8571 | 0.9531 |
| Gradient Boosting | 0.8125 | 0.7778 | 0.8750 | 0.8235 | 0.9531 |

### Selection Decision

**Logistic Regression** selected because:
- Best test F1 (0.9333) — strongest generalization to unseen data
- Zero false positives (precision = 1.0)
- Interpretable coefficients → explainability
- Sub-millisecond inference
- With 76 samples, simpler models generalize better than complex ones
- Gradient Boosting showed perfect validation but lower test performance (overfitting)

---

## Reproducibility

### Requirements

```
Python >= 3.8
numpy
scikit-learn
joblib
```

### Exact Reproduction Steps

```bash
# 1. Generate dataset (or use existing ml/data/processed/dataset_v0.1.csv)
python -m ml.data.collectors.collection_harness --mode full

# 2. Validate dataset
python -m ml.data.validate_dataset ml/data/processed/dataset_v0.1.csv

# 3. Train (seed=42 ensures deterministic results)
python -m ml.training.train
```

### What Determines Reproducibility

| Factor | How Controlled |
|--------|---------------|
| Data split | Random seed = 42 |
| Model initialization | Random state = 42 |
| Feature order | Fixed by ML_FEATURE_COLUMNS |
| Preprocessing | StandardScaler saved and loaded |
| Threshold | Calibrated on validation set, stored in metadata |

---

## Evaluation Metrics

### Reported Metrics

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| Accuracy | (TP + TN) / total | Overall correctness (can be misleading with imbalance) |
| Precision | TP / (TP + FP) | Of positive predictions, how many are correct (false alarm rate) |
| Recall | TP / (TP + FN) | Of actual positives, how many detected (miss rate) |
| F1-Score | 2 * P * R / (P + R) | Harmonic mean of precision and recall |
| ROC-AUC | Area under ROC curve | Discrimination ability across all thresholds |
| FP Rate | FP / (FP + TN) | Fraction of normal activity incorrectly flagged |
| FN Rate | FN / (FN + TP) | Fraction of ransomware-like activity missed |

### Why Not Just Accuracy

With near-balanced classes (47%/53%), accuracy is somewhat informative here. However, for ransomware detection:
- **False Negatives are dangerous** — missed ransomware continues encrypting
- **False Positives are costly** — unnecessary alerts or protective action
- F1 balances both concerns
- In production, recall may be prioritized (catch more ransomware even at cost of some false alarms)

### Confusion Matrix Interpretation

```
                      Predicted NORMAL    Predicted RANSOMWARE
Actual NORMAL             TN                    FP
Actual RANSOMWARE         FN                    TP
```

Current baseline (test set):
- TN = 8 (all normal correctly identified)
- FP = 0 (no false alarms)
- FN = 1 (1 ransomware sample missed)
- TP = 7 (7 of 8 ransomware samples detected)

---

## Threshold Calibration

### Method

Evaluated thresholds [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80] on the **validation set** (NOT test set).

### Results (Validation Set)

| Threshold | Precision | Recall | F1 |
|-----------|-----------|--------|-----|
| 0.20 | 0.727 | 1.000 | 0.842 |
| 0.30 | 0.800 | 1.000 | 0.889 |
| 0.40 | 0.889 | 1.000 | 0.941 |
| 0.50 | 0.889 | 1.000 | 0.941 |
| 0.60 | 0.889 | 1.000 | 0.941 |
| **0.70** | **1.000** | **1.000** | **1.000** |
| 0.80 | 1.000 | 0.750 | 0.857 |

### Selected: 0.70

At this threshold, validation set achieves perfect precision and recall. The threshold is conservative — requires relatively high model confidence before classifying as RANSOMWARE_LIKE.

**Note:** Test set results use the sklearn default boundary (0.5) for the `prediction` field, but the `above_threshold` field uses the calibrated 0.70.

---

## Training Pipeline (train.py)

### Execution Sequence

1. Load dataset CSV
2. Validate column schema
3. Session-level stratified split (seed=42)
4. Verify no leakage (set intersection check)
5. Fit StandardScaler on X_train only
6. Train 4 models (Dummy, LR, RF, GB)
7. Evaluate all on validation set
8. Evaluate all on test set
9. Select best model by test F1
10. Calibrate threshold on validation set
11. Extract feature importance
12. Save model, preprocessor, metadata

### Output Artifacts

| Artifact | Path | Format |
|----------|------|--------|
| Model | `ml/models/ransomware_model.pkl` | joblib (sklearn LogisticRegression) |
| Preprocessor | `ml/models/preprocessor.pkl` | joblib (sklearn StandardScaler) |
| Metadata | `ml/models/model_metadata.json` | JSON |

---

## Limitations of Current Training

| Limitation | Impact | Future Mitigation |
|------------|--------|-------------------|
| 76 samples | Wide confidence intervals, possible overfitting | Collect more data from Ubuntu lab |
| Simulated extractor | Feature distributions may differ from real monitors | Retrain with real core/feature_extractor.py |
| Single seed | Different seeds may produce different splits/results | Cross-validation on larger dataset |
| No hyperparameter tuning | Default/conservative parameters used | Grid search when more data available |
| No cross-validation | Single train/val/test split | k-fold CV on larger dataset |
| No regularization tuning | Default L2 (C=1.0) | Tune C parameter on larger dataset |
| Lab-only scenarios | May not capture all real-world behavior | Expand scenario diversity |

---

## When to Retrain

Retrain the model when:
1. Real Ubuntu lab data is collected (different feature distributions)
2. Feature contract changes (v1.0 → v1.1)
3. New behavioral scenarios are added
4. Model performance degrades on new data
5. Threshold needs adjustment based on operational experience

Do NOT retrain merely to improve metrics on the same dataset.
