#!/usr/bin/env python3
"""
多層次定價策略API端點
Task 5.3 - 多層次定價策略的REST API接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..services.pricing_strategy_service import PricingStrategyService

# 模擬導入，如果模塊不存在
try:
    from ..utils.logging_config import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)
router = APIRouter(prefix="/pricing", tags=["pricing"])

# 數據模型
class PricingRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="用戶ID")
    session_id: Optional[str] = Field(None, description="會話ID")
    user_attributes: Optional[Dict[str, Any]] = Field(None, description="用戶屬性")

class CouponApplicationRequest(BaseModel):
    coupon_code: str = Field(..., description="優惠券代碼")
    plan_id: str = Field(..., description="方案ID")
    user_id: Optional[int] = Field(None, description="用戶ID")
    session_id: Optional[str] = Field(None, description="會話ID")

class PlanSelectionRequest(BaseModel):
    plan_id: str = Field(..., description="選擇的方案ID")
    user_id: Optional[int] = Field(None, description="用戶ID")
    session_id: Optional[str] = Field(None, description="會話ID")
    coupon_code: Optional[str] = Field(None, description="使用的優惠券代碼")

# 服務實例
pricing_service = PricingStrategyService()

@router.get("/plans")
async def get_pricing_plans(
    user_id: Optional[int] = Query(None, description="用戶ID"),
    session_id: Optional[str] = Query(None, description="會話ID"),
    source: Optional[str] = Query(None, description="來源頁面"),
    utm_campaign: Optional[str] = Query(None, description="營銷活動")
):
    """
    獲取定價方案
    設計價格錨定：展示高價選項突出標準方案價值
    實現動態定價：根據用戶行為調整價格展示
    """
    try:
        # 構建用戶屬性
        user_attributes = {}
        
        if source:
            user_attributes['source'] = source
        if utm_campaign:
            user_attributes['utm_campaign'] = utm_campaign
        
        # 模擬用戶行為數據（實際應從數據庫獲取）
        if user_id:
            user_attributes.update({
                'user_age_days': 1,  # 新用戶
                'visit_count': 1,
                'engagement_score': 50,
                'investment_experience': 'beginner',
                'portfolio_size': 10000
            })
        else:
            user_attributes.update({
                'is_anonymous': True,
                'visit_count': 1,
                'source': source or 'direct'
            })
        
        result = pricing_service.get_pricing_plans(
            user_id=user_id,
            session_id=session_id,
            user_attributes=user_attributes
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "獲取定價方案失敗"))
        
        return {
            "success": True,
            "message": "定價方案獲取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取定價方案失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取定價方案失敗")

@router.post("/apply-coupon")
async def apply_coupon(request: CouponApplicationRequest):
    """
    應用優惠券
    開發優惠券系統：新用戶專屬折扣碼
    """
    try:
        result = pricing_service.apply_coupon(
            coupon_code=request.coupon_code,
            plan_id=request.plan_id,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "優惠券應用失敗"))
        
        return {
            "success": True,
            "message": "優惠券應用成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"應用優惠券失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="應用優惠券失敗")

@router.get("/coupons")
async def get_available_coupons(
    user_id: Optional[int] = Query(None, description="用戶ID"),
    user_type: Optional[str] = Query(None, description="用戶類型")
):
    """
    獲取可用優惠券
    """
    try:
        # 構建用戶屬性
        user_attributes = {}
        
        if user_type:
            user_attributes['user_type'] = user_type
        
        if user_id:
            # 模擬用戶數據
            user_attributes.update({
                'registration_days': 1,  # 新用戶
                'subscription_status': 'none',
                'feature_usage': 30
            })
        
        result = pricing_service.get_available_coupons(
            user_id=user_id,
            user_attributes=user_attributes
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "獲取優惠券失敗"))
        
        return {
            "success": True,
            "message": "可用優惠券獲取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取可用優惠券失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取可用優惠券失敗")

@router.post("/select-plan")
async def select_plan(request: PlanSelectionRequest):
    """
    選擇定價方案
    """
    try:
        # 記錄方案選擇
        selection_data = {
            'plan_id': request.plan_id,
            'user_id': request.user_id,
            'session_id': request.session_id,
            'selected_at': datetime.utcnow().isoformat()
        }
        
        # 如果有優惠券，先應用優惠券
        final_pricing = None
        if request.coupon_code:
            coupon_result = pricing_service.apply_coupon(
                coupon_code=request.coupon_code,
                plan_id=request.plan_id,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            if coupon_result.get("success"):
                final_pricing = coupon_result['discount_details']
                selection_data['coupon_applied'] = True
                selection_data['coupon_code'] = request.coupon_code
            else:
                return {
                    "success": False,
                    "error": f"優惠券應用失敗: {coupon_result.get('error', '未知錯誤')}"
                }
        
        # 這裡應該集成支付系統，暫時返回選擇確認
        return {
            "success": True,
            "message": "方案選擇成功",
            "data": {
                "selection": selection_data,
                "final_pricing": final_pricing,
                "next_step": "proceed_to_payment"
            }
        }
        
    except Exception as e:
        logger.error(f"選擇方案失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="選擇方案失敗")

@router.get("/comparison")
async def get_plan_comparison():
    """
    獲取方案對比數據
    創建付費方案對比：突出推薦方案的優勢
    """
    try:
        # 獲取基礎方案數據
        plans_result = pricing_service.get_pricing_plans()
        
        if not plans_result.get("success"):
            raise HTTPException(status_code=400, detail="獲取方案對比失敗")
        
        comparison_data = plans_result.get('comparison', {})
        plans = plans_result.get('plans', [])
        
        # 增強對比數據
        enhanced_comparison = {
            'plans_overview': [
                {
                    'id': plan['id'],
                    'name': plan['name'],
                    'tier': plan['tier'],
                    'monthly_price': plan['monthly_price'],
                    'is_recommended': plan.get('is_recommended', False),
                    'is_popular': plan.get('is_popular', False),
                    'value_proposition': plan.get('value_proposition', ''),
                    'key_features': plan.get('features', [])[:3]  # 前3個主要功能
                } for plan in plans
            ],
            'detailed_comparison': comparison_data.get('comparison_matrix', []),
            'recommendations': comparison_data.get('highlight_differences', {}),
            'value_propositions': comparison_data.get('value_propositions', {})
        }
        
        return {
            "success": True,
            "message": "方案對比數據獲取成功",
            "data": enhanced_comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取方案對比失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取方案對比失敗")

@router.get("/analytics")
async def get_pricing_analytics():
    """
    獲取定價分析數據
    """
    try:
        result = pricing_service.get_pricing_analytics()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "獲取分析數據失敗"))
        
        return {
            "success": True,
            "message": "定價分析數據獲取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取定價分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取定價分析失敗")

@router.get("/health")
async def health_check():
    """
    定價系統健康檢查
    """
    try:
        service_status = {
            "service": "pricing_strategy",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        # 檢查服務狀態
        if hasattr(pricing_service, 'plans'):
            service_status["plans_count"] = len(pricing_service.plans)
        else:
            service_status["plans_count"] = 0
            
        if hasattr(pricing_service, 'coupons'):
            service_status["coupons_count"] = len(pricing_service.coupons)
        else:
            service_status["coupons_count"] = 0
        
        return {
            "success": True,
            "data": service_status
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "status": "unhealthy"
        }

@router.get("/demo-data")
async def get_demo_data():
    """
    獲取演示數據
    """
    try:
        # 模擬不同用戶場景的定價數據
        demo_scenarios = [
            {
                'name': '新用戶場景',
                'user_attributes': {
                    'user_age_days': 0,
                    'visit_count': 1,
                    'source': 'google_ads'
                },
                'expected_discount': '新用戶50%折扣'
            },
            {
                'name': '回頭客場景',
                'user_attributes': {
                    'user_age_days': 30,
                    'visit_count': 5,
                    'engagement_score': 75
                },
                'expected_discount': '回頭客15%折扣'
            },
            {
                'name': '高價值用戶場景',
                'user_attributes': {
                    'user_age_days': 60,
                    'engagement_score': 90,
                    'portfolio_size': 500000
                },
                'expected_discount': '高價值用戶25%折扣'
            }
        ]
        
        demo_results = []
        
        for scenario in demo_scenarios:
            result = pricing_service.get_pricing_plans(
                user_id=None,
                session_id=f"demo_{scenario['name']}",
                user_attributes=scenario['user_attributes']
            )
            
            if result.get('success'):
                demo_results.append({
                    'scenario': scenario['name'],
                    'user_attributes': scenario['user_attributes'],
                    'pricing_result': result,
                    'has_discount': any(p.get('is_discounted', False) for p in result.get('plans', []))
                })
        
        return {
            "success": True,
            "message": "演示數據獲取成功",
            "data": {
                "scenarios": demo_results,
                "available_coupons": pricing_service.get_available_coupons().get('coupons', [])
            }
        }
        
    except Exception as e:
        logger.error(f"獲取演示數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取演示數據失敗")