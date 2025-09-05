#!/usr/bin/env python3
"""
管理後台版本分析系統
AdminVersionAnalyzer - 掃描和分析所有管理後台版本文件

功能:
1. 掃描所有管理後台版本文件
2. 識別技術棧 (React/Bootstrap/原生JS/Chart.js等)
3. 分析功能模組
4. 評估代碼質量和設計模式
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TechStackInfo:
    """技術棧信息"""
    framework: str = ""
    ui_library: str = ""
    chart_library: str = ""
    css_framework: str = ""
    javascript_version: str = ""
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class FunctionalModule:
    """功能模組信息"""
    name: str
    description: str = ""
    complexity: str = "low"  # low, medium, high
    api_endpoints: List[str] = None
    ui_components: List[str] = None
    
    def __post_init__(self):
        if self.api_endpoints is None:
            self.api_endpoints = []
        if self.ui_components is None:
            self.ui_components = []

@dataclass
class CodeQualityMetrics:
    """代碼質量指標"""
    file_size: int = 0
    line_count: int = 0
    function_count: int = 0
    class_count: int = 0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    documentation_score: float = 0.0
    design_pattern_score: float = 0.0

@dataclass
class AdminVersion:
    """管理後台版本信息"""
    name: str
    path: str
    tech_stack: TechStackInfo
    functional_modules: List[FunctionalModule]
    code_quality: CodeQualityMetrics
    maturity_score: float = 0.0
    recommendation_score: float = 0.0
    last_modified: str = ""
    file_hash: str = ""

class AdminVersionAnalyzer:
    """管理後台版本分析器"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.admin_files = []
        self.analysis_results = {}
        
        # 定義掃描模式
        self.scan_patterns = [
            "admin*.html",
            "admin*.js", 
            "admin*.css",
            "*admin*/",
            "complete_admin_system/*",
            "TradingAgents/functional_admin.*",
            "TradingAgents/*admin*.html"
        ]
        
        # 技術棧識別模式
        self.tech_patterns = {
            'react': [
                r'react@\d+',
                r'react-dom@\d+',
                r'React\.',
                r'ReactDOM\.',
                r'useState',
                r'useEffect'
            ],
            'bootstrap': [
                r'bootstrap@[\d.]+',
                r'bootstrap\.min\.css',
                r'btn-primary',
                r'container-fluid',
                r'navbar'
            ],
            'chart_js': [
                r'chart\.js',
                r'Chart\.',
                r'new Chart\(',
                r'chartjs'
            ],
            'font_awesome': [
                r'font-awesome',
                r'fas fa-',
                r'far fa-',
                r'fab fa-'
            ],
            'datatables': [
                r'datatables',
                r'DataTable\(',
                r'dataTables'
            ],
            'jquery': [
                r'jquery',
                r'\$\(',
                r'jQuery'
            ]
        }
        
        # 功能模組識別模式
        self.module_patterns = {
            'dashboard': [
                r'dashboard',
                r'儀表板',
                r'總覽',
                r'overview'
            ],
            'user_management': [
                r'user.*management',
                r'用戶管理',
                r'會員管理',
                r'member.*management'
            ],
            'analytics': [
                r'analytics',
                r'分析',
                r'統計',
                r'報表',
                r'chart'
            ],
            'payment': [
                r'payment',
                r'支付',
                r'付款',
                r'billing'
            ],
            'content': [
                r'content.*management',
                r'內容管理',
                r'文章管理',
                r'cms'
            ],
            'system': [
                r'system.*config',
                r'系統設置',
                r'配置',
                r'settings'
            ]
        }
    
    def scan_admin_files(self) -> List[str]:
        """掃描所有管理後台文件"""
        logger.info("開始掃描管理後台文件...")
        
        admin_files = []
        
        # 掃描根目錄的admin文件
        for pattern in ["admin_complete.html", "admin_enhanced.html", "admin_ultimate.html"]:
            file_path = self.workspace_root / pattern
            if file_path.exists():
                admin_files.append(str(file_path))
                logger.info(f"找到文件: {file_path}")
        
        # 掃描complete_admin_system目錄
        complete_admin_dir = self.workspace_root / "complete_admin_system"
        if complete_admin_dir.exists():
            for file_path in complete_admin_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.html', '.js', '.css']:
                    admin_files.append(str(file_path))
                    logger.info(f"找到文件: {file_path}")
        
        # 掃描TradingAgents目錄的admin文件
        trading_agents_dir = self.workspace_root / "TradingAgents"
        if trading_agents_dir.exists():
            for pattern in ["functional_admin.html", "functional_admin.js", "functional_admin.css"]:
                file_path = trading_agents_dir / pattern
                if file_path.exists():
                    admin_files.append(str(file_path))
                    logger.info(f"找到文件: {file_path}")
            
            # 掃描其他admin相關文件
            for file_path in trading_agents_dir.glob("*admin*.html"):
                if file_path.is_file():
                    admin_files.append(str(file_path))
                    logger.info(f"找到文件: {file_path}")
        
        self.admin_files = admin_files
        logger.info(f"總共找到 {len(admin_files)} 個管理後台文件")
        return admin_files
    
    def analyze_file_content(self, file_path: str) -> Dict[str, Any]:
        """分析單個文件的內容和特性"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                logger.warning(f"無法讀取文件: {file_path}")
                return {}
        
        file_info = {
            'path': file_path,
            'size': len(content),
            'lines': len(content.splitlines()),
            'content': content,
            'hash': hashlib.md5(content.encode()).hexdigest()
        }
        
        return file_info
    
    def identify_tech_stack(self, content: str) -> TechStackInfo:
        """識別技術棧"""
        tech_stack = TechStackInfo()
        dependencies = []
        
        # 檢測React
        for pattern in self.tech_patterns['react']:
            if re.search(pattern, content, re.IGNORECASE):
                tech_stack.framework = "React"
                dependencies.append("React")
                break
        
        # 檢測Bootstrap
        for pattern in self.tech_patterns['bootstrap']:
            if re.search(pattern, content, re.IGNORECASE):
                tech_stack.css_framework = "Bootstrap"
                dependencies.append("Bootstrap")
                # 提取版本號
                version_match = re.search(r'bootstrap@([\d.]+)', content)
                if version_match:
                    tech_stack.css_framework += f" {version_match.group(1)}"
                break
        
        # 檢測Chart.js
        for pattern in self.tech_patterns['chart_js']:
            if re.search(pattern, content, re.IGNORECASE):
                tech_stack.chart_library = "Chart.js"
                dependencies.append("Chart.js")
                break
        
        # 檢測Font Awesome
        for pattern in self.tech_patterns['font_awesome']:
            if re.search(pattern, content, re.IGNORECASE):
                tech_stack.ui_library = "Font Awesome"
                dependencies.append("Font Awesome")
                break
        
        # 檢測DataTables
        for pattern in self.tech_patterns['datatables']:
            if re.search(pattern, content, re.IGNORECASE):
                dependencies.append("DataTables")
                break
        
        # 檢測jQuery
        for pattern in self.tech_patterns['jquery']:
            if re.search(pattern, content, re.IGNORECASE):
                dependencies.append("jQuery")
                break
        
        # 檢測JavaScript版本
        if 'const ' in content or 'let ' in content or '=>' in content:
            tech_stack.javascript_version = "ES6+"
        elif 'var ' in content:
            tech_stack.javascript_version = "ES5"
        
        tech_stack.dependencies = dependencies
        return tech_stack
    
    def identify_functional_modules(self, content: str) -> List[FunctionalModule]:
        """識別功能模組"""
        modules = []
        
        for module_name, patterns in self.module_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # 計算複雜度
                    pattern_count = len(re.findall(pattern, content, re.IGNORECASE))
                    if pattern_count > 10:
                        complexity = "high"
                    elif pattern_count > 5:
                        complexity = "medium"
                    else:
                        complexity = "low"
                    
                    module = FunctionalModule(
                        name=module_name,
                        description=f"檢測到 {pattern_count} 個相關功能",
                        complexity=complexity
                    )
                    modules.append(module)
                    break
        
        return modules
    
    def calculate_code_quality(self, file_info: Dict[str, Any]) -> CodeQualityMetrics:
        """計算代碼質量指標"""
        content = file_info['content']
        
        # 基本指標
        metrics = CodeQualityMetrics(
            file_size=file_info['size'],
            line_count=file_info['lines']
        )
        
        # 計算函數數量
        function_patterns = [
            r'function\s+\w+',
            r'\w+\s*:\s*function',
            r'const\s+\w+\s*=\s*\(',
            r'let\s+\w+\s*=\s*\(',
            r'=>'
        ]
        
        for pattern in function_patterns:
            metrics.function_count += len(re.findall(pattern, content))
        
        # 計算類數量
        class_patterns = [
            r'class\s+\w+',
            r'React\.Component',
            r'Component\s*{'
        ]
        
        for pattern in class_patterns:
            metrics.class_count += len(re.findall(pattern, content))
        
        # 複雜度評分 (基於文件大小和結構)
        if metrics.file_size > 50000:  # 50KB以上
            metrics.complexity_score = 0.9
        elif metrics.file_size > 20000:  # 20KB以上
            metrics.complexity_score = 0.7
        elif metrics.file_size > 10000:  # 10KB以上
            metrics.complexity_score = 0.5
        else:
            metrics.complexity_score = 0.3
        
        # 可維護性評分 (基於函數和類的組織)
        if metrics.function_count > 20 and metrics.class_count > 5:
            metrics.maintainability_score = 0.8
        elif metrics.function_count > 10:
            metrics.maintainability_score = 0.6
        else:
            metrics.maintainability_score = 0.4
        
        # 文檔評分 (基於註釋)
        comment_lines = len(re.findall(r'//.*|/\*.*?\*/|<!--.*?-->', content, re.DOTALL))
        if comment_lines > metrics.line_count * 0.1:  # 10%以上是註釋
            metrics.documentation_score = 0.8
        elif comment_lines > metrics.line_count * 0.05:  # 5%以上是註釋
            metrics.documentation_score = 0.6
        else:
            metrics.documentation_score = 0.3
        
        # 設計模式評分 (基於代碼結構)
        design_patterns = [
            r'class\s+\w+.*extends',  # 繼承
            r'interface\s+\w+',       # 接口
            r'factory',               # 工廠模式
            r'singleton',             # 單例模式
            r'observer',              # 觀察者模式
        ]
        
        pattern_count = 0
        for pattern in design_patterns:
            pattern_count += len(re.findall(pattern, content, re.IGNORECASE))
        
        metrics.design_pattern_score = min(pattern_count * 0.2, 1.0)
        
        return metrics
    
    def calculate_maturity_score(self, tech_stack: TechStackInfo, 
                                modules: List[FunctionalModule], 
                                quality: CodeQualityMetrics) -> float:
        """計算技術成熟度評分"""
        score = 0.0
        
        # 技術棧評分 (40%)
        tech_score = 0.0
        if tech_stack.framework == "React":
            tech_score += 0.3
        if "Bootstrap" in tech_stack.css_framework:
            tech_score += 0.2
        if tech_stack.chart_library:
            tech_score += 0.2
        if tech_stack.javascript_version == "ES6+":
            tech_score += 0.2
        if len(tech_stack.dependencies) >= 3:
            tech_score += 0.1
        
        score += tech_score * 0.4
        
        # 功能完整性評分 (30%)
        module_score = min(len(modules) * 0.15, 1.0)
        score += module_score * 0.3
        
        # 代碼質量評分 (30%)
        quality_score = (
            quality.complexity_score * 0.3 +
            quality.maintainability_score * 0.3 +
            quality.documentation_score * 0.2 +
            quality.design_pattern_score * 0.2
        )
        score += quality_score * 0.3
        
        return min(score, 1.0)
    
    def analyze_version(self, file_path: str) -> AdminVersion:
        """分析單個版本"""
        logger.info(f"分析版本: {file_path}")
        
        # 獲取文件信息
        file_info = self.analyze_file_content(file_path)
        if not file_info:
            return None
        
        # 識別技術棧
        tech_stack = self.identify_tech_stack(file_info['content'])
        
        # 識別功能模組
        modules = self.identify_functional_modules(file_info['content'])
        
        # 計算代碼質量
        quality = self.calculate_code_quality(file_info)
        
        # 計算成熟度評分
        maturity_score = self.calculate_maturity_score(tech_stack, modules, quality)
        
        # 獲取文件修改時間
        try:
            mtime = os.path.getmtime(file_path)
            last_modified = datetime.fromtimestamp(mtime).isoformat()
        except:
            last_modified = ""
        
        # 創建版本對象
        version = AdminVersion(
            name=Path(file_path).name,
            path=file_path,
            tech_stack=tech_stack,
            functional_modules=modules,
            code_quality=quality,
            maturity_score=maturity_score,
            last_modified=last_modified,
            file_hash=file_info['hash']
        )
        
        return version
    
    def analyze_all_versions(self) -> Dict[str, AdminVersion]:
        """分析所有版本"""
        logger.info("開始分析所有管理後台版本...")
        
        # 掃描文件
        self.scan_admin_files()
        
        # 分析每個版本
        results = {}
        for file_path in self.admin_files:
            version = self.analyze_version(file_path)
            if version:
                results[version.name] = version
        
        self.analysis_results = results
        logger.info(f"完成分析，共 {len(results)} 個版本")
        
        return results
    
    def generate_recommendation(self) -> Dict[str, Any]:
        """生成版本推薦"""
        if not self.analysis_results:
            return {}
        
        # 按成熟度評分排序
        sorted_versions = sorted(
            self.analysis_results.values(),
            key=lambda v: v.maturity_score,
            reverse=True
        )
        
        recommendation = {
            'best_version': sorted_versions[0].name if sorted_versions else None,
            'ranking': [
                {
                    'name': v.name,
                    'score': v.maturity_score,
                    'tech_stack': v.tech_stack.framework or "Unknown",
                    'modules_count': len(v.functional_modules),
                    'file_size': v.code_quality.file_size
                }
                for v in sorted_versions
            ],
            'summary': {
                'total_versions': len(self.analysis_results),
                'average_score': sum(v.maturity_score for v in self.analysis_results.values()) / len(self.analysis_results),
                'best_score': sorted_versions[0].maturity_score if sorted_versions else 0
            }
        }
        
        return recommendation
    
    def export_analysis_report(self, output_file: str = "admin_system_analysis_report.json") -> str:
        """導出分析報告"""
        if not self.analysis_results:
            logger.warning("沒有分析結果可導出")
            return ""
        
        # 準備導出數據
        export_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'workspace_root': str(self.workspace_root),
            'total_files_analyzed': len(self.analysis_results),
            'versions': {},
            'recommendation': self.generate_recommendation()
        }
        
        # 轉換版本數據
        for name, version in self.analysis_results.items():
            export_data['versions'][name] = {
                'name': version.name,
                'path': version.path,
                'tech_stack': asdict(version.tech_stack),
                'functional_modules': [asdict(m) for m in version.functional_modules],
                'code_quality': asdict(version.code_quality),
                'maturity_score': version.maturity_score,
                'last_modified': version.last_modified,
                'file_hash': version.file_hash
            }
        
        # 寫入文件
        output_path = self.workspace_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析報告已導出到: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """打印分析摘要"""
        if not self.analysis_results:
            print("沒有分析結果")
            return
        
        print("\n" + "="*60)
        print("管理後台版本分析摘要")
        print("="*60)
        
        recommendation = self.generate_recommendation()
        
        print(f"總版本數: {recommendation['summary']['total_versions']}")
        print(f"平均評分: {recommendation['summary']['average_score']:.2f}")
        print(f"最高評分: {recommendation['summary']['best_score']:.2f}")
        print(f"推薦版本: {recommendation['best_version']}")
        
        print("\n版本排名:")
        print("-" * 60)
        for i, version in enumerate(recommendation['ranking'], 1):
            print(f"{i}. {version['name']}")
            print(f"   評分: {version['score']:.2f}")
            print(f"   技術棧: {version['tech_stack']}")
            print(f"   功能模組: {version['modules_count']} 個")
            print(f"   文件大小: {version['file_size']:,} bytes")
            print()

def main():
    """主函數"""
    print("管理後台版本分析系統")
    print("=" * 40)
    
    # 創建分析器
    analyzer = AdminVersionAnalyzer()
    
    # 執行分析
    try:
        results = analyzer.analyze_all_versions()
        
        # 打印摘要
        analyzer.print_summary()
        
        # 導出報告
        report_file = analyzer.export_analysis_report()
        print(f"\n詳細報告已保存到: {report_file}")
        
    except Exception as e:
        logger.error(f"分析過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()