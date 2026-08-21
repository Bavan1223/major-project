# Inference Specification

## Overview

This document specifies the exact input and output schemas for the ML inference module. Any system integrating with the ML predictor must conform to this specification.

**Model version:** 1.0.0  
**Feature version:** 1.0  
**Status:** Baseline (not production-ready)

---

## Interfaces

The ML module provides two interfaces:

1. **Direct Predictor** (`ml.inference.predictor.RansomwarePredictor`) — accepts 10-feature input
2. **Integration Adapter** (`ml.inference.integration.get_ml_prediction`) — accepts 12-feature extractor output

---

## Interface 1: Direct Predictor

### Import

```python
from ml.inference.predictor import RansomwarePredictor
predictor = RansomwarePredictor()
```

### Input Schema

A Python `dict` with exactly these 10 keys:

```python
{
    "total_events": int,            # >= 0
    "file_created": int,            # >= 0
    "file_modified": int,           # >= 0
    "file_deleted": int,            # >= 0
    "file_renamed": int,            # >= 0
    "unique_files_modified": int,   # >= 0
    "process_events": int,          # >= 0
    "network_events": int,          # >= 0
    "established_connections": int,  # >= 0
    "unique_remote_ips": int,       # >= 0
}
```

Alternatively, a list or numpy array of 10 values in the exact order above.

### Input Validation Rules

| Rule | Behavior on Violation |
|------|----------------------|
| All 10 features present | Raises `FeatureValidationError` with list of missing features |
| All values numeric | Raises `FeatureValidationError` identifying the non-numeric field |
| All values >= 0 | Raises `FeatureValidationError` identifying the negative field |
| No None values | Raises `FeatureValidationError` identifying the None field |
| Exactly 10 features (if list) | Raises `FeatureValidationError` showing expected vs actual count |
| Extra keys in dict | Silently ignored (safe for forward compatibility) |

### Output Schema

```python
{
    "prediction": int,           # 0 = NORMAL, 1 = RANSOMWARE_LIKE
    "label": str,                # "NORMAL" or "RANSOMWARE_LIKE"
    "probability": float,        # 0.0 to 1.0 — model score for RANSOMWARE_LIKE class
    "above_threshold": bool,     # probability >= threshold
    "threshold": float,          # Configured decision threshold (currently 0.70)
    "model_version": str,        # "1.0.0"
    "feature_version": str,      # "1.0"
    "important_features": list,  # Top 5 contributing features (see below)
    "inference_time_ms": float,  # Time taken for this prediction in milliseconds
}
```

### Important Features Schema (Explainability)

Each element in `important_features`:

```python
{
    "feature": str,         # Feature name (e.g., "unique_files_modified")
    "value": int,           # Raw input value for this feature
    "contribution": float,  # Signed contribution to prediction
    "direction": str,       # "ransomware" (positive contribution) or "normal" (negative)
}
```

Sorted by absolute contribution (highest impact first). Maximum 5 entries.

### Error Handling

On validation failure, raises:
- `FeatureValidationError` — input features are invalid
- `ModelNotLoadedError` — model artifacts not loaded

Both inherit from `PredictorError`.

---

## Interface 2: Integration Adapter

### Import

```python
from ml.inference.integration import get_ml_prediction
# or
from ml.inference.integration import MLIntegration
```

### Input Schema

The 12-feature dict produced by `core/feature_extractor.extract_features()`:

```python
{
    "total_events": int,
    "file_events": int,              # EXCLUDED — not passed to ML
    "file_created": int,
    "file_modified": int,
    "file_deleted": int,
    "file_renamed": int,
    "unique_files_modified": int,
    "process_events": int,
    "network_events": int,
    "established_connections": int,
    "unique_remote_ips": int,
    "suspicious_indicators": int,    # EXCLUDED — not passed to ML
}
```

