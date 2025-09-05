#!/usr/bin/env python3
"""
TradingAgents 架構重組方案A執行腳本
統一所有系統到 TradingAgents/ 目錄下
"""

import os
import shutil
from pathlib import Path
import json

class ArchitectureReorganizer:
    def __init__(self):
        self.root_dir = Path(".")
        self.target_dir = Path("TradingAgents")
        self.moved_items = []
        self.conflicts = []
        
    def analyze_current_structure(self):
        """分析當前架構結構"""
        print("=== 當前架構分析 ===")
        
        # 根目錄重要系統
        root_systems = [
            "configs/",
            "models/", 
            "training/",
            "tests/",
            "scripts/",
            "data/",
            "art_data/",
            "admin_content_module_react/",
            "complete_admin_system/",
            "requirements.txt"
        ]
        
        # TradingAgents目錄現有系統
        trading_systems = [
            "tradingagents/",
            "frontend/",
            "gpt_oss/",
            "gpu_training/", 
            "monitoring/",
            "requirements.txt",
            "Dockerfile"
        ]
        
        print("📂 根目錄重要系統:")
        for item in root_systems:
            path = self.root_dir / item
            if path.exists():
                if path.is_dir():
                    file_count = len(list(path.rglob("*")))
                    print(f"  ✅ {item} ({file_count} 項目)")
                else:
                    size = path.stat().st_size
                    print(f"  ✅ {item} ({size} bytes)")
            else:
                print(f"  ❌ {item} (不存在)")
        
        print("\n📁 TradingAgents/ 現有系統:")
        for item in trading_systems:
            path = self.target_dir / item
            if path.exists():
                if path.is_dir():
                    file_count = len(list(path.rglob("*")))
                    print(f"  ✅ {item} ({file_count} 項目)")
                else:
                    size = path.stat().st_size
                    print(f"  ✅ {item} ({size} bytes)")
            else:
                print(f"  ❌ {item} (不存在)")
    
    def check_conflicts(self):
        """檢查移動過程中的衝突"""
        print("\n=== 衝突檢查 ===")
        
        items_to_move = [
            ("configs", "configs"),
            ("models", "models"),
            ("training", "training"),
            ("tests", "tests"), 
            ("scripts", "scripts"),
            ("data", "data"),
            ("requirements.txt", "requirements-root.txt"),  # 重命名避免衝突
        ]
        
        for src_name, dst_name in items_to_move:
            src_path = self.root_dir / src_name
            dst_path = self.target_dir / dst_name
            
            if src_path.exists() and dst_path.exists():
                print(f"  ⚠️  衝突: {src_name} -> {dst_name} (目標已存在)")
                self.conflicts.append((src_name, dst_name))
            elif src_path.exists():
                print(f"  ✅ 可移動: {src_name} -> {dst_name}")
            else:
                print(f"  ❌ 來源不存在: {src_name}")
    
    def create_backup(self):
        """創建備份"""
        print("\n=== 創建備份 ===")
        backup_dir = Path("architecture_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # 備份TradingAgents目錄
        if self.target_dir.exists():
            shutil.copytree(self.target_dir, backup_dir / "TradingAgents_backup")
            print(f"  ✅ 已備份 TradingAgents/ -> {backup_dir}/TradingAgents_backup/")
        
        return backup_dir
    
    def move_systems(self, dry_run=True):
        """移動系統到TradingAgents/"""
        print(f"\n=== {'模擬' if dry_run else '實際'}移動系統 ===")
        
        moves = [
            ("configs", "configs"),
            ("models", "models"), 
            ("training", "training"),
            ("scripts", "scripts"),
            ("data", "data"),
            ("art_data", "art_data"),
            ("requirements.txt", "requirements-root.txt"),
        ]
        
        for src_name, dst_name in moves:
            src_path = self.root_dir / src_name
            dst_path = self.target_dir / dst_name
            
            if src_path.exists():
                if dst_path.exists():
                    print(f"  ⚠️  跳過 {src_name} -> {dst_name} (目標已存在)")
                    continue
                
                if not dry_run:
                    try:
                        if src_path.is_dir():
                            shutil.move(str(src_path), str(dst_path))
                        else:
                            shutil.move(str(src_path), str(dst_path))
                        self.moved_items.append((src_name, dst_name))
                        print(f"  ✅ 已移動 {src_name} -> {dst_name}")
                    except Exception as e:
                        print(f"  ❌ 移動失敗 {src_name}: {e}")
                else:
                    print(f"  📋 將移動 {src_name} -> {dst_name}")
            else:
                print(f"  ❌ 來源不存在: {src_name}")
    
    def handle_tests_merge(self, dry_run=True):
        """處理tests目錄的合併"""
        print(f"\n=== {'模擬' if dry_run else '實際'}合併測試系統 ===")
        
        root_tests = self.root_dir / "tests"
        target_tests = self.target_dir / "tests"
        
        if not root_tests.exists():
            print("  ❌ 根目錄tests/不存在")
            return
        
        if target_tests.exists():
            print("  ⚠️  TradingAgents/tests/已存在，需要合併")
            if not dry_run:
                # 合併策略：將根目錄tests/內容移動到TradingAgents/tests/root_tests/
                merge_target = target_tests / "root_tests"
                shutil.move(str(root_tests), str(merge_target))
                print(f"  ✅ 已合併 tests/ -> TradingAgents/tests/root_tests/")
            else:
                print("  📋 將合併到 TradingAgents/tests/root_tests/")
        else:
            if not dry_run:
                shutil.move(str(root_tests), str(target_tests))
                print(f"  ✅ 已移動 tests/ -> TradingAgents/tests/")
            else:
                print("  📋 將移動 tests/ -> TradingAgents/tests/")
    
    def update_requirements(self, dry_run=True):
        """合併和更新requirements.txt"""
        print(f"\n=== {'模擬' if dry_run else '實際'}更新依賴配置 ===")
        
        root_req = self.root_dir / "requirements.txt"
        target_req = self.target_dir / "requirements.txt"
        
        if not root_req.exists():
            print("  ❌ 根目錄requirements.txt不存在")
            return
        
        if not target_req.exists():
            print("  ❌ TradingAgents/requirements.txt不存在")
            return
        
        if not dry_run:
            # 讀取兩個requirements文件
            with open(root_req, 'r', encoding='utf-8') as f:
                root_deps = f.read()
            
            with open(target_req, 'r', encoding='utf-8') as f:
                target_deps = f.read()
            
            # 創建合併的requirements
            merged_content = f"""# TradingAgents 統一依賴配置
# 生產部署 + AI訓練系統

# ============= 生產部署依賴 =============
{target_deps}

# ============= AI訓練和開發依賴 =============  
# (從根目錄requirements.txt合併)
{root_deps}
"""
            
            # 備份原文件
            shutil.copy2(target_req, self.target_dir / "requirements-production-backup.txt")
            
            # 寫入合併文件
            with open(target_req, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            print("  ✅ 已合併requirements.txt文件")
        else:
            print("  📋 將合併兩個requirements.txt文件")
    
    def create_new_structure_report(self):
        """生成新架構結構報告"""
        print("\n=== 新架構結構 ===")
        
        report = {
            "reorganization_date": "2025-09-05",
            "target_structure": "TradingAgents/ (統一架構)",
            "moved_systems": self.moved_items,
            "conflicts": self.conflicts,
            "new_structure": {}
        }
        
        # 掃描新結構
        if self.target_dir.exists():
            for item in self.target_dir.iterdir():
                if item.is_dir():
                    file_count = len([f for f in item.rglob('*') if f.is_file()])
                    report["new_structure"][item.name] = f"directory ({file_count} files)"
                else:
                    size = item.stat().st_size
                    report["new_structure"][item.name] = f"file ({size} bytes)"
        
        # 保存報告
        report_path = self.target_dir / "ARCHITECTURE_REORGANIZATION_REPORT.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ 已生成架構報告: {report_path}")
        
        # 顯示新結構
        print("\n📁 新的統一結構:")
        for name, desc in report["new_structure"].items():
            print(f"  TradingAgents/{name}/  ({desc})")

def main():
    reorganizer = ArchitectureReorganizer()
    
    # 第1步：分析當前結構
    reorganizer.analyze_current_structure()
    
    # 第2步：檢查衝突
    reorganizer.check_conflicts()
    
    # 第3步：模擬移動（dry run）
    reorganizer.move_systems(dry_run=True)
    reorganizer.handle_tests_merge(dry_run=True)
    reorganizer.update_requirements(dry_run=True)
    
    print("\n" + "="*60)
    print("📋 架構重組計劃已準備完成！")
    print("🔧 執行實際移動請運行: python architecture_reorganization_plan_A.py --execute")
    print("="*60)


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    if "--execute" in sys.argv:
        print("⚠️  執行實際架構重組...")
        reorganizer = ArchitectureReorganizer()
        reorganizer.create_backup()
        reorganizer.move_systems(dry_run=False)
        reorganizer.handle_tests_merge(dry_run=False)
        reorganizer.update_requirements(dry_run=False)
        reorganizer.create_new_structure_report()
        print("🎉 架構重組完成！")
    else:
        main()