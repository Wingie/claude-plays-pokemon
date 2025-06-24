# Eevee Logging Strategy Specification

## Overview

This document defines the logging strategy for the Eevee Pokemon AI system, focusing on clean console output for users while maintaining comprehensive debug logging for development.

## Current State Analysis

### Files Generated in `runs/session_*` Folders

| File | Source | Purpose | Status |
|------|--------|---------|--------|
| `debug.log` | `evee_logger.py` | General debug info | ✅ Keep |
| `gemini_debug.log` | `evee_logger.py` | Detailed Gemini API calls/errors | ✅ Keep |
| `hybrid_mode.log` | `evee_logger.py` | Provider routing decisions | ✅ Keep |
| `visual_analysis.log` | `evee_logger.py` | Visual analysis details | ✅ Keep |
| `stdout.log` | `evee_logger.py` | Console output capture | ✅ Keep |
| `stderr.log` | `evee_logger.py` | Error output capture | ✅ Keep |
| `session_data.json` | `run_eevee.py` | Session metadata | ✅ Keep |
| `dataset_metadata.json` | `run_eevee.py` | Fine-tuning data | ✅ Keep |
| `fine_tuning_dataset.jsonl` | `run_eevee.py` | Training examples | ✅ Keep |
| `step_XXXX_visual_analysis.txt` | `visual_analysis.py` | Per-step visual analysis | ✅ Keep |
| `step_XXXX_grid.png` | `visual_analysis.py` | Screenshots with grid overlay | ✅ Keep |
| `diary_day_X.md` | `diary_generator.py` | Episode summaries | ✅ Keep |

## Target Console Output (User Requirement)

### Console Output (Production Mode)

**ONLY show on console:**

1. **Visual Analysis JSON** (pretty-printed from Gemini)
2. **Strategic Decision JSON** (reasoning + button press from Mistral)

```bash
=== VISUAL ANALYSIS ===
{
  "scene_type": "battle",
  "battle_data": {
    "our_pokemon": {
      "name": "PIKA",
      "hp": "14/26", 
      "level": 9
    },
    "enemy_pokemon": {
      "name": "METAPOD",
      "hp": null,
      "level": 7
    },
    "cursor_position": "FIGHT"
  },
  "valid_buttons": [
    {
      "key": "A",
      "action": "select_attack",
      "result": "perform_attack"
    }
  ],
  "recommended_template": "ai_directed_battle"
}

=== STRATEGIC DECISION ===
{
  "button_presses": ["a"],
  "reasoning": "Battle menu detected in visual context, selecting FIGHT option to engage in combat",
  "observations": "Four-option battle menu visible with spatial layout information",
  "context_detected": "battle",
  "confidence": "high"
}
```

### Move to Debug Logs

**Everything else goes to debug logs:**
- All verbose messages with emojis (🔍, 📤, ⚠️, ✅, 🔀, etc.)
- Provider routing information
- Template selection details
- Processing times and metrics
- API debugging information
- Error handling details
- Memory context information

## Implementation Requirements

### 1. No Output Truncation

**CRITICAL**: Remove ALL `[:200]` truncation patterns across the codebase. User wants full output visibility.

**Files to check:**
- `evee_logger.py` 
- `visual_analysis.py`
- `run_eevee.py`
- `llm_api.py`

### 2. Console Output Methods

#### New Methods in `evee_logger.py`:

```python
def log_visual_analysis_console(self, visual_data: dict):
    """Pretty-print visual analysis JSON to console only"""
    
def log_strategic_decision_console(self, decision_data: dict): 
    """Pretty-print strategic decision JSON to console only"""
```

#### Console Output Logic:

```python
# visual_analysis.py - replace verbose prints
if clean_output_mode:
    logger.log_visual_analysis_console(parsed_visual_data)
else:
    # Keep existing verbose output for development
    
# run_eevee.py - replace strategic decision prints  
if clean_output_mode:
    logger.log_strategic_decision_console(strategic_result)
else:
    # Keep existing verbose output for development
```

### 3. Debug Log Categories

| Category | File | Content |
|----------|------|---------|
| `debug.log` | General | Template selection, memory context, processing flows |
| `visual_analysis.log` | Visual | Full visual analysis details, prompt/response pairs |
| `hybrid_mode.log` | Routing | Provider selection, model routing decisions |
| `gemini_debug.log` | API | Detailed Gemini API calls, safety filter info |

### 4. Command Line Interface

Add `--clean-output` flag:

```bash
# Clean production output
python run_eevee.py --goal "win battle" --clean-output

# Verbose development output  
python run_eevee.py --goal "win battle" --verbose
```

## File Modifications Required

### High Priority

1. **`specs/logging_strategy.md`** - ✅ This document
2. **Remove `[:200]` patterns** - Search and replace across codebase  
3. **`visual_analysis.py`** - Add clean JSON console output
4. **`run_eevee.py`** - Add clean JSON console output for strategic decisions

### Medium Priority

5. **`visual_analysis.py`** - Move emoji prints to debug logs
6. **`run_eevee.py`** - Move emoji prints to debug logs
7. **`llm_api.py`** - Move emoji prints to debug logs  
8. **`evee_logger.py`** - Add strategic decision logging method

### Low Priority

9. **Command line flags** - Add `--clean-output` option

## Expected Benefits

1. **Clean user experience** - Only essential JSON output on console
2. **Complete debugging** - All details preserved in log files
3. **Developer friendly** - Verbose mode still available for development
4. **Full visibility** - No truncated output anywhere
5. **Structured data** - JSON format for easy parsing/analysis

## Backward Compatibility

- All existing log files remain unchanged
- Verbose mode preserves current behavior
- Clean mode is opt-in via flag
- Debug logs maintain full detail for troubleshooting

## Testing Strategy

1. Run with `--clean-output` - verify only JSON appears on console
2. Run with `--verbose` - verify all debug info still works  
3. Check log files - verify all details are captured
4. Verify no `[:200]` truncation anywhere
5. Test both Gemini visual analysis and Mistral strategic decisions