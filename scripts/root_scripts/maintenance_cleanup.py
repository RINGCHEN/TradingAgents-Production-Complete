#!/usr/bin/env python3
"""
TradingAgents 系統維護清理腳本
定期執行的輕量級清理，保持系統整潔
由 DevOps Engineer 墨子 設計
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
import schedule
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MaintenanceCleanup:
    def __init__(self, root_path="."):
        self.root_path = Path(root_path)
        self.cleanup_stats = {}

    def cleanup_temporary_files(self):
        """清理臨時文件"""
        logger.info("清理臨時文件...")
        
        temp_patterns = [
            "*.tmp", "*.temp", "*.bak", "*.swp", "*.swo",
            "*.pyc", "*~", ".DS_Store", "Thumbs.db"
        ]
        
        cleaned_count = 0
        for pattern in temp_patterns:
            for temp_file in self.root_path.rglob(pattern):
                try:
                    temp_file.unlink()
                    cleaned_count += 1
                    logger.debug(f"刪除臨時文件: {temp_file}")
                except Exception as e:
                    logger.error(f"刪除失敗 {temp_file}: {e}")
        
        self.cleanup_stats["temp_files_cleaned"] = cleaned_count
        logger.info(f"清理臨時文件完成，共清理 {cleaned_count} 個文件")

    def cleanup_old_logs(self, days_to_keep=7):
        """清理舊日誌文件"""
        logger.info(f"清理 {days_to_keep} 天前的日誌文件...")
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        logs_dir = self.root_path / "TradingAgents" / "logs"
        
        if not logs_dir.exists():
            logger.info("日誌目錄不存在，跳過日誌清理")
            return
        
        cleaned_count = 0
        for log_file in logs_dir.rglob("*.log"):
            try:
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
                    logger.debug(f"刪除舊日誌: {log_file}")
            except Exception as e:
                logger.error(f"刪除日誌失敗 {log_file}: {e}")
        
        self.cleanup_stats["old_logs_cleaned"] = cleaned_count
        logger.info(f"清理舊日誌完成，共清理 {cleaned_count} 個文件")

    def cleanup_cache_files(self):
        """清理緩存文件"""
        logger.info("清理緩存文件...")
        
        cache_patterns = [
            "__pycache__", ".pytest_cache", ".cache",
            "node_modules/.cache", ".npm", ".yarn"
        ]
        
        cleaned_count = 0
        for pattern in cache_patterns:
            for cache_path in self.root_path.rglob(pattern):
                if cache_path.is_dir():
                    try:
                        shutil.rmtree(cache_path, ignore_errors=True)
                        cleaned_count += 1
                        logger.debug(f"刪除緩存目錄: {cache_path}")
                    except Exception as e:
                        logger.error(f"刪除緩存失敗 {cache_path}: {e}")
        
        self.cleanup_stats["cache_dirs_cleaned"] = cleaned_count
        logger.info(f"清理緩存完成，共清理 {cleaned_count} 個目錄")

    def check_disk_usage(self):
        """檢查磁盤使用情況"""
        try:
            total, used, free = shutil.disk_usage(self.root_path)
            
            usage_percent = (used / total) * 100
            free_gb = free // (1024**3)
            
            logger.info(f"磁盤使用率: {usage_percent:.1f}%")
            logger.info(f"可用空間: {free_gb} GB")
            
            self.cleanup_stats["disk_usage_percent"] = round(usage_percent, 1)
            self.cleanup_stats["free_space_gb"] = free_gb
            
            # 磁盤空間警告
            if usage_percent > 85:
                logger.warning("⚠️  磁盤使用率超過85%，建議進行深度清理")
            elif free_gb < 5:
                logger.warning("⚠️  可用空間不足5GB，建議進行深度清理")
            
        except Exception as e:
            logger.error(f"檢查磁盤使用失敗: {e}")

    def optimize_git_repository(self):
        """優化Git存儲庫"""
        logger.info("優化Git存儲庫...")
        
        try:
            # 清理Git垃圾
            os.system("git gc --auto")
            logger.info("Git垃圾回收完成")
            
            # 檢查存儲庫大小
            git_dir = self.root_path / ".git"
            if git_dir.exists():
                size_mb = sum(f.stat().st_size for f in git_dir.rglob('*') if f.is_file()) / (1024**2)
                logger.info(f"Git存儲庫大小: {size_mb:.1f} MB")
                self.cleanup_stats["git_repo_size_mb"] = round(size_mb, 1)
                
        except Exception as e:
            logger.error(f"Git優化失敗: {e}")

    def generate_maintenance_report(self):
        """生成維護報告"""
        report_data = {
            "maintenance_timestamp": datetime.now().isoformat(),
            "cleanup_statistics": self.cleanup_stats
        }
        
        report_path = self.root_path / "maintenance_report.json"
        
        try:
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"維護報告已生成: {report_path}")
            
        except Exception as e:
            logger.error(f"生成維護報告失敗: {e}")

    def run_daily_maintenance(self):
        """執行日常維護"""
        logger.info("=== 開始日常維護清理 ===")
        
        try:
            self.cleanup_temporary_files()
            self.cleanup_old_logs(days_to_keep=7)
            self.cleanup_cache_files()
            self.check_disk_usage()
            self.optimize_git_repository()
            self.generate_maintenance_report()
            
            logger.info("=== 日常維護清理完成 ===")
            
        except Exception as e:
            logger.error(f"維護過程中發生錯誤: {e}")

    def run_weekly_maintenance(self):
        """執行週期維護"""
        logger.info("=== 開始週期維護清理 ===")
        
        try:
            # 週期性維護包含更徹底的清理
            self.cleanup_temporary_files()
            self.cleanup_old_logs(days_to_keep=14)  # 保留更久的日誌
            self.cleanup_cache_files()
            
            # 檢查大文件
            large_files = []
            for file_path in self.root_path.rglob("*"):
                if file_path.is_file():
                    size_mb = file_path.stat().st_size / (1024**2)
                    if size_mb > 50:  # 大於50MB的文件
                        large_files.append((str(file_path), size_mb))
            
            if large_files:
                logger.info("發現大文件（>50MB）：")
                for file_path, size_mb in sorted(large_files, key=lambda x: x[1], reverse=True)[:10]:
                    logger.info(f"  {file_path}: {size_mb:.1f} MB")
            
            self.check_disk_usage()
            self.generate_maintenance_report()
            
            logger.info("=== 週期維護清理完成 ===")
            
        except Exception as e:
            logger.error(f"週期維護過程中發生錯誤: {e}")

def main():
    """主函數 - 設置定期任務"""
    cleanup = MaintenanceCleanup()
    
    # 設置定期任務
    schedule.every().day.at("02:00").do(cleanup.run_daily_maintenance)  # 每天凌晨2點
    schedule.every().sunday.at("03:00").do(cleanup.run_weekly_maintenance)  # 每週日凌晨3點
    
    logger.info("維護清理定時任務已啟動")
    logger.info("日常清理: 每天 02:00")
    logger.info("週期清理: 每週日 03:00")
    logger.info("按 Ctrl+C 停止服務")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
    except KeyboardInterrupt:
        logger.info("維護清理服務已停止")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingAgents 維護清理工具')
    parser.add_argument('--daily', action='store_true', help='執行日常維護')
    parser.add_argument('--weekly', action='store_true', help='執行週期維護')
    parser.add_argument('--daemon', action='store_true', help='作為守護進程運行')
    
    args = parser.parse_args()
    
    cleanup = MaintenanceCleanup()
    
    if args.daily:
        cleanup.run_daily_maintenance()
    elif args.weekly:
        cleanup.run_weekly_maintenance()
    elif args.daemon:
        main()
    else:
        cleanup.run_daily_maintenance()  # 預設執行日常維護