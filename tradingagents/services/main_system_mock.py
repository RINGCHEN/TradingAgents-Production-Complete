"""
主系統模擬服務 - 用於測試數據同步功能
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class MockResponseType(Enum):
    """模擬響應類型"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


@dataclass
class MockConfig:
    """模擬配置"""
    success_rate: float = 0.95  # 成功率
    response_delay: float = 0.1  # 響應延遲（秒）
    timeout_rate: float = 0.02  # 超時率
    partial_failure_rate: float = 0.03  # 部分失敗率


class UserSyncRequest(BaseModel):
    """用戶同步請求"""
    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    personality_type: Optional[str] = None
    risk_tolerance: Optional[str] = None
    investment_style: Optional[str] = None
    source: str = "personality_test_website"


class TestResultSyncRequest(BaseModel):
    """測試結果同步請求"""
    id: str
    user_id: str
    user_email: Optional[str] = None
    personality_type: str
    risk_tolerance: str
    investment_style: str
    scores: Dict[str, Any] = {}
    answers: Dict[str, Any] = {}
    completed_at: Optional[str] = None
    source: str = "personality_test_website"


class ConversionSyncRequest(BaseModel):
    """轉換數據同步請求"""
    session_id: str
    conversion_steps: List[Dict[str, Any]]
    source: str = "personality_test_website"


class BehaviorSyncRequest(BaseModel):
    """行為數據同步請求"""
    user_id: str
    action: str
    page: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: str
    source: str = "personality_test_website"


class SyncResponse(BaseModel):
    """同步響應"""
    success: bool
    id: Optional[str] = None
    target_id: Optional[str] = None
    message: str
    timestamp: str


