#!/usr/bin/env python3
"""
Eevee v1 Dataset Extraction Pipeline
Extracts visual-strategic training pairs from existing Eevee v1 runs data
for PaliGemma fine-tuning combining visual and strategic contexts.
"""

import json
import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PaliGemmaTrainingPair:
    """Represents a single training pair for PaliGemma fine-tuning"""
    image_path: str
    prompt: str
    response: str
    metadata: Dict[str, Any]

class SessionQualityFilter:
    """Filters sessions based on quality metrics"""
    
    def __init__(self):
        self.min_successful_turns = 3
        self.min_success_rate = 0.5
        self.excluded_contexts = ["stuck_patterns", "goal_misalignment"]
    
    def is_suitable_for_training(self, session_data: Dict[str, Any]) -> bool:
        """Determine if session is suitable for training data"""
        metadata = session_data.get("session_metadata", {})
        
        # Check minimum successful turns
        successful_turns = metadata.get("successful_turns", 0)
        if successful_turns < self.min_successful_turns:
            return False
            
        # Check success rate
        total_turns = metadata.get("total_turns", 1)
        success_rate = successful_turns / total_turns
        if success_rate < self.min_success_rate:
            return False
            
        # Check for excluded patterns (if metadata exists)
        # This would be implemented based on actual metadata structure
        return True

