#!/usr/bin/env python3
"""
AI功能展示整合器 - 會員系統與AI分析師功能的混合架構橋接
天工 (TianGong) - 實現方案A混合架構，將本地AI功能與雲端會員系統結合

此模組負責：
1. 創建AI功能展示層，整合本地AI分析師能力
2. 將AI演示功能與會員權益系統結合
3. 提供會員專屬的AI分析體驗
4. 管理AI功能的權限控制和使用量追蹤
5. 實現從展示版本到完整雲端部署的平滑升級路徑
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import time

# 導入現有會員系統
from .member_permission_bridge import (
    MemberPermissionBridge, UserContext, AnalysisType, 
    PermissionLevel, check_user_can_analyze
)
from .user_context import create_user_context, UserContextManager
from ..models.membership import TierType

class AIAnalystType(Enum):
    """AI分析師類型 (對應本地訓練系統)"""
    TECHNICAL_ANALYST = "technical_analyst"
    FUNDAMENTALS_ANALYST = "fundamentals_analyst" 
    NEWS_ANALYST = "news_analyst"
    RISK_ANALYST = "risk_analyst"
    SOCIAL_MEDIA_ANALYST = "social_media_analyst"
    INVESTMENT_PLANNER = "investment_planner"

class DemoStatus(Enum):
    """演示狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AIAnalysisRequest:
    """AI分析請求"""
    user_id: str
    stock_symbol: str
    analyst_types: List[AIAnalystType]
    membership_tier: str
    demo_mode: bool = True
    use_real_data: bool = True
    max_analysts: int = 3
    timeout_minutes: int = 5

@dataclass
class AIAnalysisResult:
    """AI分析結果"""
    request_id: str
    user_id: str
    stock_symbol: str
    status: DemoStatus
    analysts_used: List[str]
    analysis_data: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    demo_limitations: List[str] = None
    
    def __post_init__(self):
        if self.demo_limitations is None:
            self.demo_limitations = []

