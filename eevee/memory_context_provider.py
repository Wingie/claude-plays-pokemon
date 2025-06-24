"""
Memory Context Provider
Provides memory context for injection into navigation prompts using existing memory tools
"""

import json
from typing import Dict, Any, Optional
from memory_tools import MemoryTools


class MemoryContextProvider:
    """Provides memory context for prompt injection using existing memory tools"""
    
    def __init__(self):
        """Initialize with existing memory tools"""
        self.memory_tools = MemoryTools()
        
    def get_memory_context_for_prompt(self, turns: int = 4, visual_context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Get memory context formatted for prompt injection
        
        Args:
            turns: Number of recent turns to include
            visual_context: Current visual analysis result
            
        Returns:
            Dict with formatted memory context for prompt variables
        """
        try:
            # Get recent memory using existing tools
            memory_result = self.memory_tools.get_recent_memory(turns)
            recent_turns = memory_result.get("memory_summary", {}).get("recent_turns", [])
            patterns = memory_result.get("memory_summary", {}).get("patterns", "exploring")
            
            # Format recent turns as compact string
            if recent_turns:
                turns_summary = []
                for turn in recent_turns:
                    summary = f"T{turn.get('turn', '?')}:{turn.get('action', '?')}->{turn.get('result', '?')}"
                    turns_summary.append(summary)
                memory_recent_turns = ", ".join(turns_summary)
            else:
                memory_recent_turns = "no_recent_data"
            
            # Analyze patterns for each direction
            pattern_analysis = []
            for action in ["up", "down", "left", "right"]:
                pattern_result = self.memory_tools.check_pattern(action)
                recommendation = pattern_result.get("recommendation", "unknown")
                success_rate = pattern_result.get("success_rate", 0)
                
                if recommendation == "safe":
                    pattern_analysis.append(f"{action}=safe({success_rate:.1f})")
                elif recommendation == "avoid":
                    pattern_analysis.append(f"{action}=avoid")
                else:
                    pattern_analysis.append(f"{action}=unknown")
            
            memory_patterns = ", ".join(pattern_analysis)
            
            # Get location advice if visual context provided
            if visual_context:
                location_result = self.memory_tools.get_location_memory(visual_context)
                location_advice = location_result.get("location_advice", "no_advice")
            else:
                location_advice = "no_visual_context"
            
            # Return formatted context for prompt injection
            return {
                "memory_recent_turns": memory_recent_turns,
                "memory_patterns": memory_patterns, 
                "memory_location_advice": location_advice
            }
            
        except Exception as e:
            # Fallback context if memory tools fail
            return {
                "memory_recent_turns": f"error: {str(e)[:50]}",
                "memory_patterns": "no_pattern_data",
                "memory_location_advice": "memory_unavailable"
            }
    
    def close(self):
        """Close memory connections"""
        if self.memory_tools:
            self.memory_tools.close()


def test_memory_context_provider():
    """Test the memory context provider"""
    print("🧪 Testing Memory Context Provider")
    print("=" * 50)
    
    provider = MemoryContextProvider()
    
    # Test basic memory context
    print("\n📖 Testing basic memory context...")
    context = provider.get_memory_context_for_prompt(4)
    print("Memory context generated:")
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    # Test with visual context
    print("\n🖼️ Testing with visual context...")
    visual_context = {
        "scene_type": "navigation",
        "player_position": "4,3", 
        "terrain": "grass and water"
    }
    
    context_with_visual = provider.get_memory_context_for_prompt(4, visual_context)
    print("Memory context with visual:")
    for key, value in context_with_visual.items():
        print(f"  {key}: {value}")
    
    # Test prompt formatting
    print("\n📝 Testing prompt formatting...")
    sample_prompt = """
Pokemon Navigation Analysis

**MEMORY CONTEXT:**
Recent turns: {memory_recent_turns}
Pattern analysis: {memory_patterns}
Location advice: {memory_location_advice}

Make your decision based on this memory context.
    """.strip()
    
    formatted_prompt = sample_prompt.format(**context_with_visual)
    print("Formatted prompt:")
    print(formatted_prompt)
    print(f"\nPrompt length: {len(formatted_prompt)} characters")
    
    provider.close()
    print("\n✅ Memory Context Provider test completed!")


if __name__ == "__main__":
    test_memory_context_provider()