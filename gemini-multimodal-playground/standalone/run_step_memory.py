"""
run_step_memory.py - Pokémon AI player with Neo4j memory storage for image embeddings and Gemini responses
"""

import io,shutil  # For saving screenshots
from common_imports import *
from google.generativeai.types import FunctionDeclaration, Tool
load_dotenv()
from gamememory import Neo4jMemory
from skyemu_client import SkyEmuClient
from skyemu_controller import SkyemuController, read_image_to_base64

def init_game():
    """Initialize the game components."""
    try:
        # Initialize the SkyEmu client and controller
        skyemu = SkyEmuClient()
        controller = SkyemuController(skyemu=skyemu)    
        memory = Neo4jMemory(GAME_GOAL)
        print(memory)

        # Initialize the Gemini model
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not found.")
            print("Please set it in the .env file.")
            sys.exit(1)
            
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        model = genai.GenerativeModel(model_name=model_name)
        
        # Test if we can find the emulator window
        status = controller.get_emulator_status()
        if not status:
            print("\nWarning: Could not find the emulator window.")
            print("Please make sure the skyemu emulator is running with a Pokémon game loaded.")
            response = input("Do you want to continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
                
        # Test screenshot functionality
        controller.capture_screen()
        print("Screenshot functionality is working.")
        
        return (model, controller, memory)
        
    except Exception as e:
        print(f"Error initializing: {str(e)}")
        traceback.print_exc()
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
    global controller, game_memory
    screenshot_file = controller.capture_screen()
    game_state = read_image_to_base64(screenshot_file)
    
    # Create the message with proper structure
    message = {
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
    
    # # Get the map visualization if available
    # map_base64 = game_memory.get_map_as_base64()
    # if map_base64:
    #     message["content"].append({
    #         "type": "image",
    #         "source": {
    #             "type": "base64",
    #             "media_type": "image/png",
    #             "data": map_base64,
    #         },
    #     })
        
    return message


# Game loop configuration
running = True
max_turns = 100  # Limit the number of turns
turn = 0
turn_delay = 1.0  # Delay between turns in seconds
save_screenshots = True  # Whether to save screenshots for later review
screenshot_dir = "screenshots"  # Directory to save screenshots
prev_spoken = ""

# Create screenshots directory if it doesn't exist and save_screenshots is enabled
if save_screenshots:
    try:
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            print(f"Created directory for screenshots: {screenshot_dir}")
    except Exception as e:
        print(f"Error creating screenshots directory: {str(e)}")
        save_screenshots = False

model, controller, game_memory = init_game();
print(f"Starting game loop with {max_turns} max turns...")
print("Press Ctrl+C to stop the loop at any time")
print("-" * 50)

### GAME RUNNING LOOP ####
try:
    while running and turn < max_turns:
        print(f"\nTurn {turn + 1}/{max_turns}")
        time.sleep(2)
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
        Your current goal is: {GAME_GOAL}
        What do you observe in the current screen? What action will you take next?
        """})
        
        # Add the current screenshot
        messages.append(make_image_message())

        print("--- Debugging: Starting prompt_parts conversion loop ---") # ADDED
        for msg in messages:
            print
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
                        prev_spoken = part.text
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
                                    button_presses.append(button.capitalize())

                            if button_presses:
                                print(f"********** Gemini requested to press: {button_presses}")
                                actions_taken = []
                                failed_actions = []
                                pre_action_screenshot = controller.capture_screen()
                                result_msg = controller.press_sequence(button_presses,delay_between=2)
                                print('result_msg',result_msg)
                                game_memory.add_turn_summary(button_presses, prev_spoken,screenshot_path=pre_action_screenshot) # barrier_detected=barrier_detected
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