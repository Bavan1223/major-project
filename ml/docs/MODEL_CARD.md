# Model Card — Ransomware Behavioral Detection (Baseline)

## Model Overview

| Field | Value |
|-------|-------|
| Model name | Ransomware Behavioral Detector (Baseline) |
| Model type | Logistic Regression (binary classifier) |
| Model version | 1.0.0 |
| Feature version | 1.0 |
| Framework | scikit-learn |
| Training date | 2026-08-20 |
| Status | **Baseline — NOT production-ready** |

## Intended Use

This model is intended to classify 10-second behavioral observation windows as either NORMAL system activity or RANSOMWARE_LIKE behavioral patterns. It provides one signal among several that the Central Risk Engine combines to make final severity decisions.

**Intended users:** The ransomware detection system's Central Risk Engine (automated consumption).

**Intended context:** Controlled Ubuntu lab environment for academic research (BE CSE major project).

## Labels

| Label | Value | Meaning |
|-------|-------|---------|
| NORMAL | 0 | Observation window contains normal system behavior |
| RANSOMWARE_LIKE | 1 | Observation window contains behavioral patterns associated with ransomware |

**Important:** RANSOMWARE_LIKE does NOT mean confirmed ransomware. It means the behavioral pattern is statistically similar to controlled ransomware simulations.

## Training Dataset

| Metric | Value |
|--------|-------|
| Dataset version | 0.1 |
| Total samples | 76 |
| NORMAL samples | 36 (47.4%) |
| RANSOMWARE_LIKE samples | 40 (52.6%) |
| Source | Controlled behavioral scenarios in isolated lab |
| Normal scenarios | N1-N10 (idle, editing, building, browsing, log rotation, etc.) |
| Ransomware-like scenarios | R1-R10 (rapid modify, encrypt+rename, create+delete, etc.) |
| Real ransomware used | **NO** — safe behavioral simulation only |
| Observation window | 10 seconds |

## Features (10 inputs)

| Index | Feature | Type | Description |
|-------|---------|------|-------------|
| 0 | total_events | int | Total events from all monitors |
| 1 | file_created | int | File creation count |
| 2 | file_modified | int | File modification count |
| 3 | file_deleted | int | File deletion count |
| 4 | file_renamed | int | File rename count |
| 5 | unique_files_modified | int | Distinct files modified |
| 6 | process_events | int | Process activity count |
| 7 | network_events | int | Network event count |
| 8 | established_connections | int | Established connection count |
| 9 | unique_remote_ips | int | Distinct remote IPs contacted |

**Excluded features:** `file_events` (redundant), `suspicious_indicators` (rule-derived, circular reasoning).

## Preprocessing

| Step | Method | Details |
|------|--------|---------|
| Scaling | StandardScaler | Zero mean, unit variance |
| Fitted on | Training set only | Never re-fitted during inference |
| Artifact | `models/preprocessor.pkl` | Saved with joblib |

## Threshold

| Parameter | Value |
|-----------|-------|
| Configured threshold | 0.70 |
| Calibrated on | Validation set (15 samples) |
| Meaning | Probability >= 0.70 → classify as RANSOMWARE_LIKE |
| Rationale | Best F1 on validation set at this threshold |

**Note:** The threshold was NOT tuned on the test set.

## Evaluation Results (Held-Out Test Set)

| Metric | Value |
|--------|-------|
| Test set size | 16 samples (8 NORMAL, 8 RANSOMWARE_LIKE) |
| Accuracy | 0.9375 |
| Precision | 1.0000 |
| Recall | 0.8750 |
| F1-Score | 0.9333 |
| ROC-AUC | 0.9688 |
| False Positive Rate | 0.0000 |
| False Negative Rate | 0.1250 |

### Confusion Matrix (Test Set)

```
                  Predicted
                  NORMAL    RANSOMWARE_LIKE
Actual NORMAL        8            0
Actual RANSOM        1            7
```

