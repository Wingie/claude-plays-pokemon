#!/usr/bin/env python3
"""
Visual Analysis Test with Movement Sequence Planning
Uses Pixtral to generate valid movement sequences with strategic reasoning
Returns structured tuples for easy storage and integration
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

class VisualAnalysis:
    """Visual analysis system with movement sequence planning using Pixtral"""
    
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
        """Parse AI response into structured movement data with sequences as tuples"""
        movement_data = {
            "location_class": "unknown",
            "valid_sequences": {
                "1_move": [],
                "2_move": [],
                "3_move": [],
                "4_move": []
            },
            "objects_detected": {
                "npcs": [],
                "buildings": [],
                "signs": [],
                "items": []
            },
            "recommended_prompt": "exploration_strategy",
            "prompt_reason": "Default recommendation"
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
        
        # Extract movement sequences using regex
        # Pattern to match tuples like ("U_L", "reason")
        sequence_pattern = r'\("([UDLR_]+)",\s*"([^"]+)"\)'
        
        # Find all sequence matches
        for match in re.finditer(sequence_pattern, response_text):
            sequence = match.group(1)
            reason = match.group(2)
            
            # Categorize by length
            move_count = len(sequence.split('_'))
            if move_count == 1:
                movement_data["valid_sequences"]["1_move"].append((sequence, reason))
            elif move_count == 2:
                movement_data["valid_sequences"]["2_move"].append((sequence, reason))
            elif move_count == 3:
                movement_data["valid_sequences"]["3_move"].append((sequence, reason))
            elif move_count == 4:
                movement_data["valid_sequences"]["4_move"].append((sequence, reason))
        
        # Extract object detections with new format
        # Find coordinate patterns in object sections
        coord_pattern = r'(\d+,\d+)'
        
        # Characters (was NPCs)
        char_section = re.search(r'characters?:.*?(?=\n\w+:|$)', response_lower, re.DOTALL)
        if char_section:
            char_coords = re.findall(coord_pattern, char_section.group(0))
            movement_data["objects_detected"]["npcs"] = char_coords
        
        # Structures (was Buildings)
        struct_section = re.search(r'structures?:.*?(?=\n\w+:|$)', response_lower, re.DOTALL)
        if struct_section:
            struct_coords = re.findall(coord_pattern, struct_section.group(0))
            movement_data["objects_detected"]["buildings"] = struct_coords
        
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
        
        # Add prompt mapping based on location class and movement availability
        location_class = movement_data["location_class"]
        total_sequences = sum(len(seqs) for seqs in movement_data["valid_sequences"].values())
        
        # Prompt mapping logic
        if total_sequences == 0:
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
        
        # Movement sequence planning prompt
        center_coord = f"{grid_size//2},{grid_size//2}"
        
        prompt = f"""VISUAL TERRAIN ANALYSIS

You are analyzing a screenshot with a {grid_size}x{grid_size} coordinate grid overlay.
Your task is to describe ONLY what you actually see, without making assumptions.

COORDINATE SYSTEM:
- U = Up (toward 0 on Y-axis)
- D = Down (toward {grid_size-1} on Y-axis)  
- L = Left (toward 0 on X-axis)
- R = Right (toward {grid_size-1} on X-axis)
- Player position: Center at ({center_coord})

CRITICAL: DESCRIBE ONLY WHAT YOU ACTUALLY SEE
Do not assume this is any specific type of game or location.
Do not invent objects, characters, or destinations that aren't clearly visible.

TERRAIN ANALYSIS TASK:
Look at the terrain around the center position and determine which directions have similar, walkable-looking terrain.

MOVEMENT VALIDATION:
From the center position, analyze each direction:
- UP: What type of terrain/surface do you see?
- DOWN: What type of terrain/surface do you see?
- LEFT: What type of terrain/surface do you see?
- RIGHT: What type of terrain/surface do you see?

SEQUENCE GENERATION:
Only generate sequences where you can visually trace the path on similar terrain.

