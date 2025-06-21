# Eevee v1 - AI Pokemon Task Execution System

## 🏗️ Architecture Overview

Eevee v1 is a sophisticated AI-powered Pokemon gameplay system that combines multimodal reasoning, real-time game control, self-improving prompt templates, and **centralized multi-provider LLM API system** supporting both Gemini and Mistral AI providers.

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

### **LLM API System** (`llm_api.py`, `provider_config.py`)
- **Primary Role**: Centralized AI provider management and API abstraction
- **Key Features**:
  - **Multi-Provider Support**: Seamless switching between Gemini and Mistral providers
  - **Unified Interface**: Single API for all LLM interactions across the system
  - **Provider Abstraction**: Consistent response format regardless of underlying provider
  - **Error Resilience**: Circuit breakers, exponential backoff, automatic fallback
  - **Environment Configuration**: Easy provider switching via `.env` variables

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

### **Complete Project Architecture**
```
claude-plays-pokemon/eevee/
├── 📋 **Core System Files**
│   ├── run_eevee.py              # Main execution & learning system
│   ├── eevee_agent.py            # SkyEmu integration & game control
│   ├── prompt_manager.py         # AI-directed template system
│   ├── llm_api.py               # Centralized LLM API (Gemini + Mistral)
│   ├── memory_system.py         # Persistent SQLite storage
│   ├── task_executor.py         # Task decomposition & execution
│   ├── provider_config.py       # Environment-based configuration
│   ├── skyemu_controller.py     # Game Boy emulator interface
│   ├── episode_reviewer.py      # Legacy review system
│   ├── diary_generator.py       # Session documentation
│   └── neo4j_memory.py         # Graph-based memory (experimental)
│
├── 🧪 **tests/** (32 test files - ORGANIZED)
│   ├── 👁️ **Vision & Screenshot Tests:**
│   │   ├── test_grid_overlay_vision.py     # Grid overlay research ✅
│   │   ├── test_pixtral_vision.py          # Vision verification tests
│   │   ├── test_prompt_variations.py       # Prompt hallucination testing
│   │   ├── test_vision_deep_research.py    # Progressive prompt research
│   │   └── test_overworld_scene_detection.py # Scene classification
│   │
│   ├── 🤖 **LLM API & Provider Tests:**
│   │   ├── test_llm_api.py                 # Multi-provider testing ✅
│   │   ├── test_provider_config.py         # Configuration validation
│   │   ├── test_eevee_migration.py         # Migration testing
│   │   ├── test_mistral_function_calling.py
│   │   └── test_mistral_prompt_styles.py
│   │
│   ├── 🧠 **Core System Tests:**
│   │   ├── test_prompt_manager_migration.py
│   │   ├── test_task_executor_migration.py
│   │   ├── test_template_hotswap.py
│   │   ├── test_template_improvement_pipeline.py
│   │   ├── test_learning_system.py
│   │   ├── test_enhanced_stuck_detection.py
│   │   └── test_ai_directed_prompts.py
│   │
│   ├── 🎮 **Gameplay & Navigation Tests:**
│   │   ├── test_actual_gameplay_prompt.py
│   │   ├── test_navigation_enhancement.py
│   │   ├── test_enhanced_prompts.py
│   │   └── test_logging.py
│   │
│   ├── 📊 **Test Results & Outputs:**
│   │   ├── grid_overlay_output.txt         # Latest test output
│   │   ├── grid_overlay_results_*.json     # Test result data
│   │   ├── overlay_images_*/               # Generated overlay images
│   │   │   ├── original_no_overlay.png
│   │   │   ├── coordinate_grid_overlay.png
│   │   │   ├── game_boy_tile_overlay.png
│   │   │   └── coordinate_questions_overlay.png
│   │   ├── vision_test_results_v2.txt      # **CRITICAL VISION ISSUE**
│   │   └── pixtral_vision_test_*.json      # Vision test data
│   │
│   └── 📝 **Standardized Import Pattern:**
│       ```python
│       # Standard for ALL test files:
│       from pathlib import Path
│       import sys
│       
│       # Navigate from tests/ to project directories
│       project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
│       eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
│       sys.path.append(str(eevee_root))                    # For eevee modules
│       sys.path.append(str(project_root))                  # For root-level modules
│       sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
│       ```
│
├── 🎯 **prompts/** (Template System)
│   ├── base/
│   │   └── base_prompts.yaml     # Auto-updated AI templates
│   ├── playbooks/               # Knowledge repositories
│   │   ├── battle.yaml          # Battle strategies & type effectiveness
│   │   ├── navigation.yaml      # Movement & pathfinding knowledge
│   │   ├── services.yaml        # Pokemon Centers, shops, facilities
│   │   └── gyms.yaml           # Gym-specific puzzle solutions
│   └── providers/
│       └── mistral/
│           └── base_prompts.yaml # Mistral-specific prompts
│
├── 💾 **memory/** (Persistent Storage)
│   ├── eevee_memory_*.db        # SQLite session databases
│   └── neo4j_data/             # Graph memory (experimental)
│
├── 📊 **runs/** (Session Data)
│   └── session_TIMESTAMP/
│       ├── session_data.json         # Turn-by-turn gameplay data
│       ├── periodic_review_turn_N.md # AI analysis & improvements
│       └── screenshots/              # Visual game state evidence
│
├── 📸 **analysis/** (Debug Images)
│   ├── skyemu_screenshot_*.png       # Game state captures
│   ├── eevee_context_*.png          # AI decision contexts
│   └── before_*/after_* button analysis
│
├── 📋 **specs/** (Technical Documentation)
│   ├── user_spec_testing_notes.md
│   └── pokemon_character_dataset_spec.md
│
├── 🎓 **Fine-Tuning/** (Model Training)
│   ├── Phi3-Vision-Finetune/
│   ├── environment.yml
│   └── fine_tuning_notes.md
│
├── 🔧 **test_runs/** (Legacy Test Data)
│   └── test_session_*/
│
└── 📝 **Configuration Files**
    ├── .env                     # API keys & provider settings
    ├── .env.example            # Configuration template
    ├── CLAUDE.md               # This comprehensive documentation
    ├── README.md               # Project overview
    ├── run_learn_fix.sh        # Automated learning script
    └── switch_provider.py      # Provider switching utility
```

