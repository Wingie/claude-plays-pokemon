# Tutorial 06: Training Monitoring & Evaluation

## Overview

This tutorial covers comprehensive monitoring, evaluation, and validation of Pokemon Gemma VLM training using Weights & Biases, custom metrics, and real-time performance analysis.

## Prerequisites

- Completed Tutorial 05 (Fine-tuning Process)
- Active training session or completed training run
- Wandb account configured (`wandb login`)

## Wandb Integration Setup

### 1. Environment Configuration

```bash
# Set up Wandb credentials
export WANDB_API_KEY="your_wandb_api_key"
export WANDB_PROJECT="pokemon-gemma-vlm"
export WANDB_ENTITY="your_username"

# Login to Wandb
wandb login
```

### 2. Training Script Wandb Integration

```python
# Already integrated in train_frame_grid.py
import wandb

def setup_wandb(args):
    wandb.init(
        project="pokemon-gemma-vlm",
        name=f"pokemon-gemma-grid-{timestamp}",
        config={
            "model_name": args.model_name_or_path,
            "dataset_size": 671,
            "learning_rate": args.learning_rate,
            "batch_size": args.per_device_train_batch_size,
            "max_steps": args.max_steps,
            "pan_and_scan": True
        }
    )
```

### 3. Custom Metric Logging

```python
# Enhanced logging in training script
def log_training_metrics(step, loss, lr, grad_norm, memory_usage):
    wandb.log({
        "train/loss": loss,
        "train/learning_rate": lr,
        "train/grad_norm": grad_norm,
        "system/gpu_memory_mb": memory_usage,
        "system/step": step
    })
```

## Real-time Monitoring Dashboard

### 1. Key Performance Indicators

```python
# Primary Metrics to Monitor
CRITICAL_METRICS = {
    "train_loss": {
        "target": "<0.5",
        "alert_threshold": ">2.0",
        "description": "Primary training objective"
    },
    "learning_rate": {
        "target": "warmup_schedule",
        "alert_threshold": "stuck_value",
        "description": "Optimizer learning rate"
    },
    "grad_norm": {
        "target": "<5.0",
        "alert_threshold": ">10.0",
        "description": "Gradient stability"
    },
    "gpu_memory": {
        "target": "<90%",
        "alert_threshold": ">95%",
        "description": "Memory utilization"
    }
}
```

### 2. Custom Monitoring Script

