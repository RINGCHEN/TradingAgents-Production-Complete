#!/usr/bin/env python3
"""
Virtual P&L System Initialization Script
GPT-OSS虛擬損益表系統初始化腳本

功能：
1. 創建所有虛擬損益表相關的數據表
2. 初始化標準成本中心層級結構
3. 設置初始預算分配
4. 創建示例成本和收益記錄
5. 生成初始P&L摘要
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from .virtual_pnl_db import VirtualPnLDB
from .virtual_pnl_models import (
    CostCategory, CostType, RevenueSource, BudgetPeriodType, AllocationMethod,
    CostTrackingCreate, RevenueAttributionCreate, BudgetAllocationCreate
)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VirtualPnLInitializer:
    """虛擬損益表系統初始化器"""
    
    def __init__(self):
        self.pnl_db = VirtualPnLDB()
        self.initialized_cost_centers = {}
        self.current_year = datetime.now().year
        self.current_date = date.today()
    
    async def initialize_complete_system(self) -> Dict[str, Any]:
        """完整系統初始化"""
        logger.info("🚀 Starting Virtual P&L System initialization...")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'success',
            'components': {},
            'errors': []
        }
        
        try:
            # 1. 初始化成本中心結構
            cost_centers_result = await self._initialize_cost_center_hierarchy()
            results['components']['cost_centers'] = cost_centers_result
            
            # 2. 設置初始預算
            budget_result = await self._initialize_budget_allocations()
            results['components']['budgets'] = budget_result
            
            # 3. 創建示例成本記錄
            costs_result = await self._create_sample_cost_records()
            results['components']['cost_records'] = costs_result
            
            # 4. 創建示例收益記錄
            revenue_result = await self._create_sample_revenue_records()
            results['components']['revenue_records'] = revenue_result
            
            # 5. 生成初始P&L摘要
            pnl_result = await self._generate_initial_pnl_summaries()
            results['components']['pnl_summaries'] = pnl_result
            
            # 6. 系統健康檢查
            health_result = await self.pnl_db.health_check()
            results['components']['health_check'] = health_result
            
            logger.info("✅ Virtual P&L System initialization completed successfully")
            
        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(str(e))
            logger.error(f"❌ System initialization failed: {e}")
        
        return results
    
    async def _initialize_cost_center_hierarchy(self) -> Dict[str, Any]:
        """初始化成本中心層級結構"""
        logger.info("📊 Initializing cost center hierarchy...")
        
        # 定義完整的成本中心結構
        cost_center_structure = [
            # 第0層 - 根級成本中心
            {
                'code': 'TWSTOCK',
                'name': 'TwStock Trading Platform',
                'description': '台股交易平台總部',
                'level': 0,
                'manager': 'CEO',
                'department': 'Executive',
                'budget_limit': Decimal('10000000.00')  # 1000萬預算上限
            },
            
            # 第1層 - 主要事業部
            {
                'code': 'TECH',
                'name': 'Technology Division',
                'description': '技術事業部',
                'parent_code': 'TWSTOCK',
                'level': 1,
                'manager': 'CTO',
                'department': 'Technology',
                'budget_limit': Decimal('5000000.00')
            },
            {
                'code': 'PRODUCT',
                'name': 'Product Division',
                'description': '產品事業部',
                'parent_code': 'TWSTOCK',
                'level': 1,
                'manager': 'CPO',
                'department': 'Product',
                'budget_limit': Decimal('2000000.00')
            },
            {
                'code': 'OPS',
                'name': 'Operations Division',
                'description': '運營事業部',
                'parent_code': 'TWSTOCK',
                'level': 1,
                'manager': 'COO',
                'department': 'Operations',
                'budget_limit': Decimal('1500000.00')
            },
            
            # 第2層 - AI服務部門
            {
                'code': 'AI_SERVICES',
                'name': 'AI Services Department',
                'description': 'AI服務部門',
                'parent_code': 'TECH',
                'level': 2,
                'manager': 'AI Director',
                'department': 'AI Engineering',
                'budget_limit': Decimal('3000000.00')
            },
            {
                'code': 'PLATFORM',
                'name': 'Platform Engineering',
                'description': '平台工程部',
                'parent_code': 'TECH',
                'level': 2,
                'manager': 'Platform Director',
                'department': 'Platform',
                'budget_limit': Decimal('1500000.00')
            },
            
            # 第3層 - GPT-OSS項目
            {
                'code': 'GPT_OSS',
                'name': 'GPT-OSS Local Inference',
                'description': 'GPT-OSS本地推理服務',
                'parent_code': 'AI_SERVICES',
                'level': 3,
                'manager': 'GPT-OSS Lead',
                'department': 'AI Engineering',
                'budget_limit': Decimal('1500000.00')
            },
            {
                'code': 'ALPHA_ENGINE',
                'name': 'Alpha Engine Premium',
                'description': '阿爾法引擎高級功能',
                'parent_code': 'AI_SERVICES',
                'level': 3,
                'manager': 'Alpha Lead',
                'department': 'Quantitative Research',
                'budget_limit': Decimal('800000.00')
            },
            
            # 第4層 - GPT-OSS子項目
            {
                'code': 'GPT_INFERENCE',
                'name': 'GPT Inference Engine',
                'description': 'GPT推理引擎',
                'parent_code': 'GPT_OSS',
                'level': 4,
                'manager': 'Inference Lead',
                'department': 'AI Engineering',
                'budget_limit': Decimal('600000.00')
            },
            {
                'code': 'GPT_INFRASTRUCTURE',
                'name': 'GPT Infrastructure',
                'description': 'GPT基礎設施',
                'parent_code': 'GPT_OSS',
                'level': 4,
                'manager': 'Infrastructure Lead',
                'department': 'DevOps',
                'budget_limit': Decimal('500000.00')
            },
            {
                'code': 'GPT_OPERATIONS',
                'name': 'GPT Operations',
                'description': 'GPT運營維護',
                'parent_code': 'GPT_OSS',
                'level': 4,
                'manager': 'Operations Lead',
                'department': 'Site Reliability',
                'budget_limit': Decimal('400000.00')
            }
        ]
        
        created_count = 0
        
        try:
            # 按層級順序創建成本中心
            for level in range(5):  # 0-4層
                for center_data in cost_center_structure:
                    if center_data['level'] == level:
                        # 處理父級關係
                        parent_id = None
                        if 'parent_code' in center_data:
                            parent_code = center_data['parent_code']
                            if parent_code in self.initialized_cost_centers:
                                parent_id = self.initialized_cost_centers[parent_code].id
                        
                        # 創建成本中心
                        cost_center = await self.pnl_db.create_cost_center(
                            code=center_data['code'],
                            name=center_data['name'],
                            description=center_data.get('description'),
                            parent_id=parent_id,
                            manager=center_data.get('manager'),
                            department=center_data.get('department'),
                            budget_limit=center_data.get('budget_limit')
                        )
                        
                        self.initialized_cost_centers[center_data['code']] = cost_center
                        created_count += 1
                        
                        logger.info(f"✅ Created cost center: {center_data['code']} - {center_data['name']}")
            
            return {
                'status': 'success',
                'created_count': created_count,
                'cost_centers': list(self.initialized_cost_centers.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize cost centers: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'created_count': created_count
            }
    
    async def _initialize_budget_allocations(self) -> Dict[str, Any]:
        """初始化預算分配"""
        logger.info("💰 Initializing budget allocations...")
        
        # GPT-OSS相關成本中心的預算分配
        budget_allocations = [
            # GPT-OSS主項目年度預算
            {
                'cost_center_code': 'GPT_OSS',
                'budget_year': self.current_year,
                'budget_period_type': BudgetPeriodType.ANNUAL,
                'total_budget': Decimal('1500000.00'),
                'hardware_budget': Decimal('600000.00'),
                'infrastructure_budget': Decimal('300000.00'),
                'power_budget': Decimal('200000.00'),
                'personnel_budget': Decimal('300000.00'),
                'maintenance_budget': Decimal('80000.00'),
                'software_budget': Decimal('20000.00'),
                'revenue_target': Decimal('2500000.00'),
                'cost_savings_target': Decimal('800000.00'),
                'roi_target': Decimal('66.67'),  # 預期ROI 66.67%
                'description': f'{self.current_year}年度GPT-OSS項目預算',
                'assumptions': {
                    'hardware_assumptions': 'GPU集群擴展計劃',
                    'personnel_assumptions': '3名AI工程師 + 2名DevOps',
                    'revenue_assumptions': '會員升級收益 + API使用費',
                    'cost_savings_assumptions': '相較於雲端API服務的節省'
                }
            },
            
            # GPT推理引擎季度預算
            {
                'cost_center_code': 'GPT_INFERENCE',
                'budget_year': self.current_year,
                'budget_period_type': BudgetPeriodType.QUARTERLY,
                'budget_period': ((self.current_date.month - 1) // 3) + 1,
                'total_budget': Decimal('150000.00'),
                'hardware_budget': Decimal('80000.00'),
                'infrastructure_budget': Decimal('30000.00'),
                'power_budget': Decimal('25000.00'),
                'personnel_budget': Decimal('15000.00'),
                'revenue_target': Decimal('300000.00'),
                'roi_target': Decimal('100.00'),
                'description': f'{self.current_year}年Q{((self.current_date.month - 1) // 3) + 1}推理引擎預算'
            },
            
            # GPT基礎設施季度預算
            {
                'cost_center_code': 'GPT_INFRASTRUCTURE',
                'budget_year': self.current_year,
                'budget_period_type': BudgetPeriodType.QUARTERLY,
                'budget_period': ((self.current_date.month - 1) // 3) + 1,
                'total_budget': Decimal('125000.00'),
                'hardware_budget': Decimal('50000.00'),
                'infrastructure_budget': Decimal('60000.00'),
                'power_budget': Decimal('10000.00'),
                'maintenance_budget': Decimal('5000.00'),
                'revenue_target': Decimal('0.00'),  # 基礎設施不直接產生收益
                'cost_savings_target': Decimal('80000.00'),
                'roi_target': Decimal('0.00'),  # 通過成本節省實現價值
                'description': f'{self.current_year}年Q{((self.current_date.month - 1) // 3) + 1}基礎設施預算'
            },
            
            # 阿爾法引擎年度預算
            {
                'cost_center_code': 'ALPHA_ENGINE',
                'budget_year': self.current_year,
                'budget_period_type': BudgetPeriodType.ANNUAL,
                'total_budget': Decimal('800000.00'),
                'hardware_budget': Decimal('200000.00'),
                'infrastructure_budget': Decimal('150000.00'),
                'personnel_budget': Decimal('400000.00'),
                'software_budget': Decimal('50000.00'),
                'revenue_target': Decimal('1500000.00'),
                'roi_target': Decimal('87.50'),  # 預期ROI 87.5%
                'description': f'{self.current_year}年度阿爾法引擎預算',
                'assumptions': {
                    'revenue_assumptions': '高級功能訂閱 + 交易佣金分成',
                    'personnel_assumptions': '量化研究團隊 + AI工程師'
                }
            }
        ]
        
        created_count = 0
        
        try:
            for budget_data in budget_allocations:
                cost_center_code = budget_data.pop('cost_center_code')
                
                if cost_center_code not in self.initialized_cost_centers:
                    logger.warning(f"⚠️ Cost center {cost_center_code} not found, skipping budget")
                    continue
                
                budget_create_data = BudgetAllocationCreate(
                    cost_center_id=self.initialized_cost_centers[cost_center_code].id,
                    **budget_data
                )
                
                budget = await self.pnl_db.create_budget_allocation(
                    budget_create_data,
                    created_by="system_init"
                )
                
                created_count += 1
                logger.info(f"✅ Created budget for {cost_center_code}: ${budget_data['total_budget']}")
            
            return {
                'status': 'success',
                'created_count': created_count
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize budgets: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'created_count': created_count
            }
    
    async def _create_sample_cost_records(self) -> Dict[str, Any]:
        """創建示例成本記錄"""
        logger.info("💸 Creating sample cost records...")
        
        # 生成過去3個月的成本記錄
        sample_costs = []
        
        for month_offset in range(3):  # 過去3個月
            record_date = (self.current_date.replace(day=1) - timedelta(days=month_offset * 30))
            
            # GPT-OSS硬體成本
            sample_costs.extend([
                {
                    'cost_center_code': 'GPT_INFERENCE',
                    'record_date': record_date,
                    'cost_category': CostCategory.HARDWARE,
                    'cost_type': CostType.AMORTIZED,
                    'amount': Decimal('25000.00'),
                    'description': 'GPU服務器攤銷成本',
                    'cost_details': {
                        'hardware_type': 'NVIDIA A100 GPU Cluster',
                        'quantity': 8,
                        'unit_cost': 3125.00,
                        'amortization_period_months': 36
                    },
                    'allocation_method': AllocationMethod.COMPUTE_TIME,
                    'source_system': 'asset_management'
                },
                
                # 電力成本
                {
                    'cost_center_code': 'GPT_INFRASTRUCTURE',
                    'record_date': record_date,
                    'cost_category': CostCategory.POWER,
                    'cost_type': CostType.VARIABLE,
                    'amount': Decimal('8500.00'),
                    'description': '數據中心電力費用',
                    'cost_details': {
                        'kwh_consumed': 85000,
                        'rate_per_kwh': 0.10,
                        'peak_hours_usage': 60000,
                        'off_peak_usage': 25000
                    },
                    'allocation_method': AllocationMethod.COMPUTE_TIME,
                    'source_system': 'facility_management'
                },
                
                # 人力成本
                {
                    'cost_center_code': 'GPT_OSS',
                    'record_date': record_date,
                    'cost_category': CostCategory.PERSONNEL,
                    'cost_type': CostType.FIXED,
                    'amount': Decimal('75000.00'),
                    'description': 'GPT-OSS團隊薪資成本',
                    'cost_details': {
                        'team_size': 5,
                        'average_salary': 15000.00,
                        'positions': ['AI Engineer', 'DevOps Engineer', 'Site Reliability Engineer'],
                        'benefits_included': True
                    },
                    'allocation_method': AllocationMethod.FIXED_RATIO,
                    'source_system': 'hr_system'
                },
                
                # 維護成本
                {
                    'cost_center_code': 'GPT_OPERATIONS',
                    'record_date': record_date,
                    'cost_category': CostCategory.MAINTENANCE,
                    'cost_type': CostType.VARIABLE,
                    'amount': Decimal('12000.00'),
                    'description': '系統維護和監控成本',
                    'cost_details': {
                        'monitoring_tools': 5000.00,
                        'support_contracts': 4000.00,
                        'spare_parts': 3000.00
                    },
                    'allocation_method': AllocationMethod.ACTIVITY_BASED,
                    'source_system': 'maintenance_system'
                },
                
                # 雲端後備成本
                {
                    'cost_center_code': 'GPT_OSS',
                    'record_date': record_date,
                    'cost_category': CostCategory.CLOUD_FALLBACK,
                    'cost_type': CostType.VARIABLE,
                    'amount': Decimal('3500.00'),
                    'description': 'OpenAI API後備服務成本',
                    'cost_details': {
                        'api_calls': 350000,
                        'tokens_processed': 10500000,
                        'average_cost_per_1k_tokens': 0.0033
                    },
                    'allocation_method': AllocationMethod.TOKEN_USAGE,
                    'source_system': 'api_billing'
                }
            ])
        
        # 批量創建成本記錄
        cost_records_to_create = []
        
        for cost_data in sample_costs:
            cost_center_code = cost_data.pop('cost_center_code')
            
            if cost_center_code not in self.initialized_cost_centers:
                continue
            
            cost_create_data = CostTrackingCreate(
                cost_center_id=self.initialized_cost_centers[cost_center_code].id,
                **cost_data
            )
            cost_records_to_create.append(cost_create_data)
        
        try:
            created_records = await self.pnl_db.batch_create_cost_tracking(
                cost_records_to_create,
                created_by="system_init"
            )
            
            logger.info(f"✅ Created {len(created_records)} sample cost records")
            
            return {
                'status': 'success',
                'created_count': len(created_records),
                'total_amount': sum(float(record.amount) for record in created_records)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample cost records: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'created_count': 0
            }
    
    async def _create_sample_revenue_records(self) -> Dict[str, Any]:
        """創建示例收益記錄"""
        logger.info("💰 Creating sample revenue records...")
        
        # 生成過去3個月的收益記錄
        sample_revenues = []
        
        for month_offset in range(3):
            record_date = (self.current_date.replace(day=1) - timedelta(days=month_offset * 30))
            
            sample_revenues.extend([
                # 會員升級收益
                {
                    'record_date': record_date,
                    'revenue_source': RevenueSource.MEMBERSHIP_UPGRADE,
                    'amount': Decimal('85000.00'),
                    'description': '由於AI功能改善帶來的會員升級收益',
                    'attribution_method': 'AI_feature_correlation_analysis',
                    'attribution_confidence': Decimal('0.85'),
                    'gpt_oss_contribution_ratio': Decimal('0.70'),
                    'customer_tier': 'premium',
                    'product_feature': 'enhanced_ai_analysis',
                    'revenue_details': {
                        'new_upgrades': 340,
                        'upgrade_value_per_user': 250.00,
                        'retention_improvement': 0.12,
                        'ai_feature_usage_correlation': 0.78
                    },
                    'baseline_period': f'{record_date.year - 1}-{record_date.month:02d}',
                    'baseline_amount': Decimal('45000.00'),
                    'incremental_amount': Decimal('40000.00')
                },
                
                # 阿爾法引擎高級功能收益
                {
                    'record_date': record_date,
                    'revenue_source': RevenueSource.ALPHA_ENGINE_PREMIUM,
                    'amount': Decimal('120000.00'),
                    'description': 'GPT增強的阿爾法引擎高級功能訂閱',
                    'attribution_method': 'direct_feature_subscription',
                    'attribution_confidence': Decimal('0.95'),
                    'gpt_oss_contribution_ratio': Decimal('0.90'),
                    'customer_tier': 'enterprise',
                    'product_feature': 'gpt_enhanced_alpha_signals',
                    'revenue_details': {
                        'active_subscriptions': 480,
                        'monthly_subscription_fee': 250.00,
                        'enterprise_tier_premium': 50.00,
                        'feature_adoption_rate': 0.73
                    }
                },
                
                # API使用費收益
                {
                    'record_date': record_date,
                    'revenue_source': RevenueSource.API_USAGE_FEES,
                    'amount': Decimal('25000.00'),
                    'description': 'GPT-OSS API第三方使用費',
                    'attribution_method': 'direct_usage_billing',
                    'attribution_confidence': Decimal('1.00'),
                    'gpt_oss_contribution_ratio': Decimal('1.00'),
                    'revenue_details': {
                        'api_calls': 2500000,
                        'billable_tokens': 75000000,
                        'rate_per_1k_tokens': 0.0033,
                        'third_party_integrations': 12
                    }
                },
                
                # 成本節省（虛擬收益）
                {
                    'record_date': record_date,
                    'revenue_source': RevenueSource.COST_SAVINGS,
                    'amount': Decimal('45000.00'),
                    'description': '相較於雲端API服務的成本節省',
                    'attribution_method': 'cost_comparison_analysis',
                    'attribution_confidence': Decimal('0.90'),
                    'gpt_oss_contribution_ratio': Decimal('1.00'),
                    'revenue_details': {
                        'tokens_processed_locally': 15000000,
                        'cloud_api_equivalent_cost': 49500.00,
                        'actual_local_cost': 4500.00,
                        'net_savings': 45000.00,
                        'savings_rate': 0.91
                    },
                    'baseline_period': 'pre_gpt_oss',
                    'baseline_amount': Decimal('49500.00')
                }
            ])
        
        created_count = 0
        total_revenue = Decimal('0')
        
        try:
            for revenue_data in sample_revenues:
                revenue_create_data = RevenueAttributionCreate(**revenue_data)
                
                revenue_record = await self.pnl_db.create_revenue_attribution(
                    revenue_create_data,
                    created_by="system_init"
                )
                
                created_count += 1
                total_revenue += revenue_record.amount
                
                logger.info(f"✅ Created revenue record: {revenue_record.revenue_source} - ${revenue_record.amount}")
            
            return {
                'status': 'success',
                'created_count': created_count,
                'total_revenue': float(total_revenue)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample revenue records: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'created_count': created_count
            }
    
    async def _generate_initial_pnl_summaries(self) -> Dict[str, Any]:
        """生成初始P&L摘要"""
        logger.info("📊 Generating initial P&L summaries...")
        
        try:
            # 觸發P&L摘要更新 - 通過創建一個虛擬記錄來觸發更新機制
            dummy_cost = CostTrackingCreate(
                cost_center_id=self.initialized_cost_centers['GPT_OSS'].id,
                record_date=self.current_date,
                cost_category=CostCategory.OTHER,
                cost_type=CostType.VARIABLE,
                amount=Decimal('0.01'),
                description='System initialization trigger record'
            )
            
            trigger_record = await self.pnl_db.create_cost_tracking(
                dummy_cost,
                created_by="system_init"
            )
            
            # 生成P&L報告驗證摘要是否正確創建
            pnl_report = await self.pnl_db.get_pnl_report(
                cost_center_ids=[self.initialized_cost_centers['GPT_OSS'].id],
                period_type="monthly"
            )
            
            logger.info("✅ P&L summaries generated successfully")
            
            return {
                'status': 'success',
                'summary_periods': pnl_report['summary']['total_periods'],
                'sample_report': pnl_report
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate P&L summaries: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

# 主要初始化函數
async def initialize_virtual_pnl_system() -> Dict[str, Any]:
    """初始化完整的虛擬損益表系統"""
    initializer = VirtualPnLInitializer()
    return await initializer.initialize_complete_system()

# 快速初始化函數（僅基本結構）
async def quick_initialize_virtual_pnl() -> Dict[str, Any]:
    """快速初始化（僅基本結構，不包含示例數據）"""
    logger.info("🚀 Starting quick Virtual P&L initialization...")
    
    try:
        pnl_db = VirtualPnLDB()
        
        # 健康檢查
        health = await pnl_db.health_check()
        
        result = {
            'status': 'success',
            'initialization_type': 'quick',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health_check': health
        }
        
        logger.info("✅ Quick Virtual P&L initialization completed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Quick initialization failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'initialization_type': 'quick'
        }

# CLI執行支持
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        result = asyncio.run(quick_initialize_virtual_pnl())
    else:
        result = asyncio.run(initialize_virtual_pnl_system())
    
    print("\n" + "="*60)
    print("Virtual P&L System Initialization Results")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Timestamp: {result.get('timestamp', 'N/A')}")
    
    if result['status'] == 'success':
        components = result.get('components', {})
        for component, details in components.items():
            if isinstance(details, dict) and 'status' in details:
                status_icon = "✅" if details['status'] == 'success' else "❌"
                print(f"{status_icon} {component}: {details.get('created_count', 'N/A')} items")
    
    if result.get('errors'):
        print("\nErrors encountered:")
        for error in result['errors']:
            print(f"❌ {error}")
    
    print("="*60)