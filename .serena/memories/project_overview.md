# Project Overview

## Purpose
This is a comprehensive AI-powered Pokemon gaming project with multiple components:

1. **Claude Plays Pokemon** - Main project using Google Gemini AI to automatically play Pokemon games on Game Boy emulators
2. **VideoGameBench Integration** - Extension of videogamebench framework to support Pokemon Fire Red with RL+LLM hybrid agents
3. **SkyEmu MCP Server** - Model Context Protocol server for controlling SkyEmu emulator via HTTP API
4. **Gemini Multimodal Playground** - Experimental AI playground with RL algorithms and multimodal interaction

## Main Tech Stack
- **Python 3.8+** as primary language
- **Google Gemini API** for AI decision making and multimodal reasoning
- **SkyEmu Emulator** with HTTP Control Server for Game Boy Advance games
- **mGBA Emulator** for Game Boy games
- **PyBoy** (in videogamebench) for Game Boy emulation
- **PyAutoGUI** for automated input simulation
- **PIL/Pillow** for image processing and screenshot capture
- **Quartz** (macOS) for window management and screen capture
- **FastAPI** for REST API development
- **LiteLLM** for unified LLM API interface
- **PyTorch** for RL agent implementation

## Project Architecture
The project is organized into several interconnected components:
- Root level: Basic Gemini-powered Pokemon controller
- `videogamebench/`: Comprehensive VLM evaluation framework
- `skyemu-mcp/`: MCP server for SkyEmu integration
- `gemini-multimodal-playground/`: Experimental playground with advanced features
- `SkyEmu/`: Emulator source code (C++)

## Target Platform
- Primary development on **macOS** (Darwin)
- Uses macOS-specific APIs (Quartz, pyobjc)
- Designed for Apple Silicon optimization