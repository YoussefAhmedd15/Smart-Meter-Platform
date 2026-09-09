import csv
import json
import random
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "structured" / "l1_knowledge_records.csv"
OUTPUT_FILE = BASE_DIR / "data" / "evaluation" / "l1_evaluation.jsonl"
CSV_OUTPUT_FILE = BASE_DIR / "data" / "evaluation" / "l1_evaluation.csv"
REPORT_FILE = BASE_DIR / "data" / "evaluation" / "evaluation_dataset_report.txt"

RANDOM_SEED = 42
EVALUATION_SIZE = 200


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def is_unknown(value):
    value = clean(value).lower()
    return value in {
        "",
        "unknown",
        "not available",
        "not available from verified source data.",
        "none",
        "n/a",
    }


def build_expected_output(row):
    issue = clean(row.get("issue_category"))
    system = clean(row.get("detected_system"))
    meter_type = clean(row.get("meter_type"))
    meter_model = clean(row.get("detected_meter_models"))
    error_code = clean(row.get("error_code"))
    support_level = clean(row.get("support_level"))

    history = clean(row.get("history"))
    resolution_source = clean(row.get("resolution_source"))

    missing = []

    if is_unknown(issue):
        missing.append("issue category")

    if is_unknown(system):
        missing.append("software/system")

    if is_unknown(meter_type):
        missing.append("meter type")

    if is_unknown(meter_model):
        missing.append("meter model")

    if is_unknown(error_code):
        missing.append("error code")

    if is_unknown(support_level):
        missing.append("support level")

    resolution = "Not available from verified source data."

    if (
        not is_unknown(history)
        and not is_unknown(resolution_source)
        and resolution_source.lower() != "unknown"
    ):
        resolution = history

    return {
        "issue_category": issue if issue else "Unknown",
        "system": system if system else "Unknown",
        "meter_type": meter_type if meter_type else "Unknown",
        "meter_model": meter_model if meter_model else "Unknown",
        "error_code": error_code if error_code else "Unknown",
        "support_level": support_level if support_level else "Unknown",
        "missing_information": missing,
        "resolution": resolution,
    }


def build_record(row):
    title = clean(row.get("title"))
    system_info = clean(row.get("system_info"))
    tags = clean(row.get("tags"))
    history = clean(row.get("history"))

    input_parts = []

    if title:
        input_parts.append(f"Title: {title}")

    if system_info:
        input_parts.append(f"System Info: {system_info}")

    if tags:
        input_parts.append(f"Tags: {tags}")

    if not is_unknown(history):
        input_parts.append(f"History: {history}")

    user_input = "\n".join(input_parts)

    instruction = (
        "Analyze this ISKRA L1 support case using only the provided evidence. "
        "Classify the issue, identify the software/system, meter type, meter model, "
        "and error code when available. Identify the support level only when explicitly "
        "supported by the source data. If information is missing, return Unknown and "
        "state what information should be requested. Never invent technical facts, "
        "root causes, firmware versions, error-code meanings, procedures, or solutions."
    )

    return {
        "case_id": clean(row.get("case_id")),
        "instruction": instruction,
        "input": user_input,
        "expected_output": build_expected_output(row),
    }


