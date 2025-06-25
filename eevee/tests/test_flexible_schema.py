#!/usr/bin/env python3
"""
Test script to verify flexible JSON schema implementation
"""

import sys
import os
from pathlib import Path

# Add eevee directory to path
eevee_dir = Path(__file__).parent
sys.path.append(str(eevee_dir))

from visual_analysis import VisualAnalysis

def test_flexible_parsing():
    """Test the new flexible parsing logic"""
    va = VisualAnalysis()
    
    # Test 1: Battle scene with flexible structure
    print("=== TEST 1: Flexible Battle Scene ===")
    battle_response = """```json
{
  "scene_type": "battle",
  "our_pokemon": {"name": "PIKACHU", "hp": "22/35", "level": 12},
  "enemy_pokemon": {"name": "RATTATA", "level": 8},
  "battle_phase": "move_selection",
  "cursor_on": "THUNDERBOLT",
  "valid_buttons": [
    {"key": "A", "action": "select_move", "result": "use_thunderbolt"},
    {"key": "↓", "action": "cursor_down", "result": "select_next_move"}
  ],
  "recommended_template": "ai_directed_battle",
  "confidence": "high"
}
```"""
    
    result = va._parse_movement_response(battle_response)
    print("Core fields:")
    print(f"  scene_type: {result.get('scene_type')}")
    print(f"  recommended_template: {result.get('recommended_template')}")
    print(f"  confidence: {result.get('confidence')}")
    print(f"  valid_buttons: {len(result.get('valid_buttons', []))} buttons")
    
    print("Dynamic fields:")
    print(f"  our_pokemon: {result.get('our_pokemon')}")
    print(f"  enemy_pokemon: {result.get('enemy_pokemon')}")
    print(f"  battle_phase: {result.get('battle_phase')}")
    print(f"  cursor_on: {result.get('cursor_on')}")
    
    # Test 2: Menu scene with different structure
    print("\n=== TEST 2: Flexible Menu Scene ===")
    menu_response = """```json
{
  "scene_type": "menu",
  "menu_type": "pokedex",
  "pokemon_entry": {"name": "PIKACHU", "number": "025"},
  "description_text": "Electric mouse Pokemon",
  "valid_buttons": [
    {"key": "←", "action": "previous_entry", "result": "show_pokemon_024"},
    {"key": "→", "action": "next_entry", "result": "show_pokemon_026"}
  ],
  "recommended_template": "ai_directed_navigation",
  "confidence": "high"
}
```"""
    
    result = va._parse_movement_response(menu_response)
    print("Core fields:")
    print(f"  scene_type: {result.get('scene_type')}")
    print(f"  recommended_template: {result.get('recommended_template')}")
    print(f"  confidence: {result.get('confidence')}")
    
    print("Dynamic fields:")
    print(f"  menu_type: {result.get('menu_type')}")
    print(f"  pokemon_entry: {result.get('pokemon_entry')}")
    print(f"  description_text: {result.get('description_text')}")
    
    # Test 3: Verify backward compatibility fields still work
    print("\n=== TEST 3: Backward Compatibility ===")
    print(f"  valid_movements: {result.get('valid_movements')}")
    print(f"  spatial_context: {result.get('spatial_context')}")
    print(f"  character_position: {result.get('character_position')}")
    print(f"  template_reason: {result.get('template_reason')}")
    
    print("\n✅ Flexible schema parsing test completed!")

if __name__ == "__main__":
    test_flexible_parsing()