#!/usr/bin/env python3
"""
FOCUSED Visual Analysis Prompt Testing
Tests only the most relevant prompts for anti-hallucination research
"""

import sys
import base64
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pprint

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
    
    # Load environment variables from .env file
    load_dotenv()
    
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

class FocusedVisualPromptTester:
    """Focused testing of 5 key anti-hallucination prompts"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.test_dir = None
        
    def get_prompt_variations(self) -> List[Dict]:
        """Test movement_context_analyzer_standard across Mistral and Gemini providers"""
        mistral_prompt = """POKEMON SCENE ANALYSIS

Analyze this Pokemon game screenshot with coordinate grid overlay.

**IMPORTANT:** The white grid lines and coordinate numbers (0,0 through 7,7) are overlaid by us to help with spatial analysis - they are NOT part of the original game interface.

**TASK:** Determine scene type and provide balanced analysis for the next AI stage.

**ANALYSIS REQUIREMENTS:**
- Identify scene type: navigation (overworld movement), battle (Pokemon combat), or menu (dialogs/interfaces)
- Describe character position and visual context
- Note template recommendation with reasoning
- Provide confidence assessment and spatial understanding
- Analyze terrain around player character to determine valid movement directions

**CRITICAL:** Return ONLY JSON with balanced analysis:

{
  "scene_type": "navigation|battle|menu|unknown",
  "recommended_template": "ai_directed_navigation|ai_directed_battle",
  "confidence": "high|medium|low",
  "spatial_context": "Grid-based spatial understanding for navigation planning",
  "character_position": "grid coordinates if visible",
  "visual_description": "Character and terrain description using grid coordinates",
  "template_reason": "Why this template fits the visual evidence",
  "valid_movements": ["up", "down", "left", "right"]
}"""
        
        gemini_prompt = """POKEMON SCENE ANALYSIS

Analyze this Pokemon game screenshot with coordinate grid overlay.

**TASK:** Determine scene type and provide balanced analysis for the next AI stage.

**ANALYSIS REQUIREMENTS:**
- Identify scene type: navigation (overworld movement), battle (Pokemon combat), or menu (dialogs/interfaces)
- Describe character position and visual context
- Note template recommendation with reasoning
- Provide confidence assessment and spatial understanding
- Analyze terrain around player character to determine valid movement directions

**CRITICAL:** Return ONLY JSON with balanced analysis:

