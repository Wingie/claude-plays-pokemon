#!/usr/bin/env python3
"""
Prompt Selection Test
Based on location class and movement analysis, select appropriate prompt template
Integration with movement validation for complete navigation system
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

class PromptSelector:
    """Select appropriate prompt template based on game context and location"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.timestamp = int(time.time())
        
        # Available prompt templates from base_prompts.yaml
        self.available_prompts = [
            "task_analysis",
            "stuck_recovery", 
            "battle_analysis",
            "pokemon_party_analysis",
            "exploration_strategy",
            "inventory_analysis",
            "ai_navigation_with_memory_control",
            "ai_battle_with_context_loading",
            "ai_maze_with_solution_memory",
            "ai_emergency_recovery_with_escalation"
        ]
        
        # Create directory for results
        self.output_dir = Path(__file__).parent / f"prompt_selection_{self.timestamp}"
        self.output_dir.mkdir(exist_ok=True)
        
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
        """Add light grey 8x8 grid overlay (optimal from previous tests)"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        width, height = image.size
        tile_width = width // grid_size
        tile_height = height // grid_size
        
        # Draw light grey grid lines
        for x in range(0, width, tile_width):
            draw.line([(x, 0), (x, height)], fill='#CCCCCC', width=1)
        
        for y in range(0, height, tile_height):
            draw.line([(0, y), (width, y)], fill='#CCCCCC', width=1)
        
        # Add coordinate labels
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        for tile_x in range(grid_size):
            for tile_y in range(grid_size):
                pixel_x = tile_x * tile_width
                pixel_y = tile_y * tile_height
                coord_text = f"{tile_x},{tile_y}"
                draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill='#CCCCCC', font=font)
        
        return overlay_image
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image back to base64"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def call_pixtral(self, prompt: str, image_base64: str) -> Dict:
        """Call Pixtral for analysis"""
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
    
    def get_movement_analysis(self, image_base64: str) -> Dict:
        """Get movement validation analysis using optimal 8x8 grid"""
        print("\n🧭 MOVEMENT ANALYSIS")
        print("=" * 50)
        
        # Add optimal grid overlay
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        grid_image = self.add_light_grey_grid(image, 8)
        
        # Save grid image
        grid_path = self.output_dir / "movement_analysis_grid.png"
        grid_image.save(grid_path)
        print(f"💾 Grid overlay saved to: {grid_path}")
        
        grid_base64 = self.image_to_base64(grid_image)
        
        # Movement analysis prompt (using our proven terrain similarity approach)
        prompt = """POKEMON MOVEMENT AND CONTEXT ANALYSIS

You are analyzing a Pokemon overworld scene with 8x8 light grey grid overlay.

PLAYER POSITION: Center tile at coordinate (4,4)

ANALYSIS TASKS:
1. MOVEMENT VALIDATION - Use terrain similarity matching
2. LOCATION CLASSIFICATION - Identify area type  
3. GAME CONTEXT - Determine current game state

TERRAIN MATCHING RULES:
- Player's current tile shows what "walkable" terrain looks like
- Adjacent terrain similar to player position = WALKABLE
- Clearly different terrain (dense trees, water, walls) = BLOCKED

REQUIRED RESPONSE FORMAT:
```
PLAYER_TERRAIN: [describe current terrain type]
LOCATION_CLASS: [forest/town/route/water/cave/building/gym/center]

MOVEMENT_VALIDATION:
UP: [WALKABLE/BLOCKED] - [terrain comparison]
DOWN: [WALKABLE/BLOCKED] - [terrain comparison]
LEFT: [WALKABLE/BLOCKED] - [terrain comparison]  
RIGHT: [WALKABLE/BLOCKED] - [terrain comparison]

GAME_CONTEXT: [overworld_navigation/battle/menu/dialogue/inventory]

SUMMARY:
Valid directions: [list walkable directions]
Current activity: [what the player is doing]
```