The adapter automatically:
1. Selects the 10 ML features
2. Discards `file_events` and `suspicious_indicators`
3. Passes the 10 features to the predictor

### Output Schema (Success)

```python
{
    "status": "success",
    "prediction": int,
    "label": str,
    "probability": float,
    "above_threshold": bool,
    "threshold": float,
    "model_version": str,
    "feature_version": str,
    "important_features": list,
    "inference_time_ms": float,
}
```

### Output Schema (Error)

```python
{
    "status": "error",
    "error_type": str,       # "feature_validation", "model_not_loaded", or "unexpected"
    "error_message": str,    # Human-readable description
    "prediction": None,
    "label": None,
    "probability": None,
}
```

The integration adapter never raises exceptions — it catches all errors and returns structured error responses.

---

## Probability Interpretation

| Probability Range | Interpretation |
|-------------------|---------------|
| 0.00 - 0.30 | Strongly suggests NORMAL behavior |
| 0.30 - 0.50 | Likely NORMAL, some uncertainty |
| 0.50 - 0.70 | Ambiguous / borderline (below threshold) |
| 0.70 - 0.90 | Above threshold — classified as RANSOMWARE_LIKE |
| 0.90 - 1.00 | High confidence RANSOMWARE_LIKE |

**WARNING:** These probabilities are NOT calibrated. A score of 0.95 does not mean a 95% real-world probability of ransomware. It is a model score reflecting learned pattern similarity.

---

## Threshold Behavior

- Default threshold: **0.70**
- If `probability >= threshold` → `above_threshold = True`
- The `prediction` field uses the model's default 0.5 decision boundary
- The `above_threshold` field applies the calibrated 0.70 threshold
- The Central Risk Engine should use `above_threshold` and `probability` together

### Example: Threshold Effects

| Probability | prediction | above_threshold | Interpretation |
|-------------|-----------|-----------------|----------------|
| 0.16 | 0 (NORMAL) | False | Clearly normal |
| 0.49 | 0 (NORMAL) | False | Borderline, classified as normal |
| 0.65 | 1 (RANSOMWARE_LIKE) | False | Model says ransomware but below threshold |
| 0.85 | 1 (RANSOMWARE_LIKE) | True | Confident ransomware detection |
| 0.99 | 1 (RANSOMWARE_LIKE) | True | Very confident ransomware detection |

---

## Integration with Central Risk Engine

The ML result should be consumed as ONE signal among many:

```
Rule signals ──────────────┐
ML signal ─────────────────┤→ Central Risk Engine → Final Severity
Process/honeypot signals ──┘
```

The ML module does NOT decide final severity. The recommended integration pattern:

```python
from core.feature_extractor import extract_features
from ml.inference.integration import get_ml_prediction

# During each observation window:
features = extract_features(window_events)
ml_result = get_ml_prediction(features)

# Pass to risk engine:
risk_engine.evaluate(
    rule_signals=...,
    ml_signal=ml_result,
    process_signals=...,
    network_signals=...,
)
```

---

## Model Loading

The predictor loads artifacts from `ml/models/`:
- `ransomware_model.pkl` — trained LogisticRegression (joblib)
- `preprocessor.pkl` — fitted StandardScaler (joblib)
- `model_metadata.json` — version, params, metrics

Loading happens once at initialization. The model is NOT retrained during inference.

---

## Thread Safety

The predictor is stateless after loading (no mutable state during predict). Multiple threads can call `predict()` concurrently on the same instance without data races, provided no thread calls `load()` while others are predicting.

---

## Performance Characteristics

| Metric | Value | Measured On |
|--------|-------|-------------|
| Mean inference | 0.36 ms | Windows, Python 3.x |
| Median inference | 0.28 ms | Windows, Python 3.x |
| P99 inference | 1.45 ms | Windows, Python 3.x |
| Model load time | ~50 ms | One-time at startup |
| Memory | ~5 MB | Model + preprocessor + numpy |
