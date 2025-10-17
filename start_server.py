#!/usr/bin/env python3
"""
生產環境服務器啟動腳本 - 繞過模組導入問題
用於啟動TradingAgents生產服務器
"""

import sys
import os
from pathlib import Path

# 確保當前目錄在Python路徑中
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 嘗試直接導入和運行
try:
    # 方法1：嘗試導入simple_app
    print("嘗試導入 simple_app...")
    from tradingagents.simple_app import app as simple_app
    print("simple_app 導入成功")
    
    import uvicorn
    print("啟動simple_app服務器在 http://localhost:8000")
    uvicorn.run(simple_app, host="0.0.0.0", port=8000, reload=True)
    
except ImportError as e:
    print(f"simple_app 導入失敗: {e}")
    
    try:
        # 方法2：嘗試導入主app
        print("嘗試導入主 app...")
        from tradingagents.app import app as main_app
        print("main app 導入成功")
        
        import uvicorn
        print("啟動main app服務器在 http://localhost:8000")
        uvicorn.run(main_app, host="0.0.0.0", port=8000, reload=True)
        
    except ImportError as e2:
        print(f"main app 也導入失敗: {e2}")
        
        try:
            # 方法3：直接執行simple_app.py文件
            print("嘗試直接執行simple_app.py...")
            import subprocess
            result = subprocess.run([
                sys.executable, 
                str(current_dir / "tradingagents" / "simple_app.py")
            ], cwd=str(current_dir))
            
        except Exception as e3:
            print(f"直接執行也失敗: {e3}")
            print("\n診斷信息:")
            print(f"當前工作目錄: {os.getcwd()}")
            print(f"腳本目錄: {current_dir}")
            print(f"Python路徑: {sys.path[:3]}...")  # 只顯示前3個
            
            # 檢查文件是否存在
            simple_app_path = current_dir / "tradingagents" / "simple_app.py"
            main_app_path = current_dir / "tradingagents" / "app.py"
            
            print(f"\n文件檢查:")
            print(f"simple_app.py 存在: {simple_app_path.exists()}")
            print(f"app.py 存在: {main_app_path.exists()}")
            
            if simple_app_path.exists():
                print(f"simple_app.py 路徑: {simple_app_path}")
            if main_app_path.exists():
                print(f"app.py 路徑: {main_app_path}")
                
            print("\n建議:")
            print("1. 檢查Python版本兼容性")
            print("2. 檢查依賴是否完全安裝")
            print("3. 嘗試在虛擬環境中運行")
            print("4. 檢查文件權限和編碼")

if __name__ == "__main__":
    pass