import pandas as pd
import re
import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "cleaned"
    / "l1_cases_cleaned.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "structured"
    / "l1_knowledge_records.csv"
)

OUTPUT_JSONL = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "structured"
    / "l1_knowledge_records.jsonl"
)


# ============================================================
# HELPERS
# ============================================================

def safe_text(value):
    """Return clean string."""
    if pd.isna(value):
        return ""

    text = str(value)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_lower(value):
    """Lowercase normalized text."""
    return safe_text(value).lower()


def contains_any(text, keywords):
    """Check whether text contains any keyword."""
    text = normalize_lower(text)

    return any(keyword.lower() in text for keyword in keywords)


def unique_list(items):
    """Keep order and remove duplicates."""
    result = []

    for item in items:
        if item and item not in result:
            result.append(item)

    return result


# ============================================================
# SOURCE TRACKING
# ============================================================

def get_source_list(
    title,
    system_info,
    tags,
    history,
    keywords
):
    """
    Determine exactly where the classification evidence exists.

    Sources:
        tag
        title
        system_info
        history
        unknown
    """

    sources = []

    if contains_any(tags, keywords):
        sources.append("tag")

    if contains_any(title, keywords):
        sources.append("title")

    if contains_any(system_info, keywords):
        sources.append("system_info")

    if contains_any(history, keywords):
        sources.append("history")

    return unique_list(sources)


def format_source(sources):
    """
    Convert source list into classification_source value.
    """

    if not sources:
        return "unknown"

    if len(sources) == 1:
        return sources[0]

    if len(sources) >= 3:
        return "multiple"

    return "+".join(sources)


# ============================================================
# ISSUE CLASSIFICATION
# ============================================================

def classify_issue(
    title,
    system_info,
    tags,
    history
):
    """
    Evidence-based issue classification.

    IMPORTANT:
    This function does NOT guess.

    It only classifies when explicit evidence exists.
    """

    categories = {
        "Software": [
            "software",
            "application",
            "program",
            "system",
            "login",
            "ui",
            "interface",
            "vending",
            "billing",
            "meterverse",
            "symbiot",
            "aqua",
        ],

        "Hardware": [
            "hardware",
            "display",
            "lcd",
            "relay",
            "battery",
            "pcb",
            "board",
            "button",
            "keypad",
        ],

        "Firmware": [
            "firmware",
            "firm",
            "firmware update",
            "firmware upgrade",
            "fw update",
            "fw upgrade",
        ],

        "Communication": [
            "communication error",
            "communication",
            "connection",
            "connectivity",
            "dlms",
            "hdlc",
            "serial",
            "optical",
        ],
    }

    detected = []

    source_map = {}

    for category, keywords in categories.items():

        sources = get_source_list(
            title,
            system_info,
            tags,
            history,
            keywords
        )

        if sources:

            detected.append(category)

            source_map[category] = sources

    # No evidence
    if not detected:
        return "Unknown", "unknown", {}

    # One clear category
    if len(detected) == 1:

        category = detected[0]

        return (
            category,
            format_source(source_map[category]),
            source_map
        )

    # Multiple categories detected
    return (
        "|".join(detected),
        "multiple",
        source_map
    )


# ============================================================
# SYSTEM DETECTION
# ============================================================

def detect_system(
    title,
    system_info,
    tags,
    history
):
    """
    Detect system only from explicit textual evidence.
    """

    systems = {
        "Billing": ["billing"],
        "Symbiot": ["symbiot"],
        "Vending": ["vending"],
        "MeterVerse": ["meterverse"],
        "Aqua": ["aqua"],
        "Electric": ["electric", "electricity"],
    }

    detected = []
    source_map = {}

    for system, keywords in systems.items():

        sources = get_source_list(
            title,
            system_info,
            tags,
            history,
            keywords
        )

        if sources:
            detected.append(system)
            source_map[system] = sources

    if not detected:
        return "Unknown", "unknown", {}

    return (
        "|".join(detected),
        "multiple" if len(detected) > 1 else format_source(
            source_map[detected[0]]
        ),
        source_map
    )


# ============================================================
# METER TYPE
# ============================================================

def detect_meter_type(
    title,
    system_info,
    tags,
    history
):
    """
    Detect meter type only when explicitly mentioned.

    We DO NOT infer:
        Aqua = Water
        Electric system = Electric meter

    unless the actual word exists in the source.
    """

    types = {
        "Water": [
            "water",
            "water meter",
        ],

        "Electric": [
            "electric meter",
            "electricity meter",
            "electric",
        ],

        "Ultrasonic": [
            "ultrasonic",
            "ultrasonic meter",
        ],
    }

    detected = []
    source_map = {}

    for meter_type, keywords in types.items():

        sources = get_source_list(
            title,
            system_info,
            tags,
            history,
            keywords
        )

        if sources:

            detected.append(meter_type)
            source_map[meter_type] = sources

    if not detected:
        return "Unknown", "unknown", {}

    if len(detected) == 1:

        meter_type = detected[0]

        return (
            meter_type,
            format_source(source_map[meter_type]),
            source_map
        )

    return (
        "|".join(detected),
        "multiple",
        source_map
    )


