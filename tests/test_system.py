"""
Automated Test Suite — Ransomware Defense System

Tests:
    1. Risk engine levels and signals
    2. ML integration
    3. Incident creation and lifecycle
    4. Incident deduplication
    5. Stale incident timeout
    6. Orphan incident auto-resolve
    7. Canary system
    8. Feature extraction
    9. Recovery (snapshot + restore)
    10. API consistency (risk state agreement)
    11. False-positive resistance

Run:
    cd ~/ransomware-lab
    source .venv/bin/activate
    python3 -m pytest tests/test_system.py -v
    OR
    python3 tests/test_system.py
"""

import os
import sys
import json
import shutil
import hashlib
from datetime import datetime, timedelta

# Project path setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ==============================================================
# TEST UTILITIES
# ==============================================================

def clean_state():
    """Reset state files for clean testing."""
    events_file = os.path.join(PROJECT_ROOT, "logs", "events.jsonl")
    incidents_file = os.path.join(PROJECT_ROOT, "logs", "incidents.json")
    audit_file = os.path.join(PROJECT_ROOT, "logs", "audit.json")
    open(events_file, "w").close()
    for f in [incidents_file, audit_file]:
        if os.path.exists(f):
            os.remove(f)


def run_test(name, test_fn):
    """Run a single test and report result."""
    try:
        test_fn()
        print(f"  PASS: {name}")
        return True
    except AssertionError as e:
        print(f"  FAIL: {name} — {e}")
        return False
    except Exception as e:
        print(f"  ERROR: {name} — {type(e).__name__}: {e}")
        return False


# ==============================================================
# TEST 1: RISK ENGINE LEVELS
# ==============================================================

def test_risk_engine_normal():
    """No activity = NORMAL risk."""
    from core.risk_engine import evaluate_risk
    features = {
        "suspicious_indicators": 0,
        "unique_files_modified": 0,
        "file_modified": 0,
        "canary_events": 0,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] == "NORMAL", f"Expected NORMAL, got {result['risk_level']}"
    assert result["signals"] == [], f"Expected no signals, got {result['signals']}"


def test_risk_engine_low():
    """Some file modification = LOW."""
    from core.risk_engine import evaluate_risk
    features = {
        "suspicious_indicators": 0,
        "unique_files_modified": 2,
        "file_modified": 3,
        "canary_events": 0,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] == "LOW", f"Expected LOW, got {result['risk_level']}"


def test_risk_engine_medium():
    """5+ unique files without rapid-mass = MEDIUM."""
    from core.risk_engine import evaluate_risk
    features = {
        "suspicious_indicators": 0,
        "unique_files_modified": 7,
        "file_modified": 7,
        "canary_events": 0,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] in ("MEDIUM", "HIGH"), f"Expected MEDIUM+, got {result['risk_level']}"


def test_risk_engine_high():
    """Suspicious indicator = HIGH."""
    from core.risk_engine import evaluate_risk
    features = {
        "suspicious_indicators": 1,
        "unique_files_modified": 15,
        "file_modified": 20,
        "canary_events": 0,
        "total_events": 25,
        "file_events": 20,
        "file_created": 0,
        "file_deleted": 0,
        "file_renamed": 0,
        "process_events": 0,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] in ("HIGH", "CRITICAL"), f"Expected HIGH+, got {result['risk_level']}"
    assert "rapid_mass_file_modification" in result["signals"]


def test_risk_engine_canary():
    """Canary event = HIGH (strong signal)."""
    from core.risk_engine import evaluate_risk
    features = {
        "suspicious_indicators": 0,
        "unique_files_modified": 1,
        "file_modified": 1,
        "canary_events": 1,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] == "HIGH", f"Expected HIGH, got {result['risk_level']}"
    assert "canary_file_triggered" in result["signals"]


# ==============================================================
# TEST 2: ML INTEGRATION
# ==============================================================

