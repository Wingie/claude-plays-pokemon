# Eevee v2 - Next-Generation AI Pokemon Gaming System

## 🏗️ Architecture Overview

Eevee v2 represents a complete architectural reimagining of AI-powered Pokemon gameplay, moving from v1's monolithic approach to a **constraint-driven, layered architecture** that solves real-time performance while maintaining intelligent decision-making.

**Key Innovation**: **Architectural Separation** - instead of optimizing slow components, we separate execution from reasoning using pause/resume control.

## 🎯 Core Design Philosophy

### Constraint-Driven Architecture
- **Real-Time Constraint**: 60 FPS = 16.7ms total budget per frame
- **V1 Problem**: 100-300ms reasoning pipeline (6-18x over budget)
- **V2 Solution**: Separated architecture with pause/resume control

### Performance-First Design Patterns

#### Layer Separation
```
EXECUTION LAYER (≤5ms):     Pattern Match → Cached Action → Execute
STRATEGIC LAYER (unlimited): Deep Reasoning → Plan Generation → Cache Update
MEMORY LAYER (async):       Background Updates → Knowledge Integration
```

#### Example Implementation Pattern
```python
# V1 WRONG: Everything in critical path
def game_loop():
    screenshot = capture_frame()          # 2ms
    analysis = ai_analyze(screenshot)     # 150ms ❌
    decision = strategic_plan(analysis)   # 100ms ❌
    execute_buttons(decision)             # 1ms
    # Total: 253ms (15x over budget)

# V2 CORRECT: Separated concerns
def game_loop():
    screenshot = capture_frame()          # 2ms
    if strategy_cache.has_plan(screenshot):
        action = strategy_cache.get_action()  # 1ms
        execute_buttons(action)           # 1ms
    else:
        pause_game()
        asyncio.create_task(deep_reasoning())  # Unlimited time
        execute_buttons(safe_fallback())  # 1ms
    # Total: 5ms (within budget)
```

## 🧠 Neural Architecture Design

### Unified 512D Embedding Space with SSM Integration
- **Vision Encoder**: CNN processing game frames with windowed temporal processing
- **Short-term Memory**: Hybrid State-Space Model (Griffin-inspired) for constant memory footprint
- **Long-term Memory Interface**: Neo4j query generation with semantic coherence tracking
- **Tool Calling Module**: Structured action outputs with length extrapolation capability
- **Heartbeat Controller**: 10Hz processing coordination with fixed-size state maintenance
- **Decision Fusion Layer**: Integrated decision making with infinite context support

### SpeechSSM-Inspired Innovations for Gaming AI

#### 1. **Constant Memory Architecture**
```python
# Inspired by SpeechSSM's constant memory decoding
class EeveeExecutionLayer:
    def __init__(self):
        self.fixed_state_size = 512  # Constant regardless of sequence length
        self.recurrent_layers = GriffinSSM(hidden_size=512)
        self.local_attention = SlidingWindowAttention(window_size=2048)
    
    def process_frame(self, game_frame, state):
        # O(1) memory complexity per frame
        new_state = self.recurrent_layers(game_frame, state)
        action = self.local_attention(new_state)
        return action, new_state  # State size never grows
```

#### 2. **Windowed Game Processing** 
- **30-second game segments** with 4-second overlap for continuity
- **Temporal tokenization** of game states for efficient processing
- **Boundary artifact minimization** between decision windows

#### 3. **Length Extrapolation for Novel Situations**
- **Training on 4-minute gameplay** sessions, extrapolating to unlimited duration
- **Semantic coherence maintenance** across extended gameplay
- **Quality consistency** beyond training scenarios

### Training Strategy
- **Phase 1**: Behavioral cloning with windowed processing (4-8 weeks, 70-80% completion)
- **Phase 2**: Memory + RL with length extrapolation (8-12 weeks, 90% completion)
- **Phase 3**: Long-form coherence optimization inspired by SpeechSSM evaluation metrics
- **ComfyUI Inspiration**: Modular "mini brains" using safetensors format
- **LoRA Fine-tuning**: Parameter-efficient adaptation
- **SSM Integration**: Griffin-style hybrid architecture for gaming sequences

