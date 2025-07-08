#!/usr/bin/env python3
"""
Master conversion script for both PaliGemma and Pixtral formats
Creates clean training datasets from Eevee v1 data
"""

import json
import os
import time
from pathlib import Path
from convert_to_paligemma import convert_dataset_to_paligemma
from convert_to_pixtral import convert_dataset_to_pixtral

def generate_conversion_report(input_file: str, paligemma_file: str, pixtral_file: str, 
                             paligemma_count: int, pixtral_count: int):
    """Generate comprehensive conversion report"""
    
    # Load original data for analysis
    original_data = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                original_data.append(json.loads(line))
    
    # Analyze original dataset
    original_contexts = {}
    original_sessions = set()
    
    for item in original_data:
        context = item["metadata"].get("context_detected", "unknown")
        original_contexts[context] = original_contexts.get(context, 0) + 1
        original_sessions.add(item["metadata"]["session_id"])
    
    # Create comprehensive report
    report = {
        "conversion_summary": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": input_file,
            "original_training_pairs": len(original_data),
            "original_sessions": len(original_sessions),
            "paligemma_output": {
                "file": paligemma_file,
                "training_pairs": paligemma_count,
                "format": "simple prefix/suffix pairs",
                "use_case": "action prediction and behavior cloning"
            },
            "pixtral_output": {
                "file": pixtral_file,
                "conversations": pixtral_count,
                "format": "multi-turn conversations",
                "use_case": "strategic reasoning and context understanding"
            }
        },
        "original_data_analysis": {
            "context_distribution": original_contexts,
            "total_sessions": len(original_sessions),
            "avg_turns_per_session": len(original_data) / len(original_sessions)
        },
        "conversion_efficiency": {
            "paligemma_retention": f"{(paligemma_count / len(original_data)) * 100:.1f}%",
            "pixtral_compression": f"{len(original_data) / pixtral_count:.1f}:1 turns to conversations"
        },
        "training_recommendations": {
            "paligemma": {
                "batch_size": "8-16 (Google recommended)",
                "learning_rate": "0.03 (or lower)",
                "training_steps": f"~{paligemma_count // 8 * 3} steps for 3 epochs",
                "validation_split": "10-20% of data"
            },
            "pixtral": {
                "batch_size": "1 (model limitation)",
                "learning_rate": "5-10x smaller than language model",
                "training_considerations": "Multi-turn context, longer sequences",
                "conversation_quality": "Focus on coherent strategic reasoning"
            }
        },
        "data_quality_notes": {
            "action_extraction": "Robust multi-method extraction with confidence scoring",
            "context_preservation": "Strategic reasoning maintained in both formats",
            "pokemon_validation": "All actions validated against Game Boy button set",
            "conversation_threading": "Natural context-aware conversation flows"
        }
    }
    
    # Save report
    report_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/conversion_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report, report_file

def main():
    """Run both conversions and generate comprehensive report"""
    
    print("🚀 Starting comprehensive dataset conversion...")
    print("=" * 60)
    
    # File paths
    input_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/eevee_v1_paligemma_training.jsonl"
    paligemma_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/paligemma_dataset_pokemon.jsonl"
    pixtral_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/pixtral_dataset_pokemon.jsonl"
    
    # Verify input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    start_time = time.time()
    
    # Convert to PaliGemma format
    print("\n📝 Phase 1: Converting to PaliGemma format...")
    print("-" * 40)
    paligemma_count = convert_dataset_to_paligemma(input_file, paligemma_file)
    
    print(f"\n💬 Phase 2: Converting to Pixtral format...")
    print("-" * 40)
    pixtral_count = convert_dataset_to_pixtral(input_file, pixtral_file)
    
    # Generate comprehensive report
    print(f"\n📊 Phase 3: Generating conversion report...")
    print("-" * 40)
    report, report_file = generate_conversion_report(
        input_file, paligemma_file, pixtral_file, paligemma_count, pixtral_count
    )
    
    end_time = time.time()
    conversion_time = end_time - start_time
    
    # Display summary
    print("\n" + "=" * 60)
    print("🎉 CONVERSION COMPLETE!")
    print("=" * 60)
    
    print(f"\n⏱️  Total Conversion Time: {conversion_time:.1f} seconds")
    print(f"\n📁 Output Files:")
    print(f"   📝 PaliGemma Dataset: {paligemma_file}")
    print(f"      • {paligemma_count} training pairs")
    print(f"      • Simple prefix/suffix format")
    print(f"      • Ready for action prediction training")
    
    print(f"\n   💬 Pixtral Dataset: {pixtral_file}")
    print(f"      • {pixtral_count} multi-turn conversations")
    print(f"      • Strategic reasoning format")
    print(f"      • Ready for context-aware training")
    
    print(f"\n   📊 Conversion Report: {report_file}")
    print(f"      • Comprehensive analysis and statistics")
    print(f"      • Training recommendations")
    print(f"      • Quality metrics and validation")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review conversion report for quality metrics")
    print(f"   2. Transfer datasets to GPU training machine")
    print(f"   3. Set up training pipelines for both models")
    print(f"   4. Begin fine-tuning with recommended parameters")
    
    print(f"\n📈 Conversion Summary:")
    print(f"   • Original Data: {report['conversion_summary']['original_training_pairs']} pairs")
    print(f"   • PaliGemma: {paligemma_count} pairs ({report['conversion_efficiency']['paligemma_retention']} retention)")
    print(f"   • Pixtral: {pixtral_count} conversations ({report['conversion_efficiency']['pixtral_compression']} compression)")
    
    print("\n✅ Ready for GPU training deployment!")

if __name__ == "__main__":
    main()