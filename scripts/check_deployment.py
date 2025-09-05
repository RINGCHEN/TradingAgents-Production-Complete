#!/usr/bin/env python3
"""
DigitalOcean 部署準備檢查工具 - 簡化版
"""

import os
from pathlib import Path

def main():
    print("TradingAgents DigitalOcean 部署準備檢查")
    print("=" * 50)
    
    # 檢查關鍵文件
    files_to_check = [
        ".do/app.yaml",
        "TradingAgents/Dockerfile", 
        "TradingAgents/requirements.txt",
        "TradingAgents/tradingagents/app.py",
        "TradingAgents/tradingagents/api/payuni_endpoints.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"OK: {file_path}")
        else:
            print(f"MISSING: {file_path}")
            all_good = False
    
    # 檢查配置內容
    try:
        with open(".do/app.yaml", 'r') as f:
            content = f.read()
            if "RINGCHEN/TradingAgents-Deploy" in content:
                print("OK: GitHub repo configured")
            else:
                print("ERROR: GitHub repo not configured")
                all_good = False
    except:
        print("ERROR: Cannot read .do/app.yaml")
        all_good = False
    
    print("=" * 50)
    if all_good:
        print("SUCCESS: All checks passed!")
        print("\nNext steps:")
        print("1. Go to DigitalOcean App Platform")
        print("2. Create new app from GitHub")
        print("3. Select: RINGCHEN/TradingAgents-Deploy")
        print("4. Set environment variables")
        print("5. Deploy!")
    else:
        print("ERROR: Please fix missing files")

if __name__ == "__main__":
    main()