from flask import Flask, Response, jsonify, render_template_string, request
from flask_cors import CORS
import json
import os
from datetime import datetime


app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:3000",
                "http://localhost:3000",
                "http://127.0.0.1:3001",
                "http://localhost:3001",
                "http://192.168.74.131:3000",
                "http://192.168.74.131:3001",
            ]
        }
    }
)

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

LOG_FILE = os.path.join(
    PROJECT_ROOT,
    "logs",
    "events.jsonl"
)


# ============================================================
# EVENT READER
# ============================================================

def read_events():
    """
    Read Common Events from the persistent JSONL log.

    Invalid JSON lines are ignored so that one malformed
    record does not break the dashboard.
    """

    events = []

    if not os.path.exists(LOG_FILE):
        return events

    try:

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:

                    event = json.loads(line)

                    if isinstance(event, dict):
                        events.append(event)

                except json.JSONDecodeError:
                    continue

    except OSError:
        pass

    return events


# ============================================================
# HELPERS
# ============================================================

def events_by_source(events, source):
    """
    Return events belonging to a specific monitor/source.
    """

    return [
        event
        for event in events
        if event.get("source") == source
    ]


def latest_events(events, limit=20):
    """
    Return newest events first.
    """

    return list(reversed(events[-limit:]))


def calculate_risk(events):
    """
    Dashboard-level risk summary.

    AUTHORITATIVE SOURCE OF TRUTH:
        The IncidentManager determines current risk.
        - Active incident exists → use its risk level
        - No active incident → NORMAL

    Historical risk_assessment events in events.jsonl are
    EVIDENCE/HISTORY, not current state. A closed incident
    does not mean the system is currently under attack.
    """
    from core.incident_manager import incident_manager

    # The incident manager is the single source of truth
    active = incident_manager.get_active_incident()

    if active:
        return {
            "risk_level": active["risk_level"],
            "reason": active["reason"],
            "signals": active["signals"],
            "detected": True,
            "timestamp": active["updated_at"],
            "ml_contributed": active.get("ml_contributed", False),
            "incident_id": active["incident_id"],
            "incident_status": active["status"],
        }

    # No active incident = system is NORMAL
    return {
        "risk_level": "NORMAL",
        "reason": (
            "No active ransomware-like behavioral "
            "activity detected."
        ),
        "signals": [],
        "detected": False,
        "timestamp": None,
        "ml_contributed": False,
        "incident_id": None,
        "incident_status": None,
    }


def build_process_summary(events):
    """
    Build a lightweight process view from process-monitor
    events and network/process attribution.

    This does not claim that a process is currently alive
    unless the event itself represents observed activity.
    """

    process_events = events_by_source(
        events,
        "process_monitor"
    )

    processes = {}

    for event in process_events:

        pid = event.get("pid")

        if pid is None:
            continue

        processes[pid] = {
            "pid": pid,
            "name": event.get("process"),
            "event_type": event.get("event_type"),
            "indicator": event.get("indicator"),
            "timestamp": event.get("timestamp"),
            "data": event.get("data", {})
        }

    return list(
        reversed(
            list(processes.values())
        )
    )


def build_file_summary(events):
    """
    Build a file-activity view from file monitor events.
    """

    file_events = events_by_source(
        events,
        "file_monitor"
    )

    result = []

    for event in reversed(file_events[-100:]):

        data = event.get(
            "data",
            {}
        )

        operation = event.get(
            "event_type",
            "unknown"
        )

        path = (
            data.get("path")
            or data.get("to")
            or data.get("from")
        )

        result.append({
            "id": (
                f'{event.get("timestamp", "")}-'
                f'{event.get("pid", "none")}-'
                f'{len(result)}'
            ),
            "timestamp": event.get(
                "timestamp"
            ),
            "operation": operation,
            "path": path,
            "pid": event.get("pid"),
            "process": event.get("process"),
            "indicator": event.get(
                "indicator"
            ),
            "data": data
        })

    return result


