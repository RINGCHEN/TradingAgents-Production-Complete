# GPU Training Scripts (SFT & LoRA)

This document explains the newly added scripts under `gpu_training/` for training and fine-tuning causal language models.

## Scripts

- `train_sft.py`: Supervised Fine-Tuning using Transformers `Trainer`
- `train_lora.py`: LoRA fine-tuning using PEFT + Transformers `Trainer`

Both scripts:
- Load dataset from a directory (expects a JSONL file like `train.jsonl` or any `*.jsonl` with fields `instruction/input/output` or `text`).
- Save outputs to the specified directory.
- Write a metadata line per run to `logs/training/training_runs.jsonl`.

## Run (Docker)

```bash
# SFT
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

# LoRA
docker run --gpus all \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  tradingagents:gpu-training \
  python3 /app/gpu_training/train_lora.py \
    --dataset /app/data/datasets/training_data \
    --base-model meta-llama/Meta-Llama-3-8B-Instruct \
    --output /app/models/lora_adapter \
    --lora-r 16 --lora-alpha 32 --lora-dropout 0.1 \
    --load-in-4bit
```

## Use the trained outputs in GPT-OSS server

- Full SFT model: set `BASE_MODEL` to the output dir or pass `--base-model` at server start.
- LoRA adapter: set `LORA_ADAPTER` to the adapter directory or pass `--lora-adapter` at server start.

```bash
docker run --gpus all -p 8080:8080 \
  -e DEVICE=auto \
  -e BASE_MODEL=/app/models/sft_model \
  -e LORA_ADAPTER=/app/models/lora_adapter \
  -e LOAD_IN_4BIT=true \
  -v $(pwd)/models:/app/models \
  tradingagents:gpt-oss \
  python -m server --host 0.0.0.0 --port 8080 --device auto
```

Notes:
- When using a local model directory, ensure `config.json`, `model.safetensors` (or shards), and tokenizer files are present.
- For LoRA, ensure the adapter directory contains the PEFT files (`adapter_config.json`, adapter weights).
