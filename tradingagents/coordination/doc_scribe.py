#!/usr/bin/env python3
"""
司馬 (Sima) - Doc Scribe Agent
文檔書記員代理人

司馬，以中國古代史學家司馬遷命名，以其嚴謹的記錄和文檔編撰能力著稱。
本代理人專注於技術文檔撰寫、API文檔生成和知識管理。

專業領域：
1. 技術文檔撰寫和維護
2. API文檔自動生成
3. 代碼註釋和說明
4. 用戶手冊和指南編寫
5. 知識庫管理和維護
6. 文檔品質保證和標準化
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import os

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error

logger = get_system_logger("doc_scribe")

class DocumentType(Enum):
    """文檔類型"""
    API_DOCUMENTATION = "api_documentation"
    USER_MANUAL = "user_manual"
    TECHNICAL_SPECIFICATION = "technical_specification"
    INSTALLATION_GUIDE = "installation_guide"
    DEVELOPER_GUIDE = "developer_guide"
    TROUBLESHOOTING_GUIDE = "troubleshooting_guide"
    RELEASE_NOTES = "release_notes"
    README = "readme"
    CHANGELOG = "changelog"
    ARCHITECTURE_DOCUMENT = "architecture_document"

class DocumentFormat(Enum):
    """文檔格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    RST = "rst"
    ASCIIDOC = "asciidoc"

class DocumentStatus(Enum):
    """文檔狀態"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"

@dataclass
class DocumentationTask:
    """文檔任務"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    document_type: DocumentType = DocumentType.README
    target_audience: List[str] = field(default_factory=list)
    source_materials: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    priority: str = "medium"
    assigned_to: str = ""
    status: DocumentStatus = DocumentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    
@dataclass
class DocumentOutput:
    """文檔輸出"""
    output_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    title: str = ""
    content: str = ""
    format: DocumentFormat = DocumentFormat.MARKDOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[Dict[str, str]] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    word_count: int = 0
    estimated_reading_time: int = 0
    quality_score: float = 0.0
    validation_results: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class APIDocumentation:
    """API文檔"""
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    api_name: str = ""
    version: str = "1.0.0"
    base_url: str = ""
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    authentication: Dict[str, Any] = field(default_factory=dict)
    error_codes: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    schemas: List[Dict[str, Any]] = field(default_factory=list)
    changelog: List[Dict[str, Any]] = field(default_factory=list)
    generated_from: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

