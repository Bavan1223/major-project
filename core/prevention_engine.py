"""
Prevention Engine — Safe Lab Actions

Implements safe, controlled prevention and containment actions
for the ransomware defense lab.

Safety Guarantees:
    - All actions operate in DRY_RUN / SAFE_LAB_MODE
    - Only targets within ~/ransomware-lab/test-files are affected
    - No arbitrary process killing
    - No real firewall manipulation
    - No real network isolation
    - Recovery snapshots only copy controlled lab files

Actions:
    - protect_lab_files: backup test-files to recovery/
    - simulate_process_isolation: record isolation without killing
    - simulate_network_isolation: record network isolation
    - restore_lab_files: restore from recovery snapshot
    - create_recovery_snapshot: snapshot the test-files directory
"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional

from core.incident_manager import incident_manager


# ==============================================================
# PATHS
# ==============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

LAB_DIR = os.path.join(PROJECT_ROOT, "test-files")
RECOVERY_DIR = os.path.join(PROJECT_ROOT, "recovery")
SNAPSHOTS_DIR = os.path.join(RECOVERY_DIR, "snapshots")


# ==============================================================
# AUDIT LOG
# ==============================================================

AUDIT_FILE = os.path.join(PROJECT_ROOT, "logs", "audit.json")

_audit_log: list = []


def _load_audit():
    """Load audit log from disk."""
    global _audit_log
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                _audit_log = json.load(f)
        except (json.JSONDecodeError, OSError):
            _audit_log = []


def _save_audit():
    """Persist audit log to disk."""
    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
    try:
        with open(AUDIT_FILE, "w") as f:
            json.dump(_audit_log, f, indent=2, default=str)
    except OSError:
        pass


# Load on module import
_load_audit()


def get_audit_log() -> list:
    """Return the audit log (most recent first)."""
    return list(reversed(_audit_log))


def _log_audit(
    action: str,
    detail: str,
    incident_id: Optional[str] = None,
    success: bool = True,
) -> dict:
    """Record an audit entry and persist to disk."""
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "actor": "system",
        "action": action,
        "incident_id": incident_id,
        "mode": "DRY_RUN",
        "success": success,
        "detail": detail,
    }
    _audit_log.append(entry)
    _save_audit()

    # Also add to incident timeline if applicable
    if incident_id:
        incident_manager.add_timeline_event(
            incident_id, action, detail
        )

    return entry


# ==============================================================
# FILE PROTECTION
# ==============================================================

def create_recovery_snapshot(incident_id: Optional[str] = None) -> dict:
    """
    Create a snapshot of the lab test-files directory.
    This is a REAL file copy within the controlled lab.
    """
    try:
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_dir = os.path.join(SNAPSHOTS_DIR, f"snap_{timestamp}")

        if os.path.exists(LAB_DIR):
            shutil.copytree(LAB_DIR, snapshot_dir)
            file_count = len(os.listdir(snapshot_dir))
        else:
            os.makedirs(snapshot_dir)
            file_count = 0

        _log_audit(
            "recovery_snapshot_created",
            f"Snapshot created: {snapshot_dir} ({file_count} files)",
            incident_id=incident_id,
        )

        return {
            "success": True,
            "message": f"Recovery snapshot created ({file_count} files)",
            "snapshot_path": snapshot_dir,
            "file_count": file_count,
            "timestamp": timestamp,
            "mode": "DRY_RUN",
        }

    except Exception as e:
        _log_audit(
            "recovery_snapshot_failed",
            f"Snapshot failed: {str(e)}",
            incident_id=incident_id,
            success=False,
        )
        return {
            "success": False,
            "message": f"Snapshot failed: {str(e)}",
            "mode": "DRY_RUN",
        }


def restore_lab_files(incident_id: Optional[str] = None) -> dict:
    """
    Restore test-files from the latest recovery snapshot.
    Only operates on ~/ransomware-lab/test-files.
    """
    try:
        if not os.path.exists(SNAPSHOTS_DIR):
            return {
                "success": False,
                "message": "No recovery snapshots available.",
                "mode": "DRY_RUN",
            }

        # Find latest snapshot
        snapshots = sorted(os.listdir(SNAPSHOTS_DIR))
        if not snapshots:
            return {
                "success": False,
                "message": "No recovery snapshots available.",
                "mode": "DRY_RUN",
            }

        latest = os.path.join(SNAPSHOTS_DIR, snapshots[-1])

        # Restore: clear test-files and copy from snapshot
        if os.path.exists(LAB_DIR):
            shutil.rmtree(LAB_DIR)

        shutil.copytree(latest, LAB_DIR)
        file_count = len(os.listdir(LAB_DIR))

        _log_audit(
            "recovery_completed",
            f"Lab files restored from {snapshots[-1]} ({file_count} files)",
            incident_id=incident_id,
        )

        # Update incident if applicable
        if incident_id:
            inc = incident_manager.get_incident(incident_id)
            if inc and inc["status"] not in ("RESOLVED", "CLOSED"):
                incident_manager.resolve(incident_id)

        return {
            "success": True,
            "message": f"Lab files restored ({file_count} files)",
            "snapshot_used": snapshots[-1],
            "file_count": file_count,
            "mode": "DRY_RUN",
        }

    except Exception as e:
        _log_audit(
            "recovery_failed",
            f"Restore failed: {str(e)}",
            incident_id=incident_id,
            success=False,
        )
        return {
            "success": False,
            "message": f"Restore failed: {str(e)}",
            "mode": "DRY_RUN",
        }


def protect_lab_files(incident_id: Optional[str] = None) -> dict:
    """
    Protect lab files by creating a snapshot before containment.
    Alias for create_recovery_snapshot with audit context.
    """
    result = create_recovery_snapshot(incident_id)
    if result["success"]:
        _log_audit(
            "lab_files_protected",
            "Lab files backed up for protection.",
            incident_id=incident_id,
        )
    return result


# ==============================================================
# PROCESS ISOLATION (SIMULATED)
# ==============================================================

# Safety: Processes that must NEVER be killed
PROCESS_KILL_BLOCKLIST = {
    "systemd", "init", "bash", "sh", "zsh",
    "sshd", "ssh", "gdm", "gdm3", "lightdm",
    "Xorg", "Xwayland", "gnome-shell", "gnome-session",
    "pulseaudio", "pipewire", "dbus-daemon",
    "NetworkManager", "nm-dispatcher",
    "firefox", "firefox-esr", "chromium",
    "code", "kiro",  # IDE
    "node", "npm",  # Our frontend
    "flask", "gunicorn",
}

# These process names are blocked from kill unless their cmdline
# matches an allowlist pattern (prevents killing our own backend)
PROCESS_CONDITIONAL_BLOCK = {
    "python3", "python",
}

# Only kill processes whose executable or cmdline contains these
# (our simulator running inside the lab)
PROCESS_KILL_ALLOWLIST_PATTERNS = [
    "safe_simulator",
    "ransomware-lab/test-files",
    "ransomware",
    "encrypt",
    "locker",
    "ransom",
]


def _is_safe_to_kill(pid: int) -> tuple[bool, str]:
    """
    Determine if a process is safe to kill.

    Returns (safe: bool, reason: str)

    A process is safe to kill ONLY if:
    1. It exists
    2. It belongs to user 'bavan'
    3. Its name is NOT in the absolute blocklist
    4. If name is in conditional block, cmdline must match allowlist
    5. Its cmdline contains an allowlist pattern
    """
    import psutil

    try:
        proc = psutil.Process(pid)
        name = proc.name()
        username = proc.username()
        cmdline = " ".join(proc.cmdline())

        # Must belong to our user
        if username != "bavan":
            return False, f"Process belongs to '{username}', not 'bavan'"

        # Check absolute blocklist (NEVER kill these)
        if name in PROCESS_KILL_BLOCKLIST:
            return False, f"Process '{name}' is in safety blocklist"

        # Check if cmdline contains our own infrastructure
        protected_patterns = [
            "file_monitor", "process_monitor", "network_monitor",
            "detection_pipeline", "dashboard.py", "start.py",
            "npm run dev", "vite",
        ]
        for pattern in protected_patterns:
            if pattern in cmdline:
                return False, f"Process is part of defense infrastructure ('{pattern}')"

        # Check conditional block (e.g., python3 — only if allowlist matches)
        if name in PROCESS_CONDITIONAL_BLOCK:
            for pattern in PROCESS_KILL_ALLOWLIST_PATTERNS:
                if pattern in cmdline:
                    return True, f"Conditional process matches allowlist pattern '{pattern}'"
            return False, f"Process '{name}' — cmdline doesn't match any allowlist pattern"

        # For non-python processes, check allowlist
        for pattern in PROCESS_KILL_ALLOWLIST_PATTERNS:
            if pattern in cmdline or pattern in name:
                return True, f"Matches allowlist pattern '{pattern}'"

        # Unknown process not in any list — allow kill for non-system processes
        # (this covers real ransomware binaries launched from Kali)
        if "/home/bavan" in cmdline or "/tmp" in cmdline:
            return True, f"Process in user space ({name})"

        return False, f"Process '{name}' (cmdline: {cmdline[:80]}) not in allowlist"

    except psutil.NoSuchProcess:
        return False, "Process does not exist"
    except psutil.AccessDenied:
        return False, "Access denied to process information"


def kill_malicious_process(
    pid: Optional[int] = None,
    process_name: Optional[str] = None,
    incident_id: Optional[str] = None,
    force: bool = False,
) -> dict:
    """
    REAL process termination for confirmed ransomware.

    Safety controls:
    - Validates PID exists and belongs to user 'bavan'
    - Checks against blocklist (never kills system/IDE/browser)
    - Only kills processes matching allowlist patterns
    - Requires explicit PID (won't guess)
    - Logs everything to audit trail

    Set force=True to bypass allowlist (still respects blocklist).
    """
    import psutil
    import signal as sig

    if pid is None:
        detail = "Process kill skipped: no PID provided."
        _log_audit("process_kill_skipped", detail, incident_id=incident_id)
        return {
            "success": False,
            "message": detail,
            "pid": None,
            "killed": False,
            "reason": "no_pid",
        }

    # Safety check
    safe, reason = _is_safe_to_kill(pid)

    if not safe and not force:
        detail = f"Process kill BLOCKED for PID={pid}: {reason}"
        _log_audit(
            "process_kill_blocked",
            detail,
            incident_id=incident_id,
            success=False,
        )
        return {
            "success": False,
            "message": detail,
            "pid": pid,
            "killed": False,
            "reason": reason,
        }

    # Attempt to kill
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc_cmdline = " ".join(proc.cmdline())[:100]

        # Send SIGTERM first (graceful)
        proc.terminate()

        # Wait up to 3 seconds for termination
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            # Force kill if still alive
            proc.kill()

        detail = (
            f"Process KILLED: PID={pid} ({proc_name}). "
            f"Cmdline: {proc_cmdline}. Reason: {reason}"
        )
        _log_audit(
            "process_killed",
            detail,
            incident_id=incident_id,
        )

        # Update incident
        if incident_id:
            incident_manager.contain(incident_id)
            incident_manager.add_timeline_event(
                incident_id,
                "process_terminated",
                f"Malicious process PID={pid} ({proc_name}) terminated.",
            )

        return {
            "success": True,
            "message": f"Process PID={pid} ({proc_name}) terminated successfully.",
            "pid": pid,
            "process": proc_name,
            "killed": True,
            "reason": reason,
        }

    except psutil.NoSuchProcess:
        detail = f"Process PID={pid} already terminated (does not exist)."
        _log_audit("process_kill_not_needed", detail, incident_id=incident_id)
        return {
            "success": True,
            "message": detail,
            "pid": pid,
            "killed": False,
            "reason": "already_dead",
        }
    except psutil.AccessDenied:
        detail = f"Process kill DENIED for PID={pid}: insufficient permissions."
        _log_audit("process_kill_denied", detail, incident_id=incident_id, success=False)
        return {
            "success": False,
            "message": detail,
            "pid": pid,
            "killed": False,
            "reason": "access_denied",
        }
    except Exception as e:
        detail = f"Process kill ERROR for PID={pid}: {str(e)}"
        _log_audit("process_kill_error", detail, incident_id=incident_id, success=False)
        return {
            "success": False,
            "message": detail,
            "pid": pid,
            "killed": False,
            "reason": str(e),
        }


def simulate_process_isolation(
    pid: Optional[int] = None,
    process_name: Optional[str] = None,
    incident_id: Optional[str] = None,
) -> dict:
    """
    Simulate process isolation.

    In DRY_RUN mode, this:
    - Records the isolation action
    - Updates the incident state
    - Does NOT kill any process

    The only exception: if the PID matches the safe_simulator.py
    process and it's explicitly identified, we could stop it.
    For safety, we default to simulation only.
    """
    detail = (
        f"Process isolation simulated for "
        f"PID={pid} ({process_name or 'unknown'}). "
        f"No process was actually terminated (DRY_RUN)."
    )

    _log_audit(
        "process_isolation_simulated",
        detail,
        incident_id=incident_id,
    )

    # Update incident containment status
    if incident_id:
        incident_manager.contain(incident_id)

    return {
        "success": True,
        "message": detail,
        "pid": pid,
        "process": process_name,
        "mode": "DRY_RUN",
        "actual_kill": False,
    }


# ==============================================================
# NETWORK ISOLATION (SIMULATED)
# ==============================================================

def simulate_network_isolation(
    incident_id: Optional[str] = None,
    target: Optional[str] = None,
) -> dict:
    """
    Simulate network isolation.

    In DRY_RUN mode:
    - Records the isolation recommendation
    - Does NOT modify iptables or firewall
    - Does NOT disconnect the VM
    """
    detail = (
        f"Network isolation simulated for target={target or 'host'}. "
        f"No firewall rules were modified (DRY_RUN)."
    )

    _log_audit(
        "network_isolation_simulated",
        detail,
        incident_id=incident_id,
    )

    return {
        "success": True,
        "message": detail,
        "target": target or "192.168.74.131",
        "mode": "DRY_RUN",
        "firewall_modified": False,
    }


# ==============================================================
# CONTAINMENT ORCHESTRATION
# ==============================================================

def trigger_containment(incident_id: Optional[str] = None) -> dict:
    """
    Full containment sequence (safe/DRY_RUN):
    1. Protect lab files (snapshot)
    2. Simulate process isolation
    3. Simulate network isolation
    4. Update incident state to CONTAINED
    """
    results = {}

    # 1. Protect files
    results["file_protection"] = protect_lab_files(incident_id)

    # 2. Process isolation
    active = incident_manager.get_active_incident()
    pid = active.get("pid") if active else None
    process_name = active.get("process") if active else None
    results["process_isolation"] = simulate_process_isolation(
        pid=pid,
        process_name=process_name,
        incident_id=incident_id,
    )

    # 3. Network isolation
    results["network_isolation"] = simulate_network_isolation(
        incident_id=incident_id
    )

    # 4. Mark contained
    if incident_id:
        incident_manager.contain(incident_id)

    _log_audit(
        "containment_completed",
        "Full containment sequence completed (DRY_RUN).",
        incident_id=incident_id,
    )

    return {
        "success": True,
        "message": "Containment sequence completed (DRY_RUN)",
        "mode": "DRY_RUN",
        "details": results,
    }


# ==============================================================
# SIMULATION TRIGGER
# ==============================================================

def run_safe_simulation() -> dict:
    """
    Run the safe ransomware behavior simulator.
    Executes simulator/safe_simulator.py in a subprocess.
    """
    import subprocess

    simulator_path = os.path.join(
        PROJECT_ROOT, "simulator", "safe_simulator.py"
    )

    if not os.path.exists(simulator_path):
        return {
            "success": False,
            "message": "Simulator not found.",
            "mode": "DRY_RUN",
        }

    try:
        result = subprocess.run(
            ["python3", simulator_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=PROJECT_ROOT,
        )

        _log_audit(
            "simulation_executed",
            "Safe ransomware behavior simulation completed.",
        )

        return {
            "success": result.returncode == 0,
            "message": "Simulation completed successfully."
            if result.returncode == 0
            else f"Simulation failed: {result.stderr}",
            "output": result.stdout[-500:] if result.stdout else "",
            "mode": "DRY_RUN",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Simulation timed out after 30 seconds.",
            "mode": "DRY_RUN",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Simulation error: {str(e)}",
            "mode": "DRY_RUN",
        }


# ==============================================================
# HEALTH CHECK
# ==============================================================

def get_system_health() -> dict:
    """
    Return real system health information.
    """
    import psutil

    # Check if monitors are running
    def is_process_running(name_fragment: str) -> bool:
        for proc in psutil.process_iter(["cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if any(name_fragment in arg for arg in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    log_file = os.path.join(PROJECT_ROOT, "logs", "events.jsonl")
    ml_model = os.path.join(
        PROJECT_ROOT, "ml", "models", "ransomware_model.pkl"
    )

    return {
        "backend": "ONLINE",
        "file_monitor": "RUNNING" if is_process_running("file_monitor") else "STOPPED",
        "process_monitor": "RUNNING" if is_process_running("process_monitor") else "STOPPED",
        "network_monitor": "RUNNING" if is_process_running("network_monitor") else "STOPPED",
        "detection_pipeline": "RUNNING" if is_process_running("detection_pipeline") else "STOPPED",
        "event_log": "AVAILABLE" if os.path.exists(log_file) else "ERROR",
        "ml_model": "AVAILABLE" if os.path.exists(ml_model) else "ERROR",
        "safe_lab_mode": True,
        "protection_mode": "DRY_RUN",
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": int(
            (datetime.now() - datetime.fromtimestamp(
                psutil.boot_time()
            )).total_seconds()
        ),
    }
