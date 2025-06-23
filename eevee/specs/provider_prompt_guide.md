# Provider-Specific Prompt Best Practices

## Overview

The Eevee AI system now supports provider-specific prompt templates optimized for different AI providers' strengths and preferences. This guide documents best practices for creating effective prompts for each supported provider.

## Supported Providers

### 🔵 Mistral (Pixtral) - Character-First Approach
**Best For**: Immediate action, roleplay, conversational responses

**Key Characteristics**:
- Prefers first-person character roleplay
- Responds well to emotional and personal context
- Works best with conversational, minimal structure
- Excellent at following character constraints

**Prompt Template Structure**:
```yaml
template: |
  I am Ash Ketchum from Pallet Town! I'm [doing activity] on my Game Boy Advance!
  
  My current mission: {task}
  What I just did: {recent_actions}
  
  Looking at my Game Boy Advance screen, [describe what Ash needs to analyze]
  
  RESPONSE RULES:
  - Speak as Ash in first person only
  - Be enthusiastic about the Pokemon adventure
  - Keep response conversational and under 150 words
  - End with one button press
  
  What I see: [description]
  My plan: [action]
  Button press: ['button']
```

**Best Practices**:
- ✅ Start with character identity: "I am Ash Ketchum"
- ✅ Use emotional language: "I'm so excited!", "This is amazing!"
- ✅ Keep structure minimal and conversational
- ✅ Specify response format explicitly
- ✅ Use character-appropriate language
- ❌ Avoid technical documentation format
- ❌ Don't use markdown headers or bullet points
- ❌ Avoid third-person references

### 🟡 Gemini - Documentation-Style Approach  
**Best For**: Detailed analysis, complex reasoning, structured responses

**Key Characteristics**:
- Excels at structured, analytical responses
- Handles complex multi-step instructions well
- Good at following detailed formatting requirements
- Strong at technical documentation style

**Prompt Template Structure**:
```yaml
template: |
  ASH KETCHUM'S [ACTIVITY] STRATEGY v5.0

  ⚔️ You are ASH KETCHUM in a Pokemon [context] on your Game Boy Advance! ⚔️

  **🎯 CORE PRINCIPLES**:
  - [Key principle 1]
  - [Key principle 2]

  **📍 CURRENT SITUATION**:
  Task Context: {task}
  Recent Actions: {recent_actions}

  **🧠 ANALYSIS FRAMEWORK**:
  1. **Observe**: What do you see on screen?
  2. **Analyze**: What does this mean for your Pokemon journey?
  3. **Strategy**: What's your best approach?
  4. **Action**: What button will you press?

  **⚡ EXECUTION RULES**:
  - Maximum 1-2 button presses per turn
  - [Additional constraints]

  Use pokemon_controller with your chosen button sequence.
```

