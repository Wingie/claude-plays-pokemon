from dotenv import load_dotenv
import os
from anthropic import Anthropic
import time
from pokemon_controller import PokemonController, read_image_to_base64

load_dotenv()

WINDOW_TITLE = os.getenv("WINDOW_TITLE") or "Pokemon - Yellow Version (UE) [C][!].gbc"
CLAUDE_KEY = os.getenv("CLAUDE_KEY")
client = Anthropic(api_key=CLAUDE_KEY)

# Initialize the Pokémon controller
# You may need to adjust these values based on your emulator position
# Set region=None to capture the entire screen, or provide coordinates for the emulator window
controller = PokemonController(region=None, window_title=WINDOW_TITLE)  

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

# Initialize messages for Claude
messages = [
    {"role": "user", "content": """You are playing Pokémon Yellow on Game Boy. You will be given screenshots of the game, and you need to decide which button to press to progress in the game.

Available buttons:
- Up, Down, Left, Right: Move around the game world
- A: Interact with NPCs or objects, select menu options, confirm choices
- B: Cancel, exit menus, speed up text
- Start: Open the main menu
- Select: Used rarely for specific functions

Your goal is to explore the game, battle trainers, capture Pokémon, and eventually become the Pokémon League Champion.

Analyze each screenshot carefully to determine what's happening in the game, and choose the most appropriate button to press. The player is always in the center of the screen.
Here are some tips:
     - Doors into buildings are always visible, if you want to enter a building, you have to find the door and walk to it."""},
]

# Game loop
running = True
max_turns = 100  # Limit the number of turns
turn = 0

while running and turn < max_turns:
    messages.append({"role": "user", "content": "What button would you like to press next? Analyze the current game state and make your decision."})
    messages.append(make_image_message())
    
    # Get Claude's next move
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        messages=messages,
        max_tokens=1000,
        tools=[pokemon_tool]
    )

    # Print Claude's thinking
    for content in response.content:
        if content.type == "text":
            print(f"Claude: {content.text}")
    
    # Add Claude's response to messages
    messages.append({"role": "assistant", "content": response.content})
    
    # Process tool use
    for content in response.content:
        if content.type == "tool_use":
            tool_use = content
            tool_name = tool_use.name
            tool_input = tool_use.input
            
            if tool_name == "pokemon_controller":
                action = tool_input["action"]
                print(f"Claude chose to press: {action}")
                
                # Execute the button press
                controller.press_button(action)
                
                # Add the result back to Claude
                tool_response = {
                    "role": "user",
                    "content": [
                        {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Button {action} pressed successfully."
                        }
                    ]
                }
                
                messages.append(tool_response)
    
    # Increment turn counter
    turn += 1
    
    # Small delay between turns
    time.sleep(1.0)

# Final message when the game loop ends
if turn >= max_turns:
    print(f"Game session ended after {max_turns} turns.")
else:
    print("Game session ended.")