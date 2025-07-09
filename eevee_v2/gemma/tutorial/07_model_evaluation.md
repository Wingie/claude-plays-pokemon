# Tutorial 07: Model Evaluation & Testing

## Overview

This tutorial covers comprehensive evaluation and testing of trained Pokemon Gemma VLM models, including inference validation, performance benchmarking, and production readiness assessment.

## Prerequisites

- Completed Tutorial 06 (Training Monitoring)
- Trained model checkpoint available
- Test dataset prepared

## Model Evaluation Framework

### 1. Inference Testing Setup

```bash
# Test trained model on sample grids
python scripts/test_grid_inference.py \
    --model_path models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000 \
    --test_grid training_data/grid_images/validation_grid.png \
    --output_file results/inference_test.json
```

### 2. Comprehensive Evaluation Script

```python
#!/usr/bin/env python3
"""
Pokemon Gemma VLM Comprehensive Evaluation
Tests model performance across multiple dimensions
"""

import json
import torch
import time
import numpy as np
from pathlib import Path
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns

class ComprehensiveEvaluator:
    def __init__(self, model_path, test_dataset_path, output_dir="evaluation_results"):
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load model and processor
        print(f"🤖 Loading model from {model_path}")
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path, torch_dtype=torch.bfloat16, device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(model_path)
        
        # Load test dataset
        print(f"📊 Loading test dataset from {test_dataset_path}")
        with open(test_dataset_path) as f:
            self.test_data = [json.loads(line) for line in f]
        
        print(f"✅ Evaluation setup complete: {len(self.test_data)} test samples")
    
    def evaluate_action_accuracy(self, sample_size=100):
        """Evaluate button prediction accuracy."""
        print(f"🎯 Evaluating action accuracy on {sample_size} samples...")
        
        correct_predictions = 0
        total_predictions = 0
        action_distribution = {}
        error_analysis = []
        
        test_samples = self.test_data[:sample_size]
        
        for i, sample in enumerate(test_samples):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(test_samples)}")
            
            try:
                # Load grid image
                grid_path = sample.get('image') or sample['frames'][0]
                grid_image = Image.open(grid_path).convert('RGB')
                
                # Generate prediction
                prediction = self._predict_action(grid_image, sample['context'], sample['question'])
                expected = json.loads(sample['output'])
                
                # Track action distribution
                predicted_button = prediction.get('button', 'unknown')
                expected_button = expected.get('button', 'unknown')
                
                action_distribution[predicted_button] = action_distribution.get(predicted_button, 0) + 1
                
                # Check accuracy
                if predicted_button == expected_button:
                    correct_predictions += 1
                else:
                    error_analysis.append({
                        'sample_id': i,
                        'predicted': predicted_button,
                        'expected': expected_button,
                        'grid_path': str(grid_path)
                    })
                
                total_predictions += 1
                
            except Exception as e:
                print(f"    Error processing sample {i}: {e}")
                error_analysis.append({
                    'sample_id': i,
                    'error': str(e),
                    'grid_path': str(grid_path) if 'grid_path' in locals() else 'unknown'
                })
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        results = {
            "action_accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions,
            "action_distribution": action_distribution,
            "error_analysis": error_analysis
        }
        
        # Save detailed results
        with open(self.output_dir / "action_accuracy_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate visualization
        self._plot_action_distribution(action_distribution)
        
        print(f"✅ Action accuracy: {accuracy:.1%} ({correct_predictions}/{total_predictions})")
        return results
    
    def evaluate_response_quality(self, sample_size=50):
        """Evaluate response formatting and completeness."""
        print(f"📝 Evaluating response quality on {sample_size} samples...")
        
        quality_metrics = {
            'valid_json_count': 0,
            'complete_responses': 0,
            'has_reasoning': 0,
            'has_context': 0,
            'valid_button': 0
        }
        
        response_examples = []
        quality_issues = []
        
        required_fields = ['button', 'reasoning', 'context']
        valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
        
        test_samples = self.test_data[:sample_size]
        
        for i, sample in enumerate(test_samples):
            try:
                grid_path = sample.get('image') or sample['frames'][0]
                grid_image = Image.open(grid_path).convert('RGB')
                
                prediction = self._predict_action(grid_image, sample['context'], sample['question'], raw_response=True)
                
                # Parse response
                try:
                    parsed_response = json.loads(prediction['raw_response'])
                    quality_metrics['valid_json_count'] += 1
                    
                    # Check completeness
                    has_all_fields = all(field in parsed_response for field in required_fields)
                    has_valid_button = parsed_response.get('button') in valid_buttons
                    has_reasoning = len(parsed_response.get('reasoning', '')) > 10
                    has_context = len(parsed_response.get('context', '')) > 5
                    
                    if has_all_fields:
                        quality_metrics['complete_responses'] += 1
                    if has_reasoning:
                        quality_metrics['has_reasoning'] += 1
                    if has_context:
                        quality_metrics['has_context'] += 1
                    if has_valid_button:
                        quality_metrics['valid_button'] += 1
                    
                    # Collect examples
                    if len(response_examples) < 10:
                        response_examples.append({
                            'sample_id': i,
                            'response': parsed_response,
                            'quality_score': sum([has_all_fields, has_valid_button, has_reasoning, has_context]) / 4
                        })
                        
                except json.JSONDecodeError as e:
                    quality_issues.append({
                        'sample_id': i,
                        'issue': 'invalid_json',
                        'raw_response': prediction.get('raw_response', '')[:200],
                        'error': str(e)
                    })
                    
            except Exception as e:
                quality_issues.append({
                    'sample_id': i,
                    'issue': 'processing_error',
                    'error': str(e)
                })
        
        # Calculate rates
        total_samples = len(test_samples)
        results = {
            "json_validity_rate": quality_metrics['valid_json_count'] / total_samples,
            "completeness_rate": quality_metrics['complete_responses'] / total_samples,
            "reasoning_quality_rate": quality_metrics['has_reasoning'] / total_samples,
            "context_quality_rate": quality_metrics['has_context'] / total_samples,
            "button_validity_rate": quality_metrics['valid_button'] / total_samples,
            "total_samples": total_samples,
            "quality_metrics": quality_metrics,
            "response_examples": response_examples,
            "quality_issues": quality_issues
        }
        
        # Save results
        with open(self.output_dir / "response_quality_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Response quality - JSON: {results['json_validity_rate']:.1%}, Complete: {results['completeness_rate']:.1%}")
        return results
    
    def evaluate_inference_speed(self, num_runs=20):
        """Benchmark inference speed and resource usage."""
        print(f"⚡ Benchmarking inference speed over {num_runs} runs...")
        
        # Use a representative test image
        test_sample = self.test_data[0]
        grid_path = test_sample.get('image') or test_sample['frames'][0]
        test_image = Image.open(grid_path).convert('RGB')
        
        # Warmup runs
        print("  Performing warmup runs...")
        for _ in range(3):
            self._predict_action(test_image, test_sample['context'], test_sample['question'])
        
        # Timing runs
        print("  Running benchmark...")
        times = []
        memory_usage = []
        
        for i in range(num_runs):
            # Measure memory before
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                memory_before = torch.cuda.memory_allocated()
            
            # Time inference
            start_time = time.time()
            self._predict_action(test_image, test_sample['context'], test_sample['question'])
            end_time = time.time()
            
            # Measure memory after
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                memory_after = torch.cuda.memory_allocated()
                memory_usage.append((memory_after - memory_before) / 1024 / 1024)  # MB
            
            times.append(end_time - start_time)
        
        results = {
            "mean_inference_time": np.mean(times),
            "std_inference_time": np.std(times),
            "min_inference_time": np.min(times),
            "max_inference_time": np.max(times),
            "median_inference_time": np.median(times),
            "p95_inference_time": np.percentile(times, 95),
            "mean_memory_usage_mb": np.mean(memory_usage) if memory_usage else 0,
            "std_memory_usage_mb": np.std(memory_usage) if memory_usage else 0,
            "num_runs": num_runs,
            "all_times": times,
            "all_memory_usage": memory_usage
        }
        
        # Save results
        with open(self.output_dir / "inference_speed_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate visualization
        self._plot_inference_times(times)
        
        print(f"✅ Mean inference time: {results['mean_inference_time']:.3f}s ± {results['std_inference_time']:.3f}s")
        return results
    
    def evaluate_temporal_understanding(self, sample_size=30):
        """Evaluate understanding of temporal sequences."""
        print(f"🕐 Evaluating temporal understanding on {sample_size} samples...")
        
        temporal_scores = []
        temporal_examples = []
        
        # Focus on grid samples with clear temporal progression
        grid_samples = [s for s in self.test_data if 'grid' in s.get('image', '')][:sample_size]
        
        for i, sample in enumerate(grid_samples):
            try:
                grid_path = sample.get('image') or sample['frames'][0]
                grid_image = Image.open(grid_path).convert('RGB')
                
                # Test with temporal analysis prompt
                temporal_question = """
                Analyze this 2x2 temporal grid showing Pokemon gameplay progression:
                
                ┌─────────┬─────────┐
                │ Frame 1 │ Frame 2 │  ← Earlier moments
                │ (t=0)   │ (t=1)   │
                ├─────────┼─────────┤
                │ Frame 3 │ Frame 4 │  ← Later moments
                │ (t=2)   │ (t=3)   │
                └─────────┴─────────┘
                
                1. What temporal pattern do you observe across the frames?
                2. What action sequence is being executed?
                3. What button should logically continue this temporal progression?
                
                Respond in JSON format with your temporal analysis.
                """
                
                prediction = self._predict_action(grid_image, sample['context'], temporal_question, raw_response=True)
                
                # Score temporal understanding
                response_text = prediction.get('raw_response', '').lower()
                temporal_keywords = [
                    'temporal', 'progression', 'sequence', 'pattern', 'continuing',
                    'frame 1', 'frame 2', 'frame 3', 'frame 4', 'earlier', 'later',
                    't=0', 't=1', 't=2', 't=3', 'movement', 'action sequence'
                ]
                
                keyword_score = sum(1 for keyword in temporal_keywords if keyword in response_text)
                temporal_score = min(keyword_score / len(temporal_keywords), 1.0)
                temporal_scores.append(temporal_score)
                
                # Collect examples
                if len(temporal_examples) < 5:
                    temporal_examples.append({
                        'sample_id': i,
                        'temporal_score': temporal_score,
                        'response': response_text[:300],
                        'grid_path': str(grid_path)
                    })
                    
            except Exception as e:
                print(f"    Error processing temporal sample {i}: {e}")
                temporal_scores.append(0.0)
        
        results = {
            "mean_temporal_score": np.mean(temporal_scores),
            "std_temporal_score": np.std(temporal_scores),
            "temporal_understanding_rate": np.mean([s > 0.3 for s in temporal_scores]),
            "total_temporal_samples": len(temporal_scores),
            "temporal_examples": temporal_examples,
            "all_scores": temporal_scores
        }
        
        # Save results
        with open(self.output_dir / "temporal_understanding_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Temporal understanding rate: {results['temporal_understanding_rate']:.1%}")
        return results
    
    def _predict_action(self, image, context, question, raw_response=False):
        """Generate action prediction for given image and context."""
        messages = [
            {"role": "system", "content": [{"type": "text", "text": context}]},
            {"role": "user", "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": question}
            ]}
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[[image]], return_tensors="pt", padding=True)
        
        # Move to device
        for key in inputs:
            if isinstance(inputs[key], torch.Tensor):
                inputs[key] = inputs[key].to(self.model.device)
        
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=128,
                temperature=0.1,
                do_sample=True,
                top_p=0.9
            )
        
        response = self.processor.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        
        if raw_response:
            return {'raw_response': response}
        
        # Parse JSON response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {'button': 'unknown', 'reasoning': 'parse_error', 'context': 'error'}
    
    def _plot_action_distribution(self, action_distribution):
        """Plot action prediction distribution."""
        plt.figure(figsize=(10, 6))
        actions = list(action_distribution.keys())
        counts = list(action_distribution.values())
        
        plt.bar(actions, counts)
        plt.title('Predicted Action Distribution')
        plt.xlabel('Actions')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.output_dir / "action_distribution.png", dpi=150, bbox_inches='tight')
        plt.close()
    
    def _plot_inference_times(self, times):
        """Plot inference time distribution."""
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.hist(times, bins=20, alpha=0.7)
        plt.title('Inference Time Distribution')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Frequency')
        
        plt.subplot(2, 2, 2)
        plt.plot(times)
        plt.title('Inference Time Over Runs')
        plt.xlabel('Run Number')
        plt.ylabel('Time (seconds)')
        
        plt.subplot(2, 2, 3)
        plt.boxplot(times)
        plt.title('Inference Time Box Plot')
        plt.ylabel('Time (seconds)')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "inference_times.png", dpi=150, bbox_inches='tight')
        plt.close()
    
    def generate_comprehensive_report(self):
        """Generate comprehensive evaluation report."""
        print("\n🎮 Pokemon Gemma VLM - Comprehensive Evaluation")
        print("=" * 60)
        
        # Run all evaluations
        action_results = self.evaluate_action_accuracy(sample_size=100)
        quality_results = self.evaluate_response_quality(sample_size=50)
        speed_results = self.evaluate_inference_speed(num_runs=20)
        temporal_results = self.evaluate_temporal_understanding(sample_size=30)
        
        # Calculate overall score
        overall_score = (
            action_results["action_accuracy"] * 0.4 +
            quality_results["completeness_rate"] * 0.3 +
            temporal_results["temporal_understanding_rate"] * 0.2 +
            min(1.0, 1.0 / max(speed_results["mean_inference_time"], 0.1)) * 0.1
        )
        
        # Compile comprehensive report
        report = {
            "model_path": str(self.model_path),
            "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_dataset_size": len(self.test_data),
            "results": {
                "action_accuracy": action_results,
                "response_quality": quality_results,
                "inference_speed": speed_results,
                "temporal_understanding": temporal_results
            },
            "overall_score": overall_score,
            "summary": {
                "action_accuracy": f"{action_results['action_accuracy']:.1%}",
                "json_validity": f"{quality_results['json_validity_rate']:.1%}",
                "completeness": f"{quality_results['completeness_rate']:.1%}",
                "temporal_understanding": f"{temporal_results['temporal_understanding_rate']:.1%}",
                "mean_inference_time": f"{speed_results['mean_inference_time']:.3f}s",
                "overall_score": f"{overall_score:.1%}"
            }
        }
        
        # Save comprehensive report
        with open(self.output_dir / "comprehensive_evaluation_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n📊 EVALUATION SUMMARY")
        print("-" * 40)
        print(f"Action Accuracy:       {report['summary']['action_accuracy']}")
        print(f"JSON Validity:         {report['summary']['json_validity']}")
        print(f"Response Completeness: {report['summary']['completeness']}")
        print(f"Temporal Understanding: {report['summary']['temporal_understanding']}")
        print(f"Mean Inference Time:   {report['summary']['mean_inference_time']}")
        print(f"Overall Score:         {report['summary']['overall_score']}")
        
        print(f"\n📄 Detailed results saved to: {self.output_dir}")
        print(f"📈 Visualizations generated in: {self.output_dir}")
        
        return report

# Usage
if __name__ == "__main__":
    evaluator = ComprehensiveEvaluator(
        model_path="models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000",
        test_dataset_path="training_data/pokemon_grid_dataset_final.jsonl"
    )
    
    comprehensive_report = evaluator.generate_comprehensive_report()
```

