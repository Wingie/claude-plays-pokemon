# Neo4j Memory Integration Final Specification

## Overview
Complete integration of Neo4j memory system with existing Eevee AI system. This document provides a fresh start after cleaning up previous implementation attempts.

## System Requirements
- Neo4j database running on `bolt://localhost:7687`
- Existing Eevee system with hybrid LLM mode working
- Screenshots stored as base64 in Neo4j
- Singleton Neo4j writer pattern
- Automatic session cleanup on exit

## Current State Analysis

### ✅ Already Implemented & Working
- **EeveeAgent**: Neo4j connection test in `_test_neo4j_connection()`
- **Neo4jWriter**: Complete CRUD operations in `neo4j_writer.py`
- **Neo4jCompactReader**: Data retrieval in `neo4j_compact_reader.py`  
- **Memory Integration**: Enhancement hook in `memory_integration.py`
- **Mandatory Neo4j**: Removed optional flags, system fails without Neo4j

### ❌ Problems to Clean Up
1. **Wrongly placed `_store_turn_in_neo4j()` method** in run_eevee.py (lines 1108-1148)
2. **Modified `_record_turn_action()` signature** incorrectly (line 1084)
3. **Missing session creation** in Neo4j during gameplay start
4. **No memory retrieval** integration in decision-making process

## Core Data Flow Design

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Game Turn     │───▶│ Visual Analysis  │───▶│ Neo4j Storage   │
│   (Current)     │    │   (Gemini)       │    │ (Complete Turn) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        │
                                │                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Strategic AI    │◀───│ Memory Context   │◀───│ Last 4 Turns   │
│  (Mistral)      │    │ (Compact JSON)   │    │ from Neo4j      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Principles
1. **Current turn**: Fresh visual analysis (not from memory)
2. **Historical context**: Last 4 turns from Neo4j memory
3. **Complete storage**: All turn data (visual + decisions + base64 screenshots)
4. **Singleton writer**: One Neo4j connection per session
5. **Automatic cleanup**: Sessions die on process exit

## Implementation Tasks

### Phase 1: Cleanup & Foundation (Priority 1)

#### Task 1.1: Remove Incorrect Implementation
- **Location**: run_eevee.py lines 1108-1148
- **Action**: Delete `_store_turn_in_neo4j()` method completely
- **Location**: run_eevee.py line 1084  
- **Action**: Restore original `_record_turn_action()` signature
- **Location**: run_eevee.py line 1106
- **Action**: Remove call to `_store_turn_in_neo4j()`

#### Task 1.2: Create Singleton Neo4j Writer
- **Location**: New file `eevee/neo4j_singleton.py`
- **Implementation**:
```python
class Neo4jSingleton:
    _instance = None
    _writer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            from neo4j_writer import Neo4jWriter
            cls._writer = Neo4jWriter()
        return cls._instance
    
    def get_writer(self):
        return self._writer
    
    def close(self):
        if self._writer:
            self._writer.close()
            self._writer = None
```

#### Task 1.3: Add Session Lifecycle Management
- **Location**: run_eevee.py `start_session()` method around line 273
- **Add after session creation**:
```python
# Create Neo4j session
neo4j = Neo4jSingleton()
writer = neo4j.get_writer()
if writer and writer.driver:
    session_data = {
        "session_id": session_id,
        "start_time": self.session.start_time,
        "goal": goal,
        "max_turns": max_turns,
        "status": "active"
    }
    writer.create_session(session_data)
    print(f"✅ Neo4j session created: {session_id}")
```

- **Location**: run_eevee.py `_get_session_summary()` method around line 1660
- **Add before return**:
```python
# Update Neo4j session status
neo4j = Neo4jSingleton()
writer = neo4j.get_writer()
if writer and writer.driver:
    writer.update_session(self.session.session_id, {
        "status": "completed",
        "turns_completed": self.session.turns_completed,
        "end_time": end_time
    })
    neo4j.close()  # Cleanup on session end
```

### Phase 2: Turn Storage Integration (Priority 2)

