#!/usr/bin/env python3
"""
Frame Grid Converter for Pokemon Gemma VLM Training
Converts 4-frame temporal sequences into 2x2 spatial grids to bypass TRL multi-image bug

This approach preserves temporal information spatially:
┌─────────┬─────────┐
│ Frame 1 │ Frame 2 │  
│ (t=0)   │ (t=1)   │
├─────────┼─────────┤
│ Frame 3 │ Frame 4 │
│ (t=2)   │ (t=3)   │
└─────────┴─────────┘
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameGridConverter:
    """Converts 4-frame sequences to 2x2 grid images."""
    
    def __init__(self, input_jsonl: str, output_dir: str, add_labels: bool = True):
        self.input_jsonl = Path(input_jsonl)
        self.output_dir = Path(output_dir)
        self.add_labels = add_labels
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.grid_images_dir = self.output_dir / "grid_images"
        self.grid_images_dir.mkdir(exist_ok=True)
        
        # Grid configuration
        self.frame_size = (240, 160)  # Game Boy Advance resolution
        self.grid_size = (480, 320)   # 2x2 grid of frames
        self.border_width = 2
        self.border_color = (255, 255, 255)  # White border
        
        # Label configuration
        self.label_font_size = 12
        self.label_color = (255, 255, 0)  # Yellow text
        
    def create_frame_grid(self, frame_paths: List[str], sequence_id: str) -> str:
        """
        Create a 2x2 grid from 4 frames with optional temporal labels.
        
        Args:
            frame_paths: List of 4 frame image paths
            sequence_id: Unique identifier for this sequence
            
        Returns:
            Path to created grid image
        """
        if len(frame_paths) != 4:
            raise ValueError(f"Expected 4 frames, got {len(frame_paths)}")
        
        # Load and validate frames
        frames = []
        for i, frame_path in enumerate(frame_paths):
            if not Path(frame_path).exists():
                logger.warning(f"Frame not found: {frame_path}")
                # Create placeholder frame
                frame = Image.new("RGB", self.frame_size, (64, 64, 64))
            else:
                try:
                    frame = Image.open(frame_path).convert("RGB")
                    # Resize to standard size if needed
                    if frame.size != self.frame_size:
                        frame = frame.resize(self.frame_size, Image.Resampling.LANCZOS)
                except Exception as e:
                    logger.warning(f"Failed to load {frame_path}: {e}")
                    frame = Image.new("RGB", self.frame_size, (64, 64, 64))
            
            frames.append(frame)
        
        # Create grid canvas
        grid_image = Image.new("RGB", self.grid_size, (32, 32, 32))
        
        # Position frames in 2x2 grid
        positions = [
            (0, 0),                           # Frame 1: Top-left (t=0)
            (self.frame_size[0], 0),          # Frame 2: Top-right (t=1)
            (0, self.frame_size[1]),          # Frame 3: Bottom-left (t=2)
            (self.frame_size[0], self.frame_size[1])  # Frame 4: Bottom-right (t=3)
        ]
        
        for i, (frame, pos) in enumerate(zip(frames, positions)):
            # Add border if specified
            if self.border_width > 0:
                bordered_frame = Image.new(
                    "RGB", 
                    (frame.size[0] + 2 * self.border_width, 
                     frame.size[1] + 2 * self.border_width),
                    self.border_color
                )
                bordered_frame.paste(frame, (self.border_width, self.border_width))
                frame = bordered_frame
                
                # Adjust position for border
                pos = (pos[0] - self.border_width, pos[1] - self.border_width)
            
            grid_image.paste(frame, pos)
        
        # Add temporal labels if requested
        if self.add_labels:
            self.add_temporal_labels(grid_image)
        
        # Save grid image
        grid_filename = f"grid_{sequence_id}.png"
        grid_path = self.grid_images_dir / grid_filename
        grid_image.save(grid_path, "PNG", optimize=True)
        
        return str(grid_path)
    
    def add_temporal_labels(self, grid_image: Image.Image) -> None:
        """Add temporal labels (t=0, t=1, t=2, t=3) to grid quadrants."""
        
        draw = ImageDraw.Draw(grid_image)
        
        # Try to load a font, fall back to default if unavailable
        try:
            font = ImageFont.truetype("Arial.ttf", self.label_font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Label positions (top-left corner of each quadrant)
        labels = ["t=0", "t=1", "t=2", "t=3"]
        positions = [
            (5, 5),                                    # Frame 1: Top-left
            (self.frame_size[0] + 5, 5),              # Frame 2: Top-right
            (5, self.frame_size[1] + 5),              # Frame 3: Bottom-left
            (self.frame_size[0] + 5, self.frame_size[1] + 5)  # Frame 4: Bottom-right
        ]
        
        for label, pos in zip(labels, positions):
            # Draw shadow for better visibility
            draw.text((pos[0] + 1, pos[1] + 1), label, fill=(0, 0, 0), font=font)
            # Draw main text
            draw.text(pos, label, fill=self.label_color, font=font)
    
    def create_grid_prompt(self, original_context: str, original_question: str) -> tuple[str, str]:
        """
        Adapt prompts for grid-based training.
        
        Args:
            original_context: Original context from 4-frame sequence
            original_question: Original question
            
        Returns:
            Tuple of (adapted_context, adapted_question)
        """
        
        # Enhanced context for spatial-temporal understanding
        grid_context = f"""🎮 You are ASH KETCHUM analyzing a Pokemon gameplay sequence.

