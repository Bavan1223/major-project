import time
from collections import deque

from event_logger import log_event


MODIFICATION_WINDOW = 10
MODIFICATION_THRESHOLD = 10

recent_modifications = deque()
alert_triggered = False


def record_modification(file_path):

    global alert_triggered

    current_time = time.time()

    recent_modifications.append(
        (current_time, file_path)
    )

    # Remove events older than our time window
    while recent_modifications:
        oldest_time = recent_modifications[0][0]

        if current_time - oldest_time > MODIFICATION_WINDOW:
            recent_modifications.popleft()
        else:
            break

    # Count unique files
    unique_files = {
        path for _, path in recent_modifications
    }

    # Reset alert state when the activity window falls below threshold
    if len(unique_files) < MODIFICATION_THRESHOLD:
        alert_triggered = False

    # Trigger only once when threshold is crossed
    if (
        len(unique_files) >= MODIFICATION_THRESHOLD
        and not alert_triggered
    ):

        alert_triggered = True

        print("\n🚨 SUSPICIOUS FILE ACTIVITY")
        print("Files modified:", len(unique_files))
        print("Time window   :", MODIFICATION_WINDOW, "seconds")
        print("Risk          : HIGH")
        print("-" * 50)

        log_event(
            source="detection_engine",
            event_type="suspicious_file_activity",
            indicator="rapid_mass_file_modification",
            data={
                "unique_files_modified": len(unique_files),
                "time_window_seconds": MODIFICATION_WINDOW,
                "risk": "HIGH"
            }
        )


print("=== Ransomware Behavior Detection Engine ===")
print("Monitoring started...")
