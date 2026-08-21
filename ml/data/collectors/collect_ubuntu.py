#!/usr/bin/env python3
"""
Ubuntu Lab Collection Script.

This script is designed to run ON the Ubuntu lab machine at:
    ~/ransomware-lab/

It uses the REAL monitors and core/feature_extractor.py to collect
genuine behavioral telemetry for ML training.

USAGE:
    cd ~/ransomware-lab
    python3 -m ml.data.collectors.collect_ubuntu --mode pilot
    python3 -m ml.data.collectors.collect_ubuntu --mode full

PREREQUISITES:
    - Ubuntu lab environment at ~/ransomware-lab/
    - Monitors operational (file_monitor, process_monitor, network_monitor)
    - core/feature_extractor.py accessible
    - ~/ransomware-lab/test-files/ directory exists
    - ml/ directory with scenario definitions present

SAFETY:
    - All file operations restricted to ~/ransomware-lab/test-files/
    - No real ransomware execution
    - No real encryption
    - No destructive operations outside test directory

NOTE:
    This script imports from both the core project (core/) and the ML module (ml/).
    It must be run from the ~/ransomware-lab/ directory.
"""

import sys
import os
import json
import csv
import time
import argparse
from datetime import datetime, timezone

# Ensure project root is in path
PROJECT_ROOT = os.path.expanduser("~/ransomware-lab")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core feature extractor
from core.feature_extractor import extract_features

# Import ML modules
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

TARGET_DIR = os.path.expanduser("~/ransomware-lab/test-files/")
SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "scenarios")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "processed")
METADATA_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "metadata")
RAW_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "raw")

NORMAL_SCENARIOS_PATH = os.path.join(SCENARIOS_DIR, "normal_scenarios.json")
RANSOMWARE_SCENARIOS_PATH = os.path.join(SCENARIOS_DIR, "ransomware_like_scenarios.json")

DATASET_VERSION = "0.1"
CSV_COLUMNS = ["session_id", "window_id", "scenario_id", "label"] + list(ML_FEATURE_COLUMNS)


# =============================================================================
# UBUNTU LAB COLLECTION
# =============================================================================

