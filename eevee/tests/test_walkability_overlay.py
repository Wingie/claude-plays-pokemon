#!/usr/bin/env python3
"""
Walkability Overlay Test
Create color-coded overlay based on AI analysis:
- Red: Unwalkable (trees, water, walls)
- Green: Walkable (paths, grass, open areas)
- Blue: Points of interest (NPCs, computers, items, doors)
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

class WalkabilityMapper:
    """Create AI-guided walkability overlays for Pokemon overworld scenes"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.timestamp = int(time.time())
        
        # Create directory for overlay images
        self.overlay_dir = Path(__file__).parent / f"walkability_overlays_{self.timestamp}"
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
    
    def add_coordinate_grid(self, image: Image.Image, grid_size: int = 8) -> Image.Image:
        """Add simple coordinate grid for AI analysis"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        width, height = image.size
        tile_width = width // grid_size
        tile_height = height // grid_size
        
        # Draw subtle grid lines
        for x in range(0, width, tile_width):
            draw.line([(x, 0), (x, height)], fill='#888888', width=1)
        
        for y in range(0, height, tile_height):
            draw.line([(0, y), (width, y)], fill='#888888', width=1)
        
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
                draw.text((pixel_x + 2, pixel_y + 2), coord_text, fill='#444444', font=font)
        
        return overlay_image
    
    def create_walkability_overlay(self, image: Image.Image, walkability_data: Dict) -> Image.Image:
        """Create color-coded walkability overlay"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        width, height = image.size
        grid_size = 8
        tile_width = width // grid_size
        tile_height = height // grid_size
        
        # Color coding
        colors = {
            'walkable': '#00FF0088',      # Green with transparency
            'unwalkable': '#FF000088',    # Red with transparency  
            'interest': '#0088FF88'       # Blue with transparency
        }
        
        # Apply color coding based on AI analysis
        for tile_coord, tile_type in walkability_data.items():
            if ',' in tile_coord:
                try:
                    x_str, y_str = tile_coord.split(',')
                    tile_x, tile_y = int(x_str), int(y_str)
                    
                    if 0 <= tile_x < grid_size and 0 <= tile_y < grid_size:
                        pixel_x = tile_x * tile_width
                        pixel_y = tile_y * tile_height
                        
                        color = colors.get(tile_type, '#FFFFFF44')
                        
                        # Draw semi-transparent overlay
                        overlay = Image.new('RGBA', (tile_width, tile_height), color)
                        overlay_image.paste(overlay, (pixel_x, pixel_y), overlay)
                        
                        # Add border for clarity
                        border_color = color.replace('88', 'FF')  # Make border opaque
                        draw.rectangle([pixel_x, pixel_y, pixel_x + tile_width, pixel_y + tile_height], 
                                     outline=border_color, width=2)
                        
                except ValueError:
                    continue
        
        return overlay_image
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image back to base64"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def call_pixtral_for_analysis(self, prompt: str, image_base64: str) -> Dict:
        """Call Pixtral for coordinate analysis"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_base64,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=800
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
    
    def parse_coordinate_analysis(self, response_text: str) -> Dict[str, str]:
        """Parse AI response to extract coordinate classifications"""
        walkability_data = {}
        
        # Patterns to match different classifications
        patterns = {
            'walkable': [
                r'(\d+,\d+).*(?:walkable|path|grass|open|clear|passable)',
                r'walkable.*(\d+,\d+)',
                r'(\d+,\d+).*green',
                r'green.*(\d+,\d+)'
            ],
            'unwalkable': [
                r'(\d+,\d+).*(?:tree|water|wall|blocked|unwalkable|obstacle)',
                r'(?:tree|water|wall|blocked|unwalkable|obstacle).*(\d+,\d+)',
                r'(\d+,\d+).*red',
                r'red.*(\d+,\d+)'
            ],
            'interest': [
                r'(\d+,\d+).*(?:npc|computer|door|item|sign|building|entrance)',
                r'(?:npc|computer|door|item|sign|building|entrance).*(\d+,\d+)',
                r'(\d+,\d+).*blue',
                r'blue.*(\d+,\d+)'
            ]
        }
        
        response_lower = response_text.lower()
        
        for classification, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, response_lower, re.IGNORECASE)
                for match in matches:
                    coord = match if isinstance(match, str) else match[0]
                    if coord and ',' in coord:
                        walkability_data[coord] = classification
        
        return walkability_data
    
    def analyze_walkability(self, image_base64: str) -> Dict:
        """Get AI analysis of walkability for each coordinate"""
        print("\n🗺️ WALKABILITY ANALYSIS")
        print("=" * 60)
        
        # Add coordinate grid
        image = self.decode_base64_to_image(image_base64)
        if not image:
            return {"success": False, "error": "Failed to decode image"}
        
        grid_image = self.add_coordinate_grid(image)
        
        # Save analysis grid
        grid_path = self.overlay_dir / "analysis_grid.png"
        grid_image.save(grid_path)
        print(f"💾 Analysis grid saved to: {grid_path}")
        
        grid_base64 = self.image_to_base64(grid_image)
        
        prompt = """POKEMON OVERWORLD WALKABILITY ANALYSIS

