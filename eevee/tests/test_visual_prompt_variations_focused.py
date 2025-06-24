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
        """Test different prompt approaches to avoid safety filters"""
        
        # Approach 1: Clear Pokemon GBA context with original format
        pokemon_gba_v1 = """Pokemon Game Boy Advance Screenshot Analysis

This is a screenshot from a classic Pokemon GBA video game (educational/nostalgic gaming content). Please analyze the game interface and extract the current game state.

Analyze the Pokemon GBA game screen and detect what type of scene this is:

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

        # Approach 2: Educational gaming context
        pokemon_educational_v1 = """Classic Pokemon Video Game Interface Analysis

I am analyzing a Pokemon Game Boy Advance screenshot for educational gaming research purposes. This is legitimate retro gaming content from Nintendo's classic Pokemon series.

Please help identify the current game state in this Pokemon GBA game:

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

JSON format only."""

        # Approach 3: Nintendo gaming context
        nintendo_context_v1 = """Nintendo Pokemon GBA Game State Detection

Analyzing a screenshot from Pokemon (Game Boy Advance) - a classic Nintendo video game series. This is legitimate gaming content analysis for game interface understanding.

Extract the current Pokemon game interface state:

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

        # Approach 4: Retro gaming preservation
        retro_gaming_v1 = """Retro Gaming Interface Documentation

This is a Pokemon Game Boy Advance screenshot being analyzed for retro gaming preservation and interface documentation purposes. Pokemon is a beloved Nintendo franchise.

Document the current game interface state:

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

Return JSON only."""

        battle_focused_v3 = """POKEMON BATTLE ANALYSIS

Analyze HP bars by COLOR (green=high, orange=medium, red=low). Detect cursor position and return ALL valid button options with SPECIFIC actions.

{
  "scene_type": "battle",
  "battle_data": {
    "our_hp": "14/26", 
    "enemy_hp_color": "green|orange|red", 
    "our_mon": "PIKACHU L9", 
    "enemy_mon": "METAPOD L7"
  },
  "cursor_info": {"selected": "FIGHT", "menu": "main"},
  "button_options": [
    {"btn": "A", "does": "select_FIGHT_open_moves_menu"},
    {"btn": "→", "does": "move_cursor_to_BAG"},
    {"btn": "↓", "does": "move_cursor_to_POKEMON"},
    {"btn": "B", "does": "back_or_cancel"}
  ],
  "fight_moves": []
}

JSON ONLY."""

        battle_focused_v4 = """POKEMON BATTLE ANALYSIS

Extract Pokemon data + cursor position + valid keys.

{
  "mode": "battle",
  "status": {"us": "NAME HP", "them": "NAME HP"},
  "cursor": "FIGHT",
  "buttons": [
    {"k": "A", "do": "select_FIGHT"},
    {"k": "→", "do": "to_BAG"}, 
    {"k": "↓", "do": "to_POKEMON"},
    {"k": "B", "do": "cancel"}
  ],
  "moves": [],
  "template": "battle"
}

JSON ONLY."""
        
        return [
            {
                "name": "pokemon_gba_v1",
                "description": "🎮 Clear Pokemon GBA context with educational framing",
                "prompt": pokemon_gba_v1,
                "provider": "gemini"
            },
            {
                "name": "pokemon_educational_v1", 
                "description": "📚 Educational gaming research context",
                "prompt": pokemon_educational_v1,
                "provider": "gemini"
            },
            {
                "name": "nintendo_context_v1",
                "description": "🕹️ Nintendo franchise context",
                "prompt": nintendo_context_v1,
                "provider": "gemini"
            },
            {
                "name": "retro_gaming_v1",
                "description": "📼 Retro gaming preservation context",
                "prompt": retro_gaming_v1,
                "provider": "gemini"
            }
        ]
    
    def run_focused_test(self):
        """Run focused test with 4 compact JSON variations"""
        print("🎯 POKEMON GBA SAFETY FILTER TESTING")
        print("=" * 60)
        print("Testing 4 different context framings to bypass Gemini safety filters")
        
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
        
        print(f"\n🧪 Testing {len(prompt_variations)} compact JSON variations")
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
                    
                # Show response preview with pretty JSON formatting
                try:
                    # Try to parse and pretty-print JSON
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', result['response'], re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        parsed_json = json.loads(json_str)
                        print("📋 PARSED JSON RESPONSE:")
                        pprint.pp(parsed_json, width=100, depth=3)
                    else:
                        # Fallback to raw response if JSON parsing fails
                        print("📋 RAW RESPONSE:")
                        preview = result['response'].replace('\n', ' ')[:200] + "..." if len(result['response']) > 200 else result['response']
                        print(preview)
                except (json.JSONDecodeError, AttributeError) as e:
                    print("📋 RAW RESPONSE (JSON parse failed):")
                    preview = result['response'].replace('\n', ' ')[:200] + "..." if len(result['response']) > 200 else result['response']
                    print(preview)
                
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