# Building Recognition Enhancement for Goal-Oriented Planning

## Problem Analysis
The current visual analysis system cannot distinguish between Pokemon Centers and Gyms. Both are classified as generic "navigation" scenes, making it impossible to execute specific building-related goals like "heal at Pokemon Center."

## Current Visual Analysis Limitations

### From the run analysis:
- **Step 66**: Generic navigation response with no building identification
- **Scene types**: Only `"battle|navigation|menu|transition"` 
- **Building context**: Missing entirely

### Current Template Output:
```json
{
  "scene_type": "navigation",
  "recommended_template": "exploration_strategy",
  "valid_buttons": [...generic movement...],
  "confidence": "high"
}
```

## Enhanced Building Recognition Solution

### 1. Visual Template Enhancement

Add building-specific detection to `visual_context_analyzer_gemini`:

```yaml
# Enhanced template section to add:
**BUILDING DETECTION (High Priority):**
If you see ANY building interior, identify the specific type:

**Pokemon Center Detection:**
- Red-haired Nurse Joy NPC
- Healing counter/desk
- PC terminal visible
- Pink/red interior walls
- "Welcome to the Pokemon Center!" text
- Healing sound effects or dialogue

**Gym Detection:**  
- Gym Leader sprite (Brock, Misty, Lt. Surge)
- Specialized gym layout (rock puzzles, water pools, electric barriers)
- Gym-specific color schemes (brown/gray for Rock, blue for Water)
- Trainer battle positions
- Gym badge podium/altar

**Building-Specific Scene Types:**
- scene_type: "pokemon_center" (instead of "navigation")
- scene_type: "gym_interior" (instead of "navigation") 
- scene_type: "building_entrance" (when standing outside)
```

### 2. Goal-Oriented Template Selection

Enhanced template recommendations:

```json
{
  "scene_type": "pokemon_center",
  "building_type": "pokemon_center",
  "location": "viridian_city|pewter_city|cerulean_city",
  "npcs_visible": ["nurse_joy"],
  "services_available": ["healing", "pc_access"],
  "recommended_template": "pokemon_center_navigation",
  "valid_buttons": [
    {"key": "↑", "action": "approach_nurse", "result": "healing_interaction"},
    {"key": "←", "action": "access_pc", "result": "pc_menu"},
    {"key": "↓", "action": "exit_building", "result": "return_to_town"}
  ],
  "confidence": "high"
}
```

### 3. New Specialized Templates

Create new prompt templates for building-specific actions:

#### Pokemon Center Template
```yaml
pokemon_center_navigation:
  name: Pokemon Center Healing Strategy
  description: Navigate Pokemon Center efficiently for healing
  template: |
    Pokemon Center Healing Navigation
    
    GOAL: {task}
    BUILDING: Pokemon Center
    LOCATION: {location}
    
    **HEALING PROCESS (4 steps):**
    1. **Approach Nurse**: Press ↑ until next to Nurse Joy
    2. **Initiate Dialogue**: Press A to start healing conversation
    3. **Confirm Healing**: Press A again to confirm "Yes" 
    4. **Wait & Exit**: Wait for healing complete, press A, then ↓ to exit
    
    **CURRENT POSITION ANALYSIS:**
    - If far from nurse: Move ↑ until adjacent
    - If at counter: Press A to interact
    - If in dialogue: Press A to continue/confirm
    - If healing complete: Press A then ↓ to exit
    
    **RESPONSE FORMAT:**
    {{
      "button_presses": ["up"],
      "reasoning": "approaching_nurse_joy",
      "step": "1_of_4",
      "progress": "moving_to_healing_counter"
    }}
```

#### Gym Recognition Template  
```yaml
gym_interior_navigation:
  name: Gym Interior Recognition & Strategy
  description: Navigate gym interiors and identify gym type
  template: |
    Pokemon Gym Interior Analysis
    
    GOAL: {task}
    BUILDING: Pokemon Gym
    
    **GYM TYPE IDENTIFICATION:**
    - **Rock Gym (Pewter)**: Brown/gray colors, rock formations, Brock sprite
    - **Water Gym (Cerulean)**: Blue colors, pools, Misty sprite  
    - **Electric Gym (Vermilion)**: Yellow colors, barriers, Lt. Surge sprite
    
    **GYM CHALLENGE PROCESS:**
    1. **Navigate Puzzle**: Solve gym-specific obstacle
    2. **Approach Leader**: Move to battle position
    3. **Initiate Battle**: Press A to challenge
    4. **Battle Strategy**: Use type advantages
    
    **RESPONSE FORMAT:**
    {{
      "button_presses": ["up"],
      "gym_type": "rock|water|electric",
      "gym_leader": "brock|misty|lt_surge",
      "challenge_phase": "puzzle|approach|battle",
      "type_advantage_needed": "water|grass|ground"
    }}
```

### 4. Integration with Goal System

The enhanced building recognition enables goal hierarchies like:

```yaml
# Goal: Heal Pokemon at Pewter City Pokemon Center
goal_hierarchy:
  epic: "defeat_elite_four"
  story: "pewter_gym_challenge" 
  chapter: "prepare_for_brock"
  task: "heal_pokemon_at_pewter_center"
  subtasks:
    - id: "enter_pokemon_center"
      status: "completed"
    - id: "approach_nurse_joy"  
      status: "in_progress"
      current_step: "moving_up_to_counter"
    - id: "initiate_healing"
      status: "pending"
    - id: "wait_for_healing"
      status: "pending" 
    - id: "exit_pokemon_center"
      status: "pending"
```

### 5. Success Criteria & State Detection

Enhanced state detection for goal completion:

```python
def detect_pokemon_center_state(visual_analysis):
    if visual_analysis.get("scene_type") == "pokemon_center":
        if "healing_complete" in visual_analysis.get("dialogue_text", ""):
            return "healing_finished"
        elif "nurse_joy" in visual_analysis.get("npcs_visible", []):
            return "inside_center"
        elif visual_analysis.get("dialogue_active"):
            return "healing_in_progress"
    elif visual_analysis.get("scene_type") == "navigation":
        # Check if we're outside Pokemon Center
        return "outside_building"
    
def detect_goal_completion(goal, visual_analysis):
    if goal.task == "heal_pokemon_at_pewter_center":
        state = detect_pokemon_center_state(visual_analysis)
        if state == "outside_building" and goal.get_subtask("exit_pokemon_center").status == "in_progress":
            return True  # Successfully completed healing and exited
    return False
```

## Implementation Strategy

### Phase 1: Template Enhancement (This Sprint)
1. **Update visual_context_analyzer_gemini** to detect buildings
2. **Add pokemon_center_navigation template**
3. **Test with "heal at Pokemon Center" goal**

### Phase 2: Goal Integration
1. **Connect enhanced recognition to goal system**
2. **Implement subtask state tracking**
3. **Test full goal hierarchy execution**

### Phase 3: Gym Support
1. **Add gym_interior_navigation template**
2. **Implement gym type detection**
3. **Connect to gym challenge goals**

## Expected Improvements

- **Goal Success Rate**: 90%+ for Pokemon Center healing
- **Recognition Accuracy**: Distinguish centers from gyms reliably  
- **Execution Efficiency**: Complete healing in 8-12 turns vs current random exploration
- **State Awareness**: Know exactly where we are in the process

This enhancement is crucial for the goal-oriented planning system to work effectively!