# Tutorial 05: Fine-tuning Process

## Overview

This tutorial covers the complete fine-tuning process for Pokemon Gemma VLM, from training execution to monitoring and checkpoint management.

## Prerequisites

- Completed Tutorial 04 (Data Preparation)
- Generated dataset: `training_data/pokemon_grid_dataset_final.jsonl` (671 sequences)
- Environment setup completed via `init.sh`

## Training Configuration

### 1. Model Architecture Setup

```python
# Model: google/gemma-3-4b-it (faster training)
# Alternative: google/gemma-3n-9b-it (higher quality)

# QLoRA Configuration
- r (rank): 32-64 (higher rank = more parameters)
- alpha: 16-32 (controls adaptation strength)
- dropout: 0.05-0.1 (regularization)
- target_modules: "all-linear" (comprehensive adaptation)
```

### 2. Training Hyperparameters

```bash
# Key Parameters (from train_grid.sh)
LEARNING_RATE="2e-4"        # Conservative for stability
BATCH_SIZE="1"              # Memory-constrained (can increase with more VRAM)
GRAD_ACCUM="4"              # Effective batch size = 4
MAX_STEPS="2000"            # ~3 epochs over 671 sequences
WARMUP_STEPS="100"          # 5% warmup
SAVE_STEPS="200"            # Regular checkpointing
```

### 3. Memory Optimization

```python
# Optimization Techniques
- bf16 training: Reduced memory, maintained precision
- gradient_checkpointing: Trade compute for memory
- QLoRA: 4-bit quantization with trainable adapters
- dataloader_pin_memory: False (reduce RAM usage)
```

## Training Execution

### 1. Start Training

```bash
# Run the training script
bash train_grid.sh

# Monitor progress
tail -f training_logs/train_$(date +%Y%m%d_%H%M%S).log
```

### 2. Training Script Breakdown

```bash
#!/bin/bash
# train_grid.sh - Complete training pipeline

# Model and data configuration
export MODEL_NAME="google/gemma-3-4b-it"
export DATASET_PATH="training_data/pokemon_grid_dataset_final.jsonl"
export OUTPUT_DIR="models/gemma-3-4b-pokemon-grid-$(date +%Y%m%d_%H%M%S)"

# Training hyperparameters
export LEARNING_RATE="2e-4"
export BATCH_SIZE="1"
export GRAD_ACCUM="4"
export MAX_STEPS="2000"
export WARMUP_STEPS="100"
export SAVE_STEPS="200"

# Launch training with accelerate
accelerate launch --config_file accelerate_configs/single_gpu.yaml \
    scripts/train_frame_grid.py \
    --model_name_or_path "$MODEL_NAME" \
    --dataset_path "$DATASET_PATH" \
    --output_dir "$OUTPUT_DIR" \
    --learning_rate "$LEARNING_RATE" \
    --per_device_train_batch_size "$BATCH_SIZE" \
    --gradient_accumulation_steps "$GRAD_ACCUM" \
    --max_steps "$MAX_STEPS" \
    --warmup_steps "$WARMUP_STEPS" \
    --save_steps "$SAVE_STEPS" \
    --logging_steps 10 \
    --bf16 \
    --dataloader_pin_memory False \
    --gradient_checkpointing \
    --report_to wandb \
    --run_name "pokemon-gemma-grid-$(date +%Y%m%d_%H%M%S)"
```

### 3. Pan & Scan Enhancement

The Gemma 3 processor includes built-in Pan & Scan for enhanced detail extraction:

```python
# Automatically enabled in train_frame_grid.py
def enable_pan_and_scan(processor, max_crops=4, min_crop_size=896, min_ratio=1.2):
    """Enable Pan & Scan for enhanced detail extraction."""
    processor.image_processor.do_pan_and_scan = True
    processor.image_processor.pan_and_scan_max_num_crops = max_crops
    processor.image_processor.pan_and_scan_min_crop_size = min_crop_size
    processor.image_processor.pan_and_scan_min_ratio_to_activate = min_ratio
    print(f"✅ Pan & Scan enabled: max_crops={max_crops}, min_size={min_crop_size}")
```

## Monitoring Training Progress

### 1. Real-time Monitoring

```bash
# Watch training logs
tail -f training_logs/train_*.log

# Monitor GPU usage
watch -n 1 nvidia-smi

# Track memory usage
watch -n 1 'free -h && echo "--- GPU Memory ---" && nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits'
```

### 2. Key Metrics to Watch

```python
# Training Metrics
- train_loss: Should decrease steadily (target: <0.5)
- learning_rate: Should follow warmup schedule
- grad_norm: Should be stable (watch for exploding gradients)
- train_runtime: Track epoch duration

# Memory Metrics
- GPU memory usage: Should be stable (not increasing)
- CPU memory: Monitor for memory leaks
- Disk I/O: Dataset loading efficiency
```

### 3. Wandb Dashboard

Access your training dashboard at: `https://wandb.ai/your-username/pokemon-gemma-vlm`

Key charts to monitor:
- **Loss curves**: Training loss over time
- **Learning rate**: Scheduler progression  
- **GPU utilization**: Hardware efficiency
- **Sample predictions**: Output quality

## Checkpoint Management

### 1. Automatic Checkpointing

