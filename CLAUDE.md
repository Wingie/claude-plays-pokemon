# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive AI-powered Pokemon gaming project that uses Google Gemini AI to automatically play Pokemon games through multiple emulator interfaces. The project combines multimodal AI reasoning, real-time game control, and advanced emulation technology to create intelligent Pokemon-playing agents.

## Project Structure

### Core Components
- **Root Pokemon Controller**: Basic Gemini-powered Pokemon gameplay (`run_step_gemini.py`)
- **Eevee v1**: Advanced AI task execution system with natural language interface (`eevee/`) (workinf Project)
- **VideoGameBench Integration**: Comprehensive VLM evaluation framework for game benchmarking
- **SkyEmu MCP Server**: Model Context Protocol server for advanced Game Boy Advance emulation (not used)
- **Gemini Multimodal Playground**: samplre old code (only refee)

### Key Entry Points
- `run_step_gemini.py`: legacy Pokemon controller using mGBA emulator
- `eevee/run_eevee.py`: Eevee v1 AI task execution system - OUR VERSINO
- `videogamebench/main.py`: legacy game evaluation framework
- `skyemu-mcp/run_server.py`: MCP server for SkyEmu integration
- `test_setup.py`: Environment validation and setup verification

## Development Commands

### Setup and Installation
```bash
# Quick setup
./setup.sh

# Manual installation
pip install -r requirements.txt

# Test environment
python test_setup.py

# VideoGameBench setup (ALREADY INSTALLED SO JS)
cd videogamebench
# conda create -n videogamebench python=3.10
conda activate videogamebench
pip install -r requirements.txt
pip install -e .
playwright install
```

### Running Applications
```bash
# Basic Pokemon controller (requires mGBA running)
python run_step_gemini.py

# Eevee v1 AI task execution system (requires SkyEmu running on port 8080)
python eevee/run_eevee.py "check and report all your pokemon party and their levels and moves and what PP left in each move"
python eevee/run_eevee.py "navigate to Pokemon Center" --verbose --save-report

# Interactive Mode - Claude Code-like interface for real-time Pokemon guidance
python eevee/run_eevee.py --interactive --enable-okr --neo4j-memory
python eevee/run_eevee.py --interactive --enable-okr --continue  # Auto-resume gameplay

# VideoGameBench with various models
python videogamebench/main.py --game pokemon_red --model gpt-4o
python videogamebench/main.py --game pokemon_crystal --model gemini/gemini-2.0-flash --enable-ui

# SkyEmu MCP server (WILL ALREADY BE RUNNING BY THE USER AND HE WILL SAVE AND LOAD THE GAME)
```

## Architecture Overview

### Multi-Layer Architecture
The project uses a layered approach:
1. **AI Decision Layer**: Gemini API for strategic reasoning and task decomposition
2. **Task Execution Layer**: Eevee v1 system for natural language task execution
3. **Control Layer**: Platform-specific input simulation (PyAutoGUI + macOS Quartz, SkyEmu HTTP API)
4. **Emulation Layer**: Multiple emulators (mGBA, SkyEmu, PyBoy)
5. **Integration Layer**: REST APIs and MCP protocols for advanced control
6. **Memory Layer**: Persistent context and session management (SQLite)

### Key Design Patterns
- **Controller Pattern**: Separate emulator controllers with unified interfaces
- **Strategy Pattern**: Swappable AI agents (RL, LLM, Hybrid)
- **Adapter Pattern**: Unified LLM interface across providers
- **Observer Pattern**: Game state monitoring and progress tracking

### Platform-Specific Integration (macOS)
- Native **Quartz framework** for window management and screen capture
- **PyObjC** for Objective-C bridge functionality
- Optimized for **Apple Silicon** and **Core Graphics**
- Requires accessibility permissions for input simulation

## Technical Stack

