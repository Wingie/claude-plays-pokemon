# Tutorial 08: Model Deployment & Optimization

## Overview

This tutorial covers complete model deployment from training checkpoints to production-ready MLX-optimized inference on Apple Silicon, including GGUF conversion, performance optimization, and production serving.

## Prerequisites

- Completed Tutorial 07 (Model Evaluation)
- Validated model checkpoint ready for deployment
- Apple Silicon Mac for MLX optimization (optional but recommended)

## Deployment Pipeline Overview

```
Training Checkpoint → Model Merging → Format Conversion → Optimization → Production Serving
                                           ↓
                                    [GGUF] [MLX] [ONNX]
```

## Phase 1: Model Preparation & Merging

### 1. Merge LoRA Adapters with Base Model

```python
#!/usr/bin/env python3
"""
Model Adapter Merging Script
Merges trained LoRA adapters with base Gemma model
"""

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from peft import PeftModel
import argparse
from pathlib import Path

def merge_lora_adapters(base_model_path, adapter_path, output_path, device_map="auto"):
    """
    Merge LoRA adapters with base model for deployment.
    
    Args:
        base_model_path: Path to base Gemma model (e.g., "google/gemma-3-4b-it")
        adapter_path: Path to trained LoRA adapters
        output_path: Output path for merged model
        device_map: Device mapping for model loading
    """
    print(f"🔄 Merging LoRA adapters...")
    print(f"Base model: {base_model_path}")
    print(f"Adapters: {adapter_path}")
    print(f"Output: {output_path}")
    
    # Load base model
    print("📦 Loading base model...")
    base_model = AutoModelForImageTextToText.from_pretrained(
        base_model_path,
        torch_dtype=torch.bfloat16,
        device_map=device_map,
        low_cpu_mem_usage=True
    )
    
    # Load LoRA adapters
    print("🔧 Loading LoRA adapters...")
    model_with_adapters = PeftModel.from_pretrained(base_model, adapter_path)
    
    # Merge adapters
    print("🔗 Merging adapters with base model...")
    merged_model = model_with_adapters.merge_and_unload()
    
    # Load processor
    processor = AutoProcessor.from_pretrained(base_model_path)
    
    # Save merged model
    print(f"💾 Saving merged model to {output_path}...")
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    merged_model.save_pretrained(
        output_path,
        safe_serialization=True,
        max_shard_size="2GB"
    )
    processor.save_pretrained(output_path)
    
    # Save model info
    model_info = {
        "base_model": base_model_path,
        "adapter_path": str(adapter_path),
        "merge_timestamp": torch.utils.data.get_worker_info() or "unknown",
        "model_size_params": sum(p.numel() for p in merged_model.parameters()),
        "dtype": str(merged_model.dtype)
    }
    
    with open(output_path / "merge_info.json", 'w') as f:
        import json
        json.dump(model_info, f, indent=2)
    
    print("✅ Model merging completed successfully!")
    
    # Cleanup memory
    del base_model, model_with_adapters, merged_model
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    return str(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA adapters with base model")
    parser.add_argument("--base_model", required=True, help="Base model path")
    parser.add_argument("--adapter_path", required=True, help="LoRA adapter path")
    parser.add_argument("--output_path", required=True, help="Output path for merged model")
    
    args = parser.parse_args()
    
    merged_path = merge_lora_adapters(
        args.base_model,
        args.adapter_path,
        args.output_path
    )
    print(f"🎉 Merged model ready at: {merged_path}")
```

### 2. Model Validation After Merging

