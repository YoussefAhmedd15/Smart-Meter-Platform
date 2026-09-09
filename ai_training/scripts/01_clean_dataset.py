import pandas as pd
import re
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "ai_training" / "data" / "raw" / "L1_Created_2131.csv"
OUTPUT_FILE = BASE_DIR / "ai_training" / "data" / "cleaned" / "l1_cases_cleaned.csv"


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """Clean text without changing its meaning."""

    if pd.isna(value):
        return ""

    text = str(value)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Convert common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_title(value):
    """Create normalized version of title."""

    text = clean_text(value)

    # Lowercase only for normalized field
    text = text.lower()

    # Normalize separators
    text = re.sub(r"[-_/]+", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_error_codes(text):
    """Extract possible error codes without assuming their meaning."""

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
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            if match not in results:
                results.append(match)

    return results


def extract_meter_models(text):
    """Extract known meter model patterns only when explicitly present."""

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
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            normalized = match.upper()

            if normalized not in results:
                results.append(normalized)

    return results


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("ISKRA L1 Dataset Cleaning")
    print("=" * 60)

    print(f"\nInput:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():
        print("\nERROR: CSV file was not found.")
        print("Put L1_Created_2131.csv inside:")
        print(INPUT_FILE.parent)
        return

    # Read CSV
    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8",
        low_memory=False
    )

    print(f"\nOriginal rows: {len(df)}")
    print(f"Original columns: {len(df.columns)}")

    print("\nOriginal columns:")
    for column in df.columns:
        print(f" - {column}")

    # --------------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------------

    df = df.dropna(how="all")

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # Clean text columns
    # --------------------------------------------------------

    text_columns = [
        "Title",
        "System Info",
        "Tags",
        "State",
        "History"
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].apply(clean_text)

    # --------------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates()

    duplicates_removed = before_duplicates - len(df)

    # --------------------------------------------------------
    # Remove duplicate Case IDs if available
    # Keep first occurrence
    # --------------------------------------------------------

    if "Case ID" in df.columns:

        before_case_duplicates = len(df)

        df = df.drop_duplicates(
            subset=["Case ID"],
            keep="first"
        )

        case_duplicates_removed = (
            before_case_duplicates - len(df)
        )

    else:
        case_duplicates_removed = 0

    # --------------------------------------------------------
    # Create combined searchable text
    # --------------------------------------------------------

    available_text_columns = [
        column
        for column in [
            "Title",
            "System Info",
            "Tags",
            "History"
        ]
        if column in df.columns
    ]

    df["combined_text"] = (
        df[available_text_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .apply(clean_text)
    )

    # --------------------------------------------------------
    # Normalized title
    # --------------------------------------------------------

    if "Title" in df.columns:
        df["title_normalized"] = (
            df["Title"]
            .apply(normalize_title)
        )

    # --------------------------------------------------------
    # Extract possible error codes
    # --------------------------------------------------------

    df["detected_error_codes"] = (
        df["combined_text"]
        .apply(extract_error_codes)
        .apply(lambda x: "|".join(x))
    )

    # --------------------------------------------------------
    # Extract meter models
    # --------------------------------------------------------

    df["detected_meter_models"] = (
        df["combined_text"]
        .apply(extract_meter_models)
        .apply(lambda x: "|".join(x))
    )

    # --------------------------------------------------------
    # Add source information
    # --------------------------------------------------------

    df["source_file"] = INPUT_FILE.name

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)

    print(f"\nFinal rows: {len(df)}")
    print(f"Exact duplicates removed: {duplicates_removed}")
    print(f"Duplicate Case IDs removed: {case_duplicates_removed}")

    print("\nDetected meter models:")

    models = set()

    for values in df["detected_meter_models"]:
        if values:
            models.update(values.split("|"))

    for model in sorted(models):
        print(f" - {model}")

    print("\nOutput:")
    print(OUTPUT_FILE)

    print("\nIMPORTANT:")
    print("The original CSV was NOT modified.")


if __name__ == "__main__":
    main()