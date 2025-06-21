#!/usr/bin/env python3
"""
Navigation Pathfinding Test
Focus on detecting walkable vs blocked paths in Pokemon overworld scenes
No battle element detection - pure navigation analysis
"""

import sys
import base64
import json
import time
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
    from skyemu_controller import SkyEmuController
    from dotenv import load_dotenv
    from llm_api import call_llm
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

load_dotenv()

class NavigationPathfinder:
    """Focus on navigation path detection in Pokemon overworld scenes"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.timestamp = int(time.time())
        
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
    
    def add_directional_grid(self, image: Image.Image) -> Image.Image:
        """Add simple directional grid for path analysis"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        width, height = image.size
        center_x, center_y = width // 2, height // 2
        
        # Draw directional indicators
        grid_size = 30
        
        # Draw cross-hair for center player
        draw.line([(center_x - 10, center_y), (center_x + 10, center_y)], fill='red', width=2)
        draw.line([(center_x, center_y - 10), (center_x, center_y + 10)], fill='red', width=2)
        
        # Add direction labels
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # UP
        draw.text((center_x - 10, center_y - grid_size), "UP", fill='blue', font=font)
        # DOWN  
        draw.text((center_x - 15, center_y + grid_size - 10), "DOWN", fill='blue', font=font)
        # LEFT
        draw.text((center_x - grid_size - 25, center_y - 8), "LEFT", fill='blue', font=font)
        # RIGHT
        draw.text((center_x + grid_size, center_y - 8), "RIGHT", fill='blue', font=font)
        
        return overlay_image
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image back to base64"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def call_pixtral_navigation(self, prompt: str, image_base64: str) -> Dict:
        """Call Pixtral with navigation-focused prompt"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_base64,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=400
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
    
    def test_pure_navigation(self, image_base64: str) -> Dict:
        """Test pure navigation path detection"""
        print("\n🧭 NAVIGATION PATHFINDING TEST")
        print("=" * 60)
        
        # Add directional overlay
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        nav_image = self.add_directional_grid(image)
        nav_base64 = self.image_to_base64(nav_image)
        
        prompt = """POKEMON OVERWORLD NAVIGATION ANALYSIS

You are a navigation assistant for Pokemon overworld exploration. Analyze this screenshot:

CONTEXT:
- Player character is at center (red crosshair)
- Each button press moves player one tile/square
- This is overworld exploration, NOT battle
- Goal: Identify movement possibilities

ANALYSIS REQUIRED:
1. Player Position: Describe what's at center
2. UP Direction: Can player move up? What blocks/allows movement?
3. DOWN Direction: Can player move down? What blocks/allows movement?  
4. LEFT Direction: Can player move left? What blocks/allows movement?
5. RIGHT Direction: Can player move right? What blocks/allows movement?
6. Best Path: Which direction offers clearest path for exploration?

RESPOND IN FORMAT:
UP: [WALKABLE/BLOCKED] - [reason]
DOWN: [WALKABLE/BLOCKED] - [reason]  
LEFT: [WALKABLE/BLOCKED] - [reason]
RIGHT: [WALKABLE/BLOCKED] - [reason]
RECOMMENDATION: [direction] - [explanation]

Focus on terrain obstacles (trees, water, walls, NPCs) not fictional UI elements."""
        
        result = self.call_pixtral_navigation(prompt, nav_base64)
        
        if result["success"]:
            print(f"✅ Navigation Analysis:")
            print(result['response'])
            
            # Parse movement possibilities
            response_text = result['response'].upper()
            result["movement_analysis"] = {
                "up_walkable": "UP: WALKABLE" in response_text,
                "down_walkable": "DOWN: WALKABLE" in response_text,
                "left_walkable": "LEFT: WALKABLE" in response_text,
                "right_walkable": "RIGHT: WALKABLE" in response_text
            }
            
            # Check for navigation focus vs battle hallucination
            result["focuses_on_navigation"] = any(word in response_text for word in [
                'WALKABLE', 'BLOCKED', 'TREE', 'WATER', 'WALL', 'PATH', 'DIRECTION'
            ])
            result["mentions_battle_elements"] = any(word in response_text for word in [
                'HEALTH', 'HP', 'BATTLE', 'COMBAT', 'MENU'
            ])
            
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def test_step_by_step_navigation(self, image_base64: str) -> Dict:
        """Test step-by-step navigation guidance"""
        print("\n🎯 STEP-BY-STEP NAVIGATION TEST")
        print("=" * 60)
        
        prompt = """STEP-BY-STEP POKEMON NAVIGATION

You are guiding a Pokemon trainer through overworld exploration. 

SITUATION:
- Trainer is exploring Pokemon world
- Current position: center of screen
- Movement: one square per button press (UP/DOWN/LEFT/RIGHT)
- Goal: Find next safe movement step

PROVIDE GUIDANCE:
1. Current Location: What type of area is this? (forest, town, route, etc.)
2. Immediate Obstacles: What blocks movement in each direction?
3. Safe Directions: Which directions are clear for movement?
4. Next Action: What specific button should be pressed next?
5. Reasoning: Why is this the best choice?