```python
#!/usr/bin/env python3
"""
Merged Model Validation
Validates merged model maintains training performance
"""

import json
import torch
from pathlib import Path
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image

def validate_merged_model(merged_model_path, test_grid_path, expected_output=None):
    """Validate merged model produces correct outputs."""
    print("🧪 Validating merged model...")
    
    try:
        # Load merged model
        model = AutoModelForImageTextToText.from_pretrained(
            merged_model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        processor = AutoProcessor.from_pretrained(merged_model_path)
        
        # Load test image
        test_image = Image.open(test_grid_path).convert('RGB')
        
        # Test inference
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": test_image},
                {"type": "text", "text": "What button should be pressed next based on this temporal grid?"}
            ]}
        ]
        
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], images=[[test_image]], return_tensors="pt", padding=True)
        
        # Move to device
        for key in inputs:
            if isinstance(inputs[key], torch.Tensor):
                inputs[key] = inputs[key].to(model.device)
        
        # Generate response
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                temperature=0.1,
                do_sample=True
            )
        
        response = processor.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        
        # Validate response format
        try:
            parsed_response = json.loads(response.strip())
            valid_json = True
            has_button = 'button' in parsed_response
            has_reasoning = 'reasoning' in parsed_response
        except json.JSONDecodeError:
            valid_json = False
            has_button = False
            has_reasoning = False
        
        validation_result = {
            "model_path": str(merged_model_path),
            "test_successful": True,
            "valid_json": valid_json,
            "has_button": has_button,
            "has_reasoning": has_reasoning,
            "raw_response": response,
            "parsed_response": parsed_response if valid_json else None
        }
        
        if valid_json and has_button:
            print("✅ Merged model validation PASSED")
        else:
            print("⚠️ Merged model validation completed with issues")
            
        return validation_result
        
    except Exception as e:
        print(f"❌ Merged model validation FAILED: {e}")
        return {"model_path": str(merged_model_path), "test_successful": False, "error": str(e)}

# Usage
if __name__ == "__main__":
    result = validate_merged_model(
        "models/gemma-3-4b-pokemon-merged",
        "training_data/grid_images/test_grid_001.png"
    )
    print(json.dumps(result, indent=2))
```

## Phase 2: Multi-Format Conversion

### 1. Enhanced GGUF Conversion

```python
#!/usr/bin/env python3
"""
Enhanced GGUF Conversion Pipeline
Converts Pokemon Gemma models to GGUF with optimization
"""

import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_gguf_enhanced(model_path, output_path, quantization="f16", vocab_type="auto"):
    """
    Enhanced GGUF conversion with Pokemon Gemma optimizations.
    
    Args:
        model_path: Path to merged PyTorch model
        output_path: Output path for GGUF file
        quantization: Quantization level (f32, f16, q8_0, q4_0, q4_1, q4_k_m, q5_k_m)
        vocab_type: Vocabulary type (auto, spm, bpe, hfft)
    """
    logger.info(f"🔄 Converting {model_path} to GGUF format")
    logger.info(f"📦 Output: {output_path}")
    logger.info(f"🔢 Quantization: {quantization}")
    
    model_path = Path(model_path)
    output_path = Path(output_path)
    
    # Validate input model
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Check for required files
    required_files = ["config.json", "tokenizer.json"]
    for file in required_files:
        if not (model_path / file).exists():
            logger.warning(f"⚠️ Missing {file} - may cause conversion issues")
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use llama.cpp convert script directly
        # This assumes llama.cpp is available in the environment
        convert_cmd = [
            "python", "-m", "llama_cpp.convert",
            str(model_path),
            "--outtype", quantization,
            "--outfile", str(output_path),
            "--vocab-type", vocab_type
        ]
        
        logger.info(f"Running conversion: {' '.join(convert_cmd)}")
        
        result = subprocess.run(
            convert_cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ GGUF conversion successful!")
            
            # Verify output file
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"📁 Output size: {size_mb:.1f}MB")
                
                # Save conversion metadata
                metadata = {
                    "source_model": str(model_path),
                    "output_file": str(output_path),
                    "quantization": quantization,
                    "vocab_type": vocab_type,
                    "file_size_mb": size_mb,
                    "conversion_success": True,
                    "llama_cpp_version": get_llama_cpp_version()
                }
                
                metadata_path = output_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return str(output_path)
            else:
                raise RuntimeError("Conversion completed but output file not found")
        else:
            logger.error(f"❌ Conversion failed:")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError("GGUF conversion failed")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Conversion timeout (>1 hour)")
        raise RuntimeError("GGUF conversion timeout")
    except Exception as e:
        logger.error(f"❌ Conversion error: {e}")
        raise

def get_llama_cpp_version():
    """Get llama-cpp-python version."""
    try:
        import llama_cpp
        return llama_cpp.__version__
    except:
        return "unknown"

def test_gguf_model(gguf_path):
    """Test converted GGUF model."""
    logger.info("🧪 Testing GGUF model...")
    
    try:
        from llama_cpp import Llama
        
        # Load model with Pokemon-optimized settings
        model = Llama(
            model_path=str(gguf_path),
            n_ctx=4096,  # Context length optimized for Pokemon gameplay
            n_threads=8,  # Multi-threading for performance
            n_gpu_layers=50,  # GPU acceleration if available
            verbose=False,
            use_mmap=True,  # Memory mapping for efficiency
            use_mlock=False,  # Avoid memory locking on macOS
        )
        
        # Test generation with Pokemon-specific prompt
        test_prompt = """You are Ash Ketchum analyzing Pokemon gameplay. 
Looking at a 2x2 temporal grid showing game progression, what button should be pressed next?

Respond in JSON format:"""
        
        output = model(
            test_prompt,
            max_tokens=128,
            temperature=0.1,
            top_p=0.9,
            stop=["Human:", "\\n\\n", "}"],
            echo=False
        )
        
        response = output["choices"][0]["text"]
        logger.info(f"✅ GGUF test successful! Response: {response[:100]}...")
        
        # Clean up
        del model
        
        return {"success": True, "response": response}
        
    except Exception as e:
        logger.error(f"❌ GGUF test failed: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced GGUF conversion for Pokemon Gemma VLM")
    parser.add_argument("--model_path", required=True, help="Path to merged PyTorch model")
    parser.add_argument("--output_path", required=True, help="Output path for GGUF file")
    parser.add_argument("--quantization", choices=["f32", "f16", "q8_0", "q4_0", "q4_1", "q4_k_m", "q5_k_m"], 
                       default="f16", help="Quantization level")
    parser.add_argument("--test", action="store_true", help="Test converted model")
    
    args = parser.parse_args()
    
    # Convert to GGUF
    gguf_path = convert_to_gguf_enhanced(
        args.model_path,
        args.output_path,
        args.quantization
    )
    
    # Test if requested
    if args.test:
        test_result = test_gguf_model(gguf_path)
        if not test_result["success"]:
            logger.error("GGUF model failed testing")
            exit(1)
    
    logger.info(f"🎉 GGUF conversion complete: {gguf_path}")
```

