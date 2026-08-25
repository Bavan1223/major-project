"""
Central Incident Manager

Manages the lifecycle of security incidents detected by the
ransomware defense system.

Incident Lifecycle:
    OPEN → INVESTIGATING → CONTAINED → RESOLVED → CLOSED

Each behavioral detection that exceeds LOW creates or updates
an incident. The same active behavioral condition maps to ONE
incident (no duplicates per polling cycle).

Safety:
    This module does NOT perform containment actions.
    It tracks state only. Actual safe-lab actions are
    delegated to the prevention_engine module.
"""

import os
import json
import uuid
from datetime import datetime
from threading import Lock


# ==============================================================
# INCIDENT STATES
# ==============================================================

INCIDENT_STATES = [
    "OPEN",
    "INVESTIGATING",
    "CONTAINED",
    "RESOLVED",
    "CLOSED",
]

RISK_LEVELS = [
    "NORMAL",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


# ==============================================================
# INCIDENT STORAGE
# ==============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INCIDENTS_FILE = os.path.join(
    PROJECT_ROOT, "logs", "incidents.json"
)


class IncidentManager:
    """
    Thread-safe incident lifecycle manager.

    Stores incidents in memory and persists to disk.
    """

    def __init__(self):
        self._lock = Lock()
        self._incidents: dict = {}
        self._active_incident_id: str | None = None
        self._load()

    # ----------------------------------------------------------
    # PERSISTENCE
    # ----------------------------------------------------------

    def _load(self):
        """Load incidents from disk."""
        if os.path.exists(INCIDENTS_FILE):
            try:
                with open(INCIDENTS_FILE, "r") as f:
                    data = json.load(f)
                self._incidents = data.get("incidents", {})
                self._active_incident_id = data.get(
                    "active_incident_id"
                )
            except (json.JSONDecodeError, OSError):
                self._incidents = {}
                self._active_incident_id = None

    def _save(self):
        """Persist incidents to disk."""
        os.makedirs(os.path.dirname(INCIDENTS_FILE), exist_ok=True)
        try:
            with open(INCIDENTS_FILE, "w") as f:
                json.dump(
                    {
                        "incidents": self._incidents,
                        "active_incident_id": self._active_incident_id,
                    },
                    f,
                    indent=2,
                    default=str,
                )
        except OSError:
            pass

    # ----------------------------------------------------------
    # INCIDENT CREATION
    # ----------------------------------------------------------

    def create_incident(
        self,
        risk_level: str,
        reason: str,
        signals: list,
        ml_probability: float = 0.0,
        ml_contributed: bool = False,
        process: str | None = None,
        pid: int | None = None,
        file_count: int = 0,
        network_count: int = 0,
        affected_paths: list | None = None,
        remote_endpoints: list | None = None,
    ) -> dict:
        """
        Create a new incident. Returns the incident dict.
        """
        with self._lock:
            incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
            now = datetime.now().isoformat(timespec="seconds")

            incident = {
                "incident_id": incident_id,
                "created_at": now,
                "updated_at": now,
                "status": "OPEN",
                "risk_level": risk_level,
                "reason": reason,
                "signals": signals,
                "confidence": ml_probability,
                "ml_probability": ml_probability,
                "ml_contributed": ml_contributed,
                "process": process,
                "pid": pid,
                "file_count": file_count,
                "network_count": network_count,
                "affected_paths": affected_paths or [],
                "remote_endpoints": remote_endpoints or [],
                "response_action": self._response_for_level(risk_level),
                "protection_action": self._protection_for_level(risk_level),
                "containment_status": "NOT_CONTAINED",
                "recovery_status": "NOT_STARTED",
                "timeline": [
                    {
                        "timestamp": now,
                        "action": "incident_created",
                        "detail": f"Incident created at {risk_level} level.",
                    }
                ],
            }

            self._incidents[incident_id] = incident
            self._active_incident_id = incident_id
            self._save()
            return incident

    # ----------------------------------------------------------
    # INCIDENT QUERIES
    # ----------------------------------------------------------

    def get_active_incident(self) -> dict | None:
        """Return the currently active incident, or None."""
        with self._lock:
            if self._active_incident_id:
                inc = self._incidents.get(self._active_incident_id)
                if inc and inc["status"] not in ("RESOLVED", "CLOSED"):
                    return inc
            return None

    def get_incident(self, incident_id: str) -> dict | None:
        """Return a specific incident by ID."""
        with self._lock:
            return self._incidents.get(incident_id)

    def get_all_incidents(self) -> list:
        """Return all incidents, newest first."""
        with self._lock:
            return sorted(
                self._incidents.values(),
                key=lambda x: x.get("created_at", ""),
                reverse=True,
            )

    @property
    def active_incident_id(self) -> str | None:
        with self._lock:
            return self._active_incident_id

    # ----------------------------------------------------------
    # STATE TRANSITIONS
    # ----------------------------------------------------------

    def acknowledge(self, incident_id: str) -> dict | None:
        """Transition to INVESTIGATING."""
        return self._transition(
            incident_id, "INVESTIGATING", "incident_acknowledged"
        )

    def contain(self, incident_id: str) -> dict | None:
        """Transition to CONTAINED."""
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                return None
            if inc["status"] in ("RESOLVED", "CLOSED"):
                return inc
            inc["status"] = "CONTAINED"
            inc["containment_status"] = "CONTAINED"
            inc["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            inc["timeline"].append({
                "timestamp": inc["updated_at"],
                "action": "containment_started",
                "detail": "Safe lab containment activated (DRY_RUN).",
            })
            self._save()
            return inc

    def resolve(self, incident_id: str) -> dict | None:
        """Transition to RESOLVED."""
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                return None
            if inc["status"] == "CLOSED":
                return inc
            inc["status"] = "RESOLVED"
            inc["recovery_status"] = "COMPLETED"
            inc["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            inc["timeline"].append({
                "timestamp": inc["updated_at"],
                "action": "incident_resolved",
                "detail": "Incident resolved. Recovery confirmed.",
            })
            self._save()
            return inc

    def close(self, incident_id: str) -> dict | None:
        """Transition to CLOSED."""
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                return None
            inc["status"] = "CLOSED"
            inc["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            inc["timeline"].append({
                "timestamp": inc["updated_at"],
                "action": "incident_closed",
                "detail": "Incident closed.",
            })
            # Clear active if this was the active incident
            if self._active_incident_id == incident_id:
                self._active_incident_id = None
            self._save()
            return inc

    def update_risk(
        self,
        incident_id: str,
        risk_level: str,
        reason: str,
        signals: list,
        ml_probability: float = 0.0,
    ) -> dict | None:
        """Update the risk assessment of an active incident."""
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                return None
            if inc["status"] in ("RESOLVED", "CLOSED"):
                return inc
            inc["risk_level"] = risk_level
            inc["reason"] = reason
            inc["signals"] = signals
            inc["ml_probability"] = ml_probability
            inc["confidence"] = ml_probability
            inc["response_action"] = self._response_for_level(risk_level)
            inc["protection_action"] = self._protection_for_level(risk_level)
            inc["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            self._save()
            return inc

    def add_timeline_event(
        self, incident_id: str, action: str, detail: str
    ) -> None:
        """Add a timeline entry to an incident."""
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                return
            inc["timeline"].append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "action": action,
                "detail": detail,
            })
            inc["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            self._save()

    def clear_active(self) -> None:
        """Clear the active incident pointer (on recovery to NORMAL)."""
        with self._lock:
            self._active_incident_id = None
            self._save()

    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------

    def _transition(
        self, incident_id: str, new_status: str, action: str
    ) -> dict | None:
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                return None
            if inc["status"] in ("RESOLVED", "CLOSED"):
                return inc
            inc["status"] = new_status
            inc["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            inc["timeline"].append({
                "timestamp": inc["updated_at"],
                "action": action,
                "detail": f"Status changed to {new_status}.",
            })
            self._save()
            return inc

    @staticmethod
    def _response_for_level(level: str) -> str:
        return {
            "NORMAL": "NO_ACTION",
            "LOW": "MONITOR",
            "MEDIUM": "INCREASE_MONITORING",
            "HIGH": "CONTAINMENT_RECOMMENDED",
            "CRITICAL": "CRITICAL_RESPONSE_RESERVED",
        }.get(level, "NO_ACTION")

    @staticmethod
    def _protection_for_level(level: str) -> str:
        return {
            "NORMAL": "NO_PROTECTION",
            "LOW": "NO_PROTECTION",
            "MEDIUM": "MONITOR_ONLY",
            "HIGH": "LAB_CONTAINMENT_RECOMMENDED",
            "CRITICAL": "CRITICAL_PROTECTION_RESERVED",
        }.get(level, "NO_PROTECTION")


# ==============================================================
# SINGLETON
# ==============================================================

incident_manager = IncidentManager()
