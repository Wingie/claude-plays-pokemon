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
from prompt_template_updater import PromptTemplateUpdater, TemplateChange

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
        
        # Initialize template updater
        self.template_updater = PromptTemplateUpdater(self.prompts_dir, self.runs_dir)
    
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
        """Suggest navigation prompt improvements based on actual performance issues"""
        current_template = self.prompt_templates.get("exploration_strategy", {}).get("template", "")
        suggestions = []
        
        # Focus on the specific navigation problems observed
        if metrics.navigation_efficiency < 0.3:
            suggestions.append("Critical stuck recovery: Immediate alternative when blocked 3+ times")
            
        if metrics.stuck_patterns > 0:
            suggestions.append("Pattern detection: Recognize and break repetitive movement cycles")
            
        if metrics.items_collected == 0:
            suggestions.append("Item accessibility: Some visible items require HM moves (Cut, Surf) - skip inaccessible ones")
            suggestions.append("Path recognition: If blocked by trees/water repeatedly, try different areas")
            suggestions.append("Item prioritization: Focus on items that are actually reachable without special abilities")
            
        # If efficiency is moderate, suggest refinements
        if 0.3 <= metrics.navigation_efficiency < 0.7:
            suggestions.append("Path optimization: Choose most direct routes to visible objectives")
            suggestions.append("Boundary detection: Recognize walls and obstacles more quickly")
        
        # If template already has good content but performance is poor, suggest debugging
        if len(suggestions) == 0 and metrics.navigation_efficiency < 0.8:
            suggestions.append("Enhanced debugging: More detailed reasoning about movement choices")
            suggestions.append("Context awareness: Better interpretation of visual game elements")
        
        return "\n".join(f"- {suggestion}" for suggestion in suggestions)
    
    def _suggest_battle_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest battle prompt improvements based on actual performance"""
        current_template = self.prompt_templates.get("battle_analysis", {}).get("template", "")
        suggestions = []
        
        # Only suggest improvements that aren't already present
        if "TYPE EFFECTIVENESS" not in current_template:
            suggestions.append("Type effectiveness emphasis: Always check type advantages before selecting moves")
        
        if metrics.battles_lost > 0 and "HP" not in current_template:
            suggestions.append("HP management: Monitor Pokemon health and switch when necessary")
            
        if "PHASE" not in current_template:
            suggestions.append("Battle phase detection: Better identification of battle menu vs move selection")
            
        # If template already has good content, suggest advanced improvements
        if len(suggestions) == 0:
            suggestions.append("Advanced battle AI: Predict opponent moves and counter-strategies")
            suggestions.append("Battle efficiency: Faster menu navigation and move selection")
        
        return "\n".join(f"- {suggestion}" for suggestion in suggestions)
    
    def _suggest_goal_oriented_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest goal-oriented prompt improvements based on actual progress"""
        current_template = self.prompt_templates.get("task_analysis", {}).get("template", "")
        suggestions = []
        
        # Only suggest improvements that aren't already present
        if "OBJECTIVE FOCUS" not in current_template:
            suggestions.append("OKR integration: Always consider current objectives when making decisions")
            suggestions.append("Priority system: Gym badges > Team building > Exploration > Item collection")
        
        # Analyze specific goal deficiencies
        if metrics.progress_toward_okrs.get("gym_badges", 0) == 0:
            if "gym" not in current_template.lower():
                suggestions.append("Gym focus: Prioritize finding and challenging gym leaders")
                
        if metrics.items_collected == 0 and "item" not in current_template.lower():
            suggestions.append("Item collection: Notice and collect visible items like Pokeballs")
            
        if metrics.new_areas_discovered < 2:
            suggestions.append("Exploration strategy: Systematic area discovery and mapping")
        
        # If template already has good content, suggest advanced improvements
        if len(suggestions) == 0:
            suggestions.append("Advanced goal tracking: Sub-objective decomposition and milestone planning")
            suggestions.append("Efficiency optimization: Shortest path planning to objectives")
        
        return "\n".join(f"- {suggestion}" for suggestion in suggestions)
    
    def _suggest_stuck_recovery_improvements(self, metrics: EpisodeMetrics) -> str:
        """Suggest stuck recovery improvements based on actual stuck patterns"""
        current_template = self.prompt_templates.get("stuck_recovery", {}).get("template", "")
        suggestions = []
        
        # Analyze specific stuck patterns
        if metrics.stuck_patterns > 20:
            suggestions.append("Emergency recovery: Immediate direction change after 2 identical actions")
            suggestions.append("Pattern breaking: Systematic exploration when stuck (try all 4 directions)")
            
        if metrics.stuck_patterns > 10:
            suggestions.append("Interaction testing: Press A/B buttons when movement fails")
            suggestions.append("Context switching: Change goals when repeatedly blocked")
            
        if metrics.navigation_efficiency < 0.3:
            suggestions.append("Visual analysis: Better recognition of blocked vs open paths")
            suggestions.append("Accessibility awareness: Skip areas requiring special abilities")
        
        # If template already has good content, suggest advanced improvements
        if len(suggestions) == 0:
            suggestions.append("Advanced recovery: Multi-step unstuck sequences")
            suggestions.append("Learning integration: Remember successful recovery strategies")
        
        return "\n".join(f"- {suggestion}" for suggestion in suggestions)
    
    def update_yaml_templates(self, session_dir: Path, apply_changes: bool = True) -> Dict[str, Any]:
        """
        Apply episode review improvements to actual YAML template files
        
        Args:
            session_dir: Directory containing the session data to analyze
            apply_changes: Whether to actually apply changes or just return what would be changed
            
        Returns:
            Dictionary with update results and change information
        """
        try:
            # Analyze the episode first
            metrics = self.analyze_episode(session_dir)
            improvements = self.suggest_prompt_improvements(metrics)
            
            if not improvements:
                return {
                    "success": True,
                    "changes_applied": 0,
                    "message": "No improvements needed - excellent performance!",
                    "metrics": {
                        "navigation_efficiency": metrics.navigation_efficiency,
                        "battle_win_rate": metrics.battles_won / max(1, metrics.battles_won + metrics.battles_lost),
                        "stuck_patterns": metrics.stuck_patterns
                    }
                }
            
            # Prepare performance metrics for tracking
            performance_metrics = {
                "navigation_efficiency": metrics.navigation_efficiency,
                "battle_win_rate": metrics.battles_won / max(1, metrics.battles_won + metrics.battles_lost),
                "stuck_patterns": metrics.stuck_patterns,
                "turns_completed": metrics.turns_completed,
                "areas_discovered": metrics.new_areas_discovered
            }
            
            changes_applied = []
            session_info = f"Episode {session_dir.name} - {metrics.turns_completed} turns"
            
            if apply_changes:
                print(f"🔧 APPLYING {len(improvements)} PROMPT IMPROVEMENTS...")
                
                # Apply each improvement
                for improvement in improvements:
                    print(f"📝 Updating {improvement.prompt_name} - {improvement.reasoning}")
                    
                    change = self.template_updater.apply_improvement_suggestion(
                        improvement, performance_metrics
                    )
                    
                    if change:
                        changes_applied.append(change)
                        print(f"   ✅ {improvement.prompt_name} v{change.old_version} → v{change.new_version}")
                    else:
                        print(f"   ❌ Failed to apply changes to {improvement.prompt_name}")
                
                # Commit changes to git if any were successfully applied
                if changes_applied:
                    git_success = self.template_updater.commit_changes_to_git(changes_applied, session_info)
                    if git_success:
                        print(f"📦 Committed {len(changes_applied)} template changes to git")
                    else:
                        print(f"⚠️ Template changes applied but git commit failed")
                
                return {
                    "success": True,
                    "changes_applied": len(changes_applied),
                    "changes": [
                        {
                            "template": change.template_name,
                            "version": f"{change.old_version} → {change.new_version}",
                            "reasoning": change.reasoning
                        }
                        for change in changes_applied
                    ],
                    "git_committed": git_success if changes_applied else False,
                    "message": f"Applied {len(changes_applied)} improvements based on episode analysis",
                    "metrics": performance_metrics
                }
            else:
                # Dry run mode - just return what would be changed
                return {
                    "success": True,
                    "changes_applied": 0,
                    "dry_run": True,
                    "potential_changes": [
                        {
                            "template": improvement.prompt_name,
                            "priority": improvement.priority,
                            "reasoning": improvement.reasoning,
                            "suggested_changes": improvement.suggested_changes
                        }
                        for improvement in improvements
                    ],
                    "message": f"Would apply {len(improvements)} improvements (dry run mode)",
                    "metrics": performance_metrics
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "changes_applied": 0,
                "message": f"Failed to update templates: {e}"
            }
    
    def rollback_last_template_changes(self) -> Dict[str, Any]:
        """
        Rollback the last template changes if performance decreased
        
        Returns:
            Dictionary with rollback results
        """
        try:
            success = self.template_updater.rollback_last_change()
            
            if success:
                return {
                    "success": True,
                    "message": "Successfully rolled back last template changes",
                    "action": "rollback_completed"
                }
            else:
                return {
                    "success": False,
                    "message": "Rollback failed - check git history manually",
                    "action": "rollback_failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Rollback error: {e}",
                "action": "rollback_error"
            }
    
    def get_template_change_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent template change history for analysis
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of recent template changes
        """
        try:
            return self.template_updater.get_change_history(limit)
        except Exception as e:
            print(f"⚠️ Failed to get change history: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    reviewer = EpisodeReviewer()
    
    # Find most recent session
    runs_dir = Path("runs")
    if runs_dir.exists():
        recent_sessions = sorted(runs_dir.glob("session_*"), key=lambda x: x.stat().st_mtime, reverse=True)
        # Filter to only directories with session_data.json
        valid_sessions = [s for s in recent_sessions if s.is_dir() and (s / "session_data.json").exists()]
        if valid_sessions:
            latest_session = valid_sessions[0]
            print(f"Analyzing session: {latest_session.name}")
            
            try:
                report = reviewer.generate_episode_report(latest_session)
                print(report)
            except Exception as e:
                print(f"Error analyzing session: {e}")
        else:
            print("No valid session directories found in runs directory")
            print("Looking for directories matching 'session_*' with session_data.json")
    else:
        print("Runs directory not found")