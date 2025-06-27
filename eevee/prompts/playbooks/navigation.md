# Pokemon Game Navigation - Core Mechanics

## 🎮 **FUNDAMENTAL POKEMON GAME RULES**

### **How Trainer Battles Work**
- **Trainers battle you AUTOMATICALLY** when you enter their line of sight
- **You do NOT press any buttons to start battles** - they happen when you get close
- **Line of sight**: Trainers can see in straight lines (up/down/left/right)
- **Battle initiation**: Trainer will walk up to you and the battle starts automatically
- **Your job**: Explore areas to find trainers (they'll battle you when they see you)

### **How Wild Pokemon Work**  
- **Wild Pokemon appear AUTOMATICALLY** when walking in tall grass
- **You do NOT initiate wild encounters** - they happen randomly while walking
- **Grass areas**: Dark green/textured areas that trigger random encounters
- **Your job**: Walk through grass areas to level up and catch Pokemon

## 🧠 **ASH'S DIRECTION MEMORY**

### **How Direction Memory Works**
- Tracks your last 10 movements to detect patterns
- Identifies which directions lead to progress vs. dead ends
- Adjusts strategy based on what's worked before
- Detects when you're going in circles

### **Using Direction Memory Effectively**
1. **Recent History**:
   - Last 5-10 movements are analyzed
   - Detects repetitive patterns indicating being stuck
   - Identifies which directions have been tried recently

2. **Success Tracking**:
   - Notes which directions led to new areas
   - Remembers blocked paths to avoid retrying them
   - Adjusts strategy based on past success rates

3. **Getting Unstuck**:
   - If stuck, check which directions haven't been tried
   - Prefer directions that led to progress before
   - If all else fails, try interacting with the environment

## 🗺️ **ASH'S EXPLORATION APPROACH**

### **The Pokemon Exploration Loop**
1. **Enter a new area** (Route, Forest, Cave, etc.)
2. **Pick a direction** and follow it as far as possible
3. **When blocked**, backtrack and try a different path
4. **Battles happen automatically** as you encounter trainers
5. **Continue until area fully explored** (no new paths to try)
6. **Find the exit** to the next area

### **Depth-First Exploration Rules**
- **Rule 1**: Always follow a path to its end before trying alternatives
- **Rule 2**: When you hit a dead end, backtrack to the last fork
- **Rule 3**: Try each branch carefully (up, right, down, left)
- **Rule 4**: Don't leave an area until you've tried every possible path

## 🚫 **COMMON MISTAKES TO AVOID**

### **DO NOT**:
- ❌ **Try to initiate battles** (they happen automatically)
- ❌ **Press A to start trainer battles** (battles start when you get close)
- ❌ **Get stuck in loops** (if direction doesn't work after 2 tries, try different direction)
- ❌ **Rush to specific locations** (thorough exploration finds everything)
- ❌ **Ignore side paths** (side paths often have trainers and items)

### **DO**:
- ✅ **Explore thoroughly** (visit every possible area)
- ✅ **Try different directions** when stuck
- ✅ **Walk toward trainers** (battles start automatically when close)
- ✅ **Backtrack when blocked** (find alternative routes)
- ✅ **Complete areas fully** before moving to next area

## 🎯 **AREA COMPLETION CRITERIA**

### **How to Know an Area is Complete**
- **All paths explored**: You've tried every possible direction from every accessible tile
- **All trainers fought**: No visible trainers remaining (they all battled you already)
- **All items found**: Investigated any visible items or interactive objects
- **Dead ends reached**: Every path leads to either an exit or an obstacle

### **Signs You're Ready for Next Area**
- No new paths to explore in current area
- All visible trainers have been defeated
- Found an exit leading to a new area (cave entrance, city gate, route transition)
- Can't find any unexplored sections

## 🔧 **STUCK RECOVERY STRATEGIES**

### **When Stuck in One Spot**
1. **Try perpendicular directions** (if stuck going up/down, try left/right)
2. **Try opposite direction** (if stuck going right, try left)  
3. **Look for interactions** (press A near objects, NPCs, signs)
4. **Backtrack** to previous location and try different route
5. **Use direction memory** to avoid retrying failed paths

### **When Lost or Confused**
1. **Stop and observe** current surroundings
2. **Identify area type** (forest, route, cave, city)
3. **Pick one direction** and explore it completely
4. **Backtrack** to starting point and try next direction
5. **Repeat** until area is fully mapped

### **Advanced Recovery Techniques**
- **Wall Following**: Keep one hand on the wall to your right/left
- **Grid Search**: Move in expanding squares from starting point
- **Spiral Pattern**: Move in increasingly larger circles
- **Landmark Navigation**: Use distinctive features as reference points

## 📍 **AREA TYPES & STRATEGIES**

### **Forests (like Viridian Forest)**
# 🧭 Ash's Advanced Navigation

## 🔄 Core Navigation Loop
1. **Assess** current position and surroundings
2. **Plan** next 3-5 moves based on environment
3. **Execute** movements while scanning for changes
4. **Verify** progress and adjust strategy

## 🧩 Environment-Based Strategies

### 🌳 Forests (e.g., Viridian Forest)
- **Layout**: Complex maze with dense trees and winding paths
- **Optimal Pathfinding**:
  - Use right-hand wall following
  - Check behind every tree cluster
  - Look for subtle path indicators (worn grass, light patterns)
- **Trainer Detection**:
  - Watch for movement between trees
  - Listen for battle music cues
  - Note trainer line of sight (4-directional)

### 🛣️ Routes
- **Layout**: Linear with branching side paths
- **Efficient Exploration**:
  - Follow main path first
  - Explore side branches thoroughly
  - Use landmarks for orientation
- **Progression Markers**:
  - Route signs
  - Terrain changes
  - Camera perspective shifts

### 🏔️ Caves & Dungeons
- **Layout**: Multi-level with dark areas
- **Navigation Aids**:
  - Use Flash (if available)
  - Follow wall patterns
  - Drop items as breadcrumbs
- **Level Transitions**:
  - Note elevation changes
  - Watch for ladders/stairs
  - Listen for echo changes

## 🧠 Ash's Smart Movement

### Direction Memory
- Tracks last 10 movements
- Detects patterns and loops
- Adjusts strategy based on success rate

### Path Optimization
- Avoids retracing steps
- Prioritizes unexplored areas
- Marks dead ends

## 🚨 Recovery Protocols

### When Stuck:
1. Pause and observe surroundings
2. Check last 5 moves for patterns
3. Try perpendicular directions
4. Look for environmental interactions

### Common Issues:
- **Invisible Walls**: Try diagonal movement
- **Soft Locks**: Save frequently
- **Camera Issues**: Reset view if possible

## 🎯 **PATHFINDING TOOLS & COORDINATE NAVIGATION**

### **Coordinate-Based Navigation (PRIMARY METHOD)**
- **Visual Overlay**: Every screenshot shows X,Y coordinates on all tiles
- **Current Position**: Always visible at screen center with player sprite
- **Target Reading**: Look for destination coordinates on screen overlay
- **Action Format**: Use manual button presses for navigation

### **Navigation Examples**

#### Example 1: Pokemon Center Navigation
```json
{{
  "button_presses": ["up", "up", "right"],
  "reasoning": "Moving toward Pokemon Center visible ahead",
  "context_detected": "navigation"
}}
```

#### Example 2: Trainer Approach
```json
{{
  "button_presses": ["down", "left"],
  "reasoning": "Moving toward trainer for battle",
  "context_detected": "navigation"
}}
```

#### Example 3: Exit Navigation
```json
{{
  "button_presses": ["right", "right", "up"],
  "reasoning": "Heading toward route exit",
  "context_detected": "navigation"
}}
```

### **When to Use Manual vs Coordinate Navigation**

#### ✅ **Use Coordinate Navigation When**:
- Target coordinates are visible on screenshot overlay
- Destination is more than 2-3 tiles away
- Need to navigate around obstacles efficiently
- Moving to specific locations (Pokemon Centers, exits, trainers)
- Goal-directed navigation

#### ❌ **Use Manual Movement When**:
- Coordinate overlay not visible on screenshot
- Target is adjacent (1 tile away)
- In tight spaces requiring precise positioning
- Coordinate navigation system reports failure

### **Coordinate Navigation Best Practices**

1. **Always Read Coordinates First**
   - Scan screenshot for X,Y numbers on tiles
   - Identify your current position coordinates
   - Locate target destination coordinates

2. **Validate Coordinate Sources**
   - Confirm coordinates are from visual overlay
   - Don't guess or estimate coordinate values
   - Use exact coordinates seen on screen

3. **Coordinate Navigation Response Requirements**
   - Include `coordinate_source: "visual_overlay"`
   - Specify exact target coordinates from screen
   - Explain why coordinate navigation is chosen over manual movement

4. **Efficiency Benefits**
   - Replaces 5-10 manual button presses with 1 coordinate navigation action
   - Eliminates getting stuck on obstacles
   - Optimal movement paths automatically calculated
   - Reduces navigation time significantly

### **Navigation Decision Tree**

```
1. Can you see coordinate overlay on screenshot?
   └─ YES: Read target coordinates → Use target_coordinates
   └─ NO: Use manual button presses

2. Is target more than 2 tiles away?
   └─ YES: Prefer coordinate navigation for efficiency
   └─ NO: Manual movement acceptable

3. Are you navigating to specific destination?
   └─ YES: Use coordinate navigation for accuracy
   └─ NO: Exploration can use manual movement
```

## 📊 Performance Metrics
- **Coordinate navigation usage rate**: Should be >70% when coordinates visible
- **Navigation efficiency**: Steps per destination reached
- **Coordinate accuracy**: Successful navigation vs failed attempts
- **Exploration coverage**: Areas mapped with coordinate system
- Ash gets better over time as he learns to prioritize coordinate-based navigation