def main():
    print("=" * 70)
    print("ISKRA L1 EVALUATION DATASET BUILDER")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"\nInput records: {len(rows)}")

    if len(rows) < EVALUATION_SIZE:
        raise ValueError(
            f"Not enough records. Required: {EVALUATION_SIZE}, "
            f"available: {len(rows)}"
        )

    random.seed(RANDOM_SEED)

    # Stratified sampling by issue category where possible.
    groups = {}

    for row in rows:
        category = clean(row.get("issue_category")) or "Unknown"
        groups.setdefault(category, []).append(row)

    selected = []

    # First pass: guarantee representation of every issue category.
    for category, category_rows in groups.items():
        if category_rows:
            selected.append(random.choice(category_rows))

    selected_ids = {
        clean(row.get("case_id"))
        for row in selected
        if clean(row.get("case_id"))
    }

    remaining = [
        row
        for row in rows
        if clean(row.get("case_id")) not in selected_ids
    ]

    random.shuffle(remaining)

    needed = EVALUATION_SIZE - len(selected)

    if needed > 0:
        selected.extend(remaining[:needed])

    # Final deterministic shuffle.
    random.shuffle(selected)

    records = [build_record(row) for row in selected]

    # Remove accidental duplicate IDs.
    unique_records = []
    seen_ids = set()

    for record in records:
        case_id = record["case_id"]

        if case_id in seen_ids:
            continue

        seen_ids.add(case_id)
        unique_records.append(record)

    records = unique_records

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    csv_fields = [
        "case_id",
        "input",
        "issue_category",
        "system",
        "meter_type",
        "meter_model",
        "error_code",
        "support_level",
        "missing_information",
        "resolution",
    ]

    with CSV_OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()

        for record in records:
            expected = record["expected_output"]

            writer.writerow({
                "case_id": record["case_id"],
                "input": record["input"],
                "issue_category": expected["issue_category"],
                "system": expected["system"],
                "meter_type": expected["meter_type"],
                "meter_model": expected["meter_model"],
                "error_code": expected["error_code"],
                "support_level": expected["support_level"],
                "missing_information": "; ".join(
                    expected["missing_information"]
                ),
                "resolution": expected["resolution"],
            })

    issue_counter = Counter(
        record["expected_output"]["issue_category"]
        for record in records
    )

    system_counter = Counter(
        record["expected_output"]["system"]
        for record in records
    )

    meter_counter = Counter(
        record["expected_output"]["meter_type"]
        for record in records
    )

    verified_resolutions = sum(
        record["expected_output"]["resolution"]
        != "Not available from verified source data."
        for record in records
    )

    unknown_systems = sum(
        record["expected_output"]["system"] == "Unknown"
        for record in records
    )

    unknown_meter_types = sum(
        record["expected_output"]["meter_type"] == "Unknown"
        for record in records
    )

    report = []

    report.append("=" * 70)
    report.append("ISKRA L1 EVALUATION DATASET REPORT")
    report.append("=" * 70)
    report.append("")
    report.append(f"Input records: {len(rows)}")
    report.append(f"Evaluation records: {len(records)}")
    report.append(f"Random seed: {RANDOM_SEED}")
    report.append("")
    report.append("ISSUE CATEGORIES")
    report.append("-" * 70)

    for key, count in issue_counter.most_common():
        report.append(f"- {key}: {count}")

    report.append("")
    report.append("SYSTEMS")
    report.append("-" * 70)

    for key, count in system_counter.most_common():
        report.append(f"- {key}: {count}")

    report.append("")
    report.append("METER TYPES")
    report.append("-" * 70)

    for key, count in meter_counter.most_common():
        report.append(f"- {key}: {count}")

    report.append("")
    report.append("QUALITY")
    report.append("-" * 70)
    report.append(f"Unknown systems: {unknown_systems}")
    report.append(f"Unknown meter types: {unknown_meter_types}")
    report.append(f"Verified resolution records: {verified_resolutions}")
    report.append("")
    report.append("SAFETY")
    report.append("-" * 70)
    report.append("- Evaluation data is generated from source evidence.")
    report.append("- Unknown values are preserved.")
    report.append("- No unsupported solutions are generated.")
    report.append("- No unsupported root causes are generated.")
    report.append("- This dataset is for evaluation, not fine-tuning.")
    report.append("")
    report.append("FILES")
    report.append("-" * 70)
    report.append(str(OUTPUT_FILE))
    report.append(str(CSV_OUTPUT_FILE))
    report.append(str(REPORT_FILE))

    REPORT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\n" + "\n".join(report))

    print("\n" + "=" * 70)
    print("EVALUATION DATASET BUILD: PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()