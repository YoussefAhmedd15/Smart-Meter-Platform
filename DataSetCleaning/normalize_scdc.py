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


# Clear old normalized data

cursor.execute("""
    TRUNCATE TABLE normalized_scdc_cases
    RESTART IDENTITY
    CASCADE;
""")

print("Previous normalized data cleared.")


# Normalize and insert SCDC data

insert_query = """
INSERT INTO normalized_scdc_cases (
    raw_id,
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
SELECT
    raw_id,
    source_file,
    source_year,

    NULLIF(LOWER(TRIM(account_or_scdc)), ''),
    NULLIF(LOWER(TRIM(district)), ''),
    NULLIF(LOWER(TRIM(pos)), ''),
    NULLIF(LOWER(TRIM(case_type)), ''),

    CASE
        WHEN case_date IS NULL OR TRIM(case_date) = ''
        THEN NULL

        WHEN case_date ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
        THEN TO_DATE(TRIM(case_date), 'MM/DD/YYYY')

        WHEN case_date ~ '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
        THEN TO_DATE(TRIM(case_date), 'YYYY-MM-DD')

        ELSE NULL
    END,

    NULLIF(TRIM(meter_number), ''),
    NULLIF(LOWER(TRIM(meter_type)), ''),

    NULLIF(TRIM(case_details), ''),
    NULLIF(TRIM(action_taken), ''),
    NULLIF(UPPER(TRIM(error_code)), ''),

    NULLIF(LOWER(TRIM(categories)), ''),
    NULLIF(LOWER(TRIM(case_category)), ''),
    NULLIF(LOWER(TRIM(case_severity)), ''),
    NULLIF(LOWER(TRIM(status)), ''),

    NULLIF(TRIM(action_owner), ''),
    NULLIF(TRIM(comment), ''),
    NULLIF(TRIM(fm_team_member), '')

FROM raw_scdc_cases;
"""


cursor.execute(insert_query)

connection.commit()


# Validate data

cursor.execute("""
    SELECT COUNT(*)
    FROM normalized_scdc_cases;
""")

normalized_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM raw_scdc_cases;
""")

raw_count = cursor.fetchone()[0]


print()
print("NORMALIZATION COMPLETED")
print("------------------------------------------")
print("Raw SCDC rows:", raw_count)
print("Normalized SCDC rows:", normalized_count)
print("------------------------------------------")


# Close connection

cursor.close()
connection.close()

print("Database connection closed.")
print("Done.")