{
  "scene_type": "navigation|battle|menu|unknown",
  "recommended_template": "ai_directed_navigation|ai_directed_battle",
  "confidence": "high|medium|low",
  "spatial_context": "Grid-based spatial understanding for navigation planning",
  "character_position": "grid coordinates if visible",
  "visual_description": "Character and terrain description using grid coordinates",
  "template_reason": "Why this template fits the visual evidence",
  "valid_movements": ["up", "down", "left", "right"]
}"""
        
        return [
            {
                "name": "movement_context_analyzer_standard_mistral",
                "description": "🎮 V2: Standard (8 keys) - Mistral Pixtral",
                "prompt": mistral_prompt,
                "provider": "mistral"
            },
            {
                "name": "movement_context_analyzer_standard_gemini",
                "description": "🎮 V2: Standard (8 keys) - Gemini 2.0 Flash",
                "prompt": gemini_prompt,
                "provider": "gemini"
            }
        ]
    
    def run_focused_test(self):
        """Run focused test with 5 key prompts"""
        print("🎯 MOVEMENT CONTEXT ANALYZER Provider Comparison Testing")
        print("=" * 60)
        print("Testing movement_context_analyzer_standard across Mistral and Gemini providers")
        
        # Connect to SkyEmu and capture screenshot
        if not self.controller.is_connected():
            print("❌ SkyEmu not connected. Ensure it's running on port 8080.")
            return
        
        print("✅ Connected to SkyEmu")
        screenshot_base64 = self.controller.get_screenshot_base64()
        
        if not screenshot_base64:
            print("❌ Failed to capture screenshot")
            return
        
        # Create test directory
        import time
        timestamp = int(time.time())
        self.test_dir = Path(f"/Users/wingston/code/claude-plays-pokemon/eevee/tests/focused_test_{timestamp}")
        self.test_dir.mkdir(exist_ok=True)
        
        # Save original screenshot
        original_path = self.test_dir / "original_screenshot.png"
        with open(original_path, 'wb') as f:
            f.write(base64.b64decode(screenshot_base64))
        print(f"💾 Original screenshot saved: {original_path}")
        
        # Add grid overlay
        grid_image_base64 = self.add_coordinate_grid(screenshot_base64)
        grid_path = self.test_dir / "screenshot_with_grid.png"
        with open(grid_path, 'wb') as f:
            f.write(base64.b64decode(grid_image_base64))
        print(f"💾 Grid screenshot saved: {grid_path}")
        
        # Test all prompt variations
        prompt_variations = self.get_prompt_variations()
        results = []
        
        print(f"\n🧪 Testing {len(prompt_variations)} provider variations")
        print("=" * 60)
        
        for i, variation in enumerate(prompt_variations, 1):
            print(f"\n📝 Test {i}: {variation['name']}")
            print(f"💡 {variation['description']}")
            
            provider = variation.get('provider', 'mistral')
            result = self.test_prompt_variation(
                variation['name'],
                variation['prompt'],
                grid_image_base64,
                provider
            )
            
            if result['success']:
                # Analyze hallucination
                hallucination_analysis = self.analyze_battle_hallucination(result['response'])
                result['hallucination_analysis'] = hallucination_analysis
                
                score = hallucination_analysis['hallucination_score']
                print(f"✅ Response received (Hallucination score: {score})")
                
                # Show any hallucination warnings
                if hallucination_analysis['false_hp_bars']:
                    print("⚠️  Claims to see HP bars")
                if hallucination_analysis['false_battle_menu']:
                    print("⚠️  Claims to see battle menu")
                if hallucination_analysis['false_pokemon_sprites']:
                    print("⚠️  Claims to see Pokemon sprites")
                if score == 0:
                    print("✅ No battle hallucination detected")
                    
                # Show response preview
                preview = result['response'].replace('\n', ' ')
                pprint.pp(preview)
                
            else:
                print(f"❌ Failed: {result['error']}")
            
            results.append(result)
        
        # Save results
        results_file = self.test_dir / "focused_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "test_type": "focused_anti_hallucination",
                "prompt_results": results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Analysis summary
        print(f"\n🎯 MOVEMENT CONTEXT ANALYZER PROVIDER COMPARISON:")
        print("=" * 40)
        for result in results:
            if result['success']:
                score = result['hallucination_analysis']['hallucination_score']
                name = result['prompt_name']
                print(f"{name}: Hallucination Score {score}")
        
        return results
    
    def test_prompt_variation(self, prompt_name: str, prompt: str, image_base64: str, provider: str = "mistral") -> Dict:
        """Test a single prompt variation"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_base64,
                provider=provider,
                model="pixtral-12b-2409" if provider == "mistral" else "gemini-2.0-flash-exp",
                max_tokens=800
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            model = "pixtral-12b-2409" if provider == "mistral" else "gemini-2.0-flash-exp"
            
            return {
                "success": True,
                "prompt_name": prompt_name,
                "provider": provider,
                "model": model,
                "response": response_text,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "prompt_name": prompt_name,
                "provider": provider,
                "response": "",
                "error": str(e)
            }
    
    def analyze_battle_hallucination(self, response_text: str) -> Dict:
        """Analyze response for battle scene hallucination indicators"""
        response_lower = response_text.lower()
        
        # Battle hallucination indicators
        battle_keywords = [
            "battle", "hp bar", "health bar", "fight menu", "bag menu", "pokemon menu", "run menu",
            "battle scene", "pokemon facing", "sprites facing", "battle menu", "move selection",
            "super effective", "not very effective", "critical hit", "fainted", "wild pokemon appeared"
        ]
        
        # Navigation reality indicators
        navigation_keywords = [
            "character", "sprite", "small figure", "overworld", "terrain", "path", "route",
            "grassy", "walking", "movement", "exploration", "navigation", "coordinate", "grid"
        ]
        
        # Count matches
        battle_matches = sum(1 for keyword in battle_keywords if keyword in response_lower)
        navigation_matches = sum(1 for keyword in navigation_keywords if keyword in response_lower)
        
        # Detect specific false claims
        false_hp_bars = any(term in response_lower for term in ["hp bar", "health bar", "hp bars"])
        false_battle_menu = any(term in response_lower for term in ["fight", "bag", "pokemon", "run"] + ["battle menu"])
        false_pokemon_sprites = any(term in response_lower for term in ["pokemon facing", "sprites facing", "large pokemon"])
        
        return {
            "battle_keyword_count": battle_matches,
            "navigation_keyword_count": navigation_matches,
            "false_hp_bars": false_hp_bars,
            "false_battle_menu": false_battle_menu,
            "false_pokemon_sprites": false_pokemon_sprites,
            "hallucination_score": battle_matches,  # Higher = more hallucination
            "reality_score": navigation_matches     # Higher = more accurate
        }
    
    def add_coordinate_grid(self, image_base64: str, grid_size: int = 8) -> str:
        """Add coordinate grid overlay to image"""
        try:
            # Decode base64 to image
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_bytes)).convert('RGB')
            
            # Create overlay
            overlay_image = image.copy().convert('RGBA')
            grid_overlay = Image.new('RGBA', overlay_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(grid_overlay)
            
            width, height = image.size
            tile_width = width // grid_size
            tile_height = height // grid_size
            
            # Draw grid lines
            grid_color = (255, 255, 255, 150)  # White with transparency
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
            
            # Composite and convert back to base64
            result = Image.alpha_composite(overlay_image, grid_overlay).convert('RGB')
            buffer = BytesIO()
            result.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            print(f"Failed to add grid overlay: {e}")
            return image_base64

def main():
    """Run focused anti-hallucination testing"""
    tester = FocusedVisualPromptTester()
    results = tester.run_focused_test()
    
    if results:
        print(f"\n✅ Focused testing complete!")
        print("💡 Check results for production prompt readiness")

if __name__ == "__main__":
    main()