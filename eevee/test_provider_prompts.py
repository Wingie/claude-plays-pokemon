#!/usr/bin/env python3
"""
Test provider-specific prompt loading in PromptManager
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

def test_provider_specific_loading():
    """Test that provider-specific prompts are loaded correctly"""
    print("🧪 Testing Provider-Specific Prompt Loading")
    print("=" * 60)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Test with Mistral provider
    print("\n🔵 Testing Mistral Provider")
    print("-" * 30)
    
    os.environ['LLM_PROVIDER'] = 'mistral'
    prompt_manager = PromptManager()
    
    # Check provider info
    info = prompt_manager.get_current_provider_info()
    print(f"Current provider: {info['current_provider']}")
    print(f"Provider-specific loaded: {info['provider_specific_loaded']}")
    print(f"Template count: {info['template_count']}")
    
    # Test battle prompt
    if 'battle_analysis' in prompt_manager.base_prompts:
        battle_prompt = prompt_manager.base_prompts['battle_analysis']
        print(f"\n🎮 Battle Analysis Template:")
        print(f"  Name: {battle_prompt.get('name', 'Unknown')}")
        print(f"  Provider: {battle_prompt.get('provider', 'None specified')}")
        
        # Check if it's character-first (Mistral style)
        template_text = battle_prompt.get('template', '')
        is_character_first = 'I am Ash' in template_text or 'I\'m Ash' in template_text
        print(f"  Character-first style: {'✅' if is_character_first else '❌'}")
        print(f"  Template length: {len(template_text)} chars")
    
    # Test with Gemini provider
    print("\n🟡 Testing Gemini Provider")
    print("-" * 30)
    
    success = prompt_manager.switch_to_provider('gemini', verbose=True)
    print(f"Switch successful: {'✅' if success else '❌'}")
    
    if success:
        info = prompt_manager.get_current_provider_info()
        print(f"Current provider: {info['current_provider']}")
        print(f"Provider-specific loaded: {info['provider_specific_loaded']}")
        print(f"Template count: {info['template_count']}")
        
        # Test battle prompt style
        if 'battle_analysis' in prompt_manager.base_prompts:
            battle_prompt = prompt_manager.base_prompts['battle_analysis']
            print(f"\n🎮 Battle Analysis Template:")
            print(f"  Name: {battle_prompt.get('name', 'Unknown')}")
            print(f"  Provider: {battle_prompt.get('provider', 'None specified')}")
            
            # Check if it's documentation style (Gemini style)
            template_text = battle_prompt.get('template', '')
            is_documentation_style = '**' in template_text or '##' in template_text
            print(f"  Documentation style: {'✅' if is_documentation_style else '❌'}")
            print(f"  Template length: {len(template_text)} chars")
    
    # Test provider switching
    print("\n🔄 Testing Provider Switching")
    print("-" * 30)
    
    print("Switching back to Mistral...")
    success = prompt_manager.switch_to_provider('mistral', verbose=True)
    print(f"Switch successful: {'✅' if success else '❌'}")
    
    # Test invalid provider
    print("\nTesting invalid provider...")
    success = prompt_manager.switch_to_provider('invalid', verbose=True)
    print(f"Invalid switch rejected: {'✅' if not success else '❌'}")
    
    # Template comparison
    print("\n📊 Template Style Comparison")
    print("-" * 30)
    
    # Switch to Mistral and get battle template
    prompt_manager.switch_to_provider('mistral', verbose=False)
    mistral_info = prompt_manager.get_current_provider_info()
    mistral_battle = prompt_manager.base_prompts.get('battle_analysis', {}).get('template', '')
    
    # Switch to Gemini and get battle template  
    prompt_manager.switch_to_provider('gemini', verbose=False)
    gemini_info = prompt_manager.get_current_provider_info()
    gemini_battle = prompt_manager.base_prompts.get('battle_analysis', {}).get('template', '')
    
    print(f"Mistral template length: {len(mistral_battle)} chars")
    print(f"Gemini template length: {len(gemini_battle)} chars")
    print(f"Templates are different: {'✅' if mistral_battle != gemini_battle else '❌'}")
    
    # Show first 100 chars of each
    if mistral_battle and gemini_battle:
        print(f"\nMistral preview: {mistral_battle[:100]}...")
        print(f"Gemini preview: {gemini_battle[:100]}...")
    
    print("\n" + "=" * 60)
    print("🏁 Provider-Specific Prompt Loading Test Complete")

if __name__ == "__main__":
    test_provider_specific_loading()