import os
import psycopg2


# Data-engineering pipeline DB connection. PIPELINE_DB_PASSWORD is required
# (no hardcoded default) — see .env.example. The other values default to
# this pipeline's existing local settings but can be overridden the same way.
DB_HOST = os.getenv("PIPELINE_DB_HOST", "localhost")
DB_PORT = os.getenv("PIPELINE_DB_PORT", "5432")
DB_NAME = os.getenv("PIPELINE_DB_NAME", "scdc_intelligence")
DB_USER = os.getenv("PIPELINE_DB_USER", "postgres")
DB_PASSWORD = os.getenv("PIPELINE_DB_PASSWORD")
if not DB_PASSWORD:
    raise RuntimeError(
        "PIPELINE_DB_PASSWORD is not set. Set it before running this script "
        "(see .env.example) — there is no hardcoded default."
    )


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


# Get firmware-related records

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
    ORDER BY normalized_id
    LIMIT 50
"""

cursor.execute(query)

rows = cursor.fetchall()


# Show records

print()
print("FIRMWARE TEXT INSPECTION")
print("------------------------------------------")
print("Records displayed:", len(rows))

for row in rows:

    normalized_id = row[0]
    meter_number = row[1]
    case_details = row[2]
    action_taken = row[3]
    comment = row[4]

    print()
    print("------------------------------------------")
    print("Record ID:", normalized_id)
    print("Meter:", meter_number)
    print("Case Details:", case_details)
    print("Action Taken:", action_taken)
    print("Comment:", comment)


# Close connection

cursor.close()
connection.close()

print()
print("FIRMWARE TEXT INSPECTION COMPLETED")
print("------------------------------------------")
print("Database connection closed.")
print("Done.")