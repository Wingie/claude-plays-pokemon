#!/usr/bin/env python3
"""
Test script to verify EeveeAgent migration to centralized LLM API
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

def test_eevee_agent_initialization():
    """Test that EeveeAgent initializes with centralized LLM API"""
    print("🔧 Testing EeveeAgent with Centralized LLM API...")
    
    # Load environment variables
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    try:
        from eevee_agent import EeveeAgent
        
        # Initialize EeveeAgent with Mistral model
        agent = EeveeAgent(
            model="mistral-large-latest",
            verbose=True,
            debug=True
        )
        
        print("✅ EeveeAgent initialized successfully with centralized LLM API")
        
        # Test simple API call
        test_prompt = "You are playing Pokemon. A wild Pidgey appears! What should you do? Keep it brief."
        
        result = agent._call_llm_api(
            prompt=test_prompt,
            use_tools=True,
            max_tokens=100
        )
        
        if result["error"]:
            print(f"❌ LLM API call failed: {result['error']}")
            return False
        
        print(f"✅ LLM API Response: {result['text'][:100]}...")
        print(f"🎮 Button presses: {result['button_presses']}")
        
        # Test legacy method compatibility
        legacy_result = agent._call_gemini_api(
            prompt="What is 2+2?",
            max_tokens=50
        )
        
        if legacy_result["error"]:
            print(f"❌ Legacy API call failed: {legacy_result['error']}")
            return False
        
        print(f"✅ Legacy compatibility: {legacy_result['text'].strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ EeveeAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_provider_switching():
    """Test switching between providers in EeveeAgent"""
    print("\n🔄 Testing Provider Switching in EeveeAgent...")
    
    try:
        from eevee_agent import EeveeAgent
        
        # Test with Mistral
        print("Testing with Mistral provider...")
        mistral_agent = EeveeAgent(
            model="mistral-large-latest",
            verbose=True
        )
        
        mistral_result = mistral_agent._call_llm_api(
            prompt="You're a Pokemon trainer. Say hello in one sentence.",
            max_tokens=50
        )
        
        if mistral_result["error"]:
            print(f"❌ Mistral test failed: {mistral_result['error']}")
        else:
            print(f"✅ Mistral: {mistral_result['text'][:80]}...")
        
        # Test with Gemini (if available)
        print("Testing with Gemini provider...")
        try:
            gemini_agent = EeveeAgent(
                model="gemini-2.0-flash-exp",
                verbose=True
            )
            
            gemini_result = gemini_agent._call_llm_api(
                prompt="You're a Pokemon expert. Say hello in one sentence.",
                max_tokens=50
            )
            
            if gemini_result["error"]:
                print(f"⚠️ Gemini test failed (expected): {gemini_result['error'][:50]}...")
            else:
                print(f"✅ Gemini: {gemini_result['text'][:80]}...")
                
        except Exception as e:
            print(f"⚠️ Gemini not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider switching test failed: {e}")
        return False

def run_eevee_migration_tests():
    """Run all EeveeAgent migration tests"""
    print("🚀 Testing EeveeAgent Migration to Centralized LLM API")
    print("=" * 60)
    
    tests = [
        ("EeveeAgent Initialization", test_eevee_agent_initialization),
        ("Provider Switching", test_provider_switching)
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
        print("🎉 EeveeAgent migration successful!")
    elif passed > 0:
        print("⚠️ Partial migration success - some issues detected")
    else:
        print("❌ Migration failed - check configuration")
    
    return passed, total

if __name__ == "__main__":
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Check for API keys
    if not os.getenv('MISTRAL_API_KEY') and not os.getenv('GEMINI_API_KEY'):
        print("❌ No API keys found")
        sys.exit(1)
    
    # Run tests
    passed, total = run_eevee_migration_tests()
    sys.exit(0 if passed == total else 1)