#!/usr/bin/env python3
"""
修正缺失的關鍵系統組件

此腳本將補充完整部署版本中缺失的關鍵系統，
確保17個核心系統100%完整。

作者：天工 (TianGong) + Claude Code
日期：2025-09-05
版本：v1.0 (修正補充版)
"""

import os
import shutil
from pathlib import Path
import json

class MissingSystemsFixer:
    def __init__(self):
        self.source_dir = Path(__file__).parent.parent  # TradingAgents
        self.target_dir = self.source_dir.parent / "TradingAgents-Production-Complete"
        
        # 缺失的關鍵系統組件
        self.missing_systems = {
            'System_8_AI_Model_Service': {
                'directories': ['gpu_training', 'gpt_oss'],
                'priority': 'P2',
                'description': 'GPU加速訓練 + GPT-OSS模型服務'
            },
            'System_12_Monitoring': {
                'directories': ['monitoring'],
                'priority': 'P0',
                'description': 'Grafana + Prometheus 監控系統'
            },
            'System_15_Development_Testing': {
                'directories': ['tests', 'scripts'],
                'priority': 'P1', 
                'description': '開發測試系統 + 工具腳本'
            },
            'System_16_Business_Intelligence': {
                'directories': ['evaluation_results', 'reports', 'work_reports'],
                'priority': 'P3',
                'description': '商業智能 + 分析報告系統'
            },
            'Data_Infrastructure_Supplement': {
                'directories': ['data', 'ai_training_data'],
                'priority': 'P2',
                'description': '數據基礎設施補充'
            },
            'Security_Configuration_Supplement': {
                'directories': ['secure', 'deployment'],
                'priority': 'P1',
                'description': '安全配置 + 部署配置補充'
            }
        }

    def fix_missing_systems(self):
        """修正缺失的系統組件"""
        print("[START] 開始修正缺失的關鍵系統組件...")
        
        if not self.target_dir.exists():
            print(f"[ERROR] 目標目錄不存在: {self.target_dir}")
            return
        
        print(f"[INFO] 源目錄: {self.source_dir}")
        print(f"[INFO] 目標目錄: {self.target_dir}")
        
        # 按優先級修正系統
        priority_order = ['P0', 'P1', 'P2', 'P3']
        
        total_fixed = 0
        total_attempted = 0
        
        for priority in priority_order:
            print(f"\n[PRIORITY] 處理 {priority} 級別系統...")
            
            for system_name, config in self.missing_systems.items():
                if config['priority'] == priority:
                    print(f"\n[SYSTEM] {system_name}: {config['description']}")
                    
                    for dir_name in config['directories']:
                        total_attempted += 1
                        if self._copy_missing_directory(dir_name):
                            total_fixed += 1
        
        # 生成修正報告
        self._generate_fix_report(total_fixed, total_attempted)
        
        print(f"\n[SUCCESS] 系統修正完成: {total_fixed}/{total_attempted}")

    def _copy_missing_directory(self, dir_name):
        """複製缺失的目錄"""
        source_path = self.source_dir / dir_name
        target_path = self.target_dir / dir_name
        
        if not source_path.exists():
            print(f"  [MISSING] {dir_name}/ - 源目錄不存在")
            return False
        
        if target_path.exists():
            print(f"  [SKIP] {dir_name}/ - 已存在")
            return True
        
        try:
            # 複製目錄，排除不必要文件
            shutil.copytree(
                source_path,
                target_path,
                ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '*.log',
                    'node_modules', '.git', '.pytest_cache',
                    '*.tmp', '*.temp', 'logs', '*.db',
                    'mlruns', 'test_*.db',
                    '*.bin', '*.safetensors',  # 大型模型文件
                    'venv', '.venv', 'env'
                )
            )
            print(f"  [OK] {dir_name}/ - 複製完成")
            return True
            
        except Exception as e:
            print(f"  [ERROR] {dir_name}/ - 複製失敗: {str(e)}")
            return False

    def _generate_fix_report(self, total_fixed, total_attempted):
        """生成修正報告"""
        print(f"\n[REPORT] 生成系統修正報告...")
        
        # 重新驗證17個系統
        system_verification = self._verify_all_systems()
        
        report = {
            'fix_info': {
                'fix_date': '2025-09-05',
                'systems_attempted': total_attempted,
                'systems_fixed': total_fixed,
                'fix_success_rate': round((total_fixed / total_attempted) * 100, 1) if total_attempted > 0 else 0
            },
            'system_verification': system_verification,
            'missing_systems_status': {}
        }
        
        # 檢查每個缺失系統的修正狀態
        for system_name, config in self.missing_systems.items():
            fixed_dirs = []
            missing_dirs = []
            
            for dir_name in config['directories']:
                target_path = self.target_dir / dir_name
                if target_path.exists():
                    fixed_dirs.append(dir_name)
                else:
                    missing_dirs.append(dir_name)
            
            report['missing_systems_status'][system_name] = {
                'description': config['description'],
                'priority': config['priority'],
                'fixed_directories': fixed_dirs,
                'still_missing': missing_dirs,
                'completion_rate': round((len(fixed_dirs) / len(config['directories'])) * 100, 1)
            }
        
        # 保存報告
        with open(self.target_dir / 'SYSTEM_FIX_REPORT.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[REPORT] 報告已保存: SYSTEM_FIX_REPORT.json")

    def _verify_all_systems(self):
        """驗證所有17個系統"""
        return {
            'frontend_systems': {
                'System_1_main_frontend': (self.target_dir / 'frontend').exists(),
                'System_2_member_system': (self.target_dir / 'frontend/src/components/MemberAI').exists(),
                'System_3_admin_backend': (self.target_dir / 'frontend/src/admin/AdminApp_Ultimate.tsx').exists(),
            },
            'backend_api_systems': {
                'System_4_fastapi_core': (self.target_dir / 'tradingagents/app.py').exists(),
                'System_5_payuni_payment': (self.target_dir / 'tradingagents/api/payuni_endpoints.py').exists(),
            },
            'ai_intelligence_systems': {
                'System_6_ai_analysts': (self.target_dir / 'tradingagents/agents/analysts').exists(),
                'System_7_ai_training': (self.target_dir / 'training').exists(),
                'System_8_model_service': (self.target_dir / 'gpu_training').exists() and (self.target_dir / 'gpt_oss').exists(),
            },
            'data_infrastructure_systems': {
                'System_9_data_sources': (self.target_dir / 'tradingagents/dataflows/finmind_adapter.py').exists(),
                'System_10_database': (self.target_dir / 'tradingagents/database').exists(),
                'System_12_monitoring': (self.target_dir / 'monitoring').exists(),
            },
            'security_auth_systems': {
                'System_11_auth_system': (self.target_dir / 'tradingagents/auth').exists(),
                'System_13_data_security': (self.target_dir / 'secure').exists(),
            },
            'devops_deployment_systems': {
                'System_14_cloud_deployment': (self.target_dir / 'deployment').exists(),
                'System_15_dev_testing': (self.target_dir / 'tests').exists() and (self.target_dir / 'scripts').exists(),
            },
            'analytics_reporting_systems': {
                'System_16_business_intelligence': (self.target_dir / 'evaluation_results').exists() and (self.target_dir / 'reports').exists(),
                'System_17_investment_analysis': (self.target_dir / 'work_reports').exists(),
            }
        }

if __name__ == "__main__":
    fixer = MissingSystemsFixer()
    fixer.fix_missing_systems()