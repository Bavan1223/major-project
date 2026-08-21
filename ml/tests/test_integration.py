"""
Gate 10.1 — ML Integration Test Suite (12 tests).

Tests the complete integration between ML signal and Central Risk Engine
using the ACTUAL merged risk_engine.py with additive ML integration.

USAGE:
    python -m ml.tests.test_integration
"""

import os
import sys
import time
import ast
import inspect
from unittest.mock import patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.risk_engine import evaluate_risk


# =============================================================================
# HELPER: Feature vectors
# =============================================================================

def features_normal_idle():
    """No activity at all."""
    return {
        "suspicious_indicators": 0,
        "unique_files_modified": 0,
        "file_modified": 0,
    }


def features_low_activity():
    """Some file modification but below thresholds."""
    return {
        "suspicious_indicators": 0,
        "unique_files_modified": 2,
        "file_modified": 2,
        "total_events": 3,
        "file_created": 0,
        "file_deleted": 0,
        "file_renamed": 0,
        "process_events": 1,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


def features_rule_high():
    """Triggers rule HIGH (suspicious_indicators > 0 + many files)."""
    return {
        "suspicious_indicators": 1,
        "unique_files_modified": 20,
        "file_modified": 20,
        "total_events": 25,
        "file_created": 0,
        "file_deleted": 2,
        "file_renamed": 3,
        "process_events": 0,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


def features_moderate_no_rule():
    """Moderate activity, no rule fires (unique_files < 5, no suspicious_indicators)."""
    return {
        "suspicious_indicators": 0,
        "unique_files_modified": 3,
        "file_modified": 3,
        "total_events": 5,
        "file_created": 1,
        "file_deleted": 0,
        "file_renamed": 0,
        "process_events": 1,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


def features_ransomware_clear():
    """Clear ransomware-like pattern that ML will detect confidently."""
    return {
        "suspicious_indicators": 0,
        "unique_files_modified": 15,
        "file_modified": 15,
        "total_events": 18,
        "file_created": 0,
        "file_deleted": 1,
        "file_renamed": 2,
        "process_events": 0,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


# =============================================================================
# TEST CLASSES
# =============================================================================

class TestMLUnavailableFallback:
    """Tests 1-2: ML unavailable → rule-only."""

    def test_1_ml_unavailable_rule_only(self):
        """When ML is unavailable, rule-only severity is returned."""
        # Patch ML to be unavailable
        with patch("core.risk_engine._get_ml_signal_safe", return_value=None):
            result = evaluate_risk(features_rule_high())
            assert result["risk_level"] == "HIGH", (
                f"ML unavailable + rule HIGH should give HIGH, got {result['risk_level']}"
            )
            assert result["ml_contributed"] is False

    def test_2_ml_error_rule_only(self):
        """When ML returns error, severity is rule-only."""
        # Patch ML to return None (simulates any error)
        with patch("core.risk_engine._get_ml_signal_safe", return_value=None):
            result = evaluate_risk(features_normal_idle())
            assert result["risk_level"] == "NORMAL"
            assert result["ml_signal"] is None
            assert result["ml_contributed"] is False


class TestMLNormalNoRule:
    """Test 3: ML NORMAL + no rule signal → NORMAL."""

    def test_3_ml_normal_no_rule_gives_normal(self):
        """ML predicts NORMAL, no rules fire → NORMAL severity."""
        # Use features that produce rule NORMAL and ML NORMAL
        result = evaluate_risk(features_normal_idle())
        assert result["risk_level"] == "NORMAL", (
            f"Expected NORMAL, got {result['risk_level']}"
        )


class TestMLOnlyCapped:
    """Tests 4-5: ML-only detection capped at MEDIUM."""

    def test_4_ml_ransomware_confident_no_rule_max_medium(self):
        """ML confident RANSOMWARE + no rule (NORMAL) → max MEDIUM."""
        mock_ml = {
            "status": "success", "prediction": 1, "label": "RANSOMWARE_LIKE",
            "probability": 0.95, "above_threshold": True, "threshold": 0.70,
            "model_version": "2.0.0", "feature_version": "1.0",
            "important_features": [], "inference_time_ms": 0.5,
        }
        with patch("core.risk_engine._get_ml_signal_safe", return_value=mock_ml):
            result = evaluate_risk(features_normal_idle())
            assert result["risk_level"] == "MEDIUM", (
                f"ML-only confident should cap at MEDIUM, got {result['risk_level']}"
            )
            assert result["risk_level"] != "CRITICAL", "ML alone must NEVER produce CRITICAL"
            assert result["ml_contributed"] is True

    def test_5_ml_ransomware_uncertain_no_rule(self):
        """ML uncertain (below threshold) + no rule → no escalation (stays NORMAL)."""
        mock_ml = {
            "status": "success", "prediction": 1, "label": "RANSOMWARE_LIKE",
            "probability": 0.55, "above_threshold": False, "threshold": 0.70,
            "model_version": "2.0.0", "feature_version": "1.0",
            "important_features": [], "inference_time_ms": 0.5,
        }
        with patch("core.risk_engine._get_ml_signal_safe", return_value=mock_ml):
            result = evaluate_risk(features_normal_idle())
            # ML below threshold should NOT escalate
            assert result["risk_level"] == "NORMAL", (
                f"ML uncertain should not escalate NORMAL, got {result['risk_level']}"
            )
            assert result["ml_contributed"] is False


class TestRuleMLCombination:
    """Tests 6-8: Rule + ML combined decisions."""

    def test_6_rule_high_ml_confident_gives_critical(self):
        """Rule HIGH + ML confident RANSOMWARE → CRITICAL."""
        mock_ml = {
            "status": "success", "prediction": 1, "label": "RANSOMWARE_LIKE",
            "probability": 0.99, "above_threshold": True, "threshold": 0.70,
            "model_version": "2.0.0", "feature_version": "1.0",
            "important_features": [], "inference_time_ms": 0.5,
        }
        with patch("core.risk_engine._get_ml_signal_safe", return_value=mock_ml):
            result = evaluate_risk(features_rule_high())
            assert result["risk_level"] == "CRITICAL", (
                f"Rule HIGH + ML confident should give CRITICAL, got {result['risk_level']}"
            )
            assert "ml_ransomware_confirmed" in result["signals"]
            assert result["ml_contributed"] is True

    def test_7_rule_high_ml_normal_stays_high(self):
        """Rule HIGH + ML NORMAL → HIGH (no downgrade)."""
        mock_ml = {
            "status": "success", "prediction": 0, "label": "NORMAL",
            "probability": 0.05, "above_threshold": False, "threshold": 0.70,
            "model_version": "2.0.0", "feature_version": "1.0",
            "important_features": [], "inference_time_ms": 0.5,
        }
        with patch("core.risk_engine._get_ml_signal_safe", return_value=mock_ml):
            result = evaluate_risk(features_rule_high())
            assert result["risk_level"] == "HIGH", (
                f"Rule HIGH + ML NORMAL must stay HIGH, got {result['risk_level']}"
            )
            assert result["ml_contributed"] is False

    def test_8_no_rule_ml_confident_capped_medium(self):
        """No rule + ML confident → MEDIUM (not CRITICAL)."""
        mock_ml = {
            "status": "success", "prediction": 1, "label": "RANSOMWARE_LIKE",
            "probability": 0.92, "above_threshold": True, "threshold": 0.70,
            "model_version": "2.0.0", "feature_version": "1.0",
            "important_features": [], "inference_time_ms": 0.5,
        }
        with patch("core.risk_engine._get_ml_signal_safe", return_value=mock_ml):
            # features_moderate_no_rule gives rule LOW (file_modified > 0)
            result = evaluate_risk(features_low_activity())
            # Rule gives LOW, ML confident → should escalate to MEDIUM
            assert result["risk_level"] == "MEDIUM", (
                f"Rule LOW + ML confident should give MEDIUM, got {result['risk_level']}"
            )
            assert result["risk_level"] != "CRITICAL"


class TestDryRunProtection:
    """Test 9: ML does not perform containment."""

    def test_9_ml_does_not_perform_containment(self):
        """ML inference code contains no dangerous system calls."""
        from ml.inference import ml_signal as ml_mod
        from ml.inference import predictor as pred_mod
        from ml.inference import integration as integ_mod

        dangerous_calls = {
            "os.kill", "os.remove", "os.unlink", "shutil.rmtree",
            "subprocess.run", "subprocess.call", "subprocess.Popen",
        }

        for module in [ml_mod, pred_mod, integ_mod]:
            source = inspect.getsource(module)
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call_name = ""
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call_name = f"{node.func.value.id}.{node.func.attr}"
                    elif isinstance(node.func, ast.Name):
                        call_name = node.func.id
                    assert call_name not in dangerous_calls, (
                        f"ML module {module.__name__} calls: '{call_name}'"
                    )


class TestFullPipeline:
    """Test 10: Full E2E pipeline."""

    def test_10_full_pipeline_e2e(self):
        """Full pipeline: features → risk engine → severity with ML."""
        # Normal → NORMAL
        result_normal = evaluate_risk(features_normal_idle())
        assert result_normal["risk_level"] == "NORMAL"

        # Rule HIGH scenario → at least HIGH (CRITICAL if ML available and agrees)
        result_high = evaluate_risk(features_rule_high())
        assert result_high["risk_level"] in ("HIGH", "CRITICAL")

        # Verify structure
        for result in [result_normal, result_high]:
            assert "risk_level" in result
            assert "reason" in result
            assert "signals" in result
            assert "ml_signal" in result
            assert "ml_contributed" in result


class TestLatency:
    """Test 11: Pipeline latency."""

    def test_11_pipeline_latency_under_50ms(self):
        """Full risk evaluation completes within 50ms average."""
        features = features_rule_high()
        # Warm up
        for _ in range(5):
            evaluate_risk(features)
        # Measure
        start = time.perf_counter()
        for _ in range(20):
            evaluate_risk(features)
        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / 20
        assert avg_ms < 50, f"Average {avg_ms:.2f}ms exceeds 50ms"


class TestNoRegression:
    """Test 12: Existing ML tests still pass."""

    def test_12_no_regression(self):
        """Core ML functionality unchanged by integration."""
        from ml.config import ML_FEATURE_COLUMNS, FEATURE_VERSION
        from ml.inference.predictor import RansomwarePredictor
        from ml.inference.ml_signal import get_ml_signal_safe

        # Config intact
        assert len(ML_FEATURE_COLUMNS) == 10
        assert FEATURE_VERSION == "1.0"

        # Model loads
        p = RansomwarePredictor()
        assert p.is_loaded
        assert p.model_version == "2.0.0"
        assert p.threshold == 0.7

        # Safe wrapper works
        test_features = {
            "total_events": 3, "file_events": 2, "file_created": 0,
            "file_modified": 2, "file_deleted": 0, "file_renamed": 0,
            "unique_files_modified": 2, "process_events": 1,
            "network_events": 0, "established_connections": 0,
            "unique_remote_ips": 0, "suspicious_indicators": 0,
        }
        signal = get_ml_signal_safe(test_features)
        assert signal is not None
        assert signal["status"] == "success"
        assert signal["prediction"] in (0, 1)


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

def run_all_tests():
    test_classes = [
        TestMLUnavailableFallback,
        TestMLNormalNoRule,
        TestMLOnlyCapped,
        TestRuleMLCombination,
        TestDryRunProtection,
        TestFullPipeline,
        TestLatency,
        TestNoRegression,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]

        print(f"\n{'='*60}")
        print(f"  {cls.__name__}")
        print(f"{'='*60}")

        for method_name in sorted(test_methods):
            total += 1
            try:
                getattr(instance, method_name)()
                passed += 1
                print(f"  PASS  {method_name}")
            except AssertionError as e:
                failed += 1
                errors.append((cls.__name__, method_name, str(e)))
                print(f"  FAIL  {method_name}")
                print(f"        {e}")
            except Exception as e:
                failed += 1
                errors.append((cls.__name__, method_name, f"{type(e).__name__}: {e}"))
                print(f"  ERROR {method_name}")
                print(f"        {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"  INTEGRATION TEST RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    if errors:
        print(f"\n  FAILURES:")
        for cls_name, method, msg in errors:
            print(f"    {cls_name}.{method}")
            print(f"      {msg}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
