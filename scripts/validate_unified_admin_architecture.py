#!/usr/bin/env python3
"""
統一管理後台架構驗證器
驗證生成的架構是否完整且符合要求
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

class UnifiedAdminArchitectureValidator:
    """統一管理後台架構驗證器"""
    
    def __init__(self):
        self.admin_path = "TradingAgents/frontend/src/admin"
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "pending",
            "checks": {},
            "statistics": {},
            "recommendations": []
        }
    
    def validate_complete_architecture(self):
        """驗證完整架構"""
        print("🔍 開始驗證統一管理後台架構...")
        print(f"📅 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 驗證目錄結構
            print("\n📁 驗證目錄結構...")
            self._validate_directory_structure()
            
            # 2. 驗證文件完整性
            print("\n📄 驗證文件完整性...")
            self._validate_file_completeness()
            
            # 3. 驗證TypeScript類型
            print("\n📝 驗證TypeScript類型...")
            self._validate_typescript_types()
            
            # 4. 驗證服務層
            print("\n🔧 驗證服務層...")
            self._validate_services()
            
            # 5. 驗證組件結構
            print("\n🧩 驗證組件結構...")
            self._validate_components()
            
            # 6. 驗證配置文件
            print("\n⚙️ 驗證配置文件...")
            self._validate_configuration()
            
            # 7. 生成統計信息
            print("\n📊 生成統計信息...")
            self._generate_statistics()
            
            # 8. 生成建議
            print("\n💡 生成改進建議...")
            self._generate_recommendations()
            
            # 確定整體狀態
            self._determine_overall_status()
            
            # 9. 生成驗證報告
            print("\n📋 生成驗證報告...")
            self._generate_validation_report()
            
            print(f"\n✅ 架構驗證完成！整體狀態: {self.validation_results['overall_status']}")
            
        except Exception as e:
            print(f"\n❌ 驗證過程中發生錯誤: {e}")
            self.validation_results["overall_status"] = "error"
            self.validation_results["error"] = str(e)
            raise
    
    def _validate_directory_structure(self):
        """驗證目錄結構"""
        required_directories = [
            "components",
            "components/common",
            "components/dashboard", 
            "components/users",
            "components/analytics",
            "components/content",
            "components/financial",
            "services",
            "hooks",
            "types",
            "utils",
            "config",
            "styles",
            "assets"
        ]
        
        missing_dirs = []
        existing_dirs = []
        
        for directory in required_directories:
            full_path = os.path.join(self.admin_path, directory)
            if os.path.exists(full_path):
                existing_dirs.append(directory)
                print(f"  ✅ {directory}")
            else:
                missing_dirs.append(directory)
                print(f"  ❌ {directory} (缺失)")
        
        self.validation_results["checks"]["directory_structure"] = {
            "status": "pass" if not missing_dirs else "fail",
            "existing_directories": existing_dirs,
            "missing_directories": missing_dirs,
            "total_required": len(required_directories),
            "total_existing": len(existing_dirs)
        }
    
    def _validate_file_completeness(self):
        """驗證文件完整性"""
        required_files = [
            "types/AdminTypes.ts",
            "types/ComponentTypes.ts", 
            "services/AdminApiService.ts",
            "services/NotificationService.ts",
            "hooks/useAdminHooks.ts",
            "components/AdminLayout.tsx",
            "components/common/DataTable.tsx",
            "config/AdminConfig.ts",
            "styles/admin.css",
            "README.md"
        ]
        
        missing_files = []
        existing_files = []
        file_sizes = {}
        
        for file_path in required_files:
            full_path = os.path.join(self.admin_path, file_path)
            if os.path.exists(full_path):
                existing_files.append(file_path)
                file_sizes[file_path] = os.path.getsize(full_path)
                print(f"  ✅ {file_path} ({file_sizes[file_path]} bytes)")
            else:
                missing_files.append(file_path)
                print(f"  ❌ {file_path} (缺失)")
        
        self.validation_results["checks"]["file_completeness"] = {
            "status": "pass" if not missing_files else "fail",
            "existing_files": existing_files,
            "missing_files": missing_files,
            "file_sizes": file_sizes,
            "total_required": len(required_files),
            "total_existing": len(existing_files)
        }
    
    def _validate_typescript_types(self):
        """驗證TypeScript類型"""
        type_files = [
            "types/AdminTypes.ts",
            "types/ComponentTypes.ts"
        ]
        
        type_validation = {}
        
        for type_file in type_files:
            full_path = os.path.join(self.admin_path, type_file)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查關鍵類型定義
                key_types = [
                    "interface",
                    "export",
                    "ApiResponse",
                    "User",
                    "SystemStatus"
                ]
                
                found_types = []
                for key_type in key_types:
                    if key_type in content:
                        found_types.append(key_type)
                
                type_validation[type_file] = {
                    "status": "pass" if len(found_types) >= 3 else "warning",
                    "found_types": found_types,
                    "content_length": len(content),
                    "lines": len(content.split('\n'))
                }
                
                print(f"  ✅ {type_file}: {len(found_types)}/{len(key_types)} 關鍵類型")
            else:
                type_validation[type_file] = {
                    "status": "fail",
                    "error": "文件不存在"
                }
                print(f"  ❌ {type_file}: 文件不存在")
        
        self.validation_results["checks"]["typescript_types"] = type_validation
    
    def _validate_services(self):
        """驗證服務層"""
        service_files = [
            "services/AdminApiService.ts",
            "services/NotificationService.ts"
        ]
        
        service_validation = {}
        
        for service_file in service_files:
            full_path = os.path.join(self.admin_path, service_file)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查關鍵服務功能
                key_features = [
                    "class",
                    "async",
                    "Promise",
                    "ApiResponse",
                    "constructor"
                ]
                
                found_features = []
                for feature in key_features:
                    if feature in content:
                        found_features.append(feature)
                
                service_validation[service_file] = {
                    "status": "pass" if len(found_features) >= 3 else "warning",
                    "found_features": found_features,
                    "content_length": len(content),
                    "lines": len(content.split('\n'))
                }
                
                print(f"  ✅ {service_file}: {len(found_features)}/{len(key_features)} 關鍵功能")
            else:
                service_validation[service_file] = {
                    "status": "fail",
                    "error": "文件不存在"
                }
                print(f"  ❌ {service_file}: 文件不存在")
        
        self.validation_results["checks"]["services"] = service_validation
    
    def _validate_components(self):
        """驗證組件結構"""
        component_files = [
            "components/AdminLayout.tsx",
            "components/common/DataTable.tsx"
        ]
        
        component_validation = {}
        
        for component_file in component_files:
            full_path = os.path.join(self.admin_path, component_file)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查React組件特徵
                react_features = [
                    "import React",
                    "interface",
                    "React.FC",
                    "export",
                    "return"
                ]
                
                found_features = []
                for feature in react_features:
                    if feature in content:
                        found_features.append(feature)
                
                component_validation[component_file] = {
                    "status": "pass" if len(found_features) >= 3 else "warning",
                    "found_features": found_features,
                    "content_length": len(content),
                    "lines": len(content.split('\n'))
                }
                
                print(f"  ✅ {component_file}: {len(found_features)}/{len(react_features)} React特徵")
            else:
                component_validation[component_file] = {
                    "status": "fail",
                    "error": "文件不存在"
                }
                print(f"  ❌ {component_file}: 文件不存在")
        
        self.validation_results["checks"]["components"] = component_validation
    
    def _validate_configuration(self):
        """驗證配置文件"""
        config_file = "config/AdminConfig.ts"
        full_path = os.path.join(self.admin_path, config_file)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查配置項
            config_items = [
                "ADMIN_CONFIG",
                "API_BASE_URL",
                "THEME",
                "FEATURES",
                "export"
            ]
            
            found_items = []
            for item in config_items:
                if item in content:
                    found_items.append(item)
            
            self.validation_results["checks"]["configuration"] = {
                "status": "pass" if len(found_items) >= 3 else "warning",
                "found_items": found_items,
                "content_length": len(content),
                "lines": len(content.split('\n'))
            }
            
            print(f"  ✅ {config_file}: {len(found_items)}/{len(config_items)} 配置項")
        else:
            self.validation_results["checks"]["configuration"] = {
                "status": "fail",
                "error": "配置文件不存在"
            }
            print(f"  ❌ {config_file}: 文件不存在")
    
    def _generate_statistics(self):
        """生成統計信息"""
        total_files = 0
        total_lines = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.admin_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_files += 1
                total_size += os.path.getsize(file_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except:
                    pass
        
        self.validation_results["statistics"] = {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2),
            "average_file_size": round(total_size / total_files, 2) if total_files > 0 else 0
        }
        
        print(f"  📊 總文件數: {total_files}")
        print(f"  📊 總行數: {total_lines}")
        print(f"  📊 總大小: {self.validation_results['statistics']['total_size_kb']} KB")
    
    def _generate_recommendations(self):
        """生成改進建議"""
        recommendations = []
        
        # 檢查缺失的目錄
        if "directory_structure" in self.validation_results["checks"]:
            missing_dirs = self.validation_results["checks"]["directory_structure"].get("missing_directories", [])
            if missing_dirs:
                recommendations.append({
                    "type": "directory",
                    "priority": "high",
                    "message": f"需要創建缺失的目錄: {', '.join(missing_dirs)}"
                })
        
        # 檢查缺失的文件
        if "file_completeness" in self.validation_results["checks"]:
            missing_files = self.validation_results["checks"]["file_completeness"].get("missing_files", [])
            if missing_files:
                recommendations.append({
                    "type": "file",
                    "priority": "high", 
                    "message": f"需要創建缺失的文件: {', '.join(missing_files)}"
                })
        
        # 檢查文件大小
        if "file_completeness" in self.validation_results["checks"]:
            file_sizes = self.validation_results["checks"]["file_completeness"].get("file_sizes", {})
            small_files = [f for f, size in file_sizes.items() if size < 100]
            if small_files:
                recommendations.append({
                    "type": "content",
                    "priority": "medium",
                    "message": f"以下文件內容可能不完整: {', '.join(small_files)}"
                })
        
        # 添加功能建議
        recommendations.extend([
            {
                "type": "enhancement",
                "priority": "medium",
                "message": "建議添加單元測試文件"
            },
            {
                "type": "enhancement", 
                "priority": "low",
                "message": "建議添加Storybook組件文檔"
            },
            {
                "type": "enhancement",
                "priority": "medium", 
                "message": "建議實現具體的業務組件"
            }
        ])
        
        self.validation_results["recommendations"] = recommendations
        
        for rec in recommendations:
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"  {priority_icon} {rec['message']}")
    
    def _determine_overall_status(self):
        """確定整體狀態"""
        checks = self.validation_results["checks"]
        
        failed_checks = []
        warning_checks = []
        passed_checks = []
        
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict) and "status" in check_result:
                if check_result["status"] == "fail":
                    failed_checks.append(check_name)
                elif check_result["status"] == "warning":
                    warning_checks.append(check_name)
                else:
                    passed_checks.append(check_name)
            else:
                # 處理嵌套檢查結果
                for sub_check, sub_result in check_result.items():
                    if isinstance(sub_result, dict) and "status" in sub_result:
                        if sub_result["status"] == "fail":
                            failed_checks.append(f"{check_name}.{sub_check}")
                        elif sub_result["status"] == "warning":
                            warning_checks.append(f"{check_name}.{sub_check}")
                        else:
                            passed_checks.append(f"{check_name}.{sub_check}")
        
        if failed_checks:
            self.validation_results["overall_status"] = "fail"
        elif warning_checks:
            self.validation_results["overall_status"] = "warning"
        else:
            self.validation_results["overall_status"] = "pass"
        
        self.validation_results["check_summary"] = {
            "passed": len(passed_checks),
            "warnings": len(warning_checks),
            "failed": len(failed_checks),
            "total": len(passed_checks) + len(warning_checks) + len(failed_checks)
        }
    
    def _generate_validation_report(self):
        """生成驗證報告"""
        report_path = "unified_admin_architecture_validation_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"  📋 驗證報告已生成: {report_path}")
        
        # 生成Markdown報告
        markdown_report = self._generate_markdown_report()
        markdown_path = "unified_admin_architecture_validation_report.md"
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"  📋 Markdown報告已生成: {markdown_path}")
    
    def _generate_markdown_report(self) -> str:
        """生成Markdown格式的驗證報告"""
        stats = self.validation_results["statistics"]
        summary = self.validation_results["check_summary"]
        
        report = f"""# 統一管理後台架構驗證報告