class MainSystemMockService:
    """主系統模擬服務"""
    
    def __init__(self, config: Optional[MockConfig] = None):
        self.config = config or MockConfig()
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(title="TradingAgents Main System Mock", version="1.0.0")
        self._setup_routes()
        
        # 存儲同步的數據（內存中）
        self.synced_users: Dict[str, Dict] = {}
        self.synced_test_results: Dict[str, Dict] = {}
        self.synced_conversions: Dict[str, Dict] = {}
        self.synced_behaviors: List[Dict] = []
        
    def _setup_routes(self):
        """設置路由"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "TradingAgents Main System Mock",
                "version": "1.0.0",
                "status": "running",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "config": {
                    "success_rate": self.config.success_rate,
                    "response_delay": self.config.response_delay
                }
            }
        
        @self.app.post("/api/v1/users/sync", response_model=SyncResponse)
        async def sync_user(request: UserSyncRequest):
            """同步用戶數據"""
            return await self._handle_sync_request(
                "user", request.id, request.dict(), self.synced_users
            )
        
        @self.app.post("/api/v1/personality-tests/sync", response_model=SyncResponse)
        async def sync_test_result(request: TestResultSyncRequest):
            """同步測試結果"""
            return await self._handle_sync_request(
                "test_result", request.id, request.dict(), self.synced_test_results
            )
        
        @self.app.post("/api/v1/conversions/sync", response_model=SyncResponse)
        async def sync_conversion(request: ConversionSyncRequest):
            """同步轉換數據"""
            return await self._handle_sync_request(
                "conversion", request.session_id, request.dict(), self.synced_conversions
            )
        
        @self.app.post("/api/v1/behaviors/sync", response_model=SyncResponse)
        async def sync_behavior(request: BehaviorSyncRequest):
            """同步行為數據"""
            # 行為數據使用列表存儲
            response = await self._handle_sync_request(
                "behavior", f"{request.user_id}_{request.timestamp}", 
                request.dict(), None
            )
            
            if response.success:
                self.synced_behaviors.append(request.dict())
            
            return response
        
        @self.app.get("/api/v1/sync/stats")
        async def get_sync_stats():
            """獲取同步統計"""
            return {
                "users": len(self.synced_users),
                "test_results": len(self.synced_test_results),
                "conversions": len(self.synced_conversions),
                "behaviors": len(self.synced_behaviors),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/api/v1/users/{user_id}")
        async def get_synced_user(user_id: str):
            """獲取已同步的用戶數據"""
            if user_id in self.synced_users:
                return self.synced_users[user_id]
            else:
                raise HTTPException(status_code=404, detail="User not found")
        
        @self.app.get("/api/v1/personality-tests/{test_id}")
        async def get_synced_test_result(test_id: str):
            """獲取已同步的測試結果"""
            if test_id in self.synced_test_results:
                return self.synced_test_results[test_id]
            else:
                raise HTTPException(status_code=404, detail="Test result not found")
        
        @self.app.delete("/api/v1/sync/clear")
        async def clear_synced_data():
            """清除所有同步數據"""
            self.synced_users.clear()
            self.synced_test_results.clear()
            self.synced_conversions.clear()
            self.synced_behaviors.clear()
            
            return {
                "message": "All synced data cleared",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.put("/api/v1/mock/config")
        async def update_mock_config(
            success_rate: Optional[float] = None,
            response_delay: Optional[float] = None,
            timeout_rate: Optional[float] = None,
            partial_failure_rate: Optional[float] = None
        ):
            """更新模擬配置"""
            if success_rate is not None:
                self.config.success_rate = max(0.0, min(1.0, success_rate))
            if response_delay is not None:
                self.config.response_delay = max(0.0, response_delay)
            if timeout_rate is not None:
                self.config.timeout_rate = max(0.0, min(1.0, timeout_rate))
            if partial_failure_rate is not None:
                self.config.partial_failure_rate = max(0.0, min(1.0, partial_failure_rate))
            
            return {
                "message": "Mock configuration updated",
                "config": {
                    "success_rate": self.config.success_rate,
                    "response_delay": self.config.response_delay,
                    "timeout_rate": self.config.timeout_rate,
                    "partial_failure_rate": self.config.partial_failure_rate
                }
            }
    
    async def _handle_sync_request(
        self, 
        sync_type: str, 
        source_id: str, 
        data: Dict[str, Any],
        storage: Optional[Dict[str, Dict]] = None
    ) -> SyncResponse:
        """處理同步請求"""
        
        # 模擬響應延遲
        if self.config.response_delay > 0:
            await asyncio.sleep(self.config.response_delay)
        
        # 決定響應類型
        import random
        rand = random.random()
        
        if rand < self.config.timeout_rate:
            # 模擬超時
            await asyncio.sleep(10)  # 長時間延遲模擬超時
            response_type = MockResponseType.TIMEOUT
        elif rand < self.config.timeout_rate + self.config.partial_failure_rate:
            response_type = MockResponseType.PARTIAL
        elif rand < 1 - self.config.success_rate:
            response_type = MockResponseType.FAILURE
        else:
            response_type = MockResponseType.SUCCESS
        
        timestamp = datetime.utcnow().isoformat()
        
        if response_type == MockResponseType.SUCCESS:
            # 成功響應
            target_id = f"main_system_{sync_type}_{source_id}_{int(datetime.utcnow().timestamp())}"
            
            if storage is not None:
                storage[source_id] = {
                    **data,
                    "target_id": target_id,
                    "synced_at": timestamp
                }
            
            self.logger.info(f"Mock sync successful: {sync_type} {source_id} -> {target_id}")
            
            return SyncResponse(
                success=True,
                id=source_id,
                target_id=target_id,
                message=f"{sync_type.title()} synced successfully",
                timestamp=timestamp
            )
            
        elif response_type == MockResponseType.PARTIAL:
            # 部分失敗響應
            self.logger.warning(f"Mock sync partial failure: {sync_type} {source_id}")
            
            return SyncResponse(
                success=False,
                id=source_id,
                message=f"Partial failure syncing {sync_type}: some fields missing",
                timestamp=timestamp
            )
            
        else:
            # 失敗響應
            error_messages = [
                "Database connection failed",
                "Invalid data format",
                "Duplicate entry detected",
                "Service temporarily unavailable",
                "Authentication failed"
            ]
            
            error_message = random.choice(error_messages)
            self.logger.error(f"Mock sync failed: {sync_type} {source_id} - {error_message}")
            
            return SyncResponse(
                success=False,
                id=source_id,
                message=f"Failed to sync {sync_type}: {error_message}",
                timestamp=timestamp
            )
    
    def run(self, host: str = "localhost", port: int = 8001):
        """運行模擬服務"""
        self.logger.info(f"Starting Main System Mock Service on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


# 獨立運行的模擬服務
class StandaloneMockService:
    """獨立的模擬服務"""
    
    def __init__(self):
        self.mock_service = MainSystemMockService()
    
    def start_server(self, host: str = "localhost", port: int = 8001):
        """啟動服務器"""
        print(f"🚀 啟動主系統模擬服務...")
        print(f"📍 地址: http://{host}:{port}")
        print(f"📖 API文檔: http://{host}:{port}/docs")
        print(f"🔍 健康檢查: http://{host}:{port}/health")
        print(f"📊 同步統計: http://{host}:{port}/api/v1/sync/stats")
        print()
        print("模擬服務功能:")
        print("✅ 用戶數據同步: POST /api/v1/users/sync")
        print("✅ 測試結果同步: POST /api/v1/personality-tests/sync")
        print("✅ 轉換數據同步: POST /api/v1/conversions/sync")
        print("✅ 行為數據同步: POST /api/v1/behaviors/sync")
        print("⚙️ 配置更新: PUT /api/v1/mock/config")
        print("🗑️ 清除數據: DELETE /api/v1/sync/clear")
        print()
        
        try:
            self.mock_service.run(host, port)
        except KeyboardInterrupt:
            print("\n🛑 服務已停止")
        except Exception as e:
            print(f"❌ 服務啟動失敗: {str(e)}")


if __name__ == "__main__":
    import sys
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 解析命令行參數
    host = "localhost"
    port = 8001
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 端口號必須是數字")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    # 啟動服務
    service = StandaloneMockService()
    service.start_server(host, port)