def build_network_summary(events):
    """
    Build a network-activity view from network-monitor
    events.
    """

    network_events = events_by_source(
        events,
        "network_monitor"
    )

    result = []

    for event in reversed(network_events[-100:]):

        data = event.get(
            "data",
            {}
        )

        result.append({
            "timestamp": event.get(
                "timestamp"
            ),
            "pid": event.get(
                "pid"
            ),
            "process": event.get(
                "process"
            ),
            "indicator": event.get(
                "indicator"
            ),
            "local_address": data.get(
                "local_address"
            ),
            "remote_address": data.get(
                "remote_address"
            ),
            "status": data.get(
                "status"
            ),
            "data": data
        })

    return result


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def dashboard():
    """
    Keep the old Flask dashboard available.

    The new React SOC frontend runs separately on port 3000.
    """

    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ransomware Defense API</title>
            <style>
                body {
                    background: #10131a;
                    color: #e1e2ec;
                    font-family: monospace;
                    padding: 40px;
                }
                h1 {
                    color: #ffb4ab;
                }
                li {
                    margin: 12px 0;
                }
                code {
                    color: #9ecaff;
                }
            </style>
        </head>
        <body>

            <h1>RANSOMWARE DEFENSE // BACKEND API</h1>

            <p>
                Backend is running.
            </p>

            <h2>Available endpoints</h2>

            <ul>
                <li><code>/api/status</code></li>
                <li><code>/api/events</code></li>
                <li><code>/api/network</code></li>
                <li><code>/api/processes</code></li>
                <li><code>/api/files</code></li>
                <li><code>/api/risk</code></li>
            </ul>

            <p>
                React SOC frontend:
                <code>http://127.0.0.1:3000</code>
            </p>

        </body>
        </html>
        """
    )


@app.route("/favicon.ico")
def favicon():

    return Response(
        status=204
    )


# ============================================================
# STATUS API
# ============================================================

@app.route("/api/status")
def api_status():

    events = read_events()

    file_events = events_by_source(
        events,
        "file_monitor"
    )

    network_events = events_by_source(
        events,
        "network_monitor"
    )

    process_events = events_by_source(
        events,
        "process_monitor"
    )

    detection_events = events_by_source(
        events,
        "detection_engine"
    )

    # Count meaningful incidents (risk_assessment events
    # that are not NORMAL)
    incident_count = sum(
        1 for event in detection_events
        if (
            event.get("event_type") == "risk_assessment"
            and event.get("data", {}).get(
                "risk_level", "NORMAL"
            ) not in ("NORMAL", "LOW")
        )
    )

    risk = calculate_risk(events)

    # Get active incident info
    from core.incident_manager import incident_manager
    active = incident_manager.get_active_incident()
    ml_prob = active.get("ml_probability", 0.0) if active else 0.0
    ml_contributed = active.get("ml_contributed", False) if active else False

    return jsonify({

        "status": "ONLINE",

        "monitoring": True,

        "safe_lab_mode": True,

        "protection_mode": "DRY_RUN",

        "event_count": len(events),

        "file_event_count":
            len(file_events),

        "network_event_count":
            len(network_events),

        "process_event_count":
            len(process_events),

        "detection_event_count":
            incident_count,

        "risk_level":
            risk["risk_level"],

        "risk_reason":
            risk["reason"],

        "risk_signals":
            risk.get("signals", []),

        "active_incident_id":
            active["incident_id"] if active else None,

        "active_incident_status":
            active["status"] if active else None,

        "ml_probability":
            ml_prob,

        "ml_classification":
            "RANSOMWARE_LIKE" if ml_prob > 0.7 else "NORMAL",

        "ml_contributed":
            ml_contributed,

        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            )

    })


# ============================================================
# EVENTS API
# ============================================================

@app.route("/api/events")
def api_events():

    events = read_events()

    file_events = events_by_source(
        events,
        "file_monitor"
    )

    network_events = events_by_source(
        events,
        "network_monitor"
    )

    detection_events = events_by_source(
        events,
        "detection_engine"
    )

    # Count meaningful incidents (risk assessments above LOW)
    incident_count = sum(
        1 for event in detection_events
        if (
            event.get("event_type") == "risk_assessment"
            and event.get("data", {}).get(
                "risk_level", "NORMAL"
            ) not in ("NORMAL", "LOW")
        )
    )

    risk = calculate_risk(events)

    return jsonify({

        "total_events":
            len(events),

        "file_events":
            len(file_events),

        "network_events":
            len(network_events),

        "alerts":
            incident_count,

        "risk":
            risk["risk_level"],

        "reason":
            risk["reason"],

        "signals":
            risk.get("signals", []),

        "recent_events":
            latest_events(
                events,
                50
            ),

        "network_events_list":
            latest_events(
                network_events,
                20
            ),

        "file_events_list":
            latest_events(
                file_events,
                20
            ),

        "detection_events_list":
            latest_events(
                detection_events,
                20
            )

    })


# ============================================================
# NETWORK API
# ============================================================

@app.route("/api/network")
def api_network():

    events = read_events()

    network_events = build_network_summary(
        events
    )

    repeated_events = [
        event
        for event in events
        if (
            event.get("event_type")
            == "repeated_network_activity"
        )
    ]

    return jsonify({

        "count":
            len(network_events),

        "connections":
            network_events,

        "repeated_activity":
            latest_events(
                repeated_events,
                20
            )

    })


# ============================================================
# PROCESS API
# ============================================================

@app.route("/api/processes")
def api_processes():

    events = read_events()

    processes = build_process_summary(
        events
    )

    return jsonify({

        "count":
            len(processes),

        "processes":
            processes

    })


# ============================================================
# FILE API
# ============================================================

@app.route("/api/files")
def api_files():

    events = read_events()

    files = build_file_summary(
        events
    )

    return jsonify({

        "count":
            len(files),

        "files":
            files

    })


# ============================================================
# RISK API
# ============================================================

@app.route("/api/risk")
def api_risk():

    events = read_events()
    risk = calculate_risk(events)

    # Build consistent ML sub-object from incident manager
    from core.incident_manager import incident_manager
    active = incident_manager.get_active_incident()

    ml_prob = active.get("ml_probability", 0.0) if active else 0.0
    ml_contributed = active.get("ml_contributed", False) if active else False

    result = dict(risk)
    result["incident_id"] = active["incident_id"] if active else None
    result["ml"] = {
        "classification": "RANSOMWARE_LIKE" if ml_prob > 0.7 else "NORMAL",
        "probability": ml_prob,
        "threshold": 0.7,
        "contributed": ml_contributed,
    }
    # Ensure top-level ml_contributed matches the ml sub-object
    result["ml_contributed"] = ml_contributed

    return jsonify(result)


# ============================================================
# INCIDENTS API
# ============================================================

@app.route("/api/incidents")
def api_incidents():
    """Return all incidents."""
    from core.incident_manager import incident_manager
    incidents = incident_manager.get_all_incidents()
    active = incident_manager.get_active_incident()
    return jsonify({
        "incidents": incidents,
        "active_incident_id": active["incident_id"] if active else None,
        "count": len(incidents),
    })


@app.route("/api/incidents/<incident_id>")
def api_incident_detail(incident_id):
    """Return a specific incident."""
    from core.incident_manager import incident_manager
    inc = incident_manager.get_incident(incident_id)
    if not inc:
        return jsonify({"error": "Incident not found"}), 404
    return jsonify(inc)


@app.route("/api/incidents/<incident_id>/acknowledge", methods=["POST"])
def api_incident_acknowledge(incident_id):
    """Acknowledge an incident → INVESTIGATING."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import _log_audit
    inc = incident_manager.acknowledge(incident_id)
    if not inc:
        return jsonify({"error": "Incident not found"}), 404
    _log_audit("incident_acknowledged", f"Incident {incident_id} acknowledged.", incident_id)
    return jsonify({"success": True, "incident": inc, "mode": "DRY_RUN"})


