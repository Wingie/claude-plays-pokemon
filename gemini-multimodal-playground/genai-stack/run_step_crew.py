from common_imports import *

model, controller, window, game_memory, llm = init_game();
print(f"Starting game loop with {MAX_TURNS} max turns...")
print("Press Ctrl+C to stop the loop at any time")
print("-" * 50)

class CaptureScreenTool(BaseTool):
    name: str = "Capture Game Screen"
    description: str = "Captures the current screen of the Pokemon game emulator and returns it as a base64 encoded image string. Use this tool first in every turn to see the current game state."

    def _run(self) -> str:
        global controller
        if not controller:
            return "Error: Pokemon Controller not initialized."
        try:
            screenshot_file = controller.capture_screen()
            base64_image = read_image_to_base64(screenshot_file)
            print("[CaptureScreenTool] Screen captured.")

            # Optionally save screenshot here if needed *during* the tool run
            if save_screenshots:
                try:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(save_screenshots, f"screen_{timestamp}.jpg")
                    shutil.copy(screenshot_file, save_path)
                    # print(f"[CaptureScreenTool] Screenshot saved to {save_path}") # Optional: verbose logging
                except Exception as e:
                    print(f"[CaptureScreenTool] Error saving screenshot: {str(e)}")

            return make_image_message(controller)
        except Exception as e:
            print(f"[CaptureScreenTool] Error capturing screen: {str(e)}")
            traceback.print_exc()
            return f"Error capturing screen: {str(e)}"

class PressButtonsTool(BaseTool):
    name: str = "Press Game Buttons"
    description: str = ("Executes a sequence of button presses on the Pokemon game emulator. "
                        "Input must be a list of strings, where each string is a valid button: "
                        "'up', 'down', 'left', 'right', 'a', 'b', 'start', 'select'. "
                        "Example: ['down', 'down', 'a']")

    def _run(self, button_presses: list[str]) -> str:
        global controller, game_memory
        if not controller:
            return "Error: Pokemon Controller not initialized."
        if not isinstance(button_presses, list):
            return f"Error: Input must be a list of button strings, got {type(button_presses)}"
        if not button_presses:
            return "No buttons provided to press."

        print(f"[PressButtonsTool] Attempting to press: {button_presses}")
        actions_taken = []
        failed_actions = []
        valid_buttons = {"up", "down", "left", "right", "a", "b", "start", "select"}

        for action in button_presses:
            if action not in valid_buttons:
                failed_actions.append(f"{action} (invalid)")
                continue

            success = controller.press_button(action)
            # Add a small delay *between* individual button presses within a sequence
            time.sleep(0.2)
            if success:
                actions_taken.append(action)
            else:
                failed_actions.append(action)

        result_msg_parts = []
        if actions_taken:
            result_msg_parts.append(f"Successfully pressed: {', '.join(actions_taken)}.")
        if failed_actions:
            result_msg_parts.append(f"Failed/Invalid: {', '.join(failed_actions)}.")

        result_msg = " ".join(result_msg_parts) if result_msg_parts else "No valid buttons were pressed."
        print(f"[PressButtonsTool] Result: {result_msg}")

        # Update game memory
        if game_memory:
            game_memory.add_turn_summary(button_presses, result_msg)
        else:
            print("[PressButtonsTool] Warning: Game memory not available to record turn.")

        return result_msg
    

# Instantiate tools (controller and game_memory are now global)
capture_tool = CaptureScreenTool()
press_tool = PressButtonsTool()

# --- AGENT DEFS ---

# --- Agent Definitions ---
observer_agent = Agent(
    role="Screen Observer",
    goal="Accurately perceive and describe the current state of the game screen.",
    backstory="You are a meticulous observer focusing *only* on describing what is visually present on the game screen provided to you. Identify characters, objects, text, menus, and the general context (world, battle, menu).",
    tools=[capture_tool], # ONLY capture tool
    llm=llm,              # Needs to be multimodal
    multimodal=True,      # Explicitly enable multimodal capabilities
    verbose=True,
    allow_delegation=False
)

planner_agent = Agent(
    role="Action Planner",
    goal="Decide the next best sequence of button presses based on observation, memory, and goal, then execute them.",
    backstory="You are a strategic Pokemon player. Given a description of the current screen, a summary of past actions, and an overall goal, your job is to devise the *best short sequence* of button presses (1-5 actions like 'up', 'a', 'b') to make progress. Clearly explain your reasoning before executing the presses.",
    tools=[press_tool],   # ONLY press tool
    llm=llm,              # Can be text-based or multimodal
    verbose=True,
    allow_delegation=False,
    memory=False # Keep manual memory management
)

