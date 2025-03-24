# Gemini Plays Pokemon

This project uses Google's Gemini AI to play Pokemon games on an mGBA emulator automatically. The AI analyzes screenshots from the game and decides which buttons to press.

## Setup

### Prerequisites

- Python 3.8+
- mGBA emulator (version 0.10.5) with Pokemon game loaded
- Google Gemini API key

### Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project directory with your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

1. Start the mGBA emulator and load a Pokemon game (ideally Pokemon Yellow)
2. Make sure the window title contains "mGBA - 0.10.5" (or edit the `WINDOW_TITLE` variable in `run_step_gemini.py`)
3. Run the script:
   ```
   python run_step_gemini.py
   ```

The script will:
- Capture screenshots from the emulator
- Send these to Gemini AI
- Get a response with a button to press
- Press that button on the emulator
- Repeat until the maximum number of turns is reached or you interrupt with Ctrl+C

## Configuration

You can modify the following variables in `run_step_gemini.py`:
- `max_turns`: Maximum number of turns (default: 100)
- `turn_delay`: Delay between turns in seconds (default: 1.0)
- `save_screenshots`: Whether to save screenshots for later review (default: True)
- `screenshot_dir`: Directory to save screenshots and conversation log (default: "screenshots")

## Troubleshooting

- **Emulator window not found**: Make sure the mGBA emulator is running with the correct window title
- **API errors**: Check your API key and internet connection
- **Blank screenshots**: The window capture might be failing. Try running the emulator in windowed mode

## Files

- `run_step_gemini.py`: Main script that orchestrates the AI gameplay
- `pokemon_controller.py`: Controls the emulator via keyboard inputs
- `gemini_connection.py`: Handles communication with the Gemini API
- `voice_activity_detector.py`: Used for voice detection (not used in the main gameplay loop)
- `standalone.py`: Alternative implementation (not used in the main gameplay)
- `config_gui.py`: GUI configuration (not used in the main gameplay)

## Extending the Project

To extend or modify this project:
1. Adjust the system prompt in `run_step_gemini.py` to change the AI's behavior
2. Modify `pokemon_controller.py` to support additional buttons or sequences
3. Consider adding image preprocessing to improve AI decision making