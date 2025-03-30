"""
SkyEmu HTTP API Client

A client for interfacing with the SkyEmu HTTP Control Server.
"""
import time
import requests
from typing import Dict, List, Optional, Tuple, Union, Any
import base64
from io import BytesIO
from PIL import Image

class SkyEmuClient:
    """Client for SkyEmu's HTTP Control Server API."""
    
    def __init__(self, host="localhost", port=8080):
        """Initialize the SkyEmu client.
        
        Args:
            host: Hostname of the SkyEmu HTTP server
            port: Port number of the SkyEmu HTTP server
        """
        self.base_url = f"http://{host}:{port}"
        # Verify the server is running
        self.ping()
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Make a GET request to the SkyEmu API.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            Response from the server
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for error status codes
        return response
    
    def ping(self) -> bool:
        """Check if the SkyEmu server is running.
        
        Returns:
            True if server is running, False otherwise
        """
        try:
            response = self._get("ping")
            return response.text == "pong"
        except:
            raise ConnectionError("Could not connect to SkyEmu HTTP server")
    
    def step(self, frames: int = 1) -> bool:
        """Step the emulator forward by a specific number of frames.
        
        Args:
            frames: Number of frames to step
            
        Returns:
            True if successful
        """
        response = self._get("step", {"frames": frames})
        return response.text == "ok"
    
    def run(self) -> bool:
        """Unpause the emulator and run at normal speed.
        
        Returns:
            True if successful
        """
        response = self._get("run")
        return response.text == "ok"
    
    def get_screen(self, format="png", embed_state=False) -> Image.Image:
        """Get a screenshot of the current emulator screen.
        
        Args:
            format: Image format (png, jpg, or bmp)
            embed_state: Whether to embed emulation state in the image
            
        Returns:
            PIL Image object of the current screen
        """
        params = {"format": format}
        if embed_state:
            params["embed_state"] = 1
            
        response = self._get("screen", params)
        img_data = BytesIO(response.content)
        return Image.open(img_data)
    
    def read_bytes(self, addresses: List[int], map_id: int = 0) -> List[int]:
        """Read bytes from the emulated memory.
        
        Args:
            addresses: List of memory addresses to read
            map_id: Memory map ID (0 for default, 7 for ARM7, 9 for ARM9 in NDS)
            
        Returns:
            List of byte values read from memory
        """
        params = {}
        for i, addr in enumerate(addresses):
            params[f"addr"] = hex(addr)[2:]  # Convert to hex string without 0x prefix
            
        if map_id != 0:
            params["map"] = map_id
            
        response = self._get("read_byte", params)
        # Response is in hex format
        hex_data = response.text
        bytes_data = []
        
        # Parse hex string into bytes
        for i in range(0, len(hex_data), 2):
            if i + 1 < len(hex_data):
                byte_val = int(hex_data[i:i+2], 16)
                bytes_data.append(byte_val)
                
        return bytes_data
    
    def write_bytes(self, address_value_pairs: Dict[int, int], map_id: int = 0) -> bool:
        """Write bytes to the emulated memory.
        
        Args:
            address_value_pairs: Dictionary mapping addresses to byte values
            map_id: Memory map ID (0 for default, 7 for ARM7, 9 for ARM9 in NDS)
            
        Returns:
            True if successful
        """
        params = {}
        for addr, value in address_value_pairs.items():
            hex_addr = hex(addr)[2:]  # Convert to hex string without 0x prefix
            hex_val = hex(value)[2:].zfill(2)  # Ensure two digits
            params[hex_addr] = hex_val
            
        if map_id != 0:
            params["map"] = map_id
            
        response = self._get("write_byte", params)
        return response.text == "ok"
    
    def set_input(self, input_states: Dict[str, int]) -> bool:
        """Set the state of emulator inputs.
        
        Args:
            input_states: Dictionary mapping input names to states (0 or 1)
            
        Returns:
            True if successful
        """
        response = self._get("input", input_states)
        return response.text == "ok"
    
    def press_button(self, button: str, duration: float = 0.2) -> bool:
        """Press and release a button.
        
        Args:
            button: Name of the button to press
            duration: How long to hold the button in seconds
            
        Returns:
            True if successful
        """
        # Press the button
        self.set_input({button: 1})
        
        # Wait for the specified duration
        time.sleep(duration)
        
        # Release the button
        return self.set_input({button: 0})
    
    def hold_button(self, button: str) -> bool:
        """Hold a button down (without releasing).
        
        Args:
            button: Name of the button to hold
            
        Returns:
            True if successful
        """
        return self.set_input({button: 1})
    
    def release_button(self, button: str) -> bool:
        """Release a button.
        
        Args:
            button: Name of the button to release
            
        Returns:
            True if successful
        """
        return self.set_input({button: 0})
    
    def get_status(self) -> Dict:
        """Get the current status of the emulator.
        
        Returns:
            Dictionary containing emulator status information
        """
        response = self._get("status")
        return response.json()
    
    def save_state(self, path: str) -> bool:
        """Save the current emulation state to a file.
        
        Args:
            path: Path where to save the state
            
        Returns:
            True if successful
        """
        response = self._get("save", {"path": path})
        return response.text == "ok"
    
    def load_state(self, path: str) -> bool:
        """Load an emulation state from a file.
        
        Args:
            path: Path to the state file
            
        Returns:
            True if successful
        """
        response = self._get("load", {"path": path})
        return response.text == "ok"
    
    def load_rom(self, path: str, pause: bool = False) -> bool:
        """Load a ROM file.
        
        Args:
            path: Path to the ROM file
            pause: Whether to pause the emulator after loading
            
        Returns:
            True if successful
        """
        params = {"path": path}
        if pause:
            params["pause"] = 1
            
        response = self._get("load_rom", params)
        return response.text == "ok"
