# Prompt Template Improvement Specifications

## Current State Analysis

### Problems with Current Templates

1. **Overloaded Single Templates**
   - `battle_analysis` template is 200+ lines trying to handle all battle scenarios
   - Too many instructions lead to confusion and ignored priorities
   - JSON response format gets lost in verbose instructions

2. **Missing Enforcement Mechanisms**
   - Templates describe strategies but don't enforce them
   - HP management mentioned but not prioritized
   - Move selection logic explained but not systematically applied

3. **Poor State Management**
   - No tracking of previous decisions
   - No awareness of stuck patterns within battle context
   - Menu navigation treated as one-off decisions

## Proposed Template Architecture

### 1. Hierarchical Template System

```yaml
template_hierarchy:
  visual_analyzer:
    purpose: "Identify scene and route to appropriate handler"
    outputs:
      - scene_type
      - recommended_handler
      - extracted_context
  
  handlers:
    battle_handler:
      sub_templates:
        - battle_hp_critical
        - battle_move_selection
        - battle_menu_navigation
        - battle_item_usage
        - battle_pokemon_switch
    
    navigation_handler:
      sub_templates:
        - navigation_exploration
        - navigation_stuck_recovery
        - navigation_trainer_approach
```

### 2. Simplified Battle Templates

#### Template: battle_hp_critical
```yaml
name: Battle HP Critical Handler
description: Handles low HP situations with clear priorities
template: |
  CRITICAL HP BATTLE DECISION
  
  Current Pokemon HP: {current_hp}/{max_hp} ({hp_percentage}%)
  Has Healing Items: {has_healing_items}
  Other Healthy Pokemon: {healthy_pokemon_list}
  
  DECISION PRIORITY (MUST FOLLOW):
  1. If HP < 25% AND has_healing_items: 
     ACTION: ["right", "a"] # Go to BAG
     REASON: "critical_hp_use_item"
  
  2. If HP < 25% AND healthy_pokemon_available:
     ACTION: ["down", "a"] # Go to POKEMON
     REASON: "critical_hp_switch_pokemon"
  
  3. If HP < 25% AND no_alternatives:
     ACTION: ["a"] # Use strongest move quickly
     REASON: "critical_hp_finish_fast"
  
  RESPOND WITH JSON ONLY:
  {
    "action": ["right", "a"],
    "reason": "critical_hp_use_item",
    "hp_status": "critical"
  }
```

#### Template: battle_move_selection
```yaml
name: Battle Move Selection Handler
description: Focused move selection with navigation
template: |
  MOVE SELECTION DECISION
  
  Current Cursor: {cursor_position} 
  Target Move: {best_move}
  Move Grid:
    {move_1} | {move_2}
    {move_3} | {move_4}
  
  NAVIGATION REQUIRED:
  From {cursor_position} to {best_move}: {navigation_path}
  
  ACTION: {navigation_buttons}
  
  RESPOND WITH JSON ONLY:
  {
    "action": ["down", "a"],
    "reason": "navigate_to_thundershock",
    "from_move": "GROWL",
    "to_move": "THUNDERSHOCK"
  }
```

### 3. State-Aware Context Injection

```python
# Pseudo-code for context building
def build_battle_context(game_state):
    context = {
        'hp_percentage': calculate_hp_percentage(game_state),
        'has_healing_items': check_inventory_for_heals(game_state),
        'healthy_pokemon_list': get_healthy_team_members(game_state),
        'battle_turn_count': game_state.battle_turns,
        'recent_actions': game_state.last_5_actions,
        'stuck_indicator': detect_stuck_pattern(game_state)
    }
    
    # Select appropriate template based on context
    if context['hp_percentage'] < 25:
        return 'battle_hp_critical', context
    elif context['stuck_indicator']:
        return 'battle_stuck_recovery', context
    else:
        return 'battle_move_selection', context
```

### 4. Simplified JSON Response Format

