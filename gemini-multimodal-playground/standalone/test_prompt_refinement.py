#!/usr/bin/env python3
"""
Test script for the prompt refinement functionality.
This script demonstrates how the Gemini critique works to refine prompts
based on recent gameplay.
"""

import os
import sys
from dotenv import load_dotenv
from gamememory import Neo4jMemory
from gemini_critique import GeminiCritique

# Load environment variables
load_dotenv()

def test_prompt_refinement():
    """Test the prompt refinement functionality"""
    
    # Initialize Neo4j memory
    current_objective = "Find the Professor"
    memory = Neo4jMemory(current_objective)
    
    # Create a sample base prompt
    base_prompt = {
        "content": """
# Pokemon Game Agent Guide

You are playing Pokémon FireRed on a Game Boy Advance emulator. Your current objective is to navigate through the game world.

## CONTROLS
- Up/Down/Left/Right: Move your character
- A: Interact/Confirm
- B: Cancel/Back
- Start: Open main menu

## BASIC GAMEPLAY
1. Use directional buttons to navigate
2. Press A to talk to NPCs and interact with objects
3. Follow the main story objectives
        """
    }
    
    # Print the base prompt for comparison
    print("\n===== BASE PROMPT =====")
    print(base_prompt["content"])
    
    # Get the memory summary from Neo4j
    memory_summary = memory.recent_turns_summary()
    print("\n===== RECENT TURNS SUMMARY =====")
    print(memory_summary)
    
    # Refine the prompt using Gemini critique
    print("\n===== REFINING PROMPT... =====")
    updated_prompt = memory.get_updated_prompt(base_prompt, current_objective)
    
    # Print the updated prompt
    print("\n===== UPDATED PROMPT =====")
    print(updated_prompt["content"])
    
    print("\n===== DONE =====")
    memory.close()

if __name__ == "__main__":
    try:
        test_prompt_refinement()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