# ============================================================
# ERROR CODE
# ============================================================

def extract_error_codes(text):
    """
    Extract explicit error codes.
    """

    text = safe_text(text)

    if not text:
        return []

    patterns = [
        r"\berror\s*[-:#]?\s*(\d+)\b",
        r"\berr\s*[-:#]?\s*(\d+)\b",
        r"\be[- ]?(\d+)\b",
        r"\breject\s*[-:#]?\s*(\d+)\b",
    ]

    results = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:

            if match not in results:
                results.append(match)

    return results


# ============================================================
# METER MODELS
# ============================================================

def extract_meter_models(text):
    """
    Extract explicitly mentioned ISKRA meter models.
    """

    text = safe_text(text)

    if not text:
        return []

    patterns = [

        r"\bME514(?:-[A-Za-z0-9]+)?\b",

        r"\bMT514(?:-[A-Za-z0-9]+)?\b",

        r"\bAM550\b",

        r"\bMT880\b",

        r"\bMT800\b",

        r"\bMW5\d{2}\b",

        r"\bMV5\d{2}\b",
    ]

    results = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:

            normalized = match.upper()

            if normalized not in results:
                results.append(normalized)

    return results


# ============================================================
# SUPPORT LEVEL
# ============================================================

def detect_support_level(
    title,
    system_info,
    tags,
    history
):
    """
    Detect support level ONLY when explicitly mentioned.

    Default = Unknown.

    We must NOT assume every case is L1.
    """

    combined = " ".join(
        [
            title,
            system_info,
            tags,
            history,
        ]
    ).lower()

    if "l2 software" in combined:
        return "L2 Software", "explicit"

    if "l2 hardware" in combined:
        return "L2 Hardware", "explicit"

    if "l2 firmware" in combined:
        return "L2 Firmware", "explicit"

    if "l2" in combined:
        return "L2", "explicit"

    if "l1" in combined:
        return "L1", "explicit"

    return "Unknown", "unknown"


# ============================================================
# CASE TEXT
# ============================================================

