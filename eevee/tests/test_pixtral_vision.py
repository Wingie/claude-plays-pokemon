#!/usr/bin/env python3
"""
Comprehensive Pixtral Vision Test for Pokemon AI System
Tests base64 image encoding, scene detection, and template selection accuracy
"""

import os
import sys
import json
import base64
import time
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

def capture_and_validate_screenshot():
    """Capture screenshot and validate base64 encoding"""
    print("📸 Capturing screenshot from SkyEmu...")
    
    controller = SkyEmuController()
    
    try:
        # Capture raw screenshot data
        screenshot_data = controller.capture_screenshot()
        
        if not screenshot_data:
            print("❌ Failed to capture screenshot data")
            return None, None
            
        print(f"✅ Screenshot captured: {len(screenshot_data)} bytes base64")
        
        # Validate base64 encoding
        try:
            # Decode and re-encode to verify validity
            decoded_bytes = base64.b64decode(screenshot_data)
            re_encoded = base64.b64encode(decoded_bytes).decode('utf-8')
            
            if re_encoded == screenshot_data:
                print("✅ Base64 encoding is valid")
            else:
                print("⚠️ Base64 encoding mismatch detected")
                
        except Exception as e:
            print(f"❌ Base64 validation failed: {e}")
            return None, None
            
        # Save screenshot for visual inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = eevee_root / "analysis" / f"pixtral_test_{timestamp}.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))
            print(f"💾 Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"⚠️ Failed to save screenshot: {e}")
            
        return screenshot_data, str(screenshot_path)
        
    except Exception as e:
        print(f"❌ Screenshot capture error: {e}")
        return None, None

def test_basic_scene_detection(screenshot_b64):
    """Test basic Pixtral scene detection capabilities"""
    print("\n🧪 Test 1: Basic Scene Detection")
    print("-" * 50)
    
    scene_prompt = """Analyze this Pokemon Game Boy Advance screenshot. 

What type of game screen is this? Choose ONE:
1. BATTLE - Pokemon battle with HP bars and move selection
2. OVERWORLD - Character walking on map/terrain  
3. MENU - Game menus, inventory, or Pokemon party
4. INDOOR - Inside buildings or Pokemon Centers

Respond with just the category name: BATTLE, OVERWORLD, MENU, or INDOOR"""

    try:
        response = call_llm(
            prompt=scene_prompt,
            image_data=screenshot_b64,
            model="pixtral-12b-2409",
            provider="mistral",
            max_tokens=100
        )
        
        result = {
            "test": "basic_scene_detection",
            "response": response.text.strip(),
            "error": response.error,
            "provider": response.provider,
            "model": response.model,
            "success": bool(response.text and not response.error)
        }
        
        print(f"Response: '{response.text.strip()}'")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Error: {response.error}")
        print(f"Success: {'✅' if result['success'] else '❌'}")
        
        return result
        
    except Exception as e:
        print(f"❌ Basic scene detection failed: {e}")
        return {"test": "basic_scene_detection", "error": str(e), "success": False}

def test_structured_scene_analysis(screenshot_b64):
    """Test structured JSON scene analysis"""
    print("\n🧪 Test 2: Structured Scene Analysis")
    print("-" * 50)
    
    structured_prompt = """Analyze this Pokemon Game Boy Advance screenshot and provide a structured analysis.

Respond with EXACTLY this JSON format:
{
  "scene_type": "battle|overworld|menu|indoor",
  "confidence": 0.8,
  "visual_elements": ["element1", "element2"],
  "recommended_template": "battle_analysis|exploration_strategy|stuck_recovery",
  "reasoning": "brief explanation of what you see"
}

Base template selection on:
- battle_analysis: If you see HP bars, Pokemon sprites, move menus
- exploration_strategy: If you see character on map, grass, terrain
- stuck_recovery: If scene looks like a stuck/error state

Respond ONLY with valid JSON."""

    try:
        response = call_llm(
            prompt=structured_prompt,
            image_data=screenshot_b64,
            model="pixtral-12b-2409",
            provider="mistral",
            max_tokens=300
        )
        
        result = {
            "test": "structured_scene_analysis",
            "response": response.text.strip(),
            "error": response.error,
            "provider": response.provider,
            "model": response.model,
            "success": bool(response.text and not response.error)
        }
        
        # Try to parse JSON
        parsed_json = None
        if response.text:
            try:
                parsed_json = json.loads(response.text.strip())
                result["parsed_json"] = parsed_json
                result["json_valid"] = True
                print("✅ Valid JSON response!")
                print(f"Scene Type: {parsed_json.get('scene_type', 'unknown')}")
                print(f"Template: {parsed_json.get('recommended_template', 'unknown')}")
                print(f"Confidence: {parsed_json.get('confidence', 0)}")
                print(f"Elements: {parsed_json.get('visual_elements', [])}")
            except json.JSONDecodeError as e:
                result["json_valid"] = False
                result["json_error"] = str(e)
                print(f"❌ Invalid JSON: {e}")
                print(f"Raw response: {response.text}")
        
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Error: {response.error}")
        
        return result
        
    except Exception as e:
        print(f"❌ Structured scene analysis failed: {e}")
        return {"test": "structured_scene_analysis", "error": str(e), "success": False}

def test_template_selection_accuracy(screenshot_b64):
    """Test the actual template selection logic used in the system"""
    print("\n🧪 Test 3: Current Template Selection Logic")
    print("-" * 50)
    
    # This mimics the actual prompt used in prompt_manager.py
    selection_prompt = """
# POKEMON AI TEMPLATE & PLAYBOOK SELECTION

## Visual Analysis Instructions
**PRIMARY FOCUS**: Analyze what you can SEE on the game screen to choose the correct template.

**What to Look For**:
- **Battle Screen**: HP bars, Pokemon sprites, move selection menu, battle text
- **Overworld Screen**: Character sprite, map/terrain, NPCs, buildings, grass patches  
- **Menu Screen**: Lists, options, inventory, Pokemon party view

## Available Templates (Choose Based on What You See)
- battle_analysis: Pokemon battle decisions, move selection, type effectiveness
- exploration_strategy: Overworld navigation, area exploration, pathfinding
- stuck_recovery: Breaking out of loops, stuck pattern recovery

## Available Playbooks (Choose Based on Screen Context)
- battle: Battle strategies, type charts, move effectiveness, gym tactics
- navigation: Movement patterns, area navigation, stuck recovery techniques
- services: Pokemon Centers, shops, NPCs, healing locations

## Selection Criteria
1. **IF you see battle elements** (HP bars, Pokemon, moves) → Use `battle_analysis` + `battle`
2. **IF you see overworld/map** (character walking, terrain) → Use `exploration_strategy` + `navigation`  
3. **IF menu/inventory visible** → Use appropriate analysis template

**CRITICAL**: Base your decision on VISUAL ELEMENTS you can see, not text keywords.

Respond ONLY with this format:
TEMPLATE: template_name
PLAYBOOK: playbook_name
REASONING: what visual elements you see that led to this choice
"""

    try:
        response = call_llm(
            prompt=selection_prompt,
            image_data=screenshot_b64,
            model="pixtral-12b-2409",
            provider="mistral", 
            max_tokens=500
        )
        
        result = {
            "test": "template_selection_accuracy",
            "response": response.text.strip(),
            "error": response.error,
            "provider": response.provider,
            "model": response.model,
            "success": bool(response.text and not response.error)
        }
        
        # Parse template selection
        if response.text:
            lines = response.text.split('\n')
            template = None
            playbook = None
            reasoning = None
            
            for line in lines:
                if line.strip().startswith('TEMPLATE:'):
                    template = line.replace('TEMPLATE:', '').strip()
                elif line.strip().startswith('PLAYBOOK:'):
                    playbook = line.replace('PLAYBOOK:', '').strip()
                elif line.strip().startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
            
            result["extracted_template"] = template
            result["extracted_playbook"] = playbook
            result["extracted_reasoning"] = reasoning
            
            print(f"Template: {template}")
            print(f"Playbook: {playbook}")
            print(f"Reasoning: {reasoning}")
        
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Error: {response.error}")
        
        return result
        
    except Exception as e:
        print(f"❌ Template selection test failed: {e}")
        return {"test": "template_selection_accuracy", "error": str(e), "success": False}

def test_image_data_transmission(screenshot_b64):
    """Test if image data is being transmitted correctly to Mistral API"""
    print("\n🧪 Test 4: Image Data Transmission Validation")
    print("-" * 50)
    
    simple_prompt = """You are receiving a base64-encoded image. 

Can you see an image? If yes, describe what you see in 1-2 sentences.
If no image is visible, say "NO IMAGE RECEIVED"."""

    try:
        response = call_llm(
            prompt=simple_prompt,
            image_data=screenshot_b64,
            model="pixtral-12b-2409",
            provider="mistral",
            max_tokens=150
        )
        
        result = {
            "test": "image_data_transmission",
            "response": response.text.strip(),
            "error": response.error,
            "provider": response.provider,
            "model": response.model,
            "success": bool(response.text and not response.error),
            "image_received": "NO IMAGE RECEIVED" not in response.text.upper() if response.text else False
        }
        
        print(f"Response: {response.text}")
        print(f"Image Received: {'✅' if result['image_received'] else '❌'}")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Error: {response.error}")
        
        return result
        
    except Exception as e:
        print(f"❌ Image transmission test failed: {e}")
        return {"test": "image_data_transmission", "error": str(e), "success": False}

def save_test_results(screenshot_path, all_results):
    """Save comprehensive test results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = eevee_root / "analysis" / f"pixtral_vision_test_{timestamp}.json"
    
    test_summary = {
        "timestamp": timestamp,
        "screenshot_path": screenshot_path,
        "test_results": all_results,
        "summary": {
            "total_tests": len(all_results),
            "successful_tests": sum(1 for r in all_results if r.get("success", False)),
            "failed_tests": sum(1 for r in all_results if not r.get("success", False)),
            "image_transmission_working": any(r.get("image_received", False) for r in all_results if "image_received" in r)
        }
    }
    
    try:
        with open(results_path, "w") as f:
            json.dump(test_summary, f, indent=2)
        print(f"📄 Test results saved: {results_path}")
        return str(results_path)
    except Exception as e:
        print(f"⚠️ Failed to save test results: {e}")
        return None

def main():
    """Main test execution"""
    print("🔬 Pixtral Vision Validation Test Suite")
    print("=" * 60)
    
    # Load environment
    env_file = eevee_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Environment loaded")
    else:
        print("⚠️ No .env file found")
    
    # Step 1: Capture and validate screenshot
    screenshot_b64, screenshot_path = capture_and_validate_screenshot()
    
    if not screenshot_b64:
        print("❌ Cannot proceed without valid screenshot data")
        print("Make sure SkyEmu is running on port 8080 with a Pokemon game loaded")
        return
    
    # Step 2: Run all tests
    all_results = []
    
    tests = [
        test_basic_scene_detection,
        test_structured_scene_analysis, 
        test_template_selection_accuracy,
        test_image_data_transmission
    ]
    
    for test_func in tests:
        try:
            result = test_func(screenshot_b64)
            all_results.append(result)
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            all_results.append({
                "test": test_func.__name__,
                "error": str(e),
                "success": False
            })
    
    # Step 3: Save results and summarize
    results_path = save_test_results(screenshot_path, all_results)
    
    print("\n" + "=" * 60)
    print("🏁 Pixtral Vision Test Suite Complete")
    print("=" * 60)
    
    # Print summary
    successful = sum(1 for r in all_results if r.get("success", False))
    total = len(all_results)
    
    print(f"📊 Results: {successful}/{total} tests successful")
    
    for result in all_results:
        test_name = result.get("test", "unknown")
        success = "✅" if result.get("success", False) else "❌"
        print(f"  {success} {test_name}")
    
    # Specific diagnostics
    print("\n🔍 Diagnostics:")
    
    # Check image transmission
    image_tests = [r for r in all_results if "image_received" in r]
    if image_tests:
        image_working = any(r.get("image_received", False) for r in image_tests)
        print(f"  📸 Image transmission: {'✅ Working' if image_working else '❌ Failed'}")
    
    # Check template accuracy
    template_tests = [r for r in all_results if "extracted_template" in r]
    if template_tests:
        for t in template_tests:
            template = t.get("extracted_template", "unknown")
            print(f"  🎯 Template selected: {template}")
    
    print(f"\n📁 Files saved:")
    if screenshot_path:
        print(f"  📸 Screenshot: {screenshot_path}")
    if results_path:
        print(f"  📄 Results: {results_path}")
    
    print("\n💡 Next steps:")
    print("1. Review the screenshot to confirm current game state")
    print("2. Check if Pixtral correctly identified the scene type")
    print("3. Verify template selection matches the actual game context")
    print("4. If image transmission fails, check base64 encoding")

if __name__ == "__main__":
    main()