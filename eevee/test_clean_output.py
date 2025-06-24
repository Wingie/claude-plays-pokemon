#!/usr/bin/env python3
"""
Test the clean console output with flexible schema
"""

import sys
from pathlib import Path

# Add eevee directory to path
eevee_dir = Path(__file__).parent
sys.path.append(str(eevee_dir))

from visual_analysis import VisualAnalysis

def test_clean_output():
    """Test clean console output with flexible data"""
    va = VisualAnalysis()
    
    # Mock flexible battle data
    flexible_battle_data = {
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
        "confidence": "high",
        # Internal fields that should be filtered out
        "raw_pixtral_response": "long response...",
        "valid_movements": ["up", "down"],
        "spatial_context": "Scene: battle, Valid buttons: 2",
        "template_reason": "Scene type 'battle' → template 'ai_directed_battle'"
    }
    
    print("Testing clean console output for flexible battle scene:")
    print("=" * 60)
    va._log_clean_console_output(flexible_battle_data)
    
    print("\nTesting clean console output for flexible menu scene:")
    print("=" * 60)
    flexible_menu_data = {
        "scene_type": "menu",
        "menu_type": "pokedex",
        "pokemon_entry": {"name": "PIKACHU", "number": "025"},
        "description_text": "Electric mouse Pokemon",
        "valid_buttons": [
            {"key": "←", "action": "previous_entry", "result": "show_pokemon_024"}
        ],
        "recommended_template": "ai_directed_navigation",
        "confidence": "high",
        # Internal fields that should be filtered out
        "raw_pixtral_response": "long response...",
        "spatial_context": "Scene: menu, Valid buttons: 1"
    }
    
    va._log_clean_console_output(flexible_menu_data)

if __name__ == "__main__":
    test_clean_output()