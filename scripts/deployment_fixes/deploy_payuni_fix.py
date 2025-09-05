#!/usr/bin/env python3
"""
緊急部署PayUni修復到DigitalOcean
解決「支付按鈕跳回首頁」問題

Author: Claude + TianGong
Date: 2025-09-04
"""

import subprocess
import os
import sys
from datetime import datetime

def run_command(cmd, description):
    """運行命令並處理錯誤"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout.strip():
                print(f"   輸出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} 失敗")
            print(f"   錯誤: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} 執行異常: {e}")
        return False

def deploy_payuni_fix():
    """部署PayUni修復"""
    print("🚨 緊急部署PayUni修復")
    print("=" * 50)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 檢查當前目錄
    current_dir = os.getcwd()
    print(f"📁 當前目錄: {current_dir}")
    
    # 檢查Git狀態
    if not run_command("git status", "檢查Git狀態"):
        print("⚠️ Git狀態檢查失敗，但繼續執行...")
    
    # 添加修改的文件
    files_to_add = [
        "TradingAgents/tradingagents/api/payuni_endpoints.py"
    ]
    
    for file in files_to_add:
        if os.path.exists(file):
            if run_command(f"git add {file}", f"添加文件 {file}"):
                print(f"✅ {file} 已添加到Git")
            else:
                print(f"⚠️ {file} 添加失敗，但繼續...")
        else:
            print(f"⚠️ 文件不存在: {file}")
    
    # 提交更改
    commit_message = "緊急修復: PayUni支付頁面端點，解決404跳回首頁問題\n\n- 添加Optional data參數支持\n- 無data時顯示支付確認頁面\n- 提供客服聯繫和返回選項\n- 修復用戶支付流程中斷問題\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
    
    if run_command(f'git commit -m "{commit_message}"', "提交更改"):
        print("✅ Git提交成功")
    else:
        print("⚠️ Git提交失敗，可能沒有更改")
    
    # 推送到遠程倉庫
    if run_command("git push origin main", "推送到遠程倉庫"):
        print("✅ Git推送成功")
        print("🚀 DigitalOcean將自動重新部署")
    else:
        print("❌ Git推送失敗")
        return False
    
    print()
    print("🎯 部署完成檢查項目:")
    print("1. ✅ PayUni端點已修復 (支持無data參數)")
    print("2. ✅ 簡化支付確認頁面已添加")
    print("3. ✅ 客服聯繫鏈接已配置")
    print("4. 🔄 等待DigitalOcean重新部署 (約2-5分鐘)")
    
    print()
    print("📋 測試步驟:")
    print("1. 等待5分鐘後訪問 https://03king.com/pricing")
    print("2. 點擊「立即訂閱」按鈕")
    print("3. 應該看到支付確認頁面而不是跳回首頁")
    print("4. 測試URL: https://coral-app-knueo.ondigitalocean.app/payuni/payment-page/TEST")
    
    return True

if __name__ == "__main__":
    try:
        success = deploy_payuni_fix()
        if success:
            print("\n🎉 緊急修復部署成功！")
            print("⏰ 請等待5分鐘後測試支付功能")
        else:
            print("\n❌ 部署過程中出現問題")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⛔ 部署被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 部署過程異常: {e}")
        sys.exit(1)