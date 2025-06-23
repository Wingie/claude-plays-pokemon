# JSON-Only Response Standardization Specification

## Overview

This document defines the unified JSON response format that all LLM providers (Gemini, Mistral) must use for consistent parsing and integration.

## 🎯 Standard JSON Response Format

### Core Response Structure
```json
{
  "button_presses": ["up"],
  "reasoning": "Brief explanation of decision",
  "observations": "What I see on screen",
  "context_detected": "battle|navigation|menu|unknown",
  "confidence": "high|medium|low"
}
```

### Field Specifications

#### `button_presses` (Required)
- **Type**: Array of strings
- **Valid values**: ["up", "down", "left", "right", "a", "b", "start", "select"]
- **Max length**: 3 buttons per response
- **Examples**: 
  - `["a"]` - Single button press
  - `["up", "a"]` - Movement then action
  - `["down", "right", "a"]` - Navigation sequence

#### `reasoning` (Required)
- **Type**: String
- **Max length**: 200 characters
- **Purpose**: Brief explanation of why these buttons were chosen
- **Examples**:
  - `"Battle menu visible, selecting FIGHT option"`
  - `"Character can move up, continuing exploration"`
  - `"Stuck pattern detected, trying opposite direction"`

#### `observations` (Required)
- **Type**: String
- **Max length**: 300 characters
- **Purpose**: Neutral description of what's visible on screen
- **Examples**:
  - `"Four-option menu with FIGHT highlighted and triangle cursor"`
  - `"Small character sprite on grassy terrain with trees around"`
  - `"Text box with battle damage numbers and HP bar"`

#### `context_detected` (Required)
- **Type**: String (enum)
- **Valid values**: 
  - `"battle"` - Pokemon battle is active
  - `"navigation"` - Overworld movement/exploration
  - `"menu"` - In a menu or dialog screen
  - `"unknown"` - Cannot determine context
- **Purpose**: AI's assessment of current game state

#### `confidence` (Optional)
- **Type**: String (enum)
- **Valid values**: ["high", "medium", "low"]
- **Purpose**: AI's confidence in its decision
- **Default**: "medium" if not specified

## 🔄 Template-Specific Formats

### Battle Analysis Response
```json
{
  "button_presses": ["a"],
  "reasoning": "Selecting FIGHT to access move selection",
  "observations": "Battle menu showing FIGHT/BAG/POKEMON/RUN options",
  "context_detected": "battle",
  "confidence": "high",
  "battle_phase": "menu_selection",
  "move_strategy": "offensive"
}
```

### Navigation Response
```json
{
  "button_presses": ["up"],
  "reasoning": "Path is clear north, continuing exploration",
  "observations": "Character on route with grass patches and trees",
  "context_detected": "navigation", 
  "confidence": "high",
  "exploration_goal": "find_trainer_battles"
}
```

### Stuck Recovery Response
```json
{
  "button_presses": ["left"],
  "reasoning": "Breaking stuck pattern by trying perpendicular direction",
  "observations": "Same screen position for 3+ turns",
  "context_detected": "navigation",
  "confidence": "medium",
  "recovery_strategy": "perpendicular_escape"
}
```

## 🚫 Prohibited Response Elements

### NO Character Roleplay
- ❌ "I'm Ash Ketchum and I see..."
- ❌ "My Pokemon are ready for battle!"
- ✅ "Battle menu with move selection visible"

### NO Narrative Text
- ❌ "Let me analyze this exciting Pokemon battle..."
- ❌ "Time to explore the wonderful world of Pokemon!"
- ✅ Pure JSON with factual observations only

### NO Code Blocks or Markdown
- ❌ ```json\n{...}\n```
- ❌ **Bold** or *italic* formatting
- ✅ Raw JSON object only

## 🔧 Prompt Integration Guidelines

### For All Templates
Add this to every prompt template:

```
**RESPONSE FORMAT (MANDATORY):**
Return ONLY a JSON object with no additional text:

{
  "button_presses": ["button"],
  "reasoning": "why this action",
  "observations": "what you see",
  "context_detected": "battle|navigation|menu|unknown",
  "confidence": "high|medium|low"
}

Do not include any text before or after the JSON. No markdown, no code blocks, no explanations.
```

### Validation Examples
Provide these examples in prompts:

**✅ CORRECT:**
```json
{"button_presses": ["a"], "reasoning": "Confirming menu selection", "observations": "Menu with highlighted option", "context_detected": "menu"}
```

**❌ INCORRECT:**
```
Here's my analysis: The Pokemon battle is intense! 
```json
{"button_presses": ["a"]}
```
```

## 🧪 Testing Requirements

### Validation Criteria
1. **JSON Parse Test**: Response must parse as valid JSON
2. **Required Fields**: All mandatory fields must be present
3. **Button Validation**: All button names must be valid
4. **Length Limits**: Text fields must not exceed specified limits
5. **No Extra Text**: Response must contain ONLY the JSON object

### Test Cases
- Battle scene recognition
- Navigation decision making  
- Menu navigation
- Stuck pattern recovery
- Error handling with invalid visual input

## 📊 Benefits of Standardization

### Improved Reliability
- Consistent parsing across all providers
- No regex pattern matching required
- Clear error identification

### Better Debugging
- Structured observations for analysis
- Confidence scoring for decision quality
- Standardized reasoning format

### Enhanced Integration
- Direct JSON validation
- Simplified response processing
- Provider-agnostic parsing logic