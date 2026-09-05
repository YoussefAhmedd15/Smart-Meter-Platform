import re
import psycopg2
from collections import Counter


DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"


# Connect to database

connection = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = connection.cursor()

print("Connected to the database successfully.")


# Get records that mention firmware

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
print("FIRMWARE VERSION EXTRACTION")
print("------------------------------------------")
print("Records mentioning firmware:", len(rows))


# Find firmware versions

version_pattern = re.compile(
    r'\b(?:firmware\s*(?:version)?|version|ver\.?)?\s*'
    r'(?:v\s*)?(\d+(?:\.\d+)+)\b',
    re.IGNORECASE
)


versions = Counter()
examples = []


# Process records

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


# Show extracted versions

print()
print("EXTRACTED FIRMWARE VERSIONS")
print("------------------------------------------")

if not versions:

    print("No firmware versions were detected.")

else:

    print("Unique firmware versions:", len(versions))
    print()

    for version, count in versions.most_common():

        print(
            f"{version} -> {count} occurrence(s)"
        )


# Show examples

print()
print("EXAMPLES")
print("------------------------------------------")

if not examples:

    print("No examples available.")

else:

    for version, record_id, meter, text in examples:

        print("------------------------------------------")
        print("Version:", version)
        print("Record ID:", record_id)
        print("Meter:", meter)
        print("Text:", text[:300])


# Close connection

cursor.close()
connection.close()

print()
print("FIRMWARE EXTRACTION COMPLETED")
print("------------------------------------------")
print("Database connection closed.")
print("Done.")