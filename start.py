#!/usr/bin/env python3
"""
Ransomware Defense System — Unified Launcher

Starts ALL components in one command:
    - Flask Backend API (port 5000)
    - React Frontend (port 3000)
    - File Monitor
    - Process Monitor
    - Network Monitor
    - Detection Pipeline

Usage:
    cd ~/ransomware-lab
    source .venv/bin/activate
    python3 start.py

Press Ctrl+C to stop all components.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python3")
FRONTEND_DIR = str(PROJECT_ROOT / "frontend")

# Use system python if venv not found
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable


# ==============================================================
# PROCESS MANAGEMENT
# ==============================================================

processes: list[subprocess.Popen] = []


def start_process(name: str, cmd: list, cwd: str = None, env: dict = None):
    """Start a subprocess and track it."""
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    proc = subprocess.Popen(
        cmd,
        cwd=cwd or str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=proc_env,
    )
    processes.append(proc)
    print(f"  [{name}] Started (PID {proc.pid})")
    return proc


def stop_all():
    """Terminate all child processes."""
    print("\n\nShutting down all components...")
    for proc in processes:
        try:
            proc.terminate()
        except ProcessLookupError:
            pass

    # Wait briefly for graceful shutdown
    time.sleep(1)

    for proc in processes:
        try:
            proc.kill()
        except ProcessLookupError:
            pass

    print("All components stopped.")


def signal_handler(sig, frame):
    stop_all()
    sys.exit(0)


# ==============================================================
# MAIN
# ==============================================================

def main():
    print()
    print("=" * 60)
    print("  RANSOMWARE DEFENSE SYSTEM — UNIFIED LAUNCHER")
    print("=" * 60)
    print()
    print(f"  Project: {PROJECT_ROOT}")
    print(f"  Python:  {VENV_PYTHON}")
    print(f"  Mode:    SAFE LAB / DRY_RUN")
    print()
    print("-" * 60)
    print("  Starting components...")
    print("-" * 60)
    print()

    # Register cleanup handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. Backend API
    start_process(
        "Backend API",
        [VENV_PYTHON, "dashboard.py"],
    )
    time.sleep(1)

    # 2. File Monitor
    start_process(
        "File Monitor",
        [VENV_PYTHON, "monitor/file_monitor.py"],
    )

    # 3. Process Monitor
    start_process(
        "Process Monitor",
        [VENV_PYTHON, "monitor/process_monitor.py"],
    )

    # 4. Network Monitor
    start_process(
        "Network Monitor",
        [VENV_PYTHON, "monitor/network_monitor.py"],
    )

    # 5. Detection Pipeline
    start_process(
        "Detection Pipeline",
        [VENV_PYTHON, "detection_pipeline.py"],
    )

    # 6. Frontend (npm run dev)
    start_process(
        "Frontend",
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
    )

    time.sleep(2)

    print()
    print("-" * 60)
    print("  ALL COMPONENTS RUNNING")
    print("-" * 60)
    print()
    print("  Backend API:    http://192.168.74.131:5000")
    print("  SOC Dashboard:  http://192.168.74.131:3000")
    print()
    print("  Protection:     DRY_RUN")
    print("  Safe Lab Mode:  ENABLED")
    print()
    print("  To trigger detection:")
    print("    python3 simulator/safe_simulator.py")
    print()
    print("  Press Ctrl+C to stop all components.")
    print()

    # Keep running until interrupted
    try:
        while True:
            # Check if any critical process died
            for proc in processes:
                if proc.poll() is not None:
                    pass  # Non-critical — some may exit normally
            time.sleep(2)
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
