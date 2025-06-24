# Eevee v1 - AI Pokemon Task Execution System

## 🏗️ Architecture Overview

Eevee v1 achieves **intelligent Pokemon gameplay through pure prompt engineering and visual intelligence** - no fine-tuning required. The system combines multimodal reasoning, spatial intelligence, **centralized multi-provider LLM API**, and **standardized JSON response parsing**.

**Key Achievement**: Complex Pokemon gameplay behavior emerges from:
- **Visual Context Analyzer**: 8-key spatial intelligence with grid coordinates
- **AI-Directed Templates**: Context-aware prompts that adapt to navigation/battle/menu situations
- **Multi-Provider Vision**: Mistral (Pixtral) and Gemini (2.0 Flash) achieve 0-hallucination spatial understanding
- **Continuous Learning**: Real-time template improvement based on performance

## 🧩 Core Components

### **System Architecture**
```
EeveeAgent (game control) → PromptManager (AI templates) → LLM API (multi-provider) → ContinuousGameplay (learning loop)
```

| Component | Role | Key Features |
|-----------|------|--------------|
| **EeveeAgent** | SkyEmu integration | Screenshot capture, button execution, state management |
| **PromptManager** | AI template management | AI-directed selection, dynamic mapping, YAML loading |
| **LLM API System** | Provider abstraction | Gemini + Mistral support, circuit breakers, auto-fallback |
| **ContinuousGameplay** | Learning loop | Turn-based execution, template improvement, session management |
| **MemorySystem** | Persistent storage | SQLite contexts, session isolation |
| **Visual Analyzer** | Spatial intelligence | Grid overlays, scene classification, 0-hallucination accuracy |

## 🧠 AI Memories and Lessons Learned

### **Strategic Insights**
- **ok! always start making a plan to present if you find an issue**