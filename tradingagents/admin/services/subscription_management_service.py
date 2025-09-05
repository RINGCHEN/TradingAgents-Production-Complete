"""
會員訂閱管理服務
提供完整的會員訂閱管理功能實現
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..models.subscription_management import (
    SubscriptionPlan, 
    UserSubscription, 
    SubscriptionStats,
    CreateSubscriptionPlanRequest,
    UpdateSubscriptionPlanRequest,
    SubscriptionAnalytics
)

logger = logging.getLogger(__name__)

class SubscriptionManagementService:
    """會員訂閱管理服務"""
    
    def __init__(self):
        self.logger = logger
    
    async def get_subscription_plans(self, active_only: bool = False) -> List[SubscriptionPlan]:
        """獲取所有訂閱方案"""
        try:
            # 模擬數據 - 實際實現中應該從數據庫獲取
            plans = [
                SubscriptionPlan(
                    id="plan_free",
                    name="免費方案",
                    description="基礎功能，適合新手用戶",
                    price=0.0,
                    currency="TWD",
                    billing_cycle="monthly",
                    features=[
                        "基礎股票查詢",
                        "每日3次AI分析",
                        "基礎圖表功能"
                    ],
                    max_api_calls=100,
                    max_ai_requests=3,
                    is_active=True,
                    created_at=datetime.now() - timedelta(days=30),
                    updated_at=datetime.now()
                ),
                SubscriptionPlan(
                    id="plan_gold",
                    name="黃金方案",
                    description="進階功能，適合活躍投資者",
                    price=299.0,
                    currency="TWD",
                    billing_cycle="monthly",
                    features=[
                        "無限股票查詢",
                        "每日50次AI分析",
                        "高級圖表功能",
                        "實時市場數據",
                        "投資組合分析"
                    ],
                    max_api_calls=5000,
                    max_ai_requests=50,
                    is_active=True,
                    created_at=datetime.now() - timedelta(days=25),
                    updated_at=datetime.now()
                ),
                SubscriptionPlan(
                    id="plan_diamond",
                    name="鑽石方案",
                    description="專業功能，適合專業投資者",
                    price=999.0,
                    currency="TWD",
                    billing_cycle="monthly",
                    features=[
                        "無限股票查詢",
                        "無限AI分析",
                        "專業圖表工具",
                        "實時市場數據",
                        "高級投資組合分析",
                        "專屬客服支援",
                        "API訪問權限"
                    ],
                    max_api_calls=-1,  # 無限制
                    max_ai_requests=-1,  # 無限制
                    is_active=True,
                    created_at=datetime.now() - timedelta(days=20),
                    updated_at=datetime.now()
                )
            ]
            
            if active_only:
                plans = [plan for plan in plans if plan.is_active]
            
            return plans
            
        except Exception as e:
            self.logger.error(f"獲取訂閱方案失敗: {e}")
            raise
    
    async def create_subscription_plan(self, plan_data: CreateSubscriptionPlanRequest) -> SubscriptionPlan:
        """創建新的訂閱方案"""
        try:
            # 驗證數據
            if plan_data.price < 0:
                raise ValueError("價格不能為負數")
            
            if not plan_data.name.strip():
                raise ValueError("方案名稱不能為空")
            
            # 創建新方案
            new_plan = SubscriptionPlan(
                id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=plan_data.name,
                description=plan_data.description,
                price=plan_data.price,
                currency=plan_data.currency,
                billing_cycle=plan_data.billing_cycle,
                features=plan_data.features,
                max_api_calls=plan_data.max_api_calls,
                max_ai_requests=plan_data.max_ai_requests,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 實際實現中應該保存到數據庫
            self.logger.info(f"創建訂閱方案: {new_plan.name}")
            
            return new_plan
            
        except Exception as e:
            self.logger.error(f"創建訂閱方案失敗: {e}")
            raise
    
    async def get_user_subscriptions(
        self, 
        page: int = 1, 
        limit: int = 20,
        status: Optional[str] = None,
        plan_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[UserSubscription]:
        """獲取用戶訂閱列表"""
        try:
            # 模擬數據
            subscriptions = [
                UserSubscription(
                    id="sub_001",
                    user_id="user_001",
                    username="john_doe",
                    email="john@example.com",
                    plan_id="plan_gold",
                    plan_name="黃金方案",
                    status="active",
                    start_date=datetime.now() - timedelta(days=15),
                    end_date=datetime.now() + timedelta(days=15),
                    auto_renew=True,
                    payment_method="credit_card",
                    created_at=datetime.now() - timedelta(days=15),
                    updated_at=datetime.now()
                ),
                UserSubscription(
                    id="sub_002",
                    user_id="user_002",
                    username="jane_smith",
                    email="jane@example.com",
                    plan_id="plan_diamond",
                    plan_name="鑽石方案",
                    status="active",
                    start_date=datetime.now() - timedelta(days=10),
                    end_date=datetime.now() + timedelta(days=20),
                    auto_renew=True,
                    payment_method="credit_card",
                    created_at=datetime.now() - timedelta(days=10),
                    updated_at=datetime.now()
                ),
                UserSubscription(
                    id="sub_003",
                    user_id="user_003",
                    username="bob_wilson",
                    email="bob@example.com",
                    plan_id="plan_free",
                    plan_name="免費方案",
                    status="active",
                    start_date=datetime.now() - timedelta(days=5),
                    end_date=None,  # 免費方案無到期日
                    auto_renew=False,
                    payment_method=None,
                    created_at=datetime.now() - timedelta(days=5),
                    updated_at=datetime.now()
                )
            ]
            
            # 應用篩選
            if status:
                subscriptions = [sub for sub in subscriptions if sub.status == status]
            
            if plan_id:
                subscriptions = [sub for sub in subscriptions if sub.plan_id == plan_id]
            
            if search:
                search_lower = search.lower()
                subscriptions = [
                    sub for sub in subscriptions 
                    if search_lower in sub.username.lower() or search_lower in sub.email.lower()
                ]
            
            # 分頁
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            
            return subscriptions[start_idx:end_idx]
            
        except Exception as e:
            self.logger.error(f"獲取用戶訂閱失敗: {e}")
            raise
    
    async def get_subscription_stats(self) -> SubscriptionStats:
        """獲取訂閱統計數據"""
        try:
            # 模擬統計數據
            stats = SubscriptionStats(
                total_subscribers=1247,
                active_subscribers=892,
                free_users=355,
                paid_users=537,
                monthly_revenue=267430.0,
                churn_rate=0.05,
                conversion_rate=0.12,
                average_revenue_per_user=298.5,
                plan_distribution={
                    "免費方案": 355,
                    "黃金方案": 437,
                    "鑽石方案": 100
                },
                growth_rate=0.08
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"獲取訂閱統計失敗: {e}")
            raise
    
    async def get_subscription_analytics(self, days: int = 30) -> SubscriptionAnalytics:
        """獲取訂閱分析數據"""
        try:
            # 模擬分析數據
            analytics = SubscriptionAnalytics(
                period_days=days,
                new_subscriptions=45,
                cancelled_subscriptions=12,
                upgraded_subscriptions=23,
                downgraded_subscriptions=8,
                revenue_trend=[
                    {"date": "2024-01-01", "revenue": 245000},
                    {"date": "2024-01-02", "revenue": 248000},
                    {"date": "2024-01-03", "revenue": 252000},
                    {"date": "2024-01-04", "revenue": 255000},
                    {"date": "2024-01-05", "revenue": 267430}
                ],
                subscription_trend=[
                    {"date": "2024-01-01", "count": 1200},
                    {"date": "2024-01-02", "count": 1215},
                    {"date": "2024-01-03", "count": 1230},
                    {"date": "2024-01-04", "count": 1240},
                    {"date": "2024-01-05", "count": 1247}
                ],
                top_performing_plans=[
                    {"plan_name": "黃金方案", "subscribers": 437, "revenue": 130663},
                    {"plan_name": "鑽石方案", "subscribers": 100, "revenue": 99900},
                    {"plan_name": "免費方案", "subscribers": 355, "revenue": 0}
                ]
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"獲取訂閱分析失敗: {e}")
            raise
    
    async def create_user_subscription(self, user_id: str, plan_id: str) -> UserSubscription:
        """為用戶創建訂閱"""
        try:
            # 驗證用戶和方案是否存在
            # 實際實現中應該檢查數據庫
            
            new_subscription = UserSubscription(
                id=f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                username="new_user",  # 實際應該從用戶表獲取
                email="new_user@example.com",
                plan_id=plan_id,
                plan_name="方案名稱",  # 實際應該從方案表獲取
                status="active",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                auto_renew=True,
                payment_method="credit_card",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.logger.info(f"為用戶 {user_id} 創建訂閱: {plan_id}")
            
            return new_subscription
            
        except Exception as e:
            self.logger.error(f"創建用戶訂閱失敗: {e}")
            raise
    
    async def cancel_user_subscription(self, user_id: str, reason: Optional[str] = None):
        """取消用戶訂閱"""
        try:
            # 實際實現中應該更新數據庫
            self.logger.info(f"取消用戶 {user_id} 的訂閱，原因: {reason}")
            
            return {"message": "訂閱已取消", "cancelled_at": datetime.now()}
            
        except Exception as e:
            self.logger.error(f"取消用戶訂閱失敗: {e}")
            raise
    
    async def get_revenue_report(self, start_date: Optional[str], end_date: Optional[str]):
        """獲取收入報告"""
        try:
            # 模擬收入報告
            report = {
                "period": {
                    "start_date": start_date or "2024-01-01",
                    "end_date": end_date or "2024-01-31"
                },
                "total_revenue": 267430.0,
                "subscription_revenue": 245000.0,
                "upgrade_revenue": 22430.0,
                "refunds": -5000.0,
                "net_revenue": 262430.0,
                "revenue_by_plan": {
                    "黃金方案": 130663.0,
                    "鑽石方案": 99900.0,
                    "免費方案": 0.0
                },
                "daily_revenue": [
                    {"date": "2024-01-01", "revenue": 8500.0},
                    {"date": "2024-01-02", "revenue": 9200.0},
                    {"date": "2024-01-03", "revenue": 8800.0}
                ]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"獲取收入報告失敗: {e}")
            raise
    
    async def get_expiring_subscriptions(self, days: int = 7):
        """獲取即將到期的訂閱"""
        try:
            # 模擬即將到期的訂閱
            expiring = [
                {
                    "subscription_id": "sub_001",
                    "user_id": "user_001",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "plan_name": "黃金方案",
                    "expires_at": datetime.now() + timedelta(days=3),
                    "auto_renew": False
                },
                {
                    "subscription_id": "sub_004",
                    "user_id": "user_004",
                    "username": "alice_brown",
                    "email": "alice@example.com",
                    "plan_name": "鑽石方案",
                    "expires_at": datetime.now() + timedelta(days=5),
                    "auto_renew": True
                }
            ]
            
            return expiring
            
        except Exception as e:
            self.logger.error(f"獲取即將到期訂閱失敗: {e}")
            raise