### **External Dependencies**
```
../gemini-multimodal-playground/standalone/
├── skyemu_controller.py      # SkyEmu HTTP interface
├── pokemon_controller.py     # Legacy mGBA interface  
└── screen_*.py              # Screen processing utilities
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

## 🧪 Testing & Development System

### **Test Organization & Execution**

#### **Running Tests from tests/ Directory**
```bash
# Navigate to tests directory
cd tests

# Run specific test categories
python test_grid_overlay_vision.py          # Vision research
python test_llm_api.py                      # LLM API validation  
python test_prompt_variations.py            # Hallucination testing
python test_pixtral_vision.py              # Vision verification

# Monitor test outputs
tail -f grid_overlay_output.txt
ls -la overlay_images_*/                   # Generated overlay images
```

#### **Test Categories & Purposes**

**🔍 Vision & Screenshot Tests:**
- **Purpose**: Debug Pixtral vision hallucinations, test grid overlays
- **Key Files**: `test_grid_overlay_vision.py`, `test_prompt_variations.py`
- **Outputs**: Overlay images, vision analysis reports, hallucination detection

**🤖 LLM API & Provider Tests:**
- **Purpose**: Validate multi-provider system, test failover, configuration
- **Key Files**: `test_llm_api.py`, `test_provider_config.py`
- **Outputs**: API response validation, provider performance metrics

**🧠 Core System Tests:**
- **Purpose**: Test prompt management, template learning, memory systems
- **Key Files**: `test_template_*.py`, `test_learning_*.py`
- **Outputs**: Template validation, learning performance analysis

**🎮 Gameplay Tests:**
- **Purpose**: Test actual Pokemon gameplay, navigation, battle detection
- **Key Files**: `test_actual_gameplay_prompt.py`, `test_navigation_*.py`
- **Outputs**: Gameplay session data, AI decision analysis

### **Import Pattern Standards**

All test files use the standardized import pattern:
```python
from pathlib import Path
import sys

