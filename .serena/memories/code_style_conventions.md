# Code Style and Conventions

## Python Style
- **Standard Python conventions** following PEP 8
- **Class names**: PascalCase (e.g., `PokemonController`, `GeminiAPI`)
- **Function/method names**: snake_case (e.g., `press_button`, `capture_screen`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `WINDOW_TITLE`, `GEMINI_API_KEY`)
- **File names**: snake_case (e.g., `pokemon_controller.py`, `run_step_gemini.py`)

## Documentation
- **Docstrings**: Google-style docstrings for classes and functions
- **Type hints**: Used consistently for function parameters and return types
- **Inline comments**: Minimal, focusing on complex logic and emulator-specific details

## Error Handling
- **Graceful degradation**: Applications continue running with fallbacks when possible
- **Informative error messages**: Clear guidance for common setup issues
- **Exception handling**: Try-catch blocks for external API calls and system operations

## Configuration Management
- **Environment variables**: Used for API keys and sensitive configuration
- **Config files**: YAML/TOML for game-specific settings
- **Default values**: Sensible defaults provided for optional parameters

## Import Style
- **Standard library first**, then third-party, then local imports
- **Absolute imports** preferred over relative imports
- **Dynamic imports** used for optional dependencies

## API Design Patterns
- **Class-based controllers** for emulator interaction
- **Message-based APIs** for LLM communication (following OpenAI-style patterns)
- **Tool-based interfaces** for AI agent actions
- **REST APIs** for emulator control (SkyEmu HTTP API)

## File Organization
- **Root level**: Main entry points and simple controllers
- **Subdirectories**: Organized by functionality (src/, configs/, examples/)
- **Configuration separation**: Game configs in dedicated folders
- **Resource management**: Screenshots, saves, and assets in designated directories

## macOS-Specific Considerations
- **Quartz integration** for native window management
- **pyobjc usage** for Core Graphics and window operations
- **Apple Silicon optimization** where applicable
- **Screen capture**: Native macOS APIs preferred over cross-platform alternatives

## Testing Approach
- **Environment validation**: Setup test scripts to verify dependencies
- **Integration testing**: Real emulator testing with actual games
- **Manual verification**: Human-in-the-loop testing for AI behavior
- **Error condition testing**: Handling of missing windows, API failures, etc.

## Performance Considerations
- **Screenshot optimization**: JPEG compression for AI processing
- **API rate limiting**: Intelligent delays and batching for Gemini calls
- **Memory management**: Cleanup of temporary files and images
- **Real-time constraints**: Fast response times for game interaction