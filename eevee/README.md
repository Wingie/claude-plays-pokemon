# Eevee v1 - AI Pokemon Task Execution System

Eevee is an advanced AI-powered Pokemon game automation system that can execute complex tasks through natural language commands. Built on the existing claude-plays-pokemon infrastructure, Eevee provides a sophisticated interface for Pokemon game interaction, analysis, and automation.

## Features

### Core Capabilities
- **Natural Language Task Execution**: Execute Pokemon tasks via simple commands
- **Multi-step Task Decomposition**: Break complex tasks into manageable steps
- **Persistent Memory System**: Remember game state and context across sessions
- **AI-Learned Playbooks**: Automatically discover and store navigation patterns and location knowledge
- **Enhanced Logging**: Clear observation-to-action reasoning chains with template identification

### Advanced Features
- **Smart Prompt Selection**: Context-aware prompt selection (battle/navigation/gym/services)
- **Dynamic Knowledge Learning**: AI populates playbooks with discovered information during gameplay
- **Intelligent Navigation**: Smart menu navigation with pattern learning and memory retention
- **Pokemon Data Parsing**: Extract and structure Pokemon party information
- **Comprehensive Debugging**: Full visibility into AI decision-making process with structured logging

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Basic Usage
```bash
# Continuous gameplay with enhanced logging (default)
python run_eevee.py --goal "find viridian forest"

# Interactive mode with full playbook system
python run_eevee.py --interactive --enable-okr

# Execute single Pokemon task
python run_eevee.py --task "check and report all your pokemon party and their levels and moves"

# Use specific memory session
python run_eevee.py --goal "navigate to Pokemon Center" --memory-session gym-challenge
```

### Advanced Usage
```bash
# Test the enhanced prompt system
python test_enhanced_prompts.py

# Continuous gameplay with auto-resume
python run_eevee.py --continue --verbose

# Interactive debugging mode
python run_eevee.py --interactive --debug --max-turns 20
```

## Architecture

### System Components

```
eevee/
├── run_eevee.py              # Main CLI interface with enhanced logging
├── eevee_agent.py            # Core AI agent with learning capabilities
├── memory_system.py          # Persistent memory management
├── prompt_manager.py         # Simplified prompt + playbook system
├── task_executor.py          # Multi-step task execution
├── test_enhanced_prompts.py  # Test suite for new features
├── utils/
│   ├── navigation.py         # Game menu navigation
│   ├── pokemon_parser.py     # Pokemon data extraction
│   └── reporting.py          # Output formatting
├── prompts/
│   ├── base/                 # Core prompt templates (YAML)
│   └── playbooks/            # AI-learned knowledge (Markdown)
│       ├── battle.md         # Battle strategies and move knowledge
│       ├── navigation.md     # AI-discovered location connections
│       ├── gyms.md          # Gym-specific strategies and puzzles
│       └── services.md       # Pokemon Centers, shops, facilities
├── memory/                   # Session databases
├── runs/                     # Continuous gameplay logs
└── analysis/                 # Screenshots and analysis
```

### Key Classes

- **EeveeAgent**: Main orchestration class with AI learning capabilities (`learn_navigation_pattern`, `learn_location_knowledge`)
- **MemorySystem**: SQLite-based persistent memory with context retrieval
- **PromptManager**: Simplified template + playbook system with dynamic loading (`get_prompt`, `add_playbook_entry`)
- **TaskExecutor**: Multi-step execution engine with error recovery
- **ContinuousGameplay**: Simplified logging with turn-by-turn action recording and button press validation
- **PokemonParser**: Extract structured data from AI analysis text

## Enhanced Logging & Playbook System

### Logging Format
The simplified logging system provides clear insight into AI decisions with a clean one-line format:

```
🎮 TURN 1: Pressed ['up'] - 🎯 **OBSERVATION**: The player character is in Viridian City, standing on a patch of grass. To the no...
🎮 TURN 2: Pressed ['up'] - 🎯 **OBSERVATION**: The player character is at the edge of Viridian City, on a patch of grass. To th...
🎮 TURN 3: Pressed ['right'] - 🎯 **OBSERVATION**: The player character is at the edge of Viridian City, near the north exit. To th...
```

