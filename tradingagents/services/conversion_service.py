"""
轉換漏斗服務 - ConversionService

處理測試用戶的註冊轉換，包括：
1. 轉換步驟追蹤
2. 用戶註冊處理
3. 個性化歡迎郵件
4. 轉換數據分析
"""

import json
import logging
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from sqlalchemy import text
from ..utils.database_manager import DatabaseManager
from .pay_per_use_service import PayPerUseService

logger = logging.getLogger(__name__)

@dataclass
class ConversionStepData:
    """轉換步驟數據"""
    session_id: str
    step: str
    action: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class UserRegistrationData:
    """用戶註冊數據"""
    name: str
    email: str
    phone: Optional[str] = None
    result_id: Optional[str] = None
    session_id: Optional[str] = None
    utm_params: Optional[Dict[str, str]] = None
    referrer: Optional[str] = None
    ab_variant: Optional[str] = None

@dataclass
class UserRegistrationResponse:
    """用戶註冊響應"""
    user_id: str
    success: bool
    message: str
    next_steps: List[str]
    welcome_email_sent: bool = False

@dataclass
class PersonalizedWelcomeData:
    """個性化歡迎數據"""
    personality_type: str
    display_name: str
    percentile: int
    recommendations: List[str]
    investment_style: str
    next_steps: List[str]

@dataclass
class AlphaInsightPurchaseData:
    """阿爾法洞察購買數據"""
    user_id: int
    stock_id: str
    insight_type: str
    amount: float
    session_id: Optional[str] = None
    source: str = "personality_test_conversion"  # 來源追蹤

