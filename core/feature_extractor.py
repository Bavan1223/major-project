from collections import Counter


def extract_features(events):
    """
    Convert Common Events into behavioral features.

    This module does not perform ML or risk scoring.
    """

    features = {
        "total_events": len(events),

        "file_events": 0,
        "file_created": 0,
        "file_modified": 0,
        "file_deleted": 0,
        "file_renamed": 0,

        "unique_files_modified": 0,

        "process_events": 0,
        "network_events": 0,

        "established_connections": 0,
        "unique_remote_ips": 0,

        "suspicious_indicators": 0,

        "canary_events": 0,
    }

    modified_files = set()
    remote_ips = set()

    event_types = Counter()

    for event in events:

        source = event.get("source")
        event_type = event.get("event_type")
        indicator = event.get("indicator")
        data = event.get("data", {})

        event_types[event_type] += 1

        # -------------------------
        # FILE BEHAVIOR
        # -------------------------

        if source == "file_monitor":

            features["file_events"] += 1

            if event_type == "file_created":
                features["file_created"] += 1

            elif event_type == "file_modified":

                features["file_modified"] += 1

                path = data.get("path")

                if path:
                    modified_files.add(path)

            elif event_type == "file_deleted":
                features["file_deleted"] += 1

            elif event_type == "file_renamed":
                features["file_renamed"] += 1

        # -------------------------
        # PROCESS BEHAVIOR
        # -------------------------

        elif source == "process_monitor":

            features["process_events"] += 1

        # -------------------------
        # NETWORK BEHAVIOR
        # -------------------------

        elif source == "network_monitor":

            features["network_events"] += 1

            if data.get("status") == "ESTABLISHED":

                features["established_connections"] += 1

            remote_address = data.get("remote_address")

            if remote_address:

                remote_ip = remote_address.split(":")[0]
                remote_ips.add(remote_ip)

        # -------------------------
        # SUSPICIOUS INDICATORS
        # -------------------------

        if indicator in {
            "rapid_mass_file_modification",
            "suspicious_file_activity"
        }:

            features["suspicious_indicators"] += 1

        # -------------------------
        # CANARY / HONEYPOT
        # -------------------------

        if indicator in {
            "canary_triggered",
            "canary_modified",
            "canary_deleted",
        }:
            features["canary_events"] += 1

    features["unique_files_modified"] = len(modified_files)
    features["unique_remote_ips"] = len(remote_ips)

    return features


if __name__ == "__main__":

    print("=== Behavioral Feature Extractor ===")

    # Simple standalone test
    test_events = [
        {
            "source": "file_monitor",
            "event_type": "file_modified",
            "indicator": "file_modification",
            "data": {
                "path": "/tmp/file1.txt"
            }
        },
        {
            "source": "file_monitor",
            "event_type": "file_modified",
            "indicator": "file_modification",
            "data": {
                "path": "/tmp/file2.txt"
            }
        },
        {
            "source": "network_monitor",
            "event_type": "network_connection",
            "indicator": "new_established_connection",
            "data": {
                "local_address": "192.168.74.131:9001",
                "remote_address": "192.168.74.129:37146",
                "status": "ESTABLISHED"
            }
        }
    ]

    features = extract_features(test_events)

    for name, value in features.items():
        print(f"{name:25}: {value}")
