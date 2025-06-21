"""
EeveeAgent - Enhanced AI Pokemon Task Execution System
Core agent class that builds upon the basic EeveeAnalyzer with advanced capabilities
"""

import os
import sys
import time
import json
import base64
import threading
import numpy as np
import cv2
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    # Try to import SkyEmu controller first, fallback to regular controller
    try:
        from skyemu_controller import SkyEmuController, read_image_to_base64
        CONTROLLER_TYPE = "skyemu"
        print("🚀 Using SkyEmu controller")
    except ImportError:
        from pokemon_controller import PokemonController, read_image_to_base64
        CONTROLLER_TYPE = "pokemon"
        print("🔄 Using standard Pokemon controller")
    
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

class EeveeAgent:
    """Enhanced Eevee AI agent for complex Pokemon task execution"""
    
    def __init__(
        self, 
        window_title: str = "mGBA - 0.10.5",
        model: str = "gemini-1.5-flash",
        memory_session: str = "default",
        verbose: bool = False,
        debug: bool = False,
        enable_neo4j: bool = False,
        enable_okr: bool = True
    ):
        """Initialize the enhanced Eevee agent"""
        self.window_title = window_title
        self.model = model
        self.memory_session = memory_session
        self.verbose = verbose
        self.debug = debug
        self.enable_neo4j = enable_neo4j
        self.enable_okr = enable_okr
        
        # Model fallback system for rate limiting - prioritize models with available quota
        self.available_models = ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
        self.rate_limited_models = set()
        # Start with the first available model (should be one with quota)
        self.current_model = self.available_models[0] if self.available_models else model
        
        # Initialize core components
        self._init_ai_components()
        self._init_directories()
        self._init_game_controller()
        
        # Task execution state
        self.current_task = None
        self.execution_history = []
        self.context_memory = {}
        
        # Circuit breaker state for API resilience
        self.api_failure_count = 0
        self.api_failure_threshold = 5
        self.circuit_breaker_reset_time = 300  # 5 minutes
        self.last_failure_time = 0
        self.circuit_breaker_open = False
        
        if self.verbose:
            print(f"🔮 EeveeAgent initialized")
            print(f"   Model: {self.current_model} (fallbacks: {', '.join(self.available_models[1:])})")
            print(f"   Memory Session: {self.memory_session}")
            print(f"   Window: {self.window_title}")
    
    def _init_ai_components(self):
        """Initialize AI components and APIs"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize native Gemini API
        genai.configure(api_key=api_key)
        self.gemini = genai.GenerativeModel(model_name=self.current_model)
        
        # Define Pokemon controller tool - using minimal schema to avoid protobuf issues
        try:
            self.pokemon_function_declaration = FunctionDeclaration(
                name="pokemon_controller",
                description="Control Pokemon game with button presses",
                parameters={
                    "type": "object",
                    "properties": {
                        "buttons": {
                            "type": "string",
                            "description": "Single button press: up, down, left, right, a, b, start, select"
                        }
                    },
                    "required": ["buttons"]
                }
            )
        except Exception as e:
            print(f"⚠️  Function declaration failed: {e}")
            # Fallback: disable tools for this session
            self.pokemon_function_declaration = None
        if self.pokemon_function_declaration:
            self.pokemon_tool = Tool(function_declarations=[self.pokemon_function_declaration])
        else:
            self.pokemon_tool = None
            print("⚠️  Pokemon tool disabled due to function declaration failure")
        
        # Initialize memory system when available
        try:
            from memory_system import MemorySystem
            self.memory = MemorySystem(self.memory_session, enable_neo4j=self.enable_neo4j)
        except ImportError:
            self.memory = None
            if self.debug:
                print("⚠️  MemorySystem not available, using basic memory")
        
        # Initialize prompt manager when available
        try:
            from prompt_manager import PromptManager
            self.prompt_manager = PromptManager()
            if self.verbose:
                print("📖 PromptManager initialized with playbook system")
        except ImportError:
            self.prompt_manager = None
            if self.debug:
                print("⚠️  PromptManager not available, using basic prompts")
        
        # Initialize task executor when available
        try:
            from task_executor import TaskExecutor
            self.task_executor = TaskExecutor(self)
        except ImportError:
            self.task_executor = None
            if self.debug:
                print("⚠️  TaskExecutor not available, using basic execution")
    
    def _switch_to_next_model(self) -> bool:
        """
        Switch to next available model when current model is rate limited
        
        Returns:
            bool: True if successfully switched to new model, False if all models rate limited
        """
        for model in self.available_models:
            if model not in self.rate_limited_models:
                if model != self.current_model:
                    old_model = self.current_model
                    self.current_model = model
                    self.gemini = genai.GenerativeModel(model_name=model)
                    
                    if self.verbose:
                        print(f"🔄 Switched from {old_model} to {model} due to rate limiting")
                    return True
        
        if self.verbose:
            print("❌ All models are rate limited - waiting for quota reset")
        return False
    
    def _call_gemini_api(self, prompt: str, image_data: str = None, use_tools: bool = False, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Unified Gemini API calling method with smart timeout and rate limiting
        
        Args:
            prompt: Text prompt to send
            image_data: Base64 encoded image data (optional)
            use_tools: Whether to include Pokemon controller tools
            max_tokens: Maximum tokens for response
            
        Returns:
            Dict with 'text', 'button_presses', and 'error' keys
        """
        # Check circuit breaker status
        if self._check_circuit_breaker():
            return {
                "text": "",
                "button_presses": [],
                "error": "API circuit breaker is open - too many recent failures"
            }
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Prepare prompt parts
                prompt_parts = [prompt]
                
                # Add image if provided
                if image_data:
                    prompt_parts.append({
                        "mime_type": "image/jpeg",
                        "data": base64.b64decode(image_data)
                    })
                
                # Call Gemini API with timeout handling
                if use_tools and self.pokemon_tool:
                    response = self.gemini.generate_content(
                        prompt_parts,
                        generation_config={"max_output_tokens": max_tokens},
                        tools=[self.pokemon_tool]
                    )
                else:
                    # Use text-only mode if tools disabled or unavailable
                    response = self.gemini.generate_content(
                        prompt_parts,
                        generation_config={"max_output_tokens": max_tokens}
                    )
                
                # Process response
                result = {
                    "text": "",
                    "button_presses": [],
                    "error": None
                }
                
                # Essential API status info only
                if self.verbose:
                    print(f"📊 API Response: {len(response.text) if response and response.text else 0} chars")
                    has_tools = bool(response and response.candidates and any(part.function_call for part in response.candidates[0].content.parts if hasattr(part, 'function_call')))
                    print(f"🔧 Tools used: {'Yes' if has_tools else 'No'}")
                
                if use_tools and response.candidates and response.candidates[0].content.parts:
                    # Handle tool-enabled response
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            result["text"] = part.text
                        elif part.function_call and part.function_call.name == "pokemon_controller":
                            # Extract single button press from new format
                            args = dict(part.function_call.args)
                            if "buttons" in args:
                                button = args["buttons"].lower().strip()
                                result["button_presses"].append(button)
                    
                    # If we have text but no function calls, parse buttons from text
                    if result["text"] and not result["button_presses"]:
                        button_patterns = [
                            r"press (\w+)", r"button (\w+)", r"use (\w+)",
                            r"go (\w+)", r"move (\w+)", r"navigate (\w+)"
                        ]
                        for pattern in button_patterns:
                            matches = re.findall(pattern, result["text"].lower())
                            for match in matches:
                                if match in ["up", "down", "left", "right", "a", "b", "start", "select"]:
                                    result["button_presses"].append(match)
                                    break
                            if result["button_presses"]:
                                break
                        
                        
                        # Default fallback if no buttons parsed
                        if not result["button_presses"]:
                            result["button_presses"] = ["a"]  # Safe default action
                else:
                    # Handle text-only response - parse buttons from text as fallback
                    result["text"] = response.text if response.text else ""
                    
                    # Extract button commands from text response as fallback when tools fail
                    if result["text"] and not result["button_presses"]:
                        button_patterns = [
                            r"press (\w+)", r"button (\w+)", r"use (\w+)",
                            r"go (\w+)", r"move (\w+)", r"navigate (\w+)"
                        ]
                        for pattern in button_patterns:
                            matches = re.findall(pattern, result["text"].lower())
                            for match in matches:
                                if match in ["up", "down", "left", "right", "a", "b", "start", "select"]:
                                    result["button_presses"].append(match)
                                    break
                            if result["button_presses"]:
                                break
                        
                        # Default fallback if no buttons parsed
                        if not result["button_presses"]:
                            result["button_presses"] = ["a"]  # Safe default action
                
                # Record successful API call
                self._record_api_success()
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Essential error info
                if self.verbose:
                    print(f"🚨 API Exception: {e}")
                    print(f"🔍 Exception type: {type(e).__name__}")
                    print(f"🔍 Full error message: {str(e)}")
                
                # Handle specific error types
                if "whichOneof" in error_msg:
                    if self.verbose:
                        print(f"🚨 Function call parsing error - tools issue detected")
                    # Return empty result for tools parsing errors
                    return {
                        "text": "",
                        "button_presses": [],
                        "error": f"Function call parsing error: {e}"
                    }
                
                # Handle image validation errors
                if "provided image is not valid" in error_msg or "image" in error_msg:
                    if self.verbose:
                        print(f"🚨 Image validation error: {e}")
                        print(f"📷 Image data: {'Provided' if image_data else 'None'}")
                    # Try without image for this attempt
                    if attempt < max_retries - 1:
                        print(f"⚠️ Retrying without image data...")
                        return self._call_gemini_api(prompt, image_data=None, use_tools=use_tools, max_tokens=max_tokens)
                
                # Handle 429 rate limit errors with model switching
                if "429" in error_msg or "rate limit" in error_msg or "quota" in error_msg:
                    # Enhanced rate limit detection
                    if self.verbose:
                        print(f"🔄 Rate limit detected for {self.current_model}")
                    
                    # Mark current model as rate limited and try to switch
                    self.rate_limited_models.add(self.current_model)
                    
                    if self._switch_to_next_model():
                        # Successfully switched models, retry immediately with new model
                        if self.verbose:
                            print(f"✅ Switched to {self.current_model} - retrying request")
                        continue
                    else:
                        # All models rate limited, fall back to waiting
                        retry_delay = self._parse_retry_delay(str(e), base_delay * (2 ** attempt))
                        if self.verbose:
                            print(f"⚠️ All models rate limited (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay:.1f}s...")
                        time.sleep(retry_delay)
                        continue
                
                # Handle timeout and connection errors  
                elif any(keyword in error_msg for keyword in ["timeout", "connection", "network", "temporarily unavailable"]):
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        if self.verbose:
                            print(f"⚠️ Connection error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay:.1f}s...")
                        time.sleep(retry_delay)
                        continue
                
                # For other errors or final attempt, return error result
                if self.verbose and attempt == max_retries - 1:
                    print(f"❌ API call failed after {max_retries} attempts: {e}")
                
                # Record API failure for circuit breaker
                self._record_api_failure()
                
                return {
                    "text": "",
                    "button_presses": [],
                    "error": str(e)
                }
        
        # This should never be reached, but included for completeness
        self._record_api_failure()
        return {
            "text": "",
            "button_presses": [],
            "error": "Max retries exceeded"
        }
    
    def _parse_retry_delay(self, error_message: str, default_delay: float) -> float:
        """
        Parse retry delay from 429 error response headers
        
        Args:
            error_message: The error message string
            default_delay: Default delay if no specific delay found
            
        Returns:
            Delay in seconds to wait before retry
        """
        import re
        
        # Look for retry-after patterns in error message
        # Common patterns: "retry after 60 seconds", "try again in 30s", etc.
        patterns = [
            r'retry[\s\-_]*after[\s\-_]*(\d+)[\s\-_]*seconds?',
            r'try[\s\-_]*again[\s\-_]*in[\s\-_]*(\d+)[\s\-_]*s',
            r'wait[\s\-_]*(\d+)[\s\-_]*seconds?',
            r'(\d+)[\s\-_]*seconds?[\s\-_]*retry'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message.lower())
            if match:
                try:
                    parsed_delay = float(match.group(1))
                    # Cap delay at reasonable maximum (5 minutes)
                    return min(parsed_delay, 300.0)
                except (ValueError, IndexError):
                    continue
        
        # If no specific delay found, use exponential backoff with jitter
        import random
        jitter = random.uniform(0.8, 1.2)
        return min(default_delay * jitter, 60.0)  # Cap at 1 minute
    
    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker should prevent API calls
        
        Returns:
            True if circuit breaker is open (should prevent calls)
        """
        current_time = time.time()
        
        # Reset circuit breaker if enough time has passed
        if self.circuit_breaker_open and (current_time - self.last_failure_time) > self.circuit_breaker_reset_time:
            self.circuit_breaker_open = False
            self.api_failure_count = 0
            if self.verbose:
                print("🔄 Circuit breaker reset - API calls resumed")
        
        return self.circuit_breaker_open
    
    def _record_api_success(self):
        """Record successful API call and reset failure count"""
        if self.api_failure_count > 0:
            self.api_failure_count = 0
            if self.verbose:
                print("✅ API success - failure count reset")
    
    def _record_api_failure(self):
        """Record API failure and update circuit breaker state"""
        self.api_failure_count += 1
        self.last_failure_time = time.time()
        
        if self.api_failure_count >= self.api_failure_threshold and not self.circuit_breaker_open:
            self.circuit_breaker_open = True
            if self.verbose:
                print(f"🔴 Circuit breaker opened after {self.api_failure_count} failures")
                print(f"   API calls suspended for {self.circuit_breaker_reset_time//60} minutes")
    
    def _detect_overworld_context(self, image_data: str) -> Dict[str, Any]:
        """
        Use Gemini API to detect overworld context and navigation opportunities
        
        Args:
            image_data: Base64 encoded screenshot
            
        Returns:
            Dict with overworld analysis including obstacles, exits, and navigation advice
        """
        # First, create an ASCII grid overlay to help Gemini understand the layout
        try:
            ascii_overlay = self._create_ascii_grid_overlay(image_data)
        except Exception as e:
            if self.verbose:
                print(f"⚠️ ASCII overlay creation failed: {e}")
            ascii_overlay = "ASCII overlay not available"

        overworld_prompt = f"""# Pokemon Overworld Navigation Expert

