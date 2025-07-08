# Vision Model Comparison & Plan Review for Pokemon Gaming AI

## Model Capabilities Research Summary

### PaliGemma (Established)
**Key Specs:**
- **Parameters**: 3B (400M vision + 2B language)
- **Context**: ~128 tokens text
- **Vision**: SigLIP encoder, 224x224/448x448/896x896
- **Multi-image**: Supports 4-frame sequences, proven gaming applications

**Strengths:**
- Proven gaming track record (Valorant object detection)
- Coordinate tokenization for UI elements
- Fast 3B inference suitable for real-time
- Established training scripts and fine-tuning examples

**Weaknesses:**
- Very limited text context (~128 tokens)
- Basic temporal understanding
- Prone to hallucinations under pressure

**Real-time Viability**: ⭐⭐⭐⭐ (Good for simple decisions)

---

### Gemma 3 (Recent)
**Key Specs:**
- **Parameters**: 1B (text), 4B, 12B, 27B (multimodal)
- **Context**: 128K tokens (!!)
- **Vision**: SigLIP encoder with "pan & scan", 896x896
- **Multi-image**: "Hundreds of images" supported, temporal sequences confirmed

**Strengths:**
- Massive 128K context for complex game state
- 4-frame temporal sequences fully supported  
- 4B model optimal for real-time performance
- Advanced attention mechanisms (5:1 local:global)

**Weaknesses:**
- Newer model, less proven in gaming
- Requires upscaling for typical game screenshots
- Memory overhead for larger context

**Real-time Viability**: ⭐⭐⭐⭐⭐ (Excellent balance, 4B model recommended)

---

### Gemma 3n (Latest)
**Key Specs:**
- **Parameters**: E2B (2GB memory), E4B (3GB memory)
- **Context**: 32K tokens
- **Vision**: MobileNet v5 + SigLIP, 768x768/896x896
- **Features**: MatFormer, AltUp, LAuReL, PLE, activation sparsity

**Strengths:**
- **Best real-time performance** (60 FPS on mobile)
- MatFormer elasticity (dynamic E2B/E4B switching)
- Ultra-efficient memory usage (PLE reduces 40% footprint)
- Mobile-optimized architecture

**Weaknesses:**
- Smallest context (32K vs 128K)
- Newest model, limited documentation
- Complex architecture may have training challenges

**Real-time Viability**: ⭐⭐⭐⭐⭐ (Best for ≤5ms constraints)

---

### Qwen2.5-VL (Alternative)
**Key Specs:**
- **Parameters**: 3B, 7B, 72B
- **Context**: 32K tokens (64K for video)
- **Vision**: Dynamic resolution ViT, native video support
- **Multi-image**: Ultra-long video processing, precise object localization

**Strengths:**
- **Superior video/temporal understanding**
- Native 4-frame sequence support
- Precise coordinate/object detection
- Dynamic FPS sampling for variable frame rates

**Weaknesses:**
- Higher hardware requirements (7B needs 24GB VRAM)
- Non-Google ecosystem
- Less gaming-specific training examples

**Real-time Viability**: ⭐⭐⭐ (7B model too heavy, 3B untested for real-time)

---

## Model Recommendation Ranking

### For Real-Time Pokemon Gaming (≤5ms inference):

1. **Gemma 3n E2B** - Best speed, mobile-optimized, dynamic switching
2. **Gemma 3 4B** - Excellent balance, proven architecture, 128K context
3. **PaliGemma 3B** - Proven gaming performance, simple architecture
4. **Qwen2.5-VL 3B** - Superior temporal understanding, but unproven for real-time

---

## Revised Plans A, B, C

### Plan A: Single Model Classification (UPDATED)

**Target Model**: **Gemma 3n E2B** (best real-time performance)

**Training Data Format:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "frame1.png"},
        {"type": "image", "image": "frame2.png"},
        {"type": "image", "image": "frame3.png"},
        {"type": "image", "image": "frame4.png"},
        {"type": "text", "text": "pokemon game state: route1 goal:pokemon_center recent:up,left,up"}
      ]
    },
    {"role": "assistant", "content": "right"}
  ]
}
```

**Execution:**
```
4-frame stack + context → Gemma 3n E2B → single button → execute
```

**Pros:**
- Fastest possible inference (≤5ms target achievable)
- Simple training and deployment
- MatFormer allows dynamic E2B/E4B switching based on complexity

**Cons:**
- Limited context (32K) vs Gemma 3's 128K
- Single point of failure

---

### Plan B: Candidate Generation (UPDATED)

**Target Model**: **Gemma 3 4B** (best context + performance balance)

**Training Data Format:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "frame1.png"},
        {"type": "image", "image": "frame2.png"},
        {"type": "image", "image": "frame3.png"},
        {"type": "image", "image": "frame4.png"},
        {"type": "text", "text": "pokemon navigation route1 goal:pokemon_center health:pikachu_75% recent_actions:up,left,up obstacles:tall_grass team_status:ready"}
      ]
    },
    {"role": "assistant", "content": "{\"candidates\": [{\"button\": \"right\", \"confidence\": 0.9, \"reason\": \"clear_path_east\"}, {\"button\": \"up\", \"confidence\": 0.6, \"reason\": \"alternate_route\"}]}"}
  ]
}
```

