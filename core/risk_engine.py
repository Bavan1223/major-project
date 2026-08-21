"""
Central Risk Engine — Combines rule-based and ML signals.

Severity levels:
    NORMAL   — No threat detected
    LOW      — Minor file activity
    MEDIUM   — Elevated activity or ML-only detection
    HIGH     — Rule-based ransomware-like detection
    CRITICAL — Rule HIGH + ML confident agreement

ML Integration (v2.0.0):
    - ML is advisory only, never authoritative
    - ML alone caps at MEDIUM (never CRITICAL)
    - ML unavailable = rule-only (existing behavior)
    - ML NORMAL never downgrades a rule decision
    - ML does NOT perform containment actions
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from event_logger import log_event


# =============================================================================
# ML SIGNAL INTEGRATION (v2.0.0)
# =============================================================================

def _get_ml_signal_safe(features):
    """
    Safely obtain ML behavioral classification signal.
    Returns structured dict on success, None on any failure.
    ML unavailable = rule-only behavior (existing logic unchanged).
    """
    try:
        from ml.inference.ml_signal import get_ml_signal_safe
        return get_ml_signal_safe(features)
    except Exception:
        return None


def evaluate_risk(features):
    """
    Central behavioral risk evaluation.

    Combines verified rule-based signals with ML behavioral
    classification (when available).

    Rule-based detection is unchanged and authoritative.
    ML is additive and advisory only.

    Returns:
        {
            "risk_level": str,
            "reason": str,
            "signals": list,
            "ml_signal": dict or None,
            "ml_contributed": bool
        }
    """
    signals = []

    # --------------------------------------------------
    # FILE BEHAVIOR (EXISTING — UNCHANGED)
    # --------------------------------------------------

    suspicious_indicators = features.get(
        "suspicious_indicators",
        0
    )

    unique_files_modified = features.get(
        "unique_files_modified",
        0
    )

    file_modified = features.get(
        "file_modified",
        0
    )

    # Existing verified rule-based detection signal
    if suspicious_indicators > 0:
        signals.append(
            "rapid_mass_file_modification"
        )

    # Independent observable file activity
    if unique_files_modified >= 10:
        signals.append(
            "multiple_unique_files_modified"
        )

    # --------------------------------------------------
    # CURRENT SEVERITY DECISION (EXISTING — UNCHANGED)
    # --------------------------------------------------

    # HIGH:
    # Existing verified ransomware-like rule
    if "rapid_mass_file_modification" in signals:
        risk_level = "HIGH"
        reason = (
            "Rapid mass modification of multiple "
            "unique files detected."
        )

    # MEDIUM:
    # Significant file activity without the
    # confirmed rapid-mass rule
    elif unique_files_modified >= 5:
        risk_level = "MEDIUM"
        reason = (
            "Elevated file modification activity "
            "detected."
        )

    # LOW:
    # Some file modification activity
    elif file_modified > 0:
        risk_level = "LOW"
        reason = (
            "File modification activity detected, "
            "but no high-confidence ransomware-like "
            "pattern was identified."
        )

    # NORMAL:
    else:
        risk_level = "NORMAL"
        reason = (
            "No currently implemented suspicious "
            "behavior detected."
        )

    # --------------------------------------------------
    # ML BEHAVIORAL SIGNAL (ADDITIVE — v2.0.0)
    # --------------------------------------------------
    # ML is advisory only. It cannot downgrade rule decisions.
    # ML alone caps at MEDIUM. ML + rule HIGH = CRITICAL.
    # ML failure = silent fallback to rule-only (above).

    ml_signal = _get_ml_signal_safe(features)
    ml_contributed = False

    if ml_signal is not None:
        ml_prediction = ml_signal.get("prediction")
        ml_above_threshold = ml_signal.get("above_threshold", False)

        # Rule HIGH + ML confident ransomware → CRITICAL
        if risk_level == "HIGH" and ml_prediction == 1 and ml_above_threshold:
            risk_level = "CRITICAL"
            reason = (
                "Rule-based AND ML behavioral signals both "
                "indicate ransomware-like activity."
            )
            signals.append("ml_ransomware_confirmed")
            ml_contributed = True

        # Rule NORMAL + ML confident ransomware → MEDIUM (capped)
        elif risk_level == "NORMAL" and ml_prediction == 1 and ml_above_threshold:
            risk_level = "MEDIUM"
            reason = (
                "ML behavioral model detected ransomware-like "
                "pattern (no rule-based signal)."
            )
            signals.append("ml_ransomware_detected")
            ml_contributed = True

        # Rule LOW + ML confident ransomware → MEDIUM
        elif risk_level == "LOW" and ml_prediction == 1 and ml_above_threshold:
            risk_level = "MEDIUM"
            reason = (
                "ML behavioral model detected ransomware-like "
                "pattern with minor file activity."
            )
            signals.append("ml_ransomware_detected")
            ml_contributed = True

        # Rule MEDIUM + ML confident ransomware → HIGH
        elif risk_level == "MEDIUM" and ml_prediction == 1 and ml_above_threshold:
            risk_level = "HIGH"
            reason = (
                "Elevated file activity confirmed by ML "
                "behavioral detection."
            )
            signals.append("ml_ransomware_confirmed")
            ml_contributed = True

        # All other cases: ML does NOT change severity
        # (ML NORMAL never downgrades, ML uncertain never escalates)

    return {
        "risk_level": risk_level,
        "reason": reason,
        "signals": signals,
        "ml_signal": ml_signal,
        "ml_contributed": ml_contributed,
    }


def log_risk_decision(result, features):
    """
    Publish the risk decision as a Common Event.

    The risk engine makes the decision.
    The event logger validates, collects,
    and persists the resulting Common Event.
    """
    return log_event(
        source="detection_engine",
        event_type="risk_assessment",
        indicator="risk_level_assessment",
        data={
            "risk_level": result["risk_level"],
            "reason": result["reason"],
            "signals": result["signals"],
            "features": features,
            "ml_contributed": result.get("ml_contributed", False),
        }
    )


# ------------------------------------------------------
# STANDALONE TESTS
# ------------------------------------------------------

if __name__ == "__main__":
    print("=== Central Risk Engine ===")

    test_cases = {
        "NORMAL": {
            "suspicious_indicators": 0,
            "unique_files_modified": 0,
            "file_modified": 0
        },
        "LOW": {
            "suspicious_indicators": 0,
            "unique_files_modified": 2,
            "file_modified": 2
        },
        "MEDIUM": {
            "suspicious_indicators": 0,
            "unique_files_modified": 5,
            "file_modified": 5
        },
        "HIGH": {
            "suspicious_indicators": 1,
            "unique_files_modified": 10,
            "file_modified": 10
        },
        "CRITICAL (Rule+ML)": {
            "suspicious_indicators": 1,
            "unique_files_modified": 20,
            "file_modified": 20,
            "file_created": 0,
            "file_deleted": 2,
            "file_renamed": 3,
            "total_events": 25,
            "process_events": 0,
            "network_events": 0,
            "established_connections": 0,
            "unique_remote_ips": 0,
        }
    }

    for expected, features in test_cases.items():
        result = evaluate_risk(features)
        print()
        print("Expected :", expected)
        print("Actual   :", result["risk_level"])
        print("Reason   :", result["reason"])
        print("Signals  :", result["signals"])
        if result.get("ml_signal"):
            print("ML       :", result["ml_signal"].get("label"),
                  f"(prob={result['ml_signal'].get('probability')})")

    print()
    print("CRITICAL requires rule HIGH + ML confident agreement.")
    print("ML alone caps at MEDIUM.")
    print("ML unavailable = rule-only (existing behavior).")

