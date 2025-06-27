"""
Visual Analysis Module for Eevee Navigation System
Provides movement validation and object detection using Pixtral vision model
"""

import sys
import base64
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
# Import prompt manager to get universal template
from prompt_manager import PromptManager
            
# Add path for importing from the main project
project_root = Path(__file__).parent.parent  # eevee/ -> claude-plays-pokemon/
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    from skyemu_controller import SkyEmuController
    from llm_api import call_llm
except ImportError as e:
    print(f"Error importing required modules: {e}")
    raise

class VisualAnalysis:
    """Production visual analysis system for movement validation and object detection"""
    
    def __init__(self, grid_size: int = 8, save_logs: bool = True, runs_dir: Path = None):
        """
        Initialize visual analysis system
        
        Args:
            grid_size: Grid overlay size (8 recommended for better analysis)
            save_logs: Whether to save analysis logs and screenshots
            runs_dir: Directory to save logs (defaults to eevee/runs/)
        """
        self.controller = SkyEmuController()
        self.grid_size = grid_size
        self.save_logs = save_logs
        
        # Setup logging directory
        if runs_dir is None:
            runs_dir = Path(__file__).parent / "runs"
        self.runs_dir = runs_dir
        
        # Step counter for file naming
        self.step_counter = 0
        
        # Initialize coordinate mapper for pathfinding foundation
        try:
            from coordinate_mapper import CoordinateMapper
            self.coordinate_mapper = CoordinateMapper()
            self.enable_coordinate_mapping = True
        except ImportError:
            self.coordinate_mapper = None
            self.enable_coordinate_mapping = False
        
    def analyze_current_scene(self, screenshot_base64: str = None, verbose: bool = False, session_name: str = None, clean_output: bool = False) -> Dict:
        """
        Analyze current game scene for movement validation and object detection
        
        Args:
            screenshot_base64: Base64 encoded screenshot (if None, captures from SkyEmu)
            verbose: Enable verbose logging
            session_name: Session name for organizing logs (if None, uses timestamp)
            
        Returns:
            Dictionary with movement validation data and object detection
        """
        # Initialize comprehensive logger if not already done
        from evee_logger import get_comprehensive_logger, init_comprehensive_logger

        # Increment step counter
        self.step_counter += 1
        
        # Capture screenshot if not provided
        if screenshot_base64 is None:
            if not self.controller.is_connected():
                raise ConnectionError("Cannot connect to SkyEmu. Ensure it's running on port 8080.")
            
            screenshot_base64 = self.controller.get_screenshot_base64()
            if not screenshot_base64:
                raise RuntimeError("Failed to capture screenshot from SkyEmu")
        
        # Add grid overlay for spatial reference
        grid_image_base64 = self._add_grid_overlay(screenshot_base64)
        
        # Save grid overlay if logging enabled
        if self.save_logs:
            self._save_grid_image(grid_image_base64, session_name)
        
        # Collect RAM data for spatial awareness
        ram_data = self._collect_ram_data()
        
        # Get movement analysis from Pixtral with RAM context
        result = self._call_pixtral_for_analysis(grid_image_base64, verbose, ram_data)
        
        if not result["success"]:
            raise RuntimeError(f"Visual analysis failed: {result['error']}")
        
        # Parse and return structured movement data with RAM integration
        movement_data = self._parse_movement_response(result['response'], ram_data)
        
        # Save analysis results if logging enabled
        if self.save_logs:
            self._save_analysis_results(movement_data, result['response'], session_name)
        
        # Record coordinates for pathfinding foundation
        if self.enable_coordinate_mapping and ram_data.get("ram_available", False):
            screenshot_path = self._get_current_screenshot_path(session_name)
            session_id = session_name or f"session_{int(time.time())}"
            
            # Extract location data from enhanced RAM structure
            location_data = ram_data.get("location", {})
            coord_data = {
                "map_id": (location_data.get("map_bank", 0) * 1000) + location_data.get("map_id", 0),
                "x": location_data.get("x", 0),
                "y": location_data.get("y", 0),
                "map_name": location_data.get("location_name", "Unknown")
            }
            
            self.coordinate_mapper.record_coordinate(
                coord_data=coord_data,
                screenshot_path=screenshot_path,
                session_id=session_id,
                scene_analysis=movement_data
            )
            
            if verbose:
                print(f"📍 Coordinate recorded: Map {location_data.get('map_bank', 0)}-{location_data.get('map_id', 0)} X:{location_data.get('x', 0)} Y:{location_data.get('y', 0)}")
        
        if verbose:
            self._log_analysis_results(movement_data)
        
        # Clean console output for production use
        if clean_output:
            self._log_clean_console_output(movement_data)
        
        return movement_data
    
    def _get_ram_coordinates(self) -> Dict[str, Any]:
        """Get current map coordinates from RAM using enhanced compact game state"""
        try:
            import sys
            from pathlib import Path
            tests_path = Path(__file__).parent / "tests"
            if str(tests_path) not in sys.path:
                sys.path.insert(0, str(tests_path))
            from analyse_skyemu_ram import SkyEmuClient, PokemonFireRedReader
            
            client = SkyEmuClient(debug=False)
            reader = PokemonFireRedReader(client)
            
            # Get enhanced compact game state
            ram_data = reader.get_compact_game_state()
            
            # Return the full RAM data structure for consistent usage
            return ram_data
            
        except Exception as e:
            return {
                "ram_available": False,
                "error": str(e),
                "location": {"map_bank": 0, "map_id": 0, "x": 0, "y": 0, "location_name": "Error"}
            }

    def _add_grid_overlay(self, screenshot_base64: str) -> str:
        """Add light grey grid overlay to screenshot for spatial reference and coordinates"""
        try:
            # Decode base64 to image
            image_bytes = base64.b64decode(screenshot_base64)
            image = Image.open(BytesIO(image_bytes)).convert('RGB')
            
            # Create overlay
            overlay_image = image.copy().convert('RGBA')
            grid_overlay = Image.new('RGBA', overlay_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(grid_overlay)
            
            width, height = image.size
            tile_width = width // self.grid_size
            tile_height = height // self.grid_size
            
            # Draw light grey grid lines
            grid_color = (204, 204, 204, 100)  # Light grey with transparency
            for x in range(0, width, tile_width):
                draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
            
            for y in range(0, height, tile_height):
                draw.line([(0, y), (width, y)], fill=grid_color, width=1)
            
            # Add coordinate labels (real world coordinates based on player position)
            try:
                font_size = max(8, min(12, tile_width // 4))
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get player's real world coordinates from RAM
            coords = self._get_ram_coordinates()
            if coords.get("ram_available", False):
                location = coords.get("location", {})
                player_ram_x = location.get("x", 0)
                player_ram_y = location.get("y", 0)
                
                # Calculate center grid position (where player is)
                center_grid_x = self.grid_size // 2
                center_grid_y = self.grid_size // 2
                
                text_color = (204, 204, 204, 120)
                center_text_color = (255, 255, 0, 200)  # Yellow for player position
                
                for tile_x in range(self.grid_size):
                    for tile_y in range(self.grid_size):
                        pixel_x = tile_x * tile_width
                        pixel_y = tile_y * tile_height
                        
                        # Calculate real world coordinates for this tile
                        offset_x = tile_x - center_grid_x
                        offset_y = tile_y - center_grid_y
                        real_x = player_ram_x + offset_x
                        real_y = player_ram_y + offset_y
                        
                        coord_text = f"{real_x},{real_y}"
                        
                        # Use different color for center tile (player position)
                        if tile_x == center_grid_x and tile_y == center_grid_y:
                            draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill=center_text_color, font=font)
                        else:
                            draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill=text_color, font=font)
            else:
                # Fallback to visual grid coordinates if RAM not available
                text_color = (204, 204, 204, 120)
                for tile_x in range(self.grid_size):
                    for tile_y in range(self.grid_size):
                        pixel_x = tile_x * tile_width
                        pixel_y = tile_y * tile_height
                        coord_text = f"{tile_x},{tile_y}"
                        draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill=text_color, font=font)
            
            # Add map info in top-right corner (map bank/ID only, not coordinates)
            try:
                if coords.get("ram_available", False):
                    location = coords.get("location", {})
                    map_bank = location.get("map_bank", 0)
                    map_id = location.get("map_id", 0)
                    
                    # Create map display text (no coordinates since they're in the grid)
                    map_display = f"Map:{map_bank}-{map_id}"
                else:
                    map_display = "Map:?"
                
                # Use larger font for map display
                try:
                    map_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
                except:
                    map_font = ImageFont.load_default()
                
                # Get text dimensions for background box
                bbox = draw.textbbox((0, 0), map_display, font=map_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Position in top-right corner with padding
                padding = 5
                text_x = width - text_width - padding
                text_y = padding
                
                # Draw black background box
                box_coords = [
                    (text_x - padding, text_y - padding),
                    (text_x + text_width + padding, text_y + text_height + padding)
                ]
                draw.rectangle(box_coords, fill=(0, 0, 0, 200))
                
                # Draw white text
                draw.text((text_x, text_y), map_display, fill=(255, 255, 255, 255), font=map_font)
                
            except Exception as map_error:
                # Fallback map display if RAM reading fails
                map_display = "Map:?"
                draw.text((width - 60, 5), map_display, fill=(255, 255, 255, 255), font=font)
            
            # Add subtle player position indicator at screen center
            try:
                if coords.get("ram_available", False):
                    # Draw small player position indicator at screen center
                    center_x = width // 2
                    center_y = height // 2
                    
                    # Draw a small yellow circle for player position
                    circle_radius = 4
                    
                    # Draw circle outline
                    circle_bbox = [
                        center_x - circle_radius, center_y - circle_radius,
                        center_x + circle_radius, center_y + circle_radius
                    ]
                    draw.ellipse(circle_bbox, outline=(255, 255, 0, 180), width=1)
                    
            except Exception as player_indicator_error:
                # Player indicator is optional, don't fail if it doesn't work
                pass
            
            # Composite and convert back to base64
            result = Image.alpha_composite(overlay_image, grid_overlay).convert('RGB')
            buffer = BytesIO()
            result.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            raise RuntimeError(f"Failed to add grid overlay: {e}")
    
    def _collect_ram_data(self) -> Dict[str, Any]:
        """Collect current RAM data from SkyEmu for spatial awareness"""
        try:
            # Import and initialize RAM analyzer
            import sys
            from pathlib import Path
            tests_path = Path(__file__).parent / "tests"
            if str(tests_path) not in sys.path:
                sys.path.insert(0, str(tests_path))
            from analyse_skyemu_ram import SkyEmuClient, PokemonFireRedReader
            
            client = SkyEmuClient(debug=False)
            reader = PokemonFireRedReader(client)
            
            # Get compact game state using our new standardized method
            ram_data = reader.get_compact_game_state()
            
            return ram_data
            
        except ImportError as e:
            return {"ram_available": False, "error": f"RAM analyzer not available: {str(e)}"}
        except Exception as e:
            return {"ram_available": False, "error": f"RAM collection failed: {str(e)}"}
    
    def _call_pixtral_for_analysis(self, grid_image_base64: str, verbose: bool = False, ram_data: Dict = None) -> Dict:
        """Call visual_context_analyzer template with hybrid mode support and RAM data integration"""
        try:
            import time
            start_time = time.time()
            
            # Import provider configuration for hybrid mode
            from provider_config import get_provider_for_hybrid_task, get_model_for_task, get_hybrid_config
            from evee_logger import get_comprehensive_logger
            
            # Get provider and model for visual analysis in hybrid mode
            provider = get_provider_for_hybrid_task('visual')
            model = get_model_for_task('screenshot_analysis')
            hybrid_config = get_hybrid_config()
            

            # Initialize prompt manager and get appropriate template
            prompt_manager = PromptManager()
            
            # Use Gemini-specific template for Gemini provider
            if provider == 'gemini':
                template_data = prompt_manager.base_prompts.get("visual_context_analyzer_gemini", {})
                template_name = "visual_context_analyzer_gemini"
            else:
                template_data = prompt_manager.base_prompts.get("visual_context_analyzer", {})
                template_name = "visual_context_analyzer"
            
            template_content = template_data.get("template", "")
            
            if not template_content:
                error_msg = f"{template_name} template not found"
                raise RuntimeError(error_msg)
            
            # Use provider-specific template and inject RAM context if available
            prompt = template_content
            
            # Add comprehensive RAM context to the prompt if available
            if ram_data and ram_data.get("ram_available"):
                location = ram_data.get("location", {})
                player = ram_data.get("player", {})
                party_summary = ram_data.get("party_summary", {})
                quick_status = ram_data.get("quick_status", {})
                
                ram_context = f"""

CURRENT GAME STATE (from RAM):
Location: Map {location.get('map_bank', '?')}-{location.get('map_id', '?')} ({location.get('location_name', 'Unknown')})
Position: X={location.get('x', '?')}, Y={location.get('y', '?')}
Player: {player.get('name', 'Unknown')} | Money: {player.get('money', 'unknown')}

Pokemon Party Status:
- Total Pokemon: {party_summary.get('total_pokemon', 0)}
- Healthy: {party_summary.get('healthy_pokemon', 0)} | Fainted: {party_summary.get('fainted_pokemon', 0)}
- Party Health: {party_summary.get('party_health_status', 'unknown').upper()}
- Needs Healing: {'YES' if quick_status.get('needs_healing', False) else 'NO'}

Context:
- At Pokemon Center: {'YES' if quick_status.get('at_pokemon_center', False) else 'NO'}
- Can Battle: {'YES' if quick_status.get('can_battle', True) else 'NO'}
- Emergency: {'YES' if quick_status.get('emergency_situation', False) else 'NO'}

This game state data should inform your visual analysis and scene understanding.
"""
                prompt = prompt + ram_context

            # Log hybrid mode configuration
            if verbose and hybrid_config['enabled']:
                print(f"🔀 HYBRID MODE: Visual analysis using {provider} ({model})")
            
            response = call_llm(
                prompt=prompt,
                image_data=grid_image_base64,
                model=model,
                provider=provider,
                max_tokens=800  # Increased for structured response
            )
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Safely extract response text
            response_text = ""
            if hasattr(response, 'text'):
                response_text = response.text if response.text is not None else ""
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response) if response is not None else ""
            
            response_length = len(response_text)
            
            # Check for empty response and log detailed error
            if response_length == 0:
                # Log detailed error information
                error_details = {
                    'provider': provider,
                    'model': model,
                    'response_type': type(response).__name__,
                    'response_attributes': dir(response) if response else 'None',
                    'has_error_attr': hasattr(response, 'error'),
                    'error_value': getattr(response, 'error', 'No error attribute'),
                    'response_str': str(response) if response else 'None'
                }
                
                print(f"🚨 GEMINI ERROR DETECTED - DELAYING 2 MINUTES")
                print(f"   Provider: {error_details['provider']}")
                print(f"   Model: {error_details['model']}")
                print(f"   Response Type: {error_details['response_type']}")
                print(f"   Response Object: {error_details['response_str']}")
                if error_details['has_error_attr']:
                    print(f"   Error Message: {error_details['error_value']}")
                print(f"   Response Attributes: {error_details['response_attributes']}")
                
            return {
                "success": True,
                "response": response_text,  # Use the safely extracted text
                "prompt_sent": prompt,  # Store the template prompt
                "processing_time_ms": processing_time,
                "provider_used": provider,
                "model_used": model,
                "hybrid_mode": hybrid_config['enabled'],
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "prompt_sent": "visual_context_analyzer template",
                "processing_time_ms": None,
                "error": str(e)
            }
    
    def _parse_movement_response(self, response_text: str, ram_data: Dict = None) -> Dict:
        """Parse flexible visual analysis response with dynamic scene data and RAM integration"""
        import json  # Import at function level to be available in except block
        from evee_logger import get_comprehensive_logger
        
        # Always include raw response for AI analysis
        result = {
            "raw_pixtral_response": response_text
        }
        
        debug_logger = get_comprehensive_logger()
        response_preview = response_text[:100] if response_text else "EMPTY"
        
        # Try to parse JSON response
        try:
            # Clean response text (remove markdown if present)
            clean_response = response_text.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response.replace("```json", "").replace("```", "").strip()
            
            # Check for empty response
            if not clean_response:
                raise ValueError("Empty response from visual analysis")
            
            # Parse JSON  
            parsed_data = json.loads(clean_response)
            
            # Log successful JSON parsing
            if debug_logger:
                debug_logger.log_debug('INFO', f"JSON parsing successful - Response: {response_preview}")
            
            # Extract MANDATORY core fields
            result["scene_type"] = parsed_data.get("scene_type", "navigation")
            result["recommended_template"] = parsed_data.get("recommended_template", "ai_directed_navigation")
            result["valid_buttons"] = parsed_data.get("valid_buttons", [])
            result["confidence"] = parsed_data.get("confidence", "medium")
            
            # Pass through ALL dynamic scene data (everything except core fields)
            core_fields = {"scene_type", "recommended_template", "valid_buttons", "confidence", "raw_pixtral_response"}
            for key, value in parsed_data.items():
                if key not in core_fields:
                    result[key] = value
            
            # Generate default valid_buttons if missing (fallback for empty responses)
            if not result["valid_buttons"]:
                scene_type = result["scene_type"]
                if scene_type == "battle":
                    result["valid_buttons"] = [
                        {"key": "A", "action": "select_option", "result": "battle_action"},
                        {"key": "→", "action": "cursor_right", "result": "move_cursor"},
                        {"key": "↓", "action": "cursor_down", "result": "move_cursor"}
                    ]
                elif scene_type == "menu":
                    result["valid_buttons"] = [
                        {"key": "A", "action": "confirm", "result": "advance_text"},
                        {"key": "B", "action": "cancel", "result": "go_back"}
                    ]
                else:  # navigation
                    result["valid_buttons"] = [
                        {"key": "↑", "action": "move_up", "result": "character_movement"},
                        {"key": "↓", "action": "move_down", "result": "character_movement"},
                        {"key": "←", "action": "move_left", "result": "character_movement"},
                        {"key": "→", "action": "move_right", "result": "character_movement"}
                    ]
            
            # Extract valid movements from valid_buttons for backward compatibility
            movement_actions = []
            for button in result["valid_buttons"]:
                key = button.get("key", "")
                action = button.get("action", "")
                if "move" in action.lower() and key in ["↑", "↓", "←", "→", "up", "down", "left", "right"]:
                    # Map arrow symbols to direction names
                    direction_map = {"↑": "up", "↓": "down", "←": "left", "→": "right"}
                    direction = direction_map.get(key, key)
                    if direction in ["up", "down", "left", "right"]:
                        movement_actions.append(direction)
            
            result["valid_movements"] = movement_actions if movement_actions else ["up", "down", "left", "right"]
            
            # SIMPLIFIED: No template conversion needed - use direct recommendations
            # Visual analysis templates now provide correct template names directly
            
            # Add backward compatibility fields based on dynamic scene data
            scene_type = result["scene_type"]
            
            # Generate spatial context from dynamic data
            button_count = len(result["valid_buttons"])
            result["spatial_context"] = f"Scene: {scene_type}, Valid buttons: {button_count}"
            
            # Extract character position from dynamic navigation data if available
            result["character_position"] = result.get("player_position", result.get("player_pos", ""))
            
            # Enhanced visual description based on scene type and available data
            confidence = result.get("confidence", "medium")
            if scene_type == "battle":
                result["visual_description"] = f"Battle scene detected - {confidence} confidence"
            elif scene_type == "menu":
                result["visual_description"] = f"Menu/dialogue scene detected - {confidence} confidence"
            else:
                result["visual_description"] = f"Navigation scene detected - {confidence} confidence"
                
            result["template_reason"] = f"Scene type '{scene_type}' → template '{result['recommended_template']}'"
                
        except (json.JSONDecodeError, KeyError) as e:
            # Log failed JSON parsing
            if debug_logger:
                debug_logger.log_debug('ERROR', f"JSON parsing failed: {str(e)} - Response: {response_preview}")
            
            # Fallback parsing for non-JSON responses - provide minimal viable structure
            result["scene_type"] = "navigation"
            result["recommended_template"] = "ai_directed_navigation"
            result["confidence"] = "low"
            result["spatial_context"] = "Failed to parse response"
            result["character_position"] = ""
            result["visual_description"] = "Failed to parse response"
            result["template_reason"] = f"JSON parsing failed: {e}"
            result["valid_movements"] = ["up", "down", "left", "right"]
            result["valid_buttons"] = [
                {"key": "↑", "action": "move_up", "result": "character_movement"},
                {"key": "↓", "action": "move_down", "result": "character_movement"},
                {"key": "←", "action": "move_left", "result": "character_movement"},
                {"key": "→", "action": "move_right", "result": "character_movement"}
            ]
        
        # Integrate RAM data into spatial_context if available
        if ram_data and ram_data.get("ram_available"):
            # Enhance spatial_context with RAM data
            existing_spatial = result.get("spatial_context", "")
            location = ram_data.get("location", {})
            result["spatial_context"] = {
                "ram_data": {
                    "available": True,
                    "map_bank": location.get("map_bank"),
                    "map_id": location.get("map_id"),
                    "player_x": location.get("x"),
                    "player_y": location.get("y"),
                    "location_name": location.get("location_name")
                },
                "visual_context": existing_spatial
            }
        else:
            # Ensure spatial_context exists even without RAM data
            if "spatial_context" not in result:
                result["spatial_context"] = {"ram_data": {"available": False}}
            
        return result
    
    
    
    def _save_grid_image(self, grid_image_base64: str, session_name: str = None) -> None:
        """Save grid overlay image to runs directory"""
        try:
            # Create session directory and screenshots subfolder
            session_dir = self._get_session_dir(session_name)
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Create screenshots subfolder
            screenshots_dir = session_dir / "sshots"
            screenshots_dir.mkdir(exist_ok=True)
            
            # Save grid image in screenshots subfolder
            image_bytes = base64.b64decode(grid_image_base64)
            image_path = screenshots_dir / f"step_{self.step_counter:04d}_grid.png"
            
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
                
        except Exception as e:
            # Use debug logger if available, otherwise fallback to print
            from evee_logger import get_comprehensive_logger
            debug_logger = get_comprehensive_logger()
            if debug_logger:
                debug_logger.log_debug('ERROR', f"Failed to save grid image: {e}")
            else:
                print(f"⚠️ Failed to save grid image: {e}")
    
    def _save_analysis_results(self, movement_data: Dict, raw_response: str, session_name: str = None) -> None:
        """Save visual analysis results to runs directory"""
        try:
            # Create session directory
            session_dir = self._get_session_dir(session_name)
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Save analysis results
            analysis_path = session_dir / f"step_{self.step_counter:04d}_visual_analysis.txt"
            
            with open(analysis_path, 'w') as f:
                f.write(f"VISUAL ANALYSIS STEP {self.step_counter}\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"GRID SIZE: {self.grid_size}x{self.grid_size}\n")
                
                # Handle simplified data structure
                if 'raw_pixtral_response' in movement_data:
                    f.write(f"RAW PIXTRAL RESPONSE:\n{movement_data['raw_pixtral_response']}\n\n")
                else:
                    # Legacy format support
                    if 'location_class' in movement_data:
                        f.write(f"LOCATION CLASS: {movement_data['location_class']}\n\n")
                    
                    if 'valid_sequences' in movement_data and '1_move' in movement_data['valid_sequences']:
                        single_moves = movement_data['valid_sequences']['1_move']
                        valid_movements = [move for move, _ in single_moves]
                        f.write(f"VALID MOVEMENTS: {valid_movements}\n\n")
                
                # Legacy format details  
                if 'valid_sequences' in movement_data and '1_move' in movement_data['valid_sequences']:
                    single_moves = movement_data['valid_sequences']['1_move']
                    f.write("MOVEMENT DETAILS:\n")
                    for move, reason in single_moves:
                        f.write(f"  ✓ {move} - {reason}\n")
                    f.write("\n")
                
                # Objects detected (legacy format)
                if 'objects_detected' in movement_data:
                    objects = movement_data['objects_detected']
                    total_objects = sum(len(obj_list) for obj_list in objects.values())
                    f.write(f"OBJECTS DETECTED: {total_objects}\n")
                    for obj_type, coords in objects.items():
                        if coords:
                            f.write(f"  {obj_type.upper()}: {coords}\n")
                    f.write("\n")
                
                # Prompt recommendation (legacy format)
                if 'recommended_prompt' in movement_data:
                    f.write(f"RECOMMENDED PROMPT: {movement_data['recommended_prompt']}\n")
                if 'prompt_reason' in movement_data:
                    f.write(f"PROMPT REASON: {movement_data['prompt_reason']}\n\n")
                
                # Raw AI response
                f.write("--- RAW PIXTRAL RESPONSE ---\n")
                f.write(raw_response)
                f.write("\n--- END RAW RESPONSE ---\n")
                
        except Exception as e:
            # Use debug logger if available, otherwise fallback to print
            from evee_logger import get_comprehensive_logger
            debug_logger = get_comprehensive_logger()
            if debug_logger:
                debug_logger.log_debug('ERROR', f"Failed to save analysis results: {e}")
            else:
                print(f"⚠️ Failed to save analysis results: {e}")
    
    def _get_session_dir(self, session_name: str = None) -> Path:
        """Get or create session directory for logging"""
        # Use debug logger if available for session management logs
        from evee_logger import get_comprehensive_logger
        debug_logger = get_comprehensive_logger()
        
        if session_name is None:
            import time
            session_name = f"session_{int(time.time())}"
        elif not session_name.startswith("session_"):
            # Ensure session name has proper prefix  
            session_name = f"session_{session_name}"

        return self.runs_dir / session_name
    
    def reset_step_counter(self) -> None:
        """Reset step counter for new session"""
        self.step_counter = 0
    
    def _get_current_screenshot_path(self, session_name: str = None) -> str:
        """Get the path for the current screenshot file"""
        session_dir = self._get_session_dir(session_name)
        screenshots_dir = session_dir / "sshots"
        return str(screenshots_dir / f"step_{self.step_counter:04d}_grid.png")
    
    def _log_analysis_results(self, movement_data: Dict) -> None:
        """Log analysis results to console for debugging"""
        from evee_logger import get_comprehensive_logger
        debug_logger = get_comprehensive_logger()
        
        if debug_logger:
            debug_logger.log_debug('INFO', f"Visual Analysis Results - Step: {self.step_counter}")
            if 'raw_pixtral_response' in movement_data:
                response_preview = movement_data['raw_pixtral_response'][:100]
                debug_logger.log_debug('INFO', f"Response Preview: {response_preview}...")
            else:
                debug_logger.log_debug('INFO', f"Movement Data Keys: {list(movement_data.keys())}")
        else:
            print(f" Visual Analysis DONE for  Step: {self.step_counter}")
    
    def _log_clean_console_output(self, movement_data: Dict) -> None:
        """Output clean JSON for visual analysis to console"""
        from evee_logger import get_comprehensive_logger
        
        # Extract the core visual analysis data for clean output
        visual_output = {}
        
        # Always include core mandatory fields
        core_fields = ['scene_type', 'recommended_template', 'valid_buttons', 'confidence']
        for field in core_fields:
            if field in movement_data:
                visual_output[field] = movement_data[field]
        
        # Include all dynamic scene-specific data (everything except internal fields)
        internal_fields = {
            'raw_pixtral_response', 'valid_movements', 'spatial_context', 
            'character_position', 'visual_description', 'template_reason'
        }
        
        for key, value in movement_data.items():
            if key not in core_fields and key not in internal_fields and value:
                visual_output[key] = value
        
        # Use logger for clean console output
        logger = get_comprehensive_logger()
        if logger:
            logger.log_visual_analysis_console(visual_output)
        else:
            # Fallback if no logger available
            import json
            print("=== VISUAL ANALYSIS ===")
            print(json.dumps(visual_output, indent=2, ensure_ascii=False))
            print()