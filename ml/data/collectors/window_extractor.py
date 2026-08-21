"""
Window Extractor — Divides session events into 10-second observation windows.

Takes a list of Common Events from a session and groups them into
non-overlapping observation windows of WINDOW_SECONDS duration.

Each window's events are then passed to the feature extractor to produce
the behavioral feature vector.

IMPORTANT:
    - Uses the EXISTING core/feature_extractor.py for feature calculation
    - Selects only the 10 ML features per the feature contract v1.0
    - Does NOT include file_events or suspicious_indicators in ML output
"""

import sys
import os
from datetime import datetime, timezone

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DATA_DIR = os.path.dirname(SCRIPT_DIR)
ML_ROOT = os.path.dirname(ML_DATA_DIR)
PROJECT_ROOT = os.path.dirname(ML_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.config import ML_FEATURE_COLUMNS, WINDOW_SECONDS


def parse_timestamp(ts_string):
    """Parse ISO timestamp string to datetime object."""
    # Handle timezone-aware and naive timestamps
    try:
        return datetime.fromisoformat(ts_string)
    except ValueError:
        # Try replacing Z with +00:00 for older Python versions
        return datetime.fromisoformat(ts_string.replace("Z", "+00:00"))


def assign_events_to_windows(events, window_seconds=None):
    """
    Divide events into non-overlapping time windows.
    
    Args:
        events: List of Common Event dicts (must have 'timestamp' field)
        window_seconds: Window duration (defaults to config WINDOW_SECONDS)
        
    Returns:
        list of lists: Each inner list contains events for one window.
        Partial final windows (< window_seconds) are discarded.
    """
    if window_seconds is None:
        window_seconds = WINDOW_SECONDS

    if not events:
        return []

    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e["timestamp"])

    # Determine session start from first event
    session_start = parse_timestamp(sorted_events[0]["timestamp"])
    session_end = parse_timestamp(sorted_events[-1]["timestamp"])

    # Calculate total duration
    total_duration = (session_end - session_start).total_seconds()

    # Calculate number of COMPLETE windows
    num_complete_windows = int(total_duration // window_seconds)
    # Ensure at least 1 window if events exist within the first window_seconds
    if num_complete_windows == 0 and events:
        num_complete_windows = 1

    # Assign events to windows
    windows = [[] for _ in range(num_complete_windows)]

    for event in sorted_events:
        event_time = parse_timestamp(event["timestamp"])
        elapsed = (event_time - session_start).total_seconds()
        window_idx = int(elapsed // window_seconds)

        # Only assign to complete windows
        if 0 <= window_idx < num_complete_windows:
            windows[window_idx].append(event)

    return windows


def extract_ml_features_from_window(window_events, feature_extractor_fn):
    """
    Extract the 10 ML features from a window's events.
    
    Args:
        window_events: List of Common Events in this window
        feature_extractor_fn: The core feature extraction function
                              (core.feature_extractor.extract_features)
                              
    Returns:
        dict: 10 ML features matching ML_FEATURE_COLUMNS
    """
    # Call the core feature extractor (produces 12 features)
    full_features = feature_extractor_fn(window_events)

    # Select only the 10 ML features in the correct order
    ml_features = {col: full_features[col] for col in ML_FEATURE_COLUMNS}

    return ml_features


def extract_ml_features_simulated(window_events):
    """
    Extract ML features using the simulated feature extractor.
    Used for local testing when core/feature_extractor.py is not available.
    
    This mirrors the exact logic from the verified Ubuntu source code.
    """
    from ml.tests.test_feature_extractor_compatibility import simulated_extract_features
    full_features = simulated_extract_features(window_events)
    ml_features = {col: full_features[col] for col in ML_FEATURE_COLUMNS}
    return ml_features


def process_session_events(events, session_id, scenario_id, label,
                           feature_extractor_fn=None, window_seconds=None):
    """
    Process all events from a session into labeled ML feature records.
    
    Args:
        events: List of Common Events from the session
        session_id: Unique session identifier (e.g., "S_0001")
        scenario_id: Scenario that was executed (e.g., "N1", "R3")
        label: Ground truth label (0 or 1)
        feature_extractor_fn: Feature extraction function (or None for simulated)
        window_seconds: Window duration (defaults to config)
        
    Returns:
        list of dicts: One record per complete window, containing:
            - session_id
            - window_id
            - scenario_id
            - label
            - 10 ML feature values
    """
    if window_seconds is None:
        window_seconds = WINDOW_SECONDS

    # Divide events into windows
    windows = assign_events_to_windows(events, window_seconds)

    records = []
    for i, window_events in enumerate(windows):
        window_id = f"{session_id}_W{i+1:02d}"

        # Extract features
        if feature_extractor_fn is not None:
            ml_features = extract_ml_features_from_window(window_events, feature_extractor_fn)
        else:
            ml_features = extract_ml_features_simulated(window_events)

        # Build record
        record = {
            "session_id": session_id,
            "window_id": window_id,
            "scenario_id": scenario_id,
            "label": label,
        }
        # Add features in contract order
        for col in ML_FEATURE_COLUMNS:
            record[col] = ml_features[col]

        records.append(record)

    return records
