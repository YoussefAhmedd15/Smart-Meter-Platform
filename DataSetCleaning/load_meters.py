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


# Clear old meter records

cursor.execute("""
    TRUNCATE TABLE meters
    RESTART IDENTITY
    CASCADE;
""")

print("Previous meter records cleared.")


# Create meter profiles

insert_query = """
INSERT INTO meters (
    meter_number,
    meter_type,
    district,
    pos
)
SELECT
    meter_number,
    MAX(meter_type) AS meter_type,
    MAX(district) AS district,
    MAX(pos) AS pos
FROM normalized_scdc_cases
WHERE meter_number IS NOT NULL
  AND TRIM(meter_number) <> ''
GROUP BY meter_number
ON CONFLICT (meter_number)
DO UPDATE SET
    meter_type = EXCLUDED.meter_type,
    district = EXCLUDED.district,
    pos = EXCLUDED.pos;
"""


cursor.execute(insert_query)

connection.commit()


# Validate meter data

cursor.execute("""
    SELECT COUNT(*)
    FROM meters;
""")

meter_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(DISTINCT meter_number)
    FROM normalized_scdc_cases
    WHERE meter_number IS NOT NULL
      AND TRIM(meter_number) <> '';
""")

unique_source_meters = cursor.fetchone()[0]


print()
print("METERS LOAD COMPLETED")
print("------------------------------------------")
print("Unique meters in SCDC:", unique_source_meters)
print("Meters in database:", meter_count)
print("------------------------------------------")


# Close connection

cursor.close()
connection.close()

print("Database connection closed.")
print("Done.")