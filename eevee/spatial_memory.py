"""
Spatial Memory System for Eevee AI Agent
Provides location bookmarking and map connection tracking for enhanced navigation
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class LocationBookmark:
    """Represents a bookmarked location"""
    name: str
    map_bank: int
    map_id: int
    x: int
    y: int
    location_name: str
    timestamp: float
    notes: str = ""
    visit_count: int = 1


@dataclass
class MapConnection:
    """Represents a connection between two maps"""
    from_map: Tuple[int, int]  # (bank, id)
    to_map: Tuple[int, int]    # (bank, id)
    direction: str             # up, down, left, right, etc.
    method: str                # walk, door, stairs, etc.
    confidence: float = 1.0
    timestamp: float = 0.0


class SpatialMemory:
    """Manages spatial memory including bookmarks and map connections"""
    
    def __init__(self, memory_file: str = None):
        """
        Initialize spatial memory system
        
        Args:
            memory_file: Path to save spatial memory data (defaults to eevee/spatial_memory.json)
        """
        if memory_file is None:
            memory_file = Path(__file__).parent / "spatial_memory.json"
        
        self.memory_file = Path(memory_file)
        self.bookmarks: Dict[str, LocationBookmark] = {}
        self.map_connections: List[MapConnection] = []
        
        # Load existing data if available
        self._load_memory()
    
    def bookmark_current_location(self, name: str, ram_data: Dict[str, Any], notes: str = "") -> Dict[str, Any]:
        """
        Store current location as a bookmark
        
        Args:
            name: Memorable name for this location
            ram_data: Current RAM data containing position and map info
            notes: Optional notes about this location
            
        Returns:
            Dict with bookmark creation result
        """
        try:
            if not ram_data.get("ram_available"):
                return {
                    "success": False,
                    "error": "RAM data not available for bookmarking"
                }
            
            # Extract required data
            map_bank = ram_data.get("map_bank")
            map_id = ram_data.get("map_id")
            x = ram_data.get("player_x")
            y = ram_data.get("player_y")
            location_name = ram_data.get("location_name", "Unknown")
            
            if any(val is None for val in [map_bank, map_id, x, y]):
                return {
                    "success": False,
                    "error": "Incomplete location data for bookmarking"
                }
            
            # Check if bookmark already exists
            if name in self.bookmarks:
                # Update existing bookmark
                existing = self.bookmarks[name]
                existing.visit_count += 1
                existing.timestamp = time.time()
                existing.notes = notes if notes else existing.notes
                
                result = {
                    "success": True,
                    "action": "updated",
                    "bookmark_name": name,
                    "location": f"Map {map_bank}-{map_id} ({location_name})",
                    "position": f"({x}, {y})",
                    "visit_count": existing.visit_count
                }
            else:
                # Create new bookmark
                bookmark = LocationBookmark(
                    name=name,
                    map_bank=map_bank,
                    map_id=map_id,
                    x=x,
                    y=y,
                    location_name=location_name,
                    timestamp=time.time(),
                    notes=notes
                )
                
                self.bookmarks[name] = bookmark
                
                result = {
                    "success": True,
                    "action": "created",
                    "bookmark_name": name,
                    "location": f"Map {map_bank}-{map_id} ({location_name})",
                    "position": f"({x}, {y})",
                    "visit_count": 1
                }
            
            # Save to disk
            self._save_memory()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create bookmark: {str(e)}"
            }
    
    def goto_bookmark(self, bookmark_name: str, current_ram_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get navigation guidance to reach a bookmarked location
        
        Args:
            bookmark_name: Name of the bookmarked location
            current_ram_data: Current position data for calculating route
            
        Returns:
            Dict with navigation guidance
        """
        try:
            if bookmark_name not in self.bookmarks:
                return {
                    "success": False,
                    "error": f"Bookmark '{bookmark_name}' not found"
                }
            
            bookmark = self.bookmarks[bookmark_name]
            
            # Basic navigation guidance
            result = {
                "success": True,
                "bookmark_name": bookmark_name,
                "target_location": f"Map {bookmark.map_bank}-{bookmark.map_id} ({bookmark.location_name})",
                "target_position": f"({bookmark.x}, {bookmark.y})",
                "notes": bookmark.notes,
                "last_visited": time.ctime(bookmark.timestamp),
                "visit_count": bookmark.visit_count
            }
            
            # Add navigation guidance if current position is available
            if current_ram_data and current_ram_data.get("ram_available"):
                current_bank = current_ram_data.get("map_bank")
                current_id = current_ram_data.get("map_id")
                current_x = current_ram_data.get("player_x")
                current_y = current_ram_data.get("player_y")
                
                if all(val is not None for val in [current_bank, current_id, current_x, current_y]):
                    # Same map - provide direct coordinate guidance
                    if current_bank == bookmark.map_bank and current_id == bookmark.map_id:
                        dx = bookmark.x - current_x
                        dy = bookmark.y - current_y
                        
                        directions = []
                        if dx > 0:
                            directions.append(f"right {abs(dx)} steps")
                        elif dx < 0:
                            directions.append(f"left {abs(dx)} steps")
                        
                        if dy > 0:
                            directions.append(f"down {abs(dy)} steps")
                        elif dy < 0:
                            directions.append(f"up {abs(dy)} steps")
                        
                        if directions:
                            result["navigation_guidance"] = f"Move {', then '.join(directions)}"
                        else:
                            result["navigation_guidance"] = "You are already at the bookmarked location!"
                    else:
                        # Different map - check for known connections
                        route = self._find_route(
                            (current_bank, current_id),
                            (bookmark.map_bank, bookmark.map_id)
                        )
                        
                        if route:
                            result["navigation_guidance"] = f"Route found: {' → '.join(route)}"
                        else:
                            result["navigation_guidance"] = f"Need to find route to Map {bookmark.map_bank}-{bookmark.map_id}"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get navigation to bookmark: {str(e)}"
            }
    
    def track_map_connection(self, from_map: Tuple[int, int], to_map: Tuple[int, int], 
                           direction: str, method: str = "walk") -> Dict[str, Any]:
        """
        Record that two maps are connected
        
        Args:
            from_map: Source map (bank, id)
            to_map: Destination map (bank, id)
            direction: Direction of movement (up, down, left, right, etc.)
            method: Method of connection (walk, door, stairs, etc.)
            
        Returns:
            Dict with connection tracking result
        """
        try:
            # Check if connection already exists
            for connection in self.map_connections:
                if (connection.from_map == from_map and 
                    connection.to_map == to_map and 
                    connection.direction == direction):
                    # Update existing connection
                    connection.confidence += 0.1
                    connection.timestamp = time.time()
                    
                    self._save_memory()
                    
                    return {
                        "success": True,
                        "action": "updated",
                        "connection": f"Map {from_map[0]}-{from_map[1]} --{direction}--> Map {to_map[0]}-{to_map[1]}",
                        "confidence": connection.confidence
                    }
            
            # Create new connection
            connection = MapConnection(
                from_map=from_map,
                to_map=to_map,
                direction=direction,
                method=method,
                confidence=1.0,
                timestamp=time.time()
            )
            
            self.map_connections.append(connection)
            self._save_memory()
            
            return {
                "success": True,
                "action": "created",
                "connection": f"Map {from_map[0]}-{from_map[1]} --{direction}--> Map {to_map[0]}-{to_map[1]}",
                "confidence": 1.0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to track connection: {str(e)}"
            }
    
    def get_bookmarks_summary(self) -> Dict[str, Any]:
        """Get summary of all bookmarks"""
        return {
            "total_bookmarks": len(self.bookmarks),
            "bookmarks": {
                name: {
                    "location": f"Map {bookmark.map_bank}-{bookmark.map_id} ({bookmark.location_name})",
                    "position": f"({bookmark.x}, {bookmark.y})",
                    "visit_count": bookmark.visit_count,
                    "notes": bookmark.notes
                }
                for name, bookmark in self.bookmarks.items()
            }
        }
    
    def get_map_connections_summary(self) -> Dict[str, Any]:
        """Get summary of all map connections"""
        return {
            "total_connections": len(self.map_connections),
            "connections": [
                {
                    "from": f"Map {conn.from_map[0]}-{conn.from_map[1]}",
                    "to": f"Map {conn.to_map[0]}-{conn.to_map[1]}",
                    "direction": conn.direction,
                    "method": conn.method,
                    "confidence": conn.confidence
                }
                for conn in self.map_connections
            ]
        }
    
    def _find_route(self, from_map: Tuple[int, int], to_map: Tuple[int, int]) -> Optional[List[str]]:
        """
        Find route between two maps using known connections
        
        Args:
            from_map: Starting map (bank, id)
            to_map: Destination map (bank, id)
            
        Returns:
            List of map names representing the route, or None if no route found
        """
        if from_map == to_map:
            return []
        
        # Simple breadth-first search for route
        from collections import deque
        
        queue = deque([(from_map, [f"Map {from_map[0]}-{from_map[1]}"])])
        visited = {from_map}
        
        while queue:
            current_map, path = queue.popleft()
            
            # Find connections from current map
            for connection in self.map_connections:
                if connection.from_map == current_map:
                    next_map = connection.to_map
                    
                    if next_map == to_map:
                        # Found destination
                        return path + [f"Map {next_map[0]}-{next_map[1]}"]
                    
                    if next_map not in visited:
                        visited.add(next_map)
                        queue.append((next_map, path + [f"Map {next_map[0]}-{next_map[1]}"]))
        
        return None  # No route found
    
    def _load_memory(self):
        """Load spatial memory from disk"""
        if not self.memory_file.exists():
            return
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            # Load bookmarks
            bookmark_data = data.get("bookmarks", {})
            for name, bookmark_dict in bookmark_data.items():
                self.bookmarks[name] = LocationBookmark(**bookmark_dict)
            
            # Load map connections
            connection_data = data.get("map_connections", [])
            for conn_dict in connection_data:
                # Convert list tuples back to tuples
                conn_dict["from_map"] = tuple(conn_dict["from_map"])
                conn_dict["to_map"] = tuple(conn_dict["to_map"])
                self.map_connections.append(MapConnection(**conn_dict))
            
        except Exception as e:
            pass
    
    def _save_memory(self):
        """Save spatial memory to disk"""
        try:
            data = {
                "bookmarks": {
                    name: asdict(bookmark) 
                    for name, bookmark in self.bookmarks.items()
                },
                "map_connections": [
                    asdict(connection) 
                    for connection in self.map_connections
                ]
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to save spatial memory: {e}")


def test_spatial_memory():
    """Test spatial memory functionality"""
    import tempfile
    import os
    
    # Create temporary memory file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_file.close()
    
    try:
        print("🧪 Testing Spatial Memory System")
        print("=" * 50)
        
        # Initialize spatial memory
        spatial = SpatialMemory(temp_file.name)
        
        # Test RAM data
        test_ram_data = {
            "ram_available": True,
            "map_bank": 3,
            "map_id": 2,
            "player_x": 15,
            "player_y": 8,
            "location_name": "Pewter City",
            "player_name": "ASH"
        }
        
        # Test bookmark creation
        print("\n📍 Testing bookmark creation...")
        result = spatial.bookmark_current_location("pokemon_center", test_ram_data, "Healing location")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test bookmark retrieval
        print("\n🧭 Testing bookmark navigation...")
        result = spatial.goto_bookmark("pokemon_center", test_ram_data)
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test map connection tracking
        print("\n🗺️ Testing map connection tracking...")
        result = spatial.track_map_connection((3, 2), (1, 0), "north", "walk")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test summaries
        print("\n📊 Testing summaries...")
        bookmarks = spatial.get_bookmarks_summary()
        connections = spatial.get_map_connections_summary()
        print(f"Bookmarks: {json.dumps(bookmarks, indent=2)}")
        print(f"Connections: {json.dumps(connections, indent=2)}")
        
        print("\n✅ Spatial Memory test completed!")
        
    finally:
        # Clean up temporary file
        os.unlink(temp_file.name)


if __name__ == "__main__":
    test_spatial_memory()