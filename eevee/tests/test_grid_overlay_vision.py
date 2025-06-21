#!/usr/bin/env python3
"""
Grid Overlay Vision Test
Add visual grid overlays to help Pixtral understand Game Boy Advance screenshots
Based on videogamebench approach of adding coordinate grids
"""

import sys
import base64
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))                    # For eevee modules
sys.path.append(str(project_root))                  # For llm_api.py in root
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
    
    from dotenv import load_dotenv
    
    # Import centralized LLM API
    from llm_api import call_llm, get_llm_manager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

class GridOverlayTester:
    """Test Pixtral vision with grid overlays to improve spatial understanding"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.test_results: List[Dict] = []
        self.timestamp = int(time.time())
        
        # Create directory for overlay images
        self.overlay_dir = Path(__file__).parent / f"overlay_images_{self.timestamp}"
        self.overlay_dir.mkdir(exist_ok=True)
        
    def capture_screenshot(self) -> Optional[str]:
        """Capture screenshot and return base64"""
        try:
            screenshot_data = self.controller.get_screenshot_base64()
            if not screenshot_data:
                print("❌ Failed to capture screenshot")
                return None
                
            print(f"✅ Screenshot captured: {len(screenshot_data)} characters")
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
    
    def add_grid_overlay(self, image: Image.Image, grid_size: int = 20) -> Image.Image:
        """Add subtle coordinate grid overlay to minimize UI confusion"""
        # Scale up the image for better resolution and grid visibility
        scale_factor = 2
        width, height = image.size
        
        # Create high-resolution version
        high_res_image = image.resize((width * scale_factor, height * scale_factor), Image.Resampling.NEAREST)
        overlay_image = high_res_image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        scaled_width, scaled_height = high_res_image.size
        scaled_grid_size = grid_size * scale_factor
        
        # Draw subtle grid lines in blue to avoid confusion with game UI
        line_width = 1
        for x in range(0, scaled_width, scaled_grid_size):
            draw.line([(x, 0), (x, scaled_height)], fill='#4444FF', width=line_width)
        
        for y in range(0, scaled_height, scaled_grid_size):
            draw.line([(0, y), (scaled_width, y)], fill='#4444FF', width=line_width)
        
        # Try to load a smaller, less intrusive font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Add coordinate labels ONLY at strategic points to minimize confusion
        label_points = [
            (0, 0),                                    # Top-left
            (scaled_width//2, 0),                      # Top-center  
            (scaled_width-1, 0),                       # Top-right
            (0, scaled_height//2),                     # Middle-left
            (scaled_width//2, scaled_height//2),       # Center
            (scaled_width-1, scaled_height//2),        # Middle-right
            (0, scaled_height-1),                      # Bottom-left
            (scaled_width//2, scaled_height-1),        # Bottom-center
            (scaled_width-1, scaled_height-1)          # Bottom-right
        ]
        
        for x, y in label_points:
            # Convert back to original coordinates for labeling
            orig_x = x // scale_factor
            orig_y = y // scale_factor
            coord_text = f"{orig_x},{orig_y}"
            
            # Add semi-transparent background for better visibility
            if font:
                bbox = draw.textbbox((0, 0), coord_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = 30, 8
            
            # Position text with offset from edges
            text_x = max(2, min(x - text_width//2, scaled_width - text_width - 2))
            text_y = max(2, min(y - text_height//2, scaled_height - text_height - 2))
            
            # Draw subtle background
            draw.rectangle([text_x-1, text_y-1, text_x + text_width + 1, text_y + text_height + 1], 
                         fill='#FFFFCC', outline='#888888', width=1)
            
            # Draw coordinate text in dark blue
            if font:
                draw.text((text_x, text_y), coord_text, fill='#000088', font=font)
            else:
                draw.text((text_x, text_y), coord_text, fill='#000088')
        
        return overlay_image
    
    def add_game_boy_grid(self, image: Image.Image) -> Image.Image:
        """Add 8x8 tile grid overlay specific to Game Boy Advance games"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        width, height = image.size
        
        # Game Boy Advance typically uses 8x8 tile system
        tile_width = width // 8
        tile_height = height // 8
        
        # Draw tile boundaries in green
        for x in range(0, width, tile_width):
            draw.line([(x, 0), (x, height)], fill='green', width=1)
        
        for y in range(0, height, tile_height):
            draw.line([(0, y), (width, y)], fill='green', width=1)
        
        # Add tile coordinate labels
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        for tile_x in range(8):
            for tile_y in range(8):
                pixel_x = tile_x * tile_width
                pixel_y = tile_y * tile_height
                
                # Label each tile with its grid position
                tile_label = f"T{tile_x},{tile_y}"
                if font:
                    draw.text((pixel_x + 2, pixel_y + 2), tile_label, fill='green', font=font)
                else:
                    draw.text((pixel_x + 2, pixel_y + 2), tile_label, fill='green')
        
        return overlay_image
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image back to base64"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def call_pixtral_with_image(self, prompt: str, image_base64: str) -> Dict:
        """Call Pixtral with the provided image"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_base64,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=300
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
    
    def test_no_overlay(self, image_base64: str) -> Dict:
        """Test 1: Original image with no overlay"""
        print("\n📸 TEST 1: No Overlay (Original)")
        print("=" * 50)
        
        # Save original image
        image = self.decode_base64_to_image(image_base64)
        if image:
            image_path = self.overlay_dir / "original_no_overlay.png"
            image.save(image_path)
            print(f"💾 Original image saved to: {image_path}")
        
        prompt = "Look at this Pokemon overworld screenshot. The player character is in the center, surrounded by a grid-based movement system. Each button press moves the player one square. There are NO health bars or battle elements - the player is exploring the overworld. Can you identify if this is an overworld navigation scene (walking around) vs a menu/battle scene? What do you see?"
        
        result = self.call_pixtral_with_image(prompt, image_base64)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            result["sees_battle_elements"] = "yes" in result['response'].lower()
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "no_overlay"
        result["overlay_type"] = "none"
        return result
    
    def test_coordinate_grid(self, image_base64: str) -> Dict:
        """Test 2: Image with coordinate grid overlay"""
        print("\n🟩 TEST 2: Coordinate Grid Overlay")
        print("=" * 50)
        
        # Decode, add grid, re-encode
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        grid_image = self.add_grid_overlay(image, grid_size=40)
        
        # Save overlay image
        overlay_path = self.overlay_dir / "coordinate_grid_overlay.png"
        grid_image.save(overlay_path)
        print(f"💾 Grid overlay image saved to: {overlay_path}")
        
        grid_base64 = self.image_to_base64(grid_image)
        
        prompt = "This Pokemon overworld scene has debug coordinate grid overlay (blue lines with labels). The grid is NOT part of the game - it's analysis overlay. The player character is in the center and moves one square per button press. There are NO health bars in this overworld scene. Can you: 1) Identify which direction the player can move (look for walkable paths vs blocked areas), 2) Describe the terrain around the player using coordinate references, 3) Confirm this is overworld navigation (not battle/menu)?"
        
        result = self.call_pixtral_with_image(prompt, grid_base64)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            result["sees_battle_elements"] = "yes" in result['response'].lower()
            result["uses_coordinates"] = any(coord in result['response'].lower() for coord in ['(', ')', 'coordinate', 'grid'])
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "coordinate_grid"
        result["overlay_type"] = "coordinate_grid"
        return result
    
    def test_game_boy_tiles(self, image_base64: str) -> Dict:
        """Test 3: Image with Game Boy tile grid"""
        print("\n🎮 TEST 3: Game Boy Tile Grid Overlay")
        print("=" * 50)
        
        # Decode, add game boy grid, re-encode
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        tile_image = self.add_game_boy_grid(image)
        
        # Save tile overlay image
        tile_path = self.overlay_dir / "game_boy_tile_overlay.png"
        tile_image.save(tile_path)
        print(f"💾 Tile overlay image saved to: {tile_path}")
        
        tile_base64 = self.image_to_base64(tile_image)
        
        prompt = "This Pokemon overworld scene has Game Boy tile grid overlay (green lines, T0,0 to T7,7). This grid shows the 8x8 tile movement system - each tile is one movement square. The overlay is debug information, NOT game UI. The player character is at the center tile and can move one tile per button press. There are NO health bars or battle elements in overworld scenes. Can you: 1) Identify which tiles the player can walk to (open paths), 2) Which tiles are blocked (trees, water, walls), 3) What direction has the clearest path for movement?"
        
        result = self.call_pixtral_with_image(prompt, tile_base64)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            result["sees_battle_elements"] = "yes" in result['response'].lower()
            result["uses_tile_coords"] = any(tile in result['response'].lower() for tile in ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 'tile'])
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "game_boy_tiles"
        result["overlay_type"] = "tile_grid"
        return result
    
    def test_direct_coordinate_question(self, image_base64: str) -> Dict:
        """Test 4: Ask about specific coordinates"""
        print("\n📍 TEST 4: Direct Coordinate Questions")
        print("=" * 50)
        
        # Add coordinate grid
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        grid_image = self.add_grid_overlay(image, grid_size=40)
        
        # Save coordinate question overlay
        coord_path = self.overlay_dir / "coordinate_questions_overlay.png"
        grid_image.save(coord_path)
        print(f"💾 Coordinate grid image saved to: {coord_path}")
        
        grid_base64 = self.image_to_base64(grid_image)
        
        prompt = "This Pokemon overworld scene has debug coordinate overlay (blue grid). Remember: 1) This is overworld navigation, NOT battle, 2) Grid overlay is debug info, not game UI, 3) Player moves one square per button press, 4) NO health bars exist in overworld. Using coordinate references, answer: 1) Where is the player character located? 2) Which coordinates show walkable paths? 3) Which coordinates are blocked by obstacles? 4) What's the best movement direction from current position? Focus on navigation, not battle elements."
        
        result = self.call_pixtral_with_image(prompt, grid_base64)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            result["sees_battle_elements"] = "health" in result['response'].lower() or "menu" in result['response'].lower()
            result["answers_coordinates"] = any(coord in result['response'] for coord in ['(0,0)', '(120,80)', 'coordinate'])
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "coordinate_questions"
        result["overlay_type"] = "coordinate_grid"
        return result
    
    def test_path_detection(self, image_base64: str) -> Dict:
        """Test 5: Focus purely on navigation path detection"""
        print("\n🧭 TEST 5: Navigation Path Detection")
        print("=" * 50)
        
        # Add Game Boy grid for movement analysis
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        tile_image = self.add_game_boy_grid(image)
        
        # Save path detection overlay
        path_path = self.overlay_dir / "path_detection_overlay.png"
        tile_image.save(path_path)
        print(f"💾 Path detection image saved to: {path_path}")
        
        tile_base64 = self.image_to_base64(tile_image)
        
        prompt = """NAVIGATION ANALYSIS: You are looking at a Pokemon overworld scene with tile grid overlay. Your job is to help navigate.

