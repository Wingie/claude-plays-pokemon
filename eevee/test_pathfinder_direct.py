#!/usr/bin/env python3
"""
Direct pathfinder test script - moves character to coordinates 10,15
Usage: python test_pathfinder_direct.py [target_x] [target_y]
"""

import sys
import time
import json
from skyemu_controller import SkyEmuController
from eevee_agent import EeveeAgent
from run_eevee import ContinuousGameplay

def test_direct_pathfinding(target_x=10, target_y=15):
    """Test pathfinding by directly moving to target coordinates"""
    
    print(f"🎯 Direct Pathfinder Test - Moving to ({target_x}, {target_y})")
    print("=" * 60)
    
    try:
        # Initialize controller
        controller = SkyEmuController("http://localhost:8080")
        if not controller.connect():
            print("❌ Failed to connect to SkyEmu")
            return False
            
        print("✅ Connected to SkyEmu")
        
        # Initialize Eevee agent
        eevee = EeveeAgent(
            controller=controller,
            verbose=True,
            use_visual_analysis=False,  # Skip visual analysis for direct test
            neo4j_enabled=False  # Skip Neo4j for simple test
        )
        
        # Create minimal gameplay instance just for pathfinding
        gameplay = ContinuousGameplay(
            eevee=eevee,
            session_name="pathfinder_test",
            verbose=True
        )
        
        # Get current position from RAM
        print("\n📍 Getting current position from RAM...")
        ram_data = gameplay._collect_ram_data()
        
        if not ram_data or not ram_data.get("ram_available"):
            print("❌ RAM data not available")
            return False
            
        location = ram_data.get("location", {})
        current_x = location.get("x", 0)
        current_y = location.get("y", 0)
        
        print(f"📍 Current position: ({current_x}, {current_y})")
        print(f"🎯 Target position: ({target_x}, {target_y})")
        
        # Calculate distance
        distance = abs(target_x - current_x) + abs(target_y - current_y)
        print(f"📏 Manhattan distance: {distance} tiles")
        
        # Execute pathfinding
        print(f"\n🧭 Starting pathfinding to ({target_x}, {target_y})...")
        print("-" * 40)
        
        buttons = gameplay._execute_pathfinding_to_coordinate(target_x, target_y)
        
        print("-" * 40)
        print(f"\n✅ Pathfinding complete!")
        print(f"🎮 Buttons executed: {buttons}")
        print(f"📊 Total moves: {len(buttons)}")
        
        # Verify final position
        final_ram = gameplay._collect_ram_data()
        if final_ram and final_ram.get("ram_available"):
            final_location = final_ram.get("location", {})
            final_x = final_location.get("x", 0)
            final_y = final_location.get("y", 0)
            
            print(f"\n📍 Final position: ({final_x}, {final_y})")
            
            if final_x == target_x and final_y == target_y:
                print("🎉 SUCCESS: Reached target coordinates!")
                return True
            else:
                remaining = abs(target_x - final_x) + abs(target_y - final_y)
                print(f"⚠️  PARTIAL: {remaining} tiles from target")
                if remaining < distance:
                    print("✅ Made progress toward target")
                return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during pathfinding test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    # Parse command line arguments
    target_x = 10
    target_y = 15
    
    if len(sys.argv) > 2:
        try:
            target_x = int(sys.argv[1])
            target_y = int(sys.argv[2])
        except ValueError:
            print("Usage: python test_pathfinder_direct.py [target_x] [target_y]")
            print("Using default target: (10, 15)")
    
    # Run the test
    success = test_direct_pathfinding(target_x, target_y)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()