"""
轉換API端點 - 處理註冊轉換相關的API請求

包含：
1. 用戶註冊轉換
2. 轉換步驟追蹤
3. 轉換分析數據
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import text

from ..services.conversion_service import (
    ConversionService, 
    UserRegistrationData, 
    ConversionStepData,
    AlphaInsightPurchaseData
)
from ..utils.database_manager import get_database_manager

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/conversion", tags=["conversion"])

# Pydantic 模型
class UserRegistrationRequest(BaseModel):
    """用戶註冊請求"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    result_id: Optional[str] = None
    session_id: Optional[str] = None
    utm_params: Optional[Dict[str, str]] = None
    referrer: Optional[str] = None
    ab_variant: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('姓名至少需要2個字符')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.strip()) < 8:
            raise ValueError('電話號碼格式不正確')
        return v.strip() if v else None

class ConversionStepRequest(BaseModel):
    """轉換步驟追蹤請求"""
    session_id: str
    step: str
    action: str
    data: Optional[Dict[str, Any]] = None

class ConversionAnalyticsRequest(BaseModel):
    """轉換分析請求"""
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('結束日期必須晚於開始日期')
        return v

# 依賴注入
def get_conversion_service():
    """獲取轉換服務實例"""
    db_manager = get_database_manager()
    return ConversionService(db_manager)

