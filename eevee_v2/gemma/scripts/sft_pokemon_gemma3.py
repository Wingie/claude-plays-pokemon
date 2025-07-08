#!/usr/bin/env python3
"""
Pokemon Gemma-3 VLM Training Script
Adapted from TRL's multi-image implementation for 4-frame temporal sequences

Usage:
accelerate launch \
    --config_file examples/accelerate_configs/deepspeed_zero3.yaml \
    scripts/sft_pokemon_gemma3.py \
    --dataset_name pokemon_4frame_dataset \
    --model_name_or_path google/gemma-3-4b-it \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 4 \
    --output_dir gemma-3-4b-pokemon-4frame \
    --bf16 \
    --torch_dtype bfloat16 \
    --use_peft \
    --lora_target_modules all-linear \
    --attn_implementation eager \
    --max_steps 1000 \
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


def process_pokemon_vision_info(messages: List[Dict]) -> List[Image.Image]:
    """
    Extract 4-frame Pokemon sequences from messages.
    Expected format: 4 consecutive frames for temporal understanding.
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
                        # File path
                        try:
                            with open(image, "rb") as f:
                                img_bytes = f.read()
                            image = Image.open(io.BytesIO(img_bytes))
                        except Exception as e:
                            print(f"Error loading image from path {image}: {e}")
                            continue
                    elif hasattr(image, "convert"):
                        # Already PIL image
                        pass
                    elif isinstance(image, dict) and "bytes" in image:
                        # Bytes format from TRL example
                        image = Image.open(io.BytesIO(image["bytes"]))
                    else:
                        print(f"Unsupported image format: {type(image)}")
                        continue
                        
                    image_inputs.append(image.convert("RGB"))
    
    # Validate we have exactly 4 frames for Pokemon temporal sequences
    if len(image_inputs) != 4:
        print(f"Warning: Expected 4 frames, got {len(image_inputs)}. Padding/truncating.")
        if len(image_inputs) < 4:
            # Duplicate last frame if not enough
            while len(image_inputs) < 4:
                image_inputs.append(image_inputs[-1] if image_inputs else Image.new("RGB", (240, 160), "black"))
        else:
            # Take first 4 frames if too many
            image_inputs = image_inputs[:4]
    
    return image_inputs


def format_pokemon_data(samples: Dict[str, Any]) -> Dict[str, List]:
    """
    Format Pokemon training data for 4-frame sequences.
    
    Expected input format:
    {
        "frames": [["frame1.png", "frame2.png", "frame3.png", "frame4.png"], ...],
        "context": ["Ash navigating Route 1 with Pikachu", ...],
        "question": ["What button should be pressed next?", ...],
        "output": ['{"button": "right", "reasoning": "clear_path", "context": "navigation", "scene_description": "overworld"}', ...]
    }
    """
    formatted_samples = {"messages": []}
    
    for i in range(len(samples["frames"])):
        # Prepare 4-frame image sequence
        images = []
        for frame_path in samples["frames"][i]:
            images.append({"type": "image", "image": frame_path})
        
        # Create rich context prompt for 32K token utilization
        system_prompt = f"""You are Ash Ketchum, a Pokemon trainer. You receive 4 consecutive game frames showing temporal progression. 

Context: {samples["context"][i]}

Analyze the 4-frame sequence to understand:
- Current game state and scene type
- Character position and movement
- Interactive elements (NPCs, items, Pokemon)
- Optimal next action for progression

Respond with JSON: {{"button": "action", "reasoning": "brief_explanation", "context": "scene_type", "scene_description": "detailed_scene"}}

Valid buttons: up, down, left, right, a, b, start, select
Valid contexts: navigation, battle, menu, dialogue, shop"""

        formatted_samples["messages"].append([
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": images + [{"type": "text", "text": samples["question"][i]}]},
            {"role": "assistant", "content": [{"type": "text", "text": samples["output"][i]}]},
        ])
    
    return formatted_samples


def load_pokemon_dataset(dataset_path: str) -> Dataset:
    """Load Pokemon 4-frame dataset from JSONL file."""
    if dataset_path.endswith('.jsonl'):
        # Load from JSONL file
        data = []
        with open(dataset_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        
        # Convert to expected format
        frames = [item["frames"] for item in data]
        context = [item["context"] for item in data]
        question = [item["question"] for item in data]
        output = [item["output"] for item in data]
        
        dataset_dict = {
            "frames": frames,
            "context": context, 
            "question": question,
            "output": output
        }
        
        dataset = Dataset.from_dict(dataset_dict)
        dataset = dataset.map(format_pokemon_data, batched=True, batch_size=4, num_proc=1)
        
    else:
        # Load from HuggingFace dataset
        dataset = load_dataset(dataset_path)
        dataset = dataset.map(format_pokemon_data, batched=True, batch_size=4, num_proc=4)
    
    return dataset


def main():
    parser = TrlParser((ScriptArguments, SFTConfig, ModelConfig))
    script_args, training_args, model_args = parser.parse_args_and_config()
    
    # Training configuration for Pokemon gameplay
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

    model = AutoModelForImageTextToText.from_pretrained(
        model_args.model_name_or_path, 
        trust_remote_code=model_args.trust_remote_code, 
        **model_kwargs
    )

    def pokemon_collate_fn(examples):
        """Pokemon-specific collate function for 4-frame sequences."""
        texts = [
            processor.apply_chat_template(
                example["messages"], 
                tokenize=False, 
                add_generation_prompt=False
            ).strip()
            for example in examples
        ]
        
        # Process 4-frame Pokemon sequences
        images = [process_pokemon_vision_info(example["messages"]) for example in examples]
        
        # Tokenize texts and process images
        batch = processor(
            text=texts, 
            images=images, 
            return_tensors="pt", 
            padding=True,
            max_length=32768,  # Use full 32K context for rich Pokemon state
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
        dataset = load_pokemon_dataset(script_args.dataset_name)
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
        data_collator=pokemon_collate_fn,
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

    print(f"Training completed! Model saved to {training_args.output_dir}")


if __name__ == "__main__":
    main()