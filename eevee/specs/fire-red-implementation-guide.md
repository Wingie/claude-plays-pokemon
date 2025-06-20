# Fire Red Coordinate System - Implementation Guide
## Key Technical Breakthroughs & Practical Steps

**Date**: June 19, 2025  
**Purpose**: Practical implementation roadmap based on research findings

---

## Critical Discovery: Fire Red Memory System 🔍

### **Why Previous Attempts Failed**
```
Game Boy Color Pokemon Red:
├── Fixed RAM addresses (never change)
├── Player X: 0xD361 (always)
├── Player Y: 0xD362 (always)
└── Simple direct reading

Pokemon Fire Red (GBA):
├── Dynamic Memory Allocation (DMA)
├── Pointer-based system
├── Addresses change during gameplay
└── Must follow pointer chains
```

### **The Breakthrough Solution**
**Fire Red uses 3 dynamic save blocks**:
```
Static Pointers (never change):
├── 0x3005008 → Points to SaveBlock8 (map data)
├── 0x300500C → Points to SaveBlock1 (personal data)  
└── 0x3005010 → Points to SaveBlock2 (box data)

Dynamic Content (changes constantly):
├── SaveBlock8 content moves in memory
├── Must read pointer first, then follow it
└── Coordinates at SaveBlock8 + offset
```

### **Exact Implementation Method**
```python
def get_fire_red_coordinates():
    # Step 1: Read the dynamic pointer
    saveblock8_ptr = read_32bit_little_endian(0x3005008)
    
    # Step 2: Validate pointer is in GBA RAM range
    if not (0x02000000 <= saveblock8_ptr < 0x04000000):
        return None  # Invalid pointer
    
    # Step 3: Follow pointer and read coordinates
    player_x = read_16bit_little_endian(saveblock8_ptr + 0x0000)
    player_y = read_16bit_little_endian(saveblock8_ptr + 0x0002)
    
    # Step 4: Read map information
    map_bank = read_8bit(saveblock8_ptr + 0x0004)  # Likely offset
    map_id = read_8bit(saveblock8_ptr + 0x0005)    # Likely offset
    
    return {
        'x': player_x,
        'y': player_y, 
        'map_bank': map_bank,
        'map_id': map_id,
        'saveblock_ptr': saveblock8_ptr  # For debugging
    }
```

---

## Integration with Existing SkyEmu System 🔧

### **Your Existing Infrastructure** ✅
From `analyse_skyemu_ram.py`, you already have:
```python
class SkyEmuClient:
    def read_byte(self, addresses)          # ✅ Working
    def read_bytes(self, address, length)   # ✅ Working  
    def read_pointer(self, pointer_address) # ✅ Working!
    def read_bytes_via_pointer(...)         # ✅ Perfect for Fire Red!
```

### **What We Need to Add** 🆕
```python
class FireRedCoordinateReader:
    def __init__(self, skyemu_client):
        self.client = skyemu_client
        self.saveblock8_base = 0x3005008
        self.last_valid_coords = None
        self.coord_cache_time = 0
        self.cache_duration = 1.0  # Cache for 1 second
    
    def get_current_position(self):
        # Use your existing read_bytes_via_pointer method!
        try:
            # Read X coordinate via pointer
            x_data = self.client.read_bytes_via_pointer(
                self.saveblock8_base, 
                offset=0x0000, 
                length=2
            )
            
            # Read Y coordinate via pointer  
            y_data = self.client.read_bytes_via_pointer(
                self.saveblock8_base,
                offset=0x0002,
                length=2
            )
            
            if x_data and y_data:
                x = int.from_bytes(x_data, byteorder='little')
                y = int.from_bytes(y_data, byteorder='little') 
                return (x, y)
                
        except Exception as e:
            print(f"Coordinate read failed: {e}")
            return self.last_valid_coords
    
    def get_map_info(self):
        # Read map bank and ID
        try:
            map_data = self.client.read_bytes_via_pointer(
                self.saveblock8_base,
                offset=0x0004,  # Estimated offset 
                length=2
            )
            if map_data:
                map_bank = map_data[0]
                map_id = map_data[1] 
                return (map_bank, map_id)
        except:
            return None
```

---

## Immediate Implementation Steps 🚀

### **Step 1: Test Coordinate Reading** (30 minutes)
```python
# Add to existing analyse_skyemu_ram.py
def test_fire_red_coordinates():
    client = SkyEmuClient()
    coord_reader = FireRedCoordinateReader(client)
    
    print("Testing Fire Red coordinate reading...")
    for i in range(10):
        coords = coord_reader.get_current_position()
        print(f"Attempt {i+1}: {coords}")
        time.sleep(1)
        
        # Move player manually and see if coordinates change
        input("Move player and press Enter...")
```

### **Step 2: Validate Coordinate Changes** (15 minutes)
- Run test script
- Move player character manually in game
- Verify coordinates change as expected
- Document working offsets

### **Step 3: Integrate with Eevee System** (60 minutes)
```python
# Add to eevee_agent.py
class EeveeAgent:
    def __init__(self, ...):
        # Add coordinate reader
        if CONTROLLER_TYPE == "skyemu":
            self.coordinate_reader = FireRedCoordinateReader(self.controller.skyemu)
        else:
            self.coordinate_reader = None
    
    def _get_current_position(self):
        """Get exact player coordinates instead of visual analysis"""
        if self.coordinate_reader:
            return self.coordinate_reader.get_current_position()
        else:
            # Fallback to visual methods
            return self._visual_position_estimate()
```

