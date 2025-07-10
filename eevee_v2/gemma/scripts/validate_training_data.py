#!/usr/bin/env python3
"""
Training Data Validation Script for NeurIPS Pokemon Challenge
Validates existing training data quality and identifies improvement opportunities.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import argparse
from collections import defaultdict, Counter

def load_training_data(jsonl_path: str) -> List[Dict[str, Any]]:
    """Load training data from JSONL file."""
    data = []
    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print(f"JSON error at line {line_num}: {e}")
                continue
    return data

def validate_json_output(output: str) -> Tuple[bool, Dict[str, Any]]:
    """Validate JSON output format for NeurIPS competition."""
    try:
        parsed = json.loads(output)
        
        # Required fields for NeurIPS competition
        required_fields = ['button', 'reasoning', 'context']
        valid = all(field in parsed for field in required_fields)
        
        # Valid button actions
        valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
        if 'button' in parsed:
            valid &= parsed['button'] in valid_buttons
            
        return valid, parsed
    except json.JSONDecodeError:
        return False, {}

def analyze_data_quality(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Comprehensive data quality analysis."""
    
    # Basic statistics
    total_samples = len(data)
    
    # Session distribution
    session_counts = Counter()
    confidence_counts = Counter()
    button_counts = Counter()
    context_counts = Counter()
    template_counts = Counter()
    success_rates = []
    
    # Quality metrics
    valid_json_count = 0
    missing_images = 0
    
    for sample in data:
        # Extract metadata
        metadata = sample.get('metadata', {})
        session_id = metadata.get('session_id', 'unknown')
        confidence = metadata.get('confidence', 'unknown')
        success_rate = metadata.get('success_rate', 0.0)
        template_used = metadata.get('template_used', 'unknown')
        
        session_counts[session_id] += 1
        confidence_counts[confidence] += 1
        template_counts[template_used] += 1
        success_rates.append(success_rate)
        
        # Validate JSON output
        valid, parsed = validate_json_output(sample.get('output', ''))
        if valid:
            valid_json_count += 1
            button_counts[parsed.get('button', 'unknown')] += 1
            context_counts[parsed.get('context', 'unknown')] += 1
        
        # Check image existence
        image_path = sample.get('image', '')
        if image_path and not os.path.exists(image_path):
            missing_images += 1
    
    # Calculate statistics
    avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
    unique_sessions = len(session_counts)
    
    return {
        'total_samples': total_samples,
        'unique_sessions': unique_sessions,
        'avg_samples_per_session': total_samples / unique_sessions if unique_sessions > 0 else 0,
        'avg_success_rate': avg_success_rate,
        'valid_json_rate': valid_json_count / total_samples if total_samples > 0 else 0,
        'missing_images': missing_images,
        'confidence_distribution': dict(confidence_counts),
        'button_distribution': dict(button_counts),
        'context_distribution': dict(context_counts),
        'template_distribution': dict(template_counts),
        'session_distribution': dict(session_counts)
    }

def identify_data_issues(data: List[Dict[str, Any]]) -> List[str]:
    """Identify potential data quality issues."""
    issues = []
    
    # Check for duplicate sequences
    image_paths = [sample.get('image', '') for sample in data]
    if len(image_paths) != len(set(image_paths)):
        issues.append("Duplicate image paths detected")
    
    # Check for missing fields
    for i, sample in enumerate(data):
        if not sample.get('image'):
            issues.append(f"Sample {i}: Missing image path")
        if not sample.get('output'):
            issues.append(f"Sample {i}: Missing output")
        if not sample.get('context'):
            issues.append(f"Sample {i}: Missing context")
    
    # Check for malformed JSON outputs
    malformed_count = 0
    for sample in data:
        valid, _ = validate_json_output(sample.get('output', ''))
        if not valid:
            malformed_count += 1
    
    if malformed_count > 0:
        issues.append(f"{malformed_count} samples have malformed JSON outputs")
    
    return issues