class UbuntuLabCollector:
    """
    Collects ML training data using the real Ubuntu lab environment.
    
    Uses core/feature_extractor.extract_features() as the single source
    of truth for feature calculation.
    """

    def __init__(self):
        self.runner = ScenarioRunner(target_dir=TARGET_DIR)
        self.session_counter = 0
        self.all_records = []
        self.session_metadata = []
        self.errors = []

    def load_scenarios(self):
        """Load scenario definitions."""
        with open(NORMAL_SCENARIOS_PATH, "r") as f:
            self.normal_scenarios = json.load(f)
        with open(RANSOMWARE_SCENARIOS_PATH, "r") as f:
            self.ransomware_scenarios = json.load(f)
        print(f"  Loaded {len(self.normal_scenarios['scenarios'])} normal scenarios")
        print(f"  Loaded {len(self.ransomware_scenarios['scenarios'])} ransomware-like scenarios")
        return self

    def next_session_id(self):
        """Generate sequential session ID."""
        self.session_counter += 1
        return f"S_{self.session_counter:04d}"

    def run_session(self, scenario, variation=None, seed=None):
        """
        Run one collection session using the REAL feature extractor.
        
        Returns list of feature records from this session.
        """
        session_id = self.next_session_id()
        scenario_id = scenario["scenario_id"]
        label = scenario["label"]

        start_time = datetime.now(timezone.utc).isoformat()

        try:
            # Ensure test directory exists and is clean
            os.makedirs(TARGET_DIR, exist_ok=True)

            # Execute the scenario (generates Common Events)
            events = self.runner.run_scenario(scenario, variation, seed=seed)

            end_time = datetime.now(timezone.utc).isoformat()

            # Use the REAL core feature extractor
            records = process_session_events(
                events=events,
                session_id=session_id,
                scenario_id=scenario_id,
                label=label,
                feature_extractor_fn=extract_features,  # <-- REAL extractor
                window_seconds=WINDOW_SECONDS,
            )

            # Save raw events for traceability
            self._save_raw_events(session_id, events)

            # Record metadata
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
                "extractor": "core.feature_extractor.extract_features",
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
            print(f"    ERROR: {e}")
            return []

    def run_pilot(self):
        """Run 1 variation of each scenario (quick verification)."""
        print("\n" + "=" * 60)
        print("  UBUNTU LAB — PILOT COLLECTION")
        print(f"  Feature Version: {FEATURE_VERSION}")
        print(f"  Window: {WINDOW_SECONDS}s")
        print(f"  Extractor: core.feature_extractor.extract_features")
        print(f"  Target dir: {TARGET_DIR}")
        print("=" * 60)

        for scenario in self.normal_scenarios["scenarios"]:
            variation = scenario["variations"][0]
            seed = hash(variation["variation_id"]) % (2**31)
            print(f"\n  {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
            records = self.run_session(scenario, variation, seed=seed)
            print(f"{len(records)} windows")

        for scenario in self.ransomware_scenarios["scenarios"]:
            variation = scenario["variations"][0]
            seed = hash(variation["variation_id"]) % (2**31)
            print(f"\n  {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
            records = self.run_session(scenario, variation, seed=seed)
            print(f"{len(records)} windows")

        self._print_summary("PILOT")

    def run_full(self):
        """Run ALL variations of ALL scenarios."""
        print("\n" + "=" * 60)
        print("  UBUNTU LAB — FULL COLLECTION")
        print(f"  Feature Version: {FEATURE_VERSION}")
        print(f"  Window: {WINDOW_SECONDS}s")
        print(f"  Extractor: core.feature_extractor.extract_features")
        print(f"  Target dir: {TARGET_DIR}")
        print("=" * 60)

        # Normal scenarios
        print("\n  --- NORMAL SCENARIOS ---")
        for scenario in self.normal_scenarios["scenarios"]:
            for variation in scenario["variations"]:
                seed = hash(variation["variation_id"]) % (2**31)
                print(f"  {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
                records = self.run_session(scenario, variation, seed=seed)
                print(f"{len(records)} windows")

        # Ransomware-like scenarios
        print("\n  --- RANSOMWARE-LIKE SCENARIOS ---")
        for scenario in self.ransomware_scenarios["scenarios"]:
            for variation in scenario["variations"]:
                seed = hash(variation["variation_id"]) % (2**31)
                print(f"  {scenario['scenario_id']} ({variation['variation_id']})...", end=" ")
                records = self.run_session(scenario, variation, seed=seed)
                print(f"{len(records)} windows")

        self._print_summary("FULL")

    def save_dataset(self, filename=None):
        """Save dataset to CSV."""
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
        """Save session metadata."""
        os.makedirs(METADATA_DIR, exist_ok=True)
        filepath = os.path.join(METADATA_DIR, "sessions.json")

        metadata = {
            "dataset_version": DATASET_VERSION,
            "feature_version": FEATURE_VERSION,
            "window_seconds": WINDOW_SECONDS,
            "collection_environment": "ubuntu_lab",
            "collection_date": datetime.now(timezone.utc).isoformat(),
            "extractor_used": "core.feature_extractor.extract_features",
            "target_directory": TARGET_DIR,
            "total_sessions": len(self.session_metadata),
            "total_records": len(self.all_records),
            "normal_records": sum(1 for r in self.all_records if r["label"] == LABEL_NORMAL),
            "ransomware_records": sum(1 for r in self.all_records if r["label"] == LABEL_RANSOMWARE_LIKE),
            "errors": self.errors,
            "sessions": self.session_metadata,
        }

        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"  Metadata saved: {filepath}")
        return filepath

    def _save_raw_events(self, session_id, events):
        """Save raw events for a session (traceability)."""
        os.makedirs(RAW_DIR, exist_ok=True)
        filepath = os.path.join(RAW_DIR, f"{session_id}_events.jsonl")
        with open(filepath, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

    def _print_summary(self, mode):
        """Print collection summary."""
        normal_count = sum(1 for r in self.all_records if r["label"] == LABEL_NORMAL)
        ransom_count = sum(1 for r in self.all_records if r["label"] == LABEL_RANSOMWARE_LIKE)

        print(f"\n{'='*60}")
        print(f"  {mode} COLLECTION COMPLETE")
        print(f"{'='*60}")
        print(f"  Sessions:         {len(self.session_metadata)}")
        print(f"  Total records:    {len(self.all_records)}")
        print(f"  NORMAL:           {normal_count}")
        print(f"  RANSOMWARE_LIKE:  {ransom_count}")
        if normal_count + ransom_count > 0:
            print(f"  Balance:          {normal_count/(normal_count+ransom_count)*100:.1f}% / {ransom_count/(normal_count+ransom_count)*100:.1f}%")
        if self.errors:
            print(f"  ERRORS:           {len(self.errors)}")
            for err in self.errors:
                print(f"    {err['session_id']} ({err['scenario_id']}): {err['error']}")
        print(f"{'='*60}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Ubuntu Lab ML Dataset Collection",
        epilog="Run from ~/ransomware-lab/ directory"
    )
    parser.add_argument("--mode", choices=["pilot", "full"], default="pilot",
                        help="pilot = 1 variation each; full = all variations")
    parser.add_argument("--output", default=None,
                        help="Output CSV filename (default: dataset_v0.1.csv)")

    args = parser.parse_args()

    # Verify we're in the right place
    if not os.path.isfile(os.path.join(PROJECT_ROOT, "core", "feature_extractor.py")):
        print("ERROR: core/feature_extractor.py not found.")
        print("       This script must be run from ~/ransomware-lab/")
        sys.exit(1)

    if not os.path.isdir(TARGET_DIR):
        print(f"Creating target directory: {TARGET_DIR}")
        os.makedirs(TARGET_DIR, exist_ok=True)

    collector = UbuntuLabCollector()
    collector.load_scenarios()

    if args.mode == "pilot":
        collector.run_pilot()
    else:
        collector.run_full()

    collector.save_dataset(args.output)
    collector.save_metadata()

    # Final status
    if collector.errors:
        print(f"\n  WARNING: {len(collector.errors)} errors occurred during collection.")
        sys.exit(1)
    else:
        print("\n  Collection completed successfully.")
        print("  Next step: python3 -m ml.data.validate_dataset ml/data/processed/dataset_v0.1.csv")


if __name__ == "__main__":
    main()
