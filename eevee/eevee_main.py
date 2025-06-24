#!/usr/bin/env python3
"""
Eevee - AI Pokemon Analysis System
Phase 1: Game State Analysis and Awareness

This script connects to a running Pokemon game and performs systematic analysis tasks:
- Pokemon party verification (levels, moves, items)
- Map and location awareness
- Environmental analysis (NPCs, items, etc.)
- Task-based conditional analysis
"""

import os
import sys
import time
import json
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    from pokemon_controller import PokemonController, read_image_to_base64
    from llm_api import call_llm
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running from the correct environment with dependencies installed")
    sys.exit(1)

# Load environment variables
load_dotenv()

class EeveeAnalyzer:
    """Main Eevee AI system for Pokemon game analysis"""
    
    def __init__(self, window_title="mGBA - 0.10.5"):
        """Initialize Eevee with game connection and AI"""
        self.window_title = window_title
        
        # LLM API is initialized globally via call_llm()
        # No local initialization needed
        self.controller = PokemonController(window_title=window_title)
        
        # Create analysis directory
        self.analysis_dir = Path(__file__).parent / "analysis"
        self.analysis_dir.mkdir(exist_ok=True)
        
        print(f"🔮 Eevee initialized - looking for window: {window_title}")
        
    def capture_and_analyze(self, task_description="general analysis"):
        """Capture current game screen and analyze with AI"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_file = self.controller.capture_screen(f"eevee_screen_{timestamp}.jpg")
        
        # Move screenshot to analysis directory
        analysis_screenshot = self.analysis_dir / f"screen_{timestamp}.jpg"
        os.rename(screenshot_file, analysis_screenshot)
        
        # Read image for AI analysis
        image_data = read_image_to_base64(analysis_screenshot)
        
        return image_data, analysis_screenshot, timestamp
    
    def analyze_pokemon_party(self):
        """Analyze current Pokemon party - levels, moves, items"""
        print("🎮 Analyzing Pokemon Party...")
        
        # First, try to access the Pokemon menu
        self.controller.press_button('start')  # Open main menu
        time.sleep(1)
        
        image_data, screenshot_path, timestamp = self.capture_and_analyze("pokemon party analysis")
        
        party_prompt = """Analyze this Pokemon game screen and provide detailed information about the Pokemon party.

Look for:
1. **Pokemon Party Status**: Are we in the Pokemon menu? If not, describe what's on screen
2. **Pokemon List**: Name each Pokemon visible and their levels
3. **Health Status**: Current HP vs Max HP for each Pokemon
4. **Status Conditions**: Any status effects (poison, sleep, etc.)
5. **Active Pokemon**: Which Pokemon is currently selected/active
6. **Party Size**: How many Pokemon are in the party

If this is not the Pokemon menu, describe what menu or screen we're currently viewing and suggest how to navigate to the Pokemon party screen.

Format your response as a clear analysis with sections for each point above."""

        try:
            response = call_llm(
                prompt=party_prompt,
                image_data=image_data,
                max_tokens=1000,
                model="gemini-2.0-flash-exp",
                provider="gemini"
            )
            
            analysis = response.text if response.text else "No analysis generated"
            
            # Save analysis
            analysis_file = self.analysis_dir / f"party_analysis_{timestamp}.txt"
            with open(analysis_file, 'w') as f:
                f.write(f"Pokemon Party Analysis - {timestamp}\n")
                f.write("=" * 50 + "\n\n")
                f.write(analysis)
            
            print(f"📝 Party analysis saved to: {analysis_file}")
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing party: {e}")
            return None
    
    def analyze_location_and_map(self):
        """Analyze current location, map, and surroundings"""
        print("🗺️  Analyzing Location and Map...")
        
        # Return to main game view if we're in menus
        self.controller.press_button('b')  # Close any open menus
        time.sleep(1)
        
        image_data, screenshot_path, timestamp = self.capture_and_analyze("location and map analysis")
        
        location_prompt = """Analyze this Pokemon game screen for location and environmental information.

Provide detailed analysis of:

1. **Current Location**: 
   - What area/route/town are we in?
   - Indoor or outdoor environment?
   - Any visible location names or signs?

2. **Player Position**: 
   - Where is the player character on screen?
   - What direction are they facing?

3. **Map Features**:
   - Terrain type (grass, water, buildings, paths)
   - Notable landmarks or structures
   - Available exits/entrances

4. **NPCs and Characters**:
   - How many people/trainers are visible?
   - What are they doing? (standing, walking, etc.)
   - Any important NPCs (Gym Leaders, Team members, etc.)?

5. **Items and Interactables**:
   - Any visible items on the ground?
   - Objects that can be interacted with?
   - Signs, doors, or other interactive elements?

6. **Immediate Opportunities**:
   - Battles available?
   - Items to collect?
   - Areas to explore?

