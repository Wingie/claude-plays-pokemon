"""
Neo4j Writer for Eevee Memory System
Handles create, update, and delete operations for game data storage
"""

import json
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Neo4jWriter:
    """Neo4j writer for game data storage and session management"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j writer connection
        
        Args:
            uri: Neo4j connection URI (defaults to env NEO4J_URI or bolt://localhost:7687)
            user: Username (defaults to env NEO4J_USER or neo4j)
            password: Password (defaults to env NEO4J_PASSWORD or password)
        """
        # Use environment variables or defaults
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = user or os.getenv("NEO4J_USER", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            if user and password:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
            else:
                # No authentication
                self.driver = GraphDatabase.driver(uri, auth=None)
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1").single()
                
            print(f"✅ Neo4j writer connected: {uri}")
            
            # Create necessary indices and constraints
            self._create_schema()
            
        except Exception as e:
            print(f"❌ Neo4j writer connection failed: {e}")
            self.driver = None
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def _create_schema(self):
        """Create necessary indices and constraints for optimal performance"""
        if not self.driver:
            return
        
        schema_queries = [
            # Constraints for uniqueness
            "CREATE CONSTRAINT turn_id_unique IF NOT EXISTS FOR (t:Turn) REQUIRE t.turn_id IS UNIQUE",
            "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE",
            
            # Indices for performance
            "CREATE INDEX turn_timestamp_index IF NOT EXISTS FOR (t:Turn) ON (t.timestamp)",
            "CREATE INDEX turn_session_index IF NOT EXISTS FOR (t:Turn) ON (t.session_id)",
            "CREATE INDEX battle_context_index IF NOT EXISTS FOR (b:BattleContext) ON (b.session_id)",
            "CREATE INDEX pokemon_context_index IF NOT EXISTS FOR (p:PokemonContext) ON (p.session_id)",
            "CREATE INDEX session_timestamp_index IF NOT EXISTS FOR (s:Session) ON (s.start_time)"
        ]
        
        with self.driver.session() as session:
            for query in schema_queries:
                try:
                    session.run(query)
                except Exception as e:
                    # Constraint/index may already exist
                    pass
    
    def store_game_turn(self, turn_data: Dict[str, Any]) -> bool:
        """
        Store a complete game turn with all context data
        
        Args:
            turn_data: Complete turn information including:
                - turn_id: Unique turn identifier
                - session_id: Session this turn belongs to
                - timestamp: When turn occurred
                - gemini_text: AI analysis/observation
                - button_presses: Actions taken
                - screenshot_path: Path to screenshot
                - visual_context: Visual analysis data
                - memory_context: Memory context used
                - battle_context: Battle-specific data (if applicable)
                - location: Current game location
                
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Store main turn node
                turn_result = session.run("""
                    CREATE (t:Turn {
                        turn_id: $turn_id,
                        session_id: $session_id,
                        timestamp: $timestamp,
                        gemini_text: $gemini_text,
                        button_presses: $button_presses,
                        screenshot_path: $screenshot_path,
                        location: $location,
                        success: $success
                    })
                    RETURN t.turn_id as turn_id
                """, {
                    "turn_id": turn_data.get("turn_id"),
                    "session_id": turn_data.get("session_id"),
                    "timestamp": turn_data.get("timestamp", datetime.now().isoformat()),
                    "gemini_text": turn_data.get("gemini_text", ""),
                    "button_presses": json.dumps(turn_data.get("button_presses", [])),
                    "screenshot_path": turn_data.get("screenshot_path"),
                    "location": turn_data.get("location", "unknown"),
                    "success": turn_data.get("success", True)
                })
                
                stored_turn_id = turn_result.single()["turn_id"]
                
                # Store visual context if available
                if turn_data.get("visual_context"):
                    self._store_visual_context(session, stored_turn_id, turn_data["visual_context"])
                
                # Store battle context if available
                if turn_data.get("battle_context"):
                    self._store_battle_context(session, stored_turn_id, turn_data["battle_context"])
                
                # Store memory context if available
                if turn_data.get("memory_context"):
                    self._store_memory_context(session, stored_turn_id, turn_data["memory_context"])
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to store game turn: {e}")
            return False
    
    def _store_visual_context(self, session, turn_id: str, visual_context: Dict[str, Any]):
        """Store visual analysis context linked to a turn"""
        try:
            session.run("""
                MATCH (t:Turn {turn_id: $turn_id})
                CREATE (v:VisualContext {
                    scene_type: $scene_type,
                    player_position: $player_position,
                    terrain: $terrain,
                    valid_movements: $valid_movements,
                    obstacles: $obstacles,
                    timestamp: $timestamp
                })
                CREATE (t)-[:HAS_VISUAL_CONTEXT]->(v)
            """, {
                "turn_id": turn_id,
                "scene_type": visual_context.get("scene_type", "unknown"),
                "player_position": visual_context.get("player_position", "unknown"),
                "terrain": visual_context.get("terrain", "unknown"),
                "valid_movements": json.dumps(visual_context.get("valid_movements", [])),
                "obstacles": json.dumps(visual_context.get("obstacles", [])),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️ Failed to store visual context: {e}")
    
    def _store_battle_context(self, session, turn_id: str, battle_context: Dict[str, Any]):
        """Store battle-specific context linked to a turn"""
        try:
            session.run("""
                MATCH (t:Turn {turn_id: $turn_id})
                CREATE (b:BattleContext {
                    battle_phase: $battle_phase,
                    our_pokemon: $our_pokemon,
                    our_hp: $our_hp,
                    our_level: $our_level,
                    enemy_pokemon: $enemy_pokemon,
                    enemy_hp: $enemy_hp,
                    enemy_level: $enemy_level,
                    move_used: $move_used,
                    move_result: $move_result,
                    battle_type: $battle_type,
                    timestamp: $timestamp
                })
                CREATE (t)-[:HAS_BATTLE_CONTEXT]->(b)
            """, {
                "turn_id": turn_id,
                "battle_phase": battle_context.get("battle_phase", "unknown"),
                "our_pokemon": battle_context.get("our_pokemon", ""),
                "our_hp": battle_context.get("our_hp", ""),
                "our_level": battle_context.get("our_level", 0),
                "enemy_pokemon": battle_context.get("enemy_pokemon", ""),
                "enemy_hp": battle_context.get("enemy_hp", ""),
                "enemy_level": battle_context.get("enemy_level", 0),
                "move_used": battle_context.get("move_used", ""),
                "move_result": battle_context.get("move_result", ""),
                "battle_type": battle_context.get("battle_type", "wild"),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️ Failed to store battle context: {e}")
    
    def _store_memory_context(self, session, turn_id: str, memory_context: str):
        """Store memory context used for decision making"""
        try:
            session.run("""
                MATCH (t:Turn {turn_id: $turn_id})
                CREATE (m:MemoryContext {
                    context_text: $context_text,
                    timestamp: $timestamp
                })
                CREATE (t)-[:USED_MEMORY_CONTEXT]->(m)
            """, {
                "turn_id": turn_id,
                "context_text": memory_context,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️ Failed to store memory context: {e}")
    
    def create_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Create a new gameplay session
        
        Args:
            session_data: Session information including:
                - session_id: Unique session identifier
                - start_time: When session started
                - goal: Session goal/objective
                - max_turns: Maximum turns planned
                - status: Current session status
                
        Returns:
            True if created successfully, False otherwise
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE (s:Session {
                        session_id: $session_id,
                        start_time: $start_time,
                        goal: $goal,
                        max_turns: $max_turns,
                        status: $status,
                        turns_completed: 0,
                        created_timestamp: $created_timestamp
                    })
                """, {
                    "session_id": session_data.get("session_id"),
                    "start_time": session_data.get("start_time", datetime.now().isoformat()),
                    "goal": session_data.get("goal", ""),
                    "max_turns": session_data.get("max_turns", 100),
                    "status": session_data.get("status", "active"),
                    "created_timestamp": datetime.now().isoformat()
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            return False
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session with new information
        
        Args:
            session_id: Session to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Build dynamic SET clause
                set_clauses = []
                params = {"session_id": session_id}
                
                for key, value in updates.items():
                    set_clauses.append(f"s.{key} = ${key}")
                    params[key] = value
                
                if not set_clauses:
                    return True  # Nothing to update
                
                set_clause = ", ".join(set_clauses)
                query = f"""
                    MATCH (s:Session {{session_id: $session_id}})
                    SET {set_clause}, s.last_updated = $last_updated
                """
                
                params["last_updated"] = datetime.now().isoformat()
                
                session.run(query, params)
                return True
                
        except Exception as e:
            print(f"❌ Failed to update session: {e}")
            return False
    
    def store_pokemon_context(self, session_id: str, pokemon_data: Dict[str, Any]) -> bool:
        """
        Store current Pokemon party context
        
        Args:
            session_id: Current session
            pokemon_data: Pokemon party information
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (s:Session {session_id: $session_id})
                    CREATE (p:PokemonContext {
                        session_id: $session_id,
                        party_data: $party_data,
                        active_pokemon: $active_pokemon,
                        party_size: $party_size,
                        timestamp: $timestamp
                    })
                    CREATE (s)-[:HAS_POKEMON_CONTEXT]->(p)
                """, {
                    "session_id": session_id,
                    "party_data": json.dumps(pokemon_data.get("party", [])),
                    "active_pokemon": pokemon_data.get("active_pokemon", ""),
                    "party_size": pokemon_data.get("party_size", 0),
                    "timestamp": datetime.now().isoformat()
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to store Pokemon context: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 7) -> bool:
        """
        Clean up old session data to maintain performance
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            True if cleanup successful, False otherwise
        """
        if not self.driver:
            return False
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()
            
            with self.driver.session() as session:
                # Delete old turns and their related data
                result = session.run("""
                    MATCH (t:Turn)
                    WHERE t.timestamp < $cutoff_time
                    OPTIONAL MATCH (t)-[r]->(related)
                    DELETE r, related, t
                    RETURN count(t) as deleted_turns
                """, {"cutoff_time": cutoff_iso})
                
                deleted_count = result.single()["deleted_turns"]
                print(f"🧹 Cleaned up {deleted_count} old turns (older than {days_to_keep} days)")
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to cleanup old data: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the Neo4j writer connection
        
        Returns:
            True if connection is working, False otherwise
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Neo4j Writer Connected' as message")
                message = result.single()["message"]
                print(f"✅ {message}")
                return True
        except Exception as e:
            print(f"❌ Neo4j writer connection test failed: {e}")
            return False


def test_neo4j_writer():
    """Test function for Neo4j writer"""
    print("🧪 Testing Neo4j Writer")
    print("=" * 50)
    
    # Initialize writer
    writer = Neo4jWriter()
    
    # Test connection
    if not writer.test_connection():
        print("❌ Cannot test without Neo4j connection")
        return False
    
    # Test session creation
    print("\n📝 Testing session creation...")
    session_id = f"test_session_{int(time.time())}"
    session_data = {
        "session_id": session_id,
        "goal": "Test Neo4j writer functionality",
        "max_turns": 5,
        "status": "active"
    }
    
    session_created = writer.create_session(session_data)
    print(f"Session creation: {'✅ Success' if session_created else '❌ Failed'}")
    
    # Test turn storage
    print("\n📝 Testing turn storage...")
    turn_data = {
        "turn_id": f"{session_id}_turn_1",
        "session_id": session_id,
        "gemini_text": "Player is in a grassy area. Trees visible to the north.",
        "button_presses": ["up"],
        "location": "Route 1",
        "success": True,
        "visual_context": {
            "scene_type": "overworld",
            "player_position": "center",
            "terrain": "grass",
            "valid_movements": ["up", "down", "left", "right"]
        },
        "battle_context": {
            "battle_phase": "none",
            "battle_type": "none"
        }
    }
    
    turn_stored = writer.store_game_turn(turn_data)
    print(f"Turn storage: {'✅ Success' if turn_stored else '❌ Failed'}")
    
    # Test session update
    print("\n📝 Testing session update...")
    session_updated = writer.update_session(session_id, {
        "turns_completed": 1,
        "status": "in_progress"
    })
    print(f"Session update: {'✅ Success' if session_updated else '❌ Failed'}")
    
    writer.close()
    print("\n✅ Neo4j Writer test completed!")
    return True


if __name__ == "__main__":
    test_neo4j_writer()