```python
#!/usr/bin/env python3
"""
Real-time Training Monitor
Tracks training metrics and alerts on anomalies
"""

import wandb
import time
import json
import subprocess
from pathlib import Path
import matplotlib.pyplot as plt

class TrainingMonitor:
    def __init__(self, wandb_run_id, alert_thresholds=None):
        self.run_id = wandb_run_id
        self.thresholds = alert_thresholds or {}
        self.api = wandb.Api()
        self.run = self.api.run(f"your_username/pokemon-gemma-vlm/{wandb_run_id}")
        
    def get_latest_metrics(self):
        """Fetch latest metrics from Wandb."""
        history = self.run.history(samples=100)
        return history.tail(1).to_dict('records')[0] if len(history) > 0 else {}
    
    def check_alerts(self, metrics):
        """Check for metric anomalies."""
        alerts = []
        
        # Loss explosion check
        if metrics.get('train/loss', 0) > 5.0:
            alerts.append("🚨 LOSS EXPLOSION: Training loss > 5.0")
        
        # Gradient explosion check
        if metrics.get('train/grad_norm', 0) > 10.0:
            alerts.append("🚨 GRADIENT EXPLOSION: Grad norm > 10.0")
        
        # Memory overflow check
        if metrics.get('system/gpu_memory_mb', 0) > 22000:  # 22GB threshold
            alerts.append("⚠️ HIGH MEMORY: GPU memory > 22GB")
        
        # Learning rate stuck check
        if metrics.get('train/learning_rate', 1) < 1e-8:
            alerts.append("⚠️ LR TOO LOW: Learning rate < 1e-8")
            
        return alerts
    
    def generate_live_plots(self, output_dir="monitoring"):
        """Generate real-time training plots."""
        Path(output_dir).mkdir(exist_ok=True)
        
        history = self.run.history()
        
        # Loss curve
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.plot(history['_step'], history['train/loss'])
        plt.title('Training Loss')
        plt.xlabel('Steps')
        plt.ylabel('Loss')
        plt.grid(True)
        
        plt.subplot(2, 2, 2)
        plt.plot(history['_step'], history['train/learning_rate'])
        plt.title('Learning Rate Schedule')
        plt.xlabel('Steps')
        plt.ylabel('Learning Rate')
        plt.grid(True)
        
        plt.subplot(2, 2, 3)
        plt.plot(history['_step'], history.get('train/grad_norm', []))
        plt.title('Gradient Norm')
        plt.xlabel('Steps')
        plt.ylabel('Grad Norm')
        plt.grid(True)
        
        plt.subplot(2, 2, 4)
        plt.plot(history['_step'], history.get('system/gpu_memory_mb', []))
        plt.title('GPU Memory Usage')
        plt.xlabel('Steps')
        plt.ylabel('Memory (MB)')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/training_dashboard.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def monitor_loop(self, interval=30):
        """Main monitoring loop."""
        print("🎮 Pokemon Gemma VLM Training Monitor Started")
        print(f"📊 Monitoring run: {self.run_id}")
        print(f"🔄 Update interval: {interval}s")
        print("-" * 50)
        
        while True:
            try:
                metrics = self.get_latest_metrics()
                alerts = self.check_alerts(metrics)
                
                # Print status
                current_step = metrics.get('_step', 0)
                current_loss = metrics.get('train/loss', 0)
                current_lr = metrics.get('train/learning_rate', 0)
                
                print(f"Step {current_step:>4d} | Loss: {current_loss:.4f} | LR: {current_lr:.2e}")
                
                # Print alerts
                for alert in alerts:
                    print(alert)
                
                # Generate plots every 10 updates
                if current_step % 100 == 0:
                    self.generate_live_plots()
                    print("📈 Dashboard updated")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(interval)

# Usage
if __name__ == "__main__":
    monitor = TrainingMonitor("your_run_id")
    monitor.monitor_loop(interval=30)
```

### 3. System Resource Monitoring

```bash
#!/bin/bash
# system_monitor.sh - Monitor system resources during training

echo "🖥️ Pokemon Gemma VLM System Monitor"
echo "=================================="

# Create monitoring log
LOG_FILE="monitoring/system_metrics_$(date +%Y%m%d_%H%M%S).log"
mkdir -p monitoring

# Header
echo "timestamp,gpu_util,gpu_memory_used,gpu_memory_total,cpu_percent,ram_used,ram_total" > "$LOG_FILE"

# Monitoring loop
while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # GPU metrics
    if command -v nvidia-smi &> /dev/null; then
        GPU_METRICS=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits)
        GPU_UTIL=$(echo "$GPU_METRICS" | awk -F', ' '{print $1}')
        GPU_MEM_USED=$(echo "$GPU_METRICS" | awk -F', ' '{print $2}')
        GPU_MEM_TOTAL=$(echo "$GPU_METRICS" | awk -F', ' '{print $3}')
    else
        GPU_UTIL="0"
        GPU_MEM_USED="0"
        GPU_MEM_TOTAL="0"
    fi
    
    # CPU and RAM metrics
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    RAM_INFO=$(free -m | grep '^Mem:')
    RAM_USED=$(echo "$RAM_INFO" | awk '{print $3}')
    RAM_TOTAL=$(echo "$RAM_INFO" | awk '{print $2}')
    
    # Log metrics
    echo "$TIMESTAMP,$GPU_UTIL,$GPU_MEM_USED,$GPU_MEM_TOTAL,$CPU_PERCENT,$RAM_USED,$RAM_TOTAL" >> "$LOG_FILE"
    
    # Console output
    echo "[$TIMESTAMP] GPU: ${GPU_UTIL}% | VRAM: ${GPU_MEM_USED}/${GPU_MEM_TOTAL}MB | CPU: ${CPU_PERCENT}% | RAM: ${RAM_USED}/${RAM_TOTAL}MB"
    
    sleep 30
done
```