# Navigate from tests/ to project directories  
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))                    # For eevee modules
sys.path.append(str(project_root))                  # For root-level modules
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

# Then import project modules
from llm_api import call_llm
from skyemu_controller import SkyEmuController  
from prompt_manager import PromptManager
```

### **Test Output Management**

**📊 Automatic Output Saving:**
- All tests save results to both timestamped files AND persistent filenames
- Grid overlay tests save overlay images for visual inspection
- Vision tests save hallucination analysis in readable format

**📁 Output File Patterns:**
```bash
tests/
├── grid_overlay_output.txt              # Always current results
├── grid_overlay_results_TIMESTAMP.json  # Timestamped data
├── overlay_images_TIMESTAMP/            # Visual test artifacts
│   ├── original_no_overlay.png
│   ├── coordinate_grid_overlay.png  
│   ├── game_boy_tile_overlay.png
│   └── coordinate_questions_overlay.png
└── vision_test_results_v2.txt          # Vision verification results
```

### **Development Workflow**

1. **Adding New Tests:**
   ```bash
   # Use standardized naming: test_[category]_[specific_feature].py
   # Follow import pattern from existing tests
   # Save outputs to both persistent and timestamped files
   ```

2. **Debugging Import Issues:**
   ```bash
   # Check import paths
   python -c "import sys; from pathlib import Path; print([p for p in sys.path if 'eevee' in p])"
   
   # Test specific imports
   cd tests && python -c "from llm_api import call_llm; print('✅ LLM API import works')"
   ```

3. **Running Comprehensive Tests:**
   ```bash
   # Run vision research pipeline
   bash ../run_learn_fix.sh
   
   # Test all LLM providers
   python test_llm_api.py && python test_provider_config.py
   ```

## 🔍 Vision System & Hallucination Issues

### **🚨 Critical Vision Problem Identified**

**Issue**: Pixtral hallucinates battle elements in overworld scenes
**Evidence**: From `vision_test_results_v2.txt`:
```
❤️ TEST 4: HP Bar Detection
✅ Pixtral Response: "Yes, I see health/HP bars in the image."
⚔️ TEST 6: Simple Battle Detection  
✅ Pixtral Response: "Yes, this is a Pokemon battle scene."
```

**Reality**: User confirmed NO HP bars exist in overworld navigation scenes.

### **Research Findings from Grid Overlay Tests**

#### **Grid Overlay Approach** (`test_grid_overlay_vision.py`)
Based on videogamebench methodology - adding coordinate grids to help vision models understand spatial layout:

**✅ Positive Results:**
- Coordinate grids help Pixtral use spatial references
- AI provides coordinate-based descriptions when prompted
- Original images (no overlay) show NO false battle detection

**⚠️ Persistent Issues:**
- Adding coordinate grids TRIGGERS hallucinations
- Game Boy tile grids cause extensive false battle claims
- Direct coordinate questions produce invented health bars and menus

#### **Test Results Summary:**
```bash
# From latest test run:
🔍 BATTLE ELEMENT DETECTION:
   ✅ no_overlay (none): No false battle detection
   ⚠️ coordinate_grid (coordinate_grid): Claims to see battle elements  
   ⚠️ game_boy_tiles (tile_grid): Claims to see battle elements
   ⚠️ coordinate_questions (coordinate_grid): Claims to see battle elements

