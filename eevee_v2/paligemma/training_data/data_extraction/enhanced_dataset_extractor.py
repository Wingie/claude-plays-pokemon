#!/usr/bin/env python3
"""
Enhanced Dataset Extraction with Robust Action Parsing
Improves upon the original extraction script with comprehensive action extraction
and better validation for Pokemon button presses.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# Import our robust action extractor
from robust_action_extractor import PokemonActionExtractor, ExtractedAction, ActionSource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedTrainingPair:
    """Enhanced training pair with robust action extraction"""
    image_path: str
    prompt: str
    response: str
    extracted_action: Optional[ExtractedAction]
    metadata: Dict[str, Any]
    validation_passed: bool
    validation_issues: List[str]

class EnhancedDatasetExtractor:
    """Enhanced dataset extractor with robust action parsing"""
    
    def __init__(self, runs_path: str = "/Users/wingston/code/claude-plays-pokemon/eevee/runs"):
        self.runs_path = Path(runs_path)
        self.action_extractor = PokemonActionExtractor()
        self.output_dir = Path("/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "total_turns": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "action_sources": {},
            "validation_failures": 0,
            "context_distribution": {},
            "button_frequency": {}
        }
    
    def extract_action_with_validation(self, turn_data: Dict[str, Any]) -> Tuple[Optional[ExtractedAction], bool, List[str]]:
        """Extract action and validate it"""
        action = self.action_extractor.extract_action(turn_data)
        
        if not action:
            return None, False, ["No action could be extracted"]
        
        is_valid, issues = self.action_extractor.validate_action(action)
        
        # Update statistics
        self.stats["action_sources"][action.source.value] = \
            self.stats["action_sources"].get(action.source.value, 0) + 1
        
        self.stats["context_distribution"][action.context] = \
            self.stats["context_distribution"].get(action.context, 0) + 1
        
        for button in action.buttons:
            self.stats["button_frequency"][button] = \
                self.stats["button_frequency"].get(button, 0) + 1
        
        if not is_valid:
            self.stats["validation_failures"] += 1
        
        return action, is_valid, issues
    
    def create_enhanced_response(self, turn_data: Dict[str, Any], 
                               visual_analysis: str, 
                               action: ExtractedAction) -> str:
        """Create enhanced response text with action information"""
        
        # Extract strategic elements
        ai_analysis = turn_data.get("ai_analysis", {})
        parsed_json = ai_analysis.get("parsed_json", {}) if ai_analysis else {}
        if parsed_json is None:
            parsed_json = {}
        
        # Build response
        response_parts = []
        
        # Add strategic analysis
        reasoning = parsed_json.get("reasoning", "")
        observations = parsed_json.get("observations", "")
        context_detected = parsed_json.get("context_detected", action.context)
        confidence = parsed_json.get("confidence", "medium")
        
        response_parts.append(f"Context: {context_detected}")
        
        if observations:
            response_parts.append(f"Observations: {observations}")
        
        if reasoning:
            response_parts.append(f"Reasoning: {reasoning}")
        
        response_parts.append(f"Confidence: {confidence}")
        
        # Add action with source information
        action_text = ", ".join(action.buttons)
        response_parts.append(f"Action: {action_text}")
        
        # Add source metadata (for debugging/analysis)
        response_parts.append(f"Source: {action.source.value}")
        
        # Add visual analysis if available
        if visual_analysis and visual_analysis.strip():
            response_parts.append(f"\nVisual Context: {visual_analysis.strip()}")
        
        return "\n".join(response_parts)
    
    def extract_session_pairs(self, session_dir: Path, session_data: Dict[str, Any]) -> List[EnhancedTrainingPair]:
        """Extract enhanced training pairs from a session"""
        pairs = []
        turns = session_data.get("turns", [])
        session_goal = session_data.get("goal", "pokemon gameplay")
        
        for turn in turns:
            self.stats["total_turns"] += 1
            turn_number = turn.get("turn", 0)
            
            # Find screenshot
            screenshot_path = session_dir / "sshots" / f"step_{turn_number:04d}_grid.png"
            if not screenshot_path.exists():
                continue
            
            # Load visual analysis
            visual_analysis_path = session_dir / f"step_{turn_number:04d}_visual_analysis.txt"
            visual_analysis = ""
            if visual_analysis_path.exists():
                try:
                    with open(visual_analysis_path, 'r') as f:
                        visual_analysis = f.read().strip()
                except Exception as e:
                    logger.warning(f"Could not read visual analysis from {visual_analysis_path}: {e}")
            
            # Extract action with validation
            action, is_valid, issues = self.extract_action_with_validation(turn)
            
            if action:
                self.stats["successful_extractions"] += 1
                
                # Create enhanced response
                response = self.create_enhanced_response(turn, visual_analysis, action)
                
                # Create metadata
                metadata = {
                    "session_id": session_data.get("session_id"),
                    "turn": turn_number,
                    "goal": session_goal,
                    "template_used": turn.get("template_used"),
                    "template_version": turn.get("template_version"),
                    "action_source": action.source.value,
                    "action_confidence": action.confidence,
                    "context_detected": action.context,
                    "buttons_extracted": action.buttons,
                    "validation_passed": is_valid,
                    "validation_issues": issues,
                    "has_visual_analysis": len(visual_analysis) > 0,
                    "raw_action_text": action.raw_text
                }
                
                # Create training pair
                pair = EnhancedTrainingPair(
                    image_path=str(screenshot_path),
                    prompt=f"What is the next action for this Pokemon game screenshot? Goal: {session_goal}",
                    response=response,
                    extracted_action=action,
                    metadata=metadata,
                    validation_passed=is_valid,
                    validation_issues=issues
                )
                
                pairs.append(pair)
            else:
                self.stats["failed_extractions"] += 1
                logger.debug(f"Failed to extract action from turn {turn_number} in {session_dir.name}")
        
        return pairs
    
    def filter_training_pairs(self, training_pairs: List[EnhancedTrainingPair], 
                            require_validation: bool = True) -> List[EnhancedTrainingPair]:
        """Filter training pairs based on quality criteria"""
        filtered = []
        
        for pair in training_pairs:
            # Check validation requirement
            if require_validation and not pair.validation_passed:
                continue
            
            # Check image exists
            if not os.path.exists(pair.image_path):
                continue
            
            # Check for reasonable action
            if not pair.extracted_action or not pair.extracted_action.buttons:
                continue
            
            # Check confidence threshold
            if pair.extracted_action.confidence < 0.5:
                continue
            
            filtered.append(pair)
        
        logger.info(f"Filtered {len(training_pairs)} -> {len(filtered)} pairs")
        return filtered
    
    def export_enhanced_dataset(self, training_pairs: List[EnhancedTrainingPair], 
                              dataset_name: str = "enhanced_pokemon_dataset") -> str:
        """Export enhanced training pairs to JSONL format"""
        output_file = self.output_dir / f"{dataset_name}.jsonl"
        
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
                    "action_metadata": {
                        "buttons": pair.extracted_action.buttons if pair.extracted_action else [],
                        "source": pair.extracted_action.source.value if pair.extracted_action else "unknown",
                        "confidence": pair.extracted_action.confidence if pair.extracted_action else 0.0,
                        "context": pair.extracted_action.context if pair.extracted_action else "unknown",
                        "validation_passed": pair.validation_passed,
                        "validation_issues": pair.validation_issues
                    },
                    "metadata": pair.metadata
                }
                f.write(json.dumps(training_record) + '\n')
        
        logger.info(f"Exported {len(training_pairs)} enhanced training pairs to {output_file}")
        return str(output_file)
    
    def generate_enhanced_report(self, training_pairs: List[EnhancedTrainingPair]) -> Dict[str, Any]:
        """Generate comprehensive report with action extraction statistics"""
        
        # Basic statistics
        total_pairs = len(training_pairs)
        valid_pairs = sum(1 for p in training_pairs if p.validation_passed)
        
        # Button analysis
        button_combinations = {}
        for pair in training_pairs:
            if pair.extracted_action:
                combo = tuple(sorted(pair.extracted_action.buttons))
                button_combinations[combo] = button_combinations.get(combo, 0) + 1
        
        # Context analysis
        context_accuracy = {}
        for context, count in self.stats["context_distribution"].items():
            context_accuracy[context] = {
                "total": count,
                "valid": sum(1 for p in training_pairs 
                           if p.extracted_action and p.extracted_action.context == context and p.validation_passed)
            }
        
        report = {
            "extraction_summary": {
                "total_turns_processed": self.stats["total_turns"],
                "successful_extractions": self.stats["successful_extractions"],
                "failed_extractions": self.stats["failed_extractions"],
                "extraction_success_rate": self.stats["successful_extractions"] / max(self.stats["total_turns"], 1)
            },
            "validation_summary": {
                "total_training_pairs": total_pairs,
                "validation_passed": valid_pairs,
                "validation_failed": total_pairs - valid_pairs,
                "validation_success_rate": valid_pairs / max(total_pairs, 1)
            },
            "action_sources": self.stats["action_sources"],
            "context_distribution": self.stats["context_distribution"],
            "context_accuracy": context_accuracy,
            "button_frequency": self.stats["button_frequency"],
            "button_combinations": dict(sorted(button_combinations.items(), 
                                             key=lambda x: x[1], reverse=True)[:20]),
            "generation_timestamp": datetime.now().isoformat()
        }
        
        # Save report
        report_file = self.output_dir / "enhanced_extraction_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def extract_enhanced_dataset(self, require_validation: bool = True) -> Dict[str, Any]:
        """Main enhanced extraction method"""
        logger.info("Starting enhanced Pokemon dataset extraction...")
        
        training_pairs = []
        session_dirs = [d for d in self.runs_path.iterdir() if d.is_dir()]
        
        processed_sessions = 0
        
        for session_dir in session_dirs:
            logger.info(f"Processing session: {session_dir.name}")
            
            session_file = session_dir / "session_data.json"
            if not session_file.exists():
                continue
            
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    
                session_pairs = self.extract_session_pairs(session_dir, session_data)
                training_pairs.extend(session_pairs)
                processed_sessions += 1
                
                logger.info(f"Extracted {len(session_pairs)} pairs from {session_dir.name}")
                
            except Exception as e:
                logger.error(f"Error processing session {session_dir.name}: {e}")
        
        # Filter pairs
        filtered_pairs = self.filter_training_pairs(training_pairs, require_validation)
        
        # Export dataset
        output_file = self.export_enhanced_dataset(filtered_pairs)
        
        # Generate report
        report = self.generate_enhanced_report(training_pairs)
        
        # Add processing stats
        report["processing_stats"] = {
            "total_sessions_found": len(session_dirs),
            "processed_sessions": processed_sessions,
            "output_file": output_file
        }
        
        logger.info("Enhanced dataset extraction complete!")
        logger.info(f"Total training pairs: {len(training_pairs)}")
        logger.info(f"Valid training pairs: {len(filtered_pairs)}")
        logger.info(f"Extraction success rate: {self.stats['successful_extractions'] / max(self.stats['total_turns'], 1):.2%}")
        
        return report

def main():
    """Main execution function"""
    extractor = EnhancedDatasetExtractor()
    
    try:
        report = extractor.extract_enhanced_dataset(require_validation=True)
        
        print("\n" + "="*80)
        print("ENHANCED POKEMON DATASET EXTRACTION REPORT")
        print("="*80)
        
        # Extraction Summary
        ext_summary = report['extraction_summary']
        print(f"\nExtraction Summary:")
        print(f"  Total Turns Processed: {ext_summary['total_turns_processed']}")
        print(f"  Successful Extractions: {ext_summary['successful_extractions']}")
        print(f"  Failed Extractions: {ext_summary['failed_extractions']}")
        print(f"  Success Rate: {ext_summary['extraction_success_rate']:.2%}")
        
        # Validation Summary
        val_summary = report['validation_summary']
        print(f"\nValidation Summary:")
        print(f"  Total Training Pairs: {val_summary['total_training_pairs']}")
        print(f"  Validation Passed: {val_summary['validation_passed']}")
        print(f"  Validation Failed: {val_summary['validation_failed']}")
        print(f"  Validation Rate: {val_summary['validation_success_rate']:.2%}")
        
        # Action Sources
        print(f"\nAction Sources:")
        for source, count in report['action_sources'].items():
            print(f"  {source}: {count}")
        
        # Button Frequency
        print(f"\nTop Buttons:")
        for button, count in sorted(report['button_frequency'].items(), 
                                  key=lambda x: x[1], reverse=True)[:8]:
            print(f"  {button}: {count}")
        
        # Button Combinations
        print(f"\nTop Button Combinations:")
        for combo, count in list(report['button_combinations'].items())[:10]:
            combo_str = ", ".join(combo) if combo else "none"
            print(f"  [{combo_str}]: {count}")
        
        print(f"\nOutput File: {report['processing_stats']['output_file']}")
        
    except Exception as e:
        logger.error(f"Enhanced extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()