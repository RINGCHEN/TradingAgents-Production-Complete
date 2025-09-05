#!/usr/bin/env python3
"""
跨平台測試運行器
統一的測試腳本入口，自動檢測平台並運行相應的測試
"""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path

def get_script_dir():
    """獲取腳本目錄"""
    return Path(__file__).parent

def run_quick_verify(host="localhost", port=8080):
    """運行快速驗證"""
    script_path = get_script_dir() / "quick_verify.py"
    cmd = [sys.executable, str(script_path), "--host", host, "--port", str(port)]
    return subprocess.run(cmd)

def run_health_check(save_file=None, json_output=False):
    """運行健康檢查"""
    script_path = get_script_dir() / "gpt_oss_health_check.py"
    cmd = [sys.executable, str(script_path)]
    
    if save_file:
        cmd.extend(["--save", save_file])
    if json_output:
        cmd.append("--json")
    
    return subprocess.run(cmd)

def run_performance_benchmark():
    """運行性能基準測試"""
    system = platform.system().lower()
    script_dir = get_script_dir()
    
    if system == "windows":
        # Windows: 使用PowerShell腳本
        script_path = script_dir / "gpt_oss_performance_benchmark.ps1"
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    else:
        # Linux/Mac: 使用Bash腳本
        script_path = script_dir / "gpt_oss_performance_benchmark.sh"
        cmd = ["bash", str(script_path)]
    
    print(f"運行平台: {system}")
    print(f"使用腳本: {script_path}")
    
    return subprocess.run(cmd)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="GPT-OSS 跨平台測試運行器")
    parser.add_argument("test_type", choices=["quick", "health", "performance", "all"], 
                       help="測試類型")
    parser.add_argument("--host", default="localhost", help="服務主機")
    parser.add_argument("--port", type=int, default=8080, help="服務端口")
    parser.add_argument("--save", help="保存健康檢查結果到文件")
    parser.add_argument("--json", action="store_true", help="JSON格式輸出")
    
    args = parser.parse_args()
    
    print(f"=== GPT-OSS 跨平台測試運行器 ===")
    print(f"平台: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print("")
    
    if args.test_type == "quick" or args.test_type == "all":
        print("🚀 運行快速驗證...")
        result = run_quick_verify(args.host, args.port)
        if result.returncode != 0:
            print("❌ 快速驗證失敗")
            if args.test_type != "all":
                sys.exit(result.returncode)
        else:
            print("✅ 快速驗證成功")
        print("")
    
    if args.test_type == "health" or args.test_type == "all":
        print("🏥 運行健康檢查...")
        result = run_health_check(args.save, args.json)
        if result.returncode != 0:
            print("❌ 健康檢查失敗")
            if args.test_type != "all":
                sys.exit(result.returncode)
        else:
            print("✅ 健康檢查成功")
        print("")
    
    if args.test_type == "performance" or args.test_type == "all":
        print("📊 運行性能基準測試...")
        result = run_performance_benchmark()
        if result.returncode != 0:
            print("❌ 性能測試失敗")
            if args.test_type != "all":
                sys.exit(result.returncode)
        else:
            print("✅ 性能測試成功")
        print("")
    
    print("🎉 所有測試完成！")

if __name__ == "__main__":
    main()