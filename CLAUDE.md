# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

IMPORTANT DIRECTIVE FROM BOSS:
You MUST use SERENA tooling for reading and writing code while working on this project! FIRST PRIORITY IS SERENA TOOLS ALWAYS REMEMBER! if you dont know it, read serena.md

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
- **API rate limiting**: Intelligent delays and caching for Gemini calls
- **Memory management**: Cleanup of temporary screenshots and game states
- **Real-time constraints**: Fast response times for smooth gameplay

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
- **SkyEmu Integration**: Native integration with SkyEmu emulator via HTTP API
- **Persistent Memory**: SQLite-based session management with context retrieval
- **Multi-step Execution**: Automatic task decomposition with error recovery
- **Prompt Experimentation**: A/B testing framework for prompt optimization
- **Comprehensive Reporting**: Detailed analysis and execution reports

### Usage Examples
```bash
# Party management
python eevee/run_eevee.py "check and report all your pokemon party and their levels and moves and what PP left in each move"

# Navigation tasks
python eevee/run_eevee.py "navigate to Pokemon Center" --verbose

# Battle analysis
python eevee/run_eevee.py "analyze current battle situation and recommend next move"

# Inventory management
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

### Development Status
✅ **v1 Complete**: Fully implemented and tested with SkyEmu integration
🚧 **v2 Planning**: VLLM training data collection and RL scoring system