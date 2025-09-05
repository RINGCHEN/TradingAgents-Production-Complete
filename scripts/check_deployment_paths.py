#!/usr/bin/env python3
"""
部署配置路徑檢查腳本 - 檢查架構重組後的部署相關問題

檢查範圍：
- 檢查所有 Dockerfile 中的路徑引用
- 驗證部署所需的文件和目錄存在
- 檢查 requirements.txt 和其他配置文件
- 生成部署就緒報告

作者：天工 (TianGong) + Claude Code  
日期：2025-09-05
"""

import os
from pathlib import Path
from typing import List, Dict

class DeploymentPathChecker:
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).parent.parent
        self.issues = []
        self.checks_passed = 0
        self.checks_total = 0

    def check_core_files(self):
        """檢查核心部署文件"""
        print("[CORE] 檢查核心部署文件...")
        
        required_files = [
            'requirements.txt',
            'Dockerfile', 
            'tradingagents/app.py',
            'configs/data_sources.yaml'
        ]
        
        for file_path in required_files:
            self.checks_total += 1
            full_path = self.root_dir / file_path
            
            if full_path.exists():
                self.checks_passed += 1
                print(f"  [OK] {file_path} 存在")
            else:
                self.issues.append(f"缺少核心文件: {file_path}")
                print(f"  [ERR] {file_path} 不存在")

    def check_dockerfile_references(self):
        """檢查 Dockerfile 中的路徑引用"""
        print("\n[DOCKER] 檢查 Dockerfile 路徑引用...")
        
        dockerfiles = list(self.root_dir.rglob("Dockerfile*"))
        
        for dockerfile in dockerfiles:
            self.checks_total += 1
            try:
                with open(dockerfile, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查可能的問題路徑
                problematic_patterns = [
                    '../configs/',
                    '../training/', 
                    '../models/',
                    '../data/',
                    'COPY ../',
                    'ADD ../'
                ]
                
                has_issues = False
                for pattern in problematic_patterns:
                    if pattern in content:
                        has_issues = True
                        self.issues.append(f"Dockerfile {dockerfile.name} 包含問題路徑: {pattern}")
                        print(f"  [ERR] {dockerfile.relative_to(self.root_dir)} 包含: {pattern}")
                
                if not has_issues:
                    self.checks_passed += 1
                    print(f"  [OK] {dockerfile.relative_to(self.root_dir)} 路徑正常")
                    
            except Exception as e:
                self.issues.append(f"無法讀取 Dockerfile {dockerfile}: {e}")
                print(f"  [ERR] 無法讀取 {dockerfile.relative_to(self.root_dir)}: {e}")

    def check_module_imports(self):
        """檢查 Python 模組導入"""
        print("\n[IMPORTS] 檢查關鍵 Python 模組導入...")
        
        key_files = [
            'tradingagents/app.py',
            'training/technical_analyst/train_final.py',
            'scripts/analysis_tools/run_full_analysis_demo.py'
        ]
        
        for file_path in key_files:
            self.checks_total += 1
            full_path = self.root_dir / file_path
            
            if not full_path.exists():
                self.issues.append(f"關鍵文件不存在: {file_path}")
                print(f"  [ERR] {file_path} 不存在")
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查是否有新的路徑兼容性模組導入
                if 'utils.path_compatibility' in content or 'from utils.path_compatibility import' in content:
                    self.checks_passed += 1
                    print(f"  [OK] {file_path} 已使用路徑兼容性模組")
                elif 'configs/' in content or 'training/' in content:
                    # 檢查是否有相對路徑問題
                    problematic_patterns = ['../configs/', '../training/', '../models/']
                    has_issues = any(pattern in content for pattern in problematic_patterns)
                    
                    if has_issues:
                        self.issues.append(f"{file_path} 可能包含相對路徑問題")
                        print(f"  [WARN] {file_path} 可能有相對路徑問題")
                    else:
                        self.checks_passed += 1
                        print(f"  [OK] {file_path} 路徑引用看起來正常")
                else:
                    self.checks_passed += 1
                    print(f"  [OK] {file_path} 不涉及路徑問題")
                    
            except Exception as e:
                self.issues.append(f"無法分析 {file_path}: {e}")
                print(f"  [ERR] 無法分析 {file_path}: {e}")

    def check_directory_structure(self):
        """檢查目錄結構完整性"""
        print("\n[STRUCTURE] 檢查目錄結構...")
        
        required_dirs = [
            'tradingagents',
            'configs', 
            'training',
            'frontend',
            'utils'  # 新建的路徑兼容性模組目錄
        ]
        
        for dir_name in required_dirs:
            self.checks_total += 1
            dir_path = self.root_dir / dir_name
            
            if dir_path.exists() and dir_path.is_dir():
                self.checks_passed += 1
                print(f"  [OK] 目錄 {dir_name}/ 存在")
            else:
                self.issues.append(f"必要目錄不存在: {dir_name}/")
                print(f"  [ERR] 目錄 {dir_name}/ 不存在")

    def test_path_compatibility_module(self):
        """測試路徑兼容性模組"""
        print("\n[MODULE] 測試路徑兼容性模組...")
        
        self.checks_total += 1
        utils_module = self.root_dir / 'utils' / 'path_compatibility.py'
        
        if not utils_module.exists():
            self.issues.append("路徑兼容性模組不存在")
            print(f"  [ERR] utils/path_compatibility.py 不存在")
            return
            
        try:
            # 嘗試導入測試
            import sys
            sys.path.insert(0, str(self.root_dir))
            
            from utils.path_compatibility import get_config_path, get_tradingagents_root
            
            # 測試基本功能
            config_path = get_config_path('data_sources.yaml')
            root_path = get_tradingagents_root()
            
            if Path(config_path).exists():
                self.checks_passed += 1
                print(f"  [OK] 路徑兼容性模組正常工作")
                print(f"       配置路徑: {config_path}")
                print(f"       根目錄: {root_path}")
            else:
                self.issues.append("路徑兼容性模組配置路徑錯誤")
                print(f"  [WARN] 模組可導入，但配置路徑不正確")
                
        except Exception as e:
            self.issues.append(f"路徑兼容性模組測試失敗: {e}")
            print(f"  [ERR] 模組測試失敗: {e}")

    def generate_deployment_guide(self):
        """生成部署指南"""
        print("\n[GUIDE] 生成部署指南...")
        
        guide_content = f"""# TradingAgents 統一架構部署指南

## 部署檢查結果
- 檢查項目: {self.checks_total}
- 通過項目: {self.checks_passed}  
- 問題數量: {len(self.issues)}

## 發現的問題
"""
        
        if self.issues:
            for i, issue in enumerate(self.issues, 1):
                guide_content += f"{i}. {issue}\n"
        else:
            guide_content += "無問題，系統部署就緒！\n"
            
        guide_content += """
## 部署步驟 (統一架構)

### 1. 環境準備
```bash
# 確保在 TradingAgents 目錄下
cd TradingAgents

# 檢查核心文件
ls requirements.txt
ls Dockerfile
ls tradingagents/app.py
```

### 2. 本地測試
```bash
# 安裝依賴
pip install -r requirements.txt

# 測試 FastAPI 應用
uvicorn tradingagents.app:app --reload
```

### 3. Docker 構建
```bash  
# 構建鏡像
docker build -t tradingagents:latest .

# 運行容器
docker run -p 8000:8000 tradingagents:latest
```

### 4. DigitalOcean 部署
```bash
# 推送代碼 (自動觸發部署)
git add .
git commit -m "deploy: 統一架構部署更新"  
git push origin main
```

## 路徑兼容性
- 使用 `from utils.path_compatibility import get_config_path` 導入
- 所有配置和訓練文件路徑自動解析
- 支援多種執行環境 (開發/容器/雲端)

## 注意事項
- 所有腳本必須從 TradingAgents/ 目錄執行
- 使用路徑兼容性模組確保路徑正確
- 部署前確保所有問題已解決
"""

        guide_path = self.root_dir / 'DEPLOYMENT_GUIDE_UNIFIED_ARCHITECTURE.md'
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
            
        print(f"  [OK] 部署指南已生成: {guide_path.name}")

    def run_all_checks(self):
        """執行所有檢查"""
        print("[START] TradingAgents 統一架構部署檢查...\n")
        
        self.check_core_files()
        self.check_dockerfile_references() 
        self.check_module_imports()
        self.check_directory_structure()
        self.test_path_compatibility_module()
        self.generate_deployment_guide()
        
        self.print_summary()

    def print_summary(self):
        """列印檢查總結"""
        print(f"\n[COMPLETE] 部署檢查完成！")
        print(f"[STATS] 檢查統計:")
        print(f"  - 檢查項目: {self.checks_total}")
        print(f"  - 通過項目: {self.checks_passed}")
        print(f"  - 成功率: {(self.checks_passed/self.checks_total*100):.1f}%")
        
        if self.issues:
            print(f"\n[ISSUES] 發現問題:")
            for issue in self.issues:
                print(f"  - {issue}")
        else:
            print(f"\n[SUCCESS] 無問題發現，系統部署就緒！")

if __name__ == "__main__":
    checker = DeploymentPathChecker()
    checker.run_all_checks()