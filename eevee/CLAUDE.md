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

### **LLM API System**
```
eevee/
├── llm_api.py                # Centralized LLM API with provider abstraction
├── provider_config.py        # Environment-based configuration management
├── .env                      # Provider API keys and configuration
├── .env.example             # Configuration template and examples
├── switch_provider.py        # Provider switching demonstration script
└── tests/
    ├── test_llm_api.py       # LLM API system tests
    ├── test_provider_config.py # Configuration system tests
    └── test_*_migration.py   # Migration validation tests
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