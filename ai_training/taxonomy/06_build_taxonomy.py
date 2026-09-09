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


# ============================================================
# CONFIGURATION
# ============================================================

MAX_EXAMPLES_PER_VALUE = 10


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """Convert NaN/None to empty string and normalize whitespace."""
    if pd.isna(value):
        return ""

    text = str(value).strip()

    text = re.sub(r"\s+", " ", text)

    return text


def split_multi_value(value):
    """
    Split values such as:
        Software|Hardware
        MeterVerse|Electric

    Returns a clean list.
    """
    value = clean_value(value)

    if not value:
        return []

    parts = [part.strip() for part in value.split("|")]

    return [part for part in parts if part]


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def normalize_for_key(value):
    """Create a stable key for grouping."""
    value = clean_value(value)

    return value.lower()


def add_example(
    examples_dict,
    key,
    row,
):
    """
    Add a small number of representative examples for each taxonomy value.
    """

    if key not in examples_dict:
        examples_dict[key] = []

    if len(examples_dict[key]) >= MAX_EXAMPLES_PER_VALUE:
        return

    case_id = clean_value(row.get("ID", ""))

    title = clean_value(row.get("Title", ""))

    system_info = clean_value(row.get("System Info", ""))

    tags = clean_value(row.get("Tags", ""))

    example = {
        "id": case_id,
        "title": title,
        "system_info": system_info,
        "tags": tags,
    }

    # Avoid duplicate examples.
    if example not in examples_dict[key]:
        examples_dict[key].append(example)


# ============================================================
# ISSUE TAXONOMY
# ============================================================

