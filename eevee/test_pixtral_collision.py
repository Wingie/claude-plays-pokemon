#!/usr/bin/env python3
"""
Test the improved Pokemon-specific Pixtral visual analysis prompts
"""
import sys
from pathlib import Path

# Add eevee directory to path
eevee_root = Path(__file__).parent
sys.path.append(str(eevee_root))
project_root = eevee_root.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

from visual_analysis import VisualAnalysis
import time

def test_pokemon_collision_analysis():
    """Test the new Pokemon-specific collision detection prompts"""
    print("🧪 Testing improved Pokemon collision analysis...")
    
    try:
        # Initialize visual analysis with new prompts
        va = VisualAnalysis(grid_size=8, save_logs=True)
        
        print("\n📸 Capturing current game state...")
        
        # Get current screenshot analysis
        result = va.analyze_movement(verbose=True, save_analysis=True)
        
        print(f"\n🎯 ANALYSIS RESULTS:")
        print(f"   Location Class: {result.get('location_class', 'unknown')}")
        print(f"   Valid Movements: {result.get('valid_movements', [])}")
        
        # Check if Pixtral is now recognizing Pokemon terrain types
        movement_details = result.get('movement_details', {})
        print(f"\n🗺️ TERRAIN ANALYSIS:")
        for direction, details in movement_details.items():
            print(f"   {direction}: {details}")
        
        # Look for Pokemon-specific terminology in the analysis
        raw_response = result.get('raw_pixtral_response', '')
        pokemon_indicators = [
            'tree sprites', 'grass paths', 'walkable grass', 'blocked',
            'pokemon', 'trainer', 'building', 'forest', 'route'
        ]
        
        found_indicators = []
        for indicator in pokemon_indicators:
            if indicator.lower() in raw_response.lower():
                found_indicators.append(indicator)
        
        print(f"\n🎮 POKEMON CONTEXT RECOGNITION:")
        if found_indicators:
            print(f"   ✅ Pokemon-specific terms detected: {', '.join(found_indicators)}")
        else:
            print(f"   ⚠️ No Pokemon-specific terminology found")
        
        # Check for collision understanding
        collision_awareness = [
            'WALKABLE', 'BLOCKED', 'collision', 'tree sprites', 'cannot walk'
        ]
        
        collision_found = []
        for term in collision_awareness:
            if term in raw_response:
                collision_found.append(term)
        
        print(f"\n🚫 COLLISION AWARENESS:")
        if collision_found:
            print(f"   ✅ Collision detection terms found: {', '.join(collision_found)}")
            print(f"   ✅ Pixtral understands Pokemon terrain blocking rules")
        else:
            print(f"   ❌ No collision detection terminology found")
        
        # Save detailed analysis
        timestamp = int(time.time())
        analysis_file = va.runs_dir / f"pokemon_collision_test_{timestamp}.txt"
        
        with open(analysis_file, 'w') as f:
            f.write("POKEMON COLLISION ANALYSIS TEST RESULTS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Location Class: {result.get('location_class', 'unknown')}\n")
            f.write(f"Valid Movements: {result.get('valid_movements', [])}\n\n")
            f.write("TERRAIN ANALYSIS:\n")
            for direction, details in movement_details.items():
                f.write(f"  {direction}: {details}\n")
            f.write(f"\nPokemon Terms Found: {', '.join(found_indicators)}\n")
            f.write(f"Collision Terms Found: {', '.join(collision_found)}\n\n")
            f.write("RAW PIXTRAL RESPONSE:\n")
            f.write("-" * 30 + "\n")
            f.write(raw_response)
        
        print(f"\n📄 Detailed analysis saved to: {analysis_file}")
        
        # Overall assessment
        if found_indicators and collision_found:
            print(f"\n🎉 SUCCESS: Pixtral now understands Pokemon collision rules!")
            return True
        elif found_indicators:
            print(f"\n⚠️ PARTIAL: Pokemon context recognized, but collision rules unclear")
            return False
        else:
            print(f"\n❌ FAILURE: Pixtral still using generic terrain analysis")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pokemon_collision_analysis()
    sys.exit(0 if success else 1)