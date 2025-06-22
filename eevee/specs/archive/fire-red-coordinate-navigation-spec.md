# Pokemon Fire Red Coordinate-Based Navigation System
## Research-Driven Specification Document

**Date**: June 19, 2025  
**Status**: Research Complete - Ready for Implementation  
**Priority**: High - Solves core navigation issues

---

## Research Summary: Why Current Approaches Failed ❌

### **Problem 1: Visual Analysis Limitations**
- **HSV-based ASCII detection**: User confirmed "quite bad" and unreliable
- **LLM-generated ASCII maps**: User determined "won't work" 
- **Pure visual analysis**: Generally too unreliable for consistent navigation
- **Root Issue**: Pokemon Fire Red visuals too complex for consistent automated analysis

### **Problem 2: RAM Address Discovery Challenges**
- **Fire Red vs Game Boy Color**: Completely different memory systems
- **Fixed addresses don't work**: Fire Red uses dynamic memory allocation (DMA)
- **User hit wall**: "Really hard to find the ram mapping for fire red"
- **Root Issue**: Fire Red's pointer-based system where addresses change during gameplay

---

## Research Findings: Successful Pokemon AI Approaches 🚀

### **1. PWhiddy's Pokemon Red Experiments** ⭐ (Most Successful - 7.3k GitHub stars)
**Key Innovation**: Coordinate-based exploration rewards + Reinforcement Learning

**Technical Approach**:
- Replaced frame-based similarity with coordinate-based exploration rewards
- Uses `get_map_location` mapping for areas like "Pallet Town", "Viridian City", "Route 1"
- Map visualization code in dedicated visualization/ directory
- Learns navigation patterns through RL rather than hardcoded pathfinding

**Why It Works**: Eliminates visual interpretation errors by using exact coordinates

### **2. Pokemon Emerald AI Project** 🗺️ (Self-Building Maps)
**Key Innovation**: Real-time map building + A* pathfinding

**Technical Approach**:
- AI builds internal map by testing walkability of each square
- Walkable spaces marked as passable when movement succeeds
- Obstacles marked when movement fails  
- Warps detected when movement leads to new location (doorways, stairs)
- Maps updated in real-time as AI explores
- Uses A* algorithm for navigation between known points

**Why It Works**: Creates accurate maps through direct testing rather than visual analysis

### **3. RL Pathfinding Research** 🧠 (Multi-step Movement)
**Key Innovation**: Pathfinding-assisted move actions vs. single-step movement

**Research Finding**: RL agents benefit from multi-step pathfinding vs. one square at a time
- Multi-step movement allows sampling all reachable squares rather than incremental movement
- Faster exploration and goal reaching
- Agent can move multiple squares in single action

**Why It Works**: Eliminates slow one-button-at-a-time navigation

---

## Pokemon Fire Red Memory System Analysis 🔍

### **The Dynamic Memory Challenge**
Fire Red uses **DMA (Dynamic Memory Allocation)** - completely different from Game Boy Color:

| Game Boy Color | Pokemon Fire Red |
|----------------|------------------|
| Fixed RAM addresses | Pointer-based system |
| Addresses never change | Addresses change during gameplay |
| Direct memory reading | Must follow pointer chains |
| Simple implementation | Complex dynamic discovery |

### **Fire Red Memory Structure** (From Data Crystal Research)
```
Base Pointers (Static Addresses):
├── 0x3005008 → SaveBlock8 (map data) - POINTER CHANGES DYNAMICALLY
├── 0x300500C → SaveBlock1 (personal data) - POINTER CHANGES DYNAMICALLY  
└── 0x3005010 → SaveBlock2 (box data) - POINTER CHANGES DYNAMICALLY

Player Coordinates (Dynamic):
├── X: [0x3005008] + 0x0000 (follow pointer, then add offset)
├── Y: [0x3005008] + 0x0002 (follow pointer, then add offset)
└── Map Bank/ID: Additional offsets in SaveBlock8

Camera Position:
├── Camera X: [0x3005008] + 0x0000
└── Camera Y: [0x3005008] + 0x0002

Why Addresses Change:
├── Entering/exiting buildings
├── Menu transitions
├── Map transitions
└── Game events (battles, dialogues)
```

### **Dynamic Pointer Discovery Method**
```python
# CRITICAL: Must follow pointer chain each time
def get_fire_red_player_coordinates():
    # Step 1: Read the pointer (changes dynamically)
    saveblock8_ptr = read_32bit_pointer(0x3005008)
    
    # Step 2: Follow pointer and read coordinates
    if saveblock8_ptr:
        player_x = read_16bit(saveblock8_ptr + 0x0000)
        player_y = read_16bit(saveblock8_ptr + 0x0002)
        return (player_x, player_y, saveblock8_ptr)
    
    return None  # Pointer not valid
```

---

