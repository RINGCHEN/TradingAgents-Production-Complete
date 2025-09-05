#!/usr/bin/env python3
"""
Database configuration and connection management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:password@localhost:5432/tradingagents'
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_database_url():
    """Get database URL"""
    return DATABASE_URL

async def test_connection():
    """Test database connection"""
    try:
        # Simple connection test
        connection = engine.connect()
        connection.close()
        return True
    except Exception:
        return False

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()