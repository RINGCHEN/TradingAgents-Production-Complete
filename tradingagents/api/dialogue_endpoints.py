#!/usr/bin/env python3
"""
對話系統API端點
天工 (TianGong) - 專業級AI分析師對話和實時互動系統

此模組提供：
1. SSE串流對話端點
2. WebSocket實時互動支援  
3. 分析師多輪對話管理
4. 對話歷史和上下文管理
5. 實時分析進度推送
6. ART系統整合的個人化對話體驗
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, AsyncGenerator, Union, Tuple
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
import uuid
import time

# TradingAgents 核心組件
from ..agents.analysts.fundamentals_analyst import FundamentalsAnalyst
from ..agents.analysts.base_analyst import create_analysis_state, AnalysisType, AnalysisResult, AnalysisConfidenceLevel
from ..auth.dependencies import get_current_user, CurrentUser
from ..utils.user_context import UserContext, create_user_context, TierType
from ..utils.logging_config import get_api_logger
from ..utils.error_handler import handle_error

# ART 系統整合
try:
    from ..art import (
        ARTIntegration, 
        create_art_integration, 
        create_default_config,
        AnalysisMode,
        PersonalizationLevel
    )
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False

# 初始化路由器和日誌
router = APIRouter(tags=["對話系統"])
logger = get_api_logger("dialogue_endpoints")

# ==================== 數據模型 ====================

class DialogueType(Enum):
    """對話類型"""
    ANALYSIS = "analysis"           # 分析對話
    CONSULTATION = "consultation"   # 諮詢對話  
    EDUCATION = "education"         # 教育對話
    STRATEGY = "strategy"           # 策略對話

class MessageRole(Enum):
    """訊息角色"""
    USER = "user"
    ANALYST = "analyst"
    SYSTEM = "system"
    ASSISTANT = "assistant"

class DialogueStatus(Enum):
    """對話狀態"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class InteractionMode(Enum):
    """互動模式"""
    STREAMING = "streaming"         # 串流模式
    CONVERSATIONAL = "conversational"  # 對話模式
    ANALYSIS_ONLY = "analysis_only"    # 僅分析模式

class DialogueMessage(BaseModel):
    """對話訊息"""
    id: str = Field(..., description="訊息ID")
    role: MessageRole = Field(..., description="角色")
    content: str = Field(..., description="內容")
    timestamp: str = Field(..., description="時間戳")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元資料")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="分析數據")
    art_data: Optional[Dict[str, Any]] = Field(None, description="ART數據")

class DialogueRequest(BaseModel):
    """對話請求"""
    message: str = Field(..., description="用戶訊息", example="請分析台積電的投資前景")
    dialogue_type: DialogueType = Field(default=DialogueType.ANALYSIS, description="對話類型")
    interaction_mode: InteractionMode = Field(default=InteractionMode.CONVERSATIONAL, description="互動模式")
    stock_id: Optional[str] = Field(None, description="股票代號", example="2330")
    context: Optional[Dict[str, Any]] = Field(default={}, description="對話上下文")
    preferences: Optional[Dict[str, Any]] = Field(default={}, description="用戶偏好")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "台積電目前的財務狀況如何？值得投資嗎？",
                "dialogue_type": "analysis",
                "interaction_mode": "conversational",
                "stock_id": "2330",
                "context": {
                    "investment_horizon": "long_term",
                    "risk_tolerance": "moderate"
                },
                "preferences": {
                    "detail_level": "comprehensive",
                    "include_comparisons": True
                }
            }
        }

class DialogueSession(BaseModel):
    """對話會話"""
    session_id: str = Field(..., description="會話ID")
    user_id: str = Field(..., description="用戶ID")
    analyst_type: str = Field(..., description="分析師類型")
    dialogue_type: DialogueType = Field(..., description="對話類型")
    interaction_mode: InteractionMode = Field(..., description="互動模式")
    status: DialogueStatus = Field(..., description="狀態")
    messages: List[DialogueMessage] = Field(default=[], description="訊息列表")
    context: Dict[str, Any] = Field(default={}, description="會話上下文")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")
    metadata: Dict[str, Any] = Field(default={}, description="會話元資料")

class StreamingEvent(BaseModel):
    """串流事件"""
    event: str = Field(..., description="事件類型")
    data: Dict[str, Any] = Field(..., description="事件數據")
    timestamp: str = Field(..., description="時間戳")
    session_id: Optional[str] = Field(None, description="會話ID")

# ==================== 對話管理器 ====================

