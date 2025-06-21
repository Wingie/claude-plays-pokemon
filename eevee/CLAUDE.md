# Eevee v1 - AI Pokemon Task Execution System

## 🏗️ Architecture Overview

Eevee v1 is a sophisticated AI-powered Pokemon gameplay system that combines multimodal reasoning, real-time game control, and self-improving prompt templates.

## 🧩 Core Components

### **EeveeAgent** (`eevee_agent.py`)
- **Primary Role**: Main orchestration and SkyEmu integration
- **Key Functions**: Screenshot capture, button press execution, state management
- **Interfaces**: SkyEmu HTTP API, game ROM management, save/load states

### **PromptManager** (`prompt_manager.py`) 
- **Primary Role**: AI-directed template selection and management
- **Key Features**:
  - **AI Template Selection**: Analyzes memory context to choose appropriate template
  - **Dynamic Mapping**: Maps context types to base templates
  - **Template Loading**: YAML-based template system with playbook integration
  - **Version Tracking**: Maintains template versions for learning system

### **ContinuousGameplay** (`run_eevee.py`)
- **Primary Role**: Manages continuous Pokemon gameplay loop
- **Key Features**:
  - **Turn-based Execution**: Screenshot → AI Analysis → Button Press → Memory Update
  - **Periodic Learning**: AI-powered template improvement every N turns
  - **Session Management**: Persistent session data with template usage tracking
  - **Interactive Mode**: Real-time user input during autonomous gameplay

### **MemorySystem** (`memory_system.py`)
- **Primary Role**: Persistent context and session management  
- **Key Features**: SQLite-based storage, session isolation, memory contexts

### **TaskExecutor** (`task_executor.py`)
- **Primary Role**: Multi-step task decomposition and execution
- **Key Features**: Natural language task processing, error recovery

## 🧠 AI-Directed Template System

### **Template Selection Flow**
```
Memory Context → AI Analysis → Template Selection → Gameplay → Performance Tracking → Learning
```

### **Context Types**
- **`auto_select`**: AI analyzes memory_context to choose template
- **`emergency`**: Severe stuck patterns (escalation level 3-5)

### **Template Mapping**
```python
AI-Directed Templates → Base Templates (for improvement)
ai_directed_navigation → exploration_strategy
ai_directed_battle → battle_analysis  
ai_directed_emergency → stuck_recovery
```

### **AI Selection Logic** (`prompt_manager.py:762-788`)
The AI analyzes `memory_context` to detect:
- **Battle Keywords**: "wild", "trainer", "fight", "hp", "pp" → `battle_analysis`
- **Emergency Keywords**: "stuck", "loop", "repeated" → `stuck_recovery`  
- **Default**: `exploration_strategy` for navigation

## 🔄 Learning System Architecture

### **Template Usage Tracking**
Each turn records:
```json
{
  "template_used": "ai_directed_navigation",
  "template_version": "ai_directed", 
  "ai_analysis": "🎯 OBSERVATION: I see...",
  "button_presses": ["up"],
  "action_result": true
}
```

### **Performance Analysis** (`run_eevee.py:1298-1347`)
- **Stuck Pattern Detection**: 3+ consecutive identical actions
- **Failure Detection**: `action_result == false` OR stuck patterns
- **Success Rate Calculation**: Per-template performance metrics

### **AI-Powered Improvement** (`run_eevee.py:1368-1520`)
1. **Template Analysis**: Identify poorly performing templates
2. **Failure Examples**: Extract specific failure scenarios  
3. **Gemini Improvement**: Generate enhanced templates using Gemini 2.0 Flash
4. **YAML Updates**: Save improved templates with version tracking
5. **Template Reload**: Immediately use improved templates

### **Template Eligibility**
Only improves actually-used templates:
```python
valid_templates = {
    "ai_directed_navigation", "ai_directed_battle", 
    "ai_directed_maze", "ai_directed_emergency",
    # Legacy fallback templates
    "battle_analysis", "exploration_strategy", "stuck_recovery"
}
```

## 📁 File Structure

### **Core Files**
```
eevee/
├── run_eevee.py              # Main execution and learning system
├── eevee_agent.py             # SkyEmu integration
├── prompt_manager.py          # AI-directed template system
├── memory_system.py           # Persistent storage
├── task_executor.py           # Task decomposition
└── run_learn_fix.sh          # Automated learning script
```

### **Template System**
```
eevee/prompts/
├── base/
│   └── base_prompts.yaml     # Auto-updated templates
└── playbooks/
    ├── battle.yaml           # Battle knowledge  
    ├── navigation.yaml       # Movement strategies
    ├── services.yaml         # Pokemon Centers, shops
    └── gyms.yaml            # Gym-specific strategies
```

### **Session Data**
```
eevee/runs/session_TIMESTAMP/
├── session_data.json         # Turn-by-turn data with template usage
├── periodic_review_turn_N.md # AI analysis and improvements
└── screenshots/              # Visual game state evidence
```

## 🎮 Execution Modes

### **Continuous Gameplay** (Default)
```bash
python run_eevee.py --goal "walk around and win pokemon battles"
```
- AI plays autonomously while learning from performance
- Real-time template improvements every N turns
- User can interact via chat commands

### **Learning Mode**
```bash  
python run_eevee.py --episode-review-frequency 4 --max-turns 12 --no-interactive
```
- Focused on rapid template improvement
- Minimal turns for quick learning cycles
- No user interaction for pure AI learning

### **Automated Learning Script**
```bash
bash run_learn_fix.sh
```
- Runs multiple learning sessions (4-turn + 12-turn)
- Analyzes results and template updates
- Auto-launches Claude Code for analysis

## 🔧 Key Technical Decisions

### **Why AI-Directed Templates?**
- **Flexible**: AI chooses context instead of hardcoded detection
- **Accurate**: Uses actual game memory context for decision making
- **Learnable**: AI-directed templates can be improved through learning

### **Why Template Mapping?**
- **Compatibility**: AI-directed names mapped to base templates for improvement
- **Focused Learning**: Only improves templates actually being used
- **Version Control**: Maintains clear template evolution tracking

### **Why Single Review System?**
- **Consistency**: Removed conflicting old episode reviewer
- **Real-time**: Learning happens during gameplay, not after
- **Immediate**: Improved templates used in same session

## 🚀 Quick Start

### **Basic Usage**
```bash
# Standard autonomous gameplay
python run_eevee.py --goal "find and win pokemon battles"

# Learning mode with frequent improvements  
python run_eevee.py --goal "defeat gym leaders" --episode-review-frequency 5 --max-turns 20

# Automated learning cycles
bash run_learn_fix.sh
```

### **Monitoring Learning**
```bash
# Watch AI improvements in real-time
tail -f runs/session_*/periodic_review_turn_*.md

# Check template versions
grep "version:" prompts/base/base_prompts.yaml

# Analyze session performance
ls -la runs/session_*/session_data.json
```

## 🎯 Expected Behavior

### **Template Selection**
- **Battles**: AI detects battle context → uses `ai_directed_battle` → improves `battle_analysis`
- **Navigation**: AI detects movement context → uses `ai_directed_navigation` → improves `exploration_strategy`  
- **Stuck Patterns**: AI detects repetition → uses `ai_directed_emergency` → improves `stuck_recovery`

### **Learning Evolution**
1. **Turn 1-10**: Basic template usage, AI learns context patterns
2. **Turn 10-50**: Templates improve for common failure modes
3. **Turn 50+**: Sophisticated context-aware gameplay with minimal errors

This architecture enables true AI self-improvement through dynamic template selection and continuous learning from gameplay experience.