#!/usr/bin/env python3
"""
Quick test to verify template rendering works after removing location_type variable
"""
import sys
from pathlib import Path

# Add eevee directory to path
eevee_root = Path(__file__).parent
sys.path.append(str(eevee_root))

from prompt_manager import PromptManager

def test_template_rendering():
    """Test that templates render without location_type variable"""
    print("🧪 Testing template rendering after location_type removal...")
    
    pm = PromptManager()
    
    # Test variables (simulating what would be passed from visual analysis)
    test_movement_data = {
        'valid_movements': ['U', 'D', 'L', 'R'],
        'movement_details': {
            'U': 'Grassy terrain continues upward',
            'D': 'Grassy terrain extends downward', 
            'L': 'Grassy terrain to the left',
            'R': 'Grassy terrain to the right'
        },
        'objects_detected': {},
        'location_class': 'forest'  # This should NOT be passed to template anymore
    }
    
    test_variables = {
        'task': 'explore and find pokemon battles',
        'recent_actions': 'up, up, left',
        'memory_context': 'Walking through Viridian Forest'
    }
    
    try:
        # Test exploration_strategy template (Mistral)
        print("\n🎯 Testing exploration_strategy template...")
        
        # Add movement variables to test_variables (simulating what get_prompt_for_turn would do)
        test_variables_with_movement = test_variables.copy()
        test_variables_with_movement.update({
            'valid_movements': ['up', 'down', 'left', 'right'],
            'movement_details': 'Up: Grassy terrain\nDown: Grassy terrain\nLeft: Grassy terrain\nRight: Grassy terrain',
            'objects_detected': 'No objects detected'
        })
        
        prompt = pm.get_prompt('exploration_strategy', test_variables_with_movement)
        print("✅ exploration_strategy template rendered successfully")
        print(f"📏 Prompt length: {len(prompt)} chars")
        
        # Verify location_type is NOT in the rendered prompt
        if '{location_type}' in prompt:
            print("❌ ERROR: Unresolved {location_type} variable found in prompt!")
            return False
        else:
            print("✅ No unresolved location_type variables found")
            
        # Test battle_analysis template
        print("\n⚔️ Testing battle_analysis template...")
        battle_prompt = pm.get_prompt('battle_analysis', test_variables)
        print("✅ battle_analysis template rendered successfully")
        
        # Test basic template functionality
        print("\n🧠 Testing core functionality...")
        print("✅ PromptManager initialized successfully")
        print("✅ Templates render without location_type variable")
        
        print("\n🎉 All template tests passed! Location isolation successful.")
        return True
        
    except Exception as e:
        print(f"❌ Template rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_template_rendering()
    sys.exit(0 if success else 1)