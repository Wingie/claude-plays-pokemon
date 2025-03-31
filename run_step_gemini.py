from dotenv import load_dotenv
import os
import sys
import time
import importlib.util
import pathlib

# Add the path to sys.path to allow importing from the directory with dashes
standalone_dir = os.path.join(os.path.dirname(__file__), "gemini-multimodal-playground", "standalone")
sys.path.append(standalone_dir)

# Now import from the standalone directory
from pokemon_controller import PokemonController, read_image_to_base64

# Import the simplified Gemini API
from gemini_api import GeminiAPI

# Load environment variables from .env file
load_dotenv()

# Configure the emulator window title
WINDOW_TITLE = "mGBA - 0.10.5"

# Get Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    print("Please create a .env file with your API key or set it in your environment.")
    sys.exit(1)

# Initialize Gemini client and Pokemon controller
try:
    client = GeminiAPI(GEMINI_API_KEY)
    controller = PokemonController(region=None, window_title=WINDOW_TITLE)
    print(f"Looking for window with title: {WINDOW_TITLE}")
    # Test if we can find the window right away
    window = controller.find_window()
    if not window:
        print("\nWarning: Could not find the emulator window.")
        print("Please make sure the mGBA emulator is running with a Pokemon game loaded.")
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
except Exception as e:
    print(f"Error initializing: {str(e)}")
    sys.exit(1)

# Define the Pokémon controller tool
pokemon_tool = {
    "name": "pokemon_controller",
    "description": "Control the Pokémon game using button presses.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["up", "down", "left", "right", "a", "b", "start", "select"],
                "description": "The button to press on the GameBoy."
            }
        },
        "required": ["action"]
    }
}

def make_image_message():
    # Capture the current state of the emulator
    screenshot_file = controller.capture_screen()
    game_state = read_image_to_base64(screenshot_file)
    
    # Format the message for Gemini with the image data
    return {
        "role": "user",
        "content": [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": game_state,
            },
        }]
    }

# Initialize messages for Gemini
messages = [
    {"role": "user", "content": """You are playing Pokémon Yellow on Game Boy. You are an expert Pokémon player and will be given screenshots of the game. Your task is to decide which button to press to progress in the game intelligently.

Available buttons:
- Up, Down, Left, Right: Move around the game world
- A: Interact with NPCs or objects, select menu options, confirm choices
- B: Cancel, exit menus, speed up text
- Start: Open the main menu
- Select: Used rarely for specific functions

Your goal is to explore the game, battle trainers, capture Pokémon, and eventually become the Pokémon League Champion.

Game knowledge you should use:
1. The player character (Ash) is always in the center of the screen when walking around.
2. Doors to buildings are visible and you need to walk to them to enter.
3. In battles, choose effective moves based on Pokémon type advantages (e.g., Water > Fire, Electric > Water).
4. Talk to NPCs for important information and quests.
5. Pallet Town is the starting area, followed by Viridian City to the north.
6. The game follows a specific path of Gym Leaders to defeat.
7. You need to collect badges by defeating Gym Leaders.
8. You can save the game through the Start menu.

Battle Tips:
- In battles, select the most effective moves based on type matchups
- Consider using status moves (like Sleep Powder) to make catching Pokémon easier
- Heal your Pokémon when they're low on health
- For Gym battles, prepare Pokémon that have advantage against the Gym's type

Navigation Tips:
- Remember where key locations are (Pokémon Centers, PokéMarts, Gyms)
- Use the Town Map (from your items) if you're lost
- Some areas require special items to access (e.g., HM moves like Cut or Surf)

Analyze each screenshot carefully to:
1. Identify the current game state (overworld, battle, menu, dialogue)
2. Understand what's happening and what your objective should be
3. Make a strategic decision about the next button to press

Explain your thought process briefly, then use the pokemon_controller tool to execute your chosen action."""},
]