## Advanced Metrics & Analysis

### 1. Pokemon-Specific Evaluation Metrics

```python
#!/usr/bin/env python3
"""
Pokemon Gemma VLM Evaluation Metrics
Specialized metrics for gaming AI performance
"""

import json
import torch
from pathlib import Path
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import numpy as np

class PokemonEvaluator:
    def __init__(self, model_path, test_dataset_path):
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path, torch_dtype=torch.bfloat16, device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.test_data = self.load_test_data(test_dataset_path)
    
    def load_test_data(self, dataset_path):
        """Load test dataset for evaluation."""
        with open(dataset_path) as f:
            return [json.loads(line) for line in f]
    
    def evaluate_action_accuracy(self, sample_size=50):
        """Evaluate button prediction accuracy."""
        correct_predictions = 0
        total_predictions = 0
        
        test_samples = self.test_data[:sample_size]
        
        for sample in test_samples:
            # Load grid image
            grid_path = sample.get('image') or sample['frames'][0]  # Handle both formats
            grid_image = Image.open(grid_path).convert('RGB')
            
            # Create test conversation
            messages = [
                {"role": "system", "content": [{"type": "text", "text": sample['context']}]},
                {"role": "user", "content": [
                    {"type": "image", "image": grid_image},
                    {"type": "text", "text": sample['question']}
                ]}
            ]
            
            # Generate prediction
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[[grid_image]], return_tensors="pt", padding=True)
            
            # Move to device
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self.model.device)
            
            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=128, temperature=0.1)
            
            response = self.processor.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )
            
            # Parse predictions
            try:
                predicted_json = json.loads(response.strip())
                expected_json = json.loads(sample['output'])
                
                # Check button accuracy
                if predicted_json.get('button') == expected_json.get('button'):
                    correct_predictions += 1
                
                total_predictions += 1
                
            except json.JSONDecodeError:
                total_predictions += 1  # Count as incorrect
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        return {
            "action_accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions
        }
    
    def evaluate_response_quality(self, sample_size=20):
        """Evaluate response formatting and completeness."""
        valid_json_count = 0
        complete_responses = 0
        total_responses = 0
        
        required_fields = ['button', 'reasoning', 'context']
        valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
        
        test_samples = self.test_data[:sample_size]
        
        for sample in test_samples:
            grid_path = sample.get('image') or sample['frames'][0]
            grid_image = Image.open(grid_path).convert('RGB')
            
            messages = [
                {"role": "system", "content": [{"type": "text", "text": sample['context']}]},
                {"role": "user", "content": [
                    {"type": "image", "image": grid_image},
                    {"type": "text", "text": sample['question']}
                ]}
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[[grid_image]], return_tensors="pt", padding=True)
            
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self.model.device)
            
            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=128, temperature=0.7)
            
            response = self.processor.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )
            
            total_responses += 1
            
            try:
                parsed_response = json.loads(response.strip())
                valid_json_count += 1
                
                # Check completeness
                has_all_fields = all(field in parsed_response for field in required_fields)
                has_valid_button = parsed_response.get('button') in valid_buttons
                
                if has_all_fields and has_valid_button:
                    complete_responses += 1
                    
            except json.JSONDecodeError:
                pass  # Invalid JSON
        
        return {
            "json_validity_rate": valid_json_count / total_responses,
            "completeness_rate": complete_responses / total_responses,
            "valid_json_count": valid_json_count,
            "complete_responses": complete_responses,
            "total_responses": total_responses
        }
    
    def evaluate_temporal_understanding(self, sample_size=30):
        """Evaluate understanding of temporal sequences."""
        temporal_accuracy = 0
        total_samples = 0
        
        # Filter samples with clear temporal progression
        temporal_samples = [s for s in self.test_data if 'grid' in s.get('image', '') or len(s.get('frames', [])) == 4][:sample_size]
        
        for sample in temporal_samples:
            grid_path = sample.get('image') or sample['frames'][0]
            grid_image = Image.open(grid_path).convert('RGB')
            
            # Test temporal understanding with modified prompt
            temporal_question = """
            Analyze the 2x2 grid showing temporal progression:
            Top-left (t=0) → Top-right (t=1) → Bottom-left (t=2) → Bottom-right (t=3)
            
            What pattern do you observe in the temporal sequence? What button should logically continue this pattern?
            """
            
            messages = [
                {"role": "system", "content": [{"type": "text", "text": sample['context']}]},
                {"role": "user", "content": [
                    {"type": "image", "image": grid_image},
                    {"type": "text", "text": temporal_question}
                ]}
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[[grid_image]], return_tensors="pt", padding=True)
            
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self.model.device)
            
            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=256, temperature=0.3)
            
            response = self.processor.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )
            
            # Check for temporal reasoning keywords
            temporal_keywords = ['progression', 'sequence', 'pattern', 'temporal', 'continuing', 'next', 'following']
            if any(keyword in response.lower() for keyword in temporal_keywords):
                temporal_accuracy += 1
            
            total_samples += 1
        
        return {
            "temporal_understanding_rate": temporal_accuracy / total_samples if total_samples > 0 else 0,
            "temporal_responses": temporal_accuracy,
            "total_temporal_samples": total_samples
        }
    
    def generate_evaluation_report(self, output_file="evaluation_report.json"):
        """Generate comprehensive evaluation report."""
        print("🧪 Running Pokemon Gemma VLM Evaluation...")
        
        # Run all evaluations
        action_metrics = self.evaluate_action_accuracy()
        quality_metrics = self.evaluate_response_quality()
        temporal_metrics = self.evaluate_temporal_understanding()
        
        # Compile report
        report = {
            "timestamp": torch.utils.data.get_worker_info() or "unknown",
            "model_path": str(self.model.config.name_or_path),
            "test_dataset_size": len(self.test_data),
            "metrics": {
                "action_accuracy": action_metrics,
                "response_quality": quality_metrics,
                "temporal_understanding": temporal_metrics
            },
            "overall_score": (
                action_metrics["action_accuracy"] * 0.5 +
                quality_metrics["completeness_rate"] * 0.3 +
                temporal_metrics["temporal_understanding_rate"] * 0.2
            )
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n📊 EVALUATION SUMMARY")
        print("=" * 40)
        print(f"Action Accuracy:       {action_metrics['action_accuracy']:.1%}")
        print(f"JSON Validity:         {quality_metrics['json_validity_rate']:.1%}")
        print(f"Response Completeness: {quality_metrics['completeness_rate']:.1%}")
        print(f"Temporal Understanding: {temporal_metrics['temporal_understanding_rate']:.1%}")
        print(f"Overall Score:         {report['overall_score']:.1%}")
        print(f"\n📄 Report saved: {output_file}")
        
        return report

# Usage
if __name__ == "__main__":
    evaluator = PokemonEvaluator(
        model_path="models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000",
        test_dataset_path="training_data/pokemon_grid_dataset_final.jsonl"
    )
    
    report = evaluator.generate_evaluation_report()
```