def build_issue_taxonomy(df):
    """
    Build issue taxonomy from issue_category.

    Important:
    We do NOT recalculate issue categories here.
    We use the classifications already produced by
    04_build_l1_knowledge.py.
    """

    counter = Counter()

    source_counter = Counter()

    examples = defaultdict(list)

    for _, row in df.iterrows():

        category_value = clean_value(
            row.get("issue_category", "")
        )

        if not category_value:
            category_value = "Unknown"

        categories = split_multi_value(category_value)

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
                normalize_for_key(category),
                row,
            )

    values = []

    total_records = len(df)

    for category, count in counter.most_common():

        category_examples = examples[
            normalize_for_key(category)
        ]

        values.append(
            {
                "name": category,
                "count": count,
                "percentage_of_records": round(
                    (count / total_records) * 100,
                    2,
                )
                if total_records
                else 0,
                "examples": category_examples,
            }
        )

    return {
        "taxonomy_name": "ISKRA L1 Issue Taxonomy",
        "description": (
            "Issue categories extracted from the structured "
            "L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total_records,
        "values": values,
        "classification_sources": dict(
            source_counter.most_common()
        ),
        "notes": [
            (
                "Categories are derived from the existing "
                "structured dataset."
            ),
            (
                "This taxonomy describes the dataset and "
                "does not by itself prove ground-truth correctness."
            ),
            (
                "Multi-label records may contribute to more "
                "than one category count."
            ),
        ],
    }


# ============================================================
# SYSTEM TAXONOMY
# ============================================================

def build_system_taxonomy(df):
    """
    Build system taxonomy from detected_system.

    Does not infer software classification from system names.
    """

    counter = Counter()

    source_counter = Counter()

    examples = defaultdict(list)

    for _, row in df.iterrows():

        system_value = clean_value(
            row.get("detected_system", "")
        )

        if not system_value:
            system_value = "Unknown"

        systems = split_multi_value(system_value)

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
                normalize_for_key(system),
                row,
            )

    values = []

    total_records = len(df)

    for system, count in counter.most_common():

        values.append(
            {
                "name": system,
                "count": count,
                "percentage_of_records": round(
                    (count / total_records) * 100,
                    2,
                )
                if total_records
                else 0,
                "examples": examples[
                    normalize_for_key(system)
                ],
            }
        )

    return {
        "taxonomy_name": "ISKRA L1 System Taxonomy",
        "description": (
            "Software/system names extracted from "
            "the structured L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total_records,
        "values": values,
        "system_sources": dict(
            source_counter.most_common()
        ),
        "notes": [
            (
                "Unknown means that the current dataset "
                "did not provide enough evidence to identify "
                "the system."
            ),
            (
                "System identification is kept separate from "
                "issue classification."
            ),
        ],
    }


# ============================================================
# METER TAXONOMY
# ============================================================

def build_meter_taxonomy(df):
    """
    Build meter taxonomy using meter type and detected models.
    """

    meter_type_counter = Counter()

    model_counter = Counter()

    meter_type_examples = defaultdict(list)

    model_examples = defaultdict(list)

    meter_type_source_counter = Counter()

    for _, row in df.iterrows():

        meter_type = clean_value(
            row.get("meter_type", "")
        )

        if not meter_type:
            meter_type = "Unknown"

        meter_type_counter[meter_type] += 1

        add_example(
            meter_type_examples,
            normalize_for_key(meter_type),
            row,
        )

        meter_type_source = clean_value(
            row.get("meter_type_source", "")
        )

        if meter_type_source:
            meter_type_source_counter[
                meter_type_source
            ] += 1
        else:
            meter_type_source_counter[
                "unknown"
            ] += 1

        models_value = clean_value(
            row.get("detected_meter_models", "")
        )

        if models_value:
            models = split_multi_value(models_value)

            for model in models:

                if model.lower() == "unknown":
                    continue

                model_counter[model] += 1

                add_example(
                    model_examples,
                    normalize_for_key(model),
                    row,
                )

    total_records = len(df)

    meter_types = []

    for meter_type, count in meter_type_counter.most_common():

        meter_types.append(
            {
                "name": meter_type,
                "count": count,
                "percentage_of_records": round(
                    (count / total_records) * 100,
                    2,
                )
                if total_records
                else 0,
                "examples": meter_type_examples[
                    normalize_for_key(meter_type)
                ],
            }
        )

    models = []

    for model, count in model_counter.most_common():

        models.append(
            {
                "name": model,
                "count": count,
                "examples": model_examples[
                    normalize_for_key(model)
                ],
            }
        )

    return {
        "taxonomy_name": "ISKRA L1 Meter Taxonomy",
        "description": (
            "Meter types and meter models explicitly detected "
            "from the structured L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total_records,
        "meter_types": meter_types,
        "meter_models": models,
        "meter_type_sources": dict(
            meter_type_source_counter.most_common()
        ),
        "notes": [
            (
                "Unknown means that the available case evidence "
                "was insufficient to identify the meter type."
            ),
            (
                "Detected models represent models found by the "
                "current extraction rules."
            ),
            (
                "Absence of a model does not mean the case has "
                "no meter model; it means the current dataset "
                "did not expose one through the extraction rules."
            ),
        ],
    }


# ============================================================
# ERROR CODE TAXONOMY
# ============================================================

def build_error_code_taxonomy(df):
    """
    Build error-code taxonomy from explicitly extracted error codes.
    """

    counter = Counter()

    examples = defaultdict(list)

    for _, row in df.iterrows():

        error_value = clean_value(
            row.get("error_code", "")
        )

        if not error_value:
            continue

        error_codes = split_multi_value(error_value)

        for error_code in error_codes:

            if error_code.lower() == "unknown":
                continue

            counter[error_code] += 1

            add_example(
                examples,
                normalize_for_key(error_code),
                row,
            )

    total_records = len(df)

    values = []

    for error_code, count in counter.most_common():

        values.append(
            {
                "code": error_code,
                "count": count,
                "percentage_of_records": round(
                    (count / total_records) * 100,
                    2,
                )
                if total_records
                else 0,
                "examples": examples[
                    normalize_for_key(error_code)
                ],
            }
        )

    return {
        "taxonomy_name": "ISKRA L1 Error Code Taxonomy",
        "description": (
            "Error codes explicitly extracted from the "
            "structured L1 knowledge dataset."
        ),
        "source_file": str(INPUT_FILE),
        "total_records": total_records,
        "total_unique_error_codes": len(values),
        "values": values,
        "notes": [
            (
                "Only explicitly extracted error codes are included."
            ),
            (
                "The taxonomy does not assign meanings or root causes "
                "to error codes."
            ),
            (
                "An error code appearing in this dataset does not "
                "automatically mean its solution is known."
            ),
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
    lines.append(f"Input file: {INPUT_FILE}")
    lines.append(f"Total records: {len(df)}")

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
            (count / len(df)) * 100
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
            (count / len(df)) * 100
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
    lines.append("METER TYPE")
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

        lines.append("- No meter models detected.")

    # --------------------------------------------------------
    # ERROR CODES
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("ERROR CODES")
    lines.append("=" * 70)

    lines.append(
        f"Unique error codes: "
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

        lines.append("- No error codes detected.")

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
            .eq("")
            .sum()
        )

        lines.append(
            f"- Records without issue category: "
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
            f"- Records with Unknown system: "
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
            f"- Records with Unknown meter type: "
            f"{unknown_meter}"
        )

    if "History" in df.columns:

        history_count = (
            df["History"]
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

    if "resolution" in df.columns:

        resolution_known = (
            df["resolution"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .ne("unknown")
            .sum()
        )

        lines.append(
            f"- Records with known resolution field: "
            f"{resolution_known}"
        )

    # --------------------------------------------------------
    # IMPORTANT NOTES
    # --------------------------------------------------------

    lines.append("")
    lines.append("=" * 70)
    lines.append("IMPORTANT NOTES")
    lines.append("=" * 70)

    lines.append(
        "1. This taxonomy is descriptive, not ground-truth validation."
    )

    lines.append(
        "2. Unknown values are preserved instead of being guessed."
    )

    lines.append(
        "3. No resolution or root cause is invented."
    )

    lines.append(
        "4. System names are not automatically treated as Software issues."
    )

    lines.append(
        "5. Error codes are listed without assigning a meaning or solution."
    )

    lines.append(
        "6. Manual review is recommended before using these records "
        "for supervised fine-tuning."
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
        print("ERROR: Input file was not found.")
        print("")
        print("Expected:")
        print(INPUT_FILE)

        return

    # --------------------------------------------------------
    # READ DATASET
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
        "ID",
        "Title",
        "System Info",
        "Tags",
        "History",
        "issue_category",
        "detected_system",
        "meter_type",
        "detected_meter_models",
        "classification_source",
        "system_source",
        "meter_type_source",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("")
        print("ERROR: Missing required columns:")

        for column in missing_columns:
            print(f" - {column}")

        print("")
        print(
            "The taxonomy builder was NOT executed."
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
    # BUILD TAXONOMIES
    # --------------------------------------------------------

    print("")
    print("Building issue taxonomy...")

    issue_taxonomy = build_issue_taxonomy(df)

    print(
        f"Issue values: "
        f"{len(issue_taxonomy['values'])}"
    )

    print("")
    print("Building system taxonomy...")

    system_taxonomy = build_system_taxonomy(df)

    print(
        f"System values: "
        f"{len(system_taxonomy['values'])}"
    )

    print("")
    print("Building meter taxonomy...")

    meter_taxonomy = build_meter_taxonomy(df)

    print(
        f"Meter types: "
        f"{len(meter_taxonomy['meter_types'])}"
    )

    print(
        f"Meter models: "
        f"{len(meter_taxonomy['meter_models'])}"
    )

    print("")
    print("Building error code taxonomy...")

    error_taxonomy = build_error_code_taxonomy(df)

    print(
        f"Unique error codes: "
        f"{error_taxonomy['total_unique_error_codes']}"
    )

    # --------------------------------------------------------
    # SAVE JSON FILES
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

    # --------------------------------------------------------
    # BUILD + SAVE REPORT
    # --------------------------------------------------------

    print("")
    print("Building taxonomy report...")

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
    # FINAL OUTPUT
    # --------------------------------------------------------

    print("")
    print("=" * 70)
    print("TAXONOMY BUILD COMPLETE")
    print("=" * 70)

    print("")
    print("Generated files:")

    print(f" - {ISSUE_OUTPUT}")
    print(f" - {SYSTEM_OUTPUT}")
    print(f" - {METER_OUTPUT}")
    print(f" - {ERROR_OUTPUT}")
    print(f" - {REPORT_OUTPUT}")

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
    print("Next step:")
    print(
        "Review taxonomy_report.txt before building "
        "the training dataset."
    )


if __name__ == "__main__":
    main()