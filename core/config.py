"""
Unified Configuration — Ransomware Defense System

Central configuration for all detection, prevention, and system
parameters. Avoid scattering hardcoded constants.

Safety:
    DRY_RUN = True (default)
    SAFE_LAB_MODE = True (default)
"""

import os

# ==============================================================
# PATHS
# ==============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

LAB_DIR = os.path.join(PROJECT_ROOT, "test-files")
CANARY_DIR = os.path.join(PROJECT_ROOT, "canary-files")
RECOVERY_DIR = os.path.join(PROJECT_ROOT, "recovery")
SNAPSHOTS_DIR = os.path.join(RECOVERY_DIR, "snapshots")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
EVENT_LOG = os.path.join(LOG_DIR, "events.jsonl")
INCIDENTS_FILE = os.path.join(LOG_DIR, "incidents.json")
AUDIT_FILE = os.path.join(LOG_DIR, "audit.json")

# ==============================================================
# DETECTION
# ==============================================================

# Observation window for behavioral analysis (seconds)
WINDOW_SECONDS = 30

# Detection pipeline polling interval (seconds)
POLL_INTERVAL = 2

# ==============================================================
# RISK THRESHOLDS
# ==============================================================

# Minimum unique files modified to trigger HIGH (rapid_mass_file_modification)
# This is evaluated by the detection_engine when it fires the indicator
RAPID_MASS_THRESHOLD = 10

# Minimum unique files for the "multiple_unique_files_modified" signal
UNIQUE_FILES_THRESHOLD = 10

# Minimum unique files for MEDIUM (elevated activity)
MEDIUM_FILES_THRESHOLD = 5

# ==============================================================
# ML
# ==============================================================

# ML classification threshold (probability above which = RANSOMWARE_LIKE)
ML_THRESHOLD = 0.7

# ML model version
ML_MODEL_VERSION = "2.0.0"

# ==============================================================
# INCIDENT
# ==============================================================

# Maximum age (seconds) for an active incident before it's considered
# stale. If the pipeline hasn't updated the incident within this
# window, the API should treat the system as recovering.
INCIDENT_STALE_TIMEOUT = 60

# ==============================================================
# SAFETY
# ==============================================================

# DRY_RUN: No destructive enforcement actions
DRY_RUN = True

# SAFE_LAB_MODE: All operations restricted to lab directories
SAFE_LAB_MODE = True

# ==============================================================
# CANARY
# ==============================================================

# Number of canary files to deploy
CANARY_FILE_COUNT = 5

# Canary file prefix
CANARY_PREFIX = "canary_trap_"
