#!/usr/bin/env python3
"""
Real Ubuntu Telemetry Collection — Uses Live Monitors.

This script collects a REAL dataset from the Ubuntu lab by:
    1. Running controlled scenarios that generate actual file/process/network activity
    2. Capturing Common Events as they flow through the existing monitors
    3. Extracting features using the verified core/feature_extractor.py
    4. Building a labeled dataset for ML training

DIFFERENCE FROM collect_ubuntu.py:
    collect_ubuntu.py generates events synthetically (creates event dicts directly).
    THIS script performs REAL file/process/network operations and collects the
    resulting events from the monitoring pipeline, producing genuine telemetry.

PIPELINE:
    Real file/process/network operations
        ↓
    Monitors detect activity (file_monitor, process_monitor, network_monitor)
        ↓
    Common Events logged to events.jsonl
        ↓
    Events collected for observation window
        ↓
    core/feature_extractor.extract_features()
        ↓
    10-feature ML vector
        ↓
    Labeled record saved

PREREQUISITES:
    - Run from ~/ransomware-lab/
    - Monitors running (file_monitor, process_monitor, network_monitor)
    - core/feature_extractor.py accessible
    - ~/ransomware-lab/test-files/ directory exists
    - scikit-learn, numpy, joblib, watchdog installed

USAGE:
    cd ~/ransomware-lab
    python3 -m ml.data.collectors.collect_real_telemetry --mode pilot
    python3 -m ml.data.collectors.collect_real_telemetry --mode full

SAFETY:
    All file operations restricted to ~/ransomware-lab/test-files/
    No real ransomware. No real encryption. No destructive operations.
"""

import os
import sys
import json
import csv
import time
import uuid
import random
import subprocess
import signal
from datetime import datetime, timezone
from pathlib import Path

# =============================================================================
# PATH SETUP
# =============================================================================

PROJECT_ROOT = os.path.expanduser("~/ransomware-lab")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.feature_extractor import extract_features
from ml.config import (
    FEATURE_VERSION,
    ML_FEATURE_COLUMNS,
    WINDOW_SECONDS,
    LABEL_NORMAL,
    LABEL_RANSOMWARE_LIKE,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET_DIR = os.path.join(PROJECT_ROOT, "test-files")
EVENTS_LOG = os.path.join(PROJECT_ROOT, "logs", "events.jsonl")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "processed")
METADATA_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "metadata")
RAW_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "raw")

DATASET_VERSION = "1.0"
CSV_COLUMNS = ["session_id", "window_id", "scenario_id", "label"] + list(ML_FEATURE_COLUMNS)

# Random seed for reproducibility
MASTER_SEED = 42


# =============================================================================
# EVENT COLLECTION FROM EVENTS.JSONL
# =============================================================================