🎯 ASSESSMENT:
⚠️ PARTIAL SUCCESS: Grid overlays provide spatial context but trigger hallucinations
✅ SPATIAL IMPROVEMENT: Pixtral uses coordinate references when available
```

### **Root Cause Analysis**

1. **Context-Induced Hallucination**: Game-specific prompts trigger Pokemon battle assumptions
2. **Spatial Overlay Confusion**: Grids may be interpreted as game UI elements  
3. **Template Selection Impact**: False battle detection → wrong template → poor gameplay

### **Solution Approaches**

#### **Immediate Fixes:**
```bash
# Use completely neutral prompts for template selection
"Describe what you see in this image."  # ✅ No game context
"Is this a Pokemon battle scene?"       # ❌ Induces hallucination
```

#### **Grid Overlay Improvements:**
- Use simpler coordinate grids with clear labeling
- Test higher resolution overlays for better spatial understanding
- Experiment with different overlay colors and styles

#### **Template Selection Rework:**
- Separate visual analysis from game context detection
- Use non-gaming prompts for initial scene classification  
- Implement confidence scoring for template selection

### **Testing & Validation**

**Run Grid Overlay Research:**
```bash
cd tests
python test_grid_overlay_vision.py    # Test coordinate grid approach
python test_prompt_variations.py      # Test neutral vs game prompts  
python test_vision_deep_research.py   # Progressive prompt testing
```

**Monitor Vision Issues:**
```bash
# Check latest vision test results
cat vision_test_results_v2.txt

# Review grid overlay findings  
cat grid_overlay_output.txt

# Examine overlay images
ls overlay_images_*/
```

**Expected Research Outcomes:**
- Document exactly which prompts cause hallucinations
- Identify optimal grid overlay configurations
- Develop neutral template selection prompts
- Improve spatial understanding without false detection

## 🤖 Multi-Provider LLM API System

### **Architecture Overview**
The centralized LLM API system provides a unified interface for AI interactions while supporting multiple providers with automatic fallback and error resilience.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Eevee Application Layer                      │
├─────────────────────────────────────────────────────────────────┤
│ EeveeAgent │ PromptManager │ TaskExecutor │ ContinuousGameplay │
├─────────────────────────────────────────────────────────────────┤
│                  Unified LLM API Interface                     │
│                     call_llm() function                        │
├─────────────────────────────────────────────────────────────────┤
│              LLMAPIManager (Provider Abstraction)              │
├─────────────────────────────────────────────────────────────────┤
│  GeminiProvider          │         MistralProvider             │
│  ├─ gemini-2.0-flash-exp │         ├─ mistral-large-latest     │
│  ├─ gemini-1.5-pro       │         ├─ pixtral-12b-2409        │
│  └─ Circuit Breaker      │         └─ Circuit Breaker         │
├─────────────────────────────────────────────────────────────────┤
│     Google Gemini API    │         Mistral AI API             │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Features**

#### **🔄 Provider Abstraction**
- **Unified Interface**: Single `call_llm()` function for all AI interactions
- **Standardized Response**: Consistent `LLMResponse` format across providers
- **Provider Switching**: Runtime switching without code changes
- **Model Selection**: Automatic model selection based on task requirements

#### **🛡️ Error Resilience**
- **Circuit Breakers**: Prevent cascading failures during API outages
- **Exponential Backoff**: Smart retry logic with increasing delays
- **Auto-Fallback**: Automatic provider switching on failures
- **Rate Limit Handling**: Intelligent 429 error detection and recovery

#### **⚙️ Environment Configuration**
All provider settings managed via `.env` file:
```bash
# Primary provider selection
LLM_PROVIDER=mistral                    # or 'gemini'
FALLBACK_PROVIDER=gemini               # Auto-fallback target
AUTO_FALLBACK=true                     # Enable automatic fallback

# API keys
GEMINI_API_KEY=your_gemini_key
MISTRAL_API_KEY=your_mistral_key

# Model preferences  
TEMPLATE_SELECTION_MODEL=mistral-large-latest
GAMEPLAY_MODEL=pixtral-12b-2409
```

### **Provider Capabilities**

#### **Gemini Provider**
- **Models**: `gemini-2.0-flash-exp`, `gemini-1.5-pro`, `gemini-1.5-flash`
- **Capabilities**: Text + Vision, Function calling, Fast response times
- **Best For**: Template selection, complex reasoning tasks
- **Rate Limits**: Generous free tier, good for development

#### **Mistral Provider**
- **Models**: `mistral-large-latest` (text), `pixtral-12b-2409` (vision)
- **Capabilities**: Advanced reasoning, vision analysis, competitive performance
- **Best For**: Gameplay decisions, screenshot analysis, production use
- **Rate Limits**: Pay-per-use, cost-effective for production

### **Usage Examples**

#### **Basic API Call**
```python
from llm_api import call_llm

