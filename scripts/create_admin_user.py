import os
import sys
import json
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

from backend.app.core.security import hash_password

email = "admin@admin.com"
password = "admin123"
role = "admin"

hashed = hash_password(password)

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL is not set.")

# Neon HTTP SQL endpoint
sql_endpoint = "https://ep-morning-bar-ayyfjrvs.c-5.us-east-2.aws.neon.tech/sql"
headers = {
    "Neon-Connection-String": db_url,
    "Content-Type": "application/json"
}

# Check if user already exists
check_payload = json.dumps({
    "query": "SELECT user_id, email, role FROM users WHERE email = $1;",
    "params": [email]
}).encode("utf-8")

req = urllib.request.Request(sql_endpoint, data=check_payload, headers=headers, method="POST")
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    existing_rows = result.get("rows", [])

if existing_rows:
    print(f"User {email} already exists. Updating password...")
    update_payload = json.dumps({
        "query": "UPDATE users SET password_hash = $1, role = $2, is_active = true, updated_at = NOW() WHERE email = $3 RETURNING user_id, email, role, is_active;",
        "params": [hashed, role, email]
    }).encode("utf-8")
    req = urllib.request.Request(sql_endpoint, data=update_payload, headers=headers, method="POST")
else:
    print(f"Creating new user {email}...")
    insert_payload = json.dumps({
        "query": "INSERT INTO users (email, password_hash, role, is_active, created_at, updated_at) VALUES ($1, $2, $3, true, NOW(), NOW()) RETURNING user_id, email, role, is_active;",
        "params": [email, hashed, role]
    }).encode("utf-8")
    req = urllib.request.Request(sql_endpoint, data=insert_payload, headers=headers, method="POST")

with urllib.request.urlopen(req, timeout=10) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print("SUCCESS:", res.get("rows", []))
