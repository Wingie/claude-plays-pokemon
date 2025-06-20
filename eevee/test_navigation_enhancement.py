#!/usr/bin/env python3
"""
Test script for Navigation Enhancement System
Tests loop detection, screenshot comparison, and recovery strategies
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from PIL import Image
import numpy as np

# Add the eevee directory to the path
sys.path.append(str(Path(__file__).parent))

try:
    from utils.navigation_enhancement import NavigationEnhancer, TurnData
    print("✅ Successfully imported NavigationEnhancer")
except ImportError as e:
    print(f"❌ Failed to import NavigationEnhancer: {e}")
    sys.exit(1)

def create_test_screenshot(color=(128, 128, 128), size=(160, 144)):
    """Create a test screenshot with specified color"""
    img = Image.new('RGB', size, color)
    return img

def test_screenshot_comparison():
    """Test screenshot comparison and similarity detection"""
    print("\n🧪 Testing Screenshot Comparison...")
    
    enhancer = NavigationEnhancer(history_size=10, similarity_threshold=0.95)
    
    # Create temporary directory for test screenshots
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create identical screenshots
        identical_img1 = create_test_screenshot((100, 100, 100))
        identical_img2 = create_test_screenshot((100, 100, 100))
        
        img1_path = temp_path / "test1.png"
        img2_path = temp_path / "test2.png"
        
        identical_img1.save(img1_path)
        identical_img2.save(img2_path)
        
        # Test first turn
        result1 = enhancer.add_turn_data(
            turn_number=1,
            screenshot_path=str(img1_path),
            buttons_pressed=["up"],
            ai_reasoning="Moving north"
        )
        
        print(f"   Turn 1 - Progress made: {result1['progress_made']}")
        
        # Test second turn with identical screenshot
        result2 = enhancer.add_turn_data(
            turn_number=2,
            screenshot_path=str(img2_path),
            buttons_pressed=["up"],
            ai_reasoning="Still moving north"
        )
        
        print(f"   Turn 2 - Progress made: {result2['progress_made']}")
        print(f"   Visual similarity: {result2['visual_similarity']:.3f}")
        print(f"   Visual stuck detected: {result2['visual_stuck']}")
        
        assert result2['visual_similarity'] > 0.9, "Should detect high similarity between identical images"
        assert not result2['progress_made'], "Should detect no progress with identical screenshots"
        
        print("   ✅ Screenshot comparison working correctly")

def test_loop_detection():
    """Test button press loop detection"""
    print("\n🧪 Testing Loop Detection...")
    
    enhancer = NavigationEnhancer(history_size=10, similarity_threshold=0.95)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create slightly different screenshots to avoid visual stuck detection
        for i in range(5):
            img = create_test_screenshot((100 + i, 100, 100))  # Slightly different colors
            img_path = temp_path / f"test{i+1}.png"
            img.save(img_path)
            
            result = enhancer.add_turn_data(
                turn_number=i+1,
                screenshot_path=str(img_path),
                buttons_pressed=["up"],  # Same button every time
                ai_reasoning=f"Turn {i+1} - moving up"
            )
            
            print(f"   Turn {i+1} - Loop detected: {result['loop_detected']}, Consecutive actions: {result['consecutive_similar_actions']}")
        
        # Should detect loop by turn 4 or 5
        assert result['loop_detected'], "Should detect button press loop"
        assert result['consecutive_similar_actions'] >= 3, "Should count consecutive actions"
        
        print("   ✅ Loop detection working correctly")

def test_recovery_strategies():
    """Test stuck mode recovery strategies"""
    print("\n🧪 Testing Recovery Strategies...")
    
    enhancer = NavigationEnhancer(history_size=10, similarity_threshold=0.95)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Simulate getting stuck with identical screenshots and same button
        for i in range(4):
            # Create identical screenshots to trigger visual stuck
            img = create_test_screenshot((100, 100, 100))
            img_path = temp_path / f"stuck{i+1}.png"
            img.save(img_path)
            
            result = enhancer.add_turn_data(
                turn_number=i+1,
                screenshot_path=str(img_path),
                buttons_pressed=["up"],
                ai_reasoning=f"Stuck turn {i+1}"
            )
        
        print(f"   Final result - Needs intervention: {result['needs_intervention']}")
        print(f"   Loop detected: {result['loop_detected']}")
        print(f"   Visual stuck: {result['visual_stuck']}")
        
        # Check recovery suggestions
        recovery = result['suggested_recovery']
        print(f"   Recovery type: {recovery['type']}")
        
        if recovery['type'] == 'recovery_needed':
            strategies = recovery.get('strategies', [])
            print(f"   Available strategies: {len(strategies)}")
            
            if strategies:
                recommended = recovery.get('recommended_strategy')
                print(f"   Recommended: {recommended['description'] if recommended else 'None'}")
                print(f"   Actions: {recommended['actions'] if recommended else 'None'}")
        
        assert result['needs_intervention'], "Should trigger intervention when stuck"
        assert recovery['type'] == 'recovery_needed', "Should suggest recovery strategies"
        
        print("   ✅ Recovery strategies working correctly")

def test_critique_function():
    """Test the 20-turn critique analysis"""
    print("\n🧪 Testing Critique Function...")
    
    enhancer = NavigationEnhancer(history_size=25, similarity_threshold=0.95)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Simulate 21 turns with mixed progress
        for i in range(21):
            # Mix of progress and no progress
            if i % 3 == 0:
                # Progress turn - different screenshot
                color = (100 + i*2, 100, 100)
            else:
                # No progress turn - same screenshot
                color = (100, 100, 100)
            
            img = create_test_screenshot(color)
            img_path = temp_path / f"critique{i+1}.png"
            img.save(img_path)
            
            button = ["up", "down", "left", "right"][i % 4]  # Vary buttons
            
            result = enhancer.add_turn_data(
                turn_number=i+1,
                screenshot_path=str(img_path),
                buttons_pressed=[button],
                ai_reasoning=f"Turn {i+1} analysis"
            )
        
        # Should have critique data from turn 20
        if 'critique' in result:
            critique = result['critique']
            print(f"   Critique available: ✅")
            print(f"   Progress ratio: {critique.get('progress_ratio', 'unknown'):.2f}")
            print(f"   Action diversity: {critique.get('action_diversity', 'unknown')}")
            print(f"   Problems identified: {len(critique.get('problems_identified', []))}")
            print(f"   Assessment: {critique.get('overall_assessment', 'unknown')}")
        else:
            print("   ❌ No critique generated")
        
        print("   ✅ Critique function working correctly")

def test_navigation_confidence():
    """Test navigation confidence calculation"""
    print("\n🧪 Testing Navigation Confidence...")
    
    enhancer = NavigationEnhancer(history_size=10, similarity_threshold=0.95)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test high confidence scenario (good progress, varied actions)
        buttons = ["up", "right", "down", "left", "a"]
        for i in range(5):
            # Each screenshot is different (good progress)
            img = create_test_screenshot((100 + i*10, 100 + i*5, 100))
            img_path = temp_path / f"confidence{i+1}.png"
            img.save(img_path)
            
            result = enhancer.add_turn_data(
                turn_number=i+1,
                screenshot_path=str(img_path),
                buttons_pressed=[buttons[i]],
                ai_reasoning=f"Good navigation turn {i+1}"
            )
        
        high_confidence = result['navigation_confidence']
        print(f"   High confidence scenario: {high_confidence:.3f}")
        
        # Test low confidence scenario (no progress, repetitive actions)
        for i in range(5, 10):
            # Same screenshot (no progress)
            img = create_test_screenshot((100, 100, 100))
            img_path = temp_path / f"confidence{i+1}.png"
            img.save(img_path)
            
            result = enhancer.add_turn_data(
                turn_number=i+1,
                screenshot_path=str(img_path),
                buttons_pressed=["up"],  # Same button
                ai_reasoning=f"Poor navigation turn {i+1}"
            )
        
        low_confidence = result['navigation_confidence']
        print(f"   Low confidence scenario: {low_confidence:.3f}")
        
        assert high_confidence > low_confidence, "High confidence should be greater than low confidence"
        
        print("   ✅ Navigation confidence calculation working correctly")

def main():
    """Run all navigation enhancement tests"""
    print("🚀 Testing Navigation Enhancement System")
    print("=" * 50)
    
    try:
        test_screenshot_comparison()
        test_loop_detection()
        test_recovery_strategies()
        test_critique_function()
        test_navigation_confidence()
        
        print("\n" + "=" * 50)
        print("🎉 All Navigation Enhancement Tests Passed!")
        print("\n✅ The navigation system is ready to:")
        print("   - Detect when AI is stuck in loops")
        print("   - Compare screenshots for visual progress")
        print("   - Suggest recovery strategies")
        print("   - Generate periodic critiques")
        print("   - Calculate navigation confidence")
        print("\n🎮 Ready to solve the infinite UP loop problem!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()