### 2. Training Progress Validation

```python
#!/usr/bin/env python3
"""
Training Progress Validator
Validates training effectiveness at regular intervals
"""

import json
import wandb
from pathlib import Path
import matplotlib.pyplot as plt

class TrainingValidator:
    def __init__(self, wandb_run_id, validation_interval=500):
        self.run_id = wandb_run_id
        self.validation_interval = validation_interval
        self.api = wandb.Api()
        self.run = self.api.run(f"your_username/pokemon-gemma-vlm/{wandb_run_id}")
        
    def validate_checkpoint(self, checkpoint_path, step):
        """Validate a training checkpoint."""
        from pokemon_evaluator import PokemonEvaluator
        
        evaluator = PokemonEvaluator(
            model_path=checkpoint_path,
            test_dataset_path="training_data/pokemon_grid_dataset_final.jsonl"
        )
        
        # Quick evaluation (smaller sample)
        action_metrics = evaluator.evaluate_action_accuracy(sample_size=20)
        quality_metrics = evaluator.evaluate_response_quality(sample_size=10)
        
        # Log to Wandb
        wandb.log({
            f"validation/action_accuracy": action_metrics["action_accuracy"],
            f"validation/json_validity": quality_metrics["json_validity_rate"],
            f"validation/completeness": quality_metrics["completeness_rate"],
            f"validation/step": step
        })
        
        return {
            "step": step,
            "action_accuracy": action_metrics["action_accuracy"],
            "json_validity": quality_metrics["json_validity_rate"],
            "completeness": quality_metrics["completeness_rate"]
        }
    
    def monitor_validation_checkpoints(self, output_dir):
        """Monitor and validate checkpoints as they are created."""
        output_path = Path(output_dir)
        validated_checkpoints = set()
        
        while True:
            # Find new checkpoints
            checkpoints = list(output_path.glob("checkpoint-*"))
            
            for checkpoint_dir in checkpoints:
                if checkpoint_dir.name not in validated_checkpoints:
                    step = int(checkpoint_dir.name.split('-')[1])
                    
                    if step % self.validation_interval == 0:
                        print(f"🧪 Validating checkpoint: {checkpoint_dir.name}")
                        
                        try:
                            validation_results = self.validate_checkpoint(str(checkpoint_dir), step)
                            
                            print(f"✅ Step {step} - Accuracy: {validation_results['action_accuracy']:.1%}")
                            
                            validated_checkpoints.add(checkpoint_dir.name)
                            
                        except Exception as e:
                            print(f"❌ Validation failed for {checkpoint_dir.name}: {e}")
            
            time.sleep(60)  # Check every minute

# Usage
if __name__ == "__main__":
    validator = TrainingValidator("your_run_id")
    validator.monitor_validation_checkpoints("models/gemma-3-4b-pokemon-grid-20250709")
```

