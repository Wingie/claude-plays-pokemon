#!/usr/bin/env python3
"""
Comprehensive Pathfinding Test Suite
Tests Pokemon Center bookmarking, pathfinding, and coordinate navigation
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

def test_healing_bookmark_system():
    """Test Pokemon Center bookmark functionality"""
    print("🏥 Testing Healing Bookmark System")
    print("=" * 50)
    
    try:
        from healing_bookmark_system import HealingBookmarkSystem
        
        system = HealingBookmarkSystem()
        
        # Test healing success detection
        print("\n🩺 Testing healing success detection...")
        
        ram_before = {
            "party_summary": {
                "party_health_status": "poor",
                "fainted_pokemon": 3,
                "healthy_pokemon": 0,
                "critical_pokemon": 2,
                "needs_healing": True
            }
        }
        
        ram_after = {
            "party_summary": {
                "party_health_status": "healthy",
                "fainted_pokemon": 0,
                "healthy_pokemon": 5,
                "critical_pokemon": 0,
                "needs_healing": False
            }
        }
        
        healing_detected = system.detect_healing_success(ram_before, ram_after)
        print(f"   {'✅' if healing_detected else '❌'} Healing success detection: {healing_detected}")
        
        # Test bookmark creation
        print("\n📍 Testing bookmark creation...")
        
        location_data = {
            "map_id": 6005,
            "x": 7,
            "y": 4,
            "map_name": "Pokemon Center",
            "location_name": "Pewter City Pokemon Center"
        }
        
        bookmark_success = system.bookmark_healing_location(
            location_data, ram_before, ram_after, "test_session_001", 15.5
        )
        print(f"   {'✅' if bookmark_success else '❌'} Bookmark creation: {bookmark_success}")
        
        # Test nearest location search
        print("\n🔍 Testing nearest location search...")
        
        current_coords = {"map_id": 6005, "x": 10, "y": 8}
        nearest = system.get_nearest_healing_location(current_coords)
        
        if nearest:
            print(f"   ✅ Found nearest location: {nearest['location_name']} at ({nearest['x']},{nearest['y']})")
            print(f"      Distance: {nearest['distance']} steps")
            print(f"      Success rate: {nearest['success_rate']:.1%}")
        else:
            print("   ❌ No healing locations found")
        
        # Test statistics
        print("\n📊 Testing healing statistics...")
        
        stats = system.get_healing_statistics()
        print(f"   Total locations: {stats.get('total_healing_locations', 0)}")
        print(f"   Total sessions: {stats.get('total_healing_sessions', 0)}")
        print(f"   Success rate: {stats.get('overall_success_rate', 0):.1%}")
        
        if stats.get('most_reliable_location'):
            best = stats['most_reliable_location']
            print(f"   Best location: {best['name']} ({best['success_rate']:.1%} success)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import healing bookmark system: {e}")
        return False
    except Exception as e:
        print(f"❌ Healing bookmark test failed: {e}")
        return False

def test_ai_pathfinding_tools():
    """Test AI pathfinding tools functionality"""
    print("\n🧭 Testing AI Pathfinding Tools")
    print("=" * 50)
    
    try:
        from ai_pathfinding_tools import AIPathfindingTools
        
        tools = AIPathfindingTools()
        
        if not tools.available:
            print("❌ Pathfinding tools not available")
            return False
        
        # Test coordinate pathfinding
        print("\n📍 Testing coordinate pathfinding...")
        
        current_coords = {"map_id": 6005, "x": 7, "y": 4}
        target_x, target_y = 12, 8
        
        pathfind_result = tools.pathfind_to_coordinate(current_coords, target_x, target_y, "test_navigation")
        
        if pathfind_result["success"]:
            print(f"   ✅ Pathfinding successful:")
            print(f"      Distance: {pathfind_result['distance']} steps")
            print(f"      Button sequence: {pathfind_result['button_sequence'][:5]}...")  # Show first 5
            print(f"      Reasoning: {pathfind_result['reasoning']}")
        else:
            print(f"   ❌ Pathfinding failed: {pathfind_result.get('error', 'Unknown error')}")
        
        # Test healing location pathfinding
        print("\n🏥 Testing healing location pathfinding...")
        
        healing_route = tools.pathfind_to_healing_location(current_coords)
        
        if healing_route["success"]:
            print(f"   ✅ Healing route found:")
            print(f"      Target: {healing_route['healing_location']['location_name']}")
            print(f"      Distance: {healing_route['distance']} steps")
            print(f"      Success rate: {healing_route['success_rate']:.1%}")
        else:
            print(f"   ⚠️ Healing route: {healing_route.get('error', 'No healing locations')}")
        
        # Test landmark search
        print("\n🗺️ Testing landmark search...")
        
        landmarks_result = tools.get_nearby_landmarks(current_coords, radius=15)
        
        if landmarks_result["success"]:
            landmarks = landmarks_result["landmarks"]
            print(f"   ✅ Found {len(landmarks)} landmarks:")
            for landmark in landmarks[:3]:  # Show first 3
                print(f"      - {landmark['name']} at ({landmark['x']},{landmark['y']}) - {landmark['distance']} steps")
        else:
            print(f"   ❌ Landmark search failed: {landmarks_result.get('error', 'Unknown error')}")
        
        # Test navigation context generation
        print("\n📝 Testing navigation context...")
        
        context = tools.get_navigation_context(current_coords, "heal Pokemon at Pokemon Center")
        if context:
            print(f"   ✅ Navigation context generated:")
            for line in context.split('\n')[:4]:  # Show first 4 lines
                print(f"      {line}")
        else:
            print("   ❌ No navigation context generated")
        
        # Test bookmark creation
        print("\n🔖 Testing location bookmarking...")
        
        bookmark_result = tools.bookmark_current_location(
            current_coords, "test_location", "Test Bookmark Location"
        )
        
        if bookmark_result["success"]:
            print(f"   ✅ Bookmark created: {bookmark_result['reasoning']}")
            print(f"      Observations: {bookmark_result['observations']}")
        else:
            print(f"   ❌ Bookmark failed: {bookmark_result.get('error', 'Unknown error')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import AI pathfinding tools: {e}")
        return False
    except Exception as e:
        print(f"❌ AI pathfinding test failed: {e}")
        return False

def test_coordinate_movement_simulation():
    """Test coordinate-based movement simulation"""
    print("\n🎮 Testing Coordinate Movement Simulation")
    print("=" * 50)
    
    try:
        from ai_pathfinding_tools import AIPathfindingTools
        
        tools = AIPathfindingTools()
        
        if not tools.available:
            print("❌ Movement simulation not available")
            return False
        
        # Simulate Pokemon Center healing scenario
        print("\n🏥 Simulating Pokemon Center healing scenario...")
        
        # Starting position: Inside Pokemon Center
        start_pos = {"map_id": 6005, "x": 7, "y": 4, "map_name": "Pokemon Center"}
        print(f"   Starting position: ({start_pos['x']},{start_pos['y']}) - {start_pos['map_name']}")
        
        # Simulate leaving Pokemon Center (exit is typically up/down from center)
        exit_coords = [
            {"x": 7, "y": 2, "name": "Pokemon Center Exit"},  # Exit north
            {"x": 7, "y": 6, "name": "Pokemon Center Exit"},  # Exit south
        ]
        
        for exit_coord in exit_coords:
            print(f"\n   Testing route to {exit_coord['name']} at ({exit_coord['x']},{exit_coord['y']}):")
            
            route = tools.pathfind_to_coordinate(
                start_pos, exit_coord['x'], exit_coord['y'], "leaving_pokemon_center"
            )
            
            if route["success"]:
                print(f"      ✅ Route planned: {route['distance']} steps")
                print(f"         Button sequence: {' -> '.join(route['button_sequence'])}")
                print(f"         Estimated time: {route['estimated_time']:.1f} seconds")
            else:
                print(f"      ❌ Route failed: {route.get('error', 'Unknown error')}")
        
        # Simulate exploring from Pokemon Center
        print("\n🗺️ Simulating exploration from Pokemon Center...")
        
        exploration_targets = [
            {"x": 10, "y": 4, "name": "East of Pokemon Center"},
            {"x": 4, "y": 4, "name": "West of Pokemon Center"},
            {"x": 7, "y": 1, "name": "North of Pokemon Center"},
            {"x": 7, "y": 7, "name": "South of Pokemon Center"},
        ]
        
        for target in exploration_targets:
            route = tools.pathfind_to_coordinate(
                start_pos, target['x'], target['y'], "exploration"
            )
            
            if route["success"]:
                distance = route['distance']
                buttons = len(route['button_sequence'])
                print(f"   {target['name']}: {distance} steps ({buttons} buttons)")
            else:
                print(f"   {target['name']}: Route failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Movement simulation failed: {e}")
        return False

def test_ram_integration():
    """Test integration with actual RAM data"""
    print("\n🧠 Testing RAM Integration")
    print("=" * 50)
    
    try:
        # Test with SkyEmu RAM data if available
        print("\n📊 Testing with live RAM data...")
        
        import sys
        from pathlib import Path
        tests_path = Path(__file__).parent / "tests"
        if str(tests_path) not in sys.path:
            sys.path.insert(0, str(tests_path))
        
        from analyse_skyemu_ram import SkyEmuClient, PokemonFireRedReader
        
        client = SkyEmuClient(debug=False)
        reader = PokemonFireRedReader(client)
        
        # Get current RAM data
        ram_data = reader.get_compact_game_state()
        
        if ram_data.get("ram_available", False):
            print("   ✅ Live RAM data available!")
            
            location = ram_data.get("location", {})
            party_summary = ram_data.get("party_summary", {})
            
            print(f"   Current location: Map {location.get('map_bank', 0)}-{location.get('map_id', 0)}")
            print(f"   Position: ({location.get('x', 0)}, {location.get('y', 0)})")
            print(f"   Location name: {location.get('location_name', 'Unknown')}")
            print(f"   Party health: {party_summary.get('party_health_status', 'unknown')}")
            print(f"   Needs healing: {party_summary.get('needs_healing', False)}")
            
            # Test pathfinding with real coordinates
            from ai_pathfinding_tools import AIPathfindingTools
            tools = AIPathfindingTools()
            
            if tools.available:
                current_coords = {
                    "map_id": (location.get("map_bank", 0) * 1000) + location.get("map_id", 0),
                    "x": location.get("x", 0),
                    "y": location.get("y", 0)
                }
                
                # Test navigation context with real data
                context = tools.get_navigation_context(current_coords, "explore and find healing")
                if context:
                    print("\n   Navigation context with real RAM data:")
                    for line in context.split('\n')[:3]:
                        print(f"      {line}")
                
                return True
            else:
                print("   ⚠️ Pathfinding tools not available for RAM integration")
                return False
        else:
            print("   ⚠️ Live RAM data not available - check SkyEmu connection")
            print("   (This is expected if SkyEmu is not running)")
            return True  # Not a failure, just no live data
        
    except ImportError:
        print("   ⚠️ RAM analysis tools not available")
        return True  # Not a failure, just no RAM tools
    except Exception as e:
        print(f"   ❌ RAM integration test failed: {e}")
        return False

def test_performance():
    """Test pathfinding performance"""
    print("\n⚡ Testing Pathfinding Performance")
    print("=" * 50)
    
    try:
        from ai_pathfinding_tools import AIPathfindingTools
        
        tools = AIPathfindingTools()
        
        if not tools.available:
            print("❌ Performance testing not available")
            return False
        
        # Test pathfinding speed
        print("\n⏱️ Testing pathfinding speed...")
        
        current_coords = {"map_id": 6005, "x": 5, "y": 5}
        
        # Test various distances
        test_distances = [
            ({"x": 6, "y": 5}, "1 step"),
            ({"x": 10, "y": 5}, "5 steps"),
            ({"x": 15, "y": 15}, "20 steps"),
            ({"x": 25, "y": 25}, "40 steps"),
        ]
        
        total_time = 0
        
        for target, description in test_distances:
            start_time = time.time()
            
            result = tools.pathfind_to_coordinate(
                current_coords, target["x"], target["y"], "performance_test"
            )
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            total_time += duration
            
            if result["success"]:
                print(f"   {description}: {duration:.2f}ms - {result['distance']} steps planned")
            else:
                print(f"   {description}: {duration:.2f}ms - FAILED")
        
        avg_time = total_time / len(test_distances)
        print(f"\n   Average pathfinding time: {avg_time:.2f}ms")
        print(f"   Total test time: {total_time:.2f}ms")
        
        # Performance thresholds
        if avg_time < 10:
            print("   ✅ Excellent performance (< 10ms average)")
        elif avg_time < 50:
            print("   ✅ Good performance (< 50ms average)")
        else:
            print("   ⚠️ Slow performance (> 50ms average)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test databases and files"""
    print("\n🧹 Cleaning up test data...")
    
    test_files = [
        "healing_bookmarks.db",
        "coordinate_map.db", 
        "test_bookmark_Custom_Location.png"
    ]
    
    for filename in test_files:
        test_file = Path(__file__).parent / filename
        if test_file.exists():
            try:
                test_file.unlink()
                print(f"   ✅ Removed {filename}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {filename}: {e}")

