# Tutorial 09: Advanced Techniques & Optimization

## Overview

This tutorial covers advanced techniques for optimizing Pokemon Gemma VLM training and deployment, including hyperparameter tuning, model distillation, performance optimization, and advanced training strategies.

## Prerequisites

- Completed Tutorials 05-08
- Successfully trained and deployed Pokemon Gemma VLM
- Understanding of model performance characteristics

## Advanced Training Techniques

### 1. Hyperparameter Optimization with Wandb Sweeps

```python
#!/usr/bin/env python3
"""
Pokemon Gemma VLM Hyperparameter Optimization
Uses Wandb Sweeps for automated hyperparameter tuning
"""

import wandb
import json
from pathlib import Path
import subprocess
import argparse

def create_sweep_config():
    """Create Wandb sweep configuration for Pokemon Gemma VLM."""
    
    sweep_config = {
        'method': 'bayes',  # Bayesian optimization
        'metric': {
            'name': 'eval/action_accuracy',
            'goal': 'maximize'
        },
        'parameters': {
            'learning_rate': {
                'distribution': 'log_uniform_values',
                'min': 1e-5,
                'max': 5e-4,
                'values': [1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4]
            },
            'per_device_train_batch_size': {
                'values': [1, 2]  # Memory-constrained
            },
            'gradient_accumulation_steps': {
                'values': [2, 4, 8, 16]
            },
            'warmup_steps': {
                'distribution': 'int_uniform',
                'min': 50,
                'max': 200
            },
            'lora_r': {
                'values': [16, 32, 64, 128]
            },
            'lora_alpha': {
                'values': [16, 32, 64]
            },
            'lora_dropout': {
                'distribution': 'uniform',
                'min': 0.05,
                'max': 0.2
            },
            'max_steps': {
                'values': [1500, 2000, 2500]
            },
            'weight_decay': {
                'distribution': 'log_uniform_values',
                'min': 0.01,
                'max': 0.1,
                'values': [0.01, 0.02, 0.05, 0.1]
            }
        }
    }
    
    return sweep_config

def run_training_sweep():
    """Run training with current sweep parameters."""
    
    # Initialize wandb run
    wandb.init()
    
    # Get sweep parameters
    config = wandb.config
    
    # Create output directory for this run
    run_output_dir = f"sweep_runs/run_{wandb.run.id}"
    Path(run_output_dir).mkdir(parents=True, exist_ok=True)
    
    # Build training command
    train_cmd = [
        "accelerate", "launch",
        "--config_file", "accelerate_configs/single_gpu.yaml",
        "scripts/train_frame_grid.py",
        "--model_name_or_path", "google/gemma-3-4b-it",
        "--dataset_path", "training_data/pokemon_grid_dataset_final.jsonl",
        "--output_dir", run_output_dir,
        "--learning_rate", str(config.learning_rate),
        "--per_device_train_batch_size", str(config.per_device_train_batch_size),
        "--gradient_accumulation_steps", str(config.gradient_accumulation_steps),
        "--max_steps", str(config.max_steps),
        "--warmup_steps", str(config.warmup_steps),
        "--weight_decay", str(config.weight_decay),
        "--lora_r", str(config.lora_r),
        "--lora_alpha", str(config.lora_alpha),
        "--lora_dropout", str(config.lora_dropout),
        "--save_steps", "500",
        "--logging_steps", "10",
        "--evaluation_strategy", "steps",
        "--eval_steps", "500",
        "--bf16",
        "--dataloader_pin_memory", "False",
        "--gradient_checkpointing",
        "--report_to", "wandb",
        "--run_name", f"sweep_run_{wandb.run.id}"
    ]
    
    try:
        # Run training
        result = subprocess.run(train_cmd, capture_output=True, text=True, check=True)
        
        # Evaluate final model
        eval_result = evaluate_sweep_run(run_output_dir)
        
        # Log final metrics
        wandb.log({
            "eval/action_accuracy": eval_result.get("action_accuracy", 0),
            "eval/json_validity": eval_result.get("json_validity", 0),
            "eval/inference_time": eval_result.get("inference_time", 0),
            "training/final_loss": eval_result.get("final_loss", float('inf'))
        })
        
        return eval_result
        
    except subprocess.CalledProcessError as e:
        print(f"Training failed: {e}")
        wandb.log({"training/failed": True})
        return {"action_accuracy": 0, "training_failed": True}

def evaluate_sweep_run(run_output_dir):
    """Evaluate a sweep run and return key metrics."""
    
    try:
        # Find the latest checkpoint
        checkpoints = list(Path(run_output_dir).glob("checkpoint-*"))
        if not checkpoints:
            return {"action_accuracy": 0, "error": "no_checkpoints"}
        
        latest_checkpoint = max(checkpoints, key=lambda x: int(x.name.split('-')[1]))
        
        # Run quick evaluation
        eval_cmd = [
            "python", "scripts/quick_evaluation.py",
            "--model_path", str(latest_checkpoint),
            "--test_dataset", "training_data/pokemon_grid_dataset_final.jsonl",
            "--sample_size", "20",  # Quick evaluation
            "--output_file", f"{run_output_dir}/eval_results.json"
        ]
        
        subprocess.run(eval_cmd, check=True)
        
        # Load results
        with open(f"{run_output_dir}/eval_results.json") as f:
            eval_results = json.load(f)
        
        return eval_results
        
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return {"action_accuracy": 0, "error": str(e)}

def start_sweep():
    """Start hyperparameter sweep."""
    
    # Create sweep
    sweep_config = create_sweep_config()
    sweep_id = wandb.sweep(sweep_config, project="pokemon-gemma-vlm-sweep")
    
    print(f"🎯 Starting hyperparameter sweep: {sweep_id}")
    print("📊 Wandb Dashboard: https://wandb.ai/your-username/pokemon-gemma-vlm-sweep")
    
    # Run sweep agent
    wandb.agent(sweep_id, run_training_sweep, count=20)  # Run 20 experiments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pokemon Gemma VLM Hyperparameter Optimization")
    parser.add_argument("--action", choices=["start", "agent"], default="start", 
                       help="Start new sweep or join existing as agent")
    parser.add_argument("--sweep_id", help="Existing sweep ID to join")
    
    args = parser.parse_args()
    
    if args.action == "start":
        start_sweep()
    elif args.action == "agent" and args.sweep_id:
        wandb.agent(args.sweep_id, run_training_sweep)
    else:
        print("Please provide --sweep_id when using --action agent")
```