def test_ml_inference():
    """ML model produces valid classification."""
    from ml.inference.ml_signal import get_ml_signal_safe
    features = {
        "total_events": 100,
        "file_events": 60,
        "file_created": 0,
        "file_modified": 60,
        "file_deleted": 0,
        "file_renamed": 0,
        "unique_files_modified": 30,
        "process_events": 0,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
        "suspicious_indicators": 1,
    }
    result = get_ml_signal_safe(features)
    assert result is not None, "ML signal returned None"
    assert "prediction" in result
    assert "probability" in result
    assert "label" in result
    assert result["label"] in ("NORMAL", "RANSOMWARE_LIKE")


def test_ml_ransomware_detection():
    """ML detects ransomware-like features with high probability."""
    from ml.inference.ml_signal import get_ml_signal_safe
    features = {
        "total_events": 200,
        "file_events": 120,
        "file_created": 30,
        "file_modified": 60,
        "file_deleted": 0,
        "file_renamed": 5,
        "unique_files_modified": 30,
        "process_events": 5,
        "network_events": 10,
        "established_connections": 5,
        "unique_remote_ips": 3,
        "suspicious_indicators": 2,
    }
    result = get_ml_signal_safe(features)
    assert result is not None
    assert result["probability"] > 0.7, f"Expected prob > 0.7, got {result['probability']}"
    assert result["label"] == "RANSOMWARE_LIKE"


def test_ml_normal_activity():
    """ML classifies normal activity as NORMAL."""
    from ml.inference.ml_signal import get_ml_signal_safe
    features = {
        "total_events": 5,
        "file_events": 2,
        "file_created": 1,
        "file_modified": 1,
        "file_deleted": 0,
        "file_renamed": 0,
        "unique_files_modified": 1,
        "process_events": 2,
        "network_events": 1,
        "established_connections": 1,
        "unique_remote_ips": 1,
        "suspicious_indicators": 0,
    }
    result = get_ml_signal_safe(features)
    assert result is not None
    assert result["probability"] < 0.5, f"Expected prob < 0.5, got {result['probability']}"
    assert result["label"] == "NORMAL"


# ==============================================================
# TEST 3: INCIDENT LIFECYCLE
# ==============================================================

def test_incident_lifecycle():
    """Full incident lifecycle: OPEN → INVESTIGATING → CONTAINED → RESOLVED → CLOSED."""
    clean_state()
    from core.incident_manager import IncidentManager
    mgr = IncidentManager()

    inc = mgr.create_incident(
        risk_level="CRITICAL",
        reason="Test lifecycle",
        signals=["test_signal"],
        ml_probability=0.95,
    )
    assert inc["status"] == "OPEN"

    mgr.acknowledge(inc["incident_id"])
    stored = mgr.get_incident(inc["incident_id"])
    assert stored["status"] == "INVESTIGATING"

    mgr.contain(inc["incident_id"])
    stored = mgr.get_incident(inc["incident_id"])
    assert stored["status"] == "CONTAINED"

    mgr.resolve(inc["incident_id"])
    stored = mgr.get_incident(inc["incident_id"])
    assert stored["status"] == "RESOLVED"

    mgr.close(inc["incident_id"])
    stored = mgr.get_incident(inc["incident_id"])
    assert stored["status"] == "CLOSED"

    # Active should be None after close
    assert mgr.get_active_incident() is None


# ==============================================================
# TEST 4: INCIDENT DEDUPLICATION
# ==============================================================

def test_incident_deduplication():
    """Same risk state doesn't create duplicate incidents."""
    clean_state()
    from core.incident_manager import IncidentManager
    mgr = IncidentManager()

    # Create first incident
    inc1 = mgr.create_incident(
        risk_level="CRITICAL",
        reason="Same reason",
        signals=["signal_a"],
    )

    # Simulate pipeline update (same risk, same incident)
    active = mgr.get_active_incident()
    assert active is not None
    assert active["incident_id"] == inc1["incident_id"]

    # update_risk should update, not create new
    mgr.update_risk(
        inc1["incident_id"],
        risk_level="CRITICAL",
        reason="Same reason updated",
        signals=["signal_a", "signal_b"],
    )

    all_incidents = mgr.get_all_incidents()
    assert len(all_incidents) == 1, f"Expected 1 incident, got {len(all_incidents)}"


