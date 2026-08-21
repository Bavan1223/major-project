"""
Central Response Controller

Current mode:
DRY-RUN

Responsibilities:
- Receive a risk decision
- Determine the recommended response
- Log the response recommendation as a Common Event

This module does NOT:
- kill processes
- block network connections
- delete files
- quarantine files
- modify system configuration
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
# RESPONSE POLICY
# ------------------------------------------------------

RESPONSE_POLICY = {
    "NORMAL": "NO_ACTION",
    "LOW": "MONITOR",
    "MEDIUM": "INCREASE_MONITORING",
    "HIGH": "CONTAINMENT_RECOMMENDED",
    "CRITICAL": "CRITICAL_RESPONSE_RESERVED"
}


# ------------------------------------------------------
# RESPONSE DECISION
# ------------------------------------------------------

def determine_response(risk_result):
    """
    Determine the recommended response from a risk result.

    This function only recommends an action.
    It does not perform the action.

    Returns:
        {
            "risk_level": str,
            "recommended_action": str,
            "reason": str,
            "signals": list,
            "mode": "DRY_RUN"
        }
    """

    if not isinstance(risk_result, dict):
        raise ValueError(
            "risk_result must be a dictionary"
        )

    risk_level = risk_result.get(
        "risk_level",
        "NORMAL"
    )

    if risk_level not in RESPONSE_POLICY:
        raise ValueError(
            f"Unsupported risk level: {risk_level}"
        )

    recommended_action = RESPONSE_POLICY[
        risk_level
    ]

    return {
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "reason": risk_result.get(
            "reason",
            "No reason provided."
        ),
        "signals": risk_result.get(
            "signals",
            []
        ),
        "mode": "DRY_RUN"
    }


# ------------------------------------------------------
# LOG RESPONSE DECISION
# ------------------------------------------------------

def log_response_decision(response_result):
    """
    Publish the response recommendation as a Common Event.

    The response controller decides what should be
    recommended.

    The event logger validates, collects and persists
    the Common Event.
    """

    return log_event(
        source="detection_engine",
        event_type="response_recommendation",
        indicator="response_policy_decision",
        data={
            "risk_level": response_result[
                "risk_level"
            ],
            "recommended_action": response_result[
                "recommended_action"
            ],
            "reason": response_result[
                "reason"
            ],
            "signals": response_result[
                "signals"
            ],
            "mode": response_result[
                "mode"
            ]
        }
    )


# ------------------------------------------------------
# RESPONSE PIPELINE
# ------------------------------------------------------

def process_risk_result(risk_result):
    """
    Process a risk result through the response controller.

    Steps:

        Risk Result
             ↓
        Response Decision
             ↓
        Common Event
             ↓
        Event Logger
    """

    response_result = determine_response(
        risk_result
    )

    event = log_response_decision(
        response_result
    )

    return response_result, event


# ------------------------------------------------------
# STANDALONE TEST
# ------------------------------------------------------

if __name__ == "__main__":

    print("=== Response Controller ===")
    print("Mode: DRY-RUN")
    print()

    test_cases = {

        "NORMAL": {
            "risk_level": "NORMAL",
            "reason": "No suspicious behavior detected.",
            "signals": []
        },

        "LOW": {
            "risk_level": "LOW",
            "reason": "Minor file activity detected.",
            "signals": []
        },

        "MEDIUM": {
            "risk_level": "MEDIUM",
            "reason": "Elevated file activity detected.",
            "signals": [
                "multiple_unique_files_modified"
            ]
        },

        "HIGH": {
            "risk_level": "HIGH",
            "reason": (
                "Rapid mass modification of "
                "multiple unique files detected."
            ),
            "signals": [
                "rapid_mass_file_modification",
                "multiple_unique_files_modified"
            ]
        },

        "CRITICAL": {
            "risk_level": "CRITICAL",
            "reason": (
                "Multiple independent high-confidence "
                "signals detected."
            ),
            "signals": [
                "multi_signal_detection"
            ]
        }
    }

    for expected, risk_result in test_cases.items():

        response = determine_response(
            risk_result
        )

        print("Risk Level :", response["risk_level"])
        print(
            "Recommended:",
            response["recommended_action"]
        )
        print("Mode       :", response["mode"])
        print("Reason     :", response["reason"])
        print("Signals    :", response["signals"])
        print("-" * 60)
