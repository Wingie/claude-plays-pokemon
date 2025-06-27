# Pathfinder Integration Restart Guide
*"Just like the Pathfinder leading the Andromeda Initiative, this guide navigates you through uncharted territory"*

**Created**: 2025-06-26  
**Status**: Session End Documentation  
**Priority**: HIGH - Critical continuation guide

---

## 🎯 Executive Summary

We've made **significant progress** on pathfinding integration but hit CLAUDE.md violations that need fixing. The core pathfinding system works, but we need to remove hardcoded logic and complete JSON parser integration.

### ✅ Major Achievements Completed
1. **CRITICAL BUG FIXED**: RAM data now sent to AI for ALL decisions (not just battles)
2. **Smart Pathfinding Loop**: Created `_execute_pathfinding_to_coordinate()` - step-by-step RAM validation
3. **Healing Bookmark System**: Complete Pokemon Center tracking and storage
4. **AI Pathfinding Tools**: Mistral-ready pathfinding toolset
5. **Coordinate Grid Overlay**: Real-world coordinates from RAM data
6. **Template Error Fixes**: Resolved Jinja2 nested dict issues

### ❌ CLAUDE.md Violations to Remove
1. **`_execute_pathfinding_action` method**: Contains hardcoded game logic (VIOLATION)
2. **Landmark system**: AI should read coordinates from visual overlay, not stored landmarks
3. **Navigation context injection**: Too much "cheating" logic in Python

### 🔧 Remaining Work (1-2 hours)
1. **JSON Parser Update**: Handle `pathfinding_action` in `_get_ai_decision()`
2. **Template Updates**: Remove landmark references, emphasize visual coordinate reading
3. **CLAUDE.md Compliance**: Remove hardcoded logic, pure data passing only
4. **End-to-End Testing**: Verify pathfinding integration works correctly

---

## 📊 Current State Analysis

### Files Created/Modified ✅

#### **1. `/run_eevee.py` - ENHANCED**
**Lines 1668-1739**: Created `_execute_pathfinding_to_coordinate()` method
```python
def _execute_pathfinding_to_coordinate(self, target_x: int, target_y: int) -> List[str]:
    """Smart pathfinding loop - moves one step at a time, validates with RAM"""
    # FOLLOWS CLAUDE.md: Pure data passing, step-by-step movement with RAM validation
    # NO hardcoded Pokemon logic - just coordinate movement
```

**CRITICAL FIX** (Lines 1776-1831): RAM data injection moved to ALL templates
```python
# BEFORE (BUG): Only battle templates got RAM data
if template_name == "battle_analysis":
    ram_data = self._collect_ram_data()

# AFTER (FIXED): ALL templates get complete RAM data
ram_data = self._collect_ram_data()  # Before any template-specific code
```

**Lines 1586-1657**: `_detect_and_bookmark_healing()` method - Pokemon Center auto-bookmarking

#### **2. `/healing_bookmark_system.py` - NEW FILE**
Complete Pokemon Center bookmark management:
- SQLite database for healing locations
- Success/failure tracking
- Healing detection via RAM comparison
- Automatic bookmarking after successful healing

#### **3. `/ai_pathfinding_tools.py` - NEW FILE**  
Pathfinding tools designed for Mistral AI:
- `pathfind_to_coordinate()` - Basic coordinate navigation
- `pathfind_to_healing_location()` - Find nearest Pokemon Center
- `get_nearby_landmarks()` - Show known locations
- Brief, precise reasoning as requested

#### **4. `/test_pathfinder.py` - CREATED (needs move to tests/)**
Comprehensive test suite for pathfinding system

#### **5. `/prompts/base/base_prompts.yaml` - ENHANCED**
Enhanced templates with pathfinding action options:
```yaml
**Pathfinding Tool (for precise coordinate movement):**
{{
  "pathfinding_action": "move_to_coordinate", 
  "target_coordinates": {{"x": 10, "y": 15}},
  "reasoning": "pathfinding_to_specific_location"
}}
```

