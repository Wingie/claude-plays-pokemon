# Hybrid Mode Specification

## Overview

Hybrid mode allows the Eevee AI system to use different LLM providers for different tasks, optimizing for each provider's strengths:
- **Gemini**: Visual analysis, scene understanding  
- **Mistral**: Strategic decisions, template selection

## Configuration

### Environment Variables (.env)
```bash
LLM_PROVIDER=hybrid
HYBRID_MODE=true
VISUAL_PROVIDER=gemini           # Screenshot analysis
STRATEGIC_PROVIDER=mistral       # Gameplay decisions
TEMPLATE_PROVIDER=mistral        # Template selection

GEMINI_DEFAULT_MODEL=gemini-2.0-flash-exp
MISTRAL_DEFAULT_MODEL=mistral-large-latest
```

## Expected Flow

### Turn Execution
```
1. Visual Analysis (Gemini) → screenshot + visual_context_analyzer template
2. Strategic Decision (Mistral) → memory context + gameplay template  
3. Button Execution → SkyEmu controller
```

### Data Flow
```
Screenshot → Gemini Visual Analysis → JSON Response → Template Variables → Mistral Strategy → Button Press
```

## Current Issues

### Critical Problems
1. **Empty Gemini Responses**: Visual analysis returns 0 chars
2. **JSON Parse Error**: `local variable 'json' referenced before assignment`
3. **Template Variable Missing**: `scene_type` undefined when visual analysis fails
4. **Turn Failures**: All 3 turns failed in test run

### Error Messages
```
📥 Response received: 0 chars
⚠️ WARNING: Empty response from gemini
⚠️ Visual analysis failed: local variable 'json' referenced before assignment
⚠️ Prompt manager failed: Missing required variable for prompt exploration_strategy: 'scene_type'
```

## Required Fixes

### 1. Fix JSON Variable Bug (visual_analysis.py)
- Import json module properly
- Initialize json variable before use
- Add proper error handling

### 2. Empty Response Fallback
- Default visual context when Gemini fails
- Retry logic with exponential backoff
- Provider switching (Gemini → Mistral vision)

### 3. Template Variable Safety
- Provide default values for required variables
- Safe template rendering when partial data available
- Graceful degradation for visual analysis failures

## Success Criteria

### Working Hybrid Mode Should:
1. **Visual Analysis**: Return structured JSON with scene_type, spatial_context
2. **Strategic Decisions**: Use visual context for better gameplay
3. **Error Recovery**: Continue gameplay when visual analysis fails
4. **Provider Benefits**: Leverage Gemini vision + Mistral strategy effectively

### Test Validation
- All 3 test turns complete successfully
- Visual analysis returns valid JSON or safe defaults
- Strategic decisions use visual context appropriately
- No crashes from missing template variables