#!/usr/bin/env python3
"""
Deep Vision Research Script
Progressive prompt simplification to identify where Pixtral stops hallucinating
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

class VisionResearcher:
    """Research Pixtral's actual vision capabilities with progressive prompt simplification"""
    
    def __init__(self):
        self.controller = SkyEmuController()
        self.research_results: List[Dict] = []
        self.hallucination_keywords = ['health', 'bar', 'menu', 'button', 'hp', 'fight', 'bag', 'pokemon', 'run']
        
    def capture_screenshot(self) -> Optional[str]:
        """Capture and validate screenshot"""
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
                    print(f"📸 Valid PNG: {len(decoded_bytes)} bytes")
                elif decoded_bytes.startswith(b'\xff\xd8\xff'):
                    print(f"📸 Valid JPEG: {len(decoded_bytes)} bytes")
                else:
                    print(f"⚠️ Unknown format: {decoded_bytes[:10]}")
                    
                return screenshot_data
            except Exception as e:
                print(f"❌ Base64 validation error: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            return None
    
    def call_pixtral_simple(self, prompt: str, image_data: str) -> Dict:
        """Make API call with minimal processing"""
        try:
            response = call_llm(
                prompt=prompt,
                image_data=image_data,
                model="pixtral-12b-2409",
                provider="mistral",
                max_tokens=200
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
    
    def count_hallucinations(self, text: str) -> Dict:
        """Count hallucination keywords in response"""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.hallucination_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return {
            "hallucination_count": len(found_keywords),
            "found_keywords": found_keywords,
            "has_hallucinations": len(found_keywords) > 0
        }
    
    def test_neutral_description(self, image_data: str) -> Dict:
        """Test 1: Completely neutral image description"""
        print("\n🔍 TEST 1: Neutral Description (No Context)")
        print("=" * 60)
        
        prompt = "Describe this image."
        
        result = self.call_pixtral_simple(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            hallucination_info = self.count_hallucinations(result['response'])
            result.update(hallucination_info)
            
            if hallucination_info["has_hallucinations"]:
                print(f"⚠️ HALLUCINATIONS DETECTED: {hallucination_info['found_keywords']}")
            else:
                print(f"✅ NO HALLUCINATIONS - Pure visual description")
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "neutral_description"
        result["prompt"] = prompt
        return result
    
    def test_color_identification(self, image_data: str) -> Dict:
        """Test 2: Simple color identification"""
        print("\n🎨 TEST 2: Color Identification")
        print("=" * 60)
        
        prompt = "What colors do you see in this image?"
        
        result = self.call_pixtral_simple(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            hallucination_info = self.count_hallucinations(result['response'])
            result.update(hallucination_info)
            
            if hallucination_info["has_hallucinations"]:
                print(f"⚠️ HALLUCINATIONS DETECTED: {hallucination_info['found_keywords']}")
            else:
                print(f"✅ NO HALLUCINATIONS - Pure color description")
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "color_identification"
        result["prompt"] = prompt
        return result
    
    def test_shape_counting(self, image_data: str) -> Dict:
        """Test 3: Shape and object counting"""
        print("\n🔢 TEST 3: Shape Counting")
        print("=" * 60)
        
        prompt = "How many distinct objects or shapes can you count in this image?"
        
        result = self.call_pixtral_simple(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            hallucination_info = self.count_hallucinations(result['response'])
            result.update(hallucination_info)
            
            if hallucination_info["has_hallucinations"]:
                print(f"⚠️ HALLUCINATIONS DETECTED: {hallucination_info['found_keywords']}")
            else:
                print(f"✅ NO HALLUCINATIONS - Pure counting")
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "shape_counting"
        result["prompt"] = prompt
        return result
    
    def test_background_description(self, image_data: str) -> Dict:
        """Test 4: Background description only"""
        print("\n🖼️ TEST 4: Background Description")
        print("=" * 60)
        
        prompt = "Describe only the background of this image."
        
        result = self.call_pixtral_simple(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            hallucination_info = self.count_hallucinations(result['response'])
            result.update(hallucination_info)
            
            if hallucination_info["has_hallucinations"]:
                print(f"⚠️ HALLUCINATIONS DETECTED: {hallucination_info['found_keywords']}")
            else:
                print(f"✅ NO HALLUCINATIONS - Pure background description")
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "background_description"  
        result["prompt"] = prompt
        return result
    
    def test_dominant_color(self, image_data: str) -> Dict:
        """Test 5: Dominant color identification"""
        print("\n🌈 TEST 5: Dominant Color")
        print("=" * 60)
        
        prompt = "What is the dominant color in this image?"
        
        result = self.call_pixtral_simple(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            hallucination_info = self.count_hallucinations(result['response'])
            result.update(hallucination_info)
            
            if hallucination_info["has_hallucinations"]:
                print(f"⚠️ HALLUCINATIONS DETECTED: {hallucination_info['found_keywords']}")
            else:
                print(f"✅ NO HALLUCINATIONS - Pure color analysis")
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "dominant_color"
        result["prompt"] = prompt
        return result
    
    def test_spatial_layout(self, image_data: str) -> Dict:
        """Test 6: Spatial layout description"""
        print("\n📐 TEST 6: Spatial Layout")
        print("=" * 60)
        
        prompt = "Describe the layout and positioning of elements in this image."
        
        result = self.call_pixtral_simple(prompt, image_data)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
            hallucination_info = self.count_hallucinations(result['response'])
            result.update(hallucination_info)
            
            if hallucination_info["has_hallucinations"]:
                print(f"⚠️ HALLUCINATIONS DETECTED: {hallucination_info['found_keywords']}")
            else:
                print(f"✅ NO HALLUCINATIONS - Pure spatial analysis")
        else:
            print(f"❌ Error: {result['error']}")
        
        result["test_name"] = "spatial_layout"
        result["prompt"] = prompt
        return result
    
    def run_deep_research(self) -> None:
        """Run all vision research tests"""
        print("🔬 Deep Vision Research - Progressive Prompt Simplification")
        print("=" * 80)
        print("Goal: Find where Pixtral stops hallucinating game elements")
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
        
        # Run all tests
        test_methods = [
            ("Neutral Description", self.test_neutral_description),
            ("Color Identification", self.test_color_identification),
            ("Shape Counting", self.test_shape_counting),
            ("Background Description", self.test_background_description),
            ("Dominant Color", self.test_dominant_color),
            ("Spatial Layout", self.test_spatial_layout)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method(image_data)
                self.research_results.append(result)
                
                # Brief pause between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Test '{test_name}' failed: {e}")
                self.research_results.append({
                    "test_name": test_name.lower().replace(" ", "_"),
                    "success": False,
                    "error": str(e)
                })
        
        # Analyze results
        self.analyze_hallucination_patterns()
    
    def analyze_hallucination_patterns(self) -> None:
        """Analyze when and why hallucinations occur"""
        print("\n" + "=" * 80)
        print("🔬 DEEP RESEARCH ANALYSIS")
        print("=" * 80)
        
        successful_tests = [r for r in self.research_results if r.get("success", False)]
        failed_tests = [r for r in self.research_results if not r.get("success", False)]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(self.research_results)}")
        
        if failed_tests:
            print(f"❌ Failed tests: {len(failed_tests)}")
            for test in failed_tests:
                print(f"   - {test.get('test_name', 'unknown')}: {test.get('error', 'unknown error')}")
        
        if not successful_tests:
            print("❌ No successful tests to analyze")
            return
        
        # Analyze hallucination patterns
        print(f"\n🔍 HALLUCINATION ANALYSIS:")
        
        clean_tests = []
        hallucinating_tests = []
        
        for test in successful_tests:
            if test.get("has_hallucinations", False):
                hallucinating_tests.append(test)
            else:
                clean_tests.append(test)
        
        print(f"✅ Clean responses (no game hallucinations): {len(clean_tests)}")
        print(f"⚠️ Hallucinating responses: {len(hallucinating_tests)}")
        
        if clean_tests:
            print(f"\n✅ CLEAN TESTS (Actual Vision Working):")
            for test in clean_tests:
                print(f"   - {test['test_name']}: No game keywords detected")
                print(f"     Response preview: {test['response'][:100]}...")
        
        if hallucinating_tests:
            print(f"\n⚠️ HALLUCINATING TESTS (Still Making Up Game Elements):")
            for test in hallucinating_tests:
                print(f"   - {test['test_name']}: Found keywords: {test['found_keywords']}")
                print(f"     Response preview: {test['response'][:100]}...")
        
        # Overall assessment
        print(f"\n🎯 RESEARCH CONCLUSION:")
        
        if len(clean_tests) == len(successful_tests):
            print("✅ SUCCESS: Pixtral stopped hallucinating with neutral prompts!")
            print("   - The issue is prompt-induced hallucination")
            print("   - Pixtral CAN see the image when given neutral prompts")
            print("   - Solution: Use completely neutral prompts for template selection")
        elif len(clean_tests) > 0:
            print("⚠️ PARTIAL SUCCESS: Some prompts work, others don't")
            print(f"   - {len(clean_tests)} prompts produced clean responses")
            print(f"   - {len(hallucinating_tests)} prompts still cause hallucinations")
            print("   - Solution: Use only the clean prompt styles")
        else:
            print("❌ FAILURE: All prompts cause hallucinations")
            print("   - Pixtral may not be processing the image correctly")
            print("   - Base64 transmission or API integration issue likely")
        
        # Save results
        self.save_research_results()
    
    def save_research_results(self) -> None:
        """Save detailed research results"""
        timestamp = int(time.time())
        results_file = Path(__file__).parent / f"vision_research_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.research_results, f, indent=2)
        
        print(f"\n💾 Research results saved to: {results_file}")

def main():
    """Main research execution"""
    print("🔬 Deep Vision Research - Pixtral Hallucination Analysis")
    print("=" * 70)
    print("Research Question: At what point does Pixtral stop hallucinating?")
    print("Method: Progressive prompt simplification")
    print("Success Criteria: No mentions of 'health, bar, menu, button'")
    print()
    
    # Run research
    researcher = VisionResearcher()
    researcher.run_deep_research()
    
    print("\n✅ Deep vision research complete!")
    print("\nKey Findings:")
    print("1. Which prompts cause hallucinations vs clean responses")
    print("2. Whether Pixtral can actually see the image content")
    print("3. How to fix the template selection system")

if __name__ == "__main__":
    main()