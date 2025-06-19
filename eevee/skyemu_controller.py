"""
SkyEmu Controller for Eevee
Provides Pokemon game control interface using SkyEmu HTTP API
"""

import time
import base64
from io import BytesIO
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add path to import SkyEmu client
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "skyemu-mcp"))

try:
    from skyemu_client import SkyEmuClient
except ImportError as e:
    print(f"Warning: Could not import SkyEmuClient: {e}")
    print("Make sure SkyEmu MCP server is available")
    SkyEmuClient = None

class SkyEmuController:
    """Pokemon game controller using SkyEmu HTTP API"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        Initialize SkyEmu controller
        
        Args:
            host: SkyEmu server hostname
            port: SkyEmu server port
        """
        self.host = host
        self.port = port
        self.client = None
        self.key_delay = 0.2  # Default delay between key presses
        self._connected = False  # Track connection status
        
        # Pokemon Game Boy button mapping
        self.button_mapping = {
            'up': 'Up',
            'down': 'Down', 
            'left': 'Left',
            'right': 'Right',
            'a': 'A',
            'b': 'B',
            'start': 'Start',
            'select': 'Select'
        }
        
        # Initialize connection
        self._connect()
    
    def _connect(self) -> bool:
        """Connect to SkyEmu HTTP server"""
        if SkyEmuClient is None:
            print("❌ SkyEmuClient not available - cannot connect to SkyEmu")
            return False
        
        try:
            # Create client - if ping fails in constructor, catch it
            try:
                self.client = SkyEmuClient(host=self.host, port=self.port)
                self._connected = True
                print(f"✅ Connected to SkyEmu at {self.host}:{self.port}")
                return True
            except Exception as init_error:
                # If initialization failed due to ping, try manual setup
                import requests
                
                # Test if server is responding to screenshots
                test_url = f"http://{self.host}:{self.port}/screen"
                response = requests.get(test_url, params={"format": "png"})
                response.raise_for_status()
                
                # Create minimal client manually
                self.client = SkyEmuClient.__new__(SkyEmuClient)
                self.client.base_url = f"http://{self.host}:{self.port}"
                
                # Add the _get method from SkyEmuClient
                def _get(endpoint, params=None):
                    import requests
                    url = f"{self.client.base_url}/{endpoint}"
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    return response
                
                self.client._get = _get
                self._connected = True
                
                print(f"✅ Connected to SkyEmu at {self.host}:{self.port} (bypass ping)")
                return True
                
        except Exception as e:
            print(f"❌ Failed to connect to SkyEmu: {e}")
            self.client = None
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to SkyEmu"""
        if self.client is None:
            return False
        
        # Use the connection status we tracked during initialization
        if self._connected:
            # Quick verification - try to get a screenshot
            try:
                self.client.get_screen()
                return True
            except:
                self._connected = False
                return False
        
        return False
    
    def find_window(self) -> bool:
        """Check if SkyEmu connection is available (compatibility with PokemonController)"""
        return self.is_connected()
    
    def press_button(self, button: str, duration: float = None) -> bool:
        """
        Press a Pokemon game button
        
        Args:
            button: Button name (up, down, left, right, a, b, start, select)
            duration: How long to hold the button (uses default if None)
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        # Map button name to SkyEmu format
        skyemu_button = self.button_mapping.get(button.lower())
        if not skyemu_button:
            print(f"❌ Unknown button: {button}")
            return False
        
        try:
            # Use custom duration or default
            press_duration = duration if duration is not None else self.key_delay
            
            # Try the button press - even if API returns false, it might still work
            try:
                result = self.client.press_button(skyemu_button, duration=press_duration)
            except:
                result = False
            
            # Since you reported buttons work even when API says failed,
            # let's assume success if we can communicate with SkyEmu at all
            if self.is_connected():
                # Individual button presses logged in enhanced analysis instead
                return True
            else:
                print(f"❌ Failed to press {button.upper()} button")
                return False
            
        except Exception as e:
            print(f"❌ Error pressing button {button}: {e}")
            return False
    
    def press_sequence(self, buttons: list, delay_between: float = None) -> bool:
        """
        Press a sequence of buttons
        
        Args:
            buttons: List of button names to press in order
            delay_between: Delay between button presses (uses default if None)
            
        Returns:
            True if all buttons pressed successfully
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        delay = delay_between if delay_between is not None else self.key_delay
        
        try:
            for button in buttons:
                if not self.press_button(button):
                    return False
                time.sleep(delay)
            
            # Button sequences logged in enhanced analysis instead
            return True
            
        except Exception as e:
            print(f"❌ Error pressing button sequence: {e}")
            return False
    
    def capture_screen(self, filename: str = None) -> str:
        """
        Capture current game screen
        
        Args:
            filename: Optional filename for screenshot
            
        Returns:
            Path to saved screenshot file
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return None
        
        try:
            # Get screenshot from SkyEmu
            image = self.client.get_screen(format="png")
            
            # Generate filename if not provided
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"skyemu_screenshot_{timestamp}.png"
            
            # Ensure we have the full path
            if not filename.startswith('/'):
                # Save to eevee analysis directory
                eevee_dir = Path(__file__).parent
                analysis_dir = eevee_dir / "analysis"
                analysis_dir.mkdir(exist_ok=True)
                filepath = analysis_dir / filename
            else:
                filepath = Path(filename)
            
            # Save the image
            image.save(filepath)
            # Screenshot paths logged in enhanced analysis instead
            
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error capturing screenshot: {e}")
            return None
    
    def get_screenshot_base64(self) -> Optional[str]:
        """
        Get current game screen as base64 encoded data
        
        Returns:
            Base64 encoded PNG image data
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return None
        
        try:
            # Get screenshot from SkyEmu
            image = self.client.get_screen(format="png")
            
            # Convert to base64
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            image_data = buffer.getvalue()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return base64_data
            
        except Exception as e:
            print(f"❌ Error getting screenshot as base64: {e}")
            return None
    
    def read_memory(self, addresses: list, map_id: int = 0) -> list:
        """
        Read bytes from Pokemon game memory
        
        Args:
            addresses: List of memory addresses to read
            map_id: Memory map ID (0 for default)
            
        Returns:
            List of byte values
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return []
        
        try:
            return self.client.read_bytes(addresses, map_id)
        except Exception as e:
            print(f"❌ Error reading memory: {e}")
            return []
    
    def write_memory(self, address_value_pairs: dict, map_id: int = 0) -> bool:
        """
        Write bytes to Pokemon game memory
        
        Args:
            address_value_pairs: Dictionary mapping addresses to values
            map_id: Memory map ID (0 for default)
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        try:
            return self.client.write_bytes(address_value_pairs, map_id)
        except Exception as e:
            print(f"❌ Error writing memory: {e}")
            return False
    
    def save_state(self, filename: str) -> bool:
        """
        Save current emulation state
        
        Args:
            filename: Path to save the state file
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        try:
            result = self.client.save_state(filename)
            if result:
                print(f"💾 Saved state: {filename}")
            return result
        except Exception as e:
            print(f"❌ Error saving state: {e}")
            return False
    
    def load_state(self, filename: str) -> bool:
        """
        Load emulation state
        
        Args:
            filename: Path to the state file
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        try:
            result = self.client.load_state(filename)
            if result:
                print(f"📁 Loaded state: {filename}")
            return result
        except Exception as e:
            print(f"❌ Error loading state: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get emulator status information
        
        Returns:
            Dictionary with status information
        """
        if not self.is_connected():
            return {"connected": False, "error": "Not connected to SkyEmu"}
        
        try:
            status = self.client.get_status()
            status["connected"] = True
            return status
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def step_frames(self, frames: int = 1) -> bool:
        """
        Step the emulator forward by specific number of frames
        
        Args:
            frames: Number of frames to advance
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        try:
            return self.client.step(frames)
        except Exception as e:
            print(f"❌ Error stepping frames: {e}")
            return False
    
    def run_emulator(self) -> bool:
        """
        Run emulator at normal speed
        
        Returns:
            True if successful
        """
        if not self.is_connected():
            print("❌ Not connected to SkyEmu")
            return False
        
        try:
            return self.client.run()
        except Exception as e:
            print(f"❌ Error running emulator: {e}")
            return False

def read_image_to_base64(image_path: str) -> str:
    """
    Read image file and convert to base64 (compatibility function)
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded image data
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"❌ Error reading image {image_path}: {e}")
        return ""