#!/usr/bin/env python3
"""
MLX Conversion Script for Pokemon Gemma VLM
Converts trained PyTorch models to MLX format for efficient Apple Silicon inference
"""

import argparse
import os
import json
import tempfile
from pathlib import Path
import logging
import shutil
import subprocess
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_mlx_dependencies():
    """Check if MLX dependencies are installed."""
    missing_deps = []
    
    try:
        import mlx.core as mx
        logger.info(f"✅ MLX Core found: {mx.__version__}")
    except ImportError:
        missing_deps.append("mlx")
    
    try:
        import mlx_lm
        logger.info(f"✅ MLX-LM found")
    except ImportError:
        missing_deps.append("mlx-lm")
    
    if missing_deps:
        logger.error(f"❌ Missing dependencies: {missing_deps}")
        logger.error("Install with: pip install mlx mlx-lm")
        return False
    
    return True


def verify_apple_silicon():
    """Verify running on Apple Silicon."""
    if sys.platform != "darwin":
        logger.error("❌ MLX conversion only supported on macOS")
        return False
    
    # Check if Apple Silicon
    try:
        import platform
        machine = platform.machine()
        if machine not in ["arm64", "aarch64"]:
            logger.warning(f"⚠️  Running on {machine}, MLX optimized for Apple Silicon")
        else:
            logger.info(f"✅ Running on Apple Silicon ({machine})")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Could not detect architecture: {e}")
        return True


def convert_to_mlx(model_path: str, output_path: str, quantization_bits: int = 4):
    """
    Convert Pokemon Gemma VLM to MLX format.
    
    Args:
        model_path: Path to trained PyTorch model (LoRA merged)
        output_path: Output directory for MLX model
        quantization_bits: Quantization level (4, 8, 16)
    """
    logger.info(f"🔄 Converting {model_path} to MLX format")
    logger.info(f"📦 Output: {output_path}")
    logger.info(f"🔢 Quantization: {quantization_bits}-bit")
    
    model_path = Path(model_path)
    output_path = Path(output_path)
    
    # Validate input model
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Check for required files
    required_files = ["config.json", "tokenizer.json"]
    for file in required_files:
        if not (model_path / file).exists():
            logger.warning(f"⚠️  Missing {file}, conversion may fail")
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Import MLX conversion tools
        from mlx_lm import convert
        import mlx.core as mx
        
        logger.info("🔧 Starting MLX conversion...")
        
        # Convert to MLX format with quantization
        if quantization_bits in [4, 8]:
            logger.info(f"📉 Applying {quantization_bits}-bit quantization...")
            
            # Use MLX-LM convert with quantization
            convert(
                hf_path=str(model_path),
                mlx_path=str(output_path),
                quantize=True,
                q_bits=quantization_bits,
                q_group_size=64 if quantization_bits == 4 else 128,
                dtype="float16"  # Use float16 for better performance on Apple Silicon
            )
        else:
            logger.info("📦 Converting without quantization...")
            
            # Convert without quantization (16-bit)
            convert(
                hf_path=str(model_path),
                mlx_path=str(output_path),
                quantize=False,
                dtype="float16"
            )
        
        # Verify conversion
        verify_mlx_conversion(output_path)
        
        # Generate model info
        generate_mlx_info(model_path, output_path, quantization_bits)
        
        logger.info("✅ MLX conversion completed successfully!")
        
        return {
            "success": True,
            "output_path": str(output_path),
            "quantization_bits": quantization_bits,
            "format": "mlx"
        }
        
    except ImportError as e:
        logger.error(f"❌ MLX dependencies missing: {e}")
        logger.error("Install with: pip install mlx mlx-lm")
        return {"success": False, "error": f"Missing dependencies: {e}"}
    
    except Exception as e:
        logger.error(f"❌ MLX conversion failed: {e}")
        return {"success": False, "error": str(e)}


def verify_mlx_conversion(mlx_path: Path):
    """Verify MLX model was created correctly."""
    required_files = ["weights.npz", "config.json", "tokenizer.json"]
    
    for file in required_files:
        file_path = mlx_path / file
        if not file_path.exists():
            raise FileNotFoundError(f"MLX conversion incomplete: missing {file}")
        
        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"  ✅ {file}: {size_mb:.1f} MB")


