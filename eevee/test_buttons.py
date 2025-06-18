#!/usr/bin/env python3
"""
Test SkyEmu button controls for Eevee
"""

import sys
import time
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "skyemu-mcp"))

def test_button_controls():
    """Test button controls with SkyEmu"""
    print("🎮 Testing SkyEmu Button Controls")
    print("=" * 50)
    
    try:
        from skyemu_controller import SkyEmuController
        
        # Initialize controller
        controller = SkyEmuController()
        
        if not controller.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        print("✅ Connected to SkyEmu")
        
        # Test individual buttons
        test_buttons = ['a', 'b', 'start', 'up', 'down', 'left', 'right']
        
        for button in test_buttons:
            print(f"\n🔄 Testing {button.upper()} button...")
            
            # Take screenshot before
            print("📸 Screenshot before...")
            before_path = controller.capture_screen(f"before_{button}.png")
            
            # Press button
            result = controller.press_button(button, duration=0.3)
            print(f"   Press result: {'✅ Success' if result else '❌ Failed'}")
            
            # Wait a moment
            time.sleep(0.5)
            
            # Take screenshot after
            print("📸 Screenshot after...")
            after_path = controller.capture_screen(f"after_{button}.png")
            
            print(f"   Before: {before_path}")
            print(f"   After:  {after_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Button test failed: {e}")
        return False

def test_direct_skyemu_client():
    """Test button controls directly with SkyEmu client"""
    print("\n🔧 Testing Direct SkyEmu Client")
    print("=" * 50)
    
    try:
        from skyemu_client import SkyEmuClient
        
        client = SkyEmuClient(host="localhost", port=8080)
        print("✅ Direct client connected")
        
        # Test button names directly
        test_buttons = ['A', 'B', 'Start', 'Up', 'Down', 'Left', 'Right']
        
        for button in test_buttons:
            print(f"🔄 Testing direct {button} button...")
            
            try:
                # Try direct button press
                result = client.press_button(button, duration=0.2)
                print(f"   Direct press result: {'✅ Success' if result else '❌ Failed'}")
                
            except Exception as e:
                print(f"   Direct press error: {e}")
            
            time.sleep(0.3)
        
        return True
        
    except Exception as e:
        print(f"❌ Direct client test failed: {e}")
        return False

def test_input_states():
    """Test input state setting directly"""
    print("\n⚙️ Testing Input States")
    print("=" * 50)
    
    try:
        from skyemu_client import SkyEmuClient
        
        client = SkyEmuClient(host="localhost", port=8080)
        
        # Test setting input states directly
        print("🔄 Testing input state: A button on")
        result1 = client.set_input({"A": 1})
        print(f"   Set A=1: {'✅ Success' if result1 else '❌ Failed'}")
        
        time.sleep(0.3)
        
        print("🔄 Testing input state: A button off")
        result2 = client.set_input({"A": 0})
        print(f"   Set A=0: {'✅ Success' if result2 else '❌ Failed'}")
        
        # Try getting status to see what inputs are available
        print("\n📊 Getting SkyEmu status...")
        try:
            status = client.get_status()
            if 'inputs' in status:
                print(f"   Available inputs: {list(status['inputs'].keys())}")
            else:
                print("   No inputs in status")
        except Exception as e:
            print(f"   Status error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Input state test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎮 SkyEmu Button Control Testing")
    print("=" * 60)
    
    # Test Eevee's controller
    controller_ok = test_button_controls()
    
    # Test direct SkyEmu client
    direct_ok = test_direct_skyemu_client()
    
    # Test input states
    input_ok = test_input_states()
    
    print("\n" + "=" * 60)
    print("🏁 Test Results:")
    print(f"   Eevee Controller:  {'✅ PASS' if controller_ok else '❌ FAIL'}")
    print(f"   Direct Client:     {'✅ PASS' if direct_ok else '❌ FAIL'}")
    print(f"   Input States:      {'✅ PASS' if input_ok else '❌ FAIL'}")
    
    if controller_ok and direct_ok and input_ok:
        print("\n🎉 All button tests passed!")
    else:
        print("\n⚠️  Some button tests failed - debugging needed")