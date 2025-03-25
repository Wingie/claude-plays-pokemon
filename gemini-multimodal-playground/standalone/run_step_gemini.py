from dotenv import load_dotenv
import os
import sys
import google.generativeai as genai
import time
from pokemon_controller import PokemonController, read_image_to_base64
import base64  # Import base64
from google.generativeai.types import FunctionDeclaration, Tool  # Import FunctionDeclaration and Tool
import traceback
# Load environment variables from .env file
load_dotenv()
from gamememory import GameMemory

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
    controller = PokemonController(region=None, window_title=WINDOW_TITLE)
    genai.configure(api_key=GEMINI_API_KEY) # Initialize genai with API key here
    model = genai.GenerativeModel(model_name=os.getenv("GEMINI_MODEL"))  # Specify model name here
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
    # traceback.print_exc()  # Print the full traceback
    sys.exit(1)

pokemon_function_declaration = FunctionDeclaration(
    name="pokemon_controller",
    description="Control the Pokémon game using a list of button presses.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "button_presses": {  # Changed parameter name to be more descriptive
                "type": "array",  # Changed type to array to represent a list
                "items": {
                    "type": "string",
                    "enum": ["up", "down", "left", "right", "a", "b", "start", "select"]
                },
                "description": "A list of button presses for the GameBoy."
            }
        },
        "required": ["button_presses"]  # Changed required field to match the new parameter name
    }
)


