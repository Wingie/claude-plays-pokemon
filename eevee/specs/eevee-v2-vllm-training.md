# Eevee v2 - VLLM Training Data Collection System
## Technical Specification

**Version**: 2.0  
**Status**: Planning Phase  
**Dependencies**: Eevee v1 (Complete)  
**Target**: VLLM Fine-tuning Pipeline for Pokemon AI Agents

---

## Overview

Eevee v2 extends the successful v1 implementation with sophisticated training data collection capabilities. The system will capture complete gameplay sessions, decompose them into training examples, and provide human feedback scoring for reinforcement learning optimization.

### Core Objectives

1. **Training Data Generation**: Capture high-quality Pokemon gameplay sessions in VLLM-compatible format
2. **Step-Limited Execution**: Provide `--steps` parameter for controlled run length
3. **RL Scoring System**: Human-in-the-loop 1-10 scoring for goal achievement
4. **VLLM Compatibility**: Generate instruction tuning datasets for Mistral and similar models
5. **Run Management**: Organized storage and retrieval of training sessions

---

## System Architecture

### Enhanced CLI Interface

```bash
# Basic training data collection
python run_eevee.py "check healing items in bag" --steps=15 --save-training-data

# Advanced training session
python run_eevee.py "battle gym leader" --steps=50 --training-session gym-battle-001 --collect-screenshots

# Batch training data generation
python run_eevee.py --training-mode --task-file tasks.yaml --max-sessions=100
```

### New Command Line Parameters

- `--steps=N`: Limit execution to N steps maximum
- `--save-training-data`: Enable training data collection mode
- `--training-session=NAME`: Specify custom session identifier
- `--collect-screenshots`: Save all screenshots for visual analysis
- `--training-mode`: Batch mode for multiple training sessions
- `--task-file=PATH`: YAML file with predefined tasks for batch collection

---

## Training Data Format

### VLLM Instruction Tuning Format

```json
{
  "instruction": "Check what healing items I have in my bag",
  "input": {
    "game_state": {
      "screenshot_base64": "...",
      "memory_context": "Currently in Pokemon Center, party has 3 Pokemon",
      "previous_actions": ["pressed_start", "navigated_to_bag"]
    },
    "task_context": {
      "step_number": 5,
      "total_steps": 15,
      "goal": "Inventory analysis and reporting"
    }
  },
  "output": {
    "action": "press_down",
    "reasoning": "Navigate to Items section in bag menu to check healing items",
    "expected_outcome": "Menu cursor moves to Items category"
  },
  "metadata": {
    "session_id": "healing-items-001",
    "timestamp": "2025-06-18T10:22:06Z",
    "model_used": "gemini-flash-2.0-exp",
    "success": true,
    "human_score": 8
  }
}
```

### Training Session Structure

```json
{
  "session_metadata": {
    "session_id": "healing-items-001",
    "task_description": "check what healing items I have in my bag",
    "start_time": "2025-06-18T10:22:00Z",
    "end_time": "2025-06-18T10:22:45Z",
    "total_steps": 12,
    "max_steps": 15,
    "final_score": 8,
    "task_completed": true
  },
  "execution_trace": [
    {
      "step": 1,
      "screenshot": "base64_encoded_image",
      "ai_analysis": "Player is in Pokemon Center, need to open bag",
      "action_taken": "press_start",
      "success": true,
      "timestamp": "2025-06-18T10:22:01Z"
    }
  ],
  "final_result": {
    "task_outcome": "Successfully identified 3 Potions, 2 Super Potions, 1 Full Heal",
    "completion_status": "success",
    "human_feedback": "Correctly identified all healing items, efficient navigation",
    "score_justification": "Task completed successfully but took slightly longer than optimal"
  }
}
```

---

## Runs Directory Structure

