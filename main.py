import subprocess
import sys
from pathlib import Path


# ============================================================
# MEMBER 3 - DATABASE & DATA ENGINEERING PIPELINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PIPELINE = [
    ("1. Normalize SCDC data", "normalize_scdc.py"),
    ("2. Load meters", "load_meters.py"),
    ("3. Load failures", "load_failures.py"),
    ("4. Load failure fingerprints", "load_failure_fingerprints.py"),
    ("5. Create meter analytics", "create_meter_analytics.py"),
    ("6. Create failure analytics", "create_failure_analytics.py"),
    ("7. Create dev bugs analytics", "create_dev_bugs_analytics.py"),
]


def run_step(step_number, description, script_name):
    print("\n" + "=" * 65)
    print(f"STEP {step_number}: {description}")
    print("=" * 65)

    script_path = BASE_DIR / script_name

    if not script_path.exists():
        print(f"ERROR: File not found: {script_name}")
        return False

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        print("\n" + "!" * 65)
        print(f"STEP {step_number} FAILED: {script_name}")
        print(f"Exit code: {result.returncode}")
        print("!" * 65)
        return False

    print(f"STEP {step_number} COMPLETED SUCCESSFULLY")
    return True


def main():
    print("=" * 65)

    print("=" * 65)
    print(f"Project directory: {BASE_DIR}")

    for index, (description, script_name) in enumerate(PIPELINE, start=1):
        if not run_step(index, description, script_name):
            print("\nPIPELINE STOPPED.")
            sys.exit(1)

    print("\n" + "=" * 65)
    print("MEMBER 3 PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 65)
    print("All database/data-engineering pipeline steps finished.")


if __name__ == "__main__":
    main()
