# Prompt Compact Optimization Strategy

## Current Token Waste Analysis

### **Current Battle Template Stats:**
- **Lines**: 180+ lines of text
- **Estimated Tokens**: ~1,200-1,500 tokens per battle decision
- **Redundancy**: 60%+ repeated instructions and explanations
- **Efficiency**: Low - verbose descriptions for simple decisions

### **Token Usage Breakdown:**
```yaml
Current battle_analysis template:
- Instructions: ~800 tokens (50%)
- Examples: ~400 tokens (25%) 
- Format specification: ~300 tokens (20%)
- Actual context data: ~100 tokens (5%)
```

## Ultra-Compact Optimization Strategy

### **1. Minimal Decision Trees**

**Before (180 lines):**
```yaml
battle_analysis:
  template: |
    Pokemon Strategic Battle Analysis (Enhanced)
    
    GOAL: {task}
    RECENT ACTIONS: {recent_actions}
    
    **RICH BATTLE CONTEXT PROVIDED:**
    # ... 150+ more lines of instructions
```

**After (15 lines):**
```yaml
battle_micro:
  template: |
    HP: {our_hp} | Enemy: L{enemy_level} | Our: L{our_level}
    Phase: {battle_phase} | Cursor: {cursor_on}
    
    IF hp < 30%: heal
    IF our_level > 2*enemy_level: attack
    ELSE: type_effective
    
    JSON: {{"action": "attack", "buttons": ["a"]}}
```

**Token Reduction**: 95% fewer tokens!

### **2. Function Call Syntax**

**Ultra-Compact Function Approach:**
```yaml
battle_func:
  template: |
    execute_battle_sequence({battle_context})
    
    functions:
    - check_hp({our_pokemon}) → heal_needed?
    - decide_strategy(hp_status, level_diff) → action_type
    - get_buttons(action_type, {cursor_on}) → button_array
    
    return: {{"buttons": [...], "strategy": "X"}}
```

### **3. Symbolic Logic**

**Mathematical Notation:**
```yaml
battle_symbolic:
  template: |
    Context: HP={hp}%, L={level_diff}, P={battle_phase}
    
    Rules:
    HP < 15% → heal
    HP < 30% ∧ L > 2 → switch  
    L > 2 → attack_any
    else → attack_optimal
    
    Output: {{"rule": "L > 2", "action": ["a"]}}
```

### **4. State Machine Micro-Prompts**

**State-Based Decisions:**
```yaml
state_micro:
  template: |
    State: {battle_phase}
    
    main_menu → fight: ["a"]
    move_select → move1: ["a"] 
    animation → continue: ["a"]
    
    Execute: {{"transition": "fight", "buttons": ["a"]}}
```

## A/B Testing Framework

### **Template Comparison Test**

| Template Type | Est. Tokens | Lines | Use Case |
|---------------|-------------|-------|----------|
| **Current** | 1,200 | 180 | Full context |
| **Compact** | 150 | 15 | 90% of decisions |
| **Micro** | 50 | 8 | Simple battles |
| **Function** | 100 | 12 | Complex logic |

### **Performance Metrics**

```python
class PromptOptimizationTest:
    def __init__(self):
        self.templates = {
            'verbose': current_battle_template,
            'compact': compact_battle_template, 
            'micro': micro_battle_template
        }
        self.metrics = {}
    
    def measure_template(self, template_name, context):
        return {
            'token_count': count_tokens(template),
            'response_quality': test_decision_accuracy(),
            'api_cost': estimate_cost(tokens),
            'response_time': measure_latency()
        }
```

## Implementation Plan

### **Phase 1: Micro-Templates (Day 1)**
Create ultra-compact versions of key templates:

1. **battle_micro**: 15-line battle decision
2. **nav_micro**: 8-line navigation 
3. **menu_micro**: 5-line menu interaction

### **Phase 2: Function Templates (Day 2)**  
Convert to function-call syntax:

1. **battle_func**: Function-based battle logic
2. **task_func**: Task execution prompts
3. **memory_func**: Memory query prompts

### **Phase 3: A/B Testing (Day 3)**
Run side-by-side comparison:

1. **Battle Test**: 20 battles with each template
2. **Token Measurement**: Count actual usage
3. **Quality Assessment**: Decision accuracy
4. **Cost Analysis**: API cost reduction

## Ultra-Compact Template Library

### **1. Micro Battle Template**
```yaml
battle_micro:
  name: "Ultra-Compact Battle Decision"
  template: |
    HP: {our_hp} vs L{enemy_level}
    {cursor_on} | {battle_phase}
    
    hp<30%→heal | level>2x→attack | else→optimal
    
    {{"action":"attack","buttons":["a"]}}
  variables: ["our_hp", "enemy_level", "cursor_on", "battle_phase"]
  estimated_tokens: 40
```

### **2. Micro Navigation**
```yaml
nav_micro:
  template: |
    Pos: {character_position} → Goal: {target}
    Paths: {valid_movements}
    
    move: {{"direction": "up", "buttons": ["up"]}}
  estimated_tokens: 25
```

### **3. Micro Menu**
```yaml
menu_micro:
  template: |
    Menu: {menu_type} | Cursor: {cursor_position}
    
    action: {{"select": true, "buttons": ["a"]}}
  estimated_tokens: 15
```

## Token Savings Calculation

### **Battle Decision Example:**

**Current Template:**
- Base template: 1,200 tokens
- Context injection: 200 tokens  
- **Total**: 1,400 tokens

**Micro Template:**
- Base template: 40 tokens
- Context injection: 50 tokens
- **Total**: 90 tokens

**Savings**: 93% reduction (1,310 tokens saved per decision)

### **Cost Impact:**
- **GPT-4**: $0.03/1K tokens → $0.04 saved per decision
- **100 decisions**: $4.00 savings
- **Daily usage**: $20-50 savings potential

## Quality Assurance

### **Decision Accuracy Test**
Ensure compact prompts maintain decision quality:

```python
def test_decision_accuracy():
    test_scenarios = [
        {"hp": "8/26", "enemy_level": 3, "our_level": 9},  # Should attack
        {"hp": "5/26", "enemy_level": 8, "our_level": 9},  # Should heal
        {"hp": "20/26", "enemy_level": 7, "our_level": 8}, # Should use strategy
    ]
    
    for template in ['verbose', 'compact', 'micro']:
        accuracy = test_template_decisions(template, test_scenarios)
        assert accuracy > 0.95  # 95% accuracy requirement
```

## Implementation Ready

**Next Actions:**
1. Create micro-template versions
2. Implement A/B testing framework  
3. Run 5-turn battle test with compact prompts
4. Measure token reduction and maintain quality

Ready to implement ultra-compact optimization!