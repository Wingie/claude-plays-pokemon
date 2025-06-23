#!/usr/bin/env python3
"""
Prompt Classification Testing
Tests current production prompts against 4 Pokemon game scenarios
"""

import sys
import base64
import json
import time
from pathlib import Path
from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root))

try:
    from dotenv import load_dotenv
    from llm_api import call_llm
    load_dotenv()
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

class PromptClassificationTester:
    """Test current production prompts against step_*.png scenarios"""
    
    def __init__(self):
        # Back to full classification: navigation, menu, battle (original requirements)
        self.test_scenarios = [
            ("step_overworld_alone.png", "navigation"),
            ("step_overworld_withNPC.png", "navigation"), 
            ("step_talking_NPC.png", "menu"),  # Dialogue box scenario
            ("step_battle_opening.png", "battle")  # Trainer encounter
        ]
        
        # Test universal prompts against all scenarios
        self.prompt_variations = [
            {
                "name": "universal_v1",
                "description": "Universal scene analysis - Handles all contexts",
                "prompt": """POKEMON SCENE ANALYSIS

Analyze screenshot. Detect scene type and provide appropriate data.

FOR BATTLE: Pokemon data + cursor position + button options
FOR NAVIGATION: Movement options + terrain + NPCs  
FOR MENU: Dialogue + interaction options

ALWAYS include valid_buttons for current scene:

{
  "scene_type": "battle|navigation|menu",
  "battle_data": {"our_pokemon": {"name": "NAME", "hp": "X/Y", "level": 0}, "enemy_pokemon": {"name": "NAME", "hp": "X/Y", "level": 0}, "cursor_position": "FIGHT"},
  "navigation_data": {"player_pos": "x,y", "terrain": "grass|water|path", "npcs_visible": [], "obstacles": []},
  "menu_data": {"dialogue_text": "text", "interaction_type": "npc|sign|item"},
  "valid_buttons": [
    {"key": "A", "action": "specific_action", "result": "what_happens"},
    {"key": "→", "action": "move_right_or_cursor", "result": "movement_or_menu"},
    {"key": "↓", "action": "move_down_or_cursor", "result": "movement_or_menu"}
  ],
  "recommended_template": "ai_directed_navigation|ai_directed_battle"
}

FILL ONLY RELEVANT SECTIONS. JSON ONLY."""
            },
            {
                "name": "universal_v2", 
                "description": "Streamlined universal - Compact context data",
                "prompt": """POKEMON SCENE ANALYSIS

Extract scene data + valid button options for ANY Pokemon context.

FOR BATTLE: Pokemon status + fight options
FOR NAVIGATION: Movement + terrain analysis  
FOR MENU: Dialogue + interaction options

{
  "scene_type": "battle|navigation|menu",
  "context_data": {
    "battle": {"ours": "NAME HP:X/Y", "enemy": "NAME HP:X/Y", "cursor": "FIGHT"},
    "navigation": {"terrain": "grass|path", "obstacles": [], "npcs": []},
    "menu": {"text": "dialogue content", "type": "npc|sign"}
  },
  "valid_buttons": [
    {"key": "A", "action": "context_specific_action"},
    {"key": "→", "action": "move_or_cursor_right"},
    {"key": "↓", "action": "move_or_cursor_down"}
  ],
  "recommended_template": "ai_directed_navigation|ai_directed_battle"
}

JSON ONLY."""
            }
        ]
    
    def run_classification_test(self):
        """Test 2 universal prompt variations against all scenarios"""
        print("🎯 Universal Prompt Testing")
        print("=" * 50)
        print("Testing 2 universal prompt variations against all Pokemon game scenarios")
        
        # Create output directory
        timestamp = int(time.time())
        output_dir = Path(f"/Users/wingston/code/claude-plays-pokemon/eevee/tests/prompt_variations_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        results = {
            "timestamp": timestamp,
            "test_type": "prompt_variations",
            "variations": []
        }
        
        print(f"\n📸 Testing {len(self.test_scenarios)} scenarios")
        print(f"🔬 Against {len(self.prompt_variations)} prompt variations")
        print("=" * 50)
        
        # Test each prompt variation
        for variation_idx, variation in enumerate(self.prompt_variations, 1):
            print(f"\n📝 VARIATION {variation_idx}: {variation['name']}")
            print(f"💡 {variation['description']}")
            
            variation_result = {
                "name": variation['name'],
                "description": variation['description'],
                "scenarios": []
            }
            
            # Test this variation against all scenarios
            for img_name, expected_type in self.test_scenarios:
                print(f"  🖼️  {img_name} (Expected: {expected_type})")
                
                scenario_result = self.test_variation_scenario(
                    variation['prompt'], 
                    img_name, 
                    expected_type,
                    variation['name']
                )
                
                variation_result["scenarios"].append(scenario_result)
                
                # Show result
                detected = scenario_result["detected_scene_type"]
                match = "✅" if detected == expected_type else "❌"
                print(f"      {match} Detected: {detected}")
            
            results["variations"].append(variation_result)
        
        # Save single comprehensive results file
        results_file = output_dir / "prompt_variations_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Analysis
        self.analyze_variation_results(results)
        
        return results
    
    def test_variation_scenario(self, prompt: str, img_name: str, expected_type: str, variation_name: str) -> Dict:
        """Test single prompt variation against single scenario using Mistral only"""
        
        # Load and prepare image
        img_path = Path(__file__).parent / img_name
        if not img_path.exists():
            return {
                "image_name": img_name,
                "expected_scene_type": expected_type,
                "variation_name": variation_name,
                "error": f"Image not found: {img_path}",
                "detected_scene_type": "error",
                "success": False
            }
        
        # Convert to base64 (step_*.png files already have grids)
        with open(img_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Use image as-is since step_*.png files already have coordinate grids
        grid_image_base64 = img_base64
        
        # Test with Gemini (switched from Mistral)
        try:
            response = call_llm(
                prompt=prompt,
                image_data=grid_image_base64,
                provider="gemini",
                model="gemini-2.0-flash-exp",
                max_tokens=800
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            detected_scene_type = self.extract_scene_type(response_text)
            
            return {
                "image_name": img_name,
                "expected_scene_type": expected_type,
                "variation_name": variation_name,
                "detected_scene_type": detected_scene_type,
                "raw_response": response_text,
                "success": True
            }
            
        except Exception as e:
            return {
                "image_name": img_name,
                "expected_scene_type": expected_type,
                "variation_name": variation_name,
                "error": str(e),
                "detected_scene_type": "error",
                "success": False
            }

    def analyze_variation_results(self, results: Dict):
        """Analyze prompt variation performance with Gemini"""
        print(f"\n🎯 GEMINI PROMPT VARIATION ANALYSIS:")
        print("=" * 50)
        
        variations = results["variations"]
        total_scenarios = len(self.test_scenarios)
        
        print(f"\n📊 VARIATION PERFORMANCE (Gemini 2.0 Flash):")
        
        best_accuracy = 0
        best_variation = None
        
        for variation in variations:
            name = variation["name"]
            scenarios = variation["scenarios"]
            
            correct = 0
            for scenario in scenarios:
                if scenario["detected_scene_type"] == scenario["expected_scene_type"]:
                    correct += 1
            
            accuracy = (correct / total_scenarios) * 100
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_variation = variation
            
            print(f"\n📝 {name}")
            print(f"   Accuracy: {correct}/{total_scenarios} ({accuracy:.1f}%)")
            
            # Show detailed results
            for scenario in scenarios:
                expected = scenario["expected_scene_type"]
                detected = scenario["detected_scene_type"]
                match = "✅" if detected == expected else "❌"
                print(f"   {match} {scenario['image_name']}: {expected} → {detected}")
        
        # Best performing variation
        print(f"\n🏆 BEST PERFORMING VARIATION:")
        if best_variation:
            print(f"   📝 {best_variation['name']} ({best_accuracy:.1f}%)")
            print(f"   💡 {best_variation['description']}")
        
        # Problem analysis
        print(f"\n🔍 GEMINI FAILURE PATTERNS:")
        failure_patterns = {}
        
        for variation in variations:
            for scenario in variation["scenarios"]:
                if scenario["detected_scene_type"] != scenario["expected_scene_type"]:
                    img_name = scenario["image_name"]
                    expected = scenario["expected_scene_type"]
                    detected = scenario["detected_scene_type"]
                    
                    pattern = f"{img_name}: {expected} → {detected}"
                    if pattern not in failure_patterns:
                        failure_patterns[pattern] = 0
                    failure_patterns[pattern] += 1
        
        for pattern, count in sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"   ❌ {pattern} ({count} variations failed)")
        
        # Recommendations
        print(f"\n💡 GEMINI OPTIMIZATION RECOMMENDATIONS:")
        if best_variation:
            print(f"   1. Use '{best_variation['name']}' as Gemini production prompt")
            print(f"   2. Accuracy achieved: {best_accuracy:.1f}%")
            
            # Check specific improvements
            battle_fixed = False
            dialogue_fixed = False
            
            for scenario in best_variation["scenarios"]:
                if scenario["image_name"] == "step_battle_opening.png" and scenario["detected_scene_type"] == "battle":
                    battle_fixed = True
                if scenario["image_name"] == "step_talking_NPC.png" and scenario["detected_scene_type"] == "menu":
                    dialogue_fixed = True
            
            if battle_fixed:
                print(f"   3. ✅ Battle detection working for Gemini")
            else:
                print(f"   3. ❌ Battle detection needs improvement for Gemini")
                
            if dialogue_fixed:
                print(f"   4. ✅ Dialogue detection working for Gemini") 
            else:
                print(f"   4. ❌ Dialogue detection needs improvement for Gemini")
        
        return best_variation
    
    def test_scenario(self, img_name: str, expected_type: str, output_dir: Path) -> Dict:
        """Test both prompts against a single scenario"""
        
        # Load and prepare image
        img_path = Path(__file__).parent / img_name
        if not img_path.exists():
            return {
                "image_name": img_name,
                "expected_scene_type": expected_type,
                "error": f"Image not found: {img_path}",
                "mistral_result": {"error": "Image not found"},
                "gemini_result": {"error": "Image not found"}
            }
        
        # Convert to base64 and add grid
        with open(img_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        grid_image_base64 = self.add_coordinate_grid(img_base64)
        
        # Save grid image for reference
        grid_img_path = output_dir / f"{img_name.replace('.png', '_with_grid.png')}"
        with open(grid_img_path, 'wb') as f:
            f.write(base64.b64decode(grid_image_base64))
        
        # Test with both prompts
        mistral_result = self.test_with_prompt(self.mistral_prompt, grid_image_base64, "mistral")
        gemini_result = self.test_with_prompt(self.gemini_prompt, grid_image_base64, "gemini")
        
        # Save individual responses
        scenario_name = img_name.replace('.png', '')
        
        with open(output_dir / f"{scenario_name}_mistral_response.json", 'w') as f:
            json.dump(mistral_result, f, indent=2)
        
        with open(output_dir / f"{scenario_name}_gemini_response.json", 'w') as f:
            json.dump(gemini_result, f, indent=2)
        
        return {
            "image_name": img_name,
            "expected_scene_type": expected_type,
            "mistral_result": mistral_result,
            "gemini_result": gemini_result
        }
    
    def test_with_prompt(self, prompt: str, image_base64: str, provider: str) -> Dict:
        """Test single prompt with single provider"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_base64,
                provider=provider,
                model="pixtral-12b-2409" if provider == "mistral" else "gemini-2.0-flash-exp",
                max_tokens=800
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract scene type from JSON response
            detected_scene_type = self.extract_scene_type(response_text)
            
            return {
                "provider": provider,
                "model": "pixtral-12b-2409" if provider == "mistral" else "gemini-2.0-flash-exp",
                "raw_response": response_text,
                "detected_scene_type": detected_scene_type,
                "success": True
            }
            
        except Exception as e:
            return {
                "provider": provider,
                "error": str(e),
                "detected_scene_type": "error",
                "success": False
            }
    
    def extract_scene_type(self, response: str) -> str:
        """Extract scene_type from JSON response"""
        try:
            # Look for JSON in response
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            parsed = json.loads(json_str)
            return parsed.get('scene_type', 'unknown')
            
        except Exception as e:
            # Fallback: look for scene_type in text
            if '"scene_type"' in response:
                for line in response.split('\n'):
                    if 'scene_type' in line:
                        for scene_type in ['navigation', 'battle', 'menu', 'dialogue']:
                            if scene_type in line:
                                return scene_type
            return 'parse_error'
    
    def add_coordinate_grid(self, image_base64: str, grid_size: int = 8) -> str:
        """Add coordinate grid overlay to image"""
        try:
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_bytes)).convert('RGB')
            
            overlay_image = image.copy().convert('RGBA')
            grid_overlay = Image.new('RGBA', overlay_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(grid_overlay)
            
            width, height = image.size
            tile_width = width // grid_size
            tile_height = height // grid_size
            
            # Draw grid lines
            grid_color = (255, 255, 255, 150)
            for x in range(0, width, tile_width):
                draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
            
            for y in range(0, height, tile_height):
                draw.line([(0, y), (width, y)], fill=grid_color, width=1)
            
            # Add coordinate labels
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            text_color = (255, 255, 255, 180)
            for tile_x in range(grid_size):
                for tile_y in range(grid_size):
                    pixel_x = tile_x * tile_width
                    pixel_y = tile_y * tile_height
                    coord_text = f"{tile_x},{tile_y}"
                    draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill=text_color, font=font)
            
            # Convert back to base64
            result = Image.alpha_composite(overlay_image, grid_overlay).convert('RGB')
            buffer = BytesIO()
            result.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            print(f"Failed to add grid overlay: {e}")
            return image_base64
    
    def analyze_results(self, results: Dict):
        """Analyze and display results"""
        print(f"\n🎯 CLASSIFICATION ANALYSIS:")
        print("=" * 40)
        
        scenarios = results["scenarios"]
        
        # Accuracy summary
        mistral_correct = 0
        gemini_correct = 0
        total = len(scenarios)
        
        print("\n📊 DETAILED RESULTS:")
        for scenario in scenarios:
            img_name = scenario["image_name"]
            expected = scenario["expected_scene_type"]
            
            mistral_detected = scenario["mistral_result"]["detected_scene_type"]
            gemini_detected = scenario["gemini_result"]["detected_scene_type"]
            
            mistral_match = mistral_detected == expected
            gemini_match = gemini_detected == expected
            
            if mistral_match:
                mistral_correct += 1
            if gemini_match:
                gemini_correct += 1
            
            print(f"\n🖼️  {img_name} (Expected: {expected})")
            print(f"   Mistral: {'✅' if mistral_match else '❌'} {mistral_detected}")
            print(f"   Gemini:  {'✅' if gemini_match else '❌'} {gemini_detected}")
        
        # Summary
        mistral_accuracy = (mistral_correct / total) * 100
        gemini_accuracy = (gemini_correct / total) * 100
        
        print(f"\n🏆 ACCURACY SUMMARY:")
        print(f"   Mistral: {mistral_correct}/{total} ({mistral_accuracy:.1f}%)")
        print(f"   Gemini:  {gemini_correct}/{total} ({gemini_accuracy:.1f}%)")
        
        # Identify problem areas
        print(f"\n🔍 PROBLEM AREAS:")
        for scenario in scenarios:
            expected = scenario["expected_scene_type"]
            mistral_detected = scenario["mistral_result"]["detected_scene_type"]
            gemini_detected = scenario["gemini_result"]["detected_scene_type"]
            
            if mistral_detected != expected or gemini_detected != expected:
                print(f"   ❌ {scenario['image_name']}: {expected} misclassified")
                if mistral_detected != expected:
                    print(f"      Mistral saw: {mistral_detected}")
                if gemini_detected != expected:
                    print(f"      Gemini saw: {gemini_detected}")

def main():
    """Run prompt classification testing"""
    tester = PromptClassificationTester()
    results = tester.run_classification_test()
    
    print(f"\n✅ Classification testing complete!")
    print("💡 Check output folder for detailed JSON responses")

if __name__ == "__main__":
    main()