"""
SkyEmu MCP Server

An MCP server that provides tools for controlling a SkyEmu instance through the MCP protocol.
"""
import asyncio
import os
import json
import time
import base64
from io import BytesIO
from typing import Dict, List, Optional, Any, Union

from mcp.server.fastmcp import FastMCP
from PIL import Image

from skyemu_client import SkyEmuClient

# Initialize the SkyEmu client
skyemu = SkyEmuClient()

# Initialize the MCP server
app = FastMCP("skyemu-mcp")

@app.tool()
async def press_button(button: str, hold_time: float = 0.2) -> str:
    """Press a button on the emulated controller.
    
    Args:
        button: The button to press (e.g., "A", "B", "Up", "Down", "Left", "Right", "Start", "Select")
        hold_time: How long to hold the button in seconds
    """
    skyemu.press_button(button, hold_time)
    return f"Button {button} pressed for {hold_time} seconds"

@app.tool()
async def press_sequence(buttons: List[str], hold_time: float = 0.2, delay_between: float = 0.1) -> str:
    """Press a sequence of buttons in order.
    
    Args:
        buttons: List of buttons to press in sequence
        hold_time: How long to hold each button in seconds
        delay_between: Delay between button presses in seconds
    """
    for button in buttons:
        skyemu.press_button(button, hold_time)
        if delay_between > 0 and button != buttons[-1]:
            time.sleep(delay_between)
    
    return f"Button sequence {', '.join(buttons)} executed"

@app.tool()
async def hold_buttons(buttons: List[str]) -> str:
    """Hold down multiple buttons simultaneously.
    
    Args:
        buttons: List of buttons to hold down
    """
    input_state = {button: 1 for button in buttons}
    skyemu.set_input(input_state)
    return f"Buttons {', '.join(buttons)} are being held down"

@app.tool()
async def release_buttons(buttons: List[str]) -> str:
    """Release previously held buttons.
    
    Args:
        buttons: List of buttons to release
    """
    input_state = {button: 0 for button in buttons}
    skyemu.set_input(input_state)
    return f"Buttons {', '.join(buttons)} have been released"

@app.tool()
async def release_all_buttons() -> str:
    """Release all buttons that might be currently held down."""
    status = skyemu.get_status()
    all_inputs = status.get("inputs", {})
    
    # Create a dictionary to release all buttons that are pressed
    release_inputs = {}
    for input_name, value in all_inputs.items():
        if value > 0:
            release_inputs[input_name] = 0
    
    skyemu.set_input(release_inputs)
    return "All buttons released"

@app.tool()
async def get_screenshot() -> str:
    """Get a screenshot of the current game state.
    
    Returns:
        Base64 encoded PNG image of the current screen
    """
    screen = skyemu.get_screen()
    buffered = BytesIO()
    screen.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

@app.tool()
async def step_frames(frames: int = 1) -> str:
    """Step the emulator forward by a specific number of frames.
    
    Args:
        frames: Number of frames to step forward
    """
    skyemu.step(frames)
    return f"Stepped forward {frames} frames"

@app.tool()
async def run_emulator() -> str:
    """Start/resume the emulator at normal speed."""
    skyemu.run()
    return "Emulator is now running"

@app.tool()
async def save_state(path: str) -> str:
    """Save the current game state to a file.
    
    Args:
        path: Path where to save the game state
    """
    if not os.path.isabs(path):
        path = os.path.abspath(path)
        
    skyemu.save_state(path)
    return f"Game state saved to {path}"

@app.tool()
async def load_state(path: str) -> str:
    """Load a previously saved game state.
    
    Args:
        path: Path to the saved game state
    """
    if not os.path.isabs(path):
        path = os.path.abspath(path)
        
    skyemu.load_state(path)
    return f"Game state loaded from {path}"

@app.tool()
async def load_rom(path: str, pause: bool = False) -> str:
    """Load a ROM file into the emulator.
    
    Args:
        path: Path to the ROM file
        pause: Whether to pause emulation after loading
    """
    if not os.path.isabs(path):
        path = os.path.abspath(path)
        
    skyemu.load_rom(path, pause)
    return f"ROM loaded from {path}"

@app.tool()
async def get_emulator_status() -> str:
    """Get the current status of the emulator.
    
    Returns:
        JSON string containing emulator status information
    """
    status = skyemu.get_status()
    return json.dumps(status, indent=2)

