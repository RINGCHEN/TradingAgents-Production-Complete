import bcrypt
import json
from datetime import datetime
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

email = "testuser@example.com"
password = "Admin123!";
name = "Test User"
username = "testuser"
tier = "DIAMOND"

password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# 確保連接到正確的資料庫
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:password@localhost:5432/tradingagents'
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

session = SessionLocal()
try:
    session.execute(
        text(
            '''
            INSERT INTO users (
                uuid,
                email,
                display_name,
                username,
                password_hash,
                membership_tier,
                email_verified,
                created_at,
                updated_at,
                auth_provider,
                status
            )
            VALUES (
                :uuid,
                :email,
                :display_name,
                :username,
                :password_hash,
                :membership_tier,
                TRUE,
                :created_at,
                :updated_at,
                :auth_provider,
                :status
            )
            ON CONFLICT (email)
            DO UPDATE SET
                display_name = EXCLUDED.display_name,
                username = EXCLUDED.username,
                password_hash = EXCLUDED.password_hash,
                membership_tier = EXCLUDED.membership_tier,
                updated_at = EXCLUDED.updated_at,
                uuid = EXCLUDED.uuid,
                auth_provider = EXCLUDED.auth_provider,
                status = EXCLUDED.status
            '''
        ),
        {
            "uuid": "admin_test_user", # This will be updated by sync_user_ids.py later
            "email": email,
            "display_name": name,
            "username": username,
            "password_hash": password_hash,
            "membership_tier": tier,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "auth_provider": "EMAIL",
            "status": "ACTIVE",
        },
    )
    session.commit()
    print(f"Inserted/updated {email} with membership tier {tier}")
finally:
    session.close()

