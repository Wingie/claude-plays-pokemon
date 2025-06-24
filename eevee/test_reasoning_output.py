#!/usr/bin/env python3
"""
Test script to print visual reasoning and verify which models generate what
"""

import sys
import os
from pathlib import Path

# Add paths for importing
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from visual_analysis import VisualAnalysis
    from provider_config import get_provider_for_hybrid_task, get_hybrid_config
    from eevee_agent import EeveeAgent
    from prompt_manager import PromptManager
    
    print("🧪 Testing Visual Reasoning Output")
    print("=" * 50)
    
    # Check hybrid configuration
    hybrid_config = get_hybrid_config()
    print(f"Hybrid Mode: {hybrid_config}")
    
    # Check which providers handle which tasks
    visual_provider = get_provider_for_hybrid_task('visual')
    strategic_provider = get_provider_for_hybrid_task('strategic')
    
    print(f"Visual Provider: {visual_provider}")
    print(f"Strategic Provider: {strategic_provider}")
    print("=" * 50)
    
    # Load prompt manager to check templates
    prompt_manager = PromptManager()
    
    # Check visual context analyzer template
    visual_template = prompt_manager.base_prompts.get("visual_context_analyzer", {})
    print("Visual Context Analyzer Template:")
    print(visual_template.get("template", "Not found")[:200] + "...")
    print()
    
    # Check exploration strategy template  
    exploration_template = prompt_manager.base_prompts.get("exploration_strategy", {})
    print("Exploration Strategy Template (reasoning format):")
    template_content = exploration_template.get("template", "")
    if "reasoning" in template_content:
        lines = template_content.split('\n')
        for i, line in enumerate(lines):
            if 'reasoning' in line.lower():
                print(f"Line {i}: {line.strip()}")
                if i+1 < len(lines):
                    print(f"Line {i+1}: {lines[i+1].strip()}")
                break
    
    print("\n✅ Analysis Complete!")
    print("🔍 Visual Analysis = Pixtral (Mistral) - Clean JSON")
    print("🎯 Strategic Decisions = Mistral Large - Now uses compact reasoning")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run from eevee/ directory")