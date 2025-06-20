#!/usr/bin/env python3
"""
Test script for the Episode Reviewer system
"""

import json
from pathlib import Path
from episode_reviewer import EpisodeReviewer

def create_test_session_data():
    """Create sample session data for testing"""
    test_data = {
        "session_id": "test_session_20250620",
        "goal": "Test episode review system",
        "start_time": "2025-06-20T10:00:00",
        "turns": []
    }
    
    # Generate 10 sample turns with various scenarios
    for i in range(1, 11):
        turn_data = {
            "turn": i,
            "timestamp": f"2025-06-20T10:{i:02d}:00",
            "ai_analysis": "",
            "button_presses": [],
            "action_result": True,
            "screenshot_path": f"screenshot_{i}.png",
            "execution_time": 2.0
        }
        
        # Add varied scenarios
        if i <= 3:
            # Navigation turns
            turn_data["ai_analysis"] = f"Moving through route, exploring area {i}"
            turn_data["button_presses"] = ["right"]
        elif i == 4:
            # Battle start
            turn_data["ai_analysis"] = "Wild Caterpie appeared! Starting battle"
            turn_data["button_presses"] = ["a"]
        elif i == 5:
            # Battle won
            turn_data["ai_analysis"] = "Caterpie defeated! Pikachu gained 30 EXP points"
            turn_data["button_presses"] = ["a"]
        elif i >= 6 and i <= 8:
            # Stuck pattern
            turn_data["ai_analysis"] = f"Trying to move right {i-5} times"
            turn_data["button_presses"] = ["right"]  # Repeated action = stuck pattern
        elif i == 9:
            # Item found
            turn_data["ai_analysis"] = "Found a Pokeball! Picked up item"
            turn_data["button_presses"] = ["a"]
        else:
            # New area
            turn_data["ai_analysis"] = "Entered Viridian Forest! New area discovered"
            turn_data["button_presses"] = ["up"]
        
        test_data["turns"].append(turn_data)
    
    return test_data

def test_episode_reviewer():
    """Test the episode reviewer functionality"""
    print("🧪 Testing Episode Reviewer System")
    print("=" * 50)
    
    # Create test session directory
    test_dir = Path(__file__).parent / "test_runs" / "test_session_20250620"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test session data
    session_data = create_test_session_data()
    session_file = test_dir / "session_data.json"
    
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"✅ Created test session data: {session_file}")
    
    # Initialize reviewer
    reviewer = EpisodeReviewer()
    
    # Test episode analysis
    print("\n📊 Testing Episode Analysis...")
    try:
        metrics = reviewer.analyze_episode(test_dir)
        
        print(f"   Turns Completed: {metrics.turns_completed}")
        print(f"   Navigation Efficiency: {metrics.navigation_efficiency:.2f}")
        print(f"   Battles Won: {metrics.battles_won}")
        print(f"   Stuck Patterns: {metrics.stuck_patterns}")
        print(f"   Major Achievements: {len(metrics.major_achievements)}")
        
    except Exception as e:
        print(f"❌ Episode analysis failed: {e}")
        return False
    
    # Test prompt improvements
    print("\n🔧 Testing Prompt Improvements...")
    try:
        improvements = reviewer.suggest_prompt_improvements(metrics)
        print(f"   Generated {len(improvements)} improvement suggestions")
        
        for improvement in improvements:
            print(f"   • {improvement.prompt_name} ({improvement.priority} priority)")
            
    except Exception as e:
        print(f"❌ Prompt improvements failed: {e}")
        return False
    
    # Test full report generation
    print("\n📋 Testing Report Generation...")
    try:
        report = reviewer.generate_episode_report(test_dir)
        
        # Save report
        report_file = test_dir / "test_episode_review.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"   Report generated: {report_file}")
        print(f"   Report length: {len(report)} characters")
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False
    
    print("\n✅ All tests passed! Episode Reviewer system is working correctly.")
    return True

if __name__ == "__main__":
    success = test_episode_reviewer()
    if success:
        print("\n🎉 Episode Reviewer system ready for production!")
    else:
        print("\n💥 Tests failed - check the implementation")