#### Task 2.1: Add Turn Storage After State Update
- **Location**: run_eevee.py around line 353 (after `_update_session_state()`)
- **Add new method call**:
```python
# Store complete turn data in Neo4j
self._store_complete_turn_data(turn_count, game_context, ai_result, execution_result, movement_data)
```

#### Task 2.2: Implement Complete Turn Storage Method
- **Location**: run_eevee.py (add new method)
- **Implementation**:
```python
def _store_complete_turn_data(self, turn_number: int, game_context: Dict[str, Any], 
                             ai_result: Dict[str, Any], execution_result: Dict[str, Any], 
                             movement_data: Dict[str, Any] = None):
    """Store complete turn data in Neo4j with all context"""
    try:
        neo4j = Neo4jSingleton()
        writer = neo4j.get_writer()
        
        if not writer or not writer.driver:
            if self.eevee.verbose:
                print("⚠️ Neo4j writer not available")
            return
        
        # Prepare complete turn data
        turn_data = {
            "turn_id": f"{self.session.session_id}_turn_{turn_number}",
            "session_id": self.session.session_id,
            "timestamp": datetime.now().isoformat(),
            "gemini_text": ai_result.get("analysis", ""),
            "button_presses": ai_result.get("action", []),
            "screenshot_path": game_context.get("screenshot_path"),
            "screenshot_base64": game_context.get("screenshot_data"),  # Store base64
            "location": self._extract_location_from_context(ai_result.get("analysis", "")),
            "success": execution_result.get("success", False),
            "visual_context": movement_data,
            "battle_context": self._extract_battle_context(ai_result.get("analysis", "")),
            "memory_context": getattr(self, '_last_memory_context', None)
        }
        
        success = writer.store_game_turn(turn_data)
        
        if self.eevee.verbose:
            status = "✅ stored" if success else "⚠️ failed to store"
            print(f"Neo4j turn {turn_number}: {status}")
            
    except Exception as e:
        if self.eevee.verbose:
            print(f"⚠️ Neo4j turn storage error: {e}")
```

### Phase 3: Memory Context Retrieval (Priority 3)

#### Task 3.1: Enhance Memory Context Method
- **Location**: run_eevee.py `_get_memory_context()` method around line 1016
- **Replace existing implementation**:
```python
def _get_memory_context(self) -> str:
    """Get memory context combining SQLite + Neo4j last 4 turns"""
    context_parts = []
    
    # Get general memory context (existing)
    if self.eevee.memory:
        try:
            general_context = self.eevee.memory.get_recent_gameplay_summary(limit=5)
            if general_context:
                context_parts.append(general_context)
        except:
            pass
    
    # Get last 4 turns from Neo4j
    try:
        from neo4j_compact_reader import Neo4jCompactReader
        reader = Neo4jCompactReader()
        
        if reader.test_connection():
            # Get recent turns for this session
            recent_turns = reader.get_recent_turns(4)
            if recent_turns:
                compact_memory = reader.format_turns_to_compact_json(recent_turns)
                memory_json = json.dumps(compact_memory, separators=(',', ':'))
                context_parts.append(f"**RECENT MEMORY** (last 4 turns):\n{memory_json}")
                
                # Store for turn storage
                self._last_memory_context = memory_json
        
        reader.close()
        
    except Exception as e:
        if self.eevee.verbose:
            print(f"⚠️ Neo4j memory retrieval failed: {e}")
    
    return "\n\n".join(context_parts) if context_parts else ""
```

#### Task 3.2: Add Battle Context Extraction
- **Location**: run_eevee.py (add new helper method)
- **Implementation**:
```python
def _extract_battle_context(self, analysis_text: str) -> Dict[str, Any]:
    """Extract battle context from AI analysis text"""
    analysis_lower = analysis_text.lower()
    
    # Simple battle detection
    if any(keyword in analysis_lower for keyword in [
        "battle", "pokemon", "hp", "attack", "wild", "appeared", "fight"
    ]):
        return {
            "battle_phase": "unknown",
            "battle_type": "wild" if "wild" in analysis_lower else "trainer",
            "in_battle": True
        }
    
    return {"in_battle": False}

def _extract_location_from_context(self, analysis_text: str) -> str:
    """Extract location from analysis text"""
    analysis_lower = analysis_text.lower()
    
    locations = [
        "route", "forest", "cave", "city", "town", "center", "gym",
        "viridian", "pewter", "cerulean", "vermillion", "lavender",
        "celadon", "fuchsia", "saffron", "cinnabar", "pallet"
    ]
    
    for location in locations:
        if location in analysis_lower:
            return location.title()
    
    return "unknown"
```