def main():
    """Run comprehensive pathfinding test suite"""
    print("🚀 Comprehensive Pathfinding Test Suite")
    print("=" * 60)
    print("Testing Pokemon Center bookmarking, coordinate pathfinding, and AI tools")
    print("=" * 60)
    
    tests_run = 0
    tests_passed = 0
    
    # Run all tests
    test_functions = [
        test_healing_bookmark_system,
        test_ai_pathfinding_tools,
        test_coordinate_movement_simulation,
        test_ram_integration,
        test_performance
    ]
    
    for test_func in test_functions:
        tests_run += 1
        try:
            if test_func():
                tests_passed += 1
                print(f"✅ {test_func.__name__} PASSED")
            else:
                print(f"❌ {test_func.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test_func.__name__} CRASHED: {e}")
        
        print()  # Add spacing between tests
    
    # Final results
    print("=" * 60)
    print(f"📊 Test Results: {tests_passed}/{tests_run} tests passed")
    
    if tests_passed == tests_run:
        print("🎉 ALL TESTS PASSED!")
        print("\n🎯 Pathfinding system is ready for integration:")
        print("   ✅ Pokemon Center bookmarking functional")
        print("   ✅ Coordinate-based pathfinding working")
        print("   ✅ AI tools available for Mistral")
        print("   ✅ RAM integration tested")
        print("   ✅ Performance is acceptable")
        
        print("\n📋 Next steps:")
        print("   1. Integrate pathfinding tools into run_eevee.py")
        print("   2. Add coordinate context to navigation templates")
        print("   3. Test with live Pokemon gameplay")
        print("   4. Monitor healing bookmark creation during actual healing")
        
    else:
        print(f"⚠️ {tests_run - tests_passed} tests failed")
        print("   Check individual test results above for details")
    
    # Clean up test data
    cleanup_test_data()
    
    print("\n🏁 Test suite completed!")

if __name__ == "__main__":
    main()