### **Step 4: Replace Visual Navigation** (90 minutes)
```python
# Replace in continuous gameplay loop
def start_continuous_gameplay(self, goal, ...):
    # OLD: Visual analysis
    # game_context["overworld_analysis"] = self._detect_overworld_context(image_data)
    
    # NEW: Coordinate-based context
    current_coords = self._get_current_position()
    if current_coords:
        game_context["coordinates"] = {
            "x": current_coords[0],
            "y": current_coords[1], 
            "position_type": "exact_coordinates"
        }
        
        # Add coordinate-based navigation advice
        game_context["navigation_advice"] = self._get_coordinate_navigation_advice(
            current_coords, goal
        )
```

---

## Coordinate-Based Viridian Forest Strategy 🌲

### **Landmark Coordinate Discovery**
```python
# Key locations to discover and store
VIRIDIAN_LANDMARKS = {
    'pokemon_center_entrance': None,  # To be discovered
    'viridian_forest_entrance': None, # To be discovered  
    'route_2_north': None,            # To be discovered
    'route_2_south': None,            # To be discovered
}

def discover_landmark(self, landmark_name):
    """Record current coordinates as a known landmark"""
    coords = self._get_current_position()
    if coords:
        VIRIDIAN_LANDMARKS[landmark_name] = coords
        self.memory.store_landmark(landmark_name, coords)
        print(f"📍 Recorded {landmark_name} at {coords}")
```

### **Route Planning Between Landmarks**
```python
def plan_route_to_landmark(self, target_landmark):
    current_pos = self._get_current_position()
    target_pos = VIRIDIAN_LANDMARKS.get(target_landmark)
    
    if current_pos and target_pos:
        # Calculate direct path
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        
        # Convert to button sequence
        buttons = []
        if dx > 0: buttons.extend(['right'] * dx)
        elif dx < 0: buttons.extend(['left'] * abs(dx))
        if dy > 0: buttons.extend(['down'] * dy)  
        elif dy < 0: buttons.extend(['up'] * abs(dy))
        
        return buttons
    
    return None  # Cannot plan route
```

---

## Enhanced Prompting with Coordinates 💬

### **Coordinate-Aware Prompts**
```python
def build_coordinate_navigation_prompt(self, goal, current_coords, known_landmarks):
    landmark_distances = self._calculate_landmark_distances(current_coords)
    
    prompt = f"""# Pokemon Fire Red Navigation Expert - Coordinate System

**CURRENT POSITION**: X={current_coords[0]}, Y={current_coords[1]}
**GOAL**: {goal}

**NEARBY LANDMARKS**:
{self._format_nearby_landmarks(landmark_distances)}

**COORDINATE NAVIGATION**:
- Use exact coordinates for precise movement planning
- Direct distance to Pokemon Center: {landmark_distances.get('pokemon_center', 'unknown')} steps
- Direct distance to Viridian Forest: {landmark_distances.get('viridian_forest', 'unknown')} steps

**STRATEGIC DECISION**:
Based on coordinates, what's the most efficient movement to achieve: {goal}?
Provide button sequence for optimal path.
"""
    return prompt
```

---

## Success Criteria & Testing 📊

### **Phase 1 Success** (This Week)
- [ ] Successfully read Fire Red coordinates via SkyEmu
- [ ] Coordinates change correctly when player moves
- [ ] Integration with Eevee system working
- [ ] No more reliance on visual ASCII grid

### **Phase 2 Success** (Next Week)  
- [ ] Record Pokemon Center coordinates
- [ ] Record Viridian Forest entrance coordinates
- [ ] Plan direct route between landmarks
- [ ] Execute route with >90% success rate

### **Phase 3 Success** (Week 3)
- [ ] Automatic Pokemon Center healing runs
- [ ] Automatic return to Viridian Forest training
- [ ] Route optimization based on success/failure
- [ ] Strategic decision making based on Pokemon HP

---

## Debugging & Troubleshooting 🔧

### **Common Issues**
```python
def debug_coordinate_system(self):
    """Debug coordinate reading issues"""
    
    # Test 1: Can we read the base pointer?
    ptr = self.client.read_pointer(0x3005008)
    print(f"SaveBlock8 pointer: 0x{ptr:08X}" if ptr else "Pointer read failed")
    
    # Test 2: Is pointer in valid range?
    if ptr and (0x02000000 <= ptr < 0x04000000):
        print("✅ Pointer in valid GBA RAM range")
    else:
        print("❌ Pointer invalid or out of range")
    
    # Test 3: Can we read data at pointer location?
    if ptr:
        test_data = self.client.read_bytes(ptr, 8)
        print(f"Data at pointer: {test_data.hex() if test_data else 'Read failed'}")
    
    # Test 4: Compare with known working addresses
    self._compare_with_known_addresses()
```

### **Alternative Offset Discovery**
```python
def scan_for_coordinate_offsets(self):
    """If standard offsets don't work, scan for coordinates"""
    ptr = self.client.read_pointer(0x3005008)
    if not ptr:
        return
    
    print("Scanning for coordinate patterns...")
    for offset in range(0, 64, 2):  # Check first 64 bytes, 2-byte aligned
        try:
            data = self.client.read_bytes(ptr + offset, 2)
            if data:
                value = int.from_bytes(data, byteorder='little')
                print(f"Offset 0x{offset:02X}: {value} (0x{value:04X})")
        except:
            continue
```

---

**Next Action**: Implement Step 1 (Test Coordinate Reading) using existing SkyEmu infrastructure.