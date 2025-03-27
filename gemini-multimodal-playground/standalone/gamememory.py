
class GameMemory:
    def __init__(self):
        self.locations_visited = []
        self.npcs_met = []
        self.items_found = []
        self.current_location = "Unknown"
        self.current_objective = "Find the Professor"
        self.observations = []
        self.turn_history = []
        self.discoveries = []
        
    def update_from_response(self, response_text):
        """Extract information from Gemini's response to update memory"""
        # Simple parsing logic - this can be made more sophisticated
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip().lower()
            # Location detection
            if "i am in" in line or "currently in" in line or "this is" in line and "room" in line:
                possible_location = line.split("in")[-1].strip()
                if len(possible_location) > 3 and possible_location not in self.locations_visited:
                    self.locations_visited.append(possible_location)
                    self.current_location = possible_location
            
            # NPC detection
            if "talk" in line and "to" in line or "spoke" in line or "speaking" in line:
                for word in line.split():
                    if len(word) > 3 and word not in ["talk", "spoke", "with", "speaking", "talked"]:
                        if word not in self.npcs_met and not any(char.isdigit() for char in word):
                            self.npcs_met.append(word)
            
            # Item detection
            if "found" in line or "picked up" in line or "obtained" in line:
                for word in line.split():
                    if len(word) > 3 and word not in ["found", "picked", "obtained"]:
                        if word not in self.items_found:
                            self.items_found.append(word)
            
            # Save significant observations
            if "!" in line or "important" in line or "note" in line:
                if len(line) > 10 and line not in self.observations:
                    self.observations.append(line)
        
        # Limit the size of each list to keep memory manageable
        self.locations_visited = self.locations_visited[-5:]
        self.npcs_met = self.npcs_met[-5:]
        self.items_found = self.items_found[-5:]
        self.observations = self.observations[-3:]
    
    def add_turn_summary(self, buttons_pressed, observation):
        """Add a summary of the current turn to the history"""
        summary = {
            "turn": len(self.turn_history) + 1,
            "buttons": buttons_pressed,
            "observation": observation[:100] + "..." if len(observation) > 100 else observation
        }
        print(summary)
        self.turn_history.append(summary)
        # Keep only the last 5 turns
        self.turn_history = self.turn_history[-5:]
        
        # Add to GameMemory class
    def add_discovery(self, discovery_type, description):
        """Record a new discovery"""
        discovery = {
            "type": discovery_type,  # location, npc, item, pokemon
            "description": description,
            "turn": len(self.turn_history)
        }
        self.discoveries.append(discovery)
        
    def generate_summary(self):
        """Generate a summary of the memory for the prompt"""
        summary = "## Game Memory\n"
        
        summary += "**Current Location:** " + self.current_location + "\n"
        summary += "**Current Objective:** " + self.current_objective + "\n\n"
        
        if self.locations_visited:
            summary += "**Locations Visited:** " + ", ".join(self.locations_visited) + "\n"
        
        if self.npcs_met:
            summary += "**NPCs Met:** " + ", ".join(self.npcs_met) + "\n"
        
        if self.items_found:
            summary += "**Items Found:** " + ", ".join(self.items_found) + "\n"
        
        if self.observations:
            summary += "\n**Key Observations:**\n- " + "\n- ".join(self.observations) + "\n"
        
        if self.turn_history:
            summary += "\n**Recent Actions:**\n"
            for turn in self.turn_history:
                summary += f"- Turn {turn['turn']}: Pressed {', '.join(turn['buttons'])} → {turn['observation']}\n"
        
        return summary

# Initialize memory at the beginning of your script (after other initializations)
game_memory = GameMemory()