**Key Features:**
- **Turn Number**: Clear turn tracking
- **Button Sequence**: Exactly what buttons were pressed
- **AI Reasoning**: First 100 characters of AI's observation and analysis
- **Template Info**: Shows which prompt template and playbooks were used (via separate log line)

### AI Learning System
The AI automatically learns and documents discoveries:

- **📝 Navigation Learning**: `Learned: Viridian City --north--> Viridian Forest`
- **📚 Location Knowledge**: `Learned about Viridian City: Has a Pokemon Center in the center of town`
- **🎯 Battle Memory**: Enhanced move selection with type effectiveness

### Playbook System
Knowledge is organized into specialized playbooks:

- **battle.md**: Static expert knowledge for battle strategies and type effectiveness
- **navigation.md**: AI-discovered location connections and route patterns
- **gyms.md**: Gym-specific strategies, leader info, and puzzle solutions
- **services.md**: Pokemon Centers, shops, and facility locations

### Smart Context Selection
The system intelligently chooses appropriate prompts and playbooks:

- **Battle contexts** → `battle_analysis` + `battle` playbook
- **Gym battles** → `battle_analysis` + `battle` + `gyms` playbooks
- **Navigation** → `location_analysis` + `navigation` playbook
- **Services** → `location_analysis` + `services` playbook

## Task Examples

### Pokemon Party Management
```bash
# Check party status
python run_eevee.py "show me all Pokemon in my party with their levels and health"

# Analyze moves and PP
python run_eevee.py "list all moves for each Pokemon and their remaining PP"

# Find Pokemon needing healing
python run_eevee.py "which Pokemon need healing and what are their status conditions"
```

### Navigation and Exploration
```bash
# Location analysis
python run_eevee.py "where am I and what can I do here"

# Find specific locations
python run_eevee.py "navigate to the nearest Pokemon Center"

# Explore current area
python run_eevee.py "what items and trainers are available in this area"
```

### Battle and Strategy
```bash
# Battle analysis
python run_eevee.py "analyze the current battle situation and recommend next move"

# Type effectiveness
python run_eevee.py "what moves would be most effective against the opponent Pokemon"

# Party preparation
python run_eevee.py "prepare my party for the upcoming gym battle"
```

### Inventory Management
```bash
# Check items
python run_eevee.py "show me all items in my bag and their quantities"

# Find specific items
python run_eevee.py "do I have any healing items and how many"

# Inventory recommendations
python run_eevee.py "what items should I buy for upcoming challenges"
```

## Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key    # Required: Gemini AI API key
```

### Command Line Options
- `--model`: AI model to use (default: gemini-flash-2.0-exp)
- `--memory-session`: Memory session name (default: "default")
- `--output-format`: Output format (text, json, markdown)
- `--save-report`: Save detailed report to file
- `--verbose`: Enable verbose output
- `--debug`: Enable debug mode
- `--dry-run`: Analyze without executing actions
- `--max-steps`: Maximum execution steps (default: 50)
- `--window-title`: Emulator window title (default: "mGBA - 0.10.5")

## Memory System

Eevee uses a sophisticated memory system to maintain context across sessions:

### Session-Based Storage
- Each memory session is stored in a separate SQLite database
- Game states, task history, and learned knowledge are persisted
- Context retrieval based on task similarity and relevance

### Memory Types
- **Game States**: Pokemon party, location, inventory snapshots
- **Task History**: Previous task executions and results
- **Learned Knowledge**: Pokemon data, location info, strategies
- **Context Memories**: General contextual information

### Memory Commands
```bash
# Clear session memory
python run_eevee.py "any task" --clear-memory

# Use specific session
python run_eevee.py "task" --memory-session my-playthrough

# Export session data
python -c "from memory_system import MemorySystem; m=MemorySystem('session'); m.export_session()"
```

## Prompt System

Eevee uses a simplified but powerful prompt system with AI-learned playbooks:

### Core Prompt Templates
Base prompts are stored in YAML format with variable substitution:
```yaml
battle_analysis:
  template: |
    Analyze this Pokemon battle situation:
    Task Context: {task}
    # ... detailed battle analysis prompt