### Phase 4: Prompt Integration Enhancement (Priority 4)

#### Task 4.1: Update Prompt Templates
- **Location**: `prompts/base/base_prompts.yaml`
- **Add memory section to key templates**:
```yaml
exploration_strategy:
  template: |
    You are an AI playing Pokemon. Analyze the visual context and make movement decisions.
    
    {memory_context}
    
    **CURRENT SITUATION:**
    {visual_analysis}
    
    **VALID MOVEMENTS:**
    {valid_movements}
    
    Use memory of recent turns to avoid repeated failures and choose optimal paths.
    
    Respond in JSON format:
    ```json
    {
      "observation": "What you see",
      "reasoning": "Memory-informed camelCase reasoning",
      "button_presses": ["single_optimal_button"]
    }
    ```
```

## Data Storage Specifications

### Neo4j Node Structure

#### Turn Node (Enhanced)
```cypher
(t:Turn {
    turn_id: String,              // "{session_id}_turn_{number}"
    session_id: String,
    timestamp: String,            // ISO format
    gemini_text: String,          // Full AI analysis
    button_presses: String,       // JSON array of buttons
    screenshot_path: String,      // File path
    screenshot_base64: String,    // Full base64 image data
    location: String,             // Extracted location
    success: Boolean,             // Action success
    visual_context: String,       // JSON of movement_data
    battle_context: String,       // JSON of battle info
    memory_context: String        // JSON of memory used
})
```

### Memory Context Format
```json
{
  "recent_turns": [
    {"turn": 1, "action": "up", "result": "moved", "context": "grass"},
    {"turn": 2, "action": "right", "result": "blocked", "context": "tree"},
    {"turn": 3, "action": "down", "result": "moved", "context": "path"},
    {"turn": 4, "action": "left", "result": "moved", "context": "water"}
  ],
  "turn_count": 4,
  "patterns": "hitting_obstacles"
}
```

## Testing Protocol

### Test 1: Clean Implementation
```bash
# Remove wrong implementation
cd eevee/
# Manually remove lines 1108-1148 and restore line 1084
```

### Test 2: Session Creation
```bash
python run_eevee.py --task "test session creation" --max-turns 1 --verbose
# Verify: Neo4j session node created
```

### Test 3: Turn Storage
```bash
python run_eevee.py --task "test turn storage" --max-turns 2 --verbose
# Verify: 2 turn nodes with complete data including base64 screenshots
```

### Test 4: Memory Retrieval
```bash
python run_eevee.py --task "test memory context" --max-turns 4 --verbose
# Verify: Memory context includes last 4 turns in compact JSON format
```

### Test 5: Full Integration
```bash
python run_eevee.py --task "test complete memory system" --max-turns 4 --verbose
# Verify: All components working together seamlessly
```

## Success Criteria

- [ ] No wrongly placed methods in run_eevee.py
- [ ] Singleton Neo4j writer properly manages connections
- [ ] Sessions created and updated in Neo4j
- [ ] Complete turn data stored with base64 screenshots
- [ ] Memory context includes last 4 turns from Neo4j
- [ ] Prompts enhanced with memory context
- [ ] System automatically cleans up on exit
- [ ] 4-turn test session completes without errors

## Error Handling

### Connection Failures
- Graceful degradation if Neo4j unavailable
- Continue with file-based memory as fallback
- Clear error messages for debugging

### Data Integrity
- Atomic turn storage (all or nothing)
- Session state consistency
- Proper cleanup on unexpected exit

This specification provides a complete roadmap for proper Neo4j memory integration with clear cleanup of previous implementation attempts and correct singleton pattern usage.