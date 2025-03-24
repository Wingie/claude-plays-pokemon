#!/usr/bin/env python3
import os
import sys

print("Checking environment...")

# Check if GEMINI_API_KEY is set
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Check if .env file exists
    if os.path.exists(".env"):
        print("✅ .env file found")
        # Try to load it
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        print("✅ GEMINI_API_KEY found in .env file")
                        break
                else:
                    print("❌ GEMINI_API_KEY not found in .env file")
                    print("Please add GEMINI_API_KEY=your_key_here to your .env file")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print("❌ .env file not found")
        print("Please create a .env file with your GEMINI_API_KEY")
else:
    print("✅ GEMINI_API_KEY found in environment")

# Check required packages
try:
    import google.generativeai
    print("✅ google.generativeai package installed")
except ImportError:
    print("❌ google.generativeai package not found")
    print("Install with: pip install google-generativeai")

try:
    import pyautogui
    print("✅ pyautogui package installed")
except ImportError:
    print("❌ pyautogui package not found")
    print("Install with: pip install pyautogui")

try:
    import PIL
    print("✅ Pillow package installed")
except ImportError:
    print("❌ Pillow package not found")
    print("Install with: pip install Pillow")

try:
    import dotenv
    print("✅ python-dotenv package installed")
except ImportError:
    print("❌ python-dotenv package not found")
    print("Install with: pip install python-dotenv")

# Check if the standalone directory exists
standalone_dir = os.path.join(os.path.dirname(__file__), "gemini-multimodal-playground", "standalone")
if os.path.exists(standalone_dir):
    print(f"✅ Found standalone directory: {standalone_dir}")
else:
    print(f"❌ Standalone directory not found: {standalone_dir}")

print("\nRun the script with: python run_step_gemini.py")
