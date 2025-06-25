# Task-Based System Integration Spec

## Overview
Integration of simplified task-based architecture with Neo4j memory system for improved Pokemon gameplay decision making.

## Current System Status

### ✅ Completed Components
- **Enhanced Battle Template**: HP management + level difference logic in `base_prompts.yaml`
- **Task Memory System**: `task_memory_system.py` with function-based tasks
- **Multi-turn Combat**: Battle planning with task arrays
- **Compact JSON**: Streamlined communication format

### 🔄 Task-Based Architecture

**Core Functions (Self-Documenting):**
```python
check_pokemon_health(pokemon_data)     # HP status analysis
decide_next_move(context)              # Strategic decision making  
find_strongest_move(moves, enemy_type) # Optimal move selection
play_next_move(move_choice, cursor)    # Button press conversion
```

**Neo4j Task Relationships:**
```cypher
(decide_next_move)-[:DEPENDS_ON]->(check_pokemon_health)
(play_next_move)-[:DEPENDS_ON]->(decide_next_move)
(find_strongest_move)-[:CALLED_BY]->(decide_next_move)
```

## GenAI Stack Integration Plan

### Docker Compose Integration
```yaml
# Expected genaistack structure
services:
  neo4j:
    image: neo4j:latest
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: none  # Simplified for development
  
  eevee-agent:
    depends_on: [neo4j]
    environment:
      NEO4J_URI: bolt://neo4j:7687
```

### Connection Strategy
```python
# Graceful fallback system
class TaskMemoryConnector:
    def __init__(self):
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.fallback_mode = not self._test_connection()
    
    def _test_connection(self):
        try:
            driver = GraphDatabase.driver(self.neo4j_uri)
            # No auth by default for development
            return True
        except:
            return False
```

## Prompt Improvement Brainstorm

### 1. **Function-Call Prompts**
Instead of verbose descriptions, use function signatures:

```yaml
battle_function_call:
  template: |
    Execute Pokemon battle functions in sequence:
    
    1. health = check_pokemon_health({our_pokemon})
    2. decision = decide_next_move({context})  
    3. buttons = play_next_move(decision.action, {cursor_on})
    
    Return: {{"functions_executed": [...], "final_output": buttons}}
```

### 2. **State Machine Prompts**  
```yaml
battle_state_machine:
  template: |
    Current State: {battle_phase}
    Available Transitions: {valid_buttons}
    
    State Rules:
    - main_menu → move_selection (press 'a' on FIGHT)
    - move_selection → battle_animation (select move)
    - battle_animation → main_menu (press 'a' to continue)
    
    Execute transition: {{"next_state": "X", "actions": ["a"]}}
```

### 3. **Memory-Driven Prompts**
```yaml
memory_enhanced_battle:
  template: |
    Neo4j Memory Query Results:
    - Similar battles: {similar_contexts}
    - Success rates: {task_success_rates}
    - Optimal moves: {proven_strategies}
    
    Apply learned strategy: {{"strategy": "proven", "confidence": 0.9}}
```

### 4. **Minimal Token Prompts**
```yaml
ultra_compact_battle:
  template: |
    HP: {our_hp} vs Enemy L{enemy_level}
    
    IF hp < 30%: heal
    IF our_level > 2*enemy_level: attack_any  
    ELSE: attack_optimal
    
    JSON: {{"action": "X", "buttons": ["a"]}}
```

## Implementation Phases

### Phase 1: Docker Integration
1. Analyze genaistack `docker-compose.yml`
2. Connect `task_memory_system.py` to containerized Neo4j
3. Test graceful fallback when Neo4j unavailable

### Phase 2: Function-Based Prompts
1. Replace verbose battle prompts with function calls
2. Implement state machine navigation prompts
3. Add memory-driven decision templates

### Phase 3: Memory Learning
1. Store successful battle sequences in Neo4j
2. Query similar battle contexts for strategy suggestions
3. Build task dependency graphs for complex operations

## Testing Strategy

### 5-Turn Battle Test
1. Load save before level 3 Vidal battle
2. Test enhanced prompts with HP management
3. Verify task-based decision making prevents GROWL usage
4. Measure improvement in battle efficiency

### Memory Integration Test  
1. Run multiple battle sessions
2. Verify Neo4j stores task results and dependencies
3. Test memory retrieval for similar battle contexts
4. Validate graceful fallback when Neo4j unavailable

## Success Metrics

- **Battle Efficiency**: Finish weak enemies in 1-2 turns
- **HP Management**: Heal when HP < 30%
- **Memory Utilization**: Query and apply past successful strategies
- **System Reliability**: Function with/without Neo4j connection