
class GameMemory:
    def __init__(self):
        self.locations_visited = []
        self.npcs_met = []
        self.items_found = []
        self.current_location = "Unknown"
        self.current_objective = "Find the Professor"
        self.observations = []
        self.turn_history = []
        
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
        self.turn_history.append(summary)
        # Keep only the last 5 turns
        self.turn_history = self.turn_history[-5:]
    
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

## When Stuck
1. If an action produces no result, try a different approach
2. Look for visual cues you might have missed
3. Try talking to NPCs for hints
4. Check your inventory or Pokemon team via the Start menu
5. Try entering nearby buildings or taking different paths

## Available function calls:
- You must use function call to pokemon_controller to control the emulator, providing a list of buttons in sequence
"""}
]