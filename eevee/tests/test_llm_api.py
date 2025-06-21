#!/usr/bin/env python3
"""
Test script for the unified LLM API system
Tests both Gemini and Mistral providers with various scenarios
"""

import os
import sys
import time
import base64
from pathlib import Path

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

project_root = Path(__file__).parent.parent.parent  # Go up from tests/eevee/ to root
eevee_root = Path(__file__).parent.parent  # eevee directory
from llm_api import LLMAPIManager, call_llm, get_llm_manager, LLMResponse
from dotenv import load_dotenv

def test_initialization():
    """Test LLM API manager initialization"""
    print("🔧 Testing LLM API Manager Initialization...")
    
    # Load environment variables from eevee/.env
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    try:
        manager = LLMAPIManager()
        providers = manager.get_available_providers()
        print(f"✅ LLM API Manager initialized successfully")
        print(f"📋 Available providers: {providers}")
        
        if not providers:
            print("❌ No providers available - check your API keys")
            return False
        
        # Test provider status
        status = manager.get_provider_status()
        for provider, info in status.items():
            print(f"📊 {provider}: {len(info['available_models'])} models, circuit breaker: {info['circuit_breaker_open']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_gemini_provider():
    """Test Gemini provider functionality"""
    print("\n🤖 Testing Gemini Provider...")
    
    try:
        # Test simple text call
        response = call_llm(
            prompt="What is 2+2? Answer with just the number.",
            provider="gemini",
            max_tokens=50
        )
        
        if response.error:
            print(f"❌ Gemini text test failed: {response.error}")
            return False
        
        print(f"✅ Gemini text response: '{response.text.strip()}'")
        print(f"⏱️ Response time: {response.response_time:.2f}s")
        print(f"🔧 Model used: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

def test_mistral_provider():
    """Test Mistral provider functionality"""
    print("\n🦾 Testing Mistral Provider...")
    
    try:
        # Test simple text call
        response = call_llm(
            prompt="What is 3+3? Answer with just the number.",
            provider="mistral",
            max_tokens=50
        )
        
        if response.error:
            print(f"❌ Mistral text test failed: {response.error}")
            return False
        
        print(f"✅ Mistral text response: '{response.text.strip()}'")
        print(f"⏱️ Response time: {response.response_time:.2f}s")
        print(f"🔧 Model used: {response.model}")
        
        if response.tokens_used:
            print(f"📊 Tokens used: {response.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mistral test failed: {e}")
        return False

def test_pokemon_prompt():
    """Test Pokemon-specific prompts with both providers"""
    print("\n🎮 Testing Pokemon-Specific Prompts...")
    
    pokemon_prompt = """You are playing Pokemon Red. You can see a wild Pidgey appeared! 
Your Pikachu has these moves: Thundershock, Tackle, Growl, Tail Whip.
What move should you use against Pidgey? Explain briefly and recommend a specific action."""
    
    # Test with Gemini
    print("Testing Gemini with Pokemon prompt...")
    gemini_response = call_llm(
        prompt=pokemon_prompt,
        provider="gemini",
        use_tools=True,
        max_tokens=200
    )
    
    if gemini_response.error:
        print(f"❌ Gemini Pokemon test failed: {gemini_response.error}")
    else:
        print(f"✅ Gemini Pokemon analysis: {gemini_response.text[:100]}...")
        print(f"🎮 Button presses: {gemini_response.button_presses}")
    
    # Test with Mistral
    print("\nTesting Mistral with Pokemon prompt...")
    mistral_response = call_llm(
        prompt=pokemon_prompt,
        provider="mistral", 
        max_tokens=200
    )
    
    if mistral_response.error:
        print(f"❌ Mistral Pokemon test failed: {mistral_response.error}")
    else:
        print(f"✅ Mistral Pokemon analysis: {mistral_response.text[:100]}...")
        print(f"🎮 Button presses: {mistral_response.button_presses}")
    
    return not (gemini_response.error and mistral_response.error)

def test_vision_with_sample_image():
    """Test vision capabilities with a sample image"""
    print("\n👁️ Testing Vision Capabilities...")
    
    # Look for sample Pokemon screenshot
    screenshot_paths = [
        "emulator_screen.jpg",
        "eevee/analysis/skyemu_screenshot_20250620_112642.png",
        "screenshots/turn_000.jpg"
    ]
    
    sample_image = None
    for path in screenshot_paths:
        full_path = project_root / path
        if full_path.exists():
            sample_image = full_path
            break
    
    if not sample_image:
        print("⚠️ No sample Pokemon screenshot found, skipping vision test")
        return True
    
    print(f"📸 Using sample image: {sample_image}")
    
    # Read and encode image
    try:
        with open(sample_image, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Failed to read sample image: {e}")
        return False
    
    vision_prompt = """Look at this Pokemon game screenshot. What do you see? 
Describe the current game state in 1-2 sentences."""
    
    # Test Gemini vision
    print("Testing Gemini vision...")
    gemini_vision = call_llm(
        prompt=vision_prompt,
        image_data=image_data,
        provider="gemini",
        max_tokens=150
    )
    
    if gemini_vision.error:
        print(f"❌ Gemini vision test failed: {gemini_vision.error}")
    else:
        print(f"✅ Gemini vision: {gemini_vision.text[:100]}...")
    
    # Test Mistral vision (Pixtral)
    print("Testing Mistral vision (Pixtral)...")
    mistral_vision = call_llm(
        prompt=vision_prompt,
        image_data=image_data,
        provider="mistral",
        model="pixtral-12b-2409",
        max_tokens=150
    )
    
    if mistral_vision.error:
        print(f"❌ Mistral vision test failed: {mistral_vision.error}")
    else:
        print(f"✅ Mistral vision: {mistral_vision.text[:100]}...")
    
    return not (gemini_vision.error and mistral_vision.error)

def test_provider_switching():
    """Test automatic provider switching"""
    print("\n🔄 Testing Provider Switching...")
    
    manager = get_llm_manager()
    available_providers = manager.get_available_providers()
    
    if len(available_providers) < 2:
        print(f"⚠️ Only {len(available_providers)} provider(s) available, skipping switching test")
        return True
    
    # Test switching between providers
    for provider in available_providers:
        print(f"Switching to {provider}...")
        success = manager.set_provider(provider)
        if success:
            response = call_llm(f"You are now using {provider}. Respond with 'Hello from {provider}'", max_tokens=50)
            if response.error:
                print(f"❌ {provider} failed: {response.error}")
            else:
                print(f"✅ {provider}: {response.text.strip()}")
        else:
            print(f"❌ Failed to switch to {provider}")
    
    return True

def test_error_handling():
    """Test error handling scenarios"""
    print("\n⚠️ Testing Error Handling...")
    
    # Test with invalid model
    print("Testing invalid model handling...")
    response = call_llm(
        prompt="Test invalid model",
        model="invalid-model-name",
        max_tokens=50
    )
    
    if response.error:
        print(f"✅ Invalid model handled correctly: {response.error}")
    else:
        print("⚠️ Invalid model test didn't produce expected error")
    
    # Test with very long prompt (should handle gracefully)
    print("Testing very long prompt...")
    long_prompt = "This is a test prompt. " * 1000  # Very long prompt
    response = call_llm(
        prompt=long_prompt,
        max_tokens=50
    )
    
    if response.error:
        print(f"✅ Long prompt handled: {response.error[:100]}...")
    else:
        print(f"✅ Long prompt processed successfully: {len(response.text)} chars")
    
    return True

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 Starting Comprehensive LLM API Tests")
    print("=" * 60)
    
    tests = [
        ("Initialization", test_initialization),
        ("Gemini Provider", test_gemini_provider),
        ("Mistral Provider", test_mistral_provider),
        ("Pokemon Prompts", test_pokemon_prompt),
        ("Vision Capabilities", test_vision_with_sample_image),
        ("Provider Switching", test_provider_switching),
        ("Error Handling", test_error_handling)
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
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LLM API system is ready.")
    elif passed > total // 2:
        print("⚠️ Most tests passed, system partially functional.")
    else:
        print("❌ Multiple failures detected, check configuration.")
    
    return passed, total

if __name__ == "__main__":
    # Load environment variables from eevee/.env
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Check for API keys
    if not os.getenv('GEMINI_API_KEY') and not os.getenv('MISTRAL_API_KEY'):
        print("❌ No API keys found in environment variables")
        print(f"Looked for .env file at: {env_file}")
        print("Please set GEMINI_API_KEY and/or MISTRAL_API_KEY")
        sys.exit(1)
    
    # Run tests
    passed, total = run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)