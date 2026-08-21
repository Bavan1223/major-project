"""
Lab-Safe Protection Controller

Current mode:
SAFE / DRY-RUN

Responsibilities:
- Receive a response decision
- Determine whether protection should be recommended
- Validate lab-only containment targets
- Simulate containment
- Log protection decisions as Common Events

This module does NOT:
- kill processes
- block real network traffic
- delete files
- modify system firewall rules
- perform recovery
"""

import os
import sys


# ------------------------------------------------------
# PROJECT PATH
# ------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from event_logger import log_event


# ------------------------------------------------------
# LAB CONFIGURATION
# ------------------------------------------------------

LAB_ROOT = os.path.abspath(
    os.path.join(
        PROJECT_ROOT,
        "test-files"
    )
)

QUARANTINE_DIR = os.path.join(
    PROJECT_ROOT,
    "quarantine"
)

DRY_RUN = True


# ------------------------------------------------------
# SAFETY CHECK
# ------------------------------------------------------

def is_inside_lab(path):
    """
    Confirm that a path is inside the controlled
    ransomware-lab/test-files directory.
    """

    if not isinstance(path, str):
        return False

    absolute_path = os.path.abspath(path)

    try:
        return os.path.commonpath(
            [absolute_path, LAB_ROOT]
        ) == LAB_ROOT

    except ValueError:
        return False


# ------------------------------------------------------
# PROTECTION DECISION
# ------------------------------------------------------

def determine_protection(response_result):
    """
    Convert a response recommendation into a
    protection decision.

    No actual containment is performed here.
    """

    if not isinstance(response_result, dict):
        raise ValueError(
            "response_result must be a dictionary"
        )

    risk_level = response_result.get(
        "risk_level"
    )

    recommended_action = response_result.get(
        "recommended_action"
    )

    if risk_level is None:
        raise ValueError(
            "risk_level is required"
        )

    if recommended_action is None:
        raise ValueError(
            "recommended_action is required"
        )

    if risk_level in {"NORMAL", "LOW"}:

        action = "NO_PROTECTION"

    elif risk_level == "MEDIUM":

        action = "MONITOR_ONLY"

    elif risk_level == "HIGH":

        action = "LAB_CONTAINMENT_RECOMMENDED"

    elif risk_level == "CRITICAL":

        action = "CRITICAL_PROTECTION_RESERVED"

    else:

        raise ValueError(
            f"Unsupported risk level: {risk_level}"
        )

    return {
        "risk_level": risk_level,
        "response_action": recommended_action,
        "protection_action": action,
        "mode": "DRY_RUN"
        if DRY_RUN
        else "LAB_SAFE"
    }


# ------------------------------------------------------
# SAFE CONTAINMENT SIMULATION
# ------------------------------------------------------

def simulate_containment(target_path=None):
    """
    Simulate containment of a lab file.

    In DRY_RUN mode, no file is moved or modified.
    """

    if target_path is not None:

        if not is_inside_lab(target_path):

            raise ValueError(
                "Containment target must be inside "
                "the ransomware-lab test-files directory."
            )

    if target_path is None:

        target_description = (
            "No specific target supplied"
        )

    else:

        target_description = os.path.abspath(
            target_path
        )

    if DRY_RUN:

        return {
            "status": "SIMULATED",
            "target": target_description,
            "quarantine_directory": (
                QUARANTINE_DIR
            ),
            "mode": "DRY_RUN"
        }

    # Actual lab-safe containment is intentionally
    # not enabled in this milestone.

    return {
        "status": "NOT_EXECUTED",
        "target": target_description,
        "quarantine_directory": (
            QUARANTINE_DIR
        ),
        "mode": "LAB_SAFE"
    }


# ------------------------------------------------------
# LOG PROTECTION EVENT
# ------------------------------------------------------

def log_protection_decision(
    protection_result,
    containment_result
):
    """
    Log the protection decision as a Common Event.
    """

    return log_event(
        source="detection_engine",
        event_type="protection_action",
        indicator="protection_policy_decision",
        data={
            "risk_level": protection_result[
                "risk_level"
            ],
            "response_action": protection_result[
                "response_action"
            ],
            "protection_action": protection_result[
                "protection_action"
            ],
            "containment": containment_result,
            "mode": protection_result[
                "mode"
            ]
        }
    )


# ------------------------------------------------------
# COMPLETE PROTECTION PIPELINE
# ------------------------------------------------------

def process_response(response_result, target_path=None):
    """
    Process a response recommendation through
    the protection controller.

    Pipeline:

        Response Decision
              ↓
        Protection Decision
              ↓
        Safe Containment Simulation
              ↓
        Common Event
    """

    protection_result = determine_protection(
        response_result
    )

    if protection_result[
        "protection_action"
    ] == "LAB_CONTAINMENT_RECOMMENDED":

        containment_result = simulate_containment(
            target_path
        )

    else:

        containment_result = {
            "status": "NOT_REQUIRED",
            "target": None,
            "mode": protection_result[
                "mode"
            ]
        }

    event = log_protection_decision(
        protection_result,
        containment_result
    )

    return (
        protection_result,
        containment_result,
        event
    )


# ------------------------------------------------------
# STANDALONE TEST
# ------------------------------------------------------

if __name__ == "__main__":

    print("=== Protection Controller ===")
    print("Mode:", "DRY_RUN")
    print()

    test_cases = {

        "NORMAL": {
            "risk_level": "NORMAL",
            "recommended_action": "NO_ACTION"
        },

        "LOW": {
            "risk_level": "LOW",
            "recommended_action": "MONITOR"
        },

        "MEDIUM": {
            "risk_level": "MEDIUM",
            "recommended_action": "INCREASE_MONITORING"
        },

        "HIGH": {
            "risk_level": "HIGH",
            "recommended_action": "CONTAINMENT_RECOMMENDED"
        },

        "CRITICAL": {
            "risk_level": "CRITICAL",
            "recommended_action": (
                "CRITICAL_RESPONSE_RESERVED"
            )
        }
    }

    for expected, response in test_cases.items():

        result = determine_protection(
            response
        )

        print(
            "Risk Level       :",
            result["risk_level"]
        )

        print(
            "Response Action  :",
            result["response_action"]
        )

        print(
            "Protection Action:",
            result["protection_action"]
        )

        print(
            "Mode             :",
            result["mode"]
        )

        print("-" * 60)

    print()
    print("Protection controller test complete.")