class EeveeV1DataExtractor:
    """Main data extraction class for Eevee v1 runs"""
    
    def __init__(self, runs_path: str = "/Users/wingston/code/claude-plays-pokemon/eevee/runs"):
        self.runs_path = Path(runs_path)
        self.quality_filter = SessionQualityFilter()
        self.output_dir = Path("/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_session_directories(self) -> List[Path]:
        """Get all session directories from runs path"""
        if not self.runs_path.exists():
            logger.error(f"Runs path does not exist: {self.runs_path}")
            return []
            
        session_dirs = [d for d in self.runs_path.iterdir() if d.is_dir()]
        logger.info(f"Found {len(session_dirs)} session directories")
        return session_dirs
    
    def load_session_data(self, session_dir: Path) -> Optional[Dict[str, Any]]:
        """Load session data from JSON file"""
        session_file = session_dir / "session_data.json"
        if not session_file.exists():
            logger.warning(f"No session_data.json found in {session_dir}")
            return None
            
        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading session data from {session_file}: {e}")
            return None
    
    def create_strategic_context(self, turn_data: Dict[str, Any]) -> str:
        """Create strategic context from turn data"""
        ai_analysis = turn_data.get("ai_analysis", {})
        parsed_json = ai_analysis.get("parsed_json", {})
        
        # Handle cases where parsed_json is None
        if parsed_json is None:
            parsed_json = {}
        
        # Extract strategic elements
        reasoning = parsed_json.get("reasoning", "unknown")
        observations = parsed_json.get("observations", "unknown")
        context_detected = parsed_json.get("context_detected", "unknown")
        confidence = parsed_json.get("confidence", "unknown")
        button_presses = parsed_json.get("button_presses", [])
        
        # Format strategic context
        context = f"""Strategic Analysis:
- Context: {context_detected}
- Observations: {observations}
- Reasoning: {reasoning}
- Confidence: {confidence}
- Recommended Action: {', '.join(button_presses)}"""
        
        return context
    
    def create_combined_context(self, turn_data: Dict[str, Any], visual_analysis: str) -> str:
        """Create combined context from AI analysis and visual analysis"""
        ai_analysis = turn_data.get("ai_analysis", {})
        parsed_json = ai_analysis.get("parsed_json", {})
        
        # Handle cases where parsed_json is None
        if parsed_json is None:
            parsed_json = {}
        
        # Extract strategic elements
        reasoning = parsed_json.get("reasoning", "unknown")
        observations = parsed_json.get("observations", "unknown")
        context_detected = parsed_json.get("context_detected", "unknown")
        confidence = parsed_json.get("confidence", "unknown")
        button_presses = parsed_json.get("button_presses", [])
        
        # Create combined context
        context = f"""Strategic Analysis:
- Context: {context_detected}
- AI Observations: {observations}
- Reasoning: {reasoning}
- Confidence: {confidence}
- Recommended Action: {', '.join(button_presses)}"""
        
        # Add visual analysis if available
        if visual_analysis:
            context += f"\n\nVisual Analysis:\n{visual_analysis}"
            
        return context
    
    def extract_session_pairs(self, session_dir: Path, session_data: Dict[str, Any]) -> List[PaliGemmaTrainingPair]:
        """Extract training pairs from a single session"""
        pairs = []
        turns = session_data.get("turns", [])
        session_goal = session_data.get("goal", "unknown goal")
        
        for turn in turns:
            turn_number = turn.get("turn", 0)
            # Fix screenshot path format based on actual file structure
            screenshot_path = session_dir / "sshots" / f"step_{turn_number:04d}_grid.png"
            visual_analysis_path = session_dir / f"step_{turn_number:04d}_visual_analysis.txt"
            
            # Check if screenshot exists
            if not screenshot_path.exists():
                continue
                
            # Load visual analysis if available
            visual_analysis = ""
            if visual_analysis_path.exists():
                try:
                    with open(visual_analysis_path, 'r') as f:
                        visual_analysis = f.read().strip()
                except Exception as e:
                    logger.warning(f"Could not read visual analysis from {visual_analysis_path}: {e}")
            
            # Create strategic context combining AI analysis and visual analysis
            strategic_context = self.create_combined_context(turn, visual_analysis)
            
            # Extract metadata safely
            ai_analysis = turn.get("ai_analysis", {})
            parsed_json = ai_analysis.get("parsed_json", {}) if ai_analysis else {}
            if parsed_json is None:
                parsed_json = {}
            
            # Create training pair
            pair = PaliGemmaTrainingPair(
                image_path=str(screenshot_path),
                prompt=f"Analyze this Pokemon game screenshot. Goal: {session_goal}. What should be the next action?",
                response=strategic_context,
                metadata={
                    "session_id": session_data.get("session_id"),
                    "turn": turn_number,
                    "goal": session_goal,
                    "template_used": turn.get("template_used"),
                    "template_version": turn.get("template_version"),
                    "context_detected": parsed_json.get("context_detected"),
                    "confidence": parsed_json.get("confidence"),
                    "has_visual_analysis": len(visual_analysis) > 0
                }
            )
            
            pairs.append(pair)
        
        return pairs
    
    def deduplicate_and_validate(self, training_pairs: List[PaliGemmaTrainingPair]) -> List[PaliGemmaTrainingPair]:
        """Remove duplicates and validate training pairs"""
        # Simple deduplication based on image path
        seen_images = set()
        deduplicated = []
        
        for pair in training_pairs:
            if pair.image_path not in seen_images:
                # Validate image exists
                if os.path.exists(pair.image_path):
                    seen_images.add(pair.image_path)
                    deduplicated.append(pair)
                else:
                    logger.warning(f"Image not found: {pair.image_path}")
        
        logger.info(f"Deduplicated {len(training_pairs)} -> {len(deduplicated)} pairs")
        return deduplicated
    
    def export_training_dataset(self, training_pairs: List[PaliGemmaTrainingPair]) -> str:
        """Export training pairs to JSONL format"""
        output_file = self.output_dir / "eevee_v1_paligemma_training.jsonl"
        
        with open(output_file, 'w') as f:
            for pair in training_pairs:
                training_record = {
                    "image": pair.image_path,
                    "conversations": [
                        {
                            "from": "human",
                            "value": pair.prompt
                        },
                        {
                            "from": "gpt", 
                            "value": pair.response
                        }
                    ],
                    "metadata": pair.metadata
                }
                f.write(json.dumps(training_record) + '\n')
        
        logger.info(f"Exported {len(training_pairs)} training pairs to {output_file}")
        return str(output_file)
    
    def generate_dataset_report(self, training_pairs: List[PaliGemmaTrainingPair]) -> Dict[str, Any]:
        """Generate comprehensive dataset report"""
        contexts = {}
        templates = {}
        confidence_levels = {}
        
        for pair in training_pairs:
            # Count contexts
            context = pair.metadata.get("context_detected", "unknown")
            contexts[context] = contexts.get(context, 0) + 1
            
            # Count templates
            template = pair.metadata.get("template_used", "unknown")
            templates[template] = templates.get(template, 0) + 1
            
            # Count confidence levels
            confidence = pair.metadata.get("confidence", "unknown")
            confidence_levels[confidence] = confidence_levels.get(confidence, 0) + 1
        
        report = {
            "total_training_pairs": len(training_pairs),
            "context_distribution": contexts,
            "template_distribution": templates,
            "confidence_distribution": confidence_levels,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        # Save report
        report_file = self.output_dir / "dataset_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def extract_training_dataset(self) -> Dict[str, Any]:
        """Main extraction method"""
        logger.info("Starting Eevee v1 dataset extraction...")
        
        training_pairs = []
        session_dirs = self.get_session_directories()
        
        processed_sessions = 0
        failed_sessions = 0
        
        for session_dir in session_dirs:
            logger.info(f"Processing session: {session_dir.name}")
            
            session_data = self.load_session_data(session_dir)
            if not session_data:
                failed_sessions += 1
                continue
                
            # Quality filtering
            if not self.quality_filter.is_suitable_for_training(session_data):
                logger.info(f"Skipping session {session_dir.name} - quality filter failed")
                continue
                
            # Extract pairs from this session
            session_pairs = self.extract_session_pairs(session_dir, session_data)
            training_pairs.extend(session_pairs)
            processed_sessions += 1
            
            logger.info(f"Extracted {len(session_pairs)} pairs from {session_dir.name}")
        
        # Deduplicate and validate
        training_pairs = self.deduplicate_and_validate(training_pairs)
        
        # Export dataset
        output_file = self.export_training_dataset(training_pairs)
        
        # Generate report
        report = self.generate_dataset_report(training_pairs)
        
        # Add processing stats to report
        report["processing_stats"] = {
            "total_sessions_found": len(session_dirs),
            "processed_sessions": processed_sessions,
            "failed_sessions": failed_sessions,
            "output_file": output_file
        }
        
        logger.info(f"Dataset extraction complete!")
        logger.info(f"Total training pairs: {len(training_pairs)}")
        logger.info(f"Processed sessions: {processed_sessions}/{len(session_dirs)}")
        
        return report

def main():
    """Main execution function"""
    extractor = EeveeV1DataExtractor()
    
    try:
        report = extractor.extract_training_dataset()
        
        print("\n" + "="*60)
        print("EEVEE V1 DATASET EXTRACTION REPORT")
        print("="*60)
        print(f"Total Training Pairs: {report['total_training_pairs']}")
        print(f"Processed Sessions: {report['processing_stats']['processed_sessions']}")
        print(f"Failed Sessions: {report['processing_stats']['failed_sessions']}")
        print(f"Output File: {report['processing_stats']['output_file']}")
        
        print("\nContext Distribution:")
        for context, count in report['context_distribution'].items():
            print(f"  {context}: {count}")
            
        print("\nTemplate Distribution:")
        for template, count in report['template_distribution'].items():
            print(f"  {template}: {count}")
            
        print("\nConfidence Distribution:")
        for confidence, count in report['confidence_distribution'].items():
            print(f"  {confidence}: {count}")
            
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()