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
print("=" * 50)
print("DATABASE VALIDATION")
print("=" * 50)

# ----------------------------------------------------------
# 1. Check record counts in the main tables
# ----------------------------------------------------------

tables = [
    "raw_scdc_cases",
    "normalized_scdc_cases",
    "meters",
    "firmwares",
    "failures",
    "failure_fingerprints",
    "dev_bugs",
    "users",
    "test_cases",
    "test_case_steps",
    "test_executions",
    "test_step_results",
    "test_execution_logs"
]

print()
print("TABLE RECORD COUNTS")
print("-" * 50)

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]

    print(f"{table:<30} -> {count}")


# ----------------------------------------------------------
# 2. Check raw vs normalized SCDC
# ----------------------------------------------------------

print()
print("SCDC VALIDATION")
print("-" * 50)

cursor.execute("SELECT COUNT(*) FROM raw_scdc_cases")
raw_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM normalized_scdc_cases")
normalized_count = cursor.fetchone()[0]

print("Raw SCDC rows        :", raw_count)
print("Normalized SCDC rows :", normalized_count)

if raw_count == normalized_count:
    print("SCDC normalization   : OK")
else:
    print("SCDC normalization   : CHECK")


# ----------------------------------------------------------
# 3. Check meters
# ----------------------------------------------------------

print()
print("METER VALIDATION")
print("-" * 50)

cursor.execute("SELECT COUNT(*) FROM meters")
meter_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM meters m
    INNER JOIN normalized_scdc_cases s
        ON TRIM(m.meter_number) = TRIM(s.meter_number)
""")

matched_meter_records = cursor.fetchone()[0]

print("Meters in database           :", meter_count)
print("Matched SCDC meter records   :", matched_meter_records)


# ----------------------------------------------------------
# 4. Check failures
# ----------------------------------------------------------

print()
print("FAILURE VALIDATION")
print("-" * 50)

cursor.execute("SELECT COUNT(*) FROM failures")
failure_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM failures
    WHERE meter_id IS NOT NULL
""")

linked_failures = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM failures
    WHERE meter_id IS NULL
""")

unlinked_failures = cursor.fetchone()[0]

print("Total failures        :", failure_count)
print("Linked to meters      :", linked_failures)
print("Without meter         :", unlinked_failures)


# ----------------------------------------------------------
# 5. Check fingerprints
# ----------------------------------------------------------

print()
print("FINGERPRINT VALIDATION")
print("-" * 50)

cursor.execute("SELECT COUNT(*) FROM failure_fingerprints")
fingerprint_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT failure_id)
    FROM failure_fingerprints
""")

linked_fingerprints = cursor.fetchone()[0]

print("Failure fingerprints       :", fingerprint_count)
print("Failures with fingerprint  :", linked_fingerprints)

if failure_count == fingerprint_count:
    print("Fingerprint coverage       : OK")
else:
    print("Fingerprint coverage       : CHECK")


# ----------------------------------------------------------
# 6. Check duplicate meters
# ----------------------------------------------------------

print()
print("DUPLICATE CHECK")
print("-" * 50)

cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT meter_number
        FROM meters
        GROUP BY meter_number
        HAVING COUNT(*) > 1
    ) duplicates
""")

duplicate_meters = cursor.fetchone()[0]

print("Duplicate meter numbers :", duplicate_meters)


# ----------------------------------------------------------
# 7. Check duplicate ADO bugs
# ----------------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT ado_id
        FROM dev_bugs
        GROUP BY ado_id
        HAVING COUNT(*) > 1
    ) duplicates
""")

duplicate_bugs = cursor.fetchone()[0]

print("Duplicate ADO bugs      :", duplicate_bugs)


# ----------------------------------------------------------
# 8. Check users
# ----------------------------------------------------------

print()
print("USER VALIDATION")
print("-" * 50)

cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE email IS NULL
       OR TRIM(email) = ''
""")

users_without_email = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE role IS NULL
       OR TRIM(role) = ''
""")

users_without_role = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT LOWER(TRIM(email))
        FROM users
        GROUP BY LOWER(TRIM(email))
        HAVING COUNT(*) > 1
    ) duplicates
""")

duplicate_users = cursor.fetchone()[0]

print("Users in database       :", user_count)
print("Users without email    :", users_without_email)
print("Users without role     :", users_without_role)
print("Duplicate user emails  :", duplicate_users)


# ----------------------------------------------------------
# 9. Check foreign-key integrity
# ----------------------------------------------------------

print()
print("RELATIONSHIP VALIDATION")
print("-" * 50)

cursor.execute("""
    SELECT COUNT(*)
    FROM failures f
    LEFT JOIN meters m
        ON f.meter_id = m.meter_id
    WHERE f.meter_id IS NOT NULL
      AND m.meter_id IS NULL
""")

broken_failure_meter_links = cursor.fetchone()[0]

print("Broken failure -> meter links              :", broken_failure_meter_links)


cursor.execute("""
    SELECT COUNT(*)
    FROM failure_fingerprints fp
    LEFT JOIN failures f
        ON fp.failure_id = f.failure_id
    WHERE f.failure_id IS NULL
""")

broken_fingerprint_links = cursor.fetchone()[0]

print("Broken fingerprint -> failure links       :", broken_fingerprint_links)


cursor.execute("""
    SELECT COUNT(*)
    FROM test_cases tc
    LEFT JOIN users u
        ON tc.created_by = u.user_id
    WHERE tc.created_by IS NOT NULL
      AND u.user_id IS NULL
""")

broken_test_case_user_links = cursor.fetchone()[0]

print("Broken test_case -> user links             :", broken_test_case_user_links)


cursor.execute("""
    SELECT COUNT(*)
    FROM test_executions te
    LEFT JOIN users u
        ON te.executed_by = u.user_id
    WHERE te.executed_by IS NOT NULL
      AND u.user_id IS NULL
""")

broken_test_execution_user_links = cursor.fetchone()[0]

print("Broken test_execution -> user links       :", broken_test_execution_user_links)


# ----------------------------------------------------------
# 10. Final result
# ----------------------------------------------------------

print()
print("=" * 50)
print("DATABASE VALIDATION COMPLETED")
print("=" * 50)

if (
    raw_count == normalized_count
    and unlinked_failures == 99
    and duplicate_meters == 0
    and duplicate_bugs == 0
    and duplicate_users == 0
    and users_without_email == 0
    and users_without_role == 0
    and broken_failure_meter_links == 0
    and broken_fingerprint_links == 0
    and broken_test_case_user_links == 0
    and broken_test_execution_user_links == 0
    and failure_count == fingerprint_count
):
    print("DATABASE STATUS: READY")
else:
    print("DATABASE STATUS: CHECK RESULTS ABOVE")

print("=" * 50)

cursor.close()
connection.close()

print("Database connection closed.")
print("Done.")
