#!/usr/bin/env python3
"""
Supervised Fine-Tuning (SFT) training script for causal language models.
- Loads dataset from a directory (supports JSONL with fields: instruction/input/output or text)
- Uses Hugging Face Transformers Trainer
- Saves trained model and tokenizer
- Writes a JSONL log entry to logs/training/training_runs.jsonl

Usage (Docker example):
  docker run --gpus all \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/models:/app/models \
    -v $(pwd)/logs:/app/logs \
    tradingagents:gpu-training \
    python3 /app/gpu_training/train_sft.py \
      --dataset /app/data/datasets/training_data \
      --base-model meta-llama/Meta-Llama-3-8B-Instruct \
      --output /app/models/sft_model \
      --load-in-4bit
"""

from __future__ import annotations
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from datasets import load_dataset, Dataset, DatasetDict

try:
    from transformers import BitsAndBytesConfig  # optional; for 4-bit
    HAS_BNB = True
except Exception:
    HAS_BNB = False


def infer_dtype() -> torch.dtype:
    if torch.cuda.is_available():
        # Prefer bfloat16 on modern GPUs
        return torch.bfloat16
    return torch.float32


def build_dataset(dataset_path: str) -> Dataset:
    """
    Attempts to load a dataset from the provided path.
    Supported:
      - JSONL with keys: instruction/input/output -> concatenated prompt-target
      - JSONL with key: text -> raw text for causal LM
    Returns a single Dataset with column 'text'.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset path not found: {dataset_path}")

    # Heuristic: if a .jsonl exists at the root, load it. Otherwise, try to load as HF dataset dir.
    jsonl_files = list(path.glob("*.jsonl"))
    if jsonl_files:
        ds = load_dataset("json", data_files={"train": str(jsonl_files[0])})
    else:
        # Try to load from directory (arrow/parquet/json)
        ds = load_dataset("json", data_files={"train": str(path / "train.jsonl")})

    def map_to_text(example: Dict[str, Any]) -> Dict[str, str]:
        # instruction-tuning style
        if "instruction" in example and "output" in example:
            instruction = example.get("instruction", "").strip()
            input_part = example.get("input", "").strip()
            output = example.get("output", "").strip()
            if input_part:
                text = f"Instruction: {instruction}\nInput: {input_part}\nOutput: {output}"
            else:
                text = f"Instruction: {instruction}\nOutput: {output}"
            return {"text": text}
        # plain text style
        if "text" in example:
            return {"text": str(example["text"]).strip()}
        # fallback: concatenate all fields as text
        text = " ".join(str(v) for v in example.values())
        return {"text": text}

    train_ds = ds["train"].map(map_to_text, remove_columns=[c for c in ds["train"].column_names if c != "text"])
    return train_ds


def main():
    parser = argparse.ArgumentParser(description="SFT training for causal LM")
    parser.add_argument("--dataset", required=True, type=str, help="Path to dataset directory or JSONL file")
    parser.add_argument("--base-model", required=True, type=str, help="Base model name or local path")
    parser.add_argument("--output", required=True, type=str, help="Output directory for the trained model")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--eval-batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--num-train-epochs", type=int, default=1)
    parser.add_argument("--warmup-steps", type=int, default=50)
    parser.add_argument("--save-steps", type=int, default=500)
    parser.add_argument("--logging-steps", type=int, default=50)
    parser.add_argument("--load-in-4bit", action="store_true", help="Load base model in 4-bit quantization (bitsandbytes)")
    parser.add_argument("--bf16", action="store_true", help="Force bf16 if available")
    args = parser.parse_args()

    os.makedirs("/app/logs/training", exist_ok=True)

    # Dataset
    train_ds = build_dataset(args.dataset)

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None and tokenizer.eos_token is not None:
        tokenizer.pad_token = tokenizer.eos_token

    def tokenize(examples: Dict[str, List[str]]):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=args.max_length,
            padding=False,
        )

    tokenized_train = train_ds.map(tokenize, batched=True, remove_columns=["text"])

    # Model loading
    torch_dtype = torch.bfloat16 if (args.bf16 or infer_dtype() == torch.bfloat16) else torch.float16
    model_kwargs: Dict[str, Any] = {
        "device_map": "auto",
    }
    if args.load_in_4bit:
        if not HAS_BNB:
            raise RuntimeError("bitsandbytes not available but --load-in-4bit was set")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch_dtype,
        )
        model_kwargs["quantization_config"] = bnb_config
    else:
        model_kwargs["torch_dtype"] = torch_dtype

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        **model_kwargs,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # Training args
    training_args = TrainingArguments(
        output_dir=args.output,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        bf16=(torch_dtype == torch.bfloat16),
        fp16=(torch_dtype == torch.float16),
        gradient_checkpointing=True,
        report_to=["tensorboard"],
        dataloader_num_workers=4,
        evaluation_strategy="no",
        save_strategy="steps",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    trainer.train()

    # Save model and tokenizer
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    # Log run metadata
    run_meta = {
        "type": "sft",
        "dataset": args.dataset,
        "base_model": args.base_model,
        "output": args.output,
        "timestamp": datetime.now().isoformat(),
        "load_in_4bit": bool(args.load_in_4bit),
        "bf16": (torch_dtype == torch.bfloat16),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }
    with open("/app/logs/training/training_runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(run_meta, ensure_ascii=False) + "\n")



# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    main()
