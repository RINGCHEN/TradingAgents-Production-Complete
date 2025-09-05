#!/usr/bin/env python3
"""
LLaMA Models Performance Benchmark
比較不同 LLaMA 模型在金融分析任務上的性能
"""

import os
import time
import json
import torch
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import psutil

class LLaMABenchmark:
    """LLaMA 模型性能基準測試"""
    
    def __init__(self):
        self.results = {}
        self.test_cases = self._load_test_cases()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def _load_test_cases(self) -> List[Dict[str, str]]:
        """載入測試案例"""
        return [
            {
                "id": "technical_analysis",
                "instruction": "Analyze TSMC stock technical indicators",
                "input": "TSMC price 520, volume +25%, RSI 65, MACD bullish",
                "expected_keywords": ["support", "resistance", "bullish", "momentum"]
            },
            {
                "id": "investment_analysis", 
                "instruction": "Evaluate MediaTek investment potential",
                "input": "MediaTek launches new AI chip, 40% performance boost",
                "expected_keywords": ["investment", "potential", "growth", "competitive"]
            },
            {
                "id": "sector_outlook",
                "instruction": "Assess semiconductor sector outlook",
                "input": "AI demand strong, inventory correction ending",
                "expected_keywords": ["outlook", "recovery", "demand", "cycle"]
            },
            {
                "id": "market_strategy",
                "instruction": "Provide Taiwan stock market strategy",
                "input": "Taiwan index 17800, foreign selling, TSMC strong",
                "expected_keywords": ["strategy", "allocation", "risk", "target"]
            }
        ]
    
    def _get_model_config(self, model_name: str) -> Dict[str, Any]:
        """獲取模型配置"""
        configs = {
            "Qwen/Qwen2-1.5B-Instruct": {
                "max_memory": "4GB",
                "batch_size": 1,
                "load_in_4bit": True
            },
            "meta-llama/Llama-3.2-1B-Instruct": {
                "max_memory": "6GB", 
                "batch_size": 1,
                "load_in_4bit": True
            },
            "meta-llama/Llama-3.2-3B-Instruct": {
                "max_memory": "8GB",
                "batch_size": 1, 
                "load_in_4bit": True
            },
            "meta-llama/Llama-3.2-7B-Instruct": {
                "max_memory": "12GB",
                "batch_size": 1,
                "load_in_4bit": True
            }
        }
        return configs.get(model_name, configs["Qwen/Qwen2-1.5B-Instruct"])
    
    def load_model(self, model_name: str) -> Tuple[Any, Any]:
        """載入模型和tokenizer"""
        print(f"Loading model: {model_name}")
        
        config = self._get_model_config(model_name)
        
        # 載入 tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 量化配置
        bnb_config = None
        if config["load_in_4bit"] and torch.cuda.is_available():
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        
        # 載入模型
        model_kwargs = {
            "torch_dtype": torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            "device_map": "auto" if torch.cuda.is_available() else None
        }
        
        if bnb_config:
            model_kwargs["quantization_config"] = bnb_config
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **model_kwargs
        )
        
        return model, tokenizer
    
    def run_inference_benchmark(self, model, tokenizer, test_case: Dict[str, str]) -> Dict[str, Any]:
        """運行推理基準測試"""
        
        # 構建提示詞
        if "llama" in tokenizer.name_or_path.lower():
            # LLaMA 格式
            prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{test_case['instruction']}: {test_case['input']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        else:
            # 通用格式
            prompt = f"指令: {test_case['instruction']}\n輸入: {test_case['input']}\n輸出: "
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        
        # 記錄開始時間和記憶體
        start_time = time.time()
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            start_memory = torch.cuda.memory_allocated()
        
        # 生成回應
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # 記錄結束時間和記憶體
        end_time = time.time()
        inference_time = end_time - start_time
        
        if torch.cuda.is_available():
            peak_memory = torch.cuda.max_memory_allocated()
            memory_used = (peak_memory - start_memory) / 1024**3  # GB
        else:
            memory_used = 0
        
        # 解碼回應
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = generated_text[len(prompt):].strip()
        
        # 計算tokens
        input_tokens = len(inputs.input_ids[0])
        output_tokens = len(outputs[0]) - input_tokens
        tokens_per_second = output_tokens / inference_time if inference_time > 0 else 0
        
        # 質量評估 (簡單的關鍵詞匹配)
        keywords_found = sum(1 for keyword in test_case["expected_keywords"] 
                           if keyword.lower() in response.lower())
        quality_score = keywords_found / len(test_case["expected_keywords"])
        
        return {
            "test_case_id": test_case["id"],
            "response": response,
            "inference_time": inference_time,
            "memory_used_gb": memory_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tokens_per_second": tokens_per_second,
            "quality_score": quality_score,
            "response_length": len(response)
        }
    
    def benchmark_model(self, model_name: str) -> Dict[str, Any]:
        """對單個模型進行基準測試"""
        print(f"\n{'='*50}")
        print(f"Benchmarking: {model_name}")
        print(f"{'='*50}")
        
        try:
            # 載入模型
            model, tokenizer = self.load_model(model_name)
            
            model_results = {
                "model_name": model_name,
                "device": str(model.device) if hasattr(model, 'device') else self.device,
                "test_results": [],
                "summary": {}
            }
            
            # 運行所有測試案例
            for i, test_case in enumerate(self.test_cases):
                print(f"Running test {i+1}/{len(self.test_cases)}: {test_case['id']}")
                
                result = self.run_inference_benchmark(model, tokenizer, test_case)
                model_results["test_results"].append(result)
                
                print(f"  Time: {result['inference_time']:.2f}s")
                print(f"  Tokens/s: {result['tokens_per_second']:.1f}")
                print(f"  Memory: {result['memory_used_gb']:.2f}GB")
                print(f"  Quality: {result['quality_score']:.2f}")
            
            # 計算總結統計
            test_results = model_results["test_results"]
            model_results["summary"] = {
                "avg_inference_time": np.mean([r["inference_time"] for r in test_results]),
                "avg_tokens_per_second": np.mean([r["tokens_per_second"] for r in test_results]),
                "avg_memory_used_gb": np.mean([r["memory_used_gb"] for r in test_results]),
                "avg_quality_score": np.mean([r["quality_score"] for r in test_results]),
                "total_tokens_generated": sum([r["output_tokens"] for r in test_results])
            }
            
            print(f"\nModel Summary:")
            print(f"  Avg Time: {model_results['summary']['avg_inference_time']:.2f}s")
            print(f"  Avg Tokens/s: {model_results['summary']['avg_tokens_per_second']:.1f}")
            print(f"  Avg Memory: {model_results['summary']['avg_memory_used_gb']:.2f}GB")
            print(f"  Avg Quality: {model_results['summary']['avg_quality_score']:.2f}")
            
            # 清理記憶體
            del model
            del tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return model_results
            
        except Exception as e:
            print(f"Error benchmarking {model_name}: {e}")
            return {
                "model_name": model_name,
                "error": str(e),
                "test_results": [],
                "summary": {}
            }
    
    def run_comprehensive_benchmark(self, models: List[str] = None) -> Dict[str, Any]:
        """運行全面的基準測試"""
        if models is None:
            # 默認測試模型
            models = [
                "Qwen/Qwen2-1.5B-Instruct",  # 基準模型
                "meta-llama/Llama-3.2-1B-Instruct",
                "meta-llama/Llama-3.2-3B-Instruct"
            ]
        
        print("LLaMA Models Performance Benchmark")
        print(f"Device: {self.device}")
        print(f"Models to test: {len(models)}")
        print(f"Test cases: {len(self.test_cases)}")
        
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f}GB")
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "device": self.device,
                "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
                "gpu_memory_gb": torch.cuda.get_device_properties(0).total_memory/1024**3 if torch.cuda.is_available() else 0,
                "cpu_count": psutil.cpu_count(),
                "ram_gb": psutil.virtual_memory().total / 1024**3
            },
            "models": {},
            "comparison": {}
        }
        
        # 對每個模型進行基準測試
        for model_name in models:
            benchmark_results["models"][model_name] = self.benchmark_model(model_name)
        
        # 生成比較分析
        self._generate_comparison(benchmark_results)
        
        return benchmark_results
    
    def _generate_comparison(self, results: Dict[str, Any]):
        """生成模型比較分析"""
        models = results["models"]
        valid_models = {name: data for name, data in models.items() 
                       if "error" not in data and data["summary"]}
        
        if len(valid_models) < 2:
            return
        
        comparison = {
            "fastest_inference": None,
            "highest_throughput": None,
            "most_memory_efficient": None,
            "best_quality": None,
            "rankings": {}
        }
        
        # 找出各項最佳表現
        fastest_time = float('inf')
        highest_tokens_ps = 0
        lowest_memory = float('inf')
        best_quality = 0
        
        for name, data in valid_models.items():
            summary = data["summary"]
            
            if summary["avg_inference_time"] < fastest_time:
                fastest_time = summary["avg_inference_time"]
                comparison["fastest_inference"] = name
                
            if summary["avg_tokens_per_second"] > highest_tokens_ps:
                highest_tokens_ps = summary["avg_tokens_per_second"]
                comparison["highest_throughput"] = name
                
            if summary["avg_memory_used_gb"] < lowest_memory:
                lowest_memory = summary["avg_memory_used_gb"]
                comparison["most_memory_efficient"] = name
                
            if summary["avg_quality_score"] > best_quality:
                best_quality = summary["avg_quality_score"]
                comparison["best_quality"] = name
        
        # 綜合排名
        for name in valid_models.keys():
            summary = valid_models[name]["summary"]
            
            # 綜合評分 (速度30%, 吞吐量30%, 記憶體20%, 質量20%)
            speed_score = (fastest_time / summary["avg_inference_time"]) * 0.3
            throughput_score = (summary["avg_tokens_per_second"] / highest_tokens_ps) * 0.3
            memory_score = (lowest_memory / summary["avg_memory_used_gb"]) * 0.2
            quality_score = (summary["avg_quality_score"] / best_quality) * 0.2
            
            overall_score = speed_score + throughput_score + memory_score + quality_score
            comparison["rankings"][name] = {
                "overall_score": overall_score,
                "speed_score": speed_score,
                "throughput_score": throughput_score,
                "memory_score": memory_score,
                "quality_score": quality_score
            }
        
        results["comparison"] = comparison
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """保存基準測試結果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        results_dir = Path("results/benchmarks")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = results_dir / filename
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        # 生成簡化報告
        self._generate_summary_report(results, results_dir / f"summary_{timestamp}.txt")
    
    def _generate_summary_report(self, results: Dict[str, Any], filename: Path):
        """生成簡化摘要報告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("LLaMA Models Benchmark Summary Report\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"Timestamp: {results['timestamp']}\n")
            f.write(f"System: {results['system_info']['gpu_name']} ({results['system_info']['gpu_memory_gb']:.1f}GB)\n\n")
            
            # 模型性能總結
            f.write("Model Performance Summary:\n")
            f.write("-"*30 + "\n")
            
            for name, data in results["models"].items():
                if "error" in data:
                    f.write(f"{name}: ERROR - {data['error']}\n")
                    continue
                    
                summary = data["summary"]
                f.write(f"{name}:\n")
                f.write(f"  Avg Time: {summary['avg_inference_time']:.2f}s\n")
                f.write(f"  Tokens/s: {summary['avg_tokens_per_second']:.1f}\n")
                f.write(f"  Memory: {summary['avg_memory_used_gb']:.2f}GB\n")
                f.write(f"  Quality: {summary['avg_quality_score']:.2f}\n\n")
            
            # 比較結果
            if "comparison" in results:
                comp = results["comparison"]
                f.write("Performance Leaders:\n")
                f.write("-"*20 + "\n")
                f.write(f"Fastest: {comp.get('fastest_inference', 'N/A')}\n")
                f.write(f"Highest Throughput: {comp.get('highest_throughput', 'N/A')}\n")
                f.write(f"Memory Efficient: {comp.get('most_memory_efficient', 'N/A')}\n")
                f.write(f"Best Quality: {comp.get('best_quality', 'N/A')}\n\n")
                
                f.write("Overall Rankings:\n")
                f.write("-"*15 + "\n")
                sorted_rankings = sorted(comp["rankings"].items(), 
                                       key=lambda x: x[1]["overall_score"], reverse=True)
                for i, (name, scores) in enumerate(sorted_rankings, 1):
                    f.write(f"{i}. {name} (Score: {scores['overall_score']:.3f})\n")
        
        print(f"Summary report: {filename}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLaMA Models Benchmark")
    parser.add_argument("--models", nargs="+", help="Models to benchmark")
    parser.add_argument("--output", help="Output filename")
    
    args = parser.parse_args()
    
    benchmark = LLaMABenchmark()
    
    # 運行基準測試
    results = benchmark.run_comprehensive_benchmark(args.models)
    
    # 保存結果
    benchmark.save_results(results, args.output)
    
    print("\nBenchmark completed successfully!")

if __name__ == "__main__":
    main()