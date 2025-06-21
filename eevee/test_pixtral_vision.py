#!/usr/bin/env python3
"""
Diagnostic test to check Pixtral vision processing
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
from llm_api import call_llm
from provider_config import get_model_for_task, get_provider_for_task

def test_pixtral_vision():
    """Test Pixtral's vision capabilities with a simple prompt"""
    print("🔍 Testing Pixtral Vision Processing")
    print("=" * 50)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Create a simple test image (base64 encoded red square)
    # This is a minimal 1x1 red pixel PNG
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    print("📊 Test Configuration:")
    print(f"   Task Type: screenshot_analysis")
    print(f"   Model: {get_model_for_task('screenshot_analysis')}")
    print(f"   Provider: {get_provider_for_task('screenshot_analysis')}")
    
    # Test 1: Simple vision test
    print("\n🧪 Test 1: Simple Vision Test")
    print("-" * 30)
    
    response = call_llm(
        prompt="What do you see in this image? Describe it in one sentence.",
        image_data=test_image_b64,
        model="pixtral-12b-2409",
        provider="mistral",
        max_tokens=100
    )
    
    print(f"Response: {response.text}")
    print(f"Error: {response.error}")
    print(f"Provider used: {response.provider}")
    print(f"Model used: {response.model}")
    
    # Test 2: Pokemon-specific prompt
    print("\n🎮 Test 2: Pokemon Vision Test")
    print("-" * 30)
    
    pokemon_prompt = """You are playing Pokemon. Look at this game screenshot and tell me:
1. What do you see on the screen?
2. What should I press on my Game Boy Advance?

Keep your response short and give me specific button presses like ['a'] or ['up']."""
    
    response = call_llm(
        prompt=pokemon_prompt,
        image_data=test_image_b64,
        model="pixtral-12b-2409",
        provider="mistral",
        max_tokens=200
    )
    
    print(f"Response: {response.text}")
    print(f"Error: {response.error}")
    print(f"Button presses: {response.button_presses}")
    
    # Test 3: Text-only test (for comparison)
    print("\n📝 Test 3: Text-Only Test (for comparison)")
    print("-" * 30)
    
    response = call_llm(
        prompt="You are playing Pokemon. A wild Pidgey appears! What button should you press? Answer with just the button name.",
        model="mistral-large-latest",
        provider="mistral",
        max_tokens=50
    )
    
    print(f"Response: {response.text}")
    print(f"Error: {response.error}")
    print(f"Button presses: {response.button_presses}")
    
    print("\n" + "=" * 50)
    print("🏁 Pixtral Vision Test Complete")

if __name__ == "__main__":
    test_pixtral_vision()