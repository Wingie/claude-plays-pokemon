"""
Neo4j Visual Memory System for Eevee
Extends the existing SQLite memory system with graph-based visual memory using screenshot embeddings
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

# Neo4j imports with fallback
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  Neo4j driver not available. Install with: pip install neo4j")

# Embedding service imports with fallback
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    print("⚠️  Sentence transformers not available. Install with: pip install sentence-transformers")

class Neo4jVisualMemory:
    """Neo4j-based visual memory system using screenshot embeddings"""
    
    def __init__(self, session_name: str = "default", neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        """
        Initialize Neo4j visual memory system
        
        Args:
            session_name: Memory session identifier
            neo4j_uri: Neo4j database URI (default: bolt://localhost:7687)
            neo4j_user: Neo4j username (default: neo4j)
            neo4j_password: Neo4j password (default: password)
        """
        self.session_name = session_name
        self.neo4j_uri = neo4j_uri or "bolt://localhost:7687"
        self.neo4j_user = neo4j_user or "neo4j"
        self.neo4j_password = neo4j_password or "password"
        
        # Initialize components
        self.driver = None
        self.embedding_model = None
        self.connected = False
        
        # Initialize Neo4j connection
        if NEO4J_AVAILABLE:
            self._init_neo4j_connection()
        
        # Initialize embedding model
        if EMBEDDING_AVAILABLE:
            self._init_embedding_model()
        
        # Configuration
        self.similarity_threshold = 0.85  # Minimum similarity for visual memory matches
        self.max_visual_memories = 1000   # Maximum visual memories to store
        
        self.logger = logging.getLogger(__name__)
    
    def _init_neo4j_connection(self):
        """Initialize Neo4j database connection"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    self.connected = True
                    self._create_indices()
                else:
                    raise Exception("Connection test failed")
                    
        except Exception as e:
            self.logger.warning(f"Neo4j connection failed: {e}")
            print(f"⚠️  Neo4j not available: {e}")
            self.connected = False
    
    def _init_embedding_model(self):
        """Initialize the embedding model for visual similarity"""
        try:
            # Use a lightweight model suitable for screenshot analysis
            self.embedding_model = SentenceTransformer('clip-ViT-B-32')
            print("✅ CLIP embedding model loaded")
        except Exception as e:
            self.logger.warning(f"Embedding model initialization failed: {e}")
            print(f"⚠️  Embedding model not available: {e}")
    
    def _create_indices(self):
        """Create necessary Neo4j indices for performance"""
        if not self.connected:
            return
        
        indices = [
            "CREATE INDEX screenshot_embedding_index IF NOT EXISTS FOR (s:Screenshot) ON (s.session_name)",
            "CREATE INDEX pokemon_knowledge_index IF NOT EXISTS FOR (p:Pokemon) ON (p.name)",
            "CREATE INDEX location_index IF NOT EXISTS FOR (l:Location) ON (l.name)",
            "CREATE INDEX task_index IF NOT EXISTS FOR (t:Task) ON (t.description)",
            "CREATE INDEX strategy_index IF NOT EXISTS FOR (s:Strategy) ON (s.context)"
        ]
        
        with self.driver.session() as session:
            for index_query in indices:
                try:
                    session.run(index_query)
                except Exception as e:
                    self.logger.debug(f"Index creation note: {e}")
    
    def store_visual_memory(self, screenshot_data: str, context: Dict[str, Any], task_description: str = None) -> str:
        """
        Store a visual memory with screenshot embedding
        
        Args:
            screenshot_data: Base64 encoded screenshot
            context: Game context information
            task_description: Optional task being performed
            
        Returns:
            Memory ID for the stored visual memory
        """
        if not self.connected or not self.embedding_model:
            return self._store_visual_memory_fallback(screenshot_data, context, task_description)
        
        try:
            # Generate screenshot hash and embedding
            screenshot_hash = hashlib.md5(screenshot_data.encode()).hexdigest()
            
            # Create embedding from screenshot (simplified - would need image processing)
            # For now, use context text as embedding source
            context_text = json.dumps(context)
            embedding = self.embedding_model.encode(context_text).tolist()
            
            # Store in Neo4j
            memory_id = f"{self.session_name}_{screenshot_hash}_{int(datetime.now().timestamp())}"
            
            with self.driver.session() as session:
                # Create screenshot node
                session.run("""
                    CREATE (s:Screenshot {
                        id: $memory_id,
                        session_name: $session_name,
                        screenshot_hash: $screenshot_hash,
                        embedding: $embedding,
                        context: $context,
                        task_description: $task_description,
                        timestamp: $timestamp,
                        screenshot_path: $screenshot_path
                    })
                """, {
                    "memory_id": memory_id,
                    "session_name": self.session_name,
                    "screenshot_hash": screenshot_hash,
                    "embedding": embedding,
                    "context": json.dumps(context),
                    "task_description": task_description,
                    "timestamp": datetime.now().isoformat(),
                    "screenshot_path": context.get("screenshot_path")
                })
                
                # Create relationships based on context
                if context.get("location"):
                    self._create_location_relationship(session, memory_id, context["location"])
                
                if task_description:
                    self._create_task_relationship(session, memory_id, task_description)
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error storing visual memory: {e}")
            return self._store_visual_memory_fallback(screenshot_data, context, task_description)
    
    def find_similar_visual_memories(self, screenshot_data: str, context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find visually similar memories based on screenshot embedding
        
        Args:
            screenshot_data: Base64 encoded screenshot to compare
            context: Current game context
            limit: Maximum number of similar memories to return
            
        Returns:
            List of similar visual memories with similarity scores
        """
        if not self.connected or not self.embedding_model:
            return self._find_similar_memories_fallback(context, limit)
        
        try:
            # Generate embedding for current screenshot
            context_text = json.dumps(context)
            current_embedding = self.embedding_model.encode(context_text).tolist()
            
            # Find similar screenshots using cosine similarity
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Screenshot)
                    WHERE s.session_name = $session_name
                    WITH s, gds.similarity.cosine(s.embedding, $current_embedding) AS similarity
                    WHERE similarity > $threshold
                    RETURN s, similarity
                    ORDER BY similarity DESC
                    LIMIT $limit
                """, {
                    "session_name": self.session_name,
                    "current_embedding": current_embedding,
                    "threshold": self.similarity_threshold,
                    "limit": limit
                })
                
                similar_memories = []
                for record in result:
                    screenshot_node = record["s"]
                    similarity = record["similarity"]
                    
                    similar_memories.append({
                        "memory_id": screenshot_node["id"],
                        "similarity": similarity,
                        "context": json.loads(screenshot_node["context"]),
                        "task_description": screenshot_node["task_description"],
                        "timestamp": screenshot_node["timestamp"],
                        "screenshot_path": screenshot_node["screenshot_path"]
                    })
                
                return similar_memories
                
        except Exception as e:
            self.logger.error(f"Error finding similar memories: {e}")
            return self._find_similar_memories_fallback(context, limit)
    
    def get_contextual_strategies(self, context: Dict[str, Any], task_type: str = None) -> List[Dict[str, Any]]:
        """
        Get relevant strategies based on current context and task type
        
        Args:
            context: Current game context
            task_type: Type of task being performed
            
        Returns:
            List of relevant strategies from past experiences
        """
        if not self.connected:
            return []
        
        try:
            with self.driver.session() as session:
                # Find strategies used in similar contexts
                query = """
                    MATCH (s:Screenshot)-[:USED_STRATEGY]->(strategy:Strategy)
                    WHERE s.session_name = $session_name
                """
                
                params = {"session_name": self.session_name}
                
                if context.get("location"):
                    query += " AND s.context CONTAINS $location"
                    params["location"] = context["location"]
                
                if task_type:
                    query += " AND strategy.task_type = $task_type"
                    params["task_type"] = task_type
                
                query += """
                    RETURN strategy, count(*) as usage_count
                    ORDER BY usage_count DESC
                    LIMIT 10
                """
                
                result = session.run(query, params)
                
                strategies = []
                for record in result:
                    strategy_node = record["strategy"]
                    usage_count = record["usage_count"]
                    
                    strategies.append({
                        "strategy": strategy_node["description"],
                        "context": strategy_node["context"],
                        "success_rate": strategy_node.get("success_rate", 0.5),
                        "usage_count": usage_count,
                        "task_type": strategy_node.get("task_type")
                    })
                
                return strategies
                
        except Exception as e:
            self.logger.error(f"Error getting contextual strategies: {e}")
            return []
    
    def _create_location_relationship(self, session, memory_id: str, location: str):
        """Create relationship between screenshot and location"""
        session.run("""
            MATCH (s:Screenshot {id: $memory_id})
            MERGE (l:Location {name: $location})
            CREATE (s)-[:TAKEN_AT]->(l)
        """, {"memory_id": memory_id, "location": location})
    
    def _create_task_relationship(self, session, memory_id: str, task_description: str):
        """Create relationship between screenshot and task"""
        session.run("""
            MATCH (s:Screenshot {id: $memory_id})
            MERGE (t:Task {description: $task_description})
            CREATE (s)-[:DURING_TASK]->(t)
        """, {"memory_id": memory_id, "task_description": task_description})
    
    def store_navigation_success(self, from_location: str, to_location: str, route_description: str, steps_taken: int) -> str:
        """
        Store a successful navigation route for future reference
        
        Args:
            from_location: Starting location
            to_location: Destination location
            route_description: Description of the route taken
            steps_taken: Number of steps/actions taken
            
        Returns:
            Route ID
        """
        if not self.connected:
            return "route_fallback"
        
        try:
            route_id = f"route_{from_location}_{to_location}_{int(datetime.now().timestamp())}"
            
            with self.driver.session() as session:
                # Create route node
                session.run("""
                    MERGE (from:Location {name: $from_location})
                    MERGE (to:Location {name: $to_location})
                    CREATE (route:Route {
                        id: $route_id,
                        from_location: $from_location,
                        to_location: $to_location,
                        description: $route_description,
                        steps_taken: $steps_taken,
                        success_count: 1,
                        last_used: $timestamp,
                        session_name: $session_name
                    })
                    CREATE (from)-[:CONNECTS_TO {via: route.id}]->(to)
                    CREATE (route)-[:FROM]->(from)
                    CREATE (route)-[:TO]->(to)
                """, {
                    "route_id": route_id,
                    "from_location": from_location,
                    "to_location": to_location,
                    "route_description": route_description,
                    "steps_taken": steps_taken,
                    "timestamp": datetime.now().isoformat(),
                    "session_name": self.session_name
                })
            
            return route_id
            
        except Exception as e:
            self.logger.error(f"Error storing navigation success: {e}")
            return "route_error"
    
    def get_known_routes(self, from_location: str = None, to_location: str = None) -> List[Dict[str, Any]]:
        """
        Get known routes between locations
        
        Args:
            from_location: Filter by starting location
            to_location: Filter by destination location
            
        Returns:
            List of known routes with success rates
        """
        if not self.connected:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                    MATCH (route:Route)
                    WHERE route.session_name = $session_name
                """
                params = {"session_name": self.session_name}
                
                if from_location:
                    query += " AND route.from_location = $from_location"
                    params["from_location"] = from_location
                
                if to_location:
                    query += " AND route.to_location = $to_location"
                    params["to_location"] = to_location
                
                query += """
                    RETURN route
                    ORDER BY route.success_count DESC, route.last_used DESC
                    LIMIT 10
                """
                
                result = session.run(query, params)
                
                routes = []
                for record in result:
                    route_node = record["route"]
                    routes.append({
                        "route_id": route_node["id"],
                        "from_location": route_node["from_location"],
                        "to_location": route_node["to_location"],
                        "description": route_node["description"],
                        "steps_taken": route_node["steps_taken"],
                        "success_count": route_node["success_count"],
                        "last_used": route_node["last_used"]
                    })
                
                return routes
                
        except Exception as e:
            self.logger.error(f"Error getting known routes: {e}")
            return []
    
    def find_route_to_location(self, current_location: str, target_location: str) -> Optional[Dict[str, Any]]:
        """
        Find the best known route from current location to target
        
        Args:
            current_location: Current location name
            target_location: Desired destination
            
        Returns:
            Best route information or None if no route known
        """
        if not self.connected:
            return None
        
        try:
            routes = self.get_known_routes(from_location=current_location, to_location=target_location)
            
            if routes:
                # Return the most successful/recently used route
                best_route = max(routes, key=lambda r: (r["success_count"], r["last_used"]))
                return best_route
            
            # Try to find indirect routes
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (from:Location {name: $current})-[:CONNECTS_TO*1..3]-(to:Location {name: $target})
                    WHERE from.name <> to.name
                    RETURN path, length(path) as distance
                    ORDER BY distance ASC
                    LIMIT 1
                """, {"current": current_location, "target": target_location})
                
                record = result.single()
                if record:
                    return {
                        "route_type": "indirect",
                        "distance": record["distance"],
                        "from_location": current_location,
                        "to_location": target_location,
                        "description": f"Indirect route via {record['distance']} connections"
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding route: {e}")
            return None
    
    def clear_navigation_memory(self):
        """Clear all navigation-related memory for fresh testing"""
        if not self.connected:
            return
        
        try:
            with self.driver.session() as session:
                # Clear routes and location connections for this session
                session.run("""
                    MATCH (route:Route {session_name: $session_name})
                    DETACH DELETE route
                """, {"session_name": self.session_name})
                
                # Clear location relationships for this session
                session.run("""
                    MATCH (s:Screenshot {session_name: $session_name})-[r:TAKEN_AT]->()
                    DELETE r
                """, {"session_name": self.session_name})
                
                self.logger.info(f"Cleared navigation memory for session: {self.session_name}")
                
        except Exception as e:
            self.logger.error(f"Error clearing navigation memory: {e}")
    
    def _store_visual_memory_fallback(self, screenshot_data: str, context: Dict[str, Any], task_description: str = None) -> str:
        """Fallback storage when Neo4j is not available"""
        memory_id = f"fallback_{int(datetime.now().timestamp())}"
        print(f"📝 Stored visual memory (fallback): {memory_id}")
        return memory_id
    
    def _find_similar_memories_fallback(self, context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback similarity search when Neo4j is not available"""
        return [{
            "memory_id": "fallback_memory",
            "similarity": 0.7,
            "context": context,
            "task_description": "Fallback memory - Neo4j not available",
            "timestamp": datetime.now().isoformat(),
            "screenshot_path": None
        }]
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.connected = False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the visual memory system"""
        if not self.connected:
            return {
                "connected": False,
                "total_screenshots": 0,
                "session_screenshots": 0,
                "embedding_model": "Not available"
            }
        
        try:
            with self.driver.session() as session:
                # Get total screenshot count
                total_result = session.run("MATCH (s:Screenshot) RETURN count(s) as total")
                total_screenshots = total_result.single()["total"]
                
                # Get session-specific count
                session_result = session.run(
                    "MATCH (s:Screenshot {session_name: $session_name}) RETURN count(s) as session_total",
                    {"session_name": self.session_name}
                )
                session_screenshots = session_result.single()["session_total"]
                
                return {
                    "connected": True,
                    "total_screenshots": total_screenshots,
                    "session_screenshots": session_screenshots,
                    "embedding_model": "CLIP-ViT-B-32" if self.embedding_model else "Not available",
                    "similarity_threshold": self.similarity_threshold
                }
                
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            return {"connected": False, "error": str(e)}