# ==============================================================
# TEST 5: STALE INCIDENT TIMEOUT
# ==============================================================

def test_stale_incident_timeout():
    """Stale incident auto-resolves after timeout."""
    clean_state()
    from core.incident_manager import IncidentManager
    mgr = IncidentManager()

    inc = mgr.create_incident(
        risk_level="HIGH",
        reason="Stale test",
        signals=["test"],
    )

    # Manually age the incident beyond timeout
    old_time = (datetime.now() - timedelta(seconds=120)).isoformat(timespec="seconds")
    mgr._incidents[inc["incident_id"]]["updated_at"] = old_time
    mgr._save()

    # get_active_incident should auto-resolve
    active = mgr.get_active_incident()
    assert active is None, "Expected None (stale incident should auto-resolve)"

    stored = mgr.get_incident(inc["incident_id"])
    assert stored["status"] == "RESOLVED"
    assert stored["recovery_status"] == "AUTO_RESOLVED"


# ==============================================================
# TEST 6: ORPHAN INCIDENT AUTO-RESOLVE
# ==============================================================

def test_orphan_auto_resolve():
    """clear_active() auto-resolves open incidents."""
    clean_state()
    from core.incident_manager import IncidentManager
    mgr = IncidentManager()

    inc = mgr.create_incident(
        risk_level="CRITICAL",
        reason="Orphan test",
        signals=["test"],
    )
    assert mgr.get_active_incident() is not None

    # Simulate pipeline recovery to NORMAL
    mgr.clear_active()

    # Incident should be RESOLVED, not orphaned as OPEN
    stored = mgr.get_incident(inc["incident_id"])
    assert stored["status"] == "RESOLVED", f"Expected RESOLVED, got {stored['status']}"
    assert mgr.get_active_incident() is None


# ==============================================================
# TEST 7: CANARY SYSTEM
# ==============================================================

def test_canary_deployment():
    """Canary files are deployed and detected."""
    from core.canary_manager import CanaryManager
    mgr = CanaryManager()
    status = mgr.get_status()
    assert status["status"] == "ARMED"
    assert status["total"] == 5
    assert status["intact"] == 5
    assert status["triggered"] is False


def test_canary_modification_detection():
    """Modified canary file triggers detection."""
    from core.canary_manager import CanaryManager
    from core.config import CANARY_DIR

    mgr = CanaryManager()
    # Modify a canary file
    canary_files = [
        os.path.join(CANARY_DIR, f)
        for f in os.listdir(CANARY_DIR)
    ]
    assert len(canary_files) > 0

    with open(canary_files[0], "a") as f:
        f.write("TAMPERED")

    check = mgr.check_canaries()
    assert check["triggered"] is True
    assert check["status"] == "TRIGGERED"
    assert len(check["triggered_files"]) >= 1

    # Reset for other tests
    mgr.reset()


# ==============================================================
# TEST 8: FEATURE EXTRACTION
# ==============================================================

