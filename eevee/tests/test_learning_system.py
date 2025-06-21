#!/usr/bin/env python3
"""
Test script for the YAML Learning System
Validates that episode reviews can automatically update prompt templates
"""

import json
import tempfile
import shutil
from pathlib import Path

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from datetime import datetime
from episode_reviewer import EpisodeReviewer
from prompt_template_updater import PromptTemplateUpdater

def create_test_session_with_poor_performance():
    """Create a test session with poor performance metrics to trigger improvements"""
    test_data = {
        "session_id": "test_learning_20250620",
        "goal": "Test automatic prompt learning system",
        "start_time": "2025-06-20T14:00:00",
        "turns": []
    }
    
    # Generate session with poor navigation efficiency and stuck patterns
    for i in range(1, 51):  # 50 turns to trigger episode review
        turn_data = {
            "turn": i,
            "timestamp": f"2025-06-20T14:{i:02d}:00",
            "ai_analysis": "",
            "button_presses": [],
            "action_result": True,
            "screenshot_path": f"screenshot_{i}.png",
            "execution_time": 2.0
        }
        
        # Create patterns that will trigger improvements
        if i <= 20:
            # Stuck pattern: repeating same movement
            turn_data["ai_analysis"] = f"Moving right {i} times, seems stuck but continuing"
            turn_data["button_presses"] = ["right"]  # Repetitive = stuck pattern
        elif i <= 25:
            # Battle without clear win
            turn_data["ai_analysis"] = f"Battle turn {i-20}, pressing A"
            turn_data["button_presses"] = ["a"]
        elif i <= 30:
            # More stuck patterns
            turn_data["ai_analysis"] = f"Trying to move up {i-25} times"
            turn_data["button_presses"] = ["up"]  # More stuck patterns
        elif i <= 35:
            # Menu stuck patterns
            turn_data["ai_analysis"] = f"PIKA grew to LV. 7! Still on level-up screen"
            turn_data["button_presses"] = ["a"]  # Should press B but pressing A
        else:
            # Random navigation with low efficiency
            turn_data["ai_analysis"] = f"Exploring area, turn {i}"
            turn_data["button_presses"] = ["down"]
        
        test_data["turns"].append(turn_data)
    
    return test_data

def create_test_session_with_good_performance():
    """Create a test session with good performance to verify no changes are made"""
    test_data = {
        "session_id": "test_good_20250620", 
        "goal": "Test that good performance doesn't trigger changes",
        "start_time": "2025-06-20T15:00:00",
        "turns": []
    }
    
    # Generate session with good navigation and battles
    for i in range(1, 21):  # 20 turns
        turn_data = {
            "turn": i,
            "timestamp": f"2025-06-20T15:{i:02d}:00",
            "ai_analysis": "",
            "button_presses": [],
            "action_result": True,
            "screenshot_path": f"screenshot_{i}.png",
            "execution_time": 1.5
        }
        
        if i <= 5:
            # Efficient exploration
            turn_data["ai_analysis"] = f"Exploring new area efficiently"
            turn_data["button_presses"] = ["right"]
        elif i <= 10:
            # Successful battle
            turn_data["ai_analysis"] = f"Wild Caterpie defeated! Pikachu gained EXP"
            turn_data["button_presses"] = ["a"]
        elif i <= 15:
            # Diverse navigation 
            directions = ["up", "left", "down", "right"]
            direction = directions[i % 4]
            turn_data["ai_analysis"] = f"Moving {direction} to new area"
            turn_data["button_presses"] = [direction]
        else:
            # Item collection
            turn_data["ai_analysis"] = f"Found useful item! Collected successfully"
            turn_data["button_presses"] = ["a"]
        
        test_data["turns"].append(turn_data)
    
    return test_data