Focus on terrain similarity for movement validation."""
        
        result = self.call_pixtral(prompt, grid_base64)
        
        if result["success"]:
            print(f"✅ Movement analysis completed")
            # Parse the response for structured data (simplified version)
            response = result['response'].lower()
            
            # Extract location class
            location_class = "unknown"
            for loc_type in ["forest", "town", "route", "water", "cave", "building", "gym", "center"]:
                if loc_type in response:
                    location_class = loc_type
                    break
            
            # Extract game context
            game_context = "unknown"
            for context_type in ["overworld_navigation", "battle", "menu", "dialogue", "inventory"]:
                if context_type in response:
                    game_context = context_type
                    break
            
            # Extract valid movements
            valid_movements = []
            for direction in ["up", "down", "left", "right"]:
                if f"{direction}: walkable" in response:
                    valid_movements.append(direction)
            
            result["parsed_data"] = {
                "location_class": location_class,
                "game_context": game_context,
                "valid_movements": valid_movements
            }
            
            print(f"📍 Location: {location_class}")
            print(f"🎮 Context: {game_context}")
            print(f"✅ Valid movements: {valid_movements}")
            
        else:
            print(f"❌ Movement analysis failed: {result['error']}")
        
        return result
    
    def select_optimal_prompt(self, movement_data: Dict) -> Dict:
        """Select best prompt template based on movement analysis"""
        print("\n🎯 PROMPT SELECTION")
        print("=" * 50)
        
        parsed_data = movement_data.get("parsed_data", {})
        location_class = parsed_data.get("location_class", "unknown")
        game_context = parsed_data.get("game_context", "unknown") 
        valid_movements = parsed_data.get("valid_movements", [])
        
        # Create prompt selection query
        prompt_list = "\n".join([f"- {prompt}" for prompt in self.available_prompts])
        
        selection_prompt = f"""POKEMON PROMPT TEMPLATE SELECTION

Based on the current game analysis, select the most appropriate prompt template.

CURRENT GAME STATE:
- Location Type: {location_class}
- Game Context: {game_context}
- Valid Movements: {valid_movements}
- Movement Count: {len(valid_movements)} directions available

AVAILABLE PROMPT TEMPLATES:
{prompt_list}

SELECTION CRITERIA:
- For overworld navigation in any location → "exploration_strategy" or "ai_navigation_with_memory_control"
- For battles → "battle_analysis" or "ai_battle_with_context_loading"
- For being stuck (0 valid movements) → "stuck_recovery" or "ai_emergency_recovery_with_escalation"
- For inventory management → "inventory_analysis"
- For party management → "pokemon_party_analysis"
- For complex navigation/mazes → "ai_maze_with_solution_memory"
- For general task planning → "task_analysis"

CURRENT SITUATION ANALYSIS:
Location: {location_class} suggests this is a {"navigation" if location_class in ["forest", "town", "route"] else "special"} scenario
Context: {game_context} indicates {"standard overworld exploration" if game_context == "overworld_navigation" else "special game state"}
Movement: {len(valid_movements)} valid directions {"(normal movement)" if len(valid_movements) > 0 else "(stuck - need recovery)"}

REQUIRED RESPONSE:
```
SELECTED_PROMPT: [exact template name from the list above]
REASON: [why this template is optimal for the current situation]
CONFIDENCE: [high/medium/low]
```

