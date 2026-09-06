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

try:

    print()
    print("STEP 3: METER ANALYTICS DATA")


    # Create meter analytics view

    cursor.execute("""
        DROP VIEW IF EXISTS meter_analytics;
    """)

    cursor.execute("""
        CREATE VIEW meter_analytics AS
        SELECT
            m.meter_id,
            m.meter_number,
            m.meter_type,
            m.firmware_id,
            m.hardware_revision,
            m.district,
            m.pos,

            COUNT(f.failure_id) AS total_failures,

            COUNT(
                CASE
                    WHEN f.case_severity = 'Critical'
                    THEN 1
                END
            ) AS critical_failures,

            COUNT(
                CASE
                    WHEN f.case_severity = 'Major'
                    THEN 1
                END
            ) AS major_failures,

            COUNT(
                CASE
                    WHEN f.case_severity = 'Minor'
                    THEN 1
                END
            ) AS minor_failures,

            MIN(f.reported_date) AS first_failure_date,
            MAX(f.reported_date) AS last_failure_date

        FROM meters m

        LEFT JOIN failures f
            ON m.meter_id = f.meter_id

        GROUP BY
            m.meter_id,
            m.meter_number,
            m.meter_type,
            m.firmware_id,
            m.hardware_revision,
            m.district,
            m.pos;
    """)

    connection.commit()

    print()
    print("Meter analytics view created successfully.")


    # Validate view

    cursor.execute("""
        SELECT COUNT(*)
        FROM meter_analytics;
    """)

    view_count = cursor.fetchone()[0]

    print()
    print("METER ANALYTICS VALIDATION")
    print("------------------------------------------")
    print("Meters available in analytics view:", view_count)


    # Show sample records

    cursor.execute("""
        SELECT
            meter_number,
            meter_type,
            district,
            pos,
            total_failures,
            critical_failures,
            major_failures,
            minor_failures,
            first_failure_date,
            last_failure_date
        FROM meter_analytics
        ORDER BY total_failures DESC
        LIMIT 10;
    """)

    rows = cursor.fetchall()

    print()
    print("SAMPLE METER ANALYTICS")

    for row in rows:

        print()
        print("Meter Number      :", row[0])
        print("Meter Type        :", row[1])
        print("District          :", row[2])
        print("POS               :", row[3])
        print("Total Failures    :", row[4])
        print("Critical Failures :", row[5])
        print("Major Failures    :", row[6])
        print("Minor Failures    :", row[7])
        print("First Failure     :", row[8])
        print("Last Failure      :", row[9])


    # Final check

    if view_count == 52912:

        print()
        print("METER ANALYTICS: READY")

    else:

        print()
        print("METER ANALYTICS: CHECK")


except Exception as e:

    connection.rollback()

    print()
    print("ERROR:", e)

finally:

    cursor.close()
    connection.close()

    print()
    print("DATABASE CONNECTION CLOSED")
    print("Done.")