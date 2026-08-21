# Decision: Exclusion of `suspicious_indicators` from ML Feature Set

**Decision:** EXCLUDE from ML training and inference features  
**Status:** APPROVED (pending confirmation of implementation details from lab inspection)  
**Date:** 2026-08-20  
**Feature Version:** 1.0  

---

## 1. What is `suspicious_indicators`?

`suspicious_indicators` is a feature produced by `core/feature_extractor.py` that counts
the number of suspicious behavioral indicators detected within an observation window.

Based on the project documentation, the current rule-based detection logic is:

```
10 unique modified files within 10 seconds → HIGH-risk suspicious file activity
```

This rule is implemented in `detection_engine.py` and/or the feature extractor itself.
The `suspicious_indicators` count reflects how many such rule triggers occurred.

---

## 2. Why It Must Be Excluded from ML

### The Circular Reasoning Problem

If `suspicious_indicators` is included as an ML input feature, the following loop occurs:

```
Rule-based engine detects suspicious pattern
        ↓
suspicious_indicators = 1 (or higher)
        ↓
ML model receives suspicious_indicators as input
        ↓
ML model learns: "if suspicious_indicators > 0, predict RANSOMWARE_LIKE"
        ↓
ML prediction adds no value beyond the existing rule
```

This defeats the entire purpose of adding ML to the system.

### What We Want Instead

The ML model should independently detect ransomware-like behavior from raw behavioral
features (file counts, process counts, network counts, etc.) WITHOUT being told by the
rule engine that something is already suspicious.

The value proposition of ML in this architecture is:

1. **Detect patterns the rules miss** — subtle combinations of features that don't
   trigger the 10-file/10-second rule but are still ransomware-like
2. **Reduce false positives** — cases where the rule fires but behavior is legitimate
   (e.g., a build tool creating many files)
3. **Generalize** — recognize new ransomware-like patterns without manually writing
   new rules for each one

None of these goals are achievable if the ML model simply learns to copy the rule output.

### Scientific Validity

In a viva examination, using a rule-derived feature as ML input would be challenged as:

- **Data leakage**: The label (RANSOMWARE_LIKE) and the feature (suspicious_indicators)
  are both derived from the same underlying behavioral pattern. The feature encodes
  information that is definitionally correlated with the label.
- **No independent contribution**: The ML model cannot demonstrate value beyond
  the rule system if it depends on the rule system's output as input.
- **Inflated metrics**: Accuracy/precision/recall would appear artificially high
  because the model is essentially reading the answer from its input.

---

## 3. What Happens to `suspicious_indicators` in the Architecture

It is NOT deleted or removed from the project. It continues to serve its role:

```
Feature Extractor produces all 12 features
        ↓
ML Module selects 10 features (excludes file_events, suspicious_indicators)
        ↓
ML produces independent prediction
        ↓
Central Risk Engine receives:
    - ML signal (independent)
    - Rule signal (includes suspicious_indicators logic)
    - Other signals
        ↓
Central Risk Engine makes final severity decision
```

The `suspicious_indicators` value remains available to the **Central Risk Engine**
as a rule-based signal. It is simply not fed into the ML model.

This preserves the architectural separation:
- Rules detect what rules are designed for
- ML detects what ML can learn independently
- The Risk Engine combines both for a stronger final decision

---

## 4. Verification Required

**ACTION NEEDED:** When working on the Ubuntu lab machine, inspect `core/feature_extractor.py`
to confirm:

1. How exactly `suspicious_indicators` is calculated
2. Whether it depends on `detection_engine.py` output
3. Whether it is a count of rule triggers or something else
4. Whether there are any other hidden dependencies between features and rules

If inspection reveals that `suspicious_indicators` is calculated from something
other than rule-based detection (e.g., it counts specific event types like
"indicator": "suspicious" from raw monitor events), then this decision may need
to be revisited.

**Current assumption:** It is derived from or equivalent to rule-based detection logic.

---

## 5. Impact on Model Performance

Excluding this feature means:
- The ML model has fewer features to work with (10 instead of 11 usable)
- The model must learn to detect patterns from raw behavioral counts alone
- Initial accuracy may be lower than a model that includes the rule-derived feature

This is acceptable because:
- The model's value is in what it can detect BEYOND rules
- A model that only copies rules provides zero additional capability
- The combined Rule + ML system can still achieve high overall detection

---

## 6. Summary

| Aspect | Decision |
|--------|----------|
| Feature name | `suspicious_indicators` |
| Produced by | `core/feature_extractor.py` |
| Available at inference | Yes (produced by existing pipeline) |
| Used by ML model | **NO** |
| Reason | Circular reasoning / data leakage from rule engine |
| Where it IS used | Central Risk Engine (as independent rule signal) |
| Reversible | Yes — if investigation shows it is NOT rule-derived |
| Feature version affected | 1.0 (excluded from v1.0 feature set) |
