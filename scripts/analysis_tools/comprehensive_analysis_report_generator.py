#!/usr/bin/env python3
"""
綜合分析報告生成器
生成包含版本分析、API掃描和整合狀態的完整報告
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class ComprehensiveAnalysisReportGenerator:
    """綜合分析報告生成器"""
    
    def __init__(self):
        self.admin_analysis = None
        self.api_analysis = None
        self.integration_analysis = None
        
    def load_all_analyses(self):
        """載入所有分析結果"""
        # 載入管理後台版本分析
        if os.path.exists("admin_system_analysis_report.json"):
            with open("admin_system_analysis_report.json", 'r', encoding='utf-8') as f:
                self.admin_analysis = json.load(f)
        
        # 載入API分析
        if os.path.exists("backend_api_analysis_report.json"):
            with open("backend_api_analysis_report.json", 'r', encoding='utf-8') as f:
                self.api_analysis = json.load(f)
        
        # 載入整合分析
        if os.path.exists("frontend_api_integration_report.json"):
            with open("frontend_api_integration_report.json", 'r', encoding='utf-8') as f:
                self.integration_analysis = json.load(f)
    
    def generate_comprehensive_report(self, output_file: str = "comprehensive_admin_analysis_report.md") -> str:
        """生成綜合分析報告"""
        self.load_all_analyses()
        
        report_lines = [
            "# 管理後台系統綜合分析報告",
            "",
            f"**生成時間**: {datetime.now().isoformat()}",
            f"**分析範圍**: 版本分析 + API掃描 + 整合狀態分析",
            ""
        ]
        
        # 執行摘要
        report_lines.extend(self._generate_executive_summary())
        
        # 版本分析部分
        if self.admin_analysis:
            report_lines.extend(self._generate_version_analysis_section())
        
        # API分析部分
        if self.api_analysis:
            report_lines.extend(self._generate_api_analysis_section())
        
        # 整合分析部分
        if self.integration_analysis:
            report_lines.extend(self._generate_integration_analysis_section())
        
        # 綜合建議
        report_lines.extend(self._generate_comprehensive_recommendations())
        
        # 寫入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        return output_file 
   
    def _generate_executive_summary(self) -> list:
        """生成執行摘要"""
        lines = [
            "## 📊 執行摘要",
            ""
        ]
        
        if self.admin_analysis:
            recommendation = self.admin_analysis.get('recommendation', {})
            lines.extend([
                f"- **管理後台版本數**: {recommendation.get('summary', {}).get('total_versions', 0)}",
                f"- **推薦版本**: `{recommendation.get('best_version', 'Unknown')}`",
                f"- **平均技術成熟度**: {recommendation.get('summary', {}).get('average_score', 0):.2f}",
            ])
        
        if self.api_analysis:
            stats = self.api_analysis.get('statistics', {})
            lines.extend([
                f"- **後端API端點總數**: {stats.get('total_endpoints', 0)}",
                f"- **API分類數**: {len(stats.get('categories', {}))}",
            ])
        
        if self.integration_analysis:
            summary = self.integration_analysis.get('summary', {})
            lines.extend([
                f"- **平均API覆蓋率**: {summary.get('average_coverage_rate', 0):.1%}",
                f"- **最佳整合版本**: `{summary.get('best_integration_version', 'Unknown')}`",
            ])
        
        lines.append("")
        return lines
    
    def _generate_version_analysis_section(self) -> list:
        """生成版本分析部分"""
        lines = [
            "## 🏆 管理後台版本分析",
            ""
        ]
        
        recommendation = self.admin_analysis.get('recommendation', {})
        ranking = recommendation.get('ranking', [])
        
        if ranking:
            lines.extend([
                "### 版本排名 (按技術成熟度)",
                "",
                "| 排名 | 版本名稱 | 評分 | 技術棧 | 功能模組 | 文件大小 |",
                "|------|----------|------|--------|----------|----------|"
            ])
            
            for i, version in enumerate(ranking[:10], 1):  # 只顯示前10名
                size_kb = version['file_size'] / 1024
                lines.append(
                    f"| {i} | `{version['name']}` | {version['score']:.2f} | "
                    f"{version['tech_stack']} | {version['modules_count']} | {size_kb:.1f}KB |"
                )
            
            lines.append("")
        
        return lines
    
    def _generate_api_analysis_section(self) -> list:
        """生成API分析部分"""
        lines = [
            "## 🔧 後端API功能分析",
            ""
        ]
        
        stats = self.api_analysis.get('statistics', {})
        categories = stats.get('categories', {})
        
        if categories:
            lines.extend([
                "### API分類統計",
                "",
                "| 分類 | 端點數量 | 佔比 |",
                "|------|----------|------|"
            ])
            
            total_endpoints = stats.get('total_endpoints', 0)
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_endpoints * 100) if total_endpoints > 0 else 0
                category_desc = self.api_analysis.get('category_descriptions', {}).get(category, category)
                lines.append(f"| {category_desc} | {count} | {percentage:.1f}% |")
            
            lines.append("")
        
        return lines
    
    def _generate_integration_analysis_section(self) -> list:
        """生成整合分析部分"""
        lines = [
            "## 🔗 前端API整合狀態分析",
            ""
        ]
        
        if not self.integration_analysis:
            lines.append("*整合分析數據不可用*")
            return lines
        
        summary = self.integration_analysis.get('summary', {})
        integration_data = self.integration_analysis.get('integration_analysis', {})
        
        lines.extend([
            "### 整合狀態概覽",
            "",
            f"- **平均API覆蓋率**: {summary.get('average_coverage_rate', 0):.1%}",
            f"- **平均整合質量**: {summary.get('average_quality_score', 0):.2f}",
            f"- **最佳整合版本**: `{summary.get('best_integration_version', 'Unknown')}`",
            ""
        ])
        
        if integration_data:
            lines.extend([
                "### 版本整合排名",
                "",
                "| 排名 | 版本名稱 | API調用數 | 覆蓋率 | 質量分數 |",
                "|------|----------|-----------|--------|----------|"
            ])
            
            # 按綜合分數排序
            sorted_versions = sorted(
                integration_data.items(),
                key=lambda x: x[1]['api_coverage_rate'] + x[1]['integration_quality_score'],
                reverse=True
            )
            
            for i, (version_name, data) in enumerate(sorted_versions[:10], 1):
                lines.append(
                    f"| {i} | `{version_name}` | {data['total_api_calls']} | "
                    f"{data['api_coverage_rate']:.1%} | {data['integration_quality_score']:.2f} |"
                )
            
            lines.append("")
        
        return lines
    
    def _generate_comprehensive_recommendations(self) -> list:
        """生成綜合建議"""
        lines = [
            "## 💡 綜合建議和行動計劃",
            ""
        ]
        
        # 基於分析結果的建議
        best_version = None
        if self.admin_analysis:
            best_version = self.admin_analysis.get('recommendation', {}).get('best_version')
        
        lines.extend([
            "### 🎯 主要發現",
            ""
        ])
        
        if best_version:
            lines.append(f"1. **推薦主版本**: `{best_version}` 在技術成熟度方面表現最佳")
        
        if self.api_analysis:
            total_apis = self.api_analysis.get('statistics', {}).get('total_endpoints', 0)
            lines.append(f"2. **API資源豐富**: 系統擁有 {total_apis} 個API端點，功能覆蓋全面")
        
        if self.integration_analysis:
            avg_coverage = self.integration_analysis.get('summary', {}).get('average_coverage_rate', 0)
            if avg_coverage < 0.1:  # 10%以下
                lines.append("3. **整合不足**: 前端版本與後端API整合程度較低，需要加強")
        
        lines.extend([
            "",
            "### 📋 行動計劃",
            "",
            "#### 第一階段：版本統一 (1-2週)",
            "1. 確定主要開發版本 (建議使用推薦版本)",
            "2. 分析其他版本的優秀功能",
            "3. 制定功能整合計劃",
            "",
            "#### 第二階段：API整合 (2-4週)",
            "1. 優先整合高價值API端點",
            "2. 實現完整的錯誤處理機制",
            "3. 添加載入狀態和用戶反饋",
            "",
            "#### 第三階段：質量提升 (2-3週)",
            "1. 統一代碼風格和架構",
            "2. 增加測試覆蓋率",
            "3. 優化用戶體驗",
            "",
            "### 🚀 技術建議",
            "",
            "1. **採用現代化技術棧**: 基於分析結果，建議使用React + Bootstrap的組合",
            "2. **建立API客戶端**: 創建統一的API調用層，提高整合效率",
            "3. **實施錯誤處理**: 為所有API調用添加完整的錯誤處理機制",
            "4. **添加載入狀態**: 改善用戶體驗，提供清晰的操作反饋",
            "5. **建立測試體系**: 確保系統穩定性和可維護性",
            "",
            "### ⚠️ 風險提醒",
            "",
            "1. **避免重複開發**: 充分利用現有版本的優秀功能",
            "2. **保持向後兼容**: 確保整合過程不影響現有功能",
            "3. **分階段實施**: 避免一次性大規模改動帶來的風險",
            "4. **充分測試**: 每個階段都要進行充分的測試驗證",
            ""
        ])
        
        return lines

def main():
    """主函數"""
    print("生成綜合分析報告...")
    
    try:
        generator = ComprehensiveAnalysisReportGenerator()
        report_file = generator.generate_comprehensive_report()
        print(f"綜合分析報告已生成: {report_file}")
        
    except Exception as e:
        print(f"生成報告時發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()