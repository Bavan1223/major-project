import os
import time

LAB_DIR = "/home/bavan/ransomware-lab/test-files"
FILE_COUNT = 30


def prepare_files():
    print("[1] Creating test files...")

    for i in range(1, FILE_COUNT + 1):
        path = os.path.join(LAB_DIR, f"victim_{i}.txt")

        with open(path, "w") as file:
            file.write(f"Original test data {i}\n")


def simulate_mass_modification():
    print("[2] Simulating rapid file modification...")

    for i in range(1, FILE_COUNT + 1):
        path = os.path.join(LAB_DIR, f"victim_{i}.txt")

        with open(path, "a") as file:
            file.write("SIMULATED RANSOMWARE ACTIVITY\n")

        print(f"Modified: victim_{i}.txt")

        time.sleep(0.1)


def main():
    print("=== SAFE RANSOMWARE BEHAVIOR SIMULATOR ===")
    print("Lab directory:", LAB_DIR)
    print("PID:", os.getpid())
    print()

    prepare_files()

    time.sleep(1)

    simulate_mass_modification()

    print()
    print("[3] Simulation complete.")
    print("No encryption or destructive activity was performed.")


if __name__ == "__main__":
    main()
