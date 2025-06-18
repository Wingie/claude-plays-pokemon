# Eevee v1 - AI Pokemon Task Execution System

Eevee is an advanced AI-powered Pokemon game automation system that can execute complex tasks through natural language commands. Built on the existing claude-plays-pokemon infrastructure, Eevee provides a sophisticated interface for Pokemon game interaction, analysis, and automation.

## Features

### Core Capabilities
- **Natural Language Task Execution**: Execute Pokemon tasks via simple commands
- **Multi-step Task Decomposition**: Break complex tasks into manageable steps
- **Persistent Memory System**: Remember game state and context across sessions
- **Prompt Experimentation**: A/B test different AI prompting strategies
- **Comprehensive Reporting**: Generate detailed analysis reports in multiple formats

### Advanced Features
- **Intelligent Navigation**: Smart menu navigation with state tracking
- **Pokemon Data Parsing**: Extract and structure Pokemon party information
- **Memory Management**: Session-based context persistence with SQLite backend
- **Performance Tracking**: Monitor task success rates and execution metrics
- **Extensible Architecture**: Modular design for easy enhancement and customization

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
# Execute a Pokemon task
python run_eevee.py "check and report all your pokemon party and their levels and moves and what PP left in each move"

# Save detailed report
python run_eevee.py "analyze current location" --save-report --output-format markdown

# Use specific memory session
python run_eevee.py "navigate to Pokemon Center" --memory-session gym-challenge

# Dry run (analysis only)
python run_eevee.py "find wild Pokemon to catch" --dry-run
```

### Advanced Usage
```bash
# Use experimental prompts
python run_eevee.py "check inventory" --prompt-experiment detailed-analysis

# Verbose execution
python run_eevee.py "heal all Pokemon" --verbose --debug

# JSON output
python run_eevee.py "analyze battle situation" --output-format json
```

## Architecture

### System Components

```
eevee/
├── run_eevee.py              # Main CLI interface
├── eevee_agent.py            # Core AI agent
├── memory_system.py          # Persistent memory management
├── prompt_manager.py         # Prompt experimentation system
├── task_executor.py          # Multi-step task execution
├── utils/
│   ├── navigation.py         # Game menu navigation
│   ├── pokemon_parser.py     # Pokemon data extraction
│   └── reporting.py          # Output formatting
├── prompts/
│   ├── base/                 # Core prompt templates
│   └── experimental/         # A/B testing prompts
├── memory/                   # Session databases
├── reports/                  # Generated reports
└── analysis/                 # Screenshots and analysis
```

### Key Classes

- **EeveeAgent**: Main orchestration class that coordinates all components
- **MemorySystem**: SQLite-based persistent memory with context retrieval
- **PromptManager**: Template management and A/B testing framework
- **TaskExecutor**: Multi-step execution engine with error recovery
- **NavigationHelper**: Smart menu navigation with state tracking
- **PokemonParser**: Extract structured data from AI analysis text

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

## Prompt Experimentation

Eevee includes a powerful prompt experimentation system for optimizing AI performance:

### Creating Experimental Prompts
```python
from prompt_manager import PromptManager

pm = PromptManager()
pm.create_experimental_prompt(
    experiment_name="detailed_pokemon_analysis",
    base_prompt_type="pokemon_party_analysis", 
    modifications={"template": "Enhanced template with more detail..."},
    description="More detailed Pokemon analysis"
)
```

### A/B Testing
```python
# Start A/B test
pm.start_ab_test(
    experiment_name="pokemon_analysis_test",
    prompt_type="pokemon_party_analysis",
    variant_a="base",
    variant_b="detailed_pokemon_analysis",
    traffic_split=0.5
)

# Use in CLI
python run_eevee.py "check party" --prompt-experiment detailed_pokemon_analysis
```

### Performance Tracking
```python
# Get performance report
report = pm.get_performance_report("pokemon_party_analysis")
print(json.dumps(report, indent=2))
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
1. Create experimental prompt in `prompts/experimental/`
2. Test with A/B testing framework
3. Monitor performance metrics
4. Graduate successful experiments to base prompts

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