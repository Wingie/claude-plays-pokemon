#!/usr/bin/env python3
"""
Game Boy Tile Overlay Variations Test
Test different tile overlay colors and sizes to minimize hallucinations
Focus on explaining Pokemon environment mechanics
"""

import sys
import base64
import json
import time
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

class TileOverlayTester:
    """Test different tile overlay configurations to minimize hallucinations"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.test_results: List[Dict] = []
        self.timestamp = int(time.time())
        
        # Create directory for overlay images
        self.overlay_dir = Path(__file__).parent / f"tile_variations_{self.timestamp}"
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
    
    def add_tile_overlay(self, image: Image.Image, grid_size: int = 8, 
                        color: str = "green", line_width: int = 1, 
                        add_labels: bool = True) -> Image.Image:
        """Add customizable Game Boy tile overlay"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        width, height = image.size
        
        # Calculate tile dimensions
        tile_width = width // grid_size
        tile_height = height // grid_size
        
        # Draw tile boundaries
        for x in range(0, width, tile_width):
            draw.line([(x, 0), (x, height)], fill=color, width=line_width)
        
        for y in range(0, height, tile_height):
            draw.line([(0, y), (width, y)], fill=color, width=line_width)
        
        # Add tile coordinate labels if requested
        if add_labels:
            try:
                font_size = max(8, min(12, tile_width // 4))
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            for tile_x in range(grid_size):
                for tile_y in range(grid_size):
                    pixel_x = tile_x * tile_width
                    pixel_y = tile_y * tile_height
                    
                    # Label each tile with its grid position
                    tile_label = f"T{tile_x},{tile_y}"
                    
                    # Just draw text directly without white background
                    draw.text((pixel_x + 2, pixel_y + 2), tile_label, fill=color, font=font)
        
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
                max_tokens=500
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
    
    def test_tile_variation(self, image_base64: str, config: Dict) -> Dict:
        """Test a specific tile overlay configuration"""
        test_name = config["name"]
        print(f"\n🎮 TEST: {test_name}")
        print("=" * 60)
        
        # Decode and add overlay
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        overlay_image = self.add_tile_overlay(
            image,
            grid_size=config.get("grid_size", 8),
            color=config.get("color", "green"),
            line_width=config.get("line_width", 1),
            add_labels=config.get("add_labels", True)
        )
        
        # Save overlay image
        safe_name = test_name.lower().replace(" ", "_").replace("/", "_")
        overlay_path = self.overlay_dir / f"{safe_name}_overlay.png"
        overlay_image.save(overlay_path)
        print(f"💾 {test_name} overlay saved to: {overlay_path}")
        
        overlay_base64 = self.image_to_base64(overlay_image)
        
        # Universal Pokemon environment explanation prompt
        prompt = f"""POKEMON OVERWORLD ENVIRONMENT ANALYSIS

You are analyzing a Pokemon overworld scene with {config.get('color', 'colored')} tile grid overlay.

CRITICAL UNDERSTANDING:
1. This is Pokemon OVERWORLD exploration, NOT a battle scene
2. The grid overlay is DEBUG INFORMATION added for analysis - NOT part of the game
3. There are NO health bars, HP displays, or battle UI in overworld scenes
4. The player character moves tile-by-tile through the environment

HOW POKEMON ENVIRONMENTS WORK:
- Player character starts at center and moves one tile per button press
- Trees, water, walls, and buildings BLOCK movement
- Grass, paths, and open areas ALLOW movement  
- NPCs (other characters) may block or allow interaction
- Some tiles have special functions (doors, items, encounters)

ANALYSIS TASK:
1. Scene Type: What kind of Pokemon area is this? (forest, town, route, cave, building)
2. Player Location: Describe where the player character is positioned
3. Terrain Elements: Identify trees, water, paths, buildings, NPCs
4. Movement Options: Which directions can the player move?
5. Environment Description: What would a Pokemon trainer see here?

IMPORTANT: Focus on the actual Pokemon world environment. The {config.get('color', 'colored')} grid is just analysis overlay - ignore it as game UI.

Describe what you actually see in this Pokemon world location."""
        
        result = self.call_pixtral_with_image(prompt, overlay_base64)
        
        if result["success"]:
            print(f"✅ Response: {result['response'][:200]}...")
            
            # Analyze response for hallucinations
            response_lower = result['response'].lower()
            
            # Check for battle element hallucinations
            battle_keywords = ['health bar', 'hp bar', 'health point', 'battle interface', 
                             'combat ui', 'battle menu', 'fight menu', 'pokemon battle']
            health_mentions = sum(1 for keyword in battle_keywords if keyword in response_lower)
            
            # Check for proper environment focus
            env_keywords = ['tree', 'water', 'path', 'grass', 'building', 'npc', 
                           'movement', 'tile', 'direction', 'terrain', 'area']
            env_mentions = sum(1 for keyword in env_keywords if keyword in response_lower)
            
            # Check for grid overlay confusion
            grid_keywords = ['grid', 'overlay', 'debug', 'analysis']
            grid_mentions = sum(1 for keyword in grid_keywords if keyword in response_lower)
            
            result.update({
                "config": config,
                "health_bar_mentions": health_mentions,
                "environment_focus": env_mentions,
                "grid_confusion": grid_mentions,
                "response_length": len(result['response']),
                "test_name": test_name
            })
            
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def run_tile_variation_tests(self) -> None:
        """Run comprehensive tile overlay variation tests"""
        print("🎮 Game Boy Tile Overlay Variation Testing")
        print("=" * 70)
        print("Testing different colors, sizes, and styles to minimize hallucinations")
        print("Focus: Pokemon environment understanding with minimal UI confusion")
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
        
        # Test configurations
        test_configs = [
            {
                "name": "Original Green 8x8",
                "grid_size": 8,
                "color": "green",
                "line_width": 1,
                "add_labels": True
            },
            {
                "name": "Subtle Blue 8x8",
                "grid_size": 8,
                "color": "#4444FF",
                "line_width": 1,
                "add_labels": True
            },
            {
                "name": "Light Gray 8x8",
                "grid_size": 8,
                "color": "#CCCCCC",
                "line_width": 1,
                "add_labels": True
            },
            {
                "name": "Thin Purple 8x8",
                "grid_size": 8,
                "color": "#8844FF",
                "line_width": 1,
                "add_labels": False
            },
            {
                "name": "Large Yellow 4x4",
                "grid_size": 4,
                "color": "#FFDD00",
                "line_width": 2,
                "add_labels": True
            },
            {
                "name": "Fine Orange 16x16",
                "grid_size": 16,
                "color": "#FF8800",
                "line_width": 1,
                "add_labels": False
            },
            {
                "name": "No Labels Red 8x8",
                "grid_size": 8,
                "color": "red",
                "line_width": 1,
                "add_labels": False
            }
        ]
        
        # Run all tests
        for config in test_configs:
            try:
                result = self.test_tile_variation(screenshot_base64, config)
                self.test_results.append(result)
                
                # Brief pause between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Test '{config['name']}' failed: {e}")
                self.test_results.append({
                    "test_name": config['name'],
                    "success": False,
                    "error": str(e),
                    "config": config
                })
        
        # Analyze results
        self.analyze_tile_variations()
    
    def analyze_tile_variations(self) -> None:
        """Analyze which tile configurations minimize hallucinations"""
        print("\n" + "=" * 80)
        print("🎮 TILE OVERLAY VARIATION ANALYSIS")
        print("=" * 80)
        
        successful_tests = [r for r in self.test_results if r.get("success", False)]
        
        if not successful_tests:
            print("❌ No successful tests to analyze")
            return
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(self.test_results)}")
        
        # Analyze hallucination patterns
        print(f"\n🔍 HALLUCINATION ANALYSIS:")
        
        best_configs = []
        worst_configs = []
        
        for test in successful_tests:
            config_name = test.get("test_name", "unknown")
            health_mentions = test.get("health_bar_mentions", 0)
            env_focus = test.get("environment_focus", 0)
            grid_confusion = test.get("grid_confusion", 0)
            
            print(f"   {config_name}:")
            print(f"      Health bar mentions: {health_mentions}")
            print(f"      Environment focus: {env_focus}")
            print(f"      Grid confusion: {grid_confusion}")
            
            # Score configuration (lower is better for health mentions)
            score = health_mentions * 10 + grid_confusion * 2 - env_focus
            test["hallucination_score"] = score
            
            if health_mentions == 0 and env_focus > 3:
                best_configs.append((config_name, test["config"]))
            elif health_mentions > 2:
                worst_configs.append((config_name, test["config"]))
        
        # Recommendations
        print(f"\n🏆 BEST CONFIGURATIONS (No health bar hallucinations):")
        if best_configs:
            for name, config in best_configs:
                print(f"   ✅ {name}")
                print(f"      Color: {config.get('color', 'N/A')}")
                print(f"      Grid size: {config.get('grid_size', 'N/A')}x{config.get('grid_size', 'N/A')}")
                print(f"      Labels: {config.get('add_labels', 'N/A')}")
        else:
            print("   ⚠️ No configurations completely eliminated hallucinations")
        
        print(f"\n❌ WORST CONFIGURATIONS (High hallucination rate):")
        if worst_configs:
            for name, config in worst_configs:
                print(f"   ❌ {name}")
                print(f"      Color: {config.get('color', 'N/A')}")
                print(f"      Issues: Triggers health bar hallucinations")
        else:
            print("   ✅ No particularly problematic configurations")
        
        # Find optimal configuration
        if successful_tests:
            optimal_test = min(successful_tests, key=lambda x: x.get("hallucination_score", 100))
            print(f"\n🎯 OPTIMAL CONFIGURATION:")
            print(f"   Name: {optimal_test.get('test_name', 'unknown')}")
            print(f"   Score: {optimal_test.get('hallucination_score', 'N/A')} (lower is better)")
            print(f"   Config: {optimal_test.get('config', {})}")
        
        # Save results
        self.save_tile_variation_results()
    
    def save_tile_variation_results(self) -> None:
        """Save tile variation test results"""
        results_file = Path(__file__).parent / f"tile_variations_{self.timestamp}.json"
        output_file = Path(__file__).parent / "tile_variations_output.txt"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Also save to always-available output file (overwrite)
        with open(output_file, 'w') as f:
            f.write("🎮 Game Boy Tile Overlay Variation Results\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"OVERLAY IMAGES SAVED TO: {self.overlay_dir}\n")
            f.write("-" * 60 + "\n\n")
            
            for result in self.test_results:
                if result.get("success", False):
                    f.write(f"TEST: {result.get('test_name', 'unknown')}\n")
                    f.write(f"CONFIG: {result.get('config', {})}\n")
                    f.write(f"HEALTH BAR MENTIONS: {result.get('health_bar_mentions', 0)}\n")
                    f.write(f"ENVIRONMENT FOCUS: {result.get('environment_focus', 0)}\n")
                    f.write(f"RESPONSE: {result.get('response', 'N/A')[:300]}...\n")
                    f.write("-" * 40 + "\n\n")
        
        print(f"\n💾 Tile variation results saved to: {results_file}")
        print(f"📝 Output also saved to: {output_file}")
        print(f"🖼️ Overlay images saved to: {self.overlay_dir}")

def main():
    """Main tile variation test execution"""
    print("🎮 Game Boy Tile Overlay Variation Testing")
    print("=" * 70)
    print("Goal: Find optimal tile overlay configuration to minimize hallucinations")
    print("Focus: Pokemon environment understanding with clear navigation guidance")
    print()
    
    # Run tests
    tester = TileOverlayTester()
    tester.run_tile_variation_tests()
    
    print("\n✅ Tile overlay variation testing complete!")
    print("\nKey Research:")
    print("1. Which colors reduce health bar hallucinations?")
    print("2. Do smaller/larger grids change hallucination patterns?")
    print("3. Do labels increase or decrease UI confusion?")
    print("4. What's the optimal configuration for navigation assistance?")

if __name__ == "__main__":
    main()