```python
# Checkpoints saved every 200 steps to:
# models/gemma-3-4b-pokemon-grid-TIMESTAMP/checkpoint-{step}/

# Checkpoint contents:
- pytorch_model.bin: Model weights
- adapter_config.json: LoRA configuration
- adapter_model.bin: LoRA weights
- tokenizer files: Processor configuration
- training_args.bin: Training state
```

### 2. Manual Checkpoint Creation

```python
# During training, create manual checkpoint
import torch

def save_checkpoint(model, tokenizer, output_dir, step):
    checkpoint_dir = f"{output_dir}/manual_checkpoint_{step}"
    model.save_pretrained(checkpoint_dir)
    tokenizer.save_pretrained(checkpoint_dir)
    print(f"Manual checkpoint saved: {checkpoint_dir}")
```

### 3. Checkpoint Recovery

```bash
# Resume from checkpoint
python scripts/train_frame_grid.py \
    --model_name_or_path models/gemma-3-4b-pokemon-grid-20250709/checkpoint-1000 \
    --resume_from_checkpoint models/gemma-3-4b-pokemon-grid-20250709/checkpoint-1000 \
    [other args...]
```

## Training Validation

### 1. Mid-training Testing

```bash
# Test model at checkpoint-1000
python scripts/test_grid_inference.py \
    --model_path models/gemma-3-4b-pokemon-grid-20250709/checkpoint-1000 \
    --test_grid training_data/grid_images/test_grid_001.png \
    --output_file validation/checkpoint_1000_test.json
```

### 2. Training Metrics Analysis

```python
# Analyze training logs
import json
import matplotlib.pyplot as plt

def plot_training_metrics(log_file):
    with open(log_file) as f:
        logs = [json.loads(line) for line in f if line.strip()]
    
    steps = [log['step'] for log in logs]
    losses = [log['train_loss'] for log in logs]
    
    plt.figure(figsize=(10, 6))
    plt.plot(steps, losses)
    plt.title('Training Loss Over Time')
    plt.xlabel('Training Steps')
    plt.ylabel('Loss')
    plt.grid(True)
    plt.savefig('training_loss_curve.png')
    plt.show()
```

### 3. Early Stopping Criteria

```python
# Monitor for training completion signals
- Loss plateau: No improvement for 500 steps
- Overfitting: Validation loss increasing
- Perfect accuracy: All predictions correct (rare)
- Resource limits: Time/budget constraints
```

## Troubleshooting Common Issues

### 1. Out of Memory Errors

```bash
# Solutions:
- Reduce batch_size from 1 to gradient accumulation only
- Enable gradient_checkpointing
- Reduce max_sequence_length if possible
- Use deepspeed zero stage 2/3

# Emergency memory recovery:
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### 2. Training Instability

```python
# Gradient explosion symptoms:
- Loss suddenly jumps to NaN
- grad_norm becomes very large (>10.0)
- Model outputs become gibberish

# Solutions:
- Reduce learning rate (2e-5 instead of 2e-4)
- Add gradient clipping: max_grad_norm=1.0
- Increase warmup_steps to 200
- Use fp32 instead of bf16 (slower but more stable)
```

### 3. Data Loading Issues

```bash
# Common problems:
- Missing image files
- Corrupted JSONL format
- Incorrect file paths

# Debug dataset loading:
python -c "
from datasets import load_dataset
ds = load_dataset('json', data_files='training_data/pokemon_grid_dataset_final.jsonl')
print('Dataset loaded successfully:', len(ds['train']))
print('Sample:', ds['train'][0])
"
```

### 4. Authentication Errors

```bash
# HuggingFace token issues:
export HF_TOKEN="your_token_here"
huggingface-cli login

# Test model access:
python -c "
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained('google/gemma-3-4b-it')
print('✅ Model access successful')
"
```

## Post-Training Steps

### 1. Final Model Validation

```bash
# Test final model
python scripts/test_grid_inference.py \
    --model_path models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000 \
    --test_grid training_data/grid_images/validation_grid.png \
    --output_file results/final_validation.json
```

### 2. Model Conversion Preparation

```bash
# Prepare for GGUF/MLX conversion
python scripts/merge_adapters.py \
    --base_model google/gemma-3-4b-it \
    --adapter_path models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000 \
    --output_dir models/gemma-3-4b-pokemon-merged
```

### 3. Training Summary

```python
# Generate training report
python scripts/training_summary.py \
    --output_dir models/gemma-3-4b-pokemon-grid-20250709 \
    --wandb_run pokemon-gemma-grid-20250709 \
    --report_file training_summary.json
```

## Next Steps

After successful fine-tuning:

1. **Tutorial 06**: Training Monitoring & Evaluation
2. **Tutorial 07**: Model Evaluation & Testing  
3. **Tutorial 08**: Model Deployment (GGUF/MLX conversion)
4. **Tutorial 09**: Advanced Techniques & Optimization

## Expected Training Timeline

```
Preparation:     ~15 minutes
Training:        ~2-4 hours (depending on hardware)
Validation:      ~15 minutes
Post-processing: ~30 minutes
Total:          ~3-5 hours
```

## Hardware Requirements

```
Minimum:  8GB VRAM, 16GB RAM
Recommended: 12GB+ VRAM, 32GB+ RAM
Optimal: 24GB VRAM, 64GB RAM
```

The fine-tuning process should produce a Pokemon-specialized Gemma model capable of analyzing 2x2 temporal grids and generating appropriate gaming actions in JSON format.