```

### Playbook Integration
```python
from prompt_manager import PromptManager

pm = PromptManager()

# Get context-appropriate prompt with playbook
prompt = pm.get_prompt(
    "battle_analysis", 
    {"task": "win this gym battle"}, 
    include_playbook="battle",
    verbose=True
)

# AI learning - automatically populate playbooks
agent.learn_navigation_pattern("Viridian City", "north", "Viridian Forest")
agent.learn_location_knowledge("Viridian City", "Has a Pokemon Center", "services")
```

### Usage Tracking
```python
# Get usage summary for debugging
summary = pm.get_usage_summary()
print(summary)

# Reload templates during development
pm.reload_templates()
```

## Integration

Eevee integrates seamlessly with the existing claude-plays-pokemon infrastructure:

### Required Dependencies
- Pokemon Controller (from main project)
- Gemini API wrapper
- mGBA or SkyEmu emulator
- macOS Quartz integration (for macOS)

### Emulator Support
- **mGBA**: Primary Game Boy/Game Boy Color support
- **SkyEmu**: Game Boy Advance support via MCP server
- **PyBoy**: Alternative Game Boy emulation (via VideoGameBench)

## Button Press Validation System

Eevee v1 enforces step-by-step thinking with automatic button press validation:

### Validation Features
- **Maximum Limit**: AI cannot press more than 3 buttons in one turn
- **Automatic Truncation**: If AI tries to exceed limit, only first 3 buttons are executed
- **Valid Button Check**: Only Game Boy buttons accepted (up, down, left, right, a, b, start, select)
- **Warning System**: Clear messages when AI exceeds limits or uses invalid buttons
- **Fallback Safety**: Defaults to 'a' button if no valid actions provided

### Recent Actions Memory
- **Turn Tracking**: Last 5 turns stored with observation → action → result chains
- **Loop Detection**: Warns when AI repeats same action 3+ times consecutively
- **Context Integration**: Recent actions summary included in all AI prompts via `{recent_actions}` variable
- **Pattern Recognition**: Identifies when AI is stuck and provides warnings

## Troubleshooting

### Common Issues
1. **AI Stuck in Loops**: Check recent actions log for repetitive button presses
2. **Button Validation Warnings**: AI is trying to exceed 3-button limit - prompts working correctly
3. **Invalid Button Messages**: AI attempted non-Game Boy button - validation working correctly
4. **Game window not found**: Ensure emulator is running with correct window title
5. **API key errors**: Verify GEMINI_API_KEY is set correctly

### Infinite Loop Investigation
If AI gets stuck pressing the same button repeatedly:
1. Check the recent actions warning in console output
2. Verify the AI receives the loop warning in its context
3. Consider if the game state requires a different approach (interaction vs movement)
4. Next session: investigate why loop detection didn't prevent the behavior

## Development

### Adding New Task Types
1. Create prompt template in `prompts/base/base_prompts.yaml`
2. Add parsing logic to `pokemon_parser.py` if needed
3. Extend `TaskExecutor` with specific execution logic
4. Test with various Pokemon game scenarios

### Extending Memory System
1. Add new table schema to `MemorySystem._init_database()`
2. Implement storage and retrieval methods
3. Update context retrieval algorithms
4. Add memory analytics and reporting

### Custom Prompt Strategies
1. Update templates in `prompts/base/base_prompts.yaml`
2. Test with real Pokemon game scenarios
3. Monitor button press patterns and effectiveness
4. Ensure all templates enforce 1-3 button maximum

## Troubleshooting

### Common Issues
1. **Game window not found**: Ensure emulator is running with correct window title
2. **API key errors**: Verify GEMINI_API_KEY is set correctly
3. **Memory database locked**: Close other Eevee instances using same session
4. **Import errors**: Ensure all dependencies are installed

### Debug Mode
```bash
python run_eevee.py "task" --debug --verbose
```

### Log Files
- Execution logs: `eevee/analysis/`
- Memory databases: `eevee/memory/`
- Generated reports: `eevee/reports/`

## License

Part of the claude-plays-pokemon project. See main project LICENSE for details.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues, questions, or contributions, please use the main claude-plays-pokemon repository issue tracker.