import os
import pandas as pd
import psycopg2


DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"

FOLDER_PATH = "//"


connection = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = connection.cursor()

print("Connected to the database successfully.")


# Clean text values

def clean_value(value):

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none"]:
        return None

    return value


# Clean date values

def clean_date(value):

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none"]:
        return None

    try:
        return pd.to_datetime(value).to_pydatetime()

    except Exception:
        print("Warning: Could not parse date:", value)
        return None


# Load Azure DevOps bugs

print()
print("STEP 4: DEV_BUGS IMPORT")


# Read L1 CSV

l1_df = pd.read_csv(
    os.path.join(FOLDER_PATH, "../DataSet/L1_Created.csv")
)

print("L1 CSV loaded successfully.")
print("L1 rows:", len(l1_df))


# Read L2 CSV

l2_df = pd.read_csv(
    os.path.join(FOLDER_PATH, "../DataSet/L2_Soft.csv")
)

print("L2 CSV loaded successfully.")
print("L2 rows:", len(l2_df))


# Get existing bugs

cursor.execute(
    "SELECT ado_id FROM dev_bugs"
)

existing_ids = {
    row[0]
    for row in cursor.fetchall()
}


# Insert new L1 bugs

insert_l1_query = """
    INSERT INTO dev_bugs (
        ado_id,
        work_item_type,
        title,
        assigned_to,
        created_by,
        state,
        tags,
        resolved_by,
        closed_by,
        resolved_date,
        closed_date,
        created_date,
        level
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s
    )
"""

l1_inserted = 0
l1_skipped = 0


for index, row in l1_df.iterrows():

    bug_id = int(row["ID"])

    if bug_id in existing_ids:
        l1_skipped += 1
        continue

    values = (
        bug_id,
        clean_value(row["Work Item Type"]),
        clean_value(row["Title"]),
        clean_value(row["Assigned To"]),
        clean_value(row["Created By"]),
        clean_value(row["State"]),
        clean_value(row["Tags"]),
        clean_value(row["Resolved By"]),
        clean_value(row["Closed By"]),
        clean_date(row["Resolved Date"]),
        clean_date(row["Closed Date"]),
        clean_date(row["Created Date"]),
        "L1"
    )

    cursor.execute(
        insert_l1_query,
        values
    )

    existing_ids.add(bug_id)
    l1_inserted += 1


# Update or insert L2 bugs

update_l2_query = """
    UPDATE dev_bugs
    SET
        title = %s,
        state = %s,
        tags = %s,
        resolved_by = %s,
        resolved_date = %s,
        level = 'L2'
    WHERE ado_id = %s
"""

insert_l2_query = """
    INSERT INTO dev_bugs (
        ado_id,
        work_item_type,
        title,
        state,
        tags,
        resolved_by,
        resolved_date,
        level
    )
    VALUES (
        %s, %s, %s, %s,
        %s, %s, %s, %s
    )
"""

l2_updated = 0
l2_inserted = 0


for index, row in l2_df.iterrows():

    bug_id = int(row["ID"])

    if bug_id in existing_ids:

        values = (
            clean_value(row["Title"]),
            clean_value(row["State"]),
            clean_value(row["Tags"]),
            clean_value(row["Resolved By"]),
            clean_date(row["Resolved Date"]),
            bug_id
        )

        cursor.execute(
            update_l2_query,
            values
        )

        l2_updated += 1

    else:

        values = (
            bug_id,
            clean_value(row["Work Item Type"]),
            clean_value(row["Title"]),
            clean_value(row["State"]),
            clean_value(row["Tags"]),
            clean_value(row["Resolved By"]),
            clean_date(row["Resolved Date"]),
            "L2"
        )

        cursor.execute(
            insert_l2_query,
            values
        )

        existing_ids.add(bug_id)
        l2_inserted += 1


connection.commit()

print()
print("DEV_BUGS IMPORT COMPLETED")
print("------------------------------------------")
print("New L1 bugs inserted:", l1_inserted)
print("Existing L1 bugs skipped:", l1_skipped)
print("L2 bugs updated:", l2_updated)
print("New L2 bugs inserted:", l2_inserted)
print("------------------------------------------")


# Load SCDC files

print()
print("STEP 5: SCDC DATA IMPORT")


