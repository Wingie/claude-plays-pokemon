#!/usr/bin/env python3
"""
Automatic Batch Size Finder for Pokemon Gemma VLM Training
Determines optimal batch size based on available GPU memory
"""

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Dict, Tuple, Optional

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import psutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchSizeFinder:
    """Automatically find optimal batch size for training."""
    
    def __init__(self, model_name: str, dataset_path: str, use_peft: bool = True):
        self.model_name = model_name
        self.dataset_path = dataset_path
        self.use_peft = use_peft
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model and processor
        self.processor = None
        self.model = None
        self.sample_data = None
        
    def get_system_info(self) -> Dict:
        """Get system information for batch size calculation."""
        info = {
            "cpu_count": psutil.cpu_count(),
            "ram_gb": psutil.virtual_memory().total / (1024**3),
            "platform": "unknown"
        }
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpus = []
            total_vram = 0
            
            for i in range(gpu_count):
                props = torch.cuda.get_device_properties(i)
                vram_gb = props.total_memory / (1024**3)
                total_vram += vram_gb
                
                gpus.append({
                    "id": i,
                    "name": props.name,
                    "vram_gb": vram_gb,
                    "compute_capability": f"{props.major}.{props.minor}"
                })
            
            info.update({
                "platform": "cuda",
                "gpu_count": gpu_count,
                "gpus": gpus,
                "total_vram_gb": total_vram
            })
            
        elif torch.backends.mps.is_available():
            # Apple Silicon MPS
            info.update({
                "platform": "mps",
                "unified_memory": True
            })
            
        return info
    
    def load_sample_data(self) -> Dict:
        """Load sample data for memory testing."""
        if not Path(self.dataset_path).exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        # Load one sample from JSONL
        with open(self.dataset_path, 'r') as f:
            first_line = f.readline().strip()
            sample = json.loads(first_line)
        
        # Create dummy images if files don't exist
        dummy_images = []
        for i in range(4):  # 4-frame sequences
            # Create 240x160 RGB image (Game Boy Advance resolution)
            dummy_img = Image.new("RGB", (240, 160), color=(i*60, 100, 200))
            dummy_images.append(dummy_img)
        
        return {
            "frames": dummy_images,
            "context": sample["context"],
            "question": sample["question"], 
            "output": sample["output"]
        }
    
    def load_model(self) -> None:
        """Load model and processor."""
        logger.info(f"📦 Loading model: {self.model_name}")
        
        self.processor = AutoProcessor.from_pretrained(self.model_name)
        self.processor.tokenizer.padding_side = "right"
        
        # Load model with minimal memory usage
        model_kwargs = {
            "torch_dtype": torch.bfloat16,
            "device_map": "auto" if torch.cuda.is_available() else None,
            "low_cpu_mem_usage": True
        }
        
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_name,
            **model_kwargs
        )
        
        # Setup PEFT if requested
        if self.use_peft:
            from peft import LoraConfig, get_peft_model
            
            lora_config = LoraConfig(
                r=64,
                lora_alpha=128,
                target_modules="all-linear",
                lora_dropout=0.05,
                bias="none",
                task_type="FEATURE_EXTRACTION"
            )
            
            self.model = get_peft_model(self.model, lora_config)
        
        self.model.train()
        
        # Load sample data
        self.sample_data = self.load_sample_data()
        
        logger.info("✅ Model loaded successfully")
    
    def prepare_batch(self, batch_size: int) -> Dict:
        """Prepare a batch for memory testing."""
        # Replicate sample data for batch
        batch_frames = [self.sample_data["frames"]] * batch_size
        batch_contexts = [self.sample_data["context"]] * batch_size
        batch_questions = [self.sample_data["question"]] * batch_size
        batch_outputs = [self.sample_data["output"]] * batch_size
        
        # Format messages like in training script
        messages_batch = []
        for i in range(batch_size):
            # Create image content
            images = [{"type": "image", "image": img} for img in batch_frames[i]]
            
            # System prompt
            system_prompt = f"""You are Ash Ketchum, a Pokemon trainer. Context: {batch_contexts[i]}
Analyze the 4-frame sequence and respond with JSON."""
            
            messages = [
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": images + [{"type": "text", "text": batch_questions[i]}]},
                {"role": "assistant", "content": [{"type": "text", "text": batch_outputs[i]}]}
            ]
            messages_batch.append(messages)
        
        # Process with tokenizer
        texts = [
            self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            ).strip()
            for messages in messages_batch
        ]
        
        # Extract images for processing
        images_batch = []
        for messages in messages_batch:
            images = []
            for msg in messages:
                content = msg.get("content", [])
                for element in content:
                    if isinstance(element, dict) and element.get("type") == "image":
                        images.append(element["image"])
            images_batch.append(images)
        
        # Tokenize and process
        batch = self.processor(
            text=texts,
            images=images_batch,
            return_tensors="pt",
            padding=True,
            max_length=8192,  # Reasonable length for testing
            truncation=True
        )
        
        # Move to device
        for key in batch:
            if isinstance(batch[key], torch.Tensor):
                batch[key] = batch[key].to(self.device)
        
        # Setup labels
        labels = batch["input_ids"].clone()
        labels[labels == self.processor.tokenizer.pad_token_id] = -100
        batch["labels"] = labels
        
        return batch
    
    def test_batch_size(self, batch_size: int, test_backward: bool = True) -> Tuple[bool, Dict]:
        """Test if a batch size fits in memory."""
        logger.info(f"🧪 Testing batch size: {batch_size}")
        
        try:
            # Clear cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            # Record initial memory
            initial_memory = self.get_memory_usage()
            
            # Prepare batch
            batch = self.prepare_batch(batch_size)
            
            # Forward pass
            start_time = time.time()
            
            if test_backward:
                # Full training step
                outputs = self.model(**batch)
                loss = outputs.loss
                loss.backward()
                
                # Clear gradients
                for param in self.model.parameters():
                    if param.grad is not None:
                        param.grad = None
            else:
                # Inference only
                with torch.no_grad():
                    outputs = self.model(**batch)
            
            forward_time = time.time() - start_time
            peak_memory = self.get_memory_usage()
            
            # Clean up
            del batch, outputs
            if test_backward and 'loss' in locals():
                del loss
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            final_memory = self.get_memory_usage()
            
            result = {
                "success": True,
                "batch_size": batch_size,
                "forward_time": forward_time,
                "initial_memory": initial_memory,
                "peak_memory": peak_memory,
                "final_memory": final_memory,
                "memory_used": peak_memory - initial_memory
            }
            
            logger.info(f"✅ Batch size {batch_size}: {forward_time:.2f}s, {result['memory_used']:.1f}MB used")
            return True, result
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.info(f"❌ Batch size {batch_size}: OOM")
                
                # Clean up after OOM
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                
                return False, {"success": False, "batch_size": batch_size, "error": "OOM"}
            else:
                logger.error(f"❌ Batch size {batch_size}: {e}")
                return False, {"success": False, "batch_size": batch_size, "error": str(e)}
        
        except Exception as e:
            logger.error(f"❌ Batch size {batch_size}: {e}")
            return False, {"success": False, "batch_size": batch_size, "error": str(e)}
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024**2)
        else:
            # For CPU/MPS, use process memory
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024**2)
    
    def binary_search_max_batch_size(self, max_batch_size: int = 32, safety_factor: float = 0.8) -> Dict:
        """Binary search to find maximum batch size."""
        logger.info(f"🔍 Finding maximum batch size (max: {max_batch_size})")
        
        low, high = 1, max_batch_size
        best_batch_size = 1
        test_results = []
        
        while low <= high:
            mid = (low + high) // 2
            success, result = self.test_batch_size(mid)
            test_results.append(result)
            
            if success:
                best_batch_size = mid
                low = mid + 1
            else:
                high = mid - 1
        
        # Apply safety factor
        safe_batch_size = max(1, int(best_batch_size * safety_factor))
        
        logger.info(f"🎯 Maximum batch size: {best_batch_size}")
        logger.info(f"🛡️ Recommended safe batch size: {safe_batch_size}")
        
        return {
            "max_batch_size": best_batch_size,
            "safe_batch_size": safe_batch_size,
            "safety_factor": safety_factor,
            "test_results": test_results
        }
    
    def recommend_configuration(self, system_info: Dict, batch_results: Dict) -> Dict:
        """Recommend training configuration based on findings."""
        safe_batch_size = batch_results["safe_batch_size"]
        
        # Calculate gradient accumulation for effective batch size
        target_effective_batch_size = 32  # Good default for VLM training
        grad_accum_steps = max(1, target_effective_batch_size // safe_batch_size)
        effective_batch_size = safe_batch_size * grad_accum_steps
        
        # Recommend learning rate based on effective batch size
        base_lr = 2e-4
        lr_scale = (effective_batch_size / 8) ** 0.5  # Square root scaling
        recommended_lr = base_lr * lr_scale
        
        # Hardware-specific recommendations
        recommendations = {
            "batch_size": safe_batch_size,
            "gradient_accumulation_steps": grad_accum_steps,
            "effective_batch_size": effective_batch_size,
            "learning_rate": recommended_lr,
            "dataloader_num_workers": 0,  # Avoid issues with images
        }
        
        # Platform-specific optimizations
        if system_info["platform"] == "cuda":
            total_vram = system_info.get("total_vram_gb", 0)
            if total_vram >= 24:  # High-end GPU
                recommendations.update({
                    "torch_dtype": "bfloat16",
                    "gradient_checkpointing": False,
                    "dataloader_pin_memory": True
                })
            elif total_vram >= 12:  # Mid-range GPU
                recommendations.update({
                    "torch_dtype": "bfloat16", 
                    "gradient_checkpointing": True,
                    "dataloader_pin_memory": True
                })
            else:  # Low VRAM
                recommendations.update({
                    "torch_dtype": "bfloat16",
                    "gradient_checkpointing": True,
                    "dataloader_pin_memory": False,
                    "optim": "adamw_torch_fused"
                })
        
        elif system_info["platform"] == "mps":
            recommendations.update({
                "torch_dtype": "float32",  # MPS doesn't support bfloat16 fully
                "gradient_checkpointing": True,
                "dataloader_pin_memory": False
            })
        
        return recommendations


def main():
    parser = argparse.ArgumentParser(description="Find optimal batch size for Pokemon Gemma VLM training")
    parser.add_argument("--model_name", default="google/gemma-3-4b-it", help="Model to test")
    parser.add_argument("--dataset_path", required=True, help="Path to training dataset")
    parser.add_argument("--max_batch_size", type=int, default=32, help="Maximum batch size to test")
    parser.add_argument("--use_peft", action="store_true", help="Test with PEFT/LoRA enabled")
    parser.add_argument("--output", help="Output JSON file for results")
    
    args = parser.parse_args()
    
    # Initialize finder
    finder = BatchSizeFinder(args.model_name, args.dataset_path, args.use_peft)
    
    # Get system info
    system_info = finder.get_system_info()
    logger.info(f"🖥️ System: {system_info['platform']}")
    if system_info["platform"] == "cuda":
        for gpu in system_info["gpus"]:
            logger.info(f"  GPU {gpu['id']}: {gpu['name']} ({gpu['vram_gb']:.1f}GB)")
    
    # Load model
    finder.load_model()
    
    # Find optimal batch size
    batch_results = finder.binary_search_max_batch_size(args.max_batch_size)
    
    # Generate recommendations
    recommendations = finder.recommend_configuration(system_info, batch_results)
    
    # Compile results
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_name": args.model_name,
        "dataset_path": args.dataset_path,
        "use_peft": args.use_peft,
        "system_info": system_info,
        "batch_size_results": batch_results,
        "recommendations": recommendations
    }
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("🎯 BATCH SIZE RECOMMENDATIONS")
    logger.info("="*60)
    logger.info(f"Recommended batch size: {recommendations['batch_size']}")
    logger.info(f"Gradient accumulation: {recommendations['gradient_accumulation_steps']}")
    logger.info(f"Effective batch size: {recommendations['effective_batch_size']}")
    logger.info(f"Learning rate: {recommendations['learning_rate']:.2e}")
    logger.info(f"PyTorch dtype: {recommendations.get('torch_dtype', 'default')}")
    
    # Save results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Results saved to: {output_path}")
    
    logger.info("✅ Batch size finding complete!")


if __name__ == "__main__":
    main()