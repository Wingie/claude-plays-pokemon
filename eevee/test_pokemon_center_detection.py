#!/usr/bin/env python3
"""
Pokemon Center Visual Detection Test Script

Tests the enhanced visual analysis system's ability to:
1. Detect Pokemon Centers from screenshots 
2. Identify healing states (approaching, at counter, in dialogue)
3. Generate appropriate navigation strategies
4. Use the new pokemon_center_navigation template

Usage:
    python test_pokemon_center_detection.py --image tests/pokecenter_1.png
    python test_pokemon_center_detection.py --test-all
"""

import argparse
import sys
import os
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    from prompt_manager import PromptManager
    from llm_api import call_llm
except ImportError as e:
    print(f"Error importing required modules: {e}")
    raise

class PokemonCenterDetectionTester:
    """Test Pokemon Center detection and navigation template selection"""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        
    def load_and_encode_image(self, image_path: str) -> str:
        """Load image and encode as base64 for LLM analysis"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to base64
                from io import BytesIO
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return img_base64
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def test_visual_analysis(self, image_path: str, provider: str = "gemini") -> Dict[str, Any]:
        """Test visual analysis on a Pokemon Center screenshot"""
        print(f"\n🧪 Testing Pokemon Center Detection: {image_path}")
        print("=" * 60)
        
        # Load and encode image
        img_base64 = self.load_and_encode_image(image_path)
        if not img_base64:
            return {"error": "Failed to load image"}
        
        # Get visual context analyzer template
        template_name = "visual_context_analyzer_gemini" if provider == "gemini" else "visual_context_analyzer"
        
        try:
            prompt = self.prompt_manager.get_prompt(template_name, variables={})
        except Exception as e:
            return {"error": f"Failed to get template {template_name}: {e}"}
        
        print(f"📋 Using template: {template_name}")
        print(f"🔍 Provider: {provider}")
        
        # Call LLM with image
        try:
            llm_response = call_llm(
                prompt=prompt,
                provider=provider,
                image_data=img_base64
            )
            
            # Extract the text response
            response = llm_response.text if hasattr(llm_response, 'text') else str(llm_response)
            
            print(f"\n📄 Raw LLM Response:")
            print("-" * 40)
            print(response)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (handle potential markdown formatting)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    parsed_response = json.loads(json_str)
                    
                    print(f"\n✅ Parsed JSON Response:")
                    print("-" * 40)
                    print(json.dumps(parsed_response, indent=2))
                    
                    return {
                        "success": True,
                        "raw_response": response,
                        "parsed_json": parsed_response,
                        "template_used": template_name,
                        "provider": provider
                    }
                else:
                    return {
                        "success": False,
                        "error": "No JSON found in response",
                        "raw_response": response
                    }
                    
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"JSON parsing failed: {e}",
                    "raw_response": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM call failed: {e}"
            }
    
    def test_pokemon_center_navigation(self, detection_result: Dict[str, Any], goal: str = "Heal at Pokemon Center") -> Dict[str, Any]:
        """Test the pokemon_center_navigation template if Pokemon Center was detected"""
        
        if not detection_result.get("success"):
            return {"error": "Cannot test navigation - detection failed"}
        
        parsed_json = detection_result.get("parsed_json", {})
        scene_type = parsed_json.get("scene_type")
        recommended_template = parsed_json.get("recommended_template")
        
        print(f"\n🧭 Testing Pokemon Center Navigation Template")
        print("=" * 60)
        print(f"🎯 Goal: {goal}")
        print(f"🏠 Detected scene type: {scene_type}")
        print(f"📝 Recommended template: {recommended_template}")
        
        if recommended_template != "pokemon_center_navigation":
            return {
                "success": False,
                "error": f"Expected pokemon_center_navigation, got {recommended_template}",
                "detection_result": detection_result
            }
        
        # Get the pokemon_center_navigation template
        try:
            prompt = self.prompt_manager.get_prompt("pokemon_center_navigation", variables={"task": goal})
        except Exception as e:
            return {"error": f"Failed to get pokemon_center_navigation template: {e}"}
        
        print(f"\n📋 Pokemon Center Navigation Prompt:")
        print("-" * 40)
        print(prompt + "..." if len(prompt) > 500 else prompt)
        
        # In a real scenario, this would be called with visual context
        # For testing, we'll just validate the template exists and is properly formatted
        return {
            "success": True,
            "template_found": True,
            "template_name": "pokemon_center_navigation",
            "formatted_prompt_length": len(prompt),
            "detection_result": detection_result
        }
    
    def analyze_detection_quality(self, result: Dict[str, Any], image_path: str) -> Dict[str, str]:
        """Analyze the quality of Pokemon Center detection"""
        
        if not result.get("success"):
            return {"quality": "FAILED", "reason": result.get("error", "Unknown error")}
        
        parsed_json = result.get("parsed_json", {})
        scene_type = parsed_json.get("scene_type")
        recommended_template = parsed_json.get("recommended_template")
        confidence = parsed_json.get("confidence", "unknown")
        
        # Expected results for different images
        image_name = Path(image_path).name
        expected_results = {
            "pokecenter_1.png": {
                "scene_type": "pokemon_center",
                "template": "pokemon_center_navigation",
                "description": "Interior view with Nurse Joy"
            },
            "pokecenter_2.png": {
                "scene_type": "pokemon_center", 
                "template": "pokemon_center_navigation",
                "description": "Player approaching counter"
            },
            "pokecenter_3.png": {
                "scene_type": "pokemon_center",
                "template": "pokemon_center_navigation", 
                "description": "Dialogue with Nurse Joy"
            }
        }
        
        expected = expected_results.get(image_name, {})
        
        quality_issues = []
        
        # Check scene type
        if scene_type != expected.get("scene_type"):
            quality_issues.append(f"Wrong scene_type: got '{scene_type}', expected '{expected.get('scene_type')}'")
        
        # Check template recommendation
        if recommended_template != expected.get("template"):
            quality_issues.append(f"Wrong template: got '{recommended_template}', expected '{expected.get('template')}'")
        
        # Check confidence
        if confidence == "low":
            quality_issues.append("Low confidence detection")
        
        if not quality_issues:
            return {
                "quality": "EXCELLENT",
                "reason": f"Perfect detection for {expected.get('description', 'Pokemon Center scene')}"
            }
        elif len(quality_issues) == 1 and "confidence" in quality_issues[0]:
            return {
                "quality": "GOOD", 
                "reason": f"Correct detection but {quality_issues[0]}"
            }
        else:
            return {
                "quality": "POOR",
                "reason": "; ".join(quality_issues)
            }

def main():
    parser = argparse.ArgumentParser(description="Test Pokemon Center visual detection")
    parser.add_argument("--image", type=str, help="Path to Pokemon Center screenshot")
    parser.add_argument("--test-all", action="store_true", help="Test all Pokemon Center images")
    parser.add_argument("--provider", type=str, default="gemini", choices=["gemini", "mistral"], help="LLM provider")
    parser.add_argument("--goal", type=str, default="Heal at Pokemon Center", help="Goal for navigation testing")
    
    args = parser.parse_args()
    
    tester = PokemonCenterDetectionTester()
    
    if args.test_all:
        # Test all Pokemon Center images
        test_images = [
            "tests/pokecenter_1.png",
            "tests/pokecenter_2.png", 
            "tests/pokecenter_3.png"
        ]
        
        print("🎮 Pokemon Center Detection Test Suite")
        print("=" * 60)
        
        results = []
        for image_path in test_images:
            if not Path(image_path).exists():
                print(f"❌ Image not found: {image_path}")
                continue
                
            # Test visual detection
            detection_result = tester.test_visual_analysis(image_path, args.provider)
            
            # Test navigation template (if detection succeeded)
            navigation_result = None
            if detection_result.get("success"):
                navigation_result = tester.test_pokemon_center_navigation(detection_result, args.goal)
            
            # Analyze quality
            quality_analysis = tester.analyze_detection_quality(detection_result, image_path)
            
            results.append({
                "image": image_path,
                "detection": detection_result,
                "navigation": navigation_result,
                "quality": quality_analysis
            })
            
            print(f"\n📊 Quality Assessment: {quality_analysis['quality']}")
            print(f"💭 Reason: {quality_analysis['reason']}")
        
        # Summary
        print(f"\n📈 Test Suite Summary")
        print("=" * 60)
        excellent_count = sum(1 for r in results if r["quality"]["quality"] == "EXCELLENT")
        good_count = sum(1 for r in results if r["quality"]["quality"] == "GOOD")
        poor_count = sum(1 for r in results if r["quality"]["quality"] == "POOR")
        failed_count = sum(1 for r in results if r["quality"]["quality"] == "FAILED")
        
        print(f"✅ EXCELLENT: {excellent_count}")
        print(f"👍 GOOD: {good_count}")
        print(f"⚠️  POOR: {poor_count}")
        print(f"❌ FAILED: {failed_count}")
        
        if excellent_count == len(results):
            print(f"\n🎉 All tests passed! Pokemon Center detection is working perfectly!")
        elif excellent_count + good_count == len(results):
            print(f"\n✅ Tests mostly successful! Pokemon Center detection is working well.")
        else:
            print(f"\n⚠️  Some tests failed. Pokemon Center detection needs improvement.")
    
    elif args.image:
        # Test single image
        if not Path(args.image).exists():
            print(f"❌ Image not found: {args.image}")
            return
        
        # Test visual detection
        detection_result = tester.test_visual_analysis(args.image, args.provider)
        
        # Test navigation template (if detection succeeded) 
        if detection_result.get("success"):
            navigation_result = tester.test_pokemon_center_navigation(detection_result, args.goal)
            
            if navigation_result.get("success"):
                print(f"\n🎉 SUCCESS: Pokemon Center detected and navigation template ready!")
            else:
                print(f"\n⚠️  Navigation test failed: {navigation_result.get('error')}")
        else:
            print(f"\n❌ Detection failed: {detection_result.get('error')}")
        
        # Quality analysis
        quality_analysis = tester.analyze_detection_quality(detection_result, args.image)
        print(f"\n📊 Quality: {quality_analysis['quality']}")
        print(f"💭 Reason: {quality_analysis['reason']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()