You receive a TEMPORAL GRID showing 4 consecutive game frames arranged as:
┌─────────┬─────────┐
│ Frame 1 │ Frame 2 │  (Top row: earlier frames)
│ (t=0)   │ (t=1)   │
├─────────┼─────────┤
│ Frame 3 │ Frame 4 │  (Bottom row: later frames)
│ (t=2)   │ (t=3)   │
└─────────┴─────────┘

Analyze the temporal progression and spatial relationships:
- TOP-LEFT (t=0): Initial game state
- TOP-RIGHT (t=1): First progression 
- BOTTOM-LEFT (t=2): Second progression
- BOTTOM-RIGHT (t=3): Current game state

{original_context}

Study the sequence progression across the 2x2 grid to understand:
- Movement patterns and direction changes
- Environmental transitions and scene evolution
- Character actions and their consequences
- Interactive element states and availability"""

        # Enhanced question for grid analysis
        grid_question = f"""Looking at this 2x2 temporal grid (read top-left → top-right → bottom-left → bottom-right), {original_question}

Consider the temporal flow and spatial relationships shown in the grid."""

        return grid_context, grid_question
    
    def convert_dataset(self) -> str:
        """
        Convert 4-frame dataset to grid-based single-image dataset.
        
        Returns:
            Path to output JSONL file
        """
        logger.info(f"🔄 Converting 4-frame dataset to 2x2 grids")
        logger.info(f"📖 Input: {self.input_jsonl}")
        logger.info(f"📁 Output: {self.output_dir}")
        
        if not self.input_jsonl.exists():
            raise FileNotFoundError(f"Input dataset not found: {self.input_jsonl}")
        
        # Load input dataset
        input_data = []
        with open(self.input_jsonl, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    input_data.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
        
        logger.info(f"📊 Loaded {len(input_data)} sequences")
        
        # Convert to grid format
        output_data = []
        successful_conversions = 0
        
        for i, sample in enumerate(tqdm(input_data, desc="Converting to grids")):
            try:
                # Validate input format
                if not all(key in sample for key in ["frames", "context", "question", "output"]):
                    logger.warning(f"Skipping sample {i}: missing required fields")
                    continue
                
                if len(sample["frames"]) != 4:
                    logger.warning(f"Skipping sample {i}: expected 4 frames, got {len(sample['frames'])}")
                    continue
                
                # Create sequence ID
                sequence_id = f"{i:06d}"
                
                # Create grid image
                grid_path = self.create_frame_grid(sample["frames"], sequence_id)
                
                # Adapt prompts for grid format
                grid_context, grid_question = self.create_grid_prompt(
                    sample["context"], 
                    sample["question"]
                )
                
                # Create grid-based sample
                grid_sample = {
                    "image": grid_path,
                    "context": grid_context,
                    "question": grid_question,
                    "output": sample["output"],
                    "original_frames": sample["frames"],
                    "sequence_id": sequence_id,
                    "conversion_method": "2x2_temporal_grid"
                }
                
                output_data.append(grid_sample)
                successful_conversions += 1
                
            except Exception as e:
                logger.error(f"Failed to convert sample {i}: {e}")
                continue
        
        # Save output dataset
        output_jsonl = self.output_dir / "pokemon_grid_dataset.jsonl"
        with open(output_jsonl, 'w') as f:
            for sample in output_data:
                f.write(json.dumps(sample) + '\n')
        
        # Generate conversion summary
        summary = {
            "input_sequences": len(input_data),
            "successful_conversions": successful_conversions,
            "failed_conversions": len(input_data) - successful_conversions,
            "success_rate": successful_conversions / len(input_data) if input_data else 0,
            "output_file": str(output_jsonl),
            "grid_images_dir": str(self.grid_images_dir),
            "conversion_settings": {
                "frame_size": self.frame_size,
                "grid_size": self.grid_size,
                "add_labels": self.add_labels,
                "border_width": self.border_width
            }
        }
        
        summary_path = self.output_dir / "conversion_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Log results
        logger.info("\n" + "="*60)
        logger.info("🎯 FRAME GRID CONVERSION COMPLETE")
        logger.info("="*60)
        logger.info(f"📊 Input sequences: {len(input_data)}")
        logger.info(f"✅ Successful conversions: {successful_conversions}")
        logger.info(f"❌ Failed conversions: {len(input_data) - successful_conversions}")
        logger.info(f"📈 Success rate: {summary['success_rate']:.1%}")
        logger.info(f"📄 Output dataset: {output_jsonl}")
        logger.info(f"🖼️ Grid images: {self.grid_images_dir}")
        logger.info(f"📋 Summary: {summary_path}")
        
        return str(output_jsonl)


def main():
    parser = argparse.ArgumentParser(description="Convert 4-frame sequences to 2x2 grid images")
    parser.add_argument("--input", required=True, help="Input JSONL file with 4-frame sequences")
    parser.add_argument("--output_dir", required=True, help="Output directory for grid dataset")
    parser.add_argument("--no-labels", action="store_true", help="Don't add temporal labels to grids")
    parser.add_argument("--border-width", type=int, default=2, help="Border width between frames")
    
    args = parser.parse_args()
    
    # Create converter
    converter = FrameGridConverter(
        input_jsonl=args.input,
        output_dir=args.output_dir,
        add_labels=not args.no_labels
    )
    
    # Set border width
    converter.border_width = args.border_width
    
    # Convert dataset
    try:
        output_file = converter.convert_dataset()
        logger.info(f"🎉 Conversion successful! Grid dataset: {output_file}")
    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()