Format as a structured analysis with clear sections."""

        try:
            response = call_llm(
                prompt=location_prompt,
                image_data=image_data,
                max_tokens=1000,
                model="gemini-2.0-flash-exp",
                provider="gemini"
            )
            
            analysis = response.text if response.text else "No analysis generated"
            
            # Save analysis
            analysis_file = self.analysis_dir / f"location_analysis_{timestamp}.txt"
            with open(analysis_file, 'w') as f:
                f.write(f"Location & Map Analysis - {timestamp}\n")
                f.write("=" * 50 + "\n\n") 
                f.write(analysis)
            
            print(f"📝 Location analysis saved to: {analysis_file}")
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing location: {e}")
            return None
    
    def perform_custom_task(self, task_description):
        """Perform a custom analysis task based on description"""
        print(f"🎯 Performing custom task: {task_description}")
        
        image_data, screenshot_path, timestamp = self.capture_and_analyze(task_description)
        
        custom_prompt = f"""Analyze this Pokemon game screen for the following specific task:

TASK: {task_description}

Provide a detailed analysis focused specifically on this task. Look carefully at the screen and provide relevant information that addresses the task requirements.

If the current screen doesn't show information relevant to this task, suggest what actions might be needed to gather the required information."""

        try:
            response = call_llm(
                prompt=custom_prompt,
                image_data=image_data,
                max_tokens=1000,
                model="gemini-2.0-flash-exp",
                provider="gemini"
            )
            
            analysis = response.text if response.text else "No analysis generated"
            
            # Save analysis
            safe_task_name = "".join(c for c in task_description if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            analysis_file = self.analysis_dir / f"custom_task_{safe_task_name}_{timestamp}.txt"
            with open(analysis_file, 'w') as f:
                f.write(f"Custom Task Analysis - {timestamp}\n")
                f.write(f"Task: {task_description}\n") 
                f.write("=" * 50 + "\n\n")
                f.write(analysis)
            
            print(f"📝 Custom task analysis saved to: {analysis_file}")
            return analysis
            
        except Exception as e:
            print(f"❌ Error performing custom task: {e}")
            return None
    
    def daily_memory_routine(self):
        """Perform the daily memory routine - verify Pokemon, levels, moves, items, and map"""
        print("🌅 Starting Daily Memory Routine...")
        
        routine_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        routine_file = self.analysis_dir / f"daily_routine_{routine_timestamp}.txt"
        
        with open(routine_file, 'w') as f:
            f.write(f"EEVEE DAILY MEMORY ROUTINE\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            # 1. Pokemon Party Analysis
            f.write("1. POKEMON PARTY ANALYSIS\n")
            f.write("-" * 30 + "\n")
            party_analysis = self.analyze_pokemon_party()
            if party_analysis:
                f.write(party_analysis + "\n\n")
            else:
                f.write("Failed to analyze Pokemon party\n\n")
            
            time.sleep(2)
            
            # 2. Location and Map Analysis  
            f.write("2. LOCATION & MAP ANALYSIS\n")
            f.write("-" * 30 + "\n")
            location_analysis = self.analyze_location_and_map()
            if location_analysis:
                f.write(location_analysis + "\n\n")
            else:
                f.write("Failed to analyze location and map\n\n")
            
            f.write(f"Routine completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"📋 Daily routine completed - full report saved to: {routine_file}")
        return routine_file

def main():
    """Main Eevee execution"""
    print("🔮 EEVEE - AI Pokemon Analysis System")
    print("Phase 1: Game State Analysis and Awareness")
    print("=" * 50)
    
    try:
        # Initialize Eevee
        eevee = EeveeAnalyzer()
        
        # Check if game window is available
        window = eevee.controller.find_window()
        if not window:
            print("⚠️  Warning: Pokemon game window not found")
            print(f"Make sure the game is running with window title: {eevee.window_title}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
        
        print("\n🎮 Game connection established!")
        
        # Main interaction loop
        while True:
            print("\n" + "=" * 50)
            print("EEVEE ANALYSIS OPTIONS:")
            print("1. Daily Memory Routine (Pokemon + Location analysis)")
            print("2. Analyze Pokemon Party")
            print("3. Analyze Location & Map") 
            print("4. Custom Task Analysis")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                eevee.daily_memory_routine()
                
            elif choice == '2':
                eevee.analyze_pokemon_party()
                
            elif choice == '3':
                eevee.analyze_location_and_map()
                
            elif choice == '4':
                task = input("Enter custom task description: ").strip()
                if task:
                    eevee.perform_custom_task(task)
                    
            elif choice == '5':
                print("👋 Eevee signing off!")
                break
                
            else:
                print("❌ Invalid option, please try again")
                
    except KeyboardInterrupt:
        print("\n👋 Eevee interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()