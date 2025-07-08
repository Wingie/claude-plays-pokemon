#!/usr/bin/env python3
"""
Convert Eevee v1 training data to Gemma VLM 4-frame format.

This script processes Eevee v1 data (individual screenshots + actions) into 
4-frame temporal sequences with rich context for Gemma VLM training.

Usage:
    python scripts/convert_eevee_data.py \
        --input_dir /path/to/eevee_v1/data \
        --output_file training_data/pokemon_4frame_dataset.jsonl \
        --frames_per_sequence 4 \
        --min_sequence_length 10
"""

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
import glob
from datetime import datetime

def parse_eevee_v1_action(action_str: str) -> Dict[str, str]:
    """
    Parse Eevee v1 action strings into structured button responses.
    
    Example inputs:
    - "press_right" -> {"button": "right", "reasoning": "movement_right", "context": "navigation"}
    - "talk_to_npc" -> {"button": "a", "reasoning": "npc_interaction", "context": "dialogue"}
    """
    action_mapping = {
        # Movement actions
        "press_up": {"button": "up", "reasoning": "movement_north", "context": "navigation"},
        "press_down": {"button": "down", "reasoning": "movement_south", "context": "navigation"},
        "press_left": {"button": "left", "reasoning": "movement_west", "context": "navigation"}, 
        "press_right": {"button": "right", "reasoning": "movement_east", "context": "navigation"},
        
        # Interaction actions
        "press_a": {"button": "a", "reasoning": "primary_action", "context": "interaction"},
        "press_b": {"button": "b", "reasoning": "secondary_action", "context": "interaction"},
        "talk_to_npc": {"button": "a", "reasoning": "npc_interaction", "context": "dialogue"},
        "examine_object": {"button": "a", "reasoning": "object_examination", "context": "interaction"},
        
        # Menu actions
        "open_menu": {"button": "start", "reasoning": "menu_access", "context": "menu"},
        "close_menu": {"button": "b", "reasoning": "menu_close", "context": "menu"},
        "select_option": {"button": "a", "reasoning": "menu_selection", "context": "menu"},
        
        # Battle actions
        "attack": {"button": "a", "reasoning": "battle_attack", "context": "battle"},
        "use_item": {"button": "a", "reasoning": "item_usage", "context": "battle"},
        "switch_pokemon": {"button": "a", "reasoning": "pokemon_switch", "context": "battle"},
    }
    
    # Try exact match first
    if action_str in action_mapping:
        return action_mapping[action_str]
    
    # Fallback parsing for partial matches
    if "up" in action_str.lower():
        return {"button": "up", "reasoning": "movement_north", "context": "navigation"}
    elif "down" in action_str.lower():
        return {"button": "down", "reasoning": "movement_south", "context": "navigation"}
    elif "left" in action_str.lower():
        return {"button": "left", "reasoning": "movement_west", "context": "navigation"}
    elif "right" in action_str.lower():
        return {"button": "right", "reasoning": "movement_east", "context": "navigation"}
    elif "a" in action_str.lower() or "interact" in action_str.lower():
        return {"button": "a", "reasoning": "primary_action", "context": "interaction"}
    elif "b" in action_str.lower() or "back" in action_str.lower():
        return {"button": "b", "reasoning": "secondary_action", "context": "interaction"}
    elif "start" in action_str.lower() or "menu" in action_str.lower():
        return {"button": "start", "reasoning": "menu_access", "context": "menu"}
    else:
        # Default fallback
        return {"button": "a", "reasoning": "default_action", "context": "navigation"}


def infer_scene_description(image_paths: List[str], action: Dict[str, str]) -> str:
    """
    Infer scene description from image paths and action context.
    """
    # Extract context clues from file paths
    path_str = " ".join(image_paths).lower()
    
    scene_keywords = {
        "route": "overworld_route",
        "town": "town_area", 
        "city": "city_area",
        "center": "pokemon_center",
        "mart": "pokemon_mart",
        "gym": "gym_building",
        "cave": "cave_interior",
        "forest": "forest_area",
        "battle": "pokemon_battle",
        "menu": "game_menu",
        "inventory": "inventory_screen"
    }
    
    scene_type = "overworld_generic"
    for keyword, scene in scene_keywords.items():
        if keyword in path_str:
            scene_type = scene
            break
    
    # Add context based on action
    if action["context"] == "battle":
        scene_type += "_battle_active"
    elif action["context"] == "dialogue":
        scene_type += "_npc_conversation"
    elif action["context"] == "menu":
        scene_type += "_menu_open"
    
    return scene_type


