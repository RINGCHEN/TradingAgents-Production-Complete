#!/usr/bin/env python3
"""
簡化的 LoRA 訓練腳本 - Phase 2 示範用
"""

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType
import os
from datetime import datetime

def main():
    print("Starting Phase 2 LoRA training demo")
    
    # 配置
    model_name = "Qwen/Qwen2-1.5B-Instruct"
    dataset_path = "data/datasets/phase2_demo"
    output_dir = "models/phase2_lora_adapter"
    
    print(f"Loading model: {model_name}")
    
    # 量化配置
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    # 載入 tokenizer 和模型
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    
    print("Configuring LoRA")
    
    # LoRA 配置
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    
    # 應用 LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    print("Loading training data")
    
    # 載入數據集
    dataset = load_dataset('json', data_files=f'{dataset_path}/training_data.jsonl', split='train')
    
    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        for instruction, input, output in zip(instructions, inputs, outputs):
            text = f"指令: {instruction}\n輸入: {input}\n輸出: {output}{tokenizer.eos_token}"
            texts.append(text)
        return {"text": texts}
    
    dataset = dataset.map(formatting_prompts_func, batched=True)
    
    def tokenize_function(examples):
        result = tokenizer(examples["text"], truncation=True, max_length=512)
        result["labels"] = result["input_ids"].copy()
        return result
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
    
    print("Starting training")
    
    # 訓練參數
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        warmup_steps=50,
        logging_steps=10,
        save_steps=100,
        eval_strategy="no",
        save_strategy="steps",
        remove_unused_columns=True,
        report_to="none",  # 不使用 tensorboard
        gradient_checkpointing=False,  # 關閉梯度檢查點
    )
    
    # 數據整理器
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    # 創建訓練器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
    )
    
    # 開始訓練
    trainer.train()
    
    print("Saving LoRA adapter")
    
    # 保存 LoRA 適配器
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # 記錄訓練日誌
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "dataset_path": dataset_path,
        "output_dir": output_dir,
        "status": "completed",
        "phase": "Phase 2 Demo",
        "lora_config": {
            "r": 8,
            "alpha": 16,
            "dropout": 0.1
        }
    }
    
    os.makedirs("logs/training", exist_ok=True)
    with open("logs/training/training_runs.jsonl", "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    print("Phase 2 LoRA training completed successfully!")
    print(f"Model saved in: {output_dir}")


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