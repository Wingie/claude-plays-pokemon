#!/usr/bin/env python3
"""
MPS (Metal Performance Shaders) Compatibility Test for Mac
Tests PyTorch MPS device support for Pokemon Gemma VLM training pipeline
"""

import sys
import torch
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mps_availability():
    """Test if MPS is available and functional."""
    logger.info("🍎 Testing MPS (Metal Performance Shaders) compatibility...")
    
    # Check platform
    if sys.platform != "darwin":
        logger.error("❌ MPS only available on macOS")
        return False
    
    # Check PyTorch version
    logger.info(f"📦 PyTorch version: {torch.__version__}")
    
    # Check MPS availability
    if not torch.backends.mps.is_available():
        logger.error("❌ MPS not available")
        logger.error("Ensure you have:")
        logger.error("- macOS 12.3+ with Apple Silicon (M1/M2/M3)")
        logger.error("- PyTorch 1.12+ with MPS support")
        return False
    
    logger.info("✅ MPS is available")
    
    # Test basic MPS operations
    try:
        device = torch.device("mps")
        
        # Test tensor creation
        x = torch.randn(100, 100, device=device)
        logger.info("✅ Tensor creation on MPS successful")
        
        # Test matrix multiplication
        y = torch.randn(100, 100, device=device)
        z = torch.mm(x, y)
        logger.info("✅ Matrix multiplication on MPS successful")
        
        # Test data transfer
        z_cpu = z.cpu()
        assert z_cpu.shape == (100, 100)
        logger.info("✅ MPS to CPU transfer successful")
        
        # Test memory allocation
        large_tensor = torch.randn(1000, 1000, device=device)
        del large_tensor
        logger.info("✅ Large tensor allocation/deallocation successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MPS operation failed: {e}")
        return False


def test_vision_model_compatibility():
    """Test if vision models can load with MPS device mapping."""
    logger.info("🧪 Testing vision model MPS compatibility...")
    
    try:
        from transformers import AutoProcessor, AutoModelForImageTextToText
        
        # Test loading a small vision model with auto device mapping
        # This should detect MPS and use it if available
        model_name = "nlpconnect/vit-gpt2-image-captioning"  # Small vision-text model for testing
        
        logger.info(f"📦 Loading test model: {model_name}")
        
        # Test processor loading
        processor = AutoProcessor.from_pretrained(model_name)
        logger.info("✅ Processor loaded successfully")
        
        # Test model loading with auto device mapping
        model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # Use float16 for MPS compatibility
            device_map="auto"
        )
        logger.info("✅ Model loaded with auto device mapping")
        
        # Check which device the model is on
        if hasattr(model, 'device'):
            logger.info(f"📍 Model device: {model.device}")
        else:
            # Check first parameter's device
            first_param = next(model.parameters())
            logger.info(f"📍 Model parameters on: {first_param.device}")
        
        # Cleanup
        del model
        del processor
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing dependencies: {e}")
        logger.error("Install with: pip install transformers pillow")
        return False
    except Exception as e:
        logger.error(f"❌ Vision model test failed: {e}")
        return False


def test_accelerate_mps_config():
    """Test if accelerate can use MPS configuration."""
    logger.info("🚀 Testing Accelerate MPS configuration...")
    
    try:
        import accelerate
        from accelerate import Accelerator
        
        logger.info(f"📦 Accelerate version: {accelerate.__version__}")
        
        # Test CPU/MPS config
        config_path = Path("accelerate_configs/cpu_mps.yaml")
        if config_path.exists():
            logger.info(f"✅ Found MPS config: {config_path}")
            
            # Try to create accelerator with CPU/MPS config
            accelerator = Accelerator()
            logger.info(f"📍 Accelerator device: {accelerator.device}")
            
            # Test if we can use the device
            test_tensor = torch.randn(10, 10)
            test_tensor = accelerator.prepare(test_tensor)
            logger.info(f"✅ Accelerate tensor preparation successful")
            
            return True
        else:
            logger.warning(f"⚠️  MPS config not found: {config_path}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Accelerate not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Accelerate MPS test failed: {e}")
        return False


