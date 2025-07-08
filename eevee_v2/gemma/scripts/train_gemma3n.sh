#!/bin/bash
"""
Training script for Google Gemma 3n-9B VLM on Pokemon 4-frame sequences
Optimized for 32K context with QLoRA fine-tuning
"""

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Training configuration - can be overridden with environment variables
MODEL_NAME="${MODEL_NAME:-google/gemma-3n-9b-it}"
DATASET_PATH="${DATASET_PATH:-training_data/pokemon_4frame_dataset_full.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-models/gemma-3n-9b-pokemon-4frame}"
MAX_STEPS="${MAX_STEPS:-2000}"
BATCH_SIZE="${BATCH_SIZE:-1}"
GRAD_ACCUM="${GRAD_ACCUM:-8}"
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
ACCELERATE_CONFIG="${ACCELERATE_CONFIG:-accelerate_configs/deepspeed_zero3.yaml}"

# Authentication
export HF_TOKEN="${HUGGINGFACE_TOKEN:-$HF_TOKEN}"
export WANDB_API_KEY="${WANDB_API_KEY:-}"

# Memory optimization settings
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-max_split_size_mb:512}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

echo "🎮 Training Pokemon Gemma 3n-9B VLM"
echo "Model: $MODEL_NAME"
echo "Dataset: $DATASET_PATH"
echo "Output: $OUTPUT_DIR"
echo "Max Steps: $MAX_STEPS"
echo ""

# Verify dataset exists
if [ ! -f "$DATASET_PATH" ]; then
    echo "❌ Error: Dataset not found at $DATASET_PATH"
    echo "Run convert_eevee_data.py first to generate training data"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p logs

# Training command with optimized settings for Pokemon gameplay
accelerate launch \
    --config_file "$ACCELERATE_CONFIG" \
    scripts/sft_pokemon_gemma3.py \
    --dataset_name "$DATASET_PATH" \
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
    --run_name "pokemon-gemma3n-9b-4frame" \
    2>&1 | tee logs/train_gemma3n_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "🏆 Training completed!"
echo "Model saved to: $OUTPUT_DIR"
echo "Check logs in: logs/"

# Test inference with trained model
echo ""
echo "🧪 Testing inference..."
python scripts/test_inference.py \
    --model_path "$OUTPUT_DIR" \
    --test_images "training_data/images/seq_000000_frame_*.png" \
    --output_file "results/gemma3n_inference_test.json"

echo "✅ Gemma 3n training pipeline complete!"