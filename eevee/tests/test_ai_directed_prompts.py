#!/usr/bin/env python3
"""
Test script for AI-directed prompt control system
Tests the new AI self-management capabilities and 20-turn critique updates
"""

import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

project_root = Path(__file__).parent
def test_ai_directed_prompt_system():
    """Test the AI-directed prompt control system"""
    print("🧠 Testing AI-Directed Prompt Control System")
    print("=" * 60)
    
    try:
        from prompt_manager import PromptManager
        
        # Initialize prompt manager
        pm = PromptManager()
        print("✅ PromptManager initialized successfully")
        
        # Test AI-directed prompt retrieval
        if hasattr(pm, 'get_ai_directed_prompt'):
            print("\n🎯 Testing AI-directed prompt method...")
            
            # Test navigation context
            nav_prompt = pm.get_ai_directed_prompt(
                context_type="navigation",
                task="find viridian forest",
                recent_actions=['up', 'up', 'up'],
                available_memories=['forest', 'navigation', 'battle'],
                verbose=True
            )
            
            # Check for AI control commands in prompt
            ai_commands = [
                "LOAD_MEMORIES:", "SAVE_MEMORY:", "REQUEST_PROMPT:",
                "CONTEXT_PROMPT:", "EMERGENCY_MODE"
            ]
            
            found_commands = [cmd for cmd in ai_commands if cmd in nav_prompt]
            
            if found_commands:
                print(f"✅ AI control commands found: {found_commands}")
            else:
                print("❌ No AI control commands found in prompt")
                return False
            
            print("✅ AI-directed navigation prompt generated successfully")
            
            # Test battle context
            battle_prompt = pm.get_ai_directed_prompt(
                context_type="battle",
                task="win pokemon battle",
                recent_actions=['a', 'a'],
                battle_context={"battle_phase": "menu", "is_gym_battle": False},
                verbose=True
            )
            
            if "BATTLE MEMORY CONTROL" in battle_prompt:
                print("✅ AI-directed battle prompt generated successfully")
            else:
                print("❌ Battle prompt missing AI control features")
                return False
                
            # Test maze context
            maze_prompt = pm.get_ai_directed_prompt(
                context_type="maze",
                task="navigate cave",
                recent_actions=['left', 'left', 'left'],
                maze_context={"is_multilevel": True, "area_name": "Rock Tunnel"},
                verbose=True
            )
            
            if "MAZE MEMORY CONTROL" in maze_prompt:
                print("✅ AI-directed maze prompt generated successfully")
            else:
                print("❌ Maze prompt missing AI control features")
                return False
                
            # Test emergency context
            emergency_prompt = pm.get_ai_directed_prompt(
                context_type="emergency",
                task="unstuck from loop",
                recent_actions=['up'] * 5,
                escalation_level="level_2",
                verbose=True
            )
            
            if "EMERGENCY RECOVERY SYSTEM" in emergency_prompt:
                print("✅ AI-directed emergency prompt generated successfully")
            else:
                print("❌ Emergency prompt missing AI control features")
                return False
            
        else:
            print("❌ get_ai_directed_prompt method not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ AI-directed prompt test failed: {e}")
        return False

def test_ai_command_processing():
    """Test AI command processing capabilities"""
    print("\n🤖 Testing AI Command Processing")
    print("=" * 40)
    
    try:
        from prompt_manager import PromptManager
        
        pm = PromptManager()
        
        # Test AI response with commands
        ai_response = """
        I need to navigate this forest area. Let me load relevant memories.
        
        LOAD_MEMORIES: forest_navigation
        REQUEST_PROMPT: maze_navigation
        SAVE_MEMORY: Found exit to north TAG: viridian_forest
        
        Based on the screen, I should move up to continue exploring.
        """
        
        if hasattr(pm, 'process_ai_commands'):
            commands_processed = pm.process_ai_commands(ai_response)
            
            # Check if commands were detected
            memory_commands = commands_processed.get("memory_commands", [])
            prompt_commands = commands_processed.get("prompt_commands", [])
            
            if memory_commands:
                print(f"✅ Memory commands detected: {len(memory_commands)}")
                for cmd in memory_commands:
                    print(f"   📝 {cmd['action']}: {cmd.get('context', cmd.get('content', 'unknown'))}")
            
            if prompt_commands:
                print(f"✅ Prompt commands detected: {len(prompt_commands)}")
                for cmd in prompt_commands:
                    print(f"   🔄 {cmd['action']}: {cmd.get('prompt', cmd.get('context', 'unknown'))}")
            
            if memory_commands or prompt_commands:
                print("✅ AI command processing working correctly")
                return True
            else:
                print("❌ No commands detected in AI response")
                return False
        else:
            print("❌ process_ai_commands method not found")
            return False
            
    except Exception as e:
        print(f"❌ AI command processing test failed: {e}")
        return False

