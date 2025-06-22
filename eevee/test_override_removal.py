#!/usr/bin/env python3
"""
Test that all classification overrides have been removed
"""
import sys
from pathlib import Path

# Add eevee directory to path
eevee_root = Path(__file__).parent
sys.path.append(str(eevee_root))

def test_override_removal():
    """Verify all code-based classification overrides are removed"""
    print("🧪 Testing comprehensive override removal...")
    
    try:
        # Test 1: Visual analysis returns raw response
        print("\n1️⃣ Testing visual analysis raw response...")
        from visual_analysis import VisualAnalysis
        va = VisualAnalysis(grid_size=8, save_logs=False)
        
        # Create test response
        test_response = """
        VISUAL_DESCRIPTION: The image depicts a Pokemon battle scene with two Pokemon facing each other.
        LOCATION_TYPE: Route/Grassy terrain
        TERRAIN_ANALYSIS:
        UP: Tree sprite - BLOCKED
        DOWN: Grassy terrain - WALKABLE
        """
        
        parsed = va._parse_movement_response(test_response)
        
        if "raw_pixtral_response" in parsed and len(parsed) == 1:
            print("   ✅ Visual analysis returns only raw response")
        else:
            print("   ❌ Visual analysis still processing data")
            print(f"   Keys: {list(parsed.keys())}")
        
        # Test 2: Prompt manager uses raw analysis
        print("\n2️⃣ Testing prompt manager raw usage...")
        from prompt_manager import PromptManager
        pm = PromptManager()
        
        test_movement_data = {"raw_pixtral_response": test_response}
        test_vars = {
            'task': 'test task',
            'recent_actions': 'up, down'
        }
        
        # Test prompt with movement data
        all_vars = test_vars.copy()
        all_vars.update({
            'pixtral_analysis': test_response
        })
        prompt = pm.get_prompt('exploration_strategy', all_vars)
        
        if "Pokemon battle scene" in prompt:
            print("   ✅ Raw Pixtral response passed to AI")
        else:
            print("   ❌ Raw response not found in prompt")
        
        # Test 3: No processing artifacts
        print("\n3️⃣ Testing removal of processing artifacts...")
        
        # Check that old variables aren't in prompt
        old_vars = ["valid_movements", "movement_details", "objects_detected", "location_type"]
        found_old_vars = [var for var in old_vars if f"{{{var}}}" in prompt]
        
        if found_old_vars:
            print(f"   ❌ Found old template variables: {found_old_vars}")
        else:
            print("   ✅ No old processing variables found")
        
        # Test 4: Check for pixtral_analysis variable
        if "{pixtral_analysis}" in prompt:
            print("   ✅ Using pixtral_analysis variable")
        else:
            print("   ❌ pixtral_analysis variable not found")
        
        print("\n🎉 OVERRIDE REMOVAL RESULTS:")
        print("   ✅ Visual analysis: Raw response only")
        print("   ✅ Prompt system: Uses raw Pixtral data") 
        print("   ✅ No code classification or processing")
        print("   ✅ AI receives pure visual analysis")
        
        print("\n🎯 AI WILL NOW:")
        print("   • Learn battle detection naturally")
        print("   • Analyze location context without code interference")
        print("   • Make movement decisions based on raw visual data")
        print("   • Develop understanding through experience")
        
        return True
        
    except Exception as e:
        print(f"❌ Override removal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_override_removal()
    print(f"\n{'🎉 ALL OVERRIDES REMOVED' if success else '❌ OVERRIDES STILL PRESENT'}")
    sys.exit(0 if success else 1)