@app.route("/api/incidents/<incident_id>/contain", methods=["POST"])
def api_incident_contain(incident_id):
    """Trigger containment for an incident."""
    from core.prevention_engine import trigger_containment
    result = trigger_containment(incident_id)
    return jsonify(result)


@app.route("/api/incidents/<incident_id>/resolve", methods=["POST"])
def api_incident_resolve(incident_id):
    """Resolve an incident."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import _log_audit
    inc = incident_manager.resolve(incident_id)
    if not inc:
        return jsonify({"error": "Incident not found"}), 404
    _log_audit("incident_resolved", f"Incident {incident_id} resolved.", incident_id)
    return jsonify({"success": True, "incident": inc, "mode": "DRY_RUN"})


@app.route("/api/incidents/<incident_id>/close", methods=["POST"])
def api_incident_close(incident_id):
    """Close an incident."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import _log_audit
    inc = incident_manager.close(incident_id)
    if not inc:
        return jsonify({"error": "Incident not found"}), 404
    _log_audit("incident_closed", f"Incident {incident_id} closed.", incident_id)
    return jsonify({"success": True, "incident": inc, "mode": "DRY_RUN"})


# ============================================================
# PREVENTION API
# ============================================================

@app.route("/api/prevention/protect", methods=["POST"])
def api_prevention_protect():
    """Protect lab files (create snapshot)."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import protect_lab_files
    active = incident_manager.get_active_incident()
    incident_id = active["incident_id"] if active else None
    result = protect_lab_files(incident_id)
    return jsonify(result)


@app.route("/api/prevention/isolate-process", methods=["POST"])
def api_prevention_isolate_process():
    """Simulate process isolation."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import simulate_process_isolation

    data = request.get_json(silent=True) or {}
    pid = data.get("pid")
    process_name = data.get("process")
    active = incident_manager.get_active_incident()
    incident_id = active["incident_id"] if active else None

    result = simulate_process_isolation(
        pid=pid,
        process_name=process_name,
        incident_id=incident_id,
    )
    return jsonify(result)


@app.route("/api/prevention/kill-process", methods=["POST"])
def api_prevention_kill_process():
    """
    Terminate a process that is operating on test-files/.
    ONLY kills processes connected to the lab test directory.
    Requires PID.
    """
    from core.incident_manager import incident_manager
    from core.prevention_engine import kill_malicious_process

    data = request.get_json(silent=True) or {}
    pid = data.get("pid")

    if pid is None:
        return jsonify({"success": False, "message": "PID is required."}), 400

    active = incident_manager.get_active_incident()
    incident_id = active["incident_id"] if active else None

    result = kill_malicious_process(
        pid=int(pid),
        incident_id=incident_id,
    )
    return jsonify(result)