pokemon_tool = Tool(
    function_declarations=[pokemon_function_declaration],
)
game_memory = GameMemory()

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
# Initialize messages for Gemini
init_message = [
    {"role": "user", "content": """
You are a pokemon player with ability to interact in the world via function calls:
 - you must use function call to pokemon_controller to control the emulator, you can give a list of buttons in sequence - each time you call it.

## Available Controls
- Up, Down, Left, Right: Move your character in that direction
- A: Interact/Confirm - Use when facing NPCs, signs, doors, or to confirm menu selections
- B: Cancel/Back - Exit menus or speed up text
- Start: Open main menu (Pokemon, Items, Save, etc.)
- Select: Rarely used, specific functions

## Game Understanding
- **Screen Types**: 
  * Overworld: Free movement in the environment
  * Dialog: Text boxes with conversation or information
  * Menu: Selection screens for items, Pokemon, etc.
  * Battle: Turn-based combat with wild Pokemon or trainers
  
- **Common Elements**:
  * NPCs: Characters you can talk to
  * Buildings: Can be entered through doors
  * Items: Collectible objects on the ground (often appear as small balls)
  * Pokemon Centers: Buildings with red roofs for healing Pokemon
  * PokeMarts: Buildings with blue roofs for buying items

## Memory System
- **Locations Visited**: [This section will update as you explore]
- **Key NPCs Met**: [This section will update as you meet characters]
- **Items Found**: [This section will update as you find items]
- **Current Location**: [Your current environment]
- **Current Objective**: [Your active goal]

## Navigation Strategy
1. Build a mental map using cardinal directions (North, South, East, West)
2. Note landmarks and connections between areas
3. Explore systematically, starting from one corner and moving methodically
4. Remember doors, paths, and blocked routes for future reference

## Goal Framework
- **Main Quest**: Progress through the Pokemon journey
- **Current Objective**: [Current game objective]
- **Immediate Task**: [What you should focus on right now]

## Decision Making
1. Observe the current screen carefully
2. Identify important elements and game state
3. Consider your current objective and location
4. Choose the most appropriate action
5. If an action doesn't work, try alternatives
6. Update your mental map and memory based on results

## When Stuck
1. If an action produces no result, try a different approach
2. Look for visual cues you might have missed
3. Try talking to NPCs for hints
4. Check your inventory or Pokemon team via the Start menu
5. Try entering nearby buildings or taking different paths
6. Vary your interaction methods (A button vs. directional movement)

## Current Game State
- [This section will update with your current status]
     
    """},
]
# print(messages)
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
        prompt_parts = []
        # Prepare messages for Gemini to keep context short
        messages = init_message.copy() 
        memory_summary = game_memory.generate_summary()
        print(f"Memory Summary:\n{memory_summary}")
        # Prepare messages for Gemini with memory and goal
        messages.append({"role": "user", "content": f"""
        {memory_summary}

        ## GOAL: FIND THE PROFESSOR

        What do you observe in the current screen? What action will you take next?
        """})
        
        # Add the current screenshot
        messages.append(make_image_message())

        # print("--- Debugging: Starting prompt_parts conversion loop ---") # ADDED
        for msg in messages:
            if msg["role"] == "user":
                content_part = []
                if isinstance(msg["content"], str):  # Handle string content directly
                    content_part.append(msg["content"])
                elif isinstance(msg["content"], list):  # Handle list of content items
                    for item in msg["content"]:
                        if item["type"] == "text":
                            content_part.append(item["data"])
                        elif item["type"] == "image":
                            content_part.append({
                                "mime_type": item["source"]["media_type"],
                                "data": base64.b64decode(item["source"]["data"])
                            })
                # Corrected part: Extend prompt_parts with elements of content_part, not content_part itself
                prompt_parts.extend(content_part)  # Use extend instead of append
            elif msg["role"] == "assistant":
                if isinstance(msg["content"], list):  # Handle list of content items for assistant
                    for item in msg["content"]:
                        if item["type"] == "text":
                            prompt_parts.append(item["text"])  # Use item['text'] here
                        elif item["type"] == "tool_use":
                            pass
                        elif item["type"] == "tool_result":
                            pass
        # print(prompt_parts) # ADDED
        try:
            # Get gemini's next move
            response = model.generate_content(
                prompt_parts,
                generation_config={"max_output_tokens": 1000},
                tools=[pokemon_tool]  # Pass the Tool object here
            )
            # print(response) # Print the entire response object
            assistant_content_list = []
            # Print Gemini's thinking and process tool use
            if response.candidates and response.candidates[0].content.parts:  # Check if candidates and parts exist
                for part in response.candidates[0].content.parts:
                    # print(dir(part))
                    # print(">>>test>>>",part.text) if part.text else None
                    # print("***function_call",part.function_call) if part.function_call else None
                    if part.text:
                        assistant_content_list.append({"type": "text", "text": part.text})
                        print(f"gemini-text: {part.text}")
                    elif part.function_call:
                        assistant_content_list.append({"type": "tool_use", "tool_use": part})
                        tool_use = part
                        tool_name = part.function_call.name
                        # print(tool_use)
                        
                        if tool_name == "pokemon_controller":
                            button_presses = []
                            for item,button_p in part.function_call.args.items():
                                # print(">>>>>>>",item)
                                for button in button_p:
                                    button_presses.append(button)

                            if button_presses:
                                print(f"********** Gemini chose to press: {button_presses}")
                                actions_taken = []
                                failed_actions = []

                                for action in button_presses:
                                    success = controller.press_button(action)
                                    time.sleep(1)
                                    if success:
                                        actions_taken.append(action)
                                    else:
                                        failed_actions.append(action)

                                result_msg_parts = []
                                if actions_taken:
                                    result_msg_parts.append(f"Successfully pressed buttons: {', '.join(actions_taken)}.")
                                if failed_actions:
                                    result_msg_parts.append(f"Failed to press buttons: {', '.join(failed_actions)}.")

                                result_msg = " ".join(result_msg_parts) if result_msg_parts else "No button presses attempted."
                                game_memory.add_turn_summary(button_presses, result_msg)
                            else:
                                result_msg = "No button presses found in the tool input."
                                game_memory.add_turn_summary([], result_msg)

                            # Add the result back to Gemini
                            tool_response = {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use.function_call.name,
                                        "content": result_msg
                                    }
                                ]
                            }
                            messages.append(tool_response)
                        
            else:
                print("Warning: Gemini response was empty or incomplete.")

            # Add Gemini's response to messages (using the processed list)
            messages.append({"role": "assistant", "content": assistant_content_list})

        except Exception as e:
            print(f"Error during Gemini API call: {str(e)}")
            traceback.print_exc()
            raise e  # Re-raise to stop loop for debugging

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
    traceback.print_exc()
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
                            if isinstance(content, dict) and "type" in content:
                                if content["type"] == "text":
                                    f.write(f"Gemini: {content['text']}\n\n")
                                elif content["type"] == "tool_use":
                                    tool_use_data = content["tool_use"]
                                    if hasattr(tool_use_data, "function_call"):
                                        f.write(f"Action: {tool_use_data.function_call.name}\n")
                                        if hasattr(tool_use_data.function_call, "args"):
                                            f.write(f"Args: {tool_use_data.function_call.args}\n\n")
                    elif msg["role"] == "user" and "content" in msg:
                        if isinstance(msg["content"], list):
                            for item in msg["content"]:
                                if isinstance(item, dict) and item.get("type") == "tool_result":
                                    f.write(f"Result: {item.get('content', '')}\n\n")
            print(f"Saved conversation to {conversation_file}")
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")

    print("Exiting program.")
    sys.exit(0)