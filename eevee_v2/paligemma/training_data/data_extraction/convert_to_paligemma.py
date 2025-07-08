#!/usr/bin/env python3
"""
Convert Eevee v1 dataset to PaliGemma format
Simple prefix/suffix pairs for action prediction
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from robust_action_extractor import PokemonActionExtractor

def extract_clean_action_with_extractor(extractor: PokemonActionExtractor, turn_data: Dict[str, Any], gpt_response: str) -> str:
    """Extract clean action using robust extractor"""
    actions, confidence = extractor.extract_actions(turn_data, gpt_response)
    
    if actions and confidence > 0.6:
        return ", ".join(actions)
    
    return "unknown"

def extract_context_info(turn_data: Dict[str, Any]) -> str:
    """Extract context for better prefix"""
    ai_analysis = turn_data.get("ai_analysis", {})
    parsed_json = ai_analysis.get("parsed_json", {})
    
    context = "pokemon action"
    
    if parsed_json and isinstance(parsed_json, dict):
        context_detected = parsed_json.get("context_detected")
        if context_detected:
            if context_detected == "navigation":
                context = "pokemon navigate"
            elif context_detected == "battle":
                context = "pokemon battle"
            elif context_detected == "menu":
                context = "pokemon menu"
            else:
                context = f"pokemon {context_detected}"
    
    return context

def create_paligemma_prefix(goal: str, context: str) -> str:
    """Create task-specific prefix for PaliGemma"""
    if goal and goal != "unknown goal":
        return f"{context} goal: {goal}"
    return context

def convert_session_to_paligemma(session_data: Dict[str, Any], extractor: PokemonActionExtractor) -> List[Dict[str, Any]]:
    """Convert a single session to PaliGemma format"""
    paligemma_pairs = []
    turns = session_data.get("turns", [])
    session_goal = session_data.get("goal", "pokemon gameplay")
    
    for turn in turns:
        turn_number = turn.get("turn", 0)
        image_filename = f"step_{turn_number:04d}_grid.png"
        
        # Extract clean action using robust extractor
        gpt_response = turn.get("gpt_response", "")
        action = extract_clean_action_with_extractor(extractor, turn, gpt_response)
        if action == "unknown":
            continue  # Skip turns without clear actions
            
        # Extract context for prefix
        context = extract_context_info(turn)
        prefix = create_paligemma_prefix(session_goal, context)
        
        # Create PaliGemma training pair
        paligemma_pair = {
            "image": image_filename,
            "prefix": prefix,
            "suffix": action
        }
        
        paligemma_pairs.append(paligemma_pair)
    
    return paligemma_pairs

def convert_dataset_to_paligemma(input_file: str, output_file: str):
    """Convert entire dataset to PaliGemma format"""
    print(f"Converting {input_file} to PaliGemma format...")
    
    # Initialize robust action extractor
    extractor = PokemonActionExtractor()
    
    # Load original dataset
    original_data = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                original_data.append(json.loads(line))
    
    print(f"Loaded {len(original_data)} original training pairs")
    
    # Group by session
    sessions = {}
    for item in original_data:
        session_id = item["metadata"]["session_id"]
        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "goal": item["metadata"]["goal"],
                "turns": []
            }
        
        # Reconstruct turn data from metadata and conversations
        gpt_response = item["conversations"][1]["value"]
        turn_data = {
            "turn": item["metadata"]["turn"],
            "gpt_response": gpt_response,
            "ai_analysis": {
                "parsed_json": {
                    "context_detected": item["metadata"].get("context_detected"),
                    "confidence": item["metadata"].get("confidence")
                }
            }
        }
        
        # Try to extract action from metadata first
        if "Recommended Action:" in gpt_response:
            action_lines = [line for line in gpt_response.split('\n') if "Recommended Action:" in line]
            if action_lines:
                action_text = action_lines[0].split("Recommended Action:")[-1].strip()
                turn_data["ai_analysis"]["parsed_json"]["button_presses"] = [action_text]
        
        sessions[session_id]["turns"].append(turn_data)
    
    print(f"Grouped into {len(sessions)} sessions")
    
    # Convert each session
    all_paligemma_pairs = []
    extracted_actions = 0
    skipped_actions = 0
    
    for session_id, session_data in sessions.items():
        session_pairs = convert_session_to_paligemma(session_data, extractor)
        all_paligemma_pairs.extend(session_pairs)
        extracted_actions += len(session_pairs)
        skipped_actions += len(session_data["turns"]) - len(session_pairs)
        print(f"Session {session_id}: {len(session_pairs)}/{len(session_data['turns'])} pairs extracted")
    
    # Write to output file
    with open(output_file, 'w') as f:
        for pair in all_paligemma_pairs:
            f.write(json.dumps(pair) + '\n')
    
    print(f"\n✅ Created {len(all_paligemma_pairs)} PaliGemma training pairs")
    print(f"📊 Extraction Rate: {extracted_actions}/{extracted_actions + skipped_actions} ({extracted_actions/(extracted_actions + skipped_actions)*100:.1f}%)")
    print(f"📁 Output: {output_file}")
    
    # Generate statistics
    contexts = {}
    actions = {}
    for pair in all_paligemma_pairs:
        prefix = pair["prefix"]
        suffix = pair["suffix"]
        
        # Extract context from prefix
        parts = prefix.split()
        context = parts[1] if len(parts) > 1 else "unknown"
        contexts[context] = contexts.get(context, 0) + 1
        actions[suffix] = actions.get(suffix, 0) + 1
    
    print("\n📈 Context Distribution:")
    for context, count in sorted(contexts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {context}: {count}")
    
    print("\n🎮 Top Actions:")
    for action, count in sorted(actions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {action}: {count}")
    
    return len(all_paligemma_pairs)

def main():
    input_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/eevee_v1_paligemma_training.jsonl"
    output_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/paligemma_dataset_pokemon.jsonl"
    
    convert_dataset_to_paligemma(input_file, output_file)

if __name__ == "__main__":
    main()