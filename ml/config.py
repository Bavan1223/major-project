"""
ML Module Configuration.

Central configuration for the ML pipeline.
All constants that affect feature processing, model behavior, or versioning
are defined here to avoid hard-coding values across multiple files.

VERSION POLICY:
    - FEATURE_VERSION changes when the feature contract changes
      (features added, removed, reordered, or redefined)
    - MODEL_VERSION changes when a new model is trained
    - Both must match between training artifacts and inference

WINDOW POLICY:
    - WINDOW_SECONDS defines the primary observation window
    - All rate-based features are normalized by this value
    - Changing this requires retraining the model
"""

# =============================================================================
# VERSIONING
# =============================================================================

# Feature contract version.
# Increment when feature set changes (add/remove/redefine features).
FEATURE_VERSION = "1.0"

# Model version.
# Set during training. Must match the loaded model artifact.
# Placeholder until first model is trained.
MODEL_VERSION = None  # Set to "1.0" after first successful training

# =============================================================================
# OBSERVATION WINDOW
# =============================================================================

# Primary observation window in seconds.
# This is the time window over which behavioral features are aggregated.
# Matches the existing rule-based detection window (10 unique files in 10 seconds).
# Configurable for future experimentation with 5s, 30s, 60s windows.
WINDOW_SECONDS = 10

# =============================================================================
# LABELS
# =============================================================================

# Binary classification labels.
# 0 = normal system behavior
# 1 = ransomware-like behavioral pattern
LABEL_NORMAL = 0
LABEL_RANSOMWARE_LIKE = 1

# Human-readable label mapping (used in prediction output).
LABEL_MAP = {
    LABEL_NORMAL: "NORMAL",
    LABEL_RANSOMWARE_LIKE: "RANSOMWARE_LIKE",
}

# Reverse mapping for loading labeled data.
LABEL_MAP_REVERSE = {v: k for k, v in LABEL_MAP.items()}

# =============================================================================
# MODEL ARTIFACTS
# =============================================================================

# Relative paths from the ml/ directory root.
MODEL_DIR = "models"
MODEL_FILENAME = "ransomware_model.pkl"
PREPROCESSOR_FILENAME = "preprocessor.pkl"
FEATURE_DEF_PATH = "features/feature_definition.json"

# =============================================================================
# ML FEATURES USED FOR TRAINING AND INFERENCE
# =============================================================================

# Ordered list of features consumed by the ML model.
# This defines the exact input vector the model expects.
# Order matters — the model was trained with this exact column ordering.
#
# IMPORTANT: suspicious_indicators is EXCLUDED.
# See ml/features/suspicious_indicators_decision.md for rationale.
ML_FEATURE_COLUMNS = [
    "total_events",
    "file_created",
    "file_modified",
    "file_deleted",
    "file_renamed",
    "unique_files_modified",
    "process_events",
    "network_events",
    "established_connections",
    "unique_remote_ips",
]

# Features available from feature_extractor.py but NOT used by ML.
# Documented here for traceability.
EXCLUDED_FEATURES = {
    "file_events": "Redundant — linear combination of file_created + file_modified + file_deleted + file_renamed",
    "suspicious_indicators": "Derived from rule-based detection logic — creates circular reasoning if used as ML input",
}

# =============================================================================
# PROPOSED FUTURE FEATURES (NOT YET IMPLEMENTED)
# =============================================================================
# These require changes to core/feature_extractor.py.
# Listed here for planning only. Do NOT use until approved and implemented.
#
# "file_modification_rate": unique_files_modified / WINDOW_SECONDS
# "file_ops_per_process": (file_created + file_modified + file_deleted + file_renamed) / max(process_events, 1)
# "rename_to_modify_ratio": file_renamed / max(file_modified, 1)
# "delete_to_create_ratio": file_deleted / max(file_created, 1)
# "network_file_ratio": network_events / max(file_events, 1)

# =============================================================================
# INFERENCE SETTINGS
# =============================================================================

# Score threshold for classification (only used if model outputs probabilities).
# This is a starting point — proper threshold tuning happens during evaluation.
# Do NOT interpret this as a calibrated probability cutoff.
DEFAULT_SCORE_THRESHOLD = 0.5
