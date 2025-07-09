#!/usr/bin/env python3
"""
Pokemon Gemma-3 Grid Training Script
Single-image training using 2x2 temporal grids to bypass TRL multi-image bug

This script trains on spatial grids containing temporal information:
┌─────────┬─────────┐
│ Frame 1 │ Frame 2 │  
│ (t=0)   │ (t=1)   │
├─────────┼─────────┤
│ Frame 3 │ Frame 4 │
│ (t=2)   │ (t=3)   │
└─────────┴─────────┘

Usage:
accelerate launch \
    --config_file accelerate_configs/single_gpu.yaml \
    scripts/train_frame_grid.py \
    --dataset_name pokemon_grid_dataset \
    --model_name_or_path google/gemma-3-4b-it \
    --per_device_train_batch_size 2 \
    --gradient_accumulation_steps 4 \
    --output_dir gemma-3-4b-pokemon-grid \
    --bf16 \
    --use_peft \
    --max_steps 1500 \
    --learning_rate 2e-4
"""

import io
import os
import json
from pathlib import Path
from typing import Dict, List, Any

import torch
from datasets import Dataset, load_dataset
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

from trl import (
    ModelConfig,
    ScriptArguments,
    SFTConfig,
    SFTTrainer,
    TrlParser,
    get_kbit_device_map,
    get_peft_config,
    get_quantization_config,
)


def process_grid_vision_info(messages: List[Dict]) -> List[Image.Image]:
    """
    Extract grid images from messages.
    Expected format: Single 2x2 grid image per sample.
    """
    image_inputs = []
    
    for msg in messages:
        content = msg.get("content", [])
        if not isinstance(content, list):
            content = [content]

        for element in content:
            if isinstance(element, dict) and (element.get("type") == "image" or "image" in element):
                if "image" in element:
                    image = element["image"]
                else:
                    image = element
                    
                if image is not None:
                    # Handle both PIL images and file paths
                    if isinstance(image, str):
                        # File path to grid image
                        try:
                            with open(image, "rb") as f:
                                img_bytes = f.read()
                            image = Image.open(io.BytesIO(img_bytes))
                        except Exception as e:
                            print(f"Error loading grid image from path {image}: {e}")
                            continue
                    elif hasattr(image, "convert"):
                        # Already PIL image
                        pass
                    elif isinstance(image, dict) and "bytes" in image:
                        # Bytes format
                        image = Image.open(io.BytesIO(image["bytes"]))
                    else:
                        print(f"Unsupported image format: {type(image)}")
                        continue
                        
                    image_inputs.append(image.convert("RGB"))
    
    # Validate we have exactly 1 grid image per sample
    if len(image_inputs) != 1:
        print(f"Warning: Expected 1 grid image, got {len(image_inputs)}. Using first or creating placeholder.")
        if len(image_inputs) == 0:
            # Create placeholder grid if no image found
            placeholder = Image.new("RGB", (480, 320), "black")
            image_inputs = [placeholder]
        else:
            # Use first image only
            image_inputs = [image_inputs[0]]
    
    return image_inputs


def format_grid_data(samples: Dict[str, Any]) -> Dict[str, List]:
    """
    Format Pokemon grid training data for single-image sequences.
    
    Expected input format:
    {
        "image": ["grid_000001.png", ...],
        "context": ["Enhanced context with grid explanation", ...],
        "question": ["What button should be pressed next?", ...],
        "output": ['{"button": "right", "reasoning": "clear_path", "context": "navigation"}', ...]
    }
    """
    formatted_samples = {"messages": []}
    
    for i in range(len(samples["image"])):
        # Single grid image
        grid_image = {"type": "image", "image": samples["image"][i]}
        
        # Enhanced system prompt for grid understanding
        system_prompt = f"""You are Ash Ketchum, a Pokemon trainer analyzing a temporal sequence grid.

You receive a 2x2 SPATIAL GRID showing 4 consecutive game frames:
┌─────────┬─────────┐
│ Frame 1 │ Frame 2 │  ← Top row: earlier moments
│ (t=0)   │ (t=1)   │
├─────────┼─────────┤
│ Frame 3 │ Frame 4 │  ← Bottom row: later moments  
│ (t=2)   │ (t=3)   │
└─────────┴─────────┘

ANALYSIS APPROACH:
1. Read temporally: TOP-LEFT → TOP-RIGHT → BOTTOM-LEFT → BOTTOM-RIGHT
2. Track movement: Compare character positions across frames
3. Identify changes: Note environmental and UI state evolution
4. Predict action: Consider the temporal progression shown

{samples["context"][i]}

Respond with JSON: {{"button": "action", "reasoning": "brief_explanation", "context": "scene_type", "scene_description": "detailed_scene", "temporal_analysis": "progression_observed"}}

Valid buttons: up, down, left, right, a, b, start, select
Valid contexts: navigation, battle, menu, dialogue, shop"""

        formatted_samples["messages"].append([
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [grid_image, {"type": "text", "text": samples["question"][i]}]},
            {"role": "assistant", "content": [{"type": "text", "text": samples["output"][i]}]},
        ])
    
    return formatted_samples


