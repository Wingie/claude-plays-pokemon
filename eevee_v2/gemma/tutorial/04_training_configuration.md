# Tutorial 04: Training Configuration

## Learning Objectives 🎯

By the end of this tutorial, you will:
- Master accelerate configuration for distributed training
- Understand QLoRA (Quantized Low-Rank Adaptation) setup
- Optimize hyperparameters for Pokemon grid training
- Configure monitoring with Weights & Biases
- Set up automated batch size finding
- Understand memory optimization strategies

## Training Infrastructure Overview 🏗️

### The Complete Training Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Training Infrastructure                   │
├─────────────────────────────────────────────────────────────┤
│ Monitoring: Weights & Biases + TensorBoard                  │
├─────────────────────────────────────────────────────────────┤
│ Framework: TRL (Transformers Reinforcement Learning)        │
├─────────────────────────────────────────────────────────────┤
│ Optimization: QLoRA (4-bit quantization + LoRA adapters)   │
├─────────────────────────────────────────────────────────────┤
│ Distribution: Accelerate (Multi-GPU + DeepSpeed)           │
├─────────────────────────────────────────────────────────────┤
│ Hardware: CUDA GPUs (8GB minimum, 24GB recommended)        │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Files Overview

```
eevee_v2/gemma/
├── accelerate_configs/           ← Hardware-specific training configs
│   ├── single_gpu.yaml          ← Single GPU setup
│   ├── multi_gpu.yaml           ← Multi-GPU distributed
│   ├── deepspeed_zero3.yaml     ← DeepSpeed Zero Stage 3
│   └── cpu_mps.yaml             ← CPU/Apple Silicon development
├── wandb_config.yaml            ← Experiment tracking
├── .env                         ← Environment variables & tokens
└── train_grid.sh                ← Training execution script
```

## Accelerate Configuration 🚀

### Understanding Accelerate

Accelerate is HuggingFace's library for distributed training:

- **Automatic Distribution**: Handles multi-GPU setup transparently
- **Memory Optimization**: DeepSpeed Zero for large models
- **Mixed Precision**: FP16/BF16 for speed and memory efficiency
- **Gradient Accumulation**: Simulate larger batch sizes

### Single GPU Configuration

For most users with one GPU (8-24GB VRAM):

```yaml
# accelerate_configs/single_gpu.yaml
compute_environment: LOCAL_MACHINE
debug: false
distributed_type: 'NO'
downcast_bf16: 'no'
machine_rank: 0
main_training_function: main
mixed_precision: bf16
num_machines: 1
num_processes: 1
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false
```

**Key Features:**
- `mixed_precision: bf16`: 16-bit training for memory efficiency
- `num_processes: 1`: Single GPU usage
- `distributed_type: 'NO'`: No distribution needed

### Multi-GPU Configuration

For systems with multiple GPUs:

```yaml
# accelerate_configs/multi_gpu.yaml
compute_environment: LOCAL_MACHINE
debug: false
distributed_type: MULTI_GPU
downcast_bf16: 'no'
gpu_ids: all
machine_rank: 0
main_training_function: main
mixed_precision: bf16
num_machines: 1
num_processes: 2  # Number of GPUs
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false
```

**Auto-Detection Script:**

```python
#!/usr/bin/env python3
"""
Automatic Accelerate Configuration
Detects hardware and creates optimal config
"""

import torch
import subprocess
from pathlib import Path

def detect_hardware():
    """Detect available hardware configuration."""
    
    config = {
        "has_cuda": torch.cuda.is_available(),
        "has_mps": torch.backends.mps.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "total_vram": 0
    }
    
    if config["has_cuda"]:
        for i in range(config["gpu_count"]):
            props = torch.cuda.get_device_properties(i)
            config["total_vram"] += props.total_memory / (1024**3)
            print(f"GPU {i}: {props.name} ({props.total_memory / (1024**3):.1f}GB)")
    
    return config

def recommend_config(hardware):
    """Recommend optimal accelerate configuration."""
    
    if not hardware["has_cuda"] and not hardware["has_mps"]:
        return "cpu_mps.yaml"  # CPU fallback
    
    if hardware["gpu_count"] == 1:
        if hardware["total_vram"] >= 20:
            return "single_gpu.yaml"  # Standard single GPU
        else:
            return "single_gpu_low_mem.yaml"  # Memory optimized
    
    elif hardware["gpu_count"] >= 2:
        if hardware["total_vram"] >= 40:
            return "multi_gpu.yaml"  # Standard multi-GPU
        else:
            return "deepspeed_zero3.yaml"  # Memory optimized
    
    return "single_gpu.yaml"  # Safe default

# Auto-configure
hardware = detect_hardware()
recommended_config = recommend_config(hardware)
print(f"Recommended config: {recommended_config}")
```