# Automatic provider selection based on .env
response = call_llm(
    prompt="Analyze this Pokemon battle situation",
    image_data=screenshot_base64,
    max_tokens=1000
)

print(f"Response: {response.text}")
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
```

#### **Provider-Specific Calls**
```python
# Force specific provider
gemini_response = call_llm(
    prompt="What move should I use?",
    provider="gemini",
    model="gemini-2.0-flash-exp"
)

mistral_response = call_llm(
    prompt="Analyze this screenshot",
    image_data=screenshot,
    provider="mistral", 
    model="pixtral-12b-2409"
)
```

#### **Easy Provider Switching**
```bash
# Switch to Mistral for everything
export LLM_PROVIDER=mistral
export TEMPLATE_SELECTION_MODEL=mistral-large-latest
export GAMEPLAY_MODEL=pixtral-12b-2409

# Switch to Gemini for everything  
export LLM_PROVIDER=gemini
export TEMPLATE_SELECTION_MODEL=gemini-2.0-flash-exp
export GAMEPLAY_MODEL=gemini-2.0-flash-exp

# Hybrid setup (Mistral vision + Gemini text)
export LLM_PROVIDER=gemini
export TEMPLATE_SELECTION_MODEL=gemini-2.0-flash-exp
export GAMEPLAY_MODEL=pixtral-12b-2409
```

### **Configuration Management**

#### **Quick Configuration Check**
```bash
# Show current configuration
python provider_config.py --show-config

# Validate configuration
python provider_config.py --validate

# Switch provider temporarily
python provider_config.py --set-provider mistral
```

#### **Provider Testing**
```bash
# Test all providers and models
python tests/test_llm_api.py

# Test provider switching
python switch_provider.py

# Test with Pokemon-specific prompts
python tests/test_eevee_migration.py
```

### **Migration Benefits**
- **✅ Centralized**: All LLM calls go through single API
- **✅ Multi-Provider**: Support for Gemini + Mistral with easy switching
- **✅ Resilient**: Circuit breakers and automatic fallback prevent failures
- **✅ Configurable**: Easy provider switching via environment variables
- **✅ Tested**: Comprehensive test suite validates all functionality
- **✅ Backward Compatible**: Existing code continues working without changes

---

# 🔧 DEBUGGING & IMPROVEMENT WORKFLOW

This section documents the collaborative debugging process for improving the Eevee AI system based on real session analysis.

## 📊 **Session Analysis & Issue Detection**

### **Step 1: Monitor Active Sessions**
```bash
# Check for current running sessions
ls -la /Users/wingston/code/claude-plays-pokemon/eevee/runs/session_*

# Monitor the latest session in real-time
tail -f runs/session_LATEST/session_data.json
```

### **Step 2: Identify Performance Issues**
Look for these warning signs in session data:
- **Template Degradation**: `"ai_directed_auto_select"` → `"fallback_exception"`
- **Button Spam**: `"button_presses"` with 4+ buttons in single turn
- **Empty Analysis**: `"ai_analysis": ""` indicates API failures
- **Stuck Patterns**: Repeated identical actions across turns

### **Example Issue Detection**
```json
// GOOD (Turn 20)
"template_used": "ai_directed_auto_select"
"ai_analysis": "Observation: The player is in a forest area..."

// BAD (Turn 21) 
"template_used": "fallback_exception"
"ai_analysis": ""
"button_presses": ["down", "down", "down", "down", "down"]
```

## 🛠️ **Root Cause Analysis Process**

### **Step 3: Trace System Failures**
1. **AI Template Selection Crash**: Check for `"playbook_to_include referenced before assignment"`
2. **Gemini API Issues**: Empty responses, rate limiting, timeout errors  
3. **Button Validation Missing**: 4+ buttons reaching game controller
4. **Error Propagation**: Single failure cascading to all subsequent turns

### **Step 4: Systematic Fix Implementation**

#### **🔴 Critical Fix 1: Variable Assignment Error**
```python
# BEFORE (causes crash)
if context_type == "auto_select":
    template_name, playbook_to_include = ai_select_function()
