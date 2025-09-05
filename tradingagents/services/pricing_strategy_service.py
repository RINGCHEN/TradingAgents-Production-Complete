"""
多層次定價策略服務
Task 5.3 - 多層次定價策略的核心業務邏輯
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import random
import uuid
import json
from decimal import Decimal

from ..models.pricing_strategy import (
    PricingPlan, DynamicPricingRule, CouponCode, CouponUsage, 
    PriceComparison, UserPricingHistory, PricingConfig,
    PricingTier, DiscountType, CouponStatus
)

# 模擬導入，如果模塊不存在
try:
    from ..utils.logging_config import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

try:
    from ..utils.monitoring import monitor_conversion_event
except ImportError:
    def monitor_conversion_event(event_name, data):
        pass

logger = get_logger(__name__)

class PricingStrategyService:
    """定價策略服務類"""
    
    def __init__(self, db=None):
        """初始化服務"""
        self.db = db
        self.config = PricingConfig()
        
        # 內存存儲（生產環境應使用數據庫）
        self.plans = {}
        self.dynamic_rules = {}
        self.coupons = {}
        self.usage_records = {}
        self.pricing_history = {}
        
        # 初始化默認數據
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """初始化默認數據"""
        # 創建默認定價方案
        for plan_data in self.config.get_default_plans():
            plan_id = str(uuid.uuid4())
            plan_data['id'] = plan_id
            plan_data['created_at'] = datetime.utcnow()
            plan_data['updated_at'] = datetime.utcnow()
            self.plans[plan_id] = plan_data
        
        # 創建默認優惠券
        for coupon_data in self.config.get_default_coupons():
            coupon_id = str(uuid.uuid4())
            coupon_data['id'] = coupon_id
            coupon_data['created_at'] = datetime.utcnow()
            self.coupons[coupon_data['code']] = coupon_data
    
    def get_pricing_plans(
        self, 
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        獲取定價方案
        設計價格錨定：展示高價選項突出標準方案價值
        實現動態定價：根據用戶行為調整價格展示
        """
        try:
            # 獲取基礎方案
            base_plans = list(self.plans.values())
            
            # 應用動態定價
            adjusted_plans = []
            for plan in base_plans:
                adjusted_plan = self._apply_dynamic_pricing(
                    plan, user_id, session_id, user_attributes
                )
                adjusted_plans.append(adjusted_plan)
            
            # 應用價格錨定策略
            anchored_plans = self._apply_price_anchoring(adjusted_plans)
            
            # 記錄用戶查看歷史
            self._record_pricing_view(
                adjusted_plans, user_id, session_id, user_attributes
            )
            
            # 生成方案對比數據
            comparison_data = self._generate_plan_comparison(anchored_plans)
            
            # 記錄監控事件
            monitor_conversion_event('pricing_plans_viewed', {
                'user_id': user_id,
                'session_id': session_id,
                'plans_count': len(anchored_plans),
                'has_dynamic_pricing': any(p.get('is_discounted', False) for p in anchored_plans)
            })
            
            return {
                'success': True,
                'plans': anchored_plans,
                'comparison': comparison_data,
                'recommendations': self._generate_plan_recommendations(anchored_plans, user_attributes),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f'獲取定價方案失敗: {str(e)}')
            return {'success': False, 'error': str(e)}
    
    def _apply_dynamic_pricing(
        self, 
        plan: Dict[str, Any], 
        user_id: Optional[int],
        session_id: Optional[str],
        user_attributes: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """應用動態定價規則"""
        adjusted_plan = plan.copy()
        original_price = plan['monthly_price']
        
        # 檢查動態定價觸發條件
        applicable_discounts = []
        
        if user_attributes:
            for trigger_name, trigger_config in self.config.DYNAMIC_PRICING_TRIGGERS.items():
                if self._check_trigger_conditions(trigger_config['conditions'], user_attributes):
                    applicable_discounts.append({
                        'name': trigger_name,
                        'discount': trigger_config['discount'],
                        'description': trigger_config['description']
                    })
        
        # 應用最大折扣
        if applicable_discounts:
            best_discount = max(applicable_discounts, key=lambda x: x['discount'])
            discount_percentage = best_discount['discount']
            
            discounted_price = original_price * (1 - discount_percentage / 100)
            
            adjusted_plan.update({
                'discounted_price': round(discounted_price, 2),
                'discount_percentage': discount_percentage,
                'discount_amount': round(original_price - discounted_price, 2),
                'discount_reason': best_discount['description'],
                'is_discounted': True,
                'applicable_discounts': applicable_discounts
            })
        
        return adjusted_plan
    
    def _check_trigger_conditions(
        self, 
        conditions: Dict[str, Any], 
        user_attributes: Dict[str, Any]
    ) -> bool:
        """檢查觸發條件是否滿足"""
        for key, condition in conditions.items():
            if key not in user_attributes:
                return False
            
            user_value = user_attributes[key]
            
            if isinstance(condition, dict):
                for operator, expected_value in condition.items():
                    if operator == '$lt' and user_value >= expected_value:
                        return False
                    elif operator == '$gt' and user_value <= expected_value:
                        return False
                    elif operator == '$eq' and user_value != expected_value:
                        return False
            else:
                if user_value != condition:
                    return False
        
        return True
    
    def _apply_price_anchoring(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """應用價格錨定策略"""
        anchored_plans = []
        
        for plan in plans:
            anchored_plan = plan.copy()
            
            # 添加錨定價格信息
            if 'anchor_price' in plan and plan['anchor_price']:
                current_price = plan.get('discounted_price', plan['monthly_price'])
                anchor_price = plan['anchor_price']
                
                savings = anchor_price - current_price
                savings_percentage = (savings / anchor_price) * 100
                
                anchored_plan.update({
                    'anchor_price': anchor_price,
                    'savings_amount': round(savings, 2),
                    'savings_percentage': round(savings_percentage, 1),
                    'value_proposition': f'比原價節省 ${savings:.0f} ({savings_percentage:.0f}%)'
                })
            
            # 添加競爭對手對比
            if plan['tier'] == PricingTier.STANDARD.value:
                anchored_plan['competitor_comparison'] = {
                    'traditional_advisor_cost': 3000,
                    'our_cost': plan.get('discounted_price', plan['monthly_price']),
                    'savings_vs_traditional': 3000 - plan.get('discounted_price', plan['monthly_price']),
                    'value_multiplier': '10倍專業覆蓋，1/10價格'
                }
            
            anchored_plans.append(anchored_plan)
        
        return anchored_plans
    
    def _generate_plan_comparison(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成方案對比數據
        創建付費方案對比：突出推薦方案的優勢
        """
        comparison_features = [
            {'name': 'AI分析師數量', 'key': 'analysts_count'},
            {'name': '每日分析次數', 'key': 'analysis_per_day'},
            {'name': '技術指標', 'key': 'technical_indicators'},
            {'name': '客服支援', 'key': 'support_level'},
            {'name': '投資組合功能', 'key': 'portfolio_features'},
            {'name': '風險管理', 'key': 'risk_management'},
            {'name': '市場預警', 'key': 'market_alerts'}
        ]
        
        comparison_matrix = []
        
        for feature in comparison_features:
            feature_row = {
                'feature_name': feature['name'],
                'plans': {}
            }
            
            for plan in plans:
                plan_id = plan['id']
                feature_value = self._get_feature_value(plan, feature['key'])
                feature_row['plans'][plan_id] = feature_value
            
            comparison_matrix.append(feature_row)
        
        # 找出推薦方案
        recommended_plan = next((p for p in plans if p.get('is_recommended', False)), None)
        
        return {
            'comparison_matrix': comparison_matrix,
            'recommended_plan_id': recommended_plan['id'] if recommended_plan else None,
            'highlight_differences': self._highlight_plan_differences(plans),
            'value_propositions': self._generate_value_propositions(plans)
        }
    
    def _get_feature_value(self, plan: Dict[str, Any], feature_key: str) -> str:
        """獲取功能特性值"""
        limitations = plan.get('limitations', {})
        
        feature_mapping = {
            'analysts_count': lambda: f"{limitations.get('analysts_count', 0)}位",
            'analysis_per_day': lambda: "無限制" if limitations.get('analysis_per_day', 0) == -1 else f"{limitations.get('analysis_per_day', 0)}次/日",
            'technical_indicators': lambda: self._get_indicator_level(plan['tier']),
            'support_level': lambda: self._get_support_description(limitations.get('support_level', 'none')),
            'portfolio_features': lambda: "✓" if plan['tier'] in ['standard', 'premium'] else "✗",
            'risk_management': lambda: "✓" if plan['tier'] == 'premium' else "✗",
            'market_alerts': lambda: "✓" if plan['tier'] == 'premium' else "✗"
        }
        
        return feature_mapping.get(feature_key, lambda: "N/A")()
    
    def _get_indicator_level(self, tier: str) -> str:
        """獲取技術指標級別"""
        mapping = {
            'basic': '基礎指標',
            'standard': '進階指標',
            'premium': '全套指標'
        }
        return mapping.get(tier, '基礎指標')
    
    def _get_support_description(self, support_level: str) -> str:
        """獲取支援描述"""
        mapping = {
            'email': '郵件支援',
            'chat': '即時通訊',
            'dedicated': '專屬客服',
            'none': '無支援'
        }
        return mapping.get(support_level, '無支援')
    
    def _highlight_plan_differences(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """突出方案差異"""
        differences = {}
        
        # 找出推薦方案
        recommended_plan = next((p for p in plans if p.get('is_recommended', False)), None)
        
        if recommended_plan:
            differences['recommended_advantages'] = [
                '最受歡迎的選擇',
                '最佳性價比',
                '功能與價格完美平衡',
                '適合大多數投資者'
            ]
        
        # 找出高級方案的優勢
        premium_plan = next((p for p in plans if p['tier'] == 'premium'), None)
        if premium_plan:
            differences['premium_advantages'] = [
                '最全面的功能',
                '專業級投資工具',
                '適合高級投資者',
                '完整風險管理'
            ]
        
        return differences
    
    def _generate_value_propositions(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成價值主張"""
        propositions = {}
        
        for plan in plans:
            plan_id = plan['id']
            tier = plan['tier']
            
            if tier == 'basic':
                propositions[plan_id] = {
                    'headline': '入門首選',
                    'description': '適合投資新手，提供基礎但專業的AI分析',
                    'target_audience': '投資新手、小額投資者'
                }
            elif tier == 'standard':
                propositions[plan_id] = {
                    'headline': '最佳選擇',
                    'description': '功能全面，性價比最高，適合大多數投資者',
                    'target_audience': '一般投資者、理財規劃者'
                }
            elif tier == 'premium':
                propositions[plan_id] = {
                    'headline': '專業級工具',
                    'description': '最完整的投資分析工具，適合專業投資者',
                    'target_audience': '專業投資者、資產管理者'
                }
            
            # 添加節省計算
            if plan.get('is_discounted', False):
                propositions[plan_id]['special_offer'] = f"限時優惠：立省 ${plan['discount_amount']}"
        
        return propositions
    
    def apply_coupon(
        self, 
        coupon_code: str, 
        plan_id: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        應用優惠券
        開發優惠券系統：新用戶專屬折扣碼
        """
        try:
            # 獲取優惠券
            coupon = self.coupons.get(coupon_code)
            if not coupon:
                return {'success': False, 'error': '優惠券不存在'}
            
            # 檢查優惠券狀態
            if coupon['status'] != CouponStatus.ACTIVE.value:
                return {'success': False, 'error': '優惠券已失效'}
            
            # 檢查時間有效性
            now = datetime.utcnow()
            if now < coupon['start_date'] or now > coupon['end_date']:
                return {'success': False, 'error': '優惠券已過期'}
            
            # 檢查使用次數限制
            if coupon.get('max_uses') and coupon['current_uses'] >= coupon['max_uses']:
                return {'success': False, 'error': '優惠券使用次數已達上限'}
            
            # 檢查用戶使用限制
            if user_id and coupon.get('max_uses_per_user'):
                user_usage_count = len([
                    r for r in self.usage_records.values() 
                    if r['coupon_id'] == coupon['id'] and r['user_id'] == user_id
                ])
                if user_usage_count >= coupon['max_uses_per_user']:
                    return {'success': False, 'error': '您已達到此優惠券的使用上限'}
            
            # 獲取方案信息
            plan = self.plans.get(plan_id)
            if not plan:
                return {'success': False, 'error': '方案不存在'}
            
            # 檢查最小購買金額
            original_price = plan['monthly_price']
            if coupon.get('min_purchase_amount') and original_price < coupon['min_purchase_amount']:
                return {'success': False, 'error': f'最小購買金額為 ${coupon["min_purchase_amount"]}'}
            
            # 計算折扣
            discount_result = self._calculate_coupon_discount(coupon, original_price)
            
            # 記錄使用
            usage_id = str(uuid.uuid4())
            usage_record = {
                'id': usage_id,
                'coupon_id': coupon['id'],
                'user_id': user_id,
                'session_id': session_id,
                'plan_id': plan_id,
                'original_price': original_price,
                'discount_amount': discount_result['discount_amount'],
                'final_price': discount_result['final_price'],
                'used_at': datetime.utcnow()
            }
            
            self.usage_records[usage_id] = usage_record
            
            # 更新優惠券使用次數
            coupon['current_uses'] = coupon.get('current_uses', 0) + 1
            
            # 記錄監控事件
            monitor_conversion_event('coupon_applied', {
                'coupon_code': coupon_code,
                'user_id': user_id,
                'session_id': session_id,
                'plan_id': plan_id,
                'discount_amount': discount_result['discount_amount'],
                'discount_percentage': discount_result.get('discount_percentage', 0)
            })
            
            logger.info(f'優惠券應用成功: {coupon_code} - 用戶{user_id or session_id}')
            
            return {
                'success': True,
                'usage_id': usage_id,
                'discount_details': discount_result,
                'coupon_info': {
                    'code': coupon_code,
                    'name': coupon['name'],
                    'description': coupon['description']
                }
            }
            
        except Exception as e:
            logger.error(f'應用優惠券失敗: {str(e)}')
            return {'success': False, 'error': str(e)}
    
    def _calculate_coupon_discount(self, coupon: Dict[str, Any], original_price: float) -> Dict[str, Any]:
        """計算優惠券折扣"""
        discount_type = coupon['discount_type']
        discount_value = coupon['discount_value']
        
        if discount_type == DiscountType.PERCENTAGE.value:
            discount_amount = original_price * (discount_value / 100)
            
            # 檢查最大折扣金額限制
            if coupon.get('max_discount_amount'):
                discount_amount = min(discount_amount, coupon['max_discount_amount'])
            
            final_price = original_price - discount_amount
            
            return {
                'discount_type': 'percentage',
                'discount_percentage': discount_value,
                'discount_amount': round(discount_amount, 2),
                'final_price': round(final_price, 2),
                'savings': round(discount_amount, 2)
            }
            
        elif discount_type == DiscountType.FIXED_AMOUNT.value:
            discount_amount = min(discount_value, original_price)  # 不能超過原價
            final_price = original_price - discount_amount
            discount_percentage = (discount_amount / original_price) * 100
            
            return {
                'discount_type': 'fixed_amount',
                'discount_amount': round(discount_amount, 2),
                'discount_percentage': round(discount_percentage, 1),
                'final_price': round(final_price, 2),
                'savings': round(discount_amount, 2)
            }
        
        else:
            return {
                'discount_type': 'unknown',
                'discount_amount': 0,
                'final_price': original_price,
                'savings': 0
            }
    
    def get_available_coupons(
        self, 
        user_id: Optional[int] = None,
        user_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """獲取可用優惠券"""
        try:
            available_coupons = []
            
            for coupon in self.coupons.values():
                # 檢查基本條件
                if coupon['status'] != CouponStatus.ACTIVE.value:
                    continue
                
                now = datetime.utcnow()
                if now < coupon['start_date'] or now > coupon['end_date']:
                    continue
                
                # 檢查使用次數
                if coupon.get('max_uses') and coupon['current_uses'] >= coupon['max_uses']:
                    continue
                
                # 檢查用戶細分
                if coupon.get('user_segments') and user_attributes:
                    if not self._check_user_segment_match(coupon['user_segments'], user_attributes):
                        continue
                
                # 檢查是否公開
                if not coupon.get('is_public', False) and not user_id:
                    continue
                
                available_coupons.append({
                    'code': coupon['code'],
                    'name': coupon['name'],
                    'description': coupon['description'],
                    'discount_type': coupon['discount_type'],
                    'discount_value': coupon['discount_value'],
                    'end_date': coupon['end_date'].isoformat(),
                    'min_purchase_amount': coupon.get('min_purchase_amount'),
                    'max_discount_amount': coupon.get('max_discount_amount')
                })
            
            return {
                'success': True,
                'coupons': available_coupons,
                'count': len(available_coupons)
            }
            
        except Exception as e:
            logger.error(f'獲取可用優惠券失敗: {str(e)}')
            return {'success': False, 'error': str(e)}
    
    def _check_user_segment_match(
        self, 
        required_segments: List[str], 
        user_attributes: Dict[str, Any]
    ) -> bool:
        """檢查用戶是否符合細分條件"""
        for segment_name in required_segments:
            segment_config = self.config.USER_SEGMENTS.get(segment_name)
            if not segment_config:
                continue
            
            if self._check_trigger_conditions(segment_config['conditions'], user_attributes):
                return True
        
        return False
    
    def _record_pricing_view(
        self,
        plans: List[Dict[str, Any]],
        user_id: Optional[int],
        session_id: Optional[str],
        user_attributes: Optional[Dict[str, Any]]
    ):
        """記錄用戶查看定價歷史"""
        for plan in plans:
            history_id = str(uuid.uuid4())
            history_record = {
                'id': history_id,
                'user_id': user_id,
                'session_id': session_id,
                'plan_id': plan['id'],
                'shown_price': plan.get('discounted_price', plan['monthly_price']),
                'original_price': plan['monthly_price'],
                'applied_rules': plan.get('applicable_discounts', []),
                'viewed_at': datetime.utcnow(),
                'page_url': user_attributes.get('page_url', '') if user_attributes else '',
                'referrer': user_attributes.get('referrer', '') if user_attributes else '',
                'user_agent': user_attributes.get('user_agent', '') if user_attributes else ''
            }
            
            self.pricing_history[history_id] = history_record
    
    def _generate_plan_recommendations(
        self, 
        plans: List[Dict[str, Any]], 
        user_attributes: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成方案推薦"""
        recommendations = {
            'primary_recommendation': None,
            'alternative_recommendations': [],
            'reasoning': []
        }
        
        # 基於用戶屬性推薦
        if user_attributes:
            if user_attributes.get('investment_experience', 'beginner') == 'beginner':
                basic_plan = next((p for p in plans if p['tier'] == 'basic'), None)
                if basic_plan:
                    recommendations['primary_recommendation'] = basic_plan['id']
                    recommendations['reasoning'].append('基於您的投資經驗，推薦從基礎版開始')
            
            elif user_attributes.get('portfolio_size', 0) > 100000:
                premium_plan = next((p for p in plans if p['tier'] == 'premium'), None)
                if premium_plan:
                    recommendations['primary_recommendation'] = premium_plan['id']
                    recommendations['reasoning'].append('基於您的投資組合規模，推薦使用高級版')
        
        # 默認推薦標準版
        if not recommendations['primary_recommendation']:
            standard_plan = next((p for p in plans if p.get('is_recommended', False)), None)
            if standard_plan:
                recommendations['primary_recommendation'] = standard_plan['id']
                recommendations['reasoning'].append('最受歡迎的選擇，功能全面且性價比高')
        
        return recommendations
    
    def get_pricing_analytics(self) -> Dict[str, Any]:
        """獲取定價分析數據"""
        try:
            # 統計查看數據
            total_views = len(self.pricing_history)
            
            # 統計優惠券使用
            total_coupon_usage = len(self.usage_records)
            total_discount_amount = sum(r['discount_amount'] for r in self.usage_records.values())
            
            # 統計方案受歡迎程度
            plan_views = {}
            for history in self.pricing_history.values():
                plan_id = history['plan_id']
                plan_views[plan_id] = plan_views.get(plan_id, 0) + 1
            
            # 統計動態定價效果
            dynamic_pricing_views = len([
                h for h in self.pricing_history.values() 
                if h['shown_price'] != h['original_price']
            ])
            
            return {
                'success': True,
                'analytics': {
                    'total_views': total_views,
                    'total_coupon_usage': total_coupon_usage,
                    'total_discount_amount': round(total_discount_amount, 2),
                    'dynamic_pricing_rate': round(dynamic_pricing_views / total_views * 100, 1) if total_views > 0 else 0,
                    'plan_popularity': plan_views,
                    'average_discount_per_usage': round(total_discount_amount / total_coupon_usage, 2) if total_coupon_usage > 0 else 0
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f'獲取定價分析失敗: {str(e)}')
            return {'success': False, 'error': str(e)}