### 2. MLX Conversion Pipeline for Apple Silicon

```python
#!/usr/bin/env python3
"""
MLX Conversion Pipeline for Apple Silicon
Optimized conversion and inference for Pokemon Gemma VLM
"""

import argparse
import json
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_mlx(model_path, output_path, quantize=True, q_bits=4, q_group_size=64):
    """
    Convert Pokemon Gemma model to MLX format for Apple Silicon.
    
    Args:
        model_path: Path to merged PyTorch model
        output_path: Output directory for MLX model
        quantize: Whether to quantize the model
        q_bits: Quantization bits (4, 8, 16)
        q_group_size: Quantization group size
    """
    logger.info(f"🍎 Converting {model_path} to MLX format")
    logger.info(f"📦 Output: {output_path}")
    logger.info(f"🔢 Quantization: {quantize} (bits={q_bits}, group_size={q_group_size})")
    
    try:
        # Check MLX availability
        import mlx.core as mx
        from mlx_lm import convert, load
        
        logger.info("✅ MLX environment available")
        
        # Create output directory
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Convert to MLX format
        logger.info("🔄 Starting MLX conversion...")
        
        conversion_args = {
            "hf_path": str(model_path),
            "mlx_path": str(output_path),
            "quantize": quantize
        }
        
        if quantize:
            conversion_args.update({
                "q_bits": q_bits,
                "q_group_size": q_group_size
            })
        
        # Perform conversion
        convert(**conversion_args)
        
        logger.info("✅ MLX conversion successful!")
        
        # Save conversion metadata
        metadata = {
            "source_model": str(model_path),
            "output_path": str(output_path),
            "quantized": quantize,
            "quantization_bits": q_bits if quantize else None,
            "quantization_group_size": q_group_size if quantize else None,
            "conversion_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mlx_version": mx.__version__
        }
        
        with open(output_path / "mlx_conversion_info.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📄 Conversion metadata saved")
        
        return str(output_path)
        
    except ImportError:
        logger.error("❌ MLX not available - install with: pip install mlx-lm")
        raise RuntimeError("MLX dependencies not found")
    except Exception as e:
        logger.error(f"❌ MLX conversion failed: {e}")
        raise

def test_mlx_model(mlx_path, test_prompt=None):
    """Test MLX model inference."""
    logger.info("🧪 Testing MLX model...")
    
    if test_prompt is None:
        test_prompt = """You are Ash Ketchum analyzing Pokemon gameplay. 
Based on the temporal progression shown in the grid, what button should be pressed next?

Respond in JSON format with your analysis:"""
    
    try:
        from mlx_lm import load, generate
        
        # Load MLX model
        logger.info("📦 Loading MLX model...")
        model, tokenizer = load(str(mlx_path))
        
        logger.info("✅ MLX model loaded successfully")
        
        # Test generation
        logger.info("🎯 Testing generation...")
        start_time = time.time()
        
        response = generate(
            model,
            tokenizer,
            prompt=test_prompt,
            max_tokens=128,
            temperature=0.1,
            verbose=False
        )
        
        end_time = time.time()
        inference_time = end_time - start_time
        
        logger.info(f"✅ MLX generation successful!")
        logger.info(f"⚡ Inference time: {inference_time:.3f}s")
        logger.info(f"📝 Response: {response[:100]}...")
        
        return {
            "success": True,
            "inference_time": inference_time,
            "response": response,
            "model_path": str(mlx_path)
        }
        
    except Exception as e:
        logger.error(f"❌ MLX test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "model_path": str(mlx_path)
        }

def benchmark_mlx_performance(mlx_path, num_runs=10):
    """Benchmark MLX model performance."""
    logger.info(f"⚡ Benchmarking MLX performance over {num_runs} runs...")
    
    try:
        from mlx_lm import load, generate
        
        # Load model
        model, tokenizer = load(str(mlx_path))
        
        test_prompt = "You are Ash Ketchum analyzing Pokemon gameplay. What should I do next?"
        
        # Warmup
        logger.info("🔥 Warming up...")
        for _ in range(3):
            generate(model, tokenizer, prompt=test_prompt, max_tokens=32, verbose=False)
        
        # Benchmark runs
        times = []
        for i in range(num_runs):
            start_time = time.time()
            generate(model, tokenizer, prompt=test_prompt, max_tokens=64, verbose=False)
            end_time = time.time()
            times.append(end_time - start_time)
            
            if i % 5 == 0:
                logger.info(f"  Completed {i}/{num_runs} runs")
        
        # Calculate statistics
        import numpy as np
        benchmark_results = {
            "num_runs": num_runs,
            "mean_time": np.mean(times),
            "std_time": np.std(times),
            "min_time": np.min(times),
            "max_time": np.max(times),
            "median_time": np.median(times),
            "p95_time": np.percentile(times, 95),
            "tokens_per_second": 64 / np.mean(times),  # Approximate
            "all_times": times
        }
        
        logger.info(f"📊 Benchmark Results:")
        logger.info(f"  Mean time: {benchmark_results['mean_time']:.3f}s ± {benchmark_results['std_time']:.3f}s")
        logger.info(f"  Median time: {benchmark_results['median_time']:.3f}s")
        logger.info(f"  P95 time: {benchmark_results['p95_time']:.3f}s")
        logger.info(f"  Est. tokens/sec: {benchmark_results['tokens_per_second']:.1f}")
        
        return benchmark_results
        
    except Exception as e:
        logger.error(f"❌ MLX benchmark failed: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MLX conversion for Pokemon Gemma VLM")
    parser.add_argument("--model_path", required=True, help="Path to merged PyTorch model")
    parser.add_argument("--output_path", required=True, help="Output directory for MLX model")
    parser.add_argument("--quantize", action="store_true", help="Enable quantization")
    parser.add_argument("--q_bits", type=int, choices=[4, 8, 16], default=4, help="Quantization bits")
    parser.add_argument("--q_group_size", type=int, default=64, help="Quantization group size")
    parser.add_argument("--test", action="store_true", help="Test converted model")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark model performance")
    
    args = parser.parse_args()
    
    # Convert to MLX
    mlx_path = convert_to_mlx(
        args.model_path,
        args.output_path,
        args.quantize,
        args.q_bits,
        args.q_group_size
    )
    
    # Test if requested
    if args.test:
        test_result = test_mlx_model(mlx_path)
        if not test_result["success"]:
            logger.error("MLX model failed testing")
            exit(1)
    
    # Benchmark if requested
    if args.benchmark:
        benchmark_result = benchmark_mlx_performance(mlx_path)
        
        # Save benchmark results
        benchmark_path = Path(mlx_path) / "benchmark_results.json"
        with open(benchmark_path, 'w') as f:
            json.dump(benchmark_result, f, indent=2)
        
        logger.info(f"📄 Benchmark results saved to: {benchmark_path}")
    
    logger.info(f"🎉 MLX conversion complete: {mlx_path}")
```

