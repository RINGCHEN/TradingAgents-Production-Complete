"""
A/B測試服務
Task 6.2 - A/B測試框架建立的核心業務邏輯
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import secrets  # 安全修復：使用加密安全的隨機數生成器替換random
import uuid
import json

# 簡化導入
try:
    from ..models.ab_testing import ABTest, ABTestVariant, UserTestAssignment, ABTestEvent, TestStatus, VariantType, ABTestConfig
except ImportError:
    # 如果導入失敗，創建簡化版本
    class TestStatus:
        DRAFT = "draft"
        ACTIVE = "active" 
        PAUSED = "paused"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
    
    class VariantType:
        CONTROL = "control"
        TREATMENT = "treatment"
    
    class ABTestConfig:
        DEFAULT_CONFIDENCE_LEVEL = 95.0
        DEFAULT_MINIMUM_SAMPLE_SIZE = 1000
        
        @classmethod
        def validate_config(cls, config):
            return []

class ABTestingService:
    """A/B測試服務類"""
    
    def __init__(self, db=None):
        """初始化服務"""
        self.db = db
        self.config = ABTestConfig()
        
        # 內存存儲
        self.tests = {}
        self.assignments = {}
        self.events = {}
    
    def create_ab_test(self, name: str, description: str, primary_metric: str, variants: List[Dict[str, Any]], test_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """創建A/B測試"""
        try:
            # 驗證變體配置
            if len(variants) < 2:
                return {'success': False, 'error': '至少需要2個變體'}
            
            # 驗證流量分配
            total_weight = sum(v.get('traffic_weight', 50) for v in variants)
            if abs(total_weight - 100) > 0.01:
                return {'success': False, 'error': f'流量分配總和必須為100%，當前為{total_weight}%'}
            
            # 創建測試對象
            test_id = str(uuid.uuid4())
            test_data = {
                'id': test_id,
                'name': name,
                'description': description,
                'primary_metric': primary_metric,
                'status': TestStatus.DRAFT,
                'variants': [],
                'created_at': datetime.utcnow(),
                'start_date': None,
                'end_date': None
            }
            
            # 創建變體
            for i, variant_config in enumerate(variants):
                variant_id = str(uuid.uuid4())
                variant = {
                    'id': variant_id,
                    'test_id': test_id,
                    'name': variant_config.get('name', f'變體{i+1}'),
                    'variant_type': variant_config.get('type', VariantType.TREATMENT if i > 0 else VariantType.CONTROL),
                    'traffic_weight': variant_config.get('traffic_weight', 50),
                    'config': variant_config.get('config', {})
                }
                test_data['variants'].append(variant)
            
            # 保存測試
            self.tests[test_id] = test_data
            
            return {
                'success': True,
                'test_id': test_id,
                'test_data': {
                    'id': test_id,
                    'name': name,
                    'description': description,
                    'status': TestStatus.DRAFT,
                    'primary_metric': primary_metric,
                    'variants': [
                        {
                            'id': v['id'],
                            'name': v['name'],
                            'type': v['variant_type'],
                            'traffic_weight': v['traffic_weight']
                        } for v in test_data['variants']
                    ],
                    'created_at': test_data['created_at'].isoformat()
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def manage_test_status(self, test_id: str, action: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """管理測試狀態"""
        try:
            test = self.tests.get(test_id)
            if not test:
                return {'success': False, 'error': '測試不存在'}
            
            old_status = test['status']
            
            if action == 'start':
                if test['status'] != TestStatus.DRAFT:
                    return {'success': False, 'error': '只能啟動草稿狀態的測試'}
                test['status'] = TestStatus.ACTIVE
                test['start_date'] = datetime.utcnow()
                
            elif action == 'complete':
                if test['status'] not in [TestStatus.ACTIVE, TestStatus.PAUSED]:
                    return {'success': False, 'error': '只能完成進行中或暫停的測試'}
                test['status'] = TestStatus.COMPLETED
                test['end_date'] = datetime.utcnow()
            
            return {
                'success': True,
                'test_id': test_id,
                'old_status': old_status,
                'new_status': test['status'],
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def assign_user_to_test(self, test_id: str, user_id: Optional[int] = None, session_id: Optional[str] = None, user_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """用戶測試分組"""
        try:
            test = self.tests.get(test_id)
            if not test:
                return {'success': False, 'error': '測試不存在'}
            
            if test['status'] != TestStatus.ACTIVE:
                return {'success': False, 'error': '測試未啟用'}
            
            user_key = str(user_id or session_id)
            if not user_key:
                return {'success': False, 'error': '需要用戶ID或會話ID'}
            
            # 檢查現有分組
            for assignment in self.assignments.values():
                if (assignment['test_id'] == test_id and 
                    ((user_id and assignment.get('user_id') == user_id) or 
                     (session_id and assignment.get('session_id') == session_id))):
                    
                    variant = next((v for v in test['variants'] if v['id'] == assignment['variant_id']), None)
                    if variant:
                        return {
                            'success': True,
                            'assignment': {
                                'assignment_id': assignment['id'],
                                'test_id': test_id,
                                'variant_id': variant['id'],
                                'variant_name': variant['name'],
                                'variant_type': variant['variant_type'],
                                'variant_config': variant['config'],
                                'assigned_at': assignment['assigned_at']
                            },
                            'is_new_assignment': False
                        }
            
            # 執行分組
            selected_variant = self._assign_variant(test, user_key)
            if not selected_variant:
                return {'success': False, 'error': '分組失敗'}
            
            # 創建分組記錄
            assignment_id = str(uuid.uuid4())
            assignment = {
                'id': assignment_id,
                'test_id': test_id,
                'variant_id': selected_variant['id'],
                'user_id': user_id,
                'session_id': session_id,
                'assigned_at': datetime.utcnow().isoformat()
            }
            
            self.assignments[assignment_id] = assignment
            
            return {
                'success': True,
                'assignment': {
                    'assignment_id': assignment_id,
                    'test_id': test_id,
                    'variant_id': selected_variant['id'],
                    'variant_name': selected_variant['name'],
                    'variant_type': selected_variant['variant_type'],
                    'variant_config': selected_variant['config'],
                    'assigned_at': assignment['assigned_at']
                },
                'is_new_assignment': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def track_test_event(self, test_id: str, assignment_id: str, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """追蹤測試事件"""
        try:
            test = self.tests.get(test_id)
            if not test:
                return {'success': False, 'error': '測試不存在'}
            
            assignment = self.assignments.get(assignment_id)
            if not assignment:
                return {'success': False, 'error': '分組不存在'}
            
            event_id = str(uuid.uuid4())
            event = {
                'id': event_id,
                'test_id': test_id,
                'assignment_id': assignment_id,
                'event_name': event_name,
                'event_type': event_data.get('event_type', 'custom') if event_data else 'custom',
                'event_value': event_data.get('event_value', 0) if event_data else 0,
                'timestamp': datetime.utcnow()
            }
            
            self.events[event_id] = event
            
            return {
                'success': True,
                'event_id': event_id,
                'tracked_at': event['timestamp'].isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_test_results(self, test_id: str, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """獲取測試結果"""
        try:
            test = self.tests.get(test_id)
            if not test:
                return {'success': False, 'error': '測試不存在'}
            
            # 獲取測試數據
            assignments = [a for a in self.assignments.values() if a['test_id'] == test_id]
            events = [e for e in self.events.values() if e['test_id'] == test_id]
            
            # 計算各變體結果
            variant_results = {}
            for variant in test['variants']:
                variant_assignments = [a for a in assignments if a['variant_id'] == variant['id']]
                variant_events = [e for e in events if any(a['id'] == e['assignment_id'] for a in variant_assignments)]
                
                sample_size = len(variant_assignments)
                conversion_events = [e for e in variant_events if e['event_name'] == 'conversion']
                conversion_count = len(conversion_events)
                conversion_rate = (conversion_count / sample_size) if sample_size > 0 else 0
                
                variant_results[variant['id']] = {
                    'variant_id': variant['id'],
                    'variant_name': variant['name'],
                    'variant_type': variant['variant_type'],
                    'sample_size': sample_size,
                    'conversion_count': conversion_count,
                    'conversion_rate': conversion_rate,
                    'revenue': sum(e.get('event_value', 0) for e in conversion_events),
                    'average_order_value': 0,
                    'revenue_per_visitor': 0
                }
            
            # 簡化的統計結果
            statistical_results = {
                'confidence_level': 95.0,
                'significance_threshold': 0.05,
                'comparisons': []
            }
            
            # 生成測試總結
            total_participants = sum(r['sample_size'] for r in variant_results.values())
            total_conversions = sum(r['conversion_count'] for r in variant_results.values())
            overall_conversion_rate = (total_conversions / total_participants) if total_participants > 0 else 0
            
            test_summary = {
                'test_duration_days': (datetime.utcnow() - test['created_at']).days,
                'total_participants': total_participants,
                'total_conversions': total_conversions,
                'overall_conversion_rate': overall_conversion_rate,
                'has_significant_results': False,
                'recommendation': "需要更多數據進行分析",
                'next_steps': ["繼續收集數據", "監控測試進展"]
            }
            
            return {
                'success': True,
                'test_id': test_id,
                'test_name': test['name'],
                'test_status': test['status'],
                'primary_metric': test['primary_metric'],
                'variant_results': variant_results,
                'statistical_results': statistical_results,
                'test_summary': test_summary,
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_test_dashboard(self, test_id: Optional[str] = None, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """獲取測試儀表板"""
        try:
            tests = list(self.tests.values())
            
            if test_id:
                tests = [t for t in tests if t['id'] == test_id]
            if status_filter:
                tests = [t for t in tests if t['status'] == status_filter]
            
            dashboard_data = {
                'total_tests': len(tests),
                'active_tests': len([t for t in tests if t['status'] == TestStatus.ACTIVE]),
                'completed_tests': len([t for t in tests if t['status'] == TestStatus.COMPLETED]),
                'draft_tests': len([t for t in tests if t['status'] == TestStatus.DRAFT]),
                'tests': []
            }
            
            for test in tests:
                test_summary = {
                    'id': test['id'],
                    'name': test['name'],
                    'status': test['status'],
                    'primary_metric': test['primary_metric'],
                    'variant_count': len(test['variants']),
                    'created_at': test['created_at'].isoformat(),
                    'start_date': test['start_date'].isoformat() if test['start_date'] else None,
                    'end_date': test['end_date'].isoformat() if test['end_date'] else None
                }
                dashboard_data['tests'].append(test_summary)
            
            return {
                'success': True,
                'dashboard': dashboard_data,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _assign_variant(self, test: Dict[str, Any], user_key: str) -> Optional[Dict[str, Any]]:
        """分配變體"""
        hash_value = int(hashlib.sha256(f"{test['id']}:{user_key}".encode()).hexdigest()[:8], 16)  # 安全修復：使用SHA256替換MD5
        percentage = (hash_value % 10000) / 100
        
        cumulative_weight = 0
        for variant in test['variants']:
            cumulative_weight += variant['traffic_weight']
            if percentage < cumulative_weight:
                return variant
        
        return test['variants'][0] if test['variants'] else None