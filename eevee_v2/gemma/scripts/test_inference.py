#!/usr/bin/env python3
"""
Test inference script for trained Pokemon Gemma VLM models.
Tests 4-frame sequence processing and JSON output generation.
"""

import argparse
import json
import glob
from pathlib import Path
from typing import List

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor


def load_model_and_processor(model_path: str):
    """Load trained model and processor."""
    print(f"Loading model from {model_path}...")
    
    processor = AutoProcessor.from_pretrained(model_path)
    model = AutoModelForImageTextToText.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    return model, processor


def load_4frame_sequence(image_pattern: str) -> List[Image.Image]:
    """Load 4-frame sequence from image pattern."""
    image_paths = sorted(glob.glob(image_pattern))[:4]
    
    if len(image_paths) != 4:
        print(f"Warning: Expected 4 frames, found {len(image_paths)}")
        # Pad or truncate to 4 frames
        while len(image_paths) < 4:
            image_paths.append(image_paths[-1] if image_paths else "placeholder.png")
        image_paths = image_paths[:4]
    
    images = []
    for path in image_paths:
        try:
            img = Image.open(path).convert("RGB")
            images.append(img)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            # Use black placeholder
            images.append(Image.new("RGB", (240, 160), "black"))
    
    return images


def create_test_prompt() -> List[dict]:
    """Create test prompt in the expected message format."""
    system_prompt = """You are Ash Ketchum, a Pokemon trainer. You receive 4 consecutive game frames showing temporal progression.

Analyze the 4-frame sequence to understand:
- Current game state and scene type
- Character position and movement  
- Interactive elements (NPCs, items, Pokemon)
- Optimal next action for progression

Respond with JSON: {"button": "action", "reasoning": "brief_explanation", "context": "scene_type", "scene_description": "detailed_scene"}

Valid buttons: up, down, left, right, a, b, start, select
Valid contexts: navigation, battle, menu, dialogue, shop"""

    return [
        {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
        {"role": "user", "content": []},  # Images will be added here
    ]


def test_inference(model, processor, images: List[Image.Image]) -> str:
    """Run inference on 4-frame sequence."""
    # Create message with images
    messages = create_test_prompt()
    
    # Add images to user message
    for img in images:
        messages[1]["content"].append({"type": "image", "image": img})
    
    # Add question text
    messages[1]["content"].append({
        "type": "text", 
        "text": "Analyze the 4-frame sequence and determine the optimal next action."
    })
    
    # Apply chat template
    text = processor.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Process inputs
    inputs = processor(
        text=text,
        images=images,
        return_tensors="pt",
        padding=True
    )
    
    # Move to device
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Generate response
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            temperature=0.1,
            pad_token_id=processor.tokenizer.eos_token_id
        )
    
    # Decode response
    response = processor.tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:], 
        skip_special_tokens=True
    )
    
    return response.strip()


def main():
    parser = argparse.ArgumentParser(description="Test Pokemon Gemma VLM inference")
    parser.add_argument("--model_path", required=True, help="Path to trained model")
    parser.add_argument("--test_images", required=True, help="Image pattern for 4-frame sequence")
    parser.add_argument("--output_file", help="Output JSON file for results")
    
    args = parser.parse_args()
    
    # Load model
    model, processor = load_model_and_processor(args.model_path)
    
    # Load test images
    print(f"Loading test images: {args.test_images}")
    images = load_4frame_sequence(args.test_images)
    print(f"Loaded {len(images)} frames")
    
    # Run inference
    print("Running inference...")
    response = test_inference(model, processor, images)
    
    print(f"Model response: {response}")
    
    # Try to parse as JSON
    try:
        parsed_response = json.loads(response)
        print("✅ Valid JSON response!")
        print(f"Button: {parsed_response.get('button', 'N/A')}")
        print(f"Reasoning: {parsed_response.get('reasoning', 'N/A')}")
        print(f"Context: {parsed_response.get('context', 'N/A')}")
        print(f"Scene: {parsed_response.get('scene_description', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        parsed_response = {"raw_response": response, "error": str(e)}
    
    # Save results
    if args.output_file:
        results = {
            "model_path": args.model_path,
            "test_images": args.test_images,
            "raw_response": response,
            "parsed_response": parsed_response,
            "images_loaded": len(images)
        }
        
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {args.output_file}")


if __name__ == "__main__":
    main()