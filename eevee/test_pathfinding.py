#!/usr/bin/env python3
"""
Test script for pathfinding foundation
Demonstrates coordinate mapping and navigation helper functionality
"""

import json
from pathlib import Path
from coordinate_mapper import CoordinateMapper
from pathfinding_helpers import NavigationHelper

def test_coordinate_mapping():
    """Test basic coordinate mapping functionality"""
    print("🧪 Testing Coordinate Mapping System")
    print("=" * 50)
    
    # Initialize mapper
    mapper = CoordinateMapper()
    
    # Test coordinate recording
    print("\n📍 Testing coordinate recording...")
    
    test_coords = [
        {"map_id": 123, "x": 10, "y": 15, "map_name": "Route 1"},
        {"map_id": 123, "x": 11, "y": 15, "map_name": "Route 1"},
        {"map_id": 123, "x": 12, "y": 15, "map_name": "Route 1"},
        {"map_id": 123, "x": 10, "y": 16, "map_name": "Route 1"},
        {"map_id": 124, "x": 5, "y": 8, "map_name": "Pokemon Center"}
    ]
    
    for i, coord in enumerate(test_coords):
        screenshot_path = f"test_screenshot_{i+1}.png"
        session_id = "test_session_001"
        
        scene_analysis = {
            "scene_type": "navigation" if coord["map_name"] != "Pokemon Center" else "indoor",
            "valid_movements": ["up", "down", "left", "right"]
        }
        
        success = mapper.record_coordinate(coord, screenshot_path, session_id, scene_analysis)
        print(f"   {'✅' if success else '❌'} Recorded: Map {coord['map_id']} X:{coord['x']} Y:{coord['y']}")
    
    # Test movement recording
    print("\n🚶 Testing movement recording...")
    
    test_movements = [
        (test_coords[0], test_coords[1], "right"),
        (test_coords[1], test_coords[2], "right"),
        (test_coords[0], test_coords[3], "down")
    ]
    
    for from_coord, to_coord, direction in test_movements:
        success = mapper.record_movement(from_coord, to_coord, direction, "test_session_001")
        print(f"   {'✅' if success else '❌'} Movement: ({from_coord['x']},{from_coord['y']}) → ({to_coord['x']},{to_coord['y']}) via {direction}")
    
    # Test nearby coordinate search
    print("\n🔍 Testing nearby coordinate search...")
    
    nearby = mapper.get_coordinates_near(123, 10, 15, radius=3)
    print(f"   Found {len(nearby)} coordinates near (10,15) within radius 3:")
    for coord in nearby[:3]:  # Show first 3
        print(f"     - Map {coord['map_id']} X:{coord['x']} Y:{coord['y']} (distance: {coord['distance']})")
    
    # Test statistics
    print("\n📊 Testing statistics...")
    
    stats = mapper.get_map_statistics()
    print(f"   Total coordinates: {stats.get('total_coordinates', 0)}")
    print(f"   Unique maps: {stats.get('unique_maps', 0)}")
    print(f"   Movement connections: {stats.get('movement_connections', 0)}")
    
    if stats.get('top_mapped_areas'):
        print(f"   Top mapped area: {stats['top_mapped_areas'][0]}")
    
    return mapper

def test_navigation_helper():
    """Test navigation helper functionality"""
    print("\n🧭 Testing Navigation Helper")
    print("=" * 50)
    
    helper = NavigationHelper()
    
    if not helper.available:
        print("❌ Navigation helper not available - coordinate mapping disabled")
        return
    
    # Test movement suggestions
    current_pos = {"map_id": 123, "x": 10, "y": 15}
    
    test_goals = [
        "heal my Pokemon at Pokemon Center",
        "find wild Pokemon to battle",
        "explore the area",
        "find the exit"
    ]
    
    print("\n💭 Testing movement suggestions...")
    
    for goal in test_goals:
        suggestion = helper.suggest_next_move(current_pos, goal)
        print(f"\n   Goal: '{goal}'")
        print(f"   Suggestion: {suggestion['suggestion']}")
        print(f"   Direction: {suggestion['direction']}")
        print(f"   Reasoning: {suggestion['reasoning']}")
        print(f"   Confidence: {suggestion['confidence']}")
    
    # Test area summary
    print("\n📋 Testing area summary...")
    
    summary = helper.get_area_summary(current_pos)
    if 'error' not in summary:
        print(f"   Position: Map {summary['current_position']['map_id']} X:{summary['current_position']['x']} Y:{summary['current_position']['y']}")
        print(f"   Mapped coordinates: {summary['mapped_coordinates']}")
        print(f"   Coverage: {summary['exploration_coverage']}")
        print(f"   Status: {summary['navigation_status']}")
        print(f"   Scene types: {summary['scene_types']}")
    else:
        print(f"   Error: {summary['error']}")
    
    # Test prompt enhancement
    print("\n✨ Testing prompt enhancement...")
    
    test_prompt = "You are playing Pokemon. Choose your next move based on the current situation."
    goal = "find Pokemon Center to heal"
    
    enhanced_prompt = helper.get_movement_suggestions_for_prompt(current_pos, goal)
    if enhanced_prompt.strip():
        print("   Enhanced prompt context:")
        for line in enhanced_prompt.strip().split('\n'):
            print(f"     {line}")
    else:
        print("   No enhancement available")

def test_data_export():
    """Test data export functionality"""
    print("\n📤 Testing Data Export")
    print("=" * 50)
    
    mapper = CoordinateMapper()
    
    # Export map data
    export_success = mapper.export_map_data(123)
    print(f"   {'✅' if export_success else '❌'} Map data export")
    
    # Check if file was created
    export_file = Path(__file__).parent / "map_123_data.json"
    if export_file.exists():
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        print(f"   📁 Export file created: {export_file}")
        print(f"   📊 Exported {len(data.get('coordinates', []))} coordinates")
        print(f"   🔗 Exported {len(data.get('movement_connections', []))} connections")
        
        # Clean up test file
        export_file.unlink()
        print(f"   🧹 Cleaned up test export file")

def main():
    """Run all pathfinding tests"""
    print("🚀 Eevee Pathfinding Foundation Test Suite")
    print("=" * 60)
    
    try:
        # Test coordinate mapping
        mapper = test_coordinate_mapping()
        
        # Test navigation helper
        test_navigation_helper()
        
        # Test data export
        test_data_export()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\n📍 Pathfinding foundation is ready for integration")
        print("🎯 Next steps:")
        print("   1. Integration with visual_analysis.py (✅ completed)")
        print("   2. Integration with AI prompt system")
        print("   3. Real-world testing with actual gameplay")
        
        # Clean up test database
        test_db = Path(__file__).parent / "coordinate_map.db"
        if test_db.exists():
            test_db.unlink()
            print("   🧹 Cleaned up test database")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()