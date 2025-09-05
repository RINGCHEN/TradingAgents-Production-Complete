#!/usr/bin/env python3
"""
統一管理後台架構生成器 - 主程序
整合所有部分並生成完整的統一管理後台架構
"""

import os
import sys
from datetime import datetime

# 導入所有生成器部分
sys.path.append('.')
from unified_admin_generator_part1 import UnifiedAdminArchitectureGenerator
from unified_admin_generator_part2 import TypeDefinitionsGenerator
from unified_admin_generator_part3 import ServicesGenerator
from unified_admin_generator_part4 import HooksGenerator
from unified_admin_generator_part5 import ComponentsGenerator

class UnifiedAdminGenerator:
    """統一管理後台生成器主類"""
    
    def __init__(self):
        self.base_path = "TradingAgents/frontend/src"
        self.admin_path = f"{self.base_path}/admin"
        
        # 初始化所有生成器
        self.architecture_gen = UnifiedAdminArchitectureGenerator()
        self.types_gen = TypeDefinitionsGenerator(self.base_path)
        self.services_gen = ServicesGenerator(self.base_path)
        self.hooks_gen = HooksGenerator(self.base_path)
        self.components_gen = ComponentsGenerator(self.base_path)
        
    def generate_complete_architecture(self):
        """生成完整的統一管理後台架構"""
        print("🚀 開始生成統一管理後台架構...")
        print(f"📅 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 創建目錄結構
            print("\n📁 創建目錄結構...")
            self.architecture_gen.create_directory_structure()
            
            # 2. 生成TypeScript類型定義
            print("\n📝 生成TypeScript類型定義...")
            self._write_file(
                f"{self.admin_path}/types/AdminTypes.ts",
                self.types_gen.generate_admin_types()
            )
            self._write_file(
                f"{self.admin_path}/types/ComponentTypes.ts", 
                self.types_gen.generate_component_types()
            )
            
            # 3. 生成服務層
            print("\n🔧 生成服務層...")
            self._write_file(
                f"{self.admin_path}/services/AdminApiService.ts",
                self.services_gen.generate_admin_api_service()
            )
            self._write_file(
                f"{self.admin_path}/services/NotificationService.ts",
                self.services_gen.generate_notification_service()
            )
            
            # 4. 生成React Hooks
            print("\n🪝 生成React Hooks...")
            self._write_file(
                f"{self.admin_path}/hooks/useAdminHooks.ts",
                self.hooks_gen.generate_admin_hooks()
            )
            
            # 5. 生成通用組件
            print("\n🧩 生成通用組件...")
            self._write_file(
                f"{self.admin_path}/components/AdminLayout.tsx",
                self.components_gen.generate_admin_layout()
            )
            self._write_file(
                f"{self.admin_path}/components/common/DataTable.tsx",
                self.components_gen.generate_data_table()
            )
            
            # 6. 生成配置文件
            print("\n⚙️ 生成配置文件...")
            self._generate_config_files()
            
            # 7. 生成樣式文件
            print("\n🎨 生成樣式文件...")
            self._generate_style_files()
            
            # 8. 生成README文檔
            print("\n📚 生成文檔...")
            self._generate_documentation()
            
            print("\n✅ 統一管理後台架構生成完成！")
            print(f"📂 生成位置: {self.admin_path}")
            print("\n📋 生成的文件:")
            self._list_generated_files()
            
        except Exception as e:
            print(f"\n❌ 生成過程中發生錯誤: {e}")
            raise
    
    def _write_file(self, file_path: str, content: str):
        """寫入文件"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ {file_path}")
    
    def _generate_config_files(self):
        """生成配置文件"""
        # 生成管理後台配置
        admin_config = '''/**
 * 管理後台配置
 */

export const ADMIN_CONFIG = {
  // API配置
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || '/api',
  API_TIMEOUT: 30000,
  
  // 分頁配置
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  
  // 表格配置
  TABLE_SCROLL_Y: 400,
  
  // 通知配置
  NOTIFICATION_DURATION: 5000,
  
  // 主題配置
  THEME: {
    PRIMARY_COLOR: '#667eea',
    SECONDARY_COLOR: '#764ba2',
    SUCCESS_COLOR: '#28a745',
    WARNING_COLOR: '#ffc107',
    ERROR_COLOR: '#dc3545',
    INFO_COLOR: '#17a2b8'
  },
  
  // 功能開關
  FEATURES: {
    USER_MANAGEMENT: true,
    ANALYTICS: true,
    CONTENT_MANAGEMENT: true,
    FINANCIAL_MANAGEMENT: true,
    SYSTEM_MONITORING: true
  }
};'''
        
        self._write_file(f"{self.admin_path}/config/AdminConfig.ts", admin_config)
    
    def _generate_style_files(self):
        """生成樣式文件"""
        # 生成主樣式文件
        main_styles = '''/**
 * 管理後台主樣式
 * 基於admin_enhanced.html的設計
 */

/* 全局樣式 */
.admin-container {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 側邊欄樣式 */
.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.sidebar.collapsed {
  width: 80px;
}

/* 主內容區域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 280px;
  transition: margin-left 0.3s ease;
}

.main-content.sidebar-collapsed {
  margin-left: 80px;
}

/* 表格樣式 */
.data-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table th.sortable {
  cursor: pointer;
  user-select: none;
}

.table th.sortable:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

/* 載入狀態 */
.table-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

/* 通知樣式 */
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
}

.notification {
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -280px;
    z-index: 1000;
  }
  
  .sidebar.open {
    left: 0;
  }
  
  .main-content {
    margin-left: 0;
  }
}'''
        
        self._write_file(f"{self.admin_path}/styles/admin.css", main_styles)
    
    def _generate_documentation(self):
        """生成文檔"""
        readme_content = f'''# 統一管理後台架構

## 概述
基於分析結果生成的統一管理後台架構，整合了13個版本的最佳功能。

## 生成時間
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 技術棧
- **框架**: React 18 + TypeScript
- **UI庫**: Bootstrap 5.3.0
- **圖標**: Font Awesome 6.4.0
- **圖表**: Chart.js
- **狀態管理**: React Hooks

## 目錄結構
```
admin/
├── components/          # React組件
│   ├── common/         # 通用組件
│   ├── dashboard/      # 儀表板組件
│   ├── users/          # 用戶管理組件
│   ├── analytics/      # 分析組件
│   ├── content/        # 內容管理組件
│   └── financial/      # 財務管理組件
├── services/           # 服務層
├── hooks/              # React Hooks
├── types/              # TypeScript類型定義
├── utils/              # 工具函數
├── styles/             # 樣式文件
├── config/             # 配置文件
└── assets/             # 靜態資源
```

## 核心功能
1. **統一API客戶端** - 基於486個API端點的統一調用
2. **類型安全** - 完整的TypeScript類型定義
3. **組件化設計** - 可重用的React組件
4. **狀態管理** - 基於Hooks的狀態管理
5. **通知系統** - 統一的用戶通知機制
6. **響應式設計** - 支援多種設備

## 使用方法
1. 導入所需組件和服務
2. 配置API端點
3. 使用提供的Hooks管理狀態
4. 自定義樣式和主題

## API整合
- 系統管理: `/admin/system/*`
- 用戶管理: `/admin/users/*`
- 數據分析: `/admin/analytics/*`
- 內容管理: `/admin/content/*`
- 財務管理: `/admin/financial/*`

## 下一步
1. 實現具體的業務組件
2. 整合現有API端點
3. 添加測試用例
4. 優化性能和用戶體驗
'''
        
        self._write_file(f"{self.admin_path}/README.md", readme_content)
    
    def _list_generated_files(self):
        """列出生成的文件"""
        generated_files = []
        for root, dirs, files in os.walk(self.admin_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.admin_path)
                generated_files.append(relative_path)
        
        for file_path in sorted(generated_files):
            print(f"  📄 {file_path}")

if __name__ == "__main__":
    generator = UnifiedAdminGenerator()
    generator.generate_complete_architecture()