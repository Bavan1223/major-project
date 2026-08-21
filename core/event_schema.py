from datetime import datetime


VALID_SOURCES = {
    "file_monitor",
    "process_monitor",
    "network_monitor",
    "honeypot",
    "detection_engine",
    "test"
}


def validate_event(event):
    """
    Validate a Common Event.

    Returns:
        (True, None) if valid
        (False, error_message) if invalid
    """

    if not isinstance(event, dict):
        return False, "Event must be a dictionary"

    # Required fields
    required_fields = {
        "timestamp",
        "source",
        "event_type",
        "pid",
        "process",
        "indicator",
        "data"
    }

    missing_fields = required_fields - event.keys()

    if missing_fields:
        return False, (
            "Missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    # Validate timestamp
    if not isinstance(event["timestamp"], str):
        return False, "timestamp must be a string"

    try:
        datetime.fromisoformat(event["timestamp"])
    except ValueError:
        return False, "timestamp must be a valid ISO timestamp"

    # Validate source
    if not isinstance(event["source"], str):
        return False, "source must be a string"

    if not event["source"].strip():
        return False, "source cannot be empty"

    if event["source"] not in VALID_SOURCES:
        return False, (
            f"Invalid source: {event['source']}"
        )

    # Validate event type
    if not isinstance(event["event_type"], str):
        return False, "event_type must be a string"

    if not event["event_type"].strip():
        return False, "event_type cannot be empty"

    # PID can legitimately be None
    if event["pid"] is not None:
        if not isinstance(event["pid"], int):
            return False, "pid must be an integer or None"

        if event["pid"] < 0:
            return False, "pid cannot be negative"

    # Process can legitimately be None
    if event["process"] is not None:
        if not isinstance(event["process"], str):
            return False, "process must be a string or None"

    # Indicator can legitimately be None
    if event["indicator"] is not None:
        if not isinstance(event["indicator"], str):
            return False, "indicator must be a string or None"

    # Data must be a dictionary
    if not isinstance(event["data"], dict):
        return False, "data must be a dictionary"

    return True, None