## Proposed Solution: Hybrid Coordinate-Based Navigation 🎯

### **Phase 1: Dynamic Coordinate Reading System**
**Foundation**: Use SkyEmu HTTP API for real-time pointer following

**Implementation Strategy**:
1. **Extend existing SkyEmu client** with Fire Red specific methods
2. **Dynamic pointer resolution** each time coordinates needed
3. **Coordinate validation** to detect when pointers become invalid
4. **Fallback mechanisms** when dynamic reading fails

**Technical Details**:
```python
class FireRedCoordinateReader:
    def __init__(self, skyemu_client):
        self.client = skyemu_client
        self.saveblock8_ptr = None  # Cache pointer briefly
        self.last_valid_coords = None
    
    def get_current_coordinates(self):
        # Always re-read pointer (it changes!)
        ptr = self.client.read_pointer(0x3005008)
        if ptr and self.validate_pointer(ptr):
            x = self.client.read_bytes(ptr + 0x0000, 2)
            y = self.client.read_bytes(ptr + 0x0002, 2)
            return (x, y, ptr)
        return None
    
    def validate_pointer(self, ptr):
        # Check if pointer is in valid GBA RAM range
        return 0x02000000 <= ptr < 0x04000000
```

### **Phase 2: Coordinate-Based Map Database**
**Foundation**: SQLite database storing coordinate-based navigation data

**Database Schema**:
```sql
-- Real-time coordinate tracking
CREATE TABLE coordinate_history (
    timestamp TEXT,
    x INTEGER, y INTEGER,
    map_bank INTEGER, map_id INTEGER,
    action_taken TEXT,  -- "moved_up", "entered_building", etc.
    success BOOLEAN
);

-- Known landmarks (Pokemon Center, Viridian Forest, etc.)
CREATE TABLE landmarks (
    name TEXT PRIMARY KEY,  -- "pokemon_center_viridian"
    x INTEGER, y INTEGER,
    map_bank INTEGER, map_id INTEGER,
    landmark_type TEXT,  -- "healing", "training", "shop", "transition"
    importance INTEGER   -- 1-10 priority for navigation
);

-- Successful routes between landmarks
CREATE TABLE coordinate_routes (
    from_landmark TEXT,
    to_landmark TEXT,
    coordinate_path TEXT,    -- JSON: [[x1,y1], [x2,y2], ...]
    button_sequence TEXT,    -- JSON: ["up","up","right","a"]
    success_rate REAL,
    avg_steps INTEGER,
    last_used TEXT
);

-- Walkability map (self-building like Pokemon Emerald AI)
CREATE TABLE walkability_map (
    x INTEGER, y INTEGER,
    map_bank INTEGER, map_id INTEGER,
    walkable BOOLEAN,
    is_warp BOOLEAN,      -- Leads to different location
    tested_count INTEGER  -- How many times tested
);
```

### **Phase 3: Multi-Step Pathfinding**
**Foundation**: A* pathfinding with coordinate-based planning

**Implementation**:
```python
class CoordinatePathfinder:
    def plan_route(self, start_coords, target_coords):
        # Use A* with coordinate distance heuristic
        path = self.a_star_search(start_coords, target_coords)
        
        # Convert coordinate path to button sequence
        button_sequence = self.coords_to_buttons(path)
        
        # Validate path using walkability map
        if self.validate_path(path):
            return button_sequence
        else:
            return self.fallback_planning(start_coords, target_coords)
    
    def coords_to_buttons(self, coord_path):
        buttons = []
        for i in range(len(coord_path) - 1):
            dx = coord_path[i+1][0] - coord_path[i][0]
            dy = coord_path[i+1][1] - coord_path[i][1]
            
            if dx > 0: buttons.append("right")
            elif dx < 0: buttons.append("left")
            if dy > 0: buttons.append("down")
            elif dy < 0: buttons.append("up")
        
        return buttons
```

---

## Integration with Existing Eevee System 🔧

### **Replace Visual Navigation Methods**
**Current System**:
```python
# REMOVE: Unreliable visual-based navigation
def _detect_overworld_context(self, image_data):
    # ASCII grid creation using HSV - UNRELIABLE
    
def _create_ascii_grid_overlay(self, image_data):
    # Visual analysis - FAILS TOO OFTEN
```

**New System**:
```python
# ADD: Coordinate-based navigation
def _get_current_position(self):
    # Use Fire Red coordinate reader
    return self.coordinate_reader.get_current_coordinates()

def _plan_movement_to(self, target_landmark):
    # Use coordinate pathfinder
    current_pos = self._get_current_position()
    return self.pathfinder.plan_route(current_pos, target_landmark)
```

### **Enhanced Prompting with Coordinate Data**
**Current**: Visual analysis prompts  
**New**: Coordinate-based prompts with exact position data