## Performance Benchmarking

### 1. Inference Speed Testing

```python
#!/usr/bin/env python3
"""
Pokemon Gemma VLM Performance Benchmark
Tests inference speed and memory usage
"""

import time
import torch
import psutil
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import numpy as np

class PerformanceBenchmark:
    def __init__(self, model_path):
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path, torch_dtype=torch.bfloat16, device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(model_path)
        
    def benchmark_inference_speed(self, test_image_path, num_runs=10):
        """Benchmark inference speed."""
        test_image = Image.open(test_image_path).convert('RGB')
        
        # Warmup
        for _ in range(3):
            self._single_inference(test_image)
        
        # Timing runs
        times = []
        for i in range(num_runs):
            start_time = time.time()
            self._single_inference(test_image)
            end_time = time.time()
            times.append(end_time - start_time)
            
        return {
            "mean_inference_time": np.mean(times),
            "std_inference_time": np.std(times),
            "min_inference_time": np.min(times),
            "max_inference_time": np.max(times),
            "runs": num_runs
        }
    
    def _single_inference(self, image):
        """Perform single inference."""
        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": "What button should be pressed next?"}
            ]}
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[[image]], return_tensors="pt", padding=True)
        
        for key in inputs:
            if isinstance(inputs[key], torch.Tensor):
                inputs[key] = inputs[key].to(self.model.device)
        
        with torch.inference_mode():
            outputs = self.model.generate(**inputs, max_new_tokens=64, temperature=0.1)
        
        response = self.processor.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        return response
    
    def benchmark_memory_usage(self, test_image_path):
        """Benchmark memory usage."""
        test_image = Image.open(test_image_path).convert('RGB')
        
        # Measure GPU memory
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            initial_gpu_memory = torch.cuda.memory_allocated()
            
            self._single_inference(test_image)
            
            peak_gpu_memory = torch.cuda.max_memory_allocated()
            gpu_memory_used = peak_gpu_memory - initial_gpu_memory
        else:
            gpu_memory_used = 0
        
        # Measure CPU memory
        process = psutil.Process()
        cpu_memory_mb = process.memory_info().rss / 1024 / 1024
        
        return {
            "gpu_memory_mb": gpu_memory_used / 1024 / 1024,
            "cpu_memory_mb": cpu_memory_mb,
            "model_parameters": sum(p.numel() for p in self.model.parameters())
        }

# Usage
if __name__ == "__main__":
    benchmark = PerformanceBenchmark("models/gemma-3-4b-pokemon-grid-20250709/checkpoint-2000")
    
    speed_results = benchmark.benchmark_inference_speed("training_data/grid_images/test_grid.png")
    memory_results = benchmark.benchmark_memory_usage("training_data/grid_images/test_grid.png")
    
    print("⚡ PERFORMANCE BENCHMARK RESULTS")
    print("=" * 40)
    print(f"Mean Inference Time: {speed_results['mean_inference_time']:.3f}s")
    print(f"GPU Memory Usage:    {memory_results['gpu_memory_mb']:.1f}MB")
    print(f"Model Parameters:    {memory_results['model_parameters']:,}")
```