## 🔧 Implementation Guidelines

### Development Commands

#### Setup & Installation
```bash
# Navigate to eevee_v2 directory
cd eevee_v2

# Install dependencies (check for requirements.txt/pyproject.toml)
pip install -r requirements.txt
# or
pip install -e .

# For PaliGemma fine-tuning
cd paligemma
python fine_tuning_paligemma.py
```

#### Testing Commands
```bash
# Run system tests
python -m pytest tests/

# Test specific components
python test_execution_layer.py
python test_strategic_layer.py
python test_memory_layer.py
```

### Project Structure
```
eevee_v2/
├── paligemma/              # Vision model fine-tuning
│   └── fine_tuning_paligemma.py
├── specs/                  # Architecture specifications
│   ├── AI_System_Architecture_Specification.md
│   ├── Complexity_Avoidance_Design_Patterns.md
│   ├── Performance_First_Design_Specification.md
│   └── vision.md          # Complete conversation history
└── CLAUDE.md              # This file
```

## 🎮 Core Technical Innovations

### 1. Real-Time Constraint Handling
- **Critical Path Optimization**: Only pattern matching in execution layer
- **Pause/Resume Control**: Strategic reasoning happens while game is paused
- **Cached Actions**: Pre-computed decisions for common scenarios
- **Safe Fallbacks**: Default actions when reasoning is unavailable

### 2. Modular Neural Components
- **Safetensors Format**: Portable neural components like ComfyUI nodes
- **Mini-Brain Architecture**: Specialized modules for different game aspects
- **LoRA Adaptation**: Efficient fine-tuning without full retraining
- **Pretrained Integration**: CLIP vision components with custom layers

### 3. Memory System Integration
- **Neo4j Backend**: Graph-based long-term memory
- **Spatial Memory**: World state and navigation knowledge
- **Episodic Memory**: Experience replay and learning
- **Working Memory**: Short-term context management

## 🔄 Development Workflow

### Phase 1: Execution Layer (Current Focus)
1. **Pattern Matching System**: Fast visual pattern recognition
2. **Action Cache**: Pre-computed decision storage
3. **Fallback Mechanisms**: Safe default behaviors
4. **Performance Monitoring**: Real-time latency tracking

### Phase 2: Strategic Layer
1. **Deep Reasoning Module**: Complex game analysis
2. **Plan Generation**: Multi-step strategy creation
3. **Cache Population**: Strategic decision pre-computation
4. **Learning Integration**: Experience-based improvement

### Phase 3: Memory Layer
1. **Neo4j Integration**: Graph-based memory storage
2. **Background Updates**: Non-blocking knowledge updates
3. **Cross-Session Learning**: Persistent improvement
4. **Memory Optimization**: Efficient retrieval patterns

## 📊 Performance Targets

### Execution Layer
- **Frame Budget**: ≤5ms per frame
- **Pattern Recognition**: ≤2ms
- **Action Lookup**: ≤1ms
- **Button Execution**: ≤1ms

### Strategic Layer
- **Reasoning Time**: Unlimited (pause-based)
- **Plan Quality**: >90% success rate
- **Cache Hit Rate**: >80% for common scenarios
- **Learning Rate**: Continuous improvement

### Memory Layer
- **Background Updates**: Non-blocking
- **Query Response**: ≤10ms for cached queries
- **Storage Efficiency**: Optimal graph representation
- **Knowledge Retention**: Long-term persistence

## 🎯 Long-Form Gaming Evaluation (SpeechSSM-Inspired)

### Novel Evaluation Metrics for Extended Gameplay

#### 1. **Semantic Coherence over Length (SC-L)**
```python
# Adapted from SpeechSSM's SC-L metric
def evaluate_gameplay_coherence(prompt_state, gameplay_segments):
    """
    Measure semantic consistency between initial game state 
    and each subsequent 200-action segment (~1 minute of gameplay)
    """
    prompt_embedding = encode_game_state(prompt_state)
    coherence_scores = []
    
    for segment in gameplay_segments:
        segment_embedding = encode_gameplay_actions(segment)
        similarity = cosine_similarity(prompt_embedding, segment_embedding)
        coherence_scores.append(similarity)
    
    return coherence_scores
```

