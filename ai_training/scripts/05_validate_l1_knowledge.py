import pandas as pd
import re
from pathlib import Path


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

OUTPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "evaluation"
    / "l1_validation_report.txt"
)


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize(text):
    text = clean(text).lower()

    text = re.sub(r"\s+", " ", text)

    return text


def contains_any(text, keywords):
    text = normalize(text)

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# ============================================================
# KEYWORDS
# ============================================================

SOFTWARE_KEYWORDS = [
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
]

HARDWARE_KEYWORDS = [
    "hardware",
    "display",
    "lcd",
    "relay",
    "battery",
    "pcb",
    "board",
    "button",
    "keypad",
]

FIRMWARE_KEYWORDS = [
    "firmware",
    "firm",
    "firmware update",
    "firmware upgrade",
    "fw update",
    "fw upgrade",
]

COMMUNICATION_KEYWORDS = [
    "communication",
    "communication error",
    "connection",
    "connectivity",
    "dlms",
    "hdlc",
    "serial",
    "optical",
]


# ============================================================
# EXPLICIT EVIDENCE
# ============================================================

def get_explicit_categories(row):

    categories = []

    title = normalize(row.get("title", ""))
    system_info = normalize(row.get("system_info", ""))
    tags = normalize(row.get("tags", ""))
    history = normalize(row.get("history", ""))

    sources = {
        "title": title,
        "system_info": system_info,
        "tag": tags,
        "history": history,
    }

    keyword_groups = {
        "Software": SOFTWARE_KEYWORDS,
        "Hardware": HARDWARE_KEYWORDS,
        "Firmware": FIRMWARE_KEYWORDS,
        "Communication": COMMUNICATION_KEYWORDS,
    }

    for category, keywords in keyword_groups.items():

        found = False

        for source_text in sources.values():

            if contains_any(source_text, keywords):
                found = True
                break

        if found:
            categories.append(category)

    return categories


# ============================================================
# VALIDATE ISSUE
# ============================================================

def validate_issue(row):

    predicted = clean(
        row.get("issue_category", "Unknown")
    )

    if predicted == "Unknown":
        return "UNKNOWN"

    predicted_categories = set(
        predicted.split("|")
    )

    explicit_categories = set(
        get_explicit_categories(row)
    )

    if not explicit_categories:
        return "NO_EVIDENCE"

    if predicted_categories.issubset(
        explicit_categories
    ):
        return "SUPPORTED"

    if predicted_categories.intersection(
        explicit_categories
    ):
        return "PARTIAL"

    return "POSSIBLE_CONFLICT"


# ============================================================
# VALIDATE SYSTEM
# ============================================================

def validate_system(row):

    system = clean(
        row.get("detected_system", "Unknown")
    )

    if system == "Unknown":
        return "UNKNOWN"

    source = clean(
        row.get("system_source", "unknown")
    )

    if source == "unknown":
        return "NO_EVIDENCE"

    return "SUPPORTED"


# ============================================================
# VALIDATE METER TYPE
# ============================================================