def load_grid_dataset(dataset_path: str) -> Dataset:
    """Load Pokemon grid dataset from JSONL file."""
    if dataset_path.endswith('.jsonl'):
        # Load from JSONL file
        data = []
        with open(dataset_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        
        # Convert to expected format
        images = [item["image"] for item in data]
        context = [item["context"] for item in data]
        question = [item["question"] for item in data]
        output = [item["output"] for item in data]
        
        dataset_dict = {
            "image": images,
            "context": context, 
            "question": question,
            "output": output
        }
        
        dataset = Dataset.from_dict(dataset_dict)
        dataset = dataset.map(format_grid_data, batched=True, batch_size=4, num_proc=1)
        
    else:
        # Load from HuggingFace dataset
        dataset = load_dataset(dataset_path)
        dataset = dataset.map(format_grid_data, batched=True, batch_size=4, num_proc=4)
    
    return dataset


def enable_pan_and_scan(processor, max_crops=4, min_crop_size=896, min_ratio=1.2):
    """
    Enable Pan & Scan algorithm for enhanced detail extraction.
    
    Args:
        processor: The Gemma 3 image processor
        max_crops: Maximum number of crops per image
        min_crop_size: Minimum size of each crop
        min_ratio: Minimum aspect ratio to activate pan and scan
    """
    if hasattr(processor, 'image_processor'):
        processor.image_processor.do_pan_and_scan = True
        processor.image_processor.pan_and_scan_max_num_crops = max_crops
        processor.image_processor.pan_and_scan_min_crop_size = min_crop_size
        processor.image_processor.pan_and_scan_min_ratio_to_activate = min_ratio
        
        print(f"✅ Pan & Scan enabled:")
        print(f"   Max crops: {max_crops}")
        print(f"   Min crop size: {min_crop_size}x{min_crop_size}")
        print(f"   Min ratio to activate: {min_ratio}")
    else:
        print("⚠️  Warning: No image processor found, Pan & Scan not enabled")


def main():
    parser = TrlParser((ScriptArguments, SFTConfig, ModelConfig))
    script_args, training_args, model_args = parser.parse_args_and_config()
    
    # Training configuration for Pokemon grid gameplay
    training_args.gradient_checkpointing_kwargs = dict(use_reentrant=False)
    training_args.remove_unused_columns = False
    training_args.dataset_kwargs = {"skip_prepare_dataset": True}
    training_args.dataloader_num_workers = 0  # Avoid multiprocessing issues with images

    ################
    # Model, Tokenizer & Processor
    ################
    torch_dtype = (
        model_args.torch_dtype if model_args.torch_dtype in ["auto", None] 
        else getattr(torch, model_args.torch_dtype)
    )
    quantization_config = get_quantization_config(model_args)
    model_kwargs = dict(
        revision=model_args.model_revision,
        attn_implementation=model_args.attn_implementation,
        torch_dtype=torch_dtype,
        device_map=get_kbit_device_map() if quantization_config is not None else None,
        quantization_config=quantization_config,
    )
    
    processor = AutoProcessor.from_pretrained(
        model_args.model_name_or_path, 
        trust_remote_code=model_args.trust_remote_code
    )
    processor.tokenizer.padding_side = "right"
    
    # Enable Pan & Scan for enhanced detail extraction
    enable_pan_and_scan(processor, max_crops=4, min_crop_size=896, min_ratio=1.2)

    model = AutoModelForImageTextToText.from_pretrained(
        model_args.model_name_or_path, 
        trust_remote_code=model_args.trust_remote_code, 
        **model_kwargs
    )

    def grid_collate_fn(examples):
        """Grid-specific collate function for single-image training."""
        texts = [
            processor.apply_chat_template(
                example["messages"], 
                tokenize=False, 
                add_generation_prompt=False
            ).strip()
            for example in examples
        ]
        
        # Process single grid images per example
        images = [process_grid_vision_info(example["messages"]) for example in examples]
        
        # Tokenize texts and process images
        batch = processor(
            text=texts, 
            images=images, 
            return_tensors="pt", 
            padding=True,
            max_length=8192,  # Reduced from 32K for better memory usage
            truncation=True
        )

        # Setup labels for training
        labels = batch["input_ids"].clone()
        
        # Mask special tokens
        image_token_id = processor.tokenizer.convert_tokens_to_ids(
            processor.tokenizer.special_tokens_map.get("boi_token", "<image>")
        )
        
        labels[labels == processor.tokenizer.pad_token_id] = -100
        if image_token_id:
            labels[labels == image_token_id] = -100
        labels[labels == 262144] = -100  # Additional special token masking

        batch["labels"] = labels
        return batch

    ################
    # Dataset
    ################
    if script_args.dataset_name.endswith('.jsonl'):
        # Local JSONL file
        dataset = load_grid_dataset(script_args.dataset_name)
        train_dataset = dataset
        eval_dataset = None
    else:
        # HuggingFace dataset
        dataset = load_dataset(script_args.dataset_name, name=script_args.dataset_config)
        train_dataset = dataset[script_args.dataset_train_split]
        eval_dataset = dataset.get(script_args.dataset_test_split)

    ################
    # Training
    ################
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        data_collator=grid_collate_fn,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset if training_args.eval_strategy != "no" else None,
        processing_class=processor.tokenizer,
        peft_config=get_peft_config(model_args),
    )

    # Train the model
    trainer.train()

    # Save model and processor
    trainer.save_model(training_args.output_dir)
    if training_args.push_to_hub:
        trainer.push_to_hub(dataset_name=script_args.dataset_name)
        if trainer.accelerator.is_main_process:
            processor.push_to_hub(training_args.hub_model_id)

    print(f"Grid training completed! Model saved to {training_args.output_dir}")


if __name__ == "__main__":
    main()