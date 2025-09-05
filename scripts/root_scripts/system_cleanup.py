#!/usr/bin/env python3
"""
TradingAgents 系統文件清理腳本
由 DevOps Engineer 墨子 設計
目標：從 29,465 個文件精簡至 5,000 個核心文件
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import argparse

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemCleaner:
    def __init__(self, root_path: str, dry_run: bool = True):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.backup_path = self.root_path / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = {
            "files_before": 0,
            "files_after": 0,
            "directories_removed": 0,
            "files_merged": 0,
            "files_deleted": 0,
            "space_saved_mb": 0
        }
        
        # 保護文件列表（絕對不能刪除）
        self.protected_files = {
            'main.py', 'app.py', 'requirements.txt', 'Dockerfile', 
            'docker-compose.yml', 'config.py', 'default_config.py',
            '.env', '.env.example', 'README.md', '.gitignore',
            'deploy_member_system.sh', 'alembic.ini'
        }
        
        # 保護目錄列表
        self.protected_dirs = {
            'tradingagents', 'frontend/src', 'alembic/versions',
            'nginx', 'ssl', 'backup/secrets', 'deployment/gcp',
            'deployment/aws', 'scripts'
        }

    def count_files(self) -> int:
        """統計文件數量"""
        count = 0
        for root, dirs, files in os.walk(self.root_path):
            count += len(files)
        return count

    def backup_critical_files(self):
        """備份關鍵文件"""
        logger.info("開始備份關鍵文件...")
        
        if not self.dry_run:
            self.backup_path.mkdir(parents=True, exist_ok=True)
        
        critical_patterns = [
            "*.py", "*.yml", "*.yaml", "*.json", "*.conf", "*.sh", 
            "*.sql", "*.tf", "Dockerfile*", "requirements.txt"
        ]
        
        backup_count = 0
        for pattern in critical_patterns:
            for file_path in self.root_path.rglob(pattern):
                if self._is_protected_file(file_path):
                    relative_path = file_path.relative_to(self.root_path)
                    backup_file = self.backup_path / relative_path
                    
                    if not self.dry_run:
                        backup_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, backup_file)
                    
                    backup_count += 1
                    logger.debug(f"備份: {relative_path}")
        
        logger.info(f"備份完成，共備份 {backup_count} 個關鍵文件")

    def _is_protected_file(self, file_path: Path) -> bool:
        """檢查是否為保護文件"""
        if file_path.name in self.protected_files:
            return True
        
        relative_path = str(file_path.relative_to(self.root_path))
        for protected_dir in self.protected_dirs:
            if relative_path.startswith(protected_dir):
                return True
        
        return False

    def cleanup_completion_reports(self):
        """合併完成報告文件"""
        logger.info("開始合併完成報告文件...")
        
        completion_reports = list(self.root_path.rglob("*COMPLETION_REPORT.md"))
        
        if not completion_reports:
            logger.info("未找到完成報告文件")
            return
        
        # 創建統一的完成報告
        consolidated_report_path = self.root_path / "docs" / "CONSOLIDATED_COMPLETION_REPORTS.md"
        
        if not self.dry_run:
            consolidated_report_path.parent.mkdir(exist_ok=True)
            
            with open(consolidated_report_path, 'w', encoding='utf-8') as consolidated_file:
                consolidated_file.write("# TradingAgents 系統完成報告彙總\n\n")
                consolidated_file.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                consolidated_file.write(f"合併報告數量: {len(completion_reports)}\n\n")
                consolidated_file.write("---\n\n")
                
                for report_path in sorted(completion_reports):
                    try:
                        with open(report_path, 'r', encoding='utf-8') as report_file:
                            content = report_file.read()
                            relative_path = report_path.relative_to(self.root_path)
                            
                            consolidated_file.write(f"## {relative_path}\n\n")
                            consolidated_file.write(content)
                            consolidated_file.write("\n\n---\n\n")
                            
                    except Exception as e:
                        logger.error(f"讀取報告文件失敗 {report_path}: {e}")
        
        # 刪除原始報告文件
        for report_path in completion_reports:
            if not self.dry_run:
                report_path.unlink()
            logger.info(f"刪除: {report_path.relative_to(self.root_path)}")
        
        self.stats["files_merged"] = len(completion_reports)
        logger.info(f"完成報告合併完成，共處理 {len(completion_reports)} 個文件")

    def cleanup_node_modules(self):
        """清理 node_modules 相關文件"""
        logger.info("開始清理 node_modules...")
        
        node_modules_dirs = []
        for root, dirs, files in os.walk(self.root_path):
            if 'node_modules' in dirs:
                node_modules_path = Path(root) / 'node_modules'
                # 只保留前端必需的 node_modules
                if 'frontend' not in str(node_modules_path):
                    node_modules_dirs.append(node_modules_path)
        
        for node_modules_dir in node_modules_dirs:
            if not self.dry_run:
                shutil.rmtree(node_modules_dir, ignore_errors=True)
            logger.info(f"刪除: {node_modules_dir.relative_to(self.root_path)}")
            self.stats["directories_removed"] += 1

    def cleanup_test_files(self):
        """整合測試文件"""
        logger.info("開始整合測試文件...")
        
        test_files = list(self.root_path.rglob("test_*.py"))
        tests_dir = self.root_path / "tests"
        
        if not self.dry_run:
            tests_dir.mkdir(exist_ok=True)
        
        # 按功能分類測試文件
        categories = {
            'api': [],
            'agents': [],
            'integration': [],
            'system': [],
            'misc': []
        }
        
        for test_file in test_files:
            file_name = test_file.name.lower()
            
            if any(keyword in file_name for keyword in ['api', 'endpoint', 'route']):
                categories['api'].append(test_file)
            elif any(keyword in file_name for keyword in ['analyst', 'agent']):
                categories['agents'].append(test_file)
            elif any(keyword in file_name for keyword in ['integration', 'system']):
                categories['integration'].append(test_file)
            elif any(keyword in file_name for keyword in ['monitor', 'config']):
                categories['system'].append(test_file)
            else:
                categories['misc'].append(test_file)
        
        # 移動和組織測試文件
        for category, files in categories.items():
            if not files:
                continue
                
            category_dir = tests_dir / category
            if not self.dry_run:
                category_dir.mkdir(exist_ok=True)
            
            for test_file in files:
                new_path = category_dir / test_file.name
                if not self.dry_run:
                    shutil.move(str(test_file), str(new_path))
                logger.info(f"移動測試文件: {test_file.name} -> {category}/")

    def cleanup_backup_directories(self):
        """清理備份目錄"""
        logger.info("開始清理備份目錄...")
        
        backup_patterns = ["*backup*", "*_backup_*", "tradingagents_backup_*"]
        
        for pattern in backup_patterns:
            for backup_dir in self.root_path.glob(pattern):
                if backup_dir.is_dir() and 'cleanup_backup' not in str(backup_dir):
                    if not self.dry_run:
                        shutil.rmtree(backup_dir, ignore_errors=True)
                    logger.info(f"刪除備份目錄: {backup_dir.relative_to(self.root_path)}")
                    self.stats["directories_removed"] += 1

    def cleanup_logs(self):
        """清理日誌文件"""
        logger.info("開始清理日誌文件...")
        
        logs_dir = self.root_path / "logs"
        if not logs_dir.exists():
            return
        
        # 保留最近7天的日誌
        cutoff_time = datetime.now().timestamp() - (7 * 24 * 3600)
        
        for log_file in logs_dir.rglob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                if not self.dry_run:
                    log_file.unlink()
                logger.info(f"刪除舊日誌: {log_file.relative_to(self.root_path)}")
                self.stats["files_deleted"] += 1

    def cleanup_coverage_files(self):
        """清理測試覆蓋率文件"""
        logger.info("開始清理測試覆蓋率文件...")
        
        coverage_dirs = list(self.root_path.rglob("coverage"))
        for coverage_dir in coverage_dirs:
            if coverage_dir.is_dir():
                if not self.dry_run:
                    shutil.rmtree(coverage_dir, ignore_errors=True)
                logger.info(f"刪除覆蓋率目錄: {coverage_dir.relative_to(self.root_path)}")
                self.stats["directories_removed"] += 1

    def update_dockerignore(self):
        """更新 .dockerignore 文件"""
        logger.info("更新 .dockerignore 文件...")
        
        dockerignore_path = self.root_path / ".dockerignore"
        
        dockerignore_content = """# 系統文件清理後的 .dockerignore
