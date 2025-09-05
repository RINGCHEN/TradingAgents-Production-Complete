#!/usr/bin/env python3
"""
AI分析師API端點
天工 (TianGong) - 為前端提供AI分析師服務的RESTful API

此模組提供：
1. 股票基本面分析API
2. 技術面分析API  
3. 分析歷史查詢
4. 分析師狀態管理
5. ART個人化學習整合
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Tuple
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
import uuid

# TradingAgents 核心組件
from ..agents.analysts.fundamentals_analyst import FundamentalsAnalyst
from ..agents.analysts.technical_analyst import TechnicalAnalyst
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
router = APIRouter(tags=["AI分析師"])
logger = get_api_logger("analyst_endpoints")

# ==================== 請求和響應模型 ====================

class AnalysisRequest(BaseModel):
    """分析請求模型"""
    stock_id: str = Field(..., description="股票代號", example="2330")
    analysis_type: str = Field(default="fundamental", description="分析類型", example="fundamental")
    user_preferences: Optional[Dict[str, Any]] = Field(default={}, description="用戶偏好設置")
    
    class Config:
        schema_extra = {
            "example": {
                "stock_id": "2330",
                "analysis_type": "fundamental",
                "user_preferences": {
                    "risk_tolerance": "moderate",
                    "investment_horizon": "long_term",
                    "focus_areas": ["valuation", "growth"]
                }
            }
        }

class AnalysisResponse(BaseModel):
    """分析響應模型"""
    analysis_id: str = Field(..., description="分析ID")
    stock_id: str = Field(..., description="股票代號")
    analysis_type: str = Field(..., description="分析類型")
    recommendation: str = Field(..., description="投資建議 (BUY/SELL/HOLD)")
    confidence_level: str = Field(..., description="信心度等級")
    confidence_score: float = Field(..., description="信心分數 (0-1)")
    target_price: Optional[float] = Field(None, description="目標價")
    current_price: Optional[float] = Field(None, description="當前價格")
    upside_potential: Optional[float] = Field(None, description="上漲潛力 (%)")
    reasoning: List[str] = Field(default=[], description="分析推理")
    key_insights: List[str] = Field(default=[], description="關鍵洞察")
    risk_factors: Optional[List[str]] = Field(default=[], description="風險因子")
    fundamental_metrics: Optional[Dict[str, Any]] = Field(None, description="基本面指標")
    technical_metrics: Optional[Dict[str, Any]] = Field(None, description="技術指標")
    taiwan_insights: Optional[Dict[str, Any]] = Field(None, description="台灣市場洞察")
    analysis_date: str = Field(..., description="分析日期")
    timestamp: str = Field(..., description="分析時間戳")
    
    # ART 系統整合數據
    art_data: Optional[Dict[str, Any]] = Field(None, description="ART系統整合數據")
    trajectory_id: Optional[str] = Field(None, description="軌跡收集ID")
    personalization_level: Optional[str] = Field(None, description="個人化等級")
    reward_signal: Optional[Dict[str, Any]] = Field(None, description="獎勵信號")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "analysis_12345",
                "stock_id": "2330",
                "analysis_type": "fundamental",
                "recommendation": "BUY",
                "confidence_level": "HIGH",
                "confidence_score": 0.85,
                "target_price": 650.0,
                "current_price": 580.0,
                "upside_potential": 12.07,
                "reasoning": [
                    "公司基本面強勁，ROE達到25%",
                    "半導體產業處於上升週期",
                    "估值相對合理，PE比率低於同業平均"
                ],
                "key_insights": [
                    "AI和HPC需求驅動長期成長",
                    "製程技術領先優勢明顯",
                    "現金流穩健，股息率吸引人"
                ],
                "analysis_date": "2025-08-07",
                "timestamp": "2025-08-07T10:30:00Z"
            }
        }

class AnalysisHistoryRequest(BaseModel):
    """分析歷史查詢請求"""
    stock_id: Optional[str] = Field(None, description="股票代號篩選")
    analysis_type: Optional[str] = Field(None, description="分析類型篩選")
    limit: int = Field(default=20, le=100, description="返回數量限制")
    offset: int = Field(default=0, description="偏移量")

class AnalystStatus(BaseModel):
    """分析師狀態"""
    analyst_id: str = Field(..., description="分析師ID")
    analyst_type: str = Field(..., description="分析師類型")
    status: str = Field(..., description="狀態")
    available_features: List[str] = Field(..., description="可用功能")
    art_integration: Dict[str, Any] = Field(..., description="ART系統整合狀態")

# ==================== 分析師管理器 ====================

class AnalystManager:
    """分析師管理器 - 統一管理所有AI分析師"""
    
    def __init__(self):
        self.analysts: Dict[str, Any] = {}
        self.logger = get_api_logger("analyst_endpoints")
        
        # ART 系統整合
        self.art_integration: Optional[ARTIntegration] = None
        self._art_initialized = False
        
        # 延遲初始化 ART 系統，避免在模組載入時創建異步任務
        # ART 系統將在第一次使用時初始化
    
    async def _initialize_art_system(self):
        """初始化 ART 系統"""
        try:
            if not ART_AVAILABLE:
                self.logger.warning("ART system not available, skipping initialization")
                return
            
            # 創建 ART 配置
            config = create_default_config("production")
            config.storage_root = "./art_data_production"
            config.personalization_enabled = True
            config.trajectory_collection_enabled = True
            config.reward_generation_enabled = True
            config.monitoring_enabled = True
            
            # 初始化 ART 整合系統
            self.art_integration = await create_art_integration(config)
            self._art_initialized = True
            
            self.logger.info("ART system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ART system: {e}")
            self.art_integration = None
            self._art_initialized = False
    
    async def get_fundamentals_analyst(self) -> FundamentalsAnalyst:
        """獲取基本面分析師實例"""
        if "fundamentals" not in self.analysts:
            config = {
                'analyst_id': 'production_fundamentals_analyst',
                'llm_config': {
                    'model': 'gpt-3.5-turbo',
                    'max_tokens': 3000,
                    'temperature': 0.3
                },
                'finmind_config': {
                    'enable_taiwan_features': True
                }
            }
            
            analyst = FundamentalsAnalyst(config)
            # 臨時禁用權限檢查，直到權限系統完善
            analyst.permission_bridge = None
            
            self.analysts["fundamentals"] = analyst
            self.logger.info("基本面分析師初始化完成")
        
        return self.analysts["fundamentals"]
    
    async def get_technical_analyst(self) -> TechnicalAnalyst:
        """獲取技術分析師實例"""
        if "technical" not in self.analysts:
            config = {
                'analyst_id': 'production_technical_analyst',
                'llm_config': {
                    'model': 'gpt-3.5-turbo',
                    'max_tokens': 3000,
                    'temperature': 0.2
                },
                'finmind_config': {
                    'enable_taiwan_features': True
                }
            }
            
            analyst = TechnicalAnalyst(config)
            # 臨時禁用權限檢查，直到權限系統完善
            analyst.permission_bridge = None
            
            self.analysts["technical"] = analyst
            self.logger.info("技術分析師初始化完成")
        
        return self.analysts["technical"]
    
    async def analyze_stock(
        self,
        stock_id: str,
        analysis_type: str,
        user: CurrentUser,
        user_preferences: Dict[str, Any] = None
    ) -> Tuple[AnalysisResult, Dict[str, Any]]:
        """執行股票分析 - 整合 ART 系統"""
        
        # 創建用戶上下文
        user_context = {
            'user_id': user.id if hasattr(user, 'id') else str(uuid.uuid4()),
            'tier': getattr(user, 'membership_tier', 'free'),
            'preferences': user_preferences or {}
        }
        
        # 創建分析狀態
        state = create_analysis_state(
            stock_id=stock_id,
            user_context=user_context
        )
        
        # 根據分析類型選擇分析師
        if analysis_type.lower() == "fundamental":
            analyst = await self.get_fundamentals_analyst()
            analyst_name = "基本面分析"
            
        elif analysis_type.lower() == "technical":
            analyst = await self.get_technical_analyst()
            analyst_name = "技術分析"
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的分析類型: {analysis_type}。支援的類型: fundamental, technical"
            )
        
        # 如果 ART 系統可用，使用整合分析
        if self._art_initialized and self.art_integration:
            try:
                # 確定分析模式
                analysis_mode = AnalysisMode.PERSONALIZED if user_context.get('tier') != 'free' else AnalysisMode.STANDARD
                
                # 通過 ART 系統執行分析
                result, art_data = await self.art_integration.process_analysis(
                    analyst=analyst,
                    state=state,
                    analysis_mode=analysis_mode,
                    user_context=user_context
                )
                
                self.logger.info(f"完成 {stock_id} ART 整合{analyst_name}", extra={
                    'stock_id': stock_id,
                    'user_id': user_context['user_id'],
                    'analysis_type': analysis_type,
                    'recommendation': result.recommendation,
                    'confidence': result.confidence,
                    'art_integrated': True,
                    'analysis_mode': analysis_mode.value
                })
                
                return result, art_data
                
            except Exception as e:
                self.logger.warning(f"ART integration failed, falling back to standard analysis: {e}")
        
        # 標準分析（無 ART 整合）
        result = await analyst.analyze(state)
        
        self.logger.info(f"完成 {stock_id} {analyst_name}", extra={
            'stock_id': stock_id,
            'user_id': user_context['user_id'],
            'analysis_type': analysis_type,
            'recommendation': result.recommendation,
            'confidence': result.confidence,
            'art_integrated': False
        })
        
        return result, {'art_system_status': 'disabled' if not self._art_initialized else 'fallback'}

# 創建全域分析師管理器
analyst_manager = AnalystManager()

# ==================== API端點 ====================

@router.post("/analysis/stock", response_model=AnalysisResponse)
async def analyze_stock(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser
):
    """
    執行股票分析
    
    - **stock_id**: 台股代號 (如: 2330, 2454, 2881)
    - **analysis_type**: 分析類型 (支援: fundamental, technical)
    - **user_preferences**: 用戶偏好設置
    
    返回完整的AI分析結果，包括投資建議、目標價、風險評估等。
    """
    try:
        logger.info(f"開始分析請求", extra={
            'stock_id': request.stock_id,
            'analysis_type': request.analysis_type,
            'user_id': getattr(current_user, 'id', 'unknown')
        })
        
        # 執行分析 - 現在返回 (result, art_data) 元組
        result, art_data = await analyst_manager.analyze_stock(
            stock_id=request.stock_id,
            analysis_type=request.analysis_type,
            user=current_user,
            user_preferences=request.user_preferences
        )
        
        # 轉換為API響應格式
        response = AnalysisResponse(
            analysis_id=f"analysis_{uuid.uuid4().hex[:8]}",
            stock_id=result.stock_id,
            analysis_type=result.analysis_type.value,
            recommendation=result.recommendation,
            confidence_level=result.confidence_level.value,
            confidence_score=result.confidence,
            target_price=result.target_price,
            reasoning=result.reasoning or [],
            key_insights=getattr(result, 'key_insights', []),
            risk_factors=result.risk_factors,
            fundamental_metrics=result.fundamental_metrics,
            technical_metrics=result.technical_indicators,
            taiwan_insights=result.taiwan_insights,
            analysis_date=result.analysis_date,
            timestamp=result.timestamp,
            
            # ART 系統整合數據
            art_data=art_data,
            trajectory_id=art_data.get('trajectory_id') if art_data else None,
            personalization_level=art_data.get('personalization_level') if art_data else None,
            reward_signal=art_data.get('reward_signal') if art_data else None
        )
        
        # 背景任務：記錄分析使用情況
        background_tasks.add_task(
            _log_analysis_usage,
            current_user,
            request,
            result
        )
        
        logger.info(f"分析完成", extra={
            'stock_id': request.stock_id,
            'recommendation': result.recommendation,
            'confidence': result.confidence
        })
        
        return response
        
    except Exception as e:
        logger.error(f"分析失敗: {str(e)}", extra={
            'stock_id': request.stock_id,
            'analysis_type': request.analysis_type,
            'error': str(e)
        })
        
        await handle_error(e, {
            'endpoint': 'analyze_stock',
            'stock_id': request.stock_id,
            'analysis_type': request.analysis_type
        })
        
        raise HTTPException(
            status_code=500,
            detail=f"分析失敗: {str(e)}"
        )

@router.get("/analysis/history", response_model=List[AnalysisResponse])
async def get_analysis_history(
    current_user: CurrentUser,
    request: AnalysisHistoryRequest = Depends()
):
    """
    獲取分析歷史記錄
    
    返回用戶的分析歷史，支援篩選和分頁。
    """
    try:
        # TODO: 實作從資料庫或快取中獲取歷史記錄
        # 目前返回空列表，之後需要整合資料庫存儲
        
        logger.info(f"查詢分析歷史", extra={
            'user_id': getattr(current_user, 'id', 'unknown'),
            'filters': {
                'stock_id': request.stock_id,
                'analysis_type': request.analysis_type,
                'limit': request.limit,
                'offset': request.offset
            }
        })
        
        return []  # 臨時返回空列表
        
    except Exception as e:
        logger.error(f"查詢歷史失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="查詢分析歷史失敗"
        )

@router.get("/analysts/status", response_model=List[AnalystStatus])
async def get_analysts_status(
    current_user: CurrentUser
):
    """
    獲取所有分析師的狀態
    
    返回系統中所有可用分析師的狀態信息。
    """
    try:
        statuses = []
        
        # 基本面分析師狀態
        fundamentals_analyst = await analyst_manager.get_fundamentals_analyst()
        
        status = AnalystStatus(
            analyst_id="fundamentals_analyst",
            analyst_type="基本面分析師",
            status="online",
            available_features=[
                "財務指標分析",
                "估值分析", 
                "產業比較",
                "投資建議生成",
                "風險評估",
                "台灣市場洞察"
            ],
            art_integration={
                "status": "active",
                "personalization": "enabled",
                "learning_data": "collecting"
            }
        )
        
        statuses.append(status)
        
        # 技術分析師狀態
        technical_analyst = await analyst_manager.get_technical_analyst()
        
        tech_status = AnalystStatus(
            analyst_id="technical_analyst",
            analyst_type="技術分析師",
            status="online",
            available_features=[
                "技術指標分析",
                "移動平均線分析",
                "RSI、MACD、KD指標",
                "支撐阻力位計算", 
                "圖表模式識別",
                "交易信號生成",
                "個人化分析建議",
                "台股盤勢特徵"
            ],
            art_integration={
                "status": "active",
                "personalization": "enabled",
                "learning_data": "collecting",
                "signal_optimization": "enabled"
            }
        )
        
        statuses.append(tech_status)
        
        logger.info(f"返回分析師狀態", extra={
            'analysts_count': len(statuses),
            'user_id': getattr(current_user, 'id', 'unknown')
        })
        
        return statuses
        
    except Exception as e:
        logger.error(f"獲取分析師狀態失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="獲取分析師狀態失敗"
        )

@router.get("/analysis/supported-stocks")
async def get_supported_stocks(
    current_user: CurrentUser
):
    """
    獲取支援的股票列表
    
    返回系統支援分析的股票代號列表。
    """
    try:
        # Taiwan股市主要股票
        supported_stocks = {
            "半導體": {
                "2330": {"name": "台積電", "market_cap": "large"},
                "2454": {"name": "聯發科", "market_cap": "large"},
                "3711": {"name": "日月光投控", "market_cap": "large"},
                "2317": {"name": "鴻海", "market_cap": "large"},
                "2303": {"name": "聯電", "market_cap": "medium"}
            },
            "金融": {
                "2882": {"name": "國泰金", "market_cap": "large"},
                "2881": {"name": "富邦金", "market_cap": "large"},
                "2891": {"name": "中信金", "market_cap": "large"},
                "2892": {"name": "第一金", "market_cap": "medium"},
                "2880": {"name": "華南金", "market_cap": "medium"}
            },
            "電子": {
                "2382": {"name": "廣達", "market_cap": "large"},
                "3008": {"name": "大立光", "market_cap": "large"},
                "2357": {"name": "華碩", "market_cap": "medium"}
            }
        }
        
        return {
            "supported_stocks": supported_stocks,
            "total_stocks": sum(len(stocks) for stocks in supported_stocks.values()),
            "analysis_types": ["fundamental", "technical"],
            "update_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取支援股票列表失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="獲取支援股票列表失敗"
        )

@router.get("/user/personalization")
async def get_user_personalization(
    current_user: CurrentUser
):
    """
    獲取用戶個人化數據
    
    返回用戶的ART系統個人化學習數據，包括分析偏好、推薦分析師等。
    """
    try:
        user_id = getattr(current_user, 'id', None)
        if not user_id:
            raise HTTPException(status_code=400, detail="無效的用戶ID")
        
        # 獲取個人化數據
        if analyst_manager._art_initialized and analyst_manager.art_integration:
            personalization_data = analyst_manager.art_integration.get_user_personalization_data(user_id)
            
            return {
                "user_id": user_id,
                "art_system_enabled": True,
                "personalization_data": personalization_data,
                "system_status": analyst_manager.art_integration.get_system_status()
            }
        else:
            return {
                "user_id": user_id,
                "art_system_enabled": False,
                "message": "ART系統未啟用，使用標準分析模式",
                "personalization_data": None
            }
        
    except Exception as e:
        logger.error(f"獲取用戶個人化數據失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="獲取用戶個人化數據失敗"
        )

@router.get("/art/system-status")
async def get_art_system_status(
    current_user: CurrentUser
):
    """
    獲取ART系統狀態
    
    返回ART系統的完整狀態信息，包括組件健康狀態、指標數據等。
    """
    try:
        if analyst_manager._art_initialized and analyst_manager.art_integration:
            system_status = analyst_manager.art_integration.get_system_status()
            
            return {
                "art_system_available": True,
                "system_status": system_status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "art_system_available": False,
                "message": "ART系統未初始化",
                "available_components": ART_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"獲取ART系統狀態失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="獲取ART系統狀態失敗"
        )
        
    except Exception as e:
        logger.error(f"獲取支援股票列表失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="獲取支援股票列表失敗"
        )

# ==================== 工具函數 ====================

async def _log_analysis_usage(
    user: CurrentUser,
    request: AnalysisRequest,
    result: AnalysisResult
):
    """記錄分析使用情況的背景任務"""
    try:
        logger.info("記錄分析使用情況", extra={
            'user_id': getattr(user, 'id', 'unknown'),
            'stock_id': request.stock_id,
            'analysis_type': request.analysis_type,
            'recommendation': result.recommendation,
            'confidence': result.confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        # TODO: 將使用記錄存入資料庫
        # TODO: 更新用戶API配額使用量
        # TODO: 觸發ART學習數據收集
        
    except Exception as e:
        logger.error(f"記錄分析使用失敗: {str(e)}")

# ==================== WebSocket分析串流支援 ====================

@router.websocket("/analysis/stream/{stock_id}")
async def analysis_stream(websocket: WebSocket, stock_id: str):
    """
    即時分析串流
    
    提供即時分析結果推送，支援長時間分析的進度更新。
    整合ART系統和對話系統。
    """
    await websocket.accept()
    
    try:
        logger.info(f"開始WebSocket分析串流 - 股票: {stock_id}")
        
        # 發送連接確認
        await websocket.send_json({
            "type": "connected",
            "stock_id": stock_id,
            "message": f"已連接到 {stock_id} 分析串流",
            "timestamp": datetime.now().isoformat()
        })
        
        # 模擬分析流程
        analysis_stages = [
            {"stage": "initialization", "message": "初始化分析環境...", "progress": 10},
            {"stage": "data_fetching", "message": f"獲取 {stock_id} 最新數據...", "progress": 25},
            {"stage": "fundamental_analysis", "message": "執行基本面分析...", "progress": 50},
            {"stage": "technical_analysis", "message": "執行技術面分析...", "progress": 70},
            {"stage": "art_integration", "message": "ART系統個人化分析...", "progress": 85},
            {"stage": "generating_report", "message": "生成分析報告...", "progress": 95},
            {"stage": "completed", "message": "分析完成", "progress": 100}
        ]
        
        for stage_info in analysis_stages:
            await websocket.send_json({
                "type": "progress",
                "stock_id": stock_id,
                **stage_info,
                "timestamp": datetime.now().isoformat()
            })
            
            # 模擬處理時間
            await asyncio.sleep(2)
            
            # 在特定階段發送詳細信息
            if stage_info["stage"] == "fundamental_analysis":
                await websocket.send_json({
                    "type": "partial_result",
                    "stock_id": stock_id,
                    "data": {
                        "pe_ratio": 18.5,
                        "pb_ratio": 2.3,
                        "roe": 22.1,
                        "revenue_growth": 12.5,
                        "analysis": f"{stock_id} 基本面指標表現良好"
                    },
                    "timestamp": datetime.now().isoformat()
                })
            
            elif stage_info["stage"] == "art_integration":
                await websocket.send_json({
                    "type": "art_insight",
                    "stock_id": stock_id,
                    "data": {
                        "personalization_level": "advanced",
                        "user_preference_match": 0.85,
                        "art_recommendation": "基於您的投資偏好，建議重點關注長期價值成長",
                        "trajectory_id": f"traj_{uuid.uuid4().hex[:8]}"
                    },
                    "timestamp": datetime.now().isoformat()
                })
        
        # 發送最終分析結果
        final_result = {
            "type": "final_result",
            "stock_id": stock_id,
            "analysis_result": {
                "recommendation": "BUY",
                "confidence_level": "HIGH", 
                "confidence_score": 0.87,
                "target_price": 650.0,
                "current_price": 580.0,
                "upside_potential": 12.07,
                "reasoning": [
                    f"{stock_id} 基本面強勁，ROE達到22.1%",
                    "半導體產業處於上升週期",
                    "估值相對合理，PE比率低於同業平均"
                ],
                "key_insights": [
                    "AI和HPC需求驅動長期成長",
                    "製程技術領先優勢明顯",
                    "現金流穩健，股息率吸引人"
                ],
                "risk_factors": [
                    "地緣政治風險",
                    "半導體週期性波動",
                    "匯率波動風險"
                ]
            },
            "art_data": {
                "personalized": True,
                "trajectory_collected": True,
                "reward_signal": 0.82
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send_json(final_result)
        
        # 保持連接等待客戶端關閉
        while True:
            try:
                message = await websocket.receive_text()
                if message == "close":
                    break
            except:
                break
        
        await websocket.close()
        logger.info(f"WebSocket分析串流完成 - 股票: {stock_id}")
        
    except Exception as e:
        logger.error(f"WebSocket分析串流錯誤: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "分析過程發生錯誤",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass
        finally:
            await websocket.close()