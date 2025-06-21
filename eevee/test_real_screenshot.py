#!/usr/bin/env python3
"""
Test Pixtral with a real Pokemon screenshot
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
from llm_api import call_llm
from skyemu_controller import SkyEmuController
import base64

def test_with_real_screenshot():
    """Test Pixtral with a real Pokemon screenshot from SkyEmu"""
    print("🎮 Testing Pixtral with Real Pokemon Screenshot")
    print("=" * 60)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Try to connect to SkyEmu
    controller = SkyEmuController()
    
    if not controller.is_connected():
        print("❌ SkyEmu not connected. Testing with sample screenshot file...")
        
        # Look for existing screenshot files
        screenshot_files = list(Path(".").glob("**/screenshot*.png")) + list(Path(".").glob("**/turn_*.jpg")) + list(Path(".").glob("**/skyemu_screenshot*.png"))
        
        if screenshot_files:
            screenshot_file = screenshot_files[0]
            print(f"📸 Using screenshot file: {screenshot_file}")
            
            # Read and encode the file
            with open(screenshot_file, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        else:
            print("❌ No screenshot files found. Cannot test.")
            return
    else:
        print("✅ SkyEmu connected. Getting live screenshot...")
        image_data = controller.get_screenshot_base64()
        
        if not image_data:
            print("❌ Failed to get screenshot from SkyEmu")
            return
    
    print(f"📊 Screenshot data length: {len(image_data)} chars")
    
    # Test Pixtral with the real screenshot
    pokemon_prompt = """You are Ash Ketchum playing Pokemon on your Game Boy Advance.

Look at this Pokemon game screenshot carefully and tell me:

1. **What do you see on the screen?** (Be specific about UI elements, menus, Pokemon, etc.)
2. **What phase of the game is this?** (battle, exploration, menu, etc.)
3. **What should you do next?** (Give me specific button presses)

Respond with:
- OBSERVATION: What you see
- ANALYSIS: What this means for gameplay  
- ACTION: Button sequence like ['a'] or ['up', 'a']

Keep it concise and focused on the actual game screen."""
    
    print("\n🤖 Testing Pixtral Analysis...")
    print("-" * 40)
    
    response = call_llm(
        prompt=pokemon_prompt,
        image_data=image_data,
        model="pixtral-12b-2409",
        provider="mistral",
        max_tokens=300
    )
    
    print("📊 RESPONSE ANALYSIS:")
    print(f"   Error: {response.error}")
    print(f"   Provider: {response.provider}")
    print(f"   Model: {response.model}")
    print(f"   Response length: {len(response.text)} chars")
    print(f"   Button presses: {response.button_presses}")
    
    print("\n💭 PIXTRAL RESPONSE:")
    print("-" * 40)
    print(response.text)
    
    print("\n" + "=" * 60)
    print("🏁 Real Screenshot Test Complete")
    
    # Analysis
    print("\n📊 ANALYSIS:")
    
    # Better validation: check for proper game analysis structure
    has_observation = "observation:" in response.text.lower() or "screen shows" in response.text.lower()
    has_analysis = "analysis:" in response.text.lower() or "this is" in response.text.lower()
    has_action = "action:" in response.text.lower() or "press" in response.text.lower()
    has_code = "import " in response.text or "def " in response.text or "pygame" in response.text
    
    print(f"   Has proper observation: {'✅' if has_observation else '❌'}")
    print(f"   Has game analysis: {'✅' if has_analysis else '❌'}")
    print(f"   Has action recommendation: {'✅' if has_action else '❌'}")
    print(f"   Contains code (bad): {'❌' if has_code else '✅'}")
    
    is_proper_analysis = has_observation and has_analysis and has_action and not has_code
    
    if is_proper_analysis:
        print("   ✅ Pixtral is providing proper Pokemon game analysis")
        print("   ✅ Mistral-only configuration is functioning correctly")
    else:
        print("   ❌ Pixtral response format is incorrect - may be generating code instead of analysis")
        if has_code:
            print("   ⚠️  WARNING: Response contains programming code!")

if __name__ == "__main__":
    test_with_real_screenshot()