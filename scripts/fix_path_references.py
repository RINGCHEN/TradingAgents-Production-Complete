#!/usr/bin/env python3
"""
路徑引用修復腳本 - 修復架構重組後的路徑問題
系統重組後，所有配置和模型路徑從相對根目錄變為 TradingAgents/ 內部路徑

執行範圍：
- 修復所有 Python 文件中的 configs/, training/, models/, data/ 路徑引用
- 更新 JSON/YAML 配置文件中的路徑
- 修正部署配置文件
- 保持相容性和向下兼容

作者：天工 (TianGong) + Claude Code
日期：2025-09-05
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class PathReferenceFixer:
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).parent.parent
        self.tradingagents_dir = self.root_dir
        
        # 統計信息
        self.stats = {
            'files_processed': 0,
            'references_fixed': 0,
            'files_with_changes': 0,
            'errors': []
        }
        
        # 路徑映射規則
        self.path_mappings = {
            # 配置文件路徑 (相對於 TradingAgents/)
            r"configs/": "configs/",
            r"training/": "training/",  
            r"models/": "models/",
            r"data/": "data/",
            
            # 絕對路徑引用 (需要確保從 TradingAgents/ 目錄執行)
            r"\.\.\/configs\/": "configs/",
            r"\.\.\/training\/": "training/",
            r"\.\.\/models\/": "models/",
            r"\.\.\/data\/": "data/",
        }

    def fix_python_files(self):
        """修復 Python 文件中的路徑引用"""
        print("[FIX] 修復 Python 文件中的路徑引用...")
        
        python_files = list(self.tradingagents_dir.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 修復各種路徑引用
                content = self._fix_config_paths(content)
                content = self._fix_relative_paths(content)
                content = self._add_working_directory_check(content, py_file)
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.stats['files_with_changes'] += 1
                    print(f"  [OK] 修復: {py_file.relative_to(self.tradingagents_dir)}")
                
                self.stats['files_processed'] += 1
                
            except Exception as e:
                self.stats['errors'].append(f"處理 {py_file} 時發生錯誤: {e}")
                print(f"  [ERR] 錯誤: {py_file.relative_to(self.tradingagents_dir)} - {e}")

    def fix_config_files(self):
        """修復配置文件中的路徑引用"""
        print("\n[CONFIG] 修復配置文件中的路徑引用...")
        
        config_patterns = ["*.json", "*.yaml", "*.yml"]
        
        for pattern in config_patterns:
            config_files = list(self.tradingagents_dir.rglob(pattern))
            
            for config_file in config_files:
                if self._should_skip_file(config_file):
                    continue
                    
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 修復配置文件中的路徑引用
                    content = self._fix_config_file_paths(content)
                    
                    if content != original_content:
                        with open(config_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.stats['files_with_changes'] += 1
                        print(f"  [OK] 修復: {config_file.relative_to(self.tradingagents_dir)}")
                    
                    self.stats['files_processed'] += 1
                    
                except Exception as e:
                    self.stats['errors'].append(f"處理 {config_file} 時發生錯誤: {e}")
                    print(f"  [ERR] 錯誤: {config_file.relative_to(self.tradingagents_dir)} - {e}")

    def _fix_config_paths(self, content: str) -> str:
        """修復代碼中的配置路徑"""
        # 修復常見的配置路徑引用
        patterns = [
            # 直接字符串路徑
            (r"['\"]configs/([^'\"]+)['\"]", r'"configs/\1"'),
            (r"['\"]training/([^'\"]+)['\"]", r'"training/\1"'),
            (r"['\"]models/([^'\"]+)['\"]", r'"models/\1"'),
            (r"['\"]data/([^'\"]+)['\"]", r'"data/\1"'),
            
            # os.path.join 路徑
            (r"os\.path\.join\([^)]*['\"]configs['\"][^)]*\)", self._fix_os_path_join),
            (r"os\.path\.join\([^)]*['\"]training['\"][^)]*\)", self._fix_os_path_join),
            (r"os\.path\.join\([^)]*['\"]models['\"][^)]*\)", self._fix_os_path_join),
            (r"os\.path\.join\([^)]*['\"]data['\"][^)]*\)", self._fix_os_path_join),
        ]
        
        for pattern, replacement in patterns:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)
                
        return content

    def _fix_relative_paths(self, content: str) -> str:
        """修復相對路徑引用"""
        # 修復 ../ 路徑引用
        replacements = [
            (r'\.\./\.\./configs/', 'configs/'),
            (r'\.\./\.\./training/', 'training/'),
            (r'\.\./\.\./models/', 'models/'),  
            (r'\.\./\.\./data/', 'data/'),
            (r'\.\./configs/', 'configs/'),
            (r'\.\./training/', 'training/'),
            (r'\.\./models/', 'models/'),
            (r'\.\./data/', 'data/'),
        ]
        
        for old_path, new_path in replacements:
            content = content.replace(old_path, new_path)
            
        return content

    def _add_working_directory_check(self, content: str, py_file: Path) -> str:
        """添加工作目錄檢查和自動切換"""
        # 對於需要訪問 configs/, training/ 等目錄的文件，添加目錄檢查
        if any(path in content for path in ['configs/', 'training/', 'models/', 'data/']):
            if 'import os' not in content and 'from pathlib import Path' not in content:
                # 添加必要的 import
                if 'import ' in content:
                    content = re.sub(r'^(import [^\n]+\n)', r'\1import os\nfrom pathlib import Path\n', content, flags=re.MULTILINE)
                else:
                    content = 'import os\nfrom pathlib import Path\n\n' + content
            
            # 添加工作目錄檢查函數
            dir_check_code = '''
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

'''
            
            # 如果還沒有添加過這個檢查，就添加
            if 'ensure_tradingagents_directory' not in content:
                # 在主要代碼之前添加
                if 'if __name__ == "__main__"' in content:
                    content = content.replace('if __name__ == "__main__"', dir_check_code + 'if __name__ == "__main__"')
                else:
                    # 在文件末尾添加
                    content = content + '\n\n' + dir_check_code
        
        return content

    def _fix_config_file_paths(self, content: str) -> str:
        """修復配置文件中的路徑"""
        # JSON/YAML 文件中的路徑通常已經是相對的，主要檢查是否需要調整
        replacements = [
            (r'"\.\.\/configs\/', '"configs/'),
            (r'"\.\.\/training\/', '"training/'),  
            (r'"\.\.\/models\/', '"models/'),
            (r'"\.\.\/data\/', '"data/'),
        ]
        
        for old_path, new_path in replacements:
            content = re.sub(old_path, new_path, content)
            
        return content

    def _fix_os_path_join(self, match):
        """修復 os.path.join 調用"""
        original = match.group(0)
        # 保持 os.path.join 的結構，只修復路徑
        return original.replace('../', '')

    def _should_skip_file(self, file_path: Path) -> bool:
        """判斷是否應該跳過某個文件"""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.venv',
            'node_modules',
            '.pytest_cache',
            'legacy_html',
            'fix_path_references.py'  # 跳過自己
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def create_path_compatibility_module(self):
        """創建路徑兼容性模組"""
        print("\n[MODULE] 創建路徑兼容性模組...")
        
        compatibility_code = '''"""
