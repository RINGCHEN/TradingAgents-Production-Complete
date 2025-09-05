# TradingAgents GPU Training Infrastructure

## 天工 RTX 4070 Enterprise Training Environment

### Overview

This directory contains the complete GPU training infrastructure for TradingAgents, optimized for RTX 4070 12GB VRAM. The system provides enterprise-grade training capabilities with comprehensive monitoring, version control, and cloud synchronization.

### Architecture Components

```
TradingAgents/
├── gpu_training/
│   ├── Dockerfile.gpu-training      # CUDA 12.1 + PyTorch 2.1+ container
│   ├── requirements-gpu.txt         # GPU-optimized dependencies
│   ├── training_entrypoint.py       # Unified training orchestrator
│   └── README.md                    # This documentation
├── deployment/
│   ├── dvc_setup.sh                 # DVC + Git + GCS integration
│   ├── gpu_monitor.py               # Real-time GPU monitoring
│   ├── sync_models.py               # Model synchronization pipeline
│   ├── test_gpu_infrastructure.py   # Comprehensive testing suite
│   └── setup_gpu_infrastructure.sh  # Master setup orchestrator
└── docker-compose.gpu.yml           # Multi-service orchestration
```

### Key Features

#### 🚀 **Enterprise Docker Environment**
- **CUDA 12.1** with PyTorch 2.1+ support
- **RTX 4070 12GB** memory optimizations
- **Mixed precision training** for efficiency
- **Automatic environment fingerprinting**
- **Health checks** and **thermal protection**

#### 🗂️ **Complete Version Control**
- **Git + DVC** three-way version control
- **Google Cloud Storage** backend
- **Code + Data + Model** traceability
- **One-click version snapshots**
- **Historical version restoration**

#### 📊 **Real-time Monitoring**
- **GPU temperature** and **utilization** tracking
- **Memory usage** and **power consumption**
- **Automatic thermal protection**
- **Performance optimization** suggestions
- **Alert system** with **cooldown** logic

#### ☁️ **Automated Synchronization**
- **Local ⟷ Cloud** model synchronization
- **Compression** and **encryption** support
- **Version management** with **metadata**
- **Blue-green deployment** preparation
- **Rollback capabilities**

#### 🎯 **Training Optimization**
- **GRPO** (Gradient-based Reward Policy Optimization)
- **LoRA** (Low-Rank Adaptation) fine-tuning
- **Automatic batch size** adjustment
- **Memory-efficient** gradient checkpointing
- **Distributed training** support

### Quick Start

#### 1. System Requirements

- **Linux** with NVIDIA GPU support
- **RTX 4070** or equivalent (12GB+ VRAM)
- **20GB** free disk space
- **16GB** system RAM (recommended)
- **Docker** with GPU support

#### 2. One-Command Setup

```bash
# Navigate to TradingAgents directory
cd /path/to/TradingAgents

# Run master setup script
chmod +x deployment/setup_gpu_infrastructure.sh
./deployment/setup_gpu_infrastructure.sh
```

#### 3. Start Training Environment

```bash
# Start all services
./start_gpu_training.sh

# Check status
./check_gpu_status.sh
```

#### 4. Access Services

- **TensorBoard**: http://localhost:6006
- **Jupyter Lab**: http://localhost:8888
- **Monitoring Dashboard**: http://localhost:3000
- **Training API**: http://localhost:8080

### Training Modes

#### GRPO Training (Financial Agent Optimization)

```bash
# Using Docker
docker run --gpus all -v $(pwd)/data:/app/data \
  tradingagents:gpu-training \
  python3 /app/gpu_training/training_entrypoint.py \
  --mode grpo \
  --dataset /app/data/datasets/reward_data \
  --output /app/models/grpo_model

# Using Python directly
python3 gpu_training/training_entrypoint.py \
  --mode grpo \
  --dataset data/datasets/reward_data \
  --output models/grpo_model
```

#### LoRA Fine-tuning (Memory Efficient)