You are analyzing a Pokemon overworld screenshot with an ASCII grid overlay to help with navigation.

**ASCII GRID OVERLAY (8x8 map of current screen):**
```
{ascii_overlay}
```

**GRID LEGEND:**
- P = Player position (where you are now)
- . = Grass/walkable area 
- - = Path/road (walkable)
- T = Tree (BLOCKED - cannot walk through)
- B = Building (BLOCKED)
- # = Wall (BLOCKED)
- ~ = Water (BLOCKED)

**NAVIGATION TASK:**
Based on the ASCII grid above, determine the safest movement direction to avoid obstacles.

**RESPONSE FORMAT:**
```json
{{
    "is_overworld": true/false,
    "player_position": "center/top/bottom/left/right",
    "ascii_analysis": "Brief description of what you see in the grid",
    "blocked_directions": ["up", "down", "left", "right"],
    "clear_directions": ["up", "down", "left", "right"],
    "recommended_movement": "up/down/left/right",
    "obstacle_warning": "What specific obstacles to avoid",
    "navigation_notes": "Smart movement advice based on the grid"
}}
```

**CRITICAL:** Look at the ASCII grid to see where trees (T) and obstacles are positioned relative to the player (P). Recommend movement towards open areas (.) or paths (-), NOT towards trees (T) or walls (#).

Analyze the grid and provide safe navigation guidance."""

        try:
            # Use Gemini API for overworld detection
            result = self._call_gemini_api(
                prompt=overworld_prompt,
                image_data=image_data,
                use_tools=False,
                max_tokens=500
            )
            
            if result.get("error"):
                return {"error": result["error"], "is_overworld": False}
            
            # Try to parse JSON response
            text_response = result.get("text", "")
            
            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text_response, re.DOTALL)
            if json_match:
                try:
                    overworld_data = json.loads(json_match.group(1))
                    overworld_data["raw_analysis"] = text_response
                    return overworld_data
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Parse key information from text
            return self._parse_overworld_text_response(text_response)
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Overworld detection failed: {e}")
            return {"error": str(e), "is_overworld": False}
    
    def _parse_overworld_text_response(self, text: str) -> Dict[str, Any]:
        """
        Parse overworld analysis from text response when JSON parsing fails
        
        Args:
            text: AI response text
            
        Returns:
            Parsed overworld analysis
        """
        analysis = {
            "is_overworld": True,
            "player_position": "unknown",
            "obstacles_nearby": [],
            "clear_directions": [],
            "blocked_directions": [],
            "recommended_movement": "stay",
            "exit_points": [],
            "navigation_notes": text,
            "raw_analysis": text
        }
        
        text_lower = text.lower()
        
        # Detect if this looks like overworld
        overworld_keywords = ["grass", "tree", "overworld", "route", "path", "road"]
        if any(keyword in text_lower for keyword in overworld_keywords):
            analysis["is_overworld"] = True
        
        # Extract direction information
        directions = ["up", "down", "left", "right", "north", "south", "east", "west"]
        for direction in directions:
            if f"blocked {direction}" in text_lower or f"{direction} blocked" in text_lower:
                analysis["blocked_directions"].append(direction)
            elif f"clear {direction}" in text_lower or f"{direction} clear" in text_lower:
                analysis["clear_directions"].append(direction)
        
        # Extract obstacles
        obstacles = ["tree", "building", "wall", "rock", "water"]
        for obstacle in obstacles:
            if obstacle in text_lower:
                analysis["obstacles_nearby"].append(obstacle)
        
        # Extract recommended movement
        movement_patterns = [
            r"move\s+(up|down|left|right|north|south|east|west)",
            r"go\s+(up|down|left|right|north|south|east|west)",
            r"recommended?\s+(up|down|left|right|north|south|east|west)"
        ]
        
        for pattern in movement_patterns:
            match = re.search(pattern, text_lower)
            if match:
                analysis["recommended_movement"] = match.group(1)
                break
        
        return analysis
    
    def _create_ascii_grid_overlay(self, image_data: str) -> str:
        """
        Create an 8x8 ASCII grid overlay from the screenshot to help with navigation
        
        Args:
            image_data: Base64 encoded screenshot
            
        Returns:
            ASCII grid string with walkability and obstacle information
        """
        try:
            from PIL import Image
            from io import BytesIO
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(image_bytes))
            img = img.convert('RGB')
            
            # Define grid size (8x8 for Pokemon's tile-based system)
            GRID_SIZE = 8
            
            # Calculate tile dimensions
            width, height = img.size
            tile_width = width // GRID_SIZE
            tile_height = height // GRID_SIZE
            
            # Initialize ASCII map
            ascii_map = []
            
            # Process each tile in the grid
            for y in range(GRID_SIZE):
                row = ""
                
                for x in range(GRID_SIZE):
                    # Get tile region
                    start_x = x * tile_width
                    start_y = y * tile_height
                    end_x = start_x + tile_width
                    end_y = start_y + tile_height
                    
                    tile = img.crop((start_x, start_y, end_x, end_y))
                    tile_array = np.array(tile)
                    
                    # Classify the tile using HSV analysis
                    char = self._classify_tile_for_navigation(tile_array, (y, x))
                    
                    # Mark player position at center
                    if x == GRID_SIZE // 2 and y == GRID_SIZE // 2:
                        char = "P"
                    
                    # Check if this area has been visited before
                    elif self._is_area_visited(x, y):
                        if char == ".":  # Only mark walkable areas as visited
                            char = "*"  # Visited walkable area
                    
                    row += char
                
                ascii_map.append(row)
            
            # Format the output with coordinates
            output = "  " + "".join([f"{i}" for i in range(GRID_SIZE)]) + "\n"
            
            for y, row in enumerate(ascii_map):
                output += f"{y} {row}\n"
            
            return output
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ ASCII grid overlay creation failed: {e}")
            return "ASCII grid creation failed"
    
    def _classify_tile_for_navigation(self, tile_array: np.ndarray, position: tuple) -> str:
        """
        Classify a tile for navigation purposes using HSV color analysis
        
        Args:
            tile_array: Numpy array of the tile image
            position: Tuple of (y, x) coordinates for the tile
            
        Returns:
            Single character representing the tile type
        """
        if tile_array.size == 0:
            return "."  # Default for empty tile
        
        y, x = position
        
        # Convert RGB to BGR (OpenCV format) then to HSV
        tile_bgr = cv2.cvtColor(tile_array, cv2.COLOR_RGB2BGR)
        tile_hsv = cv2.cvtColor(tile_bgr, cv2.COLOR_BGR2HSV)
        
        # Calculate average HSV color
        avg_hsv = np.mean(tile_hsv, axis=(0, 1))
        h, s, v = avg_hsv.astype(int)
        
        # Trees (dark green) - BLOCKED
        if 44 <= h <= 48 and s > 175 and 125 <= v <= 160:
            return "T"
            
        # Paths (light yellow/tan) - WALKABLE
        elif 30 <= h <= 32 and 125 <= s <= 145 and v > 200:
            return "-"
            
        # Water (blue) - BLOCKED
        elif 90 < h < 130 and s > 50:
            return "~"
            
        # Walls/buildings (dark gray/black) - BLOCKED
        elif s < 40 and v < 100:
            return "#"
            
        # Buildings/structures (usually gray/red) - BLOCKED
        elif (0 <= h < 20 or 160 < h <= 179) and s > 50 and v > 80:
            return "B"
        
        # Grass (various greens) - WALKABLE (with some exceptions)
        elif 40 <= h <= 52 and v > 150:
            # Most grass is walkable, but some edge cases
            if 3 <= y <= 4:  # Middle rows are almost always walkable
                return "."
            elif s < 160:  # Lower saturation generally means walkable
                return "."
            else:
                # Handle special cases for dense foliage
                return "."  # Default to walkable for most grass
        
        # Default - assume walkable grass
        else:
            return "."
    
    def _is_area_visited(self, x: int, y: int) -> bool:
        """
        Check if a grid area has been visited before using memory system
        
        Args:
            x, y: Grid coordinates to check
            
        Returns:
            True if area has been visited before
        """
        if not self.memory:
            return False
            
        try:
            # Create a location key for this grid position
            location_key = f"grid_{x}_{y}"
            
            # Query memory for this location
            memory_result = self.memory.get_relevant_context(f"visited {location_key}")
            
            # Check if we have any memory of visiting this location
            return len(memory_result.get("relevant_memories", [])) > 0
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error checking visited area: {e}")
            return False
    
    def _record_area_visit(self, x: int, y: int, context: str = ""):
        """
        Record that we've visited a specific grid area
        
        Args:
            x, y: Grid coordinates
            context: Additional context about the visit
        """
        if not self.memory:
            return
            
        try:
            location_key = f"grid_{x}_{y}"
            visit_memory = f"Visited location {location_key} - {context}"
            
            # Store the visit in memory
            self.memory.store_observation(
                observation=visit_memory,
                importance=0.3,  # Low importance for basic movement
                context={"type": "navigation", "grid_x": x, "grid_y": y}
            )
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error recording area visit: {e}")
    
    def _record_overworld_movement(self, button_presses: List[str], game_context: Dict[str, Any], ai_analysis: str, turn: int):
        """
        Record area visits when AI moves in the overworld
        
        Args:
            button_presses: List of button presses executed by AI
            game_context: Current game context including overworld analysis
            ai_analysis: AI's analysis of the current situation
            turn: Current turn number
        """
        if not button_presses or not self.memory:
            return
        
        try:
            # Check if this is overworld movement
            overworld_analysis = game_context.get("overworld_analysis", {})
            is_overworld = overworld_analysis.get("is_overworld", False)
            
            # Define movement buttons
            movement_buttons = ["up", "down", "left", "right"]
            
            # Check if any movement buttons were pressed
            movement_detected = any(button in movement_buttons for button in button_presses)
            
            if not movement_detected or not is_overworld:
                return
            
            # Extract movement direction(s)
            movements_made = [button for button in button_presses if button in movement_buttons]
            
            if self.verbose:
                print(f"🗺️  Overworld movement detected: {movements_made}")
            
            # Record area visit for the player's current position
            # Use center of 8x8 grid as baseline (player position)
            center_x, center_y = 4, 4  # Center of 8x8 grid
            
            # Calculate approximate new position based on movement
            for movement in movements_made:
                new_x, new_y = center_x, center_y
                
                if movement == "up":
                    new_y = max(0, center_y - 1)
                elif movement == "down":
                    new_y = min(7, center_y + 1)
                elif movement == "left":
                    new_x = max(0, center_x - 1)
                elif movement == "right":
                    new_x = min(7, center_x + 1)
                
                # Create context string with relevant information
                movement_context = f"Turn {turn}: moved {movement}"
                
                # Add AI analysis context if it mentions overworld features
                analysis_lower = ai_analysis.lower() if ai_analysis else ""
                if any(keyword in analysis_lower for keyword in ["grass", "tree", "path", "route", "overworld"]):
                    movement_context += f" - {ai_analysis[:50]}..."
                
                # Add overworld analysis context
                if overworld_analysis.get("navigation_notes"):
                    movement_context += f" - {overworld_analysis['navigation_notes'][:30]}..."
                
                # Record the area visit
                self._record_area_visit(new_x, new_y, movement_context)
                
                # Also record the general overworld exploration
                if self.memory:
                    exploration_note = f"Explored overworld in direction {movement} during turn {turn}"
                    self.memory.store_observation(
                        observation=exploration_note,
                        importance=0.4,  # Medium importance for exploration
                        context={
                            "type": "exploration", 
                            "direction": movement,
                            "turn": turn,
                            "is_overworld": True
                        }
                    )
                
                if self.verbose:
                    print(f"📍 Recorded visit to grid position ({new_x}, {new_y})")
        
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error recording overworld movement: {e}")
    
    def _init_directories(self):
        """Initialize directory structure"""
        self.eevee_dir = Path(__file__).parent
        self.analysis_dir = self.eevee_dir / "analysis"
        self.memory_dir = self.eevee_dir / "memory"
        self.reports_dir = self.eevee_dir / "reports"
        self.runs_dir = self.eevee_dir / "runs"
        
        # Create directories if they don't exist
        for directory in [self.analysis_dir, self.memory_dir, self.reports_dir, self.runs_dir]:
            directory.mkdir(exist_ok=True)
    
    def _init_game_controller(self):
        """Initialize Pokemon game controller"""
        if CONTROLLER_TYPE == "skyemu":
            # Use SkyEmu HTTP controller
            self.controller = SkyEmuController()
            
            # Test SkyEmu connection
            if not self.controller.is_connected():
                print(f"⚠️  Warning: SkyEmu server not connected")
                print("   Make sure SkyEmu is running with HTTP server enabled")
                print("   Default connection: localhost:8080")
        else:
            # Use standard Pokemon controller
            self.controller = PokemonController(window_title=self.window_title)
            
            # Test game connection
            window = self.controller.find_window()
            if not window:
                print(f"⚠️  Warning: Pokemon game window not found")
                print(f"   Looking for: {self.window_title}")
                print("   Make sure the emulator is running with a Pokemon game loaded")
    
    def execute_task(self, task_description: str, max_steps: int = 50) -> Dict[str, Any]:
        """
        Execute a complex Pokemon task described in natural language
        
        Args:
            task_description: Natural language description of the task
            max_steps: Maximum number of execution steps
            
        Returns:
            Dict containing execution results, analysis, and metadata
        """
        start_time = time.time()
        self.current_task = task_description
        
        if self.verbose:
            print(f"🎯 Starting task execution: {task_description}")
        
        try:
            # Step 1: Analyze the task and create execution plan
            execution_plan = self._analyze_task(task_description)
            
            if self.verbose:
                print(f"📋 Execution plan created with {len(execution_plan.get('steps', []))} steps")
            
            # Step 2: Execute the plan
            if self.task_executor:
                result = self.task_executor.execute_plan(execution_plan, max_steps)
            else:
                # Fallback to basic execution
                result = self._execute_basic_task(task_description)
            
            # Step 3: Post-process and format results
            result.update({
                "task": task_description,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 4: Update memory with results
            self._update_memory(task_description, result)
            
            return result
            
        except Exception as e:
            error_result = {
                "task": task_description,
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.debug:
                import traceback
                error_result["traceback"] = traceback.format_exc()
            
            return error_result
    
    def execute_task_interruptible(self, task_description: str, max_steps: int = 50, session_state: Dict = None) -> Dict[str, Any]:
        """
        Execute a task with interruption support for interactive mode
        
        Args:
            task_description: Natural language description of the task
            max_steps: Maximum number of execution steps
            session_state: Interactive session state for pause/resume control
            
        Returns:
            Dict containing execution results, analysis, and metadata
        """
        start_time = time.time()
        self.current_task = task_description
        
        if self.verbose:
            print(f"🎯 Starting interruptible task: {task_description}")
        
        try:
            # Step 1: Analyze the task and create execution plan
            execution_plan = self._analyze_task(task_description)
            
            if self.verbose:
                print(f"📋 Execution plan created with {len(execution_plan.get('steps', []))} steps")
            
            # Step 2: Execute the plan with interruption support
            if self.task_executor:
                result = self.task_executor.execute_plan_interruptible(execution_plan, max_steps, session_state)
            else:
                # Fallback to basic interruptible execution
                result = self._execute_basic_task_interruptible(task_description, session_state)
            
            # Step 3: Post-process and format results
            result.update({
                "task": task_description,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "interrupted": session_state.get("paused", False) if session_state else False
            })
            
            # Step 4: Update memory with results
            if not session_state or not session_state.get("paused", False):
                self._update_memory(task_description, result)
            
            return result
            
        except Exception as e:
            error_result = {
                "task": task_description,
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "interrupted": session_state.get("paused", False) if session_state else False
            }
            
            if self.debug:
                import traceback
                error_result["traceback"] = traceback.format_exc()
            
            return error_result
    
    def _execute_basic_task_interruptible(self, task_description: str, session_state: Dict = None) -> Dict[str, Any]:
        """
        Basic interruptible task execution with pause/resume support
        
        Args:
            task_description: Task to execute
            session_state: Session state for pause/resume control
            
        Returns:
            Execution result with interruption awareness
        """
        steps_executed = 0
        max_steps = 10  # Default for basic execution
        results = []
        
        while steps_executed < max_steps:
            # Check for pause/interruption
            if session_state and session_state.get("paused", False):
                print("⏸️  Task execution paused.")
                break
            
            step_num = steps_executed + 1
            print(f"🔮 Eevee: Executing step {step_num}/{max_steps}...")
            
            # Capture current screen for this step
            game_context = self._capture_current_context()
            
            # Check again after potentially long screenshot operation
            if session_state and session_state.get("paused", False):
                print("⏸️  Task execution paused during step.")
                break
            
            # Create step-specific prompt
            step_prompt = self._build_basic_task_prompt(f"Step {step_num}: {task_description}")
            
            try:
                # Use unified API method
                api_result = self._call_gemini_api(
                    prompt=step_prompt,
                    image_data=game_context["screenshot_data"],
                    use_tools=False,
                    max_tokens=800
                )
                
                if api_result["error"]:
                    step_analysis = f"Error: {api_result['error']}"
                else:
                    step_analysis = api_result["text"] or "No analysis generated"
                
                results.append({
                    "step": step_num,
                    "analysis": step_analysis,
                    "timestamp": datetime.now().isoformat(),
                    "screenshot_path": game_context.get("screenshot_path")
                })
                
                steps_executed += 1
                
                # Brief pause between steps to allow for interruption
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error in step {step_num}: {str(e)}"
                results.append({
                    "step": step_num,
                    "analysis": error_msg,
                    "timestamp": datetime.now().isoformat(),
                    "error": True
                })
                break
        
        # Determine final status
        was_paused = session_state and session_state.get("paused", False)
        status = "paused" if was_paused else ("completed" if steps_executed > 0 else "failed")
        
        # Combine all step analyses
        combined_analysis = "\n\n".join([
            f"Step {r['step']}: {r['analysis']}" for r in results if not r.get('error', False)
        ])
        
        return {
            "status": status,
            "analysis": combined_analysis,
            "steps_executed": steps_executed,
            "method": "basic_interruptible",
            "step_details": results,
            "interrupted": was_paused
        }
    
    def _analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze a task description and create an execution plan
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Execution plan with steps and strategies
        """
        # Get current game state context
        game_context = self._capture_current_context()
        
        # Get relevant memory context
        memory_context = self._get_memory_context(task_description)
        
        # Create task analysis prompt
        analysis_prompt = self._build_task_analysis_prompt(
            task_description, 
            game_context, 
            memory_context
        )
        
        try:
            # Use unified API method
            api_result = self._call_gemini_api(
                prompt=analysis_prompt,
                image_data=game_context["screenshot_data"],
                use_tools=False,
                max_tokens=1500
            )
            
            if api_result["error"]:
                raise Exception(api_result["error"])
            
            analysis_text = api_result["text"] or ""
            
            # Parse the analysis into structured execution plan
            execution_plan = self._parse_execution_plan(analysis_text)
            execution_plan["raw_analysis"] = analysis_text
            
            return execution_plan
            
        except Exception as e:
            if self.debug:
                print(f"⚠️  Task analysis failed: {e}")
            
            # Return basic fallback plan
            return {
                "task": task_description,
                "strategy": "basic_analysis",
                "steps": [{"action": "analyze_screen", "description": "Analyze current game state"}],
                "complexity": "unknown",
                "estimated_steps": 1
            }
    
    def _execute_basic_task(self, task_description: str) -> Dict[str, Any]:
        """
        Basic task execution fallback when TaskExecutor is not available
        
        Args:
            task_description: Task to execute
            
        Returns:
            Basic execution result
        """
        # Capture current screen
        game_context = self._capture_current_context()
        
        # Create task-specific prompt
        task_prompt = self._build_basic_task_prompt(task_description)
        
        try:
            # Use unified API method
            api_result = self._call_gemini_api(
                prompt=task_prompt,
                image_data=game_context["screenshot_data"],
                use_tools=False,
                max_tokens=1000
            )
            
            if api_result["error"]:
                return {
                    "status": "failed",
                    "error": api_result["error"],
                    "steps_executed": 0,
                    "method": "basic_analysis"
                }
            
            analysis = api_result["text"] or "No analysis generated"
            
            return {
                "status": "completed",
                "analysis": analysis,
                "steps_executed": 1,
                "method": "basic_analysis"
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "steps_executed": 0,
                "method": "basic_analysis"
            }
    
    # Note: Enhanced _capture_current_context method is implemented below
    
    def _get_memory_context(self, task_description: str) -> Dict[str, Any]:
        """Get relevant memory context for the task"""
        if self.memory:
            return self.memory.get_relevant_context(task_description)
        else:
            # Basic memory fallback
            return {
                "session": self.memory_session,
                "relevant_memories": [],
                "game_state": self.context_memory.get("last_known_state", {})
            }
    
    def _update_memory(self, task_description: str, result: Dict[str, Any]):
        """Update memory with task execution results"""
        if self.memory:
            self.memory.store_task_result(task_description, result)
        else:
            # Basic memory storage
            self.context_memory[task_description] = {
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_task_analysis_prompt(self, task: str, game_context: Dict, memory_context: Dict) -> str:
        """Build prompt for task analysis and planning"""
        if self.prompt_manager:
            return self.prompt_manager.get_task_analysis_prompt(task, game_context, memory_context)
        else:
            # Basic prompt fallback
            return f"""Analyze this Pokemon game task and create an execution plan:

TASK: {task}

Current game context:
- Screenshot captured at: {game_context.get('timestamp', 'unknown')}
- Window connection: {'✅' if game_context.get('window_found') else '❌'}

Please analyze the current screen and provide:
1. **Current Game State**: What's visible on screen
2. **Task Understanding**: Break down what needs to be accomplished
3. **Execution Strategy**: Step-by-step approach to complete the task
4. **Potential Challenges**: Any obstacles or considerations
5. **Expected Outcome**: What success looks like

Be specific and actionable in your analysis."""
    
    def _build_basic_task_prompt(self, task: str) -> str:
        """Build prompt for basic task execution"""
        return f"""Execute this Pokemon game task by analyzing the current screen:

TASK: {task}

Provide a detailed analysis focused on this specific task. Look carefully at the screen and provide relevant information that addresses the task requirements.

If additional actions or navigation are needed to complete this task, describe what steps should be taken next.

Format your response with clear sections addressing the task requirements."""
    
    def _parse_execution_plan(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI analysis into structured execution plan"""
        # Basic parsing logic - can be enhanced with more sophisticated NLP
        lines = analysis_text.split('\n')
        
        plan = {
            "task": self.current_task,
            "strategy": "ai_generated",
            "steps": [],
            "complexity": "medium",
            "estimated_steps": 1
        }
        
        # Look for step-like patterns in the analysis
        current_step = 1
        for line in lines:
            line = line.strip()
            if (line.startswith(f"{current_step}.") or 
                line.startswith("Step") or
                line.startswith("-") and len(line) > 10):
                
                plan["steps"].append({
                    "step": current_step,
                    "action": "analyze_and_execute",
                    "description": line,
                    "status": "pending"
                })
                current_step += 1
        
        # If no clear steps found, create a single analysis step
        if not plan["steps"]:
            plan["steps"] = [{
                "step": 1,
                "action": "analyze_task",
                "description": "Analyze current screen and execute task",
                "status": "pending"
            }]
        
        plan["estimated_steps"] = len(plan["steps"])
        
        return plan
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "memory_session": self.memory_session,
            "tasks_executed": len(self.execution_history),
            "current_context": self.context_memory,
            "agent_config": {
                "model": self.model,
                "window_title": self.window_title,
                "verbose": self.verbose
            }
        }
    
    def clear_session(self):
        """Clear current session data"""
        self.execution_history = []
        self.context_memory = {}
        if self.memory:
            self.memory.clear_session()
        
        if self.verbose:
            print(f"🧹 Cleared session: {self.memory_session}")
    
    def start_continuous_gameplay(self, goal: str, max_turns: int = 100, turn_delay: float = 1.0, session_state: Dict = None) -> Dict[str, Any]:
        """
        Start continuous autonomous Pokemon gameplay loop
        
        Args:
            goal: The game goal to pursue (e.g. "find and win pokemon battles")
            max_turns: Maximum number of turns to execute
            turn_delay: Delay between turns in seconds
            session_state: Interactive session state for pause/resume control
            
        Returns:
            Dict containing gameplay session results
        """
        if self.verbose:
            print(f"🎮 Starting continuous gameplay with goal: {goal}")
            print(f"📊 Max turns: {max_turns}, Turn delay: {turn_delay}s")
        
        # Initialize game loop state
        running = True
        turn = 0
        gameplay_history = []
        
        # Create run directory for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.runs_dir / f"{timestamp}_continuous"
        run_dir.mkdir(exist_ok=True)
        
        # Initialize progress tracking
        progress_file = run_dir / "progress_summary.md"
        
        try:
            while running and turn < max_turns:
                # Check for pause/resume controls if in interactive mode
                if session_state:
                    if session_state.get("paused", False):
                        time.sleep(0.5)  # Check pause state every 500ms
                        continue
                    if not session_state.get("running", True):
                        print("🛑 Stopping continuous gameplay - session ended")
                        break
                
                turn_start_time = time.time()
                print(f"\n🎯 Turn {turn + 1}/{max_turns}")
                
                # Step 1: Capture current game state
                game_context = self._capture_current_context()
                if not game_context.get("screenshot_data"):
                    print("⚠️ Failed to capture screenshot, skipping turn")
                    time.sleep(turn_delay)
                    continue
                
                # Step 2: Get memory summary for context
                memory_summary = ""
                if self.memory:
                    try:
                        memory_context = self.memory.generate_summary()
                        memory_summary = memory_context.get("summary", "")
                    except Exception as e:
                        if self.debug:
                            print(f"⚠️ Memory summary failed: {e}")
                        memory_summary = "No memory context available"
                
                # Step 3: Enhanced prompt with battle memory and expert knowledge
                battle_memory = ""
                if self.memory:
                    try:
                        battle_memory = self.memory.generate_battle_summary()
                    except Exception as e:
                        if self.debug:
                            print(f"⚠️ Battle memory failed: {e}")
                
                # Get overworld navigation context if available
                overworld_context = ""
                if game_context.get("overworld_analysis"):
                    overworld_data = game_context["overworld_analysis"]
                    if overworld_data.get("is_overworld") and not overworld_data.get("error"):
                        ascii_grid = overworld_data.get("raw_analysis", "").split("```")[1] if "```" in overworld_data.get("raw_analysis", "") else ""
                        overworld_context = f"""
**🗺️ OVERWORLD NAVIGATION DETECTED:**

**ASCII GRID MAP (8x8 current view):**
```
{ascii_grid}
```

**NAVIGATION INTELLIGENCE:**
- **Clear paths:** {', '.join(overworld_data.get('clear_directions', []))}
- **Blocked areas:** {', '.join(overworld_data.get('blocked_directions', []))} 
- **Obstacles nearby:** {', '.join(overworld_data.get('obstacles_nearby', []))}
- **AI Recommendation:** {overworld_data.get('recommended_movement', 'stay')}
- **Navigation notes:** {overworld_data.get('navigation_notes', 'No specific guidance')}

**OVERWORLD MOVEMENT RULES:**
⚠️ **AVOID TREES AND OBSTACLES:** Do NOT walk into trees (T), buildings (B), or walls (#)
✅ **USE OPEN PATHS:** Move towards grass (.) and paths (-) only
🎯 **FOLLOW GRID:** Use the ASCII grid above to see exactly where obstacles are"""

                # Step 3.5: Build enhanced prompt with landmark and coordinate data
                landmark_context = ""
                coordinate_context = ""
                
                # Include landmark detection results
                landmarks = game_context.get("landmarks", {})
                if landmarks.get("detected"):
                    landmark_details = landmarks.get("landmark_details", {})
                    navigation_advice = landmarks.get("navigation_advice", "")
                    
                    landmark_context = f"""
**🏛️ VISUAL LANDMARKS DETECTED:**
- **Landmarks found:** {', '.join(landmarks['detected'])}
- **Game state:** {landmarks.get('likely_overworld', False) and 'Overworld' or landmarks.get('likely_battle', False) and 'Battle' or landmarks.get('likely_menu', False) and 'Menu' or 'Unknown'}
- **Detection confidence:** {landmarks.get('confidence_score', 0.5):.1f}/1.0
{chr(10).join([f'- **{landmark}:** {detail}' for landmark, detail in landmark_details.items()])}
{f'- **AI Navigation advice:** {navigation_advice}' if navigation_advice else ''}

**🗺️ LANDMARK NAVIGATION STRATEGY:**
✅ **If Pokemon Center detected:** Consider healing if Pokemon health is low
✅ **If Viridian Forest detected:** Good for training and catching Pokemon  
✅ **If Route signs detected:** Use for navigation between areas
⚠️ **Follow landmark guidance** for efficient navigation between key locations"""
                
                # Include coordinate debug data when available
                coord_data = game_context.get("coordinate_debug", {})
                if coord_data.get("valid"):
                    coordinate_context = f"""
**POSITION DATA:**
- **Current Position:** ({coord_data.get('x')}, {coord_data.get('y')})
- **Status:** ✅ Position available for reference"""
                elif coord_data.get("error"):
                    coordinate_context = f"""
**POSITION:** ❌ Position unavailable - using visual navigation"""

                ai_prompt = f"""# Enhanced Pokemon Expert Agent - Continuous Gameplay

**CURRENT GOAL:** {goal}

**RECENT MEMORY CONTEXT:**
{memory_summary}

**BATTLE EXPERIENCE:**
{battle_memory}
{landmark_context}
{coordinate_context}
{overworld_context}

**CRITICAL BATTLE NAVIGATION RULES:**

🎯 **MOVE SELECTION PROCESS:**
1. **When you see battle menu** ("FIGHT", "BAG", "POKEMON", "RUN"):
   - Press **["a"]** to select "FIGHT" (usually first option)

2. **When you see move options** (like "GROWL", "THUNDERSHOCK", "TAIL WHIP"):
   - **DO NOT just press A repeatedly**
   - **READ each move name carefully** 
   - **Use DOWN arrow** to navigate to desired move
   - **Then press A** to select it

**Move Navigation Examples:**
- Want move #1 (top): ["a"]
- Want move #2 (second): ["down", "a"] 
- Want THUNDERSHOCK in position 2: ["down", "a"]
- Want move #3 in 2x2 grid: ["right", "a"]

**Type Effectiveness Quick Reference:**
- **THUNDERSHOCK** (Electric) → Super effective vs Flying/Water (like Pidgey, Magikarp)
- **TACKLE/SCRATCH** (Normal) → Reliable neutral damage vs most Pokemon
- **Status moves** (Growl, Tail Whip) → Don't deal damage, avoid in wild battles

**ANALYSIS TASK:**
1. **OBSERVE:** What screen elements are visible? Are there move names displayed?
2. **ANALYZE:** Is this a battle or overworld? What Pokemon/obstacles are involved?
3. **STRATEGIZE:** What's the best action to progress toward your goal?
4. **ACT:** Provide specific button sequence for your chosen action

What do you observe in the current screen? What action will you take next to progress toward your goal?"""
                
                # Step 4: Get AI analysis and action decision using unified API
                try:
                    api_result = self._call_gemini_api(
                        prompt=ai_prompt,
                        image_data=game_context["screenshot_data"], 
                        use_tools=True,
                        max_tokens=1000
                    )
                    
                    if api_result["error"]:
                        print(f"❌ API Error: {api_result['error']}")
                        continue
                    
                    ai_analysis = api_result["text"]
                    button_presses = api_result["button_presses"]
                    
                    if ai_analysis:
                        print(f"🤖 AI: {ai_analysis}")
                    
                    # Step 6: Execute button presses if provided
                    action_result = "No action taken"
                    if button_presses:
                        print(f"🎮 Executing buttons: {button_presses}")
                        if CONTROLLER_TYPE == "skyemu":
                            action_result = self.controller.press_sequence(button_presses, delay_between=2)
                        else:
                            # Execute buttons one by one for standard controller
                            for button in button_presses:
                                success = self.controller.press_button(button)
                                if not success:
                                    action_result = f"Failed to press {button}"
                                    break
                            else:
                                action_result = f"Successfully pressed: {', '.join(button_presses)}"
                        
                        print(f"🎯 Result: {action_result}")
                    else:
                        print("ℹ️ No button presses requested by AI")
                    
                    # Step 6.5: Record area visits for overworld movement
                    self._record_overworld_movement(
                        button_presses=button_presses,
                        game_context=game_context,
                        ai_analysis=ai_analysis,
                        turn=turn + 1
                    )
                    
                    # Step 7: Detect and store battle outcomes for learning
                    battle_context = self._extract_battle_context(ai_analysis, button_presses)
                    
                    turn_data = {
                        "turn": turn + 1,
                        "timestamp": datetime.now().isoformat(),
                        "goal": goal,
                        "ai_analysis": ai_analysis,
                        "button_presses": button_presses,
                        "action_result": action_result,
                        "screenshot_path": game_context.get("screenshot_path"),
                        "execution_time": time.time() - turn_start_time,
                        "battle_context": battle_context
                    }
                    
                    gameplay_history.append(turn_data)
                    
                    # Store in persistent memory with battle learning
                    if self.memory:
                        try:
                            self.memory.store_gameplay_turn(turn_data)
                            
                            # Store battle-specific learning if this was a battle action
                            if battle_context.get("is_battle_action"):
                                self._store_battle_learning(battle_context, ai_analysis, button_presses)
                                
                        except Exception as e:
                            if self.debug:
                                print(f"⚠️ Failed to store turn in memory: {e}")
                    
                    # Step 8: Update progress file every 5 turns
                    if turn % 5 == 0:
                        self._update_progress_file(progress_file, goal, gameplay_history[-5:])
                    
                except Exception as e:
                    print(f"❌ Error during turn {turn + 1}: {str(e)}")
                    if self.debug:
                        import traceback
                        traceback.print_exc()
                
                # Increment turn and apply delay
                turn += 1
                
                if turn < max_turns:
                    print(f"⏱️ Waiting {turn_delay}s before next turn...")
                    time.sleep(turn_delay)
        
        except KeyboardInterrupt:
            print("\n🛑 Continuous gameplay interrupted by user")
            running = False
        except Exception as e:
            print(f"\n❌ Unexpected error in gameplay loop: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            running = False
        
        finally:
            # Create final progress summary
            self._update_progress_file(progress_file, goal, gameplay_history)
            
            # Save complete session data
            session_file = run_dir / "session_data.json"
            with open(session_file, 'w') as f:
                json.dump({
                    "goal": goal,
                    "total_turns": turn,
                    "max_turns": max_turns,
                    "session_duration": sum(h.get("execution_time", 0) for h in gameplay_history),
                    "gameplay_history": gameplay_history,
                    "final_status": "completed" if turn >= max_turns else "interrupted"
                }, f, indent=2)
            
            print(f"\n✅ Continuous gameplay session completed after {turn} turns")
            print(f"📁 Session data saved to: {run_dir}")
            
            return {
                "status": "completed" if turn >= max_turns else "interrupted",
                "total_turns": turn,
                "max_turns": max_turns,
                "goal": goal,
                "run_directory": str(run_dir),
                "gameplay_history": gameplay_history
            }
    
    def _update_progress_file(self, progress_file: Path, goal: str, recent_turns: List[Dict]):
        """Update the progress summary file with recent gameplay"""
        try:
            if not recent_turns:
                return
            
            # Format recent turns for AI analysis
            turns_text = ""
            for turn_data in recent_turns:
                turns_text += f"Turn {turn_data['turn']}: {turn_data['ai_analysis']}\n"
                if turn_data['button_presses']:
                    turns_text += f"Actions: {', '.join(turn_data['button_presses'])}\n"
                turns_text += f"Result: {turn_data['action_result']}\n\n"
            
            # Ask AI to create progress summary
            prompt = f"""Create a concise progress report for our Pokemon gameplay session.

Current Goal: {goal}

Recent Gameplay Activity:
{turns_text}

Please provide:
1. Current status and achievements
2. Progress toward the goal
3. Key challenges encountered
4. Next steps and strategy

Keep it concise but informative."""

            # Use unified API method (no image needed for progress summary)
            api_result = self._call_gemini_api(
                prompt=prompt,
                image_data=None,
                use_tools=False,
                max_tokens=800
            )
            
            if api_result["error"]:
                summary = f"Error generating summary: {api_result['error']}"
            else:
                summary = api_result["text"] or "No summary generated"
            
            # Write to progress file
            with open(progress_file, 'w') as f:
                f.write(f"# Pokemon Gameplay Progress Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Goal:** {goal}\n\n")
                f.write(f"**Total Turns:** {len(recent_turns)}\n\n")
                f.write(summary)
            
            if self.verbose:
                print(f"📝 Updated progress file: {progress_file}")
                
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to update progress file: {e}")
    
    def _extract_battle_context(self, ai_analysis: str, button_presses: List[str]) -> Dict[str, Any]:
        """Extract battle context from AI analysis for learning"""
        context = {
            "is_battle_action": False,
            "opponent": None,
            "moves_mentioned": [],
            "move_used": None,
            "battle_outcome": None
        }
        
        if not ai_analysis:
            return context
        
        analysis_lower = ai_analysis.lower()
        
        # Detect if this is a battle-related action
        battle_keywords = ["battle", "fight", "thundershock", "tackle", "scratch", "growl", "tail whip", "caterpie", "pidgey", "vs", "hp"]
        if any(keyword in analysis_lower for keyword in battle_keywords):
            context["is_battle_action"] = True
        
        # Extract opponent Pokemon if mentioned
        pokemon_names = ["caterpie", "pidgey", "rattata", "weedle", "pikachu", "metapod", "kakuna"]
        for pokemon in pokemon_names:
            if pokemon in analysis_lower:
                context["opponent"] = pokemon.title()
                break
        
        # Extract moves mentioned in analysis
        move_names = ["thundershock", "tackle", "scratch", "growl", "tail whip", "ember", "vine whip"]
        for move in move_names:
            if move in analysis_lower:
                context["moves_mentioned"].append(move.title())
        
        # Determine which move was likely used based on button sequence and analysis
        if button_presses and context["is_battle_action"]:
            if button_presses == ["a"]:
                # First move (top-left) was selected
                if "thundershock" in analysis_lower:
                    context["move_used"] = "Thundershock"
                elif "tackle" in analysis_lower:
                    context["move_used"] = "Tackle"
                else:
                    context["move_used"] = "First move"
            elif button_presses == ["down", "a"]:
                # Second move was selected
                if "thundershock" in analysis_lower:
                    context["move_used"] = "Thundershock"
                else:
                    context["move_used"] = "Second move"
        
        # Detect battle outcomes
        outcome_keywords = {
            "victory": ["won", "defeated", "fainted", "victory", "gained exp"],
            "ongoing": ["battle", "attack", "use", "hp"],
            "lost": ["lost", "my pokemon fainted", "returned to pokeball"]
        }
        
        for outcome, keywords in outcome_keywords.items():
            if any(keyword in analysis_lower for keyword in keywords):
                context["battle_outcome"] = outcome
                break
        
        return context
    
    def _store_battle_learning(self, battle_context: Dict[str, Any], ai_analysis: str, button_presses: List[str]):
        """Store battle learning in memory for future reference"""
        if not self.memory or not battle_context.get("is_battle_action"):
            return
        
        try:
            # Store move effectiveness if we have enough context
            if battle_context.get("move_used") and battle_context.get("opponent"):
                move = battle_context["move_used"]
                opponent = battle_context["opponent"]
                outcome = battle_context.get("battle_outcome", "ongoing")
                
                # Determine effectiveness based on context
                effectiveness = "unknown"
                if "super effective" in ai_analysis.lower():
                    effectiveness = "super_effective"
                elif "not very effective" in ai_analysis.lower():
                    effectiveness = "not_very_effective" 
                elif outcome == "victory":
                    effectiveness = "effective"
                
                self.memory.store_move_effectiveness(
                    move_name=move,
                    move_type="unknown",  # Could be enhanced to detect type
                    target_type=opponent,
                    effectiveness=effectiveness,
                    button_sequence=button_presses
                )
            
            # Store general battle strategy learning
            if battle_context.get("battle_outcome") == "victory":
                strategy_note = f"Successful battle strategy: {ai_analysis[:100]}... Buttons used: {button_presses}"
                self.memory.store_learned_knowledge(
                    knowledge_type="battle_strategy",
                    subject="successful_battle",
                    content=strategy_note,
                    confidence_score=0.8
                )
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to store battle learning: {e}")
    
    # Enhanced Navigation Methods with Coordinate Debugging
    
    def _capture_current_context(self) -> Dict[str, Any]:
        """
        Enhanced context capture with visual landmark detection and optional coordinate debugging
        
        Returns:
            Dict containing screenshot data, visual analysis, and optional coordinate information
        """
        try:
            # Step 1: Capture screenshot (existing functionality)
            screenshot_path = self.controller.capture_screen()
            if not screenshot_path:
                return {
                    "error": "Failed to capture screenshot",
                    "window_found": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Read screenshot data for AI analysis
            screenshot_data = read_image_to_base64(screenshot_path)
            if not screenshot_data:
                return {
                    "error": "Failed to read screenshot data", 
                    "window_found": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 3: Enhanced visual landmark detection
            landmarks = self._detect_visual_landmarks(screenshot_data)
            
            # Step 4: Enhanced overworld analysis if applicable
            overworld_analysis = None
            if landmarks.get("likely_overworld", False):
                try:
                    overworld_analysis = self._detect_overworld_context(screenshot_data)
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Overworld analysis failed: {e}")
                    overworld_analysis = {"error": str(e), "is_overworld": False}
            
            # Step 5: Optional coordinate debugging (if SkyEmu available)
            coordinate_data = self._try_read_coordinates()
            
            # Step 6: Build comprehensive context
            game_context = {
                "screenshot_path": str(screenshot_path),
                "screenshot_data": screenshot_data, 
                "window_found": True,
                "timestamp": datetime.now().isoformat(),
                "landmarks": landmarks,
                "overworld_analysis": overworld_analysis,
                "coordinate_debug": coordinate_data,
                "visual_confidence": landmarks.get("confidence_score", 0.5)
            }
            
            if self.verbose:
                print(f"📸 Context captured: {len(landmarks.get('detected', []))} landmarks, coords: {'✅' if coordinate_data.get('valid') else '❌'}")
            
            return game_context
            
        except Exception as e:
            if self.debug:
                print(f"❌ Context capture failed: {e}")
            return {
                "error": str(e),
                "window_found": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def _detect_visual_landmarks(self, screenshot_data: str) -> Dict[str, Any]:
        """
        Enhanced visual landmark detection for Pokemon navigation
        
        Args:
            screenshot_data: Base64 encoded screenshot
            
        Returns:
            Dict with detected landmarks and confidence scores
        """
        landmarks = {
            "detected": [],
            "confidence_score": 0.5,
            "likely_overworld": False,
            "likely_battle": False,
            "likely_menu": False
        }
        
        try:
            # Use Gemini API to detect specific landmarks
            landmark_prompt = """# Pokemon Visual Landmark Detection Expert

Analyze this Pokemon screenshot to identify key landmarks and game state.

**LANDMARK DETECTION TASKS:**
1. **Pokemon Center** - Look for red roof buildings, "POKEMON CENTER" signs, or distinctive healing building architecture
2. **Viridian Forest** - Look for dense forest areas, tree patterns, or "VIRIDIAN FOREST" text
3. **Route Signs** - Look for numbered route signs (Route 1, Route 2, etc.)
4. **Town Entrances** - Look for building clusters, town name signs
5. **Battle Screens** - Look for Pokemon battle interface, HP bars, move selections
6. **Menu Screens** - Look for game menus, item lists, Pokemon party screens

**GAME STATE DETECTION:**
- **Overworld**: Walking around the game world, seeing grass/trees/buildings
- **Battle**: Pokemon battle in progress with HP bars and moves
- **Menu**: Game menus, inventory, Pokemon status screens
- **Indoor**: Inside buildings like Pokemon Centers

**RESPONSE FORMAT:**
```json
{
    "detected_landmarks": ["pokemon_center", "route_sign", "viridian_forest"],
    "game_state": "overworld/battle/menu/indoor",
    "confidence": 0.8,
    "landmark_details": {
        "pokemon_center": "Red roof building visible in upper area",
        "route_sign": "Route 1 sign visible on right side"
    },
    "navigation_advice": "Brief guidance based on landmarks detected"
}
```

Focus on identifying specific, actionable landmarks that can help with navigation."""

            # Call Gemini API for landmark detection
            result = self._call_gemini_api(
                prompt=landmark_prompt,
                image_data=screenshot_data,
                use_tools=False,
                max_tokens=400
            )
            
            if result.get("error"):
                landmarks["error"] = result["error"]
                return landmarks
            
            # Parse landmark response
            text_response = result.get("text", "")
            
            # Try to extract JSON response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text_response, re.DOTALL)
            if json_match:
                try:
                    landmark_data = json.loads(json_match.group(1))
                    landmarks["detected"] = landmark_data.get("detected_landmarks", [])
                    landmarks["confidence_score"] = landmark_data.get("confidence", 0.5)
                    landmarks["landmark_details"] = landmark_data.get("landmark_details", {})
                    landmarks["navigation_advice"] = landmark_data.get("navigation_advice", "")
                    
                    # Set game state flags
                    game_state = landmark_data.get("game_state", "unknown")
                    landmarks["likely_overworld"] = game_state == "overworld"
                    landmarks["likely_battle"] = game_state == "battle"
                    landmarks["likely_menu"] = game_state == "menu"
                    
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    landmarks = self._parse_landmark_text(text_response)
            else:
                # Fallback to text parsing
                landmarks = self._parse_landmark_text(text_response)
            
            return landmarks
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Landmark detection failed: {e}")
            landmarks["error"] = str(e)
            return landmarks
    
    def _parse_landmark_text(self, text: str) -> Dict[str, Any]:
        """Parse landmark information from text when JSON parsing fails"""
        landmarks = {
            "detected": [],
            "confidence_score": 0.3,  # Lower confidence for text parsing
            "likely_overworld": False,
            "likely_battle": False,
            "likely_menu": False,
            "landmark_details": {}
        }
        
        text_lower = text.lower()
        
        # Detect common landmarks
        landmark_keywords = {
            "pokemon_center": ["pokemon center", "healing", "red roof", "nurse joy"],
            "viridian_forest": ["viridian forest", "forest", "dense trees"],
            "route_sign": ["route", "sign", "path"],
            "town": ["town", "city", "pallet", "viridian"],
            "battle": ["battle", "hp", "moves", "pokemon vs"],
            "menu": ["menu", "bag", "pokemon", "save"]
        }
        
        for landmark, keywords in landmark_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                landmarks["detected"].append(landmark)
                landmarks["landmark_details"][landmark] = f"Detected via text analysis"
        
        # Determine game state
        if any(keyword in text_lower for keyword in ["grass", "tree", "overworld", "walking"]):
            landmarks["likely_overworld"] = True
        elif any(keyword in text_lower for keyword in ["battle", "hp", "attack"]):
            landmarks["likely_battle"] = True  
        elif any(keyword in text_lower for keyword in ["menu", "bag", "items"]):
            landmarks["likely_menu"] = True
        
        return landmarks
    
    def _try_read_coordinates(self) -> Dict[str, Any]:
        """
        Optional coordinate reading for debugging using existing SkyEmu infrastructure
        Never rely on this alone - always fallback gracefully
        
        Returns:
            Dict with coordinate information or error details
        """
        coordinate_data = {
            "valid": False,
            "x": None,
            "y": None,
            "method": "none",
            "error": None
        }
        
        # Only attempt if we have SkyEmu controller
        if CONTROLLER_TYPE != "skyemu" or not hasattr(self.controller, 'skyemu'):
            coordinate_data["error"] = "SkyEmu controller not available"
            return coordinate_data
        
        try:
            # Import the coordinate reader from our existing infrastructure
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent / "gemini-multimodal-playground" / "standalone"))
            from analyse_skyemu_ram import SkyEmuClient
            
            # Try to read Fire Red coordinates using the existing method
            client = SkyEmuClient(debug=self.debug)
            
            # Read coordinates via Fire Red SaveBlock8 pointer
            x_data = client.read_bytes_via_pointer(0x3005008, offset=0x0000, length=2)
            y_data = client.read_bytes_via_pointer(0x3005008, offset=0x0002, length=2)
            
            if x_data and y_data and len(x_data) == 2 and len(y_data) == 2:
                # Convert little-endian bytes to coordinates
                x_coord = int.from_bytes(x_data, byteorder='little')
                y_coord = int.from_bytes(y_data, byteorder='little')
                
                # Basic validation - coordinates should be reasonable
                if 0 <= x_coord <= 65535 and 0 <= y_coord <= 65535:
                    coordinate_data.update({
                        "valid": True,
                        "x": x_coord,
                        "y": y_coord,
                        "method": "fire_red_saveblock8",
                        "debug_info": f"Read from SaveBlock8 pointer at 0x3005008"
                    })
                    
                    if self.debug:
                        print(f"🎯 Coordinates: ({x_coord}, {y_coord})")
                else:
                    coordinate_data["error"] = f"Invalid coordinates: ({x_coord}, {y_coord})"
            else:
                coordinate_data["error"] = "Failed to read coordinate bytes via pointer"
        
        except Exception as e:
            coordinate_data["error"] = f"Coordinate reading failed: {str(e)}"
            if self.debug:
                print(f"🔧 Coordinate debug failed: {e}")
        
        return coordinate_data
    
    def learn_navigation_pattern(self, current_location: str, direction: str, destination: str, success: bool = True):
        """
        Learn and store navigation patterns discovered during gameplay
        
        Args:
            current_location: Where the AI is currently located
            direction: Direction taken (up, down, left, right, north, south, etc.)
            destination: Where the direction led to
            success: Whether this was a successful navigation
        """
        if not self.prompt_manager:
            return
        
        from datetime import datetime
        
        # Create a navigation entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if success:
            entry = f"**{timestamp}** - Navigation Discovery:\n"
            entry += f"- **From**: {current_location}\n"
            entry += f"- **Direction**: {direction}\n"
            entry += f"- **Leads to**: {destination}\n"
            entry += f"- **Status**: ✅ Confirmed route\n"
        else:
            entry = f"**{timestamp}** - Navigation Note:\n"
            entry += f"- **From**: {current_location}\n"
            entry += f"- **Direction**: {direction}\n"
            entry += f"- **Result**: ❌ Blocked or unsuccessful\n"
        
        try:
            self.prompt_manager.add_playbook_entry("navigation", entry, append=True)
            if self.verbose:
                print(f"📝 Learned: {current_location} --{direction}--> {destination if success else 'blocked'}")
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to store navigation pattern: {e}")
    
    def learn_location_knowledge(self, location: str, knowledge: str, category: str = "general"):
        """
        Store discovered knowledge about a specific location
        
        Args:
            location: Name of the location
            knowledge: What was learned about this location
            category: Type of knowledge (general, services, trainers, items, etc.)
        """
        if not self.prompt_manager:
            return
        
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"**{timestamp}** - {location} ({category}):\n"
        entry += f"- {knowledge}\n"
        
        # Determine which playbook to use
        playbook_name = "navigation"  # Default
        if "gym" in location.lower():
            playbook_name = "gyms"
        elif "center" in knowledge.lower() or "shop" in knowledge.lower():
            playbook_name = "services"
        
        try:
            self.prompt_manager.add_playbook_entry(playbook_name, entry, append=True)
            if self.verbose:
                print(f"📚 Learned about {location}: {knowledge[:50]}...")
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to store location knowledge: {e}")
    
    def get_okr_context(self) -> str:
        """
        Get contextual OKR (Objectives & Key Results) for current game state
        
        Returns:
            String containing focused, immediate objectives
        """
        if not self.enable_okr:
            return ""
        
        try:
            okr_prompt_path = Path(__file__).parent / "prompts" / "okr_prompt.md"
            if okr_prompt_path.exists():
                with open(okr_prompt_path, 'r') as f:
                    okr_content = f.read()
                return f"\n{okr_content}\n"
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to read OKR prompt: {e}")
        
        return ""
    
    def update_okr_progress(self, action: str, result: str, progress_note: str = ""):
        """
        Update OKR progress log with recent actions and results
        
        Args:
            action: Action taken by the AI
            result: Result or outcome
            progress_note: Optional note about progress toward objectives
        """
        if not self.enable_okr:
            return
        
        try:
            okr_path = Path(__file__).parent / "prompts" / "OKR.md"
            if okr_path.exists():
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Create progress entry
                if progress_note:
                    entry = f"- 🎯 [{timestamp}] {action} → {result} | {progress_note}\n"
                else:
                    entry = f"- 🎯 [{timestamp}] {action} → {result}\n"
                
                # Append to file
                with open(okr_path, 'a') as f:
                    f.write(entry)
                
                if self.verbose:
                    print(f"📊 OKR Progress: {action} → {result}")
                    
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to update OKR progress: {e}")