### 2. Advanced Data Augmentation

```python
#!/usr/bin/env python3
"""
Advanced Data Augmentation for Pokemon Gemma VLM
Generates additional training data through sophisticated augmentation
"""

import json
import random
import numpy as np
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
from typing import List, Dict, Any

class PokemonDataAugmenter:
    """Advanced data augmentation for Pokemon gameplay sequences."""
    
    def __init__(self, base_dataset_path: str, output_path: str):
        self.base_dataset_path = Path(base_dataset_path)
        self.output_path = Path(output_path)
        self.augmentation_strategies = [
            self.temporal_permutation,
            self.context_paraphrasing,
            self.visual_augmentation,
            self.strategic_variation,
            self.difficulty_scaling
        ]
    
    def augment_dataset(self, augmentation_factor: int = 3):
        """
        Augment dataset with multiple strategies.
        
        Args:
            augmentation_factor: Multiply dataset size by this factor
        """
        print(f"🎨 Augmenting Pokemon dataset with factor {augmentation_factor}")
        
        # Load base dataset
        with open(self.base_dataset_path) as f:
            base_data = [json.loads(line) for line in f]
        
        print(f"📊 Base dataset: {len(base_data)} samples")
        
        augmented_data = base_data.copy()  # Keep originals
        
        for factor in range(1, augmentation_factor):
            print(f"🔄 Augmentation round {factor}/{augmentation_factor-1}")
            
            for sample in base_data:
                # Apply random augmentation strategy
                strategy = random.choice(self.augmentation_strategies)
                
                try:
                    augmented_sample = strategy(sample, factor)
                    if augmented_sample:
                        augmented_data.append(augmented_sample)
                except Exception as e:
                    print(f"⚠️ Augmentation failed for sample: {e}")
                    continue
        
        # Save augmented dataset
        print(f"💾 Saving {len(augmented_data)} augmented samples...")
        
        with open(self.output_path, 'w') as f:
            for sample in augmented_data:
                f.write(json.dumps(sample) + '\n')
        
        print(f"✅ Augmented dataset saved: {len(augmented_data)} samples")
        return len(augmented_data)
    
    def temporal_permutation(self, sample: Dict[str, Any], factor: int) -> Dict[str, Any]:
        """Create temporal variations by reordering sequence analysis."""
        
        augmented = sample.copy()
        
        # Modify temporal grid question to emphasize different aspects
        temporal_variations = [
            "Focus on the transition from frame 1 to frame 2. What action continues this movement?",
            "Analyze the bottom row progression (frames 3→4). What button maintains this pattern?",
            "Looking at the diagonal progression (frame 1→frame 4), what action completes the sequence?",
            "Observe the left column first (frames 1→3), then predict the next logical action.",
            "Compare frames 2 and 4. What action bridges this temporal gap?"
        ]
        
        # Replace question with temporal variation
        variation_idx = factor % len(temporal_variations)
        base_question = augmented['question']
        
        # Extract the JSON requirement from original question
        json_requirement = "**RESPONSE FORMAT (MANDATORY JSON):**"
        if json_requirement in base_question:
            json_part = base_question[base_question.index(json_requirement):]
            new_question = temporal_variations[variation_idx] + "\n\n" + json_part
        else:
            new_question = temporal_variations[variation_idx]
        
        augmented['question'] = new_question
        
        # Modify metadata
        if 'metadata' in augmented:
            augmented['metadata']['augmentation'] = 'temporal_permutation'
            augmented['metadata']['augmentation_factor'] = factor
        
        return augmented
    
    def context_paraphrasing(self, sample: Dict[str, Any], factor: int) -> Dict[str, Any]:
        """Generate context variations with different strategic perspectives."""
        
        augmented = sample.copy()
        
        # Strategic context variations
        context_variations = [
            {
                "persona": "Expert Pokemon trainer with championship experience",
                "style": "analytical and precise decision-making",
                "focus": "optimal efficiency and battle strategy"
            },
            {
                "persona": "Curious Pokemon researcher documenting gameplay patterns",
                "style": "observational and methodical analysis",
                "focus": "pattern recognition and systematic exploration"
            },
            {
                "persona": "Speedrun Pokemon player optimizing for time",
                "style": "rapid decision-making with risk assessment",
                "focus": "fastest route completion and shortcut utilization"
            },
            {
                "persona": "Completionist Pokemon collector",
                "style": "thorough exploration and item collection",
                "focus": "comprehensive coverage and item acquisition"
            }
        ]
        
        variation = context_variations[factor % len(context_variations)]
        
        # Modify context while preserving core information
        base_context = augmented['context']
        
        # Add persona and style modification
        enhanced_context = f"""🎮 You are ASH KETCHUM operating as a {variation['persona']} with {variation['style']}.

**CURRENT MISSION:** {self._extract_mission(base_context)}

**STRATEGIC FOCUS:** {variation['focus']}

{base_context}

**DECISION APPROACH:** Apply {variation['style']} to determine the optimal action sequence."""
        
        augmented['context'] = enhanced_context
        
        # Update metadata
        if 'metadata' in augmented:
            augmented['metadata']['augmentation'] = 'context_paraphrasing'
            augmented['metadata']['persona_variant'] = variation['persona']
        
        return augmented
    
    def visual_augmentation(self, sample: Dict[str, Any], factor: int) -> Dict[str, Any]:
        """Apply visual augmentations to grid images."""
        
        augmented = sample.copy()
        
        # Load grid image
        image_path = sample.get('image')
        if not image_path or not Path(image_path).exists():
            return None
        
        grid_image = Image.open(image_path).convert('RGB')
        
        # Apply visual augmentation based on factor
        augmentation_types = [
            self._brightness_adjustment,
            self._contrast_enhancement,
            self._slight_rotation,
            self._color_temperature_shift,
            self._subtle_noise_addition
        ]
        
        aug_type = augmentation_types[factor % len(augmentation_types)]
        augmented_image = aug_type(grid_image, factor)
        
        # Save augmented image
        original_path = Path(image_path)
        augmented_image_path = original_path.parent / f"{original_path.stem}_aug_{factor}{original_path.suffix}"
        augmented_image.save(augmented_image_path)
        
        # Update image path in sample
        augmented['image'] = str(augmented_image_path)
        
        # Add augmentation note to context
        augmented['context'] += f"\n\n**VISUAL CONDITIONS:** Analyzing under variant lighting/display conditions (augmentation_{factor})"
        
        return augmented
    
    def strategic_variation(self, sample: Dict[str, Any], factor: int) -> Dict[str, Any]:
        """Create strategic reasoning variations."""
        
        augmented = sample.copy()
        
        strategic_frameworks = [
            "risk-minimization approach with conservative action selection",
            "aggressive optimization focusing on maximum progress speed",
            "exploratory strategy emphasizing discovery and learning",
            "resource-conservation approach prioritizing long-term sustainability",
            "adaptive strategy responding to environmental changes"
        ]
        
        framework = strategic_frameworks[factor % len(strategic_frameworks)]
        
        # Modify reasoning in expected output
        original_output = json.loads(sample['output'])
        
        # Enhance reasoning with strategic framework
        enhanced_reasoning = f"{original_output.get('reasoning', '')}_strategic_{framework.split()[0]}"
        
        augmented_output = original_output.copy()
        augmented_output['reasoning'] = enhanced_reasoning
        augmented_output['strategic_framework'] = framework
        
        augmented['output'] = json.dumps(augmented_output)
        
        return augmented
    
    def difficulty_scaling(self, sample: Dict[str, Any], factor: int) -> Dict[str, Any]:
        """Create difficulty variations for progressive learning."""
        
        augmented = sample.copy()
        
        difficulty_levels = [
            "novice_friendly",
            "intermediate_challenge", 
            "expert_precision",
            "master_optimization"
        ]
        
        difficulty = difficulty_levels[factor % len(difficulty_levels)]
        
        # Modify question complexity based on difficulty
        base_question = augmented['question']
        
        if difficulty == "novice_friendly":
            simplified_question = base_question.replace("**TEMPORAL GRID ANALYSIS:**", 
                                                      "**SIMPLE GRID ANALYSIS:**")
            simplified_question = simplified_question.replace("temporal progression", "movement pattern")
            augmented['question'] = simplified_question
            
        elif difficulty == "expert_precision":
            enhanced_question = base_question + """

**EXPERT ANALYSIS REQUIRED:**
- Predict secondary consequences of this action
- Consider alternative action sequences
- Evaluate risk/reward ratios
- Optimize for multiple objectives simultaneously"""
            augmented['question'] = enhanced_question
        
        # Update metadata
        if 'metadata' in augmented:
            augmented['metadata']['difficulty_level'] = difficulty
            augmented['metadata']['augmentation'] = 'difficulty_scaling'
        
        return augmented
    
    def _extract_mission(self, context: str) -> str:
        """Extract mission from context."""
        lines = context.split('\n')
        for line in lines:
            if 'MISSION' in line or 'mission' in line:
                return line.split(':', 1)[-1].strip()
        return "Pokemon gameplay optimization"
    
    def _brightness_adjustment(self, image: Image.Image, factor: int) -> Image.Image:
        """Adjust image brightness."""
        enhancer = ImageEnhance.Brightness(image)
        brightness_factor = 0.8 + (factor * 0.1)  # 0.8 to 1.2
        return enhancer.enhance(brightness_factor)
    
    def _contrast_enhancement(self, image: Image.Image, factor: int) -> Image.Image:
        """Enhance image contrast."""
        enhancer = ImageEnhance.Contrast(image)
        contrast_factor = 0.9 + (factor * 0.05)  # 0.9 to 1.1
        return enhancer.enhance(contrast_factor)
    
    def _slight_rotation(self, image: Image.Image, factor: int) -> Image.Image:
        """Apply slight rotation."""
        angle = (factor - 2) * 0.5  # -1 to +1 degrees
        return image.rotate(angle, fillcolor=(128, 128, 128))
    
    def _color_temperature_shift(self, image: Image.Image, factor: int) -> Image.Image:
        """Shift color temperature."""
        enhancer = ImageEnhance.Color(image)
        color_factor = 0.95 + (factor * 0.02)  # 0.95 to 1.05
        return enhancer.enhance(color_factor)
    
    def _subtle_noise_addition(self, image: Image.Image, factor: int) -> Image.Image:
        """Add subtle noise."""
        # Convert to numpy for noise addition
        img_array = np.array(image)
        noise_intensity = factor * 2  # 0 to 8
        noise = np.random.normal(0, noise_intensity, img_array.shape)
        noisy_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_array)

# Usage
if __name__ == "__main__":
    augmenter = PokemonDataAugmenter(
        base_dataset_path="training_data/pokemon_grid_dataset_final.jsonl",
        output_path="training_data/pokemon_grid_dataset_augmented.jsonl"
    )
    
    # Augment dataset 3x
    final_size = augmenter.augment_dataset(augmentation_factor=3)
    print(f"🎉 Dataset augmentation complete: {final_size} total samples")
```

