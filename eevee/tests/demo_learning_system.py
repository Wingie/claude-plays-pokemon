#!/usr/bin/env python3
"""
Demo script for the YAML Learning System
Shows how the system automatically improves prompts based on gameplay performance
"""

import json
from pathlib import Path
from episode_reviewer import EpisodeReviewer

def demo_learning_system():
    """Demonstrate the automatic learning system using test data"""
    print("🎮 YAML Learning System Demo")
    print("=" * 60)
    print("This demo shows how the AI automatically improves its prompts")
    print("based on gameplay performance analysis.")
    print()
    
    # Use the existing test data
    test_session_dir = Path(__file__).parent / "test_runs" / "test_session_20250620"
    
    if not test_session_dir.exists():
        print("❌ Test session not found. Run test_episode_reviewer.py first.")
        return False
    
    print(f"📁 Using test session: {test_session_dir.name}")
    print()
    
    # Initialize the reviewer 
    eevee_dir = Path(__file__).parent
    reviewer = EpisodeReviewer(eevee_dir)
    
    # Step 1: Show current template status
    print("📖 STEP 1: Current Template Analysis")
    print("-" * 40)
    
    base_prompts_file = eevee_dir / "prompts" / "base" / "base_prompts.yaml"
    if base_prompts_file.exists():
        import yaml
        with open(base_prompts_file, 'r') as f:
            current_templates = yaml.safe_load(f)
        
        template_count = len(current_templates)
        print(f"📝 Current templates loaded: {template_count}")
        
        for template_name, template_data in current_templates.items():
            version = template_data.get("version", "unknown")
            description = template_data.get("description", "No description")
            print(f"   • {template_name} v{version}: {description}")
    else:
        print("⚠️ No current templates found")
    
    print()
    
    # Step 2: Analyze session performance
    print("📊 STEP 2: Performance Analysis")
    print("-" * 40)
    
    try:
        metrics = reviewer.analyze_episode(test_session_dir)
        
        print(f"🎯 Episode Metrics:")
        print(f"   • Turns Completed: {metrics.turns_completed}")
        print(f"   • Navigation Efficiency: {metrics.navigation_efficiency:.2f}")
        print(f"   • Battle Win Rate: {metrics.battles_won / max(1, metrics.battles_won + metrics.battles_lost):.2f}")
        print(f"   • Stuck Patterns: {metrics.stuck_patterns}")
        print(f"   • Areas Discovered: {metrics.new_areas_discovered}")
        print(f"   • Major Achievements: {len(metrics.major_achievements)}")
        
        if metrics.major_achievements:
            for achievement in metrics.major_achievements:
                print(f"      - {achievement}")
        
        if metrics.failure_modes:
            print(f"   • Failure Modes: {len(metrics.failure_modes)}")
            for failure in metrics.failure_modes:
                print(f"      - {failure}")
    
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
        return False
    
    print()
    
    # Step 3: Show improvement suggestions 
    print("💡 STEP 3: AI-Generated Improvement Suggestions")
    print("-" * 40)
    
    improvements = reviewer.suggest_prompt_improvements(metrics)
    
    if improvements:
        print(f"🔧 {len(improvements)} improvements suggested:")
        
        for improvement in improvements:
            print(f"\n   📝 {improvement.prompt_name} (Priority: {improvement.priority})")
            print(f"      Issue: {improvement.reasoning}")
            print(f"      Changes: {improvement.suggested_changes[:100]}...")
            print(f"      Expected Impact: {improvement.expected_impact}")
    else:
        print("✅ No improvements needed - excellent performance!")
    
    print()
    
    # Step 4: Dry run to show what would be changed
    print("🔬 STEP 4: Dry Run - What Would Be Changed")
    print("-" * 40)
    
    dry_run_result = reviewer.update_yaml_templates(test_session_dir, apply_changes=False)
    
    if dry_run_result["success"]:
        if dry_run_result.get("dry_run") and "potential_changes" in dry_run_result:
            changes = dry_run_result["potential_changes"]
            print(f"🎯 Would apply {len(changes)} changes:")
            
            for change in changes:
                print(f"   📝 {change['template']} ({change['priority']} priority)")
                print(f"      Reason: {change['reasoning']}")
                print(f"      Changes: {change['suggested_changes'][:150]}...")
                print()
        else:
            print("✅ No changes would be made - performance is optimal")
    else:
        print(f"❌ Dry run failed: {dry_run_result.get('message')}")
    
    # Step 5: Show change history
    print("📚 STEP 5: Learning History")
    print("-" * 40)
    
    change_history = reviewer.get_template_change_history(limit=5)
    
    if change_history:
        print(f"📋 Recent template changes:")
        for i, change in enumerate(change_history):
            print(f"   {i+1}. {change.get('template_name', 'Unknown')} v{change.get('old_version', '?')} → v{change.get('new_version', '?')}")
            print(f"      {change.get('reasoning', 'No reasoning')}")
            print(f"      {change.get('timestamp', 'Unknown time')}")
            print()
    else:
        print("📝 No change history found (this would be the first learning session)")
    
    print("🎉 Demo Complete!")
    print()
    print("💡 In actual gameplay, this analysis runs automatically every N turns")
    print("   and applies improvements to help the AI learn and perform better!")
    print()
    print("🔧 To enable automatic learning in gameplay:")
    print("   python run_eevee.py --episode-review-frequency 5  # Review every 5 turns")
    print("   python run_eevee.py --episode-review-frequency 100  # Review every 100 turns (default)")
    
    return True

if __name__ == "__main__":
    success = demo_learning_system()
    if not success:
        print("\n💥 Demo failed. Check that test data exists.")
        exit(1)
    else:
        print("\n✨ Demo completed successfully!")
        exit(0)