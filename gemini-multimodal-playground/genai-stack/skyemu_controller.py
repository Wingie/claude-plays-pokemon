import pyautogui
import time
import os,io
import base64
from PIL import ImageGrab, Image
import json
from skyemu_client import SkyEmuClient

from typing import Dict, List, Optional, Any, Union


class SkyemuController:
    def __init__(self, skyemu):
        """
        Initialize the Pokémon controller.
        
        Args:
            window_title (str): Title of the emulator window (for window focusing)
            region (tuple): Screen region to capture (left, top, right, bottom) - used as fallback
        """
        self.skyemu = skyemu
        self.key_delay = 0.1  # Delay between key presses
        
        # GameBoy control mapping
        self.controls = {
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'a': 'x',      # Typically X is mapped to A on emulators
            'b': 'z',      # Typically Z is mapped to B on emulators
            'start': 'enter',
            'select': 'backspace'
        }

    def get_emulator_status(self) -> str:
        """Get the current status of the emulator.
        
        Returns:
            JSON string containing emulator status information
        """
        status = self.skyemu.get_status()
        return dict(status)
    
    def capture_screen(self, filename='emulator_screen.jpg'):
        """Capture the emulator window in RGB mode and save as JPEG"""
        screenshot = self.skyemu.get_screen()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        # Convert to RGB mode (in case it was captured as RGBA)
        screenshot = screenshot.convert('RGB')
        screenshot.save(filename, 'JPEG')
        return filename
    
    def press_sequence(self,buttons: List[str], hold_time: float = 0.2, delay_between: float = 0.1) -> str:
        """Press a sequence of buttons in order.
        
        Args:
            buttons: List of buttons to press in sequence
            hold_time: How long to hold each button in seconds
            delay_between: Delay between button presses in seconds
        """
        for button in buttons:
            result = self.skyemu.press_button(button, hold_time)
            if delay_between > 0 and button != buttons[-1]:
                time.sleep(delay_between)
        return f"Button sequence {', '.join(buttons)} executed"

def read_image_to_base64(image_path):
    """
    Reads an image file and converts it to a base64 encoded string.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded string representation of the image
    """
    try:
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error reading image file: {str(e)}") 