# Prompt Improvement Brainstorm

## Current Problem Analysis

### Issues with Existing Prompts
1. **Too Verbose**: 180+ line battle template with redundant instructions
2. **Single-Turn Thinking**: No multi-turn planning or state persistence  
3. **No Memory Integration**: Each decision made in isolation
4. **Poor HP Management**: Level 9 vs Level 3 → used GROWL instead of damage
5. **Rigid Structure**: Hard to adapt to new situations

## Improvement Strategies

### 1. **Function-Call Based Prompts**

**Current Approach:**
```yaml
# 50 lines of battle instructions...
"Return JSON with button_presses, reasoning, observations..."
```

**Function-Call Approach:**
```yaml
battle_functions:
  template: |
    Execute battle functions:
    
    health_check = check_pokemon_health({our_pokemon})
    move_decision = decide_next_move(health_check, {enemy_pokemon})
    button_sequence = convert_to_buttons(move_decision, {cursor_on})
    
    Return: {{"executed": ["check_pokemon_health", "decide_next_move"], "output": button_sequence}}
```

**Benefits:**
- Self-documenting function names
- Clear execution flow
- Easier to debug and modify
- Reusable components

### 2. **State Machine Prompts**

**Current:** Long conditional logic in template
**Improved:** Explicit state transitions

```yaml
pokemon_state_machine:
  template: |
    State: {current_state}
    Valid Transitions: {available_actions}
    
    Transition Rules:
    battle.main_menu + cursor_on_fight → battle.move_selection [press 'a']
    battle.move_selection + move_chosen → battle.animation [press 'a'] 
    battle.animation + animation_done → battle.main_menu [press 'a']
    
    Execute: {{"from": "{current_state}", "to": "target_state", "action": ["a"]}}
```

### 3. **Memory-Driven Prompts**

**Integration with Neo4j Task Memory:**
```yaml
memory_enhanced_decision:
  template: |
    Current Context: {battle_context}
    
    Memory Queries:
    - similar_hp_situations: {memory.query("hp < 30%")}  
    - level_advantage_strategies: {memory.query("level_diff > 2.0")}
    - proven_move_combinations: {memory.query("enemy_type = {enemy_type}")}
    
    Apply Best Strategy: {{"strategy_source": "memory", "confidence": 0.95}}
```

### 4. **Minimal Token Prompts**

**Ultra-Compact Decision Trees:**
```yaml
micro_battle_prompt:
  template: |
    HP: {hp_percent}% | Enemy: L{enemy_level} | Our: L{our_level}
    
    hp < 15% → heal
    hp < 30% AND enemy_strong → switch  
    our_level > 2*enemy_level → quick_finish
    else → type_effective
    
    {{"decision": "quick_finish", "buttons": ["a"]}}
```

### 5. **Conditional Template Loading**

**Dynamic Prompt Selection:**
```python
def select_battle_prompt(context):
    hp_percent = context['our_pokemon']['hp_percent']
    level_diff = context['our_pokemon']['level'] / context['enemy_pokemon']['level']
    
    if hp_percent < 0.15:
        return "emergency_healing_prompt"
    elif level_diff > 2.0:
        return "quick_finish_prompt"  
    else:
        return "strategic_battle_prompt"
```

### 6. **Task Dependency Prompts**

**Explicit Dependencies:**
```yaml
battle_task_chain:
  template: |
    Task Chain for {goal}:
    
    1. health_assessment → {{"status": "critical|good", "action_required": bool}}
    2. threat_evaluation → {{"enemy_strength": 1-10, "type_advantage": "us|them|neutral"}}  
    3. strategy_selection → {{"strategy": "aggressive|defensive|optimal"}}
    4. action_execution → {{"buttons": [...], "expected_outcome": "..."}}
    
    Execute chain: {{"completed_tasks": [...], "final_action": [...]}}
```

## Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. **HP Management Logic**: Add explicit HP thresholds to battle template
2. **Level Difference Handling**: "If our_level > 2*enemy_level: use any damage move"
3. **Anti-Status Move Logic**: "Avoid GROWL/LEER unless strategic benefit"

### Phase 2: Function-Based System (Week 1)
1. Convert battle template to function calls
2. Implement task dependency system  
3. Add state machine navigation

### Phase 3: Memory Integration (Week 2)
1. Connect to Neo4j task memory
2. Add memory-driven decision prompts
3. Implement strategy learning from past battles

### Phase 4: Optimization (Week 3)
1. Minimize token usage with micro-prompts
2. Dynamic template selection based on context
3. Advanced task chaining for complex operations

## Specific Template Improvements

### Enhanced Battle Template v2
```yaml
battle_analysis_v2:
  template: |
    Pokemon Battle Functions (Execute in Order):
    
    // Health Analysis
    health = check_pokemon_health({our_pokemon})
    
    // Strategy Decision  
    if health.critical: strategy = "heal_or_switch"
    elif {our_level} > 2 * {enemy_level}: strategy = "quick_finish" 
    else: strategy = "type_effective"
    
    // Action Conversion
    buttons = execute_strategy(strategy, {cursor_on}, {valid_buttons})
    
    Return: {{"strategy": "quick_finish", "health": "critical", "buttons": ["a"]}}
```

### Memory-Enhanced Navigation
```yaml
navigation_with_memory:
  template: |
    Location: {current_location} → Target: {target_location}
    
    Known Routes: {memory.get_routes(current_location, target_location)}
    Success Rates: {memory.get_success_rates()}
    
    Best Route: {{"path": [...], "confidence": 0.9, "source": "memory"}}
```

## Testing Strategy

### A/B Testing Framework
1. **Baseline**: Current verbose templates
2. **Test A**: Function-based templates  
3. **Test B**: Memory-enhanced templates
4. **Test C**: Minimal token templates

### Metrics
- **Battle Efficiency**: Turns to defeat weak enemies
- **HP Management**: Healing decisions when HP < 30%
- **Token Usage**: Prompt length and API costs
- **Success Rate**: Overall task completion rate

### 5-Turn Battle Test
Perfect opportunity to test enhanced prompts:
1. Load save before level 3 Vidal
2. Test new HP management logic
3. Verify level difference handling
4. Measure improvement vs baseline

Ready to implement these improvements!