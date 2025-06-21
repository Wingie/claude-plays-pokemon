#!/usr/bin/env python3
"""
Test API debugging to understand the empty response issue
"""

import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
import base64
from pathlib import Path

from eevee_agent import EeveeAgent
import time

def test_api_call():
    """Test a simple API call to see what's happening"""
    
    # Initialize agent
    agent = EeveeAgent(verbose=True)
    
    # Very simple test prompt
    prompt = """Look at this Pokemon game screenshot. What do you see? Then use pokemon_controller to press one button like 'right' or 'a'."""
    
    print("=" * 60)
    print("TESTING API CALL")
    print("=" * 60)
    
    # Take a screenshot first using the same method as the main code
    print("Testing capture_screen() method...")
    screenshot_path = agent.controller.capture_screen()
    print(f"Screenshot path returned: '{screenshot_path}'")
    print(f"Path exists: {bool(screenshot_path and Path(screenshot_path).exists())}")
    
    if screenshot_path and Path(screenshot_path).exists():
        print(f"File size: {Path(screenshot_path).stat().st_size} bytes")
        # Try to read and encode like the main code does
        try:
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            print(f"Base64 length: {len(image_data)}")
            print(f"Base64 starts with: '{image_data[:50]}...'")
        except Exception as e:
            print(f"Error reading file: {e}")
    
    # Also test the direct base64 method
    print("\nTesting get_screenshot_base64() method...")
    try:
        direct_base64 = agent.controller.get_screenshot_base64()
        if direct_base64:
            print(f"Direct base64 length: {len(direct_base64)}")
            print(f"Direct base64 starts with: '{direct_base64[:50]}...'")
        else:
            print("Direct base64 method returned None")
    except Exception as e:
        print(f"Error with direct base64: {e}")
    
    # Use the working method for the API test
    screenshot_data = direct_base64 if direct_base64 else None
    
    # Test with improved prompt that asks for button commands in text
    button_prompt = """Look at this Pokemon game screenshot. Analyze what you see and then tell me what button to press next.

Use this format: "I can see [description]. I should press [button_name] to [action]."

Valid buttons: up, down, left, right, a, b, start, select"""
    
    # Call API without tools first to test text parsing functionality
    print("\nTesting API without tools (should parse buttons from text)...")
    result_no_tools = agent._call_gemini_api(
        prompt=button_prompt,
        image_data=screenshot_data,
        use_tools=False,
        max_tokens=1000
    )
    
    print("NO TOOLS RESULT (with text parsing):")
    print(f"Error: {result_no_tools.get('error')}")
    print(f"Text length: {len(result_no_tools.get('text', ''))}")
    print(f"Button presses extracted: {result_no_tools.get('button_presses', [])}")
    print(f"Text preview: '{result_no_tools.get('text', '')[:200]}...'")
    
    # Now try with tools (will likely fail but let's confirm)
    print("\nTesting API with tools...")
    result = agent._call_gemini_api(
        prompt=button_prompt,
        image_data=screenshot_data,
        use_tools=True,
        max_tokens=1000
    )
    
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Error: {result.get('error')}")
    print(f"Text length: {len(result.get('text', ''))}")
    print(f"Text content: '{result.get('text', '')}'")
    print(f"Button presses: {result.get('button_presses', [])}")
    print("=" * 60)

if __name__ == "__main__":
    test_api_call()