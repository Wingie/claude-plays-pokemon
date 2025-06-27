# Debug and Analysis Tools for Claude Plays Pokemon

## Core Debugging Script

### Main Run Command
```bash
cd eevee/ && python run_eevee.py --goal "Heal your pokemon then leave the pokecenter" --episode-review-frequency 5 --max-turns 20 --no-interactive --verbose
```

**Always run this at the end of each debugging session**

## Available Debug Tools

### 1. Main Execution Script
**Location**: `eevee/run_eevee.py`

**Key Parameters**:
- `--task "description"` - Single task execution (e.g., "test compact memory", "check Pokemon party")
- `--goal "description"` - Continuous gameplay goal
- `--max-turns N` - Limit number of turns (useful for debugging)
- `--verbose` - Detailed logging output
- `--no-interactive` - Disable interactive mode
- `--episode-review-frequency N` - How often to review episodes
- `--neo4j-memory` - Enable Neo4j memory system
- `--save-report` - Save execution report

**Example Debug Commands**:
```bash
# Test memory system
python run_eevee.py --task "test compact memory" --max-turns 1 --neo4j-memory --verbose

# Quick battle test
python run_eevee.py --task "check my Pokemon party status" --max-turns 5 --verbose

# Navigation debugging
python run_eevee.py --task "navigate to Pokemon Center" --save-report --max-turns 10
```

### 2. RAM Analysis Tool
**Location**: `eevee/tests/analyse_skyemu_ram.py`

**Purpose**: Analyze Pokemon game state directly from SkyEmu memory
- Player name, location, inventory
- Pokemon party (names, levels, HP, moves, status)
- Battle state analysis
- Memory debugging for game state

**Usage**:
```bash
cd eevee/tests && python analyse_skyemu_ram.py
```

### 3. Run Analysis Tool
**Location**: `eevee/runs/claude_analyze_runs.py`

**Purpose**: Analyze completed gameplay sessions for performance patterns
- Performance issue identification
- Success/failure pattern analysis
- Session comparison and trending
- Automated report generation

**Usage**:
```bash
cd eevee/runs && python claude_analyze_runs.py
```

### 4. Visual Analysis Testing
**Location**: `eevee/tests/test_visual_prompt_variations_focused.py`

**Purpose**: Test and debug visual analysis capabilities
- Screen recognition accuracy
- Prompt template effectiveness
- Visual context analysis

### 5. Memory System Debugging
**Locations**:
- `eevee/tests/test_memory_integration.py` - Memory system integration tests
- `eevee/tests/explore_neo4j.py` - Neo4j memory debugging
- `eevee/tests/test_eevee_memory.py` - Core memory functionality tests

### 6. Goal-Oriented Planning Tests
**Location**: `eevee/tests/test_goal_oriented_planning.py`

**Purpose**: Debug goal decomposition and planning systems

## Recent Runs Analysis

**Runs Directory**: `eevee/runs/`
- Contains session folders with timestamps
- Each session has `session_data.json` with complete turn-by-turn data
- Screenshots and logs preserved for analysis
- Use `claude_analyze_runs.py` to process all sessions

## Debug Workflow

1. **Start with Basic Test**:
   ```bash
   python run_eevee.py --task "check my Pokemon party status" --max-turns 1 --verbose
   ```

2. **Analyze RAM State**:
   ```bash
   cd tests && python analyse_skyemu_ram.py
   ```

3. **Review Recent Sessions**:
   ```bash
   cd runs && python claude_analyze_runs.py
   ```

4. **Run Targeted Debug**:
   ```bash
   python run_eevee.py --goal "Heal your pokemon then leave the pokecenter" --episode-review-frequency 5 --max-turns 20 --no-interactive --verbose
   ```

## Memory Tools Available

- **Neo4j Integration**: `--neo4j-memory` flag for graph-based memory
- **Compact Memory**: Built-in SQLite memory system
- **Memory Context**: Spatial and temporal context preservation
- **Episode Review**: Periodic analysis of gameplay sessions

## Architecture Notes

- **Pure AI System**: No hardcoded Pokemon logic in Python files
- **YAML Templates**: All game knowledge in prompt templates
- **Multi-Provider LLM**: Mistral (Pixtral) + Gemini (2.0 Flash)
- **Visual Intelligence**: 8-key spatial grid analysis
- **Continuous Learning**: Real-time template improvement

## Error Debugging

- Check `eevee/evee_logger.py` for logging configuration
- Enable `--verbose` for detailed execution traces
- Use `--max-turns` to limit execution for faster debugging
- Analyze failed sessions in `runs/` directory for patterns