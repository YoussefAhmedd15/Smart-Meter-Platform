import json
import re
from collections import Counter, defaultdict
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
    / "taxonomy"
)

ISSUE_OUTPUT = OUTPUT_DIR / "issue_taxonomy.json"
SYSTEM_OUTPUT = OUTPUT_DIR / "system_taxonomy.json"
METER_OUTPUT = OUTPUT_DIR / "meter_taxonomy.json"
ERROR_OUTPUT = OUTPUT_DIR / "error_code_taxonomy.json"
REPORT_OUTPUT = OUTPUT_DIR / "taxonomy_report.txt"

MAX_EXAMPLES_PER_VALUE = 10


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)

    return text


def split_multi_value(value):
    value = clean_value(value)

    if not value:
        return []

    parts = [
        part.strip()
        for part in value.split("|")
    ]

    return [
        part
        for part in parts
        if part
    ]


def normalize_key(value):
    return clean_value(value).lower()


def add_example(examples, key, row):

    if key not in examples:
        examples[key] = []

    if len(examples[key]) >= MAX_EXAMPLES_PER_VALUE:
        return

    example = {
        "case_id": clean_value(
            row.get("case_id", "")
        ),
        "title": clean_value(
            row.get("title", "")
        ),
        "system_info": clean_value(
            row.get("system_info", "")
        ),
        "tags": clean_value(
            row.get("tags", "")
        ),
    }

    if example not in examples[key]:
        examples[key].append(example)


# ============================================================
# ISSUE TAXONOMY
# ============================================================