### 3. Model Comparison Framework

```python
#!/usr/bin/env python3
"""
Model Comparison Framework
Compare multiple checkpoints or model variants
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

class ModelComparator:
    def __init__(self, models_config):
        """
        models_config: dict of {model_name: model_path}
        """
        self.models = models_config
        self.results = {}
    
    def compare_models(self, test_dataset_path, output_dir="comparison_results"):
        """Compare multiple models on the same test set."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"🔄 Comparing {len(self.models)} models...")
        
        for model_name, model_path in self.models.items():
            print(f"\n📊 Evaluating {model_name}...")
            
            evaluator = ComprehensiveEvaluator(
                model_path=model_path,
                test_dataset_path=test_dataset_path,
                output_dir=output_path / model_name
            )
            
            self.results[model_name] = evaluator.generate_comprehensive_report()
        
        # Generate comparison report
        self._generate_comparison_report(output_path)
        return self.results
    
    def _generate_comparison_report(self, output_dir):
        """Generate model comparison report."""
        # Extract key metrics for comparison
        comparison_data = []
        
        for model_name, result in self.results.items():
            summary = result['summary']
            comparison_data.append({
                'Model': model_name,
                'Action Accuracy': float(summary['action_accuracy'].strip('%')) / 100,
                'JSON Validity': float(summary['json_validity'].strip('%')) / 100,
                'Completeness': float(summary['completeness'].strip('%')) / 100,
                'Temporal Understanding': float(summary['temporal_understanding'].strip('%')) / 100,
                'Inference Time (s)': float(summary['mean_inference_time'].strip('s')),
                'Overall Score': float(summary['overall_score'].strip('%')) / 100
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Save comparison table
        df.to_csv(output_dir / "model_comparison.csv", index=False)
        
        # Generate comparison visualizations
        self._plot_model_comparison(df, output_dir)
        
        # Find best model
        best_model = df.loc[df['Overall Score'].idxmax(), 'Model']
        
        print(f"\n🏆 Best performing model: {best_model}")
        print(f"📊 Comparison results saved to: {output_dir}")
    
    def _plot_model_comparison(self, df, output_dir):
        """Create comparison visualizations."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()
        
        metrics = ['Action Accuracy', 'JSON Validity', 'Completeness', 
                  'Temporal Understanding', 'Inference Time (s)', 'Overall Score']
        
        for i, metric in enumerate(metrics):
            ax = axes[i]
            bars = ax.bar(df['Model'], df[metric])
            ax.set_title(metric)
            ax.set_xlabel('Model')
            ax.set_ylabel(metric)
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_dir / "model_comparison.png", dpi=150, bbox_inches='tight')
        plt.close()

# Usage for checkpoint comparison
if __name__ == "__main__":
    models_to_compare = {
        "Checkpoint-1000": "models/gemma-3-4b-pokemon-grid-20250709/checkpoint-1000",
        "Checkpoint-1500": "models/gemma-3-4b-pokemon-grid-20250709/checkpoint-1500",
        "Checkpoint-2000": "models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000"
    }
    
    comparator = ModelComparator(models_to_compare)
    results = comparator.compare_models("training_data/pokemon_grid_dataset_final.jsonl")
```