@app.route("/api/prevention/isolate-network", methods=["POST"])
def api_prevention_isolate_network():
    """Simulate network isolation."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import simulate_network_isolation

    data = request.get_json(silent=True) or {}
    target = data.get("target")
    active = incident_manager.get_active_incident()
    incident_id = active["incident_id"] if active else None

    result = simulate_network_isolation(
        incident_id=incident_id,
        target=target,
    )
    return jsonify(result)


# ============================================================
# RECOVERY API
# ============================================================

@app.route("/api/recovery/snapshot", methods=["POST"])
def api_recovery_snapshot():
    """Create a recovery snapshot."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import create_recovery_snapshot
    active = incident_manager.get_active_incident()
    incident_id = active["incident_id"] if active else None
    result = create_recovery_snapshot(incident_id)
    return jsonify(result)


@app.route("/api/recovery/restore", methods=["POST"])
def api_recovery_restore():
    """Restore lab files from snapshot."""
    from core.incident_manager import incident_manager
    from core.prevention_engine import restore_lab_files
    active = incident_manager.get_active_incident()
    incident_id = active["incident_id"] if active else None
    result = restore_lab_files(incident_id)
    return jsonify(result)


# ============================================================
# SIMULATION API
# ============================================================

@app.route("/api/simulation/run", methods=["POST"])
def api_simulation_run():
    """Run the safe ransomware behavior simulator."""
    from core.prevention_engine import run_safe_simulation
    result = run_safe_simulation()
    return jsonify(result)


# ============================================================
# AUDIT API
# ============================================================

@app.route("/api/audit")
def api_audit():
    """Return the audit log."""
    from core.prevention_engine import get_audit_log
    audit = get_audit_log()
    return jsonify({
        "entries": audit,
        "count": len(audit),
    })


# ============================================================
# CANARY API
# ============================================================

@app.route("/api/canary")
def api_canary():
    """Return canary/honeypot status."""
    from core.canary_manager import canary_manager
    status = canary_manager.check_canaries()
    return jsonify(status)


@app.route("/api/canary/reset", methods=["POST"])
def api_canary_reset():
    """Reset canary files (redeploy after incident)."""
    from core.canary_manager import canary_manager
    from core.prevention_engine import _log_audit
    result = canary_manager.reset()
    _log_audit("canary_reset", "Canary files redeployed.")
    return jsonify({"success": True, "canary": result})


# ============================================================
# CORRELATION API
# ============================================================

@app.route("/api/correlation")
def api_correlation():
    """Return process-network correlation data."""
    from core.correlation_engine import correlate_process_network
    try:
        correlations = correlate_process_network()
        return jsonify({
            "count": len(correlations),
            "correlations": correlations[:50],
        })
    except Exception as e:
        return jsonify({
            "count": 0,
            "correlations": [],
            "error": str(e),
        })


# ============================================================
# HEALTH API
# ============================================================

@app.route("/api/health")
def api_health():
    """Return real system health."""
    from core.prevention_engine import get_system_health
    health = get_system_health()
    return jsonify(health)


# ============================================================
# BACKGROUND DETECTION PIPELINE
# ============================================================

import threading

def _background_detection_loop():
    """
    Runs the detection pipeline continuously in a background thread.
    This ensures detection is ALWAYS active when the backend is running.
    No need to run detection_pipeline.py separately.
    """
    import time
    import sys
    sys.path.insert(0, PROJECT_ROOT)

    from core.config import POLL_INTERVAL

    # Import pipeline functions
    from detection_pipeline import evaluate_current_window

    print("[DETECTION] Background detection pipeline started.")

    while True:
        try:
            evaluate_current_window()
        except Exception as e:
            print(f"[DETECTION] Error: {e}")
        time.sleep(POLL_INTERVAL)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # Start background detection thread
    detection_thread = threading.Thread(
        target=_background_detection_loop,
        daemon=True,
    )
    detection_thread.start()

    print()
    print(
        "=========================================="
    )
    print(
        " RANSOMWARE DEFENSE // BACKEND API"
    )
    print(
        "=========================================="
    )
    print()

    print(
        "API:"
        " http://127.0.0.1:5000"
    )

    print()

    print(
        "Event source:"
    )

    print(
        LOG_FILE
    )

    print()

    print(
        "Mode: SAFE / DRY-RUN"
    )

    print(
        "Detection: ACTIVE (background thread)"
    )

    print()

    print(
        "Press Ctrl+C to stop."
    )

    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
