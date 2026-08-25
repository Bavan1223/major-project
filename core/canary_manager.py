"""
Canary/Honeypot Manager — Defensive Decoy File System

Creates and monitors controlled canary (honeypot) files that act
as tripwires for ransomware detection. These are decoy files placed
in monitored directories that should NEVER be modified by legitimate
applications.

Any modification, deletion, or rename of a canary file is treated
as a HIGH-CONFIDENCE indicator of malicious file-system activity.

Safety:
    - Canary files are created only in the controlled canary-files/ directory
    - They contain identifiable decoy content
    - They are monitored via the existing file monitor infrastructure
    - They do not interfere with normal system operation
"""

import os
import hashlib
from datetime import datetime
from typing import Optional

from core.config import (
    CANARY_DIR,
    CANARY_FILE_COUNT,
    CANARY_PREFIX,
    PROJECT_ROOT,
)


# ==============================================================
# CANARY FILE DEFINITIONS
# ==============================================================

# Decoy filenames designed to attract ransomware behavior
CANARY_FILENAMES = [
    f"{CANARY_PREFIX}passwords_backup.txt",
    f"{CANARY_PREFIX}financial_records.xlsx",
    f"{CANARY_PREFIX}private_keys.pem",
    f"{CANARY_PREFIX}database_export.sql",
    f"{CANARY_PREFIX}important_documents.docx",
]

# Canary content (identifiable, not real sensitive data)
CANARY_CONTENT_TEMPLATE = (
    "CANARY TRIPWIRE FILE — DO NOT MODIFY\n"
    "This file is a defensive honeypot decoy.\n"
    "Any modification indicates unauthorized file-system activity.\n"
    "File: {filename}\n"
    "Deployed: {timestamp}\n"
    "Hash: {hash_placeholder}\n"
)


# ==============================================================
# CANARY STATE
# ==============================================================

class CanaryManager:
    """
    Manages canary file deployment, monitoring, and status reporting.
    """

    def __init__(self):
        self._canary_hashes: dict[str, str] = {}
        self._status: str = "NOT_DEPLOYED"
        self._triggered: bool = False
        self._triggered_files: list[str] = []
        self._deployed_at: Optional[str] = None
        self._deploy_canaries()

    def _deploy_canaries(self) -> None:
        """Deploy canary files if they don't exist."""
        os.makedirs(CANARY_DIR, exist_ok=True)

        deployed_count = 0
        for filename in CANARY_FILENAMES[:CANARY_FILE_COUNT]:
            filepath = os.path.join(CANARY_DIR, filename)

            if not os.path.exists(filepath):
                content = CANARY_CONTENT_TEMPLATE.format(
                    filename=filename,
                    timestamp=datetime.now().isoformat(timespec="seconds"),
                    hash_placeholder="pending",
                )
                with open(filepath, "w") as f:
                    f.write(content)
                deployed_count += 1

            # Record hash
            self._canary_hashes[filepath] = self._compute_hash(filepath)

        if self._canary_hashes:
            self._status = "ARMED"
            self._deployed_at = datetime.now().isoformat(timespec="seconds")

    def _compute_hash(self, filepath: str) -> str:
        """Compute SHA-256 hash of a file."""
        try:
            with open(filepath, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except OSError:
            return ""

    # ----------------------------------------------------------
    # CANARY CHECK
    # ----------------------------------------------------------

    def check_canaries(self) -> dict:
        """
        Check all canary files for modification/deletion.

        Returns status dict with:
            - status: ARMED / TRIGGERED / NOT_DEPLOYED
            - triggered: bool
            - triggered_files: list of modified/missing canaries
            - total: total canary count
            - intact: intact canary count
        """
        if not self._canary_hashes:
            return {
                "status": "NOT_DEPLOYED",
                "triggered": False,
                "triggered_files": [],
                "total": 0,
                "intact": 0,
            }

        triggered_files = []

        for filepath, original_hash in self._canary_hashes.items():
            if not os.path.exists(filepath):
                # File deleted — TRIGGERED
                triggered_files.append({
                    "path": filepath,
                    "reason": "DELETED",
                    "filename": os.path.basename(filepath),
                })
            else:
                current_hash = self._compute_hash(filepath)
                if current_hash != original_hash:
                    # File modified — TRIGGERED
                    triggered_files.append({
                        "path": filepath,
                        "reason": "MODIFIED",
                        "filename": os.path.basename(filepath),
                    })

        total = len(self._canary_hashes)
        intact = total - len(triggered_files)

        if triggered_files:
            self._status = "TRIGGERED"
            self._triggered = True
            self._triggered_files = triggered_files
        else:
            self._status = "ARMED"
            self._triggered = False
            self._triggered_files = []

        return {
            "status": self._status,
            "triggered": self._triggered,
            "triggered_files": triggered_files,
            "total": total,
            "intact": intact,
            "deployed_at": self._deployed_at,
        }

    def is_canary_path(self, path: str) -> bool:
        """Check if a given path is a canary file."""
        if not path:
            return False
        abs_path = os.path.abspath(path)
        return abs_path in self._canary_hashes

    def get_status(self) -> dict:
        """Get current canary status without re-checking files."""
        return {
            "status": self._status,
            "triggered": self._triggered,
            "triggered_files": self._triggered_files,
            "total": len(self._canary_hashes),
            "intact": len(self._canary_hashes) - len(self._triggered_files),
            "deployed_at": self._deployed_at,
            "canary_dir": CANARY_DIR,
        }

    def reset(self) -> dict:
        """Re-deploy canary files (reset after incident)."""
        self._canary_hashes = {}
        self._triggered = False
        self._triggered_files = []
        self._status = "NOT_DEPLOYED"
        self._deploy_canaries()
        return self.get_status()


# ==============================================================
# SINGLETON
# ==============================================================

canary_manager = CanaryManager()