class ConversionService:
    """轉換漏斗服務"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.pay_per_use_service = PayPerUseService()
        
    async def track_conversion_step(self, step_data: ConversionStepData) -> bool:
        """追蹤轉換步驟"""
        try:
            if not step_data.timestamp:
                step_data.timestamp = datetime.now()
            
            query = text("""
                INSERT INTO conversion_tracking (
                    session_id, step, action, data, created_at
                ) VALUES (
                    :session_id, :step, :action, :data, :created_at
                )
            """)
            
            await self.db_manager.execute_query(
                query,
                {
                    "session_id": step_data.session_id,
                    "step": step_data.step,
                    "action": step_data.action,
                    "data": json.dumps(step_data.data) if step_data.data else None,
                    "created_at": step_data.timestamp
                }
            )
            
            logger.info(f"Conversion step tracked: {step_data.step} - {step_data.action}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track conversion step: {str(e)}")
            return False
    
    async def handle_registration_from_test(self, registration_data: UserRegistrationData) -> UserRegistrationResponse:
        """處理從測試頁面來的註冊"""
        try:
            # 驗證輸入數據
            if not self._validate_registration_data(registration_data):
                return UserRegistrationResponse(
                    user_id="",
                    success=False,
                    message="註冊數據驗證失敗",
                    next_steps=[]
                )
            
            # 檢查用戶是否已存在
            existing_user = await self._check_existing_user(registration_data.email)
            if existing_user:
                return UserRegistrationResponse(
                    user_id=existing_user["id"],
                    success=False,
                    message="該郵箱已註冊，請直接登入",
                    next_steps=["login"]
                )
            
            # 獲取測試結果（如果有）
            test_result = None
            if registration_data.result_id:
                test_result = await self._get_test_result(registration_data.result_id)
            
            # 創建用戶賬號
            user_id = await self._create_user_account(registration_data, test_result)
            
            # 發送個性化歡迎郵件
            welcome_email_sent = False
            if test_result:
                welcome_email_sent = await self._send_personalized_welcome_email(
                    user_id, registration_data, test_result
                )
            else:
                welcome_email_sent = await self._send_standard_welcome_email(
                    user_id, registration_data
                )
            
            # 記錄轉換成功
            if registration_data.session_id:
                await self.track_conversion_step(ConversionStepData(
                    session_id=registration_data.session_id,
                    step="register_complete",
                    action="user_created",
                    data={
                        "user_id": user_id,
                        "personality_type": test_result.get("personality_type", {}).get("type") if test_result else None,
                        "ab_variant": registration_data.ab_variant,
                        "utm_params": registration_data.utm_params,
                        "referrer": registration_data.referrer
                    }
                ))
            
            # 獲取下一步驟
            next_steps = self._get_onboarding_steps(test_result)
            
            return UserRegistrationResponse(
                user_id=user_id,
                success=True,
                message="註冊成功！歡迎加入 TradingAgents！",
                next_steps=next_steps,
                welcome_email_sent=welcome_email_sent
            )
            
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return UserRegistrationResponse(
                user_id="",
                success=False,
                message=f"註冊失敗：{str(e)}",
                next_steps=[]
            )
    
    def _validate_registration_data(self, data: UserRegistrationData) -> bool:
        """驗證註冊數據"""
        if not data.name or len(data.name.strip()) < 2:
            return False
        
        if not data.email or "@" not in data.email:
            return False
        
        # 驗證郵箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data.email):
            return False
        
        return True
    
    async def _check_existing_user(self, email: str) -> Optional[Dict[str, Any]]:
        """檢查用戶是否已存在"""
        try:
            query = text("""
                SELECT id, email, name, created_at
                FROM users 
                WHERE email = :email
                LIMIT 1
            """)
            
            result = await self.db_manager.execute_query(query, {"email": email})
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to check existing user: {str(e)}")
            return None
    
    async def _get_test_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """獲取測試結果"""
        try:
            query = text("""
                SELECT ptr.*, pt.type, pt.title, pt.display_name, pt.description,
                       pt.characteristics, pt.investment_style, pt.icon
                FROM personality_test_results ptr
                LEFT JOIN personality_types pt ON ptr.personality_type = pt.type
                WHERE ptr.id = :result_id
                LIMIT 1
            """)
            
            result = await self.db_manager.execute_query(query, {"result_id": result_id})
            if result:
                test_data = result[0]
                # 構建完整的測試結果數據
                return {
                    "id": test_data["id"],
                    "session_id": test_data["session_id"],
                    "personality_type": {
                        "type": test_data["type"],
                        "title": test_data["title"],
                        "display_name": test_data["display_name"],
                        "description": test_data["description"],
                        "characteristics": json.loads(test_data["characteristics"]) if test_data["characteristics"] else [],
                        "investment_style": test_data["investment_style"],
                        "icon": test_data["icon"]
                    },
                    "dimension_scores": json.loads(test_data["dimension_scores"]) if test_data["dimension_scores"] else {},
                    "percentile": test_data["percentile"],
                    "recommendations": json.loads(test_data["recommendations"]) if test_data["recommendations"] else [],
                    "completed_at": test_data["completed_at"]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get test result: {str(e)}")
            return None
    
    async def _create_user_account(self, registration_data: UserRegistrationData, test_result: Optional[Dict[str, Any]]) -> str:
        """創建用戶賬號"""
        try:
            user_id = self._generate_user_id()
            
            # 準備用戶數據
            user_data = {
                "id": user_id,
                "name": registration_data.name.strip(),
                "email": registration_data.email.lower().strip(),
                "phone": registration_data.phone.strip() if registration_data.phone else None,
                "source": "personality_test",
                "utm_params": json.dumps(registration_data.utm_params) if registration_data.utm_params else None,
                "referrer": registration_data.referrer,
                "ab_variant": registration_data.ab_variant,
                "created_at": datetime.now(),
                "is_active": True,
                "email_verified": False
            }
            
            # 如果有測試結果，添加人格檔案
            if test_result:
                personality_profile = {
                    "type": test_result["personality_type"]["type"],
                    "display_name": test_result["personality_type"]["display_name"],
                    "scores": test_result["dimension_scores"],
                    "percentile": test_result["percentile"],
                    "test_date": test_result["completed_at"].isoformat() if isinstance(test_result["completed_at"], datetime) else test_result["completed_at"],
                    "result_id": test_result["id"]
                }
                user_data["personality_profile"] = json.dumps(personality_profile)
            
            # 插入用戶數據
            query = text("""
                INSERT INTO users (
                    id, name, email, phone, source, utm_params, referrer, 
                    ab_variant, personality_profile, created_at, is_active, email_verified
                ) VALUES (
                    :id, :name, :email, :phone, :source, :utm_params, :referrer,
                    :ab_variant, :personality_profile, :created_at, :is_active, :email_verified
                )
            """)
            
            await self.db_manager.execute_query(query, user_data)
            
            logger.info(f"User account created: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to create user account: {str(e)}")
            raise
    
    def _generate_user_id(self) -> str:
        """生成用戶ID"""
        timestamp = str(int(datetime.now().timestamp() * 1000))
        random_part = secrets.token_hex(8)
        return f"user_{timestamp}_{random_part}"
    
    async def _send_personalized_welcome_email(self, user_id: str, registration_data: UserRegistrationData, test_result: Dict[str, Any]) -> bool:
        """發送個性化歡迎郵件"""
        try:
            # 準備個性化數據
            welcome_data = PersonalizedWelcomeData(
                personality_type=test_result["personality_type"]["type"],
                display_name=test_result["personality_type"]["display_name"],
                percentile=test_result["percentile"],
                recommendations=test_result["recommendations"],
                investment_style=test_result["personality_type"]["investment_style"],
                next_steps=self._get_onboarding_steps(test_result)
            )
            
            # 獲取郵件模板
            email_template = self._get_personality_email_template(test_result["personality_type"]["type"])
            
            # 構建郵件內容
            email_content = self._build_welcome_email_content(
                registration_data.name,
                welcome_data,
                email_template
            )
            
            # 記錄郵件發送（實際發送需要整合郵件服務）
            await self._log_email_sent(user_id, "personalized_welcome", email_content)
            
            logger.info(f"Personalized welcome email prepared for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send personalized welcome email: {str(e)}")
            return False
    
    async def _send_standard_welcome_email(self, user_id: str, registration_data: UserRegistrationData) -> bool:
        """發送標準歡迎郵件"""
        try:
            email_content = self._build_standard_welcome_email(registration_data.name)
            await self._log_email_sent(user_id, "standard_welcome", email_content)
            
            logger.info(f"Standard welcome email prepared for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send standard welcome email: {str(e)}")
            return False
    
    def _get_personality_email_template(self, personality_type: str) -> Dict[str, str]:
        """獲取人格類型郵件模板"""
        templates = {
            "conservative": {
                "subject": "歡迎穩健型投資者！您的專屬投資建議已準備就緒",
                "greeting": "親愛的穩健型投資者",
                "intro": "恭喜您完成投資人格測試！作為穩健型投資者，您重視風險控制和長期穩定收益。",
                "benefits": [
                    "專為保守型投資者設計的風險管理策略",
                    "穩健投資組合配置建議",
                    "長期財富增長計劃",
                    "專業分析師的個人化推薦"
                ]
            },
            "aggressive": {
                "subject": "歡迎積極型投資者！發掘您的高收益投資機會",
                "greeting": "親愛的積極型投資者",
                "intro": "恭喜您完成投資人格測試！作為積極型投資者，您勇於承擔風險，追求高收益機會。",
                "benefits": [
                    "高潛力投資標的發掘",
                    "即時市場警報和交易機會",
                    "深度技術分析和基本面研究",
                    "專為積極投資者設計的進階策略"
                ]
            },
            "balanced": {
                "subject": "歡迎平衡型投資者！您的多元化投資策略指南",
                "greeting": "親愛的平衡型投資者",
                "intro": "恭喜您完成投資人格測試！作為平衡型投資者，您追求風險與收益的完美平衡。",
                "benefits": [
                    "風險與收益平衡的投資組合",
                    "多元化資產配置策略",
                    "智能投資配置建議",
                    "根據市場變化的動態調整"
                ]
            }
        }
        
        return templates.get(personality_type, templates["balanced"])
    
    def _build_welcome_email_content(self, name: str, welcome_data: PersonalizedWelcomeData, template: Dict[str, str]) -> Dict[str, str]:
        """構建歡迎郵件內容"""
        return {
            "subject": template["subject"],
            "html_content": f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #667eea; text-align: center;">歡迎加入 TradingAgents！</h1>
                    
                    <p>{template['greeting']} {name}，</p>
                    
                    <p>{template['intro']}</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #667eea;">您的投資人格：{welcome_data.display_name}</h3>
                        <p><strong>您擊敗了 {welcome_data.percentile}% 的投資者！</strong></p>
                        <p><strong>投資風格：</strong>{welcome_data.investment_style}</p>
                    </div>
                    
                    <h3 style="color: #667eea;">專為您準備的投資服務：</h3>
                    <ul>
                        {''.join([f'<li>{benefit}</li>' for benefit in template['benefits']])}
                    </ul>
                    
                    <h3 style="color: #667eea;">個性化建議：</h3>
                    <ul>
                        {''.join([f'<li>{rec}</li>' for rec in welcome_data.recommendations])}
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            開始您的投資之旅
                        </a>
                    </div>
                    
                    <h3 style="color: #667eea;">下一步：</h3>
                    <ol>
                        {''.join([f'<li>{step}</li>' for step in welcome_data.next_steps])}
                    </ol>
                    
                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
                        感謝您選擇 TradingAgents！<br>
                        如有任何問題，請隨時聯繫我們的客服團隊。
                    </p>
                </div>
            </body>
            </html>
            """,
            "text_content": f"""
            歡迎加入 TradingAgents！
            
            {template['greeting']} {name}，
            
            {template['intro']}
            
            您的投資人格：{welcome_data.display_name}
            您擊敗了 {welcome_data.percentile}% 的投資者！
            投資風格：{welcome_data.investment_style}
            
            專為您準備的投資服務：
            {chr(10).join([f'• {benefit}' for benefit in template['benefits']])}
            
            個性化建議：
            {chr(10).join([f'• {rec}' for rec in welcome_data.recommendations])}
            
            下一步：
            {chr(10).join([f'{i+1}. {step}' for i, step in enumerate(welcome_data.next_steps)])}
            
            感謝您選擇 TradingAgents！
            如有任何問題，請隨時聯繫我們的客服團隊。
            """
        }
    
    def _build_standard_welcome_email(self, name: str) -> Dict[str, str]:
        """構建標準歡迎郵件"""
        return {
            "subject": "歡迎加入 TradingAgents！開始您的投資之旅",
            "html_content": f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #667eea; text-align: center;">歡迎加入 TradingAgents！</h1>
                    
                    <p>親愛的 {name}，</p>
                    
                    <p>感謝您註冊 TradingAgents！我們很高興您選擇我們作為您的投資夥伴。</p>
                    
                    <h3 style="color: #667eea;">我們為您提供：</h3>
                    <ul>
                        <li>專業的投資分析和建議</li>
                        <li>實時市場數據和警報</li>
                        <li>個性化的投資組合管理</li>
                        <li>專業分析師團隊支援</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            開始探索
                        </a>
                    </div>
                    
                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
                        感謝您選擇 TradingAgents！<br>
                        如有任何問題，請隨時聯繫我們的客服團隊。
                    </p>
                </div>
            </body>
            </html>
            """,
            "text_content": f"""
            歡迎加入 TradingAgents！
            
            親愛的 {name}，
            
            感謝您註冊 TradingAgents！我們很高興您選擇我們作為您的投資夥伴。
            
            我們為您提供：
            • 專業的投資分析和建議
            • 實時市場數據和警報
            • 個性化的投資組合管理
            • 專業分析師團隊支援
            
            感謝您選擇 TradingAgents！
            如有任何問題，請隨時聯繫我們的客服團隊。
            """
        }
    
    async def _log_email_sent(self, user_id: str, email_type: str, content: Dict[str, str]) -> None:
        """記錄郵件發送"""
        try:
            query = text("""
                INSERT INTO email_logs (
                    user_id, email_type, subject, content, created_at
                ) VALUES (
                    :user_id, :email_type, :subject, :content, :created_at
                )
            """)
            
            await self.db_manager.execute_query(
                query,
                {
                    "user_id": user_id,
                    "email_type": email_type,
                    "subject": content["subject"],
                    "content": json.dumps(content),
                    "created_at": datetime.now()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to log email: {str(e)}")
    
    def _get_onboarding_steps(self, test_result: Optional[Dict[str, Any]]) -> List[str]:
        """獲取入門步驟"""
        if test_result:
            personality_type = test_result["personality_type"]["type"]
            
            steps_by_type = {
                "conservative": [
                    "完善您的風險偏好設定",
                    "瀏覽穩健型投資組合推薦",
                    "設置投資目標和時間範圍",
                    "訂閱市場分析報告",
                    "聯繫專屬投資顧問"
                ],
                "aggressive": [
                    "設置高收益投資警報",
                    "瀏覽積極型投資機會",
                    "學習進階交易策略",
                    "加入投資者社群",
                    "開始模擬交易練習"
                ],
                "balanced": [
                    "建立多元化投資組合",
                    "設置平衡型資產配置",
                    "學習投資組合管理",
                    "設置定期投資計劃",
                    "獲得專業投資建議"
                ]
            }
            
            return steps_by_type.get(personality_type, steps_by_type["balanced"])
        else:
            return [
                "完成投資人格測試",
                "設置投資偏好",
                "瀏覽投資機會",
                "建立投資組合",
                "開始投資之旅"
            ]
    
    async def get_conversion_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取轉換分析數據"""
        try:
            # 獲取轉換漏斗數據
            funnel_query = text("""
                SELECT 
                    step,
                    COUNT(*) as count,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM conversion_tracking 
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY step
                ORDER BY 
                    CASE step
                        WHEN 'result_view' THEN 1
                        WHEN 'cta_view' THEN 2
                        WHEN 'register_click' THEN 3
                        WHEN 'register_complete' THEN 4
                        ELSE 5
                    END
            """)
            
            funnel_data = await self.db_manager.execute_query(
                funnel_query,
                {"start_date": start_date, "end_date": end_date}
            )
            
            # 獲取A/B測試數據
            ab_test_query = text("""
                SELECT 
                    JSON_EXTRACT(data, '$.ab_variant') as variant,
                    step,
                    COUNT(*) as count
                FROM conversion_tracking 
                WHERE created_at BETWEEN :start_date AND :end_date
                    AND JSON_EXTRACT(data, '$.ab_variant') IS NOT NULL
                GROUP BY JSON_EXTRACT(data, '$.ab_variant'), step
            """)
            
            ab_test_data = await self.db_manager.execute_query(
                ab_test_query,
                {"start_date": start_date, "end_date": end_date}
            )
            
            # 計算轉換率
            conversion_rates = self._calculate_conversion_rates(funnel_data)
            
            return {
                "funnel_data": funnel_data,
                "ab_test_data": ab_test_data,
                "conversion_rates": conversion_rates,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversion analytics: {str(e)}")
            return {}
    
    def _calculate_conversion_rates(self, funnel_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算轉換率"""
        rates = {}
        
        if not funnel_data:
            return rates
        
        # 建立步驟映射
        step_counts = {row["step"]: row["unique_sessions"] for row in funnel_data}
        
        # 計算各步驟轉換率
        if "result_view" in step_counts and "cta_view" in step_counts:
            rates["result_to_cta"] = (step_counts["cta_view"] / step_counts["result_view"]) * 100
        
        if "cta_view" in step_counts and "register_click" in step_counts:
            rates["cta_to_click"] = (step_counts["register_click"] / step_counts["cta_view"]) * 100
        
        if "register_click" in step_counts and "register_complete" in step_counts:
            rates["click_to_complete"] = (step_counts["register_complete"] / step_counts["register_click"]) * 100
        
        if "result_view" in step_counts and "register_complete" in step_counts:
            rates["overall_conversion"] = (step_counts["register_complete"] / step_counts["result_view"]) * 100
        
        return rates
    
    # ==================== 按次付費整合方法 ====================
    
    async def track_alpha_insight_interest(self, user_id: int, stock_id: str, insight_type: str, 
                                         session_id: Optional[str] = None) -> bool:
        """追蹤用戶對阿爾法洞察的興趣"""
        try:
            step_data = ConversionStepData(
                session_id=session_id or f"user_{user_id}_{datetime.now().timestamp()}",
                step="alpha_insight_interest",
                action="view_alpha_preview",
                data={
                    "user_id": user_id,
                    "stock_id": stock_id,
                    "insight_type": insight_type,
                    "source": "personality_test_result"
                }
            )
            
            return await self.track_conversion_step(step_data)
            
        except Exception as e:
            logger.error(f"Failed to track alpha insight interest: {str(e)}")
            return False
    
    async def handle_alpha_insight_purchase(self, purchase_data: AlphaInsightPurchaseData) -> Dict[str, Any]:
        """處理阿爾法洞察購買（整合轉換追蹤）"""
        try:
            # 1. 追蹤購買意圖
            await self.track_conversion_step(ConversionStepData(
                session_id=purchase_data.session_id or f"user_{purchase_data.user_id}_{datetime.now().timestamp()}",
                step="alpha_purchase_intent",
                action="initiate_purchase",
                data={
                    "user_id": purchase_data.user_id,
                    "stock_id": purchase_data.stock_id,
                    "insight_type": purchase_data.insight_type,
                    "amount": purchase_data.amount,
                    "source": purchase_data.source
                }
            ))
            
            # 2. 執行購買
            purchase_result = await self.pay_per_use_service.purchase_alpha_insight(
                user_id=purchase_data.user_id,
                stock_id=purchase_data.stock_id,
                insight_type=purchase_data.insight_type
            )
            
            # 3. 追蹤購買結果
            if purchase_result.get("success"):
                await self.track_conversion_step(ConversionStepData(
                    session_id=purchase_data.session_id,
                    step="alpha_purchase_complete",
                    action="purchase_success",
                    data={
                        "user_id": purchase_data.user_id,
                        "transaction_id": purchase_result.get("transaction_id"),
                        "amount": purchase_result.get("amount"),
                        "already_purchased": purchase_result.get("already_purchased", False)
                    }
                ))
                
                # 4. 檢查升級推薦觸發
                await self._check_and_track_upgrade_opportunity(purchase_data.user_id, purchase_data.session_id)
                
            else:
                await self.track_conversion_step(ConversionStepData(
                    session_id=purchase_data.session_id,
                    step="alpha_purchase_failed",
                    action="purchase_error",
                    data={
                        "user_id": purchase_data.user_id,
                        "error": purchase_result.get("error"),
                        "code": purchase_result.get("code")
                    }
                ))
            
            return purchase_result
            
        except Exception as e:
            logger.error(f"Failed to handle alpha insight purchase: {str(e)}")
            return {
                "success": False,
                "error": "購買處理失敗",
                "code": "CONVERSION_ERROR"
            }
    
    async def get_personalized_alpha_recommendations(self, user_id: int, personality_type: str) -> List[Dict[str, Any]]:
        """基於投資人格獲取個性化阿爾法洞察推薦"""
        try:
            # 根據投資人格類型推薦相關股票和洞察類型
            personality_stock_mapping = {
                "conservative": ["2330", "2317", "2454"],  # 保守型：大型穩定股
                "aggressive": ["2603", "3008", "2382"],    # 積極型：成長股
                "balanced": ["2330", "2317", "2603"],      # 平衡型：混合
                "growth": ["3008", "2382", "6505"],        # 成長型：科技股
                "value": ["2317", "2454", "1301"]          # 價值型：傳統產業
            }
            
            personality_insight_mapping = {
                "conservative": ["fundamental_alpha", "risk_analysis"],
                "aggressive": ["technical_alpha", "momentum_analysis"],
                "balanced": ["fundamental_alpha", "technical_alpha"],
                "growth": ["technical_alpha", "sentiment_alpha"],
                "value": ["fundamental_alpha", "dcf_analysis"]
            }
            
            recommended_stocks = personality_stock_mapping.get(personality_type, ["2330", "2317"])
            recommended_insights = personality_insight_mapping.get(personality_type, ["technical_alpha"])
            
            recommendations = []
            
            for stock_id in recommended_stocks[:2]:  # 限制推薦數量
                for insight_type in recommended_insights[:1]:  # 每股票推薦一種洞察
                    # 獲取洞察預覽
                    insight = await self.pay_per_use_service.get_alpha_insight(stock_id, insight_type)
                    if insight:
                        recommendations.append({
                            "stock_id": stock_id,
                            "insight_type": insight_type,
                            "title": f"{stock_id} {insight_type.replace('_', ' ').title()}",
                            "confidence_score": insight.confidence_score,
                            "target_price": insight.target_price,
                            "price": 5.00,
                            "preview": self.pay_per_use_service.mask_content_for_free_user(insight.standard_content),
                            "purchase_cta": f"解鎖 {stock_id} 深度分析",
                            "personality_match": f"適合{personality_type}型投資者"
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get personalized alpha recommendations: {str(e)}")
            return []
    
    async def _check_and_track_upgrade_opportunity(self, user_id: int, session_id: Optional[str] = None):
        """檢查並追蹤升級機會"""
        try:
            # 獲取用戶消費摘要
            spending_summary = await self.pay_per_use_service.get_user_spending_summary(user_id)
            
            # 如果接近升級門檻，追蹤升級機會
            if spending_summary.get("monthly_spending", 0) >= 25.0:  # 達到一半門檻
                await self.track_conversion_step(ConversionStepData(
                    session_id=session_id,
                    step="upgrade_opportunity",
                    action="threshold_approaching",
                    data={
                        "user_id": user_id,
                        "monthly_spending": spending_summary.get("monthly_spending"),
                        "remaining_to_threshold": spending_summary.get("remaining_to_threshold"),
                        "upgrade_threshold_reached": spending_summary.get("upgrade_threshold_reached")
                    }
                ))
            
            # 如果達到升級門檻，追蹤升級推薦
            if spending_summary.get("upgrade_threshold_reached"):
                await self.track_conversion_step(ConversionStepData(
                    session_id=session_id,
                    step="upgrade_recommendation",
                    action="threshold_reached",
                    data={
                        "user_id": user_id,
                        "monthly_spending": spending_summary.get("monthly_spending"),
                        "recommended_tier": "DIAMOND"
                    }
                ))
                
        except Exception as e:
            logger.error(f"Failed to check upgrade opportunity: {str(e)}")
    
    async def get_alpha_purchase_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取阿爾法洞察購買分析"""
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_purchases,
                    COUNT(DISTINCT user_id) as unique_buyers,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_purchase_amount,
                    stock_id,
                    insight_type
                FROM pay_per_use_transactions 
                WHERE payment_status = 'completed'
                AND created_at BETWEEN :start_date AND :end_date
                GROUP BY stock_id, insight_type
                ORDER BY total_revenue DESC
            """)
            
            purchase_data = await self.db_manager.execute_query(
                query,
                {
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            # 獲取轉換漏斗數據
            conversion_query = text("""
                SELECT 
                    step,
                    COUNT(*) as step_count,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM conversion_tracking 
                WHERE step IN ('alpha_insight_interest', 'alpha_purchase_intent', 'alpha_purchase_complete')
                AND created_at BETWEEN :start_date AND :end_date
                GROUP BY step
                ORDER BY step
            """)
            
            conversion_data = await self.db_manager.execute_query(
                conversion_query,
                {
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            # 計算轉換率
            conversion_rates = {}
            if conversion_data:
                step_counts = {row["step"]: row["unique_sessions"] for row in conversion_data}
                
                if "alpha_insight_interest" in step_counts and "alpha_purchase_intent" in step_counts:
                    conversion_rates["interest_to_intent"] = (
                        step_counts["alpha_purchase_intent"] / step_counts["alpha_insight_interest"] * 100
                    )
                
                if "alpha_purchase_intent" in step_counts and "alpha_purchase_complete" in step_counts:
                    conversion_rates["intent_to_purchase"] = (
                        step_counts["alpha_purchase_complete"] / step_counts["alpha_purchase_intent"] * 100
                    )
                
                if "alpha_insight_interest" in step_counts and "alpha_purchase_complete" in step_counts:
                    conversion_rates["overall_alpha_conversion"] = (
                        step_counts["alpha_purchase_complete"] / step_counts["alpha_insight_interest"] * 100
                    )
            
            return {
                "purchase_summary": {
                    "total_purchases": sum(row["total_purchases"] for row in purchase_data) if purchase_data else 0,
                    "unique_buyers": len(set(row["stock_id"] for row in purchase_data)) if purchase_data else 0,
                    "total_revenue": sum(row["total_revenue"] for row in purchase_data) if purchase_data else 0.0,
                    "avg_purchase_amount": 5.00  # 固定價格
                },
                "popular_insights": purchase_data[:5] if purchase_data else [],
                "conversion_rates": conversion_rates,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get alpha purchase analytics: {str(e)}")
            return {}