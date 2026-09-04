import psycopg2

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

print()
print("==========================================")
print("FAILURE FINGERPRINT VALIDATION")
print("==========================================")

# 1. Count fingerprints
cursor.execute("""
    SELECT COUNT(*)
    FROM failure_fingerprints
""")

fingerprint_count = cursor.fetchone()[0]

# 2. Count failures
cursor.execute("""
    SELECT COUNT(*)
    FROM failures
""")

failure_count = cursor.fetchone()[0]

# 3. Check fingerprints linked to failures
cursor.execute("""
    SELECT COUNT(*)
    FROM failure_fingerprints ff
    JOIN failures f
        ON ff.failure_id = f.failure_id
""")

linked_count = cursor.fetchone()[0]

# 4. Check missing fingerprints
cursor.execute("""
    SELECT COUNT(*)
    FROM failures f
    LEFT JOIN failure_fingerprints ff
        ON f.failure_id = ff.failure_id
    WHERE ff.failure_id IS NULL
""")

missing_count = cursor.fetchone()[0]

print("Failures in database:", failure_count)
print("Fingerprints in database:", fingerprint_count)
print("Fingerprints linked to failures:", linked_count)
print("Failures without fingerprint:", missing_count)

print()
print("==========================================")
print("SAMPLE FINGERPRINTS")
print("==========================================")

cursor.execute("""
    SELECT
        ff.fingerprint_id,
        ff.failure_id,
        ff.meter_model,
        ff.firmware,
        ff.hardware_revision,
        ff.error_code,
        ff.normalized_signature
    FROM failure_fingerprints ff
    ORDER BY ff.fingerprint_id
    LIMIT 10
""")

rows = cursor.fetchall()

for row in rows:
    print("------------------------------------------")
    print("Fingerprint ID:", row[0])
    print("Failure ID:", row[1])
    print("Meter Model:", row[2])
    print("Firmware:", row[3])
    print("Hardware Revision:", row[4])
    print("Error Code:", row[5])
    print("Signature:", row[6])

print()
print("==========================================")
print("FINGERPRINT VALIDATION COMPLETED")
print("==========================================")

cursor.close()
connection.close()

print("Database connection closed.")
print("Done.")