**Execution:**
```
4-frame stack + rich context → Gemma 3 4B → JSON candidates → recommendation system → button
```

**Pros:**
- Rich 128K context for complex game state
- Multiple fallback options
- Can leverage full Pokemon game knowledge

**Cons:**
- More complex training (JSON generation)
- Two-stage system increases latency
- Recommendation system needs separate logic

---

### Plan C: Specialized Multi-Model (UPDATED)

**Target Models**: Mixed architecture optimized for each context

**Navigation Model**: **Gemma 3n E2B** (speed priority)
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "frame1.png"},
        {"type": "image", "image": "frame2.png"},
        {"type": "image", "image": "frame3.png"},
        {"type": "image", "image": "frame4.png"},
        {"type": "text", "text": "nav"}
      ]
    },
    {"role": "assistant", "content": "right"}
  ]
}
```

**Battle Model**: **Gemma 3 4B** (strategy priority)
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "battle1.png"},
        {"type": "image", "image": "battle2.png"},
        {"type": "image", "image": "battle3.png"},
        {"type": "image", "image": "battle4.png"},
        {"type": "text", "text": "battle pikachu_vs_rattata type_advantage_electric health_75%"}
      ]
    },
    {"role": "assistant", "content": "a"}
  ]
}
```

**Critique Model**: **Qwen2.5-VL 3B** (understanding priority)
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "current_scene.png"},
        {"type": "text", "text": "evaluate: pressed right, goal was pokemon_center"}
      ]
    },
    {"role": "assistant", "content": "{\"evaluation\": \"moved_east_toward_goal\", \"next_context\": \"navigation\", \"success\": true}"}
  ]
}
```

**Execution:**
```
Context Detection → Specialized Model Selection → Button Press + Parallel Critique
```

**Pros:**
- Each model optimized for its specific context
- Can use best model for each task type
- Parallel critique provides learning feedback

**Cons:**
- Most complex to implement and maintain
- Multiple models increase deployment complexity
- Context switching logic needed

---

## Training Data Strategy

### Universal Format
Design training data that can be adapted across all models:

**Base Structure:**
```json
{
  "frames": ["f1.png", "f2.png", "f3.png", "f4.png"],
  "context": "pokemon navigation route1 goal:center",
  "action": "right",
  "metadata": {
    "context_type": "navigation",
    "confidence": 0.95,
    "success": true
  }
}
```

**Model-Specific Conversion:**
- **Gemma 3/3n**: Convert to messages format with image arrays
- **PaliGemma**: Use existing processor format
- **Qwen2.5-VL**: Adapt to their conversation structure

### Context Length Utilization

**For 32K models (Gemma 3n, Qwen2.5-VL):**
```
"pokemon nav route1 goal:center health:ok recent:up,left,up"
```

**For 128K models (Gemma 3):**
```
"pokemon navigation context:
- current_location: route1_north_section
- goal: pokemon_center_healing
- party_status: pikachu_75%_charmander_100%_squirtle_0%
- recent_actions: [up,left,up,right,up]
- obstacles: tall_grass_south blocked_path_west
- strategic_plan: avoid_grass_until_healing explore_north_path
- memory: visited_route1_south battled_rattata_won
- inventory: pokeball_x3 potion_x2 antidote_x1"
```

---

## 4-Frame Multi-Image Support Analysis

### PaliGemma
- ✅ **Multi-image support**: Up to 16 frames for video tasks
- ✅ **4-frame sequences**: Confirmed supported
- ⚠️ **Memory**: 4× increase (1024 vs 256 tokens)
- ⚠️ **Performance**: Slower with multiple images

### Gemma 3
- ✅ **Multi-image support**: "Hundreds of images" in 128K context
- ✅ **4-frame sequences**: Full temporal understanding
- ✅ **Memory**: 5:1 attention ratio reduces overhead
- ✅ **Performance**: Optimized for multi-image processing

### Gemma 3n
- ✅ **Multi-image support**: Video processing confirmed
- ✅ **4-frame sequences**: 60 FPS video handling
- ✅ **Memory**: PLE optimization reduces footprint
- ✅ **Performance**: Best real-time performance

### Qwen2.5-VL
- ✅ **Multi-image support**: Native video understanding
- ✅ **4-frame sequences**: Dynamic FPS sampling
- ✅ **Memory**: Window attention for efficiency
- ⚠️ **Performance**: 7B model too heavy for real-time

---

## Final Recommendation

### **Phase 1**: Start with **Plan A + Gemma 3n E2B**
- Fastest to implement and test
- Best real-time performance guarantee
- Simple training data requirements
- MatFormer elasticity provides flexibility

### **Phase 2**: Evaluate **Plan B + Gemma 3 4B** 
- If Plan A lacks sufficient context/intelligence
- Leverage 128K context for complex game state
- More sophisticated decision making

### **Phase 3**: Consider **Plan C** for production
- If specialized models outperform general approach
- Maximum optimization for each game context
- Most complex but potentially highest performance

**Key Insight**: **Gemma 3n E2B** appears to be the best starting point for real-time constraints, with **Gemma 3 4B** as the upgrade path when more context/intelligence is needed.

**Training Data Priority**: Focus on creating the universal format that works across all models, then fine-tune based on which model performs best in initial testing.