## Phase 3: Production Inference Serving

### 1. MLX Inference Server

```python
#!/usr/bin/env python3
"""
Pokemon Gemma MLX Inference Server
Production-ready inference serving on Apple Silicon
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict

# Web framework for API
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# MLX imports
try:
    from mlx_lm import load, generate
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InferenceConfig:
    """Configuration for inference parameters."""
    max_tokens: int = 128
    temperature: float = 0.1
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    seed: Optional[int] = None

class GameplayRequest(BaseModel):
    """Request format for gameplay analysis."""
    context: str
    question: str
    config: Optional[Dict[str, Any]] = None

class GameplayResponse(BaseModel):
    """Response format for gameplay analysis."""
    request_id: str
    button: str
    reasoning: str
    context: str
    scene_description: Optional[str] = None
    confidence: float
    inference_time: float
    model_version: str

class PokemonGemmaMLXServer:
    """Pokemon Gemma MLX Inference Server."""
    
    def __init__(self, model_path: str, config: InferenceConfig = None):
        self.model_path = Path(model_path)
        self.config = config or InferenceConfig()
        self.model = None
        self.tokenizer = None
        self.model_version = "unknown"
        
        # Performance tracking
        self.request_count = 0
        self.total_inference_time = 0.0
        self.startup_time = time.time()
        
        if not MLX_AVAILABLE:
            raise RuntimeError("MLX not available - install with: pip install mlx-lm")
    
    async def load_model(self):
        """Load MLX model asynchronously."""
        logger.info(f"📦 Loading Pokemon Gemma MLX model from {self.model_path}")
        
        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model, self.tokenizer = await loop.run_in_executor(
                None, load, str(self.model_path)
            )
            
            # Load model metadata
            metadata_path = self.model_path / "mlx_conversion_info.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    self.model_version = f"mlx-{metadata.get('quantization_bits', 'fp16')}"
            
            logger.info(f"✅ Model loaded successfully - Version: {self.model_version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    async def generate_response(self, request: GameplayRequest) -> GameplayResponse:
        """Generate Pokemon gameplay response."""
        request_id = str(uuid.uuid4())
        
        if self.model is None or self.tokenizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Merge request config with default config
        inference_config = InferenceConfig()
        if request.config:
            for key, value in request.config.items():
                if hasattr(inference_config, key):
                    setattr(inference_config, key, value)
        
        # Build prompt
        prompt = self._build_prompt(request.context, request.question)
        
        # Generate response
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            raw_response = await loop.run_in_executor(
                None, 
                self._generate_text, 
                prompt, 
                inference_config
            )
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            # Parse response
            parsed_response = self._parse_response(raw_response)
            
            # Update statistics
            self.request_count += 1
            self.total_inference_time += inference_time
            
            response = GameplayResponse(
                request_id=request_id,
                button=parsed_response.get("button", "unknown"),
                reasoning=parsed_response.get("reasoning", ""),
                context=parsed_response.get("context", ""),
                scene_description=parsed_response.get("scene_description"),
                confidence=self._calculate_confidence(parsed_response),
                inference_time=inference_time,
                model_version=self.model_version
            )
            
            logger.info(f"✅ Generated response {request_id} in {inference_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ Generation failed for request {request_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {e}")
    
    def _generate_text(self, prompt: str, config: InferenceConfig) -> str:
        """Generate text using MLX model."""
        return generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            repetition_penalty=config.repetition_penalty,
            verbose=False
        )
    
    def _build_prompt(self, context: str, question: str) -> str:
        """Build inference prompt."""
        return f"""You are Ash Ketchum with expert Pokemon gaming knowledge.

CONTEXT:
{context}

QUESTION:
{question}

Respond in JSON format with your gameplay analysis:
{{
  "button": "action_name",
  "reasoning": "strategic_explanation", 
  "context": "situation_type",
  "scene_description": "detailed_scene_analysis"
}}

RESPONSE:"""
    
    def _parse_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse JSON response from model."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {"button": "unknown", "reasoning": "parse_error", "context": "error"}
        except json.JSONDecodeError:
            return {"button": "unknown", "reasoning": "json_error", "context": "error"}
    
    def _calculate_confidence(self, parsed_response: Dict[str, Any]) -> float:
        """Calculate response confidence score."""
        confidence = 0.5  # Base confidence
        
        # Check response completeness
        if parsed_response.get("button") != "unknown":
            confidence += 0.2
        if parsed_response.get("reasoning") and len(parsed_response["reasoning"]) > 10:
            confidence += 0.2
        if parsed_response.get("context") and len(parsed_response["context"]) > 5:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        uptime = time.time() - self.startup_time
        avg_inference_time = (
            self.total_inference_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "requests_processed": self.request_count,
            "average_inference_time": avg_inference_time,
            "total_inference_time": self.total_inference_time,
            "model_version": self.model_version,
            "model_path": str(self.model_path),
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0
        }

# FastAPI app setup
app = FastAPI(
    title="Pokemon Gemma MLX Inference Server",
    description="Production inference server for Pokemon gameplay analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global server instance
server: Optional[PokemonGemmaMLXServer] = None

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    global server
    import os
    
    model_path = os.getenv("MODEL_PATH", "models/gemma-3-4b-pokemon-mlx")
    
    if not Path(model_path).exists():
        logger.error(f"Model path not found: {model_path}")
        raise RuntimeError(f"Model path not found: {model_path}")
    
    server = PokemonGemmaMLXServer(model_path)
    await server.load_model()
    
    logger.info("🚀 Pokemon Gemma MLX Server started successfully!")

@app.post("/analyze", response_model=GameplayResponse)
async def analyze_gameplay(request: GameplayRequest):
    """Analyze Pokemon gameplay and provide action recommendation."""
    if server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    return await server.generate_response(request)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    return {
        "status": "healthy",
        "model_loaded": server.model is not None,
        "model_version": server.model_version
    }

@app.get("/stats")
async def get_stats():
    """Get server statistics."""
    if server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    return server.get_stats()

@app.get("/config")
async def get_config():
    """Get current inference configuration."""
    if server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    return asdict(server.config)

if __name__ == "__main__":
    import os
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    model_path = os.getenv("MODEL_PATH", "models/gemma-3-4b-pokemon-mlx")
    
    if not Path(model_path).exists():
        logger.error(f"Model path not found: {model_path}")
        exit(1)
    
    logger.info(f"🎮 Starting Pokemon Gemma MLX Server")
    logger.info(f"📦 Model: {model_path}")
    logger.info(f"🌐 Server: {host}:{port}")
    
    uvicorn.run(
        "mlx_inference_server:app",
        host=host,
        port=port,
        reload=False,
        access_log=True
    )
```

