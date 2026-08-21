from collections import deque

from core.event_schema import validate_event


class EventCollector:
    """
    Central in-memory collector for validated Common Events.

    Responsibilities:
    - receive events
    - validate events
    - temporarily retain recent events
    - provide events to future feature extraction

    It does NOT:
    - calculate risk
    - perform prevention
    - perform ML
    """

    def __init__(self, max_events=1000):
        self.events = deque(maxlen=max_events)

    def collect(self, event):
        """
        Validate and collect a Common Event.

        Returns:
            event if valid

        Raises:
            ValueError if invalid
        """

        valid, error = validate_event(event)

        if not valid:
            raise ValueError(
                f"Invalid Common Event: {error}"
            )

        self.events.append(event)

        return event

    def get_recent_events(self, limit=100):
        """
        Return the most recent collected events.
        """

        if limit <= 0:
            return []

        return list(self.events)[-limit:]

    def count(self):
        """
        Return number of currently retained events.
        """

        return len(self.events)

    def clear(self):
        """
        Clear collected events.
        """

        self.events.clear()


# Shared collector instance for the core.
collector = EventCollector()