REQUIRED RESPONSE FORMAT:
```
VISUAL_DESCRIPTION: [What you actually see in the image - terrain, colors, patterns]
LOCATION_TYPE: [describe the visual environment - grassy, rocky, paved, etc.]

TERRAIN_ANALYSIS:
UP: [describe actual visible terrain] - [WALKABLE/BLOCKED]
DOWN: [describe actual visible terrain] - [WALKABLE/BLOCKED]  
LEFT: [describe actual visible terrain] - [WALKABLE/BLOCKED]
RIGHT: [describe actual visible terrain] - [WALKABLE/BLOCKED]

VALID_SEQUENCES:
1_MOVE:
- ("U", "Similar terrain continues upward")
- ("D", "Same surface type extends downward")
- ("L", "Consistent terrain to the left")
- ("R", "Matching surface to the right")

2_MOVE:
- ("U_L", "Two-step path on similar terrain")
- ("U_R", "Diagonal path through consistent surface")
[Only include sequences you can visually verify]

OBJECTS_VISIBLE:
[ONLY list objects you can clearly see - be very conservative]
Characters: [coordinate if you see clear human/character shapes]
Structures: [coordinate if you see clear building/structure shapes]  
Signs: [coordinate if you see clear sign/post shapes]
Items: [coordinate if you see clear item/object shapes]
```

