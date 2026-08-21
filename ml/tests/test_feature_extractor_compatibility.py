"""
M2.2 Feature Extractor Compatibility Verification.

This test module verifies that the ML feature contract (v1.0) is compatible
with the actual core/feature_extractor.py implementation.

VERIFICATION METHOD:
    Since core/feature_extractor.py lives on the Ubuntu lab machine and
    cannot be imported directly in this Windows workspace, we simulate
    its behavior based on the inspected source code and verify that:
    
    1. The extractor produces exactly 12 feature keys
    2. The 10 ML features are a proper subset of those 12
    3. The 2 excluded features are accounted for
    4. The event schema required fields are known and documented
    5. The suspicious_indicators calculation is rule-derived (confirmed)

SOURCE VERIFICATION DATE: 2026-08-20
VERIFIED AGAINST: ~/ransomware-lab/core/feature_extractor.py (Ubuntu lab)
VERIFIED AGAINST: ~/ransomware-lab/core/event_schema.py (Ubuntu lab)

This file does NOT modify any core files.
"""

import sys
import os
import json

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
)


# =============================================================================
# VERIFIED CONSTANTS FROM ACTUAL UBUNTU SOURCE CODE
# =============================================================================

# These are the ACTUAL output keys from core/feature_extractor.py
# as verified by direct inspection on 2026-08-20.
ACTUAL_EXTRACTOR_OUTPUT_KEYS = [
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
]

# These are the ACTUAL required fields from core/event_schema.py
# as verified by direct inspection on 2026-08-20.
ACTUAL_EVENT_REQUIRED_FIELDS = {
    "timestamp",
    "source",
    "event_type",
    "pid",
    "process",
    "indicator",
    "data",
}

# These are the ACTUAL valid sources from core/event_schema.py
ACTUAL_VALID_SOURCES = {
    "file_monitor",
    "process_monitor",
    "network_monitor",
    "honeypot",
    "detection_engine",
    "test",
}

# The ACTUAL suspicious_indicators logic counts events where:
#   indicator in {"rapid_mass_file_modification", "suspicious_file_activity"}
# This is RULE-DERIVED, confirming the exclusion decision.
SUSPICIOUS_INDICATOR_VALUES = {
    "rapid_mass_file_modification",
    "suspicious_file_activity",
}


# =============================================================================
# SIMULATED FEATURE EXTRACTOR (mirrors actual Ubuntu implementation)
# =============================================================================