## Production Readiness Assessment

### 1. Production Readiness Checklist

```python
#!/usr/bin/env python3
"""
Production Readiness Assessment
Validates model meets production requirements
"""

import json
import torch
from pathlib import Path

class ProductionReadinessAssessment:
    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.requirements = {
            "action_accuracy": 0.85,      # 85% minimum
            "json_validity": 0.95,        # 95% valid JSON
            "completeness": 0.90,         # 90% complete responses
            "inference_time": 1.0,        # <1s inference
            "memory_usage": 8000,         # <8GB GPU memory
            "temporal_understanding": 0.7  # 70% temporal reasoning
        }
        
    def assess_production_readiness(self, evaluation_report):
        """Assess if model meets production requirements."""
        print("🏭 Production Readiness Assessment")
        print("=" * 50)
        
        assessment = {
            "overall_ready": True,
            "requirements_met": {},
            "requirements_failed": {},
            "recommendations": []
        }
        
        results = evaluation_report["results"]
        
        # Check each requirement
        checks = [
            ("action_accuracy", results["action_accuracy"]["action_accuracy"]),
            ("json_validity", results["response_quality"]["json_validity_rate"]),
            ("completeness", results["response_quality"]["completeness_rate"]),
            ("inference_time", results["inference_speed"]["mean_inference_time"]),
            ("temporal_understanding", results["temporal_understanding"]["temporal_understanding_rate"])
        ]
        
        for requirement, actual_value in checks:
            required_value = self.requirements[requirement]
            
            if requirement == "inference_time":
                # Lower is better for inference time
                meets_requirement = actual_value <= required_value
            else:
                # Higher is better for other metrics
                meets_requirement = actual_value >= required_value
            
            if meets_requirement:
                assessment["requirements_met"][requirement] = {
                    "required": required_value,
                    "actual": actual_value,
                    "status": "PASS"
                }
                print(f"✅ {requirement}: {actual_value:.3f} (required: {required_value})")
            else:
                assessment["requirements_failed"][requirement] = {
                    "required": required_value,
                    "actual": actual_value,
                    "status": "FAIL",
                    "gap": abs(actual_value - required_value)
                }
                assessment["overall_ready"] = False
                print(f"❌ {requirement}: {actual_value:.3f} (required: {required_value})")
                
                # Generate recommendations
                if requirement == "action_accuracy":
                    assessment["recommendations"].append("Increase training data or training steps")
                elif requirement == "json_validity":
                    assessment["recommendations"].append("Improve output formatting in training data")
                elif requirement == "inference_time":
                    assessment["recommendations"].append("Consider model quantization or architecture optimization")
                elif requirement == "temporal_understanding":
                    assessment["recommendations"].append("Enhance temporal reasoning in training prompts")
        
        # Overall assessment
        if assessment["overall_ready"]:
            print(f"\n🎉 Model is PRODUCTION READY!")
        else:
            print(f"\n⚠️ Model is NOT production ready. Address failed requirements.")
            print("\n📋 Recommendations:")
            for rec in assessment["recommendations"]:
                print(f"  • {rec}")
        
        # Save assessment
        with open(self.model_path.parent / "production_readiness_assessment.json", 'w') as f:
            json.dump(assessment, f, indent=2)
        
        return assessment
```

