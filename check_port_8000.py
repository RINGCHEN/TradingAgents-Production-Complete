#!/usr/bin/env python3
"""
簡單的8000端口檢查工具
檢查哪些進程正在使用8000端口，並提供清理建議
"""

import subprocess
import sys
import json
from datetime import datetime

def run_command(cmd):
    """執行系統命令並返回結果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout, result.stderr, result.returncode
    except UnicodeDecodeError:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp950')
            return result.stdout, result.stderr, result.returncode
        except:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='latin1')
            return result.stdout, result.stderr, result.returncode

def check_port_8000():
    """檢查8000端口使用情況"""
    print("🔍 檢查8000端口使用情況...")
    print("=" * 50)
    
    # 1. 檢查端口占用情況
    stdout, stderr, returncode = run_command('netstat -ano | findstr :8000')
    
    if returncode != 0 or not stdout.strip():
        print("✅ 8000端口當前沒有被任何進程使用")
        return []
    
    print("📋 8000端口當前使用情況:")
    lines = stdout.strip().split('\n')
    pids = []
    
    for line in lines:
        if ':8000' in line:
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                print(f"   {line.strip()}")
                if pid.isdigit() and pid not in pids:
                    pids.append(pid)
    
    print(f"\n📊 發現 {len(pids)} 個進程佔用8000端口: {pids}")
    
    # 2. 檢查進程詳細信息
    print("\n🔍 進程詳細信息:")
    print("-" * 30)
    
    for pid in pids:
        stdout, stderr, returncode = run_command(f'tasklist /FI "PID eq {pid}" /FO CSV')
        
        if returncode == 0 and stdout:
            # 解析CSV輸出
            lines = stdout.strip().split('\n')
            if len(lines) >= 2:
                # 跳過標題行，獲取數據行
                data_line = lines[1].strip('"').split('","')
                if len(data_line) >= 5:
                    image_name = data_line[0]
                    memory_usage = data_line[4]
                    print(f"   PID {pid}: {image_name} (記憶體: {memory_usage})")
                else:
                    print(f"   PID {pid}: 進程信息解析失敗")
            else:
                print(f"   PID {pid}: 進程不存在或已結束")
        else:
            print(f"   PID {pid}: 無法獲取進程信息")
    
    return pids

def generate_port_cleanup_script(pids):
    """生成端口清理腳本"""
    if not pids:
        return
    
    script_content = f"""@echo off
REM 8000端口清理腳本 - 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
REM 注意: 此腳本會強制終止以下進程: {', '.join(pids)}

echo 正在清理8000端口...
echo 發現的進程PIDs: {' '.join(pids)}
echo.

"""
    
    for pid in pids:
        script_content += f"""echo 終止進程 {pid}...
taskkill /PID {pid} /F
if %ERRORLEVEL% == 0 (
    echo 成功終止進程 {pid}
) else (
    echo 無法終止進程 {pid} 或進程已結束
)
echo.

"""
    
    script_content += """echo 清理完成！
echo 重新檢查8000端口...
netstat -ano | findstr :8000
if %ERRORLEVEL% == 0 (
    echo 警告: 仍有進程使用8000端口
) else (
    echo 成功: 8000端口現在可用
)

echo.
echo 按任意鍵繼續...
pause > nul
"""
    
    script_path = "C:\\Users\\Ring\\Documents\\GitHub\\twstock\\TradingAgents-Production-Complete\\cleanup_port_8000.bat"
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"\n📝 端口清理腳本已生成: {script_path}")
        print("⚠️  使用方法: 右鍵點擊該檔案 -> 以系統管理員身分執行")
        return script_path
    except Exception as e:
        print(f"❌ 無法生成清理腳本: {e}")
        return None

def main():
    print("🚀 8000端口檢查工具")
    print("適用於TradingAgents生產服務器啟動")
    print("=" * 50)
    
    # 檢查端口
    pids = check_port_8000()
    
    if pids:
        print(f"\n⚠️  解決方案建議:")
        print("1. 使用生成的清理腳本自動終止進程")
        print("2. 手動終止進程 (不推薦)")
        print("3. 更改TradingAgents服務器端口到8001")
        
        # 生成清理腳本
        script_path = generate_port_cleanup_script(pids)
        
        if script_path:
            print(f"\n✅ 建議執行步驟:")
            print(f"   1. 右鍵點擊: {script_path}")
            print(f"   2. 選擇: 以系統管理員身分執行")
            print(f"   3. 等待清理完成")
            print(f"   4. 重新啟動TradingAgents服務器")
        
        print(f"\n🔄 或者使用替代端口:")
        print(f"   uvicorn tradingagents.simple_app:app --host 0.0.0.0 --port 8001")
    
    else:
        print(f"\n✅ 8000端口可用！")
        print(f"   可以安全啟動TradingAgents生產服務器")
        print(f"   命令: uvicorn tradingagents.simple_app:app --host 0.0.0.0 --port 8000")
    
    print(f"\n📊 檢查完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()