### Core Technologies
- **Python 3.8+** (3.10+ for VideoGameBench)
- **Google Gemini API** for multimodal AI reasoning
- **PyAutoGUI** + **macOS Quartz** for input simulation
- **PIL/Pillow** for image processing and screenshot management
- **LiteLLM** for unified LLM API access
- **FastAPI** for REST API development
- **PyTorch** for RL agent implementation

### Emulation Platforms
- **mGBA**: Game Boy/Game Boy Color emulation
- **SkyEmu**: Game Boy Advance emulation with HTTP control
- **PyBoy**: Python Game Boy emulator (in VideoGameBench)
- **JS-DOS**: DOS game emulation (in VideoGameBench)

## Configuration Management

### Environment Variables
```bash
# Required for all AI functionality
GEMINI_API_KEY=your_api_key_here

# Create .env file or set in environment
echo "GEMINI_API_KEY=your_key" > .env
```

### Game Configuration
- **VideoGameBench configs**: YAML files in `videogamebench/configs/`
- **ROM management**: Place game ROMs in `videogamebench/roms/`
- **Save states**: Managed in project root and `videogamebench/saves/`

## Development Workflow

### Standard Development Process
1. **Setup**: Run `./setup.sh` and `python test_setup.py`
2. **Development**: Modify code with attention to emulator compatibility
3. **Testing**: Test with actual emulators and game ROMs
4. **Integration**: Verify cross-component compatibility

### Code Style and Conventions
- **PascalCase** for classes (`PokemonController`, `GeminiAPI`)
- **snake_case** for functions and files (`press_button`, `capture_screen`)
- **Google-style docstrings** for documentation
- **Type hints** used consistently throughout
- **Error handling** with graceful degradation and informative messages

### Testing Approach
- **Environment validation**: Use `test_setup.py` to verify setup
- **Integration testing**: Real emulator testing with actual Pokemon games
- **Platform testing**: macOS-specific window management and screen capture
- **API testing**: Gemini API connectivity and response handling
- **Resilience testing**: API timeout, rate limiting, and circuit breaker functionality

## Common Development Tasks

### Adding New Games
1. Add ROM mapping in `videogamebench/src/consts.py`
2. Create game config in `videogamebench/configs/[game]/`
3. Add game-specific prompts and settings
4. Test with target emulator platform

### Extending AI Capabilities
1. Modify prompts in game configs or main controller
2. Update action parsing in `gemini_api.py`
3. Test AI decision-making with various game scenarios
4. Monitor API costs and response quality

### Platform Integration
1. Ensure macOS Quartz integration for screen capture
2. Test window finding and focus functionality
3. Verify accessibility permissions are sufficient
4. Handle platform-specific edge cases

## Important Notes

### Security and Privacy
- **Never commit API keys** - use `.env` files (gitignored)
- **ROM files excluded** - users must provide their own legally-owned games
- **Save files protected** - personal game progress excluded from repository

### Performance Considerations
- **Screenshot optimization**: JPEG compression for AI processing
- **API resilience**: Smart timeout handling, exponential backoff, and circuit breaker protection
- **Rate limiting**: Intelligent 429 error detection with retry delay parsing
- **Memory management**: Cleanup of temporary screenshots and game states
- **Real-time constraints**: Fast response times for smooth gameplay with failure recovery

### macOS-Specific Requirements
- **Accessibility permissions** required for input simulation
- **Screen recording permissions** needed for screenshot capture
- **PyObjC dependencies** for native API access
- **Homebrew recommended** for dependency management

### No Automated Linting
The project does not use automated linting or formatting tools. Code quality is maintained through manual review, comprehensive testing, and adherence to documented conventions.

## Eevee v1 - AI Task Execution System

Eevee v1 is the primary interface for AI-powered Pokemon task execution. It provides sophisticated natural language processing capabilities with persistent memory and multi-step task decomposition.

