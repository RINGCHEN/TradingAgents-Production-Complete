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

def get_admin_user_id(email: str):
    session = SessionLocal()
    try:
        query = text("SELECT id FROM admin_users WHERE email = :email LIMIT 1;")
        result = session.execute(query, {"email": email})
        row = result.fetchone()
        if row:
            return str(row[0])
        return None
    except Exception as e:
        print(f"Error fetching admin_users ID: {e}")
        return None
    finally:
        session.close()

def update_users_table_uuid(email: str, new_uuid: str):
    session = SessionLocal()
    try:
        query = text("UPDATE users SET uuid = :new_uuid WHERE email = :email;")
        session.execute(query, {"new_uuid": new_uuid, "email": email})
        session.commit()
        print(f"Updated users.uuid for {email} to {new_uuid}")
    except Exception as e:
        print(f"Error updating users.uuid: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_email = "testuser@example.com"
    admin_id = get_admin_user_id(test_email)
    
    if admin_id:
        print(f"Admin user ID for {test_email} in admin_users table is: {admin_id}")
        update_users_table_uuid(test_email, admin_id)
    else:
        print(f"Admin user {test_email} not found in admin_users table.")
