# Pokemon Fire Red VideoGameBench Enhancement
## Product Requirements Document

**Project**: Pokemon Fire Red AI Task Execution with Eevee v1 & VLLM Training Pipeline  
**Location**: `/Users/wingston/code/claude-plays-pokemon`  
**Status**: Phase 1 Complete - Eevee v1 Operational  
**Current Goal**: Implement VLLM training data collection and RL scoring system (Eevee v2)

---

## Executive Summary

**Phase 1 Complete**: Successfully implemented Eevee v1, an advanced AI task execution system that provides natural language interface for Pokemon game automation. The system integrates with SkyEmu emulator and features persistent memory, multi-step task decomposition, and comprehensive reporting capabilities.

**Phase 2 Objective**: Enhance Eevee v1 with VLLM training data collection, step-limited execution, and RL scoring system to generate high-quality training datasets for Pokemon-specific AI model fine-tuning.

## Current State & Next Phase

**Phase 1 Achievements** ✅:
- **Eevee v1 Operational**: Full natural language task execution system
- **SkyEmu Integration**: HTTP API control for Pokemon Fire Red
- **Persistent Memory**: SQLite-based session management
- **Multi-step Execution**: Automatic task decomposition with error recovery
- **Prompt Experimentation**: A/B testing framework for optimization

**Phase 2 Requirements** 🚧:
- **VLLM Training Data**: Automated collection of gameplay sessions for fine-tuning
- **Step-Limited Execution**: `--steps` parameter for controlled run length
- **RL Scoring System**: 1-10 goal achievement evaluation interface
- **Training Data Format**: Mistral/VLLM compatible instruction tuning format
- **Runs Management**: Organized storage of training sessions

## Requirements

### Core Requirements

#### 1. GBA Emulation Integration
- **SkyEmu Integration**: Replace PyBoy with SkyEmu for GBA compatibility
- **HTTP Control Server**: Utilize SkyEmu's REST API for game control
- **Memory Reading**: Access Pokemon Fire Red memory addresses for game state
- **Save State Management**: Handle Pokemon save files and game persistence

#### 2. Pokemon Fire Red Game Configuration
- **Objectives Definition**: Define clear completion objectives (Gym badges, Elite Four, Pokedex completion)
- **Evaluation Metrics**: Pokemon-specific metrics (battle win rate, exploration efficiency, strategic decisions)
- **Checkpoint System**: Progress tracking through major game milestones
- **Game State Parsing**: Extract Pokemon party, inventory, position, and battle state

#### 3. RL+LLM Hybrid Agent Support
- **Agent Interface**: Support both RL agents (PPO/DQN) and LLM agents (Gemini/VLLM)
- **Hybrid Coordination**: Enable strategic LLM planning with tactical RL execution
- **Multi-Agent Support**: Different agents for exploration, battles, and menu navigation
- **Performance Comparison**: Benchmark RL-only vs LLM-only vs hybrid approaches

#### 4. VLLM Training Pipeline
- **Data Collection**: Capture gameplay sessions for training data generation
- **Format Conversion**: Convert gameplay to VLLM fine-tuning format
- **Training Integration**: Automated VLLM model training from collected data
- **Model Evaluation**: Test fine-tuned models on Pokemon-specific tasks

### Enhanced Requirements

#### 5. Audio Interface Integration
- **Gemini Live API**: Real-time voice command processing
- **Voice Commands**: Natural language game control ("Switch to Pikachu", "Go to Pokemon Center")
- **Audio Feedback**: Real-time strategy narration and suggestions
- **Command Parsing**: Convert voice input to game actions

#### 6. Advanced Evaluation Framework
- **Curriculum Learning**: Progressive difficulty stages (Pallet Town → Elite Four)
- **Transfer Learning**: Evaluate model performance across different Pokemon games
- **Strategic Analysis**: Measure type advantage usage, resource management, team composition
- **Failure Analysis**: Detailed logging of failure modes and recovery strategies