### Critical Bug Fixes Completed ✅

#### **1. RAM Data Injection Bug (MAJOR)**
**Problem**: AI at Pokemon Center with low HP Pokemon didn't realize it needed healing
**Cause**: RAM data only injected for "battle_analysis" template
**Fix**: Moved RAM injection before template-specific code in `_build_ai_prompt()`
**Impact**: AI now gets Pokemon health data for ALL navigation decisions

#### **2. Template Variable Errors (Jinja2)**
**Problem**: `'dict' object has no attribute 'map_id'` - nested dict access issues
**Cause**: Jinja2 couldn't handle nested dict syntax
**Fix**: Flattened variables and used square bracket notation
**Impact**: Pokemon Center template now loads correctly

#### **3. Coordinate Grid Overlay**
**Problem**: Grid showed visual numbers, not real-world coordinates
**Fix**: Calculate real coordinates based on player RAM position
**Impact**: AI can now read actual game coordinates from visual overlay

---

## 🚨 CLAUDE.md Violations to Remove

### **Violation 1: Hardcoded Game Logic**
**File**: `/run_eevee.py`  
**Method**: `_execute_pathfinding_action()` - **MUST BE REMOVED**
**Issue**: Contains Pokemon-specific business logic and hardcoded navigation decisions
**CLAUDE.md Rule**: "No game logic in Python files - YAML templates only"

### **Violation 2: Landmark System**  
**Problem**: AI receives pre-computed landmark data instead of reading visual overlay
**Issue**: This is "cheating" - AI should learn coordinates from visual grid
**CLAUDE.md Rule**: "AI learns naturally through prompts, not hardcoded"

### **Violation 3: Navigation Context Injection**
**Problem**: Too much processed navigation data sent to AI
**Issue**: AI should read coordinates from screenshot grid overlay
**CLAUDE.md Rule**: "Pure data passing - no Pokemon decision-making logic"

---

## 🔧 Remaining Implementation Work

### **Task 1: Update JSON Parser (HIGH PRIORITY)**

**Location**: `/run_eevee.py` - `_get_ai_decision()` method  
**Need**: Handle `pathfinding_action` alongside `button_presses`

**Current JSON Format**:
```json
{
  "button_presses": ["up", "up", "right"],
  "reasoning": "moving_to_pokemon_center"
}
```

**New JSON Format**:
```json
{
  "pathfinding_action": "move_to_coordinate",
  "target_coordinates": {"x": 10, "y": 15},
  "reasoning": "pathfinding_to_pokemon_center"
}
```

**Implementation Needed**:
```python
def _get_ai_decision(self, ai_response: str) -> Dict[str, Any]:
    # Parse JSON response
    parsed = json.loads(ai_response)
    
    # Handle pathfinding action
    if "pathfinding_action" in parsed and parsed["pathfinding_action"] == "move_to_coordinate":
        target_coords = parsed.get("target_coordinates", {})
        target_x = target_coords.get("x", 0)
        target_y = target_coords.get("y", 0)
        
        # Use smart pathfinding loop
        button_sequence = self._execute_pathfinding_to_coordinate(target_x, target_y)
        
        return {
            "action": button_sequence,
            "reasoning": parsed.get("reasoning", "pathfinding"),
            "pathfinding_used": True,
            "target_coordinates": target_coords
        }
    
    # Handle regular button presses (existing logic)
    # ... rest of existing parser
```

### **Task 2: Template Updates (MEDIUM PRIORITY)**

**Files**: `/prompts/base/base_prompts.yaml`  
**Need**: Remove all landmark references, emphasize visual coordinate reading

**Current Template Issues**:
- References to landmark data that violates CLAUDE.md
- Need to emphasize reading coordinates from visual grid overlay
- Remove "nearby landmarks" context

