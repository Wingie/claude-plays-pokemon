# Suggested Commands

## Setup and Installation
```bash
# Install dependencies for main project
pip install -r requirements.txt

# Setup script (includes dependency installation)
./setup.sh

# Test environment setup
python test_setup.py

# VideoGameBench setup
cd videogamebench
conda create -n videogamebench python=3.10
conda activate videogamebench
pip install -r requirements.txt
pip install -e .
playwright install
```

## Running the Applications

### Main Pokemon Controller
```bash
# Run basic Gemini Pokemon controller (requires mGBA)
python run_step_gemini.py

# Test API connection
python gemini_api.py
```

### VideoGameBench
```bash
# Run Pokemon Red with GPT-4o
python main.py --game pokemon_red --model gpt-4o

# Run Game Boy Crystal with Gemini
python main.py --game pokemon_crystal --model gemini/gemini-2.0-flash

# Run with GUI enabled
python main.py --game pokemon_red --model gpt-4o --enable-ui

# Run in headless mode
python main.py --game pokemon_red --model gpt-4o --headless
```

### SkyEmu MCP Server
```bash
cd skyemu-mcp
python run_server.py

# Test MCP tools
python examples/demo_mcp_tools.py
```

## Development Commands

### Testing
```bash
# Test environment setup
python test_setup.py

# Check for basic import issues
python -c "import google.generativeai; import pyautogui; import PIL"
```

### macOS-Specific
```bash
# Check window management (requires emulator running)
python -c "from pokemon_controller import getWindowByTitle; print(getWindowByTitle('mGBA'))"

# Test Quartz screen capture
python -c "import Quartz; print('Quartz available')"
```

### Project Structure Exploration
```bash
# List main project files
ls -la

# Explore videogamebench structure
ls -la videogamebench/

# Check SkyEmu source (C++)
ls -la SkyEmu/src/
```

## Environment Variables Required
```bash
# Required for Gemini API
export GEMINI_API_KEY="your_api_key_here"

# Or create .env file with:
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Common Development Workflow
1. Setup: `./setup.sh`
2. Test: `python test_setup.py` 
3. Run main controller: `python run_step_gemini.py`
4. For videogamebench: `cd videogamebench && python main.py --game pokemon_red --model gpt-4o`

## System Requirements
- macOS (tested on Darwin 24.5.0)
- Python 3.8+ (3.10+ recommended for videogamebench)
- mGBA emulator for main controller
- SkyEmu emulator for advanced features
- Valid Gemini API key