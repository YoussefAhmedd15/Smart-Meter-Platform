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
    print("FIRMWARE DATA FINAL CONFIRMATION")


    # Check firmware table

    cursor.execute("""
        SELECT COUNT(*)
        FROM firmwares
    """)

    firmware_count = cursor.fetchone()[0]

    print()
    print("Firmware records currently stored:", firmware_count)


    # Count firmware mentions

    cursor.execute("""
        SELECT COUNT(*)
        FROM normalized_scdc_cases
        WHERE
            LOWER(COALESCE(case_details, '')) LIKE '%firmware%'
            OR LOWER(COALESCE(action_taken, '')) LIKE '%firmware%'
            OR LOWER(COALESCE(comment, '')) LIKE '%firmware%'
    """)

    firmware_mentions = cursor.fetchone()[0]

    print("SCDC records mentioning firmware:", firmware_mentions)


    # Show examples

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
        LIMIT 10
    """)

    examples = cursor.fetchall()

    print()
    print("FIRMWARE MENTION EXAMPLES")

    for row in examples:

        normalized_id = row[0]
        meter_number = row[1]
        case_details = row[2]
        action_taken = row[3]
        comment = row[4]

        print()
        print("ID:", normalized_id)
        print("Meter:", meter_number)
        print("Details:", case_details)
        print("Action:", action_taken)
        print("Comment:", comment)


    # Check firmware versions

    cursor.execute("""
        SELECT version
        FROM firmwares
        ORDER BY firmware_id
    """)

    firmware_versions = cursor.fetchall()

    print()
    print("FIRMWARE VERSION CHECK")

    if firmware_versions:

        print("Firmware versions found:")

        for version in firmware_versions:
            print("-", version[0])

        print()
        print("FIRMWARE DATA: AVAILABLE")

    else:

        print("No firmware versions stored.")
        print()
        print("FIRMWARE DATA: NOT AVAILABLE IN CURRENT SOURCE")


    # Final firmware status

    print()
    print("FINAL FIRMWARE STATUS")

    if firmware_count == 0 and firmware_mentions > 0:

        print("Firmware mentions exist in SCDC data.")
        print("However, no valid firmware versions are available.")
        print()
        print("Firmware table remains ready for future data.")
        print("No artificial firmware versions were inserted.")
        print()
        print("FIRMWARE STRUCTURE: READY")
        print("FIRMWARE SOURCE DATA: NOT AVAILABLE")

    elif firmware_count > 0:

        print("Valid firmware records exist.")
        print()
        print("FIRMWARE STRUCTURE: READY")
        print("FIRMWARE DATA: AVAILABLE")

    else:

        print("No firmware records or firmware mentions found.")
        print()
        print("FIRMWARE STRUCTURE: READY")
        print("FIRMWARE SOURCE DATA: NOT AVAILABLE")


    print()
    print("FIRMWARE CONFIRMATION COMPLETED")


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