Choose the most appropriate template for Pokemon overworld navigation in a {location_class} area."""
        
        result = self.call_pixtral(selection_prompt, "")  # No image needed for template selection
        
        if result["success"]:
            print(f"✅ Prompt selection completed")
            
            # Parse selected prompt
            response = result['response'].lower()
            selected_prompt = "exploration_strategy"  # Default fallback
            
            for prompt_name in self.available_prompts:
                if prompt_name in response:
                    selected_prompt = prompt_name
                    break
            
            result["selected_prompt"] = selected_prompt
            print(f"🎯 Selected template: {selected_prompt}")
            
            # Extract confidence level
            confidence = "medium"
            if "high" in response:
                confidence = "high"
            elif "low" in response:
                confidence = "low"
            
            result["confidence"] = confidence
            print(f"📊 Confidence: {confidence}")
            
        else:
            print(f"❌ Prompt selection failed: {result['error']}")
            result["selected_prompt"] = "exploration_strategy"  # Safe fallback
            result["confidence"] = "low"
        
        return result
    
    def run_integrated_analysis(self) -> None:
        """Run complete movement analysis + prompt selection"""
        print("🎯 Pokemon Integrated Navigation Analysis")
        print("=" * 70)
        print("Movement Analysis → Location Classification → Prompt Selection")
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
            original_path = self.output_dir / "original_screenshot.png"
            original_image.save(original_path)
            print(f"💾 Original screenshot saved to: {original_path}")
        
        # Step 1: Movement Analysis
        movement_result = self.get_movement_analysis(screenshot_base64)
        
        if not movement_result.get("success", False):
            print("❌ Cannot proceed without movement analysis")
            return
        
        # Step 2: Prompt Selection
        selection_result = self.select_optimal_prompt(movement_result)
        
        # Step 3: Save Combined Results
        self.save_integrated_results(movement_result, selection_result)
        
        # Step 4: Final Summary
        self.display_final_summary(movement_result, selection_result)
    
    def save_integrated_results(self, movement_result: Dict, selection_result: Dict) -> None:
        """Save complete analysis results"""
        # Combined JSON results
        json_file = self.output_dir / "integrated_analysis.json"
        combined_results = {
            "timestamp": self.timestamp,
            "movement_analysis": movement_result,
            "prompt_selection": selection_result,
            "final_recommendation": {
                "location_class": movement_result.get("parsed_data", {}).get("location_class", "unknown"),
                "selected_prompt": selection_result.get("selected_prompt", "exploration_strategy"),
                "confidence": selection_result.get("confidence", "medium"),
                "valid_movements": movement_result.get("parsed_data", {}).get("valid_movements", [])
            }
        }
        
        with open(json_file, 'w') as f:
            json.dump(combined_results, f, indent=2)
        
        # Human-readable summary
        summary_file = self.output_dir / "analysis_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("🎯 Pokemon Integrated Navigation Analysis Results\n")
            f.write("=" * 60 + "\n\n")
            
            # Movement Analysis Section
            movement_data = movement_result.get("parsed_data", {})
            f.write("🧭 MOVEMENT ANALYSIS:\n")
            f.write(f"Location Class: {movement_data.get('location_class', 'unknown')}\n")
            f.write(f"Game Context: {movement_data.get('game_context', 'unknown')}\n")
            f.write(f"Valid Movements: {movement_data.get('valid_movements', [])}\n")
            f.write(f"Movement Count: {len(movement_data.get('valid_movements', []))}\n\n")
            
            # Prompt Selection Section
            f.write("🎯 PROMPT SELECTION:\n")
            f.write(f"Selected Template: {selection_result.get('selected_prompt', 'exploration_strategy')}\n")
            f.write(f"Confidence Level: {selection_result.get('confidence', 'medium')}\n\n")
            
            # Integration for Eevee
            f.write("🤖 EEVEE INTEGRATION:\n")
            f.write("Ready for integration into main navigation system\n")
            f.write("Dictionary format available in JSON file\n")
            f.write(f"Recommended prompt: {selection_result.get('selected_prompt', 'exploration_strategy')}\n")
        
        print(f"\n💾 Results saved to: {json_file}")
        print(f"📝 Summary saved to: {summary_file}")
    
    def display_final_summary(self, movement_result: Dict, selection_result: Dict) -> None:
        """Display final integrated analysis summary"""
        print("\n" + "=" * 70)
        print("🎯 INTEGRATED ANALYSIS SUMMARY")
        print("=" * 70)
        
        movement_data = movement_result.get("parsed_data", {})
        
        print(f"📍 Location: {movement_data.get('location_class', 'unknown')}")
        print(f"🎮 Context: {movement_data.get('game_context', 'unknown')}")
        print(f"✅ Valid Movements: {movement_data.get('valid_movements', [])}")
        print(f"🎯 Selected Prompt: {selection_result.get('selected_prompt', 'exploration_strategy')}")
        print(f"📊 Confidence: {selection_result.get('confidence', 'medium')}")
        
        print(f"\n🤖 FOR EEVEE INTEGRATION:")
        print("```python")
        print("{")
        print(f'  "location_class": "{movement_data.get("location_class", "unknown")}",')
        print(f'  "valid_movements": {movement_data.get("valid_movements", [])},')
        print(f'  "selected_prompt": "{selection_result.get("selected_prompt", "exploration_strategy")}",')
        print(f'  "confidence": "{selection_result.get("confidence", "medium")}"')
        print("}")
        print("```")
        
        print(f"\n✅ Complete navigation analysis ready for Eevee system!")

def main():
    """Main integrated analysis execution"""
    print("🎯 Pokemon Integrated Navigation Analysis")
    print("=" * 70)
    print("Complete system: Movement → Location → Prompt Selection")
    print()
    
    selector = PromptSelector()
    selector.run_integrated_analysis()
    
    print("\n✅ Integrated analysis complete!")
    print("\nGenerated:")
    print("1. Movement validation with terrain similarity")
    print("2. Location classification") 
    print("3. Optimal prompt template selection")
    print("4. Structured output for Eevee integration")

if __name__ == "__main__":
    main()