# --- Task Definitions ---
observe_task = Task(
    description=(
        "**Turn:** {turn_number}\n"
        "1. Use the 'Capture Game Screen' tool *immediately* to get the current visual.\n"
        "2. Analyze the captured image.\n"
        "3. Provide a detailed description covering:\n"
        "    - Player character's location and facing direction (if discernible).\n"
        "    - Surrounding environment (e.g., 'in tall grass', 'in a building', 'on a path').\n"
        "    - Visible NPCs or Pokemon.\n"
        "    - Any open menus, dialogue boxes, or text prompts.\n"
        "    - The general game state (e.g., 'overworld exploration', 'in battle', 'main menu open')."
    ),
    expected_output="A detailed textual description of the current game screen's content and context.",
    agent=observer_agent,
    tools=[capture_tool] # Explicitly associate tool with task/agent if needed by CrewAI version
)

plan_task = Task(
    description=(
        "**Turn:** {turn_number}\n"
        "**Overall Goal:** {current_goal}\n\n"
        "**Game Memory Summary:**\n{memory_summary}\n\n"
        "**Current Screen Observation:**\n{{observe_task.output}}\n\n"
        "Emumator screen is visible at /Users/wingston/code/claude-plays-pokemon/gemini-multimodal-playground/standalone/emulator_screen.jpg  "
        "**Instructions:**\n"
        "1. Review the Current Screen Observation, Game Memory, and Overall Goal.\n"
        "2. Reason step-by-step about the *best short sequence* (1-5 presses) of button actions (e.g., ['down', 'down', 'a']) to make progress towards the goal based *specifically* on the current observation and memory.\n"
        "   - If in a battle, decide the next move.\n"
        "   - If in a menu, navigate or select.\n"
        "   - If exploring, decide where to move or interact.\n"
        "   - If in dialogue, advance it (usually 'a' or 'b').\n"
        "3. Clearly state your reasoning.\n"
        "4. Use the 'Press Game Buttons' tool with the exact list of chosen button presses."
    ),
    expected_output=(
        "1. **Reasoning:** [Your step-by-step reasoning for the chosen actions based on observation, memory, and goal.]\n"
        "2. **Action:** [The list of button presses you decided on, e.g., ['a', 'a']].\n"
        "3. **Execution Result:** [Confirmation message from the 'Press Game Buttons' tool.]"
    ),
    agent=planner_agent,
    context=[observe_task], # Tell CrewAI this task depends on the output of observe_task
    tools=[press_tool]      # Explicitly associate tool with task/agent if needed
)

# --- Define the Crew ---
pokemon_crew = Crew(
    agents=[observer_agent, planner_agent],
    tasks=[observe_task, plan_task],
    process=Process.sequential, # IMPORTANT: Observe MUST happen before Plan
    verbose=True,
    memory=False, # Global memory off, passed via context
    manager_llm=llm # Optional: can use a manager LLM or let agents coordinate
)

# --- Game Loop ---
running = True
turn = 0

print(f"\nStarting CrewAI game loop with {MAX_TURNS} max turns...")
print(f"Goal: {GAME_GOAL}")
print("Press Ctrl+C to stop the loop.")
print("-" * 50)

try:
    while running and turn < MAX_TURNS:
        print(f"\n===== Turn {turn + 1}/{MAX_TURNS} =====")

        # Generate memory summary for the current turn
        memory_summary = game_memory.generate_summary()
        print(f"--- Memory Summary for Turn ---\n{memory_summary}\n-----------------------------")

        # Prepare inputs for the task
        task_inputs = {
            'turn_number': turn + 1,
            'current_goal': GAME_GOAL,
            'memory_summary': memory_summary
        }

        # Kick off the crew for one turn
        print("--- Kicking off CrewAI Task ---")
        try:
            # The result will contain the final output of the task/agent
            result = pokemon_crew.kickoff(inputs=task_inputs)
            print("\n--- CrewAI Task Result ---")
            print(result)
            print("--------------------------")

        except Exception as e:
            print(f"\nError during CrewAI kickoff: {str(e)}")
            traceback.print_exc()
            # Decide if you want to stop or try to continue
            # running = False
            print("Attempting to continue to the next turn...")

        # Increment turn counter
        turn += 1

        # Delay between turns
        print(f"Waiting {TURN_DELAY} seconds before next turn...")
        time.sleep(TURN_DELAY)

except KeyboardInterrupt:
    print("\nGame loop interrupted by user.")
    running = False
except Exception as e:
    print(f"\nUnexpected error in game loop: {str(e)}")
    traceback.print_exc()
    running = False
finally:
    pass
    # # Final message
    # if turn >= MAX_TURNS:
    #     print(f"\nGame session ended after reaching {MAX_TURNS} turns.")
    # else:
    #     print(f"\nGame session ended after {turn} turns.")

    # # Optional: Save final memory state or other logs if needed
    # try:
    #     final_memory_file = os.path.join(screenshot_dir, "final_memory.txt")
    #     with open(final_memory_file, 'w') as f:
    #         f.write(game_memory.generate_summary(full_history=True)) # Save full history maybe
    #     print(f"Saved final game memory summary to {final_memory_file}")
    # except Exception as e:
    #     print(f"Error saving final memory: {str(e)}")

    # print("Exiting program.")
    # sys.exit(0)