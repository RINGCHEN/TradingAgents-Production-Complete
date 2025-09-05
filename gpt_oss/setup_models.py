#!/usr/bin/env python3
"""
GPT-OSS 模型設置腳本
RTX 4070 8GB 優化版本 - 自動選擇合適的開源模型
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
try:
    from huggingface_hub import snapshot_download
except ImportError:
    snapshot_download = None
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def setup_model_directory():
    """設置模型目錄"""
    base_dir = Path(os.path.dirname(__file__))
    model_dir = base_dir / "models"
    cache_dir = base_dir / "cache"
    
    model_dir.mkdir(exist_ok=True, parents=True)
    cache_dir.mkdir(exist_ok=True, parents=True)
    
    logger.info(f"模型目錄: {model_dir}")
    logger.info(f"緩存目錄: {cache_dir}")
    
    return model_dir, cache_dir

def get_recommended_models() -> List[Dict[str, Any]]:
    """獲取推薦模型列表"""
    return [
        {
            "name": "microsoft/DialoGPT-medium",
            "memory_gb": 0.5,
            "description": "輕量對話模型，快速啟動",
            "chinese_support": "基礎",
            "financial_support": "一般"
        },
        {
            "name": "microsoft/DialoGPT-large", 
            "memory_gb": 1.5,
            "description": "中等對話模型，平衡性能",
            "chinese_support": "基礎",
            "financial_support": "一般"
        },
        {
            "name": "Qwen/Qwen2-1.5B-Instruct",
            "memory_gb": 2.0,
            "description": "中文優化模型，推薦選擇",
            "chinese_support": "優秀",
            "financial_support": "良好",
            "trust_remote_code": True
        },
        {
            "name": "THUDM/chatglm3-6b",
            "memory_gb": 4.0, 
            "description": "中文大模型，性能強勁",
            "chinese_support": "優秀",
            "financial_support": "優秀",
            "trust_remote_code": True
        }
    ]

def download_model(model_name: str, cache_dir: Path, trust_remote_code: bool = False) -> bool:
    """下載指定模型"""
    logger.info(f"開始下載模型: {model_name}")
    
    try:
        # 下載 tokenizer
        logger.info("  - 下載 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=str(cache_dir),
            trust_remote_code=trust_remote_code
        )
        
        # 下載模型 (使用CausalLM以支持生成)
        logger.info("  - 下載模型...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=str(cache_dir),
            trust_remote_code=trust_remote_code,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True
        )
        
        logger.info(f"✅ 模型 {model_name} 下載完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 下載模型失敗: {e}")
        if trust_remote_code:
            logger.info("嘗試不使用trust_remote_code重新下載...")
            return download_model(model_name, cache_dir, trust_remote_code=False)
        return False

def verify_gpu_setup() -> Dict[str, Any]:
    """驗證GPU設置並返回硬體信息"""
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
        memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
        
        logger.info(f"🎮 GPU可用: {gpu_count} 個設備")
        logger.info(f"🎮 主GPU: {gpu_name}")
        logger.info(f"🎮 GPU記憶體: {memory_total:.1f} GB")
        
        return {
            "available": True,
            "count": gpu_count,
            "name": gpu_name,
            "memory_gb": memory_total
        }
    else:
        logger.info("💻 CUDA不可用，將使用CPU模式")
        return {
            "available": False,
            "count": 0,
            "name": "CPU",
            "memory_gb": 0
        }

def create_model_config(model_name: str, base_dir: Path, gpu_info: Dict[str, Any]):
    """創建模型配置文件"""
    config_content = f"""# GPT-OSS 模型配置 - RTX 4070 8GB 優化