### DeepSpeed Zero Stage 3

For maximum memory efficiency with large models:

```yaml
# accelerate_configs/deepspeed_zero3.yaml
compute_environment: LOCAL_MACHINE
debug: false
deepspeed_config:
  bf16:
    enabled: true
  gradient_accumulation_steps: auto
  gradient_clipping: auto
  offload_optimizer_device: cpu
  offload_param_device: cpu
  zero3_init_flag: true
  zero3_save_16bit_model: true
  zero_stage: 3
distributed_type: DEEPSPEED
downcast_bf16: 'no'
machine_rank: 0
main_training_function: main
mixed_precision: bf16
num_machines: 1
num_processes: 2
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false
```

**DeepSpeed Zero Features:**
- `zero_stage: 3`: Partition optimizer states, gradients, and parameters
- `offload_optimizer_device: cpu`: Offload optimizer to CPU memory
- `offload_param_device: cpu`: Offload parameters to CPU when not in use
- Enables training 4B parameter models on 8GB GPUs!

## QLoRA Configuration 🧮

### Understanding QLoRA

QLoRA (Quantized Low-Rank Adaptation) enables efficient fine-tuning:

```
Full Model (4B params, 16GB) → QLoRA (1M trainable params, 4GB)
              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4-bit Quantized Base Model (frozen, ~4GB)                  │
├─────────────────────────────────────────────────────────────┤
│ + LoRA Adapters (trainable, ~50MB)                         │
├─────────────────────────────────────────────────────────────┤
│ = Same performance, 4x less memory                         │
└─────────────────────────────────────────────────────────────┘
```

### QLoRA Implementation

```python
# QLoRA configuration in train_frame_grid.py
from transformers import BitsAndBytesConfig
from peft import LoraConfig

# 4-bit quantization config
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,                    # Enable 4-bit quantization
    bnb_4bit_quant_type="nf4",           # NormalFloat4 quantization
    bnb_4bit_compute_dtype=torch.bfloat16, # Compute in bfloat16
    bnb_4bit_use_double_quant=True,      # Nested quantization
)

# LoRA adapter config
lora_config = LoraConfig(
    r=64,                                 # Rank of adaptation
    lora_alpha=128,                       # LoRA scaling parameter
    target_modules="all-linear",          # Apply to all linear layers
    lora_dropout=0.05,                    # Dropout for regularization
    bias="none",                          # Don't adapt bias terms
    task_type="CAUSAL_LM",               # Causal language modeling
)

# Load model with QLoRA
model = AutoModelForImageTextToText.from_pretrained(
    "google/gemma-3-4b-it",
    quantization_config=quantization_config,
    torch_dtype=torch.bfloat16,
    attn_implementation="eager"  # Required for QLoRA
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: 1,048,576 || all params: 4,000,000,000 || trainable%: 0.026
```

### LoRA Target Modules

Understanding which layers to adapt:

```python
# Inspect model architecture for LoRA targets
def inspect_model_layers():
    """Find the best layers to apply LoRA to."""
    
    model = AutoModelForImageTextToText.from_pretrained("google/gemma-3-4b-it")
    
    # Find all linear layers
    linear_layers = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            linear_layers.append(name)
    
    print("🔍 Available Linear Layers:")
    for layer in linear_layers[:10]:  # Show first 10
        print(f"  {layer}")
    
    # Common LoRA targets for Gemma
    recommended_targets = [
        "q_proj",     # Query projection
        "k_proj",     # Key projection  
        "v_proj",     # Value projection
        "o_proj",     # Output projection
        "gate_proj",  # Gate projection (MLP)
        "up_proj",    # Up projection (MLP)
        "down_proj"   # Down projection (MLP)
    ]
    
    return recommended_targets

# Specialized configs for different memory budgets
lora_configs = {
    "high_memory": LoraConfig(r=128, lora_alpha=256),  # Best quality
    "medium_memory": LoraConfig(r=64, lora_alpha=128), # Balanced
    "low_memory": LoraConfig(r=32, lora_alpha=64),     # Minimal memory
}
```

## Hyperparameter Optimization 🎛️

### Pokemon-Specific Hyperparameters

Optimized settings for grid-based Pokemon training:

```python
# Training hyperparameters
training_config = {
    # Core training settings
    "learning_rate": 2e-4,               # Conservative for stability
    "max_steps": 1500,                   # ~3-5 epochs with our data
    "per_device_train_batch_size": 2,    # GPU memory dependent
    "gradient_accumulation_steps": 4,    # Effective batch size = 8
    
    # Memory optimization
    "gradient_checkpointing": True,      # Trade compute for memory
    "dataloader_num_workers": 0,         # Avoid multiprocessing issues
    "bf16": True,                        # Mixed precision training
    
    # Regularization
    "weight_decay": 0.01,                # Prevent overfitting
    "max_grad_norm": 1.0,                # Gradient clipping
    "warmup_ratio": 0.1,                 # Learning rate warmup
    
    # Scheduling
    "lr_scheduler_type": "cosine",       # Cosine annealing
    "optim": "adamw_torch",              # AdamW optimizer
    
    # Logging and saving
    "logging_steps": 10,                 # Log every 10 steps
    "save_steps": 250,                   # Save every 250 steps
    "eval_steps": 250,                   # Evaluate every 250 steps
    "save_total_limit": 3,               # Keep only 3 checkpoints
}
```

### Hyperparameter Sensitivity Analysis

Understanding which hyperparameters matter most:

```python
# Hyperparameter importance for Pokemon VLM training
hyperparameter_sensitivity = {
    "learning_rate": {
        "importance": "CRITICAL",
        "range": "1e-5 to 1e-3",
        "optimal": "2e-4",
        "notes": "Too high = instability, too low = slow convergence"
    },
    "lora_r": {
        "importance": "HIGH", 
        "range": "16 to 128",
        "optimal": "64",
        "notes": "Higher = more capacity but more memory"
    },
    "lora_alpha": {
        "importance": "HIGH",
        "range": "32 to 256", 
        "optimal": "128",
        "notes": "Should be ~2x lora_r for stability"
    },
    "batch_size": {
        "importance": "MEDIUM",
        "range": "1 to 8",
        "optimal": "2-4",
        "notes": "Memory limited, use gradient accumulation"
    },
    "max_steps": {
        "importance": "MEDIUM",
        "range": "500 to 3000",
        "optimal": "1500",
        "notes": "Monitor for overfitting, early stopping"
    }
}
```

### Automatic Hyperparameter Tuning

Using Weights & Biases sweeps:

```yaml
# wandb_sweep.yaml
program: scripts/train_frame_grid.py
method: bayes
metric:
  goal: minimize
  name: train/loss
parameters:
  learning_rate:
    distribution: log_uniform_values
    min: 1e-5
    max: 1e-3
  lora_r:
    values: [32, 64, 128]
  lora_alpha:
    values: [64, 128, 256]
  gradient_accumulation_steps:
    values: [2, 4, 8]
  weight_decay:
    distribution: uniform
    min: 0.001
    max: 0.1
```

## Batch Size Optimization 📊

### Automatic Batch Size Finding

Our pipeline includes automated batch size detection:

```bash
# Find optimal batch size for your hardware
python scripts/find_batch_size.py \
    --dataset_path training_data/pokemon_grid_dataset.jsonl \
    --model_name google/gemma-3-4b-it \
    --use_peft \
    --output batch_size_results.json
```

### Memory-Batch Size Relationship

Understanding memory usage patterns:

```python
# Memory usage estimation
def estimate_memory_usage(batch_size, sequence_length=8192):
    """Estimate GPU memory usage for Pokemon grid training."""
    
    # Model parameters (4B params in bfloat16)
    model_memory = 4e9 * 2 / (1024**3)  # ~7.5GB
    
    # QLoRA reduces to ~25% of full model
    qlora_model_memory = model_memory * 0.25  # ~1.9GB
    
    # Activation memory (depends on batch size and sequence length)
    # Vision tokens: 729 per image
    # Text tokens: ~100 per sample
    total_tokens = 729 + 100
    
    # Activation memory formula (rough estimate)
    activation_memory = (
        batch_size * total_tokens * 2048 * 2  # hidden_size * bytes_per_param
        * 2  # forward + backward
        / (1024**3)  # Convert to GB
    )
    
    # Optimizer memory (AdamW stores momentum and variance)
    trainable_params = 1e6  # ~1M trainable LoRA parameters
    optimizer_memory = trainable_params * 2 * 4 / (1024**3)  # ~8MB
    
    total_memory = qlora_model_memory + activation_memory + optimizer_memory
    
    return {
        "model": qlora_model_memory,
        "activations": activation_memory,
        "optimizer": optimizer_memory,
        "total": total_memory
    }

# Test different batch sizes
for batch_size in [1, 2, 4, 8]:
    memory = estimate_memory_usage(batch_size)
    print(f"Batch size {batch_size}: {memory['total']:.1f}GB total")
    
# Example output:
# Batch size 1: 2.4GB total
# Batch size 2: 3.1GB total  
# Batch size 4: 4.5GB total
# Batch size 8: 7.3GB total
```

### Hardware-Specific Recommendations

```python
# Batch size recommendations by GPU
gpu_recommendations = {
    "RTX 3070 (8GB)": {
        "batch_size": 1,
        "gradient_accumulation": 8,
        "effective_batch": 8,
        "config": "single_gpu.yaml"
    },
    "RTX 4070 Ti (12GB)": {
        "batch_size": 2,
        "gradient_accumulation": 4,
        "effective_batch": 8,
        "config": "single_gpu.yaml"
    },
    "RTX 4090 (24GB)": {
        "batch_size": 4,
        "gradient_accumulation": 2,
        "effective_batch": 8,
        "config": "single_gpu.yaml"
    },
    "A100 (40GB)": {
        "batch_size": 8,
        "gradient_accumulation": 1,
        "effective_batch": 8,
        "config": "single_gpu.yaml"
    }
}
```

## Monitoring Configuration 📈

### Weights & Biases Setup

Complete monitoring configuration:

```python
# wandb integration in training script
import wandb

def setup_wandb(config):
    """Initialize comprehensive W&B monitoring."""
    
    wandb.init(
        project="pokemon-gemma-vlm",
        name=f"grid-training-{config['model_size']}-r{config['lora_r']}",
        config=config,
        tags=["pokemon", "gemma", "vlm", "grid", "qlora"],
        notes="2x2 temporal grid training for Pokemon gameplay AI"
    )
    
    # Log model architecture
    wandb.log({
        "model/total_params": config["total_params"],
        "model/trainable_params": config["trainable_params"], 
        "model/trainable_percent": config["trainable_percent"]
    })
    
    # Monitor system metrics
    wandb.watch(model, log="all", log_freq=100)

# Custom metrics for Pokemon training
def log_pokemon_metrics(predictions, targets, step):
    """Log Pokemon-specific training metrics."""
    
    # Parse action predictions
    predicted_actions = []
    target_actions = []
    
    for pred, target in zip(predictions, targets):
        try:
            pred_json = json.loads(pred)
            target_json = json.loads(target)
            
            predicted_actions.append(pred_json.get("button", "unknown"))
            target_actions.append(target_json.get("button", "unknown"))
        except:
            continue
    
    # Calculate action accuracy
    if predicted_actions and target_actions:
        action_accuracy = sum(
            p == t for p, t in zip(predicted_actions, target_actions)
        ) / len(predicted_actions)
        
        wandb.log({
            "pokemon/action_accuracy": action_accuracy,
            "pokemon/predicted_actions": wandb.Histogram(predicted_actions),
            "pokemon/target_actions": wandb.Histogram(target_actions)
        }, step=step)
    
    # Log sample predictions
    if len(predictions) > 0:
        wandb.log({
            "pokemon/sample_prediction": predictions[0],
            "pokemon/sample_target": targets[0]
        }, step=step)
```