class DialogueManager:
    """對話管理器 - 管理所有對話會話和分析師互動"""
    
    def __init__(self):
        self.active_sessions: Dict[str, DialogueSession] = {}
        self.active_streams: Dict[str, AsyncGenerator] = {}
        self.analyst_manager = None  # 將從 analyst_endpoints 導入
        self.logger = get_api_logger("dialogue_endpoints")
        
        # ART 系統整合
        self.art_integration: Optional['ARTIntegration'] = None
        self._art_initialized = False

        # 延遲初始化 ART 系統（避免在module導入時創建async task）
        # ART系統將在首次使用時自動初始化
        # if ART_AVAILABLE:
        #     asyncio.create_task(self._initialize_art_system())
    
    async def _initialize_art_system(self):
        """初始化 ART 系統"""
        try:
            if not ART_AVAILABLE:
                self.logger.warning("ART system not available for dialogue system")
                return
            
            # 創建 ART 配置
            config = create_default_config("production")
            config.storage_root = "./art_data_dialogue"
            config.personalization_enabled = True
            config.trajectory_collection_enabled = True
            config.reward_generation_enabled = True
            
            # 初始化 ART 整合系統
            self.art_integration = await create_art_integration(config)
            self._art_initialized = True
            
            self.logger.info("ART system initialized for dialogue system")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ART system for dialogue: {e}")
            self.art_integration = None
            self._art_initialized = False
    
    async def create_session(self, 
                           user: CurrentUser,
                           dialogue_type: DialogueType,
                           interaction_mode: InteractionMode,
                           analyst_type: str = "fundamentals") -> DialogueSession:
        """創建新的對話會話"""
        
        session_id = f"dialogue_{uuid.uuid4().hex[:12]}"
        user_id = str(user.id) if hasattr(user, 'id') else f"user_{uuid.uuid4().hex[:8]}"
        
        session = DialogueSession(
            session_id=session_id,
            user_id=user_id,
            analyst_type=analyst_type,
            dialogue_type=dialogue_type,
            interaction_mode=interaction_mode,
            status=DialogueStatus.ACTIVE,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            context={
                "user_tier": getattr(user, 'membership_tier', 'free'),
                "session_start": datetime.now().isoformat()
            }
        )
        
        self.active_sessions[session_id] = session
        
        # 系統歡迎訊息
        welcome_message = await self._create_welcome_message(session, user)
        session.messages.append(welcome_message)
        
        self.logger.info(f"Created dialogue session {session_id} for user {user_id}")
        return session
    
    async def _create_welcome_message(self, session: DialogueSession, user: CurrentUser) -> DialogueMessage:
        """創建歡迎訊息"""
        
        user_tier = getattr(user, 'membership_tier', 'free')
        analyst_name = self._get_analyst_name(session.analyst_type)
        
        if user_tier == 'free':
            welcome_content = f"歡迎使用 {analyst_name}！我是您的專業投資分析助手。作為免費用戶，您可以進行基礎的股票分析諮詢。"
        elif user_tier == 'gold':
            welcome_content = f"歡迎回來，尊貴的黃金會員！我是 {analyst_name}，將為您提供深度的個人化投資分析和策略建議。"
        else:  # diamond
            welcome_content = f"歡迎，鑽石會員！我是您的專屬 {analyst_name}，準備為您提供最高級別的投資洞察和量身定制的分析服務。"
        
        return DialogueMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=MessageRole.ANALYST,
            content=welcome_content,
            timestamp=datetime.now().isoformat(),
            metadata={
                "message_type": "welcome",
                "user_tier": user_tier,
                "analyst_type": session.analyst_type
            }
        )
    
    def _get_analyst_name(self, analyst_type: str) -> str:
        """獲取分析師名稱"""
        names = {
            "fundamentals": "基本面分析師",
            "technical": "技術分析師", 
            "sentiment": "市場情緒分析師",
            "macro": "總體經濟分析師"
        }
        return names.get(analyst_type, "AI投資分析師")
    
    async def process_message(self, 
                            session_id: str,
                            user_message: str,
                            context: Dict[str, Any] = None) -> DialogueMessage:
        """處理用戶訊息並生成回應"""
        
        if session_id not in self.active_sessions:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        session = self.active_sessions[session_id]
        
        # 添加用戶訊息
        user_msg = DialogueMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.now().isoformat(),
            metadata=context or {}
        )
        session.messages.append(user_msg)
        
        # 生成分析師回應
        analyst_response = await self._generate_analyst_response(session, user_message, context)
        session.messages.append(analyst_response)
        
        # 更新會話
        session.updated_at = datetime.now().isoformat()
        
        self.logger.info(f"Processed message in session {session_id}")
        return analyst_response
    
    async def _generate_analyst_response(self, 
                                       session: DialogueSession,
                                       user_message: str,
                                       context: Dict[str, Any] = None) -> DialogueMessage:
        """生成分析師回應"""
        
        # TODO: 實際的分析師對話邏輯
        # 這裡應該整合實際的分析師系統
        
        # 模擬分析師回應
        if "分析" in user_message or "投資" in user_message:
            content = self._generate_analysis_response(user_message, session, context)
        elif "價格" in user_message or "目標價" in user_message:
            content = self._generate_price_response(user_message, session, context)
        elif "風險" in user_message:
            content = self._generate_risk_response(user_message, session, context)
        else:
            content = self._generate_general_response(user_message, session, context)
        
        return DialogueMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=MessageRole.ANALYST,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata={
                "response_type": "analysis",
                "user_tier": session.context.get("user_tier", "free"),
                "processing_time": time.time()
            }
        )
    
    def _generate_analysis_response(self, message: str, session: DialogueSession, context: Dict[str, Any]) -> str:
        """生成分析類型回應"""
        user_tier = session.context.get("user_tier", "free")
        
        base_response = "根據我的分析，這檔股票在基本面上表現"
        
        if user_tier == 'free':
            return f"{base_response}穩健。建議您進一步關注公司的財務報表和產業趨勢。如需更深入的分析，歡迎升級到高級會員。"
        elif user_tier == 'gold':
            return f"{base_response}良好，PE比率合理，ROE表現優異。考慮到當前市場環境和產業競爭態勢，建議採取分批建倉策略。"
        else:  # diamond
            return f"{base_response}極佳，基於我的深度模型分析，該股具有15-20%的上漲潛力。建議配置權重為投資組合的8-12%，目標持有期12-18個月。"
    
    def _generate_price_response(self, message: str, session: DialogueSession, context: Dict[str, Any]) -> str:
        """生成價格類型回應"""
        user_tier = session.context.get("user_tier", "free")
        
        if user_tier == 'free':
            return "關於價格預測，建議參考技術分析指標。更精確的目標價預測需要升級到高級會員。"
        elif user_tier == 'gold':
            return "基於DCF模型和同業比較，合理目標價區間在520-580元。建議在480元以下積極買進。"
        else:  # diamond
            return "根據我的量化模型，12個月目標價為650元（+25%），6個月目標價為580元（+12%）。關鍵支撐位在450元，突破600元後可期待加速上漲。"
    
    def _generate_risk_response(self, message: str, session: DialogueSession, context: Dict[str, Any]) -> str:
        """生成風險類型回應"""
        return "主要風險因素包括：1) 半導體週期性波動 2) 地緣政治影響 3) 匯率風險。建議建立止損機制並保持投資組合多元化。"
    
    def _generate_general_response(self, message: str, session: DialogueSession, context: Dict[str, Any]) -> str:
        """生成一般回應"""
        return "我理解您的問題。作為專業的投資分析師，我會為您提供客觀、專業的投資建議。請告訴我您想了解哪支股票的具體資訊？"
    
    async def stream_analysis(self, 
                            session_id: str,
                            request: DialogueRequest) -> AsyncGenerator[str, None]:
        """串流分析過程"""
        
        if session_id not in self.active_sessions:
            raise HTTPException(status_code=404, detail="會話不存在")
        
        session = self.active_sessions[session_id]
        
        # 發送開始事件
        yield self._format_sse_data(StreamingEvent(
            event="analysis_start",
            data={
                "session_id": session_id,
                "message": "開始分析...",
                "stage": "initialization"
            },
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        ))
        
        # 模擬分析步驟
        stages = [
            ("data_collection", "收集股票數據...", 2),
            ("fundamental_analysis", "進行基本面分析...", 3),
            ("technical_analysis", "執行技術分析...", 2),
            ("risk_assessment", "評估投資風險...", 2),
            ("generating_recommendation", "生成投資建議...", 1),
        ]
        
        for stage, message, duration in stages:
            yield self._format_sse_data(StreamingEvent(
                event="analysis_progress",
                data={
                    "session_id": session_id,
                    "stage": stage,
                    "message": message,
                    "progress": (stages.index((stage, message, duration)) + 1) / len(stages) * 100
                },
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            ))
            
            await asyncio.sleep(duration)
        
        # 生成最終結果
        final_response = await self._generate_analyst_response(session, request.message, request.context)
        session.messages.append(final_response)
        
        yield self._format_sse_data(StreamingEvent(
            event="analysis_complete",
            data={
                "session_id": session_id,
                "response": final_response.dict(),
                "total_messages": len(session.messages)
            },
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        ))
    
    def _format_sse_data(self, event: StreamingEvent) -> str:
        """格式化SSE數據"""
        return f"event: {event.event}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
    
    def get_session(self, session_id: str) -> Optional[DialogueSession]:
        """獲取會話"""
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """關閉會話"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = DialogueStatus.COMPLETED
            # 不立即刪除，保留一段時間以供查詢
            self.logger.info(f"Closed dialogue session {session_id}")

# 創建全域對話管理器
dialogue_manager = DialogueManager()

# ==================== API端點 ====================

@router.post("/dialogue/sessions", response_model=DialogueSession)
async def create_dialogue_session(
    request: DialogueRequest,
    current_user: CurrentUser
):
    """
    創建新的對話會話
    
    支援不同類型的對話模式和分析師互動。
    """
    try:
        session = await dialogue_manager.create_session(
            user=current_user,
            dialogue_type=request.dialogue_type,
            interaction_mode=request.interaction_mode
        )
        
        logger.info(f"Created new dialogue session", extra={
            'session_id': session.session_id,
            'user_id': session.user_id,
            'dialogue_type': request.dialogue_type.value,
            'interaction_mode': request.interaction_mode.value
        })
        
        return session
        
    except Exception as e:
        logger.error(f"創建對話會話失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="創建對話會話失敗"
        )

@router.get("/dialogue/sessions/{session_id}", response_model=DialogueSession)
async def get_dialogue_session(
    session_id: str,
    current_user: CurrentUser
):
    """獲取對話會話詳情"""
    
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    # 簡單的權限檢查
    user_id = str(current_user.id) if hasattr(current_user, 'id') else None
    if session.user_id != user_id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="無權訪問此會話")
    
    return session

@router.post("/dialogue/sessions/{session_id}/message", response_model=DialogueMessage)
async def send_message(
    session_id: str,
    request: DialogueRequest,
    current_user: CurrentUser
):
    """
    發送訊息到對話會話
    
    支援普通對話和分析請求。
    """
    try:
        response = await dialogue_manager.process_message(
            session_id=session_id,
            user_message=request.message,
            context=request.context
        )
        
        logger.info(f"Processed dialogue message", extra={
            'session_id': session_id,
            'message_length': len(request.message),
            'response_length': len(response.content)
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理訊息失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="處理訊息失敗"
        )

@router.get("/dialogue/sessions/{session_id}/stream")
async def stream_dialogue_analysis(
    session_id: str,
    current_user: CurrentUser,
    message: str,
    dialogue_type: DialogueType = DialogueType.ANALYSIS,
    interaction_mode: InteractionMode = InteractionMode.STREAMING
):
    """
    串流對話分析
    
    提供實時的分析過程推送，適合長時間分析任務。
    """
    
    # 驗證會話存在
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    # 創建請求對象
    request = DialogueRequest(
        message=message,
        dialogue_type=dialogue_type,
        interaction_mode=interaction_mode
    )
    
    # 返回SSE流
    return StreamingResponse(
        dialogue_manager.stream_analysis(session_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.delete("/dialogue/sessions/{session_id}")
async def close_dialogue_session(
    session_id: str,
    current_user: CurrentUser
):
    """關閉對話會話"""
    
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    dialogue_manager.close_session(session_id)
    
    return {"message": "會話已關閉", "session_id": session_id}

@router.get("/dialogue/sessions/{session_id}/messages")
async def get_dialogue_messages(
    session_id: str,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0
):
    """獲取對話訊息列表"""
    
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    # 分頁訊息
    messages = session.messages[offset:offset+limit]
    
    return {
        "messages": messages,
        "total": len(session.messages),
        "offset": offset,
        "limit": limit
    }

# ==================== WebSocket端點 ====================

@router.websocket("/dialogue/ws/{session_id}")
async def websocket_dialogue(websocket: WebSocket, session_id: str):
    """
    WebSocket對話端點
    
    提供實時雙向對話功能。
    """
    await websocket.accept()
    
    try:
        # 驗證會話
        session = dialogue_manager.get_session(session_id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": "會話不存在"
            })
            await websocket.close()
            return
        
        logger.info(f"WebSocket dialogue connection established for session {session_id}")
        
        # 發送歡迎訊息
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket對話連接已建立"
        })
        
        while True:
            # 接收訊息
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # 處理用戶訊息
                user_message = data.get("content", "")
                
                # 發送處理中狀態
                await websocket.send_json({
                    "type": "processing",
                    "message": "正在處理您的訊息..."
                })
                
                # 生成回應
                response = await dialogue_manager.process_message(
                    session_id=session_id,
                    user_message=user_message,
                    context=data.get("context", {})
                )
                
                # 發送回應
                await websocket.send_json({
                    "type": "response",
                    "data": response.dict()
                })
                
            elif data.get("type") == "ping":
                # 心跳檢測
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket dialogue disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket dialogue error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "連接發生錯誤"
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

@router.get("/dialogue/status")
async def get_dialogue_system_status():
    """獲取對話系統狀態"""
    return {
        "active_sessions": len(dialogue_manager.active_sessions),
        "art_system_available": ART_AVAILABLE,
        "art_initialized": dialogue_manager._art_initialized,
        "system_status": "operational",
        "timestamp": datetime.now().isoformat()
    }