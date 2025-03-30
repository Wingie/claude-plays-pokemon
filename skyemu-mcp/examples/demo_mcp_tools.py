"""
Demo script showing how to use the MCP tools programmatically.

This demonstrates calling the MCP tools directly in Python, similar to how
an LLM like Claude would use them through the MCP protocol.
"""
import sys
import os
import asyncio
import base64
from io import BytesIO
from PIL import Image

# Add parent directory to path so we can import the MCP tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skyemu_mcp_server import (
    press_button,
    press_sequence,
    hold_buttons,
    release_buttons,
    get_screenshot,
    step_frames,
    execute_sequence,
    perform_directional_movement,
    navigate_menu
)

async def main():
    print("Running MCP tools demo...")
    
    # Take a screenshot and save it
    print("Taking a screenshot...")
    screenshot_b64 = await get_screenshot()
    screenshot_data = base64.b64decode(screenshot_b64)
    with open("screenshot.png", "wb") as f:
        f.write(screenshot_data)
    print("Screenshot saved to screenshot.png")
    
    # Press a single button
    print("Pressing the A button...")
    result = await press_button("A")
    print(f"Result: {result}")
    
    # Press a sequence of buttons
    print("Pressing a sequence of buttons: Up, Right, A...")
    result = await press_sequence(["Up", "Right", "A"])
    print(f"Result: {result}")
    
    # Perform directional movement
    print("Moving right 3 steps...")
    result = await perform_directional_movement("Right", 3)
    print(f"Result: {result}")
    
    # Navigate a menu
    print("Navigating through a menu...")
    menu_navigation = [
        {"direction": "Down", "steps": 1},
        {"direction": "Down", "steps": 1},
        {"confirm": True, "delay_after": 1.0},
        {"direction": "Up", "steps": 1},
        {"confirm": True}
    ]
    result = await navigate_menu(menu_navigation)
    print(f"Result: {result}")
    
    # Execute a complex sequence
    print("Executing a complex action sequence...")
    action_sequence = [
        {"type": "press", "button": "Start"},
        {"type": "wait", "time": 1.0},
        {"type": "press", "button": "Down"},
        {"type": "press", "button": "A"},
        {"type": "wait", "time": 0.5},
        {"type": "hold", "buttons": ["B", "Right"]},
        {"type": "wait", "time": 1.0},
        {"type": "release", "buttons": ["B", "Right"]}
    ]
    result = await execute_sequence(action_sequence)
    print(f"Result: {result}")
    
    print("Demo completed!")

if __name__ == "__main__":
    asyncio.run(main())