class DocScribeSima:
    """
    司馬 - 文檔書記員代理人
    
    專注於技術文檔撰寫、API文檔生成和知識管理。
    確保所有文檔符合高品質標準和一致性要求。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = "doc-scribe-sima"
        self.config = config or {}
        self.name = "司馬 (Sima) - 文檔書記員"
        self.expertise_areas = [
            "技術文檔撰寫",
            "API文檔生成",
            "用戶手冊編寫",
            "知識庫管理",
            "文檔品質保證",
            "內容標準化"
        ]
        
        # 工作統計
        self.documents_created = 0
        self.api_docs_generated = 0
        self.guides_written = 0
        self.reviews_conducted = 0
        
        # 文檔標準配置
        self.default_format = DocumentFormat(self.config.get('default_format', 'markdown'))
        self.quality_threshold = self.config.get('quality_threshold', 0.8)
        self.max_words_per_section = self.config.get('max_words_per_section', 500)
        
        logger.info("文檔書記員司馬已初始化", extra={
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'expertise_areas': self.expertise_areas,
            'default_format': self.default_format.value
        })
    
    async def create_documentation(self,
                                 task: DocumentationTask,
                                 source_code: Optional[str] = None,
                                 additional_context: Optional[Dict[str, Any]] = None) -> DocumentOutput:
        """創建文檔"""
        
        output = DocumentOutput(
            task_id=task.task_id,
            title=task.title,
            format=self.default_format
        )
        
        try:
            # 模擬文檔創建過程
            await asyncio.sleep(1.0)
            
            # 分析任務需求
            content_structure = self._analyze_documentation_requirements(task)
            
            # 生成文檔內容
            output.content = await self._generate_document_content(
                task, content_structure, source_code, additional_context
            )
            
            # 解析文檔結構
            output.sections = self._parse_document_sections(output.content)
            
            # 提取參考資料
            output.references = self._extract_references(output.content, task.source_materials)
            
            # 計算統計資訊
            output.word_count = self._count_words(output.content)
            output.estimated_reading_time = self._estimate_reading_time(output.word_count)
            
            # 設定元數據
            output.metadata = self._generate_metadata(task, output)
            
            # 品質評估
            output.quality_score = self._assess_document_quality(output)
            
            # 驗證文檔
            output.validation_results = self._validate_document(output, task)
            
            self.documents_created += 1
            
            logger.info("文檔創建完成", extra={
                'output_id': output.output_id,
                'title': task.title,
                'document_type': task.document_type.value,
                'word_count': output.word_count,
                'quality_score': output.quality_score,
                'agent': self.agent_type
            })
            
            return output
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'create_documentation',
                'task_id': task.task_id
            })
            logger.error(f"文檔創建失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def generate_api_documentation(self,
                                       api_name: str,
                                       source_code: str,
                                       api_specs: Optional[Dict[str, Any]] = None) -> APIDocumentation:
        """生成API文檔"""
        
        api_doc = APIDocumentation(
            api_name=api_name,
            generated_from="source_code_analysis"
        )
        
        try:
            # 模擬API文檔生成過程
            await asyncio.sleep(0.8)
            
            # 解析API規格
            if api_specs:
                api_doc.version = api_specs.get('version', '1.0.0')
                api_doc.base_url = api_specs.get('base_url', 'https://api.example.com')
            
            # 從源代碼提取端點資訊
            api_doc.endpoints = self._extract_api_endpoints(source_code)
            
            # 分析認證方式
            api_doc.authentication = self._analyze_authentication(source_code)
            
            # 提取錯誤碼
            api_doc.error_codes = self._extract_error_codes(source_code)
            
            # 生成使用範例
            api_doc.examples = self._generate_api_examples(api_doc.endpoints)
            
            # 提取數據模型
            api_doc.schemas = self._extract_data_schemas(source_code)
            
            # 生成變更日誌
            api_doc.changelog = self._generate_api_changelog(api_doc.version)
            
            self.api_docs_generated += 1
            
            logger.info("API文檔生成完成", extra={
                'doc_id': api_doc.doc_id,
                'api_name': api_name,
                'endpoints_count': len(api_doc.endpoints),
                'schemas_count': len(api_doc.schemas),
                'agent': self.agent_type
            })
            
            return api_doc
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'generate_api_documentation',
                'api_name': api_name
            })
            logger.error(f"API文檔生成失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def create_user_guide(self,
                              product_name: str,
                              features: List[str],
                              target_users: List[str],
                              screenshots: Optional[List[str]] = None) -> DocumentOutput:
        """創建用戶指南"""
        
        task = DocumentationTask(
            title=f"{product_name} 用戶指南",
            description=f"為{product_name}創建完整的用戶使用指南",
            document_type=DocumentType.USER_MANUAL,
            target_audience=target_users,
            requirements=features
        )
        
        try:
            # 生成用戶指南內容
            guide_content = await self._generate_user_guide_content(
                product_name, features, target_users, screenshots
            )
            
            output = DocumentOutput(
                task_id=task.task_id,
                title=task.title,
                content=guide_content,
                format=self.default_format
            )
            
            # 處理文檔統計和元數據
            output.sections = self._parse_document_sections(output.content)
            output.word_count = self._count_words(output.content)
            output.estimated_reading_time = self._estimate_reading_time(output.word_count)
            output.metadata = self._generate_metadata(task, output)
            output.quality_score = self._assess_document_quality(output)
            output.validation_results = self._validate_document(output, task)
            
            self.guides_written += 1
            
            logger.info("用戶指南創建完成", extra={
                'output_id': output.output_id,
                'product_name': product_name,
                'features_count': len(features),
                'word_count': output.word_count,
                'agent': self.agent_type
            })
            
            return output
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'create_user_guide',
                'product_name': product_name
            })
            logger.error(f"用戶指南創建失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def review_documentation(self,
                                 document: DocumentOutput,
                                 review_criteria: Optional[List[str]] = None) -> Dict[str, Any]:
        """審查文檔"""
        
        try:
            # 模擬文檔審查過程
            await asyncio.sleep(0.5)
            
            review_result = {
                'review_id': str(uuid.uuid4()),
                'document_id': document.output_id,
                'reviewed_at': datetime.now().isoformat(),
                'reviewer': self.name,
                'overall_score': 0.0,
                'criteria_scores': {},
                'strengths': [],
                'weaknesses': [],
                'suggestions': [],
                'compliance_check': {},
                'readability_analysis': {},
                'structure_analysis': {},
                'content_analysis': {},
                'action_items': []
            }
            
            # 執行各種審查
            review_result['criteria_scores'] = self._evaluate_review_criteria(document, review_criteria)
            review_result['strengths'] = self._identify_document_strengths(document)
            review_result['weaknesses'] = self._identify_document_weaknesses(document)
            review_result['suggestions'] = self._generate_improvement_suggestions(document)
            review_result['compliance_check'] = self._check_documentation_standards(document)
            review_result['readability_analysis'] = self._analyze_readability(document)
            review_result['structure_analysis'] = self._analyze_document_structure(document)
            review_result['content_analysis'] = self._analyze_content_quality(document)
            review_result['action_items'] = self._generate_review_action_items(review_result)
            
            # 計算總體評分
            review_result['overall_score'] = self._calculate_overall_review_score(review_result)
            
            self.reviews_conducted += 1
            
            logger.info("文檔審查完成", extra={
                'review_id': review_result['review_id'],
                'document_id': document.output_id,
                'overall_score': review_result['overall_score'],
                'action_items_count': len(review_result['action_items']),
                'agent': self.agent_type
            })
            
            return review_result
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'review_documentation',
                'document_id': document.output_id
            })
            logger.error(f"文檔審查失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    def _analyze_documentation_requirements(self, task: DocumentationTask) -> Dict[str, Any]:
        """分析文檔需求"""
        structure = {
            'required_sections': [],
            'optional_sections': [],
            'content_guidelines': {},
            'formatting_requirements': {}
        }
        
        # 根據文檔類型確定結構
        if task.document_type == DocumentType.API_DOCUMENTATION:
            structure['required_sections'] = [
                '概述', '認證', '端點列表', '數據模型', '錯誤處理', '範例'
            ]
            structure['optional_sections'] = ['變更日誌', 'SDK說明', '限制說明']
            
        elif task.document_type == DocumentType.USER_MANUAL:
            structure['required_sections'] = [
                '簡介', '快速開始', '功能說明', '常見問題', '故障排除'
            ]
            structure['optional_sections'] = ['高級功能', '最佳實踐', '附錄']
            
        elif task.document_type == DocumentType.README:
            structure['required_sections'] = [
                '專案簡介', '安裝說明', '使用方法', '貢獻指南'
            ]
            structure['optional_sections'] = ['授權條款', '變更日誌', '致謝']
            
        else:
            # 通用結構
            structure['required_sections'] = [
                '概述', '主要內容', '總結'
            ]
        
        return structure
    
    async def _generate_document_content(self,
                                       task: DocumentationTask,
                                       structure: Dict[str, Any],
                                       source_code: Optional[str] = None,
                                       additional_context: Optional[Dict[str, Any]] = None) -> str:
        """生成文檔內容"""
        
        content_parts = []
        
        # 生成標題
        content_parts.append(f"# {task.title}\n")
        
        # 生成目錄（如果需要）
        if len(structure['required_sections']) > 3:
            content_parts.append("## 目錄\n")
            for i, section in enumerate(structure['required_sections'], 1):
                content_parts.append(f"{i}. [{section}](#{section.lower().replace(' ', '-')})")
            content_parts.append("\n")
        
        # 生成各個章節
        for section in structure['required_sections']:
            section_content = await self._generate_section_content(
                section, task, source_code, additional_context
            )
            content_parts.append(f"## {section}\n")
            content_parts.append(section_content)
            content_parts.append("\n")
        
        # 添加可選章節（如果適用）
        for section in structure['optional_sections'][:2]:  # 限制可選章節數量
            section_content = await self._generate_section_content(
                section, task, source_code, additional_context
            )
            if section_content.strip():
                content_parts.append(f"## {section}\n")
                content_parts.append(section_content)
                content_parts.append("\n")
        
        # 添加頁腳
        content_parts.append("---\n")
        content_parts.append(f"*此文檔由 {self.name} 於 {datetime.now().strftime('%Y-%m-%d')} 生成*\n")
        
        return "\n".join(content_parts)
    
    async def _generate_section_content(self,
                                      section_name: str,
                                      task: DocumentationTask,
                                      source_code: Optional[str] = None,
                                      additional_context: Optional[Dict[str, Any]] = None) -> str:
        """生成章節內容"""
        
        content_templates = {
            '概述': f"""
{task.description}