## Alert System Configuration

### 1. Automated Alert Scripts

```bash
#!/bin/bash
# training_alerts.sh - Automated training alert system

WANDB_RUN_ID="your_run_id"
ALERT_EMAIL="your_email@example.com"
SLACK_WEBHOOK="your_slack_webhook_url"

# Check training status
check_training_status() {
    # Get latest metrics from Wandb API
    python -c "
import wandb
api = wandb.Api()
run = api.run('your_username/pokemon-gemma-vlm/$WANDB_RUN_ID')
history = run.history(samples=1)
if len(history) > 0:
    latest = history.iloc[-1]
    print(f'LOSS:{latest.get(\"train/loss\", 0)}')
    print(f'STEP:{latest.get(\"_step\", 0)}')
    print(f'STATUS:{run.state}')
else:
    print('STATUS:no_data')
"
}

# Send alert
send_alert() {
    local message="$1"
    local severity="$2"
    
    echo "🚨 ALERT [$severity]: $message"
    
    # Slack notification
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🎮 Pokemon Gemma Training Alert: $message\"}" \
            "$SLACK_WEBHOOK"
    fi
    
    # Email notification (requires sendmail)
    if [[ -n "$ALERT_EMAIL" ]] && command -v sendmail &> /dev/null; then
        echo "Subject: Pokemon Gemma Training Alert" | \
        echo "Training Alert: $message" | \
        sendmail "$ALERT_EMAIL"
    fi
}

# Main monitoring loop
while true; do
    STATUS_OUTPUT=$(check_training_status)
    
    if echo "$STATUS_OUTPUT" | grep -q "STATUS:failed"; then
        send_alert "Training run failed" "CRITICAL"
        break
    elif echo "$STATUS_OUTPUT" | grep -q "STATUS:finished"; then
        send_alert "Training run completed successfully" "SUCCESS"
        break
    fi
    
    # Check for loss explosion
    LOSS=$(echo "$STATUS_OUTPUT" | grep "LOSS:" | cut -d':' -f2)
    if (( $(echo "$LOSS > 5.0" | bc -l) )); then
        send_alert "Loss explosion detected: $LOSS" "CRITICAL"
    fi
    
    sleep 300  # Check every 5 minutes
done
```

## Next Steps

After mastering training monitoring:

1. **Tutorial 07**: Model Evaluation & Testing
2. **Tutorial 08**: Model Deployment (GGUF/MLX conversion)
3. **Tutorial 09**: Advanced Techniques & Optimization

## Key Takeaways

- Monitor loss curves, learning rate, and gradient norms in real-time
- Use Wandb for comprehensive experiment tracking
- Implement custom Pokemon-specific evaluation metrics
- Set up automated alerts for training anomalies
- Validate checkpoints at regular intervals
- Benchmark inference speed and memory usage

Effective monitoring ensures training quality and enables early detection of issues, leading to better-trained Pokemon gaming models.