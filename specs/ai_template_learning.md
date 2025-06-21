# AI Template Learning System Specification

## Overview

The AI Template Learning System is a revolutionary self-improvement mechanism that automatically enhances Pokemon gameplay prompt templates based on real performance data.

## Core Architecture

### Components

1. **Template Usage Tracker**: Records which template was used for each turn
2. **Performance Analyzer**: Analyzes success/failure patterns and stuck behaviors  
3. **AI Template Reviewer**: Uses Gemini to identify which templates need improvement
4. **AI Template Improver**: Uses Gemini 2.0 Flash to generate better templates
5. **Template Persistence**: Saves improved templates to YAML with version tracking

### Data Flow

```
Turn N: Screenshot → Template Selection → AI Decision → Button Press → Result Recording
        ↓
Every episode_review_frequency turns:
        ↓
Performance Analysis → Failure Detection → Template Identification → AI Improvement → YAML Update
```

## Technical Implementation

### Session Data Enhancement

Each turn in `session_data.json` now includes:
```json
{
  "turn": 1,
  "ai_analysis": "🎯 OBSERVATION: I see a battle menu...",
  "button_presses": ["a"],
  "action_result": true,
  "template_used": "battle_analysis",
  "template_version": "4.0",
  "timestamp": "2025-06-21T08:11:17"
}
```

### Failure Detection Logic

A turn is considered a "failure" if:
1. `action_result` is false (button press failed), OR
2. Turn is part of a stuck pattern (3+ consecutive identical actions)

### Template Eligibility

Only templates from the active selection system can be improved:
- `battle_analysis`
- `exploration_strategy` 
- `stuck_recovery`
- `pokemon_party_analysis`
- `inventory_analysis`
- `task_analysis`

**Never** improves:
- `fallback_*` templates
- `ai_directed_*` templates
- Unused templates

## AI Prompting Strategy

### Step 1: Performance Analysis Prompt

```
# Pokemon AI Template Performance Analysis

## Recent Gameplay Context
Goal: {goal}
Turns analyzed: {N}

## Template Performance Issues
### Template: battle_analysis
- Success rate: 0.33 (1/3)
- Recent failures: 2

**Failure Examples:**
Failure 1:
- AI Analysis: I see a battle menu with FIGHT, BAG...
- AI Decision: ['a', 'b', 'up']
- Result: Failed/No progress

## Your Analysis Task
For each template, determine:
1. Is this template causing actual failures?
2. What specific reasoning patterns are leading to poor decisions?
3. Should this template be improved?

**Response Format:**
TEMPLATE: battle_analysis
NEEDS_IMPROVEMENT: yes
REASONING: AI is pressing too many buttons in battles, causing menu confusion
PRIORITY: high
```

### Step 2: Template Improvement Prompt

```
# Pokemon AI Template Improvement Task

## Current Template Information
**Template Name:** battle_analysis
**Current Version:** 4.0

## Current Template Content:
```
{current_template_content}
```

## Performance Issues Identified:
AI is pressing too many buttons in battles, causing menu confusion

## Specific Failure Examples:
**Failure 1:**
- AI Reasoning: I see a battle menu with FIGHT, BAG, POKEMON, RUN...
- AI Action: ['a', 'b', 'up']
- Result: Failed to make progress

## Your Task
Generate an improved version that:
1. Fixes the specific reasoning patterns causing failures
2. Maintains the same structure and variables
3. Provides clearer, more actionable guidance

Return ONLY the improved template content.
```

## Configuration

### Command Line Options

- `--episode-review-frequency N`: Run AI review every N turns (default: 100)
- `--max-turns N`: Maximum turns before stopping (for testing)
- `--verbose`: Show detailed AI analysis logging
- `--no-interactive`: Disable interactive mode for automated learning

### Usage Patterns

```bash
# Rapid learning cycles (5-10 minute sessions)
python eevee/run_eevee.py --goal "win battles" --episode-review-frequency 5 --max-turns 20

# Extended learning sessions (30-60 minutes)  
python eevee/run_eevee.py --goal "explore world" --episode-review-frequency 15 --max-turns 100

# Long-term autonomous improvement (hours)
python eevee/run_eevee.py --goal "complete game" --episode-review-frequency 25 --max-turns 500
```

## Output Files

### Session Directory Structure
```
eevee/runs/session_20250621_081117/
├── session_data.json           # Enhanced with template metadata
├── periodic_review_turn_5.md   # AI analysis reports
├── periodic_review_turn_10.md  
└── screenshots/
```

### Template Files
```
eevee/prompts/base/base_prompts.yaml    # Auto-updated templates
```

## Performance Metrics

### Success Criteria
- **Template Success Rate**: % of turns using template that don't fail
- **Stuck Pattern Count**: Number of 3+ consecutive identical actions
- **Template Attribution**: Which templates caused which failures

### Learning Indicators
```
🔧 AI-POWERED PROMPT LEARNING: Applied 2 improvements
   📝 battle_analysis v4.0 → v4.1
      Reason: Improved move selection logic
   📝 exploration_strategy v2.1 → v2.2  
      Reason: Better stuck pattern recovery
   🔄 RELOADED PROMPT TEMPLATES - AI will now use improved versions
```

## Error Handling

### Graceful Degradation
- If AI analysis fails → Continue with existing templates
- If template improvement fails → Log warning, continue
- If YAML save fails → Log error, templates stay in memory

### Validation
- New templates must be >100 characters
- New templates must differ from original
- YAML syntax validation before save
- Template variable preservation check

## Integration Points

### Template Selection System
Uses existing `_determine_prompt_context()` logic to ensure only active templates are improved.

### Memory System  
Integrates with existing session management and logging.

### OKR System
Learning events can trigger OKR progress updates.

## Future Enhancements

### Potential Improvements
1. **Multi-turn Pattern Analysis**: Analyze patterns across 5-10 turns
2. **Template A/B Testing**: Test multiple versions simultaneously  
3. **Contextual Learning**: Different improvements for different game contexts
4. **Human Feedback Integration**: Allow manual template rating
5. **Performance Trending**: Track improvement over time

### Monitoring Opportunities
1. **Template Effectiveness Metrics**: Success rate trends over time
2. **Learning Velocity**: How quickly templates improve
3. **Convergence Detection**: When templates stop improving
4. **Cross-template Learning**: Patterns that help multiple templates

This system represents a breakthrough in automated prompt engineering for game AI.