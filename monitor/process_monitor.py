import time
import psutil
import os
import sys


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from event_logger import log_event


# ============================================================
# CONFIGURATION
# ============================================================

SCAN_INTERVAL = 2


# ============================================================
# PROCESS INFORMATION
# ============================================================

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


# ============================================================
# PROCESS MONITOR
# ============================================================

def monitor_processes():

    print("=== Ransomware Defense - Process Monitor ===")
    print("Monitoring running processes...")
    print("Press Ctrl+C to stop.\n")


    # --------------------------------------------------------
    # Establish baseline
    # --------------------------------------------------------

    previous_pids = {
        process.pid
        for process in psutil.process_iter()
    }


    print(
        f"Initial process baseline established: "
        f"{len(previous_pids)} processes"
    )


    # --------------------------------------------------------
    # Continuous monitoring
    # --------------------------------------------------------

    while True:

        current_pids = set()


        for process in psutil.process_iter():

            info = get_process_info(process)

            if info is None:
                continue


            pid = info["pid"]

            current_pids.add(pid)


            # ------------------------------------------------
            # Detect newly started process
            # ------------------------------------------------

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


        # Update baseline

        previous_pids = current_pids


        time.sleep(SCAN_INTERVAL)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        monitor_processes()

    except KeyboardInterrupt:
        print("\nProcess monitor stopped.")
