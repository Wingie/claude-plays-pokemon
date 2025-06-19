# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

IMPORTANT DIRECTIVE FROM BOSS:
You MUST use SERENA tooling for reading and but not WRITING code while working on this project! FIRST PRIORITY IS SERENA TOOLS ALWAYS REMEMBER! if you dont know it, read serena.md

## Repository Overview

This is a comprehensive AI-powered Pokemon gaming project that uses Google Gemini AI to automatically play Pokemon games through multiple emulator interfaces. The project combines multimodal AI reasoning, real-time game control, and advanced emulation technology to create intelligent Pokemon-playing agents.

## Project Structure

### Core Components
- **Root Pokemon Controller**: Basic Gemini-powered Pokemon gameplay (`run_step_gemini.py`)
- **Eevee v1**: Advanced AI task execution system with natural language interface (`eevee/`)
- **VideoGameBench Integration**: Comprehensive VLM evaluation framework for game benchmarking
- **SkyEmu MCP Server**: Model Context Protocol server for advanced Game Boy Advance emulation
- **Gemini Multimodal Playground**: Experimental AI features with RL integration

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

### Recent Breakthroughs (June 18, 2025)

**🎯 Major API Integration Success**
- **Fixed Critical Issue**: Replaced non-existent Claude-style API wrapper with native Google Gemini API
- **Unified Architecture**: Created single `_call_gemini_api()` method eliminating code complexity
- **Proper Tool Calling**: Implemented correct Google Gemini FunctionDeclaration format
- **Valid Model Names**: Updated to use `gemini-1.5-flash` with multimodal support

**🎮 Continuous Gameplay Achievement**
- **Action Loop Working**: Screenshot → AI analysis → button press → memory update cycles operational
- **Battle Decision Making**: AI successfully analyzes Pokemon battles and makes strategic decisions
- **Memory Integration**: Turn data stored in SQLite with session persistence
- **Real-time Logging**: Complete audit trail in runs/ directory with `tail -f` monitoring

**⚠️ Previous Limitations Resolved**
- **✅ Menu Navigation**: Enhanced battle prompts with explicit move navigation ([down, a] for Thundershock)
- **✅ Context Memory**: Battle memory summaries injected into each turn's prompt
- **✅ Button Sequence Logic**: Memory-driven learning system for move effectiveness

**🔧 Latest API Resilience Improvements (June 19, 2025)**
- **Smart Timeout Handling**: Exponential backoff with 3-retry maximum for connection issues
- **429 Rate Limit Detection**: Intelligent parsing of retry delays from API error responses
- **Circuit Breaker Pattern**: Automatic API suspension after 5 consecutive failures (5-minute cooldown)
- **Jitter & Capping**: Random jitter in delays with reasonable maximums (1 minute retry, 5 minute circuit breaker)
- **Failure Recovery**: Automatic success tracking and circuit breaker reset after recovery

**✅ Implementation Complete: Memory-Driven Battle Intelligence & API Resilience**

**🗺️ Latest Overworld Navigation Intelligence (June 19, 2025)**
- **ASCII Grid Overlay System**: 8x8 tile-based visual overlay using HSV color analysis for terrain detection
- **Smart Obstacle Detection**: Trees (T), buildings (B), walls (#), water (~) vs walkable areas (.) and paths (-)
- **Memory-Based Area Tracking**: Visited areas marked with (*) to show exploration history
- **Adaptive Prompting**: Context-aware prompts that include ASCII grid and navigation intelligence when in overworld
- **Movement Recording**: Automatic tracking of overworld movements for route learning and backtracking
- **Integrated Intelligence**: Seamless switching between battle prompts and overworld navigation based on game state

**🎯 SOLUTION IMPLEMENTED: Prompting + Memory (Not State Machines)**
Successfully implemented the `run_step_memory.py` approach using enhanced prompting and memory rather than complex code logic.

**✅ Issues Resolved:**
1. **Attack Selection Problem**: AI now properly navigates to specific moves like Thundershock
   - **Solution**: Enhanced battle prompts with explicit move navigation: ["down", "a"] for Thundershock
   - **Result**: AI can now select specific moves instead of just spamming 'A' button
   
2. **Context Loss**: AI remembers previous battle actions and outcomes
   - **Solution**: Battle memory summaries injected into each turn's prompt context
   - **Result**: Learning from previous battles and move effectiveness

3. **Interruption Support**: Real-time interruption during continuous gameplay
   - **Solution**: Threaded keyboard monitoring with queue-based communication
   - **Result**: 'p'=pause, 'r'=resume, 'q'=quit commands work during gameplay

**🎮 New Features Available:**
- **Enhanced Battle Prompts**: Include Pokemon type effectiveness and move navigation
- **Battle Memory Learning**: Store move effectiveness and successful strategies
- **Real-time Interruption**: Claude Code-like pause/resume/quit controls
- **Prompt-based Intelligence**: Battle knowledge embedded directly in AI prompts

**Usage Examples:**
```bash
# Standard continuous gameplay with battle improvements
python eevee/run_eevee.py --continuous --goal "find and win pokemon battles"

# With real-time interruption controls
python eevee/run_eevee.py --continuous --goal "find and win pokemon battles" --interruption
```

**🎯 Expected Results**: AI will now properly navigate to "Thundershock" using DOWN → A sequence, remember battle outcomes, and allow real-time interruption during gameplay.