import base64
from io import BytesIO
# Ensure Pillow (PIL) is installed: pip install Pillow
from PIL import Image
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


def get_screenshot_jpeg_base64_resized():
    """
    Captures a screenshot, resizes it smaller by a given percentage,
    converts it to JPEG, saves it to a file, and returns a
    base64 encoded string of the resized JPEG image.
    """
    if not 0 < reduction_percentage < 100:
        print("Error: Reduction percentage must be between 0 and 100.")
        return None

    try:
        # 1. Get the screen image (assuming it's a PIL Image)
        screen = skyemu.get_screen(embed_state=True)

        # 3. Resize the image
        # Use Image.Resampling.LANCZOS for high-quality downscaling
        # (Older Pillow versions might use Image.ANTIALIAS)
        resized_screen = screen.resize(new_size, resample=Image.Resampling.LANCZOS)

        # 4. Convert the *resized* image to RGB mode (required for JPEG)
        resized_screen_rgb = resized_screen.convert('RGB')

        # 5. Save the *resized* RGB image to the specified file as JPEG
        file_path = "/tmp/emulator_screen_resized.jpg" # Changed filename
        resized_screen_rgb.save(file_path, 'JPEG', quality=85) # Added quality setting
        print(f"Resized screenshot saved as JPEG to: {file_path}")

        # 6. Save the *resized* RGB image to an in-memory buffer as JPEG
        jpeg_buffer = BytesIO()
        resized_screen_rgb.save(jpeg_buffer, format='JPEG', quality=85) # Added quality setting

        # 7. Get the raw bytes from the in-memory JPEG buffer
        jpeg_bytes = jpeg_buffer.getvalue()

        # 8. Encode these JPEG bytes into base64
        base64_bytes = base64.b64encode(jpeg_bytes)

        # 9. Decode the base64 bytes into a UTF-8 string
        base64_string = base64_bytes.decode('utf-8')

        # 10. Return the base64 string
        return base64_string

    except Exception as e:
        print(f"An error occurred: {e}")
        # Handle the error appropriately, maybe return None or raise it
        return None

if __name__ == "__main__":
    s = get_screenshot_jpeg_base64_resized()
    print(len(s))
