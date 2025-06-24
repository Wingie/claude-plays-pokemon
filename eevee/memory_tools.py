"""
Memory Tools for Eevee Agent
Provides memory functions that the AI can choose to use as tools
"""

import json
import time
from typing import Dict, List, Any, Optional, Union
from neo4j_compact_reader import Neo4jCompactReader


class MemoryTools:
    """Memory tools that AI agent can choose to use"""
    
    def __init__(self):
        """Initialize memory tools with Neo4j connection"""
        self.reader = Neo4jCompactReader()
        self.session_id = f"session_{int(time.time())}"
        
    def close(self):
        """Close memory connections"""
        if self.reader:
            self.reader.close()
    
    # MEMORY READING TOOLS
    
    def get_recent_memory(self, turns: int = 4) -> Dict[str, Any]:
        """
        Get recent memory context for decision making
        
        Args:
            turns: Number of recent turns to retrieve (1-10)
            
        Returns:
            Dict with recent turns and patterns
        """
        try:
            turns = max(1, min(10, turns))  # Limit between 1-10
            recent_turns = self.reader.get_recent_turns(turns)
            memory_summary = self.reader.format_turns_to_compact_json(recent_turns)
            
            return {
                "success": True,
                "memory_summary": memory_summary,
                "turns_retrieved": len(recent_turns),
                "token_estimate": self._estimate_tokens(memory_summary)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "memory_summary": {"recent_turns": [], "patterns": "error"}
            }
    
    def check_pattern(self, action: str) -> Dict[str, Any]:
        """
        Check if an action has been tried before and its success rate
        
        Args:
            action: Action to check (up, down, left, right, a, b)
            
        Returns:
            Dict with pattern analysis for the action
        """
        try:
            recent_turns = self.reader.get_recent_turns(10)  # Look at more turns for patterns
            
            # Count occurrences and outcomes of this action
            action_count = 0
            success_count = 0
            blocked_count = 0
            contexts = []
            
            for turn in recent_turns:
                turn_action = ""
                if turn.get("button_presses"):
                    if isinstance(turn["button_presses"], list):
                        turn_action = turn["button_presses"][0] if turn["button_presses"] else ""
                    else:
                        turn_action = str(turn["button_presses"])
                
                if turn_action.lower() == action.lower():
                    action_count += 1
                    
                    # Analyze outcome from gemini_text
                    text = turn.get("gemini_text", "").lower()
                    if "blocked" in text or "wall" in text or "tree" in text or "failed" in text:
                        blocked_count += 1
                    else:
                        success_count += 1
                    
                    # Extract context
                    if "grass" in text:
                        contexts.append("grass")
                    elif "forest" in text:
                        contexts.append("forest")
                    elif "water" in text:
                        contexts.append("water")
                    elif "building" in text:
                        contexts.append("building")
            
            success_rate = (success_count / action_count) if action_count > 0 else 0
            
            return {
                "success": True,
                "action": action,
                "total_attempts": action_count,
                "success_count": success_count,
                "blocked_count": blocked_count,
                "success_rate": round(success_rate, 2),
                "common_contexts": list(set(contexts)),
                "recommendation": "avoid" if success_rate < 0.3 else "safe" if success_rate > 0.7 else "caution"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendation": "unknown"
            }
    
    def get_location_memory(self, visual_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get memory relevant to current location/visual context
        
        Args:
            visual_context: Current visual analysis result
            
        Returns:
            Dict with location-specific memory
        """
        try:
            # Extract location features
            current_pos = visual_context.get("player_position", "unknown")
            current_terrain = visual_context.get("terrain", "unknown")
            
            recent_turns = self.reader.get_recent_turns(8)
            
            # Find turns with similar contexts
            similar_contexts = []
            for turn in recent_turns:
                text = turn.get("gemini_text", "").lower()
                
                # Simple similarity matching
                terrain_match = False
                if "grass" in current_terrain.lower() and "grass" in text:
                    terrain_match = True
                elif "water" in current_terrain.lower() and "water" in text:
                    terrain_match = True
                elif "forest" in current_terrain.lower() and ("tree" in text or "forest" in text):
                    terrain_match = True
                
                if terrain_match:
                    similar_contexts.append({
                        "turn": turn.get("turn_id"),
                        "action": turn.get("button_presses"),
                        "outcome": "success" if "moved" in text else "blocked"
                    })
            
            return {
                "success": True,
                "current_location": {
                    "position": current_pos,
                    "terrain": current_terrain
                },
                "similar_contexts": similar_contexts[:4],  # Limit to 4 most recent
                "location_advice": self._generate_location_advice(similar_contexts)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "location_advice": "no_data"
            }
    
    # MEMORY WRITING TOOLS
    
    def store_observation(self, observation: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store an observation or insight to memory
        
        Args:
            observation: Text observation to store
            context: Additional context data
            
        Returns:
            Dict with storage result
        """
        try:
            # For now, store in compact memory tools (could extend to Neo4j later)
            if hasattr(self, '_observations'):
                self._observations = getattr(self, '_observations', [])
            else:
                self._observations = []
            
            observation_entry = {
                "timestamp": time.time(),
                "observation": observation,
                "context": context or {},
                "session": self.session_id
            }
            
            self._observations.append(observation_entry)
            
            # Keep only last 20 observations
            if len(self._observations) > 20:
                self._observations = self._observations[-20:]
            
            return {
                "success": True,
                "stored": True,
                "observation_count": len(self._observations)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stored": False
            }
    
    def store_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a recognized pattern for future reference
        
        Args:
            pattern_name: Name/identifier for the pattern
            pattern_data: Pattern details and context
            
        Returns:
            Dict with storage result
        """
        try:
            if not hasattr(self, '_patterns'):
                self._patterns = {}
            
            self._patterns[pattern_name] = {
                "timestamp": time.time(),
                "data": pattern_data,
                "session": self.session_id
            }
            
            return {
                "success": True,
                "pattern_stored": pattern_name,
                "total_patterns": len(self._patterns)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pattern_stored": False
            }
    
    # UTILITY FUNCTIONS
    
    def _estimate_tokens(self, data: Any) -> int:
        """Estimate token count for data"""
        text = json.dumps(data) if not isinstance(data, str) else data
        return len(text.split()) + len(text) // 4
    
    def _generate_location_advice(self, similar_contexts: List[Dict[str, Any]]) -> str:
        """Generate advice based on similar location contexts"""
        if not similar_contexts:
            return "explore_carefully"
        
        success_count = sum(1 for ctx in similar_contexts if ctx.get("outcome") == "success")
        total_count = len(similar_contexts)
        
        if success_count / total_count > 0.7:
            return "location_safe"
        elif success_count / total_count < 0.3:
            return "location_risky"
        else:
            return "location_mixed"


# TOOL FUNCTION DECLARATIONS FOR AI AGENT

def create_memory_tool_declarations():
    """
    Create tool declarations that can be provided to the AI agent
    Similar to pokemon_controller tools but for memory access
    """
    
    memory_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_recent_memory",
                "description": "Get recent memory of last few turns to inform current decision. Use when you want to avoid repeating mistakes or build on previous success.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "turns": {
                            "type": "integer",
                            "description": "Number of recent turns to retrieve (1-10)",
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["turns"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "check_pattern",
                "description": "Check if a specific action (up/down/left/right/a/b) has been tried before and its success rate. Use before making risky moves.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right", "a", "b", "start", "select"],
                            "description": "Action to check for historical success/failure"
                        }
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_location_memory", 
                "description": "Get memory relevant to current visual context/location. Use when entering new areas or trying to navigate familiar terrain.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "visual_context": {
                            "type": "object",
                            "description": "Current visual analysis result with terrain, position, etc."
                        }
                    },
                    "required": ["visual_context"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "store_observation",
                "description": "Store an important observation or insight for future reference. Use when you discover something useful.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "observation": {
                            "type": "string",
                            "description": "Text description of the observation"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context data (optional)"
                        }
                    },
                    "required": ["observation"]
                }
            }
        }
    ]
    
    return memory_tools


def test_memory_tools():
    """Test memory tools functionality"""
    print("🧪 Testing Memory Tools")
    print("=" * 50)
    
    tools = MemoryTools()
    
    # Test memory reading
    print("\n📖 Testing get_recent_memory...")
    result = tools.get_recent_memory(4)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test pattern checking
    print("\n🔍 Testing check_pattern...")
    result = tools.check_pattern("up")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test observation storage
    print("\n💾 Testing store_observation...")
    result = tools.store_observation("Found a blocked path to the north", {"terrain": "forest"})
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test tool declarations
    print("\n🛠️ Testing tool declarations...")
    declarations = create_memory_tool_declarations()
    print(f"Created {len(declarations)} tool declarations")
    
    tools.close()
    print("\n✅ Memory Tools test completed!")


if __name__ == "__main__":
    test_memory_tools()