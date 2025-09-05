#!/usr/bin/env python3
"""
批量修復前端代碼中直接使用 /api/ 路徑的問題
將所有 fetch('/api/..') 替換為 fetch(createApiUrl('/api/..'))
"""

import os
import re
import shutil
from pathlib import Path

def fix_api_calls_in_file(file_path):
    """修復單個文件中的API調用"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 備份原始內容
        original_content = content
        modifications = []
        
        # 檢查是否需要添加 createApiUrl 導入
        needs_import = False
        
        # Pattern 1: fetch('/api/...') -> fetch(createApiUrl('/api/...'))
        pattern1 = r"fetch\s*\(\s*['\"](/api/[^'\"]+)['\"]"
        matches1 = re.finditer(pattern1, content, re.IGNORECASE)
        
        for match in matches1:
            api_path = match.group(1)
            old_text = match.group(0)
            new_text = f"fetch(createApiUrl('{api_path}')"
            content = content.replace(old_text, new_text, 1)
            modifications.append(f"  - {old_text} -> {new_text}")
            needs_import = True
        
        # Pattern 2: fetch(`/api/...`) -> fetch(createApiUrl(`/api/...`))
        pattern2 = r"fetch\s*\(\s*`(/api/[^`]+)`"
        matches2 = re.finditer(pattern2, content, re.IGNORECASE)
        
        for match in matches2:
            api_path = match.group(1)
            old_text = match.group(0)
            # 需要檢查是否包含模板字符串變量
            if "${" in api_path:
                new_text = f"fetch(createApiUrl(`{api_path}`))"
            else:
                new_text = f"fetch(createApiUrl('{api_path}'))"
            content = content.replace(old_text, new_text, 1)
            modifications.append(f"  - {old_text} -> {new_text}")
            needs_import = True
        
        # 添加 createApiUrl 導入（如果需要）
        if needs_import and "createApiUrl" not in content:
            # 查找現有的導入語句
            import_patterns = [
                r"import\s+{[^}]*}\s+from\s+['\"][^'\"]*config[^'\"]*['\"];?",
                r"import\s+[^'\"\s]+\s+from\s+['\"][^'\"]*config[^'\"]*['\"];?"
            ]
            
            import_added = False
            for pattern in import_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    import_line = match.group(0)
                    if "createApiUrl" not in import_line:
                        # 修改現有導入
                        if "{" in import_line and "}" in import_line:
                            # 現有命名導入
                            new_import = import_line.replace("}", ", createApiUrl}")
                        else:
                            # 默認導入，添加命名導入
                            new_import = import_line.replace(" from ", ", { createApiUrl } from ")
                        content = content.replace(import_line, new_import)
                        modifications.append(f"  - 更新導入: {new_import}")
                        import_added = True
                        break
            
            # 如果沒有找到現有配置導入，添加新的
            if not import_added:
                first_import_match = re.search(r"^import\s+", content, re.MULTILINE)
                if first_import_match:
                    import_pos = first_import_match.start()
                    new_import = "import { createApiUrl } from '../config/apiConfig';\n"
                    content = content[:import_pos] + new_import + content[import_pos:]
                    modifications.append(f"  - 添加導入: {new_import.strip()}")
                else:
                    # 在文件開頭添加
                    new_import = "import { createApiUrl } from '../config/apiConfig';\n\n"
                    content = new_import + content
                    modifications.append(f"  - 添加導入: {new_import.strip()}")
        
        # 只有在有修改時才寫入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return modifications
        else:
            return []
            
    except Exception as e:
        print(f"❌ 處理文件 {file_path} 時發生錯誤: {e}")
        return []

def main():
    """主修復函數"""
    
    print("🔧 批量修復前端API調用問題")
    print("="*60)
    
    # 基礎目錄
    frontend_dir = Path("TradingAgents/frontend/src")
    
    if not frontend_dir.exists():
        print(f"❌ 前端目錄不存在: {frontend_dir}")
        return
    
    # 需要處理的文件類型
    file_extensions = ['.tsx', '.ts', '.js']
    
    # 收集所有需要處理的文件
    files_to_process = []
    for ext in file_extensions:
        files_to_process.extend(frontend_dir.rglob(f"*{ext}"))
    
    # 排除不需要處理的文件
    excluded_patterns = [
        'node_modules',
        '.d.ts',
        'build/',
        'dist/',
        'coverage/',
        'test/',
        'spec/',
        '__tests__'
    ]
    
    filtered_files = []
    for file_path in files_to_process:
        should_exclude = False
        for pattern in excluded_patterns:
            if pattern in str(file_path):
                should_exclude = True
                break
        if not should_exclude:
            filtered_files.append(file_path)
    
    print(f"📁 發現 {len(filtered_files)} 個文件需要檢查")
    
    total_modifications = 0
    modified_files = 0
    
    for file_path in filtered_files:
        try:
            modifications = fix_api_calls_in_file(file_path)
            if modifications:
                modified_files += 1
                total_modifications += len(modifications)
                print(f"✅ 修復 {file_path.relative_to(frontend_dir)}")
                for mod in modifications:
                    print(mod)
                print()
            
        except Exception as e:
            print(f"❌ 處理文件失敗 {file_path}: {e}")
    
    print("="*60)
    print(f"📊 修復完成統計:")
    print(f"  - 檢查文件數: {len(filtered_files)}")
    print(f"  - 修改文件數: {modified_files}")
    print(f"  - 總修改數量: {total_modifications}")
    
    if modified_files > 0:
        print(f"✅ 成功修復 {modified_files} 個文件中的API調用問題")
        print(f"🔄 請重新構建並部署前端")
    else:
        print("ℹ️  沒有發現需要修復的API調用問題")

if __name__ == "__main__":
    main()