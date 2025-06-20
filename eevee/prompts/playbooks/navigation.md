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
- **Viridian Forest Entrance**: Dark doorway at north edge of Viridian City
- **Building Entrances**: Dark rectangles in walls, walk to them + UP
- **Building Exits**: Stand on carpet/mat inside + DOWN
- **Route Transitions**: Usually at map edges, just walk in that direction

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