# Create the initial message with comprehensive instructions
init_message = [
    {"role": "user", "content": """
# Pokemon Game Agent Guide
You are playing Pokemon on a game boy advanced.
     
## Available Controls
- Up, Down, Left, Right: Move your character in that direction
- A: Interact/Confirm - Use when facing NPCs, signs, doors, or to confirm menu selections
- B: Cancel/Back - Exit menus or speed up text
- Start: Open main menu (Pokemon, Items, Save, etc.)
- Select: Rarely used, specific functions

## Game Understanding
- **Screen Types**: 
  * Overworld: Free movement in the environment
  * Dialog: Text boxes with conversation or information
  * Menu: Selection screens for items, Pokemon, etc.
  * Battle: Turn-based combat with wild Pokemon or trainers
  
- **Common Elements**:
  * NPCs: Characters you can talk to
  * Buildings: Can be entered through doors
  * Items: Collectible objects on the ground (often appear as small balls)
  * Pokemon Centers: Buildings with red roofs for healing Pokemon
  * PokeMarts: Buildings with blue roofs for buying items

## Navigation Strategy
1. Build a mental map using cardinal directions (North, South, East, West)
2. Note landmarks and connections between areas
3. Explore systematically, starting from one corner and moving methodically
4. Remember doors, paths, and blocked routes for future reference

## Decision Making
1. Observe the current screen carefully
2. Identify important elements and game state
3. Consider your current objective and location
4. Choose the most appropriate action
5. If an action doesn't work, try alternatives

## Navigation Guidelines
- **Room Transitions**:
  * Doors: Usually rectangular openings in walls - face them and press A to enter
  * Stairs: Look for step-like patterns - up stairs are usually lighter, down stairs darker
  * Carpets: Colored rectangles on the floor often indicate exits or stairs
  * Gates: Outdoor passages between areas - walk through or interact with A
  
- **Common Room Types**:
  * Houses: Small buildings with basic furniture, often have two floors
  * Pokémon Centers: Red-roofed buildings with healing services
  * Gyms: Large distinctive buildings with trainers inside
  * Labs: Professor's labs contain research equipment and books
  * Caves: Dark areas with rocky terrain and multiple paths

- **Navigation Markers**:
  * Look for colored tiles/carpets that often indicate stairs or exits
  * Arrows or signs pointing to doorways or paths
  * NPCs often stand near important room transitions
  * Different floor textures can indicate where you can or cannot walk

     ## Stair Navigation - IMPORTANT
- Stairs in Pokémon games are **objects** you must approach and interact with:
  * Stairs are NOT navigated by pressing "up" or "down" buttons directly
  * You must FIRST position your character ON or NEXT TO the staircase
  * In the image, stairs appear as step-like patterns on the side of the room
  * To use stairs:
     1. Walk TO the staircase (use left/right/up/down to position yourself)
     2. Stand ON or DIRECTLY FACING the first step
     3. Press the direction button TOWARD the stairs (if facing stairs, usually "left" or "right")
     4. Your character will automatically climb or descend

- Look at these visual indicators for stairs:
  * Stairs appear as visible step patterns on walls
  * They often have a different color or texture from surrounding tiles
  * In the current image, you can see stairs on the LEFT side of the room
  * You need to walk LEFT to reach those stairs, not press "up"

     ## Game World Perspective
- The game uses a top-down 2D view where:
  * Your character is viewed from above
  * "Up" button moves your character toward the top of the screen
  * "Down" button moves your character toward the bottom of the screen
  * "Left" and "Right" buttons move your character left and right on the screen
  * These directions are relative to the SCREEN, not your character's facing direction
  * The buttons do NOT directly correspond to "upstairs" or "downstairs"

- To interact with objects (including stairs):
  * Position your character directly adjacent to the object
  * Face toward the object (use movement buttons to change facing direction)
  * Press A to interact when facing the object
  * For some objects like stairs, simply moving toward them will trigger the interaction

 ## Systematic Exploration Framework
- When exploring a building with multiple floors:
  1. Completely explore one floor before moving to another floor
  2. Make a mental note of which floor you are currently on (1F, 2F, etc.)
  3. After fully exploring a floor, only then move to another floor
  4. Once you've explored a new floor, don't return to previous floors unless:
     * You found information directing you there
     * You've fully explored all other accessible floors
     * You're specifically backtracking to reach a new area

## Track your exploration progress:
  * Divide each room into sections (north, south, east, west)
  * Check all objects and NPCs in each section before moving on
  * Mark floors as "completely explored" or "partially explored" in your memory
  * Avoid revisiting areas unless you have a specific reason 
     
## Memory Management
After each observation, update your mental map so thateach of your text output is saved
      and fed back to you as recent actions so you dont get into a loop. 
     Its good for you to discover and note down:
- Current location name and description
- NPCs encountered (with any important dialog)
- Items found or obtained
- Key observations about the environment
- Recent actions taken and their results

## Screen Analysis Procedure
1. First identify the screen type (Overworld, Dialog, Menu, Battle)
2. For Overworld: Note character position, exits, NPCs, and interactive objects
3. For Dialog: Read and interpret the text, identify the speaker
4. For Menus: Identify all options and current selection
5. For Battles: Note your Pokemon, enemy Pokemon, and available actions

## Troubleshooting
If you encounter unexpected results:
1. Press B to cancel any menus or dialog
2. Try moving in all four directions to check for paths
3. If stuck in a loop, vary your approach (e.g., try a different path)
4. If completely lost, use Start to open the map (but remember to press b to get back to the game from the menu)
     
## Available function calls:
- You must use function call to pokemon_controller to control the emulator, providing a list of buttons in sequence
"""}
]