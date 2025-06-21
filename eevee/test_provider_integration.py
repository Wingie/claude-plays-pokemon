#!/usr/bin/env python3
"""
Test complete provider-specific system: prompts + function calling + LLM API
"""

import os
import sys
from pathlib import Path

# Add project paths
eevee_root = Path(__file__).parent
project_root = eevee_root.parent
sys.path.append(str(project_root))
sys.path.append(str(eevee_root))

from dotenv import load_dotenv
from prompt_manager import PromptManager

def test_provider_integration():
    """Test complete provider integration with real LLM calls"""
    print("🧪 Testing Complete Provider Integration")
    print("=" * 80)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Get screenshot for testing
    screenshot_files = list(Path(".").glob("**/skyemu_screenshot*.png"))
    if not screenshot_files:
        print("❌ No screenshot files found for testing")
        print("💡 Run a game session first to generate screenshots")
        return
    
    print(f"📸 Using screenshot: {screenshot_files[0]}")
    
    # Test with both providers
    providers = ["mistral", "gemini"]
    
    for provider in providers:
        print(f"\n{'='*60}")
        print(f"🧪 Testing {provider.upper()} Provider Integration")
        print(f"{'='*60}")
        
        # Set environment
        os.environ['LLM_PROVIDER'] = provider
        
        # Initialize PromptManager
        prompt_manager = PromptManager()
        
        # Check provider info
        info = prompt_manager.get_current_provider_info()
        print(f"📊 Provider Info:")
        print(f"   Current: {info['current_provider']}")
        print(f"   Provider-specific loaded: {info['provider_specific_loaded']}")
        print(f"   Template count: {info['template_count']}")
        
        # Test prompt generation
        prompt = prompt_manager.get_ai_directed_prompt(
            context_type="auto_select",
            task=f"test {provider} integration",
            recent_actions=["up", "a"],
            memory_context="Testing provider integration with battle context",
            verbose=True
        )
        
        print(f"\n📝 Generated Prompt Preview:")
        print(f"   Length: {len(prompt)} chars")
        print(f"   First 150 chars: {prompt[:150]}...")
        
        # Test function calling
        try:
            from llm_api import call_llm
            from skyemu_controller import read_image_to_base64
            
            image_data = read_image_to_base64(str(screenshot_files[0]))
            
            print(f"\n🔧 Testing Function Calling:")
            
            # Test with function calling enabled
            response_with_tools = call_llm(
                prompt="You are Ash Ketchum. Look at the Pokemon screenshot and press one button. Use pokemon_controller function.",
                image_data=image_data,
                use_tools=True,
                max_tokens=500,
                provider=provider
            )
            
            print(f"   With tools - Provider: {response_with_tools.provider}")
            print(f"   With tools - Model: {response_with_tools.model}")
            print(f"   With tools - Error: {response_with_tools.error}")
            print(f"   With tools - Button presses: {response_with_tools.button_presses}")
            print(f"   With tools - Response length: {len(response_with_tools.text)} chars")
            
            # Test without function calling
            response_without_tools = call_llm(
                prompt="You are Ash Ketchum. Look at the Pokemon screenshot and tell me what button to press next.",
                image_data=image_data,
                use_tools=False,
                max_tokens=500,
                provider=provider
            )
            
            print(f"   Without tools - Button presses: {response_without_tools.button_presses}")
            print(f"   Without tools - Response length: {len(response_without_tools.text)} chars")
            
            # Analyze results
            tools_success = not response_with_tools.error and response_with_tools.button_presses
            no_tools_success = not response_without_tools.error and response_without_tools.button_presses
            
            print(f"\n📊 Results for {provider.upper()}:")
            print(f"   Function calling: {'✅' if tools_success else '❌'}")
            print(f"   Text parsing: {'✅' if no_tools_success else '❌'}")
            
            if response_with_tools.error:
                print(f"   Error details: {response_with_tools.error}")
            
            # Test provider-specific prompt style
            if provider == "mistral":
                has_character_style = "I am Ash" in prompt or "I'm Ash" in prompt
                print(f"   Character-first style: {'✅' if has_character_style else '❌'}")
            else:  # gemini
                has_doc_style = "**" in prompt or "##" in prompt
                print(f"   Documentation style: {'✅' if has_doc_style else '❌'}")
                
        except Exception as e:
            print(f"❌ LLM API Test Failed: {e}")
    
    # Test provider switching
    print(f"\n{'='*60}")
    print("🔄 Testing Dynamic Provider Switching")
    print(f"{'='*60}")
    
    prompt_manager = PromptManager()
    
    # Switch to Mistral
    print("Switching to Mistral...")
    success = prompt_manager.switch_to_provider('mistral', verbose=True)
    print(f"Switch successful: {'✅' if success else '❌'}")
    
    # Switch to Gemini
    print("\nSwitching to Gemini...")
    success = prompt_manager.switch_to_provider('gemini', verbose=True)
    print(f"Switch successful: {'✅' if success else '❌'}")
    
    print(f"\n{'='*80}")
    print("🏁 Provider Integration Test Complete")
    print("✅ Both providers should support:")
    print("   - Provider-specific prompt templates")
    print("   - Function calling for button extraction")
    print("   - Dynamic provider switching")
    print("   - Unified LLM API interface")

if __name__ == "__main__":
    test_provider_integration()