# playbook_to_include not defined for other contexts!

# AFTER (safe initialization)
playbook_to_include = "navigation"  # Safe default
if context_type == "auto_select":
    template_name, playbook_to_include = ai_select_function()
```

#### **🔴 Critical Fix 2: Button Press Validation**
```python
# Add to eevee_agent.py after button extraction
if len(result["button_presses"]) > 3:
    original_count = len(result["button_presses"])
    result["button_presses"] = result["button_presses"][:3]
    print(f"⚠️ BUTTON LIMIT ENFORCED: {original_count} → 3")
```

#### **🟠 High Priority Fix 3: Retry Logic with Exponential Backoff**
```python
def ai_select_with_retry(memory_context, escalation_level, verbose=False):
    for attempt in range(3):
        try:
            return ai_select_template(memory_context, escalation_level, verbose)
        except Exception as e:
            if attempt == 2:  # Last attempt
                return "exploration_strategy", "navigation"
            time.sleep(2 ** attempt)  # Exponential backoff
```

#### **🟡 Medium Priority Fix 4: Enhanced Error Logging**
```python
# Add detailed logging for debugging
if verbose:
    print(f"🔍 Memory Context Length: {len(memory_context)}")
    print(f"📤 Sending selection prompt to Gemini...")
    print(f"📥 Response Length: {len(response)}")
```

## 🔄 **Testing & Validation Cycle**

### **Step 5: Real-time Testing**
```bash
# Run controlled test session
python run_eevee.py --goal "explore and win pokemon battles" \
    --episode-review-frequency 4 --max-turns 12 --verbose

# Monitor for improvements
tail -f runs/session_LATEST/session_data.json | grep -E "(template_used|button_presses)"
```

### **Step 6: Validate Fixes**
- **Button Validation**: Confirm no turns have >3 buttons in JSON
- **Template Selection**: Verify AI selection working (not fallback_exception)
- **Error Recovery**: Check retry logic activates on failures
- **Performance**: Monitor navigation efficiency and success rates

### **Expected Results After Fixes**
```json
// FIXED: Proper AI template selection
"template_used": "ai_directed_auto_select"
"ai_analysis": "OBSERVATION: I see battle elements..."

// FIXED: Button enforcement working
"button_presses": ["up", "up", "up"]  // Truncated from 7 to 3
```

## 📈 **Continuous Improvement Process**

### **Step 7: Automated Analysis Script**
Use the enhanced `run_learn_fix.sh` to automate the full cycle:
```bash
bash run_learn_fix.sh  # Runs sessions + generates analysis prompt + launches Claude Code
```

### **Step 8: Documentation Updates**
After each major fix:
1. Update CLAUDE.md with new architecture details
2. Document error patterns and their solutions  
3. Add new testing procedures and validation checks
4. Record performance improvements and metrics

## 🎯 **Key Success Metrics**

- **Template Selection Reliability**: >95% using AI selection (not fallback)
- **Button Validation**: 0% of turns with >3 buttons  
- **API Resilience**: <5% empty analysis responses
- **Session Completion**: Sessions reach intended turn limits without crashes
- **Performance Trends**: Navigation efficiency and battle win rates improving

## 💡 **Lessons Learned**

1. **Real-time Monitoring**: Watch active sessions to catch issues immediately
2. **Progressive Debugging**: Fix critical crashes before optimizing performance  
3. **Defensive Programming**: Initialize variables, validate inputs, handle errors gracefully
4. **Collaborative Analysis**: Human insight + AI code analysis = effective debugging
5. **Systematic Testing**: Test each fix in isolation before combining

This workflow ensures robust, reliable AI Pokemon gameplay with continuous improvement capabilities.