def generate_rich_context(sequence_idx: int, action: Dict[str, str]) -> str:
    """
    Generate rich context string for 32K token utilization.
    """
    # Base Ash Ketchum persona
    ash_context = "Ash Ketchum exploring with Pikachu"
    
    # Add context based on action type
    if action["context"] == "navigation":
        contexts = [
            f"{ash_context}, seeking wild Pokemon encounters for training",
            f"{ash_context}, exploring new areas with full party health",
            f"{ash_context}, searching for rare Pokemon and items",
            f"{ash_context}, progressing toward next gym challenge"
        ]
    elif action["context"] == "battle":
        contexts = [
            f"{ash_context}, Pikachu health 85%, facing wild Pokemon with type advantage",
            f"{ash_context}, strategic battle positioning for effective attack",
            f"{ash_context}, considering best move against opponent Pokemon",
            f"{ash_context}, managing PP and health during extended battle"
        ]
    elif action["context"] == "dialogue":
        contexts = [
            f"{ash_context}, receiving important information from local NPC",
            f"{ash_context}, learning about local Pokemon and area secrets",
            f"{ash_context}, getting directions to next destination",
            f"{ash_context}, gathering intel about gym leader strategies"
        ]
    elif action["context"] == "menu":
        contexts = [
            f"{ash_context}, managing inventory and Pokemon party status",
            f"{ash_context}, organizing items for optimal battle readiness",
            f"{ash_context}, checking Pokemon health and abilities",
            f"{ash_context}, planning item usage for upcoming challenges"
        ]
    else:
        contexts = [
            f"{ash_context}, making strategic decisions for Pokemon journey",
            f"{ash_context}, exploring game world with determination",
            f"{ash_context}, pursuing Pokemon master goals with Pikachu"
        ]
    
    # Select context based on sequence to add variety
    return contexts[sequence_idx % len(contexts)]


def load_eevee_v1_data(input_dir: str) -> List[Tuple[str, str]]:
    """
    Load Eevee v1 data from directory structure.
    Expected format: image files with corresponding action files or metadata.
    """
    input_path = Path(input_dir)
    data_pairs = []
    
    # Look for common Eevee v1 file patterns
    image_patterns = ["*.png", "*.jpg", "*.jpeg"]
    
    for pattern in image_patterns:
        image_files = sorted(input_path.glob(f"**/{pattern}"))
        
        for img_file in image_files:
            # Look for corresponding action file
            action_file = img_file.with_suffix('.txt')
            json_file = img_file.with_suffix('.json')
            
            action_str = "press_a"  # Default action
            
            if action_file.exists():
                action_str = action_file.read_text().strip()
            elif json_file.exists():
                try:
                    action_data = json.loads(json_file.read_text())
                    action_str = action_data.get('action', 'press_a')
                except:
                    pass
            
            data_pairs.append((str(img_file), action_str))
    
    return data_pairs


def create_4frame_sequences(data_pairs: List[Tuple[str, str]], frames_per_sequence: int = 4, min_sequence_length: int = 10) -> List[Dict[str, Any]]:
    """
    Group individual data pairs into 4-frame temporal sequences.
    """
    sequences = []
    
    # Group data pairs into sequences of specified length
    for i in range(0, len(data_pairs) - frames_per_sequence + 1, frames_per_sequence):
        if i + min_sequence_length > len(data_pairs):
            break
            
        # Extract 4-frame sequence
        frame_group = data_pairs[i:i + frames_per_sequence]
        image_paths = [pair[0] for pair in frame_group]
        
        # Use the action from the last frame as the target action
        last_action_str = frame_group[-1][1]
        action_dict = parse_eevee_v1_action(last_action_str)
        
        # Generate rich context and scene description
        context = generate_rich_context(len(sequences), action_dict)
        scene_description = infer_scene_description(image_paths, action_dict)
        
        # Create complete output JSON
        output_json = {
            "button": action_dict["button"],
            "reasoning": action_dict["reasoning"],
            "context": action_dict["context"],
            "scene_description": scene_description
        }
        
        # Create training example
        sequence = {
            "frames": image_paths,
            "context": context,
            "question": "Analyze the 4-frame sequence and determine the optimal next action.",
            "output": json.dumps(output_json)
        }
        
        sequences.append(sequence)
    
    return sequences


