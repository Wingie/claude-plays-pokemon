#!/usr/bin/env python3
"""
Test fixed prompts with real gameplay to verify no code generation
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
from llm_api import call_llm
from skyemu_controller import read_image_to_base64

def test_fixed_prompts():
    """Test that fixed prompts no longer generate code"""
    print("🎯 Testing Fixed Prompts for Character Consistency")
    print("=" * 70)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Get a real screenshot
    screenshot_files = list(Path(".").glob("**/skyemu_screenshot*.png"))
    if not screenshot_files:
        print("❌ No screenshot files found")
        return
    
    image_data = read_image_to_base64(str(screenshot_files[0]))
    print(f"📸 Using screenshot: {screenshot_files[0]}")
    
    # Create PromptManager
    prompt_manager = PromptManager()
    
    # Test battle context (most likely to generate code)
    print(f"\n🎮 Testing Battle Context:")
    print("-" * 50)
    
    try:
        prompt = prompt_manager.get_ai_directed_prompt(
            context_type="auto_select",
            task="win this pokemon battle",
            recent_actions=["a", "down", "a"],
            memory_context="Pokemon battle with HP bars visible, move selection menu showing",
            verbose=False
        )
        
        print(f"📝 Prompt Generated: {len(prompt)} chars")
        
        # Send to Pixtral with the real screenshot
        response = call_llm(
            prompt=prompt,
            image_data=image_data,
            model="pixtral-12b-2409",
            provider="mistral",
            max_tokens=1000
        )
        
        # Analyze response
        response_text = response.text
        
        # Check for code generation
        has_code = any(keyword in response_text for keyword in [
            'import ', 'def ', 'class ', 'pygame', 'python', '# Initialize', 'def main'
        ])
        
        # Check for character consistency
        has_character = any(keyword in response_text.lower() for keyword in [
            'i see', 'i can see', 'my pikachu', 'observation:', 'analysis:', 'action:'
        ])
        
        # Check for third person references (bad)
        has_third_person = any(phrase in response_text.lower() for phrase in [
            'ash ketchum is', 'the player', 'the user', 'the trainer'
        ])
        
        print(f"\n📊 ANALYSIS:")
        print(f"   Contains Code: {'❌ YES' if has_code else '✅ NO'}")
        print(f"   Character Consistency: {'✅ YES' if has_character else '❌ NO'}")
        print(f"   Third Person (bad): {'❌ YES' if has_third_person else '✅ NO'}")
        print(f"   Response Length: {len(response_text)} chars")
        print(f"   Button Presses: {response.button_presses}")
        
        print(f"\n💭 PIXTRAL RESPONSE:")
        print("-" * 40)
        print(response_text[:600] + "..." if len(response_text) > 600 else response_text)
        
        # Final assessment
        if not has_code and has_character and not has_third_person:
            print(f"\n🎉 SUCCESS: Fixed prompts are working correctly!")
        else:
            print(f"\n⚠️  ISSUES: Prompts may need further refinement")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    print("\n" + "=" * 70)
    print("🏁 Fixed Prompts Test Complete")

if __name__ == "__main__":
    test_fixed_prompts()