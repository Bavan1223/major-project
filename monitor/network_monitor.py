import psutil
import time
import os
import sys
from collections import defaultdict, deque


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from event_logger import log_event


SCAN_INTERVAL = 2

# Number of connections required before we
# record a repeated-connection behavioral signal.
REPEAT_THRESHOLD = 3

# Keep timestamps for recent connections.
connection_history = defaultdict(deque)


def get_process_name(pid):
    if not pid:
        return None

    try:
        return psutil.Process(pid).name()

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):
        return None


def monitor_network():

    print("=== Ransomware Defense - Network Monitor ===")
    print("Monitoring network connections...")
    print("Press Ctrl+C to stop.\n")

    previous_connections = set()

    while True:

        current_connections = set()

        connections = psutil.net_connections(
            kind="inet"
        )

        current_time = time.time()

        for conn in connections:

            if conn.status != psutil.CONN_ESTABLISHED:
                continue

            if not conn.laddr:
                continue

            process_name = get_process_name(conn.pid)

            local_address = (
                f"{conn.laddr.ip}:{conn.laddr.port}"
            )

            if conn.raddr:

                remote_address = (
                    f"{conn.raddr.ip}:{conn.raddr.port}"
                )

            else:
                remote_address = "Unknown"

            connection_id = (
                conn.pid,
                local_address,
                remote_address
            )

            current_connections.add(
                connection_id
            )

            if connection_id not in previous_connections:

                print("[NEW CONNECTION]")
                print("Process :", process_name or "Unknown")
                print("PID     :", conn.pid)
                print("Local   :", local_address)
                print("Remote  :", remote_address)
                print("Status  :", conn.status)

                log_event(
                    source="network_monitor",
                    event_type="network_connection",
                    indicator="new_established_connection",
                    pid=conn.pid,
                    process=process_name,
                    data={
                        "local_address": local_address,
                        "remote_address": remote_address,
                        "status": conn.status
                    }
                )

                # Track repeated connections to the same endpoint.
                endpoint = remote_address

                history = connection_history[endpoint]

                history.append(current_time)

                # Keep only the last 30 seconds.
                while history:
                    if current_time - history[0] > 30:
                        history.popleft()
                    else:
                        break

                # Behavioral signal:
                # repeated connections to same endpoint.
                if len(history) == REPEAT_THRESHOLD:

                    log_event(
                        source="network_monitor",
                        event_type="repeated_network_activity",
                        indicator="repeated_connection_to_endpoint",
                        pid=conn.pid,
                        process=process_name,
                        data={
                            "remote_address":
                                remote_address,
                            "connection_count":
                                len(history),
                            "window_seconds":
                                30
                        }
                    )

                    print(
                        "[NETWORK BEHAVIOR] "
                        "Repeated connection detected"
                    )

                print("-" * 50)

        previous_connections = current_connections

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    monitor_network()
