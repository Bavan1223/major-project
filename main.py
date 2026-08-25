"""
Ransomware Defense System — Main Entry Point

Usage:
    python3 main.py          # Run automated test suite
    python3 main.py --help   # Show available commands

Individual components:
    python3 dashboard.py                    # Flask API backend
    python3 detection_pipeline.py           # Live detection loop
    python3 monitor/file_monitor.py         # File monitor
    python3 monitor/process_monitor.py      # Process monitor
    python3 monitor/network_monitor.py      # Network monitor
    python3 simulator/safe_simulator.py     # Safe simulation
    python3 tests/test_system.py            # Test suite
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    print("Ransomware Defense System — Running test suite...")
    print()

    # Run the automated test suite
    from tests.test_system import main as run_tests
    run_tests()


if __name__ == "__main__":
    main()