def generate_enhancement_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations for data enhancement."""
    recommendations = []
    
    # Success rate recommendations
    if analysis['avg_success_rate'] < 0.8:
        recommendations.append(f"Consider filtering low success rate samples (current avg: {analysis['avg_success_rate']:.2f})")
    
    # Session distribution recommendations
    if analysis['avg_samples_per_session'] < 5:
        recommendations.append(f"Low samples per session ({analysis['avg_samples_per_session']:.1f}). Consider windowing to increase data.")
    
    # Button distribution recommendations
    button_dist = analysis['button_distribution']
    total_buttons = sum(button_dist.values())
    if total_buttons > 0:
        most_common = max(button_dist, key=button_dist.get)
        if button_dist[most_common] / total_buttons > 0.5:
            recommendations.append(f"Button distribution is imbalanced ('{most_common}': {button_dist[most_common]/total_buttons:.1%})")
    
    # Context distribution recommendations
    context_dist = analysis['context_distribution']
    if len(context_dist) < 3:
        recommendations.append(f"Limited context diversity ({len(context_dist)} unique contexts). Consider data augmentation.")
    
    # Missing images
    if analysis['missing_images'] > 0:
        recommendations.append(f"Fix {analysis['missing_images']} missing image paths")
    
    return recommendations

def main():
    parser = argparse.ArgumentParser(description="Validate Pokemon training data for NeurIPS competition")
    parser.add_argument("--data-path", default="training_data/pokemon_grid_dataset_final.jsonl", 
                       help="Path to training data JSONL file")
    parser.add_argument("--output-report", default="validation_report.json",
                       help="Output validation report path")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.data_path):
        print(f"Error: Training data file not found: {args.data_path}")
        sys.exit(1)
    
    print(f"Loading training data from {args.data_path}...")
    data = load_training_data(args.data_path)
    
    if not data:
        print("Error: No valid training data found")
        sys.exit(1)
    
    print(f"Analyzing {len(data)} training samples...")
    
    # Perform quality analysis
    analysis = analyze_data_quality(data)
    issues = identify_data_issues(data)
    recommendations = generate_enhancement_recommendations(analysis)
    
    # Generate report
    report = {
        'analysis': analysis,
        'issues': issues,
        'recommendations': recommendations,
        'neurips_readiness': {
            'total_samples': analysis['total_samples'],
            'valid_json_rate': analysis['valid_json_rate'],
            'avg_success_rate': analysis['avg_success_rate'],
            'ready_for_competition': (
                analysis['valid_json_rate'] > 0.95 and 
                analysis['avg_success_rate'] > 0.7 and 
                len(issues) == 0
            )
        }
    }
    
    # Save report
    with open(args.output_report, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("NEURIPS POKEMON CHALLENGE - TRAINING DATA VALIDATION")
    print("="*60)
    print(f"Total Samples: {analysis['total_samples']}")
    print(f"Unique Sessions: {analysis['unique_sessions']}")
    print(f"Average Success Rate: {analysis['avg_success_rate']:.2%}")
    print(f"Valid JSON Rate: {analysis['valid_json_rate']:.2%}")
    print(f"Missing Images: {analysis['missing_images']}")
    
    print(f"\nButton Distribution:")
    for button, count in sorted(analysis['button_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {button}: {count} ({count/analysis['total_samples']:.1%})")
    
    print(f"\nContext Distribution:")
    for context, count in sorted(analysis['context_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {context}: {count} ({count/analysis['total_samples']:.1%})")
    
    if issues:
        print(f"\nIssues Found:")
        for issue in issues:
            print(f"  - {issue}")
    
    if recommendations:
        print(f"\nRecommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    print(f"\nNeurIPS Competition Readiness: {'✅ READY' if report['neurips_readiness']['ready_for_competition'] else '⚠️ NEEDS IMPROVEMENT'}")
    print(f"Report saved to: {args.output_report}")

if __name__ == "__main__":
    main()