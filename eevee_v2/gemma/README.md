# Pokemon Gemma VLM Training Pipeline

A complete production-ready training pipeline for fine-tuning Google Gemma Vision-Language Models on Pokemon gameplay data using 4-frame temporal sequences.

tl;dr
```
  cd eevee_v2/gemma
  ./init.sh                    # Setup environment
  cp .env.example .env         # Add your tokens
  python scripts/validate_training.py  # Test everything
  ./train_gemma3.sh           # Start training!
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Run the initialization script
./init.sh

# Activate the conda environment
conda activate pokemon-gemma-vlm
```

### 2. Authentication Setup
```bash
# Add your tokens to .env file
cp .env.example .env
# Edit .env with your actual tokens:
# HUGGINGFACE_TOKEN=hf_your_token_here
# WANDB_API_KEY=your_wandb_key_here
```

### 3. Data Conversion
```bash
# Convert Eevee v1 data to 4-frame training format
python scripts/convert_eevee_data_v2.py \
    --eevee_data_dir /path/to/eevee/v1/data \
    --output_dir training_data \
    --min_frames 4
```

### 4. Validation
```bash
# Validate the complete training setup
python scripts/validate_training.py
```

### 5. Find Optimal Batch Size
```bash
# Automatically determine best batch size for your hardware
python scripts/find_batch_size.py \
    --dataset_path training_data/pokemon_4frame_dataset_full.jsonl \
    --use_peft \
    --output batch_size_results.json
```

### 6. Training
```bash
# Train Gemma 3-4B model
./train_gemma3.sh

# Or train Gemma 3n-9B model (requires more VRAM)
./train_gemma3n.sh
```

## 📁 Project Structure

```
eevee_v2/gemma/
├── init.sh                    # Environment setup script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── wandb_config.yaml         # Weights & Biases configuration
│
├── scripts/
│   ├── convert_eevee_data_v2.py    # Data conversion script
│   ├── sft_pokemon_gemma3.py       # Main training script
│   ├── validate_training.py        # Pre-training validation
│   ├── find_batch_size.py          # Automatic batch size finder
│   ├── merge_qlora.py              # Post-training model merger
│   ├── convert_to_gguf.py          # GGUF conversion for inference
│   └── setup_wandb.py              # Weights & Biases setup
│
├── accelerate_configs/
│   ├── single_gpu.yaml             # Single GPU training
│   ├── multi_gpu.yaml              # Multi-GPU training
│   ├── deepspeed_zero3.yaml        # DeepSpeed Zero Stage 3
│   └── cpu_mps.yaml                # CPU/MPS development
│
├── train_gemma3.sh                 # Training script for Gemma 3-4B
└── train_gemma3n.sh                # Training script for Gemma 3n-9B
```

## 🛠️ Advanced Usage

### Custom Training Configuration

All training parameters can be configured via environment variables in `.env`:

```bash
# Model selection
MODEL_NAME=google/gemma-3-4b-it  # or google/gemma-3n-9b-it

# Dataset path
DATASET_PATH=training_data/pokemon_4frame_dataset_full.jsonl

# Training parameters
MAX_STEPS=2000
BATCH_SIZE=2
GRAD_ACCUM=4
LEARNING_RATE=2e-4

# Hardware configuration
CUDA_VISIBLE_DEVICES=0
ACCELERATE_CONFIG=accelerate_configs/single_gpu.yaml
```

### Hyperparameter Sweeps

```bash
# Setup wandb and create sweep
python scripts/setup_wandb.py --create-sweep

# Run sweep agent
wandb agent your-entity/pokemon-gemma-vlm/sweep-id
```

### Model Deployment

```bash
# Merge LoRA adapters with base model
python scripts/merge_qlora.py \
    --base_model google/gemma-3-4b-it \
    --lora_path models/gemma-3-4b-pokemon-4frame \
    --output_path models/gemma-3-4b-pokemon-merged

# Convert to GGUF for efficient inference
python scripts/convert_to_gguf.py \
    --model_path models/gemma-3-4b-pokemon-merged \
    --output_dir models/gguf \
    --quantization f16
```

## 🎯 Training Data Format

The pipeline expects JSONL files with 4-frame temporal sequences:

```json
{
  "frames": ["frame1.png", "frame2.png", "frame3.png", "frame4.png"],
  "context": "🎮 You are ASH KETCHUM navigating Route 1...",
  "question": "What button should be pressed next?",
  "output": "{\"button\": \"right\", \"reasoning\": \"clear_path\", \"context\": \"navigation\"}"
}
```

## 📊 Hardware Requirements

### Minimum Requirements
- **GPU**: 8GB VRAM (RTX 3070, RTX 4060 Ti)
- **RAM**: 16GB system memory
- **Storage**: 50GB free space
- **CUDA**: 11.8 or later

