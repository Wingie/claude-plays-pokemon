#!/usr/bin/env python3
"""
Test script to demonstrate the goal-oriented planning system
Shows 3 steps with reviews for each step
"""

import subprocess
import sys
import time

def run_test_with_small_steps():
    """Run a test with forced periodic reviews every 3 turns"""
    
    print("🎯 Testing Goal-Oriented Planning System")
    print("="*60)
    print("This test will run 3 turns with a review after each turn")
    print("We'll use --episode-review-frequency 1 to force reviews")
    print("="*60)
    
    # Command to run eevee with:
    # - A simple goal
    # - Max 3 turns
    # - Episode review every 1 turn (to see reviews after each step)
    # - Verbose output
    cmd = [
        "python", "run_eevee.py",
        "--goal", "check my pokemon party status",
        "--max-turns", "3",
        "--episode-review-frequency", "1",
        "--verbose",
        "--no-interactive"  # Non-interactive mode for testing
    ]
    
    print(f"\n📋 Running command: {' '.join(cmd)}")
    print("="*60)
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
            check=False
        )
        
        print("\n" + "="*60)
        print(f"✅ Test completed with return code: {result.returncode}")
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Goal System Test")
    print("This will demonstrate the goal-oriented planning flow")
    print("Watch for:")
    print("  1. Goal decomposition (_decompose_task_into_goals)")
    print("  2. Periodic reviews after each turn (_run_periodic_episode_review)")
    print("  3. Goal progress analysis (_run_goal_oriented_planning_review)")
    print("  4. The three print statements showing results")
    print()
    
    run_test_with_small_steps()