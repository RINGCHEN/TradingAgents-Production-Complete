import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 像應用程式一樣從環境變數獲取 DATABASE_URL
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:password@localhost:5432/tradingagents'
)

# 創建引擎
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def query_user_details(email: str):
    session = SessionLocal()
    try:
        query = text("SELECT uuid, membership_tier FROM users WHERE email = :email LIMIT 1;")
        result = session.execute(query, {"email": email})
        row = result.fetchone()
        if row:
            print(f"User details for {email}: UUID={row[0]}, Membership Tier={row[1]}")
        else:
            print(f"User {email} not found in users table.")
    except Exception as e:
        print(f"Error querying user details: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_email = "testuser@example.com"
    print("Querying user details...")
    query_user_details(test_email)
    print("Query complete.")
