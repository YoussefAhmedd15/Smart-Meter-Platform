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

try:

    print()
    print("STEP 3: DEV BUGS ANALYTICS DATA")


    # Create dev bugs analytics view

    cursor.execute("""
        DROP VIEW IF EXISTS dev_bugs_analytics;
    """)

    cursor.execute("""
        CREATE VIEW dev_bugs_analytics AS
        SELECT
            bug_id,
            ado_id,
            work_item_type,
            title,
            assigned_to,
            created_by,
            state,
            tags,
            resolved_by,
            closed_by,
            resolved_date,
            closed_date,
            created_date,
            level,
            loaded_at,

            CASE
                WHEN level = 'L1' THEN 'Level 1'
                WHEN level = 'L2' THEN 'Level 2'
                ELSE 'Unknown'
            END AS bug_level_name,

            CASE
                WHEN state IS NOT NULL
                     AND LOWER(state) IN ('closed', 'done', 'resolved')
                THEN TRUE
                ELSE FALSE
            END AS is_resolved

        FROM dev_bugs;
    """)

    connection.commit()

    print()
    print("Dev bugs analytics view created successfully.")


    # Get total bugs

    cursor.execute("""
        SELECT COUNT(*)
        FROM dev_bugs_analytics;
    """)

    total_bugs = cursor.fetchone()[0]


    # Get L1 bugs

    cursor.execute("""
        SELECT COUNT(*)
        FROM dev_bugs_analytics
        WHERE level = 'L1';
    """)

    l1_bugs = cursor.fetchone()[0]


    # Get L2 bugs

    cursor.execute("""
        SELECT COUNT(*)
        FROM dev_bugs_analytics
        WHERE level = 'L2';
    """)

    l2_bugs = cursor.fetchone()[0]


    # Get resolved bugs

    cursor.execute("""
        SELECT COUNT(*)
        FROM dev_bugs_analytics
        WHERE is_resolved = TRUE;
    """)

    resolved_bugs = cursor.fetchone()[0]


    # Show validation

    print()
    print("DEV BUGS ANALYTICS VALIDATION")
    print("------------------------------------------")
    print("Total bugs available :", total_bugs)
    print("L1 bugs              :", l1_bugs)
    print("L2 bugs              :", l2_bugs)
    print("Resolved bugs        :", resolved_bugs)


    # Show sample records

    cursor.execute("""
        SELECT
            bug_id,
            ado_id,
            title,
            level,
            state,
            assigned_to,
            created_date
        FROM dev_bugs_analytics
        ORDER BY bug_id
        LIMIT 10;
    """)

    rows = cursor.fetchall()

    print()
    print("SAMPLE DEV BUG ANALYTICS")

    for row in rows:

        print()
        print("Bug ID        :", row[0])
        print("ADO ID        :", row[1])
        print("Title         :", row[2])
        print("Level         :", row[3])
        print("State         :", row[4])
        print("Assigned To   :", row[5])
        print("Created Date  :", row[6])


    # Final check

    if (
        total_bugs == 3507
        and l1_bugs + l2_bugs == total_bugs
    ):

        print()
        print("DEV BUGS ANALYTICS: READY")

    else:

        print()
        print("DEV BUGS ANALYTICS: CHECK")


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