You are analyzing a Pokemon overworld scene with coordinate grid (0,0 to 7,7).

CRITICAL: Look carefully at each coordinate to identify terrain features.

VISUAL IDENTIFICATION GUIDE:
🌳 TREES: Dark green dense areas with tree-like textures - UNWALKABLE
🌊 WATER: Blue areas representing rivers, ponds, lakes - UNWALKABLE  
🏠 BUILDINGS: Solid structures, walls, houses - UNWALKABLE
🧑 NPCs: Character sprites (people/trainers) - POINTS OF INTEREST
📱 OBJECTS: Signs, computers, items, doors - POINTS OF INTEREST
🛤️ PATHS: Clear walkable ground, light grass, routes - WALKABLE

CLASSIFICATION RULES:
🟢 WALKABLE: Clear ground, light grass, paths, walkable floor areas
🔴 UNWALKABLE: Trees (dark green), water (blue), walls, buildings, solid obstacles
🔵 INTEREST: NPCs, signs, computers, doors, interactive objects

ANALYSIS INSTRUCTIONS:
1. Look at EACH coordinate carefully
2. Identify the visual terrain/object at that coordinate
3. Apply the classification rules strictly
4. Trees and water are ALWAYS unwalkable
5. Clear paths and light grass are walkable

RESPONSE FORMAT - For each coordinate (0,0 through 7,7):
"X,Y: UNWALKABLE - tree" (if you see a tree)
"X,Y: UNWALKABLE - water" (if you see water/blue area)
"X,Y: WALKABLE - path" (if you see clear walkable ground)
"X,Y: INTEREST - NPC" (if you see a character)