### 2. Automated Testing Pipeline

```bash
#!/bin/bash
# automated_evaluation.sh - Complete model evaluation pipeline

MODEL_PATH="$1"
TEST_DATASET="$2"
OUTPUT_DIR="evaluation_$(date +%Y%m%d_%H%M%S)"

if [[ -z "$MODEL_PATH" ]] || [[ -z "$TEST_DATASET" ]]; then
    echo "Usage: $0 <model_path> <test_dataset>"
    exit 1
fi

echo "🧪 Starting automated evaluation pipeline"
echo "Model: $MODEL_PATH"
echo "Dataset: $TEST_DATASET"
echo "Output: $OUTPUT_DIR"
echo "=================================="

# Create output directory
mkdir -p "$OUTPUT_DIR"

# 1. Basic inference test
echo "📝 Running basic inference test..."
python scripts/test_grid_inference.py \
    --model_path "$MODEL_PATH" \
    --test_grid training_data/grid_images/test_grid_001.png \
    --output_file "$OUTPUT_DIR/basic_inference.json"

# 2. Comprehensive evaluation
echo "📊 Running comprehensive evaluation..."
python scripts/comprehensive_evaluation.py \
    --model_path "$MODEL_PATH" \
    --test_dataset "$TEST_DATASET" \
    --output_dir "$OUTPUT_DIR"

# 3. Performance benchmark
echo "⚡ Running performance benchmark..."
python scripts/benchmark_performance.py \
    --model_path "$MODEL_PATH" \
    --output_file "$OUTPUT_DIR/performance_benchmark.json"

# 4. Production readiness assessment
echo "🏭 Assessing production readiness..."
python scripts/production_assessment.py \
    --model_path "$MODEL_PATH" \
    --evaluation_report "$OUTPUT_DIR/comprehensive_evaluation_report.json" \
    --output_file "$OUTPUT_DIR/production_assessment.json"

# 5. Generate summary report
echo "📄 Generating summary report..."
python -c "
import json
from pathlib import Path

output_dir = Path('$OUTPUT_DIR')
summary = {
    'model_path': '$MODEL_PATH',
    'evaluation_completed': True,
    'files_generated': [str(f.name) for f in output_dir.glob('*.json')],
    'plots_generated': [str(f.name) for f in output_dir.glob('*.png')]
}

with open(output_dir / 'evaluation_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('✅ Evaluation pipeline completed')
print(f'📁 Results available in: {output_dir}')
"

echo ""
echo "🎯 Evaluation Complete!"
echo "📁 Results: $OUTPUT_DIR"
echo "📊 View comprehensive_evaluation_report.json for detailed results"
echo "🏭 Check production_assessment.json for deployment readiness"
```

