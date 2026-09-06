import psycopg2


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


# Clear old failure records

cursor.execute("""
    TRUNCATE TABLE failures
    RESTART IDENTITY
    CASCADE;
""")

print("Previous failure records cleared.")


# Load SCDC cases into failures

insert_query = """
INSERT INTO failures (
    meter_id,
    case_type,
    case_category,
    case_severity,
    error_code,
    case_details,
    action_taken,
    status,
    action_owner,
    district,
    pos,
    source,
    reported_date,
    resolved_date
)
SELECT
    m.meter_id,
    n.case_type,
    n.case_category,
    n.case_severity,
    n.error_code,
    n.case_details,
    n.action_taken,
    n.status,
    n.action_owner,
    n.district,
    n.pos,
    'scdc_tracker',
    n.case_date,
    NULL
FROM normalized_scdc_cases n
LEFT JOIN meters m
    ON TRIM(m.meter_number) = TRIM(n.meter_number)
WHERE n.case_details IS NOT NULL
   OR n.error_code IS NOT NULL
   OR n.case_category IS NOT NULL
   OR n.case_type IS NOT NULL;
"""


cursor.execute(insert_query)

connection.commit()


# Validate failure data

cursor.execute("""
    SELECT COUNT(*)
    FROM failures;
""")

failure_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM failures
    WHERE source = 'scdc_tracker';
""")

scdc_failure_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM failures
    WHERE meter_id IS NOT NULL;
""")

linked_meter_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM failures
    WHERE meter_id IS NULL;
""")

unlinked_meter_count = cursor.fetchone()[0]


print()
print("FAILURE LOAD COMPLETED")
print("------------------------------------------")
print("Total failure records:", failure_count)
print("SCDC failure records:", scdc_failure_count)
print("Failures linked to meters:", linked_meter_count)
print("Failures without meter:", unlinked_meter_count)
print("------------------------------------------")


# Close connection

cursor.close()
connection.close()

print("Database connection closed.")
print("Done.")