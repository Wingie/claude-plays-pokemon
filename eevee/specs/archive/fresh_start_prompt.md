# Fresh Start: Neo4j Memory Integration for Claude-plays-pokemon

## Context
You are working on the claude-plays-pokemon/eevee system - an AI that plays Pokemon using Gemini for visual analysis and Mistral for strategic decisions. The system needs Neo4j memory integration to remember the last 4 turns and improve decision making.

## Current Problem
Previous implementation attempts left incorrect code in run_eevee.py that needs cleanup before proper integration. The system should use a singleton Neo4j writer, store base64 screenshots, and provide memory context to AI decisions.

## Your Task
Implement proper Neo4j memory integration following the cleanup-first approach in the specification.

## Key Files to Understand
1. `/eevee/run_eevee.py` - Main game loop (contains incorrect implementation to clean up)
2. `/eevee/neo4j_writer.py` - Neo4j CRUD operations (already working)
3. `/eevee/neo4j_compact_reader.py` - Data retrieval and formatting (already working)
4. `/eevee/specs/neo4j_memory_integration_final.md` - Complete specification
5. `/eevee/specs/memory_integration_comprehensive.md` - Updated implementation plan

## Current State Issues
- **Lines 1108-1148** in run_eevee.py: Wrong `_store_turn_in_neo4j()` method (DELETE)
- **Line 1084** in run_eevee.py: Wrong signature for `_record_turn_action()` (RESTORE)
- **Line 1106** in run_eevee.py: Wrong method call (REMOVE)
- **Missing**: Neo4j singleton pattern
- **Missing**: Session lifecycle management
- **Missing**: Memory context retrieval

## Requirements
1. **Singleton pattern**: One Neo4j writer per session, global scope
2. **Base64 storage**: Store screenshots as base64 in Neo4j, not just paths  
3. **Auto cleanup**: Sessions die automatically on process exit
4. **Complete data**: Store visual analysis + strategic decisions + execution results
5. **Memory context**: Last 4 turns from Neo4j fed to AI prompts
6. **Token efficiency**: Memory context under 100 tokens

## Implementation Approach
Follow the 25-step plan in `/eevee/specs/memory_integration_comprehensive.md`:

### Phase 1: Code Cleanup (Do First)
1. Remove wrong implementation from run_eevee.py
2. Restore original method signatures  
3. Test that system runs cleanly
4. Commit clean state

### Phase 2: Singleton & Sessions
5. Create Neo4j singleton pattern
6. Add session creation/cleanup
7. Test session lifecycle

### Phase 3: Turn Storage  
8. Add proper turn storage with complete data
9. Store base64 screenshots
10. Test data persistence

### Phase 4: Memory Retrieval
11. Integrate memory context into AI decisions
12. Use last 4 turns from Neo4j
13. Test memory-driven decisions

### Phase 5: Full Testing
14. Run 4-turn test session with all features

## Success Criteria
- ✅ System runs without errors after cleanup
- ✅ Neo4j sessions created and updated properly  
- ✅ Complete turn data stored including base64 screenshots
- ✅ Last 4 turns retrieved and formatted as compact JSON
- ✅ Memory context integrated into AI prompts
- ✅ 4-turn test session completes successfully

## Test Command
```bash
python run_eevee.py --task "test compact memory" --max-turns 4 --verbose
```

## Data Flow
```
Current Turn → Visual Analysis → Strategic Decision → Execute Action
     ↓              ↓                    ↓              ↓
Store in Neo4j ← Complete Turn Data ← Memory Context ← Last 4 Turns
```

## Key Integration Points
- **run_eevee.py line 353**: After `_update_session_state()` add turn storage
- **run_eevee.py line 1016**: In `_get_memory_context()` add Neo4j retrieval  
- **run_eevee.py line 273**: In `start_session()` add Neo4j session creation
- **run_eevee.py line 1660**: In `_get_session_summary()` add cleanup

Start with Phase 1 cleanup, test each phase independently, and commit working milestones before proceeding to the next phase.