import psycopg2
import bcrypt
import secrets
import hashlib


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

print("Connected to PostgreSQL successfully.")


# Password functions

def hash_password(password):
    if not password:
        raise ValueError("Password cannot be empty.")

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, password_hash):
    if not password or not password_hash:
        return False

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


# Token functions

def generate_token():
    return secrets.token_urlsafe(32)


def hash_token(token):
    if not token:
        raise ValueError("Token cannot be empty.")

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def verify_token(token, token_hash):
    if not token or not token_hash:
        return False

    return hash_token(token) == token_hash


# Create user

def create_user(email, password, role):

    if not email or not email.strip():
        raise ValueError("Email cannot be empty.")

    if not password:
        raise ValueError("Password cannot be empty.")

    if not role or not role.strip():
        raise ValueError("Role cannot be empty.")

    email = email.strip().lower()
    role = role.strip().lower()

    password_hash = hash_password(password)

    token = generate_token()
    token_hash = hash_token(token)

    try:
        cursor.execute(
            """
            INSERT INTO users (
                email,
                password_hash,
                role,
                api_token_hash
            )
            VALUES (%s, %s, %s, %s)
            RETURNING user_id;
            """,
            (
                email,
                password_hash,
                role,
                token_hash
            )
        )

        user_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "user_id": user_id,
            "email": email,
            "role": role,
            "token": token
        }

    except psycopg2.errors.UniqueViolation:
        connection.rollback()
        raise ValueError("A user with this email already exists.")


# Get user

def get_user_by_email(email):

    if not email:
        return None

    email = email.strip().lower()

    cursor.execute(
        """
        SELECT
            user_id,
            email,
            password_hash,
            role,
            api_token_hash,
            is_active
        FROM users
        WHERE email = %s;
        """,
        (email,)
    )

    row = cursor.fetchone()

    if not row:
        return None

    return {
        "user_id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "role": row[3],
        "api_token_hash": row[4],
        "is_active": row[5]
    }


# Login

def authenticate_user(email, password):

    user = get_user_by_email(email)

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "role": user["role"]
    }


# Check token

def authenticate_token(token):

    if not token:
        return None

    token_hash = hash_token(token)

    cursor.execute(
        """
        SELECT
            user_id,
            email,
            role,
            is_active
        FROM users
        WHERE api_token_hash = %s;
        """,
        (token_hash,)
    )

    row = cursor.fetchone()

    if not row:
        return None

    if not row[3]:
        return None

    return {
        "user_id": row[0],
        "email": row[1],
        "role": row[2]
    }


# Delete user

def delete_user(user_id):

    cursor.execute(
        """
        DELETE FROM users
        WHERE user_id = %s;
        """,
        (user_id,)
    )

    deleted = cursor.rowcount

    connection.commit()

    return deleted == 1


# Test

if __name__ == "__main__":

    print("=" * 50)
    print("USERS TEST")
    print("=" * 50)

    test_email = "test.user@example.com"
    test_password = "TestPassword123!"
    test_role = "tester"

    test_user_id = None

    try:

        existing_user = get_user_by_email(test_email)

        if existing_user:
            delete_user(existing_user["user_id"])

        print()
        print("Creating test user...")

        user = create_user(
            test_email,
            test_password,
            test_role
        )

        test_user_id = user["user_id"]

        print("User created successfully.")
        print("User ID :", user["user_id"])
        print("Email   :", user["email"])
        print("Role    :", user["role"])
        print("Token generated successfully.")

        print()
        print("Testing password authentication...")

        authenticated_user = authenticate_user(
            test_email,
            test_password
        )

        if authenticated_user:
            print("Password Authentication: SUCCESS")
        else:
            print("Password Authentication: FAILED")

        print()
        print("Testing token authentication...")

        token_user = authenticate_token(
            user["token"]
        )

        if token_user:
            print("Token Authentication: SUCCESS")
        else:
            print("Token Authentication: FAILED")

    except ValueError as error:

        print()
        print("ERROR:", error)

    except Exception as error:

        connection.rollback()

        print()
        print("UNEXPECTED ERROR:", error)

    finally:

        if test_user_id is not None:
            try:
                delete_user(test_user_id)
                print()
                print("Temporary test user removed successfully.")
            except Exception:
                connection.rollback()

        cursor.close()
        connection.close()

        print()
        print("=" * 50)
        print("DATABASE CONNECTION CLOSED")
        print("Done.")