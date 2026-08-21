from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from detection_engine import record_modification
from event_logger import log_event


WATCH_DIRECTORY = "/home/bavan/ransomware-lab/test-files"


class RansomwareFileMonitor(FileSystemEventHandler):

    def on_created(self, event):
        if not event.is_directory:
            print("[FILE CREATED]")
            print("Path:", event.src_path)

            log_event(
                source="file_monitor",
                event_type="file_created",
                indicator="file_creation",
                data={
                    "path": event.src_path
                }
            )

            print("-" * 50)

    def on_modified(self, event):
        if not event.is_directory:
            print("[FILE MODIFIED]")
            print("Path:", event.src_path)

            record_modification(event.src_path)

            log_event(
                source="file_monitor",
                event_type="file_modified",
                indicator="file_modification",
                data={
                    "path": event.src_path
                }
            )

            print("-" * 50)

    def on_deleted(self, event):
        if not event.is_directory:
            print("[FILE DELETED]")
            print("Path:", event.src_path)

            log_event(
                source="file_monitor",
                event_type="file_deleted",
                indicator="file_deletion",
                data={
                    "path": event.src_path
                }
            )

            print("-" * 50)

    def on_moved(self, event):
        if not event.is_directory:
            print("[FILE RENAMED]")
            print("From:", event.src_path)
            print("To  :", event.dest_path)

            log_event(
                source="file_monitor",
                event_type="file_renamed",
                indicator="file_rename",
                data={
                    "from": event.src_path,
                    "to": event.dest_path
                }
            )

            print("-" * 50)


event_handler = RansomwareFileMonitor()

observer = Observer()

observer.schedule(
    event_handler,
    WATCH_DIRECTORY,
    recursive=True
)

observer.start()

print("=== Ransomware Defense - File Monitor ===")
print("Monitoring:", WATCH_DIRECTORY)
print("Press Ctrl+C to stop.\n")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    observer.stop()

observer.join()
