import json
from pathlib import Path
from collections import Counter


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "training"
    / "l1_training.jsonl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "evaluation"
    / "training_dataset_validation.txt"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ISKRA L1 TRAINING DATASET VALIDATION")
    print("=" * 70)

    print("\nInput:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():

        print("\nERROR: Training dataset not found.")
        return

    records = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):

            line = line.strip()

            if not line:
                continue

            try:

                record = json.loads(line)

                records.append(record)

            except json.JSONDecodeError as error:

                print(
                    f"\nERROR: Invalid JSON on line "
                    f"{line_number}"
                )

                print(error)

                return

    total = len(records)

    print(
        f"\nLoaded records: {total}"
    )

    # ========================================================
    # VALIDATION COUNTERS
    # ========================================================

    missing_instruction = []
    missing_input = []
    missing_output = []

    duplicate_case_ids = []

    case_ids = []

    invalid_outputs = []

    unsupported_resolution = []

    unknown_issue = 0
    unknown_system = 0
    unknown_meter = 0

    resolution_records = 0

    multi_label_issues = 0
    multi_system_cases = 0
    multi_meter_cases = 0

    issue_counter = Counter()
    system_counter = Counter()
    meter_counter = Counter()

    # ========================================================
    # VALIDATE RECORDS
    # ========================================================

    for index, record in enumerate(
        records,
        start=1
    ):

        # ----------------------------------------------------
        # Required top-level fields
        # ----------------------------------------------------

        if not record.get("instruction"):
            missing_instruction.append(index)

        if not record.get("input"):
            missing_input.append(index)

        if not record.get("output"):
            missing_output.append(index)
            continue

        output = record["output"]

        if not isinstance(
            output,
            dict
        ):

            invalid_outputs.append(index)
            continue

        # ----------------------------------------------------
        # Case ID
        # ----------------------------------------------------

        case_id = output.get(
            "case_id",
            "Unknown"
        )

        if case_id != "Unknown":

            if case_id in case_ids:

                duplicate_case_ids.append(
                    case_id
                )

            case_ids.append(
                case_id
            )

        # ----------------------------------------------------
        # Issue
        # ----------------------------------------------------

        issue = output.get(
            "issue_category",
            "Unknown"
        )

        if not issue:
            issue = "Unknown"

        issue_counter[issue] += 1

        if issue == "Unknown":
            unknown_issue += 1

        if "|" in issue:
            multi_label_issues += 1

        # ----------------------------------------------------
        # System
        # ----------------------------------------------------

        system = output.get(
            "system",
            "Unknown"
        )

        if not system:
            system = "Unknown"

        system_counter[system] += 1

        if system == "Unknown":
            unknown_system += 1

        if "|" in system:
            multi_system_cases += 1

        # ----------------------------------------------------
        # Meter
        # ----------------------------------------------------

        meter = output.get(
            "meter_type",
            "Unknown"
        )

        if not meter:
            meter = "Unknown"

        meter_counter[meter] += 1

        if meter == "Unknown":
            unknown_meter += 1

        if "|" in meter:
            multi_meter_cases += 1

        # ----------------------------------------------------
        # Resolution
        # ----------------------------------------------------

        resolution = output.get(
            "resolution",
            ""
        )

        resolution_source = output.get(
            "resolution_source",
            "none"
        )

        if (
            resolution_source != "none"
            and resolution
            and resolution
            != "Not available from verified source data."
        ):

            resolution_records += 1

        else:

            if resolution != (
                "Not available from verified source data."
            ):

                unsupported_resolution.append(
                    case_id
                )

    # ========================================================
    # REPORT
    # ========================================================

    report = []

    report.append("=" * 70)
    report.append(
        "ISKRA L1 TRAINING DATASET VALIDATION REPORT"
    )
    report.append("=" * 70)

    report.append("")
    report.append(
        f"Total records: {total}"
    )

    # ========================================================
    # STRUCTURE
    # ========================================================

    report.append("")
    report.append(
        "STRUCTURE VALIDATION"
    )
    report.append("-" * 70)

    report.append(
        f"Missing instruction: "
        f"{len(missing_instruction)}"
    )

    report.append(
        f"Missing input: "
        f"{len(missing_input)}"
    )

    report.append(
        f"Missing output: "
        f"{len(missing_output)}"
    )

    report.append(
        f"Invalid output objects: "
        f"{len(invalid_outputs)}"
    )

    report.append(
        f"Duplicate case IDs: "
        f"{len(duplicate_case_ids)}"
    )

    # ========================================================
    # ISSUE
    # ========================================================

    report.append("")
    report.append(
        "ISSUE CLASSIFICATION"
    )
    report.append("-" * 70)

    for key, value in issue_counter.items():

        report.append(
            f"- {key}: {value}"
        )

    report.append(
        f"\nUnknown issues: {unknown_issue}"
    )

    report.append(
        f"Multi-label issue cases: "
        f"{multi_label_issues}"
    )

    # ========================================================
    # SYSTEM
    # ========================================================

    report.append("")
    report.append(
        "SYSTEM CLASSIFICATION"
    )
    report.append("-" * 70)

    for key, value in system_counter.items():

        report.append(
            f"- {key}: {value}"
        )

    report.append(
        f"\nUnknown systems: {unknown_system}"
    )

    report.append(
        f"Multi-system cases: "
        f"{multi_system_cases}"
    )

    # ========================================================
    # METER
    # ========================================================

    report.append("")
    report.append(
        "METER TYPE"
    )
    report.append("-" * 70)

    for key, value in meter_counter.items():

        report.append(
            f"- {key}: {value}"
        )

    report.append(
        f"\nUnknown meter type: {unknown_meter}"
    )

    report.append(
        f"Multi-meter cases: "
        f"{multi_meter_cases}"
    )

    # ========================================================
    # RESOLUTION
    # ========================================================

    report.append("")
    report.append(
        "RESOLUTION SAFETY"
    )
    report.append("-" * 70)

    report.append(
        f"Verified resolution records: "
        f"{resolution_records}"
    )

    report.append(
        f"Unexpected/unsupported resolution records: "
        f"{len(unsupported_resolution)}"
    )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    has_errors = (
        len(missing_instruction)
        + len(missing_input)
        + len(missing_output)
        + len(invalid_outputs)
        + len(duplicate_case_ids)
        + len(unsupported_resolution)
    )

    report.append("")
    report.append("=" * 70)

    if has_errors == 0:

        report.append(
            "VALIDATION STATUS: PASSED"
        )

    else:

        report.append(
            "VALIDATION STATUS: REVIEW REQUIRED"
        )

    report.append("=" * 70)

    report.append("")
    report.append(
        "IMPORTANT:"
    )

    report.append(
        "This validation checks dataset structure and "
        "safety constraints."
    )

    report.append(
        "It does NOT prove that the classifications are "
        "ground-truth correct."
    )

    report.append(
        "Manual review is still required before fine-tuning."
    )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(report)
        )

    # ========================================================
    # PRINT
    # ========================================================

    print("")

    for line in report:

        print(line)

    print("")
    print(
        f"Report saved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()