```python
def build_navigation_prompt(self, goal, current_coords, known_landmarks):
    return f"""# Pokemon Navigation Expert - Coordinate-Based

**CURRENT POSITION**: {current_coords}
**GOAL**: {goal}

**NEARBY LANDMARKS**:
{self.format_nearby_landmarks(current_coords)}

**SUGGESTED ROUTE**:
{self.get_route_to_goal(current_coords, goal)}

**NAVIGATION TASK**: Use the coordinate data above to make smart movement decisions.
If route is blocked, try alternative paths or explore new areas.
"""
```

---

## Implementation Priority & Timeline 📅

### **Week 1: Foundation (HIGH PRIORITY)**
- [ ] Extend SkyEmu client with Fire Red coordinate reading
- [ ] Implement dynamic pointer following 
- [ ] Create coordinate validation and error handling
- [ ] Test coordinate reading accuracy with real gameplay

### **Week 2: Database & Routes (HIGH PRIORITY)**  
- [ ] Create SQLite coordinate database schema
- [ ] Implement landmark detection and storage
- [ ] Build route recording and playback system
- [ ] Test route efficiency between Pokemon Center ↔ Viridian Forest

### **Week 3: Pathfinding (MEDIUM PRIORITY)**
- [ ] Implement A* pathfinding for coordinates
- [ ] Create multi-step movement planning
- [ ] Add walkability testing (Pokemon Emerald style)
- [ ] Integrate with existing Eevee prompt system

### **Week 4: Integration & Testing (MEDIUM PRIORITY)**
- [ ] Replace visual navigation with coordinate system
- [ ] Update Eevee prompts to use coordinate data
- [ ] Test Viridian Forest training loop automation
- [ ] Performance optimization and error handling

---

## Expected Outcomes & Success Metrics ✅

### **Immediate Benefits**
- **100% reliable positioning** (vs ~70% visual accuracy)
- **10x faster navigation** (multi-step vs single button)
- **Persistent route learning** (builds knowledge over time)
- **Strategic goal achievement** (Pokemon Center ↔ Viridian Forest automation)

### **Success Metrics**
- [ ] Successfully read Fire Red coordinates in real-time
- [ ] Navigate Pokemon Center → Viridian Forest in <30 steps  
- [ ] Navigate Viridian Forest → Pokemon Center in <25 steps
- [ ] Achieve 95%+ route success rate after learning
- [ ] Complete healing cycle (low HP → Pokemon Center → return) automatically

### **Long-term Goals**
- [ ] Full Viridian Forest map exploration
- [ ] Trainer battle location memory
- [ ] Optimal training route discovery
- [ ] Automatic expedition planning based on Pokemon status

---

## Technical Risks & Mitigation 🚨

### **Risk 1: Dynamic Pointers Fail**
**Mitigation**: 
- Multiple fallback pointer addresses
- Visual confirmation when coordinates seem wrong
- Manual calibration mode for unknown situations

### **Risk 2: Coordinate System Inaccuracy**
**Mitigation**:
- Validate coordinates against known landmarks
- Cross-check with visual templates for key locations
- Allow manual coordinate correction

### **Risk 3: SkyEmu API Limitations**
**Mitigation**:
- Implement robust error handling for failed reads
- Cache last known good coordinates
- Fallback to visual navigation when coordinate system fails

---

## References & Sources 📚

### **Technical Documentation**
- [Pokemon Fire Red RAM Map - Data Crystal](https://datacrystal.tcrf.net/wiki/Pokémon_3rd_Generation/Pokémon_FireRed_and_LeafGreen/RAM_map)
- [Fire Red Save Data Structure - PokéCommunity](https://www.pokecommunity.com/threads/fire-red-save-data-structure.349936/)
- [Pokemon Fire Red RAM Offset List - PokéCommunity](https://www.pokecommunity.com/threads/pokemon-firered-ram-offset-list.342546/)

### **Successful AI Projects**
- [PWhiddy's Pokemon Red Experiments - GitHub](https://github.com/PWhiddy/PokemonRedExperiments)
- [Pokemon RL Project - drubinstein.github.io](https://drubinstein.github.io/pokerl/)
- [Pokemon Emerald AI Navigation Blog](https://remptongames.com/2020/06/22/how-i-taught-an-ai-to-play-pokemon-emerald/)

### **Memory Analysis Tools**
- [Notable Breakpoints - Project Pokemon](https://projectpokemon.org/home/docs/other/notable-breakpoints-r31/)
- [GBA Memory Analysis - Cheat Engine Forums](https://forum.cheatengine.org/viewtopic.php?t=562757)
- [Reverse Engineering GBA Games - Starcube Labs](https://www.starcubelabs.com/reverse-engineering-gba/)

---

**Next Step**: Begin Phase 1 implementation with Fire Red coordinate reading system using existing SkyEmu infrastructure.