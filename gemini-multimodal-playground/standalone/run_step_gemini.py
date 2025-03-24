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
import time

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
messages = [
    {"role": "user", "content": """
You are a streamer playing a leets play series of Pokémon Yellow on Game Boy Color. You are an expert Pokémon player and will be given screenshots of the game. Your task is to decide which button to press to progress in the game intelligently.

Available buttons:
- Up, Down, Left, Right: Move your character one step in that direction on the current screen. You can only move along paths, grass, or other traversable tiles. You cannot walk through walls, buildings, trees, or other solid objects visible on the screen.
- A: Interact with people (NPCs), objects (like items on the ground, signs), or the environment (like doors to enter buildings). You need to be directly facing the person or object to interact with it. This button is also used to select options in menus and confirm choices.
- B: Cancel actions, go back in menus, or speed up the text in dialogues.
- Start: Open the main menu where you can access options like saving the game, checking your party, or looking at your items.
- Select: Used rarely for specific functions, usually not needed for basic progression.

Game knowledge you should use:
1. Your character (Ash) is always positioned in the center of the screen when walking in the overworld. The environment around you will scroll as you move.
2. To enter a building, you need to walk directly towards the doorway until you are standing right in front of it. If it's an accessible building, pressing 'A' will usually trigger entry. Look for visual cues like a darker doorway or a change in the environment indicating a door.
3. In Pokémon battles, choose moves that are super effective against the opponent's Pokémon type. Remember basic type matchups (e.g., Water is strong against Fire, Electric is strong against Water, etc.).
4. Talk to every person you encounter. They often provide valuable information, hints about where to go next, or even items. Approach them directly and press 'A' to initiate a conversation.
5. You begin your journey in Pallet Town. A common first step is to try and leave town to the north, towards Viridian City. However, there might be someone you need to speak to first.
6. The game world is divided into different areas (towns, routes, caves). You progress by exploring these areas, battling other trainers, and eventually defeating Gym Leaders to earn badges.
7. Collecting all eight badges will allow you to challenge the Pokémon League.
8. Remember to save your progress frequently by opening the Start menu and selecting the "SAVE" option.

Analyzing the Screenshots:
1. Carefully observe the layout of the screen. Identify any paths, buildings, objects, and characters present.
2. Pay attention to any text on the screen, such as dialogue boxes or menu options, as this provides crucial information about your current situation and objectives.
3. Consider what you were doing in the previous turn. Are you trying to reach a specific location? Are you in a conversation? Are you trying to interact with an object?
4. Based on the visual information and your current objective, decide which button press is most likely to lead to progress in the game.

Explain your thought process step-by-step in text before performing function calls to move. For example, "I see a door in front of me, so I will press 'A' to try and enter the building." or "The NPC is facing me, so I will press 'A' to talk to them." Then, use the `pokemon_controller` tool to execute your chosen action.
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
        # Prepare messages for Gemini
        messages.append({"role": "user", "content": "What button would you like to press next? Analyze the current game state and make your decision."})
        messages.append(make_image_message())

        print("--- Debugging: Starting prompt_parts conversion loop ---") # ADDED
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
                        print(tool_use)
                        

                        if tool_name == "pokemon_controller":
                            button_presses = []
                            for item,button_p in part.function_call.args.items():
                                print(">>>>>>>",item)
                                for button in button_p:
                                    button_presses.append(button)

                            if button_presses:
                                print(f"********** Gemini chose to press: {button_presses}")
                                actions_taken = []
                                failed_actions = []

                                for action in button_presses:
                                    success = controller.press_button(action, 0.5)
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
                            else:
                                result_msg = "No button presses found in the tool input."

                            # Add the result back to Gemini
                            tool_response = {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": button_presses,
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
                                f.write(f"Action: {content.tool_use.input.get('action', 'unknown')}\n\n")  # Access tool_use from content
            print(f"Saved conversation to {conversation_file}")
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")

    print("Exiting program.")
    sys.exit(0)