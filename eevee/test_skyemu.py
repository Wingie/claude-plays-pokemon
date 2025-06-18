#!/usr/bin/env python3
"""
Test SkyEmu connection for Eevee
Quick test script to verify SkyEmu HTTP server connectivity
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "skyemu-mcp"))

def test_skyemu_connection():
    """Test SkyEmu HTTP server connection"""
    print("🔮 Testing SkyEmu Connection for Eevee")
    print("=" * 50)
    
    try:
        from skyemu_client import SkyEmuClient
        print("✅ SkyEmu client imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SkyEmu client: {e}")
        print("   Make sure skyemu-mcp directory exists and has skyemu_client.py")
        return False
    
    # Test connection
    try:
        print("🔗 Attempting to connect to SkyEmu at localhost:8080...")
        client = SkyEmuClient(host="localhost", port=8080)
        print("✅ Connected to SkyEmu successfully!")
        
        # Test basic functionality
        print("🏓 Testing ping...")
        if client.ping():
            print("✅ Ping successful")
        else:
            print("❌ Ping failed")
            
        # Test screenshot
        print("📸 Testing screenshot...")
        try:
            image = client.get_screen()
            print(f"✅ Screenshot captured: {image.size} pixels")
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
        
        # Test status
        print("📊 Testing status...")
        try:
            status = client.get_status()
            print(f"✅ Status retrieved: {len(status)} fields")
        except Exception as e:
            print(f"❌ Status failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to SkyEmu: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure SkyEmu is running")
        print("2. Verify HTTP Control Server is enabled in SkyEmu")
        print("3. Check that SkyEmu is listening on localhost:8080")
        print("4. Try a different port if SkyEmu is configured differently")
        return False

def test_eevee_skyemu_controller():
    """Test Eevee's SkyEmu controller"""
    print("\n🎮 Testing Eevee SkyEmu Controller")
    print("=" * 50)
    
    try:
        from skyemu_controller import SkyEmuController
        print("✅ SkyEmu controller imported successfully")
        
        # Test controller initialization
        controller = SkyEmuController()
        
        print(f"🔍 Controller client object: {controller.client}")
        print(f"🔍 Testing is_connected()...")
        connected = controller.is_connected()
        print(f"🔍 is_connected() returned: {connected}")
        
        if connected:
            print("✅ Controller connected to SkyEmu")
            
            # Test screenshot method
            print("📸 Testing controller screenshot...")
            screenshot_path = controller.capture_screen("test_screenshot.png")
            if screenshot_path:
                print(f"✅ Screenshot saved: {screenshot_path}")
            else:
                print("❌ Screenshot failed")
            
            # Test base64 screenshot
            print("🔄 Testing base64 screenshot...")
            base64_data = controller.get_screenshot_base64()
            if base64_data:
                print(f"✅ Base64 screenshot: {len(base64_data)} characters")
            else:
                print("❌ Base64 screenshot failed")
            
            return True
        else:
            print("❌ Controller not connected to SkyEmu")
            return False
            
    except Exception as e:
        print(f"❌ Controller test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔮 Eevee SkyEmu Integration Test")
    print("=" * 60)
    
    # Test basic SkyEmu connection
    skyemu_ok = test_skyemu_connection()
    
    # Test Eevee controller integration
    if skyemu_ok:
        controller_ok = test_eevee_skyemu_controller()
    else:
        controller_ok = False
    
    print("\n" + "=" * 60)
    print("🏁 Test Results:")
    print(f"   SkyEmu Connection: {'✅ PASS' if skyemu_ok else '❌ FAIL'}")
    print(f"   Eevee Controller:  {'✅ PASS' if controller_ok else '❌ FAIL'}")
    
    if skyemu_ok and controller_ok:
        print("\n🎉 All tests passed! Eevee is ready to use with SkyEmu.")
        print("\nYou can now run:")
        print('   python run_eevee.py "your task here"')
    else:
        print("\n⚠️  Some tests failed. Please check SkyEmu setup.")
        print("\nNext steps:")
        print("1. Start SkyEmu emulator")
        print("2. Load a Pokemon ROM")
        print("3. Enable HTTP Control Server in SkyEmu")
        print("4. Run this test again")
    
    sys.exit(0 if (skyemu_ok and controller_ok) else 1)