## 驗證概要
- **驗證時間**: {self.validation_results['timestamp']}
- **整體狀態**: {self.validation_results['overall_status'].upper()}
- **通過檢查**: {summary['passed']}
- **警告檢查**: {summary['warnings']}
- **失敗檢查**: {summary['failed']}

## 統計信息
- **總文件數**: {stats['total_files']}
- **總代碼行數**: {stats['total_lines']}
- **總大小**: {stats['total_size_kb']} KB
- **平均文件大小**: {stats['average_file_size']} bytes

## 檢查結果詳情

### 目錄結構檢查
"""
        
        # 添加檢查結果詳情
        for check_name, check_result in self.validation_results["checks"].items():
            report += f"\n### {check_name.replace('_', ' ').title()}\n"
            
            if isinstance(check_result, dict) and "status" in check_result:
                status_icon = "✅" if check_result["status"] == "pass" else "⚠️" if check_result["status"] == "warning" else "❌"
                report += f"**狀態**: {status_icon} {check_result['status'].upper()}\n\n"
            
        # 添加建議
        report += "\n## 改進建議\n\n"
        for i, rec in enumerate(self.validation_results["recommendations"], 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            report += f"{i}. {priority_icon} **{rec['type'].title()}**: {rec['message']}\n"
        
        report += f"\n---\n*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return report

if __name__ == "__main__":
    validator = UnifiedAdminArchitectureValidator()
    validator.validate_complete_architecture()