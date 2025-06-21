"""
PromptTemplateUpdater - Smart YAML Template Modification System
Handles automatic prompt template updates based on episode review suggestions
"""

import yaml
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TemplateChange:
    """Represents a change made to a template"""
    template_name: str
    old_version: str
    new_version: str
    old_content: str
    new_content: str
    reasoning: str
    timestamp: str
    performance_before: Dict[str, float]
    performance_after: Optional[Dict[str, float]] = None

class PromptTemplateUpdater:
    """Handles smart updates to YAML prompt templates with version control"""
    
    def __init__(self, prompts_dir: Path, runs_dir: Path):
        """
        Initialize the template updater
        
        Args:
            prompts_dir: Directory containing prompt templates
            runs_dir: Directory for logging changes
        """
        self.prompts_dir = prompts_dir
        self.runs_dir = runs_dir
        self.base_prompts_file = prompts_dir / "base" / "base_prompts.yaml"
        self.changes_log_dir = runs_dir / "prompt_changes"
        self.changes_log_dir.mkdir(exist_ok=True)
        
        # Load current templates
        self.current_templates = self._load_yaml_templates()
        
    def _load_yaml_templates(self) -> Dict[str, Any]:
        """Load current YAML templates"""
        if self.base_prompts_file.exists():
            with open(self.base_prompts_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _save_yaml_templates(self, templates: Dict[str, Any]) -> bool:
        """Save templates back to YAML file"""
        try:
            # Create backup first
            backup_file = self.base_prompts_file.with_suffix('.yaml.backup')
            if self.base_prompts_file.exists():
                import shutil
                shutil.copy2(self.base_prompts_file, backup_file)
            
            # Save new templates
            with open(self.base_prompts_file, 'w') as f:
                yaml.dump(templates, f, default_flow_style=False, indent=2, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"❌ Failed to save YAML templates: {e}")
            return False
    
    def apply_improvement_suggestion(self, improvement, performance_metrics: Dict[str, float]) -> Optional[TemplateChange]:
        """
        Apply a specific improvement suggestion to a template
        
        Args:
            improvement: PromptImprovement object from episode reviewer
            performance_metrics: Current performance metrics before change
            
        Returns:
            TemplateChange object if successful, None if failed
        """
        template_name = improvement.prompt_name
        
        if template_name not in self.current_templates:
            print(f"⚠️ Template '{template_name}' not found in current templates")
            return None
        
        template = self.current_templates[template_name]
        old_content = template.get("template", "")
        old_version = template.get("version", "1.0")
        
        # Apply the suggested changes
        new_content = self._apply_suggested_changes(old_content, improvement.suggested_changes)
        new_version = self._increment_version(old_version)
        
        if new_content == old_content:
            print(f"⚠️ No changes applied to template '{template_name}'")
            return None
        
        # Create change record
        change = TemplateChange(
            template_name=template_name,
            old_version=old_version,
            new_version=new_version,
            old_content=old_content,
            new_content=new_content,
            reasoning=improvement.reasoning,
            timestamp=datetime.now().isoformat(),
            performance_before=performance_metrics.copy()
        )
        
        # Apply the change
        self.current_templates[template_name]["template"] = new_content
        self.current_templates[template_name]["version"] = new_version
        
        # Save templates
        if self._save_yaml_templates(self.current_templates):
            # Log the change
            self._log_template_change(change)
            print(f"✅ Updated template '{template_name}' to version {new_version}")
            return change
        else:
            print(f"❌ Failed to save template changes for '{template_name}'")
            return None
    
    def _apply_suggested_changes(self, template_content: str, suggested_changes: str) -> str:
        """
        Apply suggested changes to template content using intelligent text processing
        
        Args:
            template_content: Original template content
            suggested_changes: Suggested modifications from episode reviewer
            
        Returns:
            Modified template content
        """
        new_content = template_content
        
        # Parse the suggested changes to identify specific modifications
        changes = self._parse_suggested_changes(suggested_changes)
        
        for change in changes:
            if change["type"] == "add_section":
                new_content = self._add_section(new_content, change["content"], change.get("position", "end"))
            elif change["type"] == "replace_text":
                new_content = self._replace_text(new_content, change["find"], change["replace"])
            elif change["type"] == "add_rule":
                new_content = self._add_rule(new_content, change["content"])
            elif change["type"] == "enhance_detection":
                new_content = self._enhance_detection(new_content, change["content"])
        
        return new_content
    
    def _parse_suggested_changes(self, suggested_changes: str) -> List[Dict[str, Any]]:
        """
        Parse suggested changes text into structured modifications
        
        Args:
            suggested_changes: Text description of changes
            
        Returns:
            List of structured change objects
        """
        changes = []
        lines = suggested_changes.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('-'):
                continue
                
            # Remove the "- " prefix
            suggestion = line[2:].strip()
            
            # Parse specific improvement suggestions
            if "Critical stuck recovery" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- CRITICAL: If blocked 3+ times, immediately try opposite or perpendicular direction"
                })
            
            elif "Pattern detection" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- PATTERN DETECTION: Break repetitive cycles by trying completely different approach"
                })
            
            elif "Item interaction" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- ITEM COLLECTION: Press 'A' button when near visible items (Pokeballs, etc.)"
                })
                
            elif "Visual awareness" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- VISUAL FOCUS: Actively look for and move toward items visible on screen"
                })
            
            elif "Type effectiveness emphasis" in suggestion:
                changes.append({
                    "type": "add_section",
                    "content": "\n**TYPE EFFECTIVENESS PRIORITY**:\n- Always check type advantages before selecting moves\n- Super Effective (2x damage) > Neutral (1x) > Not Very Effective (0.5x)",
                    "position": "after_task"
                })
                
            elif "HP management" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- HP MONITORING: Switch Pokemon or use healing items when HP below 30%"
                })
            
            elif "OKR integration" in suggestion:
                changes.append({
                    "type": "add_section",
                    "content": "\n**OBJECTIVE FOCUS**:\n- Always consider current objectives when making decisions\n- Priority: Gym badges > Team building > Exploration > Item collection",
                    "position": "end"
                })
                
            elif "Item accessibility" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- ACCESSIBILITY: Some items require HM moves (Cut/Surf) - skip blocked items early game"
                })
                
            elif "Path recognition" in suggestion:
                changes.append({
                    "type": "add_rule", 
                    "content": "- PATH BLOCKING: If repeatedly blocked by trees/water, explore different accessible areas"
                })
                
            elif "Item prioritization" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- REACHABILITY: Focus on items accessible without special abilities (no Cut/Surf needed)"
                })
                
            elif "Emergency recovery" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- EMERGENCY: Change direction immediately after 2 identical actions"
                })
                
            elif "Pattern breaking" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- PATTERN_BREAK: Try all 4 directions systematically when stuck"
                })
                
            elif "Interaction testing" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- INTERACTION: Press A/B buttons when movement repeatedly fails"
                })
                
            elif "Accessibility awareness" in suggestion:
                changes.append({
                    "type": "add_rule",
                    "content": "- ACCESSIBILITY: Skip areas requiring special abilities when early game"
                })
        
        return changes
    
    def _add_section(self, content: str, new_section: str, position: str = "end") -> str:
        """Add a new section to the template content, avoiding duplicates"""
        # Check if similar content already exists to avoid duplicates
        section_key = new_section.strip().split('\n')[0]  # Use first line as key
        if section_key in content:
            print(f"⚠️ Section already exists, skipping: {section_key}")
            return content
            
        if position == "start":
            return new_section + "\n\n" + content
        elif position == "after_task":
            # Add after the task context line
            if "Task Context:" in content or "Current Task:" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "Task Context:" in line or "Current Task:" in line:
                        lines.insert(i + 1, new_section)
                        break
                return '\n'.join(lines)
            else:
                return content + "\n" + new_section
        else:  # position == "end"
            return content + "\n" + new_section
    
    def _replace_text(self, content: str, find_text: str, replace_text: str) -> str:
        """Replace specific text in the content"""
        return content.replace(find_text, replace_text)
    
    def _add_rule(self, content: str, rule: str) -> str:
        """Add a rule to an existing rules section or create one"""
        # Look for existing rules sections
        if "RULES:" in content or "CRITICAL RULES:" in content:
            lines = content.split('\n')
            # Find the last rule line and add after it
            last_rule_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('- ') and any(keyword in line.lower() for keyword in ['rule', 'never', 'always', 'critical']):
                    last_rule_idx = i
            
            if last_rule_idx >= 0:
                lines.insert(last_rule_idx + 1, rule)
                return '\n'.join(lines)
        
        # No existing rules section, add at end
        return content + f"\n\n**CRITICAL RULES**:\n{rule}"
    
    def _enhance_detection(self, content: str, enhancement: str) -> str:
        """Enhance detection capabilities in the template"""
        # Add to observation or analysis section
        if "OBSERVE" in content or "OBSERVATION" in content:
            enhanced_content = content.replace(
                "OBSERVE", 
                f"OBSERVE {enhancement}"
            )
            return enhanced_content
        else:
            return self._add_section(content, f"\n**ENHANCED DETECTION**: {enhancement}", "after_task")
    
    def _increment_version(self, version: str) -> str:
        """Increment version number (e.g., '1.0' -> '1.1')"""
        try:
            parts = version.split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                return f"{major}.{minor + 1}"
            else:
                return f"{version}.1"
        except:
            return f"{version}.updated"
    
    def _log_template_change(self, change: TemplateChange):
        """Log a template change to the runs directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        change_file = self.changes_log_dir / f"change_{timestamp}_{change.template_name}.json"
        
        # Create detailed change log
        log_data = {
            "template_name": change.template_name,
            "old_version": change.old_version,
            "new_version": change.new_version,
            "reasoning": change.reasoning,
            "timestamp": change.timestamp,
            "performance_before": change.performance_before,
            "diff": self._create_diff(change.old_content, change.new_content)
        }
        
        with open(change_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Also create a human-readable diff file
        diff_file = self.changes_log_dir / f"diff_{timestamp}_{change.template_name}.txt"
        with open(diff_file, 'w') as f:
            f.write(f"Template Change: {change.template_name}\n")
            f.write(f"Version: {change.old_version} → {change.new_version}\n")
            f.write(f"Timestamp: {change.timestamp}\n")
            f.write(f"Reasoning: {change.reasoning}\n")
            f.write(f"\n{'='*60}\n")
            f.write(f"DIFF:\n")
            f.write(f"{'='*60}\n")
            f.write(self._create_diff(change.old_content, change.new_content))
        
        print(f"📝 Change logged: {change_file}")
    
    def _create_diff(self, old_content: str, new_content: str) -> str:
        """Create a unified diff between old and new content"""
        import difflib
        
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines, 
            new_lines,
            fromfile="old_template",
            tofile="new_template",
            lineterm=""
        )
        
        return ''.join(diff)
    
    def commit_changes_to_git(self, changes: List[TemplateChange], session_info: str) -> bool:
        """
        Git commits disabled - user will commit manually
        """
        # Suppress unused parameter warnings
        _ = changes, session_info
        return False  # Always return False since git commits are disabled
    
    def rollback_last_change(self) -> bool:
        """
        Rollback the last template change using git
        
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Get the last commit that changed prompts
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "10", "--", str(self.base_prompts_file)],
                cwd=self.prompts_dir.parent,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                print("⚠️ No prompt changes found in git history")
                return False
            
            commits = result.stdout.strip().split('\n')
            if len(commits) < 2:
                print("⚠️ Not enough prompt history for rollback")
                return False
            
            # Get the commit hash before the last change
            previous_commit = commits[1].split()[0]
            
            # Reset the prompts file to the previous commit
            subprocess.run(
                ["git", "checkout", previous_commit, "--", str(self.base_prompts_file)],
                cwd=self.prompts_dir.parent,
                check=True
            )
            
            # Reload templates
            self.current_templates = self._load_yaml_templates()
            
            print(f"✅ Rolled back prompts to commit {previous_commit}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git rollback failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during rollback: {e}")
            return False
    
    def get_change_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of template changes
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of change records
        """
        changes = []
        
        # Get change log files
        log_files = sorted(self.changes_log_dir.glob("change_*.json"), 
                          key=lambda x: x.stat().st_mtime, reverse=True)
        
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r') as f:
                    change_data = json.load(f)
                    changes.append(change_data)
            except Exception as e:
                print(f"⚠️ Failed to read change log {log_file}: {e}")
        
        return changes