def generate_mlx_info(model_path: Path, output_path: Path, quantization_bits: int):
    """Generate MLX model information file."""
    
    # Load original config
    config_path = model_path / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            original_config = json.load(f)
    else:
        original_config = {}
    
    # Calculate sizes
    original_size = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())
    mlx_size = sum(f.stat().st_size for f in output_path.rglob("*") if f.is_file())
    
    mlx_info = {
        "model_type": "pokemon_gemma_vlm_mlx",
        "base_model": original_config.get("_name_or_path", "google/gemma-3-4b-it"),
        "quantization_bits": quantization_bits,
        "original_size_mb": original_size / (1024 * 1024),
        "mlx_size_mb": mlx_size / (1024 * 1024),
        "compression_ratio": original_size / mlx_size if mlx_size > 0 else 1.0,
        "architecture": original_config.get("architectures", ["Gemma3ForImageTextToText"]),
        "vocab_size": original_config.get("vocab_size", 32768),
        "hidden_size": original_config.get("hidden_size", 3072),
        "num_hidden_layers": original_config.get("num_hidden_layers", 28),
        "num_attention_heads": original_config.get("num_attention_heads", 24),
        "conversion_info": {
            "converted_from": str(model_path),
            "mlx_format_version": "1.0",
            "supports_inference": True,
            "supports_generation": True,
            "apple_silicon_optimized": True
        }
    }
    
    info_path = output_path / "mlx_model_info.json"
    with open(info_path, 'w') as f:
        json.dump(mlx_info, f, indent=2)
    
    logger.info(f"📊 Model size: {original_size/(1024*1024):.1f} MB → {mlx_size/(1024*1024):.1f} MB")
    logger.info(f"📈 Compression: {mlx_info['compression_ratio']:.1f}x")


def test_mlx_inference(mlx_path: Path):
    """Quick test of MLX model inference."""
    try:
        import mlx_lm
        
        logger.info("🧪 Testing MLX model inference...")
        
        # Load model
        model, tokenizer = mlx_lm.load(str(mlx_path))
        
        # Simple test prompt
        test_prompt = "Test inference"
        
        # Generate (very short to just test loading)
        response = mlx_lm.generate(
            model=model,
            tokenizer=tokenizer,
            prompt=test_prompt,
            max_tokens=5,
            verbose=False
        )
        
        logger.info("✅ MLX inference test passed")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  MLX inference test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert Pokemon Gemma VLM to MLX format")
    parser.add_argument("--model_path", required=True, help="Path to trained PyTorch model")
    parser.add_argument("--output_path", required=True, help="Output directory for MLX model")
    parser.add_argument("--quantization_bits", type=int, choices=[4, 8, 16], default=4,
                       help="Quantization level (4, 8, or 16 bits)")
    parser.add_argument("--test_inference", action="store_true",
                       help="Test inference after conversion")
    parser.add_argument("--force", action="store_true",
                       help="Overwrite existing output directory")
    
    args = parser.parse_args()
    
    # Verify environment
    if not verify_apple_silicon():
        sys.exit(1)
    
    if not check_mlx_dependencies():
        sys.exit(1)
    
    # Check output directory
    output_path = Path(args.output_path)
    if output_path.exists() and not args.force:
        logger.error(f"❌ Output directory exists: {output_path}")
        logger.error("Use --force to overwrite")
        sys.exit(1)
    
    # Perform conversion
    result = convert_to_mlx(
        model_path=args.model_path,
        output_path=args.output_path,
        quantization_bits=args.quantization_bits
    )
    
    if not result["success"]:
        logger.error(f"❌ Conversion failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    # Test inference if requested
    if args.test_inference:
        test_mlx_inference(output_path)
    
    logger.info("🎉 MLX conversion completed successfully!")
    logger.info(f"📁 MLX model ready: {output_path.absolute()}")


if __name__ == "__main__":
    main()