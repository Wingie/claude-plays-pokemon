# Tutorial 02: Gemma 3 VLM Architecture Deep Dive

## Learning Objectives 🎯

By the end of this tutorial, you will:
- Understand Gemma 3's multimodal architecture in detail
- Learn how SigLIP vision encoder processes images
- Explore the Pan & Scan algorithm for image handling
- Understand token representation and attention mechanisms
- Know how to inspect and debug model components

## Introduction to Multimodal Architecture

### The Big Picture

Gemma 3 Vision-Language Models combine three key components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SigLIP        │    │   Gemma 3        │    │   Text          │
│ Vision Encoder  │───▶│  Transformer     │───▶│  Generation     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                       ▲
    Image Input              Vision + Text            Generated Text
   (896x896 px)               Tokens                  (Pokemon Actions)
```

### Component Breakdown

1. **SigLIP Vision Encoder**
   - Converts images to high-dimensional vectors
   - Handles variable image sizes with Pan & Scan
   - Produces vision tokens for the transformer

2. **Gemma 3 Transformer**
   - Processes both vision and text tokens
   - Uses cross-modal attention mechanisms
   - Generates coherent multimodal understanding

3. **Text Generation Head**
   - Converts final hidden states to text tokens
   - Produces structured outputs (JSON for Pokemon actions)

## SigLIP Vision Encoder 🔍

### What is SigLIP?

SigLIP (Sigmoid Loss for Language Image Pre-training) is Google's advanced vision encoder:

- **Sigmoid Loss**: More stable than contrastive learning
- **High Resolution**: Processes 896x896 images natively
- **Efficient**: Optimized for vision-language tasks

### Architecture Details

```python
# SigLIP Components
SigLIP Vision Encoder:
├── Patch Embedding Layer
│   ├── Input: (896, 896, 3) RGB image
│   ├── Patch Size: 14x14 pixels
│   └── Output: (64 x 64, 1152) patch embeddings
│
├── Vision Transformer Layers (x27)
│   ├── Multi-Head Self-Attention
│   ├── Layer Normalization
│   ├── Feed-Forward Network
│   └── Residual Connections
│
└── Final Projection
    ├── Input: (4096, 1152) vision features
    └── Output: (729, 2048) vision tokens for Gemma
