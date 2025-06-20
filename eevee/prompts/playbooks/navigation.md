# Navigation Knowledge Base

*This playbook contains location knowledge discovered by the AI during gameplay.*

## Discovered Locations and Routes

*AI will populate this section with learned navigation patterns*

## Notable Landmarks

*AI will document significant buildings, NPCs, and terrain features*

## Route Connections

*AI will map out how different areas connect to each other*

## Healing and Service Locations

*AI will note Pokemon Centers, shops, and other useful services*

## Common Navigation Problems & Solutions

### Getting Stuck at Area Boundaries
**Problem**: AI repeatedly tries to move in one direction but can't progress
**Example**: Stuck at "northern edge of Viridian City" pressing UP repeatedly
**Solutions to Try**:
1. **LOOK FOR DOORS/ENTRANCES**: Dark rectangular areas in walls, carpet patterns
2. **WALK TO THE DOOR**: Move toward the entrance point first
3. **ENTER PROPERLY**: Once at door, press UP to enter or DOWN to exit
4. Try different directions (left/right to find proper path)
5. Check if there are any blocking NPCs that need to be talked to

### Door and Entrance Recognition
**What to Look For**:
- **Dark rectangular areas** in walls (building entrances)
- **Carpet/mat patterns** on the ground (entrance indicators)
- **Different floor textures** (transition zones)
- **Archways or doorframes** (visual entrance markers)
- **Color changes** indicating building interiors vs exteriors

**How to Use Doors**:
1. **Identify the door** - Look for dark rectangle in wall
2. **Walk TO the door** - Move your character to stand in front of it
3. **Enter the door** - Press UP when standing at the entrance
4. **Exit buildings** - Press DOWN when on carpet/mat inside

### Area Transition Rules
- **Simple Buildings**: One entrance/exit - dark rectangles + UP to enter, carpet + DOWN to exit
- **Transition Buildings (Route Gates)**: Special buildings connecting different areas
- **Route Transitions**: Usually at map edges, just walk in that direction

### CRITICAL: Transition Building Mechanics
**What are Transition Buildings?**
- Buildings that connect two different areas (like Viridian City ↔ Viridian Forest)
- These buildings have **MULTIPLE exits** - each leads to a different destination
- **NOT** single-door buildings - they have directional carpet exits

**How to Navigate Transition Buildings:**
1. **Enter**: Walk to dark rectangle + UP (same as normal buildings)
2. **Inside**: Look for **multiple carpet areas** - usually north and south ends
3. **Choose Direction**: 
   - **North carpet** = Forward destination (e.g., Viridian Forest)
   - **South carpet** = Back to origin (e.g., Viridian City)
4. **Explore**: Use LEFT/RIGHT to find the correct carpet for your destination
5. **Exit**: Stand on chosen carpet + UP to proceed to that area

**Specific Route: Viridian City → Viridian Forest**
- **Building**: Gatehouse at north edge of Viridian City
- **Inside Layout**: Rectangular room with TWO carpet areas
  - **South Carpet**: Bottom of room (leads back to Viridian City)
  - **North Carpet**: Top of room (leads forward to Viridian Forest)
- **Navigation Strategy**: 
  1. Enter building (dark rectangle + UP)
  2. Use LEFT/RIGHT to explore and find BOTH carpet areas
  3. Move to NORTH carpet (top of room)
  4. Press UP to exit toward Viridian Forest
- **Critical**: Don't exit at first carpet you see - explore to find the correct one!

### Infinite Loop Detection
**Warning Signs**: Same button pressed 3+ consecutive turns
**AI Should**: Immediately try alternative approaches when warned about repetition

## Discovered Routes

**Test Entry**: This is a test navigation note

**2025-06-19 19:09** - Navigation Discovery:
- **From**: Viridian City
- **Direction**: north
- **Leads to**: Viridian Forest
- **Status**: ✅ Confirmed route

**CRITICAL ROUTE KNOWLEDGE - Viridian City to Viridian Forest**:
- **Challenge**: Most common AI failure point - infinite UP/DOWN loop
- **Building Type**: Route Gate (transition building with multiple exits)
- **Success Strategy**: 
  1. Find dark rectangular entrance at north edge of Viridian City
  2. Enter with UP
  3. **CRUCIAL**: Inside, explore LEFT/RIGHT to map the room
  4. Find TWO carpet areas (one at each end)
  5. Move to NORTH carpet (far end of room)
  6. Press UP to exit to Viridian Forest
- **Common Mistake**: Exiting immediately at first carpet (leads back to city)

**2025-06-19 Evening** - Navigation Problem SOLVED:
- **Location**: Northern edge of Viridian City  
- **Issue**: AI stuck pressing UP repeatedly (16+ turns)
- **SOLUTION**: Look for dark rectangular door in wall, walk TO the door, then press UP to enter
- **Status**: ✅ Door navigation system implemented

**2025-06-20** - Door Navigation Rules Added:
- **Viridian Forest Entry**: Dark doorway at north edge - walk to it + UP to enter
- **Building Doors**: Dark rectangles in walls - walk to them + UP to enter  
- **Exit Buildings**: Stand on carpet/mat inside + DOWN to exit
- **Key Learning**: Don't just press directional buttons at boundaries - FIND THE DOOR FIRST!