VALIDATION RULES:
- Only suggest moves on terrain that looks similar to the center position
- Only list objects you can clearly and confidently identify
- Be conservative - if unsure, don't include it
- Focus on actual visual terrain matching, not game assumptions"""
        
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
            
            # Display movement sequences
            print(f"\n🎮 MOVEMENT SEQUENCES:")
            
            sequences = movement_data['valid_sequences']
            
            # 1-move options
            if sequences['1_move']:
                print(f"\n1-MOVE OPTIONS ({len(sequences['1_move'])}):")
                for seq, reason in sequences['1_move']:
                    print(f"  ✓ {seq} - {reason}")
            
            # 2-move combos
            if sequences['2_move']:
                print(f"\n2-MOVE COMBOS ({len(sequences['2_move'])}):")
                for seq, reason in sequences['2_move']:
                    print(f"  ➤ {seq} - {reason}")
            
            # 3-move paths
            if sequences['3_move']:
                print(f"\n3-MOVE PATHS ({len(sequences['3_move'])}):")
                for seq, reason in sequences['3_move']:
                    print(f"  🎯 {seq} - {reason}")
            
            # 4-move sequences
            if sequences['4_move']:
                print(f"\n4-MOVE SEQUENCES ({len(sequences['4_move'])}):")
                for seq, reason in sequences['4_move']:
                    print(f"  🚀 {seq} - {reason}")
            
            # Display object detections
            objects = movement_data['objects_detected']
            total_objects = sum(len(obj_list) for obj_list in objects.values())
            if total_objects > 0:
                print(f"\n🎯 Objects detected: {total_objects}")
                for obj_type, coords in objects.items():
                    if coords:
                        print(f"   {obj_type}: {coords}")
            else:
                print("\n🎯 No interactive objects detected")
            
            # Display prompt recommendation
            recommended_prompt = movement_data.get('recommended_prompt', 'exploration_strategy')
            prompt_reason = movement_data.get('prompt_reason', 'Default recommendation')
            print(f"\n🤖 Recommended prompt: {recommended_prompt}")
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
            sequences = movement_data.get("valid_sequences", {})
            
            total_sequences = sum(len(seqs) for seqs in sequences.values())
            
            print(f"\n📊 {grid_size}x{grid_size} Grid Results:")
            print(f"   Location: {movement_data.get('location_class', 'unknown')}")
            print(f"   Total sequences generated: {total_sequences}")
            print(f"   - 1-move: {len(sequences.get('1_move', []))}")
            print(f"   - 2-move: {len(sequences.get('2_move', []))}")
            print(f"   - 3-move: {len(sequences.get('3_move', []))}")
            print(f"   - 4-move: {len(sequences.get('4_move', []))}")
        
        # Determine better configuration
        if len(successful_results) == 2:
            result_4x4 = next((r for r in successful_results if r.get("grid_size") == 4), None)
            result_8x8 = next((r for r in successful_results if r.get("grid_size") == 8), None)
            
            if result_4x4 and result_8x8:
                data_4x4 = result_4x4.get("movement_data", {})
                data_8x8 = result_8x8.get("movement_data", {})
                
                sequences_4x4 = sum(len(seqs) for seqs in data_4x4.get("valid_sequences", {}).values())
                sequences_8x8 = sum(len(seqs) for seqs in data_8x8.get("valid_sequences", {}).values())
                
                print(f"\n🏆 RECOMMENDATION:")
                if sequences_8x8 > sequences_4x4:
                    print("✅ 8x8 Grid provides better movement analysis")
                    print("   - Higher resolution for precise path planning")
                    print("   - More detailed movement sequences generated")
                elif sequences_4x4 > sequences_8x8:
                    print("✅ 4x4 Grid provides better movement analysis")
                    print("   - Simpler analysis with clearer path reasoning")
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
            f.write("🧭 Pokemon Visual Analysis Results with Movement Sequences\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"OVERLAY IMAGES: {self.overlay_dir}\n")
            f.write("-" * 60 + "\n\n")
            
            for result in results:
                if result.get("success", False):
                    movement_data = result.get("movement_data", {})
                    f.write(f"TEST: {result.get('test_name', 'Unknown')}\n")
                    f.write(f"GRID SIZE: {result.get('grid_size', 'Unknown')}x{result.get('grid_size', 'Unknown')}\n")
                    f.write(f"LOCATION CLASS: {movement_data.get('location_class', 'unknown')}\n")
                    
                    # Summary of valid movements (simplified)
                    sequences = movement_data.get('valid_sequences', {})
                    simple_movements = [move for move, _ in sequences.get('1_move', [])]
                    f.write(f"VALID MOVEMENTS: {simple_movements}\n")
                    
                    # Objects summary
                    objects = movement_data.get('objects_detected', {})
                    total_objects = sum(len(obj_list) for obj_list in objects.values())
                    f.write(f"OBJECTS DETECTED: {total_objects}\n")
                    for obj_type, coords in objects.items():
                        if coords:
                            f.write(f"  {obj_type.upper()}: {coords}\n")
                    
                    f.write(f"RECOMMENDED PROMPT: {movement_data.get('recommended_prompt', 'exploration_strategy')}\n")
                    f.write(f"PROMPT REASON: {movement_data.get('prompt_reason', 'Default recommendation')}\n")
                    f.write("-" * 40 + "\n\n")
                    
                    # Write detailed movement sequences
                    f.write(f"DETAILED MOVEMENT SEQUENCES:\n")
                    
                    # 1-move
                    if sequences.get('1_move'):
                        f.write(f"1-MOVE ({len(sequences['1_move'])}):\n")
                        for seq, reason in sequences['1_move']:
                            f.write(f"  ✓ {seq} - {reason}\n")
                    
                    # 2-move
                    if sequences.get('2_move'):
                        f.write(f"\n2-MOVE ({len(sequences['2_move'])}):\n")
                        for seq, reason in sequences['2_move']:
                            f.write(f"  ➤ {seq} - {reason}\n")
                    
                    # 3-move
                    if sequences.get('3_move'):
                        f.write(f"\n3-MOVE ({len(sequences['3_move'])}):\n")
                        for seq, reason in sequences['3_move']:
                            f.write(f"  🎯 {seq} - {reason}\n")
                    
                    # 4-move
                    if sequences.get('4_move'):
                        f.write(f"\n4-MOVE ({len(sequences['4_move'])}):\n")
                        for seq, reason in sequences['4_move']:
                            f.write(f"  🚀 {seq} - {reason}\n")
                    
                    # Add raw AI response at the end
                    if 'response' in result:
                        f.write(f"\n--- RAW AI RESPONSE ---\n")
                        f.write(result['response'])
                        f.write(f"\n--- END RAW RESPONSE ---\n")
                    
                    f.write("\n" + "=" * 80 + "\n\n")
                else:
                    # Save failed results too
                    f.write(f"TEST: {result.get('test_name', 'Unknown')} - FAILED\n")
                    f.write(f"ERROR: {result.get('error', 'Unknown error')}\n")
                    f.write("-" * 80 + "\n\n")
        
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
    """Main visual analysis test with movement sequences"""
    print("🧭 Pokemon Visual Analysis Test with Movement Sequences")
    print("=" * 70)
    print("Testing Pixtral's ability to generate strategic movement sequences")
    print()
    
    validator = VisualAnalysis()
    validator.run_movement_validation_test()
    
    print("\n✅ Visual analysis test complete!")
    print("\nGenerated Dictionary Format:")
    print("{")
    print('  "location_class": "forest",')
    print('  "valid_sequences": {')
    print('    "1_move": [("U", "Clear path north"), ("R", "Open route east")],')
    print('    "2_move": [("U_L", "Reach item"), ("R_D", "Follow path")],')
    print('    "3_move": [("U_U_L", "To Pokemon Center"), ("R_D_L", "Around water")],')
    print('    "4_move": [("L_L_U_U", "Complex path to shop")]')
    print('  },')
    print('  "objects_detected": {"npcs": ["2,3"], "buildings": ["7,7"]},')
    print('  "recommended_prompt": "exploration_strategy",')
    print('  "prompt_reason": "Overworld forest area - navigation needed"')
    print("}")

if __name__ == "__main__":
    main()