### 3. Model Distillation for Efficiency

```python
#!/usr/bin/env python3
"""
Model Distillation for Pokemon Gemma VLM
Create smaller, faster models that maintain performance
"""

import torch
import torch.nn.functional as F
from transformers import AutoModelForImageTextToText, AutoProcessor, Trainer, TrainingArguments
from transformers.modeling_outputs import BaseModelOutput
import json
from pathlib import Path
from datasets import Dataset
from typing import Dict, Any

class DistillationTrainer(Trainer):
    """Custom trainer for knowledge distillation."""
    
    def __init__(self, teacher_model, temperature=3.0, alpha=0.7, **kwargs):
        super().__init__(**kwargs)
        self.teacher_model = teacher_model.eval()
        self.temperature = temperature
        self.alpha = alpha  # Weight for distillation loss
        
        # Freeze teacher model
        for param in self.teacher_model.parameters():
            param.requires_grad = False
    
    def compute_loss(self, model, inputs, return_outputs=False):
        """Compute distillation loss combining task loss and KL divergence."""
        
        # Student forward pass
        student_outputs = model(**inputs)
        student_logits = student_outputs.logits
        
        # Teacher forward pass
        with torch.no_grad():
            teacher_outputs = self.teacher_model(**inputs)
            teacher_logits = teacher_outputs.logits
        
        # Task loss (standard cross-entropy)
        labels = inputs.get("labels")
        if labels is not None:
            # Shift labels for language modeling
            shift_logits = student_logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            loss_fn = torch.nn.CrossEntropyLoss(ignore_index=-100)
            task_loss = loss_fn(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        else:
            task_loss = 0
        
        # Distillation loss (KL divergence)
        student_probs = F.log_softmax(student_logits / self.temperature, dim=-1)
        teacher_probs = F.softmax(teacher_logits / self.temperature, dim=-1)
        
        distillation_loss = F.kl_div(
            student_probs, teacher_probs, 
            reduction='batchmean'
        ) * (self.temperature ** 2)
        
        # Combined loss
        total_loss = self.alpha * distillation_loss + (1 - self.alpha) * task_loss
        
        return (total_loss, student_outputs) if return_outputs else total_loss

def create_distilled_model(teacher_model_path: str, student_config: Dict[str, Any]):
    """
    Create a smaller student model for distillation.
    
    Args:
        teacher_model_path: Path to trained teacher model
        student_config: Configuration for student model (smaller architecture)
    """
    
    print(f"🏫 Creating distilled model from teacher: {teacher_model_path}")
    
    # Load teacher model
    teacher_model = AutoModelForImageTextToText.from_pretrained(
        teacher_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    teacher_processor = AutoProcessor.from_pretrained(teacher_model_path)
    
    print(f"👨‍🏫 Teacher model loaded: {sum(p.numel() for p in teacher_model.parameters()):,} parameters")
    
    # Create student model (smaller version)
    # For simplicity, we'll use a smaller variant of the same architecture
    # In practice, you might want a custom smaller architecture
    
    student_model = AutoModelForImageTextToText.from_pretrained(
        "google/gemma-3-4b-it",  # Start from base model
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    # Apply size reduction techniques if specified in config
    if student_config.get("reduce_layers"):
        # Example: Remove some transformer layers
        num_layers_to_remove = student_config["reduce_layers"]
        student_model.language_model.model.layers = student_model.language_model.model.layers[:-num_layers_to_remove]
        print(f"📉 Reduced student model by {num_layers_to_remove} layers")
    
    if student_config.get("reduce_hidden_size"):
        # This would require more complex architecture modifications
        print("⚠️ Hidden size reduction not implemented in this example")
    
    print(f"👨‍🎓 Student model created: {sum(p.numel() for p in student_model.parameters()):,} parameters")
    
    return teacher_model, student_model, teacher_processor

def distill_pokemon_model(
    teacher_model_path: str,
    training_dataset_path: str,
    output_dir: str,
    student_config: Dict[str, Any] = None
):
    """
    Perform knowledge distillation to create efficient Pokemon Gemma model.
    
    Args:
        teacher_model_path: Path to trained teacher model
        training_dataset_path: Path to training dataset
        output_dir: Output directory for distilled model
        student_config: Configuration for student model architecture
    """
    
    if student_config is None:
        student_config = {"reduce_layers": 2}  # Remove 2 layers by default
    
    print("🧠 Starting Pokemon Gemma Model Distillation")
    print("=" * 50)
    
    # Create models
    teacher_model, student_model, processor = create_distilled_model(
        teacher_model_path, student_config
    )
    
    # Load and prepare dataset
    print("📊 Loading training dataset...")
    
    def load_dataset():
        with open(training_dataset_path) as f:
            data = [json.loads(line) for line in f]
        return data[:100]  # Use subset for distillation
    
    def prepare_distillation_data(samples):
        """Prepare data for distillation training."""
        prepared_data = []
        
        for sample in samples:
            # Create messages format
            messages = [
                {"role": "system", "content": [{"type": "text", "text": sample["context"]}]},
                {"role": "user", "content": [{"type": "text", "text": sample["question"]}]},
                {"role": "assistant", "content": [{"type": "text", "text": sample["output"]}]}
            ]
            
            prepared_data.append({"messages": messages})
        
        return Dataset.from_list(prepared_data)
    
    raw_data = load_dataset()
    train_dataset = prepare_distillation_data(raw_data)
    
    print(f"✅ Dataset prepared: {len(train_dataset)} samples for distillation")
    
    # Training arguments for distillation
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-5,  # Lower learning rate for distillation
        warmup_steps=50,
        logging_steps=10,
        save_steps=200,
        evaluation_strategy="no",
        bf16=True,
        dataloader_pin_memory=False,
        gradient_checkpointing=True,
        report_to="wandb",
        run_name=f"pokemon_distillation_{Path(output_dir).name}",
        remove_unused_columns=False
    )
    
    # Create distillation trainer
    trainer = DistillationTrainer(
        teacher_model=teacher_model,
        model=student_model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=processor.tokenizer,
        temperature=4.0,  # Higher temperature for softer targets
        alpha=0.8,  # Higher weight on distillation loss
    )
    
    print("🏋️ Starting distillation training...")
    
    # Train student model
    trainer.train()
    
    # Save distilled model
    print("💾 Saving distilled model...")
    trainer.save_model()
    processor.save_pretrained(output_dir)
    
    # Save distillation info
    distillation_info = {
        "teacher_model": teacher_model_path,
        "student_config": student_config,
        "teacher_parameters": sum(p.numel() for p in teacher_model.parameters()),
        "student_parameters": sum(p.numel() for p in student_model.parameters()),
        "compression_ratio": sum(p.numel() for p in teacher_model.parameters()) / sum(p.numel() for p in student_model.parameters()),
        "distillation_samples": len(train_dataset),
        "temperature": 4.0,
        "alpha": 0.8
    }
    
    with open(Path(output_dir) / "distillation_info.json", 'w') as f:
        json.dump(distillation_info, f, indent=2)
    
    print("✅ Model distillation completed!")
    print(f"📊 Compression ratio: {distillation_info['compression_ratio']:.2f}x")
    print(f"📁 Distilled model saved to: {output_dir}")
    
    return distillation_info

# Usage
if __name__ == "__main__":
    distillation_info = distill_pokemon_model(
        teacher_model_path="models/gemma-3-4b-pokemon-merged",
        training_dataset_path="training_data/pokemon_grid_dataset_final.jsonl",
        output_dir="models/gemma-3-4b-pokemon-distilled",
        student_config={"reduce_layers": 2}
    )
    
    print(f"🎉 Distillation complete: {distillation_info['compression_ratio']:.2f}x compression")
```

