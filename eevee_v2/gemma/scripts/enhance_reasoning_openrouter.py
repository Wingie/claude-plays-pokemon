#!/usr/bin/env python3
"""
OpenRouter Reasoning Enhancement Script for NeurIPS Pokemon Challenge
Generates alternative reasoning chains using OpenRouter's Gemini 2.0 Flash Exp to enhance training data diversity.
"""

import json
import os
import argparse
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import base64
from PIL import Image
import io
import time
import random
import re
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
def setup_logging(log_file: str = "enhancement.log"):
    """Setup file and console logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct:free"

class OpenRouterClient:
    """OpenRouter API client for Gemini 2.0 Flash Exp."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API requests."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (OpenRouter has size limits)
                if img.width > 1024 or img.height > 1024:
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode to base64
                return base64.b64encode(img_byte_arr).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    async def generate_reasoning(self, prompt: str, image_path: str, max_retries: int = 3) -> Optional[str]:
        """Call OpenRouter API with Gemini 2.0 Flash Exp with retry logic."""
        for attempt in range(max_retries):
            try:
                # Encode image
                image_b64 = self._encode_image(image_path)
                if not image_b64:
                    return None
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/anthropics/claude-plays-pokemon",
                    "X-Title": "Pokemon AI Training Data Enhancement"
                }
                
                payload = {
                    "model": GEMINI_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                async with self.session.post(OPENROUTER_API_URL, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        error_text = await response.text()
                        wait_time = 4 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries})")
                        logger.info(f"Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error {response.status}: {error_text}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error calling OpenRouter API (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None
        
        return None

class ReasoningEnhancer:
    """Generates alternative reasoning chains for existing training sequences."""
    
    def __init__(self, api_client: OpenRouterClient):
        self.api_client = api_client
        
        # Alternative reasoning perspectives
        self.reasoning_perspectives = [
            {
                "name": "strategic_depth",
                "system": "You are a Pokemon battle strategist with deep knowledge of type effectiveness, move sets, and competitive play.",
                "focus": "strategic implications, type matchups, and tactical advantages"
            },
            {
                "name": "exploration_efficiency", 
                "system": "You are a Pokemon exploration expert focused on efficient navigation and area coverage.",
                "focus": "navigation efficiency, pathfinding, and discovery opportunities"
            },
            {
                "name": "speedrun_optimization",
                "system": "You are a Pokemon speedrunner focused on frame-perfect execution and route optimization.",
                "focus": "time optimization, movement efficiency, and speedrun tactics"
            }
        ]
    
    def _create_enhancement_prompt(self, sequence: Dict[str, Any], perspective: Dict[str, str]) -> str:
        """Create enhancement prompt for a specific perspective."""
        
        # Extract original data
        try:
            original_output = json.loads(sequence.get("output", "{}"))
            button = original_output.get("button", "a")
            original_reasoning = original_output.get("reasoning", "pokemon_action")
            context_type = original_output.get("context", "navigation")
            scene_description = original_output.get("scene_description", "pokemon_gameplay")
        except:
            button = "a"
            original_reasoning = "pokemon_action"
            context_type = "navigation"
            scene_description = "pokemon_gameplay"
        
        # Build context
        context = sequence.get("context", "Pokemon gameplay sequence")
        metadata = sequence.get("metadata", {})
        session_goal = metadata.get("session_goal", "Pokemon adventure")
        
        prompt = f"""**SYSTEM:** {perspective["system"]}

**POKEMON GAMEPLAY ANALYSIS:**
You are analyzing a 2x2 grid showing 4 consecutive Pokemon gameplay frames (~960ms total):

┌─────────┬─────────┐
│ t=0     │ t=1     │  ← Temporal progression  
│ (start) │ (+240ms)│
├─────────┼─────────┤
│ t=2     │ t=3     │
│ (+480ms)│ (+720ms)│
└─────────┴─────────┘

**CONTEXT:**
- Session Goal: {session_goal}
- Game Context: {context}
- Situation Type: {context_type}
- Scene: {scene_description}

**ORIGINAL ANALYSIS:**
- Action: {button}
- Reasoning: {original_reasoning}

**YOUR TASK:**
Analyze this temporal sequence from a **{perspective["focus"]}** perspective. 
The optimal action is **{button}** - provide alternative reasoning for WHY this action is optimal.

Focus on {perspective["focus"]} in your analysis.

**RESPONSE FORMAT (MANDATORY JSON):**
```json
{{
  "button": "{button}",
  "reasoning": "your_alternative_reasoning_here",
  "context": "{context_type}",
  "scene_description": "your_scene_analysis_here"
}}
```

**IMPORTANT:** 
- Keep the same button action ({button})
- Provide fresh reasoning from your perspective
- Use concise, technical language
- Focus on the specific aspects mentioned above"""

        return prompt
    
    async def enhance_sequence(self, sequence: Dict[str, Any], 
                             max_alternatives: int = 2) -> List[Dict[str, Any]]:
        """Generate alternative reasoning chains for a sequence."""
        enhanced_sequences = []
        
        # Select random perspectives
        selected_perspectives = random.sample(
            self.reasoning_perspectives, 
            min(max_alternatives, len(self.reasoning_perspectives))
        )
        
        # Get image path
        image_path = sequence.get("image", "")
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return []
        
        for perspective in selected_perspectives:
            try:
                # Create prompt
                prompt = self._create_enhancement_prompt(sequence, perspective)
                
                # Generate reasoning
                response = await self.api_client.generate_reasoning(prompt, image_path)
                if not response:
                    continue
                
                # Extract JSON from response
                json_text = self._extract_json_from_response(response)
                if not json_text:
                    continue
                
                # Parse JSON
                try:
                    parsed_json = json.loads(json_text)
                    
                    # Validate required fields
                    if not all(field in parsed_json for field in ["button", "reasoning", "context"]):
                        continue
                    
                    # Create enhanced sequence
                    enhanced_sequence = sequence.copy()
                    enhanced_sequence["output"] = json.dumps(parsed_json)
                    enhanced_sequence["metadata"] = sequence.get("metadata", {}).copy()
                    enhanced_sequence["metadata"]["reasoning_perspective"] = perspective["name"]
                    enhanced_sequence["metadata"]["enhancement_timestamp"] = datetime.now().isoformat()
                    enhanced_sequence["metadata"]["enhanced_by"] = GEMINI_MODEL
                    
                    enhanced_sequences.append(enhanced_sequence)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}")
                    continue
                
                # Rate limiting for free tier
                logger.debug(f"Rate limiting: waiting 3s...")
                await asyncio.sleep(3.0)
                
            except Exception as e:
                logger.error(f"Error enhancing sequence with {perspective['name']}: {e}")
                continue
        
        return enhanced_sequences
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON from API response."""
        # Try to find JSON in code blocks
        json_pattern = r'```json\n(.*?)\n```'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try to find JSON object
        json_pattern = r'\{[^{}]*"button"[^{}]*"reasoning"[^{}]*"context"[^{}]*\}'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            return match.group(0)
        
        # Try to find any JSON-like structure
        json_pattern = r'\{.*?"button".*?\}'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            return match.group(0)
        
        return None

async def main():
    parser = argparse.ArgumentParser(description="Enhance Pokemon training data with OpenRouter")
    parser.add_argument("--input_file", default="training_data/pokemon_grid_dataset_final.jsonl", 
                       help="Input JSONL training file")
    parser.add_argument("--output_file", default="training_data/pokemon_grid_dataset_final.jsonl", 
                       help="Output enhanced JSONL file (defaults to append to input file)")
    parser.add_argument("--max_sequences", type=int, default=50, 
                       help="Maximum sequences to enhance (for testing)")
    parser.add_argument("--alternatives_per_sequence", type=int, default=2, 
                       help="Alternative reasoning chains per sequence")
    parser.add_argument("--openrouter_key", 
                       help="OpenRouter API key (or use OPENROUTER_API_KEY env var)")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.openrouter_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OpenRouter API key is required")
        logger.error("Set OPENROUTER_API_KEY environment variable or use --openrouter_key")
        return
    
    # Load input data
    logger.info(f"Loading training data from {args.input_file}...")
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        return
    
    sequences = []
    with open(args.input_file, 'r') as f:
        for line in f:
            try:
                sequences.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    
    logger.info(f"Loaded {len(sequences)} sequences")
    
    if args.max_sequences:
        sequences = sequences[:args.max_sequences]
        logger.info(f"Processing first {len(sequences)} sequences for testing")
    
    # Create output directory
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Process sequences
    enhanced_count = 0
    total_sequences = []
    
    logger.info(f"Enhancing sequences with OpenRouter ...", GEMINI_MODEL)
    logger.info(f"Target: {len(sequences)} sequences × {args.alternatives_per_sequence} alternatives = {len(sequences) * args.alternatives_per_sequence} new sequences")
    
    # Open output file for appending (or write if new file)
    append_mode = args.output_file == args.input_file
    file_mode = 'a' if append_mode else 'w'
    
    if append_mode:
        logger.info(f"Appending enhanced sequences to existing file: {args.output_file}")
    else:
        logger.info(f"Writing enhanced sequences to new file: {args.output_file}")
    
    with open(args.output_file, file_mode) as output_file:
        async with OpenRouterClient(api_key) as client:
            enhancer = ReasoningEnhancer(client)
            
            for i, sequence in enumerate(sequences):
                logger.info(f"Processing sequence {i+1}/{len(sequences)}...")
                
                # Only write original sequence if not appending to same file
                if not append_mode:
                    output_file.write(json.dumps(sequence) + '\n')
                    output_file.flush()  # Force write to disk
                    total_sequences.append(sequence)
                else:
                    # When appending, only count original sequences, don't write them again
                    total_sequences.append(sequence)
                
                # Generate alternatives
                alternatives = await enhancer.enhance_sequence(sequence, args.alternatives_per_sequence)
                
                # Write each alternative immediately as it's generated
                for alt in alternatives:
                    output_file.write(json.dumps(alt) + '\n')
                    output_file.flush()  # Force write to disk
                    
                total_sequences.extend(alternatives)
                enhanced_count += len(alternatives)
                
                logger.info(f"Generated {len(alternatives)} alternatives for sequence {i+1} - written to file")
                
                # Progress report
                if (i + 1) % 5 == 0:
                    logger.info(f"PROGRESS: {i+1}/{len(sequences)} sequences processed, {enhanced_count} alternatives generated")
                    logger.info(f"Current enhancement ratio: {len(total_sequences)/len(sequences):.1f}x")
                    logger.info(f"File size: {os.path.getsize(args.output_file)} bytes")
    
    logger.info(f"Final enhanced dataset saved to {args.output_file}")
    
    # Create summary
    summary = {
        "enhancement_timestamp": datetime.now().isoformat(),
        "original_sequences": len(sequences),
        "enhanced_sequences": enhanced_count,
        "total_sequences": len(total_sequences),
        "enhancement_ratio": len(total_sequences) / len(sequences) if sequences else 0,
        "model_used": GEMINI_MODEL,
        "alternatives_per_sequence": args.alternatives_per_sequence
    }
    
    summary_path = output_path.parent / f"{output_path.stem}_enhancement_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\n✅ Enhancement complete!")
    logger.info(f"Original sequences: {len(sequences)}")
    logger.info(f"Enhanced sequences: {enhanced_count}")
    logger.info(f"Total sequences: {len(total_sequences)}")
    logger.info(f"Enhancement ratio: {len(total_sequences)/len(sequences):.1f}x")
    logger.info(f"Summary saved to: {summary_path}")
    logger.info(f"Enhanced dataset: {args.output_file}")
    logger.info(f"Log file: enhancement.log")

if __name__ == "__main__":
    asyncio.run(main())