BASE_MODEL={model_name}
TORCH_DTYPE=float16
LOAD_IN_4BIT={'true' if gpu_info['memory_gb'] <= 8 and gpu_info['available'] else 'false'}
DEVICE_MAP={'auto' if gpu_info['available'] else 'cpu'}
MAX_LENGTH=4096
MAX_NEW_TOKENS=2048
TEMPERATURE=0.3
TOP_P=0.9
HOST=0.0.0.0
PORT=8080
WORKERS=1
"""
    
    config_path = base_dir / "model.env"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"✅ 模型配置文件已創建: {config_path}")
    return config_path

def select_best_model(models: List[Dict[str, Any]], gpu_info: Dict[str, Any]) -> Dict[str, Any]:
    """根據硬體選擇最佳模型"""
    if not gpu_info['available']:
        # CPU模式選擇最輕量的模型
        return models[0]  # DialoGPT-medium
    
    # GPU模式根據VRAM選擇
    max_memory = gpu_info['memory_gb'] * 0.8  # 預留20%記憶體
    
    suitable_models = [m for m in models if m['memory_gb'] <= max_memory]
    
    if not suitable_models:
        return models[0]  # 備選最小的模型
    
    # 優先選擇中文支援好的模型
    for model in suitable_models:
        if model.get('chinese_support') == '優秀':
            return model
    
    # 否則選擇最大的合適模型
    return max(suitable_models, key=lambda x: x['memory_gb'])

def test_model_generation(model_name: str, cache_dir: Path, trust_remote_code: bool = False) -> bool:
    """測試模型生成能力"""
    logger.info(f"🧪 測試模型生成: {model_name}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            cache_dir=str(cache_dir),
            trust_remote_code=trust_remote_code
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            cache_dir=str(cache_dir),
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=trust_remote_code
        )
        
        # 設定pad_token
        if tokenizer.pad_token is None:
            if tokenizer.eos_token is not None:
                tokenizer.pad_token = tokenizer.eos_token
            else:
                tokenizer.pad_token = tokenizer.unk_token
        
        # 測試生成
        test_prompt = "請分析台積電股票"
        inputs = tokenizer(test_prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=30,
                temperature=0.7,
                pad_token_id=tokenizer.pad_token_id,
                do_sample=True
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"  ✅ 生成結果: {generated_text[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ 模型生成測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🎯 GPT-OSS 模型設置工具 (RTX 4070 8GB 優化)")
    print("=" * 60)
    
    # 檢查GPU
    gpu_info = verify_gpu_setup()
    
    # 設置目錄
    model_dir, cache_dir = setup_model_directory()
    
    # 獲取推薦模型
    models = get_recommended_models()
    
    print(f"\n📋 推薦模型 (根據您的硬體: {gpu_info['name']}, {gpu_info['memory_gb']:.1f}GB):")
    for i, model in enumerate(models, 1):
        emoji = "🚀" if model.get('chinese_support') == '優秀' else "📝"
        print(f"  {i}. {emoji} {model['name']}")
        print(f"     記憶體需求: {model['memory_gb']}GB")
        print(f"     中文支持: {model['chinese_support']}")
        print(f"     金融領域: {model['financial_support']}")
        print(f"     描述: {model['description']}")
        print()
    
    # 自動選擇最佳模型
    best_model = select_best_model(models, gpu_info)
    
    print(f"⚡ 自動選擇最佳模型: {best_model['name']}")
    print(f"   理由: {best_model['description']}")
    print(f"   記憶體需求: {best_model['memory_gb']}GB")
    
    # 下載模型
    trust_remote_code = best_model.get('trust_remote_code', False)
    success = download_model(best_model['name'], cache_dir, trust_remote_code)
    
    if success:
        # 測試模型
        print("\n🧪 測試模型生成能力...")
        test_success = test_model_generation(best_model['name'], cache_dir, trust_remote_code)
        
        if test_success:
            print("✅ 模型測試通過")
        else:
            print("⚠️  模型測試失敗，但仍可嘗試使用")
        
        # 創建配置文件
        config_path = create_model_config(best_model['name'], cache_dir.parent, gpu_info)
        
        # 成功完成
        print("\n" + "=" * 60)
        print("🎉 GPT-OSS 模型設置完成！")
        print("=" * 60)
        print(f"📝 已配置模型: {best_model['name']}")
        print(f"📁 配置文件: {config_path}")
        print(f"🎮 運行環境: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB)")
        print("\n💡 現在可以運行啟動命令:")
        print("   Windows: start_gpt_oss.bat")
        print("   Linux:   ./start_gpt_oss.sh")
        print("   Python:  python server.py")
        print("\n🌐 啟動後訪問: http://localhost:8080/health")
        print("=" * 60)
        
    else:
        # 嘗試備選模型
        print("❌ 首選模型下載失敗，嘗試備選模型...")
        backup_model = models[0]  # DialoGPT-medium
        
        if download_model(backup_model['name'], cache_dir, False):
            config_path = create_model_config(backup_model['name'], cache_dir.parent, gpu_info)
            print(f"✅ 備選模型 {backup_model['name']} 設置完成")
            print(f"📁 配置文件: {config_path}")
        else:
            print("❌ 所有模型設置失敗")
            print("💡 請檢查網路連接或手動下載模型")
            sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 用戶中斷操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 設置過程發生錯誤: {e}")
        sys.exit(1)