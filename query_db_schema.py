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

def get_table_schema(table_name: str):
    session = SessionLocal()
    try:
        query = text(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
            ORDER BY ordinal_position;
        """
        )
        result = session.execute(query, {"table_name": table_name})
        print(f"\n--- Schema for table: {table_name} ---")
        for row in result:
            print(f"  Column: {row.column_name}, Type: {row.data_type}, Nullable: {row.is_nullable}, Default: {row.column_default}")
        
        # Also fetch some sample data for ID columns
        print(f"--- Sample IDs from table: {table_name} ---")
        id_columns = []
        if table_name == 'users':
            id_columns.append('uuid') # Corrected to uuid
            id_columns.append('id') 
        elif table_name == 'admin_users':
            id_columns.append('id')

        for col in id_columns:
            try:
                sample_query = text(f"SELECT {col} FROM {table_name} LIMIT 3;")
                sample_result = session.execute(sample_query)
                sample_ids = [str(r[0]) for r in sample_result.fetchall()]
                print(f"  Sample {col}s: {', '.join(sample_ids)}")
            except Exception as e:
                print(f"  Could not fetch sample {col}s: {e}")

    except Exception as e:
        print(f"Error fetching schema for {table_name}: {e}")
    finally:
        session.close()

def get_enum_values(enum_type_name: str):
    session = SessionLocal()
    try:
        query = text("""
            SELECT enumlabel
            FROM pg_enum
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
            WHERE pg_type.typname = :enum_type_name
            ORDER BY enumsortorder;
        """
        )
        result = session.execute(query, {"enum_type_name": enum_type_name})
        enum_values = [row[0] for row in result.fetchall()]
        print(f"\n--- Enum values for type: {enum_type_name} ---")
        print(f"  Values: {', '.join(enum_values)}")
    except Exception as e:
        print(f"Error fetching enum values for {enum_type_name}: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Querying database schema...")
    get_table_schema("users")
    get_table_schema("admin_users")
    get_enum_values("authprovider") # Query for authprovider enum
    get_enum_values("membershiptier") # Query for membershiptier enum
    get_enum_values("userstatus") # Query for userstatus enum
    print("Schema query complete.")
