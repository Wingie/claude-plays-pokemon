import os
import sys
import time
import traceback
import base64
import shutil # Import shutil for file operations
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from langchain_google_genai import ChatGoogleGenerativeAI # Use Langchain wrapper for CrewAI
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

from pokemon_controller import PokemonController, read_image_to_base64
from gamememory import GameMemory, init_message # 
load_dotenv()
# Configure the emulator window title
WINDOW_TITLE = "mGBA - 0.10.5"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
# Game loop configuration
running = True
MAX_TURNS = 10  # Limit the number of turns
turn = 0
TURN_DELAY = 1.0  # Delay between turns in seconds
save_screenshots = True  # Whether to save screenshots for later review
screenshot_dir = "screenshots"  # Directory to save screenshots

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-g", "--goal", dest="goal",
                    help="short term run goal", metavar="FILE")
args = parser.parse_args()
GAME_GOAL= args.goal

# Create screenshots directory if it doesn't exist and save_screenshots is enabled
if save_screenshots:
    try:
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            print(f"Created directory for screenshots: {screenshot_dir}")
    except Exception as e:
        print(f"Error creating screenshots directory: {str(e)}")
        save_screenshots = False

# Initialize Gemini client and Pokemon controller
def init_game():
    try:
        controller = PokemonController(region=None, window_title=WINDOW_TITLE)
        game_memory = GameMemory()
        llm = LLM(
            model="gemini/gemini-2.0-flash", # Or another specific Gemini model ID
            api_key=GEMINI_API_KEY
        )
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
        return (model, controller, window, game_memory, llm)
    except Exception as e:
        print(f"Error initializing: {str(e)}")
        # traceback.print_exc()  # Print the full traceback
        sys.exit(1)
