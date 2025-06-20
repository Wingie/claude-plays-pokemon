"""
Navigation Enhancement System for Eevee
Implements screenshot comparison, loop detection, and stuck recovery strategies
"""

import cv2
import numpy as np
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import deque


@dataclass
class TurnData:
    """Represents data for a single turn"""
    turn_number: int
    timestamp: str
    screenshot_path: str
    screenshot_hash: str
    buttons_pressed: List[str]
    visual_similarity: float
    progress_made: bool
    ai_reasoning: str


class NavigationEnhancer:
    """
    Enhanced navigation system with loop detection and visual progress tracking
    """
    
    def __init__(self, history_size: int = 20, similarity_threshold: float = 0.95):
        """
        Initialize navigation enhancer
        
        Args:
            history_size: Number of recent turns to track
            similarity_threshold: Threshold for detecting identical screenshots
        """
        self.history_size = history_size
        self.similarity_threshold = similarity_threshold
        
        # Turn history tracking
        self.turn_history: deque[TurnData] = deque(maxlen=history_size)
        self.recent_actions: deque[List[str]] = deque(maxlen=10)
        
        # Loop detection state
        self.stuck_counter = 0
        self.stuck_threshold = 3  # Number of consecutive identical actions to trigger stuck mode
        self.stuck_mode = False
        self.last_stuck_trigger = 0
        
        # Visual similarity tracking
        self.last_screenshot_hash = None
        self.consecutive_similar_screenshots = 0
        
        # Progress tracking
        self.visual_landmarks = []
        self.position_progress_score = 0.0
        
    def add_turn_data(
        self, 
        turn_number: int, 
        screenshot_path: str, 
        buttons_pressed: List[str], 
        ai_reasoning: str = ""
    ) -> Dict[str, Any]:
        """
        Process a new turn and detect navigation issues
        
        Args:
            turn_number: Current turn number
            screenshot_path: Path to screenshot file
            buttons_pressed: List of buttons pressed this turn
            ai_reasoning: AI's reasoning for this action
            
        Returns:
            Analysis results with progress and loop detection info
        """
        # Calculate screenshot hash for comparison
        screenshot_hash = self._calculate_screenshot_hash(screenshot_path)
        
        # Calculate visual similarity with previous screenshot
        visual_similarity = self._calculate_visual_similarity(screenshot_path)
        
        # Detect if visual progress was made
        progress_made = visual_similarity < self.similarity_threshold
        
        # Create turn data
        turn_data = TurnData(
            turn_number=turn_number,
            timestamp=datetime.now().isoformat(),
            screenshot_path=screenshot_path,
            screenshot_hash=screenshot_hash,
            buttons_pressed=buttons_pressed,
            visual_similarity=visual_similarity,
            progress_made=progress_made,
            ai_reasoning=ai_reasoning
        )
        
        # Add to history
        self.turn_history.append(turn_data)
        self.recent_actions.append(buttons_pressed)
        
        # Update tracking state
        self._update_tracking_state(turn_data)
        
        # Detect navigation issues
        loop_detected = self._detect_button_loop()
        visual_stuck = self._detect_visual_stuck()
        
        # Generate navigation analysis
        analysis = {
            "turn_number": turn_number,
            "progress_made": progress_made,
            "visual_similarity": visual_similarity,
            "loop_detected": loop_detected,
            "visual_stuck": visual_stuck,
            "stuck_mode": self.stuck_mode,
            "consecutive_similar_actions": self._count_consecutive_actions(),
            "consecutive_similar_screenshots": self.consecutive_similar_screenshots,
            "needs_intervention": loop_detected or visual_stuck or self.stuck_mode,
            "suggested_recovery": self._suggest_recovery_strategy(),
            "recent_action_pattern": self._analyze_action_pattern(),
            "navigation_confidence": self._calculate_navigation_confidence()
        }
        
        return analysis
    
    def _calculate_screenshot_hash(self, screenshot_path: str) -> str:
        """Calculate hash of screenshot for exact comparison"""
        try:
            with open(screenshot_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return "error"
    
    def _calculate_visual_similarity(self, screenshot_path: str) -> float:
        """
        Calculate visual similarity between current and previous screenshot
        
        Returns:
            Similarity score (0.0 = completely different, 1.0 = identical)
        """
        if len(self.turn_history) == 0:
            return 0.0
            
        try:
            # Load current and previous screenshots
            current_img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
            if current_img is None:
                return 0.0
                
            last_turn = self.turn_history[-1]
            previous_img = cv2.imread(last_turn.screenshot_path, cv2.IMREAD_GRAYSCALE)
            if previous_img is None:
                return 0.0
            
            # Resize to standard size for comparison
            height, width = 240, 160  # GBA resolution
            current_img = cv2.resize(current_img, (width, height))
            previous_img = cv2.resize(previous_img, (width, height))
            
            # Calculate structural similarity
            from skimage.metrics import structural_similarity as ssim
            similarity = ssim(current_img, previous_img)
            
            return float(similarity)
            
        except Exception as e:
            # Fallback to simple pixel difference if SSIM fails
            try:
                current_img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
                previous_img = cv2.imread(last_turn.screenshot_path, cv2.IMREAD_GRAYSCALE)
                
                if current_img is not None and previous_img is not None:
                    current_img = cv2.resize(current_img, (160, 120))
                    previous_img = cv2.resize(previous_img, (160, 120))
                    
                    # Simple pixel difference
                    diff = np.abs(current_img.astype(np.float32) - previous_img.astype(np.float32))
                    mean_diff = np.mean(diff) / 255.0
                    similarity = 1.0 - mean_diff
                    
                    return max(0.0, min(1.0, similarity))
            except Exception:
                pass
            
            return 0.0
    
    def _update_tracking_state(self, turn_data: TurnData):
        """Update internal tracking state based on new turn data"""
        # Update consecutive similar screenshots counter
        if turn_data.visual_similarity >= self.similarity_threshold:
            self.consecutive_similar_screenshots += 1
        else:
            self.consecutive_similar_screenshots = 0
        
        # Update last screenshot hash
        self.last_screenshot_hash = turn_data.screenshot_hash
    
    def _detect_button_loop(self) -> bool:
        """Detect if AI is stuck in a button press loop"""
        if len(self.recent_actions) < 3:
            return False
        
        # Check for consecutive identical actions
        last_action = self.recent_actions[-1]
        consecutive_count = 1
        
        for i in range(len(self.recent_actions) - 2, -1, -1):
            if self.recent_actions[i] == last_action:
                consecutive_count += 1
            else:
                break
        
        return consecutive_count >= self.stuck_threshold
    
    def _detect_visual_stuck(self) -> bool:
        """Detect if AI is visually stuck (no progress despite actions)"""
        return self.consecutive_similar_screenshots >= 3
    
    def _count_consecutive_actions(self) -> int:
        """Count consecutive identical actions"""
        if len(self.recent_actions) == 0:
            return 0
        
        last_action = self.recent_actions[-1]
        count = 1
        
        for i in range(len(self.recent_actions) - 2, -1, -1):
            if self.recent_actions[i] == last_action:
                count += 1
            else:
                break
                
        return count
    
    def _suggest_recovery_strategy(self) -> Dict[str, Any]:
        """Suggest recovery strategy when stuck"""
        if not (self.stuck_mode or self._detect_button_loop() or self._detect_visual_stuck()):
            return {"type": "continue", "description": "No intervention needed"}
        
        # Analyze the problem
        consecutive_actions = self._count_consecutive_actions()
        last_action = self.recent_actions[-1] if self.recent_actions else []
        
        strategies = []
        
        # Strategy 1: Try perpendicular directions
        if last_action and len(last_action) == 1:
            button = last_action[0].lower()
            if button in ['up', 'down']:
                strategies.append({
                    "type": "perpendicular_movement",
                    "actions": ["left", "right"],
                    "description": f"Try horizontal movement instead of {button}"
                })
            elif button in ['left', 'right']:
                strategies.append({
                    "type": "perpendicular_movement", 
                    "actions": ["up", "down"],
                    "description": f"Try vertical movement instead of {button}"
                })
        
        # Strategy 2: Try interaction
        if consecutive_actions >= 3:
            strategies.append({
                "type": "interaction",
                "actions": ["a"],
                "description": "Try interacting with environment (A button)"
            })
        
        # Strategy 3: Retreat and approach differently
        if consecutive_actions >= 5:
            strategies.append({
                "type": "retreat_and_approach",
                "actions": ["down", "down", "left", "up", "up"],
                "description": "Back away and try different approach"
            })
        
        # Strategy 4: Systematic exploration
        if consecutive_actions >= 7:
            strategies.append({
                "type": "systematic_exploration",
                "actions": ["left", "down", "right", "up"],
                "description": "Try all four directions systematically"
            })
        
        return {
            "type": "recovery_needed",
            "problem": f"Stuck with {consecutive_actions} consecutive {last_action} actions",
            "strategies": strategies,
            "recommended_strategy": strategies[0] if strategies else None
        }
    
    def _analyze_action_pattern(self) -> Dict[str, Any]:
        """Analyze recent action patterns"""
        if len(self.recent_actions) < 3:
            return {"type": "insufficient_data"}
        
        # Flatten actions to analyze button patterns
        all_buttons = []
        for action_list in self.recent_actions:
            all_buttons.extend(action_list)
        
        # Count button frequencies
        button_counts = {}
        for button in all_buttons:
            button_counts[button] = button_counts.get(button, 0) + 1
        
        # Find most common button
        most_common = max(button_counts.items(), key=lambda x: x[1]) if button_counts else ("none", 0)
        
        # Analyze patterns
        pattern_analysis = {
            "total_actions": len(self.recent_actions),
            "total_buttons": len(all_buttons),
            "button_frequencies": button_counts,
            "most_common_button": most_common[0],
            "most_common_count": most_common[1],
            "diversity_score": len(button_counts) / max(1, len(all_buttons)),
            "repetition_ratio": most_common[1] / max(1, len(all_buttons))
        }
        
        return pattern_analysis
    
    def _calculate_navigation_confidence(self) -> float:
        """Calculate confidence score for navigation decisions"""
        if len(self.turn_history) < 3:
            return 0.5
        
        # Factors that increase confidence
        recent_progress = sum(1 for turn in list(self.turn_history)[-5:] if turn.progress_made)
        action_diversity = self._analyze_action_pattern().get("diversity_score", 0)
        
        # Factors that decrease confidence
        consecutive_stuck = self.consecutive_similar_screenshots
        loop_detected = self._detect_button_loop()
        
        # Calculate confidence (0.0 to 1.0)
        confidence = 0.5  # Base confidence
        confidence += (recent_progress / 5) * 0.3  # Progress boost
        confidence += action_diversity * 0.2  # Diversity boost
        confidence -= (consecutive_stuck / 10) * 0.3  # Stuck penalty
        confidence -= 0.4 if loop_detected else 0  # Loop penalty
        
        return max(0.0, min(1.0, confidence))
    
    def trigger_stuck_mode(self):
        """Manually trigger stuck mode"""
        self.stuck_mode = True
        self.last_stuck_trigger = time.time()
    
    def reset_stuck_mode(self):
        """Reset stuck mode"""
        self.stuck_mode = False
        self.stuck_counter = 0
        self.consecutive_similar_screenshots = 0
    
    def generate_critique(self) -> Dict[str, Any]:
        """Generate a critique of the last 20 turns for strategy adjustment"""
        if len(self.turn_history) < 5:
            return {"status": "insufficient_data"}
        
        turns = list(self.turn_history)
        
        # Analyze progress over time
        progress_made_count = sum(1 for turn in turns if turn.progress_made)
        total_turns = len(turns)
        progress_ratio = progress_made_count / total_turns
        
        # Analyze action patterns
        all_actions = []
        for turn in turns:
            all_actions.extend(turn.buttons_pressed)
        
        action_counts = {}
        for action in all_actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Identify problem areas
        problems = []
        
        if progress_ratio < 0.3:
            problems.append("Low progress rate - many turns without visual changes")
        
        if len(action_counts) <= 2:
            problems.append("Very limited action diversity - may be stuck in pattern")
        
        most_common_action = max(action_counts.items(), key=lambda x: x[1]) if action_counts else ("none", 0)
        if most_common_action[1] > total_turns * 0.7:
            problems.append(f"Excessive repetition of '{most_common_action[0]}' button")
        
        # Generate recommendations
        recommendations = []
        
        if progress_ratio < 0.5:
            recommendations.append("Try more diverse movement patterns")
            recommendations.append("Consider interaction (A button) at suspected boundaries")
        
        if self._detect_button_loop():
            recommendations.append("Switch to perpendicular movement directions")
            recommendations.append("Try retreat and approach from different angle")
        
        critique = {
            "analysis_period": f"Last {total_turns} turns",
            "progress_ratio": progress_ratio,
            "action_diversity": len(action_counts),
            "most_common_action": most_common_action,
            "problems_identified": problems,
            "recommendations": recommendations,
            "overall_assessment": self._generate_overall_assessment(progress_ratio, problems),
            "suggested_prompt_changes": self._suggest_prompt_changes(problems)
        }
        
        return critique
    
    def _generate_overall_assessment(self, progress_ratio: float, problems: List[str]) -> str:
        """Generate overall assessment of navigation performance"""
        if progress_ratio > 0.7 and len(problems) == 0:
            return "Excellent navigation - making consistent progress"
        elif progress_ratio > 0.5 and len(problems) <= 1:
            return "Good navigation with minor issues"
        elif progress_ratio > 0.3:
            return "Moderate navigation - some stuck patterns detected"
        else:
            return "Poor navigation - significant intervention needed"
    
    def _suggest_prompt_changes(self, problems: List[str]) -> List[str]:
        """Suggest prompt template changes based on identified problems"""
        suggestions = []
        
        if any("Low progress" in problem for problem in problems):
            suggestions.append("Switch to exploration-focused prompts")
            suggestions.append("Add more emphasis on environmental interaction")
        
        if any("repetition" in problem.lower() for problem in problems):
            suggestions.append("Use stuck-detection prompts with alternative strategies")
            suggestions.append("Emphasize trying different directions when stuck")
        
        if any("limited action diversity" in problem for problem in problems):
            suggestions.append("Encourage more varied button combinations")
            suggestions.append("Add systematic exploration patterns to prompts")
        
        return suggestions