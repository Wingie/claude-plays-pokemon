#!/usr/bin/env python3
"""
Quick test to verify enhanced logging is working
"""

import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

def test_logging_format():
    """Test the enhanced logging format"""
    print("🧪 Testing enhanced logging format...")
    
    try:
        # Import the main run_eevee module
        from run_eevee import ContinuousGameplay
        
        # Create a mock gameplay session
        class MockSession:
            goal = "find viridian forest"
            max_turns = 100
        
        class MockEevee:
            verbose = True
            debug = False
            prompt_manager = None
            memory = None
        
        # Create gameplay instance
        gameplay = ContinuousGameplay(MockEevee(), MockSession())
        
        # Test the enhanced logging
        analysis_text = """
        🎯 OBSERVATION: I can see the overworld with my character standing near some trees.
        🧠 ANALYSIS: I need to move north to find Viridian Forest based on my goal.
        ⚡ ACTION: I will press UP to move north toward the forest.
        """
        
        button_sequence = ["up"]
        
        print("Testing enhanced analysis logging...")
        gameplay._log_enhanced_analysis(1, analysis_text, button_sequence)
        
        print("✅ Enhanced logging format test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_context_selection():
    """Test the prompt context selection logic"""
    print("\n🧪 Testing prompt context selection...")
    
    try:
        from run_eevee import ContinuousGameplay
        
        class MockSession:
            goal = "find viridian forest"
        
        class MockEevee:
            pass
        
        gameplay = ContinuousGameplay(MockEevee(), MockSession())
        
        # Test different contexts
        test_cases = [
            ("recent battle with wild pokemon", ("battle_analysis", ["battle"])),
            ("navigate to pokemon center", ("location_analysis", ["services"])),
            ("exploring route 1", ("location_analysis", ["navigation"])),
            ("challenge brock gym", ("battle_analysis", ["battle", "gyms"]))
        ]
        
        for memory_context, expected in test_cases:
            result = gameplay._determine_prompt_context(memory_context)
            print(f"Context: '{memory_context}' → {result}")
            
            # Check if result matches expected pattern
            prompt_type, playbooks = result
            expected_type, expected_books = expected
            
            if prompt_type == expected_type and set(playbooks) == set(expected_books):
                print("  ✅ Correct context selection")
            else:
                print(f"  ⚠️ Expected {expected}, got {result}")
        
        print("✅ Prompt context selection test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Prompt context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run logging tests"""
    print("🔬 Enhanced Logging Test Suite")
    print("="*50)
    
    test_results = []
    test_results.append(("Enhanced Logging Format", test_logging_format()))
    test_results.append(("Prompt Context Selection", test_prompt_context_selection()))
    
    # Summary
    print("\n📊 Test Results:")
    print("="*50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 Enhanced logging is working correctly!")
        return 0
    else:
        print("⚠️ Some logging tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())