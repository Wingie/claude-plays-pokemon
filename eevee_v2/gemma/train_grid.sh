#!/bin/bash
"""
Training script for Pokemon Gemma 3 VLM using 2x2 temporal grids
Bypasses TRL multi-image bug by using single grid images
"""

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Training configuration - can be overridden with environment variables
MODEL_NAME="${MODEL_NAME:-google/gemma-3-4b-it}"
GRID_DATASET_PATH="${GRID_DATASET_PATH:-training_data/pokemon_grid_dataset_final.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-models/gemma-3-4b-pokemon-grid}"
MAX_STEPS="${MAX_STEPS:-2000}"
BATCH_SIZE="${BATCH_SIZE:-2}"
GRAD_ACCUM="${GRAD_ACCUM:-4}"
LEARNING_RATE="${LEARNING_RATE:-2e-4}"
ACCELERATE_CONFIG="${ACCELERATE_CONFIG:-accelerate_configs/single_gpu.yaml}"

# Authentication
export HF_TOKEN="${HUGGINGFACE_TOKEN:-$HF_TOKEN}"
export WANDB_API_KEY="${WANDB_API_KEY:-}"

# Memory optimization settings
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-max_split_size_mb:512}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

echo "🎮 Training Pokemon Gemma 3 VLM with 2x2 Temporal Grids"
echo "Model: $MODEL_NAME"
echo "Grid Dataset: $GRID_DATASET_PATH"
echo "Output: $OUTPUT_DIR"
echo "Max Steps: $MAX_STEPS"
echo "Approach: Single-image grid training (bypasses TRL multi-image bug)"
echo ""

# Verify grid dataset exists
if [ ! -f "$GRID_DATASET_PATH" ]; then
    echo "❌ Error: Grid dataset not found at $GRID_DATASET_PATH"
    echo "Run the following to create grid dataset:"
    echo "  python scripts/convert_eevee_data_v2.py --eevee_runs_dir /path/to/eevee/runs --output_file training_data/pokemon_grid_dataset_final.jsonl --create_grids --copy_images"
    echo "  Then use: GRID_DATASET_PATH=training_data/pokemon_grid_dataset_final.jsonl $0"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p logs

echo "🔧 Using single-image grid approach:"
echo "   ┌─────────┬─────────┐"
echo "   │ Frame 1 │ Frame 2 │  ← Temporal progression"
echo "   │ (t=0)   │ (t=1)   │"
echo "   ├─────────┼─────────┤"
echo "   │ Frame 3 │ Frame 4 │"
echo "   │ (t=2)   │ (t=3)   │"
echo "   └─────────┴─────────┘"
echo ""

# Training command optimized for grid-based temporal learning
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
    --bf16 \
    --torch_dtype bfloat16 \
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
    --report_to wandb \
    --run_name "pokemon-gemma3-grid-final-671seqs" \
    2>&1 | tee logs/train_grid_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "🏆 Grid training completed!"
echo "Model saved to: $OUTPUT_DIR"
echo "Check logs in: logs/"

# Test inference with trained model
echo ""
echo "🧪 Testing grid inference..."
python scripts/test_grid_inference.py \
    --model_path "$OUTPUT_DIR" \
    --test_grid "training_data/grid_images/grid_000001.png" \
    --output_file "results/grid_inference_test.json"

echo "✅ Gemma 3 grid training pipeline complete!"
echo ""
echo "📊 Next steps:"
echo "  1. Merge LoRA: python scripts/merge_qlora.py --base_model $MODEL_NAME --lora_path $OUTPUT_DIR --output_path models/merged"
echo "  2. Convert for deployment: python scripts/convert_to_gguf.py --model_path models/merged --output_dir models/gguf"
echo "  3. Test performance: python scripts/benchmark_grid_model.py --model_path models/merged"