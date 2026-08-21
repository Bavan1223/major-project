"""
Scenario Definition Validator.

Validates that normal_scenarios.json and ransomware_like_scenarios.json
are well-formed, internally consistent, and compatible with the ML feature contract.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DATA_DIR = os.path.dirname(SCRIPT_DIR)
ML_ROOT = os.path.dirname(ML_DATA_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import (
    FEATURE_VERSION,
    ML_FEATURE_COLUMNS,
    WINDOW_SECONDS,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
)

NORMAL_PATH = os.path.join(SCRIPT_DIR, "normal_scenarios.json")
RANSOMWARE_PATH = os.path.join(SCRIPT_DIR, "ransomware_like_scenarios.json")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


class TestScenarioStructure:
    """Validate scenario file structure."""

    def setup(self):
        self.normal = load_json(NORMAL_PATH)
        self.ransomware = load_json(RANSOMWARE_PATH)

    def test_files_exist(self):
        assert os.path.isfile(NORMAL_PATH), f"Missing: {NORMAL_PATH}"
        assert os.path.isfile(RANSOMWARE_PATH), f"Missing: {RANSOMWARE_PATH}"

    def test_feature_version_matches(self):
        assert self.normal["feature_version"] == FEATURE_VERSION
        assert self.ransomware["feature_version"] == FEATURE_VERSION

    def test_window_seconds_matches(self):
        assert self.normal["window_seconds"] == WINDOW_SECONDS
        assert self.ransomware["window_seconds"] == WINDOW_SECONDS

    def test_normal_label_is_zero(self):
        assert self.normal["label"] == LABEL_NORMAL
        for s in self.normal["scenarios"]:
            assert s["label"] == LABEL_NORMAL, f"{s['scenario_id']} has wrong label"

    def test_ransomware_label_is_one(self):
        assert self.ransomware["label"] == LABEL_RANSOMWARE_LIKE
        for s in self.ransomware["scenarios"]:
            assert s["label"] == LABEL_RANSOMWARE_LIKE, f"{s['scenario_id']} has wrong label"

    def test_normal_has_10_scenarios(self):
        assert len(self.normal["scenarios"]) == 10, (
            f"Expected 10 normal scenarios, got {len(self.normal['scenarios'])}"
        )

    def test_ransomware_has_10_scenarios(self):
        assert len(self.ransomware["scenarios"]) == 10, (
            f"Expected 10 ransomware scenarios, got {len(self.ransomware['scenarios'])}"
        )

    def test_normal_scenario_ids_sequential(self):
        expected_ids = [f"N{i}" for i in range(1, 11)]
        actual_ids = [s["scenario_id"] for s in self.normal["scenarios"]]
        assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"

    def test_ransomware_scenario_ids_sequential(self):
        expected_ids = [f"R{i}" for i in range(1, 11)]
        actual_ids = [s["scenario_id"] for s in self.ransomware["scenarios"]]
        assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"

    def test_no_duplicate_scenario_ids(self):
        all_ids = (
            [s["scenario_id"] for s in self.normal["scenarios"]] +
            [s["scenario_id"] for s in self.ransomware["scenarios"]]
        )
        assert len(all_ids) == len(set(all_ids)), "Duplicate scenario IDs found"


class TestScenarioContent:
    """Validate scenario content and expected features."""

    def setup(self):
        self.normal = load_json(NORMAL_PATH)
        self.ransomware = load_json(RANSOMWARE_PATH)
        self.all_scenarios = self.normal["scenarios"] + self.ransomware["scenarios"]

    def test_all_scenarios_have_required_fields(self):
        required = {"scenario_id", "name", "purpose", "label", "parameters",
                    "execution", "expected_features", "variations", "randomization"}
        for s in self.all_scenarios:
            missing = required - set(s.keys())
            assert not missing, (
                f"{s['scenario_id']} missing fields: {missing}"
            )

    def test_expected_features_use_ml_columns(self):
        for s in self.all_scenarios:
            ef = s["expected_features"]
            for col in ML_FEATURE_COLUMNS:
                assert col in ef, (
                    f"{s['scenario_id']} missing expected feature: {col}"
                )

    def test_expected_features_are_ranges(self):
        for s in self.all_scenarios:
            ef = s["expected_features"]
            for col in ML_FEATURE_COLUMNS:
                rng = ef[col]
                assert isinstance(rng, list) and len(rng) == 2, (
                    f"{s['scenario_id']}.{col} must be [min, max] range, got {rng}"
                )
                assert rng[0] <= rng[1], (
                    f"{s['scenario_id']}.{col} min > max: {rng}"
                )
                assert rng[0] >= 0, (
                    f"{s['scenario_id']}.{col} has negative min: {rng[0]}"
                )

    def test_all_scenarios_have_variations(self):
        for s in self.all_scenarios:
            assert len(s["variations"]) >= 2, (
                f"{s['scenario_id']} needs at least 2 variations, has {len(s['variations'])}"
            )

    def test_variation_ids_unique_within_scenario(self):
        for s in self.all_scenarios:
            var_ids = [v["variation_id"] for v in s["variations"]]
            assert len(var_ids) == len(set(var_ids)), (
                f"{s['scenario_id']} has duplicate variation IDs"
            )

    def test_all_variation_ids_globally_unique(self):
        all_var_ids = []
        for s in self.all_scenarios:
            for v in s["variations"]:
                all_var_ids.append(v["variation_id"])
        assert len(all_var_ids) == len(set(all_var_ids)), "Duplicate variation IDs across scenarios"

    def test_safety_constraints_present(self):
        assert "safety" in self.normal
        assert "safety" in self.ransomware
        assert self.normal["safety"]["destructive_operations"] is False
        assert self.ransomware["safety"]["destructive_operations"] is False
        assert self.ransomware["safety"]["real_ransomware"] is False
        assert self.ransomware["safety"]["real_encryption"] is False

    def test_no_suspicious_indicators_in_expected_features(self):
        for s in self.all_scenarios:
            assert "suspicious_indicators" not in s["expected_features"], (
                f"{s['scenario_id']} references excluded feature suspicious_indicators"
            )

    def test_no_file_events_in_expected_features(self):
        for s in self.all_scenarios:
            assert "file_events" not in s["expected_features"], (
                f"{s['scenario_id']} references excluded feature file_events"
            )


class TestScenarioDiversity:
    """Validate that scenarios provide behavioral diversity and cross-class overlap."""

    def setup(self):
        self.normal = load_json(NORMAL_PATH)["scenarios"]
        self.ransomware = load_json(RANSOMWARE_PATH)["scenarios"]

    def test_normal_includes_high_activity(self):
        """At least one normal scenario should have total_events max >= 20."""
        max_totals = [s["expected_features"]["total_events"][1] for s in self.normal]
        assert max(max_totals) >= 20, (
            "Normal scenarios lack high-activity examples (max total_events < 20)"
        )

    def test_normal_includes_high_file_modified(self):
        """N8 (log rotation) should show high file_modified but low unique_files."""
        n8 = next(s for s in self.normal if s["scenario_id"] == "N8")
        assert n8["expected_features"]["file_modified"][1] >= 10, (
            "N8 should have high file_modified"
        )
        assert n8["expected_features"]["unique_files_modified"][1] <= 3, (
            "N8 should have low unique_files_modified"
        )

    def test_ransomware_includes_low_intensity(self):
        """R6 should overlap with N3 in unique_files_modified range."""
        r6 = next(s for s in self.ransomware if s["scenario_id"] == "R6")
        n3 = next(s for s in self.normal if s["scenario_id"] == "N3")
        # R6 min should be <= N3 max (overlap exists)
        assert r6["expected_features"]["unique_files_modified"][0] <= n3["expected_features"]["unique_files_modified"][1], (
            "R6 and N3 should have overlapping unique_files_modified ranges"
        )

    def test_multiple_ransomware_signatures(self):
        """Ransomware scenarios must use different primary operation patterns."""
        primary_ops = set()
        for s in self.ransomware:
            ef = s["expected_features"]
            # Determine dominant pattern
            if ef["file_modified"][1] >= 8 and ef["file_renamed"][1] >= 8:
                primary_ops.add("modify_rename")
            elif ef["file_created"][1] >= 8 and ef["file_deleted"][1] >= 8:
                primary_ops.add("create_delete")
            elif ef["file_renamed"][1] >= 10 and ef["file_modified"][1] <= 2:
                primary_ops.add("rename_only")
            elif ef["file_modified"][1] >= 8 and ef["network_events"][1] >= 3:
                primary_ops.add("modify_network")
            elif ef["file_modified"][1] >= 8 and ef["process_events"][1] >= 3:
                primary_ops.add("modify_process")
            elif ef["file_modified"][1] >= 8:
                primary_ops.add("modify_only")
            else:
                primary_ops.add("mixed")

        assert len(primary_ops) >= 4, (
            f"Need at least 4 distinct ransomware patterns, found {len(primary_ops)}: {primary_ops}"
        )

    def test_normal_covers_network_heavy(self):
        """At least one normal scenario should have high network_events."""
        max_network = max(s["expected_features"]["network_events"][1] for s in self.normal)
        assert max_network >= 5, "Normal scenarios lack network-heavy example"

    def test_normal_covers_process_heavy(self):
        """At least one normal scenario should have high process_events."""
        max_process = max(s["expected_features"]["process_events"][1] for s in self.normal)
        assert max_process >= 5, "Normal scenarios lack process-heavy example"

    def test_total_variations_sufficient(self):
        """Total variations should provide enough independent sessions."""
        normal_vars = sum(len(s["variations"]) for s in self.normal)
        ransom_vars = sum(len(s["variations"]) for s in self.ransomware)
        total = normal_vars + ransom_vars
        assert total >= 60, (
            f"Need at least 60 total variations for dataset diversity, have {total}"
        )


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

def run_all_tests():
    test_classes = [
        TestScenarioStructure,
        TestScenarioContent,
        TestScenarioDiversity,
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
    print(f"  SCENARIO VALIDATION: {passed}/{total} passed, {failed} failed")
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
