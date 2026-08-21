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
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta

from core.feature_extractor import extract_features
from core.risk_engine import evaluate_risk
from core.response_controller import process_risk_result
from core.protection_controller import process_response


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
    """

    now = datetime.now(timezone.utc)

    cutoff = (
        now -
        timedelta(seconds=WINDOW_SECONDS)
    )

    recent = []

    for event in events:

        timestamp = parse_timestamp(
            event.get("timestamp")
        )

        if timestamp is None:
            continue

        if timestamp >= cutoff:
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


def evaluate_current_window():

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

    response_result, _ = process_risk_result(
        risk_result
    )

    protection_result, _, _ = process_response(
        response_result
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
