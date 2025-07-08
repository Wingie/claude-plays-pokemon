# Research References for Eevee v2

## Core Architectural Inspirations

### SpeechSSM: Long-Form Speech Generation with Spoken Language Models
**Paper**: `2412.18603v1.pdf` (ICML 2025)  
**Authors**: Se Jin Park, Julian Salazar, Aren Jansen, Keisuke Kinoshita, Yong Man Ro, RJ Skerry-Ryan

#### Key Insights Applied to Eevee v2:

1. **Constant Memory Architecture**
   - Griffin SSM with fixed-size state for unbounded sequence generation
   - Hybrid recurrent + local attention layers
   - O(1) memory complexity during decoding

2. **Windowed Processing Strategy**
   - 30-second segments with 4-second overlap
   - Boundary artifact minimization techniques
   - Temporal tokenization for efficient processing

3. **Length Extrapolation Capability**
   - Training on 4-minute sequences, extrapolating to 16+ minutes
   - Quality maintenance beyond training lengths
   - Novel situation handling through architectural design

4. **Long-Form Evaluation Framework**
   - Semantic Coherence over Length (SC-L) metrics
   - Time-stratified quality assessments
   - LLM-as-Judge evaluation protocols

#### Technical Implementation Parallels:

| SpeechSSM Component | Eevee v2 Equivalent | Application |
|---------------------|---------------------|-------------|
| Semantic Tokens | Game State Embeddings | Visual scene understanding |
| Acoustic Tokens | Action Sequences | Button press generation |
| Griffin SSM | Hybrid Gaming SSM | Real-time decision making |
| Windowed Decoding | Temporal Game Segments | Continuous gameplay processing |
| Speaker Conditioning | Game Context Conditioning | Situation-aware responses |

#### Performance Achievements:
- **Real-time Factor**: <0.2x (16k tokens in 100 seconds)
- **Memory Efficiency**: Constant regardless of sequence length
- **Throughput**: >120x speedup vs Transformer for long sequences
- **Quality**: Matches Transformer performance while enabling unlimited generation

### Future Research Areas:

1. **Hybrid Architectures for Gaming**
   - State-space models for temporal reasoning
   - Local attention for immediate context
   - Memory-efficient long-term planning

2. **Gaming-Specific Evaluation Metrics**
   - Strategic coherence measurement
   - Long-term goal achievement tracking
   - Adaptability assessment frameworks

3. **Extrapolation Beyond Training**
   - Novel situation handling
   - Transfer learning capabilities
   - Generalization across game scenarios

---

*This document tracks research papers and insights that influence Eevee v2's architectural decisions and implementation strategies.*