### Key Features
- **Natural Language Interface**: Execute complex Pokemon tasks via simple commands
- **Interactive Mode**: Claude Code-like chat interface for real-time guidance and interruption
- **SkyEmu Integration**: Native integration with SkyEmu emulator via HTTP API
- **Continuous Game Loop**: Screenshot → Gemini analysis → button press → memory update cycles
- **Persistent Memory**: SQLite-based session management with Neo4j visual memory
- **Multi-step Execution**: Automatic task decomposition with error recovery and pause/resume
- **Real-time Logging**: Live monitoring with `tail -f` support in runs/ folder
- **Navigation Intelligence**: Route learning, location memory, and pathfinding
- **OKR Progress Tracking**: Automatic objectives and key results updates
- **Session Continuity**: Resume gameplay from previous sessions
- **🧠 AI-Powered Template Learning**: Gemini 2.0 Flash automatically improves prompt templates based on gameplay performance

### Usage Examples
```bash
# Party management
python eevee/run_eevee.py "check and report all your pokemon party and their levels and moves and what PP left in each move"

# Navigation tasks
python eevee/run_eevee.py "navigate to Pokemon Center" --verbose

# Interactive mode with full features
python eevee/run_eevee.py --interactive --enable-okr --neo4j-memory

# Auto-resume continuous gameplay
python eevee/run_eevee.py --interactive --enable-okr --continue

# Battle analysis
python eevee/run_eevee.py "analyze current battle situation and recommend next move"

# Inventory management with real-time monitoring
python eevee/run_eevee.py "check what healing items I have in my bag" --save-report

# 🧠 AI-POWERED CONTINUOUS LEARNING (NEW!)
# The system automatically improves its own prompts every N turns
python eevee/run_eevee.py --goal "walk around and win pokemon battles" --verbose --episode-review-frequency 4 --max-turns 12 --no-interactive

# Long-running self-improvement sessions
python eevee/run_eevee.py --goal "complete pokemon red" --episode-review-frequency 10 --max-turns 100
```

### Architecture Components
- **EeveeAgent**: Main orchestration class with SkyEmu integration
- **MemorySystem**: SQLite-based persistent memory with session isolation
- **TaskExecutor**: Multi-step task decomposition engine
- **PromptManager**: Template-based prompt system with A/B testing
- **NavigationHelper**: Smart menu navigation with state tracking
- **PokemonParser**: Extract structured data from AI analysis

### Memory Sessions
Eevee v1 supports persistent memory sessions for maintaining context across runs:
```bash
# Use specific session
python eevee/run_eevee.py "task" --memory-session gym-challenge

# Clear session memory
python eevee/run_eevee.py "task" --clear-memory
```

### Interactive Commands
```bash
# Available in interactive mode:
/pause          # Pause current gameplay
/resume         # Resume gameplay  
/status         # Show game connection and task status
/memory         # Display memory system status
/okr            # Show objectives and progress
/reset-memory   # Clear navigation memory for fresh test
/show-route     # Display known routes
/location-stats # Show location recognition confidence
/play           # Start continuous autonomous gameplay
/goal           # Show current USER_GOAL and suggest task
/help           # Show all commands
/quit           # Exit interactive mode
```

### Real-time Monitoring
```bash
# Monitor game progress in real-time
tail -f runs/TIMESTAMP_session.log

# Watch screenshot analysis
ls -la runs/TIMESTAMP_screenshots/

# Check memory updates
tail -f runs/TIMESTAMP_memory.log
```

### Development Status
✅ **v1 Complete**: Interactive mode with continuous game loop implementation
✅ **Phase 1**: Basic task execution system with SkyEmu integration
✅ **Phase 2**: Interactive Claude Code-like interface with pause/resume
✅ **Phase 3**: Navigation testing framework with memory retention
✅ **Phase 4**: Core game loop implementation (screenshot → AI → action → memory)

### Recent Breakthroughs (June 19, 2025)