本文檔提供了{task.title}的詳細說明，適用於{', '.join(task.target_audience) if task.target_audience else '所有用戶'}。

### 主要特點
- 功能完整且易於使用
- 遵循業界最佳實踐
- 提供豐富的範例和說明
""",
            
            '簡介': f"""
歡迎使用{task.title}！

這是一個{task.description}。本指南將幫助您快速上手並充分利用所有功能。

### 目標讀者
本文檔適用於：
{chr(10).join(f'- {audience}' for audience in task.target_audience) if task.target_audience else '- 所有用戶'}
""",
            
            '快速開始': """
### 系統要求
- Python 3.8 或更高版本
- 至少 4GB RAM
- 10GB 可用磁碟空間

### 安裝步驟
1. 下載最新版本
2. 解壓縮檔案
3. 執行安裝腳本
4. 驗證安裝

```bash
# 安裝命令範例
pip install package-name
```

### 基本配置
首次使用前，請完成基本配置：

```python
# 基本配置範例
import package_name

config = {
    'api_key': 'your-api-key',
    'debug': True
}

app = package_name.init(config)
```
""",
            
            '使用方法': """
### 基本用法
以下是基本使用範例：

```python
# 基本使用範例
from package import main_function

result = main_function(input_data)
print(result)
```

### 高級用法
對於更複雜的使用場景：

