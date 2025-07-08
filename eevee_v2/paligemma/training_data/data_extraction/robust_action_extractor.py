#!/usr/bin/env python3
"""
Robust Action Extractor for Pokemon Game Data
Extracts clean button presses from various AI response formats
"""

import re
import json
from typing import List, Optional, Dict, Any, Tuple

class PokemonActionExtractor:
    """Robust action extraction with multiple fallback methods"""
    
    def __init__(self):
        # Valid Pokemon Game Boy buttons
        self.valid_buttons = {
            'up', 'down', 'left', 'right', 'a', 'b', 'start', 'select'
        }
        
        # Unicode variants mapping
        self.unicode_mappings = {
            '↑': 'up', '⬆': 'up', '⬆️': 'up',
            '↓': 'down', '⬇': 'down', '⬇️': 'down', 
            '←': 'left', '⬅': 'left', '⬅️': 'left',
            '→': 'right', '➡': 'right', '➡️': 'right',
            'A': 'a', 'B': 'b',
            'START': 'start', 'SELECT': 'select'
        }
        
        # Action phrase mappings
        self.action_phrases = {
            'move_up': 'up', 'move_north': 'up', 'go_up': 'up',
            'move_down': 'down', 'move_south': 'down', 'go_down': 'down',
            'move_left': 'left', 'move_west': 'left', 'go_left': 'left', 
            'move_right': 'right', 'move_east': 'right', 'go_right': 'right',
            'interact': 'a', 'select': 'a', 'confirm': 'a',
            'cancel': 'b', 'back': 'b', 'exit': 'b',
            'menu': 'start', 'pause': 'start'
        }
        
        # Regex patterns for extraction
        self.patterns = [
            # Direct button array: ["up", "down"]
            r'"button_presses":\s*\[\s*"([^"]+)"[^\]]*\]',
            # Recommended Action: up
            r'Recommended Action:\s*([a-zA-Z, ]+)',
            # Action: move_up
            r'Action:\s*([a-zA-Z_]+)',
            # Single button in quotes
            r'"([a-zA-Z]+)"\s*(?:button|action|move)',
            # JSON button_presses field
            r'button_presses["\']:\s*\[([^\]]+)\]',
            # Button press sequences
            r'(?:press|hit|use)\s+([a-zA-Z]+)\s*(?:button)?'
        ]
    
    def normalize_button(self, button: str) -> Optional[str]:
        """Normalize button to standard format"""
        if not button:
            return None
            
        button = button.strip().lower()
        
        # Direct match
        if button in self.valid_buttons:
            return button
            
        # Unicode mapping
        if button in self.unicode_mappings:
            return self.unicode_mappings[button]
            
        # Phrase mapping
        if button in self.action_phrases:
            return self.action_phrases[button]
            
        # Partial matches
        for phrase, action in self.action_phrases.items():
            if phrase in button or button in phrase:
                return action
                
        return None
    
    def extract_from_parsed_json(self, turn_data: Dict[str, Any]) -> List[str]:
        """Extract actions from parsed JSON structure"""
        ai_analysis = turn_data.get("ai_analysis", {})
        parsed_json = ai_analysis.get("parsed_json", {})
        
        if not parsed_json or parsed_json is None:
            return []
            
        # Try button_presses array
        button_presses = parsed_json.get("button_presses", [])
        if button_presses:
            actions = []
            for button in button_presses:
                normalized = self.normalize_button(str(button))
                if normalized:
                    actions.append(normalized)
            return actions
            
        return []
    
    def extract_from_raw_text(self, turn_data: Dict[str, Any]) -> List[str]:
        """Extract actions from raw AI response text"""
        ai_analysis = turn_data.get("ai_analysis", {})
        raw_text = ai_analysis.get("raw_text", "")
        
        if not raw_text:
            return []
            
        # Try JSON extraction from raw text
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                button_presses = json_data.get("button_presses", [])
                if button_presses:
                    actions = []
                    for button in button_presses:
                        normalized = self.normalize_button(str(button))
                        if normalized:
                            actions.append(normalized)
                    return actions
        except:
            pass
        
        # Try regex patterns
        for pattern in self.patterns:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Handle comma-separated actions
                    if ',' in match:
                        actions = []
                        for action in match.split(','):
                            normalized = self.normalize_button(action.strip())
                            if normalized:
                                actions.append(normalized)
                        if actions:
                            return actions
                    else:
                        normalized = self.normalize_button(match)
                        if normalized:
                            return [normalized]
        
        return []
    
    def extract_from_strategic_analysis(self, gpt_response: str) -> List[str]:
        """Extract actions from strategic analysis response"""
        if not gpt_response:
            return []
            
        # Look for "Recommended Action:" line
        lines = gpt_response.split('\n')
        for line in lines:
            if 'Recommended Action:' in line:
                action_text = line.split('Recommended Action:')[-1].strip()
                
                # Handle comma-separated actions
                if ',' in action_text:
                    actions = []
                    for action in action_text.split(','):
                        normalized = self.normalize_button(action.strip())
                        if normalized:
                            actions.append(normalized)
                    return actions
                else:
                    normalized = self.normalize_button(action_text)
                    if normalized:
                        return [normalized]
        
        return []
    
    def extract_from_visual_analysis(self, turn_data: Dict[str, Any]) -> List[str]:
        """Extract actions from visual analysis data"""
        # This would be implemented if visual analysis contains action data
        # For now, placeholder
        return []
    
    def extract_actions(self, turn_data: Dict[str, Any], gpt_response: str = "") -> Tuple[List[str], float]:
        """
        Extract actions using multiple methods with confidence scoring
        Returns: (actions, confidence_score)
        """
        extraction_methods = [
            ("parsed_json", self.extract_from_parsed_json),
            ("raw_text", self.extract_from_raw_text), 
            ("strategic_analysis", lambda td: self.extract_from_strategic_analysis(gpt_response)),
            ("visual_analysis", self.extract_from_visual_analysis)
        ]
        
        for method_name, extract_func in extraction_methods:
            try:
                actions = extract_func(turn_data)
                if actions:
                    # Calculate confidence based on method and action validity
                    confidence = self.calculate_confidence(actions, method_name)
                    return actions, confidence
            except Exception as e:
                continue
        
        return [], 0.0
    
    def calculate_confidence(self, actions: List[str], method: str) -> float:
        """Calculate confidence score for extracted actions"""
        if not actions:
            return 0.0
            
        # Base confidence by extraction method
        method_confidence = {
            "parsed_json": 0.95,
            "raw_text": 0.85,
            "strategic_analysis": 0.80,
            "visual_analysis": 0.75
        }
        
        base_confidence = method_confidence.get(method, 0.5)
        
        # Validate all actions are valid Pokemon buttons
        valid_actions = sum(1 for action in actions if action in self.valid_buttons)
        validity_ratio = valid_actions / len(actions) if actions else 0
        
        return base_confidence * validity_ratio
    
    def validate_actions(self, actions: List[str]) -> Dict[str, Any]:
        """Validate extracted actions against Pokemon rules"""
        validation_result = {
            "valid": True,
            "actions": actions,
            "issues": []
        }
        
        if not actions:
            validation_result["valid"] = False
            validation_result["issues"].append("No actions extracted")
            return validation_result
        
        # Check for invalid buttons
        for action in actions:
            if action not in self.valid_buttons:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Invalid button: {action}")
        
        # Check for conflicting directional inputs
        directions = set(actions) & {'up', 'down', 'left', 'right'}
        if len(directions) > 1:
            conflicting = {'up', 'down'} & directions
            if len(conflicting) == 2:
                validation_result["issues"].append("Conflicting vertical directions")
            conflicting = {'left', 'right'} & directions  
            if len(conflicting) == 2:
                validation_result["issues"].append("Conflicting horizontal directions")
        
        return validation_result

def main():
    """Demo of robust action extraction"""
    extractor = PokemonActionExtractor()
    
    # Test cases
    test_cases = [
        {
            "ai_analysis": {
                "parsed_json": {"button_presses": ["up"]},
                "raw_text": "```json\n{\"button_presses\": [\"up\"]}\n```"
            }
        },
        {
            "ai_analysis": {
                "raw_text": "I recommend pressing the up button to move north"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        actions, confidence = extractor.extract_actions(test_case)
        validation = extractor.validate_actions(actions)
        
        print(f"Extracted Actions: {actions}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Validation: {validation}")

if __name__ == "__main__":
    main()