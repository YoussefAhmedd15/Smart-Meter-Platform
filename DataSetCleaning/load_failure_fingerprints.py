import os
import psycopg2
import re


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


# Clear old fingerprints

cursor.execute("""
    TRUNCATE TABLE failure_fingerprints
    RESTART IDENTITY CASCADE
""")

print("Previous fingerprint records cleared.")


# Get failures

query = """
    SELECT
        f.failure_id,
        f.meter_id,
        f.firmware_id,
        f.case_type,
        f.case_category,
        f.case_severity,
        f.error_code,
        f.case_details,
        f.action_taken,
        m.meter_type,
        m.hardware_revision
    FROM failures f
    LEFT JOIN meters m
        ON f.meter_id = m.meter_id
    WHERE f.source = 'scdc_tracker'
"""

cursor.execute(query)

rows = cursor.fetchall()

print()
print("FAILURE FINGERPRINT LOAD")
print("------------------------------------------")
print("Failures processed:", len(rows))


# Normalize text

def normalize_text(value):

    if value is None:
        return ""

    value = str(value).lower()

    value = re.sub(r'[^a-z0-9]+', ' ', value)

    value = re.sub(r'\s+', ' ', value)

    return value.strip()


# Insert fingerprints

insert_query = """
    INSERT INTO failure_fingerprints (
        failure_id,
        meter_model,
        firmware,
        hardware_revision,
        error_code,
        normalized_signature
    )
    VALUES (%s, %s, %s, %s, %s, %s)
"""

inserted = 0


for row in rows:

    (
        failure_id,
        meter_id,
        firmware_id,
        case_type,
        case_category,
        case_severity,
        error_code,
        case_details,
        action_taken,
        meter_type,
        hardware_revision
    ) = row

    signature_parts = [
        normalize_text(case_type),
        normalize_text(case_category),
        normalize_text(case_severity),
        normalize_text(error_code),
        normalize_text(case_details),
        normalize_text(action_taken)
    ]

    normalized_signature = " | ".join(
        part for part in signature_parts if part
    )

    cursor.execute(
        insert_query,
        (
            failure_id,
            meter_type,
            None,
            hardware_revision,
            normalize_text(error_code) or None,
            normalized_signature
        )
    )

    inserted += 1


# Save changes

connection.commit()


# Validate fingerprints

cursor.execute("""
    SELECT COUNT(*)
    FROM failure_fingerprints
""")

fingerprint_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM failure_fingerprints
    WHERE normalized_signature IS NOT NULL
      AND normalized_signature <> ''
""")

signature_count = cursor.fetchone()[0]


print()
print("FAILURE FINGERPRINT LOAD COMPLETED")
print("------------------------------------------")
print("Fingerprints inserted:", inserted)
print("Fingerprints in database:", fingerprint_count)
print("Records with normalized signature:", signature_count)


# Show examples

print()
print("FINGERPRINT EXAMPLES")


cursor.execute("""
    SELECT
        fingerprint_id,
        failure_id,
        meter_model,
        error_code,
        normalized_signature
    FROM failure_fingerprints
    ORDER BY fingerprint_id
    LIMIT 10
""")

examples = cursor.fetchall()

for row in examples:

    print("------------------------------------------")
    print("Fingerprint ID:", row[0])
    print("Failure ID:", row[1])
    print("Meter Model:", row[2])
    print("Error Code:", row[3])
    print("Signature:", row[4])


# Close connection

cursor.close()
connection.close()

print()
print("DATABASE CONNECTION CLOSED")
print("Done.")