#!/usr/bin/env python3
"""
安全的系統文件清理腳本
處理 Windows 路徑長度限制問題
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_remove_directory(dir_path):
    """安全刪除目錄，處理長路徑問題"""
    try:
        if os.path.exists(dir_path):
            # 使用 Windows 長路徑前綴
            if os.name == 'nt' and len(str(dir_path)) > 260:
                dir_path = "\\\\?\\" + os.path.abspath(dir_path)
            
            shutil.rmtree(dir_path, ignore_errors=True)
            logger.info(f"已刪除: {dir_path}")
            return True
    except Exception as e:
        logger.error(f"刪除失敗 {dir_path}: {e}")
        return False

def cleanup_node_modules():
    """清理 node_modules"""
    logger.info("開始清理 node_modules...")
    
    # 只保留前端必需的 node_modules
    keep_paths = [
        "TradingAgents/frontend/node_modules"
    ]
    
    # 查找所有 node_modules 目錄
    for root, dirs, files in os.walk("."):
        if "node_modules" in dirs:
            node_modules_path = os.path.join(root, "node_modules")
            
            # 檢查是否應該保留
            should_keep = False
            for keep_path in keep_paths:
                if keep_path in node_modules_path.replace("\\", "/"):
                    should_keep = True
                    break
            
            if not should_keep:
                safe_remove_directory(node_modules_path)
                # 移除目錄以避免遞歸
                dirs.remove("node_modules")

def cleanup_completion_reports():
    """清理完成報告"""
    logger.info("開始清理完成報告...")
    
    reports = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if "COMPLETION_REPORT.md" in file:
                reports.append(os.path.join(root, file))
    
    logger.info(f"找到 {len(reports)} 個完成報告文件")
    
    # 創建合併報告
    with open("CONSOLIDATED_COMPLETION_REPORTS.md", "w", encoding="utf-8") as f:
        f.write("# 合併完成報告\n\n")
        f.write(f"生成時間: {datetime.now()}\n")
        f.write(f"合併文件數: {len(reports)}\n\n")
        
        for report_path in reports:
            try:
                with open(report_path, "r", encoding="utf-8") as rf:
                    content = rf.read()
                    f.write(f"## {report_path}\n\n")
                    f.write(content)
                    f.write("\n\n---\n\n")
                
                # 刪除原文件
                os.remove(report_path)
                logger.info(f"已處理: {report_path}")
                
            except Exception as e:
                logger.error(f"處理報告失敗 {report_path}: {e}")

def cleanup_backup_directories():
    """清理備份目錄"""
    logger.info("開始清理備份目錄...")
    
    backup_patterns = ["tradingagents_backup_", "_backup"]
    
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:  # 使用切片創建副本
            if any(pattern in dir_name for pattern in backup_patterns):
                backup_path = os.path.join(root, dir_name)
                safe_remove_directory(backup_path)
                dirs.remove(dir_name)  # 移除以避免遞歸

def cleanup_test_files():
    """整理測試文件"""
    logger.info("開始整理測試文件...")
    
    # 創建測試目錄結構
    os.makedirs("tests/api", exist_ok=True)
    os.makedirs("tests/agents", exist_ok=True)
    os.makedirs("tests/integration", exist_ok=True)
    os.makedirs("tests/system", exist_ok=True)
    
    # 移動測試文件
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                old_path = os.path.join(root, file)
                
                # 分類測試文件
                if "api" in file or "endpoint" in file:
                    new_path = os.path.join("tests/api", file)
                elif "analyst" in file or "agent" in file:
                    new_path = os.path.join("tests/agents", file)
                elif "integration" in file or "system" in file:
                    new_path = os.path.join("tests/integration", file)
                else:
                    new_path = os.path.join("tests/system", file)
                
                try:
                    shutil.move(old_path, new_path)
                    logger.info(f"已移動: {file}")
                except Exception as e:
                    logger.error(f"移動失敗 {file}: {e}")

def cleanup_logs():
    """清理日誌文件"""
    logger.info("開始清理日誌文件...")
    
    cutoff_time = datetime.now().timestamp() - (7 * 24 * 3600)  # 7天前
    
    for root, dirs, files in os.walk("TradingAgents/logs"):
        for file in files:
            if file.endswith(".log"):
                log_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(log_path) < cutoff_time:
                        os.remove(log_path)
                        logger.info(f"已刪除舊日誌: {file}")
                except Exception as e:
                    logger.error(f"刪除日誌失敗 {file}: {e}")

def main():
    logger.info("=== 開始安全系統清理 ===")
    
    # 統計清理前文件數
    file_count_before = sum([len(files) for r, d, files in os.walk(".")])
    logger.info(f"清理前文件數: {file_count_before:,}")
    
    # 執行清理
    cleanup_node_modules()
    cleanup_completion_reports()
    cleanup_backup_directories()
    cleanup_test_files()
    cleanup_logs()
    
    # 統計清理後文件數
    file_count_after = sum([len(files) for r, d, files in os.walk(".")])
    logger.info(f"清理後文件數: {file_count_after:,}")
    logger.info(f"減少文件數: {file_count_before - file_count_after:,}")
    logger.info(f"減少比例: {((file_count_before - file_count_after) / file_count_before * 100):.1f}%")
    
    logger.info("=== 系統清理完成 ===")

if __name__ == "__main__":
    main()