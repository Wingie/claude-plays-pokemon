#!/usr/bin/env python3
"""
Grid Inference Test Script for Pokemon Gemma VLM
Tests trained model on 2x2 temporal grid images
"""

import argparse
import json
import torch
from pathlib import Path
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_grid_inference(model_path: str, test_grid: str, output_file: str = None):
    """
    Test inference on a 2x2 temporal grid image.
    
    Args:
        model_path: Path to trained model
        test_grid: Path to test grid image
        output_file: Optional output file for results
    """
    
    logger.info(f"🧪 Testing grid inference")
    logger.info(f"📦 Model: {model_path}")
    logger.info(f"🖼️ Test Grid: {test_grid}")
    
    # Load model and processor
    try:
        model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        processor = AutoProcessor.from_pretrained(model_path)
        logger.info("✅ Model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        return
    
    # Load test grid image
    try:
        grid_image = Image.open(test_grid).convert("RGB")
        logger.info(f"✅ Grid image loaded: {grid_image.size}")
    except Exception as e:
        logger.error(f"❌ Failed to load grid image: {e}")
        return
    
    # Create test conversation
    test_messages = [
        {
            "role": "system", 
            "content": [{
                "type": "text", 
                "text": """You are Ash Ketchum analyzing a Pokemon gameplay sequence.

You receive a 2x2 SPATIAL GRID showing 4 consecutive game frames:
┌─────────┬─────────┐
│ Frame 1 │ Frame 2 │  ← Top row: earlier moments
│ (t=0)   │ (t=1)   │
├─────────┼─────────┤
│ Frame 3 │ Frame 4 │  ← Bottom row: later moments  
│ (t=2)   │ (t=3)   │
└─────────┴─────────┘

Analyze the temporal progression across the grid and determine the optimal action."""
            }]
        },
        {
            "role": "user",
            "content": [
                {"type": "image", "image": grid_image},
                {"type": "text", "text": "Looking at this 2x2 temporal grid, what button should be pressed next? Analyze the progression from top-left → top-right → bottom-left → bottom-right."}
            ]
        }
    ]
    
    # Apply chat template
    try:
        text = processor.apply_chat_template(
            test_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        logger.info("✅ Chat template applied")
    except Exception as e:
        logger.error(f"❌ Chat template failed: {e}")
        return
    
    # Tokenize and prepare inputs
    try:
        inputs = processor(
            text=[text],
            images=[[grid_image]],
            return_tensors="pt",
            padding=True
        )
        
        # Move to device
        for key in inputs:
            if isinstance(inputs[key], torch.Tensor):
                inputs[key] = inputs[key].to(model.device)
        
        logger.info("✅ Inputs prepared")
    except Exception as e:
        logger.error(f"❌ Input preparation failed: {e}")
        return
    
    # Generate response
    try:
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )
        
        # Decode response
        response = processor.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        )
        
        logger.info("✅ Generation successful")
        logger.info(f"🎯 Response: {response}")
        
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        return
    
    # Parse JSON response if possible
    parsed_response = None
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed_response = json.loads(json_match.group())
            logger.info(f"✅ Parsed JSON: {parsed_response}")
    except:
        logger.warning("⚠️ Could not parse JSON from response")
    
    # Create results
    results = {
        "model_path": str(model_path),
        "test_grid": str(test_grid),
        "grid_size": grid_image.size,
        "raw_response": response,
        "parsed_response": parsed_response,
        "success": parsed_response is not None,
        "timestamp": torch.utils.data.get_worker_info() or "unknown"
    }
    
    # Save results if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Results saved to: {output_path}")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("🎯 GRID INFERENCE TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"Model: {Path(model_path).name}")
    logger.info(f"Grid: {Path(test_grid).name}")
    logger.info(f"Response Length: {len(response)} chars")
    logger.info(f"JSON Parsed: {'✅ Yes' if parsed_response else '❌ No'}")
    
    if parsed_response:
        logger.info("📊 Parsed Action:")
        for key, value in parsed_response.items():
            logger.info(f"  {key}: {value}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test Pokemon Gemma VLM on grid images")
    parser.add_argument("--model_path", required=True, help="Path to trained model")
    parser.add_argument("--test_grid", required=True, help="Path to test grid image")
    parser.add_argument("--output_file", help="Output JSON file for results")
    
    args = parser.parse_args()
    
    # Run test
    try:
        results = test_grid_inference(args.model_path, args.test_grid, args.output_file)
        if results and results["success"]:
            logger.info("🎉 Grid inference test successful!")
        else:
            logger.warning("⚠️ Grid inference test completed with issues")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()