scdc_files = [
    (
        "SCDC_Tracker_2020.xlsx",
        "Data Container",
        2020
    ),
    (
        "SCDC_Tracker_2021.xlsx",
        "Data Container",
        2021
    ),
    (
        "SCDC_Tracker_2022.xlsx",
        "2022",
        2022
    ),
    (
        "SCDC_Tracker_2023.xlsx",
        "2023",
        2023
    ),
    (
        "SCDC_Tracker_2024.xlsx",
        "Sheet1",
        2024
    )
]


# Standardize SCDC columns

def standardize_scdc_columns(df):

    if "SCDC" in df.columns:
        df = df.rename(
            columns={
                "SCDC": "Account"
            }
        )

    useless_columns = [
        column
        for column in df.columns
        if str(column).startswith("Unnamed:")
    ]

    if useless_columns:
        df = df.drop(
            columns=useless_columns
        )

    return df


# Clean SCDC data

def clean_scdc_dataframe(df):

    df = standardize_scdc_columns(df)

    if "Categories" not in df.columns:
        df["Categories"] = None

    if "FM team member" not in df.columns:
        df["FM team member"] = None

    for column in df.columns:

        if column == "Date":
            continue

        df[column] = df[column].apply(
            clean_value
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    return df


# Read and clean each year

scdc_dataframes = []


for file_name, sheet_name, source_year in scdc_files:

    print()
    print("------------------------------------------")
    print("Processing:", file_name)
    print("Sheet:", sheet_name)
    print("------------------------------------------")

    file_path = os.path.join(
        FOLDER_PATH,
        file_name
    )

    if not os.path.exists(file_path):

        print(
            "ERROR: File not found:",
            file_path
        )

        continue

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name
    )

    print(
        "Original rows:",
        len(df)
    )

    df = clean_scdc_dataframe(df)

    before_duplicates = len(df)

    df = df.drop_duplicates(
        keep="first"
    )

    duplicates_removed = (
        before_duplicates - len(df)
    )

    print(
        "Exact duplicates removed:",
        duplicates_removed
    )

    print(
        "Clean rows:",
        len(df)
    )

    df["source_file"] = file_name
    df["source_year"] = source_year

    scdc_dataframes.append(df)


# Combine all years

if len(scdc_dataframes) == 0:

    raise Exception(
        "No SCDC files were loaded successfully."
    )


scdc_combined = pd.concat(
    scdc_dataframes,
    ignore_index=True
)

print()
print("------------------------------------------")
print(
    "Total cleaned SCDC rows:",
    len(scdc_combined)
)
print("------------------------------------------")


# Load SCDC into database

print()
print("STEP 6: LOAD raw_scdc_cases")


source_file_names = [
    file_name
    for file_name, sheet_name, source_year
    in scdc_files
]


# Delete old normalized data

delete_normalized_query = """
    DELETE FROM normalized_scdc_cases
    WHERE raw_id IN (
        SELECT raw_id
        FROM raw_scdc_cases
        WHERE source_file = %s
    )
"""


# Delete old raw data

delete_raw_query = """
    DELETE FROM raw_scdc_cases
    WHERE source_file = %s
"""


for source_file in source_file_names:

    cursor.execute(
        delete_normalized_query,
        (source_file,)
    )

    cursor.execute(
        delete_raw_query,
        (source_file,)
    )


connection.commit()


# Insert SCDC data

insert_scdc_query = """
    INSERT INTO raw_scdc_cases (
        source_file,
        source_year,
        account_or_scdc,
        district,
        pos,
        case_type,
        case_date,
        meter_number,
        meter_type,
        case_details,
        action_taken,
        error_code,
        categories,
        case_category,
        case_severity,
        status,
        action_owner,
        comment,
        fm_team_member
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    )
"""

scdc_inserted = 0


for index, row in scdc_combined.iterrows():

    case_date = None

    if pd.notna(row["Date"]):
        case_date = row["Date"].date()

    values = (
        clean_value(row["source_file"]),
        int(row["source_year"]),
        clean_value(row["Account"]),
        clean_value(row["District"]),
        clean_value(row["POS"]),
        clean_value(row["Case Type"]),
        case_date,
        clean_value(row["Meter Number / Customer Number"]),
        clean_value(row["Meter Type"]),
        clean_value(row["Case Details"]),
        clean_value(row["Action Taken"]),
        clean_value(row["Error Code"]),
        clean_value(row["Categories"]),
        clean_value(row["Case Category"]),
        clean_value(row["Case Severity"]),
        clean_value(row["Status"]),
        clean_value(row["Action Owner"]),
        clean_value(row["Comment"]),
        clean_value(row["FM team member"])
    )

    cursor.execute(
        insert_scdc_query,
        values
    )

    scdc_inserted += 1


