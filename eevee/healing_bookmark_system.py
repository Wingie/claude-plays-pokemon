"""
Pokemon Center Bookmark System
Automatically bookmarks healing locations after successful healing sessions
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HealingLocation:
    """Represents a Pokemon Center or healing location"""
    map_id: int
    x: int
    y: int
    map_name: str
    location_name: str
    success_count: int = 0
    failure_count: int = 0
    last_used: str = ""
    average_healing_time: float = 0.0
    
class HealingBookmarkSystem:
    """
    Manages bookmarks for Pokemon healing locations
    Automatically tracks successful healing sessions and provides pathfinding assistance
    """
    
    def __init__(self, database_path: Path = None):
        """Initialize healing bookmark system with SQLite database"""
        if database_path is None:
            database_path = Path(__file__).parent / "healing_bookmarks.db"
        
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for healing bookmarks"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Healing locations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS healing_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    map_id INTEGER NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    map_name TEXT NOT NULL,
                    location_name TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    average_healing_time REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(map_id, x, y)
                )
            """)
            
            # Healing sessions table (detailed history)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS healing_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER,
                    session_id TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    pokemon_before TEXT,  -- JSON: party health before healing
                    pokemon_after TEXT,   -- JSON: party health after healing
                    healing_successful BOOLEAN,
                    healing_duration REAL,
                    notes TEXT,
                    FOREIGN KEY (location_id) REFERENCES healing_locations (id)
                )
            """)
            
            conn.commit()
    
    def detect_healing_success(self, ram_before: Dict[str, Any], ram_after: Dict[str, Any]) -> bool:
        """
        Detect if healing was successful by comparing RAM data before and after
        
        Args:
            ram_before: RAM data before healing attempt
            ram_after: RAM data after healing attempt
            
        Returns:
            bool: True if healing was successful
        """
        try:
            # Extract party health summaries
            before_summary = ram_before.get("party_summary", {})
            after_summary = ram_after.get("party_summary", {})
            
            # Check if health status improved
            before_status = before_summary.get("party_health_status", "unknown")
            after_status = after_summary.get("party_health_status", "unknown")
            
            # Check if fainted Pokemon were healed
            before_fainted = before_summary.get("fainted_pokemon", 0)
            after_fainted = after_summary.get("fainted_pokemon", 0)
            
            # Check if healthy Pokemon count increased
            before_healthy = before_summary.get("healthy_pokemon", 0)
            after_healthy = after_summary.get("healthy_pokemon", 0)
            
            # Healing is successful if:
            # 1. Health status improved (poor -> healthy)
            # 2. Fainted count decreased
            # 3. Healthy count increased
            # 4. No longer needs healing
            
            status_improved = (before_status in ["poor", "critical"] and after_status == "healthy")
            fainted_decreased = before_fainted > after_fainted
            healthy_increased = after_healthy > before_healthy
            no_longer_needs_healing = not after_summary.get("needs_healing", True)
            
            return status_improved or fainted_decreased or healthy_increased or no_longer_needs_healing
            
        except Exception as e:
            print(f"⚠️ Healing detection failed: {e}")
            return False
    
    def bookmark_healing_location(self, location_data: Dict[str, Any], ram_before: Dict[str, Any], 
                                 ram_after: Dict[str, Any], session_id: str, 
                                 healing_duration: float = 0.0) -> bool:
        """
        Bookmark a healing location after a healing session
        
        Args:
            location_data: Location info (map_id, x, y, location_name)
            ram_before: RAM data before healing
            ram_after: RAM data after healing
            session_id: Current session identifier
            healing_duration: Time taken for healing in seconds
            
        Returns:
            bool: True if successfully bookmarked
        """
        try:
            # Detect if healing was successful
            healing_successful = self.detect_healing_success(ram_before, ram_after)
            
            # Extract location information
            map_id = location_data.get("map_id", 0)
            x = location_data.get("x", 0)
            y = location_data.get("y", 0)
            map_name = location_data.get("map_name", "Unknown")
            location_name = location_data.get("location_name", "Pokemon Center")
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Check if location already exists
                cursor.execute("""
                    SELECT id, success_count, failure_count, average_healing_time 
                    FROM healing_locations
                    WHERE map_id = ? AND x = ? AND y = ?
                """, (map_id, x, y))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing location
                    location_id, success_count, failure_count, avg_time = existing
                    
                    if healing_successful:
                        success_count += 1
                        # Update average healing time
                        if avg_time > 0:
                            avg_time = (avg_time + healing_duration) / 2
                        else:
                            avg_time = healing_duration
                    else:
                        failure_count += 1
                    
                    cursor.execute("""
                        UPDATE healing_locations 
                        SET success_count = ?, failure_count = ?, last_used = CURRENT_TIMESTAMP,
                            average_healing_time = ?, location_name = ?
                        WHERE id = ?
                    """, (success_count, failure_count, avg_time, location_name, location_id))
                    
                else:
                    # Insert new location
                    cursor.execute("""
                        INSERT INTO healing_locations 
                        (map_id, x, y, map_name, location_name, success_count, failure_count, average_healing_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        map_id, x, y, map_name, location_name,
                        1 if healing_successful else 0,
                        0 if healing_successful else 1,
                        healing_duration
                    ))
                    
                    location_id = cursor.lastrowid
                
                # Record healing session details
                cursor.execute("""
                    INSERT INTO healing_sessions 
                    (location_id, session_id, start_time, end_time, pokemon_before, pokemon_after, 
                     healing_successful, healing_duration, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    location_id, session_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(ram_before.get("party_summary", {})),
                    json.dumps(ram_after.get("party_summary", {})),
                    healing_successful,
                    healing_duration,
                    f"Healing {'successful' if healing_successful else 'failed'} at {location_name}"
                ))
                
                conn.commit()
                
                if healing_successful:
                    print(f"✅ Bookmarked healing location: {location_name} at Map {map_id} ({x},{y})")
                else:
                    print(f"⚠️ Recorded failed healing attempt at {location_name}")
                
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to bookmark healing location: {e}")
            return False
    
    def get_nearest_healing_location(self, current_coords: Dict[str, Any], max_distance: int = 50) -> Optional[Dict[str, Any]]:
        """
        Find the nearest known healing location
        
        Args:
            current_coords: Current position (map_id, x, y)
            max_distance: Maximum search distance
            
        Returns:
            Dict with nearest healing location info, or None if none found
        """
        try:
            map_id = current_coords.get("map_id", 0)
            x = current_coords.get("x", 0)
            y = current_coords.get("y", 0)
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Find healing locations on same map, ordered by distance
                cursor.execute("""
                    SELECT map_id, x, y, map_name, location_name, success_count, failure_count,
                           average_healing_time, last_used,
                           ABS(x - ?) + ABS(y - ?) as distance
                    FROM healing_locations
                    WHERE map_id = ? AND (ABS(x - ?) + ABS(y - ?) <= ?)
                    AND success_count > 0
                    ORDER BY distance ASC, success_count DESC
                    LIMIT 1
                """, (x, y, map_id, x, y, max_distance))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "map_id": result[0],
                        "x": result[1],
                        "y": result[2],
                        "map_name": result[3],
                        "location_name": result[4],
                        "success_count": result[5],
                        "failure_count": result[6],
                        "average_healing_time": result[7],
                        "last_used": result[8],
                        "distance": result[9],
                        "success_rate": result[5] / (result[5] + result[6]) if (result[5] + result[6]) > 0 else 0
                    }
                
                return None
                
        except Exception as e:
            print(f"⚠️ Failed to find nearest healing location: {e}")
            return None
    
    def get_all_healing_locations(self, map_id: int = None) -> List[Dict[str, Any]]:
        """
        Get all known healing locations, optionally filtered by map
        
        Args:
            map_id: Optional map filter
            
        Returns:
            List of healing location dictionaries
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                if map_id is not None:
                    cursor.execute("""
                        SELECT map_id, x, y, map_name, location_name, success_count, failure_count,
                               average_healing_time, last_used
                        FROM healing_locations
                        WHERE map_id = ?
                        ORDER BY success_count DESC, last_used DESC
                    """, (map_id,))
                else:
                    cursor.execute("""
                        SELECT map_id, x, y, map_name, location_name, success_count, failure_count,
                               average_healing_time, last_used
                        FROM healing_locations
                        ORDER BY success_count DESC, last_used DESC
                    """)
                
                locations = []
                for row in cursor.fetchall():
                    locations.append({
                        "map_id": row[0],
                        "x": row[1],
                        "y": row[2],
                        "map_name": row[3],
                        "location_name": row[4],
                        "success_count": row[5],
                        "failure_count": row[6],
                        "average_healing_time": row[7],
                        "last_used": row[8],
                        "success_rate": row[5] / (row[5] + row[6]) if (row[5] + row[6]) > 0 else 0
                    })
                
                return locations
                
        except Exception as e:
            print(f"⚠️ Failed to get healing locations: {e}")
            return []
    
    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get overview statistics of healing bookmark system"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Total locations and sessions
                cursor.execute("SELECT COUNT(*) FROM healing_locations")
                total_locations = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM healing_sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Success statistics
                cursor.execute("""
                    SELECT SUM(success_count), SUM(failure_count) 
                    FROM healing_locations
                """)
                success_stats = cursor.fetchone()
                total_successes = success_stats[0] or 0
                total_failures = success_stats[1] or 0
                
                # Most reliable location
                cursor.execute("""
                    SELECT location_name, success_count, failure_count,
                           CAST(success_count AS REAL) / (success_count + failure_count) as success_rate
                    FROM healing_locations
                    WHERE (success_count + failure_count) > 0
                    ORDER BY success_rate DESC, success_count DESC
                    LIMIT 1
                """)
                
                best_location = cursor.fetchone()
                
                return {
                    "total_healing_locations": total_locations,
                    "total_healing_sessions": total_sessions,
                    "total_successful_healings": total_successes,
                    "total_failed_healings": total_failures,
                    "overall_success_rate": total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0,
                    "most_reliable_location": {
                        "name": best_location[0],
                        "success_count": best_location[1],
                        "success_rate": best_location[3]
                    } if best_location else None
                }
                
        except Exception as e:
            print(f"⚠️ Failed to get healing statistics: {e}")
            return {"error": str(e)}


# Convenience function for easy integration
def get_healing_bookmark_system() -> HealingBookmarkSystem:
    """Get healing bookmark system instance"""
    return HealingBookmarkSystem()