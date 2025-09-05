#!/usr/bin/env python3
"""
後端API功能掃描器
BackendAPIScanner - 掃描所有管理相關的API端點
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """API端點信息"""
    path: str
    method: str
    function_name: str
    description: str = ""
    parameters: List[str] = None
    response_format: str = ""
    category: str = "unknown"
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []

@dataclass
class APICategory:
    """API分類信息"""
    name: str
    description: str
    endpoints: List[APIEndpoint] = None
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = []

class BackendAPIScanner:
    """後端API掃描器"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.api_endpoints = []
        self.api_categories = {}
        
        # API分類定義
        self.category_patterns = {
            'analytics': {
                'description': '數據分析API',
                'patterns': [
                    r'/analytics',
                    r'/dashboard',
                    r'/stats',
                    r'/metrics',
                    r'/reports'
                ]
            },
            'user_management': {
                'description': '用戶管理API',
                'patterns': [
                    r'/users',
                    r'/members',
                    r'/auth',
                    r'/login',
                    r'/register'
                ]
            },
            'content': {
                'description': '內容管理API',
                'patterns': [
                    r'/content',
                    r'/articles',
                    r'/posts',
                    r'/media'
                ]
            },
            'financial': {
                'description': '財務管理API',
                'patterns': [
                    r'/payment',
                    r'/billing',
                    r'/subscription',
                    r'/financial'
                ]
            },
            'system': {
                'description': '系統管理API',
                'patterns': [
                    r'/admin',
                    r'/config',
                    r'/settings',
                    r'/health',
                    r'/system'
                ]
            }
        }
        
        # API端點識別模式
        self.endpoint_patterns = [
            # FastAPI patterns
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            # Flask patterns
            r'@app\.route\(["\']([^"\']+)["\'].*methods=\[([^\]]+)\]',
            r'@bp\.route\(["\']([^"\']+)["\'].*methods=\[([^\]]+)\]',
            # Django patterns
            r'path\(["\']([^"\']+)["\']',
            r'url\(r["\']([^"\']+)["\']',
        ]
    
    def scan_backend_files(self) -> List[str]:
        """掃描後端文件"""
        logger.info("開始掃描後端API文件...")
        
        backend_files = []
        
        # 掃描TradingAgents目錄
        trading_agents_dir = self.workspace_root / "TradingAgents"
        if trading_agents_dir.exists():
            # 掃描Python文件
            for pattern in ["*.py", "**/*.py"]:
                for file_path in trading_agents_dir.glob(pattern):
                    if file_path.is_file() and self._is_api_file(file_path):
                        backend_files.append(str(file_path))
                        logger.info(f"找到API文件: {file_path}")
        
        # 掃描根目錄的API文件
        for file_path in self.workspace_root.glob("*.py"):
            if file_path.is_file() and self._is_api_file(file_path):
                backend_files.append(str(file_path))
                logger.info(f"找到API文件: {file_path}")
        
        logger.info(f"總共找到 {len(backend_files)} 個後端API文件")
        return backend_files
    
    def _is_api_file(self, file_path: Path) -> bool:
        """判斷是否為API文件"""
        # 排除測試文件和其他非API文件
        if any(exclude in str(file_path).lower() for exclude in ['test_', '__pycache__', '.pyc']):
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 檢查是否包含API相關關鍵字
                api_keywords = [
                    '@app.', '@router.', '@bp.', 'FastAPI', 'Flask',
                    'def get_', 'def post_', 'def put_', 'def delete_',
                    'APIRouter', 'Blueprint'
                ]
                return any(keyword in content for keyword in api_keywords)
        except:
            return False
    
    def extract_api_endpoints(self, file_path: str) -> List[APIEndpoint]:
        """從文件中提取API端點"""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            logger.warning(f"無法讀取文件: {file_path}")
            return endpoints
        
        # 使用正則表達式提取API端點
        for pattern in self.endpoint_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                if len(match.groups()) >= 2:
                    if 'methods=' in pattern:
                        # Flask style
                        path = match.group(1)
                        methods = match.group(2).replace('"', '').replace("'", "").split(',')
                        for method in methods:
                            method = method.strip()
                            endpoint = self._create_endpoint(path, method, file_path, content)
                            if endpoint:
                                endpoints.append(endpoint)
                    else:
                        # FastAPI style
                        method = match.group(1).upper()
                        path = match.group(2)
                        endpoint = self._create_endpoint(path, method, file_path, content)
                        if endpoint:
                            endpoints.append(endpoint)
        
        return endpoints
    
    def _create_endpoint(self, path: str, method: str, file_path: str, content: str) -> Optional[APIEndpoint]:
        """創建API端點對象"""
        # 查找函數名
        function_name = self._extract_function_name(path, method, content)
        
        # 分類API
        category = self._categorize_endpoint(path)
        
        # 提取參數
        parameters = self._extract_parameters(path, content)
        
        # 生成描述
        description = self._generate_description(path, method, function_name)
        
        endpoint = APIEndpoint(
            path=path,
            method=method,
            function_name=function_name,
            description=description,
            parameters=parameters,
            category=category
        )
        
        return endpoint
    
    def _extract_function_name(self, path: str, method: str, content: str) -> str:
        """提取函數名"""
        # 簡化的函數名提取邏輯
        path_parts = path.strip('/').split('/')
        if path_parts:
            base_name = path_parts[-1].replace('{', '').replace('}', '')
            if base_name:
                return f"{method.lower()}_{base_name}"
        
        return f"{method.lower()}_endpoint"
    
    def _categorize_endpoint(self, path: str) -> str:
        """對API端點進行分類"""
        for category, info in self.category_patterns.items():
            for pattern in info['patterns']:
                if re.search(pattern, path, re.IGNORECASE):
                    return category
        
        return 'unknown'
    
    def _extract_parameters(self, path: str, content: str) -> List[str]:
        """提取API參數"""
        parameters = []
        
        # 從路徑中提取路徑參數
        path_params = re.findall(r'\{([^}]+)\}', path)
        parameters.extend(path_params)
        
        # 從內容中提取查詢參數（簡化版）
        query_params = re.findall(r'request\.args\.get\(["\']([^"\']+)["\']', content)
        parameters.extend(query_params)
        
        return list(set(parameters))  # 去重
    
    def _generate_description(self, path: str, method: str, function_name: str) -> str:
        """生成API描述"""
        action_map = {
            'GET': '獲取',
            'POST': '創建',
            'PUT': '更新',
            'DELETE': '刪除',
            'PATCH': '修改'
        }
        
        action = action_map.get(method, method)
        resource = path.strip('/').split('/')[-1] or 'resource'
        
        return f"{action}{resource}信息"
    
    def scan_all_apis(self) -> Dict[str, List[APIEndpoint]]:
        """掃描所有API"""
        logger.info("開始掃描所有後端API...")
        
        # 掃描文件
        backend_files = self.scan_backend_files()
        
        # 提取API端點
        all_endpoints = []
        for file_path in backend_files:
            endpoints = self.extract_api_endpoints(file_path)
            all_endpoints.extend(endpoints)
        
        # 按分類組織
        categorized_apis = {}
        for endpoint in all_endpoints:
            category = endpoint.category
            if category not in categorized_apis:
                categorized_apis[category] = []
            categorized_apis[category].append(endpoint)
        
        self.api_endpoints = all_endpoints
        logger.info(f"總共找到 {len(all_endpoints)} 個API端點")
        
        return categorized_apis
    
    def generate_api_report(self, output_file: str = "backend_api_analysis_report.json") -> str:
        """生成API分析報告"""
        if not self.api_endpoints:
            logger.warning("沒有API端點數據可導出")
            return ""
        
        # 按分類組織數據
        categorized_apis = {}
        for endpoint in self.api_endpoints:
            category = endpoint.category
            if category not in categorized_apis:
                categorized_apis[category] = []
            categorized_apis[category].append(asdict(endpoint))
        
        # 生成統計信息
        stats = {
            'total_endpoints': len(self.api_endpoints),
            'categories': {},
            'methods': {}
        }
        
        for endpoint in self.api_endpoints:
            # 分類統計
            category = endpoint.category
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # 方法統計
            method = endpoint.method
            stats['methods'][method] = stats['methods'].get(method, 0) + 1
        
        # 準備導出數據
        export_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'workspace_root': str(self.workspace_root),
            'statistics': stats,
            'categories': categorized_apis,
            'category_descriptions': {
                name: info['description'] 
                for name, info in self.category_patterns.items()
            }
        }
        
        # 寫入文件
        output_path = self.workspace_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"API分析報告已導出到: {output_path}")
        return str(output_path)
    
    def print_api_summary(self):
        """打印API摘要"""
        if not self.api_endpoints:
            print("沒有找到API端點")
            return
        
        print("\n" + "="*60)
        print("後端API功能掃描摘要")
        print("="*60)
        
        # 統計信息
        total_endpoints = len(self.api_endpoints)
        categories = {}
        methods = {}
        
        for endpoint in self.api_endpoints:
            categories[endpoint.category] = categories.get(endpoint.category, 0) + 1
            methods[endpoint.method] = methods.get(endpoint.method, 0) + 1
        
        print(f"總API端點數: {total_endpoints}")
        print(f"API分類數: {len(categories)}")
        
        print("\n分類統計:")
        print("-" * 40)
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            description = self.category_patterns.get(category, {}).get('description', category)
            print(f"{description}: {count} 個端點")
        
        print("\n方法統計:")
        print("-" * 40)
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            print(f"{method}: {count} 個端點")
        
        print("\n詳細端點列表:")
        print("-" * 60)
        for category, endpoints in self._group_endpoints_by_category().items():
            description = self.category_patterns.get(category, {}).get('description', category)
            print(f"\n{description} ({category}):")
            for endpoint in endpoints:
                print(f"  {endpoint.method} {endpoint.path} - {endpoint.description}")
    
    def _group_endpoints_by_category(self) -> Dict[str, List[APIEndpoint]]:
        """按分類分組端點"""
        grouped = {}
        for endpoint in self.api_endpoints:
            category = endpoint.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(endpoint)
        
        return grouped

def main():
    """主函數"""
    print("後端API功能掃描器")
    print("=" * 40)
    
    # 創建掃描器
    scanner = BackendAPIScanner()
    
    # 執行掃描
    try:
        categorized_apis = scanner.scan_all_apis()
        
        # 打印摘要
        scanner.print_api_summary()
        
        # 導出報告
        report_file = scanner.generate_api_report()
        print(f"\n詳細報告已保存到: {report_file}")
        
    except Exception as e:
        logger.error(f"掃描過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()