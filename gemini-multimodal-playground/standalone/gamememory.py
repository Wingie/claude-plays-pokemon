import numpy as np
from PIL import Image
import cv2
import base64
import io
import os
import time
import traceback
from neo4j import GraphDatabase

def read_image_to_base64(image_path):
    """
    Reads an image file and converts it to a base64 encoded string.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded string representation of the image
    """
    try:
        # print(">>>>",image_path)
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error reading image file: {str(e)}") 

class Neo4jMemory:
    """Class for storing and retrieving game memory in Neo4j"""

        
    def close(self):
        """Close the Neo4j connection"""
        self.driver.close()

    def get_map_as_base64(self,image_path):
        """Convert the current map visualization to a base64 string for embedding in prompts"""
        # if self.current_map is None or self.player_position is None:
        #     return None
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def generate_summary(self):
        """Generate a text summary of the current memory state."""
        summary = "## Game Memory from Neo4j\n\n"
        
        with self.driver.session() as session:
            # Get most recent turns
            result = session.run("""
                MATCH (t:Turn)
                RETURN t.turn_id, t.gemini_text, t.timestamp
                ORDER BY t.timestamp DESC
                LIMIT 5
            """)
            
            turns = []
            for record in result:
                turns.append({
                    "turn_id": record["t.turn_id"],
                    "text": record["t.gemini_text"]
                })
            
            if turns:
                summary += "**Recent Actions:**\n"
                for turn in reversed(turns):  # Show in chronological order
                    summary += f"- {turn['turn_id']}: {turn['text'][:100]}...\n"
            else:
                summary += "No turns recorded yet.\n"
        print("generate_summary >>>>> ", summary)

        return summary
    
    def init_db(self):
        """Initialize the database schema"""
        with self.driver.session() as session:
            # Create constraints and indexes
            # session.run("""
            #     CREATE CONSTRAINT IF NOT EXISTS FOR (t:Turn) REQUIRE t.turn_id IS UNIQUE
            # """)
            
            # Create vector index for image embeddings if not exists
            try:
                session.run("""
                    CREATE VECTOR INDEX image_embedding IF NOT EXISTS
                    FOR (t:Turn) ON t.image_embedding
                """)
            except Exception as e:
                print(f"Warning: Could not create vector index: {str(e)}")
                print("Vector search functionality may not be available.")

    def add_turn_neo4j(self, buttons_pressed, observation, screenshot_file=None, turn_number=-1):
        """Store a game turn in Neo4j
        
        Args:
            base64_image: Base64-encoded image of the game state
                def add_turn_summary(self, buttons_pressed, observation, base64_image=None, turn_number=-1):
: The text response from Gemini
            turn_number: The turn number
            
        Returns:
            str: The ID of the created turn node
        """
        # Generate embedding for the image
        base64_image = read_image_to_base64(screenshot_file)
        image_embedding = self._generate_image_embedding(base64_image)
        
        # Store in Neo4j
        with self.driver.session() as session:
            result = session.run("""
                CREATE (t:Turn {
                    turn_id: $turn_id,
                    timestamp: datetime(),
                    gemini_text: $gemini_text,
                    image_base64: $image_base64,
                    image_embedding: $image_embedding
                })
                RETURN t.turn_id as turn_id
            """, {
                "turn_id": f"turn_{turn_number}",
                "gemini_text": observation,
                "image_base64": base64_image,
                "image_embedding": image_embedding
            })
            res = result.single()["turn_id"]
            print("###### STORED {turn_number}",res)
            return res
    
    def query_memory(self, questions):
        """Query the memory to answer specific questions
        
        Args:
            questions: List of questions to answer
            
        Returns:
            list: List of answers
        """
        answers = []
        
        with self.driver.session() as session:
            for question in questions:
                if "last turn" in question.lower() or "previous action" in question.lower():
                    # Get the most recent turn
                    result = session.run("""
                        MATCH (t:Turn)
                        RETURN t.turn_id, t.gemini_text
                        ORDER BY t.timestamp DESC
                        LIMIT 1
                    """)
                    
                    record = result.single()
                    if record:
                        answers.append({
                            "question": question,
                            "answer": f"Last turn ({record['t.turn_id']}): {record['t.gemini_text']}"
                        })
                    else:
                        answers.append({
                            "question": question,
                            "answer": "No turns recorded yet."
                        })
                
                elif "similar" in question.lower() or "previous state" in question.lower():
                    # Get the current turn's image embedding
                    result = session.run("""
                        MATCH (t:Turn)
                        RETURN t.image_embedding
                        ORDER BY t.timestamp DESC
                        LIMIT 1
                    """)
                    
                    record = result.single()
                    if record and record["t.image_embedding"]:
                        current_embedding = record["t.image_embedding"]
                        
                        # Find similar previous states using vector search
                        try:
                            similar_results = session.run("""
                                MATCH (t:Turn)
                                WHERE t.timestamp < datetime() - duration('PT10S')
                                RETURN t.turn_id, t.gemini_text, t.timestamp,
                                       distance(t.image_embedding, $current_embedding) as distance
                                ORDER BY distance ASC
                                LIMIT 3
                            """, {"current_embedding": current_embedding})
                            
                            similar_states = []
                            for record in similar_results:
                                if record["distance"] < 0.2:  # Threshold for similarity
                                    similar_states.append({
                                        "turn_id": record["t.turn_id"],
                                        "gemini_text": record["t.gemini_text"],
                                        "distance": record["distance"]
                                    })
                            
                            if similar_states:
                                answer = "Similar previous states found:\n"
                                for state in similar_states:
                                    answer += f"- {state['turn_id']} (similarity: {1-state['distance']:.2f}): {state['gemini_text'][:50]}...\n"
                                
                                answers.append({
                                    "question": question,
                                    "answer": answer
                                })
                            else:
                                answers.append({
                                    "question": question,
                                    "answer": "No similar previous states found."
                                })
                        except Exception as e:
                            answers.append({
                                "question": question,
                                "answer": f"Error performing vector search: {str(e)}"
                            })
                    else:
                        answers.append({
                            "question": question,
                            "answer": "No turns with embeddings available."
                        })
                
                elif "all turns" in question.lower() or "history" in question.lower():
                    # Get all turns
                    result = session.run("""
                        MATCH (t:Turn)
                        RETURN t.turn_id, t.gemini_text
                        ORDER BY t.timestamp ASC
                    """)
                    
                    turns = []
                    for record in result:
                        turns.append(f"{record['t.turn_id']}: {record['t.gemini_text'][:50]}...")
                    
                    if turns:
                        answers.append({
                            "question": question,
                            "answer": "\n".join(turns)
                        })
                    else:
                        answers.append({
                            "question": question,
                            "answer": "No turns recorded yet."
                        })
                
                else:
                    answers.append({
                        "question": question,
                        "answer": "Question not recognized. Try asking about 'last turn', 'similar states', or 'history'."
                    })
        
        return answers
    
    def _generate_image_embedding(self, base64_image):
        """Generate a simple embedding for an image
        
        Args:
            base64_image: Base64-encoded image
            
        Returns:
            list: Image embedding as a vector
        """
        try:
            # Convert base64 to image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            # Resize to a small size for faster processing
            image = image.resize((32, 32)).convert('L')
            
            # Convert to numpy array and normalize
            image_array = np.array(image).flatten() / 255.0
            
            # Reduce dimensions with simple averaging (basic embedding)
            # In a real implementation, you'd use a proper embedding model
            embedding = []
            chunks = np.array_split(image_array, 64)  # Create a 64-dimensional embedding
            for chunk in chunks:
                embedding.append(float(np.mean(chunk)))
            
            return embedding
        except Exception as e:
            print(f"Error generating image embedding: {str(e)}")
            return [0.0] * 64  # Return a zero vector as fallback
        

    def __init__(self,current_objective):
        # Existing attributes
        self.locations_visited = []
        self.npcs_met = []
        self.items_found = []
        self.current_location = "Unknown"
        self.current_objective = current_objective
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
        
        # Initialize Neo4j memory
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        self.init_db()

        # Tracking game progress
        self.last_screen_hash = None
        self.consecutive_similar_screens = 0
    
    def detect_player_and_elements(self, screenshot_path):
        """
        Analyze screenshot to detect the player character and key elements
        
        Args:
            screenshot_path: Path to the screenshot image
            
        Returns:
            dict: Contains 'map_grid', 'player_position', 'stair_position', etc.
        """
        try:
            # Load image
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
            
            return {
                'map_grid': map_grid,
                'player_position': player_position,
                'stair_position': stair_position,
                'original_image': img_rgb
            }
            
        except Exception as e:
            print(f"Error analyzing screenshot: {str(e)}")
            traceback.print_exc()  # Add this to see the full stack trace
            return None
        
    def visualize_enhanced_map(self, screenshot_path_or_data, map_grid=None, player_pos=None, stair_pos=None, path=None, original_image_path=None):
        """Create an enhanced visual map with coordinates, original image overlay, and path visualization"""
        # Constants for visualization
        cell_size = 50  # Larger cells for better visualization

        # Handle both parameter types (screenshot path or map data dictionary)
        is_dict = isinstance(screenshot_path_or_data, dict)
        screenshot_path = None
        
        if is_dict:
            # Handle case where first parameter is a map data dictionary
            map_data = screenshot_path_or_data
            if map_grid is None:
                map_grid = map_data.get('map_grid')
            if player_pos is None:
                player_pos = map_data.get('player_position')
            if stair_pos is None:
                stair_pos = map_data.get('stair_position')
            
            # Check if there's an original image in the data
            screenshot_path = original_image_path
        else:
            # Handle case where first parameter is a screenshot path
            screenshot_path = screenshot_path_or_data
            
            if screenshot_path and map_grid is None:
                # Process the screenshot to get map info
                map_info = self.detect_player_and_elements(screenshot_path)
                if not map_info:
                    print(f"Error: Could not process screenshot at {screenshot_path}")
                    return
                # Extract the map grid and other info from map_info
                map_grid = map_info.get('map_grid')
                player_pos = map_info.get('player_position')
                stair_pos = map_info.get('stair_position')
        grid_height, grid_width = map_grid.shape
        
        # Create a blank RGB image with margin for coordinate labels
        margin = 30
        vis_map = np.ones((grid_height * cell_size + margin, grid_width * cell_size + margin, 3), dtype=np.uint8) * 255
        
        # Draw coordinate grid
        for x in range(grid_width + 1):
            cv2.line(vis_map, 
                    (x * cell_size + margin, margin), 
                    (x * cell_size + margin, grid_height * cell_size + margin), 
                    (0, 0, 0), 1)
        for y in range(grid_height + 1):
            cv2.line(vis_map, 
                    (margin, y * cell_size + margin), 
                    (grid_width * cell_size + margin, y * cell_size + margin), 
                    (0, 0, 0), 1)
        
        # Draw coordinate labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        for x in range(grid_width):
            cv2.putText(vis_map, str(x), 
                    (x * cell_size + cell_size//2 + margin, 20), 
                    font, font_scale, (0, 0, 0), 1)
        for y in range(grid_height):
            cv2.putText(vis_map, str(y), 
                    (10, y * cell_size + cell_size//2 + margin), 
                    font, font_scale, (0, 0, 0), 1)
        
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
                else:
                    color = (255, 255, 255)  # White for unknown
                
                # Draw the cell with coordinate offset
                y1 = y * cell_size + margin
                y2 = (y + 1) * cell_size + margin
                x1 = x * cell_size + margin
                x2 = (x + 1) * cell_size + margin
                cv2.rectangle(vis_map, (x1, y1), (x2, y2), color, -1)
                
                # Add coordinate text in each cell
                coord_text = f"({x},{y})"
                text_size = cv2.getTextSize(coord_text, font, font_scale*0.8, 1)[0]
                text_x = x1 + (cell_size - text_size[0]) // 2
                text_y = y1 + (cell_size + text_size[1]) // 2
                cv2.putText(vis_map, coord_text, (text_x, text_y), font, font_scale*0.8, (0, 0, 0), 1)
        

        # If original image is provided, create a version with overlay
        if screenshot_path:
            try:
                # Load original image
                orig_img = cv2.imread(screenshot_path)
                
                # Extract the game area (assuming it's centered in the screenshot)
                h, w = orig_img.shape[:2]
                game_area = orig_img[int(h*0.1):int(h*0.9), int(w*0.1):int(w*0.9)]
                
                # Resize to match our grid size
                game_area_resized = cv2.resize(game_area, 
                                            (grid_width * cell_size, grid_height * cell_size))
                
                # Create a copy of the visualization with the game area embedded
                vis_map_with_orig = vis_map.copy()
                
                # Insert the game area at the grid position
                vis_map_with_orig[margin:margin+grid_height*cell_size, 
                                margin:margin+grid_width*cell_size] = cv2.addWeighted(
                    vis_map_with_orig[margin:margin+grid_height*cell_size, margin:margin+grid_width*cell_size],
                    0.5, game_area_resized, 0.4, 0)
                # save
                timestamp = int(time.time())
                map_path = os.path.join(self.map_snapshot_path, f"map_{timestamp}.png")
                cv2.imwrite(map_path, cv2.cvtColor(vis_map_with_orig, cv2.COLOR_RGB2BGR))
                return vis_map_with_orig
            except Exception as e:
                print(f"Error overlaying original image: {str(e)}")
        
        # Return just the basic visualization if no overlay
        return vis_map
    
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
    
    def add_turn_summary(self, turn, buttons_pressed, observation, barrier_detected=False, screenshot_path=None):
        """Enhanced turn summary with barrier detection and map analysis"""
        # Update map from screenshot if provided
        self.add_turn_neo4j(buttons_pressed, observation, screenshot_file=screenshot_path, turn_number=turn)
        if screenshot_path:
            try:
                # First process the screenshot to get map data
                map_data = self.detect_player_and_elements(screenshot_path)
                
                if map_data is not None:
                    print("Successfully processed screenshot")
                    
                    # Update room maps
                    if self.current_location not in self.room_maps:
                        self.room_maps[self.current_location] = {}
                    
                    # Update map data safely
                    self.room_maps[self.current_location]['map_grid'] = map_data.get('map_grid')
                    self.room_maps[self.current_location]['player_position'] = map_data.get('player_position')
                    
                    # Update current state
                    self.current_map = map_data.get('map_grid')
                    self.player_position = map_data.get('player_position')
                    
                    # Now generate and save visualization
                    vis_map = self.visualize_enhanced_map(screenshot_path, map_data.get('map_grid'), 
                                      map_data.get('player_position'), 
                                      map_data.get('stair_position'))
                    if vis_map is not None:
                        timestamp = int(time.time())
                        save_path = os.path.join(self.map_snapshot_path, f"map_{timestamp}.png")
                        cv2.imwrite(save_path, vis_map)
                else:
                    print("Failed to process screenshot")
            except Exception as e:
                print(f"Error during map processing: {str(e)}")
                traceback.print_exc()
        
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

    
    def generate_summary(self):
        """Enhanced summary with visual map and spatial awareness"""
        summary = "## Game Memory\n"
        
        summary += "**Current Location:** " + self.current_location + "\n"
        summary += "**Current Floor:** " + self.current_floor + "\n"
        summary += "**Current Objective:** " + self.current_objective + "\n\n"
        
        # Add navigation information based on the map
        if self.player_position is not None:
            summary += f"**Player Position:** {self.player_position}\n"

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
                

        
        if self.observations:
            summary += "\n**Key Observations:**\n- " + "\n- ".join(self.observations) + "\n"
        print(self.generate_map_description(),"**************************************")
        # Enhanced turn history with barrier information
        if self.turn_history:
            summary += "\n**Recent Actions:**\n"
            for turn in self.turn_history[-5:]:  # Show 5 most recent
                barrier_info = " [BARRIER DETECTED]" if turn.get("barrier_detected") else ""
                position_info = f" @ {turn.get('player_position')}" if turn.get('player_position') else ""
                summary += f"- Turn {turn['turn']}: Pressed {', '.join(turn['buttons'])}{barrier_info}{position_info} → {turn['observation']}\n"
        
        return summary
    
    def detect_barrier_from_movement(self, pre_screenshot, post_screenshot, direction):
            """
            Detect barriers by analyzing player movement between screenshots
            
            Args:
                pre_screenshot: Path to screenshot before movement
                post_screenshot: Path to screenshot after movement attempt
                direction: Direction of attempted movement
                
            Returns:
                tuple: (barrier_detected, barrier_position)
            """
            try:
                # Detect player in both screenshots
                pre_info = self.detect_player_and_elements(pre_screenshot)
                post_info = self.detect_player_and_elements(post_screenshot)
                
                if not pre_info or not post_info:
                    return False, None
                    
                pre_player_pos = pre_info.get('player_position')
                post_player_pos = post_info.get('player_position')
                
                if not pre_player_pos or not post_player_pos:
                    return False, None
                    
                # Check if player position changed significantly
                px1, py1 = pre_player_pos
                px2, py2 = post_player_pos
                
                # Calculate Euclidean distance between positions
                movement_distance = ((px2-px1)**2 + (py2-py1)**2)**0.5
                
                # If player barely moved, likely hit a barrier
                if movement_distance < 0.8:  # Threshold can be adjusted
                    # Calculate where the barrier would be based on direction
                    barrier_x, barrier_y = px1, py1
                    
                    if direction == "up":
                        barrier_y -= 1
                    elif direction == "down":
                        barrier_y += 1
                    elif direction == "left":
                        barrier_x -= 1
                    elif direction == "right":
                        barrier_x += 1
                        
                    return True, (barrier_x, barrier_y)
                    
                return False, None
                
            except Exception as e:
                print(f"Error in barrier detection: {str(e)}")
                return False, None
            
    def generate_map_description(self):
        """Generate a detailed textual description of the map for Gemini"""
        if self.current_map is None or self.player_position is None:
            return "Map not yet available."
        
        description = []
        description.append("## Map Analysis")
        
        # Describe player position
        px, py = self.player_position
        description.append(f"- You (player) are at grid position ({px}, {py})")
        
        # Describe stairs if visible
        stairs_visible = False
        stairs_pos = None
        if self.current_map is not None:
            stairs_positions = np.where(self.current_map == 3)
            if len(stairs_positions[0]) > 0:
                stairs_visible = True
                sy = stairs_positions[0][0]
                sx = stairs_positions[1][0]
                stairs_pos = (sx, sy)
                description.append(f"- Stairs are at position ({sx}, {sy})")
                
                # Calculate relative direction to stairs
                x_diff = sx - px
                y_diff = sy - py
                directions = []
                
                if abs(x_diff) > abs(y_diff):  # Primarily horizontal
                    if x_diff > 0:
                        directions.append("right/east")
                    else:
                        directions.append("left/west")
                        
                    if y_diff > 0:
                        directions.append("slightly down/south")
                    elif y_diff < 0:
                        directions.append("slightly up/north")
                else:  # Primarily vertical
                    if y_diff > 0:
                        directions.append("down/south")
                    else:
                        directions.append("up/north")
                        
                    if x_diff > 0:
                        directions.append("slightly right/east")
                    elif x_diff < 0:
                        directions.append("slightly left/west")
                        
                direction_text = " and ".join(directions)
                manhattan_dist = abs(x_diff)

# Create the initial message with comprehensive instructions
init_message = [
    {"role": "user", "content": """
# Enhanced Pokémon Game Agent Guide

You are playing Pokémon FireRed/FlameRed on a Game Boy Advance emulator. Your current objective is to **reach Viridian City**.

## TURN STRUCTURE
For every turn, follow this exact process:

1. **OBSERVE**: Carefully analyze the current screen
   - Identify screen type (Overworld, Dialog, Menu, Battle)
   - Note your character position coordinates (x, y)
   - Compare current coordinates to previous coordinates
   - Identify key elements (NPCs, objects, exits, text)
   - Look for obstacles that might block movement
   - Note any changes from previous turns

2. **ANALYZE**: Process what you see
   - Determine your current location
   - Update your mental map
   - Evaluate progress toward your goal
   - Check if you're stuck in a loop
   - Check if position coordinates changed after movement
   - If coordinates didn't change, identify the obstacle

3. **PLAN**: Decide your next moves
   - Set a specific short-term objective
   - Determine optimal path/action sequence
   - Plan paths AROUND obstacles, not through them
   - Avoid repeating failed movements
   - Prepare contingencies
   - If blocked, plan a zigzag path (move sideways, then forward)

4. **ACT**: Execute your plan
   - Select specific button presses
   - Use minimal, precise inputs (1-2 buttons per turn)
   - NEVER repeat the same button if it didn't change your position
   - Try a completely different direction if blocked

## SCREEN TYPE PROTOCOLS

### Overworld Protocol
1. Identify your current location and surroundings
2. Check cardinal directions (N/S/E/W) for paths
3. Prioritize unexplored paths toward your destination
4. Move using single directional presses
5. If blocked, try another direction
6. Interact with objects/NPCs using A when facing them

### Dialog Protocol
1. Read and understand the text content
2. Press A to advance dialog
3. For questions/options, carefully select appropriate response
4. If multiple A presses don't advance, try B to exit

### Menu Protocol
1. Identify current menu context
2. Use directional buttons to navigate options
3. Press A to select, B to cancel/back
4. In item/Pokémon menus, select based on current needs

### Battle Protocol
1. If Pokémon are low health, prioritize escaping (Down + A on RUN)
2. For required battles, use strongest attacks (typically first option)
3. After fainting, you'll be taken to the last Pokémon Center or home
4. Heal at Pokémon Centers before continuing exploration

## NAVIGATION STRATEGIES

### Town Navigation
- Towns have buildings, NPCs, and paths
- Identify exits (typically at town edges)
- For Pallet Town, the exit to Route 1 is at the NORTH edge
- For unknown towns, explore systematically clockwise from entry point

### Route Navigation
- Routes are linear or branching paths connecting towns
- Stay on clear paths to avoid unnecessary wild Pokémon encounters
- Route 1 is a mostly linear path heading NORTH to Viridian City
- Routes have obstacles (signs, ledges, trainers) that you must navigate AROUND
- If blocked by a sign when going north:
  * Try going LEFT, then UP, then RIGHT to go around it
  * Or try going RIGHT, then UP, then LEFT
  * NEVER repeatedly try to walk straight through signs or obstacles

### Building Navigation
- Doors are entered by facing them and pressing A
- Inside buildings, explore all accessible areas
- Stairs connect floors (position yourself on stairs, then press direction)
- Exit buildings through doors on first floor (often indicated by light/rug)

## OBSTACLE AVOIDANCE & ANTI-LOOPING MEASURES

### Common Obstacles
- **Signs**: Cannot walk through signs - must go AROUND them (left or right)
- **Trees**: Block movement, always navigate around them
- **Fences/Walls**: Cannot be passed through, find an opening
- **NPCs**: Cannot walk through people, navigate around them
- **Flowers/Tall Grass**: Can walk through but may trigger Pokémon battles
- **Water**: Cannot cross without special moves/Pokémon


## AVAILABLE CONTROLS
- **Up/Down/Left/Right**: Move your character
- **A**: Interact/Confirm - Use for NPCs, signs, doors, menu selections
- **B**: Cancel/Back - Exit menus or speed up text
- **Start**: Open main menu (rarely needed)
- **Select**: Rarely used

## FUNCTION CALL FORMAT
You must use function calls to control the emulator, providing a list of buttons in sequence:

```
pokemon_controller: Takes a list of buttons to press in sequence
```

Remember: Always analyze the current screen carefully before making moves. Use minimal precise inputs rather than many speculative inputs.
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
        # print(similar_pixels)
        return similar_pixels > threshold
    except Exception as e:
        print(f"Error comparing images: {e}")
        return False