@router.post("/register")
async def register_user(
    request: UserRegistrationRequest,
    background_tasks: BackgroundTasks,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """
    用戶註冊轉換
    
    處理從測試頁面來的用戶註冊，包括：
    - 創建用戶賬號
    - 同步測試數據
    - 發送歡迎郵件
    - 記錄轉換數據
    """
    try:
        # 轉換請求數據
        registration_data = UserRegistrationData(
            name=request.name,
            email=request.email,
            phone=request.phone,
            result_id=request.result_id,
            session_id=request.session_id,
            utm_params=request.utm_params,
            referrer=request.referrer,
            ab_variant=request.ab_variant
        )
        
        # 處理註冊
        response = await conversion_service.handle_registration_from_test(registration_data)
        
        if response.success:
            # 在背景任務中處理額外的後續操作
            background_tasks.add_task(
                _handle_post_registration_tasks,
                response.user_id,
                registration_data
            )
            
            return {
                "success": True,
                "message": response.message,
                "user_id": response.user_id,
                "next_steps": response.next_steps,
                "welcome_email_sent": response.welcome_email_sent
            }
        else:
            return {
                "success": False,
                "message": response.message,
                "next_steps": response.next_steps
            }
            
    except Exception as e:
        logger.error(f"Registration endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"註冊處理失敗：{str(e)}"
        )

@router.post("/track-step")
async def track_conversion_step(
    request: ConversionStepRequest,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """
    追蹤轉換步驟
    
    記錄用戶在轉換漏斗中的各個步驟，用於分析和優化
    """
    try:
        step_data = ConversionStepData(
            session_id=request.session_id,
            step=request.step,
            action=request.action,
            data=request.data
        )
        
        success = await conversion_service.track_conversion_step(step_data)
        
        if success:
            return {
                "success": True,
                "message": "轉換步驟記錄成功"
            }
        else:
            return {
                "success": False,
                "message": "轉換步驟記錄失敗"
            }
            
    except Exception as e:
        logger.error(f"Track conversion step error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"轉換步驟追蹤失敗：{str(e)}"
        )

@router.get("/analytics")
async def get_conversion_analytics(
    start_date: datetime,
    end_date: datetime,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """
    獲取轉換分析數據
    
    提供轉換漏斗分析、A/B測試結果等數據
    """
    try:
        # 驗證日期範圍
        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="結束日期必須晚於開始日期"
            )
        
        # 限制查詢範圍（最多90天）
        if (end_date - start_date).days > 90:
            raise HTTPException(
                status_code=400,
                detail="查詢範圍不能超過90天"
            )
        
        analytics_data = await conversion_service.get_conversion_analytics(
            start_date, end_date
        )
        
        return {
            "success": True,
            "data": analytics_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversion analytics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取轉換分析數據失敗：{str(e)}"
        )

@router.get("/funnel-summary")
async def get_funnel_summary(
    days: int = 7,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """
    獲取轉換漏斗摘要
    
    提供最近N天的轉換漏斗關鍵指標
    """
    try:
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=400,
                detail="天數範圍必須在1-90之間"
            )
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await conversion_service.get_conversion_analytics(
            start_date, end_date
        )
        
        # 提取關鍵指標
        summary = {
            "period_days": days,
            "total_views": 0,
            "total_registrations": 0,
            "conversion_rate": 0.0,
            "funnel_steps": [],
            "ab_test_performance": {}
        }
        
        if analytics_data.get("funnel_data"):
            funnel_data = analytics_data["funnel_data"]
            conversion_rates = analytics_data.get("conversion_rates", {})
            
            # 統計總數
            for step_data in funnel_data:
                if step_data["step"] == "result_view":
                    summary["total_views"] = step_data["unique_sessions"]
                elif step_data["step"] == "register_complete":
                    summary["total_registrations"] = step_data["unique_sessions"]
            
            # 計算總轉換率
            if summary["total_views"] > 0:
                summary["conversion_rate"] = (summary["total_registrations"] / summary["total_views"]) * 100
            
            summary["funnel_steps"] = funnel_data
            summary["conversion_rates"] = conversion_rates
        
        # 處理A/B測試數據
        if analytics_data.get("ab_test_data"):
            ab_data = analytics_data["ab_test_data"]
            ab_summary = {}
            
            for row in ab_data:
                variant = row["variant"]
                if variant not in ab_summary:
                    ab_summary[variant] = {"total_actions": 0, "registrations": 0}
                
                ab_summary[variant]["total_actions"] += row["count"]
                if row["step"] == "register_complete":
                    ab_summary[variant]["registrations"] = row["count"]
            
            # 計算A/B測試轉換率
            for variant, data in ab_summary.items():
                if data["total_actions"] > 0:
                    data["conversion_rate"] = (data["registrations"] / data["total_actions"]) * 100
                else:
                    data["conversion_rate"] = 0.0
            
            summary["ab_test_performance"] = ab_summary
        
        return {
            "success": True,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get funnel summary error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取漏斗摘要失敗：{str(e)}"
        )

@router.post("/prefill-data")
async def get_prefill_data(
    result_id: str,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """
    獲取註冊表單預填數據
    
    基於測試結果提供表單預填信息
    """
    try:
        # 獲取測試結果
        test_result = await conversion_service._get_test_result(result_id)
        
        if not test_result:
            raise HTTPException(
                status_code=404,
                detail="找不到測試結果"
            )
        
        # 構建預填數據
        prefill_data = {
            "personality_type": test_result["personality_type"]["display_name"],
            "percentile": test_result["percentile"],
            "investment_style": test_result["personality_type"]["investment_style"],
            "recommendations": test_result["recommendations"][:3],  # 只顯示前3個建議
            "suggested_next_steps": conversion_service._get_onboarding_steps(test_result)[:3]
        }
        
        return {
            "success": True,
            "prefill_data": prefill_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get prefill data error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取預填數據失敗：{str(e)}"
        )

# 背景任務函數
async def _handle_post_registration_tasks(user_id: str, registration_data: UserRegistrationData):
    """處理註冊後的背景任務"""
    try:
        # 這裡可以添加額外的後續處理
        # 例如：發送到CRM系統、觸發營銷自動化等
        
        logger.info(f"Post-registration tasks completed for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Post-registration tasks failed for user {user_id}: {str(e)}")

# ==================== 按次付費整合端點 ====================

class AlphaInsightInterestRequest(BaseModel):
    """阿爾法洞察興趣追蹤請求"""
    user_id: int
    stock_id: str
    insight_type: str
    session_id: Optional[str] = None

class AlphaInsightPurchaseRequest(BaseModel):
    """阿爾法洞察購買請求"""
    user_id: int
    stock_id: str
    insight_type: str
    amount: float = 5.00
    session_id: Optional[str] = None
    source: str = "personality_test_conversion"

class AlphaRecommendationRequest(BaseModel):
    """阿爾法洞察推薦請求"""
    user_id: int
    personality_type: str

@router.post("/alpha-insight/track-interest")
async def track_alpha_insight_interest(
    request: AlphaInsightInterestRequest,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """追蹤用戶對阿爾法洞察的興趣"""
    try:
        success = await conversion_service.track_alpha_insight_interest(
            user_id=request.user_id,
            stock_id=request.stock_id,
            insight_type=request.insight_type,
            session_id=request.session_id
        )
        
        return {
            "success": success,
            "message": "興趣追蹤成功" if success else "興趣追蹤失敗"
        }
        
    except Exception as e:
        logger.error(f"Track alpha insight interest error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"興趣追蹤失敗：{str(e)}"
        )

@router.post("/alpha-insight/purchase")
async def purchase_alpha_insight(
    request: AlphaInsightPurchaseRequest,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """處理阿爾法洞察購買（整合轉換追蹤）"""
    try:
        purchase_data = AlphaInsightPurchaseData(
            user_id=request.user_id,
            stock_id=request.stock_id,
            insight_type=request.insight_type,
            amount=request.amount,
            session_id=request.session_id,
            source=request.source
        )
        
        result = await conversion_service.handle_alpha_insight_purchase(purchase_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Alpha insight purchase error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"購買處理失敗：{str(e)}"
        )

@router.post("/alpha-insight/recommendations")
async def get_personalized_alpha_recommendations(
    request: AlphaRecommendationRequest,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """獲取基於投資人格的個性化阿爾法洞察推薦"""
    try:
        recommendations = await conversion_service.get_personalized_alpha_recommendations(
            user_id=request.user_id,
            personality_type=request.personality_type
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total_count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Get alpha recommendations error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取推薦失敗：{str(e)}"
        )

@router.get("/alpha-insight/analytics")
async def get_alpha_purchase_analytics(
    days: int = 30,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """獲取阿爾法洞察購買分析"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400,
                detail="天數範圍必須在1-365之間"
            )
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await conversion_service.get_alpha_purchase_analytics(
            start_date, end_date
        )
        
        return {
            "success": True,
            "data": analytics_data,
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alpha purchase analytics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取分析數據失敗：{str(e)}"
        )

@router.get("/alpha-insight/conversion-funnel")
async def get_alpha_conversion_funnel(
    days: int = 7,
    conversion_service: ConversionService = Depends(get_conversion_service)
):
    """獲取阿爾法洞察轉換漏斗數據"""
    try:
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=400,
                detail="天數範圍必須在1-90之間"
            )
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await conversion_service.get_alpha_purchase_analytics(
            start_date, end_date
        )
        
        # 提取轉換漏斗關鍵指標
        funnel_summary = {
            "period_days": days,
            "conversion_rates": analytics_data.get("conversion_rates", {}),
            "purchase_summary": analytics_data.get("purchase_summary", {}),
            "popular_insights": analytics_data.get("popular_insights", [])
        }
        
        return {
            "success": True,
            "funnel_data": funnel_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alpha conversion funnel error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取轉換漏斗數據失敗：{str(e)}"
        )

# 健康檢查端點
@router.get("/health")
async def health_check():
    """轉換服務健康檢查"""
    return {
        "status": "healthy",
        "service": "conversion",
        "timestamp": datetime.now().isoformat()
    }