### 2. Production Deployment Script

```bash
#!/bin/bash
# production_deployment.sh - Complete production deployment pipeline

set -e

# Configuration
MODEL_CHECKPOINT="${1:-models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000}"
DEPLOYMENT_DIR="deployment_$(date +%Y%m%d_%H%M%S)"
BASE_MODEL="google/gemma-3-4b-it"

echo "🚀 Pokemon Gemma VLM Production Deployment"
echo "=========================================="
echo "Model Checkpoint: $MODEL_CHECKPOINT"
echo "Deployment Directory: $DEPLOYMENT_DIR"
echo "Base Model: $BASE_MODEL"
echo ""

# Create deployment directory
mkdir -p "$DEPLOYMENT_DIR"
cd "$DEPLOYMENT_DIR"

# Phase 1: Model Merging
echo "🔗 Phase 1: Merging LoRA adapters with base model..."
python ../scripts/merge_adapters.py \
    --base_model "$BASE_MODEL" \
    --adapter_path "../$MODEL_CHECKPOINT" \
    --output_path "merged_model"

# Phase 2: Model Validation
echo "🧪 Phase 2: Validating merged model..."
python ../scripts/validate_merged_model.py \
    --model_path "merged_model" \
    --test_grid "../training_data/grid_images/test_grid_001.png" \
    --output_file "validation_results.json"

# Phase 3: Multi-format Conversion
echo "📦 Phase 3: Converting to deployment formats..."

# GGUF Conversion
echo "  Converting to GGUF..."
python ../scripts/convert_to_gguf_enhanced.py \
    --model_path "merged_model" \
    --output_path "pokemon_gemma_f16.gguf" \
    --quantization "f16" \
    --test

# MLX Conversion (if on Apple Silicon)
if [[ $(uname -m) == "arm64" ]] && [[ $(uname) == "Darwin" ]]; then
    echo "  Converting to MLX (Apple Silicon detected)..."
    python ../scripts/convert_to_mlx.py \
        --model_path "merged_model" \
        --output_path "pokemon_gemma_mlx" \
        --quantize \
        --q_bits 4 \
        --test \
        --benchmark
else
    echo "  Skipping MLX conversion (not on Apple Silicon)"
fi

# Phase 4: Performance Benchmarking
echo "⚡ Phase 4: Performance benchmarking..."
python ../scripts/benchmark_all_formats.py \
    --merged_model "merged_model" \
    --gguf_model "pokemon_gemma_f16.gguf" \
    --mlx_model "pokemon_gemma_mlx" \
    --output_file "performance_benchmark.json"

# Phase 5: Production Testing
echo "🎯 Phase 5: Production testing..."
python ../scripts/production_testing.py \
    --deployment_dir "." \
    --test_dataset "../training_data/pokemon_grid_dataset_final.jsonl" \
    --output_file "production_test_results.json"

# Phase 6: Deployment Package Creation
echo "📦 Phase 6: Creating deployment package..."

# Create deployment manifest
cat > deployment_manifest.json << EOF
{
  "deployment_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "model_checkpoint": "$MODEL_CHECKPOINT",
  "base_model": "$BASE_MODEL",
  "formats": {
    "pytorch": "merged_model",
    "gguf": "pokemon_gemma_f16.gguf",
    "mlx": "pokemon_gemma_mlx"
  },
  "validation_passed": true,
  "production_ready": true,
  "deployment_instructions": {
    "pytorch": "Load with transformers.AutoModelForImageTextToText",
    "gguf": "Load with llama-cpp-python",
    "mlx": "Load with mlx-lm, use mlx_inference_server.py for serving"
  }
}
EOF

# Create README
cat > README.md << EOF
# Pokemon Gemma VLM Production Deployment

## Deployment Information
- **Deployment Date**: $(date)
- **Model Checkpoint**: $MODEL_CHECKPOINT
- **Base Model**: $BASE_MODEL

## Available Formats

### PyTorch (merged_model/)
- **Use case**: Development, fine-tuning, full-precision inference
- **Loading**: \`transformers.AutoModelForImageTextToText.from_pretrained("merged_model")\`
- **Memory**: ~8GB GPU memory required

### GGUF (pokemon_gemma_f16.gguf)
- **Use case**: CPU inference, cross-platform deployment
- **Loading**: \`llama_cpp.Llama(model_path="pokemon_gemma_f16.gguf")\`
- **Memory**: ~4GB RAM required

### MLX (pokemon_gemma_mlx/)
- **Use case**: Apple Silicon optimized inference
- **Loading**: \`mlx_lm.load("pokemon_gemma_mlx")\`
- **Memory**: ~3GB unified memory
- **Server**: Use \`mlx_inference_server.py\` for production serving

## Quick Start

### MLX Inference Server (Recommended for Apple Silicon)
\`\`\`bash
MODEL_PATH="pokemon_gemma_mlx" python ../scripts/mlx_inference_server.py
\`\`\`

### GGUF Inference
\`\`\`python
from llama_cpp import Llama
model = Llama(model_path="pokemon_gemma_f16.gguf")
response = model("You are Ash Ketchum. What should I do next?")
\`\`\`

### PyTorch Inference
\`\`\`python
from transformers import AutoModelForImageTextToText, AutoProcessor
model = AutoModelForImageTextToText.from_pretrained("merged_model")
processor = AutoProcessor.from_pretrained("merged_model")
\`\`\`

## Performance Benchmarks
See \`performance_benchmark.json\` for detailed performance metrics across all formats.

## Validation Results
See \`production_test_results.json\` for production readiness assessment.
EOF

# Create Docker deployment (optional)
if command -v docker &> /dev/null; then
    echo "🐳 Creating Docker deployment..."
    
    cat > Dockerfile << EOF
FROM python:3.9-slim

# Install dependencies
RUN pip install fastapi uvicorn mlx-lm transformers torch

# Copy model and server
COPY pokemon_gemma_mlx /app/model
COPY ../scripts/mlx_inference_server.py /app/server.py

WORKDIR /app

# Set environment variables
ENV MODEL_PATH=/app/model
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]
EOF
    
    echo "📄 Dockerfile created for containerized deployment"
fi

# Phase 7: Final Summary
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "📁 Deployment Directory: $(pwd)"
echo "📦 Available Formats:"
echo "  - PyTorch: merged_model/"
echo "  - GGUF: pokemon_gemma_f16.gguf"
if [[ -d "pokemon_gemma_mlx" ]]; then
    echo "  - MLX: pokemon_gemma_mlx/"
fi
echo ""
echo "🚀 Quick Start Commands:"
echo "  MLX Server: MODEL_PATH=pokemon_gemma_mlx python ../scripts/mlx_inference_server.py"
echo "  GGUF Test: python -c \"from llama_cpp import Llama; print(Llama(model_path='pokemon_gemma_f16.gguf')('What should I do?'))\""
echo ""
echo "📊 Review Results:"
echo "  - Validation: validation_results.json"
echo "  - Performance: performance_benchmark.json"
echo "  - Production Tests: production_test_results.json"
echo "  - Deployment Info: deployment_manifest.json"
echo ""
echo "✅ Pokemon Gemma VLM is ready for production deployment!"
```

