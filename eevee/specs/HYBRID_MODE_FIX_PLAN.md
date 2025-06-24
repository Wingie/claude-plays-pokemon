# 🔧 Hybrid Mode Integration Fix Plan

## 🚨 Current Issues Identified

### **Critical Issue 1: Gemini Empty Responses (0 chars)**
- **Problem**: Gemini visual analysis returning 0 chars
- **Symptom**: `📥 Response received: 0 chars` in logs
- **Effect**: System defaults to navigation mode instead of battle detection

### **Critical Issue 2: Template Variable Conflicts**
- **Problem**: Universal template format may not be compatible with Gemini
- **Symptom**: Template parsing failures or empty responses
- **Effect**: JSON parsing fails, falls back to low confidence navigation

### **Critical Issue 3: Provider Routing Logic**
- **Problem**: Hybrid task routing may have bugs in visual_analysis.py
- **Effect**: Wrong provider called or incorrect model selection

## 🎯 Fix Implementation Plan

### **Phase 1: Debug & Monitoring Setup** ✅ COMPLETED
- [x] Created debug_logger.py for real-time monitoring
- [x] Separate log file that can be tailed: `tail -f runs/session_*/debug.log`

### **Phase 2: Fix Gemini Visual Analysis (HIGH PRIORITY)**

#### **Fix 2A: Template Compatibility**
```yaml
# visual_context_analyzer needs Gemini-specific format
visual_context_analyzer_gemini:
  name: Gemini Scene Analyzer
  template: |
    Analyze this Pokemon screenshot and return JSON.
    
    Identify scene type and provide button recommendations:
    
    ```json
    {
      "scene_type": "battle|navigation|menu",
      "recommended_template": "ai_directed_battle|ai_directed_navigation",
      "valid_buttons": [
        {"key": "A", "action": "select", "result": "advance_text"}
      ]
    }
    ```
```

#### **Fix 2B: Simplified Visual Prompt**
- Remove complex universal template for Gemini
- Use basic scene detection that works reliably
- Focus on battle vs navigation detection

### **Phase 3: Provider Routing Validation**

#### **Fix 3A: Debug Provider Selection**
```python
# Add to visual_analysis.py _call_pixtral_for_analysis
if verbose:
    print(f"🔍 HYBRID DEBUG:")
    print(f"   Task category: visual")
    print(f"   Provider selected: {provider}")
    print(f"   Model selected: {model}")
    print(f"   Hybrid enabled: {hybrid_config['enabled']}")
```

#### **Fix 3B: Provider Validation**
```python
# Ensure provider is correctly set
if provider not in ['gemini', 'mistral']:
    print(f"⚠️ Invalid provider '{provider}', falling back to mistral")
    provider = 'mistral'
    model = 'pixtral-12b-2409'
```

### **Phase 4: Template Integration**

#### **Fix 4A: Backward Compatibility Mapping**
```python
# visual_analysis.py _parse_movement_response needs universal → old format mapping
def map_universal_to_old_format(universal_data):
    return {
        "scene_type": universal_data.get("scene_type", "navigation"),
        "recommended_template": universal_data.get("recommended_template", "ai_directed_navigation"),
        "confidence": "high" if universal_data.get("scene_type") else "low",
        "spatial_context": f"Scene: {universal_data.get('scene_type', 'unknown')}",
        "valid_movements": ["up", "down", "left", "right"],  # Safe default
        # Add all required old format fields
    }
```

## 🧪 Testing Protocol

### **Test 1: Debug Logger Validation**
```bash
# Initialize debug logging
python -c "
from debug_logger import init_debug_logger
logger = init_debug_logger()
logger.log_hybrid_mode('gemini', 'mistral', True)
print(f'Debug log: {logger.get_debug_log_path()}')
"

# Monitor debug output
tail -f runs/session_*/debug.log
```

### **Test 2: Provider Routing Test**
```bash
# Test hybrid mode environment
export LLM_PROVIDER=hybrid
export HYBRID_MODE=true
export VISUAL_PROVIDER=gemini
export STRATEGIC_PROVIDER=mistral

# Test provider selection
python -c "
from provider_config import get_provider_for_hybrid_task, get_model_for_task
print(f'Visual provider: {get_provider_for_hybrid_task(\"visual\")}')
print(f'Visual model: {get_model_for_task(\"screenshot_analysis\")}')
print(f'Strategic provider: {get_provider_for_hybrid_task(\"strategic\")}')
"
```

### **Test 3: Gemini API Direct Test**
```bash
# Test Gemini API directly
python -c "
from llm_api import call_llm
import base64
from pathlib import Path

# Test with simple prompt
response = call_llm(
    prompt='Analyze this Pokemon scene. Return JSON with scene_type and valid_buttons.',
    provider='gemini',
    model='gemini-2.0-flash-exp'
)
print(f'Response length: {len(response.text) if response.text else 0}')
print(f'Response preview: {response.text[:100] if response.text else \"EMPTY\"}')
"
```

### **Test 4: End-to-End Hybrid Test**
```bash
# Run short hybrid session with debug logging
python run_eevee.py --goal "test hybrid mode" --max-turns 3 --no-interactive --verbose
```

## 🔍 Expected Debug Output

### **Working Hybrid Mode Should Show:**
```
[12:34:56] 🔀 HYBRID MODE: ENABLED
[12:34:56]    👁️  Visual: gemini
[12:34:56]    🧠 Strategic: mistral
[12:34:57] 👁️  VISUAL ANALYSIS: gemini (gemini-2.0-flash-exp)
[12:34:57]    📥 Response: 156 chars
[12:34:57]    ⏱️  Time: 1250.2ms
[12:34:58] 📊 JSON PARSING: SUCCESS
[12:34:58]    🔑 Keys found: ['scene_type', 'recommended_template', 'valid_buttons']
[12:34:59] 🧠 STRATEGIC DECISION: mistral (mistral-large-latest)
[12:34:59]    📋 Template: ai_directed_navigation
[12:34:59]    🎮 Buttons: ['up']
```

### **Broken Mode Shows:**
```
[12:34:56] 🔀 HYBRID MODE: ENABLED
[12:34:57] 👁️  VISUAL ANALYSIS: gemini (gemini-2.0-flash-exp)
[12:34:57]    📥 Response: 0 chars
[12:34:57]    ⚠️  EMPTY RESPONSE - POTENTIAL BUG!
[12:34:58] 📊 JSON PARSING: FAILED
[12:34:58]    ⚠️  Falling back to navigation mode
```

## 🚀 Quick Fix Implementation Order

1. **IMMEDIATE**: Integrate debug logger into visual_analysis.py and run_eevee.py
2. **CRITICAL**: Fix Gemini visual analysis empty response issue
3. **HIGH**: Add provider validation and fallback logic
4. **MEDIUM**: Improve template compatibility for Gemini
5. **TESTING**: Validate end-to-end hybrid mode functionality

## 🎯 Success Criteria

- ✅ Debug logger shows detailed hybrid mode operation
- ✅ Gemini visual analysis returns >0 chars consistently  
- ✅ JSON parsing succeeds for both providers
- ✅ Battle scenes properly detected (not defaulting to navigation)
- ✅ Strategic decisions use correct provider (Mistral)
- ✅ Complete hybrid gameplay session without crashes

Would you like me to start implementing these fixes in order?