```bash
# Using Docker
docker run --gpus all -v $(pwd)/data:/app/data \
  tradingagents:gpu-training \
  python3 /app/gpu_training/training_entrypoint.py \
  --mode lora \
  --dataset /app/data/datasets/training_data \
  --output /app/models/lora_model

# Using Python directly  
python3 gpu_training/training_entrypoint.py \
  --mode lora \
  --dataset data/datasets/training_data \
  --output models/lora_model
```

#### Environment Verification

```bash
# Verify GPU setup
python3 gpu_training/training_entrypoint.py --mode verify

# Run comprehensive tests
python3 deployment/test_gpu_infrastructure.py
```

### Configuration

#### Training Configuration (`gpu_training/training_config.yaml`)

```yaml
lora:
  model_name: "microsoft/DialoGPT-medium"
  batch_size: 4                    # Optimized for RTX 4070
  gradient_accumulation_steps: 8
  learning_rate: 5e-4
  num_train_epochs: 3
  warmup_steps: 100
  fp16: true                       # Mixed precision

grpo:
  model_name: "microsoft/DialoGPT-medium"
  batch_size: 4
  gradient_accumulation_steps: 8
  learning_rate: 5e-5
  ppo_epochs: 3
  warmup_steps: 100
  fp16: true
```

#### Monitoring Configuration (`deployment/monitoring_config.yml`)

```yaml
monitoring_interval: 10          # seconds
temp_threshold: 80              # °C
memory_threshold: 95            # %
power_threshold: 220            # W (RTX 4070 limit)
enable_thermal_protection: true
enable_auto_scaling: true
alert_cooldown: 300            # seconds
```

### Data Version Control (DVC)

#### Initialize DVC System

```bash
# Setup DVC with Google Cloud Storage
./deployment/dvc_setup.sh
```

#### Create Version Snapshots

```bash
# Create complete version snapshot
./deployment/create_version_snapshot.sh "training_v1"

# List available snapshots
git tag | grep "snapshot_"
```

#### Restore Previous Versions

```bash
# Restore specific snapshot
./deployment/restore_version_snapshot.sh "training_v1"

# Restore by timestamp
./deployment/restore_version_snapshot.sh "snapshot_20240806_143000"
```

#### Track Training History

```bash
# View training history
python3 deployment/training_history.py list

# Compare training runs
python3 deployment/training_history.py compare run_1 run_2
```

### Model Synchronization

#### Manual Synchronization

```bash
# Sync specific model to cloud
python3 deployment/sync_models.py \
  --action sync-to-cloud \
  --model my_trained_model

# Sync from cloud
python3 deployment/sync_models.py \
  --action sync-from-cloud \
  --model my_trained_model

# Bulk sync all models
python3 deployment/sync_models.py --action bulk-sync
```

#### Continuous Synchronization

```bash
# Start continuous sync daemon
python3 deployment/sync_models.py --action continuous
```

#### Deploy to Production

```bash
# Deploy to staging
python3 deployment/sync_models.py \
  --action deploy \
  --model my_trained_model \
  --environment staging

# Deploy to production
python3 deployment/sync_models.py \
  --action deploy \
  --model my_trained_model \
  --environment production
```

### Monitoring and Alerts

#### Real-time Monitoring

```bash
# Start monitoring daemon
python3 deployment/gpu_monitor.py --daemon

# Get current metrics
python3 deployment/gpu_monitor.py

# Performance summary
python3 deployment/gpu_monitor.py --summary --hours 24
```

#### Monitor GPU Status

```bash
# Basic GPU info
nvidia-smi

# Detailed monitoring
watch -n 1 'nvidia-smi'

# Memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

### Troubleshooting

#### Common Issues

**1. CUDA Out of Memory**
```bash
# Reduce batch size in training_config.yaml
batch_size: 2  # Reduce from 4

# Or use gradient accumulation
gradient_accumulation_steps: 16  # Increase from 8
```

**2. GPU Not Detected**
```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

