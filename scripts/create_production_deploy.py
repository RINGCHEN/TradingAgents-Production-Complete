#!/usr/bin/env python3
"""
TradingAgents 生產部署文件準備器
只包含部署必需的核心文件，移除所有測試和開發文件
"""

import os
import shutil
import glob
from pathlib import Path

def create_production_deployment():
    """創建生產部署版本"""
    
    # 源目錄和目標目錄
    source_dir = Path("TradingAgents")
    deploy_dir = Path("/tmp/tradingagents-production-ready")
    
    print("==> 開始創建生產部署版本...")
    
    # 清理並創建部署目錄
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir(parents=True)
    
    # 必需的核心文件和目錄
    essential_files = [
        "Dockerfile",
        "requirements.txt", 
        "README.md",
        "README_v2.0.md"
    ]
    
    essential_dirs = [
        "tradingagents",  # 主應用
        "frontend",       # React前端
        "configs",        # 系統配置 (如果存在)
    ]
    
    # 複製核心文件
    print("==> 複製核心文件...")
    for file_name in essential_files:
        src_file = source_dir / file_name
        if src_file.exists():
            shutil.copy2(src_file, deploy_dir / file_name)
            print(f"  [OK] {file_name}")
        else:
            print(f"  [SKIP] 未找到 {file_name}")
    
    # 複製核心目錄
    print("==> 複製核心目錄...")
    for dir_name in essential_dirs:
        src_dir = source_dir / dir_name
        dst_dir = deploy_dir / dir_name
        
        if src_dir.exists():
            # 複製目錄，但排除不需要的文件
            shutil.copytree(
                src_dir, 
                dst_dir, 
                ignore=ignore_files
            )
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ 未找到 {dir_name}/")
    
    # 創建 .gitignore
    create_production_gitignore(deploy_dir)
    
    # 顯示結果
    show_deployment_summary(deploy_dir)
    
    return deploy_dir

def ignore_files(dir, files):
    """定義要忽略的文件和目錄"""
    ignore_patterns = [
        # 測試和開發文件
        "*test*",
        "*debug*", 
        "*temp*",
        "*.log",
        "*.db",
        "*.sqlite",
        "*.tmp",
        "nul",
        
        # Node.js
        "node_modules",
        "*.log",
        
        # Python
        "__pycache__",
        "*.pyc",
        "*.pyo",
        
        # 開發工具
        ".vscode",
        ".idea",
        
        # 大型數據文件
        "art_data*",
        "models",
        "cache",
        "mlruns*",
        
        # 日誌和報告
        "logs",
        "*_report*",
        "*_REPORT*",
        
        # 臨時和備份
        "*.bak",
        "*.backup",
        "*~",
    ]
    
    ignored = []
    for file in files:
        for pattern in ignore_patterns:
            if pattern.startswith("*") and pattern.endswith("*"):
                # 包含匹配
                if pattern[1:-1].lower() in file.lower():
                    ignored.append(file)
                    break
            elif pattern.startswith("*"):
                # 結尾匹配
                if file.lower().endswith(pattern[1:].lower()):
                    ignored.append(file)
                    break
            elif pattern.endswith("*"):
                # 開頭匹配
                if file.lower().startswith(pattern[:-1].lower()):
                    ignored.append(file)
                    break
            else:
                # 完全匹配
                if file.lower() == pattern.lower():
                    ignored.append(file)
                    break
    
    return ignored

def create_production_gitignore(deploy_dir):
    """創建生產環境專用的 .gitignore"""
    gitignore_content = """# TradingAgents 生產部署 .gitignore

# 開發環境
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*

# 日誌
*.log
logs/

# 資料庫
*.db
*.sqlite*

# IDE
.vscode/
.idea/

# 系統文件
.DS_Store
Thumbs.db
nul

# 環境變數
.env
.env.*

# 臨時文件
*.tmp
*.temp
*.pid

# 測試
coverage/
.pytest_cache/
"""
    
    gitignore_path = deploy_dir / ".gitignore"
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("  ✅ .gitignore")

def show_deployment_summary(deploy_dir):
    """顯示部署摘要"""
    print("\n" + "="*50)
    print("🎯 生產部署版本創建完成！")
    print("="*50)
    
    # 計算目錄大小
    total_size = sum(f.stat().st_size for f in deploy_dir.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    # 計算文件數量
    file_count = len([f for f in deploy_dir.rglob('*') if f.is_file()])
    
    print(f"📍 部署目錄: {deploy_dir}")
    print(f"📊 總大小: {size_mb:.1f} MB")
    print(f"📝 文件數: {file_count}")
    print(f"🎯 狀態: 🟢 部署就緒")
    
    print("\n📋 核心目錄結構:")
    for item in sorted(deploy_dir.iterdir()):
        if item.is_dir():
            sub_files = len([f for f in item.rglob('*') if f.is_file()])
            print(f"  📁 {item.name}/ ({sub_files} files)")
        else:
            file_size = item.stat().st_size
            if file_size > 1024*1024:
                size_str = f"{file_size/(1024*1024):.1f}MB"
            elif file_size > 1024:
                size_str = f"{file_size/1024:.1f}KB"
            else:
                size_str = f"{file_size}B"
            print(f"  📄 {item.name} ({size_str})")
    
    print("\n🚀 下一步:")
    print(f"1. cd {deploy_dir}")
    print("2. git init")
    print("3. git add .")
    print("4. git commit -m 'Initial production deployment'")
    print("5. git remote add origin https://github.com/RINGCHEN/TradingAgents-Production.git")
    print("6. git push -u origin main")

if __name__ == "__main__":
    create_production_deployment()