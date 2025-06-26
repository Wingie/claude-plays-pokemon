"""
Coordinate Mapping System for Pathfinding Foundation
Stores screenshot-coordinate pairs to build spatial database for navigation
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class CoordinateEntry:
    """Represents a single coordinate-screenshot mapping"""
    map_id: int
    x: int
    y: int
    screenshot_path: str
    timestamp: str
    session_id: str
    map_name: str = "Unknown"
    scene_type: str = "navigation"
    valid_movements: List[str] = None
    
    def __post_init__(self):
        if self.valid_movements is None:
            self.valid_movements = []

class CoordinateMapper:
    """
    Coordinate mapping system that builds a spatial database from screenshots
    Enables pathfinding by tracking visited locations and their connections
    """
    
    def __init__(self, database_path: Path = None):
        """
        Initialize coordinate mapper with SQLite database
        
        Args:
            database_path: Path to SQLite database file (defaults to eevee/coordinate_map.db)
        """
        if database_path is None:
            database_path = Path(__file__).parent / "coordinate_map.db"
        
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with coordinate mapping tables"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Main coordinates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coordinates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    map_id INTEGER NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    screenshot_path TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    map_name TEXT DEFAULT 'Unknown',
                    scene_type TEXT DEFAULT 'navigation',
                    valid_movements TEXT,  -- JSON array of valid movement directions
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(map_id, x, y, session_id)
                )
            """)
            
            # Movement connections table (tracks which coordinates connect to which)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movement_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_map_id INTEGER NOT NULL,
                    from_x INTEGER NOT NULL,
                    from_y INTEGER NOT NULL,
                    to_map_id INTEGER NOT NULL,
                    to_x INTEGER NOT NULL,
                    to_y INTEGER NOT NULL,
                    movement_direction TEXT NOT NULL,  -- 'up', 'down', 'left', 'right'
                    session_id TEXT NOT NULL,
                    success_count INTEGER DEFAULT 1,
                    failure_count INTEGER DEFAULT 0,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_map_id, from_x, from_y, to_map_id, to_x, to_y, movement_direction)
                )
            """)
            
            # Map metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS map_metadata (
                    map_id INTEGER PRIMARY KEY,
                    map_name TEXT,
                    map_type TEXT,  -- 'overworld', 'indoor', 'battle', etc.
                    min_x INTEGER,
                    max_x INTEGER,
                    min_y INTEGER,
                    max_y INTEGER,
                    total_coordinates INTEGER DEFAULT 0,
                    last_visited DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def record_coordinate(self, coord_data: Dict[str, Any], screenshot_path: str, 
                         session_id: str, scene_analysis: Dict[str, Any] = None) -> bool:
        """
        Record a new coordinate-screenshot mapping
        
        Args:
            coord_data: Coordinate data from RAM (map_id, x, y, map_name)
            screenshot_path: Path to the screenshot file
            session_id: Current session identifier
            scene_analysis: Optional visual analysis data
            
        Returns:
            bool: True if successfully recorded, False otherwise
        """
        try:
            # Extract coordinate information
            map_id = coord_data.get("map_id", 0)
            x = coord_data.get("x", 0)
            y = coord_data.get("y", 0)
            map_name = coord_data.get("map_name", "Unknown")
            
            # Extract scene information if available
            scene_type = "navigation"
            valid_movements = []
            
            if scene_analysis:
                scene_type = scene_analysis.get("scene_type", "navigation")
                valid_movements = scene_analysis.get("valid_movements", [])
            
            # Create coordinate entry
            entry = CoordinateEntry(
                map_id=map_id,
                x=x,
                y=y,
                screenshot_path=str(screenshot_path),
                timestamp=datetime.now().isoformat(),
                session_id=session_id,
                map_name=map_name,
                scene_type=scene_type,
                valid_movements=valid_movements
            )
            
            # Store in database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Insert coordinate entry (or update if exists)
                cursor.execute("""
                    INSERT OR REPLACE INTO coordinates 
                    (map_id, x, y, screenshot_path, timestamp, session_id, map_name, scene_type, valid_movements)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.map_id, entry.x, entry.y, entry.screenshot_path,
                    entry.timestamp, entry.session_id, entry.map_name,
                    entry.scene_type, json.dumps(entry.valid_movements)
                ))
                
                # Update map metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO map_metadata 
                    (map_id, map_name, min_x, max_x, min_y, max_y, total_coordinates, last_visited)
                    VALUES (?, ?, 
                            COALESCE((SELECT MIN(min_x, ?) FROM map_metadata WHERE map_id = ?), ?),
                            COALESCE((SELECT MAX(max_x, ?) FROM map_metadata WHERE map_id = ?), ?),
                            COALESCE((SELECT MIN(min_y, ?) FROM map_metadata WHERE map_id = ?), ?),
                            COALESCE((SELECT MAX(max_y, ?) FROM map_metadata WHERE map_id = ?), ?),
                            (SELECT COUNT(*) FROM coordinates WHERE map_id = ?),
                            CURRENT_TIMESTAMP)
                """, (
                    entry.map_id, entry.map_name,
                    x, entry.map_id, x,  # min_x
                    x, entry.map_id, x,  # max_x
                    y, entry.map_id, y,  # min_y
                    y, entry.map_id, y,  # max_y
                    entry.map_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to record coordinate: {e}")
            return False
    
    def record_movement(self, from_coord: Dict[str, Any], to_coord: Dict[str, Any], 
                       movement_direction: str, session_id: str, success: bool = True) -> bool:
        """
        Record a movement connection between two coordinates
        
        Args:
            from_coord: Starting coordinate (map_id, x, y)
            to_coord: Destination coordinate (map_id, x, y)
            movement_direction: Direction moved ('up', 'down', 'left', 'right')
            session_id: Current session identifier
            success: Whether the movement was successful
            
        Returns:
            bool: True if successfully recorded, False otherwise
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Check if connection already exists
                cursor.execute("""
                    SELECT success_count, failure_count FROM movement_connections
                    WHERE from_map_id = ? AND from_x = ? AND from_y = ?
                    AND to_map_id = ? AND to_x = ? AND to_y = ?
                    AND movement_direction = ?
                """, (
                    from_coord["map_id"], from_coord["x"], from_coord["y"],
                    to_coord["map_id"], to_coord["x"], to_coord["y"],
                    movement_direction
                ))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing connection
                    success_count, failure_count = existing
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    cursor.execute("""
                        UPDATE movement_connections 
                        SET success_count = ?, failure_count = ?, last_used = CURRENT_TIMESTAMP
                        WHERE from_map_id = ? AND from_x = ? AND from_y = ?
                        AND to_map_id = ? AND to_x = ? AND to_y = ?
                        AND movement_direction = ?
                    """, (
                        success_count, failure_count,
                        from_coord["map_id"], from_coord["x"], from_coord["y"],
                        to_coord["map_id"], to_coord["x"], to_coord["y"],
                        movement_direction
                    ))
                else:
                    # Insert new connection
                    cursor.execute("""
                        INSERT INTO movement_connections 
                        (from_map_id, from_x, from_y, to_map_id, to_x, to_y, 
                         movement_direction, session_id, success_count, failure_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        from_coord["map_id"], from_coord["x"], from_coord["y"],
                        to_coord["map_id"], to_coord["x"], to_coord["y"],
                        movement_direction, session_id,
                        1 if success else 0, 0 if success else 1
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to record movement: {e}")
            return False
    
    def get_coordinates_near(self, map_id: int, x: int, y: int, radius: int = 5) -> List[Dict[str, Any]]:
        """
        Get coordinates within radius of given position
        
        Args:
            map_id: Map identifier
            x, y: Center coordinates
            radius: Search radius
            
        Returns:
            List of coordinate records within radius
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT map_id, x, y, screenshot_path, map_name, scene_type, valid_movements
                    FROM coordinates
                    WHERE map_id = ? 
                    AND ABS(x - ?) <= ? 
                    AND ABS(y - ?) <= ?
                    ORDER BY ABS(x - ?) + ABS(y - ?) ASC
                """, (map_id, x, radius, y, radius, x, y))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "map_id": row[0],
                        "x": row[1],
                        "y": row[2],
                        "screenshot_path": row[3],
                        "map_name": row[4],
                        "scene_type": row[5],
                        "valid_movements": json.loads(row[6]) if row[6] else [],
                        "distance": abs(row[1] - x) + abs(row[2] - y)
                    })
                
                return results
                
        except Exception as e:
            print(f"⚠️ Failed to get nearby coordinates: {e}")
            return []
    
    def find_path_to_target(self, start_coord: Dict[str, Any], target_coord: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find a path from start to target using recorded movement data
        Simple implementation using known movement connections
        
        Args:
            start_coord: Starting position (map_id, x, y)
            target_coord: Target position (map_id, x, y)
            
        Returns:
            List of movement steps to reach target, or empty list if no path found
        """
        try:
            # For now, implement simple adjacent movement suggestions
            # Future enhancement: A* pathfinding with movement connection graph
            
            if start_coord["map_id"] != target_coord["map_id"]:
                return []  # Cannot path across different maps yet
            
            # Simple directional movement suggestion
            dx = target_coord["x"] - start_coord["x"]
            dy = target_coord["y"] - start_coord["y"]
            
            movements = []
            
            # Prefer horizontal movement first, then vertical
            if dx > 0:
                movements.extend([{"direction": "right", "steps": abs(dx)}])
            elif dx < 0:
                movements.extend([{"direction": "left", "steps": abs(dx)}])
            
            if dy > 0:
                movements.extend([{"direction": "down", "steps": abs(dy)}])
            elif dy < 0:
                movements.extend([{"direction": "up", "steps": abs(dy)}])
            
            return movements
            
        except Exception as e:
            print(f"⚠️ Failed to find path: {e}")
            return []
    
    def get_map_statistics(self) -> Dict[str, Any]:
        """Get overview statistics of mapped coordinates"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Total coordinates
                cursor.execute("SELECT COUNT(*) FROM coordinates")
                total_coords = cursor.fetchone()[0]
                
                # Unique maps
                cursor.execute("SELECT COUNT(DISTINCT map_id) FROM coordinates")
                unique_maps = cursor.fetchone()[0]
                
                # Movement connections
                cursor.execute("SELECT COUNT(*) FROM movement_connections")
                total_connections = cursor.fetchone()[0]
                
                # Map details
                cursor.execute("""
                    SELECT map_id, map_name, total_coordinates, 
                           (max_x - min_x + 1) * (max_y - min_y + 1) as map_area
                    FROM map_metadata
                    ORDER BY total_coordinates DESC
                    LIMIT 10
                """)
                
                top_maps = []
                for row in cursor.fetchall():
                    top_maps.append({
                        "map_id": row[0],
                        "map_name": row[1],
                        "coordinates_mapped": row[2],
                        "map_area": row[3]
                    })
                
                return {
                    "total_coordinates": total_coords,
                    "unique_maps": unique_maps,
                    "movement_connections": total_connections,
                    "top_mapped_areas": top_maps
                }
                
        except Exception as e:
            print(f"⚠️ Failed to get statistics: {e}")
            return {"error": str(e)}
    
    def export_map_data(self, map_id: int, output_path: Path = None) -> bool:
        """
        Export coordinate data for a specific map to JSON file
        Useful for debugging and visualization
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Get all coordinates for the map
                cursor.execute("""
                    SELECT map_id, x, y, screenshot_path, map_name, scene_type, 
                           valid_movements, timestamp, session_id
                    FROM coordinates
                    WHERE map_id = ?
                    ORDER BY y ASC, x ASC
                """, (map_id,))
                
                coordinates = []
                for row in cursor.fetchall():
                    coordinates.append({
                        "map_id": row[0],
                        "x": row[1],
                        "y": row[2],
                        "screenshot_path": row[3],
                        "map_name": row[4],
                        "scene_type": row[5],
                        "valid_movements": json.loads(row[6]) if row[6] else [],
                        "timestamp": row[7],
                        "session_id": row[8]
                    })
                
                # Get movement connections
                cursor.execute("""
                    SELECT from_x, from_y, to_x, to_y, movement_direction, 
                           success_count, failure_count
                    FROM movement_connections
                    WHERE from_map_id = ? AND to_map_id = ?
                """, (map_id, map_id))
                
                connections = []
                for row in cursor.fetchall():
                    connections.append({
                        "from": {"x": row[0], "y": row[1]},
                        "to": {"x": row[2], "y": row[3]},
                        "direction": row[4],
                        "success_rate": row[5] / (row[5] + row[6]) if (row[5] + row[6]) > 0 else 0
                    })
                
                map_data = {
                    "map_id": map_id,
                    "coordinates": coordinates,
                    "movement_connections": connections,
                    "exported_at": datetime.now().isoformat()
                }
                
                if output_path is None:
                    output_path = Path(__file__).parent / f"map_{map_id}_data.json"
                
                with open(output_path, 'w') as f:
                    json.dump(map_data, f, indent=2)
                
                print(f"✅ Exported map {map_id} data to {output_path}")
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to export map data: {e}")
            return False