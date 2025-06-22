#!/usr/bin/env python3
"""
Debug the final prompt sent to Pixtral
"""

import os
import sys
from pathlib import Path

# Add project paths
eevee_root = Path(__file__).parent
project_root = eevee_root.parent
sys.path.append(str(project_root))
sys.path.append(str(eevee_root))

from dotenv import load_dotenv
from prompt_manager import PromptManager

def debug_final_prompt():
    """Show the exact prompt being sent to Pixtral"""
    print("🔍 Debugging Final Prompt Structure")
    print("=" * 70)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Create PromptManager
    prompt_manager = PromptManager()
    
    # Generate a battle prompt
    prompt = prompt_manager.get_ai_directed_prompt(
        context_type="battle",
        task="win this pokemon battle",
        recent_actions=["a", "down", "a"],
        memory_context="Pokemon battle with HP bars visible",
        verbose=False
    )
    
    print(f"📝 Full Prompt Length: {len(prompt)} chars")
    print("-" * 70)
    print("🔍 COMPLETE PROMPT BEING SENT TO PIXTRAL:")
    print("-" * 70)
    print(prompt)
    print("-" * 70)
    
    # Analyze structure
    lines = prompt.split('\n')
    has_ash_character = False
    has_first_person = False
    has_documentation_format = False
    
    for line in lines:
        if 'you are ash' in line.lower():
            has_ash_character = True
        if any(phrase in line.lower() for phrase in ['i see', 'i can', 'my pokemon']):
            has_first_person = True
        if line.startswith('#') or line.startswith('##'):
            has_documentation_format = True
    
    print(f"\n📊 PROMPT ANALYSIS:")
    print(f"   Has Ash Character Instructions: {'✅' if has_ash_character else '❌'}")
    print(f"   Has First Person Examples: {'✅' if has_first_person else '❌'}")  
    print(f"   Uses Documentation Format: {'✅' if has_documentation_format else '❌'}")
    
    if has_documentation_format and not has_ash_character:
        print(f"\n⚠️  ISSUE IDENTIFIED:")
        print(f"   The prompt is primarily documentation/guide format")
        print(f"   This may cause Pixtral to respond with documentation instead of roleplay")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    debug_final_prompt()