#### 7. Performance Optimization
- **API Cost Management**: Intelligent caching and batching for Gemini API calls
- **Parallel Training**: Multiple game instances for data collection
- **Resource Monitoring**: GPU/CPU usage tracking during training and evaluation
- **Scalability**: Support for distributed training across multiple machines

## Technical Specifications

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                VideoGameBench Core                         │
├─────────────────────────────────────────────────────────────┤
│  Pokemon Fire Red Module                                    │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ SkyEmu Client   │    │ Game State      │                │
│  │ (HTTP API)      │    │ Parser          │                │
│  └─────────────────┘    └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  RL+LLM Agent Framework                                     │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Hybrid Agent    │    │ Strategy Layer  │                │
│  │ Controller      │    │ (LLM)          │                │
│  └─────────────────┘    └─────────────────┘                │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Tactical Layer  │    │ Audio Interface │                │
│  │ (RL)           │    │ (Gemini Live)   │                │
│  └─────────────────┘    └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  VLLM Training Pipeline                                     │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Data Collector  │    │ Training        │                │
│  │                 │    │ Scheduler       │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### SkyEmu Integration
```python
class SkyEmuClient:
    """HTTP client for SkyEmu emulator control"""
    
    def __init__(self, host="localhost", port=8080):
        self.base_url = f"http://{host}:{port}"
        
    async def send_input(self, button, duration=0.1):
        """Send button input to emulator"""
        
    async def read_memory(self, addresses):
        """Batch read memory addresses"""
        
    async def capture_screen(self):
        """Get current game screenshot"""
        
    async def load_save_state(self, save_path):
        """Load game save state"""
```

#### Pokemon Game Environment
```python
class PokemonFireRedEnvironment(GameEnvironment):
    """Pokemon Fire Red specific game environment"""
    
    def __init__(self):
        self.skyemu = SkyEmuClient()
        self.state_parser = PokemonStateParser()
        self.objective_tracker = ObjectiveTracker()
        
    def step(self, action):
        """Execute action and return new state"""
        
    def reset(self):
        """Reset to start of game or checkpoint"""
        
    def get_objectives(self):
        """Return current game objectives"""
        
    def calculate_progress_score(self):
        """Calculate completion percentage"""
```

#### Hybrid Agent Interface
```python
class HybridPokemonAgent(VLMAgent):
    """RL+LLM hybrid agent for Pokemon gameplay"""
    
    def __init__(self, rl_agent, llm_agent):
        self.rl_agent = rl_agent
        self.llm_agent = llm_agent
        self.meta_controller = MetaController()
        
    def act(self, observation, game_state):
        """Choose action using hybrid strategy"""
        
    def update_strategy(self, feedback):
        """Update long-term strategy based on performance"""
```

### Data Formats

#### Training Data Schema
```json
{
  "session_id": "pokemon_session_001",
  "timestamp": "2025-01-17T10:30:00Z",
  "game_state": {
    "player": {
      "position": {"x": 123, "y": 456, "map": "viridian_forest"},
      "party": [
        {
          "species": "wartortle",
          "level": 18,
          "hp": {"current": 45, "max": 52},
          "moves": ["water_gun", "tackle", "tail_whip", "withdraw"]
        }
      ],
      "inventory": {"pokeball": 5, "potion": 3}
    },
    "battle": {
      "active": true,
      "opponent": {"species": "pidgey", "level": 12, "hp": 8}
    }
  },
  "llm_reasoning": "Use Water Gun for type advantage against Normal-type Pidgey",
  "rl_action": "attack_water_gun",
  "outcome": {
    "success": true,
    "damage_dealt": 15,
    "battle_won": true
  },
  "screenshot": "base64_encoded_image"
}
```

## Implementation Plan

### Phase 1: Core Integration (Week 1-2)
1. **SkyEmu Client Development**
   - HTTP API wrapper for game control
   - Memory reading utilities for Pokemon data
   - Screenshot capture and save state management

