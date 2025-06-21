#!/usr/bin/env python3
"""
Test Mistral function calling fix for empty responses
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

def test_mistral_function_calling():
    """Test that Mistral function calling provides meaningful responses"""
    print("🧪 Testing Mistral Function Calling Fix")
    print("=" * 60)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Get screenshot for testing
    screenshot_files = list(Path(".").glob("**/skyemu_screenshot*.png"))
    if not screenshot_files:
        print("❌ No screenshot files found for testing")
        return
    
    try:
        from llm_api import call_llm
        from skyemu_controller import read_image_to_base64
        
        image_data = read_image_to_base64(str(screenshot_files[0]))
        
        print(f"📸 Using screenshot: {screenshot_files[0]}")
        print(f"🖼️ Image data length: {len(image_data)} chars")
        
        # Test Mistral with function calling
        print("\n🔧 Testing Mistral Function Calling:")
        
        response = call_llm(
            prompt="You are Ash Ketchum. Look at this Pokemon screenshot and use pokemon_controller to press one button.",
            image_data=image_data,
            use_tools=True,
            max_tokens=500,
            provider="mistral"
        )
        
        print(f"✅ Provider: {response.provider}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Error: {response.error}")
        print(f"✅ Response text: '{response.text}'")
        print(f"✅ Response length: {len(response.text)} chars")
        print(f"✅ Button presses: {response.button_presses}")
        print(f"✅ Response time: {response.response_time:.2f}s")
        print(f"✅ Tokens used: {response.tokens_used}")
        
        # Analyze results
        has_text = bool(response.text and len(response.text) > 0)
        has_buttons = bool(response.button_presses)
        no_error = not response.error
        
        print(f"\n📊 Analysis:")
        print(f"   Has meaningful text: {'✅' if has_text else '❌'}")
        print(f"   Has button presses: {'✅' if has_buttons else '❌'}")
        print(f"   No errors: {'✅' if no_error else '❌'}")
        
        if has_text and has_buttons and no_error:
            print(f"🎉 SUCCESS: Mistral function calling working correctly!")
        else:
            print(f"⚠️ ISSUES: Function calling needs more work")
            
        # Test without function calling for comparison
        print(f"\n🔧 Testing Mistral WITHOUT Function Calling:")
        
        response_no_tools = call_llm(
            prompt="You are Ash Ketchum. Look at this Pokemon screenshot and tell me what button to press. End with: Button: [button]",
            image_data=image_data,
            use_tools=False,
            max_tokens=500,
            provider="mistral"
        )
        
        print(f"✅ Response text length: {len(response_no_tools.text)} chars")
        print(f"✅ Button presses: {response_no_tools.button_presses}")
        print(f"✅ Error: {response_no_tools.error}")
        
        # Comparison
        print(f"\n📊 Comparison:")
        print(f"   Function calling response length: {len(response.text)} chars")
        print(f"   Text parsing response length: {len(response_no_tools.text)} chars")
        print(f"   Both extracted buttons: {'✅' if response.button_presses and response_no_tools.button_presses else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🏁 Mistral Function Calling Test Complete")

if __name__ == "__main__":
    test_mistral_function_calling()