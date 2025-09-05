#!/usr/bin/env python3
"""
前端API整合狀態分析器 - 增強版
FrontendAPIIntegrationAnalyzer - 專門分析admin_ultimate.html中mock數據與真實API端點的對比
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MockDataStructure:
    """Mock數據結構"""
    name: str
    fields: List[str]
    sample_data: Any
    usage_context: str
    api_suggestions: List[str]

@dataclass
class APIEndpointMapping:
    """API端點映射"""
    mock_endpoint: str
    real_endpoint: str
    method: str
    match_score: float
    category: str
    priority: int  # 1=高, 2=中, 3=低
    implementation_complexity: str  # simple, medium, complex
    dependencies: List[str]

@dataclass
class APIIntegration:
    """API整合信息"""
    endpoint: str
    method: str
    integration_status: str  # integrated, partial, missing, mock_only
    frontend_usage_count: int = 0
    implementation_quality: str = "unknown"  # good, fair, poor, unknown
    error_handling: bool = False
    loading_states: bool = False
    mock_data_used: bool = False

@dataclass
class FrontendAPIAnalysis:
    """前端API分析結果"""
    version_name: str
    total_api_calls: int
    integrated_apis: List[APIIntegration]
    missing_apis: List[str]
    api_coverage_rate: float
    integration_quality_score: float
    mock_data_structures: List[MockDataStructure] = None
    api_mappings: List[APIEndpointMapping] = None

class FrontendAPIIntegrationAnalyzer:
    """前端API整合狀態分析器 - 增強版"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.backend_apis = []
        self.frontend_versions = {}
        self.integration_results = {}
        self.mock_data_structures = []
        self.api_mappings = []
        
        # API調用模式
        self.api_call_patterns = [
            # Fetch API patterns
            r'fetch\(["\']([^"\']+)["\']',
            r'fetch\(`([^`]+)`',
            # Axios patterns
            r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'axios\(["\']([^"\']+)["\']',
            # jQuery AJAX patterns
            r'\$\.ajax\({[^}]*url:\s*["\']([^"\']+)["\']',
            r'\$\.(get|post|put|delete)\(["\']([^"\']+)["\']',
            # XMLHttpRequest patterns
            r'\.open\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']',
        ]
        
        # 錯誤處理模式
        self.error_handling_patterns = [
            r'\.catch\(',
            r'try\s*{.*?catch',
            r'error\s*:',
            r'onError',
            r'\.fail\(',
        ]
        
        # 載入狀態模式
        self.loading_patterns = [
            r'loading',
            r'isLoading',
            r'spinner',
            r'Loading',
            r'載入',
        ]
        
        # Mock數據結構模式
        self.mock_data_patterns = [
            r'const\s+mockData\s*=\s*\{([^}]+)\}',  # const mockData = {...}
            r'mockData\s*=\s*\{([^}]+)\}',  # mockData = {...}
            r'let\s+mockData\s*=\s*\{([^}]+)\}',  # let mockData = {...}
        ]
        
        # API端點優先級分類
        self.api_priority_categories = {
            'authentication': {'priority': 1, 'keywords': ['auth', 'login', 'token', 'user']},
            'user_management': {'priority': 1, 'keywords': ['users', 'profile', 'account']},
            'system_health': {'priority': 2, 'keywords': ['health', 'status', 'system']},
            'analytics': {'priority': 2, 'keywords': ['stats', 'analytics', 'report']},
            'configuration': {'priority': 2, 'keywords': ['config', 'settings', 'admin']},
            'content_management': {'priority': 3, 'keywords': ['content', 'data', 'stock']},
        }
    
    def extract_mock_data_structures(self, file_path: str) -> List[MockDataStructure]:
        """從admin_ultimate.html提取mock數據結構"""
        logger.info(f"分析文件中的mock數據結構: {file_path}")
        
        mock_structures = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            logger.warning(f"無法讀取文件: {file_path}")
            return []
        
        # 提取完整的mockData對象
        mock_data_match = re.search(r'const\s+mockData\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', content, re.DOTALL)
        
        if mock_data_match:
            mock_content = mock_data_match.group(1)
            
            # 分析各個數據結構
            structures = self._parse_mock_data_content(mock_content)
            mock_structures.extend(structures)
        
        # 分析數據使用上下文
        for structure in mock_structures:
            structure.usage_context = self._analyze_usage_context(content, structure.name)
            structure.api_suggestions = self._suggest_apis_for_mock_data(structure)
        
        logger.info(f"發現 {len(mock_structures)} 個mock數據結構")
        return mock_structures
    
    def _parse_mock_data_content(self, mock_content: str) -> List[MockDataStructure]:
        """解析mock數據內容"""
        structures = []
        
        # 正則匹配各個屬性
        property_pattern = r'(\w+):\s*({[^{}]*(?:{[^{}]*}[^{}]*)*}|\[[^\]]*\]|[^,}]+)'
        
        matches = re.finditer(property_pattern, mock_content, re.DOTALL)
        
        for match in matches:
            property_name = match.group(1).strip()
            property_value = match.group(2).strip()
            
            # 解析字段和樣本數據
            fields = self._extract_fields_from_value(property_value)
            sample_data = self._extract_sample_data(property_value)
            
            structure = MockDataStructure(
                name=property_name,
                fields=fields,
                sample_data=sample_data,
                usage_context="",
                api_suggestions=[]
            )
            
            structures.append(structure)
        
        return structures
    
    def _extract_fields_from_value(self, value: str) -> List[str]:
        """從值中提取字段名稱"""
        fields = []
        
        if value.strip().startswith('{'):
            # 對象類型
            field_matches = re.finditer(r'(\w+):', value)
            fields = [match.group(1) for match in field_matches]
        elif value.strip().startswith('['):
            # 數組類型，提取第一個元素的字段
            array_content = value.strip()[1:-1]
            if '{' in array_content:
                first_object_match = re.search(r'\{([^}]+)\}', array_content)
                if first_object_match:
                    object_content = first_object_match.group(1)
                    field_matches = re.finditer(r'(\w+):', object_content)
                    fields = [match.group(1) for match in field_matches]
        
        return fields
    
    def _extract_sample_data(self, value: str) -> Any:
        """提取樣本數據"""
        try:
            # 簡單的JSON解析嘗試
            if value.strip().startswith('{') or value.strip().startswith('['):
                # 清理JavaScript語法為JSON
                json_str = re.sub(r"'", '"', value)
                json_str = re.sub(r'(\w+):', r'"\1":', json_str)
                return json.loads(json_str)
        except:
            pass
        
        return value
    
    def _analyze_usage_context(self, content: str, structure_name: str) -> str:
        """分析數據結構的使用上下文"""
        contexts = []
        
        # 搜索使用該結構的地方
        usage_pattern = rf'mockData\.{structure_name}'
        matches = re.finditer(usage_pattern, content)
        
        for match in matches:
            # 獲取前後文
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            
            # 提取組件或函數名
            component_match = re.search(r'const\s+(\w+)\s*=', context)
            if component_match:
                contexts.append(component_match.group(1))
        
        return ', '.join(set(contexts))
    
    def _suggest_apis_for_mock_data(self, structure: MockDataStructure) -> List[str]:
        """為mock數據結構建議對應的API端點"""
        suggestions = []
        
        # 基於結構名稱的建議
        name_mappings = {
            'systemStats': ['/api/system/stats', '/admin/system/overview', '/api/dashboard/stats'],
            'users': ['/api/users', '/admin/users', '/api/user/list'],
            'apiEndpoints': ['/api/system/endpoints', '/admin/api/status', '/api/monitoring/endpoints'],
            'systemConfig': ['/api/system/config', '/admin/config', '/api/settings'],
            'activities': ['/api/system/activities', '/admin/logs', '/api/audit/activities']
        }
        
        if structure.name in name_mappings:
            suggestions.extend(name_mappings[structure.name])
        
        # 基於字段的建議
        for field in structure.fields:
            if 'user' in field.lower():
                suggestions.extend(['/api/users', '/api/user/profile'])
            elif 'config' in field.lower() or 'setting' in field.lower():
                suggestions.extend(['/api/config', '/api/settings'])
            elif 'stat' in field.lower() or 'metric' in field.lower():
                suggestions.extend(['/api/stats', '/api/metrics'])
        
        return list(set(suggestions))
    
    def create_api_endpoint_mappings(self, mock_structures: List[MockDataStructure]) -> List[APIEndpointMapping]:
        """創建API端點映射"""
        mappings = []
        
        for mock_structure in mock_structures:
            for suggested_api in mock_structure.api_suggestions:
                # 尋找最匹配的真實API端點
                best_match = self._find_best_api_match(suggested_api)
                
                if best_match:
                    priority = self._calculate_api_priority(mock_structure.name, best_match)
                    complexity = self._estimate_implementation_complexity(mock_structure, best_match)
                    dependencies = self._identify_dependencies(mock_structure.name)
                    
                    mapping = APIEndpointMapping(
                        mock_endpoint=f"mockData.{mock_structure.name}",
                        real_endpoint=best_match['path'],
                        method=best_match['method'],
                        match_score=0.8,  # 可以進一步優化
                        category=best_match['category'],
                        priority=priority,
                        implementation_complexity=complexity,
                        dependencies=dependencies
                    )
                    
                    mappings.append(mapping)
        
        return mappings
    
    def _find_best_api_match(self, suggested_api: str) -> Optional[Dict]:
        """尋找最佳的API匹配"""
        best_match = None
        best_score = 0
        
        for api in self.backend_apis:
            score = self._calculate_api_similarity(suggested_api, api['path'])
            if score > best_score:
                best_score = score
                best_match = api
        
        return best_match if best_score > 0.3 else None
    
    def _calculate_api_similarity(self, suggested: str, real: str) -> float:
        """計算API相似度"""
        suggested_parts = suggested.lower().split('/')
        real_parts = real.lower().split('/')
        
        common_parts = 0
        max_parts = max(len(suggested_parts), len(real_parts))
        
        for i in range(min(len(suggested_parts), len(real_parts))):
            if suggested_parts[i] in real_parts[i] or real_parts[i] in suggested_parts[i]:
                common_parts += 1
        
        return common_parts / max_parts if max_parts > 0 else 0
    
    def _calculate_api_priority(self, mock_name: str, api_info: Dict) -> int:
        """計算API優先級"""
        for category, config in self.api_priority_categories.items():
            keywords = config['keywords']
            if any(keyword in mock_name.lower() for keyword in keywords):
                return config['priority']
            if any(keyword in api_info['path'].lower() for keyword in keywords):
                return config['priority']
        
        return 3  # 默認低優先級
    
    def _estimate_implementation_complexity(self, mock_structure: MockDataStructure, api_info: Dict) -> str:
        """估計實施複雜度"""
        field_count = len(mock_structure.fields)
        
        if field_count <= 3:
            return 'simple'
        elif field_count <= 8:
            return 'medium'
        else:
            return 'complex'
    
    def _identify_dependencies(self, mock_name: str) -> List[str]:
        """識別依賴關係"""
        dependencies = []
        
        dependency_map = {
            'users': ['authentication', 'authorization'],
            'systemStats': ['monitoring', 'metrics_collection'],
            'systemConfig': ['authentication', 'admin_privileges'],
            'activities': ['logging', 'audit_system'],
            'apiEndpoints': ['monitoring', 'health_check']
        }
        
        return dependency_map.get(mock_name, [])
    
    def analyze_admin_ultimate_integration(self) -> Dict[str, Any]:
        """專門分析admin_ultimate.html的API整合狀態"""
        logger.info("開始分析admin_ultimate.html的API整合狀態")
        
        # 載入後端API數據
        self.load_backend_apis()
        
        admin_ultimate_path = self.workspace_root / "admin_ultimate.html"
        
        # 提取mock數據結構
        mock_structures = self.extract_mock_data_structures(str(admin_ultimate_path))
        self.mock_data_structures = mock_structures
        
        # 創建API映射
        api_mappings = self.create_api_endpoint_mappings(mock_structures)
        self.api_mappings = api_mappings
        
        # 分析結果
        result = {
            'analysis_timestamp': datetime.now().isoformat(),
            'target_file': str(admin_ultimate_path),
            'mock_data_analysis': {
                'total_structures': len(mock_structures),
                'structures': [asdict(s) for s in mock_structures]
            },
            'api_mapping_analysis': {
                'total_mappings': len(api_mappings),
                'high_priority_count': len([m for m in api_mappings if m.priority == 1]),
                'medium_priority_count': len([m for m in api_mappings if m.priority == 2]),
                'low_priority_count': len([m for m in api_mappings if m.priority == 3]),
                'mappings': [asdict(m) for m in api_mappings]
            },
            'integration_recommendations': self._generate_integration_recommendations(api_mappings),
            'priority_implementation_plan': self._generate_priority_plan(api_mappings)
        }
        
        logger.info(f"分析完成: 發現 {len(mock_structures)} 個mock數據結構, {len(api_mappings)} 個API映射")
        
        return result
    
    def _generate_integration_recommendations(self, mappings: List[APIEndpointMapping]) -> List[Dict[str, Any]]:
        """生成整合建議"""
        recommendations = []
        
        # 按優先級和複雜度分組
        priority_groups = defaultdict(list)
        for mapping in mappings:
            priority_groups[mapping.priority].append(mapping)
        
        for priority in sorted(priority_groups.keys()):
            group_mappings = priority_groups[priority]
            
            recommendation = {
                'priority_level': priority,
                'priority_name': {1: '高優先級', 2: '中優先級', 3: '低優先級'}[priority],
                'total_apis': len(group_mappings),
                'simple_apis': len([m for m in group_mappings if m.implementation_complexity == 'simple']),
                'medium_apis': len([m for m in group_mappings if m.implementation_complexity == 'medium']),
                'complex_apis': len([m for m in group_mappings if m.implementation_complexity == 'complex']),
                'recommended_order': [
                    f"{m.mock_endpoint} -> {m.real_endpoint}"
                    for m in sorted(group_mappings, key=lambda x: len(x.dependencies))
                ]
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_priority_plan(self, mappings: List[APIEndpointMapping]) -> Dict[str, Any]:
        """生成優先級實施計劃"""
        high_priority = [m for m in mappings if m.priority == 1]
        
        plan = {
            'immediate_actions': [
                f"實施 {m.real_endpoint} ({m.method})"
                for m in high_priority
                if m.implementation_complexity == 'simple'
            ],
            'short_term_goals': [
                f"實施 {m.real_endpoint} ({m.method})"
                for m in high_priority
                if m.implementation_complexity in ['medium', 'complex']
            ],
            'dependencies_to_resolve': list(set([
                dep for m in high_priority for dep in m.dependencies
            ])),
            'estimated_implementation_time': {
                'simple_apis': len([m for m in high_priority if m.implementation_complexity == 'simple']) * 2,
                'medium_apis': len([m for m in high_priority if m.implementation_complexity == 'medium']) * 5,
                'complex_apis': len([m for m in high_priority if m.implementation_complexity == 'complex']) * 10,
                'unit': 'hours'
            }
        }
        
        return plan

    def load_backend_apis(self, api_report_file: str = "backend_api_analysis_report.json"):
        """載入後端API數據"""
        api_file_path = self.workspace_root / api_report_file
        if api_file_path.exists():
            with open(api_file_path, 'r', encoding='utf-8') as f:
                api_data = json.load(f)
                
            # 提取所有API端點
            self.backend_apis = []
            for category, endpoints in api_data.get('categories', {}).items():
                for endpoint in endpoints:
                    self.backend_apis.append({
                        'path': endpoint['path'],
                        'method': endpoint['method'],
                        'category': category,
                        'description': endpoint.get('description', '')
                    })
            
            logger.info(f"載入了 {len(self.backend_apis)} 個後端API端點")
        else:
            logger.warning(f"後端API報告文件不存在: {api_file_path}")
    
    def load_frontend_versions(self, admin_report_file: str = "admin_system_analysis_report.json"):
        """載入前端版本數據"""
        admin_file_path = self.workspace_root / admin_report_file
        if admin_file_path.exists():
            with open(admin_file_path, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
                
            self.frontend_versions = admin_data.get('versions', {})
            logger.info(f"載入了 {len(self.frontend_versions)} 個前端版本")
        else:
            logger.warning(f"前端版本報告文件不存在: {admin_file_path}")
    
    def extract_api_calls_from_content(self, content: str) -> List[Dict[str, Any]]:
        """從內容中提取API調用"""
        api_calls = []
        
        for pattern in self.api_call_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                groups = match.groups()
                if len(groups) >= 1:
                    if len(groups) == 1:
                        # 只有URL
                        url = groups[0]
                        method = "GET"  # 默認方法
                    elif len(groups) == 2:
                        # 方法和URL
                        if groups[0].upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            method = groups[0].upper()
                            url = groups[1]
                        else:
                            method = groups[1].upper() if groups[1] else "GET"
                            url = groups[0]
                    else:
                        continue
                    
                    # 清理URL
                    url = self._clean_url(url)
                    if url:
                        api_calls.append({
                            'url': url,
                            'method': method,
                            'raw_match': match.group(0)
                        })
        
        return api_calls
    
    def _clean_url(self, url: str) -> str:
        """清理URL"""
        # 移除變量插值
        url = re.sub(r'\$\{[^}]+\}', '{param}', url)
        url = re.sub(r'\${[^}]+}', '{param}', url)
        
        # 移除查詢參數
        url = url.split('?')[0]
        
        # 移除片段
        url = url.split('#')[0]
        
        # 標準化路徑參數
        url = re.sub(r'/\d+', '/{id}', url)
        url = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', url)
        
        return url.strip()
    
    def analyze_api_integration_quality(self, content: str, api_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析API整合質量"""
        quality_metrics = {
            'has_error_handling': False,
            'has_loading_states': False,
            'error_handling_count': 0,
            'loading_state_count': 0
        }
        
        # 檢查錯誤處理
        for pattern in self.error_handling_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            quality_metrics['error_handling_count'] += len(matches)
        
        quality_metrics['has_error_handling'] = quality_metrics['error_handling_count'] > 0
        
        # 檢查載入狀態
        for pattern in self.loading_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            quality_metrics['loading_state_count'] += len(matches)
        
        quality_metrics['has_loading_states'] = quality_metrics['loading_state_count'] > 0
        
        return quality_metrics
    
    def match_frontend_to_backend_apis(self, frontend_api_calls: List[Dict[str, Any]]) -> List[APIIntegration]:
        """匹配前端API調用與後端API"""
        integrations = []
        
        for api_call in frontend_api_calls:
            frontend_url = api_call['url']
            frontend_method = api_call['method']
            
            # 尋找匹配的後端API
            best_match = None
            best_score = 0
            
            for backend_api in self.backend_apis:
                backend_url = backend_api['path']
                backend_method = backend_api['method']
                
                # 計算匹配分數
                score = self._calculate_api_match_score(
                    frontend_url, frontend_method,
                    backend_url, backend_method
                )
                
                if score > best_score and score > 0.7:  # 閾值
                    best_score = score
                    best_match = backend_api
            
            if best_match:
                integration = APIIntegration(
                    endpoint=best_match['path'],
                    method=best_match['method'],
                    integration_status='integrated',
                    frontend_usage_count=1
                )
            else:
                integration = APIIntegration(
                    endpoint=frontend_url,
                    method=frontend_method,
                    integration_status='missing',
                    frontend_usage_count=1
                )
            
            integrations.append(integration)
        
        return integrations
    
    def _calculate_api_match_score(self, frontend_url: str, frontend_method: str,
                                 backend_url: str, backend_method: str) -> float:
        """計算API匹配分數"""
        score = 0.0
        
        # 方法匹配 (30%)
        if frontend_method == backend_method:
            score += 0.3
        
        # URL匹配 (70%)
        url_score = self._calculate_url_similarity(frontend_url, backend_url)
        score += url_score * 0.7
        
        return score
    
    def _calculate_url_similarity(self, url1: str, url2: str) -> float:
        """計算URL相似度"""
        # 簡化的URL相似度計算
        url1_parts = url1.strip('/').split('/')
        url2_parts = url2.strip('/').split('/')
        
        if not url1_parts or not url2_parts:
            return 0.0
        
        # 計算最長公共子序列
        max_len = max(len(url1_parts), len(url2_parts))
        min_len = min(len(url1_parts), len(url2_parts))
        
        if max_len == 0:
            return 1.0
        
        common_parts = 0
        for i in range(min_len):
            if url1_parts[i] == url2_parts[i] or \
               ('{' in url1_parts[i] and '}' in url1_parts[i]) or \
               ('{' in url2_parts[i] and '}' in url2_parts[i]):
                common_parts += 1
        
        return common_parts / max_len
    
    def analyze_version_api_integration(self, version_name: str, version_data: Dict[str, Any]) -> FrontendAPIAnalysis:
        """分析單個版本的API整合狀態"""
        logger.info(f"分析版本API整合: {version_name}")
        
        # 讀取文件內容
        file_path = version_data['path']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            logger.warning(f"無法讀取文件: {file_path}")
            return FrontendAPIAnalysis(
                version_name=version_name,
                total_api_calls=0,
                integrated_apis=[],
                missing_apis=[],
                api_coverage_rate=0.0,
                integration_quality_score=0.0
            )
        
        # 提取API調用
        api_calls = self.extract_api_calls_from_content(content)
        
        # 分析整合質量
        quality_metrics = self.analyze_api_integration_quality(content, api_calls)
        
        # 匹配前後端API
        integrations = self.match_frontend_to_backend_apis(api_calls)
        
        # 計算覆蓋率
        integrated_count = len([i for i in integrations if i.integration_status == 'integrated'])
        total_backend_apis = len(self.backend_apis)
        coverage_rate = integrated_count / total_backend_apis if total_backend_apis > 0 else 0.0
        
        # 計算質量分數
        quality_score = self._calculate_integration_quality_score(quality_metrics, integrations)
        
        # 找出缺失的API
        integrated_endpoints = {i.endpoint for i in integrations if i.integration_status == 'integrated'}
        missing_apis = []
        for backend_api in self.backend_apis:
            if backend_api['path'] not in integrated_endpoints:
                missing_apis.append(f"{backend_api['method']} {backend_api['path']}")
        
        return FrontendAPIAnalysis(
            version_name=version_name,
            total_api_calls=len(api_calls),
            integrated_apis=integrations,
            missing_apis=missing_apis[:20],  # 限制數量
            api_coverage_rate=coverage_rate,
            integration_quality_score=quality_score
        )
    
    def _calculate_integration_quality_score(self, quality_metrics: Dict[str, Any], 
                                           integrations: List[APIIntegration]) -> float:
        """計算整合質量分數"""
        score = 0.0
        
        # 錯誤處理 (40%)
        if quality_metrics['has_error_handling']:
            score += 0.4
        
        # 載入狀態 (30%)
        if quality_metrics['has_loading_states']:
            score += 0.3
        
        # API整合完整性 (30%)
        if integrations:
            integrated_count = len([i for i in integrations if i.integration_status == 'integrated'])
            integration_rate = integrated_count / len(integrations)
            score += integration_rate * 0.3
        
        return score
    
    def analyze_all_versions(self) -> Dict[str, FrontendAPIAnalysis]:
        """分析所有版本的API整合狀態"""
        logger.info("開始分析所有版本的API整合狀態...")
        
        # 載入數據
        self.load_backend_apis()
        self.load_frontend_versions()
        
        if not self.backend_apis:
            logger.error("沒有後端API數據，請先運行 backend_api_scanner.py")
            return {}
        
        if not self.frontend_versions:
            logger.error("沒有前端版本數據，請先運行 admin_system_analyzer.py")
            return {}
        
        # 分析每個版本
        results = {}
        for version_name, version_data in self.frontend_versions.items():
            analysis = self.analyze_version_api_integration(version_name, version_data)
            results[version_name] = analysis
        
        self.integration_results = results
        logger.info(f"完成分析，共 {len(results)} 個版本")
        
        return results
    
    def generate_integration_report(self, output_file: str = "frontend_api_integration_report.json") -> str:
        """生成API整合報告"""
        if not self.integration_results:
            logger.warning("沒有整合分析結果可導出")
            return ""
        
        # 準備導出數據
        export_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'workspace_root': str(self.workspace_root),
            'total_backend_apis': len(self.backend_apis),
            'total_frontend_versions': len(self.integration_results),
            'integration_analysis': {},
            'summary': self._generate_summary()
        }
        
        # 轉換分析結果
        for version_name, analysis in self.integration_results.items():
            export_data['integration_analysis'][version_name] = {
                'version_name': analysis.version_name,
                'total_api_calls': analysis.total_api_calls,
                'integrated_apis': [asdict(api) for api in analysis.integrated_apis],
                'missing_apis': analysis.missing_apis,
                'api_coverage_rate': analysis.api_coverage_rate,
                'integration_quality_score': analysis.integration_quality_score
            }
        
        # 寫入文件
        output_path = self.workspace_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"API整合報告已導出到: {output_path}")
        return str(output_path)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成摘要統計"""
        if not self.integration_results:
            return {}
        
        total_api_calls = sum(r.total_api_calls for r in self.integration_results.values())
        avg_coverage_rate = sum(r.api_coverage_rate for r in self.integration_results.values()) / len(self.integration_results)
        avg_quality_score = sum(r.integration_quality_score for r in self.integration_results.values()) / len(self.integration_results)
        
        # 找出最佳版本
        best_version = max(self.integration_results.items(), 
                          key=lambda x: x[1].api_coverage_rate + x[1].integration_quality_score)
        
        return {
            'total_api_calls_across_versions': total_api_calls,
            'average_coverage_rate': avg_coverage_rate,
            'average_quality_score': avg_quality_score,
            'best_integration_version': best_version[0],
            'best_version_coverage': best_version[1].api_coverage_rate,
            'best_version_quality': best_version[1].integration_quality_score
        }
    
    def print_integration_summary(self):
        """打印API整合摘要"""
        if not self.integration_results:
            print("沒有API整合分析結果")
            return
        
        print("\n" + "="*70)
        print("前端API整合狀態分析摘要")
        print("="*70)
        
        summary = self._generate_summary()
        
        print(f"後端API總數: {len(self.backend_apis)}")
        print(f"前端版本數: {len(self.integration_results)}")
        print(f"平均API覆蓋率: {summary['average_coverage_rate']:.1%}")
        print(f"平均整合質量: {summary['average_quality_score']:.2f}")
        print(f"最佳整合版本: {summary['best_integration_version']}")
        
        print("\n版本API整合排名:")
        print("-" * 70)
        
        # 按綜合分數排序
        sorted_versions = sorted(
            self.integration_results.items(),
            key=lambda x: x[1].api_coverage_rate + x[1].integration_quality_score,
            reverse=True
        )
        
        for i, (version_name, analysis) in enumerate(sorted_versions, 1):
            print(f"{i}. {version_name}")
            print(f"   API調用數: {analysis.total_api_calls}")
            print(f"   覆蓋率: {analysis.api_coverage_rate:.1%}")
            print(f"   質量分數: {analysis.integration_quality_score:.2f}")
            print(f"   缺失API數: {len(analysis.missing_apis)}")
            print()

def main():
    """主函數"""
    print("前端API整合狀態分析器 - admin_ultimate.html專門版本")
    print("=" * 60)
    
    # 創建分析器
    analyzer = FrontendAPIIntegrationAnalyzer()
    
    # 執行分析
    try:
        # 專門分析admin_ultimate.html
        print("1. 分析admin_ultimate.html中的mock數據結構...")
        admin_analysis = analyzer.analyze_admin_ultimate_integration()
        
        # 保存分析結果
        output_file = "admin_ultimate_api_integration_analysis.json"
        output_path = analyzer.workspace_root / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(admin_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"[完成] admin_ultimate.html API分析完成!")
        print(f"[統計] 發現 {admin_analysis['mock_data_analysis']['total_structures']} 個mock數據結構")
        print(f"[映射] 生成 {admin_analysis['api_mapping_analysis']['total_mappings']} 個API映射")
        print(f"[高優先級] {admin_analysis['api_mapping_analysis']['high_priority_count']} 個API")
        print(f"[中優先級] {admin_analysis['api_mapping_analysis']['medium_priority_count']} 個API")
        print(f"[低優先級] {admin_analysis['api_mapping_analysis']['low_priority_count']} 個API")
        
        # 顯示優先級實施計劃
        plan = admin_analysis['priority_implementation_plan']
        print(f"\n[實施計劃] 優先級實施計劃:")
        print(f"   立即行動項目: {len(plan['immediate_actions'])} 個")
        print(f"   短期目標: {len(plan['short_term_goals'])} 個")
        print(f"   需要解決的依賴: {len(plan['dependencies_to_resolve'])} 個")
        
        # 顯示時間估計
        time_est = plan['estimated_implementation_time']
        total_hours = time_est['simple_apis'] + time_est['medium_apis'] + time_est['complex_apis']
        print(f"   估計實施時間: {total_hours} {time_est['unit']}")
        
        print(f"\n[報告] 詳細報告已保存到: {output_path}")
        
        # 執行完整版本分析（如果需要）
        print("\n2. 執行完整版本分析...")
        results = analyzer.analyze_all_versions()
        
        # 打印摘要
        analyzer.print_integration_summary()
        
        # 導出完整報告
        full_report_file = analyzer.generate_integration_report()
        print(f"[報告] 完整版本分析報告已保存到: {full_report_file}")
        
    except Exception as e:
        logger.error(f"分析過程中發生錯誤: {e}")
        raise

def analyze_admin_ultimate_only():
    """只分析admin_ultimate.html的快速模式"""
    print("admin_ultimate.html Mock數據 -> 真實API 分析工具")
    print("=" * 60)
    
    analyzer = FrontendAPIIntegrationAnalyzer()
    
    try:
        # 只執行admin_ultimate.html分析
        analysis = analyzer.analyze_admin_ultimate_integration()
        
        # 顯示Mock數據結構
        print("\n[Mock數據] 發現的Mock數據結構:")
        for i, structure in enumerate(analysis['mock_data_analysis']['structures'], 1):
            print(f"  {i}. {structure['name']}")
            print(f"     字段數量: {len(structure['fields'])}")
            print(f"     使用組件: {structure['usage_context']}")
            print(f"     API建議: {', '.join(structure['api_suggestions'][:3])}...")
            print()
        
        # 顯示API映射
        print("\n[API映射] API端點映射:")
        mappings = analysis['api_mapping_analysis']['mappings']
        high_priority = [m for m in mappings if m['priority'] == 1]
        
        print("  高優先級映射:")
        for mapping in high_priority[:10]:  # 顯示前10個
            print(f"    {mapping['mock_endpoint']} -> {mapping['real_endpoint']} ({mapping['method']})")
            print(f"      複雜度: {mapping['implementation_complexity']}, 分類: {mapping['category']}")
        
        # 保存結果
        output_file = "admin_ultimate_mock_api_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\n[完成] 分析完成! 結果保存到: {output_file}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"分析失敗: {e}")
        return None

if __name__ == "__main__":
    main()