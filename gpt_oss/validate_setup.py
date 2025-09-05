#!/usr/bin/env python3
"""
GPT-OSS 配置驗證腳本
驗證所有配置和環境是否正確設置
"""

import os
import sys
import yaml
import torch
from pathlib import Path
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTOSSValidator:
    """GPT-OSS 配置驗證器"""
    
    def __init__(self):
        self.base_dir = Path(os.path.dirname(__file__))
        self.errors = []
        self.warnings = []
        
    def validate_environment(self) -> bool:
        """驗證運行環境"""
        logger.info("🔍 檢查運行環境...")
        
        # 檢查Python版本
        if sys.version_info < (3, 8):
            self.errors.append(f"Python版本過低: {sys.version_info}, 需要3.8+")
        else:
            logger.info(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}")
        
        # 檢查CUDA
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"✅ CUDA可用: {gpu_name} ({memory_gb:.1f}GB)")
            
            if memory_gb < 6:
                self.warnings.append(f"GPU記憶體較少 ({memory_gb:.1f}GB), 建議使用輕量模型")
        else:
            self.warnings.append("CUDA不可用，將使用CPU模式")
            logger.info("⚠️  CUDA不可用，將使用CPU模式")
        
        return len(self.errors) == 0
    
    def validate_dependencies(self) -> bool:
        """驗證依賴包"""
        logger.info("🔍 檢查依賴包...")
        
        required_packages = [
            ('torch', 'PyTorch'),
            ('transformers', 'Transformers'),
            ('fastapi', 'FastAPI'),
            ('uvicorn', 'Uvicorn'),
            ('pydantic', 'Pydantic')
        ]
        
        optional_packages = [
            ('bitsandbytes', 'BitsAndBytes (量化支持)'),
            ('peft', 'PEFT (LoRA支持)'),
            ('flash_attn', 'Flash Attention (性能優化)')
        ]
        
        for package, name in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {name}")
            except ImportError:
                self.errors.append(f"缺少必要包: {name} ({package})")
        
        for package, name in optional_packages:
            try:
                __import__(package)
                logger.info(f"✅ {name}")
            except ImportError:
                self.warnings.append(f"缺少可選包: {name} ({package})")
        
        return len(self.errors) == 0
    
    def validate_config_file(self) -> bool:
        """驗證配置文件"""
        logger.info("🔍 檢查配置文件...")
        
        config_path = self.base_dir / "config.yaml"
        if not config_path.exists():
            self.errors.append(f"配置文件不存在: {config_path}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 檢查必要配置
            required_sections = ['server', 'model', 'performance']
            for section in required_sections:
                if section not in config:
                    self.errors.append(f"配置文件缺少必要節: {section}")
                else:
                    logger.info(f"✅ 配置節 '{section}' 存在")
            
            # 檢查模型配置
            if 'model' in config:
                model_config = config['model']
                model_name = model_config.get('name')
                if model_name:
                    logger.info(f"✅ 配置的模型: {model_name}")
                    
                    # 驗證模型記憶體需求
                    memory_requirements = {
                        "microsoft/DialoGPT-medium": 0.5,
                        "microsoft/DialoGPT-large": 1.5,
                        "Qwen/Qwen2-1.5B-Instruct": 2.0,
                        "THUDM/chatglm3-6b": 4.0,
                        "baichuan-inc/Baichuan2-7B-Chat": 5.0
                    }
                    
                    model_memory = memory_requirements.get(model_name, 2.0)
                    if torch.cuda.is_available():
                        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                        if model_memory > gpu_memory * 0.8:
                            self.warnings.append(f"模型記憶體需求 ({model_memory}GB) 可能超過可用VRAM ({gpu_memory:.1f}GB)")
                else:
                    self.errors.append("配置文件未指定模型名稱")
            
            logger.info("✅ 配置文件格式正確")
            return True
            
        except Exception as e:
            self.errors.append(f"配置文件解析失敗: {e}")
            return False
    
    def validate_startup_scripts(self) -> bool:
        """驗證啟動腳本"""
        logger.info("🔍 檢查啟動腳本...")
        
        scripts = [
            ("start_gpt_oss.bat", "Windows啟動腳本"),
            ("start_gpt_oss.sh", "Linux啟動腳本"),
            ("server.py", "主服務器腳本")
        ]
        
        for script, description in scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                logger.info(f"✅ {description}")
                
                # 檢查執行權限 (僅Linux)
                if script.endswith('.sh') and os.name == 'posix':
                    if not os.access(script_path, os.X_OK):
                        self.warnings.append(f"{script} 無執行權限，運行: chmod +x {script}")
            else:
                self.errors.append(f"缺少{description}: {script}")
        
        return len([e for e in self.errors if any(s in e for s in ['start_gpt_oss', 'server.py'])]) == 0
    
    def validate_model_setup_script(self) -> bool:
        """驗證模型設置腳本"""
        logger.info("🔍 檢查模型設置腳本...")
        
        setup_script = self.base_dir / "setup_models.py"
        if setup_script.exists():
            logger.info("✅ 模型設置腳本存在")
            return True
        else:
            self.warnings.append("模型設置腳本不存在，需要手動下載模型")
            return False
    
    def run_validation(self) -> bool:
        """運行完整驗證"""
        logger.info("🎯 開始 GPT-OSS 配置驗證")
        logger.info("=" * 50)
        
        validations = [
            ("環境檢查", self.validate_environment),
            ("依賴包檢查", self.validate_dependencies),
            ("配置文件檢查", self.validate_config_file),
            ("啟動腳本檢查", self.validate_startup_scripts),
            ("模型設置腳本檢查", self.validate_model_setup_script)
        ]
        
        all_passed = True
        for name, validator in validations:
            try:
                result = validator()
                if not result:
                    all_passed = False
            except Exception as e:
                self.errors.append(f"{name}過程出錯: {e}")
                all_passed = False
        
        # 顯示結果
        self.show_results()
        
        return all_passed and len(self.errors) == 0
    
    def show_results(self):
        """顯示驗證結果"""
        logger.info("=" * 50)
        logger.info("📊 驗證結果總結")
        logger.info("=" * 50)
        
        if self.errors:
            logger.error(f"❌ 發現 {len(self.errors)} 個錯誤:")
            for i, error in enumerate(self.errors, 1):
                logger.error(f"  {i}. {error}")
        
        if self.warnings:
            logger.warning(f"⚠️  發現 {len(self.warnings)} 個警告:")
            for i, warning in enumerate(self.warnings, 1):
                logger.warning(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            logger.info("🎉 所有檢查通過！配置完美！")
        elif not self.errors:
            logger.info("✅ 主要配置正確，有一些次要警告")
            logger.info("💡 建議處理警告以獲得最佳性能")
        else:
            logger.error("❌ 配置存在問題，需要修復後才能正常運行")
        
        # 提供下一步建議
        if not self.errors:
            logger.info("\n💡 下一步操作:")
            logger.info("1. 運行模型設置: python setup_models.py")
            logger.info("2. 啟動服務: start_gpt_oss.bat (Windows) 或 ./start_gpt_oss.sh (Linux)")
            logger.info("3. 測試健康檢查: curl http://localhost:8080/health")
        else:
            logger.info("\n🔧 修復建議:")
            logger.info("1. 安裝缺少的依賴包: pip install -r requirements-gpt-oss.txt")
            logger.info("2. 檢查並修復配置文件")
            logger.info("3. 重新運行驗證: python validate_setup.py")

def main():
    """主函數"""
    validator = GPTOSSValidator()
    success = validator.run_validation()
    
    if success:
        logger.info("🎯 配置驗證成功，可以開始使用GPT-OSS！")
        return 0
    else:
        logger.error("❌ 配置驗證失敗，請修復問題後重試")
        return 1

if __name__ == "__main__":
    sys.exit(main())