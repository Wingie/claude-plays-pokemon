# Memory Integration Fresh Start Specification

## Overview
Complete Neo4j memory system integration with Eevee AI after cleaning up previous implementation attempts. Focus on proper singleton pattern, base64 screenshot storage, and automatic cleanup.

## Current System Status

### ✅ Working Components
- **Neo4j Connection**: Connected to `bolt://localhost:7687`
- **Neo4jWriter**: Complete CRUD operations (`neo4j_writer.py`)
- **Neo4jCompactReader**: Data retrieval (`neo4j_compact_reader.py`)
- **EeveeAgent**: Neo4j connection testing (`_test_neo4j_connection()`)
- **Mandatory Neo4j**: System fails without Neo4j (flags removed)

### ❌ Problems Requiring Cleanup
- **Wrongly placed `_store_turn_in_neo4j()` method** (lines 1108-1148 in run_eevee.py)
- **Modified `_record_turn_action()` signature** incorrectly (line 1084)
- **Missing singleton pattern** for Neo4j writer
- **No session lifecycle management** in Neo4j
- **No memory retrieval integration**

### 🎯 Updated Requirements
1. **Singleton Neo4j writer** (global scope, one connection per session)
2. **Base64 screenshot storage** (not just paths)
3. **Automatic session cleanup** (sessions die on exit)
4. **Complete turn storage** (visual + strategic + execution data)

## Implementation Plan - Cleanup First Approach

### Phase 1: Code Cleanup (Priority 1)
1. **Remove wrong implementation** - Delete `_store_turn_in_neo4j()` method (lines 1108-1148)
2. **Restore original signature** - Fix `_record_turn_action()` method (line 1084)
3. **Remove wrong call** - Delete call to `_store_turn_in_neo4j()` (line 1106)
4. **Create Neo4j singleton** - New `neo4j_singleton.py` file with global scope pattern
5. **Test cleanup** - Verify system runs without errors after cleanup
6. **Commit cleanup** - Save clean state before adding new features

### Phase 2: Singleton Pattern & Session Lifecycle (Priority 2)
7. **Implement singleton writer** - Global Neo4j writer instance with proper lifecycle
8. **Add session creation** - Create Neo4j session nodes at gameplay start
9. **Add session updates** - Update session status and cleanup on exit  
10. **Test session lifecycle** - Run 1-turn session, verify Neo4j session created/closed
11. **Add error handling** - Graceful degradation if Neo4j fails
12. **Commit session management** - Save working session lifecycle

### Phase 3: Complete Turn Storage (Priority 3)
13. **Add turn storage hook** - Call after `_update_session_state()` with complete data
14. **Implement storage method** - Store visual+strategic+execution+base64 screenshot
15. **Add context extraction** - Extract battle context and location from AI analysis
16. **Test turn storage** - Run 2-turn session, verify complete data in Neo4j
17. **Optimize data format** - Ensure efficient storage and retrieval
18. **Commit turn storage** - Save working turn storage system

### Phase 4: Memory Context Retrieval (Priority 4)
19. **Update memory context method** - Retrieve last 4 turns from Neo4j
20. **Format compact JSON** - Use existing `neo4j_compact_reader` formatting
21. **Integrate with prompts** - Inject memory context into AI decision prompts
22. **Test memory flow** - Run 4-turn session, verify memory context in decisions
23. **Optimize token usage** - Keep memory context under 100 tokens
24. **Commit memory integration** - Save complete working system

### Phase 5: Final Testing & Validation (Priority 5)
25. **Complete system test** - Run full 4-turn session with all features enabled

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