connection.commit()


# Validate imported data

print()
print("IMPORT VALIDATION")


cursor.execute(
    "SELECT COUNT(*) FROM raw_scdc_cases"
)

database_scdc_count = cursor.fetchone()[0]


cursor.execute(
    "SELECT COUNT(*) FROM dev_bugs"
)

database_bug_count = cursor.fetchone()[0]


print(
    "SCDC rows inserted:",
    scdc_inserted
)

print(
    "SCDC rows currently in database:",
    database_scdc_count
)

print(
    "Dev bugs currently in database:",
    database_bug_count
)


# SCDC count by year

cursor.execute("""
    SELECT
        source_year,
        COUNT(*)
    FROM raw_scdc_cases
    GROUP BY source_year
    ORDER BY source_year
""")

year_counts = cursor.fetchall()

print()
print("SCDC rows by year:")

for year, count in year_counts:

    print(
        year,
        "->",
        count
    )


# Check SCDC data

print()
print("STEP 9: SCDC NORMALIZATION INSPECTION")


columns_to_check = [
    "account_or_scdc",
    "district",
    "pos",
    "case_type",
    "meter_type",
    "error_code",
    "categories",
    "case_category",
    "case_severity",
    "status"
]


for column in columns_to_check:

    print()
    print("------------------------------------------")
    print("COLUMN:", column)
    print("------------------------------------------")

    query = f"""
        SELECT
            {column},
            COUNT(*) AS record_count
        FROM raw_scdc_cases
        WHERE {column} IS NOT NULL
        GROUP BY {column}
        ORDER BY record_count DESC
        LIMIT 30
    """

    cursor.execute(query)

    results = cursor.fetchall()

    for value, count in results:

        print(
            repr(value),
            "->",
            count
        )


# Check NULL values

print()
print("NULL VALUE CHECK")


null_checks = [
    "account_or_scdc",
    "district",
    "pos",
    "case_type",
    "case_date",
    "meter_number",
    "meter_type",
    "case_details",
    "action_taken",
    "error_code",
    "case_category",
    "case_severity",
    "status"
]


for column in null_checks:

    query = f"""
        SELECT COUNT(*)
        FROM raw_scdc_cases
        WHERE {column} IS NULL
    """

    cursor.execute(query)

    null_count = cursor.fetchone()[0]

    print(
        column,
        "-> NULL:",
        null_count
    )


# Check text differences

print()
print("CASE / SPACE INCONSISTENCY CHECK")


for column in [
    "district",
    "pos",
    "case_type",
    "meter_type",
    "error_code",
    "case_category",
    "case_severity",
    "status"
]:

    query = f"""
        SELECT
            {column},
            LOWER(TRIM({column})) AS normalized_value,
            COUNT(*) AS count
        FROM raw_scdc_cases
        WHERE {column} IS NOT NULL
        GROUP BY
            {column},
            LOWER(TRIM({column}))
        HAVING COUNT(*) > 0
        ORDER BY normalized_value
        LIMIT 100
    """

    cursor.execute(query)

    results = cursor.fetchall()

    print()
    print("COLUMN:", column)

    for original, normalized, count in results:

        if str(original) != str(normalized):

            print(
                "Original:",
                repr(original),
                "| Normalized:",
                repr(normalized),
                "| Count:",
                count
            )


# Check duplicate meter numbers

print()
print("METER NUMBER DUPLICATE CHECK")


cursor.execute("""
    SELECT
        meter_number,
        COUNT(*) AS count
    FROM raw_scdc_cases
    WHERE meter_number IS NOT NULL
    GROUP BY meter_number
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 30
""")

results = cursor.fetchall()

for meter_number, count in results:

    print(
        repr(meter_number),
        "->",
        count
    )


print()
print("NORMALIZATION INSPECTION COMPLETED")


cursor.close()
connection.close()

print()
print("DATABASE CONNECTION CLOSED")
print("Done.")