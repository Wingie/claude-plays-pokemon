#!/usr/bin/env python3
"""
Test script to verify that the playbook and navigation system fixes work correctly
"""

import sys
from pathlib import Path

# Add eevee directory to path
sys.path.append(str(Path(__file__).parent))

from prompt_manager import PromptManager
from memory_system import MemorySystem

def test_prompt_manager_playbooks():
    """Test that prompt manager loads playbooks correctly"""
    print("🧪 Testing Prompt Manager with Playbooks...")
    
    # Initialize prompt manager
    pm = PromptManager()
    
    # Check that playbooks are loaded
    print(f"📚 Available playbooks: {list(pm.playbooks.keys())}")
    
    # Test AI-directed prompt with navigation context
    try:
        prompt = pm.get_ai_directed_prompt(
            context_type="navigation",
            task="find a Pokemon ball",
            recent_actions=["up", "up", "up"],
            verbose=True
        )
        
        print("✅ AI-directed prompt with navigation playbook generated successfully")
        
        # Check if navigation playbook content is included
        if "Navigation" in prompt or "POKEMON GAME RULES" in prompt:
            print("✅ Navigation playbook content found in prompt")
        else:
            print("❌ Navigation playbook content missing from prompt")
            
    except Exception as e:
        print(f"❌ AI-directed prompt failed: {e}")
    
    # Test regular prompt with playbook
    try:
        prompt = pm.get_prompt(
            "exploration_strategy",
            {"task": "test task"},
            include_playbook="navigation",
            verbose=True
        )
        
        print("✅ Regular prompt with playbook generated successfully")
        
    except Exception as e:
        print(f"❌ Regular prompt with playbook failed: {e}")

def test_memory_system():
    """Test that memory system works correctly"""
    print("\n🧪 Testing Memory System...")
    
    # Initialize memory system
    memory = MemorySystem(session_name="test_fix")
    
    # Test recent gameplay summary
    try:
        summary = memory.get_recent_gameplay_summary()
        print(f"✅ Memory summary generated: {summary[:100]}...")
        
    except Exception as e:
        print(f"❌ Memory summary failed: {e}")
    
    # Test storing gameplay turn
    try:
        turn_id = memory.store_gameplay_turn(
            turn_number=1,
            analysis="Test analysis",
            actions=["up", "a"],
            success=True,
            reasoning="Test reasoning"
        )
        print(f"✅ Gameplay turn stored with ID: {turn_id}")
        
    except Exception as e:
        print(f"❌ Gameplay turn storage failed: {e}")
    
    # Clean up test data
    try:
        memory.clear_session()
        print("✅ Test session cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing Eevee Navigation and Playbook Fixes\n")
    
    test_prompt_manager_playbooks()
    test_memory_system()
    
    print("\n🎯 Test completed!")