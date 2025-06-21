#!/usr/bin/env python3
"""
Test the actual prompt system used during gameplay
"""

import os
import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

project_root = eevee_root.parent
sys.path.append(str(eevee_root))

from dotenv import load_dotenv
from prompt_manager import PromptManager

def test_actual_gameplay_prompts():
    """Test the actual prompts used during gameplay"""
    print("🔍 Testing Actual Gameplay Prompt System")
    print("=" * 70)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Create PromptManager 
    prompt_manager = PromptManager()
    
    # Test different context types that might lead to code generation
    test_contexts = [
        ("auto_select", "battle context"),
        ("auto_select", "exploration context"), 
        ("auto_select", "stuck in menu"),
        ("auto_select", "Pokemon battle expert playbook"),
        ("battle", "wild pokemon appeared"),
        ("navigation", "exploring viridian forest")
    ]
    
    for context_type, memory_context in test_contexts:
        print(f"\n🎮 Testing Context: '{context_type}' with memory: '{memory_context}'")
        print("-" * 60)
        
        try:
            prompt = prompt_manager.get_ai_directed_prompt(
                context_type=context_type,
                task="test new task mapping system",
                recent_actions=["up", "up", "a"],
                available_memories=["viridian_forest", "pokemon_center"],
                memory_context=memory_context,
                verbose=True
            )
            
            print(f"📝 Generated Prompt Length: {len(prompt)} chars")
            
            # Check for problematic content
            has_code_instructions = any(keyword in prompt.lower() for keyword in [
                'python', 'pygame', 'import', 'def ', 'class ', 'javascript'
            ])
            
            has_character_context = any(keyword in prompt.lower() for keyword in [
                'ash ketchum', 'you are ash', 'pikachu', 'pokemon master'
            ])
            
            has_response_format = any(keyword in prompt.lower() for keyword in [
                'observation:', 'analysis:', 'action:', 'game boy advance'
            ])
            
            print(f"🚨 Contains Code Instructions: {'❌ YES' if has_code_instructions else '✅ NO'}")
            print(f"🎭 Has Character Context: {'✅ YES' if has_character_context else '❌ NO'}")  
            print(f"📋 Has Response Format: {'✅ YES' if has_response_format else '❌ NO'}")
            
            # Show first 300 chars of prompt
            print(f"\n🔍 PROMPT PREVIEW:")
            preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
            print(preview)
            
            # Look for specific problematic patterns
            if "pokemon battle expert playbook" in prompt.lower():
                print("⚠️  WARNING: Found 'Pokemon Battle Expert Playbook' - this might trigger code generation!")
            
        except Exception as e:
            print(f"❌ Error generating prompt: {e}")
        
        print("-" * 60)
    
    print("\n" + "=" * 70)
    print("🏁 Actual Gameplay Prompt Test Complete")

if __name__ == "__main__":
    test_actual_gameplay_prompts()