#### 2. **Gaming Performance over Time (GPT)**
- **Action Quality**: Measure decision accuracy across gameplay duration
- **Goal Achievement**: Track objective completion over extended sessions
- **Strategy Consistency**: Evaluate long-term plan adherence
- **Error Recovery**: Assess ability to recover from mistakes over time

#### 3. **Length Extrapolation Benchmarks**
- **Training Duration**: 4-minute gameplay sessions
- **Evaluation Duration**: 16-minute extended gameplay
- **Coherence Maintenance**: Quality consistency beyond training length
- **Memory Efficiency**: Constant memory usage regardless of session length

### Gaming-Specific Adaptations

#### Pokemon-Long Benchmark (LibriSpeech-Long Equivalent)
- **Extended Gameplay Sessions**: 4-minute Pokemon encounters/exploration
- **Reference Trajectories**: Expert human gameplay for comparison
- **Multi-metric Evaluation**: Action accuracy, goal achievement, exploration efficiency

#### Side-by-Side Gaming Evaluation (LLM-as-Judge)
```
Evaluation Criteria:
- Strategic Coherence: How well does the AI maintain long-term strategy?
- Adaptability: How effectively does it respond to unexpected situations?
- Efficiency: How optimal are the chosen action sequences?
- Learning: Does performance improve within the session?
```

### Performance Degradation Analysis
- **Quality over Time**: Track decision accuracy as gameplay progresses
- **Memory Utilization**: Monitor state-space efficiency during extended play
- **Strategic Drift**: Measure deviation from initial objectives over time
- **Extrapolation Success**: Evaluate performance beyond training scenarios

## 🛠️ Technical Specifications

### Hardware Requirements
- **GPU**: CUDA-compatible for neural inference
- **RAM**: 16GB+ for model loading
- **Storage**: SSD recommended for fast I/O
- **CPU**: Multi-core for async processing

### Software Dependencies
- **Python 3.8+**: Core runtime
- **PyTorch**: Neural network framework
- **Neo4j**: Graph database
- **OpenCV**: Computer vision
- **AsyncIO**: Concurrent processing

## 🚀 Getting Started

### Quick Start
```bash
# Clone and setup
git clone <repo-url>
cd claude-plays-pokemon/eevee_v2

# Install dependencies
pip install -r requirements.txt

# Run basic tests
python test_execution_layer.py

# Start development server
python main.py --dev-mode
```

### Development Environment
- **IDE**: VS Code with Python extension
- **Debugging**: Built-in debugger with breakpoints
- **Testing**: pytest for unit tests
- **Profiling**: cProfile for performance analysis

## 📚 Documentation Standards

### Code Documentation
- **Docstrings**: All functions and classes
- **Type Hints**: Full type annotation
- **Comments**: Explain complex algorithms
- **Examples**: Usage examples in docstrings

### Architecture Documentation
- **Design Decisions**: Rationale for architectural choices
- **Performance Metrics**: Benchmarks and targets
- **Future Roadmap**: Planned improvements
- **Troubleshooting**: Common issues and solutions

## 🎯 Success Metrics

### Performance Metrics
- **Real-time Compliance**: 100% frames within budget
- **Action Accuracy**: >95% correct decisions
- **Learning Rate**: Measurable improvement over time
- **System Stability**: <1% crash rate

### Gaming Metrics
- **Pokemon Battles**: Win rate improvement
- **Navigation**: Efficient pathfinding
- **Goal Achievement**: Task completion rate
- **Exploration**: Map coverage and discovery

## 🔮 Future Roadmap

### Near-term (1-3 months)
- Complete execution layer implementation
- Basic strategic layer integration
- Performance optimization
- Initial testing and validation

### Medium-term (3-6 months)
- Full strategic layer deployment
- Memory system integration
- Advanced learning algorithms
- Multi-game support

### Long-term (6+ months)
- Generalized gaming AI
- Transfer learning capabilities
- Advanced reasoning systems
- Community deployment

---

*This document serves as the comprehensive guide for Eevee v2 development. All code changes should align with these architectural principles and performance targets.*