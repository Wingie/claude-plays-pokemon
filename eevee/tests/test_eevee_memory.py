#!/usr/bin/env python3
"""
Test Eevee Memory Integration
Tests memory tools integration with Eevee agent for memory-driven decisions
"""

import sys
import json
import time
from pathlib import Path

# Add paths for importing
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from memory_tools import MemoryTools, create_memory_tool_declarations
    from eevee_agent import EeveeAgent
    from visual_analysis import VisualAnalysis
    from prompt_manager import PromptManager
    
    print("✅ All imports successful")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class EeveeMemoryTester:
    """Test harness for Eevee memory integration"""
    
    def __init__(self):
        """Initialize memory testing components"""
        self.memory_tools = MemoryTools()
        self.visual_analysis = VisualAnalysis()
        self.prompt_manager = PromptManager()
        
        # Store memory tool functions for agent access
        self.available_memory_functions = {
            "get_recent_memory": self.memory_tools.get_recent_memory,
            "check_pattern": self.memory_tools.check_pattern,
            "get_location_memory": self.memory_tools.get_location_memory,
            "store_observation": self.memory_tools.store_observation
        }
        
        print("🧠 Memory testing environment initialized")
    
    def test_memory_tool_access(self):
        """Test basic memory tool access"""
        print("\n" + "="*60)
        print("🧪 TESTING MEMORY TOOL ACCESS")
        print("="*60)
        
        # Test get_recent_memory
        print("\n📖 Testing get_recent_memory...")
        memory_result = self.available_memory_functions["get_recent_memory"](4)
        print(f"Memory retrieved: {memory_result['turns_retrieved']} turns")
        print(f"Pattern detected: {memory_result['memory_summary']['patterns']}")
        print(f"Token estimate: {memory_result['token_estimate']}")
        
        # Test check_pattern
        print("\n🔍 Testing check_pattern...")
        pattern_result = self.available_memory_functions["check_pattern"]("up")
        print(f"Action 'up' analysis: {pattern_result['recommendation']} (success rate: {pattern_result['success_rate']})")
        
        # Test store_observation
        print("\n💾 Testing store_observation...")
        obs_result = self.available_memory_functions["store_observation"](
            "Testing memory integration - found grass terrain", 
            {"test": True, "terrain": "grass"}
        )
        print(f"Observation stored: {obs_result['stored']}")
        
        return True
    
    def test_visual_analysis_with_memory(self):
        """Test combining visual analysis with memory context"""
        print("\n" + "="*60)
        print("🧪 TESTING VISUAL ANALYSIS + MEMORY")
        print("="*60)
        
        try:
            # Get current visual analysis
            print("\n📸 Capturing current visual state...")
            visual_result = self.visual_analysis.analyze_current_scene(
                verbose=True, 
                session_name="memory_test"
            )
            
            print(f"Visual analysis success: {visual_result.get('success', False)}")
            if visual_result.get('success'):
                movement_data = visual_result.get('movement_data', {})
                print(f"Scene type: {movement_data.get('scene_type', 'unknown')}")
                print(f"Valid movements: {movement_data.get('valid_movements', [])}")
                
                # Get memory relevant to this location
                print("\n🗺️ Getting location-relevant memory...")
                location_memory = self.available_memory_functions["get_location_memory"](movement_data)
                print(f"Location advice: {location_memory.get('location_advice', 'unknown')}")
                print(f"Similar contexts found: {len(location_memory.get('similar_contexts', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ Visual analysis error: {e}")
            return False
    
    def simulate_memory_driven_decision(self):
        """Simulate how an AI agent would use memory to make decisions"""
        print("\n" + "="*60)
        print("🧪 SIMULATING MEMORY-DRIVEN DECISION")
        print("="*60)
        
        # Step 1: Get recent memory
        print("\n🧠 Step 1: Checking recent memory...")
        memory_context = self.available_memory_functions["get_recent_memory"](4)
        recent_turns = memory_context["memory_summary"]["recent_turns"]
        
        if recent_turns:
            print(f"Last {len(recent_turns)} turns:")
            for turn in recent_turns:
                print(f"  Turn {turn['turn']}: {turn['action']} -> {turn['result']} ({turn['context']})")
        
        # Step 2: Check pattern for potential actions
        potential_actions = ["up", "down", "left", "right"]
        action_analysis = {}
        
        print("\n🔍 Step 2: Analyzing action patterns...")
        for action in potential_actions:
            pattern_result = self.available_memory_functions["check_pattern"](action)
            action_analysis[action] = pattern_result
            print(f"  {action}: {pattern_result['recommendation']} (success: {pattern_result['success_rate']})")
        
        # Step 3: Make memory-informed decision
        print("\n🎯 Step 3: Making memory-informed decision...")
        
        # Simple decision logic based on memory
        best_action = "up"  # default
        best_score = -1
        
        for action, analysis in action_analysis.items():
            score = analysis['success_rate']
            if analysis['recommendation'] == "safe":
                score += 0.3
            elif analysis['recommendation'] == "avoid":
                score -= 0.5
            
            if score > best_score:
                best_score = score
                best_action = action
        
        # Generate camelCase reasoning based on memory
        memory_pattern = memory_context["memory_summary"]["patterns"]
        reasoning = f"memoryGuided{best_action.title()}_{memory_pattern}"
        
        decision = {
            "button": best_action,
            "reasoning": reasoning,
            "confidence": "high" if best_score > 0.5 else "medium" if best_score > 0 else "low",
            "memory_used": True,
            "memory_context": {
                "recent_turns": len(recent_turns),
                "pattern": memory_pattern,
                "action_analysis": {k: v['recommendation'] for k, v in action_analysis.items()}
            }
        }
        
        print(f"🤖 Final Decision: {json.dumps(decision, indent=2)}")
        
        # Step 4: Store this decision as an observation
        print("\n💾 Step 4: Storing decision observation...")
        obs_result = self.available_memory_functions["store_observation"](
            f"Made memory-driven decision: {best_action} with reasoning {reasoning}",
            decision
        )
        print(f"Observation stored: {obs_result['stored']}")
        
        return decision
    
    def test_prompt_integration(self):
        """Test how memory context can be integrated into prompts"""
        print("\n" + "="*60)
        print("🧪 TESTING PROMPT INTEGRATION")
        print("="*60)
        
        # Get memory context
        memory_context = self.available_memory_functions["get_recent_memory"](4)
        
        # Create a sample prompt with memory context
        prompt_template = """
Pokemon Navigation Decision

**CURRENT SITUATION:**
- Available actions: up, down, left, right
- Goal: Navigate efficiently

**MEMORY CONTEXT:**
Recent turns: {recent_turns}
Pattern detected: {pattern}
Token usage: {tokens} tokens

**INSTRUCTIONS:**
Use memory to make optimal decision. Return JSON:
{{"button": "action", "reasoning": "camelCaseReason"}}
        """.strip()
        
        formatted_prompt = prompt_template.format(
            recent_turns=json.dumps(memory_context["memory_summary"]["recent_turns"]),
            pattern=memory_context["memory_summary"]["patterns"],
            tokens=memory_context["token_estimate"]
        )
        
        print(f"\n📝 Sample prompt with memory context:")
        print(f"Prompt length: {len(formatted_prompt)} characters")
        print(f"Estimated tokens: ~{len(formatted_prompt.split()) + len(formatted_prompt)//4}")
        print("\nPrompt preview:")
        print(formatted_prompt[:300] + "..." if len(formatted_prompt) > 300 else formatted_prompt)
        
        return True
    
    def run_complete_test(self):
        """Run complete memory integration test"""
        print("🚀 STARTING COMPLETE EEVEE MEMORY INTEGRATION TEST")
        print("="*80)
        
        success_count = 0
        total_tests = 4
        
        # Test 1: Basic memory tool access
        if self.test_memory_tool_access():
            success_count += 1
            print("✅ Memory tool access: PASSED")
        else:
            print("❌ Memory tool access: FAILED")
        
        # Test 2: Visual analysis with memory
        if self.test_visual_analysis_with_memory():
            success_count += 1
            print("✅ Visual analysis + memory: PASSED")
        else:
            print("❌ Visual analysis + memory: FAILED")
        
        # Test 3: Memory-driven decision simulation
        try:
            decision = self.simulate_memory_driven_decision()
            if decision and "button" in decision:
                success_count += 1
                print("✅ Memory-driven decision: PASSED")
            else:
                print("❌ Memory-driven decision: FAILED")
        except Exception as e:
            print(f"❌ Memory-driven decision: FAILED ({e})")
        
        # Test 4: Prompt integration
        if self.test_prompt_integration():
            success_count += 1
            print("✅ Prompt integration: PASSED")
        else:
            print("❌ Prompt integration: FAILED")
        
        # Final results
        print("\n" + "="*80)
        print(f"🏁 FINAL RESULTS: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 ALL TESTS PASSED! Memory integration is working!")
        elif success_count >= total_tests // 2:
            print("⚠️ Most tests passed. Memory integration is mostly working.")
        else:
            print("❌ Multiple test failures. Memory integration needs work.")
        
        return success_count == total_tests
    
    def cleanup(self):
        """Clean up resources"""
        if self.memory_tools:
            self.memory_tools.close()


def main():
    """Main test function"""
    tester = EeveeMemoryTester()
    
    try:
        success = tester.run_complete_test()
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())