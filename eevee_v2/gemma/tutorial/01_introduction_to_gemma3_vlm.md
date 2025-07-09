# Tutorial 01: Introduction to Gemma 3 Vision-Language Models

## Welcome to Pokemon Gemma 3 VLM Fine-tuning! 🎮✨

This comprehensive tutorial series will teach you how to fine-tune Google's Gemma 3 Vision-Language Models for Pokemon gameplay AI using real gaming data from Eevee v1.

### What You'll Learn

By the end of this series, you'll understand:
- **Gemma 3 VLM Architecture**: How vision-language models process images and text
- **Gaming AI Applications**: Temporal sequence modeling for real-time gameplay
- **Fine-tuning Techniques**: QLoRA, PEFT, and distributed training
- **Production Deployment**: From training to inference optimization
- **Performance Optimization**: Memory management and hardware utilization

## Course Overview

### Tutorial Structure

| Tutorial | Topic | Duration | Prerequisites |
|----------|-------|----------|---------------|
| **01** | Introduction & Setup | 30 min | Basic Python |
| **02** | Understanding Gemma 3 VLM | 45 min | Tutorial 01 |
| **03** | Data Preparation & Conversion | 60 min | Tutorial 02 |
| **04** | Training Configuration | 45 min | Tutorial 03 |
| **05** | Fine-tuning Process | 90 min | Tutorial 04 |
| **06** | Monitoring & Debugging | 60 min | Tutorial 05 |
| **07** | Model Evaluation | 45 min | Tutorial 06 |
| **08** | Deployment & Optimization | 75 min | Tutorial 07 |
| **09** | Advanced Techniques | 60 min | Tutorial 08 |

### Learning Approach

Each tutorial follows this structure:
- **🎯 Objectives**: Clear learning goals
- **📚 Theory**: Conceptual understanding
- **🛠️ Practice**: Hands-on implementation
- **🔍 Deep Dive**: Advanced concepts
- **💡 Tips**: Best practices and troubleshooting
- **🚀 Next Steps**: Preparation for the next tutorial

## What is Gemma 3 VLM?

### Overview

Gemma 3 Vision-Language Models represent Google's latest advancement in multimodal AI:

- **Vision Encoder**: SigLIP (Sigmoid Loss for Language Image Pre-training)
- **Language Model**: Gemma 3 transformer architecture
- **Context Length**: Up to 128K tokens
- **Multimodal Integration**: Native image-text understanding

### Key Capabilities

```
🖼️ Image Understanding:
   • Object detection and recognition
   • Spatial relationship analysis
   • Scene understanding and context

📝 Text Generation:
   • Contextual responses
   • Structured output (JSON)
   • Long-form reasoning

🎮 Gaming Applications:
   • Frame-by-frame analysis
   • Action prediction
   • State understanding
```

### Architecture Deep Dive

```
Input Images → SigLIP Encoder → Vision Tokens
     ↓
Input Text → Tokenizer → Text Tokens
     ↓
Vision Tokens + Text Tokens → Gemma 3 Transformer → Output Tokens
     ↓
Output Tokens → Decoder → Generated Text
```

## Why Fine-tune for Pokemon?

### The Challenge

Pokemon games present unique AI challenges:

1. **Temporal Understanding**: Actions depend on frame sequences
2. **Complex State Space**: Menu systems, battles, exploration
3. **Strategic Planning**: Long-term goal achievement
4. **Real-time Constraints**: Must respond within frame budget

### Our Solution: 2x2 Grid Approach

Instead of processing 4 separate frames (which causes TRL bugs), we:

```
Frame 1 | Frame 2     →     ┌─────────┬─────────┐
Frame 3 | Frame 4           │ Frame 1 │ Frame 2 │
                             │ (t=0)   │ (t=1)   │
4 separate images            ├─────────┼─────────┤
(TRL bug)                    │ Frame 3 │ Frame 4 │
                             │ (t=2)   │ (t=3)   │
                             └─────────┴─────────┘
                             Single grid image
                             (Works perfectly!)
```

## Prerequisites & Environment Setup

### Hardware Requirements

**Minimum**:
- GPU: 8GB VRAM (RTX 3070, RTX 4060 Ti)
- RAM: 16GB system memory
- Storage: 50GB free space

