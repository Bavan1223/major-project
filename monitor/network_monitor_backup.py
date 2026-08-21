import psutil
import time
import os
import sys


# Add project root to Python path
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from event_logger import log_event


def get_process_name(pid):
    if not pid:
        return "Unknown"

    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "Unknown"


def monitor_network():
    print("=== Ransomware Defense - Network Monitor ===")
    print("Monitoring network connections...")
    print("Press Ctrl+C to stop.\n")

    previous_connections = set()

    while True:

        current_connections = set()

        connections = psutil.net_connections(kind="inet")

        for conn in connections:

            if conn.status != psutil.CONN_ESTABLISHED:
                continue

            process_name = get_process_name(conn.pid)

            local_address = f"{conn.laddr.ip}:{conn.laddr.port}"

            if conn.raddr:
                remote_address = f"{conn.raddr.ip}:{conn.raddr.port}"
            else:
                remote_address = "Unknown"

            connection_id = (
                conn.pid,
                local_address,
                remote_address
            )

            current_connections.add(connection_id)

            if connection_id not in previous_connections:

                # Existing terminal output
                print("[NEW CONNECTION]")
                print("Process :", process_name)
                print("PID     :", conn.pid)
                print("Local   :", local_address)
                print("Remote  :", remote_address)
                print("Status  :", conn.status)

                # Save structured network event
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

                print("-" * 50)

        previous_connections = current_connections

        time.sleep(2)


if __name__ == "__main__":
    monitor_network()