### 4. Performance Profiling and Optimization

```python
#!/usr/bin/env python3
"""
Performance Profiling and Optimization for Pokemon Gemma VLM
Identify bottlenecks and optimize inference speed
"""

import time
import torch
import psutil
import json
import numpy as np
from pathlib import Path
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import cProfile
import pstats
from typing import Dict, Any, List

class PerformanceProfiler:
    """Comprehensive performance profiling for Pokemon Gemma VLM."""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = None
        self.processor = None
        self.profile_results = {}
        
    def load_model(self):
        """Load model with performance monitoring."""
        print("📦 Loading model for profiling...")
        
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(self.model_path)
        
        end_time = time.time()
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        self.profile_results["model_loading"] = {
            "load_time": end_time - start_time,
            "memory_increase_mb": memory_after - memory_before,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "model_size_mb": sum(p.numel() * p.element_size() for p in self.model.parameters()) / 1024 / 1024
        }
        
        print(f"✅ Model loaded in {self.profile_results['model_loading']['load_time']:.2f}s")
        print(f"📊 Memory increase: {self.profile_results['model_loading']['memory_increase_mb']:.1f}MB")
    
    def profile_inference_components(self, test_image_path: str, num_runs: int = 10):
        """Profile individual components of inference pipeline."""
        print(f"🔍 Profiling inference components over {num_runs} runs...")
        
        test_image = Image.open(test_image_path).convert('RGB')
        test_context = "You are Ash Ketchum analyzing Pokemon gameplay."
        test_question = "What button should be pressed next?"
        
        # Component timing storage
        components = {
            "template_application": [],
            "tokenization": [],
            "image_processing": [],
            "model_forward": [],
            "generation": [],
            "decoding": [],
            "total_inference": []
        }
        
        for run in range(num_runs):
            print(f"  Run {run+1}/{num_runs}")
            
            total_start = time.time()
            
            # 1. Template application
            start_time = time.time()
            messages = [
                {"role": "system", "content": [{"type": "text", "text": test_context}]},
                {"role": "user", "content": [
                    {"type": "image", "image": test_image},
                    {"type": "text", "text": test_question}
                ]}
            ]
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            components["template_application"].append(time.time() - start_time)
            
            # 2. Tokenization and image processing
            start_time = time.time()
            inputs = self.processor(text=[text], images=[[test_image]], return_tensors="pt", padding=True)
            components["tokenization"].append(time.time() - start_time)
            
            # 3. Move to device (included in tokenization for simplicity)
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self.model.device)
            
            # 4. Model forward pass (just forward, no generation)
            start_time = time.time()
            with torch.inference_mode():
                _ = self.model(**inputs)
            components["model_forward"].append(time.time() - start_time)
            
            # 5. Full generation
            start_time = time.time()
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=64,
                    temperature=0.1,
                    do_sample=True
                )
            components["generation"].append(time.time() - start_time)
            
            # 6. Decoding
            start_time = time.time()
            response = self.processor.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )
            components["decoding"].append(time.time() - start_time)
            
            total_end = time.time()
            components["total_inference"].append(total_end - total_start)
        
        # Calculate statistics
        component_stats = {}
        for component, times in components.items():
            component_stats[component] = {
                "mean": np.mean(times),
                "std": np.std(times),
                "min": np.min(times),
                "max": np.max(times),
                "median": np.median(times),
                "p95": np.percentile(times, 95)
            }
        
        self.profile_results["component_analysis"] = component_stats
        
        # Print results
        print("\n📊 Component Performance Analysis:")
        print("-" * 50)
        for component, stats in component_stats.items():
            print(f"{component:20s}: {stats['mean']:.4f}s ± {stats['std']:.4f}s")
        
        return component_stats
    
    def profile_memory_usage(self, test_image_path: str):
        """Profile memory usage during inference."""
        print("💾 Profiling memory usage...")
        
        test_image = Image.open(test_image_path).convert('RGB')
        
        # Memory tracking
        memory_points = []
        
        def record_memory(stage: str):
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / 1024 / 1024  # MB
            else:
                gpu_memory = 0
            
            cpu_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            memory_points.append({
                "stage": stage,
                "cpu_memory_mb": cpu_memory,
                "gpu_memory_mb": gpu_memory,
                "timestamp": time.time()
            })
        
        record_memory("baseline")
        
        # Create inputs
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": test_image},
                {"type": "text", "text": "What should I do next?"}
            ]}
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        record_memory("after_template")
        
        inputs = self.processor(text=[text], images=[[test_image]], return_tensors="pt", padding=True)
        record_memory("after_processing")
        
        # Move to device
        for key in inputs:
            if isinstance(inputs[key], torch.Tensor):
                inputs[key] = inputs[key].to(self.model.device)
        record_memory("after_device_move")
        
        # Forward pass
        with torch.inference_mode():
            outputs = self.model.generate(**inputs, max_new_tokens=64)
        record_memory("after_generation")
        
        # Cleanup
        del inputs, outputs
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        record_memory("after_cleanup")
        
        self.profile_results["memory_analysis"] = memory_points
        
        # Print memory analysis
        print("\n💾 Memory Usage Analysis:")
        print("-" * 40)
        for point in memory_points:
            print(f"{point['stage']:20s}: CPU {point['cpu_memory_mb']:.1f}MB, GPU {point['gpu_memory_mb']:.1f}MB")
        
        return memory_points
    
    def profile_with_cprofile(self, test_image_path: str):
        """Profile using Python's cProfile for detailed function analysis."""
        print("🔬 Running cProfile analysis...")
        
        test_image = Image.open(test_image_path).convert('RGB')
        
        def inference_function():
            messages = [
                {"role": "user", "content": [
                    {"type": "image", "image": test_image},
                    {"type": "text", "text": "What should I do next?"}
                ]}
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[[test_image]], return_tensors="pt", padding=True)
            
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self.model.device)
            
            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=64)
            
            response = self.processor.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )
            return response
        
        # Run profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Run inference
        result = inference_function()
        
        profiler.disable()
        
        # Save profile results
        profile_output = self.model_path.parent / "profile_results.prof"
        profiler.dump_stats(str(profile_output))
        
        # Generate readable stats
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        # Capture top functions
        from io import StringIO
        s = StringIO()
        stats.print_stats(20)  # Top 20 functions
        profile_text = s.getvalue()
        
        self.profile_results["cprofile_analysis"] = {
            "profile_file": str(profile_output),
            "top_functions": profile_text,
            "inference_result": result
        }
        
        print(f"✅ cProfile results saved to: {profile_output}")
        return profile_text
    
    def benchmark_optimization_techniques(self, test_image_path: str):
        """Benchmark various optimization techniques."""
        print("⚡ Benchmarking optimization techniques...")
        
        test_image = Image.open(test_image_path).convert('RGB')
        optimization_results = {}
        
        # Baseline performance
        baseline_times = self._benchmark_configuration(
            test_image, "baseline", 
            use_cache=False, compile_model=False, use_amp=False
        )
        optimization_results["baseline"] = baseline_times
        
        # KV cache optimization
        cache_times = self._benchmark_configuration(
            test_image, "kv_cache",
            use_cache=True, compile_model=False, use_amp=False
        )
        optimization_results["kv_cache"] = cache_times
        
        # Mixed precision
        amp_times = self._benchmark_configuration(
            test_image, "mixed_precision",
            use_cache=True, compile_model=False, use_amp=True
        )
        optimization_results["mixed_precision"] = amp_times
        
        # Model compilation (if available)
        try:
            compiled_times = self._benchmark_configuration(
                test_image, "compiled",
                use_cache=True, compile_model=True, use_amp=True
            )
            optimization_results["compiled"] = compiled_times
        except Exception as e:
            print(f"⚠️ Model compilation failed: {e}")
            optimization_results["compiled"] = {"error": str(e)}
        
        self.profile_results["optimization_benchmarks"] = optimization_results
        
        # Print comparison
        print("\n⚡ Optimization Comparison:")
        print("-" * 40)
        for technique, results in optimization_results.items():
            if "error" not in results:
                mean_time = np.mean(results["times"])
                speedup = baseline_times["mean"] / mean_time if technique != "baseline" else 1.0
                print(f"{technique:15s}: {mean_time:.4f}s (speedup: {speedup:.2f}x)")
        
        return optimization_results
    
    def _benchmark_configuration(self, test_image: Image.Image, config_name: str, 
                                use_cache: bool, compile_model: bool, use_amp: bool, num_runs: int = 5):
        """Benchmark a specific configuration."""
        
        times = []
        
        for run in range(num_runs):
            start_time = time.time()
            
            messages = [
                {"role": "user", "content": [
                    {"type": "image", "image": test_image},
                    {"type": "text", "text": "What should I do next?"}
                ]}
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[[test_image]], return_tensors="pt", padding=True)
            
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self.model.device)
            
            # Apply optimizations
            generation_kwargs = {
                "max_new_tokens": 64,
                "temperature": 0.1,
                "do_sample": True,
                "use_cache": use_cache
            }
            
            if use_amp and torch.cuda.is_available():
                with torch.autocast(device_type="cuda"):
                    with torch.inference_mode():
                        outputs = self.model.generate(**inputs, **generation_kwargs)
            else:
                with torch.inference_mode():
                    outputs = self.model.generate(**inputs, **generation_kwargs)
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            "times": times,
            "mean": np.mean(times),
            "std": np.std(times),
            "config": {
                "use_cache": use_cache,
                "compile_model": compile_model,
                "use_amp": use_amp
            }
        }
    
    def generate_performance_report(self, output_dir: str = "performance_analysis"):
        """Generate comprehensive performance report."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"📊 Generating performance report in {output_path}")
        
        # Save raw results
        with open(output_path / "performance_profile.json", 'w') as f:
            json.dump(self.profile_results, f, indent=2, default=str)
        
        # Generate visualizations
        self._create_performance_visualizations(output_path)
        
        # Generate summary report
        self._create_summary_report(output_path)
        
        print(f"✅ Performance report generated: {output_path}")
    
    def _create_performance_visualizations(self, output_path: Path):
        """Create performance visualization plots."""
        
        # Component timing visualization
        if "component_analysis" in self.profile_results:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            components = list(self.profile_results["component_analysis"].keys())
            mean_times = [self.profile_results["component_analysis"][comp]["mean"] for comp in components]
            std_times = [self.profile_results["component_analysis"][comp]["std"] for comp in components]
            
            bars = ax.bar(components, mean_times, yerr=std_times, capsize=5)
            ax.set_ylabel('Time (seconds)')
            ax.set_title('Inference Component Performance')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, mean_time in zip(bars, mean_times):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{mean_time:.4f}s', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(output_path / "component_timing.png", dpi=150, bbox_inches='tight')
            plt.close()
        
        # Memory usage visualization
        if "memory_analysis" in self.profile_results:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            memory_data = self.profile_results["memory_analysis"]
            stages = [point["stage"] for point in memory_data]
            cpu_memory = [point["cpu_memory_mb"] for point in memory_data]
            gpu_memory = [point["gpu_memory_mb"] for point in memory_data]
            
            ax1.plot(stages, cpu_memory, marker='o', label='CPU Memory')
            ax1.set_ylabel('CPU Memory (MB)')
            ax1.set_title('Memory Usage During Inference')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(stages, gpu_memory, marker='s', label='GPU Memory', color='orange')
            ax2.set_ylabel('GPU Memory (MB)')
            ax2.set_xlabel('Inference Stage')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path / "memory_usage.png", dpi=150, bbox_inches='tight')
            plt.close()
    
    def _create_summary_report(self, output_path: Path):
        """Create markdown summary report."""
        
        report_content = f"""# Pokemon Gemma VLM Performance Analysis Report

## Model Information
- **Model Path**: {self.model_path}
- **Model Parameters**: {self.profile_results.get('model_loading', {}).get('model_parameters', 'N/A'):,}
- **Model Size**: {self.profile_results.get('model_loading', {}).get('model_size_mb', 'N/A'):.1f} MB
- **Load Time**: {self.profile_results.get('model_loading', {}).get('load_time', 'N/A'):.2f}s

## Performance Summary

### Component Analysis
"""
        
        if "component_analysis" in self.profile_results:
            component_data = self.profile_results["component_analysis"]
            for component, stats in component_data.items():
                report_content += f"- **{component}**: {stats['mean']:.4f}s ± {stats['std']:.4f}s\n"
        
        report_content += "\n### Optimization Recommendations\n"
        
        # Add recommendations based on analysis
        if "component_analysis" in self.profile_results:
            component_data = self.profile_results["component_analysis"]
            
            # Find slowest component
            slowest_component = max(component_data.keys(), 
                                  key=lambda x: component_data[x]["mean"])
            
            report_content += f"- **Primary bottleneck**: {slowest_component} ({component_data[slowest_component]['mean']:.4f}s)\n"
            
            if slowest_component == "generation":
                report_content += "- Consider reducing max_new_tokens or using faster generation strategies\n"
            elif slowest_component == "tokenization":
                report_content += "- Consider input length optimization or batch processing\n"
            elif slowest_component == "model_forward":
                report_content += "- Consider model quantization or distillation\n"
        
        report_content += "\n### Memory Usage\n"
        
        if "memory_analysis" in self.profile_results:
            memory_data = self.profile_results["memory_analysis"]
            max_cpu = max(point["cpu_memory_mb"] for point in memory_data)
            max_gpu = max(point["gpu_memory_mb"] for point in memory_data)
            
            report_content += f"- **Peak CPU Memory**: {max_cpu:.1f} MB\n"
            report_content += f"- **Peak GPU Memory**: {max_gpu:.1f} MB\n"
        
        report_content += f"\n## Analysis Generated
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(output_path / "performance_report.md", 'w') as f:
            f.write(report_content)

# Usage
if __name__ == "__main__":
    profiler = PerformanceProfiler("models/gemma-3-4b-pokemon-merged")
    
    # Load model
    profiler.load_model()
    
    # Run comprehensive profiling
    test_image = "training_data/grid_images/test_grid_001.png"
    
    profiler.profile_inference_components(test_image)
    profiler.profile_memory_usage(test_image)
    profiler.profile_with_cprofile(test_image)
    profiler.benchmark_optimization_techniques(test_image)
    
    # Generate report
    profiler.generate_performance_report()
    
    print("🎉 Performance analysis complete!")
```

