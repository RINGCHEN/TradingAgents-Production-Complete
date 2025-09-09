#!/usr/bin/env python3
"""
生產環境服務器啟動腳本 - 使用port 8001
避免與其他服務的端口衝突
"""

import sys
import os
from pathlib import Path

# 確保當前目錄在Python路徑中
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def start_production_server():
    """啟動生產服務器在port 8001"""
    
    print("🚀 啟動TradingAgents生產服務器...")
    print(f"📂 當前目錄: {current_dir}")
    
    try:
        # 嘗試直接執行simple_app.py在不同端口
        import subprocess
        
        # 修改simple_app.py中的端口為8001
        simple_app_path = current_dir / "tradingagents" / "simple_app.py"
        
        if not simple_app_path.exists():
            print(f"❌ 找不到文件: {simple_app_path}")
            return
        
        print(f"✅ 找到文件: {simple_app_path}")
        print("🌟 啟動服務器在 http://localhost:8001")
        print("⚡ 如果成功，您將看到 'Application startup complete.'")
        print("\n" + "="*50)
        
        # 直接運行simple_app.py，但先修改端口
        env = os.environ.copy()
        env['PORT'] = '8001'
        
        # 執行腳本
        result = subprocess.run([
            sys.executable,
            str(simple_app_path)
        ], cwd=str(current_dir / "tradingagents"), env=env)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        
        # 備用方案：嘗試導入並直接運行
        try:
            print("\n🔄 嘗試備用方案...")
            from tradingagents.simple_app import app
            import uvicorn
            
            print("✅ 模組導入成功")
            print("🚀 啟動uvicorn在port 8001...")
            
            uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
            
        except Exception as e2:
            print(f"❌ 備用方案也失敗: {e2}")
            return 1

if __name__ == "__main__":
    print("🏭 TradingAgents 生產環境服務器啟動器")
    print("=" * 50)
    
    exit_code = start_production_server()
    
    if exit_code == 0:
        print("\n🎉 服務器成功啟動！")
    else:
        print(f"\n❌ 服務器啟動失敗，退出代碼: {exit_code}")
    
    sys.exit(exit_code or 0)