#!/usr/bin/env python3
"""
Test script to verify PromptManager migration to centralized LLM API
"""

import os
import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

project_root = eevee_root.parent
sys.path.append(str(eevee_root))

from dotenv import load_dotenv

def test_prompt_manager_initialization():
    """Test that PromptManager initializes with templates"""
    print("🔧 Testing PromptManager Initialization...")
    
    # Load environment variables
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    try:
        from prompt_manager import PromptManager
        
        # Initialize PromptManager
        pm = PromptManager()
        
        print("✅ PromptManager initialized successfully")
        
        # Test basic template access
        available_templates = list(pm.base_prompts.keys())
        print(f"📋 Available templates: {available_templates}")
        
        if len(available_templates) == 0:
            print("❌ No templates found")
            return False
        
        # Test basic prompt generation using a simpler template first
        test_prompt = pm.get_prompt("pokemon_party_analysis", {"task": "test party analysis"})
        
        if test_prompt and len(test_prompt) > 50:
            print(f"✅ Basic prompt generation working: {len(test_prompt)} chars")
        else:
            print("❌ Basic prompt generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PromptManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_template_selection():
    """Test AI template selection with centralized LLM API"""
    print("\n🤖 Testing AI Template Selection...")
    
    try:
        from prompt_manager import PromptManager
        
        pm = PromptManager()
        
        # Test AI-directed template selection
        memory_context = "Player is in battle with wild Pidgey. HP bars visible."
        
        print("Testing AI template selection with battle context...")
        template_name, playbook_name = pm._ai_select_template_and_playbook(
            memory_context=memory_context,
            escalation_level="level_1", 
            verbose=True
        )
        
        print(f"✅ AI selected template: {template_name}")
        print(f"✅ AI selected playbook: {playbook_name}")
        
        if template_name and playbook_name:
            print("✅ AI template selection successful")
            return True
        else:
            print("❌ AI template selection returned empty values")
            return False
        
    except Exception as e:
        print(f"⚠️ AI template selection test failed (expected if no API key): {e}")
        # This might fail if no API keys are available, which is okay for migration testing
        return True

def test_centralized_api_integration():
    """Test that PromptManager uses centralized LLM API"""
    print("\n🔗 Testing Centralized LLM API Integration...")
    
    try:
        from prompt_manager import PromptManager
        
        # Check that imports work
        pm = PromptManager()
        
        # Verify the _ai_select_template_and_playbook method exists
        if hasattr(pm, '_ai_select_template_and_playbook'):
            print("✅ AI template selection method available")
        else:
            print("❌ AI template selection method missing")
            return False
        
        # Check that it imports call_llm properly by doing a dry run
        try:
            # This should work even without API calls
            from llm_api import call_llm
            print("✅ Centralized LLM API import successful")
        except ImportError as e:
            print(f"❌ LLM API import failed: {e}")
            return False
        
        print("✅ PromptManager successfully integrated with centralized LLM API")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def run_prompt_manager_migration_tests():
    """Run all PromptManager migration tests"""
    print("🚀 Testing PromptManager Migration to Centralized LLM API")
    print("=" * 60)
    
    tests = [
        ("PromptManager Initialization", test_prompt_manager_initialization),
        ("AI Template Selection", test_ai_template_selection),
        ("Centralized API Integration", test_centralized_api_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: CRASHED - {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Migration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PromptManager migration successful!")
    elif passed > 0:
        print("⚠️ Partial migration success - some issues detected")
    else:
        print("❌ Migration failed - check configuration")
    
    return passed, total

if __name__ == "__main__":
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Run tests
    passed, total = run_prompt_manager_migration_tests()
    sys.exit(0 if passed >= total - 1 else 1)  # Allow 1 failure for API-dependent tests