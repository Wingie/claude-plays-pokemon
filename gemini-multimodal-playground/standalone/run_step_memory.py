"""
run_step_memory.py - Pokémon AI player with Neo4j memory storage for image embeddings and Gemini responses
"""

import io, shutil  # For saving screenshots
import os
import json
from datetime import datetime
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
    
    # Get the map visualization if available
    map_base64 = game_memory.get_map_as_base64(screenshot_file)
    if map_base64:
        message["content"].append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": map_base64,
            },
        })
        
    return message


def update_game_progress_file(model, memory):
    """
    Update the game progress summary file by asking the AI to optimize
    and summarize the last 10 turns from Neo4j.
    
    Args:
        model: The Gemini model instance
        memory: The Neo4jMemory instance
        
    Returns:
        str: Path to the created progress file, or None if failed
    """
    try:
        # Create game_progress directory if it doesn't exist
        progress_dir = "game_progress"
        if not os.path.exists(progress_dir):
            os.makedirs(progress_dir)
            print(f"Created directory for game progress: {progress_dir}")
            
        # Get the last 10 turns from Neo4j memory
        recent_turns = memory.get_recent_turns(10)
        
        if not recent_turns:
            print("No turns found in memory. Cannot create progress summary.")
            return None
            
        # Prepare timestamp and filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_file = os.path.join(progress_dir, f"progress_summary_{timestamp}.md")
        
        # Format the turns for the AI prompt
        turns_text = ""
        for turn in recent_turns:
            turns_text += f"Turn {turn['turn_id']}: {turn['gemini_text']}\n\n"
        
        # Ask the AI to optimize and summarize the turns
        prompt = f"""
        Based on the following recent game turns, create an optimized and summarized progress report 
        for our Pokémon FireRed/LeafGreen gameplay. Format it as a well-structured Markdown document
        with sections for current status, recent actions, key discoveries, and next objectives.
        
        Current goal: {GAME_GOAL}
        
        Recent turns:
        {turns_text}
        
        Please create a coherent narrative that captures important progress, challenges, and future plans.
        Include any insights about the game world, obstacles faced, and strategies that worked or failed.
        """
        
        response = model.generate_content(prompt, generation_config={"max_output_tokens": 1500})
        
        # Save the AI's summary to the progress file
        with open(progress_file, 'w') as f:
            f.write(f"# Pokémon Game Progress Summary\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Current Goal:** {GAME_GOAL}\n\n")
            f.write(response.text)
        
        print(f"Updated game progress summary at {progress_file}")
        
        # Also update a latest.md file that always contains the most recent summary
        latest_file = os.path.join(progress_dir, "latest.md")
        with open(latest_file, 'w') as f:
            f.write(f"# Pokémon Game Progress Summary\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Current Goal:** {GAME_GOAL}\n\n")
            f.write(response.text)
        
        return progress_file
        
    except Exception as e:
        print(f"Error updating game progress file: {str(e)}")
        traceback.print_exc()
        return None


def store_prompt_in_neo4j(memory, prompt_text, prompt_type="default"):
    """Store the prompt used for the AI in Neo4j for future reference"""
    try:
        prompt_id = memory.add_prompt(prompt_text, prompt_type)
        return prompt_id
    except Exception as e:
        print(f"Error storing prompt in Neo4j: {str(e)}")
        return None


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

# Create game_progress directory if it doesn't exist
progress_dir = "game_progress"
try:
    if not os.path.exists(progress_dir):
        os.makedirs(progress_dir)
        print(f"Created directory for game progress: {progress_dir}")
except Exception as e:
    print(f"Error creating game progress directory: {str(e)}")

model, controller, game_memory = init_game()

# First, update the game progress file using the last 10 turns from the previous runs
progress_file = update_game_progress_file(model, game_memory)
if progress_file:
    print(f"Created initial game progress summary at {progress_file}")
else:
    print("No initial game progress summary created (possibly no previous turns found).")

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

        # if turn%25 == 0:
        #     init_message = game_memory.get_updated_prompt(init_message,GAME_GOAL)
        #     print("------>*>*>*>*> get_updated_prompt >*>*>*>",init_message)
        messages = init_message.copy() 
        memory_summary = game_memory.generate_summary()
        print(f"Memory Summary:\n{memory_summary}")
        
        # Store the memory summary as a prompt in Neo4j
        memory_prompt_id = store_prompt_in_neo4j(game_memory, memory_summary, "memory_summary")
        
        # Prepare the AI prompt with memory and goal
        ai_prompt = f"""
        {memory_summary}
        Your current goal is: {GAME_GOAL}
        What do you observe in the current screen? What action will you take next?
        """
        
        # Store the AI prompt in Neo4j
        ai_prompt_id = store_prompt_in_neo4j(game_memory, ai_prompt, "ai_prompt")
        
        # Prepare messages for Gemini with memory and goal
        messages.append({"role": "user", "content": ai_prompt})
        
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
        
        try:
            # Get gemini's next move
            response = model.generate_content(
                prompt_parts,
                generation_config={"max_output_tokens": 1000},
                tools=[pokemon_tool]  # Pass the Tool object here
            )
            
            assistant_content_list = []
            # Process Gemini's response
            if response.candidates and response.candidates[0].content.parts:  # Check if candidates and parts exist
                for part in response.candidates[0].content.parts:
                    if part.text:
                        assistant_content_list.append({"type": "text", "text": part.text})
                        prev_spoken = part.text
                        print(f"gemini-text: {part.text}")
                        
                        # Store the Gemini response in Neo4j and link it to the prompt
                        response_id = store_prompt_in_neo4j(game_memory, part.text, "gemini_response")
                        if response_id and ai_prompt_id:
                            game_memory.link_prompt_to_response(ai_prompt_id, response_id)
                            
                    elif part.function_call:
                        assistant_content_list.append({"type": "tool_use", "tool_use": part})
                        tool_use = part
                        tool_name = part.function_call.name
                        
                        if tool_name == "pokemon_controller":
                            button_presses = []
                            for item, button_p in part.function_call.args.items():
                                for button in button_p:
                                    button_presses.append(button.capitalize())
    
                            if button_presses:
                                print(f"********** Gemini requested to press: {button_presses}")
                                actions_taken = []
                                failed_actions = []
                                pre_action_screenshot = controller.capture_screen()
                                result_msg = controller.press_sequence(button_presses, delay_between=2)
                                print('result_msg', result_msg)
                                
                                # Add turn summary with button presses to Neo4j memory
                                turn_id = game_memory.add_turn_summary(turn, button_presses, prev_spoken, screenshot_path=pre_action_screenshot)
                                
                                # Link the turn to the prompt and response
                                if turn_id and ai_prompt_id and response_id:
                                    game_memory.link_turn_to_prompt_response(turn_id, ai_prompt_id, response_id)
                    
                            else:
                                result_msg = "No button presses found in the tool input."
                                game_memory.add_turn_summary(turn, [], prev_spoken)

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
        
        # Update game progress summary every 5 turns
        if turn % 5 == 0:
            progress_file = update_game_progress_file(model, game_memory)
            if progress_file:
                print(f"Updated game progress summary at {progress_file}")

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

    # Create a final game progress summary
    progress_file = update_game_progress_file(model, game_memory)
    if progress_file:
        print(f"Created final game progress summary at {progress_file}")

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
