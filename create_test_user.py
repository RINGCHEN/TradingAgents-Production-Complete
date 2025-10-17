import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set or .env file not found")

# User data
email = "testuser@example.com"
plain_password = "Admin123!"
name = "Test User"
role = "admin"
permissions = ["user_management", "system_config", "analytics", "reports"]

# Hash the password
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

conn = None
cursor = None
try:
    # Connect to the database
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    # Use INSERT ... ON CONFLICT to create or update the user
    cursor.execute("""
        INSERT INTO admin_users (email, name, role, permissions, password_hash, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            permissions = EXCLUDED.permissions,
            password_hash = EXCLUDED.password_hash,
            is_active = EXCLUDED.is_active;
    """, (email, name, role, permissions, password_hash, True))

    # Commit the transaction
    conn.commit()

    print(f"Successfully created/updated admin user '{email}'")

except Exception as e:
    print(f"Error: {e}")
    if conn:
        conn.rollback()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