BE SPECIFIC about what terrain feature you see at each coordinate."""
        
        result = self.call_pixtral_for_analysis(prompt, grid_base64)
        
        if result["success"]:
            print(f"✅ AI Analysis received ({len(result['response'])} characters)")
            
            # Parse response for coordinate classifications  
            walkability_data = self.parse_coordinate_analysis(result['response'])
            result["walkability_data"] = walkability_data
            
            print(f"📊 Parsed {len(walkability_data)} coordinate classifications")
            
            # Display summary
            walkable = len([k for k, v in walkability_data.items() if v == 'walkable'])
            unwalkable = len([k for k, v in walkability_data.items() if v == 'unwalkable'])
            interest = len([k for k, v in walkability_data.items() if v == 'interest'])
            
            print(f"   🟢 Walkable: {walkable}")
            print(f"   🔴 Unwalkable: {unwalkable}")
            print(f"   🔵 Points of Interest: {interest}")
            
        else:
            print(f"❌ Analysis failed: {result['error']}")
        
        return result
    
    def create_walkability_map(self, image_base64: str) -> None:
        """Create complete walkability visualization"""
        print("\n🎨 CREATING WALKABILITY MAP")
        print("=" * 60)
        
        # Get AI analysis
        analysis_result = self.analyze_walkability(image_base64)
        
        if not analysis_result.get("success", False):
            print("❌ Cannot create walkability map without analysis")
            return
        
        walkability_data = analysis_result.get("walkability_data", {})
        
        if not walkability_data:
            print("⚠️ No walkability data found in analysis")
            return
        
        # Create walkability overlay
        image = self.decode_base64_to_image(image_base64)
        if not image:
            print("❌ Failed to decode image for overlay")
            return
        
        walkability_overlay = self.create_walkability_overlay(image, walkability_data)
        
        # Save walkability map
        map_path = self.overlay_dir / "walkability_map.png"
        walkability_overlay.save(map_path)
        print(f"💾 Walkability map saved to: {map_path}")
        
        # Save analysis results
        self.save_walkability_results(analysis_result, walkability_data)
        
        print("\n🎯 WALKABILITY MAP LEGEND:")
        print("🟢 Green overlay: Walkable areas (player can move)")
        print("🔴 Red overlay: Unwalkable areas (blocked by obstacles)")
        print("🔵 Blue overlay: Points of interest (NPCs, items, doors)")
    
    def save_walkability_results(self, analysis_result: Dict, walkability_data: Dict) -> None:
        """Save walkability analysis results"""
        # JSON results
        json_file = Path(__file__).parent / f"walkability_results_{self.timestamp}.json"
        results = {
            "timestamp": self.timestamp,
            "analysis": analysis_result,
            "walkability_data": walkability_data,
            "summary": {
                "total_coordinates": len(walkability_data),
                "walkable": len([k for k, v in walkability_data.items() if v == 'walkable']),
                "unwalkable": len([k for k, v in walkability_data.items() if v == 'unwalkable']),
                "interest": len([k for k, v in walkability_data.items() if v == 'interest'])
            }
        }
        
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Human-readable output
        output_file = Path(__file__).parent / "walkability_output.txt"
        with open(output_file, 'w') as f:
            f.write("🗺️ Pokemon Overworld Walkability Analysis\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"OVERLAY IMAGES: {self.overlay_dir}\n")
            f.write("-" * 60 + "\n\n")
            
            f.write("COORDINATE CLASSIFICATIONS:\n")
            for coord, classification in sorted(walkability_data.items()):
                f.write(f"{coord}: {classification.upper()}\n")
            
            f.write(f"\nSUMMARY:\n")
            f.write(f"🟢 Walkable: {results['summary']['walkable']}\n")
            f.write(f"🔴 Unwalkable: {results['summary']['unwalkable']}\n")
            f.write(f"🔵 Points of Interest: {results['summary']['interest']}\n")
            f.write(f"📊 Total Analyzed: {results['summary']['total_coordinates']}\n")
            
            f.write(f"\nAI ANALYSIS:\n")
            f.write(analysis_result.get('response', 'N/A'))
        
        print(f"\n💾 Results saved to: {json_file}")
        print(f"📝 Output saved to: {output_file}")
    
    def run_walkability_mapping(self) -> None:
        """Run complete walkability mapping process"""
        print("🗺️ Pokemon Overworld Walkability Mapping")
        print("=" * 70)
        print("Creating AI-guided walkability overlays:")
        print("🟢 Green: Walkable areas")
        print("🔴 Red: Unwalkable obstacles") 
        print("🔵 Blue: Points of interest")
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
        
        # Create walkability map
        self.create_walkability_map(screenshot_base64)

def main():
    """Main walkability mapping execution"""
    print("🗺️ Pokemon Overworld Walkability Mapping")
    print("=" * 70)
    print("AI-guided navigation assistance with color-coded overlays")
    print()
    
    mapper = WalkabilityMapper()
    mapper.run_walkability_mapping()
    
    print("\n✅ Walkability mapping complete!")
    print("\nGenerated Files:")
    print("1. analysis_grid.png - Coordinate grid for AI analysis")
    print("2. walkability_map.png - Color-coded walkability overlay")
    print("3. walkability_output.txt - Detailed analysis results")
    print("\nUse the walkability map to guide Pokemon navigation!")

if __name__ == "__main__":
    main()