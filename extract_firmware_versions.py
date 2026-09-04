import re
import psycopg2
from collections import Counter


# ==========================================================
# FIRMWARE VERSION EXTRACTION
# ==========================================================

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"


# ----------------------------------------------------------
# 1. Connect to database
# ----------------------------------------------------------

connection = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = connection.cursor()

print("Connected to the database successfully.")


# ----------------------------------------------------------
# 2. Get SCDC records that mention firmware
# ----------------------------------------------------------

query = """
    SELECT
        normalized_id,
        meter_number,
        case_details,
        action_taken,
        comment
    FROM normalized_scdc_cases
    WHERE
        LOWER(COALESCE(case_details, '')) LIKE '%firmware%'
        OR LOWER(COALESCE(action_taken, '')) LIKE '%firmware%'
        OR LOWER(COALESCE(comment, '')) LIKE '%firmware%'
"""

cursor.execute(query)

rows = cursor.fetchall()

print()
print("==========================================")
print("FIRMWARE VERSION EXTRACTION")
print("==========================================")
print("Records mentioning firmware:", len(rows))


# ----------------------------------------------------------
# 3. Search for firmware versions
# ----------------------------------------------------------

# Examples that this pattern can detect:
# V3.12
# V3.1
# v3.12
# Version 3.12
# Firmware 3.12
#
# We are ONLY extracting values that actually exist
# in the database. We are NOT creating any values ourselves.

version_pattern = re.compile(
    r'\b(?:firmware\s*(?:version)?|version|ver\.?)?\s*'
    r'(?:v\s*)?(\d+(?:\.\d+)+)\b',
    re.IGNORECASE
)


versions = Counter()
examples = []


# ----------------------------------------------------------
# 4. Process records
# ----------------------------------------------------------

for row in rows:

    normalized_id = row[0]
    meter_number = row[1]
    case_details = row[2] or ""
    action_taken = row[3] or ""
    comment = row[4] or ""

    combined_text = " ".join([
        str(case_details),
        str(action_taken),
        str(comment)
    ])

    matches = version_pattern.findall(combined_text)

    for version in matches:

        # Store normalized representation
        clean_version = "V" + version

        versions[clean_version] += 1

        if len(examples) < 30:
            examples.append(
                (
                    clean_version,
                    normalized_id,
                    meter_number,
                    combined_text
                )
            )


# ----------------------------------------------------------
# 5. Display extracted versions
# ----------------------------------------------------------

print()
print("==========================================")
print("EXTRACTED FIRMWARE VERSIONS")
print("==========================================")

if not versions:

    print("No firmware versions were detected.")

else:

    print("Unique firmware versions:", len(versions))
    print()

    for version, count in versions.most_common():

        print(
            f"{version} -> {count} occurrence(s)"
        )


# ----------------------------------------------------------
# 6. Display examples
# ----------------------------------------------------------

print()
print("==========================================")
print("EXAMPLES")
print("==========================================")

if not examples:

    print("No examples available.")

else:

    for version, record_id, meter, text in examples:

        print("------------------------------------------")
        print("Version:", version)
        print("Record ID:", record_id)
        print("Meter:", meter)
        print("Text:", text[:300])


# ----------------------------------------------------------
# 7. Close connection
# ----------------------------------------------------------

cursor.close()
connection.close()

print()
print("==========================================")
print("FIRMWARE EXTRACTION COMPLETED")
print("==========================================")
print("Database connection closed.")
print("Done.")