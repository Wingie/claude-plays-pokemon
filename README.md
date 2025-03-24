# Claude Plays Pokemon with Gemini

This project uses Google's Gemini AI to play Pokemon games on an mGBA emulator automatically. The AI analyzes screenshots from the game and decides which buttons to press.

## Setup

### Prerequisites

- Python 3.8+
- mGBA emulator with Pokemon game loaded
- Google Gemini API key

### Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root directory with your Gemini API key:
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

## How It Works

1. The script captures screenshots of the mGBA emulator window
2. These screenshots are sent to the Google Gemini API along with instructions
3. Gemini analyzes the game state and decides which button to press
4. The script simulates the button press on the emulator
5. This process repeats until you stop the script or it reaches the maximum number of turns

## Configuration

You can modify these variables at the top of `run_step_gemini.py`:
- `max_turns`: Maximum number of turns (default: 100)
- `turn_delay`: Delay between turns in seconds (default: 1.0)
- `save_screenshots`: Whether to save screenshots for later review
- `screenshot_dir`: Directory to save screenshots

## Troubleshooting

- **Emulator window not found**: Make sure mGBA is running with the correct window title
- **API errors**: Check your API key and internet connection
- **Blank screenshots**: The window capture might be failing. Try running the emulator in a different screen position

## Dependencies

- `google-generativeai`: Google's Gemini API client
- `python-dotenv`: For loading environment variables
- `pyautogui`: For simulating key presses
- `Pillow`: For image processing
- `pyobjc`: For macOS window management

## Extending

- Modify the system prompt to adjust AI behavior
- Add more sophisticated button sequences for complex actions
- Implement image preprocessing to improve AI perception
- Add game state memory to make the AI remember previous actions