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


# Find unmatched SCDC meters

query = """
SELECT
    n.normalized_id,
    n.raw_id,
    n.meter_number,
    n.meter_type,
    n.case_type,
    n.case_category,
    n.error_code,
    n.source_year
FROM normalized_scdc_cases n
LEFT JOIN meters m
    ON TRIM(m.meter_number) = TRIM(n.meter_number)
WHERE n.meter_number IS NOT NULL
  AND TRIM(n.meter_number) <> ''
  AND m.meter_id IS NULL
ORDER BY n.source_year, n.normalized_id;
"""

cursor.execute(query)

rows = cursor.fetchall()


# Show results

print()
print("UNMATCHED METER CHECK")
print("------------------------------------------")
print("Unmatched records:", len(rows))
print("------------------------------------------")


for row in rows:

    print(
        "normalized_id:", row[0],
        "| raw_id:", row[1],
        "| meter_number:", repr(row[2]),
        "| meter_type:", repr(row[3]),
        "| case_type:", repr(row[4]),
        "| category:", repr(row[5]),
        "| error_code:", repr(row[6]),
        "| year:", row[7]
    )


# Close connection

cursor.close()
connection.close()

print()
print("Database connection closed.")
print("Done.")