Keep response practical and action-oriented. Focus on actual terrain, not imaginary game UI."""
        
        result = self.call_pixtral_navigation(prompt, image_base64)
        
        if result["success"]:
            print(f"✅ Step-by-Step Guidance:")
            print(result['response'])
            
            # Extract action recommendation
            response_lower = result['response'].lower()
            for direction in ['up', 'down', 'left', 'right']:
                if f"press {direction}" in response_lower or f"move {direction}" in response_lower:
                    result["recommended_action"] = direction.upper()
                    break
            else:
                result["recommended_action"] = "NONE"
                
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def run_navigation_tests(self) -> None:
        """Run comprehensive navigation pathfinding tests"""
        print("🧭 Pokemon Overworld Navigation Pathfinding")
        print("=" * 70)
        print("Testing Pixtral's ability to detect walkable paths vs obstacles")
        print("Focus: Navigation assistance, NOT battle detection")
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
        
        # Run navigation tests
        results = []
        
        try:
            # Test 1: Pure navigation analysis
            nav_result = self.test_pure_navigation(screenshot_base64)
            results.append(nav_result)
            
            time.sleep(1)
            
            # Test 2: Step-by-step guidance
            step_result = self.test_step_by_step_navigation(screenshot_base64)
            results.append(step_result)
            
        except Exception as e:
            print(f"❌ Navigation testing failed: {e}")
            return
        
        # Save results
        self.save_navigation_results(results)
        
        # Analysis
        self.analyze_navigation_performance(results)
    
    def save_navigation_results(self, results: List[Dict]) -> None:
        """Save navigation test results"""
        output_file = Path(__file__).parent / "navigation_pathfinding_output.txt"
        json_file = Path(__file__).parent / f"navigation_results_{self.timestamp}.json"
        
        # Save JSON data
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save readable output
        with open(output_file, 'w') as f:
            f.write("🧭 Pokemon Navigation Pathfinding Results\n")
            f.write("=" * 60 + "\n\n")
            
            for i, result in enumerate(results, 1):
                if result.get("success", False):
                    f.write(f"TEST {i}:\n")
                    f.write(f"RESPONSE: {result.get('response', 'N/A')}\n")
                    f.write("-" * 40 + "\n\n")
        
        print(f"\n💾 Navigation results saved to: {output_file}")
        print(f"📊 JSON data saved to: {json_file}")
    
    def analyze_navigation_performance(self, results: List[Dict]) -> None:
        """Analyze navigation detection performance"""
        print("\n" + "=" * 70)
        print("🧭 NAVIGATION ANALYSIS SUMMARY")
        print("=" * 70)
        
        successful_tests = [r for r in results if r.get("success", False)]
        
        if not successful_tests:
            print("❌ No successful tests to analyze")
            return
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        
        # Navigation focus analysis
        nav_focused = sum(1 for r in successful_tests if r.get("focuses_on_navigation", False))
        battle_mentions = sum(1 for r in successful_tests if r.get("mentions_battle_elements", False))
        
        print(f"\n🎯 NAVIGATION FOCUS:")
        print(f"   ✅ Tests focusing on navigation: {nav_focused}/{len(successful_tests)}")
        print(f"   ⚠️ Tests mentioning battle elements: {battle_mentions}/{len(successful_tests)}")
        
        if battle_mentions == 0:
            print("🎉 SUCCESS: Pixtral completely focused on navigation!")
            print("   - No false battle element detection")
            print("   - Pure focus on pathfinding and movement")
        elif battle_mentions < len(successful_tests):
            print("📈 IMPROVEMENT: Reduced battle hallucinations with navigation prompts")
        else:
            print("⚠️ ISSUE: Still detecting non-existent battle elements")
        
        # Action guidance analysis
        action_tests = [r for r in successful_tests if "recommended_action" in r]
        if action_tests:
            actions = [r["recommended_action"] for r in action_tests]
            print(f"\n🎮 ACTION RECOMMENDATIONS:")
            for action in set(actions):
                count = actions.count(action)
                print(f"   {action}: {count} recommendations")
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if nav_focused == len(successful_tests) and battle_mentions == 0:
            print("✅ EXCELLENT: Perfect navigation focus with actionable pathfinding")
        elif nav_focused > len(successful_tests) // 2:
            print("✅ GOOD: Strong navigation focus with minimal hallucinations")
        else:
            print("⚠️ NEEDS WORK: Still struggling with navigation vs battle detection")

def main():
    """Main navigation pathfinding test"""
    print("🧭 Pokemon Overworld Navigation Pathfinding Test")
    print("=" * 70)
    print("Focus: Pure navigation and pathfinding assistance")
    print("Goal: Eliminate battle hallucinations, enhance movement guidance")
    print()
    
    pathfinder = NavigationPathfinder()
    pathfinder.run_navigation_tests()
    
    print("\n✅ Navigation pathfinding test complete!")
    print("\nKey Results:")
    print("1. Can Pixtral focus purely on navigation without battle hallucinations?")
    print("2. Does it provide actionable movement guidance?")
    print("3. Can it distinguish walkable paths from obstacles?")

if __name__ == "__main__":
    main()