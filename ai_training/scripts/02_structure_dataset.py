import pandas as pd
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "cleaned"
    / "l1_cases_cleaned.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "structured"
    / "l1_cases_structured.csv"
)


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def detect_system(text):
    text = text.lower()

    systems = {
        "Billing": ["billing"],
        "Symbiot": ["symbiot"],
        "Vending": ["vending"],
        "MeterVerse": ["meterverse"],
        "Aqua": ["aqua"],
        "Electric": ["electric"]
    }

    detected = []

    for system, keywords in systems.items():
        if any(keyword in text for keyword in keywords):
            detected.append(system)

    return "|".join(detected) if detected else "Unknown"


def detect_issue_category(text):
    text = text.lower()

    rules = {
        "Firmware": [
            "firmware",
            "fw",
            "firm",
            "upgrade firmware",
            "firmware update"
        ],
        "Hardware": [
            "hardware",
            "display",
            "lcd",
            "relay",
            "battery",
            "board",
            "pcb"
        ],
        "Communication": [
            "communication",
            "communication error",
            "connection",
            "connect",
            "dlms",
            "hdlc",
            "serial",
            "optical"
        ],
        "Software": [
            "software",
            "application",
            "system",
            "program",
            "login",
            "interface"
        ],
        "Configuration": [
            "configuration",
            "config",
            "parameter",
            "setting"
        ],
        "Testing": [
            "test",
            "testing",
            "test case",
            "validation"
        ]
    }

    for category, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "Unknown"


def detect_meter_type(text):
    text = text.lower()

    if "water" in text or "aqua" in text or "ultrasonic" in text:
        if "ultrasonic" in text:
            return "Ultrasonic"
        return "Water"

    if "electric" in text or "electricity" in text:
        return "Electric"

    return "Unknown"


def detect_support_level(text):
    text = text.lower()

    if "l2 software" in text:
        return "L2 Software"

    if "l2 hardware" in text:
        return "L2 Hardware"

    if "l2 firmware" in text:
        return "L2 Firmware"

    return "L1"


def extract_error_code(text):
    patterns = [
        r"\berror\s*[-:#]?\s*(\d+)\b",
        r"\berr\s*[-:#]?\s*(\d+)\b",
        r"\be[- ]?(\d+)\b"
    ]

    codes = []

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match in matches:
            if match not in codes:
                codes.append(match)

    return "|".join(codes) if codes else "Unknown"


def main():

    print("=" * 60)
    print("ISKRA L1 Dataset Structuring")
    print("=" * 60)

    print(f"\nInput:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():
        print("\nERROR: Cleaned dataset not found.")
        return

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )

    print(f"\nInput rows: {len(df)}")

    # Make sure combined text exists
    if "combined_text" not in df.columns:

        text_columns = [
            "Title",
            "System Info",
            "Tags",
            "History"
        ]

        available = [
            c for c in text_columns
            if c in df.columns
        ]

        df["combined_text"] = (
            df[available]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
        )

    df["case_text"] = df["combined_text"].apply(safe_text)

    # --------------------------------------------------
    # Detect system
    # --------------------------------------------------

    df["detected_system"] = (
        df["case_text"]
        .apply(detect_system)
    )

    # --------------------------------------------------
    # Detect issue category
    # --------------------------------------------------

    df["issue_category"] = (
        df["case_text"]
        .apply(detect_issue_category)
    )

    # --------------------------------------------------
    # Detect meter type
    # --------------------------------------------------

    df["meter_type"] = (
        df["case_text"]
        .apply(detect_meter_type)
    )

    # --------------------------------------------------
    # Support level
    # --------------------------------------------------

    df["support_level"] = (
        df["case_text"]
        .apply(detect_support_level)
    )

    # --------------------------------------------------
    # Error code
    # --------------------------------------------------

    df["error_code"] = (
        df["case_text"]
        .apply(extract_error_code)
    )

    # --------------------------------------------------
    # Keep explicit model detection
    # --------------------------------------------------

    if "detected_meter_models" not in df.columns:
        df["detected_meter_models"] = "Unknown"

    df["detected_meter_models"] = (
        df["detected_meter_models"]
        .replace("", "Unknown")
    )

    # --------------------------------------------------
    # Resolution
    # --------------------------------------------------

    # We DO NOT invent resolutions.
    df["resolution"] = "Unknown"

    # --------------------------------------------------
    # Root cause
    # --------------------------------------------------

    # We DO NOT invent root causes.
    df["root_cause"] = "Unknown"

    # --------------------------------------------------
    # Confidence
    # --------------------------------------------------

    df["classification_confidence"] = "Rule-based"

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 60)
    print("STRUCTURING COMPLETE")
    print("=" * 60)

    print(f"\nFinal rows: {len(df)}")

    print("\nIssue categories:")
    print(df["issue_category"].value_counts())

    print("\nSystems:")
    print(df["detected_system"].value_counts())

    print("\nMeter types:")
    print(df["meter_type"].value_counts())

    print("\nOutput:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()