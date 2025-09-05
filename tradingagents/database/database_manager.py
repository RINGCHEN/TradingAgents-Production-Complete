"""
數據庫管理器 - 統一的數據庫連接和會話管理
"""

import os
import sqlite3
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool


class DatabaseManager:
    """數據庫管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # 設置數據庫URL
        if database_url:
            self.database_url = database_url
        else:
            # 默認使用SQLite
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tradingagents.db")
            self.database_url = f"sqlite+aiosqlite:///{db_path}"
        
        # 創建異步引擎
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        
        # 創建會話工廠
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self.logger.info(f"Database manager initialized with URL: {self.database_url}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """獲取數據庫會話"""
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: Optional[dict] = None) -> any:
        """執行查詢"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result
    
    async def close(self):
        """關閉數據庫連接"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connections closed")


# 全局數據庫管理器實例
_database_manager: Optional[DatabaseManager] = None


def get_database_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """獲取數據庫管理器實例"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager(database_url)
    return _database_manager


def set_database_manager(manager: DatabaseManager):
    """設置數據庫管理器實例"""
    global _database_manager
    _database_manager = manager


# 簡化的同步數據庫連接（用於遷移腳本）
class SimpleDatabaseManager:
    """簡化的數據庫管理器（同步版本）"""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path:
            self.database_path = database_path
        else:
            self.database_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "tradingagents.db"
            )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Simple database manager initialized with path: {self.database_path}")
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.database_path)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> any:
        """執行查詢"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                result = cursor.execute(query, params)
            else:
                result = cursor.execute(query)
            conn.commit()
            return result
    
    def execute_script(self, script: str):
        """執行SQL腳本"""
        with self.get_connection() as conn:
            conn.executescript(script)
            conn.commit()


def get_simple_database_manager(database_path: Optional[str] = None) -> SimpleDatabaseManager:
    """獲取簡化數據庫管理器實例"""
    return SimpleDatabaseManager(database_path)