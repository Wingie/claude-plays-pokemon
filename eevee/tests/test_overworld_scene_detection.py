#!/usr/bin/env python3
"""
Test Pixtral scene detection for Pokemon overworld state
Captures current game screenshot and tests scene classification
"""

import os
import sys
import json
import base64
from pathlib import Path

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from datetime import datetime

project_root = eevee_root.parent
sys.path.append(str(eevee_root))

from dotenv import load_dotenv
from llm_api import call_llm
from skyemu_controller import SkyEmuController

def capture_screenshot():
    """Capture current game screenshot"""
    controller = SkyEmuController()
    
    try:
        screenshot_data = controller.capture_screenshot()
        if screenshot_data:
            print("✅ Screenshot captured successfully")
            return screenshot_data
        else:
            print("❌ Failed to capture screenshot")
            return None
    except Exception as e:
        print(f"❌ Screenshot capture error: {e}")
        return None

def test_scene_detection_prompt(screenshot_b64):
    """Test Pixtral with Pokemon scene detection prompt"""
    
    scene_detection_prompt = """You are a Pokemon AI agent analyzing a Game Boy Advance screenshot. 

Identify the current game mode and provide possible actions in this exact JSON format:

{
  "mode": "battle|navigation|menu|party|bag|save",
  "observation": "Brief description of what you see",
  "possible_actions": [
    {
      "button_sequence": ["button1", "button2"],
      "description": "what this action does"
    }
  ]
}

For overworld/navigation scenes, typical actions are:
- Move in directions: ["up"], ["down"], ["left"], ["right"] 
- Interact with objects: ["a"]
- Open menu: ["start"]
- Check party: ["x"]

Analyze the screenshot and respond ONLY with valid JSON."""

    response = call_llm(
        prompt=scene_detection_prompt,
        image_data=screenshot_b64,
        model="pixtral-12b-2409",
        provider="mistral",
        max_tokens=300
    )
    
    return response

def test_simple_overworld_prompt(screenshot_b64):
    """Test simpler overworld-specific prompt"""
    
    simple_prompt = """Look at this Pokemon Game Boy Advance screenshot. You are in the overworld.

What should the player do next? Choose ONE action:
1. Move (up/down/left/right)
2. Interact with something (a button)
3. Open menu (start button)

Respond with just the button name: up, down, left, right, a, or start"""

    response = call_llm(
        prompt=simple_prompt,
        image_data=screenshot_b64,
        model="pixtral-12b-2409", 
        provider="mistral",
        max_tokens=50
    )
    
    return response

def save_test_results(screenshot_b64, responses):
    """Save test results for analysis"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save screenshot
    screenshot_path = eevee_root / f"analysis/overworld_test_{timestamp}.png"
    screenshot_path.parent.mkdir(exist_ok=True)
    
    try:
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot_b64))
        print(f"📸 Screenshot saved: {screenshot_path}")
    except Exception as e:
        print(f"⚠️ Failed to save screenshot: {e}")
    
    # Save responses
    results_path = eevee_root / f"analysis/overworld_test_{timestamp}.json"
    results = {
        "timestamp": timestamp,
        "screenshot_path": str(screenshot_path),
        "tests": responses
    }
    
    try:
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved: {results_path}")
    except Exception as e:
        print(f"⚠️ Failed to save results: {e}")

def main():
    """Main test function"""
    print("🎮 Pokemon Overworld Scene Detection Test")
    print("=" * 50)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Step 1: Capture current screenshot
    print("📸 Capturing current game screenshot...")
    screenshot_b64 = capture_screenshot()
    
    if not screenshot_b64:
        print("❌ Cannot proceed without screenshot. Make sure SkyEmu is running on port 8080.")
        return
    
    responses = {}
    
    # Step 2: Test structured scene detection
    print("\n🧪 Test 1: Structured Scene Detection")
    print("-" * 40)
    
    try:
        response = test_scene_detection_prompt(screenshot_b64)
        print(f"Response: {response.text}")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Error: {response.error}")
        
        # Try to parse JSON
        try:
            parsed = json.loads(response.text)
            print(f"✅ Valid JSON detected!")
            print(f"Mode: {parsed.get('mode', 'unknown')}")
            print(f"Actions: {len(parsed.get('possible_actions', []))}")
        except json.JSONDecodeError:
            print("⚠️ Response is not valid JSON")
        
        responses["structured_scene_detection"] = {
            "prompt": "structured scene detection with JSON output",
            "response": response.text,
            "error": response.error,
            "provider": response.provider,
            "model": response.model
        }
        
    except Exception as e:
        print(f"❌ Structured test failed: {e}")
        responses["structured_scene_detection"] = {"error": str(e)}
    
    # Step 3: Test simple overworld prompt
    print("\n🧪 Test 2: Simple Overworld Action")
    print("-" * 40)
    
    try:
        response = test_simple_overworld_prompt(screenshot_b64)
        print(f"Response: {response.text}")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Error: {response.error}")
        
        responses["simple_overworld"] = {
            "prompt": "simple overworld button recommendation",
            "response": response.text,
            "error": response.error,
            "provider": response.provider,
            "model": response.model
        }
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        responses["simple_overworld"] = {"error": str(e)}
    
    # Step 4: Save results
    print("\n💾 Saving test results...")
    save_test_results(screenshot_b64, responses)
    
    print("\n" + "=" * 50)
    print("🏁 Overworld Scene Detection Test Complete")
    print("\nNext steps:")
    print("1. Check the saved screenshot in analysis/ folder")
    print("2. Review JSON responses for accuracy")
    print("3. Compare structured vs simple prompt effectiveness")

if __name__ == "__main__":
    main()