```
runs/
├── session_20250618_102200_healing-items-001/
│   ├── session_metadata.json          # Session overview and scoring
│   ├── execution_trace.json           # Complete step-by-step trace
│   ├── training_data.jsonl            # VLLM-ready training examples
│   ├── screenshots/                   # All captured screenshots
│   │   ├── step_01_before_action.png
│   │   ├── step_01_after_action.png
│   │   └── ...
│   ├── memory_snapshots/              # Memory system state
│   │   ├── before_session.db
│   │   └── after_session.db
│   └── analysis/                      # AI reasoning and performance
│       ├── prompt_variations.json
│       └── error_analysis.json
├── session_20250618_103000_gym-battle-002/
└── batch_training_20250618/           # Batch collection results
    ├── summary_report.json
    ├── aggregated_training_data.jsonl
    └── performance_metrics.json
```

---

## Step-Limited Execution System

### Implementation Strategy

```python
class StepLimitedExecutor:
    def __init__(self, max_steps: int):
        self.max_steps = max_steps
        self.current_step = 0
        self.execution_trace = []
        
    def execute_step(self, action: str) -> bool:
        if self.current_step >= self.max_steps:
            return False  # Step limit reached
        
        # Execute action and record
        result = self.perform_action(action)
        self.record_step(action, result)
        self.current_step += 1
        
        return True
    
    def record_step(self, action: str, result: dict):
        step_data = {
            "step": self.current_step + 1,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "screenshot": self.capture_screenshot()
        }
        self.execution_trace.append(step_data)
```

### Step Budget Management

- **Soft Limits**: Warn when approaching step limit
- **Hard Limits**: Stop execution at exact step count
- **Adaptive Limits**: Adjust based on task complexity
- **Emergency Extension**: Allow override for critical completion

---

## RL Scoring System

### Human-in-the-Loop Scoring Interface

```python
class RLScoringSystem:
    def collect_human_feedback(self, session_data: dict) -> int:
        """Present session results and collect 1-10 score"""
        
        print(f"Task: {session_data['task_description']}")
        print(f"Result: {session_data['final_result']}")
        print(f"Steps Used: {session_data['steps_used']}/{session_data['max_steps']}")
        
        # Display key screenshots
        self.show_before_after_screenshots(session_data)
        
        while True:
            try:
                score = int(input("Rate task completion (1-10): "))
                if 1 <= score <= 10:
                    break
                print("Please enter a score between 1 and 10")
            except ValueError:
                print("Please enter a valid number")
        
        # Optional detailed feedback
        feedback = input("Additional feedback (optional): ")
        
        return {
            "score": score,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
```

### Scoring Criteria Guidelines

**Score 9-10**: Perfect execution
- Task completed successfully
- Optimal path taken
- No unnecessary actions
- Clear, accurate reporting

**Score 7-8**: Good execution  
- Task completed successfully
- Minor inefficiencies
- Good overall strategy

**Score 5-6**: Acceptable execution
- Task mostly completed
- Some errors or confusion
- Achieved basic objectives

**Score 3-4**: Poor execution
- Task partially completed
- Significant errors
- Inefficient approach

**Score 1-2**: Failed execution
- Task not completed
- Major errors or failure
- Unable to achieve objectives

---

## VLLM Training Integration

### Dataset Preparation Pipeline

```python
class VLLMDatasetBuilder:
    def __init__(self, runs_directory: str):
        self.runs_dir = runs_directory
        
    def build_instruction_dataset(self, filter_score: int = 6) -> list:
        """Build VLLM instruction tuning dataset from high-quality runs"""
        
        dataset = []
        for session_dir in self.get_session_directories():
            session_data = self.load_session_data(session_dir)
            
            # Filter by quality score
            if session_data['final_score'] < filter_score:
                continue
                
            # Convert to instruction format
            examples = self.convert_to_instruction_format(session_data)
            dataset.extend(examples)
        
        return dataset
    
    def export_for_vllm(self, dataset: list, output_path: str):
        """Export dataset in VLLM-compatible format"""
        
        with open(output_path, 'w') as f:
            for example in dataset:
                f.write(json.dumps(example) + '\n')
```

### Training Data Quality Metrics

