"""
Pathfinding Helper Functions
Navigation assistance using coordinate mapping database
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

try:
    from coordinate_mapper import CoordinateMapper
    COORDINATE_MAPPING_AVAILABLE = True
except ImportError:
    COORDINATE_MAPPING_AVAILABLE = False
    print("⚠️ Coordinate mapping not available - pathfinding helpers disabled")

class NavigationHelper:
    """
    Navigation helper that provides pathfinding assistance using recorded coordinates
    Integrates with the AI's decision-making process
    """
    
    def __init__(self):
        """Initialize navigation helper with coordinate mapper"""
        self.available = COORDINATE_MAPPING_AVAILABLE
        if self.available:
            self.mapper = CoordinateMapper()
        else:
            self.mapper = None
    
    def suggest_next_move(self, current_coords: Dict[str, Any], goal_description: str) -> Dict[str, Any]:
        """
        Suggest next movement based on current position and goal
        
        Args:
            current_coords: Current position (map_id, x, y)
            goal_description: Natural language description of goal
            
        Returns:
            Dictionary with movement suggestion and reasoning
        """
        if not self.available:
            return {
                "suggestion": "explore",
                "direction": "random",
                "reasoning": "Coordinate mapping not available - explore randomly",
                "confidence": "low"
            }
        
        try:
            map_id = current_coords.get("map_id", 0)
            x = current_coords.get("x", 0)
            y = current_coords.get("y", 0)
            
            # Get nearby coordinates to understand local area
            nearby_coords = self.mapper.get_coordinates_near(map_id, x, y, radius=10)
            
            if not nearby_coords:
                return {
                    "suggestion": "explore",
                    "direction": "random",
                    "reasoning": "No mapped coordinates in this area - explore to map territory",
                    "confidence": "medium"
                }
            
            # Analyze goal type and suggest appropriate movement
            goal_lower = goal_description.lower()
            
            if "heal" in goal_lower or "pokemon center" in goal_lower or "pokecenter" in goal_lower:
                return self._suggest_healing_destination(current_coords, nearby_coords)
            
            elif "battle" in goal_lower or "trainer" in goal_lower or "wild" in goal_lower:
                return self._suggest_battle_location(current_coords, nearby_coords)
            
            elif "exit" in goal_lower or "door" in goal_lower or "leave" in goal_lower:
                return self._suggest_exit_route(current_coords, nearby_coords)
            
            else:
                # General exploration
                return self._suggest_exploration_direction(current_coords, nearby_coords)
        
        except Exception as e:
            return {
                "suggestion": "explore",
                "direction": "random",
                "reasoning": f"Navigation analysis failed: {e}",
                "confidence": "low"
            }
    
    def _suggest_healing_destination(self, current_coords: Dict[str, Any], nearby_coords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest movement toward healing locations"""
        # Look for indoor areas (likely to have Pokemon Centers)
        indoor_locations = [coord for coord in nearby_coords if "indoor" in coord.get("scene_type", "").lower()]
        
        if indoor_locations:
            closest_indoor = min(indoor_locations, key=lambda c: c["distance"])
            direction = self._calculate_direction(current_coords, closest_indoor)
            
            return {
                "suggestion": "move_toward_healing",
                "direction": direction,
                "target": {"x": closest_indoor["x"], "y": closest_indoor["y"]},
                "reasoning": f"Moving toward indoor area at ({closest_indoor['x']}, {closest_indoor['y']}) - likely Pokemon Center",
                "confidence": "medium"
            }
        
        # If no indoor areas, suggest exploring to find one
        unexplored_direction = self._find_unexplored_direction(current_coords, nearby_coords)
        
        return {
            "suggestion": "explore_for_healing",
            "direction": unexplored_direction,
            "reasoning": "No known healing locations nearby - exploring to find Pokemon Center",
            "confidence": "low"
        }
    
    def _suggest_battle_location(self, current_coords: Dict[str, Any], nearby_coords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest movement toward battle opportunities"""
        # Look for outdoor/grass areas (likely to have wild Pokemon)
        outdoor_locations = [coord for coord in nearby_coords if "navigation" in coord.get("scene_type", "").lower()]
        
        if outdoor_locations:
            # Prefer locations further from current position (more likely to have encounters)
            distant_outdoor = max(outdoor_locations, key=lambda c: c["distance"])
            direction = self._calculate_direction(current_coords, distant_outdoor)
            
            return {
                "suggestion": "move_toward_battle",
                "direction": direction,
                "target": {"x": distant_outdoor["x"], "y": distant_outdoor["y"]},
                "reasoning": f"Moving toward outdoor area at ({distant_outdoor['x']}, {distant_outdoor['y']}) - likely to have Pokemon encounters",
                "confidence": "medium"
            }
        
        # Default to exploring outward
        return {
            "suggestion": "explore_for_battles",
            "direction": "random",
            "reasoning": "No known battle areas nearby - exploring to find wild Pokemon",
            "confidence": "low"
        }
    
    def _suggest_exit_route(self, current_coords: Dict[str, Any], nearby_coords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest movement toward exits"""
        # Look for edge coordinates (likely exits)
        map_stats = self.mapper.get_map_statistics()
        
        if map_stats and "top_mapped_areas" in map_stats:
            current_map_info = next(
                (area for area in map_stats["top_mapped_areas"] 
                 if area["map_id"] == current_coords.get("map_id", 0)), 
                None
            )
            
            if current_map_info:
                # Move toward edges of mapped area
                x = current_coords.get("x", 0)
                y = current_coords.get("y", 0)
                
                # Calculate distance to edges (simplified)
                edge_directions = ["up", "down", "left", "right"]
                chosen_direction = edge_directions[hash(str(current_coords)) % len(edge_directions)]
                
                return {
                    "suggestion": "move_toward_exit",
                    "direction": chosen_direction,
                    "reasoning": f"Moving {chosen_direction} to find map boundary/exit",
                    "confidence": "medium"
                }
        
        return {
            "suggestion": "explore_for_exit",
            "direction": "random",
            "reasoning": "Searching for exits by exploring boundaries",
            "confidence": "low"
        }
    
    def _suggest_exploration_direction(self, current_coords: Dict[str, Any], nearby_coords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest direction for general exploration"""
        unexplored_direction = self._find_unexplored_direction(current_coords, nearby_coords)
        
        return {
            "suggestion": "explore",
            "direction": unexplored_direction,
            "reasoning": f"Exploring {unexplored_direction} to discover new areas",
            "confidence": "medium"
        }
    
    def _calculate_direction(self, from_coord: Dict[str, Any], to_coord: Dict[str, Any]) -> str:
        """Calculate primary direction to move from one coordinate to another"""
        dx = to_coord["x"] - from_coord.get("x", 0)
        dy = to_coord["y"] - from_coord.get("y", 0)
        
        # Prefer horizontal movement first
        if abs(dx) >= abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"
    
    def _find_unexplored_direction(self, current_coords: Dict[str, Any], nearby_coords: List[Dict[str, Any]]) -> str:
        """Find direction with least explored coordinates"""
        x = current_coords.get("x", 0)
        y = current_coords.get("y", 0)
        
        # Count coordinates in each direction
        direction_counts = {"up": 0, "down": 0, "left": 0, "right": 0}
        
        for coord in nearby_coords:
            coord_x, coord_y = coord["x"], coord["y"]
            
            if coord_y < y:
                direction_counts["up"] += 1
            elif coord_y > y:
                direction_counts["down"] += 1
                
            if coord_x < x:
                direction_counts["left"] += 1
            elif coord_x > x:
                direction_counts["right"] += 1
        
        # Choose direction with least coordinates (most unexplored)
        min_direction = min(direction_counts.keys(), key=lambda d: direction_counts[d])
        return min_direction
    
    def get_area_summary(self, current_coords: Dict[str, Any], radius: int = 15) -> Dict[str, Any]:
        """
        Get summary of mapped area around current position
        Useful for AI context
        """
        if not self.available:
            return {"error": "Coordinate mapping not available"}
        
        try:
            map_id = current_coords.get("map_id", 0)
            x = current_coords.get("x", 0)
            y = current_coords.get("y", 0)
            
            nearby_coords = self.mapper.get_coordinates_near(map_id, x, y, radius)
            
            # Analyze nearby area
            scene_types = {}
            total_mapped = len(nearby_coords)
            
            for coord in nearby_coords:
                scene_type = coord.get("scene_type", "unknown")
                scene_types[scene_type] = scene_types.get(scene_type, 0) + 1
            
            # Calculate exploration coverage
            expected_coords = (2 * radius + 1) ** 2  # Theoretical max coordinates in radius
            coverage_percentage = (total_mapped / expected_coords) * 100 if expected_coords > 0 else 0
            
            return {
                "current_position": {"map_id": map_id, "x": x, "y": y},
                "mapped_coordinates": total_mapped,
                "exploration_coverage": f"{coverage_percentage:.1f}%",
                "scene_types": scene_types,
                "area_summary": f"Mapped {total_mapped} coordinates within {radius} steps",
                "navigation_status": "well_mapped" if coverage_percentage > 50 else "partially_explored" if total_mapped > 5 else "unexplored"
            }
            
        except Exception as e:
            return {"error": f"Area summary failed: {e}"}
    
    def get_movement_suggestions_for_prompt(self, current_coords: Dict[str, Any], goal: str) -> str:
        """
        Generate text suggestions for AI prompt injection
        Returns formatted text suitable for adding to AI prompts
        """
        if not self.available:
            return ""
        
        try:
            movement_suggestion = self.suggest_next_move(current_coords, goal)
            area_summary = self.get_area_summary(current_coords)
            
            suggestion_text = f"""
NAVIGATION CONTEXT (from coordinate mapping):
• Current area: {area_summary.get('navigation_status', 'unknown')} - {area_summary.get('area_summary', 'no data')}
• Movement suggestion: {movement_suggestion['suggestion']} - {movement_suggestion['reasoning']}
• Recommended direction: {movement_suggestion['direction']} (confidence: {movement_suggestion['confidence']})
• Area types nearby: {', '.join(area_summary.get('scene_types', {}).keys()) or 'unknown'}
"""
            
            if movement_suggestion.get('target'):
                target = movement_suggestion['target']
                suggestion_text += f"• Target coordinates: X:{target['x']} Y:{target['y']}\n"
            
            return suggestion_text
            
        except Exception as e:
            return f"Navigation context unavailable: {e}"


# Convenience function for easy integration
def get_navigation_helper() -> NavigationHelper:
    """Get navigation helper instance"""
    return NavigationHelper()

def add_navigation_context_to_prompt(prompt: str, current_coords: Dict[str, Any], goal: str) -> str:
    """
    Add navigation context to an AI prompt
    
    Args:
        prompt: Original AI prompt
        current_coords: Current position data
        goal: Goal description
        
    Returns:
        Enhanced prompt with navigation context
    """
    helper = get_navigation_helper()
    if not helper.available:
        return prompt
    
    navigation_context = helper.get_movement_suggestions_for_prompt(current_coords, goal)
    
    if navigation_context.strip():
        enhanced_prompt = prompt + "\n\n" + navigation_context
        return enhanced_prompt
    
    return prompt