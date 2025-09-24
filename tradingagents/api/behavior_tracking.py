"""
用戶行為追蹤API端點
接收和處理前端發送的用戶行為事件
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os

from ..auth.dependencies import get_current_user
from ...analytics.behavior.behavior_tracker import BehaviorTracker

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/analytics", tags=["用戶行為追蹤"])

# 全局變量存儲追蹤器實例
_behavior_tracker = None

def get_behavior_tracker() -> BehaviorTracker:
    """獲取行為追蹤器實例"""
    global _behavior_tracker
    
    if _behavior_tracker is None:
        # 這裡需要從依賴注入獲取warehouse_manager
        # 暫時使用環境變量
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL環境變數未設置")
        
        # 導入數據倉庫管理器
        from ...analytics.warehouse.data_warehouse_manager import DataWarehouseManager
        warehouse_manager = DataWarehouseManager(database_url)
        _behavior_tracker = BehaviorTracker(warehouse_manager)
    
    return _behavior_tracker

# Pydantic模型定義
class EventData(BaseModel):
    """事件數據模型"""
    user_id: Optional[int] = None
    session_id: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=50)
    event_category: str = Field(default="general", max_length=50)
    page_url: Optional[str] = Field(None, max_length=2000)
    element_selector: Optional[str] = Field(None, max_length=200)
    event_data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(..., description="ISO格式時間戳")
    referrer: Optional[str] = Field(None, max_length=2000)
    utm_source: Optional[str] = Field(None, max_length=50)
    utm_medium: Optional[str] = Field(None, max_length=50)
    utm_campaign: Optional[str] = Field(None, max_length=50)

class BatchEventsRequest(BaseModel):
    """批量事件請求模型"""
    events: List[EventData] = Field(..., min_items=1, max_items=100)

class SessionStartRequest(BaseModel):
    """會話開始請求模型"""
    session_id: Optional[str] = None
    user_id: Optional[int] = None
    entry_page: Optional[str] = None
    traffic_source: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    geo_info: Optional[Dict[str, Any]] = None

class SessionEndRequest(BaseModel):
    """會話結束請求模型"""
    session_id: str = Field(..., min_length=1)
    exit_page: Optional[str] = None

class ConversionRequest(BaseModel):
    """轉換標記請求模型"""
    session_id: str = Field(..., min_length=1)
    conversion_value: Optional[float] = None
    conversion_type: str = Field(default="purchase")

@router.post("/events")
async def track_events(
    request: BatchEventsRequest,
    http_request: Request
):
    """
    批量接收用戶行為事件
    
    支援一次提交多個事件，提高傳輸效率
    自動提取IP地址、User-Agent等請求元數據
    """
    try:
        tracker = get_behavior_tracker()
        
        # 提取請求元數據
        request_meta = {
            'ip_address': http_request.client.host if http_request.client else None,
            'user_agent': http_request.headers.get('user-agent'),
            'referrer': http_request.headers.get('referer')
        }
        
        # 處理每個事件
        processed_events = 0
        failed_events = 0
        
        for event_data in request.events:
            try:
                # 解析時間戳
                timestamp = datetime.fromisoformat(event_data.timestamp.replace('Z', '+00:00'))
                
                # 追蹤事件
                success = await tracker.track_event(
                    user_id=event_data.user_id,
                    session_id=event_data.session_id,
                    event_type=event_data.event_type,
                    event_category=event_data.event_category,
                    page_url=event_data.page_url,
                    element_selector=event_data.element_selector,
                    event_data=event_data.event_data,
                    request_meta=request_meta
                )
                
                if success:
                    processed_events += 1
                else:
                    failed_events += 1
                    
            except Exception as e:
                logger.error(f"處理單個事件失敗: {e}")
                failed_events += 1
        
        return {
            "success": True,
            "message": f"事件處理完成",
            "processed_events": processed_events,
            "failed_events": failed_events,
            "total_events": len(request.events)
        }
        
    except Exception as e:
        logger.error(f"批量事件處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"事件處理失敗: {str(e)}")

@router.post("/events/single")
async def track_single_event(
    event_data: EventData,
    http_request: Request
):
    """
    接收單個用戶行為事件
    
    用於實時事件追蹤，立即處理並返回結果
    """
    try:
        tracker = get_behavior_tracker()
        
        # 提取請求元數據
        request_meta = {
            'ip_address': http_request.client.host if http_request.client else None,
            'user_agent': http_request.headers.get('user-agent'),
            'referrer': http_request.headers.get('referer')
        }
        
        # 解析時間戳
        timestamp = datetime.fromisoformat(event_data.timestamp.replace('Z', '+00:00'))
        
        # 追蹤事件
        success = await tracker.track_event(
            user_id=event_data.user_id,
            session_id=event_data.session_id,
            event_type=event_data.event_type,
            event_category=event_data.event_category,
            page_url=event_data.page_url,
            element_selector=event_data.element_selector,
            event_data=event_data.event_data,
            request_meta=request_meta
        )
        
        if success:
            return {
                "success": True,
                "message": "事件追蹤成功",
                "event_type": event_data.event_type,
                "session_id": event_data.session_id
            }
        else:
            raise HTTPException(status_code=400, detail="事件驗證失敗")
            
    except Exception as e:
        logger.error(f"單個事件處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"事件處理失敗: {str(e)}")

@router.post("/sessions/start")
async def start_session(
    request: SessionStartRequest,
    http_request: Request
):
    """
    開始新的用戶會話
    
    創建會話ID並初始化會話追蹤
    返回會話ID供前端使用
    """
    try:
        tracker = get_behavior_tracker()
        
        # 提取設備和地理信息
        device_info = request.device_info or {}
        device_info.update({
            'user_agent': http_request.headers.get('user-agent'),
            'accept_language': http_request.headers.get('accept-language'),
            'accept_encoding': http_request.headers.get('accept-encoding')
        })
        
        geo_info = request.geo_info or {}
        if http_request.client:
            geo_info['ip_address'] = http_request.client.host
        
        # 開始會話
        session_id = await tracker.start_session(
            session_id=request.session_id,
            user_id=request.user_id,
            entry_page=request.entry_page,
            traffic_source=request.traffic_source,
            device_info=device_info,
            geo_info=geo_info
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "會話已開始"
        }
        
    except Exception as e:
        logger.error(f"開始會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"開始會話失敗: {str(e)}")

@router.post("/sessions/end")
async def end_session(request: SessionEndRequest):
    """
    結束用戶會話
    
    計算會話持續時間並保存會話數據
    """
    try:
        tracker = get_behavior_tracker()
        
        success = await tracker.end_session(
            session_id=request.session_id,
            exit_page=request.exit_page
        )
        
        if success:
            return {
                "success": True,
                "message": "會話已結束",
                "session_id": request.session_id
            }
        else:
            raise HTTPException(status_code=404, detail="會話不存在")
            
    except Exception as e:
        logger.error(f"結束會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"結束會話失敗: {str(e)}")

@router.post("/conversions")
async def mark_conversion(request: ConversionRequest):
    """
    標記轉換事件
    
    用於追蹤重要的業務轉換，如購買、註冊等
    """
    try:
        tracker = get_behavior_tracker()
        
        success = await tracker.mark_conversion(
            session_id=request.session_id,
            conversion_value=request.conversion_value,
            conversion_type=request.conversion_type
        )
        
        if success:
            return {
                "success": True,
                "message": "轉換已標記",
                "session_id": request.session_id,
                "conversion_type": request.conversion_type,
                "conversion_value": request.conversion_value
            }
        else:
            raise HTTPException(status_code=404, detail="會話不存在")
            
    except Exception as e:
        logger.error(f"標記轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"標記轉換失敗: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """
    獲取會話信息
    
    返回指定會話的詳細信息和統計數據
    """
    try:
        tracker = get_behavior_tracker()
        
        session = await tracker.get_session(session_id)
        
        if session:
            return {
                "success": True,
                "session": {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "duration_seconds": session.duration_seconds,
                    "page_views": session.page_views,
                    "events_count": session.events_count,
                    "bounce": session.bounce,
                    "conversion": session.conversion,
                    "conversion_value": session.conversion_value,
                    "entry_page": session.entry_page,
                    "exit_page": session.exit_page,
                    "traffic_source": session.traffic_source,
                    "device_info": session.device_info,
                    "geo_info": session.geo_info
                }
            }
        else:
            raise HTTPException(status_code=404, detail="會話不存在")
            
    except Exception as e:
        logger.error(f"獲取會話信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取會話信息失敗: {str(e)}")

@router.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: int):
    """
    獲取用戶的活躍會話
    
    返回指定用戶當前的所有活躍會話
    """
    try:
        tracker = get_behavior_tracker()
        
        sessions = await tracker.get_user_active_sessions(user_id)
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.session_id,
                "start_time": session.start_time.isoformat(),
                "page_views": session.page_views,
                "events_count": session.events_count,
                "entry_page": session.entry_page,
                "traffic_source": session.traffic_source
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "active_sessions": session_list,
            "session_count": len(session_list)
        }
        
    except Exception as e:
        logger.error(f"獲取用戶會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取用戶會話失敗: {str(e)}")

@router.get("/stats")
async def get_tracking_stats(hours: int = 24):
    """
    獲取追蹤統計信息
    
    返回指定時間範圍內的事件統計和系統狀態
    """
    try:
        tracker = get_behavior_tracker()
        
        stats = await tracker.get_event_stats(hours=hours)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"獲取追蹤統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計信息失敗: {str(e)}")

@router.get("/health")
async def tracking_health_check():
    """行為追蹤系統健康檢查"""
    try:
        tracker = get_behavior_tracker()
        
        # 獲取系統狀態
        stats = await tracker.get_event_stats(hours=1)
        
        return {
            "success": True,
            "service": "behavior_tracking",
            "status": "healthy",
            "active_sessions": stats.get('active_sessions', 0),
            "buffer_size": stats.get('buffer_size', 0),
            "recent_events": stats.get('total_events', 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"行為追蹤健康檢查失敗: {e}")
        return {
            "success": False,
            "service": "behavior_tracking", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# OPTIONS處理器，支援CORS預檢請求
@router.options("/events")
async def events_options():
    """處理事件端點的CORS預檢請求"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        },
        content={}
    )

@router.options("/sessions/start")
async def session_start_options():
    """處理會話開始端點的CORS預檢請求"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        },
        content={}
    )