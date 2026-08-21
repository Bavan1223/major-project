"""
Auditd-based file/process attribution.

Parses auditd records for the controlled
ransomware-lab/test-files directory.

This module does NOT:
- modify audit rules
- kill processes
- modify files
- perform containment
- change ML features
"""

import os
import re
import subprocess


LAB_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "test-files"
    )
)


def is_inside_lab(path):
    """Check whether path is an actual file inside test-files."""

    if not isinstance(path, str):
        return False

    path = os.path.abspath(path)

    try:
        return (
            os.path.commonpath(
                [path, LAB_ROOT]
            ) == LAB_ROOT
            and path != LAB_ROOT
            and not path.endswith(os.sep)
        )

    except ValueError:
        return False


def resolve_audit_path(name, cwd):
    """Resolve relative audit PATH names using CWD."""

    if not name:
        return None

    name = name.strip().strip('"')

    if os.path.isabs(name):
        return os.path.abspath(name)

    if not cwd:
        return None

    cwd = cwd.strip().strip('"')

    return os.path.abspath(
        os.path.join(cwd, name)
    )


def extract_event_id(line):
    """
    Extract the numeric audit event ID.

    Example:
        msg=audit(08/20/2026 20:51:55.798:689)

    Returns:
        "689"
    """

    match = re.search(
        r"msg=audit\(.*:(\d+)\)",
        line
    )

    if match:
        return match.group(1)

    return None


def extract_field(line, field):
    """Extract a simple key=value field."""

    match = re.search(
        rf"\b{re.escape(field)}=(\"[^\"]*\"|\S+)",
        line
    )

    if not match:
        return None

    return match.group(1).strip('"')


def run_audit_search(key="ransomware_lab"):
    """Retrieve interpreted audit records."""

    result = subprocess.run(
        [
            "sudo",
            "ausearch",
            "-k",
            key,
            "-i"
        ],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode not in (0, 1):

        raise RuntimeError(
            result.stderr.strip()
            or "ausearch failed"
        )

    return result.stdout


def parse_audit_records(raw_output):
    """
    Parse audit records grouped by event ID.

    Only successful file activity inside the controlled
    test-files directory is returned.
    """

    groups = {}

    current_event_id = None

    for raw_line in raw_output.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        event_id = extract_event_id(line)

        if event_id is not None:

            current_event_id = event_id

            if event_id not in groups:

                groups[event_id] = {
                    "event_id": event_id,
                    "cwd": None,
                    "pid": None,
                    "process": None,
                    "executable": None,
                    "syscall": None,
                    "success": None,
                    "write_activity": False,
                    "rename_activity": False,
                    "ignore": False,
                    "paths": []
                }

        if current_event_id is None:
            continue

        group = groups[current_event_id]

        # -----------------------------------------
        # CONFIGURATION EVENTS
        # -----------------------------------------

        if line.startswith(
            "type=CONFIG_CHANGE"
        ):

            group["ignore"] = True
            continue

        # -----------------------------------------
        # SYSCALL
        # -----------------------------------------

        if line.startswith("type=SYSCALL"):

            pid = extract_field(
                line,
                "pid"
            )

            if pid is not None:

                try:
                    group["pid"] = int(pid)

                except ValueError:
                    group["pid"] = None

            group["process"] = extract_field(
                line,
                "comm"
            )

            group["executable"] = extract_field(
                line,
                "exe"
            )

            group["syscall"] = extract_field(
                line,
                "syscall"
            )

            group["success"] = extract_field(
                line,
                "success"
            )

            # Never attribute audit administration.
            if group["process"] == "auditctl":
                group["ignore"] = True

            # Detect write/create activity.
            if any(
                flag in line
                for flag in (
                    "O_WRONLY",
                    "O_RDWR",
                    "O_CREAT",
                    "O_TRUNC"
                )
            ):
                group["write_activity"] = True

            if group["syscall"] in {
                "write",
                "pwrite",
                "pwrite64",
                "writev",
                "pwritev"
            }:
                group["write_activity"] = True

            if group["syscall"] in {
                "rename",
                "renameat",
                "renameat2"
            }:
                group["rename_activity"] = True

        # -----------------------------------------
        # CWD
        # -----------------------------------------

        elif line.startswith("type=CWD"):

            group["cwd"] = extract_field(
                line,
                "cwd"
            )

        # -----------------------------------------
        # PATH
        # -----------------------------------------

        elif line.startswith("type=PATH"):

            name = extract_field(
                line,
                "name"
            )

            nametype = extract_field(
                line,
                "nametype"
            )

            # PARENT is a directory context,
            # not the modified file.
            if nametype == "PARENT":
                continue

            if not name:
                continue

            group["paths"].append(
                {
                    "name": name,
                    "nametype": nametype
                }
            )

    # -----------------------------------------
    # BUILD ATTRIBUTION RESULTS
    # -----------------------------------------

    records = []

    for group in groups.values():

        if group["ignore"]:
            continue

        if group["pid"] is None:
            continue

        if group["success"] not in (
            None,
            "yes"
        ):
            continue

        for path_info in group["paths"]:

            name = path_info["name"]
            nametype = path_info["nametype"]

            path = resolve_audit_path(
                name,
                group["cwd"]
            )

            if not path:
                continue

            if not is_inside_lab(path):
                continue

            # Directory must never become a file event.
            if os.path.isdir(path):
                continue

            # Operation classification.
            if nametype == "CREATE":

                operation = "CREATE"

            elif nametype == "DELETE":

                operation = "DELETE"

            elif group["rename_activity"]:

                operation = "RENAME"

            elif group["write_activity"]:

                operation = "MODIFY"

            else:

                operation = "ACCESS"

            records.append(
                {
                    "event_id": group["event_id"],
                    "path": path,
                    "pid": group["pid"],
                    "process": group["process"],
                    "executable": group["executable"],
                    "syscall": group["syscall"],
                    "success": group["success"],
                    "operation": operation
                }
            )

    return records


def get_file_process_attribution(
    key="ransomware_lab"
):
    """Retrieve current lab attribution data."""

    raw_output = run_audit_search(key)

    return parse_audit_records(
        raw_output
    )


if __name__ == "__main__":

    print(
        "=== Auditd File → Process Attribution ==="
    )

    records = get_file_process_attribution()

    if not records:

        print(
            "No valid lab file/process attribution records found."
        )

    else:

        for record in records:

            print()
            print(
                "[ATTRIBUTED FILE ACTIVITY]"
            )

            print(
                "Path       :",
                record["path"]
            )

            print(
                "PID        :",
                record["pid"]
            )

            print(
                "Process    :",
                record["process"]
            )

            print(
                "Executable :",
                record["executable"]
            )

            print(
                "Syscall    :",
                record["syscall"]
            )

            print(
                "Operation  :",
                record["operation"]
            )

            print(
                "Event ID   :",
                record["event_id"]
            )

            print("-" * 50)
