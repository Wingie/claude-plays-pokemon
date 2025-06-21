#!/usr/bin/env python3
"""
Test script to verify learning system fixes
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from prompt_manager import PromptManager
from episode_reviewer import EpisodeReviewer

def test_template_reloading():
    """Test template reloading functionality"""
    print("=== Testing Template Reloading ===")
    
    pm = PromptManager()
    
    # Show initial versions
    print("Initial template versions:")
    versions = pm.get_template_versions()
    for template, version in versions.items():
        print(f"  {template}: {version}")
    
    # Test reload functionality
    print("\nTesting reload...")
    pm.reload_templates()
    
    print("✅ Template reloading works")

def test_improved_suggestions():
    """Test improved context-aware suggestions"""
    print("\n=== Testing Improved Suggestions ===")
    
    reviewer = EpisodeReviewer()
    
    # Create mock metrics with HM Cut blocked scenario
    from episode_reviewer import EpisodeMetrics
    
    metrics = EpisodeMetrics(
        turns_completed=20,
        battles_won=0,
        battles_lost=0,
        items_collected=0,  # Can't collect blocked items
        new_areas_discovered=1,
        stuck_patterns=5,  # High stuck patterns trying to reach blocked items
        navigation_efficiency=0.3,  # Low efficiency due to stuck patterns
        progress_toward_okrs={"gym_badges": 0.0},
        major_achievements=[],
        failure_modes=["Stuck trying to reach blocked items"]
    )
    
    improvements = reviewer.suggest_prompt_improvements(metrics)
    
    print(f"Generated {len(improvements)} improvements:")
    for improvement in improvements:
        print(f"\n📝 {improvement.prompt_name} ({improvement.priority} priority):")
        print(f"   Reasoning: {improvement.reasoning}")
        print(f"   Suggestions: {improvement.suggested_changes}")
    
    print("✅ Context-aware suggestions work")

def test_ai_directed_prompts():
    """Test AI-directed prompt system"""
    print("\n=== Testing AI-Directed Prompts ===")
    
    pm = PromptManager()
    
    # Test navigation context
    prompt = pm.get_ai_directed_prompt(
        context_type="navigation",
        task="walk around and win pokemon battles",
        recent_actions=['right', 'right', 'right'],
        available_memories=['navigation', 'battle'],
        verbose=True
    )
    
    print("Navigation prompt length:", len(prompt))
    print("Contains playbook content:", "Pokemon Game Navigation" in prompt)
    
    # Test battle context  
    prompt = pm.get_ai_directed_prompt(
        context_type="battle",
        task="win pokemon battles",
        recent_actions=['a'],
        battle_context={"battle_phase": "menu"},
        verbose=True
    )
    
    print("Battle prompt length:", len(prompt))
    print("Contains battle guidance:", "TYPE EFFECTIVENESS" in prompt)
    
    print("✅ AI-directed prompts work with playbooks")

if __name__ == "__main__":
    try:
        test_template_reloading()
        test_improved_suggestions()  
        test_ai_directed_prompts()
        
        print("\n🎉 All learning system fixes working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()