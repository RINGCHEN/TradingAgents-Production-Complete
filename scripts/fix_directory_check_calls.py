#!/usr/bin/env python3
"""
修復自動執行的目錄檢查調用

移除所有在模組級別自動執行的 ensure_tradingagents_directory() 調用，
因為這些調用在模組導入時就會執行，導致路徑問題。

作者：天工 (TianGong) + Claude Code
日期：2025-09-05
"""

import os
from pathlib import Path
import re

def fix_directory_check_calls(root_dir: Path):
    """移除自動執行的目錄檢查調用"""
    print("[FIX] 修復自動執行的目錄檢查調用...")
    
    files_fixed = 0
    
    # 查找所有 Python 文件
    for py_file in root_dir.rglob("*.py"):
        if 'fix_directory_check_calls.py' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 替換獨立調用的 ensure_tradingagents_directory()
            # 但保留函數定義
            patterns_to_fix = [
                # 移除模組級別的自動調用
                (r'\n# 確保目錄正確\nensure_tradingagents_directory\(\)\n', 
                 '\n# 目錄檢查函數已準備好，但不在模組導入時自動執行\n# 只在需要時手動調用 ensure_tradingagents_directory()\n'),
                
                # 移除其他自動調用模式
                (r'\nensure_tradingagents_directory\(\)(?=\s*\n)', 
                 '\n# ensure_tradingagents_directory() # 已註釋，避免模組導入時執行'),
            ]
            
            for pattern, replacement in patterns_to_fix:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_fixed += 1
                print(f"  [OK] 修復: {py_file.relative_to(root_dir)}")
                
        except Exception as e:
            print(f"  [ERR] 處理 {py_file.relative_to(root_dir)} 時出錯: {e}")
    
    print(f"\n[COMPLETE] 修復完成，共修復 {files_fixed} 個文件")

if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent
    fix_directory_check_calls(root_dir)