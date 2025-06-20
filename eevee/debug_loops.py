#!/usr/bin/env python3
"""
Quick debug script to check for loop patterns in recent runs
Usage: python debug_loops.py
"""

import os
import json
from pathlib import Path
from datetime import datetime

def analyze_recent_runs():
    """Analyze recent run data for loop patterns"""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        print("No runs directory found")
        return
    
    # Get most recent run directory
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        print("No run directories found")
        return
    
    latest_run = max(run_dirs, key=lambda x: x.name)
    print(f"📁 Analyzing latest run: {latest_run.name}")
    
    # Check for session data
    session_file = latest_run / "session_data.json"
    if session_file.exists():
        with open(session_file, 'r') as f:
            data = json.load(f)
            
        # Analyze action patterns
        if "actions_taken" in data:
            actions = data["actions_taken"]
            print(f"\n🎮 Total actions: {len(actions)}")
            
            # Find consecutive patterns
            consecutive_count = 1
            last_action = None
            max_consecutive = 0
            current_consecutive = 1
            
            for i, action in enumerate(actions):
                if action == last_action:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    if current_consecutive > 2:
                        print(f"🔄 Found {current_consecutive} consecutive '{last_action}' at position {i-current_consecutive}")
                    current_consecutive = 1
                last_action = action
            
            print(f"⚠️  Max consecutive same action: {max_consecutive}")
            
            # Show last 10 actions
            print(f"\n📋 Last 10 actions: {actions[-10:] if len(actions) >= 10 else actions}")
    
    # Check for progress summary
    progress_file = latest_run / "progress_summary.md"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            content = f.read()
            if "stuck" in content.lower() or "loop" in content.lower():
                print(f"\n⚠️  Progress summary mentions loops/stuck:")
                print(content[-200:])  # Show last 200 chars

if __name__ == "__main__":
    analyze_recent_runs()