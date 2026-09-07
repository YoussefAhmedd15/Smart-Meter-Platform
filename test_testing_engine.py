import os
import psycopg2
import bcrypt
from datetime import datetime


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
    print("=" * 50)
    print("TESTING ENGINE STORAGE TEST")
    print("=" * 50)


    # Get a meter

    cursor.execute("""
        SELECT meter_id, meter_number
        FROM meters
        LIMIT 1
    """)

    meter = cursor.fetchone()

    if not meter:
        raise Exception("No meter found in database.")

    meter_id = meter[0]
    meter_number = meter[1]

    print()
    print("Using meter:", meter_number)


    # Create test user

    test_email = "testing.engine@example.com"
    test_password = "TestPassword123!"
    test_role = "tester"

    password_hash = bcrypt.hashpw(
        test_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    cursor.execute("""
        INSERT INTO users (
            email,
            password_hash,
            role
        )
        VALUES (%s, %s, %s)
        RETURNING user_id
    """, (
        test_email,
        password_hash,
        test_role
    ))

    user_id = cursor.fetchone()[0]

    print("Temporary test user created:", user_id)


    # Create test case

    cursor.execute("""
        INSERT INTO test_cases (
            name,
            description,
            test_type,
            status,
            priority,
            version,
            expected_result,
            created_by,
            is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING test_case_id
    """, (
        "Database Storage Test",
        "Temporary test case used to verify Testing Engine database storage.",
        "Integration",
        "Active",
        "High",
        1,
        "Testing Engine data should be stored successfully.",
        user_id,
        True
    ))

    test_case_id = cursor.fetchone()[0]

    print("Test case created:", test_case_id)


    # Create test step

    cursor.execute("""
        INSERT INTO test_case_steps (
            test_case_id,
            step_number,
            name,
            action,
            description,
            expected_result,
            parameters
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING step_id
    """, (
        test_case_id,
        1,
        "Meter Connection Test",
        "CONNECT",
        "Testing Engine connects to the meter.",
        "Meter connection successful.",
        '{"test": true}'
    ))

    step_id = cursor.fetchone()[0]

    print("Test step created:", step_id)


    # Create test execution

    started_at = datetime.now()
    completed_at = datetime.now()

    cursor.execute("""
        INSERT INTO test_executions (
            test_case_id,
            meter_id,
            status,
            started_at,
            completed_at,
            duration_ms,
            executed_by
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING execution_id
    """, (
        test_case_id,
        meter_id,
        "PASSED",
        started_at,
        completed_at,
        250,
        user_id
    ))

    execution_id = cursor.fetchone()[0]

    print("Test execution created:", execution_id)


    # Store step result

    cursor.execute("""
        INSERT INTO test_step_results (
            execution_id,
            step_id,
            status,
            actual_result,
            expected_result,
            response_data,
            duration_ms
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        execution_id,
        step_id,
        "PASSED",
        "Meter connection successful.",
        "Meter connection successful.",
        '{"connected": true}',
        250
    ))

    print("Test step result stored.")


    # Store execution log

    cursor.execute("""
        INSERT INTO test_execution_logs (
            execution_id,
            step_id,
            log_level,
            message,
            request_data,
            response_data
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        execution_id,
        step_id,
        "INFO",
        "Testing Engine successfully connected to meter.",
        '{"action": "CONNECT"}',
        '{"status": "SUCCESS"}'
    ))

    print("Execution log stored.")

    connection.commit()


    # Validation

    cursor.execute("""
        SELECT COUNT(*)
        FROM test_cases
        WHERE test_case_id = %s
          AND created_by = %s
    """, (test_case_id, user_id))

    test_case_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM test_case_steps
        WHERE test_case_id = %s
    """, (test_case_id,))

    step_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM test_executions
        WHERE execution_id = %s
          AND executed_by = %s
    """, (execution_id, user_id))

    execution_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM test_step_results
        WHERE execution_id = %s
    """, (execution_id,))

    result_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM test_execution_logs
        WHERE execution_id = %s
    """, (execution_id,))

    log_count = cursor.fetchone()[0]


    print()
    print("=" * 50)
    print("TESTING ENGINE VALIDATION")
    print("=" * 50)

    print("Test cases stored       :", test_case_count)
    print("Test steps stored       :", step_count)
    print("Executions stored       :", execution_count)
    print("Step results stored     :", result_count)
    print("Execution logs stored   :", log_count)

    if (
        test_case_count == 1
        and step_count == 1
        and execution_count == 1
        and result_count == 1
        and log_count == 1
    ):
        print()
        print("TESTING ENGINE STORAGE: READY")
    else:
        print()
        print("TESTING ENGINE STORAGE: CHECK")


    # Remove test data

    cursor.execute("""
        DELETE FROM test_execution_logs
        WHERE execution_id = %s
    """, (execution_id,))

    cursor.execute("""
        DELETE FROM test_step_results
        WHERE execution_id = %s
    """, (execution_id,))

    cursor.execute("""
        DELETE FROM test_executions
        WHERE execution_id = %s
    """, (execution_id,))

    cursor.execute("""
        DELETE FROM test_case_steps
        WHERE step_id = %s
    """, (step_id,))

    cursor.execute("""
        DELETE FROM test_cases
        WHERE test_case_id = %s
    """, (test_case_id,))

    cursor.execute("""
        DELETE FROM users
        WHERE user_id = %s
    """, (user_id,))

    connection.commit()

    print()
    print("Temporary test data removed successfully.")

except Exception as e:

    connection.rollback()

    print()
    print("ERROR:", e)

finally:

    cursor.close()
    connection.close()

    print()
    print("=" * 50)
    print("DATABASE CONNECTION CLOSED")
    print("Done.")