def build_case_text(
    case_id,
    title,
    system_info,
    tags,
    history,
    meter_models,
    error_codes,
    issue_category,
    detected_system,
    meter_type
):
    """
    Build structured text that can later be used by RAG.
    """

    history_value = history if history else "Unknown"

    models_value = (
        ", ".join(meter_models)
        if meter_models
        else "Unknown"
    )

    errors_value = (
        ", ".join(error_codes)
        if error_codes
        else "Unknown"
    )

    return f"""
Case ID: {case_id}

Title:
{title or "Unknown"}

System Info:
{system_info or "Unknown"}

Tags:
{tags or "Unknown"}

History:
{history_value}

Detected Meter Model:
{models_value}

Detected Error Code:
{errors_value}

Issue Category:
{issue_category}

Detected System:
{detected_system}

Meter Type:
{meter_type}
""".strip()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ISKRA L1 Knowledge Builder")
    print("=" * 70)

    print("\nInput:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():

        print("\nERROR: Input file was not found.")
        print(INPUT_FILE)

        return

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )

    print(f"\nInput rows: {len(df)}")

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "ID",
        "Title",
        "System Info",
        "Tags",
        "History",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Missing required columns:")

        for column in missing_columns:
            print(f" - {column}")

        return

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    records = []

    for _, row in df.iterrows():

        case_id = safe_text(row["ID"])

        title = safe_text(row["Title"])

        system_info = safe_text(
            row["System Info"]
        )

        tags = safe_text(
            row["Tags"]
        )

        history = safe_text(
            row["History"]
        )

        state = safe_text(
            row["State"]
            if "State" in df.columns
            else ""
        )

        assigned_to = safe_text(
            row["Assigned To"]
            if "Assigned To" in df.columns
            else ""
        )

        resolved_by = safe_text(
            row["Resolved By"]
            if "Resolved By" in df.columns
            else ""
        )

        # ----------------------------------------------------
        # COMBINED TEXT
        # ----------------------------------------------------

        combined_text = " ".join(
            [
                title,
                system_info,
                tags,
                history,
            ]
        ).strip()

        # ----------------------------------------------------
        # ERROR CODES
        # ----------------------------------------------------

        error_codes = extract_error_codes(
            combined_text
        )

        # ----------------------------------------------------
        # METER MODELS
        # ----------------------------------------------------

        meter_models = extract_meter_models(
            combined_text
        )

        # ----------------------------------------------------
        # ISSUE
        # ----------------------------------------------------

        (
            issue_category,
            classification_source,
            classification_source_map
        ) = classify_issue(
            title,
            system_info,
            tags,
            history
        )

        # ----------------------------------------------------
        # SYSTEM
        # ----------------------------------------------------

        (
            detected_system,
            system_source,
            system_source_map
        ) = detect_system(
            title,
            system_info,
            tags,
            history
        )

        # ----------------------------------------------------
        # METER TYPE
        # ----------------------------------------------------

        (
            meter_type,
            meter_type_source,
            meter_type_source_map
        ) = detect_meter_type(
            title,
            system_info,
            tags,
            history
        )

        # ----------------------------------------------------
        # SUPPORT LEVEL
        # ----------------------------------------------------

        (
            support_level,
            support_level_source
        ) = detect_support_level(
            title,
            system_info,
            tags,
            history
        )

        # ----------------------------------------------------
        # RESOLUTION EVIDENCE
        # ----------------------------------------------------

        if history:

            resolution_evidence = history

            resolution_source = "history"

        else:

            resolution_evidence = "Unknown"

            resolution_source = "unknown"

        # ----------------------------------------------------
        # KNOWLEDGE TEXT
        # ----------------------------------------------------

        knowledge_text = build_case_text(
            case_id=case_id,
            title=title,
            system_info=system_info,
            tags=tags,
            history=history,
            meter_models=meter_models,
            error_codes=error_codes,
            issue_category=issue_category,
            detected_system=detected_system,
            meter_type=meter_type,
        )

        # ----------------------------------------------------
        # RECORD
        # ----------------------------------------------------

        record = {

            "case_id": case_id,

            "title": title,

            "system_info": system_info,

            "tags": tags,

            "state": state,

            "assigned_to": assigned_to,

            "resolved_by": resolved_by,

            "history": history,

            "detected_meter_models": (
                "|".join(meter_models)
                if meter_models
                else "Unknown"
            ),

            "error_code": (
                "|".join(error_codes)
                if error_codes
                else "Unknown"
            ),

            "issue_category": issue_category,

            "classification_source": classification_source,

            "classification_source_details": json.dumps(
                classification_source_map,
                ensure_ascii=False
            ),

            "detected_system": detected_system,

            "system_source": system_source,

            "system_source_details": json.dumps(
                system_source_map,
                ensure_ascii=False
            ),

            "meter_type": meter_type,

            "meter_type_source": meter_type_source,

            "meter_type_source_details": json.dumps(
                meter_type_source_map,
                ensure_ascii=False
            ),

            "support_level": support_level,

            "support_level_source": support_level_source,

            "resolution_evidence": resolution_evidence,

            "resolution_source": resolution_source,

            "knowledge_text": knowledge_text,
        }

        records.append(record)

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    output_df = pd.DataFrame(records)

    # --------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------------

    output_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # SAVE JSONL
    # --------------------------------------------------------

    with open(
        OUTPUT_JSONL,
        "w",
        encoding="utf-8"
    ) as file:

        for record in records:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    # ========================================================
    # REPORT
    # ========================================================

    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)

    print(f"\nFinal records: {len(output_df)}")

    print("\nIssue categories:")

    print(
        output_df[
            "issue_category"
        ].value_counts()
    )

    print("\nClassification sources:")

    print(
        output_df[
            "classification_source"
        ].value_counts()
    )

    print("\nSystem sources:")

    print(
        output_df[
            "system_source"
        ].value_counts()
    )

    print("\nMeter type sources:")

    print(
        output_df[
            "meter_type_source"
        ].value_counts()
    )

    print("\nSupport level:")

    print(
        output_df[
            "support_level"
        ].value_counts()
    )

    # --------------------------------------------------------
    # EVIDENCE STATISTICS
    # --------------------------------------------------------

    history_count = (
        output_df["history"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    error_count = (
        output_df["error_code"]
        .ne("Unknown")
        .sum()
    )

    model_count = (
        output_df["detected_meter_models"]
        .ne("Unknown")
        .sum()
    )

    print("\nEvidence statistics:")

    print(
        f" - Cases with History: {history_count}"
    )

    print(
        f" - Cases with Error Code: {error_count}"
    )

    print(
        f" - Cases with Meter Model: {model_count}"
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print("\nOutput CSV:")
    print(OUTPUT_CSV)

    print("\nOutput JSONL:")
    print(OUTPUT_JSONL)

    print("\nIMPORTANT:")
    print(
        "No resolution or root cause was invented."
    )

    print(
        "Classification source is preserved for traceability."
    )

    print(
        "Unknown is used when there is insufficient evidence."
    )


if __name__ == "__main__":
    main()