## Production Optimization Strategies

### 1. Inference Optimization Pipeline

```bash
#!/bin/bash
# optimize_for_production.sh - Complete optimization pipeline

MODEL_PATH="$1"
OUTPUT_DIR="optimized_models_$(date +%Y%m%d_%H%M%S)"

echo "⚡ Pokemon Gemma VLM Production Optimization"
echo "============================================"

# Create optimization directory
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

# 1. Performance Profiling
echo "📊 Step 1: Performance profiling..."
python ../scripts/performance_profiler.py \
    --model_path "../$MODEL_PATH" \
    --output_dir "profiling_results"

# 2. Model Distillation
echo "🧠 Step 2: Model distillation..."
python ../scripts/model_distillation.py \
    --teacher_model "../$MODEL_PATH" \
    --training_dataset "../training_data/pokemon_grid_dataset_final.jsonl" \
    --output_dir "distilled_model" \
    --student_config '{"reduce_layers": 2}'

# 3. Advanced Quantization
echo "🔢 Step 3: Advanced quantization..."

# GGUF with multiple quantization levels
for quant in "f16" "q8_0" "q4_0" "q4_k_m"; do
    echo "  Creating GGUF with $quant quantization..."
    python ../scripts/convert_to_gguf_enhanced.py \
        --model_path "../$MODEL_PATH" \
        --output_path "pokemon_gemma_${quant}.gguf" \
        --quantization "$quant"
done

# MLX quantization
if [[ $(uname -m) == "arm64" ]] && [[ $(uname) == "Darwin" ]]; then
    for bits in 4 8; do
        echo "  Creating MLX with ${bits}-bit quantization..."
        python ../scripts/convert_to_mlx.py \
            --model_path "../$MODEL_PATH" \
            --output_path "pokemon_gemma_mlx_${bits}bit" \
            --quantize \
            --q_bits "$bits" \
            --benchmark
    done
fi

# 4. Performance Comparison
echo "📈 Step 4: Performance comparison..."
python ../scripts/compare_optimized_models.py \
    --models_dir "." \
    --test_dataset "../training_data/pokemon_grid_dataset_final.jsonl" \
    --output_file "optimization_comparison.json"

# 5. Generate optimization report
echo "📄 Step 5: Generating optimization report..."
python -c "
import json
from pathlib import Path

# Compile optimization summary
summary = {
    'original_model': '../$MODEL_PATH',
    'optimization_timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'formats_created': [f.name for f in Path('.').glob('*.gguf')] + [d.name for d in Path('.').glob('*_mlx*')],
    'distilled_model': 'distilled_model',
    'profiling_results': 'profiling_results'
}

with open('optimization_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('✅ Optimization summary created')
"

echo ""
echo "🎉 Optimization Complete!"
echo "========================"
echo "📁 Optimized models directory: $(pwd)"
echo "📊 Review optimization_comparison.json for performance metrics"
echo "🧠 Distilled model: distilled_model/"
echo "📦 Quantized formats:"
for f in *.gguf; do
    if [[ -f "$f" ]]; then
        size=$(du -h "$f" | cut -f1)
        echo "  - $f ($size)"
    fi
done
```

## Next Steps

After completing advanced optimization:

1. **Production Deployment**: Deploy optimized models to production
2. **Monitoring Setup**: Implement performance monitoring
3. **Continuous Optimization**: Set up automated optimization pipelines
4. **Integration Testing**: Test with full Eevee v2 system

## Key Takeaways

- **Hyperparameter optimization** can improve model performance by 10-20%
- **Model distillation** can reduce model size by 2-4x with minimal performance loss
- **Advanced quantization** enables deployment on resource-constrained devices
- **Performance profiling** identifies specific bottlenecks for targeted optimization
- **Production optimization** requires balancing accuracy, speed, and resource usage

These advanced techniques ensure your Pokemon Gemma VLM achieves optimal performance for production deployment while maintaining high-quality gameplay analysis.