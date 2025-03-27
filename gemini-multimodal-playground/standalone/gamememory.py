import random
import numpy as np
from PIL import Image
import cv2
import base64
import io
import os
import time

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
        
        # Enhanced spatial awareness attributes
        self.room_grids = {}  # Store room layouts
        self.current_position = (0, 0)  # Approximate position (x, y)
        self.failed_moves = []  # Track failed movements
        self.current_floor = "1F"  # Track current floor
        self.barrier_positions = []  # Track barriers
        
        # Visual mapping enhancements
        self.room_maps = {}  # Store visual maps of rooms
        self.current_map = None  # Current room map as a 2D grid
        self.player_position = None  # Player position in the current map
        self.map_snapshot_path = "map_snapshots"  # Directory to save map snapshots
        
        # Create snapshot directory if it doesn't exist
        if not os.path.exists(self.map_snapshot_path):
            try:
                os.makedirs(self.map_snapshot_path)
            except:
                print("Warning: Could not create map snapshot directory")
        
        # Element colors for visual identification (RGB)
        self.color_map = {
            'player': (255, 0, 0),    # Red - player character
            'carpet': (0, 255, 0),    # Green - walkable areas like carpets
            'stairs': (255, 255, 0),  # Yellow - stairs
            'barrier': (100, 100, 100), # Gray - barriers/furniture
            'path': (0, 0, 255)       # Blue - suggested path
        }
        
        # Tracking game progress
        self.last_screen_hash = None
        self.consecutive_similar_screens = 0
        
    def detect_player_and_elements(self, screenshot_path):
        """
        Analyze screenshot to detect the player character and key elements
        
        This uses basic image processing to find:
        - The player character (typically red hat in Pokémon)
        - Carpets/walkable areas (green areas)
        - Barriers/furniture (by color and position)
        - Stairs (typically light-colored angled patterns)
        """
        try:
            # Load image
            print("#####",screenshot_path)
            img = cv2.imread(screenshot_path)
            if img is None:
                print(f"Error: Failed to load image {screenshot_path}")
                return None
                
            # Convert to RGB (OpenCV uses BGR)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Create a map representation (simplified 16x12 grid)
            height, width = img_rgb.shape[:2]
            
            # Focus on the game area only (remove borders)
            # Assuming the game area is in the center of the screenshot
            game_area_start_x = int(width * 0.1)
            game_area_end_x = int(width * 0.9)
            game_area_start_y = int(height * 0.1)
            game_area_end_y = int(height * 0.9)
            
            game_area = img_rgb[game_area_start_y:game_area_end_y, game_area_start_x:game_area_end_x]
            g_height, g_width = game_area.shape[:2]
            
            # Create a simplified map grid (16x12 cells)
            grid_width, grid_height = 16, 12
            cell_width = g_width // grid_width
            cell_height = g_height // grid_height
            
            # Initialize map grid
            map_grid = np.zeros((grid_height, grid_width), dtype=int)
            
            # Detect player character (looking for red hat color)
            # This is a simplified approach - better detection would use ML
            red_lower = np.array([150, 0, 0])
            red_upper = np.array([255, 100, 100])
            red_mask = cv2.inRange(game_area, red_lower, red_upper)
            red_pixels = np.where(red_mask > 0)
            
            player_position = None
            if len(red_pixels[0]) > 0:
                # Take the center of mass of the red pixels
                player_y = int(np.median(red_pixels[0]))
                player_x = int(np.median(red_pixels[1]))
                
                # Convert to grid coordinates
                player_grid_y = min(player_y // cell_height, grid_height - 1)
                player_grid_x = min(player_x // cell_width, grid_width - 1)
                
                player_position = (player_grid_x, player_grid_y)
                map_grid[player_grid_y, player_grid_x] = 1  # Mark player position
                
                print(f"Detected player at position: {player_position}")
            else:
                print("Could not detect player character")
            
            # Detect carpets/green areas
            green_lower = np.array([0, 150, 0])
            green_upper = np.array([100, 255, 100])
            green_mask = cv2.inRange(game_area, green_lower, green_upper)
            
            # Find contours of green areas
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Mark carpeted areas on the grid
            for contour in contours:
                # Process larger contours only to avoid noise
                if cv2.contourArea(contour) > 50:
                    for point in contour:
                        x, y = point[0]
                        grid_y = min(y // cell_height, grid_height - 1)
                        grid_x = min(x // cell_width, grid_width - 1)
                        map_grid[grid_y, grid_x] = 2  # Mark as carpet
            
            # Detect stairs - looking for yellow/tan colors common in stair graphics
            stair_lower = np.array([150, 150, 0])
            stair_upper = np.array([255, 255, 150])
            stair_mask = cv2.inRange(game_area, stair_lower, stair_upper)
            
            # Find contours for stairs
            stair_contours, _ = cv2.findContours(stair_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            stair_position = None
            
            # Mark stair areas on the grid
            for contour in stair_contours:
                if cv2.contourArea(contour) > 30:
                    # Find the centroid of the stair area
                    M = cv2.moments(contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        # Convert to grid coordinates
                        stair_grid_y = min(cy // cell_height, grid_height - 1)
                        stair_grid_x = min(cx // cell_width, grid_width - 1)
                        
                        map_grid[stair_grid_y, stair_grid_x] = 3  # Mark as stairs
                        stair_position = (stair_grid_x, stair_grid_y)
                        print(f"Detected stairs at position: {stair_position}")
            
            # Create a visual representation of the map
            map_display = self.visualize_map(map_grid, player_position, stair_position)
            
            # Save the most recent map
            self.current_map = map_grid
            self.player_position = player_position
            
            # Save a snapshot of the map
            timestamp = int(time.time())
            map_path = os.path.join(self.map_snapshot_path, f"map_{timestamp}.png")
            cv2.imwrite(map_path, cv2.cvtColor(map_display, cv2.COLOR_RGB2BGR))
            
            return {
                'map_grid': map_grid,
                'player_position': player_position,
                'stair_position': stair_position,
                'map_display': map_display
            }
            
        except Exception as e:
            print(f"Error analyzing screenshot: {str(e)}")
            return None
    
    def visualize_map(self, map_grid, player_pos=None, stair_pos=None):
        """Create a visual representation of the map grid"""
        # Constants for visualization
        cell_size = 20
        grid_height, grid_width = map_grid.shape
        
        # Create a blank RGB image
        vis_map = np.zeros((grid_height * cell_size, grid_width * cell_size, 3), dtype=np.uint8)
        
        # Fill the map based on cell values
        for y in range(grid_height):
            for x in range(grid_width):
                cell_value = map_grid[y, x]
                # Set cell color based on value
                if cell_value == 0:  # Empty space
                    color = (220, 220, 220)  # Light gray
                elif cell_value == 1:  # Player
                    color = self.color_map['player']
                elif cell_value == 2:  # Carpet
                    color = self.color_map['carpet']
                elif cell_value == 3:  # Stairs
                    color = self.color_map['stairs']
                elif cell_value == 4:  # Barrier
                    color = self.color_map['barrier']
                
                # Draw the cell
                y1 = y * cell_size
                y2 = (y + 1) * cell_size
                x1 = x * cell_size
                x2 = (x + 1) * cell_size
                vis_map[y1:y2, x1:x2] = color
                
                # Add grid lines
                cv2.rectangle(vis_map, (x1, y1), (x2, y2), (0, 0, 0), 1)
        
        # Mark player position with a circle if provided
        if player_pos is not None:
            px, py = player_pos
            center_x = px * cell_size + cell_size // 2
            center_y = py * cell_size + cell_size // 2
            cv2.circle(vis_map, (center_x, center_y), cell_size // 2, (255, 0, 0), -1)
        
        # Mark stairs position with a triangle if provided
        if stair_pos is not None:
            sx, sy = stair_pos
            center_x = sx * cell_size + cell_size // 2
            center_y = sy * cell_size + cell_size // 2
            
            triangle_points = np.array([
                [center_x, center_y - cell_size // 2],
                [center_x - cell_size // 2, center_y + cell_size // 2],
                [center_x + cell_size // 2, center_y + cell_size // 2]
            ], np.int32)
            
            cv2.fillPoly(vis_map, [triangle_points], self.color_map['stairs'])
        
        return vis_map
    
    def suggest_path_to_destination(self, destination_type="stairs"):
        """
        Suggest a path from the player's position to a destination
        
        Args:
            destination_type: Type of destination to find ("stairs", "carpet", etc.)
            
        Returns:
            List of movements to reach the destination, or None if no path found
        """
        if self.current_map is None or self.player_position is None:
            print("Cannot suggest path: Map or player position unknown")
            return None
        
        # Find the destination coordinates based on type
        destination = None
        grid_height, grid_width = self.current_map.shape
        
        if destination_type == "stairs":
            # Look for stairs (value 3) in the grid
            stair_positions = np.where(self.current_map == 3)
            if len(stair_positions[0]) > 0:
                # Use the first stairs found
                y = stair_positions[0][0]
                x = stair_positions[1][0]
                destination = (x, y)
        
        if destination is None:
            print(f"Cannot find destination of type '{destination_type}'")
            return None
        
        # Simple path finding using BFS
        visited = np.zeros_like(self.current_map, dtype=bool)
        queue = [(self.player_position, [])]  # (position, path)
        
        movement_map = {
            (0, -1): "up",
            (0, 1): "down",
            (-1, 0): "left",
            (1, 0): "right"
        }
        
        while queue:
            (x, y), path = queue.pop(0)
            
            # Check if we've reached the destination
            if (x, y) == destination:
                return path
            
            # Mark as visited
            visited[y, x] = True
            
            # Try each direction
            for (dx, dy), move_name in movement_map.items():
                nx, ny = x + dx, y + dy
                
                # Check boundaries
                if 0 <= nx < grid_width and 0 <= ny < grid_height:
                    # Check if the cell is walkable and not visited
                    # Values 0 (empty), 2 (carpet), and 3 (stairs) are walkable
                    if not visited[ny, nx] and self.current_map[ny, nx] in [0, 2, 3]:
                        queue.append(((nx, ny), path + [move_name]))
        
        # If we get here, no path was found
        print("No path found to destination")
        return None
    
    def record_failed_move(self, direction):
        """Record a failed movement attempt"""
        if self.player_position is None:
            print("Cannot record failed move: Player position unknown")
            return
            
        failed_move = (self.player_position, direction)
        if failed_move not in self.failed_moves:
            self.failed_moves.append(failed_move)
            print(f"Recorded failed move: {direction} from {self.player_position}")
            
            # Update the map grid to mark this as a barrier in the direction
            if self.current_map is not None:
                x, y = self.player_position
                # Convert direction to delta coordinates
                dx, dy = 0, 0
                if direction == "up":
                    dy = -1
                elif direction == "down":
                    dy = 1
                elif direction == "left":
                    dx = -1
                elif direction == "right":
                    dx = 1
                
                # Mark the cell in that direction as a barrier
                grid_height, grid_width = self.current_map.shape
                barrier_x, barrier_y = x + dx, y + dy
                if 0 <= barrier_x < grid_width and 0 <= barrier_y < grid_height:
                    self.current_map[barrier_y, barrier_x] = 4  # Mark as barrier
    
    def is_stuck_in_loop(self, window_size=3):
        """Detect if the agent is stuck in a loop of repetitive actions"""
        if len(self.turn_history) < window_size * 2:
            return False
            
        recent_actions = [tuple(turn["buttons"]) for turn in self.turn_history[-window_size:]]
        previous_actions = [tuple(turn["buttons"]) for turn in self.turn_history[-(window_size*2):-window_size]]
        
        # Check if the same sequence of actions is being repeated
        is_loop = recent_actions == previous_actions
        
        # Also check if screen hasn't changed
        if self.consecutive_similar_screens >= 3:
            is_loop = True
            
        return is_loop
    
    def suggest_alternative_action(self):
        """Suggest an alternative action when stuck in a loop"""
        # First, try to find a path to stairs if we know where they are
        path_to_stairs = self.suggest_path_to_destination("stairs")
        if path_to_stairs and len(path_to_stairs) > 0:
            print(f"Suggesting path to stairs: {path_to_stairs}")
            return path_to_stairs[0]  # Return the first step of the path
        
        # If we can't find a path to stairs, try a different approach
        # Check which directions haven't been tried recently
        tried_directions = set()
        for turn in self.turn_history[-5:]:
            for button in turn["buttons"]:
                if button in ["up", "down", "left", "right"]:
                    tried_directions.add(button)
                    
        all_directions = {"up", "down", "left", "right"}
        untried_directions = all_directions - tried_directions
        
        # First look for directions that aren't blocked
        unblocked_directions = set()
        if self.player_position and self.current_map is not None:
            x, y = self.player_position
            grid_height, grid_width = self.current_map.shape
            
            # Check each direction for barriers
            direction_deltas = {
                "up": (0, -1),
                "down": (0, 1),
                "left": (-1, 0),
                "right": (1, 0)
            }
            
            for direction, (dx, dy) in direction_deltas.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < grid_width and 0 <= ny < grid_height:
                    if self.current_map[ny, nx] != 4:  # Not a barrier
                        unblocked_directions.add(direction)
        
        # Prefer untried and unblocked directions
        viable_directions = untried_directions.intersection(unblocked_directions)
        
        if viable_directions:
            return list(viable_directions)[0]
        elif unblocked_directions:
            return list(unblocked_directions)[0]
        elif untried_directions:
            return list(untried_directions)[0]
        elif random.random() > 0.7:
            return "b"  # Sometimes try canceling
        else:
            # Try a completely different approach
            return random.choice(["down", "left", "a", "start"])
    
    def check_screen_change(self, screenshot_path):
        """
        Check if the screen has changed significantly from the last frame
        Used to detect when the player is stuck against an obstacle
        """
        try:
            # Get a simple hash of the image
            img = Image.open(screenshot_path).resize((32, 32))
            img_array = np.array(img)
            img_hash = hash(img_array.tobytes())
            
            # Compare with previous hash
            if self.last_screen_hash is None:
                self.last_screen_hash = img_hash
                return True  # First screen, assume it's new
            
            # Check if the screen is similar
            is_similar = (img_hash == self.last_screen_hash)
            
            # Update counter of similar screens
            if is_similar:
                self.consecutive_similar_screens += 1
            else:
                self.consecutive_similar_screens = 0
                self.last_screen_hash = img_hash
            
            return not is_similar
            
        except Exception as e:
            print(f"Error checking screen change: {str(e)}")
            return True  # Assume screen changed if we can't check
    
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
                    
                    # Check if floor information is mentioned
                    floor_indicators = ["1f", "2f", "b1", "floor 1", "floor 2", "basement"]
                    for indicator in floor_indicators:
                        if indicator in line:
                            self.current_floor = indicator.upper()
            
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
            
            # Object and furniture detection to help with navigation
            furniture_keywords = ["desk", "table", "bed", "chair", "counter", "bookshelf", "shelf", "cabinet"]
            if any(keyword in line for keyword in furniture_keywords):
                # Extract the furniture information as an observation
                if len(line) > 10 and line not in self.observations:
                    self.observations.append(line)
            
            # Save significant observations
            if "!" in line or "important" in line or "note" in line:
                if len(line) > 10 and line not in self.observations:
                    self.observations.append(line)
        
        # Limit the size of each list to keep memory manageable
        self.locations_visited = self.locations_visited[-5:]
        self.npcs_met = self.npcs_met[-5:]
        self.items_found = self.items_found[-5:]
        self.observations = self.observations[-5:]  # Keep more observations
    
    def add_turn_summary(self, buttons_pressed, observation, barrier_detected=False, screenshot_path=None):
        """Enhanced turn summary with barrier detection and map analysis"""
        # Update map from screenshot if provided
        if screenshot_path:
            # Check if screen has significantly changed
            screen_changed = self.check_screen_change(screenshot_path)
            print("****<>>M><><><><><>>")
            # Analyze the screenshot for map information
            map_info = self.detect_player_and_elements(screenshot_path)
            print(map_info)
            if map_info:
                # If we've analyzed the map, update the room state
                if self.current_location not in self.room_maps:
                    self.room_maps[self.current_location] = {}
                
                # Update room map
                self.room_maps[self.current_location]['map_grid'] = map_info['map_grid']
                self.room_maps[self.current_location]['player_position'] = map_info['player_position']
                
                # Update current state
                self.current_map = map_info['map_grid']
                self.player_position = map_info['player_position']
        
        # Create the turn summary
        summary = {
            "turn": len(self.turn_history) + 1,
            "buttons": buttons_pressed,
            "observation": observation[:150] + "..." if len(observation) > 150 else observation,
            "barrier_detected": barrier_detected,
            "player_position": self.player_position
        }
        
        # Keep track of the results of this action
        if barrier_detected:
            summary["result"] = "BARRIER"
        else:
            summary["result"] = "SUCCESS"
        
        self.turn_history.append(summary)
        
        # Keep the last 10 turns for better context
        self.turn_history = self.turn_history[-10:]
        
        # Update barriers if detected
        if barrier_detected and buttons_pressed:
            # The last button pressed likely hit the barrier
            direction = None
            for button in reversed(buttons_pressed):
                if button in ["up", "down", "left", "right"]:
                    direction = button
                    break
                    
            if direction:
                self.record_failed_move(direction)
    
    def get_map_as_base64(self):
        """Convert the current map visualization to a base64 string for embedding in prompts"""
        if self.current_map is None or self.player_position is None:
            return None
            
        # Create a visualization of the current map
        map_vis = self.visualize_map(self.current_map, self.player_position)
        
        # Convert to base64
        try:
            # Convert to PIL Image
            map_pil = Image.fromarray(map_vis)
            
            # Save to bytes buffer
            buffer = io.BytesIO()
            map_pil.save(buffer, format="PNG")
            
            # Convert to base64
            map_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return map_base64
        except Exception as e:
            print(f"Error converting map to base64: {str(e)}")
            return None
    
    def generate_summary(self):
        """Enhanced summary with visual map and spatial awareness"""
        summary = "## Game Memory\n"
        
        summary += "**Current Location:** " + self.current_location + "\n"
        summary += "**Current Floor:** " + self.current_floor + "\n"
        summary += "**Current Objective:** " + self.current_objective + "\n\n"
        
        # Add navigation information based on the map
        if self.player_position is not None:
            summary += f"**Player Position:** {self.player_position}\n"
            
            # Check if stairs are visible
            stairs_visible = False
            if self.current_map is not None:
                stairs_positions = np.where(self.current_map == 3)
                if len(stairs_positions[0]) > 0:
                    stairs_visible = True
                    y = stairs_positions[0][0]
                    x = stairs_positions[1][0]
                    summary += f"**Stairs Position:** ({x}, {y})\n"
                    
                    # Suggest a path to the stairs
                    path = self.suggest_path_to_destination("stairs")
                    if path:
                        summary += f"**Path to Stairs:** {', '.join(path)}\n"
        
        if self.locations_visited:
            summary += "**Locations Visited:** " + ", ".join(self.locations_visited) + "\n"
        
        if self.npcs_met:
            summary += "**NPCs Met:** " + ", ".join(self.npcs_met) + "\n"
        
        if self.items_found:
            summary += "**Items Found:** " + ", ".join(self.items_found) + "\n"
        
        # Add barrier information and navigation advice
        if self.failed_moves:
            summary += "\n**Navigation Information:**\n"
            
            # Group failed moves by position for clearer presentation
            failed_moves_by_pos = {}
            for pos, direction in self.failed_moves[-5:]:  # Show only the 5 most recent
                if pos not in failed_moves_by_pos:
                    failed_moves_by_pos[pos] = []
                failed_moves_by_pos[pos].append(direction)
            
            # List barriers at each position
            for pos, directions in failed_moves_by_pos.items():
                summary += f"- Position {pos}: Cannot move {', '.join(directions)}\n"
            
        # Loop detection - CRITICAL enhancement
        if self.is_stuck_in_loop():
            summary += "\n**IMPORTANT NAVIGATION ALERT:**\n"
            summary += "- You appear to be stuck in a movement loop!\n"
            
            if self.consecutive_similar_screens >= 3:
                summary += "- The screen hasn't changed in several turns\n"
                summary += "- You're likely hitting a barrier repeatedly\n"
                
            # Suggested alternative based on the map
            alternative = self.suggest_alternative_action()
            if isinstance(alternative, list):
                summary += f"- Try this path: {', '.join(alternative)}\n"
            else:
                summary += f"- Try a completely different approach: '{alternative}'\n"
                
            summary += "- To reach the stairs, find a path AROUND furniture\n"
            summary += "- Remember: You cannot walk through barriers - look for clear paths\n"
        
        if self.observations:
            summary += "\n**Key Observations:**\n- " + "\n- ".join(self.observations) + "\n"
        
        # Enhanced turn history with barrier information
        if self.turn_history:
            summary += "\n**Recent Actions:**\n"
            for turn in self.turn_history[-5:]:  # Show 5 most recent
                barrier_info = " [BARRIER DETECTED]" if turn.get("barrier_detected") else ""
                position_info = f" @ {turn.get('player_position')}" if turn.get('player_position') else ""
                summary += f"- Turn {turn['turn']}: Pressed {', '.join(turn['buttons'])}{barrier_info}{position_info} → {turn['observation']}\n"
        
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