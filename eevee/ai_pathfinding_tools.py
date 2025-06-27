"""
AI Pathfinding Tools for Mistral
Provides coordinate-based navigation tools for the AI agent
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

try:
    from coordinate_mapper import CoordinateMapper
    from healing_bookmark_system import HealingBookmarkSystem
    from pathfinding_helpers import NavigationHelper
    PATHFINDING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Pathfinding tools not available: {e}")
    PATHFINDING_AVAILABLE = False

class AIPathfindingTools:
    """
    Pathfinding tools specifically designed for AI agent use
    Provides brief, efficient navigation assistance with coordinate-based planning
    """
    
    def __init__(self):
        """Initialize pathfinding tools"""
        self.available = PATHFINDING_AVAILABLE
        if self.available:
            self.coordinate_mapper = CoordinateMapper()
            self.healing_system = HealingBookmarkSystem()
            self.navigation_helper = NavigationHelper()
        else:
            self.coordinate_mapper = None
            self.healing_system = None
            self.navigation_helper = None
    
    def pathfind_to_coordinate(self, current_coords: Dict[str, Any], target_x: int, target_y: int, 
                              reason: str = "navigation") -> Dict[str, Any]:
        """
        Generate pathfinding route to specific coordinates
        
        Args:
            current_coords: Current position (map_id, x, y)
            target_x: Target X coordinate
            target_y: Target Y coordinate
            reason: Brief reason for navigation
            
        Returns:
            Dict with navigation plan and button sequence
        """
        if not self.available:
            return {
                "success": False,
                "error": "Pathfinding not available",
                "button_sequence": [],
                "reasoning": "pathfinding_unavailable"
            }
        
        try:
            current_x = current_coords.get("x", 0)
            current_y = current_coords.get("y", 0)
            map_id = current_coords.get("map_id", 0)
            
            # Calculate simple directional movement
            dx = target_x - current_x
            dy = target_y - current_y
            
            button_sequence = []
            
            # Generate movement sequence (horizontal first, then vertical)
            if dx > 0:
                button_sequence.extend(["right"] * abs(dx))
            elif dx < 0:
                button_sequence.extend(["left"] * abs(dx))
            
            if dy > 0:
                button_sequence.extend(["down"] * abs(dy))
            elif dy < 0:
                button_sequence.extend(["up"] * abs(dy))
            
            distance = abs(dx) + abs(dy)
            
            return {
                "success": True,
                "button_sequence": button_sequence,
                "distance": distance,
                "target_coords": {"x": target_x, "y": target_y},
                "reasoning": f"{reason}_to_({target_x},{target_y})_dist_{distance}",
                "observations": f"Planning route: {distance} steps to ({target_x},{target_y})",
                "estimated_time": distance * 0.5  # Rough estimate: 0.5 seconds per step
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "button_sequence": [],
                "reasoning": f"pathfinding_failed_{reason}"
            }
    
    def pathfind_to_healing_location(self, current_coords: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find route to nearest known healing location
        
        Args:
            current_coords: Current position
            
        Returns:
            Dict with navigation plan to Pokemon Center
        """
        if not self.available:
            return {
                "success": False,
                "error": "Healing pathfinding not available",
                "reasoning": "healing_system_unavailable"
            }
        
        try:
            # Find nearest healing location
            healing_location = self.healing_system.get_nearest_healing_location(current_coords)
            
            if not healing_location:
                return {
                    "success": False,
                    "error": "No known healing locations",
                    "reasoning": "no_healing_locations_found",
                    "observations": "No Pokemon Centers bookmarked - explore to find one"
                }
            
            # Generate route to healing location
            result = self.pathfind_to_coordinate(
                current_coords,
                healing_location["x"],
                healing_location["y"],
                "healing"
            )
            
            if result["success"]:
                result.update({
                    "healing_location": healing_location,
                    "reasoning": f"healing_route_to_{healing_location['location_name']}",
                    "observations": f"Route to {healing_location['location_name']}: {result['distance']} steps",
                    "success_rate": healing_location.get("success_rate", 0)
                })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reasoning": "healing_pathfinding_error"
            }
    
    def bookmark_current_location(self, current_coords: Dict[str, Any], location_type: str, 
                                 name: str = "Custom Location") -> Dict[str, Any]:
        """
        Bookmark current location for future reference
        
        Args:
            current_coords: Current position
            location_type: Type of location (healing, training, shop, etc.)
            name: Custom name for the location
            
        Returns:
            Dict with bookmark result
        """
        if not self.available:
            return {
                "success": False,
                "error": "Bookmarking not available",
                "reasoning": "bookmark_system_unavailable"
            }
        
        try:
            # Use coordinate mapper to record location
            session_id = f"bookmark_{int(time.time())}"
            screenshot_path = f"bookmark_{name.replace(' ', '_')}.png"
            
            scene_analysis = {
                "scene_type": location_type,
                "valid_movements": ["up", "down", "left", "right"]
            }
            
            success = self.coordinate_mapper.record_coordinate(
                current_coords, screenshot_path, session_id, scene_analysis
            )
            
            if success:
                return {
                    "success": True,
                    "reasoning": f"bookmarked_{location_type}_{name.replace(' ', '_')}",
                    "observations": f"Saved {name} at ({current_coords.get('x', 0)},{current_coords.get('y', 0)})",
                    "bookmark_info": {
                        "name": name,
                        "type": location_type,
                        "coordinates": {"x": current_coords.get("x", 0), "y": current_coords.get("y", 0)},
                        "map_id": current_coords.get("map_id", 0)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to save bookmark",
                    "reasoning": "bookmark_save_failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reasoning": "bookmark_error"
            }
    
    def get_nearby_landmarks(self, current_coords: Dict[str, Any], radius: int = 10) -> Dict[str, Any]:
        """
        Get nearby known landmarks and locations
        
        Args:
            current_coords: Current position
            radius: Search radius
            
        Returns:
            Dict with nearby landmarks information
        """
        if not self.available:
            return {
                "success": False,
                "error": "Landmark search not available",
                "landmarks": []
            }
        
        try:
            map_id = current_coords.get("map_id", 0)
            x = current_coords.get("x", 0)
            y = current_coords.get("y", 0)
            
            # Get nearby coordinates from mapper
            nearby_coords = self.coordinate_mapper.get_coordinates_near(map_id, x, y, radius)
            
            # Get healing locations
            healing_locations = self.healing_system.get_all_healing_locations(map_id)
            
            landmarks = []
            
            # Add coordinate-based landmarks
            for coord in nearby_coords[:5]:  # Limit to 5 closest
                landmarks.append({
                    "type": "coordinate",
                    "name": f"{coord.get('scene_type', 'location')}",
                    "x": coord["x"],
                    "y": coord["y"],
                    "distance": coord["distance"],
                    "scene_type": coord.get("scene_type", "unknown")
                })
            
            # Add healing locations within radius
            for healing_loc in healing_locations:
                heal_distance = abs(healing_loc["x"] - x) + abs(healing_loc["y"] - y)
                if heal_distance <= radius:
                    landmarks.append({
                        "type": "healing",
                        "name": healing_loc["location_name"],
                        "x": healing_loc["x"],
                        "y": healing_loc["y"],
                        "distance": heal_distance,
                        "success_rate": healing_loc.get("success_rate", 0),
                        "scene_type": "pokemon_center"
                    })
            
            # Sort by distance
            landmarks.sort(key=lambda l: l["distance"])
            
            return {
                "success": True,
                "landmarks": landmarks[:8],  # Limit to 8 for brevity
                "total_found": len(landmarks),
                "reasoning": f"found_{len(landmarks)}_landmarks_within_{radius}",
                "observations": f"{len(landmarks)} landmarks within {radius} steps"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "landmarks": [],
                "reasoning": "landmark_search_failed"
            }
    
    def calculate_route_to(self, current_coords: Dict[str, Any], target_coords: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate route between two coordinate sets
        
        Args:
            current_coords: Starting position
            target_coords: Target position
            
        Returns:
            Dict with route calculation
        """
        if not self.available:
            return {
                "success": False,
                "error": "Route calculation not available",
                "reasoning": "route_calc_unavailable"
            }
        
        try:
            # Extract coordinates
            start_x = current_coords.get("x", 0)
            start_y = current_coords.get("y", 0)
            target_x = target_coords.get("x", 0)
            target_y = target_coords.get("y", 0)
            
            # Check if same map
            if current_coords.get("map_id", 0) != target_coords.get("map_id", 0):
                return {
                    "success": False,
                    "error": "Cross-map navigation not supported",
                    "reasoning": "different_maps",
                    "observations": "Cannot route between different maps"
                }
            
            # Use pathfind_to_coordinate
            return self.pathfind_to_coordinate(current_coords, target_x, target_y, "route_calculation")
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reasoning": "route_calculation_error"
            }
    
    def get_navigation_context(self, current_coords: Dict[str, Any], goal: str = "") -> str:
        """
        Generate navigation context for AI prompt injection
        Provides brief, relevant coordinate and landmark information
        
        Args:
            current_coords: Current position
            goal: Current goal description
            
        Returns:
            Formatted text for prompt injection
        """
        if not self.available:
            return ""
        
        try:
            map_id = current_coords.get("map_id", 0)
            x = current_coords.get("x", 0)
            y = current_coords.get("y", 0)
            
            # Get nearby landmarks
            landmarks_result = self.get_nearby_landmarks(current_coords, radius=8)
            landmarks = landmarks_result.get("landmarks", [])
            
            # Build context string
            context_lines = [
                f"COORDINATE CONTEXT: Map {map_id} at ({x},{y})"
            ]
            
            if landmarks:
                context_lines.append("NEARBY LANDMARKS:")
                for landmark in landmarks[:3]:  # Show only closest 3 for brevity
                    distance = landmark["distance"]
                    name = landmark["name"]
                    coords = f"({landmark['x']},{landmark['y']})"
                    context_lines.append(f"  • {name} {coords} - {distance} steps")
            
            # Add goal-specific suggestions
            if "heal" in goal.lower() or "pokemon center" in goal.lower():
                healing_result = self.pathfind_to_healing_location(current_coords)
                if healing_result.get("success"):
                    healing_info = healing_result.get("healing_location", {})
                    context_lines.append(f"HEALING: {healing_info.get('location_name', 'Pokemon Center')} at ({healing_info.get('x', 0)},{healing_info.get('y', 0)}) - {healing_result.get('distance', 0)} steps")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            return f"Navigation context error: {e}"


# Tool functions for AI integration
def get_pathfinding_tools() -> AIPathfindingTools:
    """Get pathfinding tools instance"""
    return AIPathfindingTools()

def create_pathfinding_tool_functions(tools_instance: AIPathfindingTools) -> Dict[str, Any]:
    """
    Create function definitions for AI tool access
    Returns dict of functions that can be added to AI's available tools
    """
    if not tools_instance.available:
        return {}
    
    return {
        "pathfind_to_coordinate": {
            "function": tools_instance.pathfind_to_coordinate,
            "description": "Navigate to specific coordinates efficiently",
            "parameters": {
                "current_coords": "Current position data",
                "target_x": "Target X coordinate",
                "target_y": "Target Y coordinate", 
                "reason": "Brief reason for navigation"
            }
        },
        "pathfind_to_healing_location": {
            "function": tools_instance.pathfind_to_healing_location,
            "description": "Find and navigate to nearest Pokemon Center",
            "parameters": {
                "current_coords": "Current position data"
            }
        },
        "bookmark_current_location": {
            "function": tools_instance.bookmark_current_location,
            "description": "Save current location as landmark",
            "parameters": {
                "current_coords": "Current position data",
                "location_type": "Type of location (healing, training, shop)",
                "name": "Custom name for location"
            }
        },
        "get_nearby_landmarks": {
            "function": tools_instance.get_nearby_landmarks,
            "description": "Show nearby known locations and landmarks",
            "parameters": {
                "current_coords": "Current position data",
                "radius": "Search radius (default 10)"
            }
        },
        "calculate_route_to": {
            "function": tools_instance.calculate_route_to,
            "description": "Calculate movement route between coordinates",
            "parameters": {
                "current_coords": "Starting position",
                "target_coords": "Target position"
            }
        }
    }