- **Completion Rate**: Percentage of tasks successfully completed
- **Efficiency Score**: Steps used vs. optimal path
- **Consistency**: Similar tasks should have similar approaches
- **Coverage**: Diversity of game states and scenarios
- **Human Approval**: Average human scoring across sessions

---

## Implementation Phases

### Phase 2.1: Core Infrastructure (Week 1)
- [ ] Implement `--steps` parameter and step-limited execution
- [ ] Design and create runs/ directory structure
- [ ] Build basic training data collection framework
- [ ] Implement human scoring interface

### Phase 2.2: Data Format & Export (Week 2)
- [ ] Design VLLM-compatible training data format
- [ ] Implement session data export functionality
- [ ] Build dataset aggregation and filtering tools
- [ ] Create quality metrics and validation

### Phase 2.3: Batch Processing & Analytics (Week 3)
- [ ] Implement batch training mode
- [ ] Build performance analytics dashboard
- [ ] Create automated quality assessment
- [ ] Implement data visualization tools

### Phase 2.4: VLLM Integration & Testing (Week 4)
- [ ] Integrate with VLLM fine-tuning pipeline
- [ ] Comprehensive testing with various Pokemon scenarios
- [ ] Performance benchmarking and optimization
- [ ] Documentation and deployment guides

---

## Technical Requirements

### System Dependencies
- **Eevee v1**: Complete implementation required
- **SkyEmu**: Running emulator instance on port 8080
- **Python 3.8+**: Core runtime environment
- **SQLite**: Enhanced for training data storage
- **PIL/Pillow**: Screenshot processing and optimization
- **VLLM**: Model serving and fine-tuning integration

### Storage Requirements
- **Per Session**: ~10-50 MB (screenshots + metadata)
- **100 Sessions**: ~1-5 GB total storage
- **Batch Collection**: Consider SSD for performance

### Performance Considerations
- **Screenshot Compression**: Balance quality vs. storage
- **Memory Management**: Cleanup between sessions
- **Parallel Processing**: Multiple session collection
- **API Rate Limiting**: Gemini API usage optimization

---

## Success Metrics

### Primary Metrics
- **Training Data Quality**: Average human score > 7/10
- **Dataset Size**: 1000+ high-quality training examples
- **Task Coverage**: 50+ distinct Pokemon task types
- **VLLM Performance**: Fine-tuned model outperforms base model

### Secondary Metrics
- **Collection Efficiency**: Sessions per hour
- **Storage Optimization**: MB per training example
- **Human Annotation Time**: Minutes per session scoring
- **System Reliability**: Successful session completion rate

---

## Risk Assessment & Mitigation

### Technical Risks
- **Storage Growth**: Large screenshot datasets
  - *Mitigation*: Compression and cleanup policies
- **API Costs**: Extensive Gemini usage
  - *Mitigation*: Caching and batch optimization
- **Data Quality**: Inconsistent human scoring
  - *Mitigation*: Scoring guidelines and validation

### Operational Risks
- **Manual Scoring Burden**: Time-intensive human feedback
  - *Mitigation*: Batch scoring interface and guidelines
- **Session Failures**: Incomplete training data
  - *Mitigation*: Robust error handling and recovery

---

## Future Enhancements

### Phase 3: Advanced Features
- **Automated Scoring**: ML-based quality assessment
- **Active Learning**: Intelligent task selection for training
- **Multi-Model Training**: Support for various VLLM architectures
- **Distributed Collection**: Multi-instance training data generation
- **Real-time Analytics**: Live training data quality monitoring

### Integration Opportunities
- **Pokemon Showdown**: Battle simulation training data
- **ROM Hacking**: Custom scenario generation
- **Community Collection**: Crowdsourced training sessions
- **Research Collaboration**: Academic dataset sharing

---

This specification provides the foundation for transforming Eevee v1 into a powerful VLLM training data collection platform, enabling the development of highly specialized Pokemon AI agents through supervised fine-tuning and human feedback optimization.