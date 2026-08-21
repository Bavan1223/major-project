#!/usr/bin/env python3
"""
Ubuntu End-to-End ML Inference Validation.

This script validates the complete ML pipeline against the REAL Ubuntu lab:

    Ubuntu Monitors → Common Events → Feature Extractor → ML Prediction

It runs two controlled scenarios:
    1. Normal activity (light file editing)
    2. Ransomware-like activity (rapid file modification)

And records the ACTUAL:
    - Feature vectors from core/feature_extractor.py
    - ML predictions from the baseline model
    - Probabilities
    - Threshold decisions
    - Explainability output
    - Inference latency

PREREQUISITES:
    - Run from ~/ransomware-lab/ on the Ubuntu lab machine
    - ml/ directory present with trained model artifacts
    - core/feature_extractor.py accessible
    - ~/ransomware-lab/test-files/ directory exists
    - scikit-learn, numpy, joblib installed

USAGE:
    cd ~/ransomware-lab
    python3 -m ml.tests.e2e_ubuntu_validation

SAFETY:
    - All file operations restricted to ~/ransomware-lab/test-files/
    - No real ransomware
    - No real encryption
    - No destructive operations outside test directory

OUTPUT:
    Prints full validation report to stdout.
    Saves JSON report to ml/tests/e2e_report.json
"""

import os
import sys
import time
import json
import uuid
import platform
from datetime import datetime, timezone

# =============================================================================
# PATH SETUP
# =============================================================================

PROJECT_ROOT = os.path.expanduser("~/ransomware-lab")
if not os.path.isdir(PROJECT_ROOT):
    # Fallback for running from within the ml model workspace
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =============================================================================
# IMPORTS
# =============================================================================

try:
    from core.feature_extractor import extract_features
    CORE_EXTRACTOR_AVAILABLE = True
except ImportError:
    CORE_EXTRACTOR_AVAILABLE = False
    # Fallback to simulated extractor for local testing
    from ml.tests.test_feature_extractor_compatibility import simulated_extract_features as extract_features

from ml.config import ML_FEATURE_COLUMNS, FEATURE_VERSION, WINDOW_SECONDS
from ml.inference.predictor import RansomwarePredictor
from ml.inference.integration import MLIntegration, get_ml_prediction

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET_DIR = os.path.join(PROJECT_ROOT, "test-files")
REPORT_PATH = os.path.join(PROJECT_ROOT, "ml", "tests", "e2e_report.json")


# =============================================================================
# SCENARIO EXECUTION (generates real Common Events)
# =============================================================================

def generate_normal_events():
    """
    Scenario: Normal light file editing.
    Creates 3 files and modifies 2 of them with natural timing.
    Returns list of Common Events.
    """
    events = []
    os.makedirs(TARGET_DIR, exist_ok=True)

    # Create 3 test files
    files = []
    for i in range(3):
        filepath = os.path.join(TARGET_DIR, f"normal_test_{uuid.uuid4().hex[:8]}.txt")
        with open(filepath, "w") as f:
            f.write(f"Normal test file {i}\n")
        files.append(filepath)
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "file_monitor",
            "event_type": "file_created",
            "pid": os.getpid(),
            "process": "python3",
            "indicator": "file_creation",
            "data": {"path": filepath},
        })
        time.sleep(0.5)

    # Modify 2 files (light editing)
    for filepath in files[:2]:
        time.sleep(1.0)  # Natural pause between edits
        with open(filepath, "a") as f:
            f.write(f"Edit at {datetime.now().isoformat()}\n")
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "file_monitor",
            "event_type": "file_modified",
            "pid": os.getpid(),
            "process": "python3",
            "indicator": "file_modification",
            "data": {"path": filepath},
        })

    # Cleanup
    for f in files:
        if os.path.exists(f):
            os.remove(f)

    return events


def generate_ransomware_like_events():
    """
    Scenario: Ransomware-like rapid file modification.
    Creates 15 files and rapidly modifies all of them (simulates encryption).
    Returns list of Common Events.
    """
    events = []
    os.makedirs(TARGET_DIR, exist_ok=True)

    # Create target files
    files = []
    for i in range(15):
        filepath = os.path.join(TARGET_DIR, f"victim_{uuid.uuid4().hex[:8]}.txt")
        with open(filepath, "w") as f:
            f.write(f"Important document {i}\n" * 10)
        files.append(filepath)

    # Small pause to separate creation from modification
    time.sleep(0.2)

    # Rapidly modify all files (simulate encryption)
    for filepath in files:
        with open(filepath, "wb") as f:
            f.write(os.urandom(128))  # Write random bytes
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "file_monitor",
            "event_type": "file_modified",
            "pid": os.getpid(),
            "process": "python3",
            "indicator": "file_modification",
            "data": {"path": filepath},
        })
        time.sleep(0.05)  # Very short delay (rapid)

    # Cleanup
    for f in files:
        if os.path.exists(f):
            os.remove(f)

    return events


