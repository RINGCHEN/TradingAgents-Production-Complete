#!/usr/bin/env python3
"""
批量修復日誌調用問題
修復所有 get_api_logger() 調用缺少參數的問題
"""

import os
import re
import glob

def fix_logger_calls_in_file(file_path):
    """修復單個文件中的日誌調用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 提取文件名作為日誌名稱
        file_name = os.path.basename(file_path).replace('.py', '')
        
        # 修復各種日誌調用
        patterns_and_replacements = [
            (r'get_api_logger\(\)', f'get_api_logger("{file_name}")'),
            (r'get_security_logger\(\)', f'get_security_logger("{file_name}")'),
            (r'get_system_logger\(\)', f'get_system_logger("{file_name}")'),
            (r'get_analysis_logger\(\)', f'get_analysis_logger("{file_name}")'),
            (r'get_performance_logger\(\)', f'get_performance_logger("{file_name}")'),
        ]
        
        changes_made = False
        for pattern, replacement in patterns_and_replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
        
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修復: {file_path}")
            return True
        else:
            print(f"⚪ 跳過: {file_path} (無需修改)")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤: {file_path} - {e}")
        return False

def main():
    """主函數"""
    print("🔧 開始批量修復日誌調用問題...")
    
    # 查找所有Python文件
    base_path = "C:/Users/Ring/Documents/GitHub/twstock/TradingAgents/tradingagents"
    python_files = glob.glob(f"{base_path}/**/*.py", recursive=True)
    
    fixed_count = 0
    total_count = len(python_files)
    
    for file_path in python_files:
        if fix_logger_calls_in_file(file_path):
            fixed_count += 1
    
    print(f"\n📊 修復完成:")
    print(f"   總文件數: {total_count}")
    print(f"   修復文件數: {fixed_count}")
    print(f"   成功率: {(fixed_count/total_count)*100:.1f}%")

if __name__ == "__main__":
    main()