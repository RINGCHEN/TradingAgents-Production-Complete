#!/usr/bin/env python3
"""
修復批量替換導致的語法錯誤
"""

import re
from pathlib import Path

def fix_syntax_errors_in_file(file_path):
    """修復單個文件中的語法錯誤"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修復模式1: fetch(...)), { -> fetch(..., {
        content = re.sub(
            r'fetch\(createApiUrl\([^)]+\)\)\s*,\s*\{',
            lambda m: m.group(0).replace(')), {', ', {'),
            content
        )
        
        # 修復模式2: createApiUrl(...))) -> createApiUrl(...))
        content = re.sub(
            r'createApiUrl\([^)]+\)\)\)',
            lambda m: m.group(0)[:-1],
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ 錯誤 {file_path}: {e}")
        return False

def main():
    frontend_dir = Path("TradingAgents/frontend/src")
    
    if not frontend_dir.exists():
        print(f"❌ 目錄不存在: {frontend_dir}")
        return
    
    files = list(frontend_dir.rglob("*.tsx")) + list(frontend_dir.rglob("*.ts"))
    
    fixed_count = 0
    for file_path in files:
        if fix_syntax_errors_in_file(file_path):
            print(f"✅ 修復 {file_path}")
            fixed_count += 1
    
    print(f"📊 修復了 {fixed_count} 個文件")

if __name__ == "__main__":
    main()