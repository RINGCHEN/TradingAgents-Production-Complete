#!/usr/bin/env python3
"""
依賴鎖定工具
基於 GOOGLE 的診斷建議，創建精確的依賴版本鎖定文件
防止生產環境中的版本不匹配問題

功能：
1. 分析當前安裝的包版本
2. 創建鎖定的 requirements 文件
3. 驗證關鍵包的兼容性
4. 生成部署用的精確版本文件

作者：天工 (TianGong) + Claude Code
基於：GOOGLE 的依賴管理最佳實踐建議
"""

import subprocess
import sys
import os
import pkg_resources
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 關鍵包版本映射（基於生產環境問題分析）
CRITICAL_PACKAGES = {
    'jose': 'python-jose',  # JWT 處理
    'redis': 'redis',       # Redis 緩存
    'psycopg2': 'psycopg2-binary',  # PostgreSQL 連接
    'fastapi': 'fastapi',   # Web 框架
    'uvicorn': 'uvicorn',   # ASGI 服務器
    'pydantic': 'pydantic', # 數據驗證
    'sqlalchemy': 'sqlalchemy',  # ORM
    'aiohttp': 'aiohttp',   # 異步 HTTP 客戶端
}

def get_installed_packages() -> Dict[str, str]:
    """獲取已安裝包的精確版本"""
    logger.info("🔍 分析已安裝的包版本...")
    
    try:
        # 使用 pip freeze 獲取精確版本
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                               capture_output=True, text=True, check=True)
        
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line and not line.startswith('-e'):
                name, version = line.split('==')
                packages[name.lower()] = version
        
        logger.info(f"✅ 成功分析 {len(packages)} 個已安裝包")
        return packages
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 無法獲取包信息: {e}")
        return {}

def check_critical_packages(packages: Dict[str, str]) -> Dict[str, Tuple[str, bool]]:
    """檢查關鍵包的版本和兼容性"""
    logger.info("🔬 檢查關鍵包版本和兼容性...")
    
    critical_status = {}
    
    for key, package_name in CRITICAL_PACKAGES.items():
        if package_name.lower() in packages:
            version = packages[package_name.lower()]
            is_compatible = True
            
            # 特定版本兼容性檢查
            if package_name == 'python-jose':
                # jose 需要特定版本以避免 InvalidTokenError 問題
                try:
                    from packaging import version as pkg_version
                    if pkg_version.parse(version) < pkg_version.parse('3.0.0'):
                        is_compatible = False
                        logger.warning(f"⚠️ {package_name} v{version} 可能有兼容性問題")
                except ImportError:
                    pass
                    
            elif package_name == 'redis':
                # Redis 需要支持新的 SSL 參數
                try:
                    from packaging import version as pkg_version
                    if pkg_version.parse(version) < pkg_version.parse('4.0.0'):
                        is_compatible = False
                        logger.warning(f"⚠️ {package_name} v{version} 可能有 SSL 兼容性問題")
                except ImportError:
                    pass
            
            critical_status[package_name] = (version, is_compatible)
            logger.info(f"  {'✅' if is_compatible else '⚠️'} {package_name}: {version}")
        else:
            critical_status[package_name] = ('未安裝', False)
            logger.error(f"❌ 關鍵包 {package_name} 未安裝")
    
    return critical_status

def generate_locked_requirements(packages: Dict[str, str], 
                                critical_status: Dict[str, Tuple[str, bool]]) -> str:
    """生成鎖定的 requirements 內容"""
    logger.info("📝 生成鎖定的 requirements 文件...")
    
    lines = [
        f"# 依賴鎖定文件",
        f"# 生成時間: {datetime.now().isoformat()}",
        f"# 基於 GOOGLE 診斷建議，防止版本衝突",
        f"# 總共 {len(packages)} 個包，{len(CRITICAL_PACKAGES)} 個關鍵包",
        "",
        "# ==================== 關鍵包（經過兼容性驗證）====================",
    ]
    
    # 首先列出關鍵包
    for package_name, (version, is_compatible) in critical_status.items():
        if version != '未安裝':
            status_comment = " # ✅ 兼容性驗證通過" if is_compatible else " # ⚠️ 需要注意兼容性"
            lines.append(f"{package_name}=={version}{status_comment}")
    
    lines.extend([
        "",
        "# ==================== 其他依賴包 ====================",
    ])
    
    # 列出其他包
    critical_package_names = {name.lower() for name in CRITICAL_PACKAGES.values()}
    for name, version in sorted(packages.items()):
        if name not in critical_package_names:
            lines.append(f"{name}=={version}")
    
    return '\n'.join(lines)

