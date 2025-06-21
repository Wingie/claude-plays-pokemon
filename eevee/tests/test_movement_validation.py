#!/usr/bin/env python3
"""
Movement Validation Test
Compare 4x4 vs 8x8 light grey grids for directional movement analysis
Return structured dictionary with location class and valid movements
"""

import sys
import base64
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))                    # For eevee modules
sys.path.append(str(project_root))                  # For llm_api.py in root
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    from skyemu_controller import SkyEmuController
    from dotenv import load_dotenv
    from llm_api import call_llm
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

load_dotenv()

class MovementValidator:
    """Compare grid sizes for directional movement validation"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.timestamp = int(time.time())
        
        # Create directory for overlay images
        self.overlay_dir = Path(__file__).parent / f"movement_validation_{self.timestamp}"
        self.overlay_dir.mkdir(exist_ok=True)
        
    def capture_screenshot(self) -> Optional[str]:
        """Capture screenshot and return base64"""
        try:
            screenshot_data = self.controller.get_screenshot_base64()
            if not screenshot_data:
                print("❌ Failed to capture screenshot")
                return None
            return screenshot_data
        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            return None
    
    def decode_base64_to_image(self, base64_data: str) -> Optional[Image.Image]:
        """Convert base64 to PIL Image"""
        try:
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_bytes))
            return image.convert('RGB')
        except Exception as e:
            print(f"❌ Failed to decode base64: {e}")
            return None
    
    def add_light_grey_grid(self, image: Image.Image, grid_size: int = 8) -> Image.Image:
        """Add semi-transparent light grey grid overlay for better sprite visibility"""
        overlay_image = image.copy().convert('RGBA')
        
        # Create a transparent overlay layer
        grid_overlay = Image.new('RGBA', overlay_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(grid_overlay)
        
        width, height = image.size
        tile_width = width // grid_size
        tile_height = height // grid_size
        
        # Draw semi-transparent light grey grid lines
        grid_color = (204, 204, 204, 100)  # Light grey with transparency
        for x in range(0, width, tile_width):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        
        for y in range(0, height, tile_height):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
        # Add coordinate labels with transparency
        try:
            font_size = max(8, min(12, tile_width // 4))
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        text_color = (204, 204, 204, 120)  # Light grey text with transparency
        for tile_x in range(grid_size):
            for tile_y in range(grid_size):
                pixel_x = tile_x * tile_width
                pixel_y = tile_y * tile_height
                
                coord_text = f"{tile_x},{tile_y}"
                draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill=text_color, font=font)
        
        # Composite the grid overlay onto the original image
        result = Image.alpha_composite(overlay_image, grid_overlay)
        return result.convert('RGB')
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image back to base64"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def call_pixtral_for_movement(self, prompt: str, image_base64: str) -> Dict:
        """Call Pixtral for movement analysis"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_base64,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=600
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "success": True,
                "response": response_text,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def parse_movement_response(self, response_text: str) -> Dict:
        """Parse AI response into structured movement data"""
        movement_data = {
            "location_class": "unknown",
            "valid_movements": [],
            "blocked_movements": [],
            "movement_reasons": {},
            "objects_detected": {
                "npcs": [],
                "buildings": [],
                "signs": [],
                "items": []
            },
            "movement_sequences": {
                "1_step": [],
                "2_step": [],
                "3_step": []
            }
        }
        
        response_lower = response_text.lower()
        
        # Extract location classification
        location_patterns = [
            (r"forest|wooded|tree", "forest"),
            (r"town|city|building", "town"),
            (r"route|path|road", "route"),
            (r"water|lake|river|pond", "water"),
            (r"cave|cavern", "cave"),
            (r"gym|center", "building")
        ]
        
        for pattern, classification in location_patterns:
            if re.search(pattern, response_lower):
                movement_data["location_class"] = classification
                break
        
        # Extract movement validations
        directions = ["up", "down", "left", "right"]
        
        for direction in directions:
            # Look for explicit movement statements
            valid_patterns = [
                rf"{direction}.*(?:walkable|clear|open|valid|can move|passable)",
                rf"(?:walkable|clear|open|valid|can move|passable).*{direction}",
                rf"{direction}.*allowed",
                rf"move {direction}"
            ]
            
            blocked_patterns = [
                rf"{direction}.*(?:blocked|unwalkable|tree|water|wall|obstacle)",
                rf"(?:blocked|unwalkable|tree|water|wall|obstacle).*{direction}",
                rf"{direction}.*not allowed",
                rf"cannot.*{direction}"
            ]
            
            is_valid = any(re.search(pattern, response_lower) for pattern in valid_patterns)
            is_blocked = any(re.search(pattern, response_lower) for pattern in blocked_patterns)
            
            if is_valid and not is_blocked:
                movement_data["valid_movements"].append(direction)
            elif is_blocked:
                movement_data["blocked_movements"].append(direction)
                
                # Extract reason for blocking
                for pattern in blocked_patterns:
                    match = re.search(pattern, response_lower)
                    if match:
                        context = match.group(0)
                        if "tree" in context:
                            movement_data["movement_reasons"][direction] = "tree"
                        elif "water" in context:
                            movement_data["movement_reasons"][direction] = "water"
                        elif "wall" in context:
                            movement_data["movement_reasons"][direction] = "wall"
                        else:
                            movement_data["movement_reasons"][direction] = "obstacle"
                        break
        
        # Extract object detections  
        # Find coordinate patterns in object sections
        coord_pattern = r'(\d+,\d+)'
        
        # NPCs
        npc_section = re.search(r'npcs?:.*?(?=\n\w+:|$)', response_lower, re.DOTALL)
        if npc_section:
            npc_coords = re.findall(coord_pattern, npc_section.group(0))
            movement_data["objects_detected"]["npcs"] = npc_coords
        
        # Buildings
        building_section = re.search(r'buildings?:.*?(?=\n\w+:|$)', response_lower, re.DOTALL)
        if building_section:
            building_coords = re.findall(coord_pattern, building_section.group(0))
            movement_data["objects_detected"]["buildings"] = building_coords
        
        # Signs
        sign_section = re.search(r'signs?:.*?(?=\n\w+:|$)', response_lower, re.DOTALL)
        if sign_section:
            sign_coords = re.findall(coord_pattern, sign_section.group(0))
            movement_data["objects_detected"]["signs"] = sign_coords
        
        # Items
        item_section = re.search(r'items?:.*?(?=\n\w+:|$)', response_lower, re.DOTALL)
        if item_section:
            item_coords = re.findall(coord_pattern, item_section.group(0))
            movement_data["objects_detected"]["items"] = item_coords
        
        # Add prompt mapping based on location class
        location_class = movement_data["location_class"]
        valid_movement_count = len(movement_data["valid_movements"])
        
        # Prompt mapping logic
        if valid_movement_count == 0:
            # Stuck - need recovery
            movement_data["recommended_prompt"] = "stuck_recovery"
            movement_data["prompt_reason"] = "No valid movements available - emergency recovery needed"
        elif location_class in ["forest", "route"]:
            # Overworld navigation/exploration
            movement_data["recommended_prompt"] = "exploration_strategy" 
            movement_data["prompt_reason"] = f"Overworld {location_class} area - navigation and exploration needed"
        elif location_class in ["town", "building"]:
            # Navigation in populated areas
            movement_data["recommended_prompt"] = "ai_navigation_with_memory_control"
            movement_data["prompt_reason"] = f"Urban {location_class} area - structured navigation needed"
        elif location_class == "cave":
            # Maze-like navigation
            movement_data["recommended_prompt"] = "ai_maze_with_solution_memory"
            movement_data["prompt_reason"] = "Cave environment - maze navigation with memory needed"
        elif location_class == "gym":
            # Battle preparation area
            movement_data["recommended_prompt"] = "battle_analysis"
            movement_data["prompt_reason"] = "Gym area - battle preparation and strategy needed"
        else:
            # Default fallback
            movement_data["recommended_prompt"] = "exploration_strategy"
            movement_data["prompt_reason"] = f"Unknown {location_class} area - default exploration strategy"
        
        return movement_data
    
    def test_movement_validation(self, image_base64: str, grid_size: int, test_name: str) -> Dict:
        """Test movement validation with specific grid size"""
        print(f"\n🧭 MOVEMENT VALIDATION - {test_name}")
        print("=" * 60)
        
        # Add grid overlay
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        grid_image = self.add_light_grey_grid(image, grid_size)
        
        # Save grid image
        safe_name = test_name.lower().replace(" ", "_")
        grid_path = self.overlay_dir / f"{safe_name}_grid.png"
        grid_image.save(grid_path)
        print(f"💾 Grid overlay saved to: {grid_path}")
        
        grid_base64 = self.image_to_base64(grid_image)
        
        # Movement validation prompt
        center_coord = f"{grid_size//2},{grid_size//2}"
        
        prompt = f"""POKEMON MOVEMENT VALIDATION ANALYSIS

You are analyzing a Pokemon overworld scene with {grid_size}x{grid_size} light grey grid overlay.

PLAYER POSITION: Center tile at coordinate ({center_coord})

CRITICAL GUIDANCE:
1. The player is currently standing on a WALKABLE surface (this is the reference)
2. If adjacent areas look SIMILAR to where the player is standing, they are also WALKABLE
3. Only mark as BLOCKED if there are clear DIFFERENT obstacles (trees, water, walls)

TERRAIN MATCHING STRATEGY:
- Look at the player's current tile - this shows what "walkable" looks like
- Compare adjacent tiles to the player's current position
- If adjacent terrain matches player's terrain = WALKABLE
- If adjacent terrain is clearly different (trees, water, walls) = BLOCKED

MOVEMENT ANALYSIS:
🔺 UP: Does the terrain above match the player's current terrain?
🔻 DOWN: Does the terrain below match the player's current terrain?
◀️ LEFT: Does the terrain to the left match the player's current terrain?
▶️ RIGHT: Does the terrain to the right match the player's current terrain?

OBJECT DETECTION PRIORITY:
Before answering, systematically examine EVERY tile in the 8x8 grid. Pay special attention to:
- Corner tiles: (0,0), (0,7), (7,0), (7,7)  
- RIGHT EDGE CRITICAL: Examine coordinates 7,0 through 7,7 very carefully for character sprites
- LEFT EDGE: Examine coordinates 0,0 through 0,7 for any sprites
- Look for human-shaped sprites, character figures, Pokemon trainers, or anything that differs from terrain
- NPCs may be small, colorful, or have different textures than trees/water/paths
- Check for any moving or animated elements that stand out

CLASSIFICATION RULES:
- WALKABLE: Terrain that matches where player is currently standing
- BLOCKED: Clearly different terrain (dense trees, blue water, solid walls)

REQUIRED RESPONSE FORMAT:
```
PLAYER_TERRAIN: [describe what the player is standing on]
LOCATION_CLASS: [forest/town/route/water/cave/building]

MOVEMENT_VALIDATION:
UP: [WALKABLE/BLOCKED] - [terrain comparison to player position]
DOWN: [WALKABLE/BLOCKED] - [terrain comparison to player position]
LEFT: [WALKABLE/BLOCKED] - [terrain comparison to player position]  
RIGHT: [WALKABLE/BLOCKED] - [terrain comparison to player position]

OBJECTS_DETECTED:
IMPORTANT: Scan the ENTIRE grid systematically from 0,0 to 7,7. Look carefully for:

NPCs: [CRITICAL: Examine each coordinate 0,0 through 7,7 systematically. List coordinates of ANY people/characters/trainers visible - they may be small sprites, different colored figures, human-like shapes, or Pokemon trainers. Pay extra attention to edges (coordinates with 0 or 7). Look for sprites that differ from background terrain, e.g., "2,3", "5,1", "7,4"]
Buildings: [list coordinates of buildings/structures/houses/doors, e.g., "1,0", "7,7"]  
Signs: [list coordinates of signs/posts/markers, e.g., "3,4"]
Items: [list coordinates of visible items/objects/pickups, e.g., "6,2"]

DETECTION TIPS:
- NPCs often appear as small human figures, different from terrain
- Check edge tiles (0,x and 7,x coordinates) especially carefully
- Look for sprites that stand out from background terrain  
- Characters may be facing different directions
- Don't miss partially visible objects at screen edges

MOVEMENT_SEQUENCES:
1_step_movements: [all valid single steps: "up", "down", "left", "right"]
2_step_combinations: [valid 2-step sequences: "up,left", "down,right", etc.]
3_step_paths: [valid 3-step paths before hitting obstacles: "up,up,left", etc.]

SUMMARY:
Valid directions: [directions with similar terrain to player]
Blocked directions: [directions with clearly different terrain]
Interactive objects: [total count of NPCs + buildings + signs + items]
Max movement depth: [how many steps possible before hitting obstacles]
```

Remember: The player can move on terrain similar to what they're currently standing on!"""
        
        result = self.call_pixtral_for_movement(prompt, grid_base64)
        
        if result["success"]:
            print(f"✅ Movement analysis received")
            
            # Parse structured movement data
            movement_data = self.parse_movement_response(result['response'])
            result["movement_data"] = movement_data
            result["grid_size"] = grid_size
            result["test_name"] = test_name
            
            # Display parsed results
            print(f"📍 Location: {movement_data['location_class']}")
            print(f"✅ Valid movements: {movement_data['valid_movements']}")
            print(f"❌ Blocked movements: {movement_data['blocked_movements']}")
            
            if movement_data['movement_reasons']:
                print(f"🚫 Block reasons: {movement_data['movement_reasons']}")
            
            # Display object detections
            objects = movement_data['objects_detected']
            total_objects = sum(len(obj_list) for obj_list in objects.values())
            if total_objects > 0:
                print(f"🎯 Objects detected: {total_objects}")
                for obj_type, coords in objects.items():
                    if coords:
                        print(f"   {obj_type}: {coords}")
            else:
                print("🎯 No interactive objects detected")
            
            # Display prompt recommendation
            recommended_prompt = movement_data.get('recommended_prompt', 'exploration_strategy')
            prompt_reason = movement_data.get('prompt_reason', 'Default recommendation')
            print(f"🤖 Recommended prompt: {recommended_prompt}")
            print(f"💡 Reason: {prompt_reason}")
            
        else:
            print(f"❌ Analysis failed: {result['error']}")
        
        return result
    
    def compare_grid_sizes(self, image_base64: str) -> None:
        """Compare 4x4 vs 8x8 grid movement validation"""
        print("\n🔄 GRID SIZE COMPARISON")
        print("=" * 60)
        
        # Test configurations
        test_configs = [
            {"grid_size": 4, "name": "Coarse 4x4 Grid"},
            {"grid_size": 8, "name": "Fine 8x8 Grid"}
        ]
        
        results = []
        
        for config in test_configs:
            try:
                result = self.test_movement_validation(
                    image_base64, 
                    config["grid_size"], 
                    config["name"]
                )
                results.append(result)
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Test '{config['name']}' failed: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "grid_size": config["grid_size"],
                    "test_name": config["name"]
                })
        
        # Analyze comparison
        self.analyze_grid_comparison(results)
        
        # Save results
        self.save_movement_results(results)
    
    def analyze_grid_comparison(self, results: List[Dict]) -> None:
        """Analyze which grid size provides better movement validation"""
        print("\n" + "=" * 70)
        print("🔄 GRID SIZE COMPARISON ANALYSIS")
        print("=" * 70)
        
        successful_results = [r for r in results if r.get("success", False)]
        
        if len(successful_results) < 2:
            print("❌ Need at least 2 successful tests for comparison")
            return
        
        print(f"✅ Comparing {len(successful_results)} grid configurations")
        
        # Compare movement detection accuracy
        for result in successful_results:
            movement_data = result.get("movement_data", {})
            grid_size = result.get("grid_size", "unknown")
            
            valid_count = len(movement_data.get("valid_movements", []))
            blocked_count = len(movement_data.get("blocked_movements", []))
            total_analyzed = valid_count + blocked_count
            
            print(f"\n📊 {grid_size}x{grid_size} Grid Results:")
            print(f"   Location: {movement_data.get('location_class', 'unknown')}")
            print(f"   Valid movements: {valid_count}")
            print(f"   Blocked movements: {blocked_count}")
            print(f"   Total analyzed: {total_analyzed}/4 directions")
            print(f"   Coverage: {(total_analyzed/4)*100:.1f}%")
        
        # Determine better configuration
        if len(successful_results) == 2:
            result_4x4 = next((r for r in successful_results if r.get("grid_size") == 4), None)
            result_8x8 = next((r for r in successful_results if r.get("grid_size") == 8), None)
            
            if result_4x4 and result_8x8:
                data_4x4 = result_4x4.get("movement_data", {})
                data_8x8 = result_8x8.get("movement_data", {})
                
                coverage_4x4 = len(data_4x4.get("valid_movements", [])) + len(data_4x4.get("blocked_movements", []))
                coverage_8x8 = len(data_8x8.get("valid_movements", [])) + len(data_8x8.get("blocked_movements", []))
                
                print(f"\n🏆 RECOMMENDATION:")
                if coverage_8x8 > coverage_4x4:
                    print("✅ 8x8 Grid provides better movement analysis")
                    print("   - Higher resolution for precise obstacle detection")
                    print("   - More detailed spatial understanding")
                elif coverage_4x4 > coverage_8x8:
                    print("✅ 4x4 Grid provides better movement analysis")
                    print("   - Simpler analysis with clearer results")
                    print("   - Less overwhelming for AI processing")
                else:
                    print("🤝 Both grids provide similar movement analysis")
                    print("   - Choice depends on performance requirements")
        
        print(f"\n💡 USAGE RECOMMENDATION:")
        print("For Eevee navigation system:")
        print("- Use the configuration with highest movement coverage")
        print("- Light grey overlay minimizes UI confusion")
        print("- Structured dictionary output ready for integration")
    
    def save_movement_results(self, results: List[Dict]) -> None:
        """Save movement validation results"""
        # JSON results in the overlay directory
        json_file = self.overlay_dir / "movement_validation_results.json"
        
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Human-readable output in the overlay directory
        output_file = self.overlay_dir / "movement_validation_output.txt"
        with open(output_file, 'w') as f:
            f.write("🧭 Pokemon Movement Validation Results\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"OVERLAY IMAGES: {self.overlay_dir}\n")
            f.write("-" * 60 + "\n\n")
            
            for result in results:
                if result.get("success", False):
                    movement_data = result.get("movement_data", {})
                    f.write(f"TEST: {result.get('test_name', 'Unknown')}\n")
                    f.write(f"GRID SIZE: {result.get('grid_size', 'Unknown')}x{result.get('grid_size', 'Unknown')}\n")
                    f.write(f"LOCATION CLASS: {movement_data.get('location_class', 'unknown')}\n")
                    f.write(f"VALID MOVEMENTS: {movement_data.get('valid_movements', [])}\n")
                    f.write(f"BLOCKED MOVEMENTS: {movement_data.get('blocked_movements', [])}\n")
                    f.write(f"BLOCK REASONS: {movement_data.get('movement_reasons', {})}\n")
                    
                    # Add object detection data
                    objects = movement_data.get('objects_detected', {})
                    total_objects = sum(len(obj_list) for obj_list in objects.values())
                    f.write(f"OBJECTS DETECTED: {total_objects}\n")
                    for obj_type, coords in objects.items():
                        if coords:
                            f.write(f"  {obj_type.upper()}: {coords}\n")
                    
                    # Add prompt recommendation
                    f.write(f"RECOMMENDED PROMPT: {movement_data.get('recommended_prompt', 'exploration_strategy')}\n")
                    f.write(f"PROMPT REASON: {movement_data.get('prompt_reason', 'Default recommendation')}\n")
                    
                    f.write("-" * 40 + "\n\n")
        
        print(f"\n💾 Results saved to: {json_file}")
        print(f"📝 Output saved to: {output_file}")
        print(f"🖼️ All files in directory: {self.overlay_dir}")
    
    def run_movement_validation_test(self) -> None:
        """Run complete movement validation comparison"""
        print("🧭 Pokemon Movement Validation Test")
        print("=" * 70)
        print("Comparing 4x4 vs 8x8 light grey grids for movement analysis")
        print("Goal: Structured dictionary output for Eevee navigation")
        print()
        
        # Check connection
        if not self.controller.is_connected():
            print("❌ Cannot connect to SkyEmu. Please ensure SkyEmu is running on port 8080.")
            return
        
        print("✅ SkyEmu connection verified")
        
        # Capture screenshot
        screenshot_base64 = self.capture_screenshot()
        if not screenshot_base64:
            print("❌ Failed to capture screenshot")
            return
        
        # Save original
        original_image = self.decode_base64_to_image(screenshot_base64)
        if original_image:
            original_path = self.overlay_dir / "original_screenshot.png"
            original_image.save(original_path)
            print(f"💾 Original screenshot saved to: {original_path}")
        
        # Compare grid sizes
        self.compare_grid_sizes(screenshot_base64)

def main():
    """Main movement validation test"""
    print("🧭 Pokemon Movement Validation Test")
    print("=" * 70)
    print("Testing optimal grid configuration for directional movement analysis")
    print()
    
    validator = MovementValidator()
    validator.run_movement_validation_test()
    
    print("\n✅ Movement validation test complete!")
    print("\nGenerated Dictionary Format:")
    print("{")
    print('  "location_class": "forest",')
    print('  "valid_movements": ["up", "right"],')
    print('  "blocked_movements": ["down", "left"],')
    print('  "movement_reasons": {"down": "water", "left": "tree"},')
    print('  "objects_detected": {"npcs": [], "buildings": [], "signs": [], "items": []},')
    print('  "recommended_prompt": "exploration_strategy",')
    print('  "prompt_reason": "Overworld forest area - navigation and exploration needed"')
    print("}")

if __name__ == "__main__":
    main()