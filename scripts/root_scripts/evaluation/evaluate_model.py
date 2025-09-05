import os
import yaml
import torch
import argparse
import json
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import PeftModel
import numpy as np

def load_config(config_path):
    """Loads a YAML configuration file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def prepare_dataset(tokenizer, jsonl_path, test_size=0.2):
    """
    Loads a JSONL file, splits it into train/test sets, and tokenizes it.
    """
    dataset = load_dataset('json', data_files=jsonl_path, split='train')
    
    if len(dataset) * test_size < 1:
        print("Warning: Dataset is too small to create a test split. Using the entire dataset for evaluation.")
        eval_dataset = dataset
    else:
        dataset_split = dataset.train_test_split(test_size=test_size, seed=42)
        eval_dataset = dataset_split['test']

    def tokenize_function(examples):
        text = [p + c for p, c in zip(examples.get("prompt", ""), examples.get("completion", ""))]
        return tokenizer(text, truncation=True, padding='max_length', max_length=256)

    tokenized_eval_dataset = eval_dataset.map(tokenize_function, batched=True, remove_columns=eval_dataset.column_names)
    return tokenized_eval_dataset

def main():
    """
    Main function to evaluate a trained model adapter.
    """
    parser = argparse.ArgumentParser(description="Evaluate a fine-tuned AI analyst model.")
    parser.add_argument("--analyst_name", type=str, required=True, help="The name of the analyst to evaluate (e.g., 'risk_analyst').")
    args = parser.parse_args()

    analyst_name = args.analyst_name
    print(f"\n--- Starting Evaluation for {analyst_name} ---")

    # --- Configuration and Paths ---
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_config_path = os.path.join(project_root, "configs/data_sources.yaml")
    training_config_path = os.path.join(project_root, f"training/{analyst_name}/config.yaml")

    if not os.path.exists(training_config_path):
        print(f"Error: Configuration file not found for {analyst_name} at {training_config_path}")
        return

    data_cfg = load_config(data_config_path)
    train_cfg = load_config(training_config_path)

    # --- Load Dataset ---
    storage_base = os.environ.get('TRADING_AGENTS_DATA_DIR', os.path.join(project_root, 'ai_training_data'))
    source_file = train_cfg['data']['source_file']
    processed_subdir = data_cfg['storage']['processed_subdir']
    jsonl_path = os.path.join(storage_base, processed_subdir, source_file)

    if not os.path.exists(jsonl_path):
        print(f"Error: Data file not found at {jsonl_path}. Please ensure data processing has been run.")
        return

    # --- Model and Tokenizer ---
    model_name = train_cfg['model']['base_model']
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto"
    )

    # --- Load the PEFT Adapter (Dynamically) ---
    models_base_dir = os.environ.get('TRADING_AGENTS_MODELS_DIR', os.path.join(project_root, 'models'))
    # Dynamically get output_dir from the analyst's config
    adapter_subpath = train_cfg['model'].get('output_dir', analyst_name) # Fallback to analyst_name
    adapter_path = os.path.join(models_base_dir, adapter_subpath)

    # Check for a 'final_adapter' subdirectory, which is a common pattern
    if os.path.exists(os.path.join(adapter_path, 'final_adapter')):
        adapter_path = os.path.join(adapter_path, 'final_adapter')

    if not os.path.exists(adapter_path):
        print(f"Error: Trained model adapter not found at {adapter_path}. Please ensure training has been run.")
        return
        
    print(f"Loading adapter from: {adapter_path}")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval() # Set the model to evaluation mode

    print("--- Model and Adapter Loaded Successfully ---")

    # --- Prepare Dataset and Trainer ---
    eval_dataset = prepare_dataset(tokenizer, jsonl_path)
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    eval_args = TrainingArguments(
        output_dir=f"./evaluation_results/{analyst_name}",
        per_device_eval_batch_size=4,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=eval_args,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    # --- Run Evaluation ---
    print("--- Running Evaluation ---")
    results = trainer.evaluate()
    
    # --- Display Results ---
    print("--- Evaluation Complete. Results: ---")
    for key, value in results.items():
        print(f"{key}: {value:.4f}")
        
    try:
        perplexity = np.exp(results["eval_loss"])
        print(f"Perplexity: {perplexity:.4f}")
    except KeyError:
        print("Could not calculate perplexity because 'eval_loss' was not found in the results.")


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