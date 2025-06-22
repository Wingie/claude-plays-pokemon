"""
Visual Analysis Module for Eevee Navigation System
Provides movement validation and object detection using Pixtral vision model
"""

import sys
import base64
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

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
        
    def analyze_current_scene(self, screenshot_base64: str = None, verbose: bool = False, session_name: str = None) -> Dict:
        """
        Analyze current game scene for movement validation and object detection
        
        Args:
            screenshot_base64: Base64 encoded screenshot (if None, captures from SkyEmu)
            verbose: Enable verbose logging
            session_name: Session name for organizing logs (if None, uses timestamp)
            
        Returns:
            Dictionary with movement validation data and object detection
        """
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
        
        # Get movement analysis from Pixtral
        result = self._call_pixtral_for_analysis(grid_image_base64, verbose)
        
        if not result["success"]:
            raise RuntimeError(f"Visual analysis failed: {result['error']}")
        
        # Parse and return structured movement data
        movement_data = self._parse_movement_response(result['response'])
        
        # Save analysis results if logging enabled
        if self.save_logs:
            self._save_analysis_results(movement_data, result['response'], session_name)
        
        if verbose:
            self._log_analysis_results(movement_data)
        
        return movement_data
    
    def _add_grid_overlay(self, screenshot_base64: str) -> str:
        """Add light grey grid overlay to screenshot for spatial reference"""
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
            
            # Add coordinate labels
            try:
                font_size = max(8, min(12, tile_width // 4))
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            text_color = (204, 204, 204, 120)
            for tile_x in range(self.grid_size):
                for tile_y in range(self.grid_size):
                    pixel_x = tile_x * tile_width
                    pixel_y = tile_y * tile_height
                    coord_text = f"{tile_x},{tile_y}"
                    draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill=text_color, font=font)
            
            # Composite and convert back to base64
            result = Image.alpha_composite(overlay_image, grid_overlay).convert('RGB')
            buffer = BytesIO()
            result.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            raise RuntimeError(f"Failed to add grid overlay: {e}")
    
    def _call_pixtral_for_analysis(self, grid_image_base64: str, verbose: bool = False) -> Dict:
        """Call Pixtral for visual movement analysis"""
        center_coord = f"{self.grid_size//2},{self.grid_size//2}"
        
        prompt = f"""POKEMON GAME TERRAIN COLLISION ANALYSIS

You are analyzing a Pokemon Game Boy Advance screenshot with a {self.grid_size}x{self.grid_size} coordinate grid overlay.
Your task is to identify Pokemon terrain collision rules and determine which directions are WALKABLE vs BLOCKED.

COORDINATE SYSTEM:
- up = Up movement (toward 0 on Y-axis)
- down = Down movement (toward {self.grid_size-1} on Y-axis)  
- left = Left movement (toward 0 on X-axis)
- right = Right movement (toward {self.grid_size-1} on X-axis)
- Player position: Center at ({center_coord})

POKEMON COLLISION RULES:
🚫 BLOCKED TERRAIN (cannot walk through):
- Tree sprites (even if they look like grass textures)
- Water tiles (blue areas, ponds, rivers)
- Building walls and structures
- Rock formations and cliffs
- NPCs and trainers (character sprites)

✅ WALKABLE TERRAIN (can walk through):
- Grass paths (actual walkable grass, not tree sprites)
- Dirt/sand paths and roads
- Wooden floors and indoor tiles
- Open doorways and entrances

VISUAL RECOGNITION TIPS:
- Tree sprites often have darker green or brown trunks even with grass-like tops
- Water has distinct blue coloring and reflective appearance
- Walkable grass paths are usually lighter/different shade than tree areas
- Building walls have straight edges and solid colors

REQUIRED RESPONSE FORMAT:
```
VISUAL_DESCRIPTION: [What you see - include details about Pokemon terrain elements]
LOCATION_TYPE: [forest/town/route/cave/building/water based on Pokemon environment]

TERRAIN_ANALYSIS:
up: [Pokemon terrain type] - [WALKABLE/BLOCKED based on collision rules]
down: [Pokemon terrain type] - [WALKABLE/BLOCKED based on collision rules]  
left: [Pokemon terrain type] - [WALKABLE/BLOCKED based on collision rules]
right: [Pokemon terrain type] - [WALKABLE/BLOCKED based on collision rules]

VALID_SEQUENCES:
1_MOVE:
- ("up", "Grassy terrain continues upward")
- ("down", "Grassy terrain extends downward")
- ("left", "Grassy terrain to the left")
- ("right", "Grassy terrain to the right")

OBJECTS_VISIBLE:
Characters: [List any trainers or NPCs visible]
Structures: [List any buildings or structures]
Signs: [List any signs or posts]
Items: [List any items or objects]
```

CRITICAL ANALYSIS FOCUS:
- Apply Pokemon game collision detection rules
- Distinguish tree sprites from walkable grass paths
- Recognize water, walls, and other blocking terrain
- Only mark directions as WALKABLE if they follow Pokemon movement rules"""

        try:
            import time
            start_time = time.time()
            
            response = call_llm(
                prompt=prompt,
                image_data=grid_image_base64,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=600
            )
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if verbose:
                print(f"📤 Pixtral visual analysis request sent")
                print(f"📥 Response received: {len(response.text) if response.text else 0} chars")
            
            return {
                "success": True,
                "response": response.text if hasattr(response, 'text') else str(response),
                "prompt_sent": prompt,  # ENHANCED: Store the complete prompt
                "processing_time_ms": processing_time,  # ENHANCED: Store timing
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "prompt_sent": prompt,  # ENHANCED: Store prompt even on failure
                "processing_time_ms": None,
                "error": str(e)
            }
    
    def _parse_movement_response(self, response_text: str) -> Dict:
        """Return raw Pixtral response for AI to analyze naturally"""
        return {
            "raw_pixtral_response": response_text
        }
    
    
    
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
            print(f"⚠️ Failed to save analysis results: {e}")
    
    def _get_session_dir(self, session_name: str = None) -> Path:
        """Get or create session directory for logging"""
        if session_name is None:
            import time
            session_name = f"session_{int(time.time())}"
            print(f"⚠️ Visual analysis: No session_name provided, creating: {session_name}")
        elif not session_name.startswith("session_"):
            # Ensure session name has proper prefix  
            session_name = f"session_{session_name}"
            print(f"🔧 Visual analysis: Using session folder: {session_name}")
        else:
            print(f"✅ Visual analysis: Using existing session folder: {session_name}")
        
        return self.runs_dir / session_name
    
    def reset_step_counter(self) -> None:
        """Reset step counter for new session"""
        self.step_counter = 0
    
    def _log_analysis_results(self, movement_data: Dict) -> None:
        """Log analysis results to console for debugging"""
        print(f"🔍 Visual Analysis Results:")
        print(f"   Step: {self.step_counter}")
        if 'raw_pixtral_response' in movement_data:
            response_preview = movement_data['raw_pixtral_response'][:100]
            print(f"   Response Preview: {response_preview}...")
        else:
            print(f"   Movement Data Keys: {list(movement_data.keys())}")