def test_feature_extraction():
    """Feature extractor produces expected output from events."""
    from core.feature_extractor import extract_features

    events = [
        {"source": "file_monitor", "event_type": "file_modified",
         "indicator": "file_modification", "data": {"path": "/tmp/a.txt"}},
        {"source": "file_monitor", "event_type": "file_modified",
         "indicator": "file_modification", "data": {"path": "/tmp/b.txt"}},
        {"source": "file_monitor", "event_type": "file_created",
         "indicator": "file_creation", "data": {"path": "/tmp/c.txt"}},
        {"source": "network_monitor", "event_type": "network_connection",
         "indicator": "new_established_connection",
         "data": {"local_address": "1.2.3.4:1234", "remote_address": "5.6.7.8:443", "status": "ESTABLISHED"}},
        {"source": "process_monitor", "event_type": "process_started",
         "indicator": "new_process", "data": {"exe": "/usr/bin/test"}},
    ]

    features = extract_features(events)
    assert features["total_events"] == 5
    assert features["file_modified"] == 2
    assert features["file_created"] == 1
    assert features["unique_files_modified"] == 2
    assert features["network_events"] == 1
    assert features["established_connections"] == 1
    assert features["unique_remote_ips"] == 1
    assert features["process_events"] == 1
    assert features["canary_events"] == 0


# ==============================================================
# TEST 9: RECOVERY (SNAPSHOT + RESTORE)
# ==============================================================

def test_recovery_snapshot_restore():
    """Snapshot and restore produce verifiable file recovery."""
    from core.prevention_engine import create_recovery_snapshot, restore_lab_files
    from core.config import LAB_DIR, SNAPSHOTS_DIR

    # Ensure test-files exist with known content
    os.makedirs(LAB_DIR, exist_ok=True)
    test_file = os.path.join(LAB_DIR, "recovery_test.txt")
    original_content = "ORIGINAL_CONTENT_FOR_RECOVERY_TEST"
    with open(test_file, "w") as f:
        f.write(original_content)

    # Create snapshot
    snap_result = create_recovery_snapshot()
    assert snap_result["success"] is True, f"Snapshot failed: {snap_result.get('message')}"

    # Modify the file (simulate damage)
    with open(test_file, "w") as f:
        f.write("DAMAGED_BY_RANSOMWARE")

    # Verify file is damaged
    with open(test_file) as f:
        assert f.read() == "DAMAGED_BY_RANSOMWARE"

    # Restore
    restore_result = restore_lab_files()
    assert restore_result["success"] is True, f"Restore failed: {restore_result.get('message')}"

    # Verify content restored
    with open(test_file) as f:
        restored = f.read()
    assert restored == original_content, f"Content mismatch: got '{restored[:50]}...'"

    # Cleanup extra snapshots
    if os.path.exists(SNAPSHOTS_DIR):
        shutil.rmtree(SNAPSHOTS_DIR)


# ==============================================================
# TEST 10: API CONSISTENCY (RISK STATE)
# ==============================================================

def test_api_risk_normal_when_no_incident():
    """When no active incident, calculate_risk returns NORMAL."""
    clean_state()
    # Force fresh import
    from core.incident_manager import IncidentManager
    import core.incident_manager as im_mod
    im_mod.incident_manager = IncidentManager()

    # Import dashboard calculate_risk
    sys.path.insert(0, PROJECT_ROOT)
    from dashboard import calculate_risk
    result = calculate_risk([])  # events not used
    assert result["risk_level"] == "NORMAL"
    assert result["detected"] is False
    assert result["incident_id"] is None


def test_api_risk_critical_with_active_incident():
    """When active incident exists, calculate_risk reflects it."""
    clean_state()
    from core.incident_manager import IncidentManager
    import core.incident_manager as im_mod
    mgr = IncidentManager()
    im_mod.incident_manager = mgr

    mgr.create_incident(
        risk_level="CRITICAL",
        reason="Test active",
        signals=["sig_a", "sig_b"],
        ml_probability=0.95,
        ml_contributed=True,
    )

    from dashboard import calculate_risk
    result = calculate_risk([])
    assert result["risk_level"] == "CRITICAL"
    assert result["detected"] is True
    assert result["ml_contributed"] is True
    assert "sig_a" in result["signals"]


