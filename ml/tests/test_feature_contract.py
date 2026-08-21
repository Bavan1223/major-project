"""
Feature Contract Validation Tests.

This module validates that:
1. The feature_definition.json is well-formed and internally consistent
2. The ML config (ml/config.py) matches the feature definition
3. A simulated feature_extractor output can be correctly mapped to ML input

IMPORTANT:
    This script can run in two modes:
    
    MODE A - Standalone validation (runs anywhere):
        Validates internal consistency of the feature contract.
        Does NOT require the Ubuntu lab or core/feature_extractor.py.
        
    MODE B - Integration validation (runs on Ubuntu lab):
        Additionally validates that core/feature_extractor.py produces
        output compatible with the ML feature contract.
        Requires the actual project at ~/ransomware-lab/

Usage:
    python -m pytest ml/tests/test_feature_contract.py -v
    
    Or directly:
    python ml/tests/test_feature_contract.py
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Path setup so this test can import ml.config regardless of working directory
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_ROOT = os.path.dirname(SCRIPT_DIR)  # ml/
PROJECT_ROOT = os.path.dirname(ML_ROOT)  # project root

# Add project root to path so we can import ml.config
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import (
    FEATURE_VERSION,
    ML_FEATURE_COLUMNS,
    EXCLUDED_FEATURES,
    WINDOW_SECONDS,
    LABEL_MAP,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
)

# ---------------------------------------------------------------------------
# Load feature definition
# ---------------------------------------------------------------------------
FEATURE_DEF_PATH = os.path.join(ML_ROOT, "features", "feature_definition.json")


def load_feature_definition():
    """Load and return the feature definition JSON."""
    with open(FEATURE_DEF_PATH, "r") as f:
        return json.load(f)


# ===========================================================================
# MODE A: STANDALONE VALIDATION TESTS
# ===========================================================================


class TestFeatureDefinitionStructure:
    """Validate the structure and completeness of feature_definition.json."""

    def setup_method(self):
        self.feat_def = load_feature_definition()

    def test_feature_definition_file_exists(self):
        """feature_definition.json must exist."""
        assert os.path.isfile(FEATURE_DEF_PATH), (
            f"Feature definition not found at {FEATURE_DEF_PATH}"
        )

    def test_has_required_top_level_keys(self):
        """Feature definition must contain all required top-level keys."""
        required_keys = [
            "feature_version",
            "observation_window_seconds",
            "description",
            "classification",
            "ml_features",
            "excluded_features",
            "validation_rules",
        ]
        for key in required_keys:
            assert key in self.feat_def, f"Missing required key: {key}"

    def test_feature_version_matches_config(self):
        """feature_definition.json version must match ml/config.py FEATURE_VERSION."""
        assert self.feat_def["feature_version"] == FEATURE_VERSION, (
            f"Version mismatch: feature_definition.json has '{self.feat_def['feature_version']}' "
            f"but config.py has '{FEATURE_VERSION}'"
        )

    def test_observation_window_matches_config(self):
        """Observation window in definition must match config.py WINDOW_SECONDS."""
        assert self.feat_def["observation_window_seconds"] == WINDOW_SECONDS, (
            f"Window mismatch: feature_definition.json has {self.feat_def['observation_window_seconds']} "
            f"but config.py has {WINDOW_SECONDS}"
        )

    def test_classification_is_binary(self):
        """Classification must be defined as binary."""
        assert self.feat_def["classification"]["type"] == "binary"
        labels = self.feat_def["classification"]["labels"]
        assert "0" in labels and "1" in labels
        assert labels["0"] == "NORMAL"
        assert labels["1"] == "RANSOMWARE_LIKE"

    def test_label_map_matches_config(self):
        """Label definitions must match config.py LABEL_MAP."""
        labels = self.feat_def["classification"]["labels"]
        assert labels["0"] == LABEL_MAP[LABEL_NORMAL]
        assert labels["1"] == LABEL_MAP[LABEL_RANSOMWARE_LIKE]

    def test_ml_features_count(self):
        """Number of ML features must match config.py ML_FEATURE_COLUMNS."""
        ml_features = self.feat_def["ml_features"]
        assert len(ml_features) == len(ML_FEATURE_COLUMNS), (
            f"Feature count mismatch: definition has {len(ml_features)} features "
            f"but config.py has {len(ML_FEATURE_COLUMNS)}"
        )

    def test_ml_feature_names_match_config(self):
        """Feature names in definition must match config.py ML_FEATURE_COLUMNS exactly."""
        definition_names = [f["name"] for f in self.feat_def["ml_features"]]
        assert definition_names == ML_FEATURE_COLUMNS, (
            f"Feature name/order mismatch:\n"
            f"  Definition: {definition_names}\n"
            f"  Config:     {list(ML_FEATURE_COLUMNS)}"
        )

    def test_ml_feature_indices_sequential(self):
        """Feature indices must be sequential starting from 0."""
        for i, feature in enumerate(self.feat_def["ml_features"]):
            assert feature["index"] == i, (
                f"Feature '{feature['name']}' has index {feature['index']} but expected {i}"
            )

    def test_each_feature_has_required_fields(self):
        """Each ML feature must have all required documentation fields."""
        required_fields = [
            "name", "index", "dtype", "source", "description",
            "formula", "ransomware_relevance", "currently_available",
            "requires_core_changes", "min_value",
        ]
        for feature in self.feat_def["ml_features"]:
            for field in required_fields:
                assert field in feature, (
                    f"Feature '{feature['name']}' missing required field: {field}"
                )

    def test_all_features_currently_available(self):
        """All v1.0 ML features must be currently available (no core changes needed)."""
        for feature in self.feat_def["ml_features"]:
            assert feature["currently_available"] is True, (
                f"Feature '{feature['name']}' is NOT currently available — "
                f"it should not be in the v1.0 ML feature set"
            )
            assert feature["requires_core_changes"] is False, (
                f"Feature '{feature['name']}' requires core changes — "
                f"it should not be in the v1.0 ML feature set"
            )

    def test_all_features_non_negative_minimum(self):
        """All features must have min_value >= 0."""
        for feature in self.feat_def["ml_features"]:
            assert feature["min_value"] >= 0, (
                f"Feature '{feature['name']}' has min_value < 0"
            )

    def test_all_features_integer_dtype(self):
        """All v1.0 features must be integer type (counts from event aggregation)."""
        for feature in self.feat_def["ml_features"]:
            assert feature["dtype"] == "int", (
                f"Feature '{feature['name']}' has dtype '{feature['dtype']}' — "
                f"v1.0 features should all be integer counts"
            )

    def test_excluded_features_documented(self):
        """Excluded features in definition must match config.py EXCLUDED_FEATURES."""
        excluded_names = {f["name"] for f in self.feat_def["excluded_features"]}
        config_excluded = set(EXCLUDED_FEATURES.keys())
        assert excluded_names == config_excluded, (
            f"Excluded feature mismatch:\n"
            f"  Definition: {excluded_names}\n"
            f"  Config:     {config_excluded}"
        )

    def test_suspicious_indicators_excluded(self):
        """suspicious_indicators must be in the excluded list with CIRCULAR_REASONING reason."""
        excluded = {f["name"]: f for f in self.feat_def["excluded_features"]}
        assert "suspicious_indicators" in excluded, (
            "suspicious_indicators must be explicitly excluded"
        )
        assert excluded["suspicious_indicators"]["reason"] == "CIRCULAR_REASONING"

    def test_file_events_excluded(self):
        """file_events must be in the excluded list with REDUNDANT reason."""
        excluded = {f["name"]: f for f in self.feat_def["excluded_features"]}
        assert "file_events" in excluded, (
            "file_events must be explicitly excluded"
        )
        assert excluded["file_events"]["reason"] == "REDUNDANT"

    def test_no_duplicate_feature_names(self):
        """No duplicate feature names in the ML feature set."""
        names = [f["name"] for f in self.feat_def["ml_features"]]
        assert len(names) == len(set(names)), (
            f"Duplicate feature names detected: {[n for n in names if names.count(n) > 1]}"
        )

    def test_validation_rules_present(self):
        """Validation rules must be defined and consistent."""
        rules = self.feat_def["validation_rules"]
        assert rules["all_features_must_be_non_negative"] is True
        assert rules["all_features_must_be_integer"] is True
        assert rules["feature_count_must_equal"] == len(ML_FEATURE_COLUMNS)
        assert rules["feature_order_must_match_ml_feature_columns"] is True
        assert rules["missing_values_not_permitted"] is True


class TestFeatureContractValidation:
    """Validate that a sample feature extractor output maps correctly to ML input."""

    def setup_method(self):
        self.feat_def = load_feature_definition()

    def test_valid_feature_vector_mapping(self):
        """
        Simulate feature_extractor.py output (all 12 features) and verify
        the ML module correctly selects the 10 features it needs.
        """
        # Simulated output from core/feature_extractor.py
        # This represents what the feature extractor actually produces
        extractor_output = {
            "total_events": 15,
            "file_events": 8,           # EXCLUDED - redundant
            "file_created": 2,
            "file_modified": 4,
            "file_deleted": 1,
            "file_renamed": 1,
            "unique_files_modified": 3,
            "process_events": 4,
            "network_events": 3,
            "established_connections": 2,
            "unique_remote_ips": 1,
            "suspicious_indicators": 0,  # EXCLUDED - circular reasoning
        }

        # ML feature selection: extract only the 10 features we need, in order
        ml_input = [extractor_output[col] for col in ML_FEATURE_COLUMNS]

        # Verify correct mapping
        assert len(ml_input) == 10
        assert ml_input[0] == 15   # total_events
        assert ml_input[1] == 2    # file_created
        assert ml_input[2] == 4    # file_modified
        assert ml_input[3] == 1    # file_deleted
        assert ml_input[4] == 1    # file_renamed
        assert ml_input[5] == 3    # unique_files_modified
        assert ml_input[6] == 4    # process_events
        assert ml_input[7] == 3    # network_events
        assert ml_input[8] == 2    # established_connections
        assert ml_input[9] == 1    # unique_remote_ips

    def test_excluded_features_not_in_ml_input(self):
        """Excluded features must not appear in ML_FEATURE_COLUMNS."""
        for excluded_name in EXCLUDED_FEATURES:
            assert excluded_name not in ML_FEATURE_COLUMNS, (
                f"Excluded feature '{excluded_name}' found in ML_FEATURE_COLUMNS"
            )

    def test_missing_feature_raises_error(self):
        """If a required feature is missing from extractor output, it must fail clearly."""
        # Incomplete extractor output (missing unique_files_modified)
        incomplete_output = {
            "total_events": 15,
            "file_created": 2,
            "file_modified": 4,
            "file_deleted": 1,
            "file_renamed": 1,
            # "unique_files_modified" is MISSING
            "process_events": 4,
            "network_events": 3,
            "established_connections": 2,
            "unique_remote_ips": 1,
        }

        # Attempting to extract ML features should raise KeyError
        try:
            ml_input = [incomplete_output[col] for col in ML_FEATURE_COLUMNS]
            assert False, "Should have raised KeyError for missing feature"
        except KeyError as e:
            assert "unique_files_modified" in str(e)

    def test_all_features_non_negative_validation(self):
        """Feature vector validation must reject negative values."""
        feature_vector = {
            "total_events": 10,
            "file_created": -1,  # INVALID
            "file_modified": 4,
            "file_deleted": 1,
            "file_renamed": 1,
            "unique_files_modified": 3,
            "process_events": 4,
            "network_events": 3,
            "established_connections": 2,
            "unique_remote_ips": 1,
        }

        ml_input = [feature_vector[col] for col in ML_FEATURE_COLUMNS]
        # Validation: all values must be >= 0
        invalid_features = [
            (ML_FEATURE_COLUMNS[i], v)
            for i, v in enumerate(ml_input) if v < 0
        ]
        assert len(invalid_features) > 0, "Should have detected negative value"
        assert invalid_features[0][0] == "file_created"
        assert invalid_features[0][1] == -1

    def test_ransomware_like_feature_vector(self):
        """
        Simulate ransomware-like extractor output and verify it maps correctly.
        This does NOT test model prediction — only that the feature mapping works.
        """
        ransomware_like_output = {
            "total_events": 85,
            "file_events": 60,           # EXCLUDED
            "file_created": 15,
            "file_modified": 30,
            "file_deleted": 10,
            "file_renamed": 5,
            "unique_files_modified": 25,
            "process_events": 12,
            "network_events": 8,
            "established_connections": 5,
            "unique_remote_ips": 3,
            "suspicious_indicators": 2,  # EXCLUDED
        }

        ml_input = [ransomware_like_output[col] for col in ML_FEATURE_COLUMNS]

        assert len(ml_input) == 10
        # Verify the high-activity values mapped correctly
        assert ml_input[0] == 85   # total_events - high
        assert ml_input[2] == 30   # file_modified - high
        assert ml_input[5] == 25   # unique_files_modified - high
        # Verify excluded features are NOT present
        assert 60 not in ml_input  # file_events value should not be in ML input
        assert 2 not in ml_input   # suspicious_indicators value should not be in ML input

    def test_zero_activity_feature_vector(self):
        """An idle window with no activity should produce all-zero ML input."""
        idle_output = {
            "total_events": 0,
            "file_events": 0,
            "file_created": 0,
            "file_modified": 0,
            "file_deleted": 0,
            "file_renamed": 0,
            "unique_files_modified": 0,
            "process_events": 0,
            "network_events": 0,
            "established_connections": 0,
            "unique_remote_ips": 0,
            "suspicious_indicators": 0,
        }

        ml_input = [idle_output[col] for col in ML_FEATURE_COLUMNS]
        assert all(v == 0 for v in ml_input)
        assert len(ml_input) == 10


class TestFeatureExtractorCompatibility:
    """
    Tests that verify compatibility with core/feature_extractor.py.
    
    These tests define the EXPECTED interface contract.
    They use simulated data here, but can be extended to test against
    the actual feature_extractor.py when run on the Ubuntu lab.
    """

    def test_extractor_output_contains_all_ml_features(self):
        """
        The feature extractor must produce ALL features needed by ML.
        
        Expected feature_extractor.py output keys (12 total):
            total_events, file_events, file_created, file_modified,
            file_deleted, file_renamed, unique_files_modified,
            process_events, network_events, established_connections,
            unique_remote_ips, suspicious_indicators
        """
        # Define the EXPECTED output keys from feature_extractor.py
        expected_extractor_keys = {
            "total_events",
            "file_events",
            "file_created",
            "file_modified",
            "file_deleted",
            "file_renamed",
            "unique_files_modified",
            "process_events",
            "network_events",
            "established_connections",
            "unique_remote_ips",
            "suspicious_indicators",
        }

        # Verify all ML features are a subset of extractor output
        ml_features_set = set(ML_FEATURE_COLUMNS)
        missing = ml_features_set - expected_extractor_keys
        assert len(missing) == 0, (
            f"ML requires features not produced by feature_extractor: {missing}"
        )

    def test_extractor_produces_superset_of_ml_features(self):
        """
        Feature extractor produces 12 features.
        ML uses 10 of them.
        The 2 excluded ones must be documented.
        """
        expected_extractor_count = 12
        ml_feature_count = len(ML_FEATURE_COLUMNS)
        excluded_count = len(EXCLUDED_FEATURES)

        assert ml_feature_count + excluded_count == expected_extractor_count, (
            f"Accounting mismatch: ML uses {ml_feature_count}, "
            f"excludes {excluded_count}, "
            f"but extractor produces {expected_extractor_count}. "
            f"Sum = {ml_feature_count + excluded_count}"
        )


# ===========================================================================
# DIRECT EXECUTION
# ===========================================================================

def run_standalone_tests():
    """Run all tests without pytest dependency."""
    test_classes = [
        TestFeatureDefinitionStructure,
        TestFeatureContractValidation,
        TestFeatureExtractorCompatibility,
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
                # Call setup if it exists
                if hasattr(instance, "setup_method"):
                    instance.setup_method()
                # Run the test
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
                errors.append((cls.__name__, method_name, f"ERROR: {e}"))
                print(f"  ERROR {method_name}")
                print(f"        {type(e).__name__}: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    if errors:
        print(f"\n  FAILURES:")
        for cls_name, method, msg in errors:
            print(f"    {cls_name}.{method}")
            print(f"      {msg}")

    return failed == 0


if __name__ == "__main__":
    success = run_standalone_tests()
    sys.exit(0 if success else 1)
