# Task Completion Checklist

## After Completing Any Coding Task

### 1. Code Quality Verification
- [ ] **Check imports**: Ensure all imports are properly organized
- [ ] **Verify syntax**: Run basic Python syntax validation
- [ ] **Type consistency**: Check that function parameters and returns match expected types
- [ ] **Error handling**: Ensure graceful handling of common failure modes

### 2. Environment Testing
- [ ] **Run test script**: Execute `python test_setup.py` to verify dependencies
- [ ] **Import validation**: Test that all new modules can be imported
- [ ] **API connectivity**: Verify Gemini API connection if relevant
- [ ] **Emulator compatibility**: Test with target emulator if game-related

### 3. Integration Testing
- [ ] **Main entry points**: Test that `python run_step_gemini.py` works
- [ ] **VideoGameBench**: Test relevant videogamebench functionality if modified
- [ ] **MCP server**: Test SkyEmu MCP server if modified
- [ ] **Cross-component compatibility**: Ensure changes don't break other modules

### 4. macOS-Specific Validation
- [ ] **Window management**: Test Quartz-based window finding and capturing
- [ ] **Screen capture**: Verify screenshot functionality works correctly
- [ ] **Permissions**: Check that accessibility permissions are sufficient
- [ ] **Native APIs**: Test pyobjc and macOS-specific functionality

### 5. Documentation Updates
- [ ] **Docstrings**: Update docstrings for new or modified functions
- [ ] **README updates**: Update relevant README files if functionality changed
- [ ] **Configuration docs**: Update config documentation if new settings added
- [ ] **Example updates**: Update example code if APIs changed

### 6. File Management
- [ ] **Cleanup temporary files**: Remove test screenshots, temp files
- [ ] **Check .gitignore**: Ensure sensitive files (.env, saves) are excluded
- [ ] **Organize outputs**: Ensure screenshots/ and logs/ directories are properly managed
- [ ] **Resource cleanup**: Clean up any downloaded ROMs or temporary assets

## Before Committing Changes

### 7. Final Validation
- [ ] **Clean run**: Fresh run of main functionality from clean state
- [ ] **Error scenarios**: Test common error conditions (missing API key, no emulator)
- [ ] **Resource usage**: Check for memory leaks or excessive resource consumption
- [ ] **Performance**: Verify no significant performance regressions

### 8. Security Check
- [ ] **API key security**: Ensure no API keys are hardcoded or committed
- [ ] **Sensitive data**: Check for accidentally included save files or personal data
- [ ] **File permissions**: Verify appropriate file permissions on scripts and configs

## Project-Specific Checks

### For Pokemon Controller Changes
- [ ] **Game compatibility**: Test with target Pokemon games
- [ ] **Button mapping**: Verify all game controls work correctly
- [ ] **AI reasoning**: Test that Gemini responses are properly parsed
- [ ] **Screenshot quality**: Ensure screenshots are clear and properly formatted

### For VideoGameBench Changes
- [ ] **Game configurations**: Test affected game configs
- [ ] **Agent interfaces**: Verify agent APIs still work correctly
- [ ] **Logging functionality**: Check that logs are generated properly
- [ ] **Multi-model support**: Test with different LLM providers if applicable

### For SkyEmu Integration Changes
- [ ] **HTTP API**: Test SkyEmu HTTP server communication
- [ ] **Memory reading**: Verify game state reading functionality
- [ ] **Save state handling**: Test save/load functionality
- [ ] **Emulator stability**: Check for crashes or stability issues

## No Linting/Formatting Tools
**Note**: This project does not currently use automated linting or formatting tools like flake8, black, or mypy. Code quality is maintained through manual review and testing.