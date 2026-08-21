import json
import os
from datetime import datetime

from core.event_schema import validate_event
from core.event_collector import collector


LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "logs",
    "events.jsonl"
)


def log_event(
    source,
    event_type,
    indicator=None,
    pid=None,
    process=None,
    data=None
):

    event = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "event_type": event_type,
        "pid": pid,
        "process": process,
        "indicator": indicator,
        "data": data or {}
    }

    # Validate before collection
    valid, error = validate_event(event)

    if not valid:
        raise ValueError(
            f"Invalid Common Event: {error}"
        )

    # Send validated event to central collector
    collector.collect(event)

    # Persist event
    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(event) + "\n"
        )

    return event
