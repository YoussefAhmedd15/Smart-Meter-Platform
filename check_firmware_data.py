import psycopg2


# ==========================================================
# STEP 9: CHECK FIRMWARE DATA
# ==========================================================

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"


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
# 1. Check whether normalized SCDC contains firmware data
# ----------------------------------------------------------

print()
print("==========================================")
print("FIRMWARE DATA CHECK")
print("==========================================")


# Check columns in normalized_scdc_cases
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'normalized_scdc_cases'
    ORDER BY ordinal_position;
""")

columns = [row[0] for row in cursor.fetchall()]

print("Columns in normalized_scdc_cases:")
for column in columns:
    print("-", column)


# ----------------------------------------------------------
# 2. Check existing firmware records
# ----------------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM firmwares;
""")

firmware_count = cursor.fetchone()[0]

print()
print("Existing firmware records:", firmware_count)


# ----------------------------------------------------------
# 3. Check whether meter data currently contains firmware
# ----------------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM meters
    WHERE firmware_id IS NOT NULL;
""")

meters_with_firmware = cursor.fetchone()[0]

print("Meters linked to firmware:", meters_with_firmware)


# ----------------------------------------------------------
# 4. Check SCDC text fields for firmware-related values
# ----------------------------------------------------------

search_query = """
SELECT
    COUNT(*)
FROM normalized_scdc_cases
WHERE
    LOWER(COALESCE(case_details, '')) LIKE '%firmware%'
    OR LOWER(COALESCE(action_taken, '')) LIKE '%firmware%'
    OR LOWER(COALESCE(comment, '')) LIKE '%firmware%'
    OR LOWER(COALESCE(categories, '')) LIKE '%firmware%'
    OR LOWER(COALESCE(case_category, '')) LIKE '%firmware%';
"""

cursor.execute(search_query)

firmware_mentions = cursor.fetchone()[0]

print("SCDC records mentioning 'firmware':", firmware_mentions)


# ----------------------------------------------------------
# 5. Display some examples
# ----------------------------------------------------------

cursor.execute("""
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
LIMIT 20;
""")

rows = cursor.fetchall()

print()
print("Examples:")
print("------------------------------------------")

for row in rows:
    print(
        "ID:", row[0],
        "| Meter:", row[1],
        "| Details:", row[2],
        "| Action:", row[3],
        "| Comment:", row[4]
    )


# ----------------------------------------------------------
# 6. Close connection
# ----------------------------------------------------------

cursor.close()
connection.close()

print()
print("==========================================")
print("FIRMWARE DATA CHECK COMPLETED")
print("==========================================")
print("Database connection closed.")
print("Done.")