**3. DVC Sync Issues**
```bash
# Check GCS credentials
export GOOGLE_APPLICATION_CREDENTIALS=/app/deployment/gcs_credentials.json

# Test DVC status
dvc status
```

**4. Monitoring Alerts**
```bash
# Check alert history
cat /app/logs/monitoring/alerts.jsonl

# View monitoring logs
tail -f /app/logs/monitoring/gpu_monitor.log
```

#### Performance Optimization

**RTX 4070 Specific Optimizations:**

1. **Memory Management**
   - Use `fp16=True` for mixed precision
   - Set `gradient_checkpointing=True`
   - Limit `per_device_train_batch_size=4`

2. **Compute Optimization**
   - Enable `torch.backends.cudnn.benchmark=True`
   - Use `torch.compile()` for PyTorch 2.0+
   - Set `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512`

3. **Thermal Management**
   - Monitor temperature < 80°C
   - Ensure adequate case ventilation
   - Consider power limit adjustments

### Advanced Usage

#### Custom Training Scripts

```python
from gpu_training.training_entrypoint import GPUTrainingOrchestrator

# Initialize orchestrator
orchestrator = GPUTrainingOrchestrator()

# Verify environment
verification = orchestrator.verify_gpu_environment()

# Setup training
config = orchestrator.setup_training_environment()

# Run custom training
success = orchestrator.run_lora_finetuning(
    dataset_path="data/custom_dataset",
    model_output_path="models/custom_model"
)
```

#### Integration with TradingAgents

```python
# Import TradingAgents services
from tradingagents.services.training_pipeline import TrainingPipeline
from gpu_training.training_entrypoint import GPUTrainingOrchestrator

# Create integrated training pipeline
pipeline = TrainingPipeline(
    orchestrator=GPUTrainingOrchestrator(),
    analyst_type="fundamentals_analyst",
    market_data_source="taiwan_market"
)

# Run training with market data
pipeline.train_on_market_data(
    start_date="2023-01-01",
    end_date="2024-01-01",
    stocks=["2330", "2454", "2881"]
)
```

### Security Considerations

- **Credentials**: Store GCS credentials securely
- **Network**: Use VPN for cloud synchronization
- **Data**: Encrypt sensitive training data
- **Access**: Limit Docker daemon access
- **Logs**: Rotate and secure log files

### Performance Benchmarks

**RTX 4070 12GB Expected Performance:**

| Model Size | Batch Size | Training Speed | Memory Usage |
|------------|------------|----------------|--------------|
| DialoGPT-medium (117M) | 4 | ~2.5 steps/sec | ~8GB |
| DialoGPT-large (345M) | 2 | ~1.2 steps/sec | ~11GB |
| Custom LoRA (16-rank) | 8 | ~4.0 steps/sec | ~6GB |
| GRPO Fine-tune | 4 | ~2.0 steps/sec | ~9GB |

### Support and Maintenance

#### Log Locations

- **Training**: `/app/logs/training/`
- **Monitoring**: `/app/logs/monitoring/`
- **Sync**: `/app/logs/sync/`
- **Setup**: `/app/logs/setup/`

#### Cleanup

```bash
# Stop all services
./cleanup_gpu_training.sh

# Remove Docker images
docker system prune -f

# Clear logs
rm -rf logs/training/* logs/monitoring/* logs/sync/*
```

#### Updates

```bash
# Update Docker images
docker pull nvidia/cuda:12.1-devel-ubuntu22.04

# Rebuild training image
docker build -f gpu_training/Dockerfile.gpu-training -t tradingagents:gpu-training .

# Update Python dependencies
pip install -r gpu_training/requirements-gpu.txt --upgrade
```

---

## Contributing

When contributing to the GPU training infrastructure:

1. **Test thoroughly** on RTX 4070 hardware
2. **Update documentation** for any configuration changes
3. **Maintain backward compatibility** with existing models
4. **Follow security best practices** for credentials
5. **Optimize for memory efficiency** given 12GB limit

## License

This GPU training infrastructure is part of the TradingAgents system and follows the same licensing terms.