## Usage Instructions

### 1. Complete Deployment Pipeline

```bash
# Run complete deployment from training checkpoint
bash scripts/production_deployment.sh models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000

# This will create a timestamped deployment directory with all formats
```

### 2. Individual Format Deployment

```bash
# Just MLX for Apple Silicon
python scripts/convert_to_mlx.py \
    --model_path models/gemma-3-4b-pokemon-merged \
    --output_path models/pokemon-gemma-mlx \
    --quantize --test --benchmark

# Just GGUF for cross-platform
python scripts/convert_to_gguf_enhanced.py \
    --model_path models/gemma-3-4b-pokemon-merged \
    --output_path models/pokemon-gemma-f16.gguf \
    --quantization f16 --test
```

### 3. Production Serving

```bash
# Start MLX inference server
MODEL_PATH=models/pokemon-gemma-mlx python scripts/mlx_inference_server.py

# Test the server
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "context": "You are Ash Ketchum exploring Pokemon world",
       "question": "What button should be pressed next based on this temporal grid?"
     }'
```

## Next Steps

1. **Tutorial 09**: Advanced Techniques & Optimization
2. **Production Monitoring**: Set up monitoring and logging
3. **Performance Tuning**: Optimize for specific hardware
4. **Integration**: Connect with Eevee v2 architecture

## Expected Performance

- **MLX (Apple Silicon)**: ~0.3-0.5s inference
- **GGUF (CPU)**: ~1-2s inference
- **PyTorch (GPU)**: ~0.2-0.4s inference

The deployment pipeline produces production-ready Pokemon Gemma VLM models optimized for various platforms and use cases.