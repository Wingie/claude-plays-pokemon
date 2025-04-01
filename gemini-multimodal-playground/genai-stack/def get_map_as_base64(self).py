def get_map_as_base64(self):
    """Convert the current map visualization to a base64 string for embedding in prompts"""
    if self.current_map is None or self.player_position is None:
        return None
            
    # Create a visualization of the current map
    # Create a dictionary with the map data
    map_data = {
        'map_grid': self.current_map,
        'player_position': self.player_position,
        # Include other relevant data
        'stair_position': None  # Add if you have it
    }
    
    # Call visualize_enhanced_map with the map data
    map_vis = self.visualize_enhanced_map(map_data)
    
    # Convert to base64
    try:
        # Convert to PIL Image
        map_pil = Image.fromarray(map_vis)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        map_pil.save(buffer, format="PNG")
        
        # Convert to base64
        map_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return map_base64
    except Exception as e:
        print(f"Error converting map to base64: {str(e)}")
        return None