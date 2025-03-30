# SkyEmu MCP Server

An MCP (Model Context Protocol) server for controlling SkyEmu through natural language commands via Claude or other LLMs.

## Overview

This project provides a bridge between Large Language Models (LLMs) like Claude and the SkyEmu emulator. It allows the LLM to control any game running in SkyEmu by translating natural language commands into emulator actions.

## Prerequisites

- Python 3.8 or higher
- SkyEmu with HTTP Control Server enabled (port 8080 by default)
- Claude (or another LLM that supports MCP)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/skyemu-mcp.git
   cd skyemu-mcp
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Setting up SkyEmu

1. Start SkyEmu and enable the HTTP Control Server:
   - Go to Advanced Settings
   - Enable "HTTP Control Server"
   - Set the port to 8080 (or update the port in the code)
   - Load a ROM file

2. Alternatively, launch SkyEmu in headless mode:
   ```
   ./SkyEmu http_server 8080 /path/to/rom.gba
   ```

### Running the MCP Server

Start the MCP server:

```
python skyemu_mcp_server.py
```

The server will connect to SkyEmu and provide tools for controlling the emulator through MCP.

### Connecting with Claude

In your conversation with Claude, you can now use natural language to control SkyEmu:

```
You: "Move the character to the right and press A to talk to the NPC"
Claude: [uses MCP tools to control SkyEmu]
```

## Available Tools

The MCP server exposes the following tools:

- **press_button**: Press a button on the emulated controller
- **press_sequence**: Press a sequence of buttons in order
- **hold_buttons**: Hold down multiple buttons simultaneously
- **release_buttons**: Release previously held buttons
- **release_all_buttons**: Release all buttons
- **get_screenshot**: Get a screenshot of the current game state
- **step_frames**: Step the emulator forward by frames
- **run_emulator**: Start/resume the emulator
- **save_state**: Save the game state to a file
- **load_state**: Load a saved game state
- **load_rom**: Load a ROM file
- **get_emulator_status**: Get the emulator status
- **execute_sequence**: Execute a complex sequence of actions
- **perform_directional_movement**: Simple directional movement
- **navigate_menu**: Navigate through game menus

## Example Commands

Here are some examples of natural language commands that Claude can process:

- "Move the character to the right for 5 steps"
- "Press A to talk to the character in front of me"
- "Navigate to the 'Save Game' option in the menu and select it"
- "Take a screenshot of the current game state"
- "Save the game state to 'mysave.png'"
- "Hold down the B button while moving right"

## Troubleshooting

- Ensure SkyEmu's HTTP server is running on the expected port
- Check that you have the correct buttons for your game (some games may use different control schemes)
- If the connection fails, try restarting both SkyEmu and the MCP server

## License

[Your license information here]

## Acknowledgments

- SkyEmu for providing the HTTP Control Server API
- Model Context Protocol for the framework
- [Add any other acknowledgments]