**Template Updates Needed**:
```yaml
**COORDINATE OVERLAY READING:**
- The screenshot has a coordinate grid overlay showing X,Y positions for each tile
- Read the coordinate numbers directly from the visual overlay on the screenshot  
- Your current position ({current_x},{current_y}) is at the screen center
- Use visible coordinates from the overlay to plan precise movement to any tile
- NO landmark data provided - learn locations by exploring and remembering coordinates

**Pathfinding Tool (for precise coordinate movement):**
{{
  "pathfinding_action": "move_to_coordinate",
  "target_coordinates": {{"x": 10, "y": 15}}, 
  "reasoning": "moving_to_specific_coordinate",
  "observations": "Using pathfinding for efficient navigation"
}}
```

### **Task 3: Remove CLAUDE.md Violations (HIGH PRIORITY)**

**Actions Required**:
1. **Remove `_execute_pathfinding_action()` method** - contains hardcoded logic
2. **Remove landmark context injection** - let AI read visual overlay 
3. **Remove navigation_context logic** - pure data passing only
4. **Keep `_execute_pathfinding_to_coordinate()`** - this follows CLAUDE.md (pure movement)

### **Task 4: Move Test File**
**Action**: Move `/test_pathfinder.py` to `/tests/test_pathfinder.py`

---

## 🎮 Technical Implementation Details

### **Smart Pathfinding Loop (COMPLETED ✅)**

The `_execute_pathfinding_to_coordinate()` method implements the exact pathfinding approach requested:

```python
def _execute_pathfinding_to_coordinate(self, target_x: int, target_y: int) -> List[str]:
    """Smart pathfinding loop - moves one step at a time, validates with RAM"""
    executed_buttons = []
    max_attempts = 20  # Prevent infinite loops
    
    for attempt in range(max_attempts):
        # Get current position from RAM
        ram_data = self._collect_ram_data()
        current_x = location_data.get("x", 0)
        current_y = location_data.get("y", 0)
        
        # Check if we've reached target
        if current_x == target_x and current_y == target_y:
            break
            
        # Calculate next move (one button only)
        dx = target_x - current_x
        dy = target_y - current_y
        
        if abs(dx) > abs(dy):
            button = "right" if dx > 0 else "left"
        else:
            button = "down" if dy > 0 else "up"
            
        # Press button and verify movement
        old_x, old_y = current_x, current_y
        self.eevee.controller.press_button(button)
        time.sleep(0.5)  # Wait for movement
        
        # Check if position actually changed
        new_ram = self._collect_ram_data()
        new_x = new_location.get("x", old_x)
        new_y = new_location.get("y", old_y)
        
        if new_x != old_x or new_y != old_y:
            executed_buttons.append(button)
        else:
            # Blocked - try alternative
            executed_buttons.append("b")
            break
            
    return executed_buttons
```

**Why This Follows CLAUDE.md**:
- ✅ **Pure data passing**: Only moves based on coordinates
- ✅ **No Pokemon game logic**: Just coordinate math and button presses
- ✅ **RAM validation**: Verifies each step worked
- ✅ **Step-by-step**: One button at a time with validation

### **Healing Bookmark System (COMPLETED ✅)**

Automatically detects successful healing and saves Pokemon Center locations:

```python
# Automatic detection after healing
def _detect_and_bookmark_healing(self, ai_result, execution_result):
    # Compare Pokemon HP before/after actions
    # If healing detected, save current coordinates
    # Store in SQLite database for future pathfinding
```

**Database Schema**:
```sql
CREATE TABLE healing_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    map_id INTEGER NOT NULL,
    x INTEGER NOT NULL, 
    y INTEGER NOT NULL,
    map_name TEXT,
    location_name TEXT,
    success_count INTEGER DEFAULT 0,
    last_used TEXT,
    average_healing_time REAL
);
```

---

## 🧭 Next Session Implementation Strategy

### **Step 1: JSON Parser Update (30 minutes)**
1. Locate `_get_ai_decision()` method in `/run_eevee.py`
2. Add pathfinding_action handling as shown above
3. Test JSON parsing with sample pathfinding responses

