#!/usr/bin/env python3
"""
QLoRA Merge Script for Pokemon Gemma VLM
Merges LoRA adapters with base model for deployment
"""

import argparse
import torch
from pathlib import Path
from transformers import AutoModelForImageTextToText, AutoProcessor
from peft import PeftModel
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_qlora_model(base_model_path: str, lora_path: str, output_path: str, 
                     device_map: str = "auto", torch_dtype: str = "bfloat16"):
    """
    Merge LoRA adapters with base model.
    
    Args:
        base_model_path: Path to base Gemma model
        lora_path: Path to trained LoRA adapters
        output_path: Output directory for merged model
        device_map: Device mapping strategy
        torch_dtype: PyTorch data type
    """
    logger.info(f"🔗 Merging LoRA adapters from {lora_path}")
    logger.info(f"📦 Base model: {base_model_path}")
    logger.info(f"💾 Output: {output_path}")
    
    # Parse torch dtype
    dtype_map = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32
    }
    torch_dtype = dtype_map.get(torch_dtype, torch.bfloat16)
    
    # Load base model
    logger.info("Loading base model...")
    base_model = AutoModelForImageTextToText.from_pretrained(
        base_model_path,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=True
    )
    
    # Load LoRA model
    logger.info("Loading LoRA adapters...")
    model = PeftModel.from_pretrained(
        base_model,
        lora_path,
        torch_dtype=torch_dtype
    )
    
    # Merge adapters
    logger.info("Merging LoRA adapters with base model...")
    merged_model = model.merge_and_unload()
    
    # Load processor
    logger.info("Loading processor...")
    processor = AutoProcessor.from_pretrained(base_model_path)
    
    # Create output directory
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save merged model
    logger.info(f"Saving merged model to {output_path}...")
    merged_model.save_pretrained(
        output_path,
        safe_serialization=True,
        max_shard_size="2GB"
    )
    
    # Save processor
    processor.save_pretrained(output_path)
    
    # Save model info
    model_info = {
        "model_type": "pokemon_gemma_vlm",
        "base_model": base_model_path,
        "lora_path": lora_path,
        "torch_dtype": str(torch_dtype),
        "merged_timestamp": str(torch.utils.data.get_worker_info() or "unknown"),
        "parameters": sum(p.numel() for p in merged_model.parameters()),
        "trainable_parameters": sum(p.numel() for p in merged_model.parameters() if p.requires_grad)
    }
    
    with open(output_path / "model_info.json", "w") as f:
        json.dump(model_info, f, indent=2)
    
    logger.info("✅ Model merging completed successfully!")
    logger.info(f"📊 Total parameters: {model_info['parameters']:,}")
    logger.info(f"🔧 Trainable parameters: {model_info['trainable_parameters']:,}")
    
    return str(output_path)


def test_merged_model(model_path: str):
    """Test the merged model with a simple inference."""
    logger.info("🧪 Testing merged model...")
    
    try:
        # Load merged model
        model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        processor = AutoProcessor.from_pretrained(model_path)
        
        # Create test prompt
        messages = [{
            "role": "system",
            "content": [{"type": "text", "text": "You are Ash Ketchum, analyzing Pokemon gameplay."}]
        }, {
            "role": "user", 
            "content": [{"type": "text", "text": "What should I do next in Pokemon?"}]
        }]
        
        # Apply chat template
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = processor(text=text, return_tensors="pt")
        
        # Generate
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=64,
                do_sample=False,
                temperature=0.1
            )
        
        # Decode
        response = processor.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        )
        
        logger.info(f"✅ Test successful! Model response: {response[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapters with base Gemma model")
    parser.add_argument("--base_model", required=True, help="Base model path")
    parser.add_argument("--lora_path", required=True, help="LoRA adapters path")
    parser.add_argument("--output_path", required=True, help="Output directory")
    parser.add_argument("--device_map", default="auto", help="Device mapping")
    parser.add_argument("--torch_dtype", default="bfloat16", help="PyTorch data type")
    parser.add_argument("--test", action="store_true", help="Test merged model")
    
    args = parser.parse_args()
    
    # Merge model
    merged_path = merge_qlora_model(
        args.base_model,
        args.lora_path,
        args.output_path,
        args.device_map,
        args.torch_dtype
    )
    
    # Test if requested
    if args.test:
        test_merged_model(merged_path)
    
    logger.info("🎉 QLoRA merge completed!")


if __name__ == "__main__":
    main()