class AIDemoIntegrator:
    """AI功能展示整合器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.permission_bridge = MemberPermissionBridge()
        self.context_manager = UserContextManager()
        
        # 演示會話管理
        self.active_demos: Dict[str, AIAnalysisResult] = {}
        self.demo_queue = queue.Queue()
        self.processing_lock = threading.Lock()
        
        # 配置
        self.project_root = self._get_project_root()
        self.demo_config = self._load_demo_config()
        
        # 會員等級與AI功能映射
        self.tier_analyst_mapping = {
            'FREE': [AIAnalystType.TECHNICAL_ANALYST],
            'GOLD': [
                AIAnalystType.TECHNICAL_ANALYST,
                AIAnalystType.FUNDAMENTALS_ANALYST,
                AIAnalystType.NEWS_ANALYST,
                AIAnalystType.SOCIAL_MEDIA_ANALYST
            ],
            'DIAMOND': [
                AIAnalystType.TECHNICAL_ANALYST,
                AIAnalystType.FUNDAMENTALS_ANALYST,
                AIAnalystType.NEWS_ANALYST,
                AIAnalystType.SOCIAL_MEDIA_ANALYST,
                AIAnalystType.RISK_ANALYST,
                AIAnalystType.INVESTMENT_PLANNER
            ]
        }
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_project_root(self) -> str:
        """獲取項目根目錄"""
        current_file = os.path.abspath(__file__)
        # 從 TradingAgents/tradingagents/utils/ai_demo_integrator.py 回到項目根目錄
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
    
    def _load_demo_config(self) -> Dict[str, Any]:
        """載入演示配置"""
        try:
            config_path = os.path.join(self.project_root, 'configs', 'ai_demo_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"載入演示配置失敗，使用預設配置: {e}")
        
        # 預設配置
        return {
            'max_concurrent_demos': 3,
            'default_timeout_minutes': 5,
            'demo_stock_symbols': ['2330.TW', '2317.TW', '2454.TW'],
            'use_simplified_analysis': True,
            'enable_real_time_data': True,
            'demo_limitations': [
                '演示版本，分析深度有限',
                '每日使用次數有限制',
                '完整功能請升級會員'
            ]
        }
    
    async def create_ai_demo_session(
        self, 
        user_id: str, 
        stock_symbol: str,
        analyst_preferences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """創建AI演示會話"""
        
        try:
            # 獲取用戶上下文
            user_context = await self.permission_bridge.get_user_context(user_id)
            
            if not user_context:
                return {
                    'success': False,
                    'error': 'user_not_found',
                    'message': '用戶不存在或未登入'
                }
            
            # 檢查會員權限
            membership_tier = user_context.membership_tier
            available_analysts = self.tier_analyst_mapping.get(membership_tier, [])
            
            # 根據會員等級選擇分析師
            selected_analysts = self._select_analysts_for_tier(
                membership_tier, analyst_preferences, available_analysts
            )
            
            if not selected_analysts:
                return {
                    'success': False,
                    'error': 'no_analysts_available',
                    'message': f'您的 {membership_tier} 會員等級暫無可用的AI分析師'
                }
            
            # 檢查使用配額
            quota_check = await self._check_demo_quota(user_context)
            if not quota_check['allowed']:
                return {
                    'success': False,
                    'error': 'quota_exceeded',
                    'message': quota_check['message']
                }
            
            # 創建演示請求
            request_id = f"demo_{user_id}_{stock_symbol}_{int(datetime.now().timestamp())}"
            
            demo_request = AIAnalysisRequest(
                user_id=user_id,
                stock_symbol=stock_symbol,
                analyst_types=selected_analysts,
                membership_tier=membership_tier,
                demo_mode=True,
                use_real_data=self.demo_config.get('enable_real_time_data', True),
                max_analysts=len(selected_analysts),
                timeout_minutes=self.demo_config.get('default_timeout_minutes', 5)
            )
            
            # 開始演示處理
            demo_result = await self._start_ai_demo_processing(request_id, demo_request)
            
            return {
                'success': True,
                'request_id': request_id,
                'selected_analysts': [a.value for a in selected_analysts],
                'estimated_completion_time': datetime.now() + timedelta(
                    minutes=demo_request.timeout_minutes
                ),
                'demo_limitations': self._get_tier_limitations(membership_tier),
                'status': demo_result.status.value
            }
            
        except Exception as e:
            self.logger.error(f"創建AI演示會話失敗: {str(e)}")
            return {
                'success': False,
                'error': 'internal_error',
                'message': '創建演示會話時發生錯誤'
            }
    
    def _select_analysts_for_tier(
        self, 
        tier: str, 
        preferences: Optional[List[str]], 
        available: List[AIAnalystType]
    ) -> List[AIAnalystType]:
        """根據會員等級選擇分析師"""
        
        if not available:
            return []
        
        # 如果有偏好設置，優先選擇偏好的分析師
        if preferences:
            selected = []
            for pref in preferences:
                try:
                    analyst_type = AIAnalystType(pref)
                    if analyst_type in available:
                        selected.append(analyst_type)
                except ValueError:
                    continue
            if selected:
                return selected[:3]  # 最多3個
        
        # 根據會員等級的預設選擇
        tier_defaults = {
            'FREE': [AIAnalystType.TECHNICAL_ANALYST],
            'GOLD': [
                AIAnalystType.TECHNICAL_ANALYST, 
                AIAnalystType.FUNDAMENTALS_ANALYST,
                AIAnalystType.NEWS_ANALYST
            ],
            'DIAMOND': available[:4] if len(available) >= 4 else available
        }
        
        return tier_defaults.get(tier, available[:1])
    
    async def _check_demo_quota(self, user_context: UserContext) -> Dict[str, Any]:
        """檢查演示配額"""
        
        # 基本配額檢查 (使用現有的權限系統)
        quota_check = await self.permission_bridge._check_quota(user_context)
        
        if not quota_check['available']:
            return quota_check
        
        # 檢查並發演示限制
        user_active_demos = [
            demo for demo in self.active_demos.values() 
            if demo.user_id == user_context.user_id and demo.status == DemoStatus.RUNNING
        ]
        
        max_concurrent = self.demo_config.get('max_concurrent_demos', 3)
        
        if len(user_active_demos) >= max_concurrent:
            return {
                'allowed': False,
                'message': f'同時進行的AI演示已達上限 ({max_concurrent} 個)',
                'type': 'concurrent_demo_limit'
            }
        
        return {
            'allowed': True,
            'remaining_quota': quota_check.get('daily_remaining', -1),
            'concurrent_available': max_concurrent - len(user_active_demos)
        }
    
    async def _start_ai_demo_processing(
        self, 
        request_id: str, 
        demo_request: AIAnalysisRequest
    ) -> AIAnalysisResult:
        """開始AI演示處理"""
        
        # 創建演示結果對象
        demo_result = AIAnalysisResult(
            request_id=request_id,
            user_id=demo_request.user_id,
            stock_symbol=demo_request.stock_symbol,
            status=DemoStatus.PENDING,
            analysts_used=[a.value for a in demo_request.analyst_types],
            analysis_data={},
            start_time=datetime.now(),
            demo_limitations=self._get_tier_limitations(demo_request.membership_tier)
        )
        
        # 添加到活躍演示列表
        self.active_demos[request_id] = demo_result
        
        # 異步處理演示
        asyncio.create_task(self._process_ai_demo(demo_request, demo_result))
        
        return demo_result
    
    async def _process_ai_demo(
        self, 
        demo_request: AIAnalysisRequest, 
        demo_result: AIAnalysisResult
    ):
        """處理AI演示 (異步執行)"""
        
        try:
            demo_result.status = DemoStatus.RUNNING
            self.logger.info(f"開始AI演示處理: {demo_result.request_id}")
            
            # 調用本地AI分析演示
            analysis_results = await self._run_local_ai_analysis(
                demo_request.stock_symbol,
                demo_request.analyst_types,
                demo_request.membership_tier
            )
            
            demo_result.analysis_data = analysis_results
            demo_result.status = DemoStatus.COMPLETED
            demo_result.end_time = datetime.now()
            
            self.logger.info(f"AI演示處理完成: {demo_result.request_id}")
            
        except Exception as e:
            demo_result.status = DemoStatus.FAILED
            demo_result.error_message = str(e)
            demo_result.end_time = datetime.now()
            self.logger.error(f"AI演示處理失敗: {demo_result.request_id}, 錯誤: {e}")
    
    async def _run_local_ai_analysis(
        self, 
        stock_symbol: str,
        analyst_types: List[AIAnalystType],
        membership_tier: str
    ) -> Dict[str, Any]:
        """執行本地AI分析 (調用訓練完成的模型)"""
        
        try:
            # 檢查本地AI演示腳本是否存在
            demo_script_path = os.path.join(self.project_root, 'run_full_analysis_demo.py')
            
            if not os.path.exists(demo_script_path):
                return {
                    'error': 'demo_script_not_found',
                    'message': '本地AI演示腳本不存在',
                    'available_analysts': [],
                    'analysis_summary': '演示功能暫時不可用，請聯繫客服'
                }
            
            # 構建演示命令
            analysts_arg = ','.join([a.value for a in analyst_types])
            
            cmd = [
                sys.executable,
                demo_script_path,
                '--stock', stock_symbol,
                '--analysts', analysts_arg,
                '--tier', membership_tier,
                '--demo-mode'
            ]
            
            # 設置超時執行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5分鐘超時
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'error': 'analysis_timeout',
                    'message': 'AI分析演示超時',
                    'partial_results': '分析處理時間過長，請稍後再試'
                }
            
            if process.returncode != 0:
                self.logger.warning(f"AI演示腳本執行警告: {stderr.decode('utf-8', errors='ignore')}")
            
            # 解析結果
            output = stdout.decode('utf-8', errors='ignore')
            
            return {
                'status': 'completed',
                'stock_symbol': stock_symbol,
                'analysts_used': analysts_arg,
                'membership_tier': membership_tier,
                'analysis_output': output,
                'generated_at': datetime.now().isoformat(),
                'demo_mode': True,
                'limitations': self._get_tier_limitations(membership_tier)
            }
            
        except Exception as e:
            self.logger.error(f"執行本地AI分析失敗: {str(e)}")
            return {
                'error': 'analysis_failed',
                'message': f'AI分析執行失敗: {str(e)}',
                'fallback_analysis': self._generate_fallback_analysis(stock_symbol, membership_tier)
            }
    
    def _generate_fallback_analysis(self, stock_symbol: str, tier: str) -> Dict[str, str]:
        """生成備用分析 (當AI模型不可用時)"""
        
        tier_features = {
            'FREE': '基礎技術分析概覽',
            'GOLD': '完整基本面分析 + 技術分析 + 新聞情緒',
            'DIAMOND': '全方位深度分析 + 風險評估 + 投資建議'
        }
        
        return {
            'technical_analysis': f'{stock_symbol} 技術面分析: 根據您的 {tier} 會員等級提供 {tier_features.get(tier, "基礎")} 分析服務',
            'summary': f'這是 {tier} 會員的演示分析結果。完整功能需要升級到更高等級會員',
            'recommendation': '建議: 升級會員以獲得更詳細的AI分析功能',
            'next_steps': '聯繫客服了解完整功能，或升級會員體驗全方位AI投資顧問服務'
        }
    
    def _get_tier_limitations(self, tier: str) -> List[str]:
        """獲取會員等級限制說明"""
        
        base_limitations = self.demo_config.get('demo_limitations', [])
        
        tier_specific_limitations = {
            'FREE': [
                '僅提供基礎技術分析',
                '每日分析次數: 5次',
                '不包含實時數據更新',
                '升級至 GOLD 享受完整基本面分析'
            ],
            'GOLD': [
                '提供基本面 + 技術面 + 新聞分析',
                '每日分析次數: 50次',
                '包含部分實時數據',
                '升級至 DIAMOND 享受風險評估和投資建議'
            ],
            'DIAMOND': [
                '提供全方位深度分析',
                '無限制分析次數',
                '包含完整實時數據和優先支援'
            ]
        }
        
        return base_limitations + tier_specific_limitations.get(tier, [])
    
    async def get_demo_result(self, request_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取演示結果"""
        
        if request_id not in self.active_demos:
            return None
        
        demo_result = self.active_demos[request_id]
        
        # 驗證用戶權限
        if demo_result.user_id != user_id:
            return None
        
        result_dict = asdict(demo_result)
        result_dict['status'] = demo_result.status.value
        result_dict['start_time'] = demo_result.start_time.isoformat()
        
        if demo_result.end_time:
            result_dict['end_time'] = demo_result.end_time.isoformat()
            result_dict['duration_seconds'] = (
                demo_result.end_time - demo_result.start_time
            ).total_seconds()
        
        return result_dict
    
    async def list_user_demos(self, user_id: str) -> List[Dict[str, Any]]:
        """列出用戶的演示歷史"""
        
        user_demos = [
            demo for demo in self.active_demos.values()
            if demo.user_id == user_id
        ]
        
        return [
            {
                'request_id': demo.request_id,
                'stock_symbol': demo.stock_symbol,
                'status': demo.status.value,
                'analysts_used': demo.analysts_used,
                'start_time': demo.start_time.isoformat(),
                'end_time': demo.end_time.isoformat() if demo.end_time else None
            }
            for demo in sorted(user_demos, key=lambda x: x.start_time, reverse=True)
        ]
    
    async def cleanup_expired_demos(self, hours_old: int = 24):
        """清理過期的演示會話"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        expired_keys = []
        
        for request_id, demo in self.active_demos.items():
            if demo.start_time < cutoff_time and demo.status in [
                DemoStatus.COMPLETED, DemoStatus.FAILED, DemoStatus.CANCELLED
            ]:
                expired_keys.append(request_id)
        
        for key in expired_keys:
            del self.active_demos[key]
        
        self.logger.info(f"清理了 {len(expired_keys)} 個過期的AI演示會話")
        return len(expired_keys)
    
    async def get_membership_ai_features(self, tier: str) -> Dict[str, Any]:
        """獲取會員等級對應的AI功能"""
        
        available_analysts = self.tier_analyst_mapping.get(tier, [])
        
        return {
            'membership_tier': tier,
            'available_analysts': [
                {
                    'type': analyst.value,
                    'name': self._get_analyst_display_name(analyst),
                    'description': self._get_analyst_description(analyst)
                }
                for analyst in available_analysts
            ],
            'max_concurrent_demos': self.demo_config.get('max_concurrent_demos', 3),
            'daily_analysis_limit': self._get_daily_limit_for_tier(tier),
            'limitations': self._get_tier_limitations(tier),
            'upgrade_benefits': self._get_upgrade_benefits(tier)
        }
    
    def _get_analyst_display_name(self, analyst: AIAnalystType) -> str:
        """獲取分析師顯示名稱"""
        name_mapping = {
            AIAnalystType.TECHNICAL_ANALYST: '技術分析師',
            AIAnalystType.FUNDAMENTALS_ANALYST: '基本面分析師',
            AIAnalystType.NEWS_ANALYST: '新聞分析師',
            AIAnalystType.RISK_ANALYST: '風險分析師',
            AIAnalystType.SOCIAL_MEDIA_ANALYST: '社群媒體分析師',
            AIAnalystType.INVESTMENT_PLANNER: '投資規劃師'
        }
        return name_mapping.get(analyst, analyst.value)
    
    def _get_analyst_description(self, analyst: AIAnalystType) -> str:
        """獲取分析師描述"""
        desc_mapping = {
            AIAnalystType.TECHNICAL_ANALYST: '提供技術指標分析、趨勢預測和進出場點建議',
            AIAnalystType.FUNDAMENTALS_ANALYST: '分析財務報表、營收成長和公司基本面',
            AIAnalystType.NEWS_ANALYST: '分析新聞情緒、市場事件影響和媒體趨勢',
            AIAnalystType.RISK_ANALYST: '評估投資風險、波動性分析和風險管理建議',
            AIAnalystType.SOCIAL_MEDIA_ANALYST: '分析社群討論、投資人情緒和網路聲量',
            AIAnalystType.INVESTMENT_PLANNER: '制定投資策略、資產配置和投資組合建議'
        }
        return desc_mapping.get(analyst, '專業AI分析服務')
    
    def _get_daily_limit_for_tier(self, tier: str) -> int:
        """獲取會員等級每日限制"""
        limits = {
            'FREE': 5,
            'GOLD': 50,
            'DIAMOND': -1  # 無限制
        }
        return limits.get(tier, 5)
    
    def _get_upgrade_benefits(self, current_tier: str) -> List[str]:
        """獲取升級收益說明"""
        
        if current_tier == 'FREE':
            return [
                '升級至 GOLD: 獲得基本面分析師 + 新聞分析師',
                '每日分析次數提升至 50次',
                '包含社群媒體情緒分析',
                '優先客服支援'
            ]
        elif current_tier == 'GOLD':
            return [
                '升級至 DIAMOND: 獲得風險分析師 + 投資規劃師',
                '無限制分析次數',
                '完整實時數據訪問',
                '個人化投資建議和資產配置'
            ]
        else:
            return ['您已享受完整的AI分析功能']

# 便利函數
async def create_ai_demo_for_member(
    user_id: str,
    stock_symbol: str,
    tier: str = 'FREE',
    analyst_preferences: Optional[List[str]] = None
) -> Dict[str, Any]:
    """為會員創建AI演示的便利函數"""
    
    integrator = AIDemoIntegrator()
    return await integrator.create_ai_demo_session(
        user_id, stock_symbol, analyst_preferences
    )

async def get_member_ai_features(tier: str) -> Dict[str, Any]:
    """獲取會員AI功能的便利函數"""
    
    integrator = AIDemoIntegrator()
    return await integrator.get_membership_ai_features(tier)

# 全局整合器實例
_demo_integrator = AIDemoIntegrator()

def get_ai_demo_integrator() -> AIDemoIntegrator:
    """獲取全局AI演示整合器實例"""
    return _demo_integrator

if __name__ == "__main__":
    # 測試腳本
    async def test_ai_demo_integration():
        print("🤖 測試AI功能展示整合器")
        
        integrator = AIDemoIntegrator()
        
        # 測試不同等級會員的AI功能
        test_users = [
            ("free_user_demo", "FREE"),
            ("gold_user_demo", "GOLD"), 
            ("diamond_user_demo", "DIAMOND")
        ]
        
        for user_id, tier in test_users:
            print(f"\n測試 {tier} 會員: {user_id}")
            
            # 獲取AI功能特性
            features = await integrator.get_membership_ai_features(tier)
            print(f"  可用分析師: {len(features['available_analysts'])}")
            print(f"  每日限制: {features['daily_analysis_limit']}")
            
            # 創建AI演示
            demo_result = await integrator.create_ai_demo_session(
                user_id, "2330.TW", ["technical_analyst"]
            )
            print(f"  演示創建: {'✅ 成功' if demo_result['success'] else '❌ 失敗'}")
            
            if demo_result['success']:
                print(f"  演示ID: {demo_result['request_id']}")
                print(f"  選中分析師: {demo_result['selected_analysts']}")
        
        print("\n✅ 測試完成")
    
    asyncio.run(test_ai_demo_integration())