def test_api_risk_returns_normal_after_close():
    """After incident closure, risk returns to NORMAL."""
    clean_state()
    from core.incident_manager import IncidentManager
    import core.incident_manager as im_mod
    mgr = IncidentManager()
    im_mod.incident_manager = mgr

    inc = mgr.create_incident(
        risk_level="CRITICAL",
        reason="Close test",
        signals=["sig"],
    )
    mgr.close(inc["incident_id"])

    from dashboard import calculate_risk
    result = calculate_risk([])
    assert result["risk_level"] == "NORMAL"
    assert result["detected"] is False


# ==============================================================
# TEST 11: FALSE-POSITIVE RESISTANCE
# ==============================================================

def test_false_positive_normal_activity():
    """Normal file/network activity doesn't trigger HIGH/CRITICAL."""
    from core.risk_engine import evaluate_risk
    # Simulate normal browsing + minor file editing
    features = {
        "suspicious_indicators": 0,
        "unique_files_modified": 3,
        "file_modified": 4,
        "file_created": 1,
        "file_deleted": 0,
        "file_renamed": 0,
        "canary_events": 0,
        "total_events": 20,
        "file_events": 5,
        "process_events": 5,
        "network_events": 10,
        "established_connections": 8,
        "unique_remote_ips": 5,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] in ("NORMAL", "LOW"), \
        f"False positive: got {result['risk_level']} for normal activity"


def test_false_positive_browser_traffic():
    """Network-heavy browser activity alone is not ransomware."""
    from core.risk_engine import evaluate_risk
    features = {
        "suspicious_indicators": 0,
        "unique_files_modified": 0,
        "file_modified": 0,
        "file_created": 0,
        "file_deleted": 0,
        "file_renamed": 0,
        "canary_events": 0,
        "total_events": 50,
        "file_events": 0,
        "process_events": 2,
        "network_events": 48,
        "established_connections": 40,
        "unique_remote_ips": 15,
    }
    result = evaluate_risk(features)
    assert result["risk_level"] == "NORMAL", \
        f"False positive: browser traffic got {result['risk_level']}"


# ==============================================================
# TEST RUNNER
# ==============================================================

ALL_TESTS = [
    ("Risk Engine: NORMAL state", test_risk_engine_normal),
    ("Risk Engine: LOW state", test_risk_engine_low),
    ("Risk Engine: MEDIUM state", test_risk_engine_medium),
    ("Risk Engine: HIGH state", test_risk_engine_high),
    ("Risk Engine: Canary signal", test_risk_engine_canary),
    ("ML: Valid inference", test_ml_inference),
    ("ML: Ransomware detection", test_ml_ransomware_detection),
    ("ML: Normal classification", test_ml_normal_activity),
    ("Incident: Full lifecycle", test_incident_lifecycle),
    ("Incident: Deduplication", test_incident_deduplication),
    ("Incident: Stale timeout", test_stale_incident_timeout),
    ("Incident: Orphan auto-resolve", test_orphan_auto_resolve),
    ("Canary: Deployment", test_canary_deployment),
    ("Canary: Modification detection", test_canary_modification_detection),
    ("Features: Extraction", test_feature_extraction),
    ("Recovery: Snapshot + Restore", test_recovery_snapshot_restore),
    ("API: NORMAL when no incident", test_api_risk_normal_when_no_incident),
    ("API: CRITICAL with active incident", test_api_risk_critical_with_active_incident),
    ("API: NORMAL after incident close", test_api_risk_returns_normal_after_close),
    ("False Positive: Normal activity", test_false_positive_normal_activity),
    ("False Positive: Browser traffic", test_false_positive_browser_traffic),
]


def main():
    print("=" * 65)
    print(" RANSOMWARE DEFENSE — AUTOMATED TEST SUITE")
    print("=" * 65)
    print()

    passed = 0
    failed = 0

    for name, fn in ALL_TESTS:
        if run_test(name, fn):
            passed += 1
        else:
            failed += 1

    print()
    print("-" * 65)
    print(f" RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print("-" * 65)

    if failed > 0:
        print(" STATUS: FAILED")
        sys.exit(1)
    else:
        print(" STATUS: ALL PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
