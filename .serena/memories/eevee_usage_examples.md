# Eevee v1 Usage Examples and Commands

## Basic Usage

### Command Structure
```bash
python run_eevee.py "natural language task" [options]
```

### Tested Working Examples

#### Pokemon Party Analysis
```bash
python run_eevee.py "check and report all your pokemon party and their levels and moves and what PP left in each move"
```
- ✅ Works: Creates 6-step execution plan
- ✅ Analyzes: Pokemon Center, main menu state
- ✅ Plans: Navigate to Pokemon menu, check each Pokemon
- ✅ Reports: Detailed step-by-step analysis

#### Combined Analysis
```bash
python run_eevee.py "check and report what all pokemon you have and also your healing items"
```
- ✅ Works: Dual-objective task handling
- ✅ Analyzes: Menu state and required navigation
- ✅ Plans: Check both Pokemon party AND bag items
- ✅ Reports: Strategic button sequences for both tasks

### Command Options

#### Essential Options
- `--verbose`: Show step-by-step execution details
- `--dry-run`: Analyze and plan without executing actions
- `--save-report`: Save detailed report to file
- `--output-format json|markdown|text`: Control output format

#### Memory Management
- `--memory-session name`: Use specific memory session
- `--clear-memory`: Clear session before starting

#### Advanced Options
- `--model gemini-flash-2.0-exp`: Choose AI model
- `--prompt-experiment name`: Use experimental prompts
- `--max-steps 50`: Limit execution steps

## AI Analysis Quality

### Game State Recognition
- **Pokemon Centers**: Correctly identifies building interiors
- **Menu States**: Recognizes main menu, bag, Pokemon party
- **Navigation Context**: Understands current position in menu hierarchy
- **Item Recognition**: Can identify Pokeballs, healing items

### Strategic Planning
- **Multi-step Tasks**: Breaks complex requests into logical steps
- **Menu Navigation**: Provides specific button sequences
- **Error Recovery**: Suggests alternative approaches
- **Context Awareness**: Considers current game state

### Example AI Analysis Output
```
Screen Analysis: The screen shows a scene inside a building (likely a Pokemon Center), 
with the player character standing before a counter. A dialogue box displays the text 
"We hope to see you again!" The main menu is open, displaying options including: 
POKÉDEX, POKÉMON, BAG, SAVE, OPTION, and EXIT.

Actions Needed: To complete the step, the player needs to access their Pokémon party 
and their bag.

Recommended Actions:
* Press DOWN (twice): This will highlight "BAG" in the menu
* Press A: This will open the player's Bag. Inspect all items
* Press B: This closes the Bag  
* Press UP (once): This will highlight "POKÉMON" in the menu
* Press A: This will open the player's Pokemon party
```

## Development Commands

### Testing and Debugging
```bash
# Test SkyEmu connectivity
python test_skyemu.py

# Test button controls
python test_buttons.py

# CLI help
python run_eevee.py --help
```

### Memory Operations
```bash
# View available memory sessions
python -c "from memory_system import MemorySystem; m=MemorySystem(); print(m.get_memory_stats())"

# Export session data
python -c "from memory_system import MemorySystem; m=MemorySystem('default'); print(m.export_session())"
```

## Successful Integration Workflows

### 1. SkyEmu Pokemon Game Analysis
- Connect to SkyEmu HTTP server (localhost:8080)
- Capture Pokemon game screenshots (240x160)
- Analyze with Gemini Flash 2.0
- Generate actionable plans and reports

### 2. Multi-format Reporting
- Text reports for console output
- JSON for programmatic processing  
- Markdown for documentation
- File saving for persistence

### 3. Session Memory
- SQLite-based persistent storage
- Task history and results
- Pokemon knowledge accumulation
- Context retention across sessions