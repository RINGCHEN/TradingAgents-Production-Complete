#!/usr/bin/env python3
"""
End-to-End (E2E) Demo Script for the AI Analyst Team.

This script showcases the full analytical pipeline by taking a stock symbol,
invoking a series of specialized AI analysts, and aggregating their insights
into a final, comprehensive report.
"""

import os
import yaml
import torch
import argparse
import json
import re
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)
from peft import PeftModel
from typing import Dict, Any, Optional, List

# --- Configuration ---

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Utility Functions ---

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_project_root() -> str:
    """Gets the absolute path of the project root directory."""
    return os.path.dirname(os.path.abspath(__file__))

def get_latest_data_records(jsonl_path: str, num_records: int = 1) -> List[Dict[str, Any]]:
    """Gets the last N valid JSON records from a JSONL file."""
    if not os.path.exists(jsonl_path):
        return []
    
    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in reversed(lines):
        if len(records) >= num_records:
            break
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
            
    return list(reversed(records))

# --- Core Inference Class ---

class AnalystInference:
    """A class to handle loading a model and running inference for a single analyst."""
    
    def __init__(self, analyst_name: str, project_root: str):
        self.analyst_name = analyst_name
        self.project_root = project_root
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"[{self.analyst_name}] Initialized on device: {self.device}")

    def load_model(self):
        """Loads the base model and the fine-tuned adapter for the analyst."""
        logger.info(f"[{self.analyst_name}] Loading model...")
        try:
            training_config_path = os.path.join(self.project_root, f"training/{self.analyst_name}/config.yaml")
            train_cfg = load_config(training_config_path)
            base_model_name = train_cfg['model']['base_model']

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )

            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True
            )

            self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            models_base_dir = os.environ.get('TRADING_AGENTS_MODELS_DIR', os.path.join(self.project_root, 'models'))
            
            if self.analyst_name == 'technical_analyst':
                adapter_subpath = train_cfg['model'].get('output_dir', self.analyst_name)
                adapter_path = os.path.join(models_base_dir, adapter_subpath, 'final_adapter')
            else:
                adapter_path = os.path.join(models_base_dir, self.analyst_name, 'final_model_v1', 'final_adapter')

            logger.info(f"[{self.analyst_name}] Loading adapter from: {adapter_path}")
            self.model = PeftModel.from_pretrained(base_model, adapter_path)
            self.model = self.model.to(self.device)
            self.model.eval()
            logger.info(f"[{self.analyst_name}] Model loaded successfully.")

        except Exception as e:
            logger.error(f"[{self.analyst_name}] Failed to load model: {e}", exc_info=True)
            raise

    def generate_analysis(self, prompt: str) -> str:
        """Generates an analysis for a given prompt."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model is not loaded. Call load_model() first.")
        
        logger.info(f"[{self.analyst_name}] Generating analysis for prompt: '{prompt[:150]}...'" )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt):].strip()

    def unload_model(self):
        logger.info(f"[{self.analyst_name}] Unloading model.")
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# --- Main Orchestration ---

def create_prompt_for_analyst(analyst_name: str, stock_symbol: str, project_root: str, all_insights: Dict[str, str] = None) -> str:
    """Creates a specific, data-driven prompt for a given analyst and stock symbol."""
    data_dir = os.path.join(os.environ.get('TRADING_AGENTS_DATA_DIR'), 'processed')

    if analyst_name == "technical_analyst":
        jsonl_path = os.path.join(data_dir, f"{stock_symbol}_processed.jsonl")
        latest_data = get_latest_data_records(jsonl_path, 1)
        if latest_data and 'prompt' in latest_data[0]:
            data_summary = latest_data[0]['prompt']
            return f"Given the latest market data: '{data_summary}'. Provide a detailed technical analysis and short-term outlook."
        else:
            return f"Provide a generic technical analysis summary for the stock {stock_symbol}."

    elif analyst_name == "fundamentals_analyst":
        stock_id = stock_symbol.split('.')[0]
        jsonl_path = os.path.join(data_dir, f"{stock_id}_financial_reports_processed.jsonl")
        latest_data = get_latest_data_records(jsonl_path, 1)
        if latest_data and 'prompt' in latest_data[0]:
            data_summary = latest_data[0]['prompt']
            return f"Given the following financial statement data for {stock_symbol}: '{data_summary}'. Provide a detailed fundamental analysis of the company's health, performance, and market position."
        else:
            return f"Provide a generic fundamental analysis summary for the company {stock_symbol}."

    elif analyst_name == "news_analyst":
        jsonl_path = os.path.join(data_dir, "news_articles_processed.jsonl")
        latest_articles = get_latest_data_records(jsonl_path, 5)
        if latest_articles:
            headlines = []
            for article in latest_articles:
                match = re.search(r"標題：(.*?)\\n", article.get('prompt', ''))
                if match:
                    headlines.append(match.group(1))
            if headlines:
                headline_str = "\n".join([f"- {h}" for h in headlines])
                return f"Based on the following recent news headlines for the Taiwan market:\n{headline_str}\n\nWhat is the current overall market sentiment and what are the key narratives?"
        return f"Summarize the recent news and overall sentiment for the company {stock_symbol}."

    elif analyst_name == "risk_analyst":
        if all_insights:
            combined_insights = "\n\n".join([f"--- {name.replace('_', ' ').upper()} ---\n{insight}" for name, insight in all_insights.items()])
            return f"Given the following analysis on technicals, fundamentals, and news:\n\n{combined_insights}\n\nBased on this context, identify and summarize the key risks (market, regulatory, operational) for {stock_symbol}."
        else:
            return f"Identify and summarize the key risks associated with investing in {stock_symbol}."

    elif analyst_name == "social_media_analyst":
        jsonl_path = os.path.join(data_dir, "ptt_posts_processed.jsonl")
        latest_posts = get_latest_data_records(jsonl_path, 3)
        if latest_posts:
            posts_str = "\n\n".join([post.get('prompt', '').replace('請根據以下PTT文章內容，判斷其對股市的影響是利多、利空還是中性，並簡要說明原因：\n', '') for post in latest_posts])
            return f"Based on the following recent posts from the PTT stock forum:\n\n{posts_str}\n\nWhat is the general sentiment and what are the key discussion points about the market and specific stocks?"
        return f"What is the general sentiment and discussion about {stock_symbol} on social media platforms like PTT and Twitter?"

    elif analyst_name == "investment_planner":
        if all_insights:
            combined_insights = "\n\n".join([f"--- {name.replace('_', ' ').upper()} ---\n{insight}" for name, insight in all_insights.items()])
            return f"Based on the following comprehensive analysis from multiple expert analysts, please provide a final investment summary, recommendation, and confidence score for {stock_symbol}.\n\n{combined_insights}\n\n--- FINAL RECOMMENDATION (Confidence Score: Low/Medium/High) ---"
        else:
            return f"Provide a final investment summary and recommendation for {stock_symbol}."
    else:
        return f"What is your analysis of {stock_symbol}?"

def run_demo(stock_symbol: str):
    logger.info(f"--- Starting Full Analysis Demo for Stock: {stock_symbol} ---")
    project_root = get_project_root()
    
    analyst_sequence = [
        "technical_analyst",
        "fundamentals_analyst",
        "news_analyst",
        "risk_analyst",
        "social_media_analyst",
        "investment_planner"
    ]
    
    all_insights = {}

    for analyst_name in analyst_sequence:
        try:
            analyst = AnalystInference(analyst_name, project_root)
            analyst.load_model()
            prompt = create_prompt_for_analyst(analyst_name, stock_symbol, project_root, all_insights)
            insight = analyst.generate_analysis(prompt)
            all_insights[analyst_name] = insight
            logger.info(f"[{analyst_name}] Insight: {insight}")
        except Exception as e:
            logger.error(f"Failed to get insight from {analyst_name}: {e}")
            all_insights[analyst_name] = "Error generating analysis."
        finally:
            if 'analyst' in locals() and analyst.model:
                analyst.unload_model()

    # --- Final Report Generation ---
    print("\n" + "="*50)
    print(f"      COMPREHENSIVE ANALYSIS REPORT FOR: {stock_symbol}")
    print("="*50 + "\n")

    for analyst, insight in all_insights.items():
        # Encode to utf-8 to handle potential special characters in the console
        safe_insight = insight.encode('utf-8', errors='replace').decode('utf-8')
        if analyst != "investment_planner":
            print(f"--- {analyst.replace('_', ' ').upper()} ---")
            print(safe_insight)
            print()

    print("\n" + "-"*20 + " FINAL SUMMARY " + "-"*20)
    if 'investment_planner' in all_insights:
        safe_summary = all_insights['investment_planner'].encode('utf-8', errors='replace').decode('utf-8')
        print(safe_summary)
    else:
        print("Could not generate a final investment plan.")

    print("\n--- END OF REPORT ---")


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
    parser = argparse.ArgumentParser(description="Run a full analysis demo for a given stock symbol.")
    parser.add_argument("--stock", type=str, default="2330.TW", help="The stock symbol to analyze (e.g., '2330.TW').")
    args = parser.parse_args()
    run_demo(stock_symbol=args.stock)
