# Claude Plays Pokemon - AI Gaming System

## Project Overview

This repository contains a comprehensive AI gaming system for Pokemon, featuring multiple generations of AI agents and experimental frameworks for autonomous gameplay.

## Project Structure

### Main Components

#### **eevee/** - Eevee v1 (Current Production)
- **Purpose**: AI Pokemon task execution through pure prompt engineering
- **Architecture**: Monolithic agent with visual intelligence and multi-provider LLM API
- **Key Features**: 
  - Zero-hallucination spatial understanding
  - Multi-provider vision (Mistral Pixtral, Gemini 2.0 Flash)
  - Continuous learning through template improvement
  - Interactive and one-shot task modes
- **Usage**: `python run_eevee.py --task "navigate to Pokemon Center"`

#### **eevee_v2/** - Eevee v2 (Next-Generation Architecture)
- **Purpose**: Constraint-driven, layered architecture for real-time AI gameplay
- **Architecture**: Separated execution/strategic/memory layers
- **Key Innovation**: Architectural separation with pause/resume control
- **Status**: Development phase - implementing execution layer
- **Target**: 60 FPS gameplay with unlimited reasoning time

##### **eevee_v2/gemma/** - Gemma VLM Training System
- **Purpose**: Fine-tune Gemma 3/3n VLMs for 4-frame Pokemon temporal sequences
- **Architecture**: TRL-based multi-image training with QLoRA optimization
- **Key Features**:
  - 4-frame temporal sequence processing (960ms Pokemon gameplay)
  - 32K context utilization for rich game state (Ash persona + party + inventory)
  - JSON button output format: `{"button": "right", "reasoning": "clear_path", "context": "navigation"}`
  - Behavioral cloning from Eevee v1 expert demonstrations
- **Models**: Gemma 3-4B (fast) and Gemma 3n-9B (high quality) variants
- **Training**: Leverages existing TRL multi-image implementation for Pokemon-specific adaptation

#### **Core Infrastructure**
- **SkyEmu/**: Game Boy Advance emulator integration
- **gemini-multimodal-playground/**: Gemini API experiments
- **skyemu-mcp/**: Model Context Protocol server for SkyEmu
- **videogamebench/**: Gaming AI benchmarking framework

## Development Commands

### Eevee v1 (Production)
```bash
# Interactive continuous gameplay
python eevee/run_eevee.py

# One-shot task execution
python eevee/run_eevee.py --task "check my Pokemon party status"

# Testing with memory systems
python eevee/run_eevee.py --task "test compact memory" --max-turns 1 --neo4j-memory --verbose
```

### Eevee v2 (Development)
```bash
# Navigate to v2 directory
cd eevee_v2

# Gemma VLM Training (New)
cd eevee_v2/gemma

# Convert Eevee v1 data to 4-frame sequences
python scripts/convert_eevee_data.py \
    --input_dir ../../eevee/data \
    --output_file training_data/pokemon_4frame_dataset.jsonl \
    --copy_images

# Train Gemma 3-4B VLM (faster)
bash scripts/train_gemma3.sh

# Train Gemma 3n-9B VLM (higher quality)
bash scripts/train_gemma3n.sh

# Test trained model inference
python scripts/test_inference.py \
    --model_path models/gemma-3-4b-pokemon-4frame \
    --test_images "training_data/images/seq_000000_frame_*.png"
```


## Technical Architecture

### Eevee v1 Architecture
```
EeveeAgent (game control) → PromptManager (AI templates) → LLM API (multi-provider) → ContinuousGameplay (learning loop)
```

### Eevee v2 Architecture
```
EXECUTION LAYER (≤5ms):     Pattern Match → Cached Action → Execute
STRATEGIC LAYER (unlimited): Deep Reasoning → Plan Generation → Cache Update
MEMORY LAYER (async):       Background Updates → Knowledge Integration
```

## Performance Constraints

### Eevee v1 (Current)
- **Reasoning Pipeline**: 100-300ms per decision
- **Target**: Interactive gameplay with learning
- **Status**: Production ready, continuous improvement

### Eevee v2 (Target)
- **Real-time Constraint**: 60 FPS = 16.7ms budget per frame
- **Execution Layer**: ≤5ms per frame
- **Strategic Layer**: Unlimited time (pause-based)
- **Memory Layer**: Async background updates

## Command Memories

- Ran command: `python run_eevee.py --task "test compact memory" --max-turns 1 --neo4j-memory --verbose`