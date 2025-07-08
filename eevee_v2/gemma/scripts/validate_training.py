#!/usr/bin/env python3
"""
Pokemon Gemma VLM Training Validation Script
Tests the complete training pipeline before full training
"""

import argparse
import json
import os
import sys
import time
import torch
from pathlib import Path
from typing import Dict, Any
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TrainingValidator:
    """Validates the complete training pipeline."""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.test_results = {}
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load validation configuration."""
        default_config = {
            "model_name": "google/gemma-3-4b-it",
            "dataset_path": "training_data/pokemon_4frame_dataset_full.jsonl",
            "max_test_samples": 10,
            "test_steps": 3,
            "batch_size": 1,
            "accelerate_config": "accelerate_configs/single_gpu.yaml"
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
            default_config.update(user_config)
            
        return default_config
    
    def test_environment(self) -> bool:
        """Test the environment setup."""
        logger.info("🔍 Testing environment setup...")
        
        try:
            # Test Python imports
            import torch
            import transformers
            import trl
            import accelerate
            import datasets
            from PIL import Image
            
            logger.info(f"✅ PyTorch: {torch.__version__}")
            logger.info(f"✅ Transformers: {transformers.__version__}")
            logger.info(f"✅ TRL: {trl.__version__}")
            logger.info(f"✅ Accelerate: {accelerate.__version__}")
            
            # Test GPU availability
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                for i in range(gpu_count):
                    props = torch.cuda.get_device_properties(i)
                    memory_gb = props.total_memory / 1024**3
                    logger.info(f"✅ GPU {i}: {props.name} ({memory_gb:.1f}GB)")
            elif torch.backends.mps.is_available():
                logger.info("✅ MPS acceleration available")
            else:
                logger.warning("⚠️ No GPU acceleration available")
            
            self.test_results["environment"] = True
            return True
            
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            self.test_results["environment"] = False
            return False
    
    def test_authentication(self) -> bool:
        """Test HuggingFace authentication."""
        logger.info("🔐 Testing HuggingFace authentication...")
        
        try:
            from transformers import AutoTokenizer
            
            # Test model access
            tokenizer = AutoTokenizer.from_pretrained(self.config["model_name"])
            logger.info(f"✅ Successfully accessed {self.config['model_name']}")
            
            self.test_results["authentication"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            logger.error("Please check your HuggingFace token and model access")
            self.test_results["authentication"] = False
            return False
    
    def test_dataset(self) -> bool:
        """Test dataset loading and format."""
        logger.info("📊 Testing dataset...")
        
        try:
            dataset_path = Path(self.config["dataset_path"])
            if not dataset_path.exists():
                logger.error(f"❌ Dataset not found: {dataset_path}")
                self.test_results["dataset"] = False
                return False
            
            # Load and validate dataset format
            with open(dataset_path) as f:
                lines = f.readlines()
            
            logger.info(f"📄 Dataset size: {len(lines)} sequences")
            
            # Test first few samples
            test_samples = []
            for i, line in enumerate(lines[:self.config["max_test_samples"]]):
                try:
                    sample = json.loads(line.strip())
                    
                    # Validate required fields
                    required_fields = ["frames", "context", "question", "output"]
                    for field in required_fields:
                        if field not in sample:
                            raise ValueError(f"Missing field: {field}")
                    
                    # Validate frame count
                    if len(sample["frames"]) != 4:
                        raise ValueError(f"Expected 4 frames, got {len(sample['frames'])}")
                    
                    # Check image files exist
                    for frame_path in sample["frames"]:
                        if not Path(frame_path).exists():
                            logger.warning(f"⚠️ Image not found: {frame_path}")
                    
                    test_samples.append(sample)
                    
                except Exception as e:
                    logger.error(f"❌ Invalid sample {i}: {e}")
                    continue
            
            logger.info(f"✅ Validated {len(test_samples)} samples")
            
            # Test data loading with TRL
            from datasets import Dataset
            dataset_dict = {
                "messages": []
            }
            
            for sample in test_samples[:3]:
                # Convert to messages format
                messages = [
                    {"role": "system", "content": [{"type": "text", "text": sample["context"]}]},
                    {"role": "user", "content": [{"type": "text", "text": sample["question"]}]},
                    {"role": "assistant", "content": [{"type": "text", "text": sample["output"]}]}
                ]
                dataset_dict["messages"].append(messages)
            
            dataset = Dataset.from_dict(dataset_dict)
            logger.info(f"✅ Dataset loading successful: {len(dataset)} samples")
            
            self.test_results["dataset"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Dataset test failed: {e}")
            self.test_results["dataset"] = False
            return False
    
    def test_model_loading(self) -> bool:
        """Test model and processor loading."""
        logger.info("🤖 Testing model loading...")
        
        try:
            from transformers import AutoModelForImageTextToText, AutoProcessor
            
            # Load processor
            processor = AutoProcessor.from_pretrained(self.config["model_name"])
            logger.info("✅ Processor loaded successfully")
            
            # Load model with minimal memory
            model = AutoModelForImageTextToText.from_pretrained(
                self.config["model_name"],
                torch_dtype=torch.bfloat16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            logger.info("✅ Model loaded successfully")
            
            # Test basic forward pass
            test_text = ["Test input"]
            inputs = processor(text=test_text, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                outputs = model(**inputs)
            
            logger.info("✅ Forward pass successful")
            
            # Clean up memory
            del model
            del processor
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            self.test_results["model_loading"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            self.test_results["model_loading"] = False
            return False
    
    def test_training_script(self) -> bool:
        """Test the training script with minimal steps."""
        logger.info("🏋️ Testing training script...")
        
        try:
            # Prepare test training command
            test_output_dir = "test_training_output"
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "MODEL_NAME": self.config["model_name"],
                "DATASET_PATH": self.config["dataset_path"],
                "OUTPUT_DIR": test_output_dir,
                "MAX_STEPS": str(self.config["test_steps"]),
                "BATCH_SIZE": str(self.config["batch_size"]),
                "GRAD_ACCUM": "1",
                "LEARNING_RATE": "2e-4",
                "ACCELERATE_CONFIG": self.config["accelerate_config"]
            })
            
            # Run training script
            cmd = ["accelerate", "launch", 
                   "--config_file", self.config["accelerate_config"],
                   "scripts/sft_pokemon_gemma3.py",
                   "--dataset_name", self.config["dataset_path"],
                   "--model_name_or_path", self.config["model_name"],
                   "--per_device_train_batch_size", str(self.config["batch_size"]),
                   "--gradient_accumulation_steps", "1",
                   "--output_dir", test_output_dir,
                   "--max_steps", str(self.config["test_steps"]),
                   "--learning_rate", "2e-4",
                   "--bf16",
                   "--use_peft",
                   "--lora_target_modules", "all-linear",
                   "--report_to", "none"
                   ]
            
            logger.info(f"Running test training: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Test training completed in {duration:.1f}s")
                
                # Check output directory
                output_path = Path(test_output_dir)
                if output_path.exists():
                    files = list(output_path.glob("*"))
                    logger.info(f"✅ Training outputs: {len(files)} files created")
                
                # Clean up
                import shutil
                if output_path.exists():
                    shutil.rmtree(output_path)
                
                self.test_results["training_script"] = True
                return True
            else:
                logger.error(f"❌ Training script failed:")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                self.test_results["training_script"] = False
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Training script timeout")
            self.test_results["training_script"] = False
            return False
        except Exception as e:
            logger.error(f"❌ Training script test failed: {e}")
            self.test_results["training_script"] = False
            return False
    
    def run_full_validation(self) -> bool:
        """Run complete validation pipeline."""
        logger.info("🎮 Starting Pokemon Gemma VLM Training Validation")
        logger.info("=" * 60)
        
        tests = [
            ("Environment", self.test_environment),
            ("Authentication", self.test_authentication),
            ("Dataset", self.test_dataset),
            ("Model Loading", self.test_model_loading),
            ("Training Script", self.test_training_script)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running {test_name} test...")
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} test PASSED")
                else:
                    logger.error(f"❌ {test_name} test FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} test ERROR: {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(f"🎯 Validation Summary: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Ready for training!")
            return True
        else:
            logger.error("❌ Some tests failed. Please fix issues before training.")
            return False
    
    def generate_report(self, output_file: str = None):
        """Generate validation report."""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.config,
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(self.test_results.values()),
                "failed": len(self.test_results) - sum(self.test_results.values())
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📄 Report saved to {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Validate Pokemon Gemma VLM training setup")
    parser.add_argument("--config", help="Validation config file")
    parser.add_argument("--output", help="Output report file")
    parser.add_argument("--test", choices=["env", "auth", "dataset", "model", "training", "all"], 
                       default="all", help="Specific test to run")
    
    args = parser.parse_args()
    
    validator = TrainingValidator(args.config)
    
    if args.test == "all":
        success = validator.run_full_validation()
    else:
        test_map = {
            "env": validator.test_environment,
            "auth": validator.test_authentication,
            "dataset": validator.test_dataset,
            "model": validator.test_model_loading,
            "training": validator.test_training_script
        }
        success = test_map[args.test]()
    
    # Generate report
    if args.output:
        validator.generate_report(args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()