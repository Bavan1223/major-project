import time
import psutil
import os
import sys


# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from event_logger import log_event


SCAN_INTERVAL = 2


def get_process_info(process):
    """
    Safely collect basic information about a process.
    """

    try:
        with process.oneshot():

            return {
                "pid": process.pid,
                "name": process.name(),
                "exe": process.exe(),
                "username": process.username(),
                "create_time": process.create_time()
            }

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):
        return None


def monitor_processes():

    print("=== Ransomware Defense - Process Monitor ===")
    print("Monitoring running processes...")
    print("Press Ctrl+C to stop.\n")

    # Establish a baseline of processes that already exist.
# Existing processes are not reported as newly started.
previous_pids = {
    process.pid
    for process in psutil.process_iter()
}

print(
    f"Initial process baseline established: "
    f"{len(previous_pids)} processes"
)

while True:

        current_pids = set()

        for process in psutil.process_iter():

            info = get_process_info(process)

            if info is None:
                continue

            pid = info["pid"]

            current_pids.add(pid)

            # Detect newly observed processes
            if pid not in previous_pids:

                print("[NEW PROCESS]")
                print("Name :", info["name"])
                print("PID  :", info["pid"])
                print("EXE  :", info["exe"])
                print("-" * 50)

                log_event(
                    source="process_monitor",
                    event_type="process_started",
                    pid=info["pid"],
                    process=info["name"],
                    indicator="new_process",
                    data={
                        "exe": info["exe"],
                        "username": info["username"],
                        "create_time": info["create_time"]
                    }
                )

        previous_pids = current_pids

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    monitor_processes()
