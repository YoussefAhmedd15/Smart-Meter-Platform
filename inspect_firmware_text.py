import psycopg2


# ==========================================================
# INSPECT FIRMWARE TEXT
# ==========================================================

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"


# ----------------------------------------------------------
# 1. Connect
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
# 2. Get firmware-related records
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
    ORDER BY normalized_id
    LIMIT 50
"""

cursor.execute(query)

rows = cursor.fetchall()


# ----------------------------------------------------------
# 3. Display records
# ----------------------------------------------------------

print()
print("==========================================")
print("FIRMWARE TEXT INSPECTION")
print("==========================================")

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


# ----------------------------------------------------------
# 4. Close
# ----------------------------------------------------------

cursor.close()
connection.close()

print()
print("==========================================")
print("FIRMWARE TEXT INSPECTION COMPLETED")
print("==========================================")
print("Database connection closed.")
print("Done.")