# Architecture Overview

## High-Level System Architecture

The project consists of multiple interconnected components organized around AI-powered Pokemon gaming:

```
┌─────────────────────────────────────────────────────────────┐
│                Root Pokemon Controller                      │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ run_step_gemini │    │ pokemon_controller.py           │ │
│  │      .py        │◄───┤ (mGBA/Quartz integration)      │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│              │                       │                     │
│              ▼                       ▼                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ gemini_api.py   │    │ Screen Capture & Input Control  │ │
│  │ (AI interface)  │    │ (PyAutoGUI + macOS Quartz)     │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  VideoGameBench Framework                   │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ main.py         │    │ VLM Agent Infrastructure        │ │
│  │ (entry point)   │◄───┤ (LiteLLM + Multi-model support)│ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│              │                       │                     │
│              ▼                       ▼                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Game Evaluators │    │ Emulator Controllers            │ │
│  │ (DOS/GB/GBA)    │    │ (PyBoy, JS-DOS, SkyEmu)        │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    SkyEmu MCP Server                        │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ skyemu_mcp_     │    │ Model Context Protocol          │ │
│  │ server.py       │◄───┤ (Claude integration tools)     │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│              │                       │                     │
│              ▼                       ▼                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ skyemu_client   │    │ HTTP Control Server             │ │
│  │     .py         │    │ (REST API for SkyEmu)          │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Interactions

### 1. Pokemon Controller (Root Level)
- **Entry Point**: `run_step_gemini.py` - Main game loop
- **AI Interface**: `gemini_api.py` - Simplified Gemini API wrapper  
- **Input Control**: `pokemon_controller.py` - mGBA emulator control via PyAutoGUI
- **Platform Integration**: macOS Quartz for window management and screen capture

### 2. VideoGameBench Framework
- **Multi-emulator support**: PyBoy (GB), JS-DOS (DOS), SkyEmu (GBA)
- **LLM abstraction**: LiteLLM for unified API access across providers
- **Game configuration**: YAML-based game configs with custom prompts
- **Evaluation pipeline**: Standardized benchmarking and logging

### 3. SkyEmu Integration
- **HTTP API**: REST interface for advanced emulator control
- **Memory reading**: Direct game state access for Pokemon data
- **MCP Protocol**: Claude-compatible tool interface
- **Save state management**: Advanced save/load functionality

### 4. Gemini Multimodal Playground
- **RL algorithms**: PyTorch-based reinforcement learning
- **Multimodal AI**: Advanced Gemini API usage patterns
- **Experimental features**: Voice control, advanced reasoning

## Data Flow Architecture

### Game State Pipeline
```
Game Screen → Screenshot → Base64 Encoding → Gemini API → Action Decision → Input Simulation → Game State Change
```

### AI Decision Making
1. **Visual Analysis**: Gemini processes game screenshots
2. **Strategic Reasoning**: AI analyzes game state and objectives  
3. **Action Selection**: Maps high-level strategy to button presses
4. **Execution**: PyAutoGUI simulates controller input
5. **Feedback Loop**: Screenshot capture for next iteration

### Memory and State Management
- **Game saves**: Pokemon save files and emulator state files
- **Session logs**: Conversation history and decision rationale
- **Screenshot archive**: Visual record of gameplay progression
- **Performance metrics**: Battle outcomes, progress tracking

## Key Architectural Patterns

### 1. Controller Pattern
- Separate controllers for different emulators (mGBA, SkyEmu)
- Abstracted input interface regardless of underlying emulator
- Platform-specific optimizations (macOS Quartz, Windows alternatives)

### 2. Strategy Pattern  
- Multiple AI agents (RL, LLM, Hybrid) with common interface
- Swappable decision-making engines
- Configuration-driven agent selection

### 3. Observer Pattern
- Game state monitoring and event logging
- Progress tracking and milestone detection
- Performance metrics collection

### 4. Adapter Pattern
- Unified LLM interface across providers (Gemini, GPT, Claude)
- Emulator abstraction for different platforms
- Cross-platform compatibility layers

## Platform-Specific Architecture (macOS)

### Native Integration
- **Quartz framework**: Window management and screen capture
- **Core Graphics**: Optimized image processing
- **Accessibility APIs**: Input simulation and window control
- **Apple Silicon**: Native performance optimization

### System Dependencies
- **PyObjC**: Python-to-Objective-C bridge
- **Cocoa APIs**: Native macOS application integration
- **Security permissions**: Accessibility and screen recording access

## Scalability Considerations

### Horizontal Scaling
- Multiple emulator instances for parallel data collection
- Distributed training across multiple machines
- Load balancing for API calls and processing

### Vertical Scaling  
- GPU acceleration for AI inference
- Memory optimization for large-scale training
- Storage optimization for gameplay data

### Performance Optimization
- Screenshot compression and caching
- API call batching and rate limiting
- Efficient memory management for long sessions