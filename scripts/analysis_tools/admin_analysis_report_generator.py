#!/usr/bin/env python3
"""
管理後台分析報告生成器
生成詳細的Markdown格式分析報告
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class AdminAnalysisReportGenerator:
    """管理後台分析報告生成器"""
    
    def __init__(self, analysis_file: str = "admin_system_analysis_report.json"):
        self.analysis_file = analysis_file
        self.analysis_data = None
        self.load_analysis_data()
    
    def load_analysis_data(self):
        """載入分析數據"""
        if os.path.exists(self.analysis_file):
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                self.analysis_data = json.load(f)
        else:
            raise FileNotFoundError(f"分析文件不存在: {self.analysis_file}")
    
    def generate_markdown_report(self, output_file: str = "admin_system_analysis_report.md") -> str:
        """生成Markdown格式的分析報告"""
        if not self.analysis_data:
            return ""
        
        report_lines = []
        
        # 報告標題
        report_lines.extend([
            "# 管理後台系統版本分析報告",
            "",
            f"**分析時間**: {self.analysis_data['analysis_timestamp']}",
            f"**工作目錄**: {self.analysis_data['workspace_root']}",
            f"**分析文件數**: {self.analysis_data['total_files_analyzed']}",
            ""
        ])
        
        # 執行摘要
        recommendation = self.analysis_data['recommendation']
        report_lines.extend([
            "## 📊 執行摘要",
            "",
            f"- **總版本數**: {recommendation['summary']['total_versions']}",
            f"- **平均評分**: {recommendation['summary']['average_score']:.2f}",
            f"- **最高評分**: {recommendation['summary']['best_score']:.2f}",
            f"- **推薦版本**: `{recommendation['best_version']}`",
            ""
        ])
        
        # 版本排名
        report_lines.extend([
            "## 🏆 版本排名",
            "",
            "| 排名 | 版本名稱 | 評分 | 技術棧 | 功能模組 | 文件大小 |",
            "|------|----------|------|--------|----------|----------|"
        ])
        
        for i, version in enumerate(recommendation['ranking'], 1):
            size_kb = version['file_size'] / 1024
            report_lines.append(
                f"| {i} | `{version['name']}` | {version['score']:.2f} | "
                f"{version['tech_stack']} | {version['modules_count']} | {size_kb:.1f}KB |"
            )
        
        report_lines.append("")
        
        # 詳細版本分析
        report_lines.extend([
            "## 📋 詳細版本分析",
            ""
        ])
        
        # 按評分排序版本
        sorted_versions = sorted(
            self.analysis_data['versions'].items(),
            key=lambda x: x[1]['maturity_score'],
            reverse=True
        )
        
        for name, version in sorted_versions:
            report_lines.extend(self._generate_version_section(name, version))
        
        # 技術棧統計
        report_lines.extend(self._generate_tech_stack_analysis())
        
        # 功能模組統計
        report_lines.extend(self._generate_module_analysis())
        
        # 建議和結論
        report_lines.extend(self._generate_recommendations())
        
        # 寫入文件
        report_content = "\n".join(report_lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_file
    
    def _generate_version_section(self, name: str, version: Dict[str, Any]) -> list:
        """生成單個版本的詳細分析"""
        lines = [
            f"### {name}",
            "",
            f"**路徑**: `{version['path']}`",
            f"**評分**: {version['maturity_score']:.2f}",
            f"**最後修改**: {version['last_modified'][:19] if version['last_modified'] else 'Unknown'}",
            ""
        ]
        
        # 技術棧信息
        tech_stack = version['tech_stack']
        lines.extend([
            "#### 🔧 技術棧",
            "",
            f"- **框架**: {tech_stack['framework'] or 'Unknown'}",
            f"- **CSS框架**: {tech_stack['css_framework'] or 'None'}",
            f"- **UI庫**: {tech_stack['ui_library'] or 'None'}",
            f"- **圖表庫**: {tech_stack['chart_library'] or 'None'}",
            f"- **JavaScript版本**: {tech_stack['javascript_version'] or 'Unknown'}",
            f"- **依賴項**: {', '.join(tech_stack['dependencies']) if tech_stack['dependencies'] else 'None'}",
            ""
        ])
        
        # 功能模組
        if version['functional_modules']:
            lines.extend([
                "#### 📦 功能模組",
                ""
            ])
            
            for module in version['functional_modules']:
                lines.append(f"- **{module['name']}**: {module['description']} (複雜度: {module['complexity']})")
            
            lines.append("")
        
        # 代碼質量指標
        quality = version['code_quality']
        lines.extend([
            "#### 📈 代碼質量指標",
            "",
            f"- **文件大小**: {quality['file_size']:,} bytes ({quality['file_size']/1024:.1f}KB)",
            f"- **代碼行數**: {quality['line_count']:,}",
            f"- **函數數量**: {quality['function_count']}",
            f"- **類數量**: {quality['class_count']}",
            f"- **複雜度評分**: {quality['complexity_score']:.2f}",
            f"- **可維護性評分**: {quality['maintainability_score']:.2f}",
            f"- **文檔評分**: {quality['documentation_score']:.2f}",
            f"- **設計模式評分**: {quality['design_pattern_score']:.2f}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_tech_stack_analysis(self) -> list:
        """生成技術棧統計分析"""
        lines = [
            "## 🔧 技術棧統計分析",
            ""
        ]
        
        # 統計各技術棧使用情況
        frameworks = {}
        css_frameworks = {}
        ui_libraries = {}
        chart_libraries = {}
        
        for version in self.analysis_data['versions'].values():
            tech = version['tech_stack']
            
            # 統計框架
            framework = tech['framework'] or 'Unknown'
            frameworks[framework] = frameworks.get(framework, 0) + 1
            
            # 統計CSS框架
            css_fw = tech['css_framework'] or 'None'
            css_frameworks[css_fw] = css_frameworks.get(css_fw, 0) + 1
            
            # 統計UI庫
            ui_lib = tech['ui_library'] or 'None'
            ui_libraries[ui_lib] = ui_libraries.get(ui_lib, 0) + 1
            
            # 統計圖表庫
            chart_lib = tech['chart_library'] or 'None'
            chart_libraries[chart_lib] = chart_libraries.get(chart_lib, 0) + 1
        
        # 生成統計表格
        lines.extend([
            "### JavaScript框架使用統計",
            "",
            "| 框架 | 使用次數 | 佔比 |",
            "|------|----------|------|"
        ])
        
        total_versions = len(self.analysis_data['versions'])
        for framework, count in sorted(frameworks.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_versions) * 100
            lines.append(f"| {framework} | {count} | {percentage:.1f}% |")
        
        lines.extend([
            "",
            "### CSS框架使用統計",
            "",
            "| CSS框架 | 使用次數 | 佔比 |",
            "|---------|----------|------|"
        ])
        
        for css_fw, count in sorted(css_frameworks.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_versions) * 100
            lines.append(f"| {css_fw} | {count} | {percentage:.1f}% |")
        
        lines.append("")
        
        return lines
    
    def _generate_module_analysis(self) -> list:
        """生成功能模組統計分析"""
        lines = [
            "## 📦 功能模組統計分析",
            ""
        ]
        
        # 統計功能模組
        module_stats = {}
        complexity_stats = {'low': 0, 'medium': 0, 'high': 0}
        
        for version in self.analysis_data['versions'].values():
            for module in version['functional_modules']:
                module_name = module['name']
                module_stats[module_name] = module_stats.get(module_name, 0) + 1
                complexity_stats[module['complexity']] += 1
        
        lines.extend([
            "### 功能模組分布",
            "",
            "| 模組名稱 | 出現次數 | 覆蓋率 |",
            "|----------|----------|--------|"
        ])
        
        total_versions = len(self.analysis_data['versions'])
        for module_name, count in sorted(module_stats.items(), key=lambda x: x[1], reverse=True):
            coverage = (count / total_versions) * 100
            lines.append(f"| {module_name} | {count} | {coverage:.1f}% |")
        
        lines.extend([
            "",
            "### 複雜度分布",
            "",
            "| 複雜度 | 模組數量 | 佔比 |",
            "|--------|----------|------|"
        ])
        
        total_modules = sum(complexity_stats.values())
        for complexity, count in complexity_stats.items():
            percentage = (count / total_modules) * 100 if total_modules > 0 else 0
            lines.append(f"| {complexity} | {count} | {percentage:.1f}% |")
        
        lines.append("")
        
        return lines
    
    def _generate_recommendations(self) -> list:
        """生成建議和結論"""
        lines = [
            "## 💡 建議和結論",
            ""
        ]
        
        recommendation = self.analysis_data['recommendation']
        best_version = recommendation['best_version']
        
        if best_version:
            best_version_data = self.analysis_data['versions'][best_version]
            
            lines.extend([
                "### 🎯 主要發現",
                "",
                f"1. **推薦版本**: `{best_version}` 獲得最高評分 {best_version_data['maturity_score']:.2f}",
                f"2. **技術優勢**: 該版本使用 {best_version_data['tech_stack']['framework']} 框架，具有現代化的技術棧",
                f"3. **功能完整性**: 包含 {len(best_version_data['functional_modules'])} 個功能模組",
                f"4. **代碼質量**: 代碼結構良好，可維護性評分 {best_version_data['code_quality']['maintainability_score']:.2f}",
                ""
            ])
        
        lines.extend([
            "### 📋 開發建議",
            "",
            "1. **統一技術棧**: 建議以推薦版本為基礎，統一所有管理後台的技術架構",
            "2. **功能整合**: 將其他版本的優秀功能模組整合到主版本中",
            "3. **代碼重構**: 對評分較低的版本進行代碼重構，提升可維護性",
            "4. **文檔完善**: 增加代碼註釋和文檔，提升團隊協作效率",
            "5. **測試覆蓋**: 建立完整的測試體系，確保系統穩定性",
            "",
            "### 🚀 下一步行動",
            "",
            "1. 確定主要開發版本",
            "2. 制定功能整合計劃",
            "3. 建立統一的開發規範",
            "4. 實施代碼質量監控",
            "5. 定期進行版本分析和評估",
            ""
        ])
        
        return lines

def main():
    """主函數"""
    print("生成管理後台分析報告...")
    
    try:
        generator = AdminAnalysisReportGenerator()
        report_file = generator.generate_markdown_report()
        print(f"Markdown報告已生成: {report_file}")
        
    except Exception as e:
        print(f"生成報告時發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()