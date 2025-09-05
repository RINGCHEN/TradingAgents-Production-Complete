#!/usr/bin/env python3
"""
簡化版本的 TradingAgents 部署就緒檢查

檢查關鍵文件和目錄是否存在，確保部署包完整性。

作者：天工 (TianGong) + Claude Code
日期：2025-09-05
"""

import os
import sys
from pathlib import Path
import json
import time

def check_critical_files():
    """檢查關鍵文件存在性"""
    critical_files = [
        "tradingagents/app.py",
        "requirements.txt", 
        "Dockerfile",
        ".env.example",
        ".gitignore",
        "DEPLOYMENT_MASTER_PLAN.md",
        "DIGITALOCEAN_SETUP_GUIDE.md",
        "EMERGENCY_ROLLBACK.md"
    ]
    
    print("=== 檢查關鍵文件 ===")
    missing_files = []
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def check_17_systems():
    """檢查17個核心系統目錄結構"""
    systems = {
        # 前端系統群組 (3個)
        "frontend": "前端系統",
        "frontend/src/admin/AdminApp_Ultimate.tsx": "管理後台",
        
        # 後端API系統群組 (2個)
        "tradingagents/app.py": "FastAPI核心",
        "tradingagents/api/payuni_endpoints.py": "PayUni支付",
        
        # AI智能系統群組 (3個)
        "tradingagents/agents/analysts": "AI分析師",
        "training": "AI訓練系統",
        "gpu_training": "GPU訓練",
        "gpt_oss": "模型服務",
        
        # 數據基礎設施群組 (3個)
        "tradingagents/dataflows/finmind_adapter.py": "數據源",
        "tradingagents/database": "資料庫",
        "monitoring": "監控系統",
        
        # 安全認證系統群組 (2個)
        "tradingagents/auth": "認證系統",
        "secure": "安全配置",
        
        # 部署DevOps系統群組 (2個)
        "deployment": "部署配置",
        "tests": "測試系統",
        "scripts": "開發工具",
        
        # 分析報告系統群組 (2個)
        "evaluation_results": "評估結果",
        "reports": "分析報告",
        "work_reports": "工作報告"
    }
    
    print("\n=== 檢查17個核心系統 ===")
    missing_systems = []
    present_systems = 0
    
    for path, description in systems.items():
        if Path(path).exists():
            print(f"[OK] {description}: {path}")
            present_systems += 1
        else:
            print(f"[MISSING] {description}: {path}")
            missing_systems.append((path, description))
    
    total_systems = len(systems)
    completion_rate = (present_systems / total_systems) * 100
    
    print(f"\n系統完整度: {present_systems}/{total_systems} ({completion_rate:.1f}%)")
    
    return completion_rate >= 90, missing_systems, present_systems, total_systems

def check_environment_template():
    """檢查環境變數模板"""
    print("\n=== 檢查環境變數模板 ===")
    
    if not Path(".env.example").exists():
        print("[ERROR] .env.example 不存在")
        return False
    
    with open(".env.example", 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    required_vars = [
        "PORT=",
        "DATABASE_URL=",
        "PAYUNI_MERCHANT_ID=",
        "SECRET_KEY=",
        "JWT_SECRET="
    ]
    
    missing_vars = []
    for var in required_vars:
        if var in env_content:
            print(f"[OK] {var.split('=')[0]}")
        else:
            print(f"[MISSING] {var.split('=')[0]}")
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

def check_dockerfile():
    """檢查 Dockerfile 配置"""
    print("\n=== 檢查 Dockerfile ===")
    
    if not Path("Dockerfile").exists():
        print("[ERROR] Dockerfile 不存在")
        return False
    
    with open("Dockerfile", 'r') as f:
        dockerfile_content = f.read()
    
    required_elements = [
        "FROM python:",
        "WORKDIR /app",
        "COPY requirements.txt",
        "RUN pip install",
        "EXPOSE 8000",
        "CMD"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element in dockerfile_content:
            print(f"[OK] {element}")
        else:
            print(f"[MISSING] {element}")
            missing_elements.append(element)
    
    return len(missing_elements) == 0, missing_elements

def generate_readiness_report():
    """生成部署就緒報告"""
    print("=" * 80)
    print("TradingAgents 部署就緒檢查")
    print("=" * 80)
    
    # 執行所有檢查
    files_ok, missing_files = check_critical_files()
    systems_ok, missing_systems, present_systems, total_systems = check_17_systems()
    env_ok, missing_env_vars = check_environment_template()
    docker_ok, missing_docker = check_dockerfile()
    
    # 計算總體就緒度
    checks_passed = sum([files_ok, systems_ok, env_ok, docker_ok])
    total_checks = 4
    overall_ready = checks_passed == total_checks and present_systems >= 15
    
    # 生成報告
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "timestamp": timestamp,
        "overall_ready": overall_ready,
        "checks": {
            "critical_files": {
                "passed": files_ok,
                "missing": missing_files
            },
            "system_architecture": {
                "passed": systems_ok,
                "present": present_systems,
                "total": total_systems,
                "completion_rate": round((present_systems / total_systems) * 100, 1),
                "missing": [(path, desc) for path, desc in missing_systems]
            },
            "environment_config": {
                "passed": env_ok,
                "missing": missing_env_vars
            },
            "docker_config": {
                "passed": docker_ok,
                "missing": missing_docker
            }
        },
        "summary": {
            "checks_passed": checks_passed,
            "total_checks": total_checks,
            "readiness_score": round((checks_passed / total_checks) * 100, 1)
        }
    }
    
    # 保存報告
    report_file = f"deployment_readiness_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 顯示結果
    print("=" * 80)
    print("檢查結果總結")
    print("=" * 80)
    
    status_icon = "[READY]" if overall_ready else "[NOT_READY]"
    print(f"{status_icon} 總體就緒狀態: {'就緒' if overall_ready else '未就緒'}")
    print(f"[INFO] 檢查通過: {checks_passed}/{total_checks}")
    print(f"[INFO] 系統完整度: {present_systems}/{total_systems} ({report['checks']['system_architecture']['completion_rate']}%)")
    print(f"[INFO] 就緒分數: {report['summary']['readiness_score']}%")
    print(f"[INFO] 報告已保存: {report_file}")
    
    if overall_ready:
        print("\n[SUCCESS] 系統已準備好進行部署！")
        print("下一步:")
        print("1. 執行 deploy_to_github.bat 創建 GitHub 倉庫")
        print("2. 參考 DIGITALOCEAN_SETUP_GUIDE.md 配置 DigitalOcean")
        print("3. 配置環境變數並啟動部署")
    else:
        print("\n[WARNING] 系統尚未完全準備好，請解決以上問題。")
        if missing_files:
            print("缺失關鍵文件:", missing_files)
        if missing_systems:
            print("缺失系統組件:", [desc for _, desc in missing_systems])
    
    return overall_ready

def main():
    """主函數"""
    try:
        # 切換到腳本所在目錄
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # 執行檢查
        ready = generate_readiness_report()
        
        # 設置退出碼
        sys.exit(0 if ready else 1)
        
    except Exception as e:
        print(f"[ERROR] 檢查過程發生錯誤: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()