#!/usr/bin/env python3
"""
快速修復多餘括號的問題
"""

import re
from pathlib import Path

def fix_parentheses_in_file(file_path):
    """修復文件中的多餘括號"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修復模式: createApiUrl(...)))
        pattern = r'createApiUrl\([^)]*\)\)\)\)'
        content = re.sub(pattern, lambda m: m.group(0)[:-2], content)
        
        # 修復模式: createApiUrl(...)))
        pattern = r'createApiUrl\([^)]*\)\)\)'
        content = re.sub(pattern, lambda m: m.group(0)[:-1], content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修復 {file_path}")
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
        if fix_parentheses_in_file(file_path):
            fixed_count += 1
    
    print(f"📊 修復了 {fixed_count} 個文件")

if __name__ == "__main__":
    main()