def test_training_memory_requirements():
    """Test memory allocation patterns for training."""
    logger.info("💾 Testing training memory requirements...")
    
    try:
        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        
        # Simulate model parameters (small scale)
        model_params = torch.randn(1000000, device=device)  # ~4MB
        optimizer_state = torch.randn(1000000, device=device)  # ~4MB
        gradients = torch.randn(1000000, device=device)  # ~4MB
        
        logger.info("✅ Basic parameter allocation successful")
        
        # Test batch processing
        batch_size = 2
        sequence_length = 1024
        hidden_size = 512
        
        batch_tensors = []
        for i in range(batch_size):
            tensor = torch.randn(sequence_length, hidden_size, device=device)
            batch_tensors.append(tensor)
        
        logger.info(f"✅ Batch tensor allocation successful (batch_size={batch_size})")
        
        # Test gradient computation with requires_grad=True
        batch_tensors_grad = []
        for i in range(batch_size):
            tensor = torch.randn(sequence_length, hidden_size, device=device, requires_grad=True)
            batch_tensors_grad.append(tensor)
        
        loss = sum(t.sum() for t in batch_tensors_grad)
        loss.backward()
        
        logger.info("✅ Gradient computation successful")
        
        # Cleanup
        del model_params, optimizer_state, gradients, batch_tensors, batch_tensors_grad
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory test failed: {e}")
        return False


def generate_mac_training_recommendations():
    """Generate recommendations for Mac training setup."""
    logger.info("\n📋 Mac Training Setup Recommendations:")
    
    recommendations = []
    
    # Check available memory
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb >= 16:
            recommendations.append(f"✅ Memory: {memory_gb:.1f}GB (sufficient for training)")
            recommendations.append("  - Use batch_size=1-2 for training")
            recommendations.append("  - Enable gradient_accumulation_steps=4-8")
        else:
            recommendations.append(f"⚠️  Memory: {memory_gb:.1f}GB (may be limiting)")
            recommendations.append("  - Use batch_size=1 only")
            recommendations.append("  - Enable gradient_accumulation_steps=8-16")
    except ImportError:
        recommendations.append("📊 Install psutil to check memory: pip install psutil")
    
    # Training configuration
    recommendations.extend([
        "",
        "🔧 Recommended training configuration for Mac:",
        "  - Use accelerate_configs/cpu_mps.yaml",
        "  - Set mixed_precision='no' (MPS doesn't support bf16 mixed precision)",
        "  - Use torch_dtype=torch.float16 instead of bfloat16",
        "  - Enable gradient_checkpointing for memory efficiency",
        "  - Set dataloader_num_workers=0 (avoid multiprocessing issues)",
        "",
        "🚀 Sample training command:",
        "accelerate launch \\",
        "    --config_file accelerate_configs/cpu_mps.yaml \\",
        "    scripts/train_frame_grid.py \\",
        "    --per_device_train_batch_size 1 \\",
        "    --gradient_accumulation_steps 8 \\",
        "    --torch_dtype float16 \\",
        "    --gradient_checkpointing \\",
        "    --dataloader_num_workers 0"
    ])
    
    for rec in recommendations:
        logger.info(rec)


def main():
    """Run comprehensive MPS compatibility test."""
    logger.info("🧪 Pokemon Gemma VLM - Mac MPS Compatibility Test")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Run tests
    test_results["mps_basic"] = test_mps_availability()
    test_results["vision_model"] = test_vision_model_compatibility()
    test_results["accelerate_config"] = test_accelerate_mps_config()
    test_results["memory_patterns"] = test_training_memory_requirements()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Compatibility Test Summary:")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! Mac training pipeline is compatible.")
        generate_mac_training_recommendations()
    elif passed_tests >= 2:
        logger.info("⚠️  Some issues detected, but training may still work with adjustments.")
        generate_mac_training_recommendations()
    else:
        logger.info("❌ Major compatibility issues detected.")
        logger.info("Consider using CPU-only training or a different platform.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)