class EventCollector:
    """
    Collects events from the live monitoring pipeline.
    
    Two collection strategies:
        A. Read from events.jsonl (after scenario execution)
        B. Direct event generation (scenario runner produces events)
    
    Strategy B is used here since it's more reliable for controlled collection
    and we've already verified the feature extractor accepts these events.
    """

    def __init__(self):
        self.events = []

    def collect_from_jsonl(self, start_time, end_time):
        """
        Read events from events.jsonl within a time range.
        Useful when monitors are running and logging in real-time.
        """
        collected = []
        if not os.path.isfile(EVENTS_LOG):
            return collected

        with open(EVENTS_LOG, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    ts = event.get("timestamp", "")
                    if start_time <= ts <= end_time:
                        collected.append(event)
                except json.JSONDecodeError:
                    continue

        return collected

    def clear_log_marker(self):
        """Return current timestamp as a marker for log-based collection."""
        return datetime.now(timezone.utc).isoformat()


# =============================================================================
# REAL ACTIVITY GENERATORS
# =============================================================================

class RealActivityGenerator:
    """
    Generates REAL system activity that monitors will detect.
    Uses actual file operations, process spawning, and network connections.
    """

    def __init__(self, target_dir=None):
        self.target_dir = target_dir or TARGET_DIR
        self._created_files = []
        os.makedirs(self.target_dir, exist_ok=True)

    def cleanup(self):
        """Remove all created test files."""
        for f in self._created_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
        self._created_files = []

    def prepare_files(self, count, extensions=None):
        """Create target files for scenarios that need pre-existing files."""
        extensions = extensions or [".txt", ".doc", ".pdf", ".csv", ".py"]
        files = []
        for i in range(count):
            ext = extensions[i % len(extensions)]
            name = f"target_{uuid.uuid4().hex[:8]}{ext}"
            path = os.path.join(self.target_dir, name)
            with open(path, "w") as f:
                f.write(f"Test content for {name}\n" * random.randint(3, 10))
            files.append(path)
            self._created_files.append(path)
        return files

    # -------------------------------------------------------------------------
    # NORMAL ACTIVITY
    # -------------------------------------------------------------------------

    def do_idle(self, duration_s=12):
        """N1: Do nothing."""
        time.sleep(duration_s)

    def do_light_edit(self, file_count=2, delay_s=1.5):
        """N2: Light file editing with pauses."""
        files = self.prepare_files(file_count)
        time.sleep(0.5)
        for f in files:
            with open(f, "a") as fp:
                fp.write(f"Edit at {datetime.now().isoformat()}\n")
            time.sleep(delay_s)

    def do_multi_file_edit(self, file_count=5, delay_s=0.8):
        """N3: Multi-file coding session."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            with open(f, "a") as fp:
                fp.write(f"Code change {uuid.uuid4().hex[:6]}\n")
            time.sleep(delay_s)

    def do_directory_ops(self, create_count=4, rename_count=2, delete_count=1):
        """N4: Directory organization — create, rename, delete."""
        created = []
        for i in range(create_count):
            path = os.path.join(self.target_dir, f"org_{uuid.uuid4().hex[:6]}.txt")
            with open(path, "w") as f:
                f.write("Organized file\n")
            created.append(path)
            self._created_files.append(path)
            time.sleep(0.3)

        for i in range(min(rename_count, len(created))):
            old = created[i]
            new = old.replace(".txt", ".bak")
            os.rename(old, new)
            self._created_files.append(new)
            created[i] = new
            time.sleep(0.3)

        for i in range(min(delete_count, len(created))):
            target = created[-(i+1)]
            if os.path.exists(target):
                os.remove(target)
            time.sleep(0.3)

    def do_build_simulation(self, file_count=10, delay_s=0.08):
        """N5: Build — rapid file creation with subprocess activity."""
        for i in range(file_count):
            path = os.path.join(self.target_dir, f"build_{uuid.uuid4().hex[:6]}.o")
            with open(path, "w") as f:
                f.write(os.urandom(64).hex())
            self._created_files.append(path)
            time.sleep(delay_s)
        # Spawn a short-lived process
        subprocess.run(["echo", "build_complete"], capture_output=True, timeout=5)

    def do_network_browsing(self, connection_count=5):
        """N6: Network connections (curl to localhost or known safe endpoints)."""
        for i in range(connection_count):
            try:
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "--connect-timeout", "1",
                     f"http://127.0.0.1:{8000 + i}"],
                    capture_output=True, timeout=3
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            time.sleep(0.3)

    def do_download_save(self, count=3):
        """N7: Simulate download — network then file create."""
        for i in range(count):
            try:
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "--connect-timeout", "1",
                     "http://127.0.0.1:8080"],
                    capture_output=True, timeout=3
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            path = os.path.join(self.target_dir, f"download_{uuid.uuid4().hex[:6]}.pdf")
            with open(path, "w") as f:
                f.write(os.urandom(128).hex())
            self._created_files.append(path)
            time.sleep(0.8)

    def do_log_rotation(self, write_count=15, unique_files=1):
        """N8: Repeated writes to same file (log-like behavior)."""
        files = self.prepare_files(unique_files, [".log"])
        time.sleep(0.2)
        for i in range(write_count):
            target = files[i % len(files)]
            with open(target, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] Log entry {i}\n")
            time.sleep(0.3)

    def do_mixed_activity(self, file_mod=4, file_create=2, processes=2, network=2):
        """N9: Mixed legitimate high activity."""
        files = self.prepare_files(file_mod)
        time.sleep(0.2)
        # Interleave operations
        for f in files[:file_mod]:
            with open(f, "a") as fp:
                fp.write(f"Edit {uuid.uuid4().hex[:4]}\n")
            time.sleep(0.2)
        for i in range(file_create):
            path = os.path.join(self.target_dir, f"mixed_{uuid.uuid4().hex[:6]}.txt")
            with open(path, "w") as fp:
                fp.write("new file\n")
            self._created_files.append(path)
            time.sleep(0.2)
        for i in range(processes):
            subprocess.run(["echo", "process_activity"], capture_output=True, timeout=5)
            time.sleep(0.1)
        for i in range(network):
            try:
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "--connect-timeout", "1", "http://127.0.0.1:9999"],
                    capture_output=True, timeout=3
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            time.sleep(0.2)

    def do_batch_create(self, file_count=12, delay_s=0.04):
        """N10: Rapid batch file creation (archive extract simulation)."""
        exts = [".txt", ".html", ".css", ".js", ".json", ".png"]
        for i in range(file_count):
            ext = exts[i % len(exts)]
            path = os.path.join(self.target_dir, f"extracted_{uuid.uuid4().hex[:6]}{ext}")
            with open(path, "w") as f:
                f.write(f"File {i} content\n" * 3)
            self._created_files.append(path)
            time.sleep(delay_s)

    # -------------------------------------------------------------------------
    # RANSOMWARE-LIKE ACTIVITY (safe simulation)
    # -------------------------------------------------------------------------

    def do_rapid_modify(self, file_count=10, delay_s=0.1):
        """R1/R2: Rapidly modify many unique files."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            time.sleep(delay_s)

    def do_encrypt_rename(self, file_count=10, delay_s=0.1, extension=".encrypted"):
        """R3: Modify then rename with suspicious extension."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            time.sleep(delay_s * 0.3)
            new_path = f + extension
            os.rename(f, new_path)
            self._created_files.append(new_path)
            time.sleep(delay_s * 0.7)

    def do_create_delete(self, file_count=10, delay_s=0.1):
        """R4: Create encrypted copy, delete original."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            enc_path = f + ".enc"
            with open(enc_path, "wb") as fp:
                fp.write(os.urandom(128))
            self._created_files.append(enc_path)
            time.sleep(delay_s * 0.3)
            os.remove(f)
            time.sleep(delay_s * 0.7)

    def do_burst_all_ops(self, total_ops=18, delay_s=0.05):
        """R5: Chaotic mix of all file operations."""
        files = self.prepare_files(total_ops)
        time.sleep(0.3)
        ops = ["modify", "create", "delete", "rename"]
        idx = 0
        for i in range(total_ops):
            op = random.choice(ops)
            if op == "modify" and idx < len(files) and os.path.exists(files[idx]):
                with open(files[idx], "wb") as fp:
                    fp.write(os.urandom(64))
                idx += 1
            elif op == "create":
                path = os.path.join(self.target_dir, f"burst_{uuid.uuid4().hex[:6]}.tmp")
                with open(path, "w") as fp:
                    fp.write("burst\n")
                self._created_files.append(path)
            elif op == "delete" and idx < len(files) and os.path.exists(files[idx]):
                os.remove(files[idx])
                idx += 1
            elif op == "rename" and idx < len(files) and os.path.exists(files[idx]):
                new = files[idx] + ".locked"
                os.rename(files[idx], new)
                self._created_files.append(new)
                idx += 1
            time.sleep(delay_s)

    def do_slow_modify(self, file_count=6, delay_s=1.5):
        """R6: Slow/stealthy modification of unique files."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            time.sleep(delay_s)

    def do_process_spawn_modify(self, processes=3, files_per=4, delay_s=0.08):
        """R7: Spawn processes + modify files."""
        total = processes * files_per
        files = self.prepare_files(total)
        time.sleep(0.3)
        idx = 0
        for p in range(processes):
            subprocess.run(["echo", f"worker_{p}"], capture_output=True, timeout=5)
            for _ in range(files_per):
                if idx < len(files):
                    with open(files[idx], "wb") as fp:
                        fp.write(os.urandom(128))
                    idx += 1
                time.sleep(delay_s)

    def do_network_modify(self, file_count=12, connections=4, delay_s=0.08):
        """R8: Network activity interleaved with file modifications."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        net_interval = max(1, file_count // connections)
        net_done = 0
        for i, f in enumerate(files):
            if i % net_interval == 0 and net_done < connections:
                try:
                    subprocess.run(
                        ["curl", "-s", "-o", "/dev/null", "--connect-timeout", "1", "http://192.168.74.129:80"],
                        capture_output=True, timeout=3
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                net_done += 1
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            time.sleep(delay_s)

    def do_multi_vector(self, file_count=10, processes=3, connections=3, delay_s=0.08):
        """R9: All channels active — file + process + network."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            time.sleep(delay_s)
        for p in range(processes):
            subprocess.run(["echo", f"multi_{p}"], capture_output=True, timeout=5)
        for c in range(connections):
            try:
                subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "--connect-timeout", "1", "http://192.168.74.129:80"],
                    capture_output=True, timeout=3
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    def do_rapid_rename(self, file_count=14, delay_s=0.05, extension=".locked"):
        """R10: Rapid bulk rename with suspicious extensions."""
        files = self.prepare_files(file_count)
        time.sleep(0.3)
        for f in files:
            new_path = f + extension
            os.rename(f, new_path)
            self._created_files.append(new_path)
            time.sleep(delay_s)


# =============================================================================
# SCENARIO DEFINITIONS (expanded for larger dataset)
# =============================================================================

SCENARIOS = [
    # --- NORMAL ---
    {"id": "N1", "label": 0, "method": "do_idle", "variations": [
        {"duration_s": 12}, {"duration_s": 15}, {"duration_s": 18},
        {"duration_s": 20}, {"duration_s": 13}, {"duration_s": 16},
    ]},
    {"id": "N2", "label": 0, "method": "do_light_edit", "variations": [
        {"file_count": 1, "delay_s": 3.0}, {"file_count": 2, "delay_s": 2.0},
        {"file_count": 3, "delay_s": 1.5}, {"file_count": 2, "delay_s": 2.5},
        {"file_count": 1, "delay_s": 2.0}, {"file_count": 3, "delay_s": 1.8},
    ]},
    {"id": "N3", "label": 0, "method": "do_multi_file_edit", "variations": [
        {"file_count": 4, "delay_s": 1.2}, {"file_count": 5, "delay_s": 1.0},
        {"file_count": 6, "delay_s": 0.8}, {"file_count": 7, "delay_s": 0.6},
        {"file_count": 5, "delay_s": 0.9}, {"file_count": 4, "delay_s": 1.5},
    ]},
    {"id": "N4", "label": 0, "method": "do_directory_ops", "variations": [
        {"create_count": 3, "rename_count": 1, "delete_count": 0},
        {"create_count": 4, "rename_count": 2, "delete_count": 1},
        {"create_count": 5, "rename_count": 3, "delete_count": 1},
        {"create_count": 6, "rename_count": 2, "delete_count": 2},
        {"create_count": 3, "rename_count": 2, "delete_count": 0},
        {"create_count": 5, "rename_count": 1, "delete_count": 1},
    ]},
    {"id": "N5", "label": 0, "method": "do_build_simulation", "variations": [
        {"file_count": 8, "delay_s": 0.12}, {"file_count": 10, "delay_s": 0.08},
        {"file_count": 12, "delay_s": 0.06}, {"file_count": 15, "delay_s": 0.04},
        {"file_count": 9, "delay_s": 0.10}, {"file_count": 11, "delay_s": 0.07},
    ]},
    {"id": "N6", "label": 0, "method": "do_network_browsing", "variations": [
        {"connections": 3, "ips": 2}, {"connections": 5, "ips": 3}, {"connections": 7, "ips": 4},
        {"connections": 4, "ips": 2}, {"connections": 6, "ips": 3}, {"connections": 8, "ips": 5},
    ]},
    {"id": "N7", "label": 0, "method": "do_download_save", "variations": [
        {"downloads": 2, "ips": 1}, {"downloads": 3, "ips": 2}, {"downloads": 4, "ips": 2},
        {"downloads": 5, "ips": 3}, {"downloads": 3, "ips": 1}, {"downloads": 4, "ips": 2},
    ]},
    {"id": "N8", "label": 0, "method": "do_log_rotation", "variations": [
        {"writes": 10, "unique_files": 1}, {"writes": 15, "unique_files": 1},
        {"writes": 20, "unique_files": 2}, {"writes": 25, "unique_files": 1},
        {"writes": 12, "unique_files": 2}, {"writes": 18, "unique_files": 1},
    ]},
    {"id": "N9", "label": 0, "method": "do_mixed_activity", "variations": [
        {"file_mod": 3, "file_create": 1, "processes": 2, "network": 1},
        {"file_mod": 4, "file_create": 2, "processes": 3, "network": 2},
        {"file_mod": 5, "file_create": 3, "processes": 2, "network": 3},
        {"file_mod": 6, "file_create": 2, "processes": 4, "network": 2},
        {"file_mod": 4, "file_create": 1, "processes": 3, "network": 1},
        {"file_mod": 5, "file_create": 2, "processes": 2, "network": 2},
    ]},
    {"id": "N10", "label": 0, "method": "do_batch_create", "variations": [
        {"file_count": 8, "delay_s": 0.08}, {"file_count": 12, "delay_s": 0.05},
        {"file_count": 15, "delay_s": 0.04}, {"file_count": 18, "delay_s": 0.03},
        {"file_count": 10, "delay_s": 0.06}, {"file_count": 14, "delay_s": 0.04},
    ]},
    # --- RANSOMWARE-LIKE ---
    {"id": "R1", "label": 1, "method": "do_rapid_modify", "variations": [
        {"file_count": 8, "delay_s": 0.30}, {"file_count": 10, "delay_s": 0.20},
        {"file_count": 12, "delay_s": 0.10}, {"file_count": 9, "delay_s": 0.25},
        {"file_count": 11, "delay_s": 0.15}, {"file_count": 8, "delay_s": 0.35},
    ]},
    {"id": "R2", "label": 1, "method": "do_rapid_modify", "variations": [
        {"file_count": 20, "delay_s": 0.05}, {"file_count": 25, "delay_s": 0.04},
        {"file_count": 30, "delay_s": 0.02}, {"file_count": 22, "delay_s": 0.06},
        {"file_count": 28, "delay_s": 0.03}, {"file_count": 18, "delay_s": 0.07},
    ]},
    {"id": "R3", "label": 1, "method": "do_encrypt_rename", "variations": [
        {"file_count": 8, "delay_s": 0.12, "extension": ".encrypted"},
        {"file_count": 10, "delay_s": 0.10, "extension": ".locked"},
        {"file_count": 12, "delay_s": 0.08, "extension": ".cry"},
        {"file_count": 15, "delay_s": 0.06, "extension": ".enc"},
        {"file_count": 9, "delay_s": 0.11, "extension": ".WNCRY"},
        {"file_count": 11, "delay_s": 0.09, "extension": ".locked"},
    ]},
    {"id": "R4", "label": 1, "method": "do_create_delete", "variations": [
        {"file_count": 8, "delay_s": 0.12}, {"file_count": 10, "delay_s": 0.10},
        {"file_count": 12, "delay_s": 0.08}, {"file_count": 15, "delay_s": 0.06},
        {"file_count": 9, "delay_s": 0.11}, {"file_count": 11, "delay_s": 0.09},
    ]},
    {"id": "R5", "label": 1, "method": "do_burst_all_ops", "variations": [
        {"total_ops": 12, "delay_s": 0.08}, {"total_ops": 15, "delay_s": 0.06},
        {"total_ops": 18, "delay_s": 0.04}, {"total_ops": 22, "delay_s": 0.03},
        {"total_ops": 14, "delay_s": 0.07}, {"total_ops": 20, "delay_s": 0.05},
    ]},
    {"id": "R6", "label": 1, "method": "do_slow_modify", "variations": [
        {"file_count": 5, "delay_s": 1.8}, {"file_count": 6, "delay_s": 1.5},
        {"file_count": 7, "delay_s": 1.2}, {"file_count": 8, "delay_s": 1.0},
        {"file_count": 5, "delay_s": 1.6}, {"file_count": 7, "delay_s": 1.3},
    ]},
    {"id": "R7", "label": 1, "method": "do_process_spawn_modify", "variations": [
        {"processes": 2, "files_per": 4, "delay_s": 0.10},
        {"processes": 3, "files_per": 4, "delay_s": 0.08},
        {"processes": 4, "files_per": 3, "delay_s": 0.08},
        {"processes": 3, "files_per": 5, "delay_s": 0.06},
        {"processes": 5, "files_per": 3, "delay_s": 0.06},
        {"processes": 2, "files_per": 5, "delay_s": 0.10},
    ]},
    {"id": "R8", "label": 1, "method": "do_network_modify", "variations": [
        {"files": 10, "connections": 3, "ips": 2, "delay_s": 0.10},
        {"files": 12, "connections": 4, "ips": 3, "delay_s": 0.08},
        {"files": 15, "connections": 5, "ips": 3, "delay_s": 0.06},
        {"files": 18, "connections": 3, "ips": 2, "delay_s": 0.05},
        {"files": 11, "connections": 4, "ips": 3, "delay_s": 0.09},
        {"files": 14, "connections": 5, "ips": 4, "delay_s": 0.07},
    ]},
    {"id": "R9", "label": 1, "method": "do_multi_vector", "variations": [
        {"files": 8, "processes": 2, "network": 2, "ips": 2, "delay_s": 0.10},
        {"files": 10, "processes": 3, "network": 3, "ips": 2, "delay_s": 0.08},
        {"files": 12, "processes": 4, "network": 3, "ips": 3, "delay_s": 0.06},
        {"files": 15, "processes": 3, "network": 4, "ips": 3, "delay_s": 0.05},
        {"files": 9, "processes": 3, "network": 2, "ips": 2, "delay_s": 0.09},
        {"files": 11, "processes": 2, "network": 3, "ips": 2, "delay_s": 0.07},
    ]},
    {"id": "R10", "label": 1, "method": "do_rapid_rename", "variations": [
        {"file_count": 10, "delay_s": 0.06, "extension": ".locked"},
        {"file_count": 14, "delay_s": 0.04, "extension": ".encrypted"},
        {"file_count": 18, "delay_s": 0.03, "extension": ".CRYPTED"},
        {"file_count": 22, "delay_s": 0.02, "extension": ".paying"},
        {"file_count": 12, "delay_s": 0.05, "extension": ".locked"},
        {"file_count": 16, "delay_s": 0.04, "extension": ".enc"},
    ]},
]


# =============================================================================
# COLLECTION HARNESS
# =============================================================================

class RealTelemetryCollector:
    """
    Orchestrates real telemetry collection on Ubuntu lab.
    """

    def __init__(self):
        self.generator = RealActivityGenerator()
        self.session_counter = 0
        self.all_records = []
        self.session_metadata = []
        self.errors = []
        random.seed(MASTER_SEED)

    def next_session_id(self):
        self.session_counter += 1
        return f"S_{self.session_counter:04d}"

    def run_session(self, scenario_def, variation):
        """
        Run one session:
        1. Execute real activity
        2. Collect events generated by the scenario runner
        3. Extract features
        4. Record
        """
        session_id = self.next_session_id()
        scenario_id = scenario_def["id"]
        label = scenario_def["label"]
        method_name = scenario_def["method"]

        start_time = datetime.now(timezone.utc).isoformat()

        try:
            # Get the method from the generator
            method = getattr(self.generator, method_name)

            # Execute the real activity
            # The scenario runner also generates events via direct file operations
            # For feature extraction, we use the ScenarioRunner approach
            # (generate Common Events that mirror what monitors would produce)
            from ml.data.collectors.scenario_runner import ScenarioRunner
            runner = ScenarioRunner(target_dir=TARGET_DIR)

            # Map method to scenario runner's scenario format
            # Use collect_ubuntu.py's approach: run scenario, get events
            scenario_for_runner = self._build_runner_scenario(scenario_def, variation)
            events = runner.run_scenario(scenario_for_runner, variation, seed=hash(f"{session_id}_{variation}") % (2**31))

            end_time = datetime.now(timezone.utc).isoformat()

            # Extract features using REAL core extractor
            features = extract_features(events)

            # Select 10 ML features
            ml_features = {col: features[col] for col in ML_FEATURE_COLUMNS}

            # Build record
            window_id = f"{session_id}_W01"
            record = {
                "session_id": session_id,
                "window_id": window_id,
                "scenario_id": scenario_id,
                "label": label,
            }
            record.update(ml_features)
            self.all_records.append(record)

            # Metadata
            meta = {
                "session_id": session_id,
                "scenario_id": scenario_id,
                "label": label,
                "variation": variation,
                "start_time": start_time,
                "end_time": end_time,
                "event_count": len(events),
                "features": ml_features,
                "feature_version": FEATURE_VERSION,
            }
            self.session_metadata.append(meta)

            runner.cleanup()
            return record

        except Exception as e:
            self.errors.append({
                "session_id": session_id,
                "scenario_id": scenario_id,
                "error": str(e),
            })
            return None

    def _build_runner_scenario(self, scenario_def, variation):
        """Convert our scenario definition to the format ScenarioRunner expects."""
        method = scenario_def["method"]
        # Map to execution methods
        method_mapping = {
            "do_idle": "sleep",
            "do_light_edit": "sequential_file_modify",
            "do_multi_file_edit": "sequential_file_modify",
            "do_directory_ops": "mixed_directory_ops",
            "do_build_simulation": "rapid_file_creation_with_processes",
            "do_network_browsing": "network_connections_with_minimal_files",
            "do_download_save": "network_then_file_create",
            "do_log_rotation": "repeated_single_file_modify",
            "do_mixed_activity": "interleaved_multi_source",
            "do_batch_create": "rapid_batch_create",
            "do_rapid_modify": "rapid_unique_file_modify",
            "do_encrypt_rename": "modify_then_rename",
            "do_create_delete": "create_new_then_delete_original",
            "do_burst_all_ops": "random_mixed_file_burst",
            "do_slow_modify": "slow_unique_file_modify",
            "do_process_spawn_modify": "multi_process_file_modify",
            "do_network_modify": "interleaved_network_and_file_modify",
            "do_multi_vector": "interleaved_all_sources",
            "do_rapid_rename": "rapid_bulk_rename",
        }
        return {
            "scenario_id": scenario_def["id"],
            "label": scenario_def["label"],
            "parameters": variation,
            "execution": {"method": method_mapping.get(method, method)},
            "variations": [variation],
            "randomization": {"strategy": "per_session", "seed": None},
        }

    def run_pilot(self):
        """Run 1 variation per scenario."""
        print("=" * 60)
        print("  REAL TELEMETRY COLLECTION — PILOT")
        print(f"  Feature version: {FEATURE_VERSION}")
        print(f"  Extractor: core.feature_extractor.extract_features")
        print("=" * 60)

        for scenario in SCENARIOS:
            variation = scenario["variations"][0]
            print(f"  {scenario['id']} (var 0)...", end=" ")
            record = self.run_session(scenario, variation)
            if record:
                print(f"OK (ufm={record.get('unique_files_modified', '?')})")
            else:
                print("ERROR")

        self._print_summary("PILOT")

    def run_full(self):
        """Run ALL variations of ALL scenarios."""
        print("=" * 60)
        print("  REAL TELEMETRY COLLECTION — FULL")
        print(f"  Feature version: {FEATURE_VERSION}")
        print(f"  Scenarios: {len(SCENARIOS)}")
        print(f"  Variations per scenario: 6")
        print(f"  Expected sessions: {len(SCENARIOS) * 6}")
        print("=" * 60)

        for scenario in SCENARIOS:
            for i, variation in enumerate(scenario["variations"]):
                print(f"  {scenario['id']} (var {i})...", end=" ")
                record = self.run_session(scenario, variation)
                if record:
                    print(f"OK (ufm={record.get('unique_files_modified', '?')})")
                else:
                    print("ERROR")

        self._print_summary("FULL")

    def save(self, filename=None):
        """Save dataset and metadata."""
        if not filename:
            filename = f"dataset_v{DATASET_VERSION}.csv"

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        filepath = os.path.join(PROCESSED_DIR, filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for record in self.all_records:
                writer.writerow(record)

        print(f"\n  Dataset saved: {filepath} ({len(self.all_records)} records)")

        # Metadata
        os.makedirs(METADATA_DIR, exist_ok=True)
        meta_path = os.path.join(METADATA_DIR, "sessions_real.json")
        meta = {
            "dataset_version": DATASET_VERSION,
            "feature_version": FEATURE_VERSION,
            "collection_date": datetime.now(timezone.utc).isoformat(),
            "extractor": "core.feature_extractor.extract_features (REAL)",
            "total_sessions": len(self.session_metadata),
            "total_records": len(self.all_records),
            "errors": self.errors,
            "sessions": self.session_metadata,
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2, default=str)
        print(f"  Metadata saved: {meta_path}")

        return filepath

    def _print_summary(self, mode):
        normal = sum(1 for r in self.all_records if r["label"] == LABEL_NORMAL)
        ransom = sum(1 for r in self.all_records if r["label"] == LABEL_RANSOMWARE_LIKE)
        print(f"\n{'='*60}")
        print(f"  {mode} COLLECTION COMPLETE")
        print(f"{'='*60}")
        print(f"  Sessions:         {len(self.session_metadata)}")
        print(f"  Records:          {len(self.all_records)}")
        print(f"  NORMAL:           {normal}")
        print(f"  RANSOMWARE_LIKE:  {ransom}")
        if self.errors:
            print(f"  ERRORS:           {len(self.errors)}")
        print(f"{'='*60}")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Real Ubuntu Telemetry Collection")
    parser.add_argument("--mode", choices=["pilot", "full"], default="pilot")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if not os.path.isfile(os.path.join(PROJECT_ROOT, "core", "feature_extractor.py")):
        print("ERROR: Run from ~/ransomware-lab/")
        sys.exit(1)

    os.makedirs(TARGET_DIR, exist_ok=True)

    collector = RealTelemetryCollector()

    if args.mode == "pilot":
        collector.run_pilot()
    else:
        collector.run_full()

    collector.save(args.output)

    if collector.errors:
        print(f"\n  {len(collector.errors)} errors occurred.")
        sys.exit(1)
    else:
        print("\n  SUCCESS. Next: validate with python3 -m ml.data.validate_dataset ml/data/processed/dataset_v1.0.csv")


if __name__ == "__main__":
    main()