# =============================================================================
# VALIDATION PIPELINE
# =============================================================================

def run_e2e_scenario(scenario_name, event_generator, expected_label):
    """
    Run one E2E validation scenario.
    
    Pipeline:
        event_generator() → events
        extract_features(events) → 12-feature dict
        get_ml_prediction(features) → structured result
    
    Returns:
        dict with full validation results
    """
    print(f"\n  --- Scenario: {scenario_name} ---")
    print(f"  Expected: {'NORMAL' if expected_label == 0 else 'RANSOMWARE_LIKE'}")

    # Step 1: Generate events
    print("  [1] Generating events...")
    start_total = time.perf_counter()
    events = event_generator()
    event_time_ms = (time.perf_counter() - start_total) * 1000
    print(f"      Events generated: {len(events)}")

    # Step 2: Extract features using REAL core extractor
    print("  [2] Extracting features (core/feature_extractor.py)...")
    start_extract = time.perf_counter()
    full_features = extract_features(events)
    extract_time_ms = (time.perf_counter() - start_extract) * 1000
    print(f"      Features extracted: {len(full_features)} keys")
    print(f"      Extractor: {'REAL core/feature_extractor.py' if CORE_EXTRACTOR_AVAILABLE else 'SIMULATED (local testing)'}")

    # Step 3: Run ML prediction via integration adapter
    print("  [3] Running ML inference (integration adapter)...")
    start_infer = time.perf_counter()
    ml_result = get_ml_prediction(full_features)
    infer_time_ms = (time.perf_counter() - start_infer) * 1000

    total_time_ms = (time.perf_counter() - start_total) * 1000

    # Step 4: Display results
    print(f"\n  RESULTS:")
    print(f"    Status:        {ml_result.get('status', 'N/A')}")
    print(f"    Prediction:    {ml_result.get('prediction', 'N/A')}")
    print(f"    Label:         {ml_result.get('label', 'N/A')}")
    print(f"    Probability:   {ml_result.get('probability', 'N/A')}")
    print(f"    Above threshold: {ml_result.get('above_threshold', 'N/A')}")
    print(f"    Threshold:     {ml_result.get('threshold', 'N/A')}")
    print(f"    Model version: {ml_result.get('model_version', 'N/A')}")
    print(f"    Feature ver:   {ml_result.get('feature_version', 'N/A')}")

    if ml_result.get("important_features"):
        print(f"\n    Top contributing features:")
        for feat in ml_result["important_features"][:5]:
            direction = "+" if feat["direction"] == "ransomware" else "-"
            print(f"      {direction} {feat['feature']:<25} val={feat['value']:>3}  contrib={feat['contribution']:>7.4f}")

    print(f"\n    Timing:")
    print(f"      Event generation:   {event_time_ms:.2f} ms")
    print(f"      Feature extraction: {extract_time_ms:.4f} ms")
    print(f"      ML inference:       {infer_time_ms:.4f} ms")
    print(f"      Total pipeline:     {total_time_ms:.2f} ms")

    # Step 5: Validate correctness
    correct = ml_result.get("prediction") == expected_label
    print(f"\n    Expected label: {expected_label} ({'NORMAL' if expected_label == 0 else 'RANSOMWARE_LIKE'})")
    print(f"    Actual label:   {ml_result.get('prediction')} ({ml_result.get('label')})")
    print(f"    CORRECT:        {'YES' if correct else 'NO'}")

    # Build report
    report = {
        "scenario": scenario_name,
        "expected_label": expected_label,
        "expected_label_name": "NORMAL" if expected_label == 0 else "RANSOMWARE_LIKE",
        "event_count": len(events),
        "full_features": full_features,
        "ml_features_used": {col: full_features.get(col) for col in ML_FEATURE_COLUMNS},
        "excluded_features": {
            "file_events": full_features.get("file_events"),
            "suspicious_indicators": full_features.get("suspicious_indicators"),
        },
        "ml_result": ml_result,
        "correct_prediction": correct,
        "timing": {
            "event_generation_ms": round(event_time_ms, 2),
            "feature_extraction_ms": round(extract_time_ms, 4),
            "ml_inference_ms": round(infer_time_ms, 4),
            "total_pipeline_ms": round(total_time_ms, 2),
        },
        "extractor_type": "real" if CORE_EXTRACTOR_AVAILABLE else "simulated",
    }

    return report


# =============================================================================
# MAIN VALIDATION
# =============================================================================