@app.tool()
async def execute_sequence(
    actions: List[Dict[str, Any]], 
    delay_between: float = 0.5
) -> str:
    """Execute a sequence of actions with delays in between.
    
    Args:
        actions: List of action dictionaries, each containing:
            - 'type': The action type ('press', 'hold', 'release', 'wait')
            - Additional parameters specific to each action type
        delay_between: Default delay between actions in seconds
    
    Action Types:
    - 'press': Press and release a button
        - 'button': The button to press
        - 'hold_time': How long to hold the button (optional)
    - 'hold': Hold down one or more buttons
        - 'buttons': List of buttons to hold
    - 'release': Release one or more buttons
        - 'buttons': List of buttons to release
    - 'wait': Wait for a specified amount of time
        - 'time': Time to wait in seconds
    """
    result_messages = []
    
    for i, action in enumerate(actions):
        action_type = action.get('type')
        
        if action_type == 'press':
            button = action.get('button')
            hold_time = action.get('hold_time', 0.2)
            skyemu.press_button(button, hold_time)
            result_messages.append(f"Pressed {button} for {hold_time}s")
            
        elif action_type == 'hold':
            buttons = action.get('buttons', [])
            input_state = {button: 1 for button in buttons}
            skyemu.set_input(input_state)
            result_messages.append(f"Holding buttons: {', '.join(buttons)}")
            
        elif action_type == 'release':
            buttons = action.get('buttons', [])
            input_state = {button: 0 for button in buttons}
            skyemu.set_input(input_state)
            result_messages.append(f"Released buttons: {', '.join(buttons)}")
            
        elif action_type == 'wait':
            wait_time = action.get('time', delay_between)
            time.sleep(wait_time)
            result_messages.append(f"Waited for {wait_time}s")
        
        # Add delay between actions except after the last one
        if i < len(actions) - 1 and action_type != 'wait':
            time.sleep(delay_between)
    
    return "\n".join(result_messages)

@app.tool()
async def perform_directional_movement(
    direction: str, 
    steps: int = 1, 
    hold_time: float = 0.2, 
    delay_between: float = 0.1
) -> str:
    """Perform a directional movement in the game.
    
    Args:
        direction: The direction to move ("Up", "Down", "Left", "Right")
        steps: Number of button presses to perform
        hold_time: How long to hold the button for each press
        delay_between: Delay between button presses
    """
    if direction not in ["Up", "Down", "Left", "Right"]:
        return f"Invalid direction: {direction}. Must be Up, Down, Left, or Right."
    
    for _ in range(steps):
        skyemu.press_button(direction, hold_time)
        if _ < steps - 1:  # No delay after the last press
            time.sleep(delay_between)
    
    return f"Moved {direction} for {steps} steps"

@app.tool()
async def navigate_menu(
    selections: List[Dict[str, Any]],
    delay_between: float = 0.5
) -> str:
    """Navigate through menu selections with directional and confirmation buttons.
    
    Args:
        selections: List of selection dictionaries, each containing:
            - 'direction': Direction to move ("Up", "Down", "Left", "Right")
            - 'steps': Number of presses in that direction (default: 1)
            - 'confirm': Whether to press the confirmation button (default: False)
            - 'confirm_button': Button to press for confirmation (default: "A")
            - 'delay_after': Additional delay after this selection (default: 0)
        delay_between: Default delay between actions in seconds
    """
    results = []
    
    for selection in selections:
        direction = selection.get('direction')
        steps = selection.get('steps', 1)
        confirm = selection.get('confirm', False)
        confirm_button = selection.get('confirm_button', 'A')
        delay_after = selection.get('delay_after', 0)
        
        # Move in the specified direction
        if direction and direction in ["Up", "Down", "Left", "Right"]:
            for _ in range(steps):
                skyemu.press_button(direction, 0.2)
                time.sleep(0.1)
            results.append(f"Moved {direction} {steps} times")
            time.sleep(delay_between)
        
        # Press confirmation button if requested
        if confirm:
            skyemu.press_button(confirm_button, 0.2)
            results.append(f"Pressed {confirm_button} to confirm")
            time.sleep(delay_between)
        
        # Additional delay if specified
        if delay_after > 0:
            time.sleep(delay_after)
            results.append(f"Waited for {delay_after}s")
    
    return "\n".join(results)

if __name__ == "__main__":
    print("Starting SkyEmu MCP Server")
    print("Connecting to SkyEmu at localhost:8080...")
    
    try:
        app.run()
    except Exception as e:
        print(f"Error: {e}")
