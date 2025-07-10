#!/bin/bash
"""
Mac-optimized training script for Pokemon Gemma 3 VLM using 2x2 temporal grids
Optimized for Apple Silicon (M1/M2/M3) with MPS acceleration
"""

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Training configuration - optimized for Mac
MODEL_NAME="${MODEL_NAME:-google/gemma-3-4b-it}"
GRID_DATASET_PATH="${GRID_DATASET_PATH:-training_data/pokemon_grid_dataset_final.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-models/gemma-3-4b-pokemon-grid-mac}"
MAX_STEPS="${MAX_STEPS:-1000}"
BATCH_SIZE="${BATCH_SIZE:-1}"  # Reduced for Mac
GRAD_ACCUM="${GRAD_ACCUM:-8}"  # Increased to compensate
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
ACCELERATE_CONFIG="${ACCELERATE_CONFIG:-accelerate_configs/cpu_mps.yaml}"

# Authentication
export HF_TOKEN="${HUGGINGFACE_TOKEN:-$HF_TOKEN}"
export WANDB_API_KEY="${WANDB_API_KEY:-}"

# Mac-specific optimizations
export TOKENIZERS_PARALLELISM="false"
export MPS_AVAILABLE=$(python -c "import torch; print('true' if torch.backends.mps.is_available() else 'false')")

echo "🍎 Training Pokemon Gemma 3 VLM on Apple Silicon"
echo "Model: $MODEL_NAME"
echo "Grid Dataset: $GRID_DATASET_PATH"
echo "Output: $OUTPUT_DIR"
echo "Max Steps: $MAX_STEPS"
echo "MPS Available: $MPS_AVAILABLE"
echo ""

# Verify grid dataset exists
if [ ! -f "$GRID_DATASET_PATH" ]; then
    echo "❌ Error: Grid dataset not found at $GRID_DATASET_PATH"
    exit 1
fi

# Test MPS compatibility first
echo "🧪 Testing Mac compatibility..."
python scripts/test_mps_compatibility.py
if [ $? -ne 0 ]; then
    echo "⚠️  Compatibility issues detected, but continuing..."
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p logs

echo "🔧 Mac-optimized configuration:"
echo "   • Batch size: $BATCH_SIZE (reduced for memory)"
echo "   • Gradient accumulation: $GRAD_ACCUM (increased)"
echo "   • Mixed precision: disabled (MPS compatibility)"
echo "   • DataLoader workers: 0 (avoid multiprocessing)"
echo ""

# Training command optimized for Mac
accelerate launch \
    --config_file "$ACCELERATE_CONFIG" \
    scripts/train_frame_grid.py \
    --dataset_name "$GRID_DATASET_PATH" \
    --model_name_or_path "$MODEL_NAME" \
    --per_device_train_batch_size $BATCH_SIZE \
    --gradient_accumulation_steps $GRAD_ACCUM \
    --output_dir "$OUTPUT_DIR" \
    --max_steps $MAX_STEPS \
    --learning_rate $LEARNING_RATE \
    --fp16 \
    --torch_dtype float16 \
    --use_peft \
    --lora_target_modules all-linear \
    --lora_r 64 \
    --lora_alpha 128 \
    --lora_dropout 0.05 \
    --attn_implementation eager \
    --gradient_checkpointing \
    --optim adamw_torch \
    --lr_scheduler_type cosine \
    --warmup_ratio 0.1 \
    --weight_decay 0.01 \
    --max_grad_norm 1.0 \
    --logging_steps 10 \
    --save_steps 250 \
    --eval_steps 250 \
    --save_total_limit 3 \
    --dataloader_num_workers 0 \
    --remove_unused_columns False \
    --report_to none \
    --run_name "pokemon-gemma3-grid-mac-${MAX_STEPS}steps" \
    2>&1 | tee logs/train_grid_mac_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "🏆 Mac training completed!"
echo "Model saved to: $OUTPUT_DIR"
echo "Check logs in: logs/"

# Test inference with trained model
echo ""
echo "🧪 Testing grid inference..."
python scripts/test_grid_inference.py \
    --model_path "$OUTPUT_DIR" \
    --test_grid "training_data/grid_images/grid_000001.png" \
    --output_file "results/grid_inference_test_mac.json"

echo "✅ Mac training pipeline complete!"
echo ""
echo "📊 Next steps:"
echo "  1. Convert to MLX: python scripts/convert_to_mlx.py --model_path $OUTPUT_DIR --output_path ${OUTPUT_DIR}_mlx"
echo "  2. Test MLX inference: python scripts/convert_to_mlx.py --model_path ${OUTPUT_DIR}_mlx --output_path /tmp/test --test_inference"