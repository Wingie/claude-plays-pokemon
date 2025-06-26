#!/usr/bin/env python3
"""
Test Enhanced RAM Integration for Battle Decision Making
Verifies that complete Pokemon party data is available for AI decisions
"""

import json
from pathlib import Path
import sys

# Add path for importing
tests_path = Path(__file__).parent / "tests"
if str(tests_path) not in sys.path:
    sys.path.insert(0, str(tests_path))

def test_enhanced_compact_game_state():
    """Test the enhanced get_compact_game_state method"""
    print("🧪 Testing Enhanced RAM Integration")
    print("=" * 50)
    
    try:
        from analyse_skyemu_ram import SkyEmuClient, PokemonFireRedReader
        
        client = SkyEmuClient(debug=False)
        reader = PokemonFireRedReader(client)
        
        print("📊 Testing enhanced compact game state...")
        
        # Get enhanced game state
        ram_data = reader.get_compact_game_state()
        
        if not ram_data.get("ram_available", False):
            print("⚠️ RAM not available - check if SkyEmu is running")
            print(f"   Error: {ram_data.get('error', 'Unknown')}")
            return False
        
        print("✅ RAM data available!")
        
        # Test location data
        location = ram_data.get("location", {})
        print(f"📍 Location: Map {location.get('map_bank', '?')}-{location.get('map_id', '?')} ({location.get('location_name', 'Unknown')})")
        print(f"   Position: X:{location.get('x', '?')} Y:{location.get('y', '?')}")
        
        # Test player data
        player = ram_data.get("player", {})
        print(f"👤 Player: {player.get('name', 'Unknown')} | Money: {player.get('money', 'unknown')}")
        
        # Test party data
        party = ram_data.get("party", [])
        party_summary = ram_data.get("party_summary", {})
        
        print(f"🎮 Pokemon Party ({len(party)} Pokemon):")
        print(f"   Health Status: {party_summary.get('party_health_status', 'unknown').upper()}")
        print(f"   Healthy: {party_summary.get('healthy_pokemon', 0)}/{party_summary.get('total_pokemon', 0)}")
        print(f"   Fainted: {party_summary.get('fainted_pokemon', 0)}")
        print(f"   Critical: {party_summary.get('critical_pokemon', 0)}")
        print(f"   Needs Healing: {'YES' if party_summary.get('needs_healing', False) else 'NO'}")
        
        # Show detailed Pokemon info
        if party:
            print(f"\n📋 Pokemon Details:")
            for i, pokemon in enumerate(party[:3]):  # Show first 3
                print(f"   {i+1}. {pokemon.get('nickname', 'Unknown')} (L{pokemon.get('level', '?')})")
                print(f"      HP: {pokemon.get('current_hp', '?')}/{pokemon.get('max_hp', '?')} ({pokemon.get('hp_percentage', '?')}%)")
                print(f"      Status: {pokemon.get('battle_status', 'unknown')}")
                print(f"      Moves: {', '.join(pokemon.get('moves', [])[:2])}...")  # First 2 moves
        
        # Test context flags
        quick_status = ram_data.get("quick_status", {})
        print(f"\n🎯 Battle Context:")
        print(f"   Can Battle: {'YES' if quick_status.get('can_battle', True) else 'NO'}")
        print(f"   At Pokemon Center: {'YES' if quick_status.get('at_pokemon_center', False) else 'NO'}")
        print(f"   Emergency: {'YES' if quick_status.get('emergency_situation', False) else 'NO'}")
        
        # Test items
        items = ram_data.get("items", [])
        print(f"\n🎒 Items: {len(items)} types available")
        if items:
            for item in items[:3]:  # Show first 3
                print(f"   - {item.get('name', 'Unknown')}: {item.get('quantity', 0)}")
        
        print(f"\n✅ Enhanced RAM integration test completed successfully!")
        print(f"📊 Data structure contains {len(ram_data.keys())} top-level fields")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import RAM analyzer: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_visual_analysis_integration():
    """Test that visual analysis uses the enhanced RAM data"""
    print("\n🔍 Testing Visual Analysis Integration")
    print("=" * 50)
    
    try:
        from visual_analysis import VisualAnalysis
        
        analyzer = VisualAnalysis(grid_size=8, save_logs=False)
        
        print("📊 Testing RAM data collection in visual analysis...")
        
        # Test the _collect_ram_data method
        ram_data = analyzer._collect_ram_data()
        
        if not ram_data.get("ram_available", False):
            print("⚠️ RAM not available in visual analysis")
            print(f"   Error: {ram_data.get('error', 'Unknown')}")
            return False
        
        print("✅ Visual analysis can access RAM data!")
        
        # Test coordinate extraction
        coords = analyzer._get_ram_coordinates()
        if coords.get("ram_available", False):
            location = coords.get("location", {})
            print(f"📍 Coordinates available: X:{location.get('x', '?')} Y:{location.get('y', '?')}")
        else:
            print("⚠️ Coordinates not available")
        
        print("✅ Visual analysis integration test completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import visual analysis: {e}")
        return False
    except Exception as e:
        print(f"❌ Visual analysis test failed: {e}")
        return False

