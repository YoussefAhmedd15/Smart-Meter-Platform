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

try:

    print()
    print("=" * 60)
    print("STEP 3: FAILURE ANALYTICS DATA")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Create failure analytics view
    # --------------------------------------------------

    cursor.execute("""
        DROP VIEW IF EXISTS failure_analytics;
    """)

    cursor.execute("""
        CREATE VIEW failure_analytics AS
        SELECT
            f.failure_id,
            f.meter_id,
            m.meter_number,
            m.meter_type,
            m.district,
            m.pos,

            f.case_type,
            f.case_category,
            f.case_severity,
            f.error_code,
            f.status,

            f.reported_date,
            f.resolved_date,

            CASE
                WHEN f.resolved_date IS NOT NULL
                     AND f.reported_date IS NOT NULL
                THEN f.resolved_date - f.reported_date
                ELSE NULL
            END AS resolution_days,

            ff.fingerprint_id,
            ff.normalized_signature

        FROM failures f

        LEFT JOIN meters m
            ON f.meter_id = m.meter_id

        LEFT JOIN failure_fingerprints ff
            ON f.failure_id = ff.failure_id;
    """)

    connection.commit()

    print()
    print("Failure analytics view created successfully.")

    # --------------------------------------------------
    # 2. Validate total records
    # --------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM failure_analytics;
    """)

    failure_count = cursor.fetchone()[0]

    print()
    print("=" * 60)
    print("FAILURE ANALYTICS VALIDATION")
    print("=" * 60)

    print("Failures available in analytics view:", failure_count)

    # --------------------------------------------------
    # 3. Validate fingerprints
    # --------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM failure_analytics
        WHERE fingerprint_id IS NOT NULL;
    """)

    fingerprint_count = cursor.fetchone()[0]

    print("Failures with fingerprints:", fingerprint_count)

    # --------------------------------------------------
    # 4. Validate meter links
    # --------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM failure_analytics
        WHERE meter_id IS NOT NULL;
    """)

    linked_meter_count = cursor.fetchone()[0]

    print("Failures linked to meters:", linked_meter_count)

    # --------------------------------------------------
    # 5. Show sample records
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            failure_id,
            meter_number,
            meter_type,
            district,
            case_category,
            case_severity,
            error_code,
            status,
            reported_date,
            resolved_date,
            resolution_days
        FROM failure_analytics
        ORDER BY failure_id
        LIMIT 10;
    """)

    rows = cursor.fetchall()

    print()
    print("=" * 60)
    print("SAMPLE FAILURE ANALYTICS")
    print("=" * 60)

    for row in rows:

        print()
        print("Failure ID       :", row[0])
        print("Meter Number     :", row[1])
        print("Meter Type       :", row[2])
        print("District         :", row[3])
        print("Case Category    :", row[4])
        print("Case Severity    :", row[5])
        print("Error Code       :", row[6])
        print("Status           :", row[7])
        print("Reported Date    :", row[8])
        print("Resolved Date    :", row[9])
        print("Resolution Days  :", row[10])

    # --------------------------------------------------
    # 6. Final validation
    # --------------------------------------------------

    if (
        failure_count == 58341
        and fingerprint_count == 58341
    ):
        print()
        print("FAILURE ANALYTICS: READY")
    else:
        print()
        print("FAILURE ANALYTICS: CHECK")

except Exception as e:

    connection.rollback()

    print()
    print("ERROR:", e)

finally:

    cursor.close()
    connection.close()

    print()
    print("=" * 60)
    print("DATABASE CONNECTION CLOSED")
    print("=" * 60)
    print("Done.")