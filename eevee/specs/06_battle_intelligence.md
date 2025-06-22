# Memory-Driven Pokemon Battle Intelligence - Prompting Solution

## Problem Analysis

From the session log, the core issue is that the AI:
1. Recognizes "Thundershock" is available but only presses 'A'
2. Doesn't understand Pokemon battle menu navigation (need DOWN → A for move selection)
3. Loses battle context between turns
4. Lacks interruption capability during continuous play

## Solution: Enhanced Prompting + Neo4j Memory (Not State Machines)

Based on your successful `run_step_memory.py` approach, we'll use **prompting intelligence** and **memory summaries** rather than complex code.

### Phase 1: Enhanced Battle Prompt System

**1.1 Pokemon Battle Prompt Template** (`eevee/prompts/battle/pokemon_battle_expert.md`)
- Copy the structure from `fight_pokemon_2.md` with battle-specific instructions
- Add explicit move selection logic: "When you see move names, use DOWN to navigate, then A to select"
- Include battle state tracking variables like your system
- Add type effectiveness knowledge directly in prompts

**1.2 Battle Context Memory Integration**
- Enhance the memory summary to include recent battle turns
- Use Neo4j visual memory to track battle screenshots and outcomes
- Store battle-specific context: opponent, moves used, effectiveness results

### Phase 2: Memory-Driven Context Persistence

**2.1 Battle Memory Summary Enhancement** (`eevee/memory_system.py` updates)
- Add `generate_battle_summary()` method similar to your `recent_turns_summary()`
- Track last 5 battle turns with move selection and results
- Store type effectiveness learnings for future battles

**2.2 Prompt Context Injection**
- Inject battle memory into AI prompts like your approach:
  ```python
  battle_memory = memory.generate_battle_summary()
  ai_prompt = f"""
  {battle_memory}
  Your current goal is: {goal}
  
  BATTLE CONTEXT: If you see move names like "THUNDERSHOCK", "GROWL", etc:
  1. Use DOWN arrow to navigate to the desired move
  2. Press A to select it
  3. Don't just press A repeatedly
  
  Recent battle experience: {battle_memory}
  """
  ```

### Phase 3: Smart Interruption via Threading

**3.1 Non-Blocking Input Monitoring** (`eevee/utils/interruption.py`)
- Simple threaded keyboard listener (not complex state machines)
- Monitor for Ctrl+C, 'p' (pause), 'r' (resume), 'q' (quit)
- Use queue system for communication between threads

**3.2 Enhanced Interactive Loop** (`eevee/run_eevee.py` updates)
- Add threaded execution to continuous mode
- Real-time command processing during gameplay
- Graceful pause/resume with state preservation

### Phase 4: Prompt-Based Battle Intelligence

**4.1 Type Effectiveness Prompt Knowledge**
- Include Pokemon type chart directly in battle prompts
- Add move effectiveness examples in the prompt
- Use memory to remember what works against specific opponents

**4.2 Move Selection Strategy Prompts**
- Clear instructions for different battle scenarios
- Examples of proper button sequences for move navigation
- Battle outcome learning through memory summaries

## Implementation Approach

### Files to Create/Modify:

```
specs/
  └── pokemon-battle-memory-prompting-spec.md    # This document

eevee/prompts/battle/
  ├── pokemon_battle_expert.md                   # NEW: Battle-specific prompt template
  ├── move_selection_guide.md                    # NEW: Move navigation instructions
  └── type_effectiveness_chart.md                # NEW: Type matchup knowledge

eevee/
  ├── memory_system.py                           # MODIFY: Add battle memory methods
  ├── eevee_agent.py                             # MODIFY: Enhanced battle prompts
  ├── run_eevee.py                               # MODIFY: Add threaded interruption
  └── utils/
      └── interruption.py                        # NEW: Simple keyboard monitoring
```

### Key Changes:

**Memory-Driven Context:**
- Use Neo4j memory like your `gamememory.py` approach
- Battle summaries injected into prompts with recent turn context
- Visual memory for battle screenshot recognition

**Enhanced Battle Prompts:**
- Copy your detailed state tracking approach from `fight_pokemon_2.md`
- Add explicit move selection instructions
- Include battle memory context in each turn

**Simple Interruption System:**
- Threaded keyboard monitoring (not complex state machines)
- Queue-based communication between game loop and input monitoring
- Real-time pause/resume capability

## Expected Results:

**After Implementation:**
- AI will properly navigate to "Thundershock" using DOWN → A sequence
- Battle context maintained through memory summaries across turns
- Real-time interruption capability during continuous gameplay
- Learning from previous battles through Neo4j memory storage

**The key insight:** Use prompting intelligence + memory rather than complex code logic. Your `run_step_memory.py` demonstrates this works well for Pokemon gameplay.