IMPORTANT FACTS:
- Player character is in the center
- Each tile = one movement step (up/down/left/right button press)
- Green grid shows movement tiles, NOT game UI
- This is overworld exploration, NOT battle
- NO health bars exist in overworld scenes

ANALYSIS TASK:
1. Identify player location (which tile)
2. List walkable directions: UP, DOWN, LEFT, RIGHT (which are open paths?)
3. List blocked directions (trees, water, walls, NPCs)
4. Recommend best movement direction for exploration
5. Describe terrain type (forest, town, route, building)

Focus on MOVEMENT POSSIBILITIES, not fictional battle elements."""
        
        result = self.call_pixtral_with_image(prompt, tile_base64)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            # Check if focuses on navigation vs battle
            response_lower = result['response'].lower()
            result["focuses_on_navigation"] = any(word in response_lower for word in ['walkable', 'movement', 'direction', 'path', 'blocked'])
            result["mentions_health_bars"] = any(word in response_lower for word in ['health', 'hp', 'battle', 'combat'])
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "path_detection"
        result["overlay_type"] = "navigation_grid"
        return result
    
    def run_grid_overlay_tests(self) -> None:
        """Run all grid overlay tests"""
        print("🟩 Grid Overlay Vision Testing")
        print("=" * 60)
        print("Testing if grid overlays help Pixtral understand Game Boy screenshots")
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
        
        # Run all tests
        test_methods = [
            ("No Overlay", self.test_no_overlay),
            ("Coordinate Grid", self.test_coordinate_grid),
            ("Game Boy Tiles", self.test_game_boy_tiles), 
            ("Direct Coordinates", self.test_direct_coordinate_question),
            ("Path Detection", self.test_path_detection)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method(screenshot_base64)
                self.test_results.append(result)
                
                # Brief pause between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Test '{test_name}' failed: {e}")
                self.test_results.append({
                    "test_name": test_name.lower().replace(" ", "_"),
                    "success": False,
                    "error": str(e)
                })
        
        # Analyze results
        self.analyze_grid_overlay_results()
    
    def analyze_grid_overlay_results(self) -> None:
        """Analyze if grid overlays help Pixtral accuracy"""
        print("\n" + "=" * 80)
        print("🟩 GRID OVERLAY ANALYSIS")
        print("=" * 80)
        
        successful_tests = [r for r in self.test_results if r.get("success", False)]
        
        if not successful_tests:
            print("❌ No successful tests to analyze")
            return
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(self.test_results)}")
        
        # Analyze battle element detection
        print(f"\n🔍 BATTLE ELEMENT DETECTION:")
        
        for test in successful_tests:
            test_name = test.get("test_name", "unknown")
            overlay_type = test.get("overlay_type", "unknown")
            sees_battle = test.get("sees_battle_elements", False)
            
            if sees_battle:
                print(f"   ⚠️ {test_name} ({overlay_type}): Claims to see battle elements")
            else:
                print(f"   ✅ {test_name} ({overlay_type}): No false battle detection")
        
        # Analyze coordinate usage
        print(f"\n📍 COORDINATE SYSTEM USAGE:")
        
        coord_tests = [t for t in successful_tests if "uses_coordinates" in t or "uses_tile_coords" in t]
        
        for test in coord_tests:
            test_name = test.get("test_name", "unknown")
            uses_coords = test.get("uses_coordinates", False) or test.get("uses_tile_coords", False)
            
            if uses_coords:
                print(f"   ✅ {test_name}: Uses coordinate references")
            else:
                print(f"   ⚠️ {test_name}: Ignores coordinate system")
        
        # Overall assessment
        print(f"\n🎯 GRID OVERLAY ASSESSMENT:")
        
        battle_detection_count = sum(1 for t in successful_tests if t.get("sees_battle_elements", False))
        coord_usage_count = sum(1 for t in successful_tests if t.get("uses_coordinates", False) or t.get("uses_tile_coords", False))
        
        if battle_detection_count == 0:
            print("✅ SUCCESS: Grid overlays eliminated false battle detection!")
            print("   - Pixtral no longer hallucinates battle elements")
            print("   - Grid coordinates help provide spatial context")
        elif battle_detection_count < len(successful_tests):
            print("⚠️ PARTIAL SUCCESS: Some overlays help reduce hallucinations")
            print(f"   - {len(successful_tests) - battle_detection_count} tests showed no false detection")
            print(f"   - {battle_detection_count} tests still detected false battles")
        else:
            print("❌ NO IMPROVEMENT: Grid overlays don't help")
            print("   - Pixtral still hallucinates battle elements with grids")
            print("   - The issue may be deeper than spatial understanding")
        
        if coord_usage_count > 0:
            print(f"✅ SPATIAL IMPROVEMENT: {coord_usage_count} tests used coordinate references")
            print("   - Grid overlays provide spatial context to Pixtral")
        else:
            print("⚠️ LIMITED SPATIAL IMPACT: Pixtral ignores coordinate overlays")
        
        # Save results
        self.save_grid_test_results()
    
    def save_grid_test_results(self) -> None:
        """Save test results with overlay images"""
        results_file = Path(__file__).parent / f"grid_overlay_results_{self.timestamp}.json"
        output_file = Path(__file__).parent / "grid_overlay_output.txt"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Also save to always-available output file (overwrite)
        with open(output_file, 'w') as f:
            f.write("🟩 Grid Overlay Vision Test Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"OVERLAY IMAGES SAVED TO: {self.overlay_dir}\n")
            f.write("-" * 50 + "\n\n")
            
            for result in self.test_results:
                if result.get("success", False):
                    f.write(f"TEST: {result.get('test_name', 'unknown')}\n")
                    f.write(f"OVERLAY: {result.get('overlay_type', 'none')}\n")
                    f.write(f"RESPONSE: {result.get('response', 'N/A')}\n")
                    f.write(f"HALLUCINATIONS: {result.get('found_keywords', [])}\n")
                    f.write("-" * 30 + "\n\n")
        
        print(f"\n💾 Grid overlay test results saved to: {results_file}")
        print(f"📝 Output also saved to: {output_file}")
        print(f"🖼️ Overlay images saved to: {self.overlay_dir}")

def main():
    """Main test execution"""
    print("🟩 Grid Overlay Vision Testing for Pixtral")
    print("=" * 60)
    print("Based on videogamebench approach:")
    print("- Add coordinate grids to help vision models understand spatial layout")
    print("- Test if overlays reduce Pokemon battle hallucinations")
    print("- Compare different overlay types (coordinates vs game tiles)")
    print()
    
    # Run tests
    tester = GridOverlayTester()
    tester.run_grid_overlay_tests()
    
    print("\n✅ Grid overlay testing complete!")
    print("\nKey Research:")
    print("1. Do coordinate grids help Pixtral understand the game screen?")
    print("2. Do Game Boy tile grids reduce false battle detection?")
    print("3. Can spatial overlays eliminate the 'health bar' hallucinations?")

if __name__ == "__main__":
    main()