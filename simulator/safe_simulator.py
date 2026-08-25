#!/usr/bin/env python3
"""
Safe Ransomware Behavior Simulator — Enhanced v2.0

Simulates realistic ransomware behavioral patterns for detection testing.
ALL operations are confined to ~/ransomware-lab/test-files/ ONLY.

Behavioral stages (mimics real ransomware kill chain):
    Phase 1: Reconnaissance — create target files
    Phase 2: Encryption simulation — modify + rename extensions
    Phase 3: Destruction — delete originals, drop ransom notes
    Phase 4: Rapid burst — mass modification wave

Safety:
    - ONLY operates on ~/ransomware-lab/test-files/
    - NO real encryption (just overwrites with random-looking data)
    - NO network communication
    - NO privilege escalation
    - NO persistence mechanisms
    - Completely reversible (recovery system restores everything)
"""

import os
import time
import random
import string
import hashlib

# ==============================================================
# SAFETY: HARDCODED PATH — NEVER CHANGES
# ==============================================================
LAB_DIR = "/home/bavan/ransomware-lab/test-files"
FILE_COUNT = 50

# Ransomware extension to simulate
ENCRYPTED_EXT = ".locked"
RANSOM_NOTE_NAME = "README_RESTORE_FILES.txt"


def _safety_check():
    """Verify we're operating in the correct directory."""
    if not LAB_DIR.startswith("/home/bavan/ransomware-lab/test-files"):
        print("SAFETY ERROR: Invalid lab directory!")
        exit(1)
    os.makedirs(LAB_DIR, exist_ok=True)


def _generate_fake_encrypted_content(original_content: str) -> str:
    """
    Generate content that LOOKS like encrypted data.
    This is NOT real encryption — just random bytes representation.
    A real ransomware would use AES/RSA here.
    """
    # Create a hash-based "encrypted" look
    seed = hashlib.sha256(original_content.encode()).hexdigest()
    fake_cipher = ''.join(
        random.choices(string.ascii_letters + string.digits + '+/=', k=256)
    )
    return (
        f"-----BEGIN LOCKED DATA-----\n"
        f"Algorithm: SIMULATED (not real encryption)\n"
        f"Key-Hash: {seed[:32]}\n"
        f"IV: {''.join(random.choices('0123456789abcdef', k=32))}\n"
        f"\n"
        f"{fake_cipher[:64]}\n"
        f"{fake_cipher[64:128]}\n"
        f"{fake_cipher[128:192]}\n"
        f"{fake_cipher[192:256]}\n"
        f"-----END LOCKED DATA-----\n"
    )


def _generate_ransom_note() -> str:
    """Generate a simulated ransom note (for behavioral detection only)."""
    return (
        "=" * 60 + "\n"
        "        YOUR FILES HAVE BEEN LOCKED (SIMULATION)\n"
        "=" * 60 + "\n"
        "\n"
        "This is a SAFE LAB SIMULATION.\n"
        "No real encryption was performed.\n"
        "No payment is required.\n"
        "\n"
        "This file was created by the ransomware behavior simulator\n"
        "to test the detection and prevention system.\n"
        "\n"
        "Recovery: Use the SOC dashboard Recovery function\n"
        "          or run: python3 start.py\n"
        "\n"
        f"Simulation PID: {os.getpid()}\n"
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "\n"
        "=" * 60 + "\n"
    )


# ==============================================================
# PHASE 1: RECONNAISSANCE — Create target files
# ==============================================================

def phase_1_create_targets():
    """Create victim files with realistic content."""
    print("[PHASE 1] Creating target files...")

    file_types = [
        ("document_{}.txt", "Important business document content. Confidential data here."),
        ("spreadsheet_{}.csv", "Name,Account,Balance\nJohn,ACC001,50000\nJane,ACC002,75000"),
        ("report_{}.txt", "Quarterly financial report. Revenue: $2.4M. Expenses: $1.8M."),
        ("backup_{}.dat", "Database backup record. Tables: users, transactions, configs."),
        ("notes_{}.txt", "Meeting notes: Project deadline Q4. Budget approved."),
    ]

    created = 0
    for i in range(1, FILE_COUNT + 1):
        template, content = file_types[i % len(file_types)]
        filename = template.format(i)
        filepath = os.path.join(LAB_DIR, filename)

        with open(filepath, "w") as f:
            f.write(f"{content}\nFile #{i} — Created at {time.strftime('%H:%M:%S')}\n")
        created += 1

    print(f"  Created {created} target files")
    return created


# ==============================================================
# PHASE 2: ENCRYPTION SIMULATION — Modify + Rename
# ==============================================================