路徑兼容性模組 - TradingAgents 統一架構

提供向後兼容的路徑解析功能，確保所有模組能正確找到配置文件、模型文件等。

使用方法:
    from utils.path_compatibility import get_config_path, get_model_path, get_data_path
    
    config_path = get_config_path('data_sources.yaml')
    model_path = get_model_path('technical_analyst/config.yaml')
"""

import os
from pathlib import Path
from typing import Union

class TradingAgentsPath:
    """TradingAgents 路徑解析器"""
    
    def __init__(self):
        self._tradingagents_root = self._find_tradingagents_root()
        
    def _find_tradingagents_root(self) -> Path:
        """自動尋找 TradingAgents 根目錄"""
        current = Path.cwd()
        
        # 檢查當前目錄
        if self._is_tradingagents_root(current):
            return current
            
        # 檢查是否在 TradingAgents 的子目錄
        for parent in current.parents:
            if parent.name == 'TradingAgents' and self._is_tradingagents_root(parent):
                return parent
                
        # 檢查當前目錄下是否有 TradingAgents
        tradingagents_dir = current / 'TradingAgents'
        if tradingagents_dir.exists() and self._is_tradingagents_root(tradingagents_dir):
            return tradingagents_dir
            
        raise FileNotFoundError("無法找到 TradingAgents 根目錄")
        
    def _is_tradingagents_root(self, path: Path) -> bool:
        """檢查是否為 TradingAgents 根目錄"""
        required_items = ['tradingagents', 'configs', 'training']
        return all((path / item).exists() for item in required_items)
        
    def get_config_path(self, config_file: str) -> Path:
        """獲取配置文件路徑"""
        return self._tradingagents_root / 'configs' / config_file
        
    def get_training_path(self, training_file: str) -> Path:
        """獲取訓練配置路徑"""
        return self._tradingagents_root / 'training' / training_file
        
    def get_model_path(self, model_file: str) -> Path:
        """獲取模型文件路徑"""
        return self._tradingagents_root / 'models' / model_file
        
    def get_data_path(self, data_file: str) -> Path:
        """獲取數據文件路徑"""
        return self._tradingagents_root / 'data' / data_file
        
    def get_root_path(self) -> Path:
        """獲取 TradingAgents 根目錄路徑"""
        return self._tradingagents_root

# 全局路徑解析器實例
_path_resolver = TradingAgentsPath()

# 便利函數
def get_config_path(config_file: str) -> str:
    """獲取配置文件路徑 (字符串)"""
    return str(_path_resolver.get_config_path(config_file))

def get_training_path(training_file: str) -> str:
    """獲取訓練配置路徑 (字符串)"""
    return str(_path_resolver.get_training_path(training_file))

def get_model_path(model_file: str) -> str:
    """獲取模型文件路徑 (字符串)"""  
    return str(_path_resolver.get_model_path(model_file))

def get_data_path(data_file: str) -> str:
    """獲取數據文件路徑 (字符串)"""
    return str(_path_resolver.get_data_path(data_file))

def get_tradingagents_root() -> str:
    """獲取 TradingAgents 根目錄路徑 (字符串)"""
    return str(_path_resolver.get_root_path())

def ensure_tradingagents_cwd():
    """確保當前工作目錄為 TradingAgents 根目錄"""
    root_path = _path_resolver.get_root_path()
    if Path.cwd() != root_path:
        os.chdir(root_path)
        print(f"[DIR] 切換工作目錄到: {root_path}")
'''
        
        utils_dir = self.tradingagents_dir / 'utils'
        utils_dir.mkdir(exist_ok=True)
        
        # 創建 __init__.py
        (utils_dir / '__init__.py').touch()
        
        # 創建路徑兼容性模組
        with open(utils_dir / 'path_compatibility.py', 'w', encoding='utf-8') as f:
            f.write(compatibility_code)
            
        print(f"  [OK] 創建: utils/path_compatibility.py")

    def run_all_fixes(self):
        """執行所有修復"""
        print("[START] 開始修復 TradingAgents 架構重組後的路徑引用問題...\n")
        
        # 創建路徑兼容性模組
        self.create_path_compatibility_module()
        
        # 修復 Python 文件
        self.fix_python_files()
        
        # 修復配置文件
        self.fix_config_files()
        
        # 顯示統計結果
        self.print_summary()

    def print_summary(self):
        """顯示修復統計結果"""
        print(f"\n[COMPLETE] 路徑引用修復完成！")
        print(f"[STATS] 統計結果:")
        print(f"  - 處理文件數: {self.stats['files_processed']}")
        print(f"  - 修改文件數: {self.stats['files_with_changes']}")
        print(f"  - 修復引用數: {self.stats['references_fixed']}")
        
        if self.stats['errors']:
            print(f"\n[WARNING] 發生錯誤: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # 只顯示前5個錯誤
                print(f"  - {error}")

if __name__ == "__main__":
    fixer = PathReferenceFixer()
    fixer.run_all_fixes()