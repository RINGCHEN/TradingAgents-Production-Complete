#!/usr/bin/env python3
"""
創建乾淨的部署專用版本

此腳本將創建一個只包含生產部署必需文件的乾淨版本，
準備上傳到新的 GitHub 倉庫進行 DigitalOcean 部署。

作者：天工 (TianGong) + Claude Code
日期：2025-09-05
"""

import os
import shutil
from pathlib import Path
import json

class CleanDeploymentCreator:
    def __init__(self):
        self.source_dir = Path(__file__).parent.parent
        self.deployment_dir = self.source_dir.parent / "TradingAgents-Production"
        
        # 生產部署必需的文件和目錄
        self.essential_items = {
            # 核心應用文件
            'files': [
                'requirements.txt',
                'Dockerfile',
                '.env.example',  # 環境變量模板
                'README.md',     # 我們需要創建
                '.gitignore'     # 我們需要創建乾淨版本
            ],
            
            # 核心目錄
            'directories': [
                'tradingagents',      # FastAPI 核心應用
                'frontend/dist',      # 前端構建結果 (如果存在)
                'configs',            # 配置文件
                'utils'               # 路徑兼容性模組
            ],
            
            # 可選目錄 (如果存在且需要)
            'optional_directories': [
                'training',           # AI訓練配置 (生產可能需要)
                'models',            # 訓練好的模型
            ]
        }

    def create_clean_deployment(self):
        """創建乾淨的部署版本"""
        print("[START] 開始創建乾淨的 TradingAgents 部署版本...")
        
        # 創建部署目錄
        if self.deployment_dir.exists():
            print(f"[WARN] 部署目錄已存在，將覆蓋: {self.deployment_dir}")
            shutil.rmtree(self.deployment_dir)
        
        self.deployment_dir.mkdir()
        print(f"[DIR] 創建部署目錄: {self.deployment_dir}")
        
        # 複製核心文件
        self._copy_essential_files()
        
        # 複製核心目錄
        self._copy_essential_directories()
        
        # 創建部署專用文件
        self._create_deployment_files()
        
        # 生成統計報告
        self._generate_deployment_report()

    def _copy_essential_files(self):
        """複製必需的文件"""
        print("\n[FILES] 複製核心文件...")
        
        for file_name in self.essential_items['files']:
            source_file = self.source_dir / file_name
            dest_file = self.deployment_dir / file_name
            
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                print(f"  [OK] {file_name}")
            else:
                print(f"  [WARN] {file_name} 不存在，將創建模板")

    def _copy_essential_directories(self):
        """複製必需的目錄"""
        print("\n[DIRS] 複製核心目錄...")
        
        # 必需目錄
        for dir_name in self.essential_items['directories']:
            source_dir = self.source_dir / dir_name
            dest_dir = self.deployment_dir / dir_name
            
            if source_dir.exists():
                # 對於某些目錄，我們需要選擇性複製
                if dir_name == 'tradingagents':
                    self._copy_tradingagents_selectively(source_dir, dest_dir)
                else:
                    shutil.copytree(source_dir, dest_dir, 
                                  ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.log', 'test_*'))
                print(f"  [OK] {dir_name}/")
            else:
                print(f"  [MISSING] {dir_name}/ 不存在")
        
        # 可選目錄
        for dir_name in self.essential_items['optional_directories']:
            source_dir = self.source_dir / dir_name
            dest_dir = self.deployment_dir / dir_name
            
            if source_dir.exists():
                # 只複製配置文件，不複製大型模型文件
                if dir_name == 'training':
                    self._copy_training_configs_only(source_dir, dest_dir)
                elif dir_name == 'models':
                    self._copy_model_configs_only(source_dir, dest_dir)
                print(f"  [OK] {dir_name}/ (配置)")

    def _copy_tradingagents_selectively(self, source_dir: Path, dest_dir: Path):
        """選擇性複製 tradingagents 目錄"""
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # 需要的子目錄
        essential_subdirs = [
            'api', 'admin', 'auth', 'utils', 'agents',
            'graph', 'dataflows', 'services'
        ]
        
        # 複製核心文件
        for item in source_dir.iterdir():
            if item.is_file() and item.suffix == '.py':
                shutil.copy2(item, dest_dir / item.name)
        
        # 複製必需的子目錄
        for subdir in essential_subdirs:
            source_subdir = source_dir / subdir
            if source_subdir.exists():
                dest_subdir = dest_dir / subdir
                shutil.copytree(source_subdir, dest_subdir,
                              ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'test_*', '*_test.py'))

    def _copy_training_configs_only(self, source_dir: Path, dest_dir: Path):
        """只複製訓練配置文件"""
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for analyst_dir in source_dir.iterdir():
            if analyst_dir.is_dir():
                dest_analyst_dir = dest_dir / analyst_dir.name
                dest_analyst_dir.mkdir(exist_ok=True)
                
                # 只複製配置文件
                for file in analyst_dir.iterdir():
                    if file.suffix in ['.yaml', '.yml', '.json'] or file.name in ['config.py', 'inference.py']:
                        shutil.copy2(file, dest_analyst_dir / file.name)

    def _copy_model_configs_only(self, source_dir: Path, dest_dir: Path):
        """只複製模型配置，不複製大型模型文件"""
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for item in source_dir.iterdir():
            if item.is_file() and item.suffix in ['.json', '.yaml', '.yml', '.txt']:
                shutil.copy2(item, dest_dir / item.name)
            elif item.is_dir():
                dest_subdir = dest_dir / item.name
                dest_subdir.mkdir(exist_ok=True)
                # 只複製小型配置文件
                for file in item.iterdir():
                    if file.is_file() and file.stat().st_size < 10 * 1024 * 1024:  # 小於10MB
                        shutil.copy2(file, dest_subdir / file.name)

    def _create_deployment_files(self):
        """創建部署專用文件"""
        print("\n[CREATE] 創建部署專用文件...")
        
        # 創建生產專用 .gitignore
        gitignore_content = """# TradingAgents Production .gitignore

# Environment variables
.env
.env.local
.env.production

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

# Temporary files
*.tmp
*.temp
temp/

# Node modules (if any)
node_modules/

# Database
*.db
*.sqlite

# Model files (too large for git)
*.bin
*.safetensors
models/*.bin
models/*.safetensors

# Training artifacts
mlruns/
training_logs/

# Build artifacts
dist/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Local development
local_*
dev_*
test_*
*_test.py
"""
        
        with open(self.deployment_dir / '.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("  [OK] .gitignore")
        
        # 創建 README.md
        readme_content = """# TradingAgents Production

**不老傳說 AI 投資分析平台** - 生產部署版本

## 快速部署

### 環境要求
- Python 3.11+
- Docker (推薦)

### Docker 部署
```bash
# 構建鏡像
docker build -t tradingagents:latest .

# 運行容器
docker run -p 8000:8000 tradingagents:latest
```

### 本地部署
```bash
# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
cp .env.example .env
# 編輯 .env 文件設置實際值

# 啟動應用
uvicorn tradingagents.app:app --host 0.0.0.0 --port 8000
```

### DigitalOcean 部署
1. 推送代碼到 GitHub
2. 連接 DigitalOcean App Platform
3. 自動部署

## API 文檔
部署後訪問: `http://your-domain/docs`

## 系統架構
- **前端**: React + TypeScript
- **後端**: FastAPI + Python  
- **AI**: 多代理人投資分析師系統
- **支付**: PayUni 整合
- **部署**: DigitalOcean App Platform

## 聯絡
- 系統開發：天工 (TianGong)
- AI架構：Claude Code
"""
        
        with open(self.deployment_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("  [OK] README.md")
        
        # 創建環境變量模板
        env_example_content = """# TradingAgents Production Environment Variables

# Basic Configuration
PORT=8000
ENVIRONMENT=production
PYTHONPATH=/app

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tradingagents

# PayUni Payment System
PAYUNI_MERCHANT_ID=U03823060
PAYUNI_HASH_KEY=your_hash_key
PAYUNI_HASH_IV=your_hash_iv
PAYUNI_BASE_URL=https://api.payuni.com.tw
PAYUNI_SANDBOX_MODE=false

# Security
SECRET_KEY=your-secret-key-for-production-2024
JWT_SECRET=your-jwt-secret-key-for-production-2024

# AI Training (Optional)
TRADING_AGENTS_DATA_DIR=/app/data
TRADING_AGENTS_MODELS_DIR=/app/models
"""
        
        with open(self.deployment_dir / '.env.example', 'w', encoding='utf-8') as f:
            f.write(env_example_content)
        print("  [OK] .env.example")

    def _generate_deployment_report(self):
        """生成部署報告"""
        print("\n[REPORT] 生成部署統計...")
        
        total_files = sum(1 for _ in self.deployment_dir.rglob('*') if _.is_file())
        total_size = sum(f.stat().st_size for f in self.deployment_dir.rglob('*') if f.is_file())
        
        report = {
            'deployment_directory': str(self.deployment_dir),
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'core_components': {
                'tradingagents_api': (self.deployment_dir / 'tradingagents').exists(),
                'configs': (self.deployment_dir / 'configs').exists(),
                'utils': (self.deployment_dir / 'utils').exists(),
                'dockerfile': (self.deployment_dir / 'Dockerfile').exists(),
                'requirements': (self.deployment_dir / 'requirements.txt').exists(),
            }
        }
        
        with open(self.deployment_dir / 'deployment_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SUCCESS] 部署版本創建完成！")
        print(f"[DIR] 位置: {self.deployment_dir}")
        print(f"[FILES] 文件數: {total_files}")
        print(f"[SIZE] 大小: {report['total_size_mb']} MB")
        print(f"\n下一步:")
        print(f"1. 檢查 {self.deployment_dir} 內容")
        print(f"2. 創建新的 GitHub 倉庫")
        print(f"3. 上傳到 GitHub")
        print(f"4. 配置 DigitalOcean 部署")

if __name__ == "__main__":
    creator = CleanDeploymentCreator()
    creator.create_clean_deployment()