# Game loop configuration
running = True
max_turns = 100  # Limit the number of turns
turn = 0
turn_delay = 1.0  # Delay between turns in seconds
save_screenshots = True  # Whether to save screenshots for later review
screenshot_dir = "screenshots"  # Directory to save screenshots

# Create screenshots directory if it doesn't exist and save_screenshots is enabled
if save_screenshots:
    try:
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            print(f"Created directory for screenshots: {screenshot_dir}")
    except Exception as e:
        print(f"Error creating screenshots directory: {str(e)}")
        save_screenshots = False

print(f"Starting game loop with {max_turns} max turns...")
print("Press Ctrl+C to stop the loop at any time")
print("-" * 50)

try:
    while running and turn < max_turns:
        print(f"\nTurn {turn + 1}/{max_turns}")
        
        # Capture and save the screenshot
        screenshot_file = controller.capture_screen()
        if save_screenshots:
            try:
                # Save a copy with the turn number for later review
                save_path = os.path.join(screenshot_dir, f"turn_{turn:03d}.jpg")
                import shutil
                shutil.copy(screenshot_file, save_path)
            except Exception as e:
                print(f"Error saving screenshot: {str(e)}")
        
        # Prepare messages for Gemini
        messages.append({"role": "user", "content": "What button would you like to press next? Analyze the current game state and make your decision."})
        messages.append(make_image_message())
        
        try:
            # Get gemini's next move
            response = client.messages.create(
                model="gemini-flash-2.0-exp",
                messages=messages,
                max_tokens=1000,
                tools=[pokemon_tool]
            )

            # Print Gemini's thinking
            for content in response.content:
                if content.type == "text":
                    print(f"Gemini: {content.text}")
            
            # Add Gemini's response to messages
            messages.append({"role": "assistant", "content": response.content})
            
            # Process tool use
            action_taken = False
            for content in response.content:
                if content.type == "tool_use":
                    tool_use = content
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    
                    if tool_name == "pokemon_controller":
                        action = tool_input["action"]
                        print(f"Gemini chose to press: {action}")
                        
                        # Execute the button press
                        success = controller.press_button(action)
                        
                        if success:
                            action_taken = True
                            result_msg = f"Button {action} pressed successfully."
                        else:
                            result_msg = f"Failed to press button {action}."
                        
                        # Add the result back to Gemini
                        tool_response = {
                            "role": "user",
                            "content": [
                                {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": result_msg
                                }
                            ]
                        }
                        
                        messages.append(tool_response)
            
            # If no action was taken, press the default button (A)
            if not action_taken:
                print("No valid action received from Gemini. Pressing 'a' button as default.")
                controller.press_button('a')
                
        except Exception as e:
            print(f"Error during Gemini API call: {str(e)}")
            # Continue with the next turn even if there was an error
        
        # Increment turn counter
        turn += 1
        
        # Small delay between turns
        print(f"Waiting {turn_delay} seconds before next turn...")
        time.sleep(turn_delay)

except KeyboardInterrupt:
    print("\nGame loop interrupted by user.")
    running = False
except Exception as e:
    print(f"\nUnexpected error in game loop: {str(e)}")
    running = False
finally:
    # Final message when the game loop ends
    if turn >= max_turns:
        print(f"\nGame session ended after {max_turns} turns.")
    else:
        print(f"\nGame session ended after {turn} turns.")
    
    # Save the conversation if there was at least one turn
    if turn > 0 and save_screenshots:
        try:
            conversation_file = os.path.join(screenshot_dir, "conversation.txt")
            with open(conversation_file, 'w') as f:
                for msg in messages:
                    if msg["role"] == "assistant" and "content" in msg:
                        for content in msg["content"]:
                            if hasattr(content, "type") and content.type == "text":
                                f.write(f"Gemini: {content.text}\n\n")
                            elif hasattr(content, "type") and content.type == "tool_use":
                                f.write(f"Action: {content.input.get('action', 'unknown')}\n\n")
            print(f"Saved conversation to {conversation_file}")
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")
    
    print("Exiting program.")
    sys.exit(0)