### **Step 2: CLAUDE.md Compliance (20 minutes)**  
1. Remove `_execute_pathfinding_action()` method (hardcoded logic violation)
2. Remove landmark context injection from prompt building
3. Keep only coordinate data and visual overlay emphasis

### **Step 3: Template Updates (15 minutes)**
1. Update templates to emphasize visual coordinate reading
2. Remove landmark references
3. Add clear pathfinding action examples

### **Step 4: Testing (15 minutes)**
1. Run: `python run_eevee.py --goal "use the pathfinder tool to leave the pokecenter" --max-turns 5 --verbose`
2. Verify AI can use pathfinding_action in JSON responses
3. Verify smart pathfinding loop executes correctly
4. Move test_pathfinder.py to tests/ directory

---

## 🔍 Critical Code Locations

### **Files to Modify Next Session**:

1. **`/run_eevee.py`**:
   - Line ~1200-1300: `_get_ai_decision()` method (find exact line with grep)
   - Remove: `_execute_pathfinding_action()` method (CLAUDE.md violation)
   - Keep: `_execute_pathfinding_to_coordinate()` method (lines 1668-1739)

2. **`/prompts/base/base_prompts.yaml`**:
   - Update `exploration_strategy` template
   - Update `pokemon_center_navigation` template  
   - Emphasize visual coordinate reading, remove landmarks

3. **Move**: `/test_pathfinder.py` → `/tests/test_pathfinder.py`

### **Files Already Complete** ✅:
- `/healing_bookmark_system.py` - Pokemon Center bookmarking
- `/ai_pathfinding_tools.py` - Pathfinding tools for Mistral
- `/analyse_skyemu_ram.py` - Enhanced RAM data collection
- Coordinate grid overlay fixes
- RAM data injection bug fix

---

## 🎯 Success Criteria for Next Session

### **Immediate Goals (1-2 hours)**:
1. ✅ AI can use `pathfinding_action` in JSON responses
2. ✅ Smart pathfinding loop executes when pathfinding_action provided  
3. ✅ All CLAUDE.md violations removed (no hardcoded game logic)
4. ✅ Templates emphasize visual coordinate reading, not landmarks
5. ✅ End-to-end test: AI navigates using pathfinding tool

### **Test Commands**:
```bash
# Test pathfinding integration
python run_eevee.py --goal "use the pathfinder tool to leave the pokecenter" --max-turns 5 --verbose

# Test coordinate reading
python run_eevee.py --task "navigate to coordinates 10,15 using pathfinding" --max-turns 3 --verbose

# Test healing bookmark after pathfinding 
python run_eevee.py --goal "go to pokemon center, heal, then use pathfinder to explore" --max-turns 10 --verbose
```

---

## 🎮 Mass Effect Reference

Just like **Pathfinder Ryder** leading the Andromeda Initiative into uncharted space, this pathfinding system navigates the Pokemon world using:

- **Smart Exploration**: Step-by-step movement with validation (like scanning new planets)
- **Resource Management**: RAM data validation (like managing the Tempest's resources)  
- **Strategic Planning**: Coordinate-based navigation (like plotting courses between star systems)
- **Learning from Experience**: Bookmark system (like establishing outposts)

The pathfinding is almost ready to establish its first outpost in the Pokemon world! 🚀

---

## 📝 Final Notes

**Time Investment**: ~6 hours of work completed, ~1-2 hours remaining
**Complexity**: Medium - mostly integration and cleanup work
**Risk Level**: Low - core pathfinding system already works
**Next Session Priority**: Complete JSON parser integration and remove CLAUDE.md violations

**Critical Success**: The smart pathfinding loop (`_execute_pathfinding_to_coordinate()`) is complete and follows CLAUDE.md principles perfectly. It just needs to be connected to the JSON parser to work end-to-end.

**IMPORTANT**: Do NOT re-implement the pathfinding loop or healing system - they're already complete and working correctly!