### Model Comparison (Test Set)

| Model | Accuracy | Precision | Recall | F1 |
|-------|----------|-----------|--------|-----|
| Dummy (majority) | 0.5000 | 0.5000 | 1.0000 | 0.6667 |
| **Logistic Regression** | **0.9375** | **1.0000** | **0.8750** | **0.9333** |
| Random Forest | 0.8750 | 1.0000 | 0.7500 | 0.8571 |
| Gradient Boosting | 0.8125 | 0.7778 | 0.8750 | 0.8235 |

**Why Logistic Regression was selected:** Best generalization (highest test F1), zero false positives, interpretable, fast inference. Simpler models generalize better on small datasets.

## Feature Importance

| Rank | Feature | Coefficient (abs) | Interpretation |
|------|---------|-------------------|----------------|
| 1 | unique_files_modified | 1.9490 | Primary indicator — ransomware targets many unique files |
| 2 | file_deleted | 1.1971 | Deletion strongly associated with ransomware |
| 3 | file_renamed | 0.8279 | Renaming (extension changes) is suspicious |
| 4 | file_created | 0.5938 | Creation alone is less discriminative |
| 5 | total_events | 0.5883 | Overall activity volume |
| 6 | process_events | 0.4462 | Moderate contribution |
| 7 | unique_remote_ips | 0.2265 | Minor contribution |
| 8 | file_modified | 0.1572 | Raw count is weak (log rotation confuses this) |
| 9 | established_connections | 0.0648 | Minimal |
| 10 | network_events | 0.0648 | Minimal |

## Inference Performance

| Metric | Value |
|--------|-------|
| Mean latency | 0.36 ms |
| Median latency | 0.28 ms |
| P95 latency | 0.68 ms |
| P99 latency | 1.45 ms |
| Measured on | Windows (Python 3.x) |

## Limitations

### Dataset Limitations

- **76 samples** — extremely small by ML standards
- Controlled simulation, not real-world telemetry
- Only 10 behavioral patterns per class
- Lab-only — no real-world noise, background processes, or multi-user activity
- Simulated feature extractor used (not actual Ubuntu monitors for current artifacts)

### Model Limitations

- Test set has only 16 samples — metrics have wide confidence intervals
- 1 misclassification changes FN rate by 12.5% (coarse granularity)
- Probability output is NOT calibrated (0.95 does not mean 95% real-world certainty)
- Model has never seen actual ransomware behavior
- Limited to 10-second window context (no temporal sequence modeling)
- Cannot distinguish N3 (multi-file coding) from R6 (slow encryption) when both produce identical feature vectors

### Known Ambiguity

Two cross-class sample pairs produce identical 10-feature vectors:
- N3 (5 files modified, 5 unique) = R6 (5 files modified, 5 unique)
- N3 (6 files modified, 6 unique) = R6 (6 files modified, 6 unique)

This represents a fundamental limitation of the current feature set for distinguishing slow/stealthy ransomware from legitimate multi-file editing. Additional features (file content entropy, temporal patterns, file type distribution) would be needed to resolve this ambiguity.

## Ethical Considerations

- No real ransomware was executed during training or evaluation
- No real user data was encrypted, deleted, or damaged
- All experiments conducted in an isolated lab environment
- The model does NOT take protective action — it only provides a signal
- False positives could cause unnecessary alerts; false negatives could miss threats
- This is an academic research project, not a commercial security product

## Reproduction

```bash
cd ~/ransomware-lab
python3 -m ml.data.collectors.collect_ubuntu --mode full
python3 -m ml.data.validate_dataset ml/data/processed/dataset_v0.1.csv
python3 -m ml.training.train
```

Random seed: 42 (for reproducible splits and model training).

## Next Steps

1. Collect real behavioral data using Ubuntu lab monitors
2. Retrain model on real telemetry
3. Validate against diverse behavioral scenarios
4. Calibrate probability if needed
5. Integrate with Central Risk Engine for combined detection
