#!/usr/bin/env python3
"""
GGUF Conversion Script for Pokemon Gemma VLM
Converts trained PyTorch models to GGUF format for efficient CPU/MPS inference
"""

import argparse
import os
import subprocess
import tempfile
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_llama_cpp_python():
    """Check if llama-cpp-python is installed."""
    try:
        import llama_cpp
        logger.info(f"✅ llama-cpp-python found: {llama_cpp.__version__}")
        return True
    except ImportError:
        logger.error("❌ llama-cpp-python not found")
        logger.error("Install with: pip install llama-cpp-python")
        return False


def convert_to_gguf(model_path: str, output_path: str, quantization: str = "f16"):
    """
    Convert Pokemon Gemma VLM to GGUF format.
    
    Args:
        model_path: Path to trained PyTorch model
        output_path: Output path for GGUF file
        quantization: Quantization level (f32, f16, q8_0, q4_0, q4_1)
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
            logger.warning(f"⚠️ Missing {file} - may cause issues")
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert using llama.cpp convert script
    try:
        # Check if we have the conversion script
        llama_cpp_path = subprocess.check_output(
            ["python", "-c", "import llama_cpp; print(llama_cpp.__path__[0])"],
            text=True
        ).strip()
        
        convert_script = Path(llama_cpp_path) / "llama_cpp" / "convert.py"
        
        if not convert_script.exists():
            # Try alternative path
            convert_script = Path(llama_cpp_path) / "convert.py"
        
        if not convert_script.exists():
            raise FileNotFoundError("llama.cpp convert script not found")
        
        # Run conversion
        cmd = [
            "python", str(convert_script),
            str(model_path),
            "--outtype", quantization,
            "--outfile", str(output_path)
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("✅ GGUF conversion successful!")
            
            # Verify output file
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"📁 Output size: {size_mb:.1f}MB")
            
            return str(output_path)
        else:
            logger.error(f"❌ Conversion failed:")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError("GGUF conversion failed")
            
    except Exception as e:
        logger.error(f"❌ Conversion error: {e}")
        raise


def test_gguf_model(gguf_path: str):
    """Test the converted GGUF model."""
    logger.info("🧪 Testing GGUF model...")
    
    try:
        from llama_cpp import Llama
        
        # Load model
        model = Llama(
            model_path=gguf_path,
            n_ctx=2048,  # Context length
            n_threads=4,  # Number of threads
            verbose=False
        )
        
        # Test generation
        prompt = "You are Ash Ketchum analyzing Pokemon gameplay. What should I do next?"
        
        output = model(
            prompt,
            max_tokens=64,
            temperature=0.1,
            stop=["Human:", "\n\n"]
        )
        
        response = output["choices"][0]["text"]
        logger.info(f"✅ Test successful! Response: {response[:100]}...")
        
        # Clean up
        del model
        
    except Exception as e:
        logger.error(f"❌ GGUF test failed: {e}")
        raise


def convert_for_mlx(model_path: str, output_path: str):
    """
    Convert model to MLX format for Apple Silicon inference.
    
    Args:
        model_path: Path to trained PyTorch model
        output_path: Output directory for MLX model
    """
    logger.info(f"🍎 Converting {model_path} to MLX format")
    
    try:
        # Check if MLX is available
        import mlx.core as mx
        from mlx_lm import convert
        
        # Convert to MLX format
        convert(
            model_path,
            output_path,
            quantize=True,  # Enable quantization for efficiency
            q_bits=4,      # 4-bit quantization
            q_group_size=64
        )
        
        logger.info(f"✅ MLX conversion successful: {output_path}")
        
    except ImportError:
        logger.error("❌ MLX not available - install with: pip install mlx-lm")
        raise
    except Exception as e:
        logger.error(f"❌ MLX conversion failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Convert Pokemon Gemma VLM to efficient inference formats")
    parser.add_argument("--model_path", required=True, help="Path to trained PyTorch model")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--format", choices=["gguf", "mlx", "both"], default="gguf", 
                       help="Conversion format")
    parser.add_argument("--quantization", choices=["f32", "f16", "q8_0", "q4_0", "q4_1"], 
                       default="f16", help="Quantization level for GGUF")
    parser.add_argument("--test", action="store_true", help="Test converted model")
    
    args = parser.parse_args()
    
    model_path = Path(args.model_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get model name for output files
    model_name = model_path.name
    
    converted_files = []
    
    if args.format in ["gguf", "both"]:
        # GGUF conversion
        if not check_llama_cpp_python():
            logger.error("Cannot convert to GGUF without llama-cpp-python")
            return
        
        gguf_path = output_dir / f"{model_name}-{args.quantization}.gguf"
        converted_path = convert_to_gguf(args.model_path, gguf_path, args.quantization)
        converted_files.append(("GGUF", converted_path))
        
        if args.test:
            test_gguf_model(converted_path)
    
    if args.format in ["mlx", "both"]:
        # MLX conversion
        mlx_path = output_dir / f"{model_name}-mlx"
        try:
            convert_for_mlx(args.model_path, mlx_path)
            converted_files.append(("MLX", str(mlx_path)))
        except Exception as e:
            logger.error(f"MLX conversion failed: {e}")
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("🎉 Conversion Summary:")
    for format_name, path in converted_files:
        logger.info(f"  {format_name}: {path}")
    
    # Save conversion info
    conversion_info = {
        "source_model": str(model_path),
        "conversions": [
            {"format": fmt, "path": path} for fmt, path in converted_files
        ],
        "quantization": args.quantization if args.format in ["gguf", "both"] else None
    }
    
    info_path = output_dir / "conversion_info.json"
    with open(info_path, "w") as f:
        json.dump(conversion_info, f, indent=2)
    
    logger.info(f"📄 Conversion info saved to: {info_path}")


if __name__ == "__main__":
    main()