```

### Practical Exploration

Let's inspect SigLIP in action:

```python
#!/usr/bin/env python3
"""
SigLIP Vision Encoder Exploration
Understanding how images become tokens
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import numpy as np

# Load model and processor
model_name = "google/gemma-3-4b-it"
processor = AutoProcessor.from_pretrained(model_name)
model = AutoModelForImageTextToText.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# Create sample Pokemon screenshot (240x160 → 896x896)
def create_sample_pokemon_frame():
    """Create a synthetic Pokemon game frame for analysis."""
    # Game Boy Advance resolution: 240x160
    frame = Image.new("RGB", (240, 160), color=(50, 100, 200))
    
    # Add some "game elements" (simple rectangles)
    import PIL.ImageDraw as ImageDraw
    draw = ImageDraw.Draw(frame)
    
    # Player character (red square)
    draw.rectangle([100, 80, 120, 100], fill=(200, 50, 50))
    
    # UI elements (white rectangles)
    draw.rectangle([10, 10, 50, 30], fill=(255, 255, 255))
    draw.rectangle([190, 10, 230, 30], fill=(255, 255, 255))
    
    return frame

# Analyze vision processing
def analyze_vision_processing():
    """Deep dive into how SigLIP processes images."""
    
    # Create test image
    test_image = create_sample_pokemon_frame()
    print(f"Original image size: {test_image.size}")
    
    # Process image through SigLIP
    inputs = processor(images=test_image, return_tensors="pt")
    
    print(f"Processed image shape: {inputs['pixel_values'].shape}")
    # Expected: [1, 3, 896, 896] (batch, channels, height, width)
    
    # Extract vision features
    with torch.no_grad():
        vision_outputs = model.vision_tower(inputs['pixel_values'])
        print(f"Vision features shape: {vision_outputs.last_hidden_state.shape}")
        # Expected: [1, 729, 1152] (batch, patches, features)
        
        # Project to language space
        vision_embeds = model.multi_modal_projector(vision_outputs.last_hidden_state)
        print(f"Vision embeddings shape: {vision_embeds.shape}")
        # Expected: [1, 729, 2048] (batch, vision_tokens, embed_dim)
    
    return vision_embeds

# Run analysis
if __name__ == "__main__":
    vision_tokens = analyze_vision_processing()
    print(f"✅ SigLIP converted image to {vision_tokens.shape[1]} vision tokens")
```

## Pan & Scan Algorithm 📐

### What is Pan & Scan?

Pan & Scan is Gemma 3's algorithm for handling images of different sizes and aspect ratios:

1. **Resize**: Scale image to fit within 896x896 while preserving aspect ratio
2. **Crop**: Extract 896x896 patches from the resized image
3. **Process**: Feed each patch through SigLIP independently
4. **Combine**: Merge patch features into final representation

### Pokemon Game Implications

For Pokemon screenshots (240x160 aspect ratio):

```python
# Pan & Scan for Pokemon frames
Original Pokemon Frame: 240x160 (3:2 aspect ratio)
                     ↓
Resize to fit 896x896: 896x597 (maintains aspect ratio)
                     ↓
Pan & Scan extraction: 896x896 crop from center
                     ↓
SigLIP processing: 896x896 → 729 vision tokens
```

### Implementation Details

```python
def understand_pan_and_scan():
    """Demonstrate Pan & Scan algorithm."""
    
    # Original Pokemon frame
    pokemon_frame = Image.new("RGB", (240, 160), "blue")
    print(f"Original: {pokemon_frame.size}")
    
    # Step 1: Resize maintaining aspect ratio
    target_size = 896
    aspect_ratio = pokemon_frame.width / pokemon_frame.height
    
    if aspect_ratio > 1:  # Wider than tall
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:  # Taller than wide
        new_height = target_size
        new_width = int(target_size * aspect_ratio)
    
    resized = pokemon_frame.resize((new_width, new_height))
    print(f"Resized: {resized.size}")
    
    # Step 2: Create 896x896 canvas and center the image
    canvas = Image.new("RGB", (896, 896), "black")
    
    # Calculate centering offset
    x_offset = (896 - new_width) // 2
    y_offset = (896 - new_height) // 2
    
    canvas.paste(resized, (x_offset, y_offset))
    print(f"Final canvas: {canvas.size}")
    
    return canvas

# This is how processor.py internally handles images
processed_image = understand_pan_and_scan()
```

### Grid Training Considerations

Our 2x2 grid approach benefits from Pan & Scan:

```
Original Grid: 480x320 (4 frames of 240x160)
              ↓
Pan & Scan: Resize to 896x597, center in 896x896
           ↓  
Result: Each quadrant gets ~448x299 pixels
        Perfect for temporal analysis!
```

## Token Representation 🧮

### Vision Tokens

SigLIP converts our 2x2 Pokemon grid into **729 vision tokens**:

```python
# Token breakdown
Image Patches: 896x896 ÷ 14x14 = 64x64 = 4096 patches
              ↓
Vision Transformer: 4096 patches → 729 tokens (with pooling)
                   ↓
Each token represents: ~1.23x1.23 pixel regions
                      ↓
For our grid: Each frame gets ~182 tokens
             Perfect temporal granularity!
```

### Text Tokens

Gemma 3 tokenizer converts our prompts and responses:

```python
# Example tokenization
prompt = "Looking at this 2x2 temporal grid, what button should be pressed next?"
tokens = processor.tokenizer.encode(prompt)
print(f"Prompt tokens: {len(tokens)}")  # ~20 tokens

response = '{"button": "right", "reasoning": "clear_path", "context": "navigation"}'
response_tokens = processor.tokenizer.encode(response)
print(f"Response tokens: {len(response_tokens)}")  # ~15 tokens
```

### Combined Token Sequence

During training, Gemma 3 processes:

```
[BOS] [SYSTEM_PROMPT] [729_VISION_TOKENS] [USER_QUESTION] [ASSISTANT_RESPONSE] [EOS]
  1   +      ~50      +       729        +      ~20      +       ~15         + 1
                                   = ~816 total tokens

Context budget: 128K tokens
Usage: 816 tokens (0.6%)
Efficiency: Excellent! 99.4% context remaining for complex scenarios
```

## Attention Mechanisms 🧠

### Cross-Modal Attention

Gemma 3 uses sophisticated attention to connect vision and text:

```python
# Attention patterns in Gemma 3
def visualize_attention_concept():
    """Conceptual understanding of cross-modal attention."""
    
    # Vision tokens attend to each other (spatial relationships)
    vision_self_attention = """
    Frame 1 tokens ←→ Frame 2 tokens (temporal progression)
    Frame 3 tokens ←→ Frame 4 tokens (movement patterns)
    All frames ←→ All frames (global scene understanding)
    """
    
    # Text tokens attend to vision tokens (grounding)
    text_vision_attention = """
    "what button" → [action-relevant image regions]
    "next" → [temporal progression indicators]
    "grid" → [spatial layout understanding]
    """
    
    # Vision tokens attend to text tokens (contextualization)
    vision_text_attention = """
    [player character] → "what button should be pressed"
    [movement arrows] → "next action"
    [UI elements] → "menu navigation context"
    """
    
    print("Cross-modal attention enables rich understanding!")
    return vision_self_attention, text_vision_attention, vision_text_attention
```

### Temporal Attention in Grids

Our 2x2 grid layout enables temporal attention patterns:

```
Grid Layout:    Attention Flow:
┌─────┬─────┐   t=0 → t=1 (progression)
│ t=0 │ t=1 │    ↓     ↓
├─────┼─────┤   t=2 ← t=3 (current state)
│ t=2 │ t=3 │
└─────┴─────┘   

The model learns to:
1. Compare t=0 vs t=1 (recent change)
2. Compare t=1 vs t=3 (overall progression)  
3. Focus on t=3 (current state for action)
4. Use all frames (full context)
```

## Model Inspection Tools 🔧

### Component Analysis

```python
#!/usr/bin/env python3
"""
Gemma 3 Model Inspection Tools
Deep dive into model components
"""

def inspect_model_architecture():
    """Examine Gemma 3 VLM structure."""
    
    model = AutoModelForImageTextToText.from_pretrained("google/gemma-3-4b-it")
    
    print("🔍 Model Components:")
    print(f"  Vision Tower: {type(model.vision_tower).__name__}")
    print(f"  Language Model: {type(model.language_model).__name__}")  
    print(f"  Projector: {type(model.multi_modal_projector).__name__}")
    
    # Vision tower details
    vision_config = model.vision_tower.config
    print(f"\n👁️ Vision Configuration:")
    print(f"  Image Size: {vision_config.image_size}")
    print(f"  Patch Size: {vision_config.patch_size}")
    print(f"  Hidden Size: {vision_config.hidden_size}")
    print(f"  Num Layers: {vision_config.num_hidden_layers}")
    
    # Language model details
    lang_config = model.language_model.config
    print(f"\n💬 Language Configuration:")
    print(f"  Vocab Size: {lang_config.vocab_size}")
    print(f"  Hidden Size: {lang_config.hidden_size}")
    print(f"  Num Layers: {lang_config.num_hidden_layers}")
    print(f"  Context Length: {lang_config.max_position_embeddings}")
    
    return model

def analyze_parameter_distribution():
    """Understand where model parameters are allocated."""
    
    model = inspect_model_architecture()
    
    # Count parameters by component
    vision_params = sum(p.numel() for p in model.vision_tower.parameters())
    language_params = sum(p.numel() for p in model.language_model.parameters())
    projector_params = sum(p.numel() for p in model.multi_modal_projector.parameters())
    total_params = sum(p.numel() for p in model.parameters())
    
    print(f"\n📊 Parameter Distribution:")
    print(f"  Vision Tower: {vision_params:,} ({vision_params/total_params:.1%})")
    print(f"  Language Model: {language_params:,} ({language_params/total_params:.1%})")
    print(f"  Projector: {projector_params:,} ({projector_params/total_params:.1%})")
    print(f"  Total: {total_params:,}")
    
    return {
        'vision': vision_params,
        'language': language_params, 
        'projector': projector_params,
        'total': total_params
    }

# Run analysis
if __name__ == "__main__":
    param_stats = analyze_parameter_distribution()
```

### Memory Analysis

```python
def analyze_memory_usage():
    """Understand memory requirements for different configurations."""
    
    import torch
    
    # Model loading options
    configs = {
        'full_precision': {
            'torch_dtype': torch.float32,
            'description': 'Full 32-bit precision'
        },
        'half_precision': {
            'torch_dtype': torch.float16,
            'description': '16-bit half precision'
        },
        'bfloat16': {
            'torch_dtype': torch.bfloat16,
            'description': 'Brain float 16'
        }
    }
    
    print("💾 Memory Usage Estimates:")
    
    # Base parameter count (from previous analysis)
    total_params = 4_000_000_000  # ~4B parameters
    
    for config_name, config in configs.items():
        if config['torch_dtype'] == torch.float32:
            bytes_per_param = 4
        else:  # float16 or bfloat16
            bytes_per_param = 2
            
        memory_gb = (total_params * bytes_per_param) / (1024**3)
        
        print(f"  {config['description']}: {memory_gb:.1f}GB")
    
    print(f"\n🧮 Training Memory (with gradients & optimizer):")
    print(f"  Training adds ~3x memory overhead")
    print(f"  QLoRA reduces this to ~1.5x with 4-bit quantization")

# Memory analysis
analyze_memory_usage()
```

## Performance Characteristics ⚡

### Inference Speed

Understanding speed bottlenecks:

```python
# Inference timing breakdown
Vision Processing:  ~50ms (SigLIP encoding)
Language Processing: ~100ms (text generation) 
Total Inference:    ~150ms per sample

# For real-time gaming:
Target: <5ms (Eevee v2 requirement)
Current: 150ms (30x too slow)
Solution: Optimized deployment + caching
```

### Training Throughput

```python
# Training speed factors
Batch Size 1:      ~2 seconds/step
Batch Size 2:      ~3 seconds/step (memory limited)
Gradient Accum 8:  Effective batch 16
Steps per epoch:   ~42 (671 samples ÷ 16 batch)
Time per epoch:    ~2.5 hours
```

## Practical Exercises 🛠️

### Exercise 1: Model Loading

```bash
# Load and inspect Gemma 3
python -c "
from transformers import AutoModelForImageTextToText, AutoProcessor
import torch

print('Loading Gemma 3...')
model = AutoModelForImageTextToText.from_pretrained(
    'google/gemma-3-4b-it',
    torch_dtype=torch.bfloat16,
    device_map='auto'
)
processor = AutoProcessor.from_pretrained('google/gemma-3-4b-it')

print(f'✅ Model loaded: {model.config.model_type}')
print(f'✅ Processor loaded: {processor.tokenizer.__class__.__name__}')
print(f'📊 Parameters: {sum(p.numel() for p in model.parameters()):,}')
"
```

### Exercise 2: Image Processing

```python
# Test SigLIP on Pokemon-style image
from PIL import Image
import torch

# Create test grid (2x2 Pokemon frames)
test_grid = Image.new("RGB", (480, 320), "blue")

# Process through SigLIP
inputs = processor(images=test_grid, return_tensors="pt")
print(f"Input shape: {inputs['pixel_values'].shape}")

# Extract vision features
with torch.no_grad():
    vision_features = model.vision_tower(inputs['pixel_values'])
    print(f"Vision features: {vision_features.last_hidden_state.shape}")
```

## Key Takeaways 💡

1. **Architecture Understanding**: Gemma 3 combines SigLIP vision + Gemma language
2. **Pan & Scan**: Intelligently handles different image sizes and aspect ratios
3. **Token Efficiency**: 729 vision tokens + minimal text = efficient context usage
4. **Cross-Modal Attention**: Rich interaction between vision and language
5. **Memory Requirements**: ~8GB for inference, ~16GB for training with QLoRA

## Next Steps 🚀

In **Tutorial 03**, we'll focus on:
- Converting Eevee v1 data to grid format
- Understanding the conversion pipeline
- Quality filtering and data validation
- Creating rich context prompts for Pokemon gameplay

### Preparation for Tutorial 03

1. **Run model inspection**: Complete the exercises above
2. **Download sample data**: We'll work with real Eevee v1 sessions
3. **Understand data flow**: Review the conversion pipeline

```bash
# Prepare for data conversion (Tutorial 03)
cd /Users/wingston/code/claude-plays-pokemon/eevee_v2/gemma
python scripts/validate_training.py --test env
echo "✅ Ready for Tutorial 03: Data Preparation!"
```

---

**Great work! You now understand Gemma 3's architecture. Ready for data preparation in Tutorial 03? 📊**