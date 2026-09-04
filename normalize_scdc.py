import psycopg2


# ==========================================================
# NORMALIZE SCDC DATA
# ==========================================================

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"


# ----------------------------------------------------------
# 1. Connect to PostgreSQL
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
# 2. Clear previous normalized data
# ----------------------------------------------------------

cursor.execute("""
    TRUNCATE TABLE normalized_scdc_cases
    RESTART IDENTITY
    CASCADE;
""")

print("Previous normalized data cleared.")


# ----------------------------------------------------------
# 3. Insert normalized data
#
# IMPORTANT:
# PostgreSQL case_date is DATE.
# raw_scdc_cases.case_date is TEXT.
#
# We convert the text date using PostgreSQL TO_DATE().
# ----------------------------------------------------------

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


# ----------------------------------------------------------
# 4. Execute normalization
# ----------------------------------------------------------

cursor.execute(insert_query)

connection.commit()


# ----------------------------------------------------------
# 5. Validation
# ----------------------------------------------------------

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
print("==========================================")
print("NORMALIZATION COMPLETED")
print("==========================================")
print("Raw SCDC rows:", raw_count)
print("Normalized SCDC rows:", normalized_count)
print("==========================================")


# ----------------------------------------------------------
# 6. Close connection
# ----------------------------------------------------------

cursor.close()
connection.close()

print("Database connection closed.")
print("Done.")