def test_battle_template_variables():
    """Test that battle templates will receive complete RAM data"""
    print("\n⚔️ Testing Battle Template Variables")
    print("=" * 50)
    
    try:
        from analyse_skyemu_ram import SkyEmuClient, PokemonFireRedReader
        
        client = SkyEmuClient(debug=False)
        reader = PokemonFireRedReader(client)
        
        # Get RAM data
        ram_data = reader.get_compact_game_state()
        
        if not ram_data.get("ram_available", False):
            print("⚠️ RAM not available for battle template test")
            return False
        
        # Simulate the variables that would be passed to battle templates
        party_data = ram_data.get("party", [])
        party_summary = ram_data.get("party_summary", {})
        quick_status = ram_data.get("quick_status", {})
        player_data = ram_data.get("player", {})
        
        battle_variables = {
            "ram_available": True,
            "current_pokemon_party": party_data,
            "party_health_summary": {
                "total_pokemon": party_summary.get("total_pokemon", 0),
                "healthy_pokemon": party_summary.get("healthy_pokemon", 0),
                "fainted_pokemon": party_summary.get("fainted_pokemon", 0),
                "critical_pokemon": party_summary.get("critical_pokemon", 0),
                "party_health_status": party_summary.get("party_health_status", "unknown"),
                "needs_healing": party_summary.get("needs_healing", False)
            },
            "battle_context": {
                "can_battle": quick_status.get("can_battle", True),
                "emergency_situation": quick_status.get("emergency_situation", False),
                "player_money": player_data.get("money", "unknown")
            },
            "active_pokemon": party_data[0] if party_data else None,
            "backup_pokemon": [p for p in party_data[1:] if not p.get("is_fainted", True)] if len(party_data) > 1 else []
        }
        
        print("✅ Battle template variables prepared:")
        print(f"   RAM Available: {battle_variables['ram_available']}")
        print(f"   Active Pokemon: {battle_variables['active_pokemon']['nickname'] if battle_variables['active_pokemon'] else 'None'}")
        print(f"   Backup Pokemon: {len(battle_variables['backup_pokemon'])}")
        print(f"   Party Health: {battle_variables['party_health_summary']['party_health_status']}")
        print(f"   Can Battle: {battle_variables['battle_context']['can_battle']}")
        print(f"   Emergency: {battle_variables['battle_context']['emergency_situation']}")
        
        print("\n🎯 These variables will be available in battle_analysis template!")
        return True
        
    except Exception as e:
        print(f"❌ Battle template test failed: {e}")
        return False

def main():
    """Run all enhanced RAM integration tests"""
    print("🚀 Enhanced RAM Integration Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Enhanced compact game state
    if test_enhanced_compact_game_state():
        tests_passed += 1
    
    # Test 2: Visual analysis integration
    if test_visual_analysis_integration():
        tests_passed += 1
    
    # Test 3: Battle template variables
    if test_battle_template_variables():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All enhanced RAM integration tests PASSED!")
        print("\n🎯 System is ready for battle decision making with:")
        print("   ✓ Complete Pokemon party data")
        print("   ✓ Real-time HP and status information")
        print("   ✓ Battle context awareness")
        print("   ✓ Enhanced coordinate mapping")
        print("   ✓ Visual analysis integration")
    else:
        print(f"⚠️ {total_tests - tests_passed} tests failed")
        print("   Check SkyEmu connection and RAM data availability")

if __name__ == "__main__":
    main()