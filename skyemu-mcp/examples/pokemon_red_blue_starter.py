"""
Example script showing how to use the SkyEmu MCP tools with Pokemon Red/Blue.

This script demonstrates the beginning sequence of Pokemon Red/Blue,
from the player's bedroom to choosing the first Pokemon.
"""
import sys
import os
import time

# Add parent directory to path so we can import the SkyEmu client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skyemu_client import SkyEmuClient

# Initialize SkyEmu client
skyemu = SkyEmuClient()

def main():
    print("Starting Pokemon Red/Blue example sequence...")
    
    # Navigate from bedroom to downstairs
    print("Navigating from bedroom to downstairs...")
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(1.5) # Wait for stairs animation
    
    # Navigate out of the house
    print("Leaving the house...")
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(2.0) # Wait for exit animation
    
    # Navigate to tall grass (where Professor Oak stops you)
    print("Walking to the tall grass...")
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    
    # Handle Professor Oak's dialogue
    print("Handling Professor Oak's dialogue...")
    time.sleep(3.0) # Wait for cutscene
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    
    # Wait for walking back to lab animation
    print("Following Oak to the lab...")
    time.sleep(7.0)
    
    # Handle dialogue in the lab
    print("In the lab...")
    for _ in range(10):
        skyemu.press_button("A", 0.2)
        time.sleep(0.5)
    
    # Navigate to choose the starter Pokemon (Bulbasaur)
    print("Selecting Bulbasaur...")
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Right", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Up", 0.2)
    time.sleep(0.1)
    
    # Choose Bulbasaur
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    
    # Rival chooses Charmander
    time.sleep(1.0)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    
    # Move to center for battle
    skyemu.press_button("Left", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    skyemu.press_button("Down", 0.2)
    time.sleep(0.1)
    
    # Battle dialogue
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    skyemu.press_button("A", 0.2)
    time.sleep(0.5)
    
    # First battle is starting
    print("First battle is starting...")
    time.sleep(7.0)  # Wait for battle to start
    
    print("Example completed!")
    print("You can now continue playing the game manually")
    
if __name__ == "__main__":
    main()