## Integration Testing

### 1. End-to-End Integration Test

```python
#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests model integration with Eevee v2 architecture
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path for Eevee imports
sys.path.append(str(Path(__file__).parent.parent.parent))

class EeveeIntegrationTest:
    def __init__(self, model_path):
        self.model_path = model_path
        
    def test_eevee_integration(self):
        """Test integration with Eevee v2 system."""
        print("🔌 Testing Eevee v2 Integration")
        print("-" * 40)
        
        integration_results = {
            "model_loading": False,
            "inference_compatibility": False,
            "response_format": False,
            "performance_acceptable": False,
            "overall_integration": False
        }
        
        try:
            # Test 1: Model loading compatibility
            print("1. Testing model loading compatibility...")
            from scripts.test_grid_inference import test_grid_inference
            
            test_result = test_grid_inference(
                model_path=self.model_path,
                test_grid="training_data/grid_images/test_grid_001.png",
                output_file=None
            )
            
            if test_result and test_result.get("success"):
                integration_results["model_loading"] = True
                print("   ✅ Model loads successfully")
            else:
                print("   ❌ Model loading failed")
                
        except Exception as e:
            print(f"   ❌ Model loading error: {e}")
        
        # Additional integration tests would go here...
        
        # Overall assessment
        integration_results["overall_integration"] = all(integration_results.values())
        
        if integration_results["overall_integration"]:
            print("\n🎉 Integration tests PASSED - Ready for Eevee v2 deployment")
        else:
            print("\n⚠️ Integration tests FAILED - Address issues before deployment")
        
        return integration_results
```

## Next Steps

After completing model evaluation:

1. **Tutorial 08**: Model Deployment (GGUF/MLX conversion)
2. **Tutorial 09**: Advanced Techniques & Optimization
3. **Production Deployment**: Deploy validated model to production

## Key Evaluation Metrics

- **Action Accuracy**: >85% for production readiness
- **JSON Validity**: >95% properly formatted responses
- **Response Completeness**: >90% complete responses
- **Inference Speed**: <1s per prediction
- **Temporal Understanding**: >70% temporal reasoning

## Troubleshooting Evaluation Issues

### Common Problems

1. **Low Action Accuracy**:
   - Check training data quality
   - Increase training steps
   - Adjust learning rate

2. **Poor JSON Formatting**:
   - Improve training data formatting
   - Add output format validation
   - Use consistent templates

3. **Slow Inference**:
   - Enable model quantization
   - Optimize batch processing
   - Consider model distillation

4. **Memory Issues**:
   - Reduce batch size
   - Use gradient checkpointing
   - Consider model pruning

A comprehensive evaluation ensures your Pokemon Gemma VLM meets production requirements and performs reliably in real gaming scenarios.