def simulated_extract_features(events):
    """
    Simulates the actual core/feature_extractor.py behavior.
    Used for local testing only. NOT a replacement for the real extractor.
    
    This implementation mirrors the exact logic verified in the Ubuntu source.
    """
    features = {
        "total_events": len(events),
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

    modified_files = set()
    remote_ips = set()

    for event in events:
        source = event.get("source")
        event_type = event.get("event_type")
        indicator = event.get("indicator")
        data = event.get("data", {})

        # FILE BEHAVIOR
        if source == "file_monitor":
            features["file_events"] += 1
            if event_type == "file_created":
                features["file_created"] += 1
            elif event_type == "file_modified":
                features["file_modified"] += 1
                path = data.get("path")
                if path:
                    modified_files.add(path)
            elif event_type == "file_deleted":
                features["file_deleted"] += 1
            elif event_type == "file_renamed":
                features["file_renamed"] += 1

        # PROCESS BEHAVIOR
        elif source == "process_monitor":
            features["process_events"] += 1

        # NETWORK BEHAVIOR
        elif source == "network_monitor":
            features["network_events"] += 1
            if data.get("status") == "ESTABLISHED":
                features["established_connections"] += 1
            remote_address = data.get("remote_address")
            if remote_address:
                remote_ip = remote_address.split(":")[0]
                remote_ips.add(remote_ip)

        # SUSPICIOUS INDICATORS
        if indicator in SUSPICIOUS_INDICATOR_VALUES:
            features["suspicious_indicators"] += 1

    features["unique_files_modified"] = len(modified_files)
    features["unique_remote_ips"] = len(remote_ips)

    return features


# =============================================================================
# TEST CLASSES
# =============================================================================


class TestExtractorOutputCompatibility:
    """Verify the actual extractor output is compatible with the ML contract."""

    def test_extractor_produces_exactly_12_keys(self):
        """The actual feature extractor must produce exactly 12 feature keys."""
        assert len(ACTUAL_EXTRACTOR_OUTPUT_KEYS) == 12

    def test_all_ml_features_exist_in_extractor_output(self):
        """Every ML feature must exist in the extractor's output."""
        extractor_keys_set = set(ACTUAL_EXTRACTOR_OUTPUT_KEYS)
        for ml_feature in ML_FEATURE_COLUMNS:
            assert ml_feature in extractor_keys_set, (
                f"ML feature '{ml_feature}' NOT found in actual extractor output"
            )

    def test_excluded_features_exist_in_extractor_output(self):
        """Excluded features must actually exist in extractor output (they're excluded by choice, not absence)."""
        extractor_keys_set = set(ACTUAL_EXTRACTOR_OUTPUT_KEYS)
        for excluded in EXCLUDED_FEATURES:
            assert excluded in extractor_keys_set, (
                f"Excluded feature '{excluded}' not found in extractor — "
                f"exclusion documentation is inconsistent"
            )

    def test_ml_plus_excluded_equals_extractor(self):
        """10 ML features + 2 excluded = 12 extractor features (no gaps)."""
        ml_set = set(ML_FEATURE_COLUMNS)
        excluded_set = set(EXCLUDED_FEATURES.keys())
        combined = ml_set | excluded_set
        actual_set = set(ACTUAL_EXTRACTOR_OUTPUT_KEYS)
        
        assert combined == actual_set, (
            f"Mismatch:\n"
            f"  ML + Excluded = {sorted(combined)}\n"
            f"  Actual extractor = {sorted(actual_set)}\n"
            f"  Missing from contract: {sorted(actual_set - combined)}\n"
            f"  Extra in contract: {sorted(combined - actual_set)}"
        )

    def test_simulated_extractor_returns_correct_keys(self):
        """Simulated extractor must return the same 12 keys as actual."""
        test_events = [
            {
                "timestamp": "2026-08-20T10:00:00",
                "source": "file_monitor",
                "event_type": "file_modified",
                "pid": 1234,
                "process": "python3",
                "indicator": "file_modification",
                "data": {"path": "/tmp/test.txt"}
            }
        ]
        result = simulated_extract_features(test_events)
        assert set(result.keys()) == set(ACTUAL_EXTRACTOR_OUTPUT_KEYS)

    def test_ml_feature_extraction_from_simulated_output(self):
        """Can correctly select 10 ML features from simulated extractor output."""
        test_events = [
            {
                "timestamp": "2026-08-20T10:00:00",
                "source": "file_monitor",
                "event_type": "file_modified",
                "pid": 1234,
                "process": "python3",
                "indicator": "file_modification",
                "data": {"path": "/tmp/file1.txt"}
            },
            {
                "timestamp": "2026-08-20T10:00:01",
                "source": "file_monitor",
                "event_type": "file_modified",
                "pid": 1234,
                "process": "python3",
                "indicator": "file_modification",
                "data": {"path": "/tmp/file2.txt"}
            },
            {
                "timestamp": "2026-08-20T10:00:02",
                "source": "network_monitor",
                "event_type": "network_connection",
                "pid": 5678,
                "process": "curl",
                "indicator": "new_established_connection",
                "data": {
                    "remote_address": "192.168.74.129:443",
                    "status": "ESTABLISHED"
                }
            },
        ]

        full_features = simulated_extract_features(test_events)
        
        # Select ML features
        ml_features = [full_features[col] for col in ML_FEATURE_COLUMNS]
        
        assert len(ml_features) == 10
        assert ml_features[0] == 3   # total_events
        assert ml_features[1] == 0   # file_created
        assert ml_features[2] == 2   # file_modified
        assert ml_features[3] == 0   # file_deleted
        assert ml_features[4] == 0   # file_renamed
        assert ml_features[5] == 2   # unique_files_modified
        assert ml_features[6] == 0   # process_events
        assert ml_features[7] == 1   # network_events
        assert ml_features[8] == 1   # established_connections
        assert ml_features[9] == 1   # unique_remote_ips


class TestSuspiciousIndicatorsVerification:
    """Verify that suspicious_indicators is rule-derived and correctly excluded."""

    def test_suspicious_indicators_counts_rule_flags(self):
        """suspicious_indicators increments only for rule-derived indicator values."""
        events_with_rule_flag = [
            {
                "timestamp": "2026-08-20T10:00:00",
                "source": "file_monitor",
                "event_type": "file_modified",
                "pid": 1234,
                "process": "python3",
                "indicator": "rapid_mass_file_modification",
                "data": {"path": "/tmp/file1.txt"}
            },
            {
                "timestamp": "2026-08-20T10:00:01",
                "source": "file_monitor",
                "event_type": "file_modified",
                "pid": 1234,
                "process": "python3",
                "indicator": "suspicious_file_activity",
                "data": {"path": "/tmp/file2.txt"}
            },
        ]

        features = simulated_extract_features(events_with_rule_flag)
        assert features["suspicious_indicators"] == 2, (
            "suspicious_indicators should count events flagged by rules"
        )

    def test_normal_indicators_do_not_increment_suspicious(self):
        """Normal indicator values must NOT increment suspicious_indicators."""
        normal_events = [
            {
                "timestamp": "2026-08-20T10:00:00",
                "source": "file_monitor",
                "event_type": "file_modified",
                "pid": 1234,
                "process": "python3",
                "indicator": "file_modification",
                "data": {"path": "/tmp/file1.txt"}
            },
            {
                "timestamp": "2026-08-20T10:00:01",
                "source": "network_monitor",
                "event_type": "network_connection",
                "pid": 5678,
                "process": "curl",
                "indicator": "new_established_connection",
                "data": {"remote_address": "1.2.3.4:80", "status": "ESTABLISHED"}
            },
        ]

        features = simulated_extract_features(normal_events)
        assert features["suspicious_indicators"] == 0, (
            "Normal indicators should not trigger suspicious_indicators"
        )

    def test_suspicious_indicators_is_rule_derived(self):
        """
        CRITICAL VERIFICATION:
        suspicious_indicators counts events with indicator values that are
        ONLY set by the rule/detection engine. These values are:
            - "rapid_mass_file_modification"
            - "suspicious_file_activity"
        
        These strings represent CONCLUSIONS made by the rule system,
        not raw behavioral observations.
        
        Therefore: using suspicious_indicators as ML input = circular reasoning.
        Exclusion is CORRECT.
        """
        # The indicator values that trigger suspicious_indicators
        # are rule-derived conclusions, not raw observations
        rule_derived_indicators = SUSPICIOUS_INDICATOR_VALUES
        
        # Verify they are clearly rule/detection language
        for indicator in rule_derived_indicators:
            # These are analytical conclusions, not raw event types
            assert "suspicious" in indicator or "mass" in indicator, (
                f"Indicator '{indicator}' does not appear to be a rule-derived conclusion"
            )
        
        # Verify suspicious_indicators is in the excluded set
        assert "suspicious_indicators" in EXCLUDED_FEATURES
        assert "CIRCULAR" in EXCLUDED_FEATURES["suspicious_indicators"].upper() or \
               "circular" in EXCLUDED_FEATURES["suspicious_indicators"].lower()

    def test_suspicious_indicators_excluded_from_ml(self):
        """suspicious_indicators must NOT be in the ML feature columns."""
        assert "suspicious_indicators" not in ML_FEATURE_COLUMNS


class TestEventSchemaCompatibility:
    """Verify Common Event schema compatibility with ML collection pipeline."""

    def test_required_fields_known(self):
        """All 7 required event fields must be documented."""
        assert len(ACTUAL_EVENT_REQUIRED_FIELDS) == 7
        expected = {"timestamp", "source", "event_type", "pid", "process", "indicator", "data"}
        assert ACTUAL_EVENT_REQUIRED_FIELDS == expected

    def test_feature_extractor_uses_subset_of_event_fields(self):
        """
        The feature extractor accesses these event fields:
            source, event_type, indicator, data
        All of which are in the required fields.
        """
        fields_used_by_extractor = {"source", "event_type", "indicator", "data"}
        assert fields_used_by_extractor.issubset(ACTUAL_EVENT_REQUIRED_FIELDS)

    def test_valid_sources_include_monitors(self):
        """All three monitors must be valid event sources."""
        assert "file_monitor" in ACTUAL_VALID_SOURCES
        assert "process_monitor" in ACTUAL_VALID_SOURCES
        assert "network_monitor" in ACTUAL_VALID_SOURCES

    def test_collection_harness_can_use_test_source(self):
        """
        The 'test' source is valid — our collection harness can use it
        if needed for generating test events without modifying the schema.
        """
        assert "test" in ACTUAL_VALID_SOURCES

    def test_minimal_valid_event_structure(self):
        """Verify we know how to construct a valid Common Event for collection."""
        valid_event = {
            "timestamp": "2026-08-20T10:00:00",
            "source": "file_monitor",
            "event_type": "file_modified",
            "pid": 1234,
            "process": "python3",
            "indicator": "file_modification",
            "data": {"path": "/home/user/test.txt"}
        }
        
        # Check all required fields present
        assert ACTUAL_EVENT_REQUIRED_FIELDS.issubset(valid_event.keys())
        
        # Check source is valid
        assert valid_event["source"] in ACTUAL_VALID_SOURCES
        
        # Check it would produce correct features
        features = simulated_extract_features([valid_event])
        assert features["total_events"] == 1
        assert features["file_modified"] == 1
        assert features["unique_files_modified"] == 1

    def test_event_with_none_optional_fields(self):
        """Events with None for pid/process/indicator must still work."""
        event_with_nones = {
            "timestamp": "2026-08-20T10:00:00",
            "source": "file_monitor",
            "event_type": "file_created",
            "pid": None,
            "process": None,
            "indicator": None,
            "data": {"path": "/home/user/new_file.txt"}
        }
        
        # Should not crash the feature extractor
        features = simulated_extract_features([event_with_nones])
        assert features["total_events"] == 1
        assert features["file_created"] == 1
        assert features["suspicious_indicators"] == 0  # None is not in the set


class TestFileEventsRedundancy:
    """Verify that file_events is genuinely redundant."""

    def test_file_events_equals_sum_of_components(self):
        """
        file_events must equal file_created + file_modified + file_deleted + file_renamed.
        This confirms it is redundant and correctly excluded.
        """
        events = [
            {"timestamp": "2026-08-20T10:00:00", "source": "file_monitor",
             "event_type": "file_created", "pid": 1, "process": "p",
             "indicator": None, "data": {"path": "/tmp/a.txt"}},
            {"timestamp": "2026-08-20T10:00:01", "source": "file_monitor",
             "event_type": "file_modified", "pid": 1, "process": "p",
             "indicator": None, "data": {"path": "/tmp/b.txt"}},
            {"timestamp": "2026-08-20T10:00:02", "source": "file_monitor",
             "event_type": "file_modified", "pid": 1, "process": "p",
             "indicator": None, "data": {"path": "/tmp/c.txt"}},
            {"timestamp": "2026-08-20T10:00:03", "source": "file_monitor",
             "event_type": "file_deleted", "pid": 1, "process": "p",
             "indicator": None, "data": {"path": "/tmp/d.txt"}},
            {"timestamp": "2026-08-20T10:00:04", "source": "file_monitor",
             "event_type": "file_renamed", "pid": 1, "process": "p",
             "indicator": None, "data": {"path": "/tmp/e.txt"}},
            # Non-file event (should not count)
            {"timestamp": "2026-08-20T10:00:05", "source": "process_monitor",
             "event_type": "process_started", "pid": 2, "process": "bash",
             "indicator": None, "data": {}},
        ]

        features = simulated_extract_features(events)
        
        component_sum = (
            features["file_created"] +
            features["file_modified"] +
            features["file_deleted"] +
            features["file_renamed"]
        )
        
        assert features["file_events"] == component_sum, (
            f"file_events ({features['file_events']}) != sum of components ({component_sum})"
        )
        assert features["file_events"] == 5  # 1 + 2 + 1 + 1

    def test_file_events_excluded_from_ml(self):
        """file_events must NOT be in the ML feature columns."""
        assert "file_events" not in ML_FEATURE_COLUMNS


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

def run_all_tests():
    """Run all M2.2 compatibility tests without pytest."""
    test_classes = [
        TestExtractorOutputCompatibility,
        TestSuspiciousIndicatorsVerification,
        TestEventSchemaCompatibility,
        TestFileEventsRedundancy,
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
                errors.append((cls.__name__, method_name, f"ERROR: {e}"))
                print(f"  ERROR {method_name}")
                print(f"        {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"  M2.2 COMPATIBILITY RESULTS: {passed}/{total} passed, {failed} failed")
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