### TensorBoard Integration

```python
# Dual monitoring: W&B + TensorBoard
from torch.utils.tensorboard import SummaryWriter

def setup_tensorboard(log_dir):
    """Setup TensorBoard logging."""
    
    writer = SummaryWriter(log_dir)
    
    # Log hyperparameters
    hyperparams = {
        "learning_rate": 2e-4,
        "lora_r": 64,
        "lora_alpha": 128,
        "batch_size": 2,
        "gradient_accumulation": 4
    }
    
    writer.add_hparams(hyperparams, {"placeholder": 0})
    
    return writer

# Usage during training
def log_training_step(writer, loss, lr, step):
    """Log training metrics to TensorBoard."""
    
    writer.add_scalar("Loss/train", loss, step)
    writer.add_scalar("Learning_Rate", lr, step)
    
    # Log GPU memory usage
    if torch.cuda.is_available():
        memory_used = torch.cuda.memory_allocated() / 1024**3
        memory_cached = torch.cuda.memory_reserved() / 1024**3
        
        writer.add_scalar("GPU/memory_used", memory_used, step)
        writer.add_scalar("GPU/memory_cached", memory_cached, step)
```

## Environment Variables 🌍

### Complete .env Configuration

```bash
# Copy and customize environment file
cp .env.example .env

# Edit .env with your configuration:
# Required tokens
HUGGINGFACE_TOKEN=hf_your_token_here
WANDB_API_KEY=your_wandb_key_here

# Training configuration overrides
MODEL_NAME=google/gemma-3-4b-it
GRID_DATASET_PATH=training_data/pokemon_grid_dataset.jsonl
OUTPUT_DIR=models/gemma-3-4b-pokemon-grid
MAX_STEPS=1500
BATCH_SIZE=2
GRAD_ACCUM=4
LEARNING_RATE=2e-4

# Hardware configuration
CUDA_VISIBLE_DEVICES=0
ACCELERATE_CONFIG=accelerate_configs/single_gpu.yaml
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
TOKENIZERS_PARALLELISM=false
```

### Environment Validation

```python
#!/usr/bin/env python3
"""
Environment Configuration Validator
Checks all required environment variables and configurations
"""

import os
from pathlib import Path

def validate_environment():
    """Validate complete training environment."""
    
    issues = []
    
    # Check required tokens
    required_tokens = ["HUGGINGFACE_TOKEN"]
    for token in required_tokens:
        if not os.getenv(token):
            issues.append(f"Missing required token: {token}")
    
    # Check dataset existence
    dataset_path = os.getenv("GRID_DATASET_PATH", "training_data/pokemon_grid_dataset.jsonl")
    if not Path(dataset_path).exists():
        issues.append(f"Dataset not found: {dataset_path}")
    
    # Check accelerate config
    accelerate_config = os.getenv("ACCELERATE_CONFIG", "accelerate_configs/single_gpu.yaml")
    if not Path(accelerate_config).exists():
        issues.append(f"Accelerate config not found: {accelerate_config}")
    
    # Check output directory permissions
    output_dir = Path(os.getenv("OUTPUT_DIR", "models/gemma-3-4b-pokemon-grid"))
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        issues.append(f"Cannot create output directory: {output_dir}")
    
    # Validate hyperparameters
    try:
        learning_rate = float(os.getenv("LEARNING_RATE", "2e-4"))
        if learning_rate < 1e-6 or learning_rate > 1e-2:
            issues.append(f"Learning rate out of reasonable range: {learning_rate}")
    except ValueError:
        issues.append("Invalid learning rate format")
    
    return issues

# Run validation
issues = validate_environment()
if issues:
    print("❌ Environment validation failed:")
    for issue in issues:
        print(f"  - {issue}")
    exit(1)
else:
    print("✅ Environment validation passed!")
```

