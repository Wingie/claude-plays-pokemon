import random
import numpy as np
from PIL import Image

class GameMemory:
    def __init__(self):
        # Existing attributes
        self.locations_visited = []
        self.npcs_met = []
        self.items_found = []
        self.current_location = "Unknown"
        self.current_objective = "Find the Professor"
        self.observations = []
        self.turn_history = []
        
        #  spatial awareness attributes
        self.room_grids = {}  # Store room layouts
        self.current_position = (0, 0)  # Approximate position
        self.failed_moves = []  # Track failed movements
        self.current_floor = "1F"  # Track current floor
        self.barrier_positions = []  # Track barriers
        
    def record_failed_move(self, direction):
        """Record a failed movement attempt"""
        failed_move = (self.current_position, direction)
        if failed_move not in self.failed_moves:
            self.failed_moves.append(failed_move)
            print(f"Recorded failed move: {direction} from {self.current_position}")
    
    def is_stuck_in_loop(self, window_size=3):
        """Detect if the agent is stuck in a loop of repetitive actions"""
        if len(self.turn_history) < window_size * 2:
            return False
            
        recent_actions = [tuple(turn["buttons"]) for turn in self.turn_history[-window_size:]]
        previous_actions = [tuple(turn["buttons"]) for turn in self.turn_history[-(window_size*2):-window_size]]
        
        # Check if the same sequence of actions is being repeated
        return recent_actions == previous_actions
    
    def suggest_alternative_action(self):
        """Suggest an alternative action when stuck in a loop"""
        # Check which directions haven't been tried recently
        tried_directions = set()
        for turn in self.turn_history[-5:]:
            for button in turn["buttons"]:
                if button in ["up", "down", "left", "right"]:
                    tried_directions.add(button)
                    
        all_directions = {"up", "down", "left", "right"}
        untried_directions = all_directions - tried_directions
        
        if untried_directions:
            return list(untried_directions)[0]
        elif random.random() > 0.5:
            return "b"  # Try canceling
        else:
            # Try a completely different approach
            return random.choice(["down", "left", "a", "start"])
    
    def add_turn_summary(self, buttons_pressed, observation, barrier_detected=False):
        """Enhanced turn summary with barrier detection"""
        summary = {
            "turn": len(self.turn_history) + 1,
            "buttons": buttons_pressed,
            "observation": observation[:100] + "..." if len(observation) > 100 else observation,
            "barrier_detected": barrier_detected
        }
        self.turn_history.append(summary)
        
        # Keep the last 10 turns for better context
        self.turn_history = self.turn_history[-10:]
        
        # Update barriers if detected
        if barrier_detected and buttons_pressed:
            direction = buttons_pressed[-1]  # The last button press that hit barrier
            self.record_failed_move(direction)
    
    def generate_summary(self):
        """Enhanced summary with spatial awareness"""
        summary = "## Game Memory\n"
        
        summary += "**Current Location:** " + self.current_location + "\n"
        summary += "**Current Floor:** " + self.current_floor + "\n"
        summary += "**Current Objective:** " + self.current_objective + "\n\n"
        
        if self.locations_visited:
            summary += "**Locations Visited:** " + ", ".join(self.locations_visited) + "\n"
        
        if self.npcs_met:
            summary += "**NPCs Met:** " + ", ".join(self.npcs_met) + "\n"
        
        if self.items_found:
            summary += "**Items Found:** " + ", ".join(self.items_found) + "\n"
        
        # Add barrier information and navigation advice
        if self.failed_moves:
            summary += "\n**Navigation Information:**\n"
            directions = [d for _, d in self.failed_moves[-3:]]
            summary += f"- Recently blocked directions: {', '.join(directions)}\n"
            
        # Loop detection - CRITICAL enhancement
        if self.is_stuck_in_loop():
            summary += "\n**IMPORTANT NAVIGATION ALERT:**\n"
            summary += "- You appear to be stuck in a movement loop!\n"
            summary += "- There must be furniture or walls blocking your path\n"
            summary += f"- Try a completely different approach: '{self.suggest_alternative_action()}'\n"
            summary += "- To reach the stairs, find a path AROUND furniture\n"
        
        if self.observations:
            summary += "\n**Key Observations:**\n- " + "\n- ".join(self.observations) + "\n"
        
        # Enhanced turn history with barrier information
        if self.turn_history:
            summary += "\n**Recent Actions:**\n"
            for turn in self.turn_history[-5:]:  # Show 5 most recent
                barrier_info = " [BARRIER DETECTED]" if turn.get("barrier_detected") else ""
                summary += f"- Turn {turn['turn']}: Pressed {', '.join(turn['buttons'])}{barrier_info} → {turn['observation']}\n"
        
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

## Screen Analysis Tips
1. First identify the screen type (Overworld, Dialog, Menu, Battle)
2. For Overworld: Note character position, exits, NPCs, and interactive objects
3. For Dialog: Read and interpret the text, identify the speaker
4. For Menus: Identify all options and current selection
5. For Battles: Note your Pokemon, enemy Pokemon, and available actions

## Troubleshooting if something goes wrong
If you encounter unexpected results:
1. Press B to cancel any menus or dialog
2. Try moving in all four directions to check for paths
3. If stuck in a loop, vary your approach (e.g., try a different path)
4. If completely lost, use Start to open the map (but remember to press b to get back to the game from the)
     
## Barrier Navigation - CRITICAL
- When you encounter a barrier (furniture, walls, counters):
  * You CANNOT walk through barriers - you must go AROUND them
  * If you try to move in a direction and don't change position, there's a barrier
  * Look for an alternate path - if you can't go right, try going down then right
  * If your recent movements aren't working, try a completely different direction
  * DO NOT repeat the same movement pattern if it's not working

## Room Navigation Strategy
- For rooms with furniture (like the bedroom you're in):
  * Furniture blocks your path - you must navigate around it
  * There is always a valid path to reach stairs or doors
  * Sometimes you need to plan and think step by step by describing the image, 
  * It's important to make a plan for every navigation goal so that you can 
     think about how to sequence and plan out the button presses.
  * Review the memory sumary to ensure you dont repeat the same strategy again and again. be varied.

## When You're Stuck
- If the memory indicates you're in a movement loop:
  1. Stop repeating the failed approach
  2. Try a completely different path (often the opposite direction)
  3. Map out the room by trying each direction systematically
  4. Remember that you might need to take a longer path around barriers
     
## Available function calls:
- You must use function call to pokemon_controller to control the emulator, providing a list of buttons in sequence
"""}
]

def are_images_similar(image1_path, image2_path, threshold=0.95):
    """Compare two images to detect if movement was blocked by a barrier"""
    try:
        img1 = Image.open(image1_path).convert('RGB')
        img2 = Image.open(image2_path).convert('RGB')
        
        # Focus on game area only by cropping
        img1 = img1.resize((200, 200))
        img2 = img2.resize((200, 200))
        
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Simple comparison - check percentage of identical pixels
        similar_pixels = np.sum(np.abs(arr1 - arr2) < 10) / arr1.size
        print(similar_pixels)
        return similar_pixels > threshold
    except Exception as e:
        print(f"Error comparing images: {e}")
        return False