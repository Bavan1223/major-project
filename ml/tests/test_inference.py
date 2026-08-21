"""
Comprehensive ML Inference Tests.

Tests:
    - Model loading and artifact verification
    - Feature validation (correct, missing, extra, negative, wrong count)
    - Prediction output structure
    - Normal sample prediction
    - Ransomware-like sample prediction
    - Borderline/ambiguous sample prediction
    - Integration adapter (12-feature → 10-feature → prediction)
    - Error handling (missing model, missing preprocessor, invalid input)
    - Threshold behavior
    - Explainability output
    - Inference latency

USAGE:
    python -m ml.tests.test_inference
"""

import os
import sys
import time
import json
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import (
    ML_FEATURE_COLUMNS,
    FEATURE_VERSION,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
    MODEL_DIR,
    MODEL_FILENAME,
    PREPROCESSOR_FILENAME,
)
from ml.inference.predictor import (
    RansomwarePredictor,
    ModelNotLoadedError,
    FeatureValidationError,
)
from ml.inference.integration import MLIntegration, get_ml_prediction


# =============================================================================
# TEST FIXTURES
# =============================================================================

def normal_features():
    """Normal behavior: light file editing."""
    return {
        "total_events": 3,
        "file_created": 0,
        "file_modified": 2,
        "file_deleted": 0,
        "file_renamed": 0,
        "unique_files_modified": 2,
        "process_events": 1,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


def ransomware_features():
    """Ransomware-like behavior: rapid modification of many unique files."""
    return {
        "total_events": 25,
        "file_created": 0,
        "file_modified": 20,
        "file_deleted": 2,
        "file_renamed": 3,
        "unique_files_modified": 20,
        "process_events": 0,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


def borderline_features():
    """Ambiguous behavior: overlaps N3/R6 zone (5-6 unique files modified)."""
    return {
        "total_events": 6,
        "file_created": 0,
        "file_modified": 6,
        "file_deleted": 0,
        "file_renamed": 0,
        "unique_files_modified": 6,
        "process_events": 0,
        "network_events": 0,
        "established_connections": 0,
        "unique_remote_ips": 0,
    }


def full_extractor_output_normal():
    """Full 12-feature output from feature extractor (normal)."""
    return {
        "total_events": 5,
        "file_events": 3,              # EXCLUDED
        "file_created": 1,
        "file_modified": 2,
        "file_deleted": 0,
        "file_renamed": 0,
        "unique_files_modified": 2,
        "process_events": 1,
        "network_events": 1,
        "established_connections": 1,
        "unique_remote_ips": 1,
        "suspicious_indicators": 0,    # EXCLUDED
    }


def full_extractor_output_ransomware():
    """Full 12-feature output from feature extractor (ransomware-like)."""
    return {
        "total_events": 30,
        "file_events": 25,             # EXCLUDED
        "file_created": 2,
        "file_modified": 18,
        "file_deleted": 3,
        "file_renamed": 2,
        "unique_files_modified": 18,
        "process_events": 3,
        "network_events": 2,
        "established_connections": 2,
        "unique_remote_ips": 1,
        "suspicious_indicators": 1,    # EXCLUDED
    }


# =============================================================================
# TEST CLASSES
# =============================================================================

class TestModelArtifacts:
    """Verify model artifacts exist and are valid."""

    def test_model_file_exists(self):
        model_path = os.path.join(ML_ROOT, MODEL_DIR, MODEL_FILENAME)
        assert os.path.isfile(model_path), f"Model not found: {model_path}"

    def test_preprocessor_file_exists(self):
        prep_path = os.path.join(ML_ROOT, MODEL_DIR, PREPROCESSOR_FILENAME)
        assert os.path.isfile(prep_path), f"Preprocessor not found: {prep_path}"

    def test_metadata_file_exists(self):
        meta_path = os.path.join(ML_ROOT, MODEL_DIR, "model_metadata.json")
        assert os.path.isfile(meta_path), f"Metadata not found: {meta_path}"

    def test_metadata_has_required_fields(self):
        meta_path = os.path.join(ML_ROOT, MODEL_DIR, "model_metadata.json")
        with open(meta_path, "r") as f:
            meta = json.load(f)
        required = ["model_version", "feature_version", "feature_columns",
                    "threshold", "algorithm", "training_date"]
        for field in required:
            assert field in meta, f"Metadata missing: {field}"

    def test_metadata_feature_version_matches(self):
        meta_path = os.path.join(ML_ROOT, MODEL_DIR, "model_metadata.json")
        with open(meta_path, "r") as f:
            meta = json.load(f)
        assert meta["feature_version"] == FEATURE_VERSION

    def test_metadata_feature_columns_match(self):
        meta_path = os.path.join(ML_ROOT, MODEL_DIR, "model_metadata.json")
        with open(meta_path, "r") as f:
            meta = json.load(f)
        assert meta["feature_columns"] == list(ML_FEATURE_COLUMNS)


class TestPredictorLoading:
    """Test model loading behavior."""

    def test_predictor_loads_successfully(self):
        p = RansomwarePredictor(auto_load=True)
        assert p.is_loaded

    def test_predictor_model_version(self):
        p = RansomwarePredictor(auto_load=True)
        assert p.model_version == "1.0.0"

    def test_predictor_feature_version(self):
        p = RansomwarePredictor(auto_load=True)
        assert p.feature_version == FEATURE_VERSION

    def test_predictor_missing_model_raises_error(self):
        try:
            p = RansomwarePredictor(model_dir="/nonexistent/path", auto_load=True)
            assert False, "Should have raised ModelNotLoadedError"
        except ModelNotLoadedError:
            pass

    def test_predictor_no_auto_load(self):
        p = RansomwarePredictor(auto_load=False)
        assert not p.is_loaded


class TestFeatureValidation:
    """Test feature input validation."""

    def setup(self):
        self.predictor = RansomwarePredictor(auto_load=True)

    def test_valid_dict_accepted(self):
        X = self.predictor.validate_features(normal_features())
        assert X.shape == (1, 10)

    def test_valid_list_accepted(self):
        values = [3, 0, 2, 0, 0, 2, 1, 0, 0, 0]
        X = self.predictor.validate_features(values)
        assert X.shape == (1, 10)

    def test_missing_feature_rejected(self):
        features = normal_features()
        del features["unique_files_modified"]
        try:
            self.predictor.validate_features(features)
            assert False, "Should have raised FeatureValidationError"
        except FeatureValidationError as e:
            assert "unique_files_modified" in str(e)

    def test_wrong_feature_count_rejected(self):
        try:
            self.predictor.validate_features([1, 2, 3])  # Only 3 values
            assert False, "Should have raised FeatureValidationError"
        except FeatureValidationError as e:
            assert "Expected 10" in str(e)

    def test_negative_value_rejected(self):
        features = normal_features()
        features["file_modified"] = -1
        try:
            self.predictor.validate_features(features)
            assert False, "Should have raised FeatureValidationError"
        except FeatureValidationError as e:
            assert "negative" in str(e).lower()

    def test_none_value_rejected(self):
        features = normal_features()
        features["total_events"] = None
        try:
            self.predictor.validate_features(features)
            assert False, "Should have raised FeatureValidationError"
        except FeatureValidationError as e:
            assert "None" in str(e)

    def test_non_numeric_rejected(self):
        features = normal_features()
        features["total_events"] = "abc"
        try:
            self.predictor.validate_features(features)
            assert False, "Should have raised FeatureValidationError"
        except FeatureValidationError as e:
            assert "non-numeric" in str(e)

    def test_extra_features_ignored(self):
        features = normal_features()
        features["suspicious_indicators"] = 5  # Excluded, should be ignored
        features["file_events"] = 10  # Excluded, should be ignored
        X = self.predictor.validate_features(features)
        assert X.shape == (1, 10)


class TestPredictionOutput:
    """Test prediction output structure and correctness."""

    def setup(self):
        self.predictor = RansomwarePredictor(auto_load=True)

    def test_output_has_required_fields(self):
        result = self.predictor.predict(normal_features())
        required = ["prediction", "label", "probability", "above_threshold",
                    "threshold", "model_version", "feature_version",
                    "important_features", "inference_time_ms"]
        for field in required:
            assert field in result, f"Missing output field: {field}"

    def test_prediction_is_0_or_1(self):
        result = self.predictor.predict(normal_features())
        assert result["prediction"] in (0, 1)

    def test_label_matches_prediction(self):
        result = self.predictor.predict(normal_features())
        if result["prediction"] == 0:
            assert result["label"] == "NORMAL"
        else:
            assert result["label"] == "RANSOMWARE_LIKE"

    def test_probability_between_0_and_1(self):
        result = self.predictor.predict(normal_features())
        assert 0.0 <= result["probability"] <= 1.0

    def test_threshold_is_numeric(self):
        result = self.predictor.predict(normal_features())
        assert isinstance(result["threshold"], (int, float))

    def test_normal_sample_predicts_normal(self):
        result = self.predictor.predict(normal_features())
        assert result["prediction"] == LABEL_NORMAL
        assert result["label"] == "NORMAL"
        assert result["probability"] < 0.5  # Should be low

    def test_ransomware_sample_predicts_ransomware(self):
        result = self.predictor.predict(ransomware_features())
        assert result["prediction"] == LABEL_RANSOMWARE_LIKE
        assert result["label"] == "RANSOMWARE_LIKE"
        assert result["probability"] > 0.5  # Should be high

    def test_borderline_produces_moderate_probability(self):
        result = self.predictor.predict(borderline_features())
        # Borderline should not be extreme in either direction
        # (may still predict one way, but probability should be less certain)
        assert 0.1 <= result["probability"] <= 0.95

    def test_inference_time_measured(self):
        result = self.predictor.predict(normal_features())
        assert result["inference_time_ms"] >= 0
        assert result["inference_time_ms"] < 100  # Should be fast


class TestExplainability:
    """Test feature importance explanation output."""

    def setup(self):
        self.predictor = RansomwarePredictor(auto_load=True)

    def test_important_features_is_list(self):
        result = self.predictor.predict(ransomware_features())
        assert isinstance(result["important_features"], list)

    def test_important_features_have_structure(self):
        result = self.predictor.predict(ransomware_features())
        for feat in result["important_features"]:
            assert "feature" in feat
            assert "value" in feat
            assert "contribution" in feat
            assert "direction" in feat
            assert feat["direction"] in ("ransomware", "normal")

    def test_important_features_sorted_by_contribution(self):
        result = self.predictor.predict(ransomware_features())
        feats = result["important_features"]
        contributions = [abs(f["contribution"]) for f in feats]
        assert contributions == sorted(contributions, reverse=True)

    def test_ransomware_prediction_shows_unique_files_as_important(self):
        result = self.predictor.predict(ransomware_features())
        feature_names = [f["feature"] for f in result["important_features"]]
        # unique_files_modified should be among top contributors for ransomware
        assert "unique_files_modified" in feature_names


class TestIntegrationAdapter:
    """Test the core integration adapter (12-feature → ML → result)."""

    def setup(self):
        self.integration = MLIntegration(auto_load=True)

    def test_integration_is_ready(self):
        assert self.integration.is_ready

    def test_normal_extractor_output(self):
        result = self.integration.predict(full_extractor_output_normal())
        assert result["status"] == "success"
        assert result["prediction"] == LABEL_NORMAL

    def test_ransomware_extractor_output(self):
        result = self.integration.predict(full_extractor_output_ransomware())
        assert result["status"] == "success"
        assert result["prediction"] == LABEL_RANSOMWARE_LIKE

    def test_excluded_features_not_used(self):
        """Changing excluded features should NOT affect prediction."""
        output1 = full_extractor_output_normal()
        output2 = full_extractor_output_normal()
        output2["suspicious_indicators"] = 99  # Should be ignored
        output2["file_events"] = 999  # Should be ignored

        result1 = self.integration.predict(output1)
        result2 = self.integration.predict(output2)
        assert result1["probability"] == result2["probability"]

    def test_missing_ml_feature_returns_error(self):
        output = full_extractor_output_normal()
        del output["unique_files_modified"]
        result = self.integration.predict(output)
        assert result["status"] == "error"
        assert result["error_type"] == "feature_validation"

    def test_non_dict_input_returns_error(self):
        result = self.integration.predict("not a dict")
        assert result["status"] == "error"

    def test_function_interface_works(self):
        result = get_ml_prediction(full_extractor_output_normal())
        assert result["status"] == "success"
        assert "prediction" in result


class TestThresholdBehavior:
    """Test threshold-based classification."""

    def setup(self):
        self.predictor = RansomwarePredictor(auto_load=True)

    def test_above_threshold_matches_probability(self):
        result = self.predictor.predict(ransomware_features())
        expected = result["probability"] >= result["threshold"]
        assert result["above_threshold"] == expected

    def test_low_probability_below_threshold(self):
        result = self.predictor.predict(normal_features())
        assert result["above_threshold"] is False

    def test_high_probability_above_threshold(self):
        result = self.predictor.predict(ransomware_features())
        assert result["above_threshold"] is True


class TestLatency:
    """Measure inference latency."""

    def setup(self):
        self.predictor = RansomwarePredictor(auto_load=True)

    def test_single_inference_under_10ms(self):
        start = time.perf_counter()
        self.predictor.predict(normal_features())
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 10, f"Single inference took {elapsed_ms:.2f}ms (>10ms)"

    def test_batch_100_under_200ms(self):
        features = normal_features()
        start = time.perf_counter()
        for _ in range(100):
            self.predictor.predict(features)
        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / 100
        assert avg_ms < 2, f"Average inference {avg_ms:.3f}ms (>2ms)"


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

def run_all_tests():
    test_classes = [
        TestModelArtifacts,
        TestPredictorLoading,
        TestFeatureValidation,
        TestPredictionOutput,
        TestExplainability,
        TestIntegrationAdapter,
        TestThresholdBehavior,
        TestLatency,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        if hasattr(instance, "setup"):
            instance.setup()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]

        print(f"\n{'='*60}")
        print(f"  {cls.__name__}")
        print(f"{'='*60}")

        for method_name in sorted(test_methods):
            total += 1
            try:
                if hasattr(instance, "setup"):
                    instance.setup()
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
    print(f"  INFERENCE TEST RESULTS: {passed}/{total} passed, {failed} failed")
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
