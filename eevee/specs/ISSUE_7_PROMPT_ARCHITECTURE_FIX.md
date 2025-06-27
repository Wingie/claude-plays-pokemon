# ISSUE 7: Prompt Architecture Fix - System Crash Resolution

## Problem Analysis

### Root Cause
The Pokemon AI system was crashing due to a broken prompt flow that created conflicts between:
1. `Pokemon Visual Landmark Detection Expert` (generic landmark detection)
2. `Pokemon Overworld Navigation Expert` (ASCII grid analysis) 
3. Coordinate overlay system (actual coordinate extraction)
4. Strategic planning system (Mistral decision making)

### Crash Pattern
```
System Flow: Landmark Detection → ASCII Analysis → ??? → CRASH
Expected Flow: Screenshot → Coordinate Analysis → Strategic Decision → Action
```

The system was running TWO separate analysis steps that provided generic descriptions instead of actionable coordinate data, causing the strategic system to receive unusable input.

## Solution Implemented

### 1. Removed Conflicting Analysis Systems

**Removed: Pokemon Visual Landmark Detection Expert**
- Location: `eevee_agent.py` lines 1795-1839
- Problem: Provided generic landmark descriptions instead of coordinate data
- Replacement: Direct coordinate-based analysis

**Removed: ASCII Grid Analysis System** 
- Location: `eevee_agent.py` lines 408-443
- Problem: Conflicted with coordinate overlay system
- Replacement: Simplified coordinate-aware navigation

### 2. Simplified Task Execution Flow

**Before (Broken)**:
```
Screenshot → Landmark Detection → ASCII Grid → ??? → Crash
```

**After (Fixed)**:
```
Screenshot → Strategic Prompt (exploration_strategy) → JSON Response → Action Execution
```

### 3. Direct Coordinate Integration

**Modified: `task_executor.py`**
- `_execute_analysis_step()`: Now uses `exploration_strategy` template directly
- `_execute_analysis_and_action_step()`: Simplified to screenshot→strategy→action flow
- Added `_parse_and_execute_strategic_response()`: Handles both button_presses and target_coordinates

### 4. Strategic Response Parsing

The system now properly handles:
```json
// Manual Movement
{
  "button_presses": ["up"],
  "reasoning": "moving_north",
  "confidence": "high"
}

// Coordinate Navigation  
{
  "target_coordinates": {"x": 15, "y": 8},
  "reasoning": "navigating_to_pokemon_center",
  "confidence": "high"
}
```

## Key Changes

### Files Modified
1. **`eevee_agent.py`**
   - Removed `Pokemon Visual Landmark Detection Expert` prompt
   - Removed ASCII grid analysis system
   - Simplified landmark detection to return basic defaults

2. **`task_executor.py`**
   - Modified `_execute_analysis_step()` to use coordinate-aware prompts
   - Simplified `_execute_analysis_and_action_step()` to direct strategic flow
   - Added `_parse_and_execute_strategic_response()` for JSON action parsing

3. **`prompts/base/base_prompts.yaml`**
   - Fixed JSON examples by removing problematic `{{{{ }}}}` braces
   - Replaced with clear "Example:" labels
   - Removed `pathfinding_action` concept, simplified to `target_coordinates`

4. **`prompts/playbooks/navigation.md`**
   - Updated all references from `pathfinding_action` to `target_coordinates`
   - Simplified coordinate navigation examples

## Architecture Benefits

### Before: Multi-Step Analysis Chain
- Screenshot → Gemini Landmark Detection → Gemini ASCII Analysis → Strategic Planning → ???
- Multiple points of failure
- Conflicting coordinate systems
- Generic analysis instead of actionable data

### After: Direct Strategic Flow
- Screenshot with Coordinates → Mistral Strategic Decision → Action Execution
- Single point of analysis
- Coordinate-aware from start to finish
- Direct JSON action responses

## Testing Validation

The system should now:
1. ✅ Capture screenshots with coordinate overlay
2. ✅ Send directly to `exploration_strategy` template
3. ✅ Get JSON response with either buttons or coordinates
4. ✅ Execute actions immediately without intermediate analysis
5. ✅ Handle coordinate navigation through existing pathfinding system

## Error Prevention

### Eliminated Error Sources:
- Brace escaping issues in JSON examples
- Missing variable errors from template conflicts
- ASCII grid vs coordinate overlay conflicts
- Dual analysis system confusion

### Robust Fallbacks:
- JSON parsing failures fall back to text-based action parsing
- Coordinate navigation failures fall back to manual movement
- Template variable issues now have clear error messages

## Performance Impact

**Efficiency Gains:**
- Reduced from 3+ LLM calls per turn to 1 strategic call
- Eliminated redundant analysis steps
- Direct coordinate→action mapping
- Faster response times through simplified flow

**Resource Optimization:**
- Single model call (Mistral strategic) per decision
- No more Gemini visual + Mistral strategic dual calls
- Simplified prompt templates reduce token usage
- Coordinate overlay provides rich context in single pass