**Best Practices**:
- ✅ Use structured sections with clear headers
- ✅ Provide detailed context and background
- ✅ Include step-by-step analysis frameworks
- ✅ Use markdown formatting (**, ##, bullet points)
- ✅ Specify detailed execution rules
- ❌ Don't make prompts too conversational
- ❌ Avoid overly simple structure

## Template Selection Guidelines

### When to Use Each Provider

**Use Mistral When**:
- Need immediate, intuitive responses
- Want natural character roleplay
- Dealing with simple action decisions
- Require fast, conversational interactions
- Working with vision analysis (Pixtral speciality)

**Use Gemini When**:
- Need detailed strategic analysis
- Working with complex multi-step tasks
- Require structured problem-solving
- Need comprehensive documentation-style responses
- Want sophisticated reasoning capabilities

### Function Calling Considerations

Both providers support function calling but with different approaches:

**Mistral Function Calling**:
```json
{
  "type": "function",
  "function": {
    "name": "pokemon_controller",
    "description": "Control Pokemon game with button presses",
    "parameters": {
      "type": "object",
      "properties": {
        "buttons": {
          "type": "string",
          "description": "Single button press: up, down, left, right, a, b, start, select"
        }
      },
      "required": ["buttons"]
    }
  }
}
```

**Gemini Function Calling**:
```python
from google.generativeai.types import Tool, FunctionDeclaration

pokemon_function = FunctionDeclaration(
    name="pokemon_controller",
    description="Control Pokemon game with button presses",
    parameters={
        "type": "object",
        "properties": {
            "buttons": {
                "type": "string",
                "description": "Single button press: up, down, left, right, a, b, start, select"
            }
        },
        "required": ["buttons"]
    }
)
```

## Implementation Guide

### Directory Structure
```
prompts/
├── providers/
│   ├── mistral/
│   │   └── base_prompts.yaml
│   └── gemini/
│       └── base_prompts.yaml
├── base/
│   └── base_prompts.yaml  # Fallback templates
└── playbooks/
    ├── battle.md
    ├── navigation.md
    └── services.md
```

### Environment Configuration
```bash
# Set primary provider
LLM_PROVIDER=mistral  # or 'gemini'

# Provider API keys
MISTRAL_API_KEY=your_mistral_key
GEMINI_API_KEY=your_gemini_key

# Model preferences
GAMEPLAY_MODEL=pixtral-12b-2409      # For vision tasks
TEMPLATE_SELECTION_MODEL=mistral-large-latest  # For text reasoning
```

### Code Integration
```python
from prompt_manager import PromptManager

# Initialize with automatic provider detection
prompt_manager = PromptManager()

# Get provider-specific prompt
prompt = prompt_manager.get_ai_directed_prompt(
    context_type="auto_select",
    task="win this pokemon battle",
    recent_actions=["a", "down"],
    memory_context="Battle context with HP bars visible"
)

# Switch providers dynamically
prompt_manager.switch_to_provider('mistral', verbose=True)
```

## Testing Guidelines

### Template Validation
```python
# Test provider-specific loading
python test_provider_prompts.py

# Test complete integration
python test_provider_integration.py

# Test with real gameplay
python run_eevee.py --goal "test provider switching" --verbose
```

### Expected Results
- **Character Consistency**: Mistral should respond as Ash in first person
- **Structural Clarity**: Gemini should provide structured, analytical responses
- **Function Calling**: Both should extract buttons correctly via tools or text parsing
- **Provider Switching**: Dynamic switching should work without errors

## Performance Optimization

### Response Time
- **Mistral**: Faster for simple decisions (~1-2 seconds)
- **Gemini**: Better for complex analysis (~2-4 seconds)

### Token Efficiency
- **Mistral**: Use shorter, focused prompts (500-1000 tokens)
- **Gemini**: Can handle longer, detailed prompts (1500-3000 tokens)

### Cost Considerations
- **Mistral**: Pay-per-use, cost-effective for production
- **Gemini**: Generous free tier, good for development

## Troubleshooting

### Common Issues

**Provider Templates Not Loading**:
- Check `LLM_PROVIDER` environment variable
- Verify provider directory exists
- Ensure YAML syntax is valid

**Function Calling Failures**:
- Verify API keys are set correctly
- Check model supports function calling
- Ensure tool schema is properly formatted

**Character Inconsistency**:
- Review prompt structure for provider
- Check template selection logic
- Validate response parsing

### Debug Commands
```bash
# Check current configuration
python provider_config.py --show-config

# Test provider switching
python -c "from prompt_manager import PromptManager; pm = PromptManager(); print(pm.get_current_provider_info())"

# Validate function calling
python test_provider_integration.py
```

## Future Enhancements

- **Additional Providers**: OpenAI GPT-4V, Claude Vision
- **Dynamic Optimization**: A/B testing between prompt styles
- **Context-Aware Selection**: Automatic provider switching based on task type
- **Performance Monitoring**: Response quality metrics per provider