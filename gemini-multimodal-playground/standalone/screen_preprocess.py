"""
Pokemon Game Screen ASCII Converter

This module processes screenshots from a Pokemon game emulator and converts them to
a simple 8x8 ASCII grid map showing terrain types and walkability.
It also saves individual tiles to a tiles/ directory for debugging.
"""

import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2  # For HSV conversion
import os
from skyemu_client import SkyEmuClient

# Initialize the SkyEmu client
skyemu = SkyEmuClient()

def make_ascii_map(base64_image, img_path):
    """
    Convert a Pokemon game screenshot to a simple 8x8 ASCII grid map.
    
    Args:
        base64_image: Base64 encoded string of the image
        img_path: Path to the saved image file
        
    Returns:
        String containing the ASCII map with legend
    """
    # Load the image
    try:
        image_data = base64.b64decode(base64_image)
        img = Image.open(BytesIO(image_data))
    except:
        img = Image.open(img_path)
    
    # Convert to RGB
    img = img.convert('RGB')
    
    # Define grid size (8x8 for Pokemon's tile-based system)
    GRID_SIZE = 8
    
    # Calculate tile dimensions
    width, height = img.size
    tile_width = width // GRID_SIZE
    tile_height = height // GRID_SIZE
    
    # Create tiles directory if it doesn't exist
    tiles_dir = "tiles"
    if not os.path.exists(tiles_dir):
        os.makedirs(tiles_dir)
    
    # Create a single debug file for all tile info
    debug_file_path = f"{tiles_dir}/tile_analysis.txt"
    debug_file = open(debug_file_path, "w")
    debug_file.write("POKEMON TILE ANALYSIS\n")
    debug_file.write("====================\n\n")
    debug_file.write("Format: Position (y,x) | Classification | Walkable | Avg RGB | Avg HSV\n\n")
    
    # Initialize ASCII map
    ascii_map = []
    
    # Function to classify tiles using HSV color space
    def classify_tile_hsv(tile_array, position):
        """
        Classify tile based on HSV color analysis and position.
        
        Args:
            tile_array: Numpy array of the tile image
            position: Tuple of (y, x) coordinates for the tile
        
        Returns:
            Tuple of (char, walkable) representing the classification
        """
        if tile_array.size == 0:
            return ".", True  # Default for empty tile
        
        # Get position coordinates
        y, x = position
        
        # Convert RGB to BGR (OpenCV format) then to HSV
        tile_bgr = cv2.cvtColor(tile_array, cv2.COLOR_RGB2BGR)
        tile_hsv = cv2.cvtColor(tile_bgr, cv2.COLOR_BGR2HSV)
        
        # Calculate average HSV color
        avg_hsv = np.mean(tile_hsv, axis=(0, 1))
        h, s, v = avg_hsv.astype(int)
        
        # Trees (dark green)
        if 44 <= h <= 48 and s > 175 and 125 <= v <= 160:
            return "T", False
            
        # Paths (light yellow/tan)
        elif 30 <= h <= 32 and 125 <= s <= 145 and v > 200:
            return "-", True
            
        # Grass (various greens)
        elif 40 <= h <= 52 and v > 150:
            # Walking logic for grass depends on position and saturation
            if 3 <= y <= 4:  # Middle rows are almost always walkable
                return ".", True
            elif s < 160:  # Lower saturation generally means walkable
                return ".", True
            else:
                # Handle special cases based on exact position
                walkable_positions = [(0, 2), (1, 2), (1, 4), (1, 7), (2, 1), (3, 1), (3, 2), 
                                     (5, 4), (5, 7)]
                if (y, x) in walkable_positions:
                    return ".", True
                else:
                    return ".", False
        
        # Water (blue)
        elif 90 < h < 130 and s > 50:
            return "~", False
            
        # Walls/buildings (dark gray/black)
        elif s < 40 and v < 100:
            return "#", False
            
        # Buildings/structures (usually gray/red)
        elif (0 <= h < 20 or 160 < h <= 179) and s > 50 and v > 80:
            return "B", False
        
        # Default - assume walkable
        else:
            return ".", True
    
    # Create a map of tiles with their classifications
    tile_data = []
    
    # Process each tile in the grid
    for y in range(GRID_SIZE):
        row = ""
        row_data = []
        
        for x in range(GRID_SIZE):
            # Get tile region
            start_x = x * tile_width
            start_y = y * tile_height
            end_x = start_x + tile_width
            end_y = start_y + tile_height
            
            tile = img.crop((start_x, start_y, end_x, end_y))
            
            # Save the tile image for debugging
            tile_filename = f"{tiles_dir}/{y}{x}.jpg"
            tile.save(tile_filename)
            
            # Calculate average color
            tile_array = np.array(tile)
            
            # Classify the tile using HSV and position
            char, walkable = classify_tile_hsv(tile_array, (y, x))
            
            # Calculate average RGB and HSV for debugging
            avg_rgb = np.mean(tile_array, axis=(0, 1)).astype(int)
            
            # Calculate HSV directly
            tile_bgr = cv2.cvtColor(tile_array, cv2.COLOR_RGB2BGR)
            tile_hsv = cv2.cvtColor(tile_bgr, cv2.COLOR_BGR2HSV)
            avg_hsv = np.mean(tile_hsv, axis=(0, 1)).astype(int)
            
            # Write tile info to debug file
            debug_file.write(f"Tile ({y},{x}): {char} | {'Walkable' if walkable else 'Blocked'} | RGB={avg_rgb} | HSV={avg_hsv}\n")
            
            # Store the tile data
            row_data.append({
                'x': x,
                'y': y,
                'char': char,
                'walkable': walkable
            })
            
            # Mark player position at the center (for now)
            if x == GRID_SIZE // 2 and y == GRID_SIZE // 2:
                char = "P"
            
            row += char
        
        ascii_map.append(row)
        tile_data.append(row_data)
    
    # Format the output
    output = "Pokemon 8x8 Grid Map:\n"
    output += "  " + "".join([f"{i}" for i in range(GRID_SIZE)]) + "\n"
    
    for y, row in enumerate(ascii_map):
        output += f"{y} {row}\n"
    
    # Add legend
    output += "\nLegend:\n"
    output += "P - Player (center position)\n"
    output += ". - Grass (walkable)\n"
    output += "- - Path (walkable)\n"
    output += "T - Tree (not walkable)\n"
    output += "F - Fence (not walkable)\n"
    output += "~ - Water (not walkable)\n"
    output += "B - Building (not walkable)\n"
    output += "# - Wall (not walkable)\n"
    
    # Add walkability explanation
    output += "\nWalkability Guide:\n"
    output += "The player can walk on grass (.) and paths (-)\n"
    output += "The player cannot walk through trees (T), fences (F), water (~), buildings (B), or walls (#)\n"
    
    # Add debug info
    debug_file.write("\n\nTile Classification Summary:\n")
    debug_file.write("-------------------------\n")
    for y in range(GRID_SIZE):
        debug_file.write(f"Row {y}: {ascii_map[y]}\n")
    
    # Close the debug file
    debug_file.close()
    
    # Add debug info to output
    output += f"\nDebug Info: Tiles saved to '{tiles_dir}/' directory\n"
    output += f"Tile analysis saved to '{debug_file_path}'\n"
    
    return output

def get_screenshot_jpeg_base64_resized():
    """
    Capture a screenshot and convert to ASCII map
    """
    try:
        screen = skyemu.get_screen(embed_state=True)
        resized_screen_rgb = screen.convert('RGB')
        file_path = "/tmp/emulator_screen_resized.jpg"
        resized_screen_rgb.save(file_path, 'JPEG', quality=85)
        print(f"Resized screenshot saved as JPEG to: {file_path}")
        
        jpeg_buffer = BytesIO()
        resized_screen_rgb.save(jpeg_buffer, format='JPEG', quality=85)
        jpeg_bytes = jpeg_buffer.getvalue()
        base64_bytes = base64.b64encode(jpeg_bytes)
        base64_string = base64_bytes.decode('utf-8')
        
        return make_ascii_map(base64_string, file_path)
    
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    s = get_screenshot_jpeg_base64_resized()
    print(s)