def validate_meter_type(row):

    meter_type = clean(
        row.get("meter_type", "Unknown")
    )

    if meter_type == "Unknown":
        return "UNKNOWN"

    source = clean(
        row.get("meter_type_source", "unknown")
    )

    if source == "unknown":
        return "NO_EVIDENCE"

    return "SUPPORTED"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ISKRA L1 KNOWLEDGE VALIDATION")
    print("=" * 70)

    print("\nInput:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():

        print("\nERROR: Knowledge dataset not found.")

        print(INPUT_FILE)

        return

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )

    print(f"\nTotal records: {len(df)}")

    report = []

    def log(text=""):

        print(text)

        report.append(text)

    # ========================================================
    # ISSUE VALIDATION
    # ========================================================

    log("\n" + "=" * 70)

    log("ISSUE CLASSIFICATION VALIDATION")

    log("=" * 70)

    df["issue_validation"] = df.apply(
        validate_issue,
        axis=1
    )

    issue_counts = (
        df["issue_validation"]
        .value_counts()
    )

    log("\nValidation results:")

    for status, count in issue_counts.items():

        percentage = (
            count / len(df) * 100
        )

        log(
            f" - {status}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # ========================================================
    # SYSTEM VALIDATION
    # ========================================================

    log("\n" + "=" * 70)

    log("SYSTEM VALIDATION")

    log("=" * 70)

    df["system_validation"] = df.apply(
        validate_system,
        axis=1
    )

    system_counts = (
        df["system_validation"]
        .value_counts()
    )

    for status, count in system_counts.items():

        percentage = (
            count / len(df) * 100
        )

        log(
            f" - {status}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # ========================================================
    # METER TYPE VALIDATION
    # ========================================================

    log("\n" + "=" * 70)

    log("METER TYPE VALIDATION")

    log("=" * 70)

    df["meter_type_validation"] = df.apply(
        validate_meter_type,
        axis=1
    )

    meter_counts = (
        df["meter_type_validation"]
        .value_counts()
    )

    for status, count in meter_counts.items():

        percentage = (
            count / len(df) * 100
        )

        log(
            f" - {status}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # ========================================================
    # CLASSIFICATION SOURCE
    # ========================================================

    log("\n" + "=" * 70)

    log("CLASSIFICATION SOURCE")

    log("=" * 70)

    source_counts = (
        df["classification_source"]
        .fillna("unknown")
        .value_counts()
    )

    for source, count in source_counts.items():

        percentage = (
            count / len(df) * 100
        )

        log(
            f" - {source}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # ========================================================
    # UNKNOWN CASES
    # ========================================================

    log("\n" + "=" * 70)

    log("UNKNOWN CASES")

    log("=" * 70)

    unknown_cases = df[
        df["issue_category"]
        .fillna("Unknown")
        .eq("Unknown")
    ]

    log(
        f"\nUnknown issue cases: "
        f"{len(unknown_cases)}"
    )

    for _, row in unknown_cases.iterrows():

        log(
            f"\nID: {clean(row.get('case_id'))}"
        )

        log(
            f"Title: {clean(row.get('title'))}"
        )

        log(
            f"Tags: {clean(row.get('tags'))}"
        )

        log(
            f"System Info: "
            f"{clean(row.get('system_info'))}"
        )

    # ========================================================
    # POSSIBLE CONFLICTS
    # ========================================================

    log("\n" + "=" * 70)

    log("POSSIBLE CLASSIFICATION CONFLICTS")

    log("=" * 70)

    conflicts = df[
        df["issue_validation"]
        .isin(
            [
                "POSSIBLE_CONFLICT",
                "PARTIAL",
            ]
        )
    ]

    log(
        f"\nCases requiring review: "
        f"{len(conflicts)}"
    )

    for _, row in conflicts.head(100).iterrows():

        log(
            f"\nID: {clean(row.get('case_id'))}"
        )

        log(
            f"Title: {clean(row.get('title'))}"
        )

        log(
            f"Tags: {clean(row.get('tags'))}"
        )

        log(
            f"Predicted: "
            f"{clean(row.get('issue_category'))}"
        )

        log(
            f"Source: "
            f"{clean(row.get('classification_source'))}"
        )

        log(
            f"Validation: "
            f"{clean(row.get('issue_validation'))}"
        )

    # ========================================================
    # SUPPORT LEVEL
    # ========================================================

    log("\n" + "=" * 70)

    log("SUPPORT LEVEL")

    log("=" * 70)

    support_counts = (
        df["support_level"]
        .fillna("Unknown")
        .value_counts()
    )

    for level, count in support_counts.items():

        log(
            f" - {level}: {count}"
        )

    # ========================================================
    # HISTORY / RESOLUTION
    # ========================================================

    log("\n" + "=" * 70)

    log("RESOLUTION EVIDENCE")

    log("=" * 70)

    history_available = (
        df["history"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    )

    history_count = history_available.sum()

    log(
        f"\nCases with actual History: "
        f"{history_count}"
    )

    log(
        f"Cases without History: "
        f"{len(df) - history_count}"
    )

    # ========================================================
    # READINESS
    # ========================================================

    log("\n" + "=" * 70)

    log("DATASET READINESS")

    log("=" * 70)

    supported = (
        df["issue_validation"]
        == "SUPPORTED"
    ).sum()

    conflicts_count = (
        df["issue_validation"]
        .isin(
            [
                "POSSIBLE_CONFLICT",
                "PARTIAL",
            ]
        )
        .sum()
    )

    unknown_count = (
        df["issue_validation"]
        == "UNKNOWN"
    ).sum()

    supported_percentage = (
        supported / len(df) * 100
    )

    log(
        f"\nIssue classifications fully supported: "
        f"{supported} "
        f"({supported_percentage:.2f}%)"
    )

    log(
        f"Cases requiring review: "
        f"{conflicts_count}"
    )

    log(
        f"Unknown cases: "
        f"{unknown_count}"
    )

    # ========================================================
    # FINAL RECOMMENDATION
    # ========================================================

    log("\n" + "=" * 70)

    log("RECOMMENDATION")

    log("=" * 70)

    log(
        "\nDo NOT fine-tune the model yet."
    )

    log(
        "Use this validation report to identify "
        "classification conflicts and improve the taxonomy."
    )

    log(
        "Do NOT invent root causes or resolutions "
        "for cases without evidence."
    )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\n" + "=" * 70)

    print("VALIDATION COMPLETE")

    print("=" * 70)

    print("\nReport saved to:")

    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()