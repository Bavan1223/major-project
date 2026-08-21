import json
import os
from collections import defaultdict

import psutil


LOG_FILE = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "logs",
    "events.jsonl"
)


def load_events():
    """
    Load valid JSON events from the Common Event log.
    """

    events = []

    if not os.path.exists(LOG_FILE):
        return events

    with open(LOG_FILE, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            try:
                event = json.loads(line)

            except json.JSONDecodeError:
                continue

            if isinstance(event, dict):
                events.append(event)

    return events


def get_live_process_info(pid):
    """
    Safely obtain process information for a currently
    running PID.

    Returns None when the PID no longer exists or
    cannot be accessed.
    """

    if pid is None:
        return None

    try:

        process = psutil.Process(pid)

        with process.oneshot():

            return {
                "pid": process.pid,
                "process": process.name(),
                "executable": process.exe()
            }

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):
        return None


def build_process_index(events):
    """
    Build PID -> most recent process-monitor event index.
    """

    processes = {}

    for event in events:

        if event.get("source") != "process_monitor":
            continue

        pid = event.get("pid")

        if pid is None:
            continue

        processes[pid] = event

    return processes


def build_network_index(events):
    """
    Build PID -> network events index.
    """

    networks = defaultdict(list)

    for event in events:

        if event.get("source") != "network_monitor":
            continue

        pid = event.get("pid")

        if pid is None:
            continue

        networks[pid].append(event)

    return networks


def get_process_context(pid, process_event=None):
    """
    Resolve process context without inventing information.

    Priority:
        1. Existing process_monitor event
        2. Live OS process lookup
        3. None for unavailable executable

    Historical network events may contain a process name,
    but executable information is not fabricated.
    """

    if process_event is not None:

        data = process_event.get("data", {})

        return {
            "pid": pid,
            "process": process_event.get("process"),
            "executable": data.get("exe"),
            "source": "process_monitor"
        }

    live_info = get_live_process_info(pid)

    if live_info is not None:

        return {
            "pid": pid,
            "process": live_info["process"],
            "executable": live_info["executable"],
            "source": "live_process_lookup"
        }

    return {
        "pid": pid,
        "process": None,
        "executable": None,
        "source": "unavailable"
    }


def correlate_process_network():
    """
    Correlate network activity with process context.

    Correlation is based on PID.

    A network event is never discarded merely because
    process_monitor did not observe the process.

    If the PID is still alive, psutil is used for enrichment.
    If the PID is dead, no executable is guessed.
    """

    events = load_events()

    processes = build_process_index(events)
    networks = build_network_index(events)

    correlations = []

    for pid, network_events in networks.items():

        process_event = processes.get(pid)

        context = get_process_context(
            pid,
            process_event
        )

        for network_event in network_events:

            network_data = network_event.get(
                "data",
                {}
            )

            correlations.append({
                "pid": pid,
                "process": (
                    context["process"]
                    or network_event.get("process")
                ),
                "executable": context["executable"],
                "process_context_source":
                    context["source"],
                "network": network_data,
                "network_event_timestamp":
                    network_event.get("timestamp")
            })

    return correlations


def correlate_file_process_network(
    audit_records=None
):
    """
    Build higher-level behavioral correlations:

        file activity
            +
        process attribution
            +
        network activity

    Audit records are optional.

    No new ML features are generated here.
    No risk score is calculated here.
    No containment is performed here.
    """

    events = load_events()

    networks = build_network_index(events)

    if audit_records is None:
        audit_records = []

    correlations = []

    for audit in audit_records:

        pid = audit.get("pid")

        if pid is None:
            continue

        context = get_process_context(pid)

        matching_networks = networks.get(pid, [])

        record = {
            "pid": pid,
            "process": (
                audit.get("process")
                or context.get("process")
            ),
            "executable": (
                audit.get("executable")
                or context.get("executable")
            ),
            "file_activity": {
                "path": audit.get("path"),
                "operation": audit.get("operation"),
                "syscall": audit.get("syscall"),
                "success": audit.get("success"),
                "event_id": audit.get("event_id")
            },
            "network_activity": [],
            "process_context_source":
                context.get("source")
        }

        for network_event in matching_networks:

            record["network_activity"].append(
                network_event.get("data", {})
            )

        correlations.append(record)

    return correlations


def print_process_network_results():

    print(
        "=== Process <-> Network Correlation ==="
    )

    results = correlate_process_network()

    if not results:

        print(
            "No network activity found."
        )

        return

    for result in results:

        print()
        print("[CORRELATED ACTIVITY]")

        print(
            "PID        :",
            result["pid"]
        )

        print(
            "Process    :",
            result["process"]
            or "Unavailable"
        )

        print(
            "Executable :",
            result["executable"]
            or "Unavailable"
        )

        print(
            "Context    :",
            result["process_context_source"]
        )

        network = result["network"]

        print(
            "Local      :",
            network.get("local_address")
        )

        print(
            "Remote     :",
            network.get("remote_address")
        )

        print(
            "Status     :",
            network.get("status")
        )

        print(
            "Timestamp  :",
            result["network_event_timestamp"]
        )

        print("-" * 50)


if __name__ == "__main__":

    print_process_network_results()
