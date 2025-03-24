import pyautogui
import time
import os
import base64
from PIL import ImageGrab, Image
import Quartz
import pygetwindow as gw  # Add this import for window management

def getWindowByTitle(title: str):
    """Returns a Window object of the currently active Window."""

    # Source: https://stackoverflow.com/questions/5286274/front-most-window-using-cgwindowlistcopywindowinfo
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if title in win.get(Quartz.kCGWindowName, ''):
            return win
    raise Exception('Could not find an active window.') # Temporary hack.

class PokemonController:
    def __init__(self, window_title=None, region=None):
        """
        Initialize the Pokémon controller.
        
        Args:
            window_title (str): Title of the emulator window (for window focusing)
            region (tuple): Screen region to capture (left, top, right, bottom) - used as fallback
        """
        self.window_title = window_title
        self.region = region
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
        
    def find_window(self):
        """Find and return the emulator window"""
        if not self.window_title:
            return None
            
        try:
            # Get all windows and find the one that matches our title
            window = getWindowByTitle(self.window_title)
            if window:
                return window
            
            print(f"No window with title containing '{self.window_title}' found.")
        except Exception as e:
            print(f"Error finding window: {str(e)}")
        
        return None
        
    def capture_screen(self, filename='emulator_screen.jpg'):
        """Capture the emulator window in RGB mode and save as JPEG"""
        screenshot = None
        
        # Try to capture the specific window
        window = self.find_window()
        if window:
            # Bring window to front
            try:
                # window.activate()
                time.sleep(0.2)  # Give the window time to come to front
                left, top, width, height = gw.getWindowGeometry(self.window_title)
                # Capture the window
                screenshot = ImageGrab.grab(bbox=(int(left), int(top), int(left + width), int(top + height)))
                print(f"Captured window: {self.window_title}")
            except Exception as e:
                print(f"Error capturing window: {str(e)}")
        
        # Fallback to region or full screen if window capture failed
        if screenshot is None:
            if self.region:
                screenshot = ImageGrab.grab(bbox=self.region)
                print("Captured specified region")
            else:
                screenshot = ImageGrab.grab()
                print("Captured entire screen")
        
        # Convert to RGB mode (in case it was captured as RGBA)
        screenshot = screenshot.convert('RGB')
        
        # Save the screenshot as JPEG
        screenshot.save(filename, 'JPEG')
        return filename
        
    def press_button(self, button, hold_time=0.1):
        """
        Press a button on the emulator
        
        Args:
            button (str): Button to press ('up', 'down', 'left', 'right', 'a', 'b', 'start', 'select')
            hold_time (float): How long to hold the button down
        """
        # Try to focus the window before pressing keys
        # print(button)x
        window = self.find_window()
        if window:
            try:
                # window.activate()
                time.sleep(0.1)  # Short delay to ensure window is active
            except Exception as e:
                print(f"Error focusing window: {str(e)}")
        
        if button in self.controls:
            key = self.controls[button]
            pyautogui.keyDown(key)
            time.sleep(hold_time)
            pyautogui.keyUp(key)
            time.sleep(self.key_delay)  # Short delay after button press
            return True
        else:
            print(f"Unknown button: {button}")
            return False
            
    def execute_action(self, action):
        """
        Execute a higher-level game action
        
        Args:
            action (dict): Action details including type and parameters
        """
        action_type = action.get('type', '')
        
        if action_type == 'button_press':
            button = action.get('button', '')
            return self.press_button(button)
            
        elif action_type == 'sequence':
            # Execute a sequence of button presses
            sequence = action.get('buttons', [])
            for button in sequence:
                self.press_button(button)
            return True
            
        elif action_type == 'navigate':
            # Navigate in a direction
            direction = action.get('direction', '')
            steps = action.get('steps', 1)
            
            for _ in range(steps):
                self.press_button(direction)
            return True
            
        return False

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