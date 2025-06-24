# Neo4j Memory Integration Plan

## Invocation Command
```bash
LLM_PROVIDER=hybrid python run_eevee.py --goal "test memory system with battle context" --max-turns 4 --no-interactive
```

## 🎯 Mission: Fix Battle Context Data Flow

### Core Problem
The system is trying to extract battle variables from visual analysis, but they should come from:
1. **Session state** (current battle state)
2. **Neo4j memory** (historical battle decisions)
3. **Visual analysis** (scene detection only)

### Phase 1: Study Current Data Flow

#### Key Files to Analyze
1. **Session Management**: Where is battle state stored?
   - `run_eevee.py` - session object and state management
   - Check for battle context in session variables

2. **Visual Analysis Output**: What does it actually provide?
   - Look at actual visual analysis JSON output in logs
   - Distinguish between scene detection vs game state

3. **Memory System**: How should Neo4j integrate?
   - `neo4j_compact_reader.py` - memory retrieval 
   - `memory_tools.py` - memory tool interface
   - Where should battle context be stored/retrieved?

### Phase 2: Fix Prompt Manager

#### Current Error Pattern
```
Missing required variable for prompt battle_analysis: 'battle_phase'
```

#### Root Cause Analysis
1. `prompt_manager.py` methods don't accept battle context parameters
2. `run_eevee.py` doesn't pass session battle state to prompt manager
3. Battle variables are extracted from wrong data source

#### Fix Strategy
1. **Update prompt manager methods** to accept session context
2. **Identify session battle state location** in run_eevee.py
3. **Pass battle context from session** to prompt manager
4. **Use Neo4j memory for historical battle context**

### Phase 3: Neo4j Memory Integration

#### Memory Data Structure
```json
{
  "turn": 67,
  "action": "THUNDERSHOCK",
  "result": "super_effective", 
  "context": "battle",
  "battle_data": {
    "our_pokemon": "PIKA",
    "our_hp": "14/26",
    "enemy_pokemon": "PIDGEY",
    "enemy_hp": "low"
  }
}
```

#### Memory Tools Integration
- **Store**: Battle decisions and outcomes
- **Retrieve**: Last 4 turns of battle history
- **Analyze**: Type effectiveness patterns
- **Recommend**: Best moves based on memory

### Phase 4: Testing Protocol

#### Test Sequence
1. **Visual Analysis Test**: Verify scene detection works
2. **Session State Test**: Check where battle state is maintained
3. **Memory Storage Test**: Store a battle decision in Neo4j
4. **Memory Retrieval Test**: Get last 4 turns for battle context
5. **Prompt Integration Test**: Verify all variables reach templates
6. **End-to-End Test**: Complete battle with memory-driven decisions

#### Success Criteria
- [ ] No missing variable errors in prompt manager
- [ ] Battle context flows from session → prompt manager
- [ ] Memory system stores and retrieves battle decisions
- [ ] AI makes memory-informed battle decisions
- [ ] Pokemon switching based on memory works

## 🔍 Investigation Questions

1. **Where is current battle state stored?** (Pokemon HP, moves, party)
2. **How does visual analysis communicate battle detection?** (scene_type only?)
3. **Where should Neo4j memory integrate?** (session updates? prompt building?)
4. **What battle variables do templates actually need?** (from YAML templates)

## 🚨 Critical Success Factors

1. **Don't modify visual analysis** - it should only detect scenes
2. **Find the session battle state** - don't create new storage
3. **Use existing memory tools** - don't rewrite memory system
4. **Test incrementally** - one component at a time

## Next Action
Start with studying current session state management in `run_eevee.py` to understand where battle context should come from.