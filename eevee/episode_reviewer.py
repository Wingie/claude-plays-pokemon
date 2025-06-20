"""
Episode Reviewer - AI Pokemon Session Analysis & Prompt Optimization
Analyzes 100-turn episodes and suggests prompt improvements based on OKR progress
"""

import json
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class EpisodeMetrics:
    """Metrics extracted from a 100-turn episode"""
    turns_completed: int
    battles_won: int
    battles_lost: int
    items_collected: int
    new_areas_discovered: int
    stuck_patterns: int
    navigation_efficiency: float
    progress_toward_okrs: Dict[str, float]
    major_achievements: List[str]
    failure_modes: List[str]

@dataclass
class PromptImprovement:
    """Suggested improvement to a prompt template"""
    prompt_name: str
    current_version: str
    suggested_changes: str
    reasoning: str
    priority: str  # high, medium, low
    expected_impact: str

class EpisodeReviewer:
    """Analyzes completed Pokemon episodes and suggests prompt optimizations"""
    
    def __init__(self, eevee_dir: Path = None):
        """Initialize the episode reviewer"""
        if eevee_dir is None:
            eevee_dir = Path(__file__).parent
        
        self.eevee_dir = eevee_dir
        self.runs_dir = eevee_dir / "runs"
        self.prompts_dir = eevee_dir / "prompts"
        self.okr_file = self.prompts_dir / "OKR.md"
        
        # Load current prompt templates
        self.prompt_templates = self._load_prompt_templates()
        self.current_okrs = self._load_current_okrs()
    
    def analyze_episode(self, session_dir: Path) -> EpisodeMetrics:
        """Analyze a completed 100-turn episode"""
        session_data_file = session_dir / "session_data.json"
        
        if not session_data_file.exists():
            raise FileNotFoundError(f"Session data not found: {session_data_file}")
        
        with open(session_data_file, 'r') as f:
            session_data = json.load(f)
        
        # Extract metrics from session data
        metrics = EpisodeMetrics(
            turns_completed=len(session_data.get('turns', [])),
            battles_won=self._count_battles_won(session_data),
            battles_lost=self._count_battles_lost(session_data),
            items_collected=self._count_items_collected(session_data),
            new_areas_discovered=self._count_new_areas(session_data),
            stuck_patterns=self._count_stuck_patterns(session_data),
            navigation_efficiency=self._calculate_navigation_efficiency(session_data),
            progress_toward_okrs=self._assess_okr_progress(session_data),
            major_achievements=self._identify_achievements(session_data),
            failure_modes=self._identify_failure_modes(session_data)
        )
        
        return metrics
    
    def suggest_prompt_improvements(self, metrics: EpisodeMetrics) -> List[PromptImprovement]:
        """Generate prompt improvement suggestions based on episode analysis"""
        improvements = []
        
        # Analyze navigation efficiency
        if metrics.navigation_efficiency < 0.5:
            improvements.append(PromptImprovement(
                prompt_name="exploration_strategy",
                current_version=self.prompt_templates.get("exploration_strategy", {}).get("version", "1.0"),
                suggested_changes=self._suggest_navigation_improvements(metrics),
                reasoning=f"Navigation efficiency is {metrics.navigation_efficiency:.2f}, indicating frequent stuck patterns and inefficient movement",
                priority="high",
                expected_impact="Reduce stuck patterns by 30-50%, improve area exploration speed"
            ))
        
        # Analyze battle performance
        battle_win_rate = metrics.battles_won / max(1, metrics.battles_won + metrics.battles_lost)
        if battle_win_rate < 0.8:
            improvements.append(PromptImprovement(
                prompt_name="battle_analysis",
                current_version=self.prompt_templates.get("battle_analysis", {}).get("version", "1.0"),
                suggested_changes=self._suggest_battle_improvements(metrics),
                reasoning=f"Battle win rate is {battle_win_rate:.2f}, below optimal threshold of 0.8",
                priority="medium",
                expected_impact="Improve battle win rate by 15-25%"
            ))
        
        # Analyze OKR progress
        if metrics.progress_toward_okrs.get("gym_badges", 0) < 0.1:
            improvements.append(PromptImprovement(
                prompt_name="task_analysis",
                current_version=self.prompt_templates.get("task_analysis", {}).get("version", "1.0"),
                suggested_changes=self._suggest_goal_oriented_improvements(metrics),
                reasoning="No progress toward gym badges detected, need better goal-oriented behavior",
                priority="high",
                expected_impact="Increase focus on primary objectives, reduce aimless exploration"
            ))
        
        # Analyze stuck patterns
        if metrics.stuck_patterns > 20:
            improvements.append(PromptImprovement(
                prompt_name="stuck_recovery",
                current_version=self.prompt_templates.get("stuck_recovery", {}).get("version", "1.0"),
                suggested_changes=self._suggest_stuck_recovery_improvements(metrics),
                reasoning=f"Detected {metrics.stuck_patterns} stuck patterns, indicating recovery system needs enhancement",
                priority="high",
                expected_impact="Reduce stuck patterns by 60-80%"
            ))
        
        return improvements
    
    def generate_episode_report(self, session_dir: Path) -> str:
        """Generate a comprehensive episode review report"""
        metrics = self.analyze_episode(session_dir)
        improvements = self.suggest_prompt_improvements(metrics)
        
        report = f"""
# Episode Review Report
**Session**: {session_dir.name}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Episode Performance Summary

### Core Metrics
- **Turns Completed**: {metrics.turns_completed}/100
- **Navigation Efficiency**: {metrics.navigation_efficiency:.2f}
- **Battles Won**: {metrics.battles_won}
- **Battles Lost**: {metrics.battles_lost}
- **Battle Win Rate**: {metrics.battles_won / max(1, metrics.battles_won + metrics.battles_lost):.2f}
- **Items Collected**: {metrics.items_collected}
- **New Areas Discovered**: {metrics.new_areas_discovered}
- **Stuck Patterns**: {metrics.stuck_patterns}

### OKR Progress Assessment
"""
        
        for okr_name, progress in metrics.progress_toward_okrs.items():
            report += f"- **{okr_name.replace('_', ' ').title()}**: {progress:.2f}/10\n"
        
        report += f"""
### Major Achievements
"""
        for achievement in metrics.major_achievements:
            report += f"- {achievement}\n"
        
        report += f"""
### Failure Modes Identified
"""
        for failure in metrics.failure_modes:
            report += f"- {failure}\n"
        
        report += f"""
## Prompt Improvement Recommendations

Found {len(improvements)} potential improvements:
"""
        
        for improvement in improvements:
            report += f"""
### {improvement.prompt_name} (Priority: {improvement.priority})

**Current Version**: {improvement.current_version}
**Issue**: {improvement.reasoning}
**Suggested Changes**:
{improvement.suggested_changes}
**Expected Impact**: {improvement.expected_impact}
"""
        
        return report
    
    def _load_prompt_templates(self) -> Dict[str, Any]:
        """Load current prompt templates"""
        templates = {}
        
        # Load base prompts
        base_prompts_file = self.prompts_dir / "base" / "base_prompts.yaml"
        if base_prompts_file.exists():
            with open(base_prompts_file, 'r') as f:
                templates.update(yaml.safe_load(f) or {})
        
        return templates
    
    def _load_current_okrs(self) -> Dict[str, Any]:
        """Load current OKR targets"""
        if not self.okr_file.exists():
            return {}
        
        with open(self.okr_file, 'r') as f:
            content = f.read()
        
        # Parse OKR scores from markdown
        okrs = {}
        for line in content.split('\n'):
            if 'Current Score:' in line:
                # Extract KR name and score
                match = re.search(r'\*\*(KR\d+)\*\*.*Current Score:\s*(\d+)/(\d+)', line)
                if match:
                    kr_name = match.group(1)
                    current_score = int(match.group(2))
                    target_score = int(match.group(3))
                    okrs[kr_name.lower()] = {"current": current_score, "target": target_score}
        
        return okrs
    
    def _count_battles_won(self, session_data: Dict) -> int:
        """Count battles won in the session"""
        battles_won = 0
        turns = session_data.get('turns', [])
        
        for turn in turns:
            ai_analysis = turn.get('ai_analysis', '').lower()
            if any(phrase in ai_analysis for phrase in ['gained exp', 'defeated', 'won battle', 'fainted']):
                battles_won += 1
        
        return battles_won
    
    def _count_battles_lost(self, session_data: Dict) -> int:
        """Count battles lost in the session"""
        battles_lost = 0
        turns = session_data.get('turns', [])
        
        for turn in turns:
            ai_analysis = turn.get('ai_analysis', '').lower()
            if any(phrase in ai_analysis for phrase in ['pokemon fainted', 'lost battle', 'whited out']):
                battles_lost += 1
        
        return battles_lost
    
    def _count_items_collected(self, session_data: Dict) -> int:
        """Count items collected in the session"""
        items_collected = 0
        turns = session_data.get('turns', [])
        
        for turn in turns:
            ai_analysis = turn.get('ai_analysis', '').lower()
            if any(phrase in ai_analysis for phrase in ['found item', 'picked up', 'obtained', 'received']):
                items_collected += 1
        
        return items_collected
    
    def _count_new_areas(self, session_data: Dict) -> int:
        """Count new areas discovered"""
        areas_mentioned = set()
        turns = session_data.get('turns', [])
        
        for turn in turns:
            ai_analysis = turn.get('ai_analysis', '').lower()
            # Look for area names
            for area in ['city', 'town', 'route', 'forest', 'cave', 'gym', 'center']:
                if area in ai_analysis:
                    areas_mentioned.add(area)
        
        return len(areas_mentioned)
    
    def _count_stuck_patterns(self, session_data: Dict) -> int:
        """Count stuck patterns in the session"""
        stuck_patterns = 0
        turns = session_data.get('turns', [])
        
        # Look for consecutive identical actions
        prev_action = None
        consecutive_count = 0
        
        for turn in turns:
            current_action = str(turn.get('button_presses', []))
            if current_action == prev_action and current_action != "[]":
                consecutive_count += 1
                if consecutive_count >= 3:  # 3+ identical actions = stuck pattern
                    stuck_patterns += 1
            else:
                consecutive_count = 0
            prev_action = current_action
        
        return stuck_patterns
    
    def _calculate_navigation_efficiency(self, session_data: Dict) -> float:
        """Calculate navigation efficiency score (0-1)"""
        turns = session_data.get('turns', [])
        if not turns:
            return 0.0
        
        # Calculate based on unique actions, area progression, and stuck patterns
        unique_actions = len(set(str(turn.get('button_presses', [])) for turn in turns))
        total_actions = len(turns)
        stuck_patterns = self._count_stuck_patterns(session_data)
        
        # Higher unique action ratio = better exploration
        action_diversity = unique_actions / max(1, total_actions)
        
        # Lower stuck patterns = better navigation
        stuck_penalty = max(0, 1 - (stuck_patterns / 50))  # Normalize to 0-1
        
        return (action_diversity + stuck_penalty) / 2
    
    def _assess_okr_progress(self, session_data: Dict) -> Dict[str, float]:
        """Assess progress toward OKRs"""
        progress = {
            "gym_badges": 0.0,
            "pokemon_team": 0.0,
            "resource_management": 0.0,
            "battle_performance": 0.0
        }
        
        turns = session_data.get('turns', [])
        
        for turn in turns:
            ai_analysis = turn.get('ai_analysis', '').lower()
            
            # Gym badge progress
            if any(phrase in ai_analysis for phrase in ['gym', 'badge', 'leader']):
                progress["gym_badges"] += 0.1
            
            # Pokemon team progress
            if any(phrase in ai_analysis for phrase in ['caught', 'pokemon', 'level']):
                progress["pokemon_team"] += 0.1
            
            # Resource management
            if any(phrase in ai_analysis for phrase in ['item', 'potion', 'pokeball']):
                progress["resource_management"] += 0.1
            
            # Battle performance
            if any(phrase in ai_analysis for phrase in ['battle', 'attack', 'move']):
                progress["battle_performance"] += 0.1
        
        # Normalize to 0-10 scale
        for key in progress:
            progress[key] = min(10.0, progress[key])
        
        return progress
    
    def _identify_achievements(self, session_data: Dict) -> List[str]:
        """Identify major achievements in the session"""
        achievements = []
        turns = session_data.get('turns', [])
        
        for turn in turns:
            ai_analysis = turn.get('ai_analysis', '').lower()
            
            if 'gym' in ai_analysis and 'badge' in ai_analysis:
                achievements.append("🏆 Gym battle progress detected")
            
            if 'caught' in ai_analysis:
                achievements.append("🎯 Pokemon capture detected")
            
            if 'evolved' in ai_analysis:
                achievements.append("⭐ Pokemon evolution detected")
            
            if 'new area' in ai_analysis or 'discovered' in ai_analysis:
                achievements.append("🗺️ New area exploration")
        
        return list(set(achievements))  # Remove duplicates
    
    def _identify_failure_modes(self, session_data: Dict) -> List[str]:
        """Identify failure modes and problems"""
        failures = []
        
        stuck_patterns = self._count_stuck_patterns(session_data)
        if stuck_patterns > 10:
            failures.append(f"🔄 Excessive stuck patterns ({stuck_patterns})")
        
        battles_lost = self._count_battles_lost(session_data)
        if battles_lost > 3:
            failures.append(f"⚔️ Multiple battle losses ({battles_lost})")
        
        turns = session_data.get('turns', [])
        if len(turns) < 100:
            failures.append(f"⏰ Session ended early ({len(turns)}/100 turns)")
        
        return failures
    
    def _suggest_navigation_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest navigation prompt improvements"""
        return f"""