def phase_2_encrypt_simulation():
    """
    Simulate file encryption:
    - Read original content
    - Overwrite with fake encrypted data
    - Rename with .locked extension
    """
    print("[PHASE 2] Simulating file encryption (content modification + rename)...")

    encrypted = 0
    files = [f for f in os.listdir(LAB_DIR) if not f.startswith("README") and not f.endswith(ENCRYPTED_EXT)]

    for filename in sorted(files)[:FILE_COUNT]:
        filepath = os.path.join(LAB_DIR, filename)

        if not os.path.isfile(filepath):
            continue

        try:
            # Read original
            with open(filepath, "r") as f:
                original = f.read()

            # Overwrite with "encrypted" content
            fake_encrypted = _generate_fake_encrypted_content(original)
            with open(filepath, "w") as f:
                f.write(fake_encrypted)

            # Rename with encrypted extension
            new_path = filepath + ENCRYPTED_EXT
            os.rename(filepath, new_path)

            encrypted += 1
            print(f"  Encrypted: {filename} → {filename}{ENCRYPTED_EXT}")

            # Small delay to create realistic timing pattern
            time.sleep(0.05)

        except (OSError, IOError) as e:
            print(f"  Skip: {filename} ({e})")

    print(f"  Total encrypted: {encrypted} files")
    return encrypted


# ==============================================================
# PHASE 3: DESTRUCTION — Delete some originals, drop ransom note
# ==============================================================

def phase_3_destruction():
    """
    Simulate post-encryption behavior:
    - Delete some backup/shadow-like files
    - Drop ransom note in the directory
    """
    print("[PHASE 3] Post-encryption behavior (deletion + ransom note)...")

    # Delete some files (simulating backup deletion)
    deleted = 0
    files = [f for f in os.listdir(LAB_DIR) if f.startswith("backup_") and f.endswith(ENCRYPTED_EXT)]
    for filename in files[:5]:
        filepath = os.path.join(LAB_DIR, filename)
        try:
            os.remove(filepath)
            deleted += 1
            print(f"  Deleted: {filename}")
        except OSError:
            pass

    # Drop ransom note
    note_path = os.path.join(LAB_DIR, RANSOM_NOTE_NAME)
    with open(note_path, "w") as f:
        f.write(_generate_ransom_note())
    print(f"  Dropped: {RANSOM_NOTE_NAME}")

    return deleted


# ==============================================================
# PHASE 4: RAPID BURST — Mass modification wave
# ==============================================================

def phase_4_rapid_burst():
    """
    Final rapid burst of activity:
    - Create additional encrypted-looking files very quickly
    - Mimics ransomware finishing encryption of remaining files
    """
    print("[PHASE 4] Rapid burst modification wave...")

    burst_count = 40
    modified = 0

    for i in range(burst_count):
        filepath = os.path.join(LAB_DIR, f"burst_victim_{i}{ENCRYPTED_EXT}")
        content = _generate_fake_encrypted_content(f"burst_data_{i}_{time.time()}")

        with open(filepath, "w") as f:
            f.write(content)
        modified += 1

        # Very fast — no sleep (simulates final burst)

    # Also modify existing encrypted files (double encryption pattern)
    existing = [f for f in os.listdir(LAB_DIR) if f.endswith(ENCRYPTED_EXT)][:10]
    for filename in existing:
        filepath = os.path.join(LAB_DIR, filename)
        try:
            with open(filepath, "a") as f:
                f.write(f"\n[RE-ENCRYPTED {time.strftime('%H:%M:%S')}]\n")
            modified += 1
        except OSError:
            pass

    print(f"  Burst modifications: {modified}")
    return modified


# ==============================================================
# MAIN
# ==============================================================

def main():
    _safety_check()

    print()
    print("=" * 60)
    print("  SAFE RANSOMWARE BEHAVIOR SIMULATOR v2.0")
    print("=" * 60)
    print()
    print(f"  Target:  {LAB_DIR}")
    print(f"  PID:     {os.getpid()}")
    print(f"  Files:   {FILE_COUNT}")
    print(f"  Mode:    SAFE LAB (no real encryption)")
    print()
    print("-" * 60)
    print()

    # Phase 1: Create targets
    created = phase_1_create_targets()
    time.sleep(0.5)

    # Phase 2: Encrypt (modify + rename)
    encrypted = phase_2_encrypt_simulation()
    time.sleep(0.3)

    # Phase 3: Destruction + ransom note
    deleted = phase_3_destruction()
    time.sleep(0.2)

    # Phase 4: Rapid burst
    burst = phase_4_rapid_burst()

    # Summary
    print()
    print("-" * 60)
    print()
    print("  SIMULATION COMPLETE")
    print()
    print(f"  Files created:    {created}")
    print(f"  Files encrypted:  {encrypted} (content modified + extension renamed)")
    print(f"  Files deleted:    {deleted}")
    print(f"  Burst activity:   {burst}")
    print(f"  Ransom note:      {RANSOM_NOTE_NAME}")
    print()
    print("  Total behavioral events generated: ~{} operations".format(
        created + encrypted * 2 + deleted + burst
    ))
    print()
    print("  SAFETY: No real encryption. No system files affected.")
    print("  SAFETY: All activity confined to test-files/ directory.")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
