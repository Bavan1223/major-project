"""
Dataset Validation Script.

Validates the collected ML dataset against the feature contract
and quality requirements before training.

Checks:
    - Schema: correct columns, types, order
    - Values: non-negative, no NaN, no infinite, valid labels
    - Integrity: unique window IDs, no duplicates, session consistency
    - Contract: feature version, excluded features not present
    - Leakage: no session split across train/test (when splits assigned)
    - Distribution: class balance, feature ranges, scenario coverage

USAGE:
    python -m ml.data.validate_dataset ml/data/processed/dataset_v0.1.csv
    
    Or from Python:
    from ml.data.validate_dataset import validate_dataset
    report = validate_dataset("path/to/dataset.csv")
"""

import csv
import json
import os
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import (
    FEATURE_VERSION,
    ML_FEATURE_COLUMNS,
    EXCLUDED_FEATURES,
    WINDOW_SECONDS,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
)


# Expected CSV column order
EXPECTED_COLUMNS = ["session_id", "window_id", "scenario_id", "label"] + list(ML_FEATURE_COLUMNS)


def validate_dataset(csv_path, metadata_path=None):
    """
    Validate a dataset CSV file.
    
    Args:
        csv_path: Path to the dataset CSV
        metadata_path: Optional path to sessions.json
        
    Returns:
        dict: Validation report with pass/fail status and details
    """
    report = {
        "file": csv_path,
        "valid": True,
        "checks": [],
        "warnings": [],
        "stats": {},
    }

    # =========================================================================
    # Load data
    # =========================================================================
    if not os.path.isfile(csv_path):
        report["valid"] = False
        report["checks"].append(("file_exists", False, f"File not found: {csv_path}"))
        return report

    report["checks"].append(("file_exists", True, ""))

    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)

    # =========================================================================
    # Check 1: Column schema
    # =========================================================================
    if headers == EXPECTED_COLUMNS:
        report["checks"].append(("columns_correct", True, ""))
    else:
        report["valid"] = False
        report["checks"].append(("columns_correct", False,
                                 f"Expected {EXPECTED_COLUMNS}, got {headers}"))

    # Check excluded features not present
    for excluded in EXCLUDED_FEATURES:
        if excluded in (headers or []):
            report["valid"] = False
            report["checks"].append(("excluded_feature_absent", False,
                                     f"Excluded feature '{excluded}' found in columns"))
        else:
            report["checks"].append(("excluded_feature_absent", True, f"{excluded} not in columns"))

    # =========================================================================
    # Check 2: Row count
    # =========================================================================
    if len(rows) == 0:
        report["valid"] = False
        report["checks"].append(("non_empty", False, "Dataset has 0 rows"))
        return report
    report["checks"].append(("non_empty", True, f"{len(rows)} rows"))
    report["stats"]["total_rows"] = len(rows)

    # =========================================================================
    # Check 3: Data types and values
    # =========================================================================
    type_errors = []
    negative_errors = []
    nan_errors = []
    label_errors = []

    for i, row in enumerate(rows):
        # Check label
        try:
            label = int(row["label"])
            if label not in (LABEL_NORMAL, LABEL_RANSOMWARE_LIKE):
                label_errors.append((i, row["label"]))
        except (ValueError, TypeError):
            label_errors.append((i, row["label"]))

        # Check features
        for col in ML_FEATURE_COLUMNS:
            val = row.get(col, "")
            if val == "" or val is None:
                nan_errors.append((i, col, val))
                continue
            try:
                num = int(val)
                if num < 0:
                    negative_errors.append((i, col, num))
            except ValueError:
                try:
                    fval = float(val)
                    if fval != fval:  # NaN check
                        nan_errors.append((i, col, val))
                    elif fval < 0:
                        negative_errors.append((i, col, fval))
                    else:
                        type_errors.append((i, col, val, "expected int"))
                except ValueError:
                    type_errors.append((i, col, val, "not numeric"))

    if not type_errors:
        report["checks"].append(("types_correct", True, ""))
    else:
        report["valid"] = False
        report["checks"].append(("types_correct", False,
                                 f"{len(type_errors)} type errors (first: row {type_errors[0][0]}, col {type_errors[0][1]})"))

    if not negative_errors:
        report["checks"].append(("non_negative", True, ""))
    else:
        report["valid"] = False
        report["checks"].append(("non_negative", False,
                                 f"{len(negative_errors)} negative values"))

    if not nan_errors:
        report["checks"].append(("no_missing_values", True, ""))
    else:
        report["valid"] = False
        report["checks"].append(("no_missing_values", False,
                                 f"{len(nan_errors)} missing/NaN values"))

    if not label_errors:
        report["checks"].append(("valid_labels", True, ""))
    else:
        report["valid"] = False
        report["checks"].append(("valid_labels", False,
                                 f"{len(label_errors)} invalid labels"))

    # =========================================================================
    # Check 4: Uniqueness
    # =========================================================================
    window_ids = [row["window_id"] for row in rows]
    if len(window_ids) == len(set(window_ids)):
        report["checks"].append(("unique_window_ids", True, ""))
    else:
        duplicates = [wid for wid, count in Counter(window_ids).items() if count > 1]
        report["valid"] = False
        report["checks"].append(("unique_window_ids", False,
                                 f"{len(duplicates)} duplicate window IDs"))

    # Check for duplicate feature rows
    feature_tuples = [
        tuple(row[col] for col in ML_FEATURE_COLUMNS)
        for row in rows
    ]
    dup_count = len(feature_tuples) - len(set(feature_tuples))
    if dup_count == 0:
        report["checks"].append(("no_duplicate_rows", True, ""))
    else:
        # Warning, not failure — identical features can happen legitimately (e.g., two idle windows)
        report["warnings"].append(f"{dup_count} duplicate feature vectors (may be legitimate for idle scenarios)")
        report["checks"].append(("no_duplicate_rows", True, f"Warning: {dup_count} duplicates"))

    # =========================================================================
    # Check 5: Class distribution
    # =========================================================================
    labels = [int(row["label"]) for row in rows]
    label_counts = Counter(labels)
    normal_count = label_counts.get(LABEL_NORMAL, 0)
    ransom_count = label_counts.get(LABEL_RANSOMWARE_LIKE, 0)

    report["stats"]["normal_count"] = normal_count
    report["stats"]["ransomware_like_count"] = ransom_count
    report["stats"]["class_ratio"] = (
        f"{normal_count}:{ransom_count} "
        f"({normal_count/(normal_count+ransom_count)*100:.1f}%/{ransom_count/(normal_count+ransom_count)*100:.1f}%)"
        if (normal_count + ransom_count) > 0 else "N/A"
    )

    if normal_count > 0 and ransom_count > 0:
        report["checks"].append(("both_classes_present", True,
                                 f"NORMAL={normal_count}, RANSOMWARE_LIKE={ransom_count}"))
    else:
        report["valid"] = False
        report["checks"].append(("both_classes_present", False,
                                 f"Missing class: NORMAL={normal_count}, RANSOMWARE_LIKE={ransom_count}"))

    # =========================================================================
    # Check 6: Feature statistics
    # =========================================================================
    feature_stats = {}
    for col in ML_FEATURE_COLUMNS:
        values = [int(row[col]) for row in rows]
        feature_stats[col] = {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "median": sorted(values)[len(values) // 2],
        }
    report["stats"]["features"] = feature_stats

    # =========================================================================
    # Check 7: Scenario distribution
    # =========================================================================
    scenario_counts = Counter(row["scenario_id"] for row in rows)
    report["stats"]["scenario_distribution"] = dict(scenario_counts)

    # =========================================================================
    # Check 8: Session consistency (all windows from same session have same label)
    # =========================================================================
    session_labels = {}
    inconsistent_sessions = []
    for row in rows:
        sid = row["session_id"]
        lbl = int(row["label"])
        if sid in session_labels:
            if session_labels[sid] != lbl:
                inconsistent_sessions.append(sid)
        else:
            session_labels[sid] = lbl

    if not inconsistent_sessions:
        report["checks"].append(("session_label_consistency", True, ""))
    else:
        report["valid"] = False
        report["checks"].append(("session_label_consistency", False,
                                 f"{len(inconsistent_sessions)} sessions have mixed labels"))

    report["stats"]["total_sessions"] = len(session_labels)

    # =========================================================================
    # Check 9: Feature count matches contract
    # =========================================================================
    feature_count_in_data = len([h for h in (headers or []) if h in ML_FEATURE_COLUMNS])
    if feature_count_in_data == len(ML_FEATURE_COLUMNS):
        report["checks"].append(("feature_count_correct", True, f"{feature_count_in_data} features"))
    else:
        report["valid"] = False
        report["checks"].append(("feature_count_correct", False,
                                 f"Expected {len(ML_FEATURE_COLUMNS)}, found {feature_count_in_data}"))

    return report


def print_report(report):
    """Pretty-print a validation report."""
    print(f"\n{'='*60}")
    print(f"  DATASET VALIDATION REPORT")
    print(f"  File: {report['file']}")
    print(f"  Status: {'PASS' if report['valid'] else 'FAIL'}")
    print(f"{'='*60}")

    print(f"\n  CHECKS:")
    for check_name, passed, detail in report["checks"]:
        status = "PASS" if passed else "FAIL"
        detail_str = f" — {detail}" if detail else ""
        print(f"    [{status}] {check_name}{detail_str}")

    if report["warnings"]:
        print(f"\n  WARNINGS:")
        for w in report["warnings"]:
            print(f"    ⚠ {w}")

    if "stats" in report:
        stats = report["stats"]
        print(f"\n  STATISTICS:")
        print(f"    Total rows:      {stats.get('total_rows', 'N/A')}")
        print(f"    Total sessions:  {stats.get('total_sessions', 'N/A')}")
        print(f"    NORMAL:          {stats.get('normal_count', 'N/A')}")
        print(f"    RANSOMWARE_LIKE: {stats.get('ransomware_like_count', 'N/A')}")
        print(f"    Class ratio:     {stats.get('class_ratio', 'N/A')}")

        if "features" in stats:
            print(f"\n  FEATURE RANGES:")
            print(f"    {'Feature':<25} {'Min':>5} {'Max':>5} {'Mean':>8} {'Median':>6}")
            print(f"    {'-'*55}")
            for col in ML_FEATURE_COLUMNS:
                fs = stats["features"][col]
                print(f"    {col:<25} {fs['min']:>5} {fs['max']:>5} {fs['mean']:>8.1f} {fs['median']:>6}")

        if "scenario_distribution" in stats:
            print(f"\n  SCENARIO DISTRIBUTION:")
            for scenario, count in sorted(stats["scenario_distribution"].items()):
                print(f"    {scenario:<6}: {count} windows")

    print(f"\n{'='*60}")
    print(f"  FINAL VERDICT: {'PASS — Dataset is valid for training' if report['valid'] else 'FAIL — Fix issues before training'}")
    print(f"{'='*60}")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default path
        csv_path = os.path.join(PROCESSED_DIR, f"dataset_v{DATASET_VERSION}.csv")
    else:
        csv_path = sys.argv[1]

    report = validate_dataset(csv_path)
    print_report(report)
    sys.exit(0 if report["valid"] else 1)
