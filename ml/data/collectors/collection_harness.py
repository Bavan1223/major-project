"""
Data Collection Harness — Orchestrates dataset generation.

This is the main entry point for generating the ML training dataset.
It coordinates:
    1. Loading scenario definitions
    2. Running scenarios via ScenarioRunner
    3. Extracting features via WindowExtractor
    4. Saving records to CSV
    5. Recording session metadata

USAGE (on Ubuntu lab):
    python -m ml.data.collectors.collection_harness --mode pilot
    python -m ml.data.collectors.collection_harness --mode full

SAFETY:
    All operations restricted to ~/ransomware-lab/test-files/
    No real ransomware. No real encryption. No destructive operations.
"""

import json
import os
import sys
import csv
import time
import random
from datetime import datetime, timezone

# Path setup
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
from ml.data.collectors.scenario_runner import ScenarioRunner
from ml.data.collectors.window_extractor import process_session_events


# =============================================================================
# CONFIGURATION
# =============================================================================

SCENARIOS_DIR = os.path.join(ML_DATA_DIR, "scenarios")
RAW_DIR = os.path.join(ML_DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(ML_DATA_DIR, "processed")
METADATA_DIR = os.path.join(ML_DATA_DIR, "metadata")

NORMAL_SCENARIOS_PATH = os.path.join(SCENARIOS_DIR, "normal_scenarios.json")
RANSOMWARE_SCENARIOS_PATH = os.path.join(SCENARIOS_DIR, "ransomware_like_scenarios.json")

DATASET_VERSION = "0.1"

# CSV column order (metadata + features + label)
CSV_COLUMNS = ["session_id", "window_id", "scenario_id", "label"] + list(ML_FEATURE_COLUMNS)


# =============================================================================
# COLLECTION HARNESS
# =============================================================================

class CollectionHarness:
    """
    Orchestrates controlled dataset collection.
    
    Manages session IDs, runs scenarios, extracts features,
    validates records, and saves the dataset.
    """

    def __init__(self, target_dir=None, feature_extractor_fn=None):
        """
        Args:
            target_dir: Directory for file operations (must exist on Ubuntu lab)
            feature_extractor_fn: The actual core/feature_extractor.extract_features
                                  function. If None, uses simulated extractor.
        """
        self.target_dir = target_dir
        self.feature_extractor_fn = feature_extractor_fn
        self.runner = ScenarioRunner(target_dir=target_dir)
        self.session_counter = 0
        self.all_records = []
        self.session_metadata = []
        self.errors = []

    def load_scenarios(self):
        """Load scenario definitions from JSON files."""
        with open(NORMAL_SCENARIOS_PATH, "r") as f:
            self.normal_scenarios = json.load(f)
        with open(RANSOMWARE_SCENARIOS_PATH, "r") as f:
            self.ransomware_scenarios = json.load(f)
        return self

    def next_session_id(self):
        """Generate the next sequential session ID."""
        self.session_counter += 1
        return f"S_{self.session_counter:04d}"

    def run_single_session(self, scenario, variation=None, seed=None):
        """
        Execute one scenario session and collect the resulting records.
        
        Args:
            scenario: Scenario dict from definitions
            variation: Optional variation dict
            seed: Random seed for reproducibility
            
        Returns:
            list: Feature records from this session
        """
        session_id = self.next_session_id()
        scenario_id = scenario["scenario_id"]
        label = scenario["label"]

        # Record start time
        start_time = datetime.now(timezone.utc).isoformat()

        try:
            # Run the scenario
            events = self.runner.run_scenario(scenario, variation, seed=seed)

            # Record end time
            end_time = datetime.now(timezone.utc).isoformat()

            # Process events into windowed feature records
            records = process_session_events(
                events=events,
                session_id=session_id,
                scenario_id=scenario_id,
                label=label,
                feature_extractor_fn=self.feature_extractor_fn,
                window_seconds=WINDOW_SECONDS,
            )

            # Record session metadata
            meta = {
                "session_id": session_id,
                "scenario_id": scenario_id,
                "scenario_type": "NORMAL" if label == 0 else "RANSOMWARE_LIKE",
                "label": label,
                "start_time": start_time,
                "end_time": end_time,
                "event_count": len(events),
                "window_count": len(records),
                "variation": variation.get("variation_id") if variation else None,
                "seed": seed,
                "feature_version": FEATURE_VERSION,
            }
            self.session_metadata.append(meta)
            self.all_records.extend(records)

            # Cleanup test files
            self.runner.cleanup()

            return records

        except Exception as e:
            end_time = datetime.now(timezone.utc).isoformat()
            self.errors.append({
                "session_id": session_id,
                "scenario_id": scenario_id,
                "error": str(e),
                "time": end_time,
            })
            self.runner.cleanup()
            return []

    def run_pilot(self):
        """
        Run a minimal pilot collection: 1 variation of each scenario.
        Purpose: Verify the pipeline works before full collection.
        """
        print("=" * 60)
        print("  PILOT DATA COLLECTION")
        print(f"  Feature Version: {FEATURE_VERSION}")
        print(f"  Window: {WINDOW_SECONDS}s")
        print("=" * 60)

        # Run 1 variation of each normal scenario
        for scenario in self.normal_scenarios["scenarios"]:
            variation = scenario["variations"][0]
            seed = hash(variation["variation_id"]) % (2**31)
            print(f"\n  Running {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
            records = self.run_single_session(scenario, variation, seed=seed)
            print(f"{len(records)} windows")

        # Run 1 variation of each ransomware-like scenario
        for scenario in self.ransomware_scenarios["scenarios"]:
            variation = scenario["variations"][0]
            seed = hash(variation["variation_id"]) % (2**31)
            print(f"\n  Running {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
            records = self.run_single_session(scenario, variation, seed=seed)
            print(f"{len(records)} windows")

        self._print_summary("PILOT")
        return self

    def run_full(self):
        """
        Run full collection: all variations of all scenarios.
        """
        print("=" * 60)
        print("  FULL DATA COLLECTION")
        print(f"  Feature Version: {FEATURE_VERSION}")
        print(f"  Window: {WINDOW_SECONDS}s")
        print("=" * 60)

        # Run all normal scenarios with all variations
        for scenario in self.normal_scenarios["scenarios"]:
            for variation in scenario["variations"]:
                seed = hash(variation["variation_id"]) % (2**31)
                print(f"  Running {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
                records = self.run_single_session(scenario, variation, seed=seed)
                print(f"{len(records)} windows")

        # Run all ransomware-like scenarios with all variations
        for scenario in self.ransomware_scenarios["scenarios"]:
            for variation in scenario["variations"]:
                seed = hash(variation["variation_id"]) % (2**31)
                print(f"  Running {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
                records = self.run_single_session(scenario, variation, seed=seed)
                print(f"{len(records)} windows")

        self._print_summary("FULL")
        return self

    def save_dataset(self, filename=None):
        """
        Save collected records to CSV.
        
        Args:
            filename: Output filename (defaults to dataset_v{VERSION}.csv)
        """
        if not filename:
            filename = f"dataset_v{DATASET_VERSION}.csv"

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        filepath = os.path.join(PROCESSED_DIR, filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for record in self.all_records:
                writer.writerow(record)

        print(f"\n  Dataset saved: {filepath}")
        print(f"  Total records: {len(self.all_records)}")
        return filepath

    def save_metadata(self):
        """Save session metadata to JSON."""
        os.makedirs(METADATA_DIR, exist_ok=True)
        filepath = os.path.join(METADATA_DIR, "sessions.json")

        metadata = {
            "dataset_version": DATASET_VERSION,
            "feature_version": FEATURE_VERSION,
            "window_seconds": WINDOW_SECONDS,
            "collection_environment": "ubuntu_lab",
            "collection_date": datetime.now(timezone.utc).isoformat(),
            "total_sessions": len(self.session_metadata),
            "total_records": len(self.all_records),
            "errors": self.errors,
            "sessions": self.session_metadata,
        }

        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"  Metadata saved: {filepath}")
        return filepath

    def _print_summary(self, mode):
        """Print collection summary."""
        normal_count = sum(1 for r in self.all_records if r["label"] == LABEL_NORMAL)
        ransom_count = sum(1 for r in self.all_records if r["label"] == LABEL_RANSOMWARE_LIKE)

        print(f"\n{'='*60}")
        print(f"  {mode} COLLECTION SUMMARY")
        print(f"{'='*60}")
        print(f"  Sessions:    {len(self.session_metadata)}")
        print(f"  Records:     {len(self.all_records)}")
        print(f"  NORMAL:      {normal_count}")
        print(f"  RANSOMWARE:  {ransom_count}")
        if self.errors:
            print(f"  ERRORS:      {len(self.errors)}")
        print(f"{'='*60}")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ML Dataset Collection Harness")
    parser.add_argument("--mode", choices=["pilot", "full"], default="pilot",
                        help="Collection mode: pilot (1 variation each) or full (all variations)")
    parser.add_argument("--target-dir", default=None,
                        help="Target directory for file operations")
    parser.add_argument("--use-core-extractor", action="store_true",
                        help="Use actual core/feature_extractor.py (requires Ubuntu lab)")

    args = parser.parse_args()

    # Attempt to import core feature extractor if requested
    feature_extractor_fn = None
    if args.use_core_extractor:
        try:
            # This path works when run from ~/ransomware-lab/
            sys.path.insert(0, os.path.expanduser("~/ransomware-lab"))
            from core.feature_extractor import extract_features
            feature_extractor_fn = extract_features
            print("  Using CORE feature extractor")
        except ImportError as e:
            print(f"  WARNING: Could not import core extractor: {e}")
            print("  Falling back to simulated extractor")

    harness = CollectionHarness(
        target_dir=args.target_dir,
        feature_extractor_fn=feature_extractor_fn,
    )
    harness.load_scenarios()

    if args.mode == "pilot":
        harness.run_pilot()
    else:
        harness.run_full()

    harness.save_dataset()
    harness.save_metadata()

    if harness.errors:
        print("\n  ERRORS OCCURRED:")
        for err in harness.errors:
            print(f"    {err['session_id']} ({err['scenario_id']}): {err['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