2. **Pokemon Environment Setup**
   - Game state parsing from memory addresses
   - Objective definition and progress tracking
   - Basic action space mapping

3. **VideoGameBench Integration**
   - Adapt existing framework for GBA games
   - Pokemon-specific configuration files
   - Initial evaluation pipeline

### Phase 2: Agent Framework (Week 2-3)
1. **RL Agent Integration**
   - PPO/DQN implementation for Pokemon actions
   - Reward function design for exploration and battles
   - Training pipeline for tactical decisions

2. **LLM Agent Integration**
   - Gemini API integration for strategic planning
   - VLLM model serving for game-specific decisions
   - Structured prompting for Pokemon contexts

3. **Hybrid Coordination**
   - Meta-controller for agent selection
   - Communication protocol between RL and LLM
   - Performance monitoring and debugging

### Phase 3: Advanced Features (Week 3-4)
1. **VLLM Training Pipeline**
   - Automated data collection from gameplay sessions
   - Training data format conversion
   - Model fine-tuning and evaluation workflow

2. **Audio Interface**
   - Gemini Live API integration
   - Voice command processing
   - Real-time audio feedback

3. **Evaluation Framework**
   - Pokemon-specific metrics and benchmarks
   - Performance comparison tools
   - Curriculum learning progression

### Phase 4: Optimization & Testing (Week 4-6)
1. **Performance Optimization**
   - API cost optimization strategies
   - Parallel training implementation
   - Resource usage monitoring

2. **Comprehensive Testing**
   - End-to-end gameplay evaluation
   - Agent performance comparison
   - Training pipeline validation

3. **Documentation & Deployment**
   - API documentation and examples
   - Deployment guides and best practices
   - Performance benchmarking results

## Success Metrics

### Primary Metrics
- **Game Completion Rate**: % of agents that successfully progress through major milestones
- **Battle Win Rate**: Success in Pokemon battles across different scenarios
- **Navigation Efficiency**: Steps required to navigate complex areas (Viridian Forest)
- **Strategic Decision Quality**: Proper use of type advantages, team composition, resource management

### Secondary Metrics
- **API Cost Efficiency**: Cost per successful game completion
- **Training Data Quality**: VLLM model performance improvement from collected data
- **System Performance**: Training time, memory usage, and scalability metrics
- **User Experience**: Ease of setup, configuration, and usage

## Dependencies & Resources

### External Dependencies
- SkyEmu emulator with HTTP Control Server
- Pokemon Fire Red ROM file
- Gemini API access for multimodal reasoning
- VLLM serving infrastructure for model inference
- Sufficient GPU resources for RL training and VLLM fine-tuning

### Development Resources
- Python 3.10+ environment
- PyTorch for RL agent implementation
- Transformers library for VLLM integration
- FastAPI for REST API development
- Docker for containerized deployment

## Risk Assessment

### Technical Risks
- **SkyEmu Stability**: Potential emulator crashes during extended training
- **API Rate Limits**: Gemini API throttling during intensive usage
- **Memory Consumption**: Large memory requirements for parallel training
- **ROM Compatibility**: Pokemon Fire Red version compatibility issues

### Mitigation Strategies
- Implement robust error handling and automatic restart mechanisms
- API request batching, caching, and intelligent retry logic
- Gradient checkpointing and model parallelization for memory efficiency
- Comprehensive testing with multiple ROM versions and save states

## Future Enhancements

- Support for additional Pokemon games (Emerald, Ruby, Sapphire)
- Multi-player battle evaluation
- Pokemon breeding and competitive strategy optimization
- Integration with Pokemon Showdown for battle simulation
- Real-time streaming and community interaction features

---

This PRD provides a comprehensive roadmap for enhancing videogamebench to support Pokemon Fire Red with advanced RL+LLM hybrid agents and VLLM fine-tuning capabilities.