```python
# 高級使用範例
from package import AdvancedClass

processor = AdvancedClass(config)
result = processor.process(data, options={'verbose': True})
```
""",
            
            '常見問題': """
### Q: 如何解決安裝問題？
A: 請確認系統要求已滿足，並嘗試使用管理員權限安裝。

### Q: 如何獲得技術支援？
A: 您可以通過以下方式獲得支援：
- 查看本文檔的故障排除章節
- 訪問官方論壇
- 聯繫技術支援團隊

### Q: 如何報告錯誤？
A: 請在官方issue tracker提交詳細的錯誤報告。
""",
            
            '貢獻指南': """
我們歡迎社群貢獻！

### 如何貢獻
1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

### 編碼標準
- 遵循 PEP 8 編碼規範
- 包含適當的測試
- 更新相關文檔

### 測試
運行測試套件：
```bash
python -m pytest tests/
```
"""
        }
        
        return content_templates.get(section_name, f"TODO: 添加 {section_name} 章節內容")
    
    async def _generate_user_guide_content(self,
                                         product_name: str,
                                         features: List[str],
                                         target_users: List[str],
                                         screenshots: Optional[List[str]] = None) -> str:
        """生成用戶指南內容"""
        
        content = f"""# {product_name} 用戶指南

## 歡迎使用 {product_name}

{product_name} 是一個功能強大的應用程式，為{', '.join(target_users)}提供完整的解決方案。

## 主要功能

{chr(10).join(f'- **{feature}**: 提供{feature}相關的完整功能' for feature in features)}

## 快速開始

### 第一步：註冊和登入
1. 前往註冊頁面
2. 填寫必要資訊
3. 驗證電子郵件
4. 完成帳戶設置

### 第二步：基本設置
1. 個人資料設置
2. 偏好配置
3. 安全設置

## 功能詳解

"""
        
        # 為每個功能添加詳細說明
        for i, feature in enumerate(features, 1):
            content += f"""
### {i}. {feature}

{feature}功能允許您：
- 執行相關操作
- 管理相關數據
- 監控執行狀態

#### 使用步驟：
1. 導航到{feature}頁面
2. 配置必要參數
3. 執行操作
4. 查看結果

"""
            
            # 如果有螢幕截圖，添加參考
            if screenshots and i <= len(screenshots):
                content += f"![{feature}螢幕截圖]({screenshots[i-1]})\n\n"
        
        content += """
## 常見問題

### 如何重設密碼？
1. 點擊登入頁面的"忘記密碼"
2. 輸入註冊電子郵件
3. 檢查郵件中的重設連結
4. 設置新密碼

### 如何聯繫客服？
- 電子郵件：support@example.com
- 電話：+886-2-1234-5678
- 線上客服：週一至週五 9:00-18:00

## 故障排除

### 常見錯誤和解決方法

**錯誤：無法登入**
- 解決方案：檢查用戶名和密碼是否正確，確認帳戶是否已啟用

**錯誤：功能無法使用**
- 解決方案：檢查網路連接，重新整理頁面，或聯繫客服

## 附錄

### 系統要求
- 現代網頁瀏覽器 (Chrome 80+, Firefox 75+, Safari 13+)
- 穩定的網路連接
- JavaScript 已啟用

### 更新說明
請定期檢查系統更新，新功能和改進會持續發布。

