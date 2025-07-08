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