### Recommended Requirements
- **GPU**: 24GB VRAM (RTX 4090, A6000)
- **RAM**: 32GB system memory
- **Storage**: 100GB SSD
- **CUDA**: 12.1 or later

### Supported Platforms
- ✅ NVIDIA CUDA GPUs
- ✅ Apple Silicon (MPS)
- ✅ CPU-only (slow, for development)

## 🔧 Troubleshooting

### Common Issues

**Out of Memory Errors**
```bash
# Use automatic batch size finder
python scripts/find_batch_size.py --dataset_path your_dataset.jsonl

# Or manually reduce batch size and increase gradient accumulation
export BATCH_SIZE=1
export GRAD_ACCUM=8
```

**Authentication Errors**
```bash
# Check HuggingFace token
huggingface-cli whoami

# Re-login if needed
huggingface-cli login
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check TRL installation
python -c "import trl; print(trl.__version__)"
```

### Performance Monitoring

```bash
# Check GPU usage during training
nvidia-smi -l 1

# Monitor training progress
tensorboard --logdir models/gemma-3-4b-pokemon-4frame/logs

# View wandb dashboard
wandb dashboard
```

## 📚 Additional Resources

- [TRL Documentation](https://huggingface.co/docs/trl)
- [Gemma Model Cards](https://huggingface.co/google/gemma-3-4b-it)
- [Pokemon AI Research](../specs/vision.md)
- [Eevee v2 Architecture](../CLAUDE.md)

## 🤝 Contributing

1. Follow the existing code style and documentation patterns
2. Test changes with `python scripts/validate_training.py`
3. Update this README for any new features
4. Ensure compatibility with different hardware configurations

---

**Ready to train your Pokemon AI! 🎮✨**


======

 Critical Issues That Must Be Fixed

  1. TRL Multi-Image Training Bug (BLOCKING)

  - Issue: Known bug #3121 in TRL prevents Gemma 3 multi-image training
  - Error: ValueError: Number of images does not match number of special image tokens
  - Impact: Training will fail completely
  - Fix: Wait for TRL fix or implement custom training loop

  2. GGUF Conversion Won't Work (BLOCKING)

  - Issue: GGUF has experimental/broken support for vision-language models
  - Impact: Deployment pipeline will produce non-functional models
  - Fix: Replace with MLX conversion for Apple Silicon or use standard HF transformers

  3. Memory Configuration Issues (MAJOR)

  - Issue: 32K context + 4 images + batching = guaranteed OOM
  - Impact: Training will crash on most hardware
  - Fix: Reduce to 2K-8K context, batch_size=1, increase grad_accum

  ✅ What Actually Works Well

  1. Data Conversion Pipeline (EXCELLENT)

  - Correctly parses Eevee v1 session structure
  - Handles temporal sequences properly
  - Rich context generation follows successful patterns
  - Will work with real data

  2. Infrastructure Setup (VERY GOOD)

  - Comprehensive init.sh with error handling
  - Proper accelerate configs for different hardware
  - Good security with .env management
  - Cross-platform support

  3. Conceptual Approach (VALIDATED)

  - 4-frame temporal sequences align with gaming AI best practices
  - Gemma 3-4B-IT has proven multi-image capabilities (128K context)
  - Pokemon gaming AI has strong research precedent
  - TRL normally supports this well (when bugs are fixed)

  ⚠️ Medium Priority Issues

  1. Model Selection

  - google/gemma-3n-9b-it doesn't exist
  - Use google/gemma-3-4b-it instead

  2. Integration Testing Gaps

  - No end-to-end pipeline validation
  - Missing production performance tests
  - Limited error recovery scenarios

  🎯 Recommended Action Plan

  Immediate (Block Training)

  1. Fix TRL Bug: Monitor GitHub issue #3121 or implement custom training loop
  2. Reduce Memory: Set context to 8K, batch_size=1, increase grad_accum to 8-16
  3. Fix Model Name: Change to google/gemma-3-4b-it

  Before Production

  1. Replace GGUF: Implement MLX conversion or standard HF deployment
  2. Add Integration Tests: Complete pipeline validation
  3. Performance Testing: Validate <5ms inference requirement

  The Pipeline Will Work After These Fixes

  The core approach is technically sound and well-implemented. The main blockers are known bugs and configuration issues rather than fundamental design
   problems.

  Assessment: 7/10 - Excellent design held back by current TRL limitations and memory configuration issues. Fixable with targeted changes.

> implement custom training loop is possible?

⏺ Yes, implementing a custom training loop is absolutely possible and would bypass the TRL multi-image bug. Let me analyze what this would involve:

  Task(Research custom VLM training loop)
  ⎿  Read 100 lines (ctrl+r to expand)
     Web Search("custom training loop Gemma 3 vision language model PyTorch manual training 2024")
     +2 more tool uses