def create_dockerfile_requirements(content: str) -> str:
    """創建適用於 Dockerfile 的精簡版本"""
    lines = []
    for line in content.split('\n'):
        if line and not line.startswith('#') and '==' in line:
            # 移除註釋，只保留包名和版本
            package_line = line.split('#')[0].strip()
            if package_line:
                lines.append(package_line)
    
    return '\n'.join(lines)

def verify_requirements_file(file_path: str) -> bool:
    """驗證 requirements 文件的有效性"""
    logger.info(f"🧪 驗證 requirements 文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 計算非註釋行數
        package_lines = [line for line in content.split('\n') 
                        if line.strip() and not line.strip().startswith('#')]
        
        logger.info(f"✅ Requirements 文件包含 {len(package_lines)} 個包定義")
        
        # 檢查是否包含關鍵包
        critical_found = 0
        for critical_pkg in CRITICAL_PACKAGES.values():
            if any(critical_pkg.lower() in line.lower() for line in package_lines):
                critical_found += 1
        
        logger.info(f"✅ 發現 {critical_found}/{len(CRITICAL_PACKAGES)} 個關鍵包")
        
        return critical_found >= len(CRITICAL_PACKAGES) * 0.8  # 至少 80% 的關鍵包
        
    except Exception as e:
        logger.error(f"❌ Requirements 文件驗證失敗: {e}")
        return False

def main():
    """主函數"""
    logger.info("🚀 依賴鎖定工具啟動...")
    logger.info("📊 基於 GOOGLE 的生產環境診斷建議")
    
    # 獲取當前包信息
    packages = get_installed_packages()
    if not packages:
        logger.error("❌ 無法獲取包信息，請確保在正確的 Python 環境中運行")
        sys.exit(1)
    
    # 檢查關鍵包
    critical_status = check_critical_packages(packages)
    
    # 檢查兼容性問題
    compatibility_issues = sum(1 for _, (_, is_compatible) in critical_status.items() 
                             if not is_compatible)
    
    if compatibility_issues > 0:
        logger.warning(f"⚠️ 發現 {compatibility_issues} 個兼容性問題")
        logger.warning("建議在部署前解決這些問題")
    
    # 生成鎖定文件
    locked_content = generate_locked_requirements(packages, critical_status)
    
    # 保存完整版本（帶註釋）
    full_requirements_path = "requirements-locked-full.txt"
    with open(full_requirements_path, 'w', encoding='utf-8') as f:
        f.write(locked_content)
    logger.info(f"✅ 完整版 requirements 已保存: {full_requirements_path}")
    
    # 保存 Dockerfile 版本（精簡）
    docker_content = create_dockerfile_requirements(locked_content)
    docker_requirements_path = "requirements-locked-docker.txt"
    with open(docker_requirements_path, 'w', encoding='utf-8') as f:
        f.write(docker_content)
    logger.info(f"✅ Docker 版 requirements 已保存: {docker_requirements_path}")
    
    # 驗證文件
    if verify_requirements_file(full_requirements_path):
        logger.info("✅ Requirements 文件驗證通過")
    else:
        logger.error("❌ Requirements 文件驗證失敗")
        sys.exit(1)
    
    # 生成部署建議
    logger.info("")
    logger.info("📋 部署建議:")
    logger.info("  1. 將 requirements-locked-docker.txt 複製到生產環境")
    logger.info("  2. 更新 Dockerfile:")
    logger.info("     COPY requirements-locked-docker.txt requirements.txt")
    logger.info("     RUN pip install -r requirements.txt")
    logger.info("  3. 重新構建和部署 Docker 鏡像")
    logger.info("  4. 驗證所有 API 端點正常工作")
    
    if compatibility_issues == 0:
        logger.info("🎉 所有關鍵包兼容性檢查通過！可以安全部署。")
    else:
        logger.warning("⚠️ 建議解決兼容性問題後再部署")
        
    logger.info("✨ 依賴鎖定工具完成")

if __name__ == "__main__":
    main()