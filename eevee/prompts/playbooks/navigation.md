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

### **Core Exploration Strategy**
- **Goal**: Explore every part of the current area systematically
- **Method**: Depth-first search - pick a direction and follow it completely
- **Completion**: Area is "done" when you've walked on every possible tile
- **Next area**: Find exits/entrances to move to new areas

## 🗺️ **SYSTEMATIC AREA EXPLORATION**

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
- **Rule 3**: Try each branch systematically (up, right, down, left)
- **Rule 4**: Don't leave an area until you've tried every possible path

### **Movement Strategy**
- **One step at a time**: Move one tile, observe, then decide next move
- **Systematic coverage**: Visit every walkable tile in the area
- **Path following**: Follow obvious paths (lighter colored ground, clearings)
- **Backtracking**: Return to previous locations to try unexplored branches

## 🚫 **COMMON MISTAKES TO AVOID**

### **DO NOT**:
- ❌ **Try to initiate battles** (they happen automatically)
- ❌ **Press A to start trainer battles** (battles start when you get close)
- ❌ **Get stuck in loops** (if direction doesn't work after 2 tries, try different direction)
- ❌ **Rush to specific locations** (systematic exploration finds everything)
- ❌ **Ignore side paths** (side paths often have trainers and items)

### **DO**:
- ✅ **Explore systematically** (visit every possible area)
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

## 🔧 **PROBLEM SOLVING**

### **When Stuck in One Spot**
1. **Try perpendicular directions** (if stuck going up/down, try left/right)
2. **Try opposite direction** (if stuck going right, try left)  
3. **Look for interactions** (press A near objects, NPCs, signs)
4. **Backtrack** to previous location and try different route

### **When Lost or Confused**
1. **Stop and observe** current surroundings
2. **Identify area type** (forest, route, cave, city)
3. **Pick one direction** and explore it completely
4. **Backtrack** to starting point and try next direction
5. **Repeat** until area is fully mapped

### **When No Progress Made**
- **Problem**: Moving in circles or hitting invisible walls
- **Solution**: Try completely different direction
- **Method**: If going horizontal, try vertical (and vice versa)
- **Last resort**: Press A to interact with environment

## 📍 **AREA TYPES & STRATEGIES**

### **Forests (like Viridian Forest)**
- **Layout**: Maze-like with many paths and dead ends
- **Strategy**: Follow each path to completion before trying next
- **Trainers**: Scattered throughout, will battle when you get close
- **Completion**: When all paths explored and no new areas to discover

### **Routes (numbered paths between cities)**
- **Layout**: Usually linear with some side branches
- **Strategy**: Follow main path, explore all side branches
- **Trainers**: Usually positioned along main and side paths
- **Completion**: Reached the destination city/area

### **Cities and Towns**
- **Layout**: Buildings, Pokemon Centers, shops
- **Strategy**: Enter every building, talk to NPCs
- **Battles**: Usually fewer trainers, mostly in gyms
- **Completion**: Visited all buildings and services

This playbook focuses on the core mechanics: **systematic exploration where battles happen automatically**. The AI's job is to explore areas completely, not to chase specific targets.