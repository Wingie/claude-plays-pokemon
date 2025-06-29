"""
MemorySystem - Persistent Context Management for Eevee
Handles long-term memory, context retention, and knowledge persistence across sessions
Enhanced with Neo4j visual memory integration
"""

import json
import sqlite3
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import uuid

# Import Neo4j visual memory with fallback
try:
    from neo4j_memory import Neo4jVisualMemory
    NEO4J_MEMORY_AVAILABLE = True
except ImportError:
    NEO4J_MEMORY_AVAILABLE = False
    print("⚠️  Neo4j visual memory not available")

class MemorySystem:
    """Persistent memory system for Eevee agent context and knowledge"""
    
    def __init__(self, session_name: str = "default", enable_neo4j: bool = False):
        """
        Initialize memory system with session-based storage
        
        Args:
            session_name: Name of the memory session for context isolation
            enable_neo4j: Enable Neo4j visual memory integration
        """
        self.session_name = session_name
        self.memory_dir = Path(__file__).parent / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # Database setup
        self.db_path = self.memory_dir / f"eevee_memory_{session_name}.db"
        self._init_database()
        
        # Neo4j visual memory integration
        self.neo4j_memory = None
        if enable_neo4j and NEO4J_MEMORY_AVAILABLE:
            try:
                self.neo4j_memory = Neo4jVisualMemory(session_name)
                print(f"✅ Neo4j visual memory enabled for session: {session_name}")
            except Exception as e:
                print(f"⚠️  Neo4j visual memory initialization failed: {e}")
        
        # Cache for frequently accessed data
        self._context_cache = {}
        self._cache_timestamp = datetime.now()
        
        # Memory configuration
        self.max_context_entries = 1000
        self.context_retention_days = 30
        self.auto_cleanup_enabled = True
    
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_states (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    location TEXT,
                    pokemon_party TEXT,
                    inventory TEXT,
                    progress_flags TEXT,
                    screenshot_hash TEXT,
                    raw_data TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    execution_result TEXT,
                    success BOOLEAN,
                    steps_taken INTEGER,
                    execution_time REAL,
                    context_id TEXT,
                    FOREIGN KEY (context_id) REFERENCES game_states (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_knowledge (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.8,
                    source_task_id TEXT,
                    FOREIGN KEY (source_task_id) REFERENCES task_history (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_memories (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    relevance_score REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)
    
    def store_game_state(
        self, 
        location: str = None,
        pokemon_party: List[Dict] = None,
        inventory: List[str] = None,
        progress_flags: Dict = None,
        screenshot_hash: str = None,
        raw_data: Dict = None
    ) -> str:
        """
        Store current game state in memory
        
        Args:
            location: Current game location/map
            pokemon_party: List of Pokemon with their stats
            inventory: List of items in inventory
            progress_flags: Game progress indicators
            screenshot_hash: Hash of current screenshot
            raw_data: Additional raw game data
            
        Returns:
            Unique ID for this game state entry
        """
        state_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO game_states 
                (id, timestamp, location, pokemon_party, inventory, progress_flags, screenshot_hash, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state_id,
                timestamp,
                location,
                json.dumps(pokemon_party) if pokemon_party else None,
                json.dumps(inventory) if inventory else None,
                json.dumps(progress_flags) if progress_flags else None,
                screenshot_hash,
                json.dumps(raw_data) if raw_data else None
            ))
        
        return state_id
    
    def store_task_result(self, task_description: str, result: Dict[str, Any]) -> str:
        """
        Store task execution result in memory
        
        Args:
            task_description: Description of the executed task
            result: Task execution result dictionary
            
        Returns:
            Unique ID for this task entry
        """
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extract key metrics from result
        success = result.get("status") in ["success", "completed"]
        steps_taken = result.get("steps_executed", 0)
        execution_time = result.get("execution_time", 0.0)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO task_history 
                (id, timestamp, task_description, execution_result, success, steps_taken, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                timestamp,
                task_description,
                json.dumps(result),
                success,
                steps_taken,
                execution_time
            ))
        
        # Extract and store learned knowledge
        self._extract_knowledge_from_task(task_id, task_description, result)
        
        return task_id
    
    def store_learned_knowledge(
        self,
        knowledge_type: str,
        subject: str,
        content: str,
        confidence_score: float = 0.8,
        source_task_id: str = None
    ) -> str:
        """
        Store learned knowledge for future reference
        
        Args:
            knowledge_type: Type of knowledge (pokemon_data, location_info, strategy, etc.)
            subject: Subject of the knowledge (Pokemon name, location, etc.)
            content: The actual knowledge content
            confidence_score: Confidence in this knowledge (0.0-1.0)
            source_task_id: ID of task that generated this knowledge
            
        Returns:
            Unique ID for this knowledge entry
        """
        knowledge_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO learned_knowledge 
                (id, timestamp, knowledge_type, subject, content, confidence_score, source_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                knowledge_id,
                timestamp,
                knowledge_type,
                subject,
                content,
                confidence_score,
                source_task_id
            ))
        
        return knowledge_id
    
    def store_visual_context(self, screenshot_data: str, game_context: Dict[str, Any], task_description: str = None) -> str:
        """
        Store visual context with screenshot embedding (if Neo4j is available)
        
        Args:
            screenshot_data: Base64 encoded screenshot
            game_context: Current game context information
            task_description: Optional task being performed
            
        Returns:
            Visual memory ID
        """
        if self.neo4j_memory:
            try:
                return self.neo4j_memory.store_visual_memory(screenshot_data, game_context, task_description)
            except Exception as e:
                print(f"⚠️  Visual memory storage failed: {e}")
        
        # Fallback: store in SQLite as game state
        return self.store_game_state(
            location=game_context.get("location"),
            screenshot_hash=hashlib.md5(screenshot_data.encode()).hexdigest() if screenshot_data else None,
            raw_data={
                "screenshot_available": bool(screenshot_data),
                "task_description": task_description,
                "context": game_context
            }
        )
    
    def get_similar_visual_memories(self, screenshot_data: str, game_context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get visually similar memories based on screenshot
        
        Args:
            screenshot_data: Base64 encoded screenshot to compare
            game_context: Current game context
            limit: Maximum number of similar memories to return
            
        Returns:
            List of similar visual memories
        """
        if self.neo4j_memory:
            try:
                return self.neo4j_memory.find_similar_visual_memories(screenshot_data, game_context, limit)
            except Exception as e:
                print(f"⚠️  Visual similarity search failed: {e}")
        
        # Fallback: return recent game states with similar context
        return self._get_similar_contexts_fallback(game_context, limit)
    
    def get_contextual_strategies(self, game_context: Dict[str, Any], task_type: str = None) -> List[Dict[str, Any]]:
        """
        Get relevant strategies based on current context
        
        Args:
            game_context: Current game context
            task_type: Type of task being performed
            
        Returns:
            List of relevant strategies from past experiences
        """
        if self.neo4j_memory:
            try:
                return self.neo4j_memory.get_contextual_strategies(game_context, task_type)
            except Exception as e:
                print(f"⚠️  Strategy retrieval failed: {e}")
        
        # Fallback: return strategies from SQLite knowledge base
        return self._get_strategies_fallback(game_context, task_type)
    
    def _get_similar_contexts_fallback(self, game_context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback method for finding similar contexts without Neo4j"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, location, raw_data 
                FROM game_states 
                WHERE raw_data IS NOT NULL 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit * 2,))  # Get more to filter
            
            similar_contexts = []
            current_location = game_context.get("location", "")
            
            for row in cursor.fetchall():
                try:
                    raw_data = json.loads(row[3]) if row[3] else {}
                    stored_context = raw_data.get("context", {})
                    
                    # Simple similarity based on location matching
                    if stored_context.get("location") == current_location:
                        similar_contexts.append({
                            "memory_id": row[0],
                            "similarity": 0.8,  # High similarity for same location
                            "context": stored_context,
                            "task_description": raw_data.get("task_description"),
                            "timestamp": row[1],
                            "screenshot_path": None
                        })
                    
                    if len(similar_contexts) >= limit:
                        break
                        
                except Exception:
                    continue
            
            return similar_contexts
    
    def _get_strategies_fallback(self, game_context: Dict[str, Any], task_type: str = None) -> List[Dict[str, Any]]:
        """Fallback method for getting strategies without Neo4j"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT subject, content, confidence_score 
                FROM learned_knowledge 
                WHERE knowledge_type = 'strategy' 
                ORDER BY confidence_score DESC 
                LIMIT 5
            """)
            
            strategies = []
            for row in cursor.fetchall():
                strategies.append({
                    "strategy": row[1],
                    "context": row[0],
                    "success_rate": row[2],
                    "usage_count": 1,
                    "task_type": task_type
                })
            
            return strategies
    
    def get_relevant_context(self, task_description: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get relevant context for a task based on memory
        
        Args:
            task_description: Description of current task
            limit: Maximum number of context entries to return
            
        Returns:
            Dictionary containing relevant context information
        """
        # Check cache first
        cache_key = f"context_{hashlib.md5(task_description.encode()).hexdigest()}"
        if (cache_key in self._context_cache and 
            datetime.now() - self._cache_timestamp < timedelta(minutes=5)):
            return self._context_cache[cache_key]
        
        context = {
            "session": self.session_name,
            "relevant_memories": [],
            "similar_tasks": [],
            "pokemon_knowledge": [],
            "location_knowledge": [],
            "game_state": {}
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Get similar tasks
            cursor = conn.execute("""
                SELECT id, timestamp, task_description, execution_result, success 
                FROM task_history 
                WHERE task_description LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{task_description}%", limit))
            
            for row in cursor.fetchall():
                context["similar_tasks"].append({
                    "id": row[0],
                    "timestamp": row[1],
                    "description": row[2],
                    "result": json.loads(row[3]) if row[3] else {},
                    "success": row[4]
                })
            
            # Get relevant knowledge
            cursor = conn.execute("""
                SELECT knowledge_type, subject, content, confidence_score 
                FROM learned_knowledge 
                WHERE subject LIKE ? OR content LIKE ?
                ORDER BY confidence_score DESC, timestamp DESC
                LIMIT ?
            """, (f"%{task_description}%", f"%{task_description}%", limit))
            
            for row in cursor.fetchall():
                knowledge_entry = {
                    "type": row[0],
                    "subject": row[1],
                    "content": row[2],
                    "confidence": row[3]
                }
                
                if row[0] == "pokemon_data":
                    context["pokemon_knowledge"].append(knowledge_entry)
                elif row[0] == "location_info":
                    context["location_knowledge"].append(knowledge_entry)
                else:
                    context["relevant_memories"].append(knowledge_entry)
            
            # Get latest game state
            cursor = conn.execute("""
                SELECT location, pokemon_party, inventory, progress_flags 
                FROM game_states 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                context["game_state"] = {
                    "location": row[0],
                    "pokemon_party": json.loads(row[1]) if row[1] else [],
                    "inventory": json.loads(row[2]) if row[2] else [],
                    "progress_flags": json.loads(row[3]) if row[3] else {}
                }
        
        # Cache the result
        self._context_cache[cache_key] = context
        self._cache_timestamp = datetime.now()
        
        return context
    
    def get_pokemon_knowledge(self, pokemon_name: str = None) -> List[Dict[str, Any]]:
        """
        Get stored knowledge about Pokemon
        
        Args:
            pokemon_name: Specific Pokemon to get knowledge about (None for all)
            
        Returns:
            List of Pokemon knowledge entries
        """
        with sqlite3.connect(self.db_path) as conn:
            if pokemon_name:
                cursor = conn.execute("""
                    SELECT subject, content, confidence_score, timestamp 
                    FROM learned_knowledge 
                    WHERE knowledge_type = 'pokemon_data' AND subject LIKE ?
                    ORDER BY confidence_score DESC
                """, (f"%{pokemon_name}%",))
            else:
                cursor = conn.execute("""
                    SELECT subject, content, confidence_score, timestamp 
                    FROM learned_knowledge 
                    WHERE knowledge_type = 'pokemon_data'
                    ORDER BY confidence_score DESC
                """)
            
            return [{
                "pokemon": row[0],
                "knowledge": row[1],
                "confidence": row[2],
                "learned_at": row[3]
            } for row in cursor.fetchall()]
    
    def get_recent_gameplay_summary(self, limit: int = 5) -> str:
        """
        Get a summary of recent gameplay for AI context
        
        Args:
            limit: Number of recent entries to include
            
        Returns:
            Formatted string summary of recent gameplay
        """
        summary_parts = []
        
        with sqlite3.connect(self.db_path) as conn:
            # Get recent game states
            cursor = conn.execute("""
                SELECT timestamp, location, pokemon_party, screenshot_hash
                FROM game_states
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            game_states = cursor.fetchall()
            if game_states:
                latest_state = game_states[0]
                if latest_state[1]:  # location
                    summary_parts.append(f"Current location: {latest_state[1]}")
                
                if latest_state[2]:  # pokemon_party
                    try:
                        party = json.loads(latest_state[2])
                        if party:
                            summary_parts.append(f"Pokemon in party: {len(party)}")
                    except:
                        pass
            
            # Get recent tasks
            cursor = conn.execute("""
                SELECT task_description, success, timestamp
                FROM task_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            recent_tasks = cursor.fetchall()
            if recent_tasks:
                summary_parts.append(f"Recent tasks: {len(recent_tasks)} completed")
                for task in recent_tasks[:3]:  # Show last 3 tasks
                    status = "✓" if task[1] else "✗"
                    summary_parts.append(f"  {status} {task[0][:50]}...")
        
        return "\n".join(summary_parts) if summary_parts else "No recent gameplay data"
    
    def get_location_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get history of visited locations
        
        Args:
            limit: Maximum number of locations to return
            
        Returns:
            List of location entries with timestamps
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT location, timestamp 
                FROM game_states 
                WHERE location IS NOT NULL 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [{
                "location": row[0],
                "visited_at": row[1]
            } for row in cursor.fetchall()]
    
    def get_task_success_rate(self, task_pattern: str = None) -> Dict[str, Any]:
        """
        Get success rate statistics for tasks
        
        Args:
            task_pattern: Pattern to filter tasks (None for all tasks)
            
        Returns:
            Dictionary with success rate statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            if task_pattern:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total, SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM task_history 
                    WHERE task_description LIKE ?
                """, (f"%{task_pattern}%",))
            else:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total, SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM task_history
                """)
            
            row = cursor.fetchone()
            total, successful = row[0], row[1] or 0
            
            return {
                "total_tasks": total,
                "successful_tasks": successful,
                "success_rate": successful / total if total > 0 else 0.0,
                "pattern": task_pattern
            }
    
    def _extract_knowledge_from_task(self, task_id: str, task_description: str, result: Dict[str, Any]):
        """Extract and store knowledge from task execution"""
        analysis = result.get("analysis", "")
        
        # Extract Pokemon-related knowledge
        if "pokemon" in task_description.lower() or "party" in task_description.lower():
            self.store_learned_knowledge(
                knowledge_type="pokemon_data",
                subject="party_analysis", 
                content=analysis,
                confidence_score=0.9 if result.get("status") == "success" else 0.6,
                source_task_id=task_id
            )
        
        # Extract location knowledge
        if any(keyword in task_description.lower() for keyword in ["location", "map", "area", "route"]):
            self.store_learned_knowledge(
                knowledge_type="location_info",
                subject="location_analysis",
                content=analysis,
                confidence_score=0.8 if result.get("status") == "success" else 0.5,
                source_task_id=task_id
            )
        
        # Extract general game strategy knowledge
        if result.get("status") == "success" and len(analysis) > 100:
            self.store_learned_knowledge(
                knowledge_type="strategy",
                subject=task_description[:50],
                content=analysis,
                confidence_score=0.7,
                source_task_id=task_id
            )
    
    def cleanup_old_memories(self, days_to_keep: int = None):
        """Clean up old memory entries beyond retention period"""
        if days_to_keep is None:
            days_to_keep = self.context_retention_days
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Clean up old game states
            conn.execute("DELETE FROM game_states WHERE timestamp < ?", (cutoff_date,))
            
            # Clean up old task history (keep longer for learning)
            task_cutoff = (datetime.now() - timedelta(days=days_to_keep * 2)).isoformat()
            conn.execute("DELETE FROM task_history WHERE timestamp < ?", (task_cutoff,))
            
            # Don't clean up learned knowledge - it's valuable long-term
            
            conn.commit()
    
    def clear_session(self):
        """Clear all memory for current session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM game_states")
            conn.execute("DELETE FROM task_history") 
            conn.execute("DELETE FROM learned_knowledge")
            conn.execute("DELETE FROM context_memories")
            conn.commit()
        
        self._context_cache = {}
    
    def export_session(self, export_path: Path = None) -> Path:
        """Export session memory to JSON file"""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.memory_dir / f"export_{self.session_name}_{timestamp}.json"
        
        export_data = {
            "session_name": self.session_name,
            "export_timestamp": datetime.now().isoformat(),
            "game_states": [],
            "task_history": [],
            "learned_knowledge": []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Export game states
            cursor = conn.execute("SELECT * FROM game_states ORDER BY timestamp")
            columns = [description[0] for description in cursor.description]
            export_data["game_states"] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Export task history
            cursor = conn.execute("SELECT * FROM task_history ORDER BY timestamp")
            columns = [description[0] for description in cursor.description]
            export_data["task_history"] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Export learned knowledge
            cursor = conn.execute("SELECT * FROM learned_knowledge ORDER BY timestamp")
            columns = [description[0] for description in cursor.description]
            export_data["learned_knowledge"] = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return export_path
    
    def generate_summary(self) -> Dict[str, str]:
        """Generate a summary of current memory context for AI prompts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get recent game states
                recent_states = conn.execute("""
                    SELECT location, timestamp FROM game_states 
                    ORDER BY timestamp DESC LIMIT 3
                """).fetchall()
                
                # Get recent successful tasks
                recent_tasks = conn.execute("""
                    SELECT task_description, success FROM task_history 
                    ORDER BY timestamp DESC LIMIT 5
                """).fetchall()
                
                # Get recent learned knowledge
                recent_knowledge = conn.execute("""
                    SELECT subject, content FROM learned_knowledge 
                    ORDER BY timestamp DESC LIMIT 3
                """).fetchall()
                
                # Build summary
                summary_parts = []
                
                if recent_states:
                    locations = [state[0] for state in recent_states if state[0]]
                    if locations:
                        summary_parts.append(f"Recent locations: {', '.join(locations[:3])}")
                
                if recent_tasks:
                    successful_tasks = [task[0] for task in recent_tasks if task[1]]
                    if successful_tasks:
                        summary_parts.append(f"Recent successful tasks: {'; '.join(successful_tasks[:2])}")
                
                if recent_knowledge:
                    knowledge_items = [f"{item[0]}: {item[1][:50]}..." for item in recent_knowledge]
                    summary_parts.append(f"Recent learning: {'; '.join(knowledge_items[:2])}")
                
                # Add battle memory
                battle_summary = self.generate_battle_summary()
                if battle_summary:
                    summary_parts.append(f"Battle experience: {battle_summary}")
                
                summary = "\n".join(summary_parts) if summary_parts else "No recent memory context available."
                
                return {"summary": summary}
                
        except Exception as e:
            return {"summary": f"Memory summary error: {str(e)}"}
    
    def store_gameplay_turn(self, turn_number: int = None, analysis: str = "", actions: List = None, success: bool = False, reasoning: str = "") -> str:
        """Store gameplay turn data for continuous play sessions"""
        turn_id = str(uuid.uuid4())
        
        if actions is None:
            actions = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store as a specialized task entry
                conn.execute("""
                    INSERT INTO task_history 
                    (id, timestamp, task_description, execution_result, success, steps_taken, execution_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    turn_id,
                    datetime.now().isoformat(),
                    f"Gameplay Turn {turn_number}: Continuous play",
                    json.dumps({
                        "ai_analysis": analysis,
                        "button_presses": actions,
                        "action_result": "success" if success else "failed",
                        "reasoning": reasoning
                    }),
                    success,
                    len(actions),
                    0.0
                ))
                conn.commit()
                
            return turn_id
            
        except Exception as e:
            # Fallback storage in context_memories table
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO context_memories (id, timestamp, content, source_context)
                        VALUES (?, ?, ?, ?)
                    """, (
                        turn_id,
                        turn_data.get("timestamp", datetime.now().isoformat()),
                        json.dumps(turn_data),
                        "gameplay_turn"
                    ))
                    conn.commit()
                    
                return turn_id
            except Exception as e2:
                print(f"Failed to store gameplay turn: {e2}")
                return turn_id
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about current memory usage"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {"session": self.session_name}
            
            # Count entries in each table
            for table in ["game_states", "task_history", "learned_knowledge", "context_memories"]:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Get date range
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM task_history")
            row = cursor.fetchone()
            if row[0] and row[1]:
                stats["date_range"] = {"earliest": row[0], "latest": row[1]}
            
            # Database size
            stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)
            
            # Neo4j visual memory stats
            if self.neo4j_memory:
                try:
                    neo4j_stats = self.neo4j_memory.get_memory_stats()
                    stats["neo4j_visual_memory"] = neo4j_stats
                except Exception as e:
                    stats["neo4j_visual_memory"] = {"error": str(e)}
            else:
                stats["neo4j_visual_memory"] = {"enabled": False}
        
        return stats
    
    def store_navigation_route(self, from_location: str, to_location: str, route_description: str, steps_taken: int) -> str:
        """Store a successful navigation route"""
        if self.neo4j_memory:
            try:
                return self.neo4j_memory.store_navigation_success(from_location, to_location, route_description, steps_taken)
            except Exception as e:
                print(f"⚠️ Navigation route storage failed: {e}")
        
        # Fallback: store as learned knowledge
        return self.store_learned_knowledge(
            knowledge_type="navigation",
            subject=f"{from_location}_to_{to_location}",
            content=f"Route: {route_description}, Steps: {steps_taken}",
            confidence_score=0.9
        )
    
    def get_route_to_location(self, current_location: str, target_location: str) -> Optional[Dict[str, Any]]:
        """Find the best known route to a location"""
        if self.neo4j_memory:
            try:
                return self.neo4j_memory.find_route_to_location(current_location, target_location)
            except Exception as e:
                print(f"⚠️ Route finding failed: {e}")
        
        # Fallback: search SQLite knowledge
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT content, confidence_score 
                FROM learned_knowledge 
                WHERE knowledge_type = 'navigation' 
                AND subject LIKE ?
                ORDER BY confidence_score DESC
                LIMIT 1
            """, (f"%{current_location}_to_{target_location}%",))
            
            row = cursor.fetchone()
            if row:
                return {
                    "route_type": "learned",
                    "description": row[0],
                    "confidence": row[1],
                    "from_location": current_location,
                    "to_location": target_location
                }
        
        return None
    
    def get_all_known_routes(self) -> List[Dict[str, Any]]:
        """Get all known navigation routes"""
        if self.neo4j_memory:
            try:
                return self.neo4j_memory.get_known_routes()
            except Exception as e:
                print(f"⚠️ Route retrieval failed: {e}")
        
        # Fallback: get from SQLite
        routes = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT subject, content, confidence_score 
                FROM learned_knowledge 
                WHERE knowledge_type = 'navigation'
                ORDER BY confidence_score DESC
            """)
            
            for row in cursor.fetchall():
                routes.append({
                    "route_id": row[0],
                    "description": row[1],
                    "confidence": row[2],
                    "source": "sqlite"
                })
        
        return routes
    
    def clear_navigation_memory(self):
        """Clear navigation memory for fresh testing"""
        if self.neo4j_memory:
            try:
                self.neo4j_memory.clear_navigation_memory()
                print("✅ Neo4j navigation memory cleared")
            except Exception as e:
                print(f"⚠️ Neo4j memory clearing failed: {e}")
        
        # Clear SQLite navigation knowledge
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM learned_knowledge WHERE knowledge_type = 'navigation'")
            conn.commit()
            print("✅ SQLite navigation knowledge cleared")
    
    def generate_battle_summary(self) -> str:
        """Generate a summary of recent battle experiences for AI prompts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get recent battle-related tasks
                battle_tasks = conn.execute("""
                    SELECT task_description, execution_result, success, timestamp
                    FROM task_history 
                    WHERE task_description LIKE '%battle%' 
                       OR task_description LIKE '%fight%'
                       OR task_description LIKE '%attack%'
                       OR task_description LIKE '%move%'
                    ORDER BY timestamp DESC LIMIT 5
                """).fetchall()
                
                # Get battle-related knowledge
                battle_knowledge = conn.execute("""
                    SELECT subject, content, confidence_score
                    FROM learned_knowledge 
                    WHERE knowledge_type = 'battle_strategy' 
                       OR knowledge_type = 'move_effectiveness'
                       OR subject LIKE '%battle%'
                    ORDER BY confidence_score DESC, timestamp DESC LIMIT 3
                """).fetchall()
                
                summary_parts = []
                
                if battle_tasks:
                    successful_battles = [task for task in battle_tasks if task[2]]  # success = True
                    if successful_battles:
                        latest_battle = successful_battles[0]
                        try:
                            result_data = json.loads(latest_battle[1]) if latest_battle[1] else {}
                            ai_analysis = result_data.get("ai_analysis", "")
                            button_presses = result_data.get("button_presses", [])
                            
                            if ai_analysis and button_presses:
                                summary_parts.append(f"Last successful battle: Used {button_presses} - {ai_analysis[:100]}...")
                        except:
                            summary_parts.append(f"Recent battle activity: {latest_battle[0][:100]}...")
                
                if battle_knowledge:
                    knowledge_items = []
                    for knowledge in battle_knowledge:
                        subject, content, confidence = knowledge
                        knowledge_items.append(f"{subject}: {content[:80]}... (confidence: {confidence:.1f})")
                    if knowledge_items:
                        summary_parts.append(f"Battle knowledge: {'; '.join(knowledge_items[:2])}")
                
                return "; ".join(summary_parts) if summary_parts else ""
                
        except Exception as e:
            return f"Battle memory error: {str(e)}"
    
    def store_battle_outcome(
        self, 
        opponent: str,
        my_pokemon: str,
        moves_used: List[str],
        button_sequences: List[List[str]],
        outcome: str,
        effectiveness_notes: str = ""
    ) -> str:
        """Store battle outcome and move effectiveness for learning"""
        
        battle_data = {
            "opponent": opponent,
            "my_pokemon": my_pokemon,
            "moves_used": moves_used,
            "button_sequences": button_sequences,
            "outcome": outcome,
            "effectiveness_notes": effectiveness_notes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store as specialized knowledge
        knowledge_id = self.store_learned_knowledge(
            knowledge_type="battle_strategy",
            subject=f"{my_pokemon}_vs_{opponent}",
            content=f"Moves: {', '.join(moves_used)}. Outcome: {outcome}. Notes: {effectiveness_notes}",
            confidence_score=0.9 if outcome == "victory" else 0.6
        )
        
        # Also store detailed battle data
        battle_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO context_memories (id, timestamp, memory_type, content, relevance_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    battle_id,
                    datetime.now().isoformat(),
                    "battle_detail",
                    json.dumps(battle_data),
                    0.8
                ))
                conn.commit()
        except Exception as e:
            print(f"Error storing detailed battle data: {e}")
        
        return knowledge_id
    
    def store_move_effectiveness(
        self,
        move_name: str,
        move_type: str,
        target_type: str,
        effectiveness: str,
        button_sequence: List[str]
    ) -> str:
        """Store move effectiveness data for future reference"""
        
        return self.store_learned_knowledge(
            knowledge_type="move_effectiveness",
            subject=f"{move_name}_{move_type}_vs_{target_type}",
            content=f"Move: {move_name} ({move_type}) vs {target_type} = {effectiveness}. Buttons: {button_sequence}",
            confidence_score=0.8
        )
    
    def get_battle_advice(self, opponent_type: str = None, available_moves: List[str] = None) -> str:
        """Get battle advice based on stored knowledge"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                advice_parts = []
                
                # Get general battle strategies
                strategies = conn.execute("""
                    SELECT content, confidence_score
                    FROM learned_knowledge 
                    WHERE knowledge_type = 'battle_strategy'
                    ORDER BY confidence_score DESC LIMIT 3
                """).fetchall()
                
                # Get move effectiveness if we have opponent type
                if opponent_type:
                    effectiveness = conn.execute("""
                        SELECT content, confidence_score
                        FROM learned_knowledge 
                        WHERE knowledge_type = 'move_effectiveness'
                        AND subject LIKE ?
                        ORDER BY confidence_score DESC LIMIT 2
                    """, (f"%_vs_{opponent_type}%",)).fetchall()
                    
                    if effectiveness:
                        advice_parts.append("Effective moves: " + "; ".join([e[0][:60] for e in effectiveness]))
                
                # Get successful button patterns
                if available_moves:
                    for move in available_moves:
                        move_data = conn.execute("""
                            SELECT content
                            FROM learned_knowledge 
                            WHERE content LIKE ?
                            ORDER BY confidence_score DESC LIMIT 1
                        """, (f"%{move}%",)).fetchone()
                        
                        if move_data:
                            advice_parts.append(f"{move}: {move_data[0][:50]}...")
                
                return "; ".join(advice_parts) if advice_parts else "No specific battle advice available"
                
        except Exception as e:
            return f"Battle advice error: {str(e)}"
    
    def close(self):
        """Close all connections"""
        if self.neo4j_memory:
            self.neo4j_memory.close()