# 由 DevOps Engineer 墨子 自動生成

# Node modules
node_modules/
frontend/node_modules/
**/node_modules/

# 測試和覆蓋率
coverage/
.nyc_output/
tests/
test_*.py
*.test.js
*.spec.js

# 日誌文件
logs/
*.log

# 備份文件
*backup*/
*.backup
*.bak

# 開發文件
.git/
.gitignore
.vscode/
.idea/
*.pyc
__pycache__/
.pytest_cache/

# 文檔文件
docs/
*.md
!README.md

# 臨時文件
tmp/
temp/
*.tmp
*.temp

# 編譯文件
dist/
build/
*.egg-info/

# 環境文件
.env.local
.env.development
.env.test

# 監控文件
monitoring/grafana/
monitoring/dashboards/

# SSL證書（生產環境除外）
ssl/
*.pem
*.key
*.crt

# 清理腳本
scripts/system_cleanup.py
cleanup.log
cleanup_backup/
"""
        
        if not self.dry_run:
            with open(dockerignore_path, 'w', encoding='utf-8') as f:
                f.write(dockerignore_content)
        
        logger.info("已更新 .dockerignore 文件")

    def run_cleanup(self):
        """執行完整清理流程"""
        logger.info("=== TradingAgents 系統文件清理開始 ===")
        logger.info(f"根目錄: {self.root_path}")
        logger.info(f"乾運行模式: {self.dry_run}")
        
        # 統計清理前文件數量
        self.stats["files_before"] = self.count_files()
        logger.info(f"清理前文件數量: {self.stats['files_before']:,}")
        
        try:
            # 執行清理步驟
            self.backup_critical_files()
            self.cleanup_completion_reports()
            self.cleanup_node_modules()
            self.cleanup_test_files()
            self.cleanup_backup_directories()
            self.cleanup_logs()
            self.cleanup_coverage_files()
            self.update_dockerignore()
            
            # 統計清理後文件數量
            self.stats["files_after"] = self.count_files()
            
            # 生成清理報告
            self.generate_cleanup_report()
            
            logger.info("=== 系統文件清理完成 ===")
            
        except Exception as e:
            logger.error(f"清理過程中發生錯誤: {e}")
            raise

    def generate_cleanup_report(self):
        """生成清理報告"""
        report_data = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "statistics": self.stats,
            "files_reduced": self.stats["files_before"] - self.stats["files_after"],
            "reduction_percentage": round(
                ((self.stats["files_before"] - self.stats["files_after"]) / self.stats["files_before"]) * 100, 2
            ) if self.stats["files_before"] > 0 else 0
        }
        
        report_path = self.root_path / "SYSTEM_CLEANUP_REPORT.json"
        
        if not self.dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"清理統計：")
        logger.info(f"  清理前文件數: {self.stats['files_before']:,}")
        logger.info(f"  清理後文件數: {self.stats['files_after']:,}")
        logger.info(f"  減少文件數: {report_data['files_reduced']:,}")
        logger.info(f"  減少比例: {report_data['reduction_percentage']}%")
        logger.info(f"  刪除目錄數: {self.stats['directories_removed']}")
        logger.info(f"  合併文件數: {self.stats['files_merged']}")

def main():
    parser = argparse.ArgumentParser(description='TradingAgents 系統文件清理工具')
    parser.add_argument('--root-path', default='.', help='根目錄路徑')
    parser.add_argument('--dry-run', action='store_true', help='乾運行模式（不實際執行）')
    parser.add_argument('--force', action='store_true', help='強制執行（跳過確認）')
    
    args = parser.parse_args()
    
    if not args.force and not args.dry_run:
        response = input("您確定要執行系統文件清理嗎？這將刪除大量文件。輸入 'YES' 確認: ")
        if response != 'YES':
            print("清理已取消")
            return
    
    cleaner = SystemCleaner(args.root_path, args.dry_run)
    cleaner.run_cleanup()

if __name__ == "__main__":
    main()