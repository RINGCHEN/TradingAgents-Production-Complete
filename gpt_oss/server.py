#!/usr/bin/env python3
"""
GPT-OSS 本地推理服務器
TradingAgents集成版 - 支持CPU和GPU推理
"""

import argparse
import asyncio
import logging
import os
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import json
from contextlib import asynccontextmanager

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 請求模型
class ChatRequest(BaseModel):
    message: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    model: Optional[str] = "llama-3-8b"
    # 允許在呼叫時覆蓋 adapter
    lora_adapter: Optional[str] = None
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    model: str
    tokens_used: int
    device: str

# GPT-OSS 服務器
class GPTOSSServer:
    def __init__(self, device: str = "auto", base_model: str = None, lora_adapter: str = None, load_in_4bit: bool = True):
        self.base_model_name = base_model or os.getenv("BASE_MODEL", "Qwen/Qwen2-1.5B-Instruct")
        self.lora_adapter_path = lora_adapter or os.getenv("LORA_ADAPTER", None)
        self.load_in_4bit = load_in_4bit if os.getenv("LOAD_IN_4BIT") is None else os.getenv("LOAD_IN_4BIT") == "true"
        self.device = self._setup_device(device)
        self.model = None
        self.tokenizer = None
        self.model_name = self.base_model_name
        self.max_memory_gb = 8  # RTX 4070 VRAM limit (8GB)
        
        # 根據不同模型調整記憶體策略
        self._adjust_memory_strategy()
        
    def _setup_device(self, device: str) -> str:
        """設置計算設備"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    def _adjust_memory_strategy(self):
        """根據模型調整記憶體策略"""
        # 輕量模型記憶體需求 (4-bit量化後)
        memory_requirements = {
            "microsoft/DialoGPT-medium": 0.5,   # ~500MB
            "microsoft/DialoGPT-large": 1.5,    # ~1.5GB
            "Qwen/Qwen2-1.5B-Instruct": 2.0,   # ~2GB
            "THUDM/chatglm3-6b": 4.0,          # ~4GB
            "baichuan-inc/Baichuan2-7B-Chat": 5.0  # ~5GB
        }
        
        model_memory = memory_requirements.get(self.base_model_name, 2.0)
        
        # 調整最大記憶體限制
        if model_memory > self.max_memory_gb * 0.8:
            logger.warning(f"模型記憶體需求 {model_memory}GB 可能超過可用 VRAM {self.max_memory_gb}GB")
            
        # 根據模型大小調整量化策略
        if model_memory <= 1.0:
            self.load_in_4bit = False  # 小模型不需要4-bit量化
            logger.info("檢測到輕量模型，停用4-bit量化")
        
        logger.info(f"模型記憶體預估: {model_memory}GB, 量化: {self.load_in_4bit}")
    
    async def initialize_model(self):
        """初始化模型或載入 base + LoRA adapter（如提供）"""
        logger.info(f"正在初始化模型 {self.base_model_name} 在設備 {self.device}")

        # 延後導入以加速啟動
        from transformers import AutoTokenizer, AutoModelForCausalLM
        try:
            from transformers import BitsAndBytesConfig
            has_bnb = True
        except Exception:
            has_bnb = False

        # Tokenizer (處理不同模型的特殊需求)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name, 
                use_fast=True,
                trust_remote_code=True  # 支援Qwen等需要trust_remote_code的模型
            )
        except Exception as e:
            logger.warning(f"使用trust_remote_code失敗，回退到標準載入: {e}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name, use_fast=True)
            
        # 設定pad_token
        if self.tokenizer.pad_token is None:
            if self.tokenizer.eos_token is not None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            elif hasattr(self.tokenizer, 'im_end_token') and self.tokenizer.im_end_token:
                self.tokenizer.pad_token = self.tokenizer.im_end_token  # Qwen模型
            else:
                self.tokenizer.pad_token = self.tokenizer.unk_token

        # Base model（可 4-bit）
        model_kwargs = {
            "device_map": "auto",
            "trust_remote_code": True  # 支援Qwen等模型
        }
        
        if self.load_in_4bit and has_bnb:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16,  # 使用float16節省記憶體
            )
            model_kwargs["quantization_config"] = bnb_config
        else:
            model_kwargs["torch_dtype"] = torch.float16  # 統一使用float16

        try:
            base_model = AutoModelForCausalLM.from_pretrained(self.base_model_name, **model_kwargs)
        except Exception as e:
            logger.warning(f"使用trust_remote_code載入失敗，回退到標準載入: {e}")
            model_kwargs.pop("trust_remote_code", None)
            base_model = AutoModelForCausalLM.from_pretrained(self.base_model_name, **model_kwargs)

        # Apply LoRA adapter if provided
        if self.lora_adapter_path:
            try:
                from peft import PeftModel
                logger.info(f"載入 LoRA adapter: {self.lora_adapter_path}")
                base_model = PeftModel.from_pretrained(base_model, self.lora_adapter_path)
            except Exception as e:
                logger.error(f"載入 LoRA adapter 失敗: {e}")

        self.model = base_model
        logger.info("模型初始化完成（含 LoRA: %s）", bool(self.lora_adapter_path))
        return True
    
    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """生成回應（真實推理，支援動態載入 LoRA adapter）"""
        # 動態切換 LoRA（若提供並不同於現有）
        if request.lora_adapter and request.lora_adapter != self.lora_adapter_path:
            try:
                from peft import PeftModel
                logger.info(f"切換 LoRA adapter -> {request.lora_adapter}")
                self.model = PeftModel.from_pretrained(self.model, request.lora_adapter)
                self.lora_adapter_path = request.lora_adapter
            except Exception as e:
                logger.error(f"切換 LoRA adapter 失敗: {e}")

        prompt = request.message
        max_new_tokens = int(request.max_tokens or 512)
        temperature = float(request.temperature if request.temperature is not None else 0.7)
        do_sample = temperature > 0

        # 決定張量放置裝置：以嵌入層權重的裝置為準（相容 device_map="auto"）
        try:
            target_device = self.model.get_input_embeddings().weight.device
        except Exception:
            target_device = torch.device("cuda" if torch.cuda.is_available() and self.device != "cpu" else "cpu")

        # 準備輸入
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        inputs = {k: v.to(target_device) for k, v in inputs.items()}

        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "temperature": max(0.0, temperature),
            "do_sample": do_sample,
            "top_p": 0.9,
            "top_k": 40,
            "repetition_penalty": 1.1,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
        }

        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        generated_ids = outputs[0]
        generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        # 粗略統計 tokens_used（僅供參考）
        try:
            tokens_used = len(self.tokenizer(generated_text, return_tensors="pt")["input_ids"][0])
        except Exception:
            tokens_used = len(generated_text.split())

        return ChatResponse(
            response=generated_text,
            model=request.model or self.model_name,
            tokens_used=int(tokens_used),
            device=str(target_device),
        )
    
    async def check_memory_usage(self) -> Dict[str, Any]:
        """檢查GPU記憶體使用情況"""
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3   # GB
            memory_free = (torch.cuda.get_device_properties(0).total_memory / 1024**3) - memory_reserved
            
            return {
                "allocated_gb": round(memory_allocated, 2),
                "reserved_gb": round(memory_reserved, 2),
                "free_gb": round(memory_free, 2),
                "usage_percentage": round((memory_reserved / self.max_memory_gb) * 100, 2)
            }
        return {"message": "CUDA not available"}
    
    async def handle_oom_protection(self):
        """OOM保護機制"""
        if torch.cuda.is_available():
            memory_info = await self.check_memory_usage()
            if memory_info.get("usage_percentage", 0) > 90:
                logger.warning("GPU記憶體使用率超過90%，執行清理")
                torch.cuda.empty_cache()
                return True
        return False
    
    async def generate_stream_response(self, request: ChatRequest):
        """生成流式回應"""
        try:
            # 動態切換 LoRA（若提供並不同於現有）
            if request.lora_adapter and request.lora_adapter != self.lora_adapter_path:
                try:
                    from peft import PeftModel
                    logger.info(f"切換 LoRA adapter -> {request.lora_adapter}")
                    self.model = PeftModel.from_pretrained(self.model, request.lora_adapter)
                    self.lora_adapter_path = request.lora_adapter
                except Exception as e:
                    logger.error(f"切換 LoRA adapter 失敗: {e}")

            prompt = request.message
            max_new_tokens = int(request.max_tokens or 512)
            temperature = float(request.temperature if request.temperature is not None else 0.7)
            do_sample = temperature > 0

            # 決定張量放置裝置
            try:
                target_device = self.model.get_input_embeddings().weight.device
            except Exception:
                target_device = torch.device("cuda" if torch.cuda.is_available() and self.device != "cpu" else "cpu")

            # 準備輸入
            inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
            inputs = {k: v.to(target_device) for k, v in inputs.items()}

            gen_kwargs = {
                "max_new_tokens": max_new_tokens,
                "temperature": max(0.0, temperature),
                "do_sample": do_sample,
                "top_p": 0.9,
                "top_k": 40,
                "repetition_penalty": 1.1,
                "eos_token_id": self.tokenizer.eos_token_id,
                "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            }

            # 流式生成（簡化版本，實際可使用TextIteratorStreamer）
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **gen_kwargs)

            generated_ids = outputs[0]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            # 模擬流式輸出
            words = generated_text.split()
            for i, word in enumerate(words):
                chunk = {
                    "text": word + " ",
                    "index": i,
                    "finished": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # 模擬流式延遲
                
        except Exception as e:
            error_chunk = {
                "error": str(e),
                "finished": True
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

# 全局服務器實例
gpt_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    global gpt_server
    
    # 啟動時初始化
    logger.info("正在初始化GPT-OSS服務器...")
    try:
        device = os.getenv("DEVICE", "auto")
        base_model = os.getenv("BASE_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
        lora_adapter = os.getenv("LORA_ADAPTER", None)
        load_in_4bit = os.getenv("LOAD_IN_4BIT", "true").lower() == "true"

        gpt_server = GPTOSSServer(
            device=device,
            base_model=base_model,
            lora_adapter=lora_adapter,
            load_in_4bit=load_in_4bit,
        )
        await gpt_server.initialize_model()
        logger.info("GPT-OSS服務器啟動完成")
    except Exception as e:
        logger.error(f"GPT-OSS服務器初始化失敗: {e}")
        raise
    
    yield
    
    # 關閉時清理
    logger.info("正在關閉GPT-OSS服務器...")
    try:
        if gpt_server and torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("GPT-OSS服務器關閉完成")
    except Exception as e:
        logger.error(f"GPT-OSS服務器關閉時發生錯誤: {e}")

# 創建FastAPI應用
app = FastAPI(
    title="GPT-OSS Local Inference Server",
    description="TradingAgents集成的本地GPT推理服務 - 支援真實推理、流式輸出、OOM保護",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    if not gpt_server:
        return {
            "status": "unhealthy",
            "service": "gpt-oss",
            "error": "服務器未初始化"
        }
    
    try:
        memory_info = await gpt_server.check_memory_usage()
        return {
            "status": "healthy",
            "service": "gpt-oss",
            "version": "2.0.0",
            "device": gpt_server.device,
            "model": gpt_server.model_name,
            "model_loaded": gpt_server.model is not None,
            "memory_info": memory_info,
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "gpt-oss",
            "error": str(e)
        }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """聊天端點 - 支援流式和非流式輸出"""
    if not gpt_server:
        raise HTTPException(status_code=503, detail="服務器未初始化")
    
    try:
        # OOM保護檢查
        await gpt_server.handle_oom_protection()
        
        if request.stream:
            # 流式輸出
            return StreamingResponse(
                gpt_server.generate_stream_response(request),
                media_type="text/plain"
            )
        else:
            # 非流式輸出
            response = await gpt_server.generate_response(request)
            return response
    except torch.cuda.OutOfMemoryError as e:
        logger.error(f"GPU記憶體不足: {e}")
        torch.cuda.empty_cache()
        raise HTTPException(status_code=507, detail="GPU記憶體不足，請稍後重試")
    except Exception as e:
        logger.error(f"生成回應時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")

@app.get("/memory")
async def get_memory_status():
    """獲取記憶體狀態"""
    if not gpt_server:
        raise HTTPException(status_code=503, detail="服務器未初始化")
    
    memory_info = await gpt_server.check_memory_usage()
    return {
        "memory_status": memory_info,
        "model_loaded": gpt_server.model is not None,
        "device": gpt_server.device
    }

@app.get("/models")
async def list_models():
    """列出可用模型"""
    return {
        "models": [
            {
                "id": "llama-3-8b",
                "name": "Llama 3 8B",
                "description": "Meta的Llama 3 8B模型",
                "status": "available"
            }
        ]
    }

@app.get("/status")
async def server_status():
    """服務器狀態"""
    return {
        "server": "gpt-oss",
        "version": "1.0.0",
        "device": gpt_server.device if gpt_server else "unknown",
        "model_loaded": gpt_server is not None,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available()
    }

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="GPT-OSS Local Inference Server")
    parser.add_argument("--host", default="0.0.0.0", help="服務器主機")
    parser.add_argument("--port", type=int, default=8080, help="服務器端口")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="計算設備")
    parser.add_argument("--workers", type=int, default=1, help="工作進程數")
    parser.add_argument("--base-model", default=None, help="基底模型（覆蓋 BASE_MODEL 環境變數）")
    parser.add_argument("--lora-adapter", default=None, help="LoRA adapter 路徑（覆蓋 LORA_ADAPTER 環境變數）")
    parser.add_argument("--load-in-4bit", action="store_true", help="以 4-bit 量化載入基底模型（覆蓋 LOAD_IN_4BIT）")
    args = parser.parse_args()
    
    # 設置環境變量與覆蓋
    os.environ["DEVICE"] = args.device
    if args.base_model:
        os.environ["BASE_MODEL"] = args.base_model
    if args.lora_adapter:
        os.environ["LORA_ADAPTER"] = args.lora_adapter
    if args.load_in_4bit:
        os.environ["LOAD_IN_4BIT"] = "true"

    logger.info(f"啟動GPT-OSS服務器在 {args.host}:{args.port}")
    logger.info(f"使用設備: {args.device}")
    
    # 啟動服務器
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=False
    )

if __name__ == "__main__":
    main()