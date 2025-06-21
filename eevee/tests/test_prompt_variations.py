#!/usr/bin/env python3
"""
Pixtral Vision Verification Script
First verifies if Pixtral can actually see the screen, then tests simple scene detection
"""

import sys
import base64
import json
import time
from pathlib import Path

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from typing import Dict, List, Optional

try:
    # Try to import SkyEmu controller first, fallback to regular controller
    try:
        from skyemu_controller import SkyEmuController, read_image_to_base64
        CONTROLLER_TYPE = "skyemu"
        print("🚀 Using SkyEmu controller")
    except ImportError:
        from pokemon_controller import PokemonController, read_image_to_base64
        CONTROLLER_TYPE = "pokemon"
        print("🔄 Using standard Pokemon controller")
    
    from dotenv import load_dotenv
    
    # Import centralized LLM API
    from llm_api import call_llm, get_llm_manager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

class PixtralVisionTester:
    """Test if Pixtral can actually see and analyze screenshots"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.test_results: List[Dict] = []
        
    def capture_screenshot(self) -> Optional[str]:
        """Capture screenshot and validate encoding"""
        try:
            screenshot_data = self.controller.get_screenshot_base64()
            if not screenshot_data:
                print("❌ Failed to capture screenshot")
                return None
                
            print(f"✅ Screenshot captured: {len(screenshot_data)} characters")
            
            # Validate base64 encoding
            try:
                decoded_bytes = base64.b64decode(screenshot_data)
                if decoded_bytes.startswith(b'\x89PNG'):
                    print("📸 Image format: PNG detected")
                elif decoded_bytes.startswith(b'\xff\xd8\xff'):
                    print("📸 Image format: JPEG detected")
                else:
                    print("⚠️ Unknown image format")
                    
                return screenshot_data
            except Exception as e:
                print(f"❌ Base64 validation error: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            return None
    
    def call_pixtral(self, prompt: str, image_data: str) -> Dict:
        """Make a single API call to Pixtral and return full results"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_data,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=300
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "success": True,
                "response": response_text,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def test_basic_vision(self, image_data: str) -> Dict:
        """Test 1: Can Pixtral see and describe the image at all?"""
        print("\n🔍 TEST 1: Basic Vision Verification")
        print("=" * 50)
        
        prompt = "Describe what you see in this image. Be specific about visual elements, colors, shapes, and any text or interface elements."
        
        result = self.call_pixtral(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Pixtral Response:")
            print(f"   {result['response']}")
            
            # Check if response seems to describe actual visual content
            response_lower = result['response'].lower()
            visual_indicators = ['color', 'text', 'button', 'menu', 'screen', 'image', 'see', 'visible', 'display']
            has_visual_content = any(indicator in response_lower for indicator in visual_indicators)
            
            result["contains_visual_description"] = has_visual_content
            if has_visual_content:
                print("   ✅ Response contains visual descriptions")
            else:
                print("   ⚠️ Response seems generic, may not be seeing image")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def test_describe_screen(self, image_data: str) -> Dict:
        """Test 2: What does Pixtral see on the game screen?"""
        print("\n🎮 TEST 2: Game Screen Description")
        print("=" * 50)
        
        prompt = "What do you see on this game screen? Describe any user interface elements, characters, terrain, or game elements visible."
        
        result = self.call_pixtral(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Pixtral Response:")
            print(f"   {result['response']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def test_identify_ui_elements(self, image_data: str) -> Dict:
        """Test 3: Can Pixtral identify specific UI elements?"""
        print("\n🔧 TEST 3: UI Element Identification")
        print("=" * 50)
        
        prompt = "Look at this game screenshot. List any UI elements you can see such as: health bars, menus, buttons, text boxes, or interface elements. If you don't see any, say 'No UI elements visible'."
        
        result = self.call_pixtral(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Pixtral Response:")
            print(f"   {result['response']}")
            
            # Check for specific UI mentions
            response_lower = result['response'].lower()
            ui_mentions = ['hp', 'health', 'bar', 'menu', 'button', 'fight', 'bag', 'pokemon', 'run']
            mentioned_ui = [ui for ui in ui_mentions if ui in response_lower]
            
            result["mentioned_ui_elements"] = mentioned_ui
            if mentioned_ui:
                print(f"   📋 UI Elements Mentioned: {', '.join(mentioned_ui)}")
            else:
                print("   📋 No specific UI elements mentioned")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def test_hp_bar_detection(self, image_data: str) -> Dict:
        """Test 4: Simple HP bar detection"""
        print("\n❤️ TEST 4: HP Bar Detection")
        print("=" * 50)
        
        prompt = "Do you see any health bars or HP bars in this image? Answer with YES if you see health/HP bars, or NO if you don't see any."
        
        result = self.call_pixtral(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Pixtral Response:")
            print(f"   {result['response']}")
            
            response_upper = result['response'].upper()
            if 'YES' in response_upper and 'NO' not in response_upper:
                result["hp_bars_detected"] = True
                print("   ✅ Claims to see HP bars")
            elif 'NO' in response_upper and 'YES' not in response_upper:
                result["hp_bars_detected"] = False
                print("   ❌ Claims no HP bars visible")
            else:
                result["hp_bars_detected"] = None
                print("   ⚠️ Unclear response")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def test_character_detection(self, image_data: str) -> Dict:
        """Test 5: Character/sprite detection"""
        print("\n👤 TEST 5: Character Detection")
        print("=" * 50)
        
        prompt = "Do you see a character or player sprite in this image? Answer YES if you see a character/player, or NO if you don't."
        
        result = self.call_pixtral(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Pixtral Response:")
            print(f"   {result['response']}")
            
            response_upper = result['response'].upper()
            if 'YES' in response_upper and 'NO' not in response_upper:
                result["character_detected"] = True
                print("   ✅ Claims to see character")
            elif 'NO' in response_upper and 'YES' not in response_upper:
                result["character_detected"] = False
                print("   ❌ Claims no character visible")
            else:
                result["character_detected"] = None
                print("   ⚠️ Unclear response")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def test_simple_battle_check(self, image_data: str) -> Dict:
        """Test 6: Simple battle scene detection"""
        print("\n⚔️ TEST 6: Simple Battle Detection")
        print("=" * 50)
        
        prompt = "Is this a Pokemon battle scene? Answer YES if this shows a Pokemon battle, or NO if it doesn't."
        
        result = self.call_pixtral(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Pixtral Response:")
            print(f"   {result['response']}")
            
            response_upper = result['response'].upper()
            if 'YES' in response_upper and 'NO' not in response_upper:
                result["battle_detected"] = True
                print("   ⚔️ Claims this is a battle scene")
            elif 'NO' in response_upper and 'YES' not in response_upper:
                result["battle_detected"] = False
                print("   🌍 Claims this is not a battle scene")
            else:
                result["battle_detected"] = None
                print("   ⚠️ Unclear response")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def run_all_tests(self) -> None:
        """Run all vision verification tests"""
        print("🚀 Pixtral Vision Verification Test Suite")
        print("=" * 60)
        print("Testing if Pixtral can actually see and analyze the game screen")
        print()
        
        # Check connection
        if not self.controller.is_connected():
            print("❌ Cannot connect to SkyEmu. Please ensure SkyEmu is running on port 8080.")
            return
        
        print("✅ SkyEmu connection verified")
        
        # Capture screenshot
        image_data = self.capture_screenshot()
        if not image_data:
            print("❌ Failed to capture screenshot")
            return
        
        # Run all tests in sequence
        test_methods = [
            ("Basic Vision", self.test_basic_vision),
            ("Screen Description", self.test_describe_screen),
            ("UI Elements", self.test_identify_ui_elements),
            ("HP Bar Detection", self.test_hp_bar_detection),
            ("Character Detection", self.test_character_detection),
            ("Battle Detection", self.test_simple_battle_check)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method(image_data)
                result["test_name"] = test_name
                self.test_results.append(result)
                
                # Brief pause between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Test '{test_name}' failed: {e}")
                self.test_results.append({
                    "test_name": test_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Analyze results
        self.analyze_vision_capability()
    
    def analyze_vision_capability(self) -> None:
        """Analyze if Pixtral is actually seeing the screen"""
        print("\n" + "=" * 80)
        print("📊 VISION CAPABILITY ANALYSIS")
        print("=" * 80)
        
        successful_tests = [r for r in self.test_results if r.get("success", False)]
        failed_tests = [r for r in self.test_results if not r.get("success", False)]
        
        print(f"✅ Successful API calls: {len(successful_tests)}/{len(self.test_results)}")
        if failed_tests:
            print(f"❌ Failed API calls: {len(failed_tests)}")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test.get('error', 'Unknown error')}")
        
        if not successful_tests:
            print("❌ No successful tests to analyze")
            return
        
        # Analyze vision capability
        print(f"\n🔍 VISION ANALYSIS:")
        
        # Check if responses contain visual descriptions
        visual_tests = [t for t in successful_tests if t.get("contains_visual_description")]
        if visual_tests:
            print(f"✅ Pixtral provided visual descriptions in {len(visual_tests)} tests")
        else:
            print(f"⚠️ No clear visual descriptions detected")
        
        # Check UI element detection
        ui_tests = [t for t in successful_tests if t.get("mentioned_ui_elements")]
        if ui_tests:
            all_ui = []
            for test in ui_tests:
                all_ui.extend(test.get("mentioned_ui_elements", []))
            unique_ui = list(set(all_ui))
            print(f"📋 UI elements mentioned: {', '.join(unique_ui)}")
        else:
            print(f"📋 No specific UI elements identified")
        
        # Check specific detections
        hp_test = next((t for t in successful_tests if "hp_bars_detected" in t), None)
        if hp_test:
            if hp_test["hp_bars_detected"]:
                print(f"❤️ Claims to see HP bars (may indicate battle scene detection)")
            elif hp_test["hp_bars_detected"] is False:
                print(f"❤️ Claims no HP bars (may indicate overworld)")
            else:
                print(f"❤️ Unclear about HP bars")
        
        char_test = next((t for t in successful_tests if "character_detected" in t), None)
        if char_test:
            if char_test["character_detected"]:
                print(f"👤 Claims to see character")
            elif char_test["character_detected"] is False:
                print(f"👤 Claims no character visible")
            else:
                print(f"👤 Unclear about character")
        
        battle_test = next((t for t in successful_tests if "battle_detected" in t), None)
        if battle_test:
            if battle_test["battle_detected"]:
                print(f"⚔️ CLAIMS THIS IS A BATTLE SCENE")
            elif battle_test["battle_detected"] is False:
                print(f"🌍 Claims this is NOT a battle scene")
            else:
                print(f"⚔️ Unclear about battle status")
        
        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        
        if len(visual_tests) >= 2 and ui_tests:
            print("✅ Pixtral appears to be analyzing visual content")
        elif len(visual_tests) >= 1:
            print("⚠️ Pixtral may be seeing some visual content")
        else:
            print("❌ Pixtral may not be processing visual content properly")
        
        # Save results
        self.save_test_results()
    
    def save_test_results(self) -> None:
        """Save detailed test results"""
        timestamp = int(time.time())
        results_file = Path(__file__).parent / f"pixtral_vision_test_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")

def main():
    """Main test execution"""
    print("👁️ Pixtral Vision Verification Test")
    print("=" * 50)
    print("This will test if Pixtral can actually see and analyze screenshots")
    print("User reports: AI claims overworld scenes are battles")
    print("Goal: Verify if Pixtral is seeing visual content or making assumptions")
    print()
    
    # Run tests
    tester = PixtralVisionTester()
    tester.run_all_tests()
    
    print("\n✅ Vision verification complete!")
    print("\nWhat we learned:")
    print("1. Whether Pixtral can actually see the screen")
    print("2. What visual elements it can identify") 
    print("3. If it's making up responses vs analyzing visuals")
    print("4. Why it might be misclassifying overworld as battle")

if __name__ == "__main__":
    main()