def build_issue_taxonomy(df):

    counter = Counter()
    source_counter = Counter()
    examples = defaultdict(list)

    for _, row in df.iterrows():

        value = clean_value(
            row.get("issue_category", "")
        )

        if not value:
            value = "Unknown"

        categories = split_multi_value(value)

        if not categories:
            categories = ["Unknown"]

        source = clean_value(
            row.get("classification_source", "")
        )

        if source:
            source_counter[source] += 1
        else:
            source_counter["unknown"] += 1

        for category in categories:

            counter[category] += 1

            add_example(
                examples,
                normalize_key(category),
                row,
            )

    total = len(df)

    values = []

    for category, count in counter.most_common():

        values.append({
            "name": category,
            "count": count,
            "percentage_of_records": round(
                (count / total) * 100,
                2
            ) if total else 0,
            "examples": examples[
                normalize_key(category)
            ],
        })

    return {
        "taxonomy_name": "ISKRA L1 Issue Taxonomy",
        "description": (
            "Issue categories extracted from the "
            "structured L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total,
        "values": values,
        "classification_sources": dict(
            source_counter.most_common()
        ),
        "notes": [
            "This taxonomy describes the existing dataset.",
            "It does not prove ground-truth correctness.",
            "Unknown values are preserved.",
            "No root cause or solution is invented.",
        ],
    }


# ============================================================
# SYSTEM TAXONOMY
# ============================================================

def build_system_taxonomy(df):

    counter = Counter()
    source_counter = Counter()
    examples = defaultdict(list)

    for _, row in df.iterrows():

        value = clean_value(
            row.get("detected_system", "")
        )

        if not value:
            value = "Unknown"

        systems = split_multi_value(value)

        if not systems:
            systems = ["Unknown"]

        source = clean_value(
            row.get("system_source", "")
        )

        if source:
            source_counter[source] += 1
        else:
            source_counter["unknown"] += 1

        for system in systems:

            counter[system] += 1

            add_example(
                examples,
                normalize_key(system),
                row,
            )

    total = len(df)

    values = []

    for system, count in counter.most_common():

        values.append({
            "name": system,
            "count": count,
            "percentage_of_records": round(
                (count / total) * 100,
                2
            ) if total else 0,
            "examples": examples[
                normalize_key(system)
            ],
        })

    return {
        "taxonomy_name": "ISKRA L1 System Taxonomy",
        "description": (
            "Systems detected in the L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total,
        "values": values,
        "system_sources": dict(
            source_counter.most_common()
        ),
        "notes": [
            "Unknown means there was not enough evidence.",
            "System classification is kept separate from issue classification.",
            "System names are not automatically treated as Software issues.",
        ],
    }


# ============================================================
# METER TAXONOMY
# ============================================================

def build_meter_taxonomy(df):

    type_counter = Counter()
    model_counter = Counter()

    type_examples = defaultdict(list)
    model_examples = defaultdict(list)

    source_counter = Counter()

    for _, row in df.iterrows():

        meter_type = clean_value(
            row.get("meter_type", "")
        )

        if not meter_type:
            meter_type = "Unknown"

        type_counter[meter_type] += 1

        add_example(
            type_examples,
            normalize_key(meter_type),
            row,
        )

        source = clean_value(
            row.get("meter_type_source", "")
        )

        if source:
            source_counter[source] += 1
        else:
            source_counter["unknown"] += 1

        models_value = clean_value(
            row.get("detected_meter_models", "")
        )

        models = split_multi_value(
            models_value
        )

        for model in models:

            if model.lower() == "unknown":
                continue

            model_counter[model] += 1

            add_example(
                model_examples,
                normalize_key(model),
                row,
            )

    total = len(df)

    meter_types = []

    for meter_type, count in type_counter.most_common():

        meter_types.append({
            "name": meter_type,
            "count": count,
            "percentage_of_records": round(
                (count / total) * 100,
                2
            ) if total else 0,
            "examples": type_examples[
                normalize_key(meter_type)
            ],
        })

    meter_models = []

    for model, count in model_counter.most_common():

        meter_models.append({
            "name": model,
            "count": count,
            "examples": model_examples[
                normalize_key(model)
            ],
        })

    return {
        "taxonomy_name": "ISKRA L1 Meter Taxonomy",
        "description": (
            "Meter types and models detected from "
            "the L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total,
        "meter_types": meter_types,
        "meter_models": meter_models,
        "meter_type_sources": dict(
            source_counter.most_common()
        ),
        "notes": [
            "Unknown values are preserved.",
            "Detected models are based on existing extraction.",
            "No unsupported meter model is invented.",
        ],
    }


# ============================================================
# ERROR CODE TAXONOMY
# ============================================================

def build_error_code_taxonomy(df):

    counter = Counter()
    examples = defaultdict(list)

    for _, row in df.iterrows():

        value = clean_value(
            row.get("error_code", "")
        )

        if not value:
            continue

        codes = split_multi_value(value)

        for code in codes:

            if code.lower() == "unknown":
                continue

            counter[code] += 1

            add_example(
                examples,
                normalize_key(code),
                row,
            )

    total = len(df)

    values = []

    for code, count in counter.most_common():

        values.append({
            "code": code,
            "count": count,
            "percentage_of_records": round(
                (count / total) * 100,
                2
            ) if total else 0,
            "examples": examples[
                normalize_key(code)
            ],
        })

    return {
        "taxonomy_name": "ISKRA L1 Error Code Taxonomy",
        "description": (
            "Explicitly detected error codes from "
            "the L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total,
        "total_unique_error_codes": len(values),
        "values": values,
        "notes": [
            "Only explicitly detected error codes are included.",
            "No meaning is assigned to an error code.",
            "No solution or root cause is invented.",
        ],
    }


# ============================================================
# REPORT
# ============================================================

def build_report(
    df,
    issue_taxonomy,
    system_taxonomy,
    meter_taxonomy,
    error_taxonomy,
):

    lines = []

    lines.append("=" * 70)
    lines.append("ISKRA L1 TAXONOMY REPORT")
    lines.append("=" * 70)

    lines.append("")
    lines.append(
        f"Input file: {INPUT_FILE}"
    )
    lines.append(
        f"Total records: {len(df)}"
    )

    # --------------------------------------------------------
    # ISSUE
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("ISSUE TAXONOMY")
    lines.append("=" * 70)

    for item in issue_taxonomy["values"]:

        lines.append(
            f"- {item['name']}: "
            f"{item['count']} "
            f"({item['percentage_of_records']}%)"
        )

    lines.append("")
    lines.append("Classification Sources:")

    for source, count in issue_taxonomy[
        "classification_sources"
    ].items():

        percentage = (
            count / len(df) * 100
            if len(df)
            else 0
        )

        lines.append(
            f"- {source}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("SYSTEM TAXONOMY")
    lines.append("=" * 70)

    for item in system_taxonomy["values"]:

        lines.append(
            f"- {item['name']}: "
            f"{item['count']} "
            f"({item['percentage_of_records']}%)"
        )

    lines.append("")
    lines.append("System Sources:")

    for source, count in system_taxonomy[
        "system_sources"
    ].items():

        percentage = (
            count / len(df) * 100
            if len(df)
            else 0
        )

        lines.append(
            f"- {source}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # --------------------------------------------------------
    # METER
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("METER TYPES")
    lines.append("=" * 70)

    for item in meter_taxonomy["meter_types"]:

        lines.append(
            f"- {item['name']}: "
            f"{item['count']} "
            f"({item['percentage_of_records']}%)"
        )

    lines.append("")
    lines.append("=" * 70)
    lines.append("METER MODELS")
    lines.append("=" * 70)

    if meter_taxonomy["meter_models"]:

        for item in meter_taxonomy["meter_models"]:

            lines.append(
                f"- {item['name']}: "
                f"{item['count']}"
            )

    else:

        lines.append(
            "- No meter models detected."
        )

    # --------------------------------------------------------
    # ERROR CODES
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("ERROR CODES")
    lines.append("=" * 70)

    lines.append(
        "Unique error codes: "
        f"{error_taxonomy['total_unique_error_codes']}"
    )

    if error_taxonomy["values"]:

        for item in error_taxonomy["values"]:

            lines.append(
                f"- {item['code']}: "
                f"{item['count']} "
                f"({item['percentage_of_records']}%)"
            )

    else:

        lines.append(
            "- No error codes detected."
        )

    # --------------------------------------------------------
    # DATA QUALITY
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("DATA QUALITY SUMMARY")
    lines.append("=" * 70)

    if "issue_category" in df.columns:

        unknown_issue = (
            df["issue_category"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("unknown")
            .sum()
        )

        lines.append(
            f"- Unknown issue category: "
            f"{unknown_issue}"
        )

    if "detected_system" in df.columns:

        unknown_system = (
            df["detected_system"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("unknown")
            .sum()
        )

        lines.append(
            f"- Unknown system: "
            f"{unknown_system}"
        )

    if "meter_type" in df.columns:

        unknown_meter = (
            df["meter_type"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("unknown")
            .sum()
        )

        lines.append(
            f"- Unknown meter type: "
            f"{unknown_meter}"
        )

    if "history" in df.columns:

        history_count = (
            df["history"]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
            .sum()
        )

        lines.append(
            f"- Records with History: "
            f"{history_count}"
        )

    if "resolution_source" in df.columns:

        known_resolution = (
            df["resolution_source"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .ne("")
            .sum()
        )

        lines.append(
            f"- Records with resolution evidence: "
            f"{known_resolution}"
        )

    # --------------------------------------------------------
    # NOTES
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("IMPORTANT NOTES")
    lines.append("=" * 70)

    lines.append(
        "1. Taxonomy describes the current dataset."
    )

    lines.append(
        "2. It is not independent ground-truth validation."
    )

    lines.append(
        "3. Unknown values are preserved."
    )

    lines.append(
        "4. No solution or root cause is invented."
    )

    lines.append(
        "5. Error codes are not assigned meanings."
    )

    lines.append(
        "6. Manual review is recommended before fine-tuning."
    )

    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


# ============================================================
# SAVE JSON
# ============================================================

def save_json(path, data):

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ISKRA L1 TAXONOMY BUILDER")
    print("=" * 70)

    print("")
    print("Input:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():

        print("")
        print(
            "ERROR: Input file was not found."
        )

        print("")
        print(
            "Expected:"
        )

        print(
            INPUT_FILE
        )

        return

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    print("")
    print("Loading dataset...")

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False,
    )

    print(
        f"Loaded records: {len(df)}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

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
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        print("")
        print(
            "ERROR: Missing required columns:"
        )

        for column in missing:
            print(
                f" - {column}"
            )

        print("")
        print(
            "Taxonomy was NOT generated."
        )

        return

    # --------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    print("")
    print("Building issue taxonomy...")

    issue_taxonomy = build_issue_taxonomy(df)

    print(
        "Issue categories:",
        len(issue_taxonomy["values"])
    )

    print("")
    print("Building system taxonomy...")

    system_taxonomy = build_system_taxonomy(df)

    print(
        "Systems:",
        len(system_taxonomy["values"])
    )

    print("")
    print("Building meter taxonomy...")

    meter_taxonomy = build_meter_taxonomy(df)

    print(
        "Meter types:",
        len(meter_taxonomy["meter_types"])
    )

    print(
        "Meter models:",
        len(meter_taxonomy["meter_models"])
    )

    print("")
    print("Building error code taxonomy...")

    error_taxonomy = build_error_code_taxonomy(df)

    print(
        "Unique error codes:",
        error_taxonomy[
            "total_unique_error_codes"
        ]
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    print("")
    print("Saving taxonomy files...")

    save_json(
        ISSUE_OUTPUT,
        issue_taxonomy,
    )

    save_json(
        SYSTEM_OUTPUT,
        system_taxonomy,
    )

    save_json(
        METER_OUTPUT,
        meter_taxonomy,
    )

    save_json(
        ERROR_OUTPUT,
        error_taxonomy,
    )

    report = build_report(
        df,
        issue_taxonomy,
        system_taxonomy,
        meter_taxonomy,
        error_taxonomy,
    )

    with open(
        REPORT_OUTPUT,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(report)

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("")
    print("=" * 70)
    print("TAXONOMY BUILD COMPLETE")
    print("=" * 70)

    print("")
    print("Generated files:")

    print(
        f" - {ISSUE_OUTPUT}"
    )

    print(
        f" - {SYSTEM_OUTPUT}"
    )

    print(
        f" - {METER_OUTPUT}"
    )

    print(
        f" - {ERROR_OUTPUT}"
    )

    print(
        f" - {REPORT_OUTPUT}"
    )

    print("")
    print("Summary:")

    print(
        f" - Records: {len(df)}"
    )

    print(
        f" - Issue categories: "
        f"{len(issue_taxonomy['values'])}"
    )

    print(
        f" - Systems: "
        f"{len(system_taxonomy['values'])}"
    )

    print(
        f" - Meter types: "
        f"{len(meter_taxonomy['meter_types'])}"
    )

    print(
        f" - Meter models: "
        f"{len(meter_taxonomy['meter_models'])}"
    )

    print(
        f" - Error codes: "
        f"{error_taxonomy['total_unique_error_codes']}"
    )

    print("")
    print(
        "Taxonomy report saved successfully."
    )


if __name__ == "__main__":
    main()