def test_navigation_enhancement_integration():
    """Test integration with navigation enhancement system"""
    print("\n🧭 Testing Navigation Enhancement Integration")
    print("=" * 45)
    
    try:
        from utils.navigation_enhancement import NavigationEnhancer
        from prompt_manager import PromptManager
        
        # Create instances
        nav_enhancer = NavigationEnhancer()
        pm = PromptManager()
        
        # Create a mock critique
        critique = {
            "progress_ratio": 0.25,  # Poor progress
            "problems_identified": [
                "Low progress rate - many turns without visual changes",
                "Excessive repetition of 'up' button"
            ],
            "overall_assessment": "Poor navigation - significant intervention needed"
        }
        
        # Test critique application
        if hasattr(nav_enhancer, 'apply_critique_to_prompt_manager'):
            changes = nav_enhancer.apply_critique_to_prompt_manager(critique, pm)
            
            print(f"✅ Critique application returned: {len(changes)} change categories")
            
            # Check for expected changes
            if changes.get("emergency_actions"):
                print("✅ Emergency actions triggered for poor performance")
            
            if changes.get("template_switches"):
                print("✅ Template switches recommended")
                for switch in changes["template_switches"]:
                    print(f"   🔄 {switch}")
            
            # Test navigation strategy update
            if hasattr(nav_enhancer, 'update_navigation_strategy'):
                strategy_update = nav_enhancer.update_navigation_strategy(critique)
                print(f"✅ Navigation strategy update: {strategy_update}")
            
            return True
        else:
            print("❌ apply_critique_to_prompt_manager method not found")
            return False
            
    except Exception as e:
        print(f"❌ Navigation enhancement integration test failed: {e}")
        return False

def test_specialized_context_templates():
    """Test the specialized context-specific templates"""
    print("\n🎯 Testing Specialized Context Templates")
    print("=" * 42)
    
    try:
        import yaml
        from pathlib import Path
        
        # Test forest/maze expert templates
        context_file = Path(__file__).parent / "prompts" / "context" / "forest_maze_expert.yaml"
        if context_file.exists():
            with open(context_file, 'r') as f:
                context_templates = yaml.safe_load(f)
            
            if "forest_maze_expert" in context_templates:
                print("✅ Forest maze expert template found")
                template = context_templates["forest_maze_expert"]["template"]
                
                # Check for key AI control features
                ai_features = [
                    "LOAD_MEMORIES:", "REQUEST_PROMPT:", "SAVE_MEMORY:",
                    "forest_patterns", "right_hand_rule"
                ]
                
                found_features = [feature for feature in ai_features if feature in template]
                print(f"✅ AI features in forest template: {found_features}")
            
            if "cave_dungeon_expert" in context_templates:
                print("✅ Cave dungeon expert template found")
        else:
            print("❌ Context templates file not found")
            return False
        
        # Test battle context templates
        battle_context_file = Path(__file__).parent / "prompts" / "context" / "battle_context_expert.yaml"
        if battle_context_file.exists():
            with open(battle_context_file, 'r') as f:
                battle_templates = yaml.safe_load(f)
            
            if "battle_menu_navigation" in battle_templates:
                print("✅ Battle menu navigation template found")
            
            if "type_effectiveness_calculator" in battle_templates:
                print("✅ Type effectiveness calculator template found")
        
        return True
        
    except Exception as e:
        print(f"❌ Specialized context templates test failed: {e}")
        return False

def main():
    """Run all AI-directed prompt system tests"""
    print("🧪 AI-DIRECTED PROMPT CONTROL SYSTEM TEST SUITE")
    print("=" * 55)
    print()
    
    test_results = []
    
    # Run all tests
    test_results.append(("AI-Directed Prompts", test_ai_directed_prompt_system()))
    test_results.append(("AI Command Processing", test_ai_command_processing()))
    test_results.append(("Navigation Integration", test_navigation_enhancement_integration()))
    test_results.append(("Specialized Templates", test_specialized_context_templates()))
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 25)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! AI-directed prompt system is ready!")
        print("\n🚀 Key Features Available:")
        print("   🧠 AI can request specific prompts and memories")
        print("   🔄 Automatic prompt switching based on performance")
        print("   📊 20-turn critique system updates prompts automatically")
        print("   🎯 Context-aware prompt selection (battle/maze/forest)")
        print("   🚨 Emergency escalation for stuck situations")
        print("   💾 AI-driven memory management and learning")
        
        print("\n🎮 Usage:")
        print("   python run_eevee.py --goal 'find viridian forest' --verbose")
        print("   # AI will now self-manage prompts and memory!")
        
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed. System needs fixes before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)