def copy_images_with_absolute_paths(sequences: List[Dict[str, Any]], output_dir: str) -> List[Dict[str, Any]]:
    """
    Copy images to output directory and update paths to absolute paths.
    """
    output_path = Path(output_dir)
    images_dir = output_path / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    updated_sequences = []
    
    for i, sequence in enumerate(sequences):
        new_frame_paths = []
        
        for j, frame_path in enumerate(sequence["frames"]):
            # Create unique filename
            original_name = Path(frame_path).name
            new_name = f"seq_{i:06d}_frame_{j}_{original_name}"
            new_path = images_dir / new_name
            
            # Copy image file
            try:
                shutil.copy2(frame_path, new_path)
                new_frame_paths.append(str(new_path.absolute()))
            except Exception as e:
                print(f"Error copying {frame_path} to {new_path}: {e}")
                new_frame_paths.append(frame_path)  # Keep original path as fallback
        
        # Update sequence with new paths
        updated_sequence = sequence.copy()
        updated_sequence["frames"] = new_frame_paths
        updated_sequences.append(updated_sequence)
    
    return updated_sequences


def main():
    parser = argparse.ArgumentParser(description="Convert Eevee v1 data to Gemma VLM format")
    parser.add_argument("--input_dir", required=True, help="Path to Eevee v1 data directory")
    parser.add_argument("--output_file", required=True, help="Output JSONL file path")
    parser.add_argument("--frames_per_sequence", type=int, default=4, help="Number of frames per sequence")
    parser.add_argument("--min_sequence_length", type=int, default=10, help="Minimum sequence length to process")
    parser.add_argument("--copy_images", action="store_true", help="Copy images to output directory")
    
    args = parser.parse_args()
    
    print(f"Loading Eevee v1 data from {args.input_dir}...")
    data_pairs = load_eevee_v1_data(args.input_dir)
    print(f"Found {len(data_pairs)} image-action pairs")
    
    if len(data_pairs) < args.min_sequence_length:
        print(f"Error: Need at least {args.min_sequence_length} data pairs, found {len(data_pairs)}")
        return
    
    print(f"Creating {args.frames_per_sequence}-frame sequences...")
    sequences = create_4frame_sequences(data_pairs, args.frames_per_sequence, args.min_sequence_length)
    print(f"Created {len(sequences)} sequences")
    
    if args.copy_images:
        output_dir = Path(args.output_file).parent
        print(f"Copying images to {output_dir}/images/...")
        sequences = copy_images_with_absolute_paths(sequences, str(output_dir))
    
    # Write JSONL output
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing training data to {args.output_file}...")
    with open(args.output_file, 'w') as f:
        for sequence in sequences:
            f.write(json.dumps(sequence) + '\n')
    
    print(f"Conversion complete!")
    print(f"- Input: {len(data_pairs)} image-action pairs")
    print(f"- Output: {len(sequences)} 4-frame sequences")
    print(f"- File: {args.output_file}")
    
    # Write summary statistics
    summary_file = output_path.with_suffix('.summary.json')
    summary = {
        "conversion_time": datetime.now().isoformat(),
        "input_directory": args.input_dir,
        "input_pairs": len(data_pairs),
        "output_sequences": len(sequences),
        "frames_per_sequence": args.frames_per_sequence,
        "images_copied": args.copy_images,
        "sample_sequence": sequences[0] if sequences else None
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary written to {summary_file}")


if __name__ == "__main__":
    main()