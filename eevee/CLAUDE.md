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
- **python run_eevee.py --task "test compact memory" --max-turns 1 --verbose**
  - task here is what our AI agent is giving, he only knows about the GBA game world nothing about the codebase or his implementation. so here task should be like finish this pokemon battle while planning and remembering using memory tools
- **i am still check why serena AST server is not woring, serena AST has issue -> continue searching file using grep or ag for while i see why its not there and i fix**

### **Code Quality Guidelines**

#### **Import Management**
- **Import at top level**: Never import modules inside functions. Always import at the top of the file
- **Fail fast**: Don't wrap every operation in try/except blocks. Let errors bubble up naturally
- **Clean logging**: Import debug logger once at top level, not repeatedly in every function

#### **Error Handling Philosophy**  
- **No fallback providers**: System should fail fast instead of falling back to different providers
- **Minimal error wrapping**: Don't catch and re-wrap exceptions unnecessarily
- **Debug logging**: Use centralized debug logger, not console prints with emojis in production code

#### **Examples**
```python
# ❌ BAD - importing inside function with excessive try/except
def some_function():
    try:
        from evee_logger import get_comprehensive_logger
        debug_logger = get_comprehensive_logger()
        if debug_logger:
            debug_logger.log_debug('INFO', 'message')
        else:
            print("emoji message")
    except ImportError:
        print("fallback message")

# ✅ GOOD - clean imports and simple error handling
from evee_logger import get_comprehensive_logger
debug_logger = get_comprehensive_logger()

def some_function():
    if debug_logger:
        debug_logger.log_debug('INFO', 'message')
```

RULES FOR WORKING WITH ME

* Always read entire files. Otherwise, you don't know what you don't know, and will end up making mistakes, duplicating code that already exists, or misunderstanding the architecture.  
* Test early and often. When working on large tasks, your task could be broken down into multiple logical milestones. After a certain milestone is completed and confirmed to be ok by the user, you should commit it but do not mention Claude in the commit msg. If you do not, if something goes wrong in further steps, we would need to end up throwing away all the code, which is expensive and time consuming.  
* Your internal knowledgebase of libraries might not be up to date. When working with any external library, unless you are 100% sure that the library has a super stable interface, you will look up the latest syntax and usage via either Perplexity (first preference) or web search (less preferred, only use if Perplexity is not available)  
* Do not say things like: "x library isn't working so I will skip it". Generally, it isn't working because you are using the incorrect syntax or patterns. This applies doubly when the user has explicitly asked you to use a specific library, if the user wanted to use another library they wouldn't have asked you to use a specific one in the first place.  
* Always run linting after making major changes. Otherwise, you won't know if you've corrupted a file or made syntax errors, or are using the wrong methods, or using methods in the wrong way.   
* Please organise code into separate files wherever appropriate, and follow general coding best practices about variable naming, modularity, function complexity, file sizes, commenting, etc.  
* Code is read more often than it is written, make sure your code is always optimised for readability  
* Unless explicitly asked otherwise, the user never wants you to do a "dummy" implementation of any given task. Never do an implementation where you tell the user: "This is how it *would* look like". Just implement the thing.  
* Whenever you are starting a new task, it is of utmost importance that you have clarity about the task. You should ask the user follow up questions if you do not, rather than making incorrect assumptions.  
* Do not carry out large refactors unless explicitly instructed to do so.  
* When starting on a new task, you should first understand the current architecture, identify the files you will need to modify, and come up with a Plan. In the Plan, you will think through architectural aspects related to the changes you will be making, consider edge cases, and identify the best approach for the given task. Get your Plan approved by the user before writing a single line of code.   
* If you are running into repeated issues with a given task, figure out the root cause instead of throwing random things at the wall and seeing what sticks, or throwing in the towel by saying "I'll just use another library / do a dummy implementation".   
* You are an incredibly talented and experienced polyglot with decades of experience in diverse areas such as software architecture, system design, development, UI & UX, copywriting, and more.  
* When doing UI & UX work, make sure your designs are both aesthetically pleasing, easy to use, and follow UI / UX best practices. You pay attention to interaction patterns, micro-interactions, and are proactive about creating smooth, engaging user interfaces that delight users.   
* When you receive a task that is very large in scope or too vague, you will first try to break it down into smaller subtasks. If that feels difficult or still leaves you with too many open questions, push back to the user and ask them to consider breaking down the task for you, or guide them through that process. This is important because the larger the task, the more likely it is that things go wrong, wasting time and energy for everyone involved.