**Recommended**:
- GPU: 24GB VRAM (RTX 4090, A6000)
- RAM: 32GB system memory
- Storage: 100GB SSD

### Software Setup

We'll use the automated setup from our pipeline:

```bash
# Navigate to project
cd /Users/wingston/code/claude-plays-pokemon/eevee_v2/gemma

# Run setup script
./init.sh

# Activate environment
conda activate pokemon-gemma-vlm

# Verify installation
python -c "import torch; print(torch.cuda.is_available())"
python -c "import transformers; print(transformers.__version__)"
python -c "import trl; print(trl.__version__)"
```

### Authentication Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your tokens
# HUGGINGFACE_TOKEN=hf_your_token_here
# WANDB_API_KEY=your_wandb_key_here
```

## Understanding the Data Pipeline

### Eevee v1 → Gemma 3 Conversion

Our pipeline transforms rich Eevee v1 session data into training-ready format:

```
Eevee v1 Sessions:
├── session_20241201_143022/
│   ├── session_data.json      ← AI decisions & reasoning
│   ├── sshots/               ← Game screenshots  
│   │   ├── step_0001_grid.png
│   │   ├── step_0002_grid.png
│   │   └── ...
│   └── visual_analysis/      ← Frame analysis
│
↓ Conversion Process
│
Pokemon Training Data:
├── grid_images/              ← 2x2 temporal grids
│   ├── grid_000001.png      
│   └── ...
└── pokemon_grid_dataset.jsonl ← Training examples
```

### Training Example Structure

Each training example contains:

```json
{
  "image": "grid_images/grid_000001.png",
  "context": "🎮 You are ASH KETCHUM with incredible memory...",
  "question": "Looking at this 2x2 temporal grid, what button should be pressed next?",
  "output": "{\"button\": \"right\", \"reasoning\": \"clear_path\", \"context\": \"navigation\"}"
}
```

## Key Concepts

### 1. Vision-Language Understanding

Gemma 3 processes images and text together:

- **Image Tokens**: SigLIP converts images to token sequences
- **Text Tokens**: Standard tokenization of instructions/responses
- **Attention**: Cross-modal attention between vision and language

### 2. Temporal Sequence Modeling

Our grid approach preserves temporal information spatially:

- **Spatial Layout**: 2x2 grid maintains temporal order
- **Visual Progression**: Model learns to read temporally
- **Action Prediction**: Based on observed changes

### 3. Parameter-Efficient Fine-tuning

We use QLoRA (Quantized Low-Rank Adaptation):

- **4-bit Quantization**: Reduces memory usage by 4x
- **LoRA Adapters**: Only train small adapter weights
- **Minimal Degradation**: Maintains model quality

## What's Next?

In **Tutorial 02**, we'll dive deep into:

- Gemma 3 VLM architecture details
- SigLIP vision encoder specifics
- Pan & Scan algorithm for image processing
- Token representation and attention mechanisms

### Preparation for Tutorial 02

1. **Complete setup**: Ensure all dependencies are installed
2. **Download test data**: We'll use sample Pokemon screenshots
3. **Explore model**: Load and inspect a pre-trained Gemma 3 model

```bash
# Test model loading (we'll do this in Tutorial 02)
python -c "
from transformers import AutoModelForImageTextToText, AutoProcessor
model = AutoModelForImageTextToText.from_pretrained('google/gemma-3-4b-it')
processor = AutoProcessor.from_pretrained('google/gemma-3-4b-it')
print('✅ Gemma 3 model loaded successfully!')
"
```

## Resources & References

### Documentation
- [Gemma Model Documentation](https://huggingface.co/google/gemma-3-4b-it)
- [TRL Training Library](https://huggingface.co/docs/trl)
- [SigLIP Paper](https://arxiv.org/abs/2303.15343)

### Community
- [HuggingFace Discord](https://discord.gg/huggingface)
- [TRL GitHub](https://github.com/huggingface/trl)
- [Transformers GitHub](https://github.com/huggingface/transformers)

---

**Ready to master Gemma 3 VLM fine-tuning? Let's continue to Tutorial 02! 🚀**