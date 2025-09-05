#!/usr/bin/env python3
"""
創建完整的乾淨部署專用版本 (修正版)

此腳本將創建一個包含17個核心系統的完整乾淨版本，
修正先前版本中缺失的關鍵系統組件。

作者：天工 (TianGong) + Claude Code
日期：2025-09-05
版本：v2.0 (修正版)
"""

import os
import shutil
from pathlib import Path
import json

class CompleteCleanDeploymentCreator:
    def __init__(self):
        self.source_dir = Path(__file__).parent.parent
        self.deployment_dir = self.source_dir.parent / "TradingAgents-Production-Complete"
        
        # 17個系統的完整文件和目錄映射
        self.system_components = {
            # 體系一：前端系統群組 (3個系統)
            'frontend_systems': {
                'directories': [
                    'frontend',  # System 1,2,3: React前端+管理後台+會員系統
                ],
                'description': '前端系統群組 (React + TypeScript + AdminApp_Ultimate)'
            },
            
            # 體系二：後端API系統群組 (2個系統)
            'backend_api_systems': {
                'directories': [
                    'tradingagents',  # System 4: FastAPI核心系統
                ],
                'files': [
                    'requirements.txt',
                    'Dockerfile',
                ],
                'description': '後端API系統群組 (FastAPI + PayUni)'
            },
            
            # 體系三：AI智能系統群組 (3個系統)
            'ai_intelligence_systems': {
                'directories': [
                    'models',         # System 6: AI分析師系統
                    'training',       # System 7: 本地AI訓練系統
                    'gpu_training',   # System 8: AI模型服務系統 (GPU加速)
                    'gpt_oss',       # AI模型服務
                ],
                'description': 'AI智能系統群組 (多代理分析師 + 訓練 + 服務)'
            },
            
            # 體系四：數據基礎設施群組 (3個系統)
            'data_infrastructure_systems': {
                'directories': [
                    'data',              # System 9: 數據源系統
                    'ai_training_data',  # System 10: 資料庫系統 (訓練數據)
                    'monitoring',        # System 12: 監控運營系統
                ],
                'description': '數據基礎設施群組 (FinMind + PostgreSQL + 監控)'
            },
            
            # 體系五：安全認證系統群組 (2個系統)
            'security_auth_systems': {
                'directories': [
                    'secure',     # System 11,13: 認證授權+數據安全系統
                ],
                'description': '安全認證系統群組 (OAuth + JWT + 安全防護)'
            },
            
            # 體系六：部署DevOps系統群組 (2個系統)
            'devops_deployment_systems': {
                'directories': [
                    'deployment', # System 14: 雲端部署系統
                    'tests',      # System 15: 開發測試系統
                    'scripts',    # 開發工具腳本
                ],
                'description': '部署DevOps系統群組 (DigitalOcean + 開發測試)'
            },
            
            # 體系七：分析報告系統群組 (2個系統)
            'analytics_reporting_systems': {
                'directories': [
                    'evaluation_results', # System 16: 商業智能系統
                    'reports',            # System 17: 投資分析引擎
                    'work_reports',       # 工作報告
                ],
                'description': '分析報告系統群組 (商業智能 + 投資分析引擎)'
            },
            
            # 核心配置和工具
            'core_config_systems': {
                'directories': [
                    'configs',
                    'utils',
                    'logs',
                ],
                'files': [
                    '.env.payuni',
                    'digitalocean-env-template.txt',
                    'business_metrics.db',
                    'ai_training_data.dvc',
                ],
                'description': '核心配置和工具系統'
            }
        }

    def create_complete_clean_deployment(self):
        """創建完整的乾淨部署版本"""
        print("[START] 開始創建完整的 TradingAgents 部署版本 (17系統完整版)...")
        
        # 創建部署目錄
        if self.deployment_dir.exists():
            print(f"[WARN] 部署目錄已存在，將覆蓋: {self.deployment_dir}")
            shutil.rmtree(self.deployment_dir)
        
        self.deployment_dir.mkdir()
        print(f"[DIR] 創建部署目錄: {self.deployment_dir}")
        
        # 按系統複製組件
        self._copy_system_components()
        
        # 創建部署專用文件
        self._create_deployment_files()
        
        # 生成完整系統報告
        self._generate_complete_system_report()

    def _copy_system_components(self):
        """按7大體系17個系統複製組件"""
        print("\n[SYSTEMS] 按17個核心系統複製組件...")
        
        total_systems = 0
        successful_systems = 0
        
        for system_group, config in self.system_components.items():
            print(f"\n[GROUP] {config['description']}")
            
            # 複製目錄
            if 'directories' in config:
                for dir_name in config['directories']:
                    source_dir = self.source_dir / dir_name
                    dest_dir = self.deployment_dir / dir_name
                    
                    total_systems += 1
                    if source_dir.exists():
                        try:
                            # 選擇性複製，排除不必要文件
                            shutil.copytree(
                                source_dir, 
                                dest_dir,
                                ignore=shutil.ignore_patterns(
                                    '__pycache__', '*.pyc', '*.log',
                                    'node_modules', '.git', '.pytest_cache',
                                    '*.tmp', 'mlruns', 'logs', '*.db',
                                    'test_*.py', '*_test.py',
                                    '*.bin', '*.safetensors'  # 大型模型文件
                                )
                            )
                            print(f"  [OK] {dir_name}/ (完整)")
                            successful_systems += 1
                        except Exception as e:
                            print(f"  [ERROR] {dir_name}/ 複製失敗: {str(e)}")
                    else:
                        print(f"  [MISSING] {dir_name}/ 不存在")
            
            # 複製文件
            if 'files' in config:
                for file_name in config['files']:
                    source_file = self.source_dir / file_name
                    dest_file = self.deployment_dir / file_name
                    
                    total_systems += 1
                    if source_file.exists():
                        try:
                            shutil.copy2(source_file, dest_file)
                            print(f"  [OK] {file_name}")
                            successful_systems += 1
                        except Exception as e:
                            print(f"  [ERROR] {file_name} 複製失敗: {str(e)}")
                    else:
                        print(f"  [MISSING] {file_name} 不存在")
        
        print(f"\n[SUMMARY] 系統組件複製完成: {successful_systems}/{total_systems}")

    def _create_deployment_files(self):
        """創建部署專用文件"""
        print("\n[CREATE] 創建部署專用文件...")
        
        # 創建完整 .gitignore
        gitignore_content = """# TradingAgents Production Complete .gitignore

# Environment variables
.env
.env.local
.env.production
.env.payuni

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
tradingagents_*.log

# Temporary files
*.tmp
*.temp
temp/

# Node modules
node_modules/
package-lock.json

# Database
*.db
*.sqlite
business_metrics.db

# Model files (too large for git)
*.bin
*.safetensors
models/*.bin
models/*.safetensors
gpu_training/models/
models/automated_training/

# Training artifacts
mlruns/
training_logs/
evaluation_results/*/logs/
work_reports/

# Build artifacts
dist/
build/
frontend/build/
frontend/dist/

# Testing
.pytest_cache/
.coverage
htmlcov/
test_*.py
*_test.py
test_*/

# AI Cache
ai_training_data/
D:/TradingAgents_AI_Cache/

# Local development
local_*
dev_*
debug_*

# Monitoring data
monitoring/data/
monitoring/logs/

# Reports
reports/
reports_root/

# Security
secure/
security_backup/
ssl/

# Deployment specific
deployment/logs/
scripts/logs/
"""
        
        with open(self.deployment_dir / '.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("  [OK] .gitignore (完整版)")
        
        # 創建完整 README.md
        readme_content = """# TradingAgents Production Complete

**不老傳說 AI 投資分析平台** - 完整生產部署版本 (17個核心系統)

## 🏛️ 系統架構 (7大體系17個核心系統)

### 📱 體系一：前端系統群組 (3個系統)
- **System 1**: 主要用戶前端系統 (`frontend/`)
- **System 2**: 個人會員專屬系統 (會員AI功能)
- **System 3**: 前端後台管理系統 (`AdminApp_Ultimate.tsx`)

### ⚙️ 體系二：後端API系統群組 (2個系統) 
- **System 4**: 後端 FastAPI 核心系統 (`tradingagents/`)
- **System 5**: PayUni 支付系統 (商店代號 U03823060)

### 🤖 體系三：AI智能系統群組 (3個系統)
- **System 6**: 多代理人AI分析師系統 (`models/`)
- **System 7**: 本地AI訓練系統 (`training/`)
- **System 8**: AI模型服務系統 (`gpu_training/`, `gpt_oss/`)

### 💾 體系四：數據基礎設施群組 (3個系統)
- **System 9**: 數據源系統 (`data/`)
- **System 10**: 資料庫系統 (PostgreSQL + 訓練數據)
- **System 12**: 監控運營系統 (`monitoring/`)

### 🔒 體系五：安全認證系統群組 (2個系統)
- **System 11**: 認證授權系統 (Google OAuth + JWT)
- **System 13**: 數據安全系統 (`secure/`)

### 🚀 體系六：部署DevOps系統群組 (2個系統)
- **System 14**: 雲端部署系統 (`deployment/`)
- **System 15**: 開發測試系統 (`tests/`, `scripts/`)

### 📊 體系七：分析報告系統群組 (2個系統)
- **System 16**: 商業智能系統 (`evaluation_results/`)
- **System 17**: 投資分析引擎 (`reports/`, `work_reports/`)

## 🚀 快速部署

### 環境要求
- Python 3.11+
- Node.js 16+
- Docker (推薦)
- CUDA (GPU訓練可選)

### Docker 部署
```bash
# 構建鏡像
docker build -t tradingagents:complete .

# 運行容器
docker run -p 8000:8000 tradingagents:complete
```

### 本地完整部署
```bash
# 後端API
pip install -r requirements.txt
uvicorn tradingagents.app:app --host 0.0.0.0 --port 8000

# 前端系統
cd frontend && npm install && npm run build && npm run dev

# 監控系統
cd monitoring && docker-compose up -d

# AI訓練 (可選)
cd gpu_training && python simple_lora_training.py
```

### DigitalOcean 部署
1. 推送代碼到 GitHub 私有倉庫
2. 連接 DigitalOcean App Platform
3. 配置環境變數 (詳見 `.env.example`)
4. 自動部署

## 🎯 系統特色
- ✅ **17個核心系統完整** - 7大體系全覆蓋
- ✅ **前後端完全統一** - React + FastAPI + AI
- ✅ **企業級監控** - Grafana + Prometheus
- ✅ **GPU加速訓練** - LoRA微調 + 本地訓練
- ✅ **完整測試體系** - pytest + Jest + 集成測試
- ✅ **商業化就緒** - PayUni支付 + 會員系統

## 📞 聯絡
- 系統開發：天工 (TianGong)
- AI架構：Claude Code
- 平台：不老傳說 AI 投資分析平台
"""
        
        with open(self.deployment_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("  [OK] README.md (17系統完整版)")
        
        # 創建完整環境變量模板
        env_example_content = """# TradingAgents Production Complete Environment Variables

# Basic Configuration
PORT=8000
ENVIRONMENT=production
PYTHONPATH=/app

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tradingagents

# PayUni Payment System (商店代號 U03823060)
PAYUNI_MERCHANT_ID=U03823060
PAYUNI_HASH_KEY=your_hash_key
PAYUNI_HASH_IV=your_hash_iv
PAYUNI_BASE_URL=https://api.payuni.com.tw
PAYUNI_SANDBOX_MODE=false

# Security
SECRET_KEY=your-secret-key-for-production-2024
JWT_SECRET=your-jwt-secret-key-for-production-2024

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AI Training (Optional)
TRADING_AGENTS_DATA_DIR=/app/ai_training_data
TRADING_AGENTS_MODELS_DIR=/app/models
CUDA_VISIBLE_DEVICES=0

# Monitoring (Optional)
GRAFANA_PASSWORD=admin123
PROMETHEUS_RETENTION=15d

# FinMind API
FINMIND_TOKEN=your-finmind-token

# Frontend Configuration  
VITE_API_URL=https://your-api-domain.com
VITE_PAYUNI_MERCHANT_ID=U03823060
"""
        
        with open(self.deployment_dir / '.env.example', 'w', encoding='utf-8') as f:
            f.write(env_example_content)
        print("  [OK] .env.example (完整配置)")

    def _generate_complete_system_report(self):
        """生成完整的系統報告"""
        print("\n[REPORT] 生成17系統完整報告...")
        
        total_files = sum(1 for _ in self.deployment_dir.rglob('*') if _.is_file())
        total_size = sum(f.stat().st_size for f in self.deployment_dir.rglob('*') if f.is_file())
        
        # 檢查17個核心系統
        system_verification = {
            'frontend_systems': {
                'System_1_main_frontend': (self.deployment_dir / 'frontend').exists(),
                'System_2_member_system': (self.deployment_dir / 'frontend/src/components').exists() if (self.deployment_dir / 'frontend/src').exists() else False,
                'System_3_admin_backend': (self.deployment_dir / 'frontend/src/admin').exists() if (self.deployment_dir / 'frontend/src').exists() else False,
            },
            'backend_api_systems': {
                'System_4_fastapi_core': (self.deployment_dir / 'tradingagents/app.py').exists(),
                'System_5_payuni_payment': (self.deployment_dir / 'tradingagents/api/payuni_endpoints.py').exists(),
            },
            'ai_intelligence_systems': {
                'System_6_ai_analysts': (self.deployment_dir / 'models').exists(),
                'System_7_ai_training': (self.deployment_dir / 'training').exists(),
                'System_8_model_service': (self.deployment_dir / 'gpu_training').exists(),
            },
            'data_infrastructure_systems': {
                'System_9_data_sources': (self.deployment_dir / 'data').exists(),
                'System_10_database': (self.deployment_dir / 'ai_training_data').exists(),
                'System_12_monitoring': (self.deployment_dir / 'monitoring').exists(),
            },
            'security_auth_systems': {
                'System_11_auth_system': (self.deployment_dir / 'tradingagents/auth').exists(),
                'System_13_data_security': (self.deployment_dir / 'secure').exists(),
            },
            'devops_deployment_systems': {
                'System_14_cloud_deployment': (self.deployment_dir / 'deployment').exists(),
                'System_15_dev_testing': (self.deployment_dir / 'tests').exists(),
            },
            'analytics_reporting_systems': {
                'System_16_business_intelligence': (self.deployment_dir / 'evaluation_results').exists(),
                'System_17_investment_analysis': (self.deployment_dir / 'work_reports').exists(),
            }
        }
        
        report = {
            'deployment_info': {
                'deployment_directory': str(self.deployment_dir),
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'deployment_type': 'Complete 17-System Enterprise Deployment',
                'version': '2.0 (Complete)',
            },
            'system_verification': system_verification,
            'system_summary': {
                'total_systems': 17,
                'verified_systems': sum(
                    sum(systems.values()) for systems in system_verification.values()
                ),
                'system_groups': len(system_verification),
                'completeness_rate': 0  # 將在下面計算
            }
        }
        
        # 計算完整性率
        total_checks = sum(len(systems) for systems in system_verification.values())
        passed_checks = sum(sum(systems.values()) for systems in system_verification.values())
        report['system_summary']['completeness_rate'] = round((passed_checks / total_checks) * 100, 1)
        
        with open(self.deployment_dir / 'complete_system_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SUCCESS] 完整部署版本創建完成！")
        print(f"[DIR] 位置: {self.deployment_dir}")
        print(f"[FILES] 文件數: {total_files}")
        print(f"[SIZE] 大小: {report['deployment_info']['total_size_mb']} MB")
        print(f"[SYSTEMS] 系統驗證: {passed_checks}/{total_checks} ({report['system_summary']['completeness_rate']}%)")
        print(f"\n下一步:")
        print(f"1. 檢查 {self.deployment_dir} 內容")
        print(f"2. 創建新的 GitHub 私有倉庫")
        print(f"3. 上傳完整版到 GitHub")
        print(f"4. 配置 DigitalOcean 完整部署")
        print(f"5. 測試17個核心系統功能")

if __name__ == "__main__":
    creator = CompleteCleanDeploymentCreator()
    creator.create_complete_clean_deployment()