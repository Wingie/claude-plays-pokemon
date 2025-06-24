# Memory Integration Comprehensive Specification

## Overview
Incremental integration of Neo4j memory system with existing Eevee AI using prompt-focused improvements and step-by-step testing.

## Current System Analysis

### ✅ Working Components
- **Neo4j Connection**: Connected to `bolt://localhost:7687`
- **Compact Memory Tools**: `compact_memory_tools.py` with remember/recall/learn functions
- **Hybrid Mode**: Visual=Gemini, Strategic=Mistral working correctly
- **TaskExecutor**: Fixed `execute_task()` method implemented
- **Compact Reasoning**: CamelCase format implemented (`north_clear_path` vs verbose)

### 🔄 Integration Points
- **Neo4j Data**: `gamememory.py` with `get_recent_turns(limit)` method
- **Visual Analysis**: Clean JSON from Gemini visual analysis
- **Strategic Decisions**: Mistral using compact reasoning format
- **Memory Context**: Need to inject last 4 turns into decision prompts

## Incremental Implementation Plan (25 Steps)

### Phase 1: Neo4j Data Reader (6 steps)
1. **Create Neo4j reader adapter** - Adapt `gamememory.py` methods for Eevee system
2. **Test Neo4j data retrieval** - Verify `get_recent_turns(4)` returns valid data
3. **Format last 4 turns to JSON** - Create compact summary format
4. **Test JSON formatting** - Run 1 turn, verify format correctness
5. **Add visual data extraction** - Extract current screenshot analysis to JSON
6. **Test combined data** - Verify last 4 turns + current visual in single JSON

### Phase 2: Memory-Driven Prompts (7 steps)
7. **Create memory context template** - Add memory section to `exploration_strategy`
8. **Test memory template** - Run 1 turn with memory context, verify prompt length
9. **Optimize token usage** - Reduce memory context to <100 tokens
10. **Test token optimization** - Verify decisions still work with compact memory
11. **Add memory reasoning** - Update prompts to use memory in camelCase reasoning
12. **Test memory reasoning** - Run 1 turn, verify camelCase memory-based decisions
13. **Validate memory decisions** - Ensure memory improves decision quality

### Phase 3: Decision Engine Enhancement (6 steps)
14. **Integrate memory into visual analysis** - Add memory context to Gemini prompts
15. **Test visual+memory** - Run 1 turn, verify Gemini uses memory correctly
16. **Integrate memory into strategic decisions** - Add memory context to Mistral prompts
17. **Test strategic+memory** - Run 1 turn, verify Mistral uses memory correctly
18. **Create memory-driven button selection** - Focus on single button with memory reasoning
19. **Test button selection** - Run 1 turn, verify single optimal button choice

### Phase 4: System Optimization (6 steps)
20. **Optimize prompt injection** - Streamline how memory enters prompt pipeline
21. **Test prompt efficiency** - Measure token usage vs decision quality
22. **Add memory learning** - System learns from successful memory-driven decisions
23. **Test memory learning** - Run 3 turns, verify learning improves decisions
24. **Create memory feedback loop** - Decisions update memory for future turns
25. **Test complete system** - Run 5 turns, verify full memory integration works

## Memory Data Format

### Last 4 Turns Summary (Target: <80 tokens)
```json
{
  "recent_turns": [
    {"turn": 1, "action": "up", "result": "moved_north", "context": "grass"},
    {"turn": 2, "action": "right", "result": "hit_tree", "context": "forest"},
    {"turn": 3, "action": "down", "result": "moved_south", "context": "path"},
    {"turn": 4, "action": "left", "result": "moved_west", "context": "water"}
  ],
  "current_visual": {
    "scene": "navigation",
    "pos": "4,3", 
    "terrain": "grass_water",
    "moves": ["up","down","left","right"]
  }
}
```

### Memory-Driven Decision Output
```json
{
  "button": "up",
  "reasoning": "northPathClearFromMemoryTurn1"
}
```

## Prompt Enhancement Strategy

### Current Templates to Modify
1. **`exploration_strategy`** - Add memory context section
2. **`visual_context_analyzer`** - Add memory-informed scene analysis
3. **`ai_directed_navigation`** - Add memory-based navigation hints

### Memory Context Template Addition
```yaml
**MEMORY CONTEXT:**
Recent 4 turns: {memory_turns_json}
Pattern detected: {pattern_summary}
Success rate: {success_metrics}

Use memory to avoid repeated failures and optimize movement decisions.
```

## Testing Protocol

### Single Turn Testing (Each Step)
1. **Run**: `python run_eevee.py --task "test memory step X" --max-turns 1 --neo4j-memory --verbose`
2. **Verify**: Check logs for memory usage, token count, decision quality
3. **Adjust**: Modify prompts based on results
4. **Repeat**: Continue to next step only after current step works

### Success Criteria (Per Step)
- ✅ No errors or crashes
- ✅ Memory data correctly injected into prompts
- ✅ Token usage within target limits
- ✅ Decision quality maintained or improved
- ✅ camelCase reasoning format preserved

## Integration Approach

### Minimal Changes Strategy
- ✅ Build on existing working components
- ✅ No major refactoring of core systems
- ✅ Prompt-focused improvements only
- ✅ Incremental testing after each change
- ✅ Roll back capability if step fails

### File Modification Priority
1. **Primary**: `prompts/base/base_prompts.yaml` - Add memory sections
2. **Secondary**: `visual_analysis.py` - Add memory context injection
3. **Tertiary**: `compact_memory_tools.py` - Enhance with Neo4j integration
4. **Minimal**: Core eevee_agent.py changes

## Expected Outcomes

### Token Efficiency
- **Current**: 1200+ tokens per decision
- **Target**: <200 tokens per decision with memory
- **Memory overhead**: <100 tokens for 4-turn context

### Decision Quality Improvements
- **Avoid repeated failures**: Remember hitting trees/walls
- **Optimize navigation**: Use successful path patterns
- **Context awareness**: Understand game state progression
- **Strategic continuity**: Maintain long-term objectives

## Risk Mitigation

### Rollback Strategy
- Each step tested independently
- Previous working state preserved
- Prompt changes easily reversible
- No database schema changes required

### Failure Handling
- Step fails → Adjust prompts → Retry
- Multiple failures → Skip to next phase
- System instability → Return to last working state
- Memory overhead too high → Reduce context size

This specification provides a clear roadmap for 25 incremental steps, each focusing on prompt adjustments and single-turn testing to gradually integrate memory capabilities into the existing system.