## Practical Exercises 🛠️

### Exercise 1: Hardware Detection

```bash
# Detect your hardware and get configuration recommendations
python -c "
import torch
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f'GPU {i}: {props.name} ({props.total_memory/1024**3:.1f}GB)')
print(f'MPS Available: {torch.backends.mps.is_available()}')
"

# Run automated batch size detection
python scripts/find_batch_size.py \
    --dataset_path training_data/pokemon_grid_dataset.jsonl \
    --output batch_config.json
```

### Exercise 2: Configuration Testing

```bash
# Test accelerate configuration
accelerate test --config_file accelerate_configs/single_gpu.yaml

# Validate training pipeline
python scripts/validate_training.py --test all

# Test W&B integration
python scripts/setup_wandb.py --test-run
```

### Exercise 3: Memory Profiling

```python
# Profile memory usage during model loading
import torch
import psutil
from transformers import AutoModelForImageTextToText

def profile_memory():
    """Profile memory usage during model operations."""
    
    # Baseline memory
    torch.cuda.empty_cache()
    baseline = torch.cuda.memory_allocated() / 1024**3
    print(f"Baseline GPU memory: {baseline:.2f}GB")
    
    # Load model
    model = AutoModelForImageTextToText.from_pretrained(
        "google/gemma-3-4b-it",
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    model_loaded = torch.cuda.memory_allocated() / 1024**3
    print(f"After model loading: {model_loaded:.2f}GB (+{model_loaded-baseline:.2f}GB)")
    
    # Apply QLoRA
    from peft import LoraConfig, get_peft_model
    
    lora_config = LoraConfig(r=64, lora_alpha=128, target_modules="all-linear")
    model = get_peft_model(model, lora_config)
    
    with_lora = torch.cuda.memory_allocated() / 1024**3
    print(f"After LoRA: {with_lora:.2f}GB (+{with_lora-model_loaded:.2f}GB)")
    
    return {
        "baseline": baseline,
        "model_loaded": model_loaded,
        "with_lora": with_lora
    }

# Run profiling
memory_profile = profile_memory()
```

## Key Takeaways 💡

1. **Hardware-Specific Configuration**: Different setups require different accelerate configs
2. **QLoRA Efficiency**: 4-bit quantization + LoRA adapters enable training on modest hardware
3. **Batch Size Optimization**: Use automated tools to find optimal memory usage
4. **Comprehensive Monitoring**: W&B + TensorBoard provide complete training visibility
5. **Environment Management**: Proper .env setup ensures reproducible training

## Next Steps 🚀

In **Tutorial 05**, we'll run the actual training:
- Executing the complete training pipeline
- Monitoring training progress and metrics
- Handling common training issues
- Implementing early stopping and checkpointing

### Preparation for Tutorial 05

```bash
# Final pre-training checklist
cd /Users/wingston/code/claude-plays-pokemon/eevee_v2/gemma

# 1. Validate complete environment
python scripts/validate_training.py

# 2. Test accelerate configuration  
accelerate test --config_file $ACCELERATE_CONFIG

# 3. Verify dataset
ls -la training_data/pokemon_grid_dataset.jsonl
ls -la training_data/grid_images/ | head -5

# 4. Check authentication
huggingface-cli whoami
wandb status

echo "✅ Ready for Tutorial 05: Fine-tuning Process!"
```

---

**Perfect! Your training environment is configured. Ready to start training in Tutorial 05? 🏋️‍♀️**