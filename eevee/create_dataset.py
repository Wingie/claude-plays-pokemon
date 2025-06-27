#!/usr/bin/env python3
"""
Dataset Creation Script for Eevee Pokemon AI Training
Extracts training data from existing session runs to create fine-tuning datasets
"""

import argparse
import json
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

class DatasetCreator:
    """Creates fine-tuning datasets from existing Eevee session data"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.runs_dir = Path(__file__).parent / "runs"
        
    def log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"📋 {message}")
    
    def find_sessions(self) -> List[Path]:
        """Find all available session directories"""
        sessions = []
        for session_dir in self.runs_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith(('battle_', 'session_')):
                # Check if it has screenshots and visual analysis
                sshots_dir = session_dir / "sshots"
                if sshots_dir.exists() and any(session_dir.glob("step_*_visual_analysis.txt")):
                    sessions.append(session_dir)
        
        return sorted(sessions, key=lambda x: x.name)
    
    def load_session_data(self, session_path: Path) -> Dict[str, Any]:
        """Load session metadata and validate data availability"""
        metadata_file = session_path / "dataset_metadata.json"
        session_data_file = session_path / "session_data.json"
        
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        session_data = {}
        if session_data_file.exists():
            with open(session_data_file, 'r') as f:
                session_data = json.load(f)
        
        # Count available data
        sshots_dir = session_path / "sshots"
        screenshots = list(sshots_dir.glob("step_*_grid.png")) if sshots_dir.exists() else []
        visual_analyses = list(session_path.glob("step_*_visual_analysis.txt"))
        
        return {
            'metadata': metadata,
            'session_data': session_data,
            'path': session_path,
            'screenshots': screenshots,
            'visual_analyses': visual_analyses,
            'total_steps': len(screenshots)
        }
    
    def encode_screenshot(self, screenshot_path: Path) -> str:
        """Encode screenshot as base64 string"""
        try:
            with open(screenshot_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            self.log(f"Error encoding {screenshot_path}: {e}")
            return ""
    
    def load_visual_analysis(self, analysis_path: Path) -> str:
        """Load visual analysis text file"""
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            self.log(f"Error reading {analysis_path}: {e}")
            return ""
    
    def create_visual_agent_entry(self, screenshot_b64: str, visual_analysis: str, step_num: int) -> Dict[str, Any]:
        """Create training entry for visual agent (screenshot analysis)"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": f"data:image/png;base64,{screenshot_b64}"
                        },
                        {
                            "type": "text", 
                            "text": "Analyze this Pokemon GBA screenshot. Identify the scene type (battle/navigation/menu/pokemon_center), describe what you see, and provide spatial analysis with grid coordinates if relevant."
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": visual_analysis
                }
            ],
            "metadata": {
                "step": step_num,
                "task_type": "visual_analysis",
                "agent_persona": "visual_context_analyzer"
            }
        }
    
    def create_strategic_agent_entry(self, screenshot_b64: str, visual_analysis: str, step_num: int) -> Dict[str, Any]:
        """Create training entry for strategic agent (decision making)"""
        # Extract any decisions or actions mentioned in visual analysis
        decision_prompt = f"""Based on this Pokemon GBA screenshot and visual analysis, make the next strategic decision.

Visual Analysis: {visual_analysis}

Provide your next action as a JSON response with button press and reasoning."""
        
        # For now, create a synthetic strategic decision based on visual analysis
        # In a real scenario, this would come from the actual decision made
        synthetic_decision = self._generate_synthetic_decision(visual_analysis, step_num)
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": f"data:image/png;base64,{screenshot_b64}"
                        },
                        {
                            "type": "text",
                            "text": decision_prompt
                        }
                    ]
                },
                {
                    "role": "assistant", 
                    "content": synthetic_decision
                }
            ],
            "metadata": {
                "step": step_num,
                "task_type": "strategic_decision",
                "agent_persona": "ash_ketchum_battle_expert"
            }
        }
    
    def create_review_agent_entry(self, screenshot_b64: str, visual_analysis: str, step_num: int) -> Dict[str, Any]:
        """Create training entry for review agent (learning and evaluation)"""
        review_prompt = f"""Review this Pokemon gameplay step and provide learning insights.

Step {step_num} Analysis: {visual_analysis}

Evaluate the effectiveness of this action and suggest improvements for future similar situations."""
        
        synthetic_review = self._generate_synthetic_review(visual_analysis, step_num)
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image", 
                            "image": f"data:image/png;base64,{screenshot_b64}"
                        },
                        {
                            "type": "text",
                            "text": review_prompt
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": synthetic_review
                }
            ],
            "metadata": {
                "step": step_num,
                "task_type": "episode_review",
                "agent_persona": "review_agent"
            }
        }
    
    def _generate_synthetic_decision(self, visual_analysis: str, step_num: int) -> str:
        """Generate synthetic strategic decision based on visual analysis"""
        # Simple heuristic-based decision generation
        analysis_lower = visual_analysis.lower()
        
        if "battle" in analysis_lower and "menu" in analysis_lower:
            return '{"action": "A", "reasoning": "In battle menu, selecting attack option"}'
        elif "navigation" in analysis_lower or "overworld" in analysis_lower:
            if "right" in analysis_lower:
                return '{"action": "RIGHT", "reasoning": "Moving right in overworld navigation"}'
            elif "left" in analysis_lower:
                return '{"action": "LEFT", "reasoning": "Moving left in overworld navigation"}'
            elif "up" in analysis_lower:
                return '{"action": "UP", "reasoning": "Moving up in overworld navigation"}'
            elif "down" in analysis_lower:
                return '{"action": "DOWN", "reasoning": "Moving down in overworld navigation"}'
        elif "pokemon center" in analysis_lower:
            return '{"action": "A", "reasoning": "Interacting with Pokemon Center NPC for healing"}'
        elif "menu" in analysis_lower:
            return '{"action": "A", "reasoning": "Selecting menu option"}'
        
        return '{"action": "A", "reasoning": "Default interaction action"}'
    
    def _generate_synthetic_review(self, visual_analysis: str, step_num: int) -> str:
        """Generate synthetic review based on visual analysis"""
        analysis_lower = visual_analysis.lower()
        
        if "battle" in analysis_lower:
            return f"Step {step_num}: Battle scene detected. Action appears appropriate for battle progression. Good spatial awareness of battle interface."
        elif "navigation" in analysis_lower:
            return f"Step {step_num}: Navigation step executed. Movement decision shows good understanding of overworld traversal. Continue exploring systematically."
        elif "pokemon center" in analysis_lower:
            return f"Step {step_num}: Pokemon Center interaction. Healing strategy is sound, maintaining party health for continued exploration."
        else:
            return f"Step {step_num}: Scene analysis completed. Decision-making process demonstrates good game state understanding."
    
    def create_datasets(self, session_path: Path, count: int) -> Dict[str, int]:
        """Create all three dataset types from session data"""
        session_data = self.load_session_data(session_path)
        
        if session_data['total_steps'] == 0:
            self.log(f"No data found in session {session_path.name}")
            return {"visual": 0, "strategic": 0, "review": 0}
        
        self.log(f"Processing session {session_path.name} with {session_data['total_steps']} steps")
        
        # Select random steps up to count limit
        available_steps = min(count, session_data['total_steps'])
        selected_indices = sorted(random.sample(range(session_data['total_steps']), available_steps))
        
        visual_entries = []
        strategic_entries = []
        review_entries = []
        
        for i, idx in enumerate(selected_indices):
            screenshot_path = session_data['screenshots'][idx]
            analysis_path = session_data['visual_analyses'][idx]
            
            # Extract step number from filename
            step_num = int(screenshot_path.stem.split('_')[1])
            
            # Load data
            screenshot_b64 = self.encode_screenshot(screenshot_path)
            visual_analysis = self.load_visual_analysis(analysis_path)
            
            if not screenshot_b64 or not visual_analysis:
                self.log(f"Skipping step {step_num} due to missing data")
                continue
            
            # Create entries for each agent type
            visual_entries.append(self.create_visual_agent_entry(screenshot_b64, visual_analysis, step_num))
            strategic_entries.append(self.create_strategic_agent_entry(screenshot_b64, visual_analysis, step_num))
            review_entries.append(self.create_review_agent_entry(screenshot_b64, visual_analysis, step_num))
            
            self.log(f"Processed step {step_num} ({i+1}/{available_steps})")
        
        # Save datasets
        output_dir = session_path
        results = {}
        
        datasets = {
            "visual_agent_dataset.jsonl": visual_entries,
            "strategic_agent_dataset.jsonl": strategic_entries, 
            "review_agent_dataset.jsonl": review_entries
        }
        
        for filename, entries in datasets.items():
            output_path = output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            results[filename.split('_')[0]] = len(entries)
            self.log(f"✅ Created {filename} with {len(entries)} entries")
        
        return results
    
    def list_available_sessions(self):
        """List all available sessions with data counts"""
        sessions = self.find_sessions()
        
        print(f"\n📊 Available Sessions ({len(sessions)} found):")
        print("=" * 80)
        
        for session_path in sessions:
            session_data = self.load_session_data(session_path)
            metadata = session_data['metadata']
            
            print(f"📁 {session_path.name}")
            print(f"   Steps: {session_data['total_steps']}")
            print(f"   Success Rate: {metadata.get('success_rate', 'N/A')}")
            print(f"   Quality Turns: {metadata.get('quality_turns', 'N/A')}")
            if 'export_timestamp' in metadata:
                print(f"   Exported: {metadata['export_timestamp']}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Create fine-tuning datasets from Eevee session data")
    parser.add_argument('--session', type=str, help='Session name to process (e.g., battle_first_20250625_103555)')
    parser.add_argument('--count', type=int, default=10, help='Number of screenshots to process (default: 10)')
    parser.add_argument('--list', action='store_true', help='List available sessions')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    creator = DatasetCreator(verbose=args.verbose)
    
    if args.list:
        creator.list_available_sessions()
        return
    
    if not args.session:
        print("❌ Please specify a session name with --session or use --list to see available sessions")
        return
    
    # Find session directory
    session_path = creator.runs_dir / args.session
    if not session_path.exists():
        print(f"❌ Session '{args.session}' not found in {creator.runs_dir}")
        creator.list_available_sessions()
        return
    
    print(f"🚀 Creating datasets from session: {args.session}")
    print(f"📊 Processing up to {args.count} screenshots")
    print(f"💾 Output directory: {session_path}")
    print()
    
    # Create datasets
    results = creator.create_datasets(session_path, args.count)
    
    print(f"\n✅ Dataset creation completed!")
    print(f"📈 Visual Agent Dataset: {results['visual']} entries")
    print(f"🎯 Strategic Agent Dataset: {results['strategic']} entries")  
    print(f"📝 Review Agent Dataset: {results['review']} entries")
    print(f"📁 Files saved to: {session_path}")


if __name__ == "__main__":
    main()