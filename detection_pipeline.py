"""
Gate 11 — Live Detection Pipeline

Connects:
    events.jsonl
        ↓
    recent event window
        ↓
    feature extractor
        ↓
    risk engine (Rules + ML)
        ↓
    response controller (DRY_RUN)
        ↓
    protection controller (DRY_RUN)

No monitor code is modified.
No containment is executed.

Incident State Management:
    - Only logs response/protection events on STATE TRANSITIONS
    - Same active incident does NOT produce duplicate events
    - Recovery to NORMAL is logged once
    - A new distinct incident produces new events
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta

from core.feature_extractor import extract_features
from core.risk_engine import evaluate_risk
from core.response_controller import (
    process_risk_result,
    determine_response,
    log_response_decision,
)
from core.protection_controller import (
    process_response,
    determine_protection,
    log_protection_decision,
    simulate_containment,
)


PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

LOG_FILE = os.path.join(
    PROJECT_ROOT,
    "logs",
    "events.jsonl"
)

WINDOW_SECONDS = 10
POLL_INTERVAL = 1


# =============================================================
# INCIDENT STATE TRACKING
# =============================================================
# The incident signature captures the meaningful behavioral
# state. If the signature hasn't changed, we do NOT log
# duplicate response/protection events.

_current_incident_signature = None


def load_events():
    """Load valid JSON events from the event log."""

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

                except json.JSONDecodeError:
                    continue

                if isinstance(event, dict):
                    events.append(event)

    except OSError as exc:

        print(
            f"[PIPELINE] Log read error: {exc}"
        )

    return events


def parse_timestamp(timestamp):
    """Convert event timestamp to timezone-aware datetime."""

    if not isinstance(timestamp, str):
        return None

    try:
        value = datetime.fromisoformat(timestamp)

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return value

    except ValueError:
        return None


def get_recent_events(events):
    """
    Return events inside the behavioral observation window.

    Note: Events are logged with local time (no timezone).
    We compare against local time to maintain consistency.
    """

    now = datetime.now()

    cutoff = (
        now -
        timedelta(seconds=WINDOW_SECONDS)
    )

    recent = []

    for event in events:

        ts_str = event.get("timestamp")

        if not isinstance(ts_str, str):
            continue

        try:
            # Parse as naive local time (matching event_logger)
            ts = datetime.fromisoformat(ts_str)

            # Strip any timezone info for consistent comparison
            if ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)

        except ValueError:
            continue

        if ts >= cutoff:
            recent.append(event)

    return recent


def print_risk_result(
    features,
    risk_result,
    response_result,
    protection_result
):

    ml_signal = risk_result.get(
        "ml_signal"
    )

    print()
    print("=" * 65)
    print(" LIVE BEHAVIORAL RISK ASSESSMENT")
    print("=" * 65)

    print(
        "Events             :",
        features["total_events"]
    )

    print(
        "File modifications :",
        features["file_modified"]
    )

    print(
        "Unique files       :",
        features["unique_files_modified"]
    )

    print(
        "Network events     :",
        features["network_events"]
    )

    print(
        "Suspicious signals :",
        features["suspicious_indicators"]
    )

    print(
        "Final risk         :",
        risk_result["risk_level"]
    )

    print(
        "Reason             :",
        risk_result["reason"]
    )

    print(
        "Signals            :",
        risk_result["signals"]
    )

    if ml_signal is None:

        print(
            "ML                 : UNAVAILABLE"
        )

    else:

        print(
            "ML                 :",
            ml_signal.get("label")
        )

        print(
            "ML probability     :",
            ml_signal.get("probability")
        )

        print(
            "ML threshold       :",
            ml_signal.get("threshold")
        )

        print(
            "ML above threshold :",
            ml_signal.get("above_threshold")
        )

        print(
            "ML contributed     :",
            risk_result.get(
                "ml_contributed",
                False
            )
        )

    print(
        "Response            :",
        response_result["recommended_action"]
    )

    print(
        "Protection          :",
        protection_result["protection_action"]
    )

    print(
        "Protection mode     :",
        protection_result["mode"]
    )

    print("=" * 65)


def _compute_incident_signature(risk_result):
    """
    Compute a stable signature for the current risk state.

    The signature is based on:
      - risk_level
      - reason
      - sorted signals

    Timestamps are NOT included because they change every
    second and would defeat deduplication.
    """

    return (
        risk_result.get("risk_level", "NORMAL"),
        risk_result.get("reason", ""),
        tuple(sorted(risk_result.get("signals", [])))
    )


def evaluate_current_window():
    """
    Evaluate the current behavioral window with incident
    state management.

    Only logs response/protection events when the incident
    state CHANGES (new incident or recovery).

    The risk assessment is ALWAYS logged so the dashboard
    can read the latest behavioral state.

    Console output continues every cycle for live visibility.
    """

    global _current_incident_signature

    events = load_events()

    recent_events = get_recent_events(
        events
    )

    features = extract_features(
        recent_events
    )

    risk_result = evaluate_risk(
        features
    )

    # --------------------------------------------------
    # INCIDENT STATE TRANSITION CHECK
    # --------------------------------------------------

    new_signature = _compute_incident_signature(
        risk_result
    )

    is_state_transition = (
        new_signature != _current_incident_signature
    )

    # --------------------------------------------------
    # ALWAYS: Determine response and protection
    # (for console display and return value)
    # --------------------------------------------------

    response_result = determine_response(
        risk_result
    )

    protection_result = determine_protection(
        response_result
    )

    # --------------------------------------------------
    # CONDITIONAL: Only log events on state transitions
    # --------------------------------------------------

    if is_state_transition:

        # Log the risk assessment event
        from core.risk_engine import log_risk_decision
        log_risk_decision(risk_result, features)

        # Log response recommendation
        log_response_decision(response_result)

        # Log protection decision
        containment_result = {
            "status": "NOT_REQUIRED",
            "target": None,
            "mode": protection_result["mode"]
        }

        if protection_result[
            "protection_action"
        ] == "LAB_CONTAINMENT_RECOMMENDED":
            containment_result = simulate_containment(
                None
            )

        log_protection_decision(
            protection_result,
            containment_result
        )

        # --------------------------------------------------
        # INCIDENT MANAGEMENT
        # --------------------------------------------------
        from core.incident_manager import incident_manager

        risk_level = risk_result["risk_level"]
        ml_signal = risk_result.get("ml_signal")
        ml_prob = (
            ml_signal.get("probability", 0.0)
            if ml_signal else 0.0
        )

        if risk_level not in ("NORMAL", "LOW"):
            # Check if there's already an active incident
            active = incident_manager.get_active_incident()

            if active is None:
                # Create a new incident
                incident_manager.create_incident(
                    risk_level=risk_level,
                    reason=risk_result["reason"],
                    signals=risk_result["signals"],
                    ml_probability=ml_prob,
                    ml_contributed=risk_result.get(
                        "ml_contributed", False
                    ),
                    file_count=features.get(
                        "unique_files_modified", 0
                    ),
                    network_count=features.get(
                        "network_events", 0
                    ),
                )
            else:
                # Update existing incident risk
                incident_manager.update_risk(
                    active["incident_id"],
                    risk_level=risk_level,
                    reason=risk_result["reason"],
                    signals=risk_result["signals"],
                    ml_probability=ml_prob,
                )
        else:
            # Risk returned to NORMAL/LOW — clear active
            active = incident_manager.get_active_incident()
            if active:
                incident_manager.add_timeline_event(
                    active["incident_id"],
                    "risk_cleared",
                    "Behavioral risk returned to NORMAL.",
                )
                incident_manager.clear_active()

        # Update current incident state
        _current_incident_signature = new_signature

        if risk_level not in ("NORMAL", "LOW"):
            print(
                "\n[INCIDENT] NEW state transition → "
                f"{risk_level}"
            )
        else:
            print(
                "\n[INCIDENT] State recovered → NORMAL"
            )

    return (
        recent_events,
        features,
        risk_result,
        response_result,
        protection_result
    )


def run_once():

    (
        recent_events,
        features,
        risk_result,
        response_result,
        protection_result
    ) = evaluate_current_window()

    print_risk_result(
        features,
        risk_result,
        response_result,
        protection_result
    )

    return risk_result


def main():

    print("=" * 65)
    print(" GATE 11 — LIVE DETECTION PIPELINE")
    print("=" * 65)

    print()
    print("Project :", PROJECT_ROOT)
    print("Log     :", LOG_FILE)
    print(
        "Window  :",
        WINDOW_SECONDS,
        "seconds"
    )
    print(
        "Mode    : DRY_RUN"
    )

    print()
    print(
        "Starting live pipeline..."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print()

    try:

        while True:

            run_once()

            time.sleep(
                POLL_INTERVAL
            )

    except KeyboardInterrupt:

        print()
        print(
            "[PIPELINE] Stopped safely."
        )


if __name__ == "__main__":
    main()