**🎮 Evening Session: Simplified Logging & Step-by-Step AI (CURRENT)**
- **Revolutionary Logging**: Replaced complex bordered logs with clean one-line format: `🎮 TURN X: Pressed [buttons] - reasoning...`
- **Button Press Validation**: Enforced 1-3 button maximum with automatic warnings when AI exceeds limits
- **Recent Actions Memory**: Turn-by-turn recording with observation → action → result chains included in prompt context
- **Step-by-step Enforcement**: All prompt templates now specify "Maximum 1-2 button presses (never more than 3)"
- **Enhanced Context Detection**: Improved battle vs navigation vs party vs inventory prompt selection
- **⚠️ Critical Issue**: AI stuck in infinite UP loop at Viridian City edge - needs investigation next session

**🎯 Previous: Enhanced Prompt System & Logging Revolution**
- **Simplified PromptManager**: Removed complex A/B testing, kept core template + playbook functionality
- **AI-Learned Playbooks**: Navigation knowledge automatically discovered and stored by AI during gameplay
- **Intelligent Context Selection**: Dynamic prompt selection based on game state (battle/navigation/gym/services)
- **Enhanced Observation Logging**: Clear 🎯 OBSERVATION → 🧠 ANALYSIS → ⚡ ACTION chains with template identification

**🎮 Smart Playbook System**
- **Battle Playbook**: Static expert knowledge for move selection and type effectiveness
- **Navigation Playbook**: AI discovers location connections ("Viridian City --north--> Viridian Forest")
- **Gym Playbook**: AI learns gym-specific strategies and puzzle solutions
- **Services Playbook**: AI maps Pokemon Centers, shops, and facilities
- **Dynamic Loading**: Appropriate playbooks automatically selected based on context

**🔧 Advanced Logging & Debugging**
- **Template Source Tracking**: Shows exactly which prompt template and playbooks are being used
- **Structured Analysis Display**: Clear observation-to-action reasoning chains
- **Real-time Knowledge Learning**: AI discoveries logged and stored for future use
- **Verbose Mode Enhancement**: Comprehensive insight into AI decision-making process

**🗺️ Intelligent Navigation System**
- **Context-Aware Prompting**: Battle contexts use battle prompts, navigation uses location prompts
- **Multi-Playbook Integration**: Gym battles combine battle + gym knowledge automatically
- **Goal-Driven Selection**: User goals influence which playbooks are loaded
- **Learning Integration**: AI automatically populates playbooks with discoveries

**✅ Implementation Complete: Enhanced Prompt System & AI Learning**

**🎯 New Logging Format:**
```
================================================================================
🎮 TURN 15 - AI DECISION PROCESS  
================================================================================
📖 PROMPT SOURCE: base/battle_analysis + playbook/battle
🎯 OBSERVATION: I can see the battle menu with FIGHT, BAG, POKEMON, RUN options
🧠 ANALYSIS: This is the start of a Pokemon battle, I should select FIGHT to access moves
⚡ BUTTON SEQUENCE: ['a']
================================================================================
```

**🧠 AI Learning in Action:**
- **Navigation**: `📝 Learned: Viridian City --north--> Viridian Forest`
- **Services**: `📚 Learned about Viridian City: Has a Pokemon Center in the center of town`
- **Battle Memory**: Enhanced move selection with type effectiveness knowledge

**🎮 Enhanced Features Available:**
- **Smart Template Selection**: AI chooses appropriate prompts based on game context
- **Knowledge Discovery**: AI learns and documents Pokemon world geography and services
- **Comprehensive Debugging**: Full visibility into AI reasoning and template usage
- **Playbook System**: Organized, learnable knowledge base for different game contexts

**Usage Examples:**
```bash
# Enhanced continuous gameplay with improved logging (no verbose flag needed)
python eevee/run_eevee.py --goal "find viridian forest"

# Interactive mode with full playbook system
python eevee/run_eevee.py --interactive --enable-okr

# Test the enhanced prompt system
python eevee/test_enhanced_prompts.py
```

**🎯 Expected Results**: AI now provides clear insight into its decision-making process, learns navigation patterns automatically, and selects appropriate knowledge based on current game context.

## 🧠 AI-Powered Template Learning System (Revolutionary!)

**Implementation Complete**: The most advanced AI learning system yet developed for Pokemon automation.

