#!/usr/bin/env python3
"""
Test script for the new Pokemon prompt system
Verifies that all template changes work correctly
"""

from prompt_manager import PromptManager

def test_new_prompt_system():
    """Test all the new prompt templates and playbooks"""
    print("🔍 Testing New Pokemon Prompt System")
    print("=" * 50)
    
    # Initialize prompt manager
    pm = PromptManager()
    print("✅ PromptManager initialized")
    
    # Test variables for the scenarios
    test_vars = {
        'task': 'walk around and win pokemon battles',
        'recent_actions': "['right', 'right', 'right']",
        'goal': 'explore viridian forest'
    }
    
    # Test 1: New exploration_strategy template
    print("\n🎮 Testing exploration_strategy template...")
    try:
        prompt = pm.get_prompt('exploration_strategy', test_vars, include_playbook='navigation')
        assert "TRAINERS BATTLE YOU AUTOMATICALLY" in prompt.upper()
        assert "EXPLORE EVERY PART" in prompt.upper()
        assert "DEPTH-FIRST" in prompt.upper()
        print("✅ exploration_strategy template works and contains key concepts")
    except Exception as e:
        print(f"❌ exploration_strategy failed: {e}")
        return False
    
    # Test 2: New stuck_recovery template  
    print("\n🚨 Testing stuck_recovery template...")
    try:
        prompt = pm.get_prompt('stuck_recovery', test_vars)
        assert "PERPENDICULAR" in prompt.upper()
        assert "NEVER REPEAT" in prompt.upper()
        assert "RIGHT" in prompt.upper()
        print("✅ stuck_recovery template works and contains recovery rules")
    except Exception as e:
        print(f"❌ stuck_recovery failed: {e}")
        return False
    
    # Test 3: Updated navigation playbook
    print("\n🗺️ Testing navigation playbook...")
    try:
        navigation_content = pm.playbooks.get('navigation', '')
        assert "TRAINERS BATTLE YOU AUTOMATICALLY" in navigation_content.upper()
        assert "SYSTEMATIC AREA EXPLORATION" in navigation_content.upper()
        assert "DEPTH-FIRST SEARCH" in navigation_content.upper()
        print("✅ navigation playbook updated with core Pokemon mechanics")
    except Exception as e:
        print(f"❌ navigation playbook failed: {e}")
        return False
    
    # Test 4: Updated battle playbook
    print("\n⚔️ Testing battle playbook...")
    try:
        battle_content = pm.playbooks.get('battle', '')
        assert "BATTLES ARE AUTOMATIC" in battle_content.upper()
        assert "YOU DON'T INITIATE THEM" in battle_content.upper()
        print("✅ battle playbook updated with automatic battle info")
    except Exception as e:
        print(f"❌ battle playbook failed: {e}")
        return False
    
    # Test 5: Template integration
    print("\n🔧 Testing full template integration...")
    try:
        # Test exploration with navigation playbook
        full_prompt = pm.get_prompt('exploration_strategy', test_vars, include_playbook='navigation')
        
        # Should contain both template and playbook content
        assert "FUNDAMENTAL" in full_prompt.upper()
        assert "EXPLORATION" in full_prompt.upper()
        print("✅ Template + playbook integration works")
    except Exception as e:
        print(f"❌ Template integration failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! New prompt system is ready.")
    print("\n📋 KEY IMPROVEMENTS:")
    print("✅ AI now knows trainers battle automatically")
    print("✅ Focus on systematic area exploration") 
    print("✅ Clear stuck recovery with perpendicular movement")
    print("✅ Depth-first search strategy for Pokemon areas")
    print("✅ No more confusion about battle initiation")
    
    return True

if __name__ == "__main__":
    success = test_new_prompt_system()
    exit(0 if success else 1)