import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "structured"
    / "l1_knowledge_records.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "training"
)

JSONL_FILE = OUTPUT_DIR / "l1_training.jsonl"
CSV_FILE = OUTPUT_DIR / "l1_training.csv"
REPORT_FILE = OUTPUT_DIR / "training_report.txt"


# ============================================================
# HELPERS
# ============================================================

def safe_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_unknown(value):
    value = safe_text(value)

    if not value:
        return "Unknown"

    return value


def build_missing_information(row):
    missing = []

    if normalize_unknown(row.get("detected_system")) == "Unknown":
        missing.append("System or software involved")

    if normalize_unknown(row.get("meter_type")) == "Unknown":
        missing.append("Meter type: Electric or Water")

    if normalize_unknown(row.get("detected_meter_models")) == "Unknown":
        missing.append("Exact meter model")

    if normalize_unknown(row.get("error_code")) == "Unknown":
        missing.append("Exact error code or error message")

    title = normalize_unknown(row.get("title"))

    if title == "Unknown" or len(title) < 15:
        missing.append(
            "Detailed problem description and reproduction steps"
        )

    return missing


# ============================================================
# BUILD TRAINING RECORD
# ============================================================

def build_training_record(row):

    case_id = normalize_unknown(row.get("case_id"))

    title = normalize_unknown(row.get("title"))
    system_info = normalize_unknown(row.get("system_info"))
    tags = normalize_unknown(row.get("tags"))
    history = normalize_unknown(row.get("history"))

    issue_category = normalize_unknown(
        row.get("issue_category")
    )

    issue_source = normalize_unknown(
        row.get("classification_source")
    )

    system = normalize_unknown(
        row.get("detected_system")
    )

    system_source = normalize_unknown(
        row.get("system_source")
    )

    meter_type = normalize_unknown(
        row.get("meter_type")
    )

    meter_type_source = normalize_unknown(
        row.get("meter_type_source")
    )

    meter_model = normalize_unknown(
        row.get("detected_meter_models")
    )

    error_code = normalize_unknown(
        row.get("error_code")
    )

    support_level = normalize_unknown(
        row.get("support_level")
    )

    support_source = normalize_unknown(
        row.get("support_level_source")
    )

    resolution_evidence = normalize_unknown(
        row.get("resolution_evidence")
    )

    resolution_source = normalize_unknown(
        row.get("resolution_source")
    )

    # ========================================================
    # INPUT
    # ========================================================

    input_parts = []

    if title != "Unknown":
        input_parts.append(
            f"Title: {title}"
        )

    if system_info != "Unknown":
        input_parts.append(
            f"System Info: {system_info}"
        )

    if tags != "Unknown":
        input_parts.append(
            f"Tags: {tags}"
        )

    if history != "Unknown":
        input_parts.append(
            f"History: {history}"
        )

    if not input_parts:
        input_parts.append(
            "No usable case description available."
        )

    input_text = "\n".join(input_parts)

    # ========================================================
    # OUTPUT
    # ========================================================

    output = {
        "case_id": case_id,

        "issue_category": issue_category,

        "issue_category_source": issue_source,

        "system": system,

        "system_source": system_source,

        "meter_type": meter_type,

        "meter_type_source": meter_type_source,

        "meter_model": meter_model,

        "error_code": error_code,

        "support_level": support_level,

        "support_level_source": support_source,

        "missing_information":
            build_missing_information(row),
    }

    # ========================================================
    # RESOLUTION
    # ========================================================

    # Only expose resolution information when actual
    # source evidence exists.

    if (
        resolution_evidence != "Unknown"
        and resolution_source != "Unknown"
        and history != "Unknown"
    ):

        output["resolution"] = history

        output["resolution_source"] = (
            resolution_source
        )

    else:

        output["resolution"] = (
            "Not available from verified source data."
        )

        output["resolution_source"] = "none"

    # ========================================================
    # FINAL RECORD
    # ========================================================

    return {

        "instruction": (
            "Analyze this ISKRA L1 support case using only "
            "the provided evidence. Classify the issue and "
            "identify the system, meter information, error "
            "code and missing information. Do not invent "
            "technical facts, root causes or solutions. "
            "If information is unavailable, return Unknown "
            "or request the missing information."
        ),

        "input": input_text,

        "output": output,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "ISKRA L1 TRAINING DATASET BUILDER"
    )

    print("=" * 70)

    print("\nInput:")

    print(INPUT_FILE)

    # ========================================================
    # CHECK INPUT
    # ========================================================

    if not INPUT_FILE.exists():

        print(
            "\nERROR: Input file was not found."
        )

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # LOAD DATASET
    # ========================================================

    print(
        "\nLoading dataset..."
    )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )

    print(
        f"Loaded records: {len(df)}"
    )

    # ========================================================
    # REQUIRED COLUMNS
    # ========================================================

    required_columns = [

        "case_id",

        "title",

        "system_info",

        "tags",

        "history",

        "issue_category",

        "classification_source",

        "detected_system",

        "system_source",

        "meter_type",

        "meter_type_source",

        "detected_meter_models",

        "error_code",

        "support_level",

        "support_level_source",

        "resolution_evidence",

        "resolution_source",
    ]

    missing_columns = [

        column

        for column in required_columns

        if column not in df.columns
    ]

    if missing_columns:

        print(
            "\nERROR: Missing required columns:"
        )

        for column in missing_columns:

            print(
                f" - {column}"
            )

        return

    # ========================================================
    # BUILD RECORDS
    # ========================================================

    training_records = []

    for _, row in df.iterrows():

        record = build_training_record(
            row
        )

        training_records.append(
            record
        )

    print(
        f"Generated training records: "
        f"{len(training_records)}"
    )

    # ========================================================
    # SAVE JSONL
    # ========================================================

    with open(
        JSONL_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for record in training_records:

            file.write(

                json.dumps(
                    record,
                    ensure_ascii=False
                )

                + "\n"
            )

    # ========================================================
    # SAVE CSV
    # ========================================================

    csv_rows = []

    for record in training_records:

        output = record["output"]

        csv_rows.append({

            "case_id":
                output["case_id"],

            "input":
                record["input"],

            "issue_category":
                output["issue_category"],

            "system":
                output["system"],

            "meter_type":
                output["meter_type"],

            "meter_model":
                output["meter_model"],

            "error_code":
                output["error_code"],

            "support_level":
                output["support_level"],

            "missing_information":
                " | ".join(
                    output[
                        "missing_information"
                    ]
                ),

            "resolution":
                output["resolution"],

            "resolution_source":
                output[
                    "resolution_source"
                ],
        })

    training_df = pd.DataFrame(
        csv_rows
    )

    training_df.to_csv(

        CSV_FILE,

        index=False,

        encoding="utf-8-sig"
    )

    # ========================================================
    # STATISTICS
    # ========================================================

    issue_counts = (

        training_df[
            "issue_category"
        ]

        .value_counts()

        .to_dict()
    )

    system_counts = (

        training_df[
            "system"
        ]

        .value_counts()

        .to_dict()
    )

    meter_counts = (

        training_df[
            "meter_type"
        ]

        .value_counts()

        .to_dict()
    )

    resolution_verified = sum(

        1

        for record in training_records

        if (
            record["output"][
                "resolution_source"
            ]
            != "none"
        )
    )

    resolution_not_available = (

        len(training_records)

        - resolution_verified
    )

    # ========================================================
    # REPORT
    # ========================================================

    report_lines = []

    report_lines.append(
        "=" * 70
    )

    report_lines.append(
        "ISKRA L1 TRAINING DATASET REPORT"
    )

    report_lines.append(
        "=" * 70
    )

    report_lines.append("")

    report_lines.append(
        f"Input records: {len(df)}"
    )

    report_lines.append(
        "Training records generated: "
        f"{len(training_records)}"
    )

    # ========================================================
    # ISSUE CATEGORIES
    # ========================================================

    report_lines.append("")

    report_lines.append(
        "ISSUE CATEGORIES"
    )

    report_lines.append(
        "-" * 70
    )

    for key, value in issue_counts.items():

        report_lines.append(
            f"- {key}: {value}"
        )

    # ========================================================
    # SYSTEMS
    # ========================================================

    report_lines.append("")

    report_lines.append(
        "SYSTEMS"
    )

    report_lines.append(
        "-" * 70
    )

    for key, value in system_counts.items():

        report_lines.append(
            f"- {key}: {value}"
        )

    # ========================================================
    # METER TYPES
    # ========================================================

    report_lines.append("")

    report_lines.append(
        "METER TYPES"
    )

    report_lines.append(
        "-" * 70
    )

    for key, value in meter_counts.items():

        report_lines.append(
            f"- {key}: {value}"
        )

    # ========================================================
    # RESOLUTION
    # ========================================================

    report_lines.append("")

    report_lines.append(
        "RESOLUTION EVIDENCE"
    )

    report_lines.append(
        "-" * 70
    )

    report_lines.append(
        "Verified resolution records: "
        f"{resolution_verified}"
    )

    report_lines.append(
        "Resolution not available: "
        f"{resolution_not_available}"
    )

    # ========================================================
    # SAFETY RULES
    # ========================================================

    report_lines.append("")

    report_lines.append(
        "SAFETY RULES"
    )

    report_lines.append(
        "-" * 70
    )

    report_lines.append(
        "- No unsupported root causes are generated."
    )

    report_lines.append(
        "- No unsupported solutions are generated."
    )

    report_lines.append(
        "- Unknown information is preserved."
    )

    report_lines.append(
        "- Missing information is explicitly requested."
    )

    report_lines.append(
        "- Resolution is included only when "
        "source evidence exists."
    )

    # ========================================================
    # FILES
    # ========================================================

    report_lines.append("")

    report_lines.append(
        "FILES"
    )

    report_lines.append(
        "-" * 70
    )

    report_lines.append(
        str(JSONL_FILE)
    )

    report_lines.append(
        str(CSV_FILE)
    )

    report_lines.append(
        str(REPORT_FILE)
    )

    report_lines.append("")

    report_lines.append(
        "=" * 70
    )

    report_lines.append(
        "END OF REPORT"
    )

    report_lines.append(
        "=" * 70
    )

    # ========================================================
    # SAVE REPORT
    # ========================================================

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(
                report_lines
            )
        )

    # ========================================================
    # DONE
    # ========================================================

    print("\n")

    print("=" * 70)

    print(
        "TRAINING DATASET BUILD COMPLETE"
    )

    print("=" * 70)

    print("\nGenerated files:")

    print(
        f" - {JSONL_FILE}"
    )

    print(
        f" - {CSV_FILE}"
    )

    print(
        f" - {REPORT_FILE}"
    )

    print("\nResolution evidence:")

    print(
        f" - Verified: "
        f"{resolution_verified}"
    )

    print(
        f" - Not available: "
        f"{resolution_not_available}"
    )


if __name__ == "__main__":
    main()