### How It Works

#### **🔄 Continuous Learning Loop**
```
Every N turns:
1. 📊 Analyze recent gameplay performance
2. 🤖 Gemini analyzes which templates caused failures  
3. 🛠️ Gemini 2.0 Flash generates improved templates
4. 💾 Templates auto-saved to disk with version tracking
5. 🔄 System reloads and uses improved templates immediately
```

#### **🎯 Smart Failure Detection**
- **Stuck Pattern Analysis**: Detects repeated button sequences (like pressing 'A' 3+ times)
- **Loop Detection**: Identifies when AI gets stuck in menu loops
- **Progress Tracking**: Monitors actual game progress vs just button success
- **Template Attribution**: Links specific templates to poor performance

#### **🚀 Usage Examples**

```bash
# Quick 5-turn learning cycles for rapid improvement
python eevee/run_eevee.py --goal "win battles" --episode-review-frequency 5 --max-turns 20 --verbose

# Long-term learning session (recommended)
python eevee/run_eevee.py --goal "complete pokemon red" --episode-review-frequency 15 --max-turns 200

# Watch the AI learn in real-time
python eevee/run_eevee.py --goal "explore viridian forest" --episode-review-frequency 8 --max-turns 50 --verbose
```

#### **📁 Output Files**
```
eevee/runs/session_TIMESTAMP/
├── session_data.json           # Turn-by-turn data with template usage
├── periodic_review_turn_5.md   # AI analysis of what went wrong
├── periodic_review_turn_10.md  # Continuous improvement tracking
└── screenshots/                # Visual evidence of failures

eevee/prompts/base/
└── base_prompts.yaml          # Templates automatically improved by AI
```

#### **🔍 Real-Time Monitoring**
```bash
# Watch live gameplay analysis
tail -f eevee/runs/session_*/periodic_review_turn_*.md

# Monitor template versions
grep "version:" eevee/prompts/base/base_prompts.yaml

# Check improvement logs
🔧 AI-POWERED PROMPT LEARNING: Applied 2 improvements
   📝 battle_analysis v4.0 → v4.1
      Reason: Improved move selection logic for type effectiveness
   📝 exploration_strategy v2.1 → v2.2  
      Reason: Better stuck pattern recovery
```

#### **🎖️ Key Benefits**
- **Self-Improving**: Templates get better automatically through gameplay
- **Context-Aware**: Only improves templates that actually caused failures
- **Intelligent**: Uses Gemini 2.0 Flash for sophisticated prompt engineering
- **Persistent**: All changes saved with version tracking and reasoning
- **Immediate**: Improved templates used in the same session

#### **🧪 Testing the System**
```bash
# Test with failure-prone scenarios (AI gets stuck in battles/menus)
python eevee/run_eevee.py --goal "defeat brock without type advantage" --episode-review-frequency 6 --max-turns 18

# Test with navigation challenges
python eevee/run_eevee.py --goal "find hidden items in viridian forest" --episode-review-frequency 4 --max-turns 16

# Continuous improvement loop (let it run for hours)
python eevee/run_eevee.py --goal "become pokemon champion" --episode-review-frequency 20 --max-turns 500
```

#### **🔧 Template Selection Integration** 
The learning system only improves templates that are actually used:
- `battle_analysis` - Pokemon battle decisions
- `exploration_strategy` - Overworld navigation
- `stuck_recovery` - Loop and stuck pattern handling
- `pokemon_party_analysis` - Party management
- `task_analysis` - Goal-oriented behavior

**Never** tries to improve unused or fallback templates, ensuring focused learning.

### Expected Performance Evolution
- **Hour 1**: Basic gameplay with occasional stuck patterns
- **Hour 2-3**: Templates learn to avoid common failure modes  
- **Hour 4+**: Sophisticated gameplay with context-aware decision making
- **Day 1+**: Expert-level Pokemon strategy with minimal human intervention

This system represents the cutting edge of AI self-improvement for game automation!