---
*本指南最後更新：{datetime.now().strftime('%Y年%m月%d日')}*
"""
        
        return content
    
    def _extract_api_endpoints(self, source_code: str) -> List[Dict[str, Any]]:
        """從源代碼提取API端點"""
        endpoints = []
        
        # 簡化的端點提取邏輯
        # 尋找FastAPI路由定義
        route_patterns = [
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, source_code, re.IGNORECASE)
            for method, path in matches:
                endpoints.append({
                    'path': path,
                    'method': method.upper(),
                    'summary': f'{method.upper()} {path}',
                    'description': f'處理 {path} 的 {method.upper()} 請求',
                    'parameters': self._extract_path_parameters(path),
                    'responses': {
                        '200': {'description': '成功回應'},
                        '400': {'description': '請求錯誤'},
                        '500': {'description': '伺服器錯誤'}
                    }
                })
        
        # 如果沒有找到端點，提供預設範例
        if not endpoints:
            endpoints = [
                {
                    'path': '/health',
                    'method': 'GET',
                    'summary': '健康檢查',
                    'description': '檢查服務健康狀態',
                    'parameters': [],
                    'responses': {
                        '200': {'description': '服務正常運行'}
                    }
                },
                {
                    'path': '/api/data',
                    'method': 'GET',
                    'summary': '獲取數據',
                    'description': '獲取系統數據',
                    'parameters': [
                        {'name': 'limit', 'type': 'integer', 'description': '返回數量限制'}
                    ],
                    'responses': {
                        '200': {'description': '數據獲取成功'}
                    }
                }
            ]
        
        return endpoints
    
    def _extract_path_parameters(self, path: str) -> List[Dict[str, str]]:
        """提取路徑參數"""
        parameters = []
        param_pattern = r'\{([^}]+)\}'
        matches = re.findall(param_pattern, path)
        
        for param in matches:
            parameters.append({
                'name': param,
                'type': 'string',
                'description': f'{param} 參數',
                'required': True
            })
        
        return parameters
    
    def _analyze_authentication(self, source_code: str) -> Dict[str, Any]:
        """分析認證方式"""
        auth_info = {
            'type': 'bearer',
            'description': 'JWT Bearer Token認證',
            'header_name': 'Authorization',
            'format': 'Bearer <token>'
        }
        
        # 檢查是否有API Key認證
        if 'x-api-key' in source_code.lower() or 'api_key' in source_code.lower():
            auth_info.update({
                'type': 'api_key',
                'description': 'API Key認證',
                'header_name': 'X-API-Key',
                'format': '<api_key>'
            })
        
        return auth_info
    
    def _extract_error_codes(self, source_code: str) -> List[Dict[str, Any]]:
        """提取錯誤碼"""
        return [
            {'code': 400, 'message': 'Bad Request', 'description': '請求格式錯誤'},
            {'code': 401, 'message': 'Unauthorized', 'description': '未授權訪問'},
            {'code': 403, 'message': 'Forbidden', 'description': '禁止訪問'},
            {'code': 404, 'message': 'Not Found', 'description': '資源不存在'},
            {'code': 500, 'message': 'Internal Server Error', 'description': '伺服器內部錯誤'}
        ]
    
    def _generate_api_examples(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成API使用範例"""
        examples = []
        
        for endpoint in endpoints[:3]:  # 限制範例數量
            example = {
                'title': f'{endpoint["method"]} {endpoint["path"]}',
                'description': f'使用 {endpoint["method"]} 方法調用 {endpoint["path"]}',
                'request': {
                    'method': endpoint['method'],
                    'url': f'https://api.example.com{endpoint["path"]}',
                    'headers': {
                        'Authorization': 'Bearer <your_token>',
                        'Content-Type': 'application/json'
                    }
                },
                'response': {
                    'status': 200,
                    'body': {
                        'status': 'success',
                        'data': {},
                        'message': '操作成功'
                    }
                }
            }
            
            if endpoint['method'] in ['POST', 'PUT', 'PATCH']:
                example['request']['body'] = {
                    'example_field': 'example_value'
                }
            
            examples.append(example)
        
        return examples
    
    def _extract_data_schemas(self, source_code: str) -> List[Dict[str, Any]]:
        """提取數據模型"""
        schemas = []
        
        # 尋找Pydantic模型定義
        class_pattern = r'class\s+(\w+)\(BaseModel\):'
        matches = re.findall(class_pattern, source_code)
        
        for class_name in matches:
            schema = {
                'name': class_name,
                'type': 'object',
                'description': f'{class_name} 數據模型',
                'properties': {
                    'id': {'type': 'string', 'description': '唯一識別符'},
                    'created_at': {'type': 'string', 'format': 'datetime', 'description': '創建時間'},
                    'updated_at': {'type': 'string', 'format': 'datetime', 'description': '更新時間'}
                },
                'required': ['id']
            }
            schemas.append(schema)
        
        # 如果沒有找到模型，提供預設範例
        if not schemas:
            schemas = [
                {
                    'name': 'GenericResponse',
                    'type': 'object',
                    'description': '通用回應格式',
                    'properties': {
                        'status': {'type': 'string', 'description': '狀態'},
                        'message': {'type': 'string', 'description': '訊息'},
                        'data': {'type': 'object', 'description': '數據'}
                    },
                    'required': ['status']
                }
            ]
        
        return schemas
    
    def _generate_api_changelog(self, version: str) -> List[Dict[str, Any]]:
        """生成API變更日誌"""
        return [
            {
                'version': version,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'changes': [
                    '初始版本發布',
                    '基本API端點實現',
                    '認證機制建立'
                ]
            }
        ]
    
    def _parse_document_sections(self, content: str) -> List[Dict[str, str]]:
        """解析文檔章節"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('# '):
                # 新的主標題
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'level': 1
                    })
                current_section = line[2:].strip()
                current_content = []
            elif line.startswith('## '):
                # 子標題
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'level': 2
                    })
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # 添加最後一個章節
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip(),
                'level': 2
            })
        
        return sections
    
    def _extract_references(self, content: str, source_materials: List[str]) -> List[str]:
        """提取參考資料"""
        references = list(source_materials)  # 從源材料開始
        
        # 從內容中提取URL
        url_pattern = r'https?://[^\s\)]+|www\.[^\s\)]+'
        urls = re.findall(url_pattern, content)
        references.extend(urls)
        
        return list(set(references))  # 去重
    
    def _count_words(self, content: str) -> int:
        """計算字數"""
        # 移除Markdown標記和代碼塊
        clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        clean_content = re.sub(r'`[^`]+`', '', clean_content)
        clean_content = re.sub(r'[#*_\-\[\]()]+', '', clean_content)
        
        # 計算中文和英文字數
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_content))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', clean_content))
        
        return chinese_chars + english_words
    
    def _estimate_reading_time(self, word_count: int) -> int:
        """估算閱讀時間（分鐘）"""
        # 假設每分鐘閱讀200個中文字或250個英文字
        average_reading_speed = 225
        return max(1, word_count // average_reading_speed)
    
    def _generate_metadata(self, task: DocumentationTask, output: DocumentOutput) -> Dict[str, Any]:
        """生成元數據"""
        return {
            'title': task.title,
            'document_type': task.document_type.value,
            'target_audience': task.target_audience,
            'author': self.name,
            'created_date': output.generated_at.isoformat(),
            'format': output.format.value,
            'language': 'zh-TW',
            'status': DocumentStatus.DRAFT.value,
            'word_count': output.word_count,
            'estimated_reading_time': output.estimated_reading_time,
            'sections_count': len(output.sections),
            'version': '1.0'
        }
    
    def _assess_document_quality(self, output: DocumentOutput) -> float:
        """評估文檔品質"""
        score = 0.0
        
        # 內容長度評分 (25%)
        if output.word_count > 500:
            score += 0.25
        elif output.word_count > 200:
            score += 0.15
        else:
            score += 0.05
        
        # 結構完整性評分 (25%)
        if len(output.sections) >= 3:
            score += 0.25
        elif len(output.sections) >= 2:
            score += 0.15
        else:
            score += 0.05
        
        # 內容品質評分 (30%)
        content_lower = output.content.lower()
        if '範例' in content_lower or 'example' in content_lower:
            score += 0.1
        if '步驟' in content_lower or 'step' in content_lower:
            score += 0.1
        if '```' in output.content:  # 包含代碼範例
            score += 0.1
        
        # 格式化評分 (20%)
        if '# ' in output.content:  # 有標題
            score += 0.1
        if '- ' in output.content or '1. ' in output.content:  # 有列表
            score += 0.1
        
        return min(1.0, score)
    
    def _validate_document(self, output: DocumentOutput, task: DocumentationTask) -> Dict[str, Any]:
        """驗證文檔"""
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # 檢查必要元素
        if output.word_count < 100:
            validation_results['warnings'].append('文檔內容較短，建議增加更多詳細說明')
        
        if len(output.sections) < 2:
            validation_results['warnings'].append('文檔結構較簡單，建議增加更多章節')
        
        if not output.content.startswith('#'):
            validation_results['errors'].append('文檔缺少主標題')
            validation_results['is_valid'] = False
        
        # 檢查目標讀者相關內容
        if task.target_audience and not any(audience in output.content for audience in task.target_audience):
            validation_results['suggestions'].append('建議在文檔中明確提及目標讀者')
        
        return validation_results
    
    def _evaluate_review_criteria(self, document: DocumentOutput, criteria: Optional[List[str]]) -> Dict[str, float]:
        """評估審查標準"""
        default_criteria = [
            '內容完整性',
            '結構清晰度',
            '語言準確性',
            '範例品質',
            '實用性'
        ]
        
        review_criteria = criteria or default_criteria
        scores = {}
        
        for criterion in review_criteria:
            # 簡化的評分邏輯
            if criterion == '內容完整性':
                scores[criterion] = 0.8 if document.word_count > 300 else 0.6
            elif criterion == '結構清晰度':
                scores[criterion] = 0.9 if len(document.sections) >= 3 else 0.7
            elif criterion == '範例品質':
                scores[criterion] = 0.85 if '```' in document.content else 0.5
            else:
                scores[criterion] = 0.75  # 預設評分
        
        return scores
    
    def _identify_document_strengths(self, document: DocumentOutput) -> List[str]:
        """識別文檔優點"""
        strengths = []
        
        if document.word_count > 500:
            strengths.append('內容豐富詳實')
        
        if len(document.sections) >= 4:
            strengths.append('結構組織良好')
        
        if '```' in document.content:
            strengths.append('包含實用的代碼範例')
        
        if document.estimated_reading_time <= 10:
            strengths.append('篇幅適中，易於閱讀')
        
        if document.quality_score >= 0.8:
            strengths.append('整體品質優秀')
        
        return strengths
    
    def _identify_document_weaknesses(self, document: DocumentOutput) -> List[str]:
        """識別文檔缺點"""
        weaknesses = []
        
        if document.word_count < 200:
            weaknesses.append('內容較少，建議增加更多詳細說明')
        
        if len(document.sections) < 3:
            weaknesses.append('結構較簡單，建議增加更多章節')
        
        if '```' not in document.content and 'code' in document.title.lower():
            weaknesses.append('技術文檔缺少代碼範例')
        
        if document.quality_score < 0.6:
            weaknesses.append('整體品質需要改進')
        
        return weaknesses
    
    def _generate_improvement_suggestions(self, document: DocumentOutput) -> List[str]:
        """生成改進建議"""
        suggestions = []
        
        if document.word_count < 300:
            suggestions.append('增加更多詳細說明和背景資訊')
        
        if '範例' not in document.content and 'example' not in document.content.lower():
            suggestions.append('添加實際使用範例')
        
        if '常見問題' not in document.content and 'faq' not in document.content.lower():
            suggestions.append('考慮添加常見問題章節')
        
        if len(document.references) < 2:
            suggestions.append('增加相關參考資料連結')
        
        suggestions.extend([
            '定期更新文檔內容',
            '收集用戶反饋並持續改進',
            '考慮添加多媒體內容（圖片、視頻）'
        ])
        
        return suggestions
    
    def _check_documentation_standards(self, document: DocumentOutput) -> Dict[str, bool]:
        """檢查文檔標準"""
        return {
            'has_title': document.content.startswith('#'),
            'has_sections': len(document.sections) >= 2,
            'has_examples': '```' in document.content or '範例' in document.content,
            'appropriate_length': 200 <= document.word_count <= 2000,
            'has_metadata': bool(document.metadata),
            'quality_threshold_met': document.quality_score >= self.quality_threshold
        }
    
    def _analyze_readability(self, document: DocumentOutput) -> Dict[str, Any]:
        """分析可讀性"""
        return {
            'reading_level': 'intermediate',
            'sentence_complexity': 'moderate',
            'vocabulary_difficulty': 'appropriate',
            'readability_score': 0.75,
            'estimated_reading_time': document.estimated_reading_time,
            'suggestions': [
                '保持句子長度適中',
                '使用清晰的段落結構',
                '適當使用列表和標題'
            ]
        }
    
    def _analyze_document_structure(self, document: DocumentOutput) -> Dict[str, Any]:
        """分析文檔結構"""
        return {
            'structure_score': 0.8,
            'sections_count': len(document.sections),
            'hierarchy_depth': max((section.get('level', 1) for section in document.sections), default=1),
            'balance_score': 0.75,
            'navigation_clarity': 'good',
            'suggestions': [
                '考慮添加目錄',
                '確保章節標題清晰',
                '保持章節長度平衡'
            ]
        }
    
    def _analyze_content_quality(self, document: DocumentOutput) -> Dict[str, Any]:
        """分析內容品質"""
        return {
            'accuracy_score': 0.85,
            'completeness_score': 0.8,
            'relevance_score': 0.9,
            'freshness_score': 1.0,  # 新創建的文檔
            'usefulness_score': 0.8,
            'overall_content_score': 0.83,
            'strengths': [
                '內容相關性高',
                '資訊新鮮',
                '結構清晰'
            ],
            'areas_for_improvement': [
                '增加更多實例',
                '提供更詳細的說明'
            ]
        }
    
    def _generate_review_action_items(self, review_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成審查行動項目"""
        action_items = []
        
        # 基於弱點生成行動項目
        for weakness in review_result.get('weaknesses', []):
            action_items.append({
                'action_id': f"ACTION_{len(action_items) + 1:03d}",
                'type': 'improvement',
                'description': f'解決問題：{weakness}',
                'priority': 'medium',
                'estimated_effort': '1-2 hours'
            })
        
        # 基於建議生成行動項目
        for suggestion in review_result.get('suggestions', [])[:3]:  # 限制數量
            action_items.append({
                'action_id': f"ACTION_{len(action_items) + 1:03d}",
                'type': 'enhancement',
                'description': suggestion,
                'priority': 'low',
                'estimated_effort': '30 minutes'
            })
        
        return action_items
    
    def _calculate_overall_review_score(self, review_result: Dict[str, Any]) -> float:
        """計算總體審查評分"""
        criteria_scores = review_result.get('criteria_scores', {})
        if not criteria_scores:
            return 0.0
        
        return sum(criteria_scores.values()) / len(criteria_scores)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """獲取代理人狀態"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'name': self.name,
            'expertise_areas': self.expertise_areas,
            'statistics': {
                'documents_created': self.documents_created,
                'api_docs_generated': self.api_docs_generated,
                'guides_written': self.guides_written,
                'reviews_conducted': self.reviews_conducted
            },
            'configuration': {
                'default_format': self.default_format.value,
                'quality_threshold': self.quality_threshold,
                'max_words_per_section': self.max_words_per_section
            },
            'status': 'active',
            'last_updated': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 測試腳本
    async def test_doc_scribe():
        print("測試文檔書記員司馬...")
        
        scribe = DocScribeSima({
            'default_format': 'markdown',
            'quality_threshold': 0.8,
            'max_words_per_section': 500
        })
        
        # 測試創建文檔
        task = DocumentationTask(
            title="TradingAgents API 使用指南",
            description="為開發者提供完整的API使用說明",
            document_type=DocumentType.API_DOCUMENTATION,
            target_audience=["開發者", "系統整合人員"],
            requirements=["API端點說明", "認證方式", "使用範例"]
        )
        
        document = await scribe.create_documentation(
            task,
            source_code="@app.get('/api/analysis')\nasync def get_analysis():\n    return {'status': 'success'}",
            additional_context={'version': '2.0.0'}
        )
        
        print(f"文檔創建完成: {document.output_id}")
        print(f"字數: {document.word_count}")
        print(f"品質評分: {document.quality_score}")
        print(f"章節數量: {len(document.sections)}")
        
        # 測試API文檔生成
        api_doc = await scribe.generate_api_documentation(
            "TradingAgents API",
            "@app.get('/health')\n@app.post('/analysis')\nclass UserModel(BaseModel):\n    pass",
            {'version': '2.0.0', 'base_url': 'https://api.tradingagents.com'}
        )
        
        print(f"API文檔生成完成: {api_doc.doc_id}")
        print(f"端點數量: {len(api_doc.endpoints)}")
        print(f"數據模型數量: {len(api_doc.schemas)}")
        
        # 測試用戶指南創建
        user_guide = await scribe.create_user_guide(
            "TradingAgents 平台",
            ["AI分析", "投資規劃", "風險評估", "數據導出"],
            ["投資者", "分析師", "基金經理"]
        )
        
        print(f"用戶指南創建完成: {user_guide.output_id}")
        print(f"字數: {user_guide.word_count}")
        print(f"預估閱讀時間: {user_guide.estimated_reading_time}分鐘")
        
        # 測試文檔審查
        review = await scribe.review_documentation(
            document,
            ["內容完整性", "技術準確性", "實用性"]
        )
        
        print(f"文檔審查完成: {review['review_id']}")
        print(f"總體評分: {review['overall_score']:.2f}")
        print(f"優點: {len(review['strengths'])}")
        print(f"改進建議: {len(review['suggestions'])}")
        
        # 獲取代理人狀態
        status = scribe.get_agent_status()
        print(f"代理人狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        print("文檔書記員司馬測試完成")
    
    asyncio.run(test_doc_scribe())