**Enhanced Navigation Template**:
1. Add explicit stuck detection: "If I've used the same action 3+ times, try a completely different direction"
2. Include area memory: "Remember visited locations to avoid backtracking"
3. Add goal-oriented pathfinding: "Prioritize movement toward known objectives (gyms, Pokemon Centers)"
4. Implement exploration strategy: "Systematically explore new areas before revisiting known ones"

**Specific Changes**:
- Add "STUCK_DETECTION: If repeating actions, change strategy immediately"
- Include "PATH_MEMORY: Track visited areas to prevent loops"
- Add "OBJECTIVE_NAVIGATION: Move toward closest known goal when lost"
"""
    
    def _suggest_battle_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest battle prompt improvements"""
        return f"""
**Enhanced Battle Strategy**:
1. Type effectiveness emphasis: "Always consider type advantages before selecting moves"
2. HP management: "Switch Pokemon or use items when HP is below 30%"
3. Status effect awareness: "Prioritize healing status conditions that prevent action"
4. Move selection strategy: "Use strongest effective moves, save PP for important battles"

**Specific Changes**:
- Add type effectiveness chart reference
- Include HP threshold decision making
- Add status condition priority matrix
- Include move power and accuracy considerations
"""
    
    def _suggest_goal_oriented_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest goal-oriented prompt improvements"""
        return f"""
