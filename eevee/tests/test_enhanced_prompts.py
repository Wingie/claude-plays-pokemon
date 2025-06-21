#!/usr/bin/env python3
"""
Test script for enhanced prompt system and logging
"""

import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

def test_prompt_manager():
    """Test the simplified PromptManager"""
    print("🧪 Testing PromptManager...")
    
    try:
        from prompt_manager import PromptManager
        
        # Initialize prompt manager
        pm = PromptManager()
        print("✅ PromptManager initialized successfully")
        
        # Test basic prompt retrieval
        prompt = pm.get_prompt("battle_analysis", {"task": "test battle"}, verbose=True)
        print("✅ Basic prompt retrieval works")
        
        # Test playbook integration
        prompt_with_playbook = pm.get_prompt(
            "battle_analysis", 
            {"task": "test battle"}, 
            include_playbook="battle",
            verbose=True
        )
        print("✅ Playbook integration works")
        
        # Test adding navigation knowledge
        pm.add_playbook_entry("navigation", "**Test Entry**: This is a test navigation note")
        print("✅ Navigation learning works")
        
        # Show usage summary
        print(pm.get_usage_summary())
        
        return True
        
    except Exception as e:
        print(f"❌ PromptManager test failed: {e}")
        return False

def test_eevee_integration():
    """Test EeveeAgent integration with prompt system"""
    print("\n🧪 Testing EeveeAgent integration...")
    
    try:
        from eevee_agent import EeveeAgent
        
        # Initialize agent (this should load the prompt manager)
        agent = EeveeAgent(verbose=True, debug=True)
        print("✅ EeveeAgent initialized successfully")
        
        # Check if prompt manager is available
        if hasattr(agent, 'prompt_manager') and agent.prompt_manager:
            print("✅ PromptManager integrated into EeveeAgent")
            
            # Test navigation learning
            agent.learn_navigation_pattern("Viridian City", "north", "Viridian Forest", success=True)
            print("✅ Navigation learning integration works")
            
            # Test location knowledge
            agent.learn_location_knowledge("Viridian City", "Has a Pokemon Center in the center of town", "services")
            print("✅ Location knowledge integration works")
            
        else:
            print("⚠️ PromptManager not available in EeveeAgent")
        
        return True
        
    except Exception as e:
        print(f"❌ EeveeAgent integration test failed: {e}")
        return False

def test_playbook_files():
    """Test that playbook files were created correctly"""
    print("\n🧪 Testing playbook files...")
    
    playbook_dir = Path(__file__).parent / "prompts" / "playbooks"
    expected_files = ["battle.md", "navigation.md", "gyms.md", "services.md"]
    
    success = True
    for filename in expected_files:
        filepath = playbook_dir / filename
        if filepath.exists():
            print(f"✅ {filename} exists")
            
            # Check if file has content
            with open(filepath, 'r') as f:
                content = f.read()
                if len(content) > 50:  # Basic content check
                    print(f"✅ {filename} has content")
                else:
                    print(f"⚠️ {filename} seems empty")
        else:
            print(f"❌ {filename} missing")
            success = False
    
    return success

def main():
    """Run all tests"""
    print("🔬 Enhanced Prompt System Test Suite")
    print("="*50)
    
    test_results = []
    
    # Run tests
    test_results.append(("PromptManager", test_prompt_manager()))
    test_results.append(("EeveeAgent Integration", test_eevee_integration()))
    test_results.append(("Playbook Files", test_playbook_files()))
    
    # Summary
    print("\n📊 Test Results:")
    print("="*50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Enhanced prompt system is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())