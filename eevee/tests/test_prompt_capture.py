#!/usr/bin/env python3
"""
Test script to capture and analyze the actual prompts being sent to Pixtral
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
from eevee_agent import EeveeAgent

def test_prompt_capture():
    """Test what prompts are actually being generated during gameplay"""
    print("🔍 Testing Prompt Generation for Character Consistency")
    print("=" * 70)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Create EeveeAgent with verbose logging
    agent = EeveeAgent(
        model="pixtral-12b-2409",
        verbose=True,  # This will show our new debug logging
        debug=True
    )
    
    # Test with a simple task to see what prompt gets generated
    test_task = "test new task mapping system"
    
    print(f"\n🎮 Testing with task: '{test_task}'")
    print("-" * 50)
    
    # Use a real screenshot for testing
    screenshot_files = list(Path(".").glob("**/skyemu_screenshot*.png"))
    if screenshot_files:
        from skyemu_controller import read_image_to_base64
        screenshot_path = screenshot_files[0]
        print(f"📸 Using screenshot: {screenshot_path}")
        
        image_data = read_image_to_base64(str(screenshot_path))
        
        print(f"\n🔍 TESTING PROMPT GENERATION:")
        print("=" * 50)
        
        # This should trigger our debug logging and show exactly what prompt is sent
        try:
            result = agent._call_llm_api(
                prompt="You are Ash Ketchum playing Pokemon. What do you see on the screen?",
                image_data=image_data,
                use_tools=False,
                max_tokens=500
            )
            
            print(f"\n📊 RESULT ANALYSIS:")
            print(f"   Response Length: {len(result['text'])} chars") 
            print(f"   Contains Code: {'✅' if any(keyword in result['text'] for keyword in ['import ', 'def ', 'pygame', 'python']) else '❌'}")
            print(f"   Character Format: {'✅' if 'OBSERVATION:' in result['text'] or 'observation:' in result['text'] else '❌'}")
            print(f"   Button Presses: {result['button_presses']}")
            print(f"   Error: {result.get('error', 'None')}")
            
            print(f"\n💭 ACTUAL RESPONSE:")
            print("-" * 50)
            print(result['text'][:800] + "..." if len(result['text']) > 800 else result['text'])
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
    else:
        print("❌ No screenshot files found for testing")
    
    print("\n" + "=" * 70)
    print("🏁 Prompt Capture Test Complete")

if __name__ == "__main__":
    test_prompt_capture()