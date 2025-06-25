"""
Neo4j Compact Reader for Eevee Memory System
Adapts gamememory.py methods for compact JSON memory integration
"""

import json
import time
import os
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Neo4jCompactReader:
    """Compact Neo4j reader for Eevee memory integration"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j connection
        
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
                
            
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            self.driver = None
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def get_recent_turns(self, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Get the most recent turns from Neo4j (adapted from gamememory.py)
        
        Args:
            limit: Maximum number of turns to retrieve (default 4)
            
        Returns:
            List of turn dictionaries with compact format
        """
        if not self.driver:
            return []
            
        turns = []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (t:Turn)
                    RETURN t.turn_id, t.gemini_text, t.timestamp, t.button_presses
                    ORDER BY t.timestamp DESC
                    LIMIT $limit
                """, {"limit": limit})
                
                for record in result:
                    turns.append({
                        "turn_id": record.get("t.turn_id", 0),
                        "gemini_text": record.get("t.gemini_text", ""),
                        "timestamp": record.get("t.timestamp", ""),
                        "button_presses": record.get("t.button_presses", [])
                    })
                    
        except Exception as e:
            print(f"❌ Failed to get recent turns: {e}")
            return []
        
        # Sort by turn_id for chronological order (oldest first)
        turns.sort(key=lambda x: x.get("turn_id", 0))
        return turns
    
    def format_turns_to_compact_json(self, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format turns data into ultra-compact JSON for memory context
        
        Args:
            turns: List of turn data from Neo4j
            
        Returns:
            Compact JSON format optimized for token efficiency
        """
        if not turns:
            return {
                "recent_turns": [],
                "turn_count": 0,
                "patterns": "no_data"
            }
        
        compact_turns = []
        
        for turn in turns:
            # Extract action from button_presses (take first button if list)
            action = "unknown"
            if turn.get("button_presses"):
                if isinstance(turn["button_presses"], list) and len(turn["button_presses"]) > 0:
                    action = turn["button_presses"][0]
                elif isinstance(turn["button_presses"], str):
                    action = turn["button_presses"]
            
            # Extract result/context from gemini_text (first few words)
            result = "moved"
            context = "terrain"
            
            if turn.get("gemini_text"):
                text = turn["gemini_text"].lower()
                # Simple keyword extraction for result
                if "failed" in text or "blocked" in text or "wall" in text:
                    result = "blocked"
                elif "moved" in text or "walked" in text:
                    result = "moved"
                elif "entered" in text:
                    result = "entered"
                
                # Simple keyword extraction for context  
                if "grass" in text:
                    context = "grass"
                elif "tree" in text or "forest" in text:
                    context = "forest"
                elif "water" in text:
                    context = "water"
                elif "path" in text or "route" in text:
                    context = "path"
                elif "building" in text or "center" in text:
                    context = "building"
            
            compact_turns.append({
                "turn": turn.get("turn_id", 0),
                "action": action,
                "result": result,
                "context": context
            })
        
        # Detect simple patterns
        actions = [t["action"] for t in compact_turns]
        results = [t["result"] for t in compact_turns]
        
        patterns = "exploring"
        if results.count("blocked") >= 2:
            patterns = "hitting_obstacles"
        elif len(set(actions)) == 1:  # All same action
            patterns = f"repeating_{actions[0]}"
        elif "entered" in results:
            patterns = "progressing"
        
        return {
            "recent_turns": compact_turns,
            "turn_count": len(compact_turns),
            "patterns": patterns
        }
    
    def get_current_visual_context(self, visual_analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract current visual context into compact format
        
        Args:
            visual_analysis_result: Result from visual analysis system
            
        Returns:
            Compact visual context for memory integration
        """
        if not visual_analysis_result:
            return {
                "scene": "unknown",
                "pos": "unknown",
                "terrain": "unknown", 
                "moves": []
            }
        
        # Extract key visual data in compact format
        scene_type = visual_analysis_result.get("scene_type", "navigation")
        player_pos = visual_analysis_result.get("player_position", "unknown")
        terrain = visual_analysis_result.get("terrain", "unknown")
        
        # Extract valid movements
        valid_moves = []
        if "valid_buttons" in visual_analysis_result:
            for button in visual_analysis_result["valid_buttons"]:
                if isinstance(button, dict) and "key" in button:
                    move = button["key"].lower()
                    if move in ["up", "down", "left", "right"]:
                        valid_moves.append(move)
        
        return {
            "scene": scene_type,
            "pos": player_pos,
            "terrain": terrain.replace(" and ", "_").replace(" ", "_"),
            "moves": valid_moves
        }
    
    def create_memory_context(self, limit: int = 4, visual_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create complete memory context combining turns + visual data
        
        Args:
            limit: Number of recent turns to include
            visual_context: Current visual analysis result
            
        Returns:
            Complete memory context in compact JSON format
        """
        # Get recent turns
        recent_turns = self.get_recent_turns(limit)
        turns_summary = self.format_turns_to_compact_json(recent_turns)
        
        # Get current visual context
        current_visual = self.get_current_visual_context(visual_context or {})
        
        # Combine into memory context
        memory_context = {
            "memory": turns_summary,
            "current": current_visual,
            "generated_at": int(time.time())
        }
        
        return memory_context
    
    def test_connection(self) -> bool:
        """
        Test Neo4j connection and data availability
        
        Returns:
            True if connection and data are available
        """
        if not self.driver:
            print("❌ No Neo4j connection")
            return False
        
        try:
            with self.driver.session() as session:
                # Test basic connection
                session.run("RETURN 1").single()
                
                # Test for Turn nodes
                result = session.run("MATCH (t:Turn) RETURN count(t) as turn_count").single()
                turn_count = result["turn_count"] if result else 0
                
                print(f"✅ Neo4j connection OK, {turn_count} turns available")
                return True
                
        except Exception as e:
            print(f"❌ Neo4j test failed: {e}")
            return False


def test_neo4j_compact_reader():
    """Test function for Neo4j compact reader"""
    print("🧪 Testing Neo4j Compact Reader")
    print("=" * 50)
    
    # Initialize reader
    reader = Neo4jCompactReader()
    
    # Test connection
    if not reader.test_connection():
        print("❌ Cannot test without Neo4j connection")
        return False
    
    # Test getting recent turns
    print("\n📖 Testing recent turns retrieval...")
    turns = reader.get_recent_turns(4)
    print(f"Retrieved {len(turns)} turns")
    
    if turns:
        print("Sample turn data:")
        for turn in turns[:2]:  # Show first 2 turns
            print(f"  Turn {turn.get('turn_id')}: {turn.get('button_presses')} -> {turn.get('gemini_text', '')[:50]}...")
    
    # Test compact JSON formatting
    print("\n🗜️ Testing compact JSON formatting...")
    compact_data = reader.format_turns_to_compact_json(turns)
    print(f"Compact format: {json.dumps(compact_data, indent=2)}")
    
    # Test memory context creation
    print("\n🧠 Testing memory context creation...")
    memory_context = reader.create_memory_context(4, {
        "scene_type": "navigation",
        "player_position": "4,3",
        "terrain": "grass and water",
        "valid_buttons": [
            {"key": "up", "action": "move_up"},
            {"key": "down", "action": "move_down"}
        ]
    })
    
    print(f"Memory context: {json.dumps(memory_context, indent=2)}")
    
    # Calculate token estimate
    context_str = json.dumps(memory_context)
    estimated_tokens = len(context_str.split()) + len(context_str) // 4  # Rough estimate
    print(f"\n📊 Estimated token usage: ~{estimated_tokens} tokens")
    
    reader.close()
    print("\n✅ Neo4j Compact Reader test completed!")
    return True


if __name__ == "__main__":
    test_neo4j_compact_reader()