**Goal-Oriented Behavior Enhancement**:
1. OKR integration: "Always consider current objectives when making decisions"
2. Priority system: "Gym badges > Team building > Exploration > Item collection"
3. Progress tracking: "Acknowledge steps toward objectives in reasoning"
4. Milestone recognition: "Celebrate achieving sub-goals (reaching new areas, leveling up)"

**Specific Changes**:
- Add OKR reference in every prompt template
- Include priority decision matrix
- Add progress acknowledgment requirements
- Include milestone celebration triggers
"""
    
    def _suggest_stuck_recovery_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest stuck recovery improvements"""
        return f"""
**Advanced Stuck Recovery**:
1. Pattern detection: "If same action repeated 2+ times, immediately change strategy"
2. Escalation system: "Try opposite direction → Try menu → Try random exploration"
3. Context switching: "When stuck, completely change objectives temporarily"
4. Memory reset: "Clear recent action memory to avoid decision loops"

**Specific Changes**:
- Reduce stuck detection threshold from 3 to 2 repeated actions
- Add escalation ladder with specific recovery strategies
- Include "emergency exploration mode" for severe stuck situations
- Add memory clearing mechanisms for loop breaking
"""

# Example usage and testing
if __name__ == "__main__":
    reviewer = EpisodeReviewer()
    
    # Find most recent session
    runs_dir = Path("runs")
    if runs_dir.exists():
        recent_sessions = sorted(runs_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
        if recent_sessions:
            latest_session = recent_sessions[0]
            print(f"Analyzing session: {latest_session.name}")
            
            try:
                report = reviewer.generate_episode_report(latest_session)
                print(report)
            except Exception as e:
                print(f"Error analyzing session: {e}")
        else:
            print("No sessions found in runs directory")
    else:
        print("Runs directory not found")