def main():
    print("=" * 70)
    print("  UBUNTU END-TO-END ML INFERENCE VALIDATION")
    print("=" * 70)
    print(f"\n  Environment:")
    print(f"    Platform:       {platform.system()} {platform.release()}")
    print(f"    Python:         {platform.python_version()}")
    print(f"    Project root:   {PROJECT_ROOT}")
    print(f"    Target dir:     {TARGET_DIR}")
    print(f"    Core extractor: {'AVAILABLE' if CORE_EXTRACTOR_AVAILABLE else 'NOT AVAILABLE (using simulated)'}")
    print(f"    Feature ver:    {FEATURE_VERSION}")
    print(f"    Window:         {WINDOW_SECONDS}s")
    print(f"    Timestamp:      {datetime.now(timezone.utc).isoformat()}")

    # Verify model is loadable
    print(f"\n  Loading ML model...")
    try:
        predictor = RansomwarePredictor()
        print(f"    Model loaded:   {predictor.model_version}")
        print(f"    Threshold:      {predictor.threshold}")
        print(f"    Algorithm:      {type(predictor.model).__name__}")
    except Exception as e:
        print(f"    ERROR: Could not load model: {e}")
        print(f"    VALIDATION CANNOT PROCEED")
        sys.exit(1)

    # Run scenarios
    scenarios = [
        ("Normal: Light file editing", generate_normal_events, 0),
        ("Ransomware-like: Rapid file modification", generate_ransomware_like_events, 1),
    ]

    reports = []
    for name, generator, expected in scenarios:
        report = run_e2e_scenario(name, generator, expected)
        reports.append(report)

    # ==========================================================================
    # INFERENCE LATENCY MEASUREMENT (dedicated)
    # ==========================================================================
    print(f"\n\n  --- Inference Latency Measurement ---")
    print(f"  (Repeated inference on same feature vector, 100 iterations)")

    # Use a representative feature vector
    test_features = {
        "total_events": 10,
        "file_events": 8,
        "file_created": 1,
        "file_modified": 5,
        "file_deleted": 1,
        "file_renamed": 1,
        "unique_files_modified": 5,
        "process_events": 1,
        "network_events": 1,
        "established_connections": 1,
        "unique_remote_ips": 1,
        "suspicious_indicators": 0,
    }

    # Warm up
    for _ in range(10):
        get_ml_prediction(test_features)

    # Measure
    latencies = []
    for _ in range(100):
        start = time.perf_counter()
        get_ml_prediction(test_features)
        latencies.append((time.perf_counter() - start) * 1000)

    latencies.sort()
    latency_stats = {
        "iterations": 100,
        "mean_ms": round(sum(latencies) / len(latencies), 4),
        "median_ms": round(latencies[50], 4),
        "min_ms": round(latencies[0], 4),
        "max_ms": round(latencies[-1], 4),
        "p95_ms": round(latencies[94], 4),
        "p99_ms": round(latencies[98], 4),
    }

    print(f"    Mean:   {latency_stats['mean_ms']:.4f} ms")
    print(f"    Median: {latency_stats['median_ms']:.4f} ms")
    print(f"    Min:    {latency_stats['min_ms']:.4f} ms")
    print(f"    Max:    {latency_stats['max_ms']:.4f} ms")
    print(f"    P95:    {latency_stats['p95_ms']:.4f} ms")
    print(f"    P99:    {latency_stats['p99_ms']:.4f} ms")

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    all_correct = all(r["correct_prediction"] for r in reports)

    print(f"\n\n{'='*70}")
    print(f"  E2E VALIDATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Scenarios tested:  {len(reports)}")
    print(f"  All correct:       {'YES' if all_correct else 'NO'}")
    print(f"  Core extractor:    {'REAL' if CORE_EXTRACTOR_AVAILABLE else 'SIMULATED'}")
    for r in reports:
        status = "PASS" if r["correct_prediction"] else "FAIL"
        print(f"    [{status}] {r['scenario']}: "
              f"prob={r['ml_result'].get('probability', 'N/A')} "
              f"→ {r['ml_result'].get('label', 'N/A')}")
    print(f"\n  Inference latency: {latency_stats['mean_ms']:.4f} ms (mean)")
    print(f"  Pipeline verdict:  {'COMPATIBLE' if all_correct else 'ISSUES DETECTED'}")
    print(f"{'='*70}")

    # ==========================================================================
    # SAVE REPORT
    # ==========================================================================
    full_report = {
        "validation_type": "e2e_ubuntu",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "project_root": PROJECT_ROOT,
            "core_extractor_available": CORE_EXTRACTOR_AVAILABLE,
            "feature_version": FEATURE_VERSION,
            "model_version": predictor.model_version,
            "threshold": predictor.threshold,
        },
        "scenarios": reports,
        "latency": latency_stats,
        "overall_result": "PASS" if all_correct else "FAIL",
        "notes": [
            "This is baseline validation, not production certification",
            "Model trained on 76-sample controlled dataset",
            f"Core extractor: {'REAL' if CORE_EXTRACTOR_AVAILABLE else 'SIMULATED — re-run on Ubuntu for real validation'}",
        ],
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(full_report, f, indent=2, default=str)
    print(f"\n  Report saved: {REPORT_PATH}")

    return all_correct


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