All templates should return:
```json
{
  "action": ["button1", "button2"],  // Max 2 buttons
  "reason": "short_snake_case_reason",
  "confidence": "high|medium|low",
  "context": "battle|navigation|menu"
}
```

### 5. Menu Navigation Improvements

```yaml
menu_navigation_tracker:
  current_menu: "battle_main"  # battle_main, move_select, bag, pokemon
  cursor_memory:
    battle_main: "FIGHT"  # Remember where cursor was
    move_select: "THUNDERSHOCK"
  navigation_map:
    battle_main:
      FIGHT: {"right": "BAG", "down": "POKEMON"}
      BAG: {"left": "FIGHT", "down": "RUN"}
      POKEMON: {"up": "FIGHT", "right": "RUN"}
      RUN: {"left": "POKEMON", "up": "BAG"}
```

### 6. Anti-Stuck Mechanisms

```yaml
stuck_detection:
  patterns:
    - repeated_action: 
        threshold: 3
        recovery: ["b", "opposite_direction"]
    - no_progress:
        threshold: 5_turns_same_state
        recovery: ["b", "b", "different_option"]
    - menu_loop:
        threshold: 3_menu_visits
        recovery: ["b", "b", "b"]
```

## Implementation Recommendations

### Phase 1: Core Battle Improvements
1. Implement `battle_hp_critical` template
2. Add HP threshold detection to visual analyzer
3. Create simple state tracking for HP and items
4. Test with low HP scenarios

### Phase 2: Navigation Enhancement
1. Implement move selection with cursor tracking
2. Add menu navigation memory
3. Create stuck detection system
4. Test with various battle states

### Phase 3: Advanced Features
1. Pokemon switching logic
2. Type effectiveness calculator
3. Battle strategy memory
4. Learning from successful battles

## Testing Strategy

### Test Cases
1. **Low HP Test**: Start battle with Pokemon at 20% HP
2. **Move Navigation Test**: Ensure correct move selection
3. **Item Usage Test**: Verify BAG navigation and item use
4. **Pokemon Switch Test**: Test switching to healthy Pokemon
5. **Stuck Recovery Test**: Simulate stuck scenarios

### Success Criteria
- 0% battles fought with HP < 25% (unless no alternatives)
- 100% correct move selection (navigate to damage moves)
- 0% manual interventions required
- <5% stuck situations lasting >3 turns

## Code Integration Points

1. **prompt_manager.py**: Add template selection logic
2. **battle_analyzer.py**: Create HP and state detection
3. **menu_tracker.py**: New module for menu state
4. **template_selector.py**: Smart template routing

## Monitoring and Metrics

Track:
- HP at battle end
- Number of items used
- Pokemon switches per battle
- Stuck recovery activations
- Battle completion rate
- Manual intervention count

## Additional Notes for Future Implementation

### Quick Summary of Run Analysis
- **Run analyzed**: `/Users/wingston/code/claude-plays-pokemon/eevee/runs/battle_first_20250625_103555`
- **Critical finding**: 92% of battle turns with critical HP, no healing attempts
- **Manual intervention required**: User had to provide keypresses to unstuck
- **Button usage stats**: 'a' (99x), 'down' (15x), 'up' (15x), 'b' (13x)

### Priority Fixes Needed
1. **HP < 25% = Immediate BAG navigation** (not just mentioned, but enforced)
2. **Cursor tracking** - Know where we are before pressing buttons
3. **Stuck detection** - If same action 3+ times, try something different
4. **Menu escape sequences** - Multiple 'b' presses when stuck

### Template Simplification Key Points
- Current templates too verbose (200+ lines)
- Need focused sub-templates (30-50 lines each)
- JSON response format gets lost in instructions
- Enforce actions, don't just describe them

### Next Steps When Revisiting
1. Create `battle_hp_critical` template first (highest priority)
2. Test with saves at low HP scenarios
3. Implement cursor position tracking
4. Add simple stuck detection (3 same actions = try 'b')
5. Create integration tests for each scenario