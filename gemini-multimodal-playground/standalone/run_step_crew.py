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

            return base64_image
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

def create_vision_agent(tools):
    return Agent(
        role="Vision Analyst",
        goal="Analyze game screens to identify objects, characters, and navigable paths",
        backstory="""You are a cartographer who looks at gameboy screens and describes what you see there and what actions are possible for the player.""",
        tools=tools,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        multimodal=True
    )

# Define the Agent
game_analyst = Agent(
    role='Expert Pokemon Player',
    goal=f"Analyze the current Pokemon game screen, consult the game memory, and decide the best sequence of button presses to achieve the overall objective: '{GAME_GOAL}'. Then execute those presses.",
    backstory=(
        "You are an AI agent controlling a Pokemon game via an emulator. "
        "You observe the game world through screenshots provided by the 'Capture Game Screen' tool. "
        "You have access to a 'Game Memory' summarizing past actions and observations. "
        "Your goal is to navigate the game world and achieve objectives. "
        "You execute actions using the 'Press Game Buttons' tool, providing a list of button presses. "
        "Think step-by-step: 1. Capture screen. 2. Analyze screen + memory. 3. Decide action(s). 4. Execute using Press Game Buttons tool."
    ),
    verbose=True,
    memory=False, # We are managing memory manually via context
    llm=llm,
    tools=[capture_tool, press_tool],
    allow_delegation=False
)

analysis_task = Task(
    description=(
        "**Turn Number:** {turn_number}\n"
        "**Overall Goal:** {current_goal}\n\n"
        "**Game Memory Summary:**\n{memory_summary}\n\n"
        "**Instructions:**\n"
        "1. Use the 'Capture Game Screen' tool to get the current visual state of the game. You MUST do this first.\n"
        "2. Analyze the captured screen image along with the provided Game Memory Summary and the Overall Goal.\n"
        "3. Based on your analysis, decide the *best sequence* of button presses (e.g., ['down', 'down', 'a']) to make progress towards the goal. Keep sequences relatively short (e.g., 1-5 presses) to observe the results.\n"
        "4. Use the 'Press Game Buttons' tool with the list of decided button presses.\n"
        "5. Provide a brief summary of your observation, reasoning for the chosen action, and the action itself."
    ),
    expected_output=(
        "A summary of your observation from the screen, your reasoning for the chosen button presses, "
        "and confirmation that the 'Press Game Buttons' tool was used, including the result reported by the tool."
    ),
    agent=game_analyst,

)

# Define the Crew
pokemon_crew = Crew(
    agents=[game_analyst],
    tasks=[analysis_task],
    process=Process.sequential,
    verbose=True, 
    memory=False,
    manager_llm=llm
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