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
    / "l1_cases_structured.csv"
)

REPORT_FILE = (
    BASE_DIR
    / "ai_training"
    / "data"
    / "evaluation"
    / "l1_dataset_analysis.txt"
)


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ISKRA L1 DATASET QUALITY ANALYSIS")
    print("=" * 70)

    print(f"\nInput:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():
        print("\nERROR: Structured dataset not found.")
        return

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )

    report = []

    def log(text=""):
        print(text)
        report.append(text)

    log("=" * 70)
    log("ISKRA L1 DATASET QUALITY ANALYSIS")
    log("=" * 70)

    # ========================================================
    # BASIC INFO
    # ========================================================

    log("\nBASIC DATASET INFORMATION")
    log("-" * 70)

    log(f"Total cases: {len(df)}")
    log(f"Total columns: {len(df.columns)}")

    log("\nColumns:")

    for column in df.columns:
        log(f" - {column}")

    # ========================================================
    # MISSING DATA
    # ========================================================

    log("\nMISSING DATA ANALYSIS")
    log("-" * 70)

    missing = df.isna().sum()

    for column, count in missing.items():

        percentage = (
            count / len(df) * 100
            if len(df) > 0
            else 0
        )

        log(
            f"{column}: "
            f"{count} missing "
            f"({percentage:.2f}%)"
        )

    # ========================================================
    # SYSTEMS
    # ========================================================

    print_section("SYSTEM ANALYSIS")

    log("\nSYSTEM DISTRIBUTION")
    log("-" * 70)

    if "detected_system" in df.columns:

        system_counts = (
            df["detected_system"]
            .fillna("Unknown")
            .value_counts()
        )

        for system, count in system_counts.items():

            percentage = count / len(df) * 100

            log(
                f"{system}: "
                f"{count} "
                f"({percentage:.2f}%)"
            )

    # ========================================================
    # ISSUE CATEGORY
    # ========================================================

    print_section("ISSUE CATEGORY ANALYSIS")

    log("\nISSUE CATEGORY DISTRIBUTION")
    log("-" * 70)

    if "issue_category" in df.columns:

        category_counts = (
            df["issue_category"]
            .fillna("Unknown")
            .value_counts()
        )

        for category, count in category_counts.items():

            percentage = count / len(df) * 100

            log(
                f"{category}: "
                f"{count} "
                f"({percentage:.2f}%)"
            )

    # ========================================================
    # METER TYPES
    # ========================================================

    print_section("METER TYPE ANALYSIS")

    log("\nMETER TYPE DISTRIBUTION")
    log("-" * 70)

    if "meter_type" in df.columns:

        meter_counts = (
            df["meter_type"]
            .fillna("Unknown")
            .value_counts()
        )

        for meter_type, count in meter_counts.items():

            percentage = count / len(df) * 100

            log(
                f"{meter_type}: "
                f"{count} "
                f"({percentage:.2f}%)"
            )

    # ========================================================
    # METER MODELS
    # ========================================================

    print_section("METER MODEL ANALYSIS")

    log("\nMETER MODEL DISTRIBUTION")
    log("-" * 70)

    if "detected_meter_models" in df.columns:

        model_counts = {}

        for value in df["detected_meter_models"]:

            value = clean(value)

            if not value or value == "Unknown":
                continue

            for model in value.split("|"):

                model = model.strip()

                if model:
                    model_counts[model] = (
                        model_counts.get(model, 0) + 1
                    )

        for model, count in sorted(
            model_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ):

            log(f"{model}: {count}")

    # ========================================================
    # ERROR CODES
    # ========================================================

    print_section("ERROR CODE ANALYSIS")

    log("\nTOP ERROR CODES")
    log("-" * 70)

    if "error_code" in df.columns:

        error_counts = {}

        for value in df["error_code"]:

            value = clean(value)

            if not value or value == "Unknown":
                continue

            for code in value.split("|"):

                code = code.strip()

                if code:
                    error_counts[code] = (
                        error_counts.get(code, 0) + 1
                    )

        for code, count in sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:50]:

            log(f"Error {code}: {count}")

    # ========================================================
    # TAG ANALYSIS
    # ========================================================

    print_section("TAG ANALYSIS")

    log("\nTOP TAGS")
    log("-" * 70)

    if "Tags" in df.columns:

        tag_counts = {}

        for value in df["Tags"]:

            value = clean(value)

            if not value:
                continue

            # Handle common separators
            tags = re.split(r"[;,|]", value)

            for tag in tags:

                tag = tag.strip()

                if not tag:
                    continue

                tag_counts[tag] = (
                    tag_counts.get(tag, 0) + 1
                )

        for tag, count in sorted(
            tag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:50]:

            log(f"{tag}: {count}")

    # ========================================================
    # RESOLUTION AVAILABILITY
    # ========================================================

    print_section("RESOLUTION DATA ANALYSIS")

    log("\nRESOLUTION AVAILABILITY")
    log("-" * 70)

    if "resolution" in df.columns:

        resolution = (
            df["resolution"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        known = (
            (resolution != "")
            & (resolution.str.lower() != "unknown")
        )

        known_count = known.sum()
        unknown_count = len(df) - known_count

        log(f"Cases with resolution: {known_count}")
        log(f"Cases without resolution: {unknown_count}")

        if len(df) > 0:

            log(
                f"Resolution coverage: "
                f"{known_count / len(df) * 100:.2f}%"
            )

    # ========================================================
    # HISTORY ANALYSIS
    # ========================================================

    print_section("HISTORY ANALYSIS")

    log("\nHISTORY AVAILABILITY")
    log("-" * 70)

    if "History" in df.columns:

        history = (
            df["History"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        known_history = (
            (history != "")
            & (history.str.lower() != "nan")
        )

        history_count = known_history.sum()

        log(f"Cases with History: {history_count}")
        log(
            f"Cases without History: "
            f"{len(df) - history_count}"
        )

        if len(df) > 0:

            log(
                f"History coverage: "
                f"{history_count / len(df) * 100:.2f}%"
            )

    # ========================================================
    # ESCALATION
    # ========================================================

    print_section("SUPPORT LEVEL ANALYSIS")

    log("\nSUPPORT LEVEL DISTRIBUTION")
    log("-" * 70)

    if "support_level" in df.columns:

        support_counts = (
            df["support_level"]
            .fillna("Unknown")
            .value_counts()
        )

        for level, count in support_counts.items():

            percentage = count / len(df) * 100

            log(
                f"{level}: "
                f"{count} "
                f"({percentage:.2f}%)"
            )

    # ========================================================
    # EXAMPLES
    # ========================================================

    print_section("SAMPLE CASES")

    log("\nEXAMPLES BY ISSUE CATEGORY")
    log("-" * 70)

    if "issue_category" in df.columns:

        for category in df["issue_category"].dropna().unique():

            sample = df[
                df["issue_category"] == category
            ].head(3)

            log(f"\n[{category}]")

            for _, row in sample.iterrows():

                case_id = clean(
                    row.get("ID", "Unknown")
                )

                title = clean(
                    row.get("Title", "")
                )

                system = clean(
                    row.get("detected_system", "Unknown")
                )

                model = clean(
                    row.get(
                        "detected_meter_models",
                        "Unknown"
                    )
                )

                error = clean(
                    row.get(
                        "error_code",
                        "Unknown"
                    )
                )

                log(
                    f"ID: {case_id} | "
                    f"Title: {title} | "
                    f"System: {system} | "
                    f"Model: {model} | "
                    f"Error: {error}"
                )

    # ========================================================
    # DATASET READINESS
    # ========================================================

    print_section("DATASET READINESS")

    log("\nINITIAL ASSESSMENT")
    log("-" * 70)

    warnings = []

    if "meter_type" in df.columns:

        unknown_meter = (
            df["meter_type"]
            .fillna("Unknown")
            .eq("Unknown")
            .sum()
        )

        if unknown_meter > len(df) * 0.5:

            warnings.append(
                "High percentage of Unknown meter types."
            )

    if "detected_system" in df.columns:

        unknown_system = (
            df["detected_system"]
            .fillna("Unknown")
            .eq("Unknown")
            .sum()
        )

        if unknown_system > len(df) * 0.5:

            warnings.append(
                "High percentage of Unknown systems."
            )

    if "resolution" in df.columns:

        unknown_resolution = (
            df["resolution"]
            .fillna("Unknown")
            .eq("Unknown")
            .sum()
        )

        if unknown_resolution > len(df) * 0.5:

            warnings.append(
                "Most cases do not have explicit resolutions."
            )

    if warnings:

        log("\nWARNINGS:")

        for warning in warnings:
            log(f" - {warning}")

    else:

        log("\nNo major automatic warnings detected.")

    log("\nRECOMMENDATION:")
    log(
        "Do NOT fine-tune the model yet. "
        "First validate labels and extract reliable "
        "L1 knowledge from the source cases."
    )

    # ========================================================
    # SAVE REPORT
    # ========================================================

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    print(f"\nReport saved to:")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()