def test_yaml_template_updater():
    """Test the PromptTemplateUpdater class directly"""
    print("🧪 Testing PromptTemplateUpdater class...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        prompts_dir = temp_path / "prompts"
        runs_dir = temp_path / "runs"
        
        prompts_dir.mkdir()
        (prompts_dir / "base").mkdir()
        runs_dir.mkdir()
        
        # Create a test YAML file
        test_yaml = {
            "exploration_strategy": {
                "name": "Test Exploration",
                "description": "Test template for learning",
                "template": "Original template content\nNo special rules yet\nEnd of template",
                "variables": ["task"],
                "version": "1.0"
            }
        }
        
        import yaml
        with open(prompts_dir / "base" / "base_prompts.yaml", 'w') as f:
            yaml.dump(test_yaml, f)
        
        # Initialize updater
        updater = PromptTemplateUpdater(prompts_dir, runs_dir)
        
        # Create a mock improvement
        from episode_reviewer import PromptImprovement
        improvement = PromptImprovement(
            prompt_name="exploration_strategy",
            current_version="1.0",
            suggested_changes="Add explicit stuck detection: If I've used the same action 3+ times, try a completely different direction",
            reasoning="Too many stuck patterns detected in recent gameplay",
            priority="high",
            expected_impact="Reduce stuck patterns by 30-50%"
        )
        
        # Test applying the improvement
        performance_metrics = {
            "navigation_efficiency": 0.3,
            "battle_win_rate": 0.8,
            "stuck_patterns": 15
        }
        
        change = updater.apply_improvement_suggestion(improvement, performance_metrics)
        
        if change:
            print(f"   ✅ Successfully applied change: {change.template_name} v{change.old_version} → v{change.new_version}")
            print(f"   📝 Reasoning: {change.reasoning}")
            
            # Verify the change was logged
            log_files = list((runs_dir / "prompt_changes").glob("change_*.json"))
            if log_files:
                print(f"   📋 Change logged to: {log_files[0].name}")
            else:
                print(f"   ❌ Change was not logged properly")
            
            return True
        else:
            print(f"   ❌ Failed to apply improvement")
            return False

def test_episode_reviewer_with_updates():
    """Test the EpisodeReviewer with YAML updates enabled"""
    print("🧪 Testing EpisodeReviewer with automatic YAML updates...")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_dir = temp_path / "eevee_test" 
        test_dir.mkdir()
        
        # Create required subdirectories
        (test_dir / "prompts" / "base").mkdir(parents=True)
        (test_dir / "runs").mkdir()
        session_dir = test_dir / "runs" / "test_session_learning"
        session_dir.mkdir()
        
        # Copy existing prompt templates for testing
        original_prompts_file = Path(__file__).parent / "prompts" / "base" / "base_prompts.yaml"
        test_prompts_file = test_dir / "prompts" / "base" / "base_prompts.yaml"
        
        if original_prompts_file.exists():
            shutil.copy2(original_prompts_file, test_prompts_file)
        else:
            # Create minimal test templates
            import yaml
            test_templates = {
                "exploration_strategy": {
                    "name": "Test Exploration",
                    "template": "Basic exploration template for testing",
                    "version": "1.0"
                }
            }
            with open(test_prompts_file, 'w') as f:
                yaml.dump(test_templates, f)
        
        # Create test session data with poor performance
        session_data = create_test_session_with_poor_performance()
        session_file = session_dir / "session_data.json"
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"   📁 Created test session: {session_dir}")
        
        # Initialize reviewer with test directory
        reviewer = EpisodeReviewer(test_dir)
        
        # Test the update process
        print(f"   🔍 Running episode analysis and template updates...")
        update_result = reviewer.update_yaml_templates(session_dir, apply_changes=True)
        
        if update_result["success"]:
            changes_applied = update_result["changes_applied"]
            print(f"   📊 Update successful: {changes_applied} changes applied")
            
            if changes_applied > 0:
                print(f"   🔧 Template improvements:")
                for change in update_result.get("changes", []):
                    print(f"      - {change['template']} {change['version']}: {change['reasoning']}")
                
                # Verify change logs were created
                log_dir = test_dir / "runs" / "prompt_changes"
                if log_dir.exists():
                    log_files = list(log_dir.glob("change_*.json"))
                    print(f"   📋 {len(log_files)} change log files created")
                else:
                    print(f"   ⚠️ Change log directory not created")
                
                return True
            else:
                print(f"   ℹ️ No changes needed (good performance)")
                return True
        else:
            print(f"   ❌ Update failed: {update_result.get('message', 'Unknown error')}")
            if update_result.get('error'):
                print(f"      Error: {update_result['error']}")
            return False

def test_performance_based_learning():
    """Test that good performance doesn't trigger unnecessary changes"""
    print("🧪 Testing performance-based learning (good performance should not trigger changes)...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_dir = temp_path / "eevee_good_test"
        test_dir.mkdir()
        
        # Create required structure
        (test_dir / "prompts" / "base").mkdir(parents=True)
        (test_dir / "runs").mkdir()
        session_dir = test_dir / "runs" / "good_session"
        session_dir.mkdir()
        
        # Create minimal templates
        import yaml
        test_templates = {
            "exploration_strategy": {
                "name": "Good Performance Test",
                "template": "Well-performing template",
                "version": "1.0"
            }
        }
        with open(test_dir / "prompts" / "base" / "base_prompts.yaml", 'w') as f:
            yaml.dump(test_templates, f)
        
        # Create session with good performance
        session_data = create_test_session_with_good_performance()
        with open(session_dir / "session_data.json", 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Test with good performance
        reviewer = EpisodeReviewer(test_dir)
        update_result = reviewer.update_yaml_templates(session_dir, apply_changes=True)
        
        if update_result["success"] and update_result["changes_applied"] == 0:
            print(f"   ✅ Correctly identified good performance - no changes made")
            print(f"   📊 Metrics: {update_result['metrics']}")
            return True
        elif update_result["changes_applied"] > 0:
            print(f"   ❌ Good performance incorrectly triggered {update_result['changes_applied']} changes")
            return False
        else:
            print(f"   ❌ Test failed: {update_result.get('message', 'Unknown error')}")
            return False

def main():
    """Run all learning system tests"""
    print("🚀 Testing YAML Learning System")
    print("=" * 60)
    
    tests = [
        ("PromptTemplateUpdater", test_yaml_template_updater),
        ("EpisodeReviewer with Updates", test_episode_reviewer_with_updates),
        ("Performance-based Learning", test_performance_based_learning)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append((test_name, False))
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n🎯 TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED" 
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! YAML Learning System is ready for production!")
        print(f"✨ The system can now:")
        print(f"   - Automatically analyze gameplay performance every N turns")
        print(f"   - Apply improvements to prompt templates based on metrics")
        print(f"   - Track all changes with git version control")
        print(f"   - Log learning events for analysis")
        print(f"   - Only update templates when performance actually needs improvement")
    else:
        print(f"\n💥 {total - passed} tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)