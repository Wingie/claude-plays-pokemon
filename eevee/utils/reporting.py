"""
Reporting Utilities for Eevee
Handles output formatting, report generation, and data visualization for Pokemon AI tasks
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict

class ReportFormatter:
    """Formats Eevee execution results into various output formats"""
    
    def __init__(self):
        self.report_templates = {
            "task_execution": {
                "title": "🔮 Eevee Task Execution Report",
                "sections": ["summary", "analysis", "steps", "performance"]
            },
            "pokemon_analysis": {
                "title": "🎮 Pokemon Party Analysis Report", 
                "sections": ["party_overview", "individual_pokemon", "recommendations"]
            },
            "session_summary": {
                "title": "📊 Eevee Session Summary",
                "sections": ["session_info", "task_history", "performance_metrics"]
            }
        }
    
    def format_task_execution_report(
        self, 
        result: Dict[str, Any], 
        format_type: str = "text"
    ) -> str:
        """
        Format task execution result into a comprehensive report
        
        Args:
            result: Task execution result dictionary
            format_type: Output format ("text", "markdown", "json")
            
        Returns:
            Formatted report string
        """
        if format_type == "json":
            return self._format_json_report(result)
        elif format_type == "markdown":
            return self._format_markdown_task_report(result)
        else:
            return self._format_text_task_report(result)
    
    def format_pokemon_party_report(
        self, 
        pokemon_data: List[Any], 
        format_type: str = "text"
    ) -> str:
        """
        Format Pokemon party data into a detailed report
        
        Args:
            pokemon_data: List of Pokemon objects or dictionaries
            format_type: Output format ("text", "markdown", "json")
            
        Returns:
            Formatted Pokemon party report
        """
        if format_type == "json":
            return json.dumps(self._pokemon_to_dict_list(pokemon_data), indent=2)
        elif format_type == "markdown":
            return self._format_markdown_pokemon_report(pokemon_data)
        else:
            return self._format_text_pokemon_report(pokemon_data)
    
    def format_session_summary(
        self,
        session_data: Dict[str, Any],
        format_type: str = "text"
    ) -> str:
        """
        Format session summary data into a report
        
        Args:
            session_data: Session summary dictionary
            format_type: Output format ("text", "markdown", "json")
            
        Returns:
            Formatted session summary report
        """
        if format_type == "json":
            return json.dumps(session_data, indent=2)
        elif format_type == "markdown":
            return self._format_markdown_session_report(session_data)
        else:
            return self._format_text_session_report(session_data)
    
    def _format_text_task_report(self, result: Dict[str, Any]) -> str:
        """Format task execution result as text"""
        lines = []
        
        # Header
        lines.append("🔮 " + "="*60)
        lines.append("🔮 EEVEE TASK EXECUTION REPORT")
        lines.append("🔮 " + "="*60)
        
        # Summary section
        lines.append("\n📋 TASK SUMMARY")
        lines.append("-" * 30)
        lines.append(f"Task: {result.get('task', 'Unknown')}")
        
        status = result.get('status', 'unknown')
        status_emoji = self._get_status_emoji(status)
        lines.append(f"Status: {status_emoji} {status.upper()}")
        
        if 'execution_time' in result:
            lines.append(f"Execution Time: {result['execution_time']:.2f} seconds")
        
        if 'steps_executed' in result:
            total_steps = result.get('total_steps', result['steps_executed'])
            lines.append(f"Steps Completed: {result['steps_executed']}/{total_steps}")
        
        # Analysis section
        if 'analysis' in result and result['analysis']:
            lines.append(f"\n📝 ANALYSIS")
            lines.append("-" * 30)
            lines.append(result['analysis'])
        
        # Step details
        if 'step_details' in result and result['step_details']:
            lines.append(f"\n🔄 STEP DETAILS")
            lines.append("-" * 30)
            for i, step in enumerate(result['step_details'], 1):
                step_status = step.get('status', 'unknown')
                step_emoji = self._get_status_emoji(step_status)
                lines.append(f"{i}. {step_emoji} {step.get('step', {}).get('description', 'Unknown step')}")
                if step.get('analysis'):
                    lines.append(f"   Analysis: {step['analysis'][:100]}...")
        
        # Performance metrics
        lines.append(f"\n⚡ PERFORMANCE")
        lines.append("-" * 30)
        lines.append(f"Method: {result.get('method', 'unknown')}")
        if 'timestamp' in result:
            lines.append(f"Completed: {result['timestamp']}")
        
        return "\n".join(lines)
    
    def _format_markdown_task_report(self, result: Dict[str, Any]) -> str:
        """Format task execution result as markdown"""
        lines = []
        
        # Header
        lines.append("# 🔮 Eevee Task Execution Report")
        lines.append("")
        
        # Summary
        lines.append("## 📋 Task Summary")
        lines.append("")
        lines.append(f"**Task:** {result.get('task', 'Unknown')}")
        
        status = result.get('status', 'unknown')
        status_emoji = self._get_status_emoji(status)
        lines.append(f"**Status:** {status_emoji} {status.upper()}")
        
        if 'execution_time' in result:
            lines.append(f"**Execution Time:** {result['execution_time']:.2f} seconds")
        
        if 'steps_executed' in result:
            total_steps = result.get('total_steps', result['steps_executed'])
            lines.append(f"**Steps Completed:** {result['steps_executed']}/{total_steps}")
        
        lines.append("")
        
        # Analysis
        if 'analysis' in result and result['analysis']:
            lines.append("## 📝 Analysis")
            lines.append("")
            lines.append(result['analysis'])
            lines.append("")
        
        # Step details
        if 'step_details' in result and result['step_details']:
            lines.append("## 🔄 Step Details")
            lines.append("")
            for i, step in enumerate(result['step_details'], 1):
                step_status = step.get('status', 'unknown')
                step_emoji = self._get_status_emoji(step_status)
                lines.append(f"{i}. {step_emoji} **{step.get('step', {}).get('description', 'Unknown step')}**")
                if step.get('analysis'):
                    lines.append(f"   - Analysis: {step['analysis']}")
                if step.get('actions_taken'):
                    lines.append(f"   - Actions: {', '.join(step['actions_taken'])}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_text_pokemon_report(self, pokemon_data: List[Any]) -> str:
        """Format Pokemon party data as text"""
        lines = []
        
        # Header
        lines.append("🎮 " + "="*50)
        lines.append(f"🎮 POKEMON PARTY REPORT ({len(pokemon_data)} Pokemon)")
        lines.append("🎮 " + "="*50)
        
        if not pokemon_data:
            lines.append("\nNo Pokemon data available.")
            return "\n".join(lines)
        
        # Individual Pokemon
        for i, pokemon in enumerate(pokemon_data, 1):
            if hasattr(pokemon, 'name'):
                # Pokemon object
                lines.append(f"\n{i}. {pokemon.name} (Level {pokemon.level})")
                
                if pokemon.max_hp > 0:
                    hp_pct = pokemon.hp_percentage()
                    hp_emoji = "🟢" if hp_pct > 70 else "🟡" if hp_pct > 30 else "🔴"
                    lines.append(f"   HP: {pokemon.current_hp}/{pokemon.max_hp} ({hp_pct:.1f}%) {hp_emoji}")
                
                if pokemon.status != "normal":
                    lines.append(f"   Status: {pokemon.status.upper()} ⚠️")
                
                if pokemon.types:
                    lines.append(f"   Type(s): {', '.join(pokemon.types).title()}")
                
                if pokemon.moves:
                    lines.append("   Moves:")
                    for move in pokemon.moves:
                        if isinstance(move, dict):
                            move_name = move.get("name", "Unknown")
                            pp_current = move.get("pp_current", 0)
                            pp_max = move.get("pp_max", 0)
                            if pp_max > 0:
                                pp_pct = (pp_current / pp_max) * 100
                                pp_emoji = "🟢" if pp_pct > 50 else "🟡" if pp_pct > 20 else "🔴"
                                lines.append(f"     • {move_name}: {pp_current}/{pp_max} PP {pp_emoji}")
                            else:
                                lines.append(f"     • {move_name}")
            else:
                # Dictionary data
                pokemon_dict = pokemon if isinstance(pokemon, dict) else {}
                name = pokemon_dict.get('name', f'Pokemon {i}')
                level = pokemon_dict.get('level', 'Unknown')
                lines.append(f"\n{i}. {name} (Level {level})")
                
                # Add other available data
                for key, value in pokemon_dict.items():
                    if key not in ['name', 'level'] and value:
                        lines.append(f"   {key.title()}: {value}")
        
        return "\n".join(lines)
    
    def _format_markdown_pokemon_report(self, pokemon_data: List[Any]) -> str:
        """Format Pokemon party data as markdown"""
        lines = []
        
        lines.append("# 🎮 Pokemon Party Report")
        lines.append("")
        lines.append(f"**Party Size:** {len(pokemon_data)} Pokemon")
        lines.append("")
        
        if not pokemon_data:
            lines.append("No Pokemon data available.")
            return "\n".join(lines)
        
        # Create table
        lines.append("| # | Pokemon | Level | HP | Status | Type(s) |")
        lines.append("|---|---------|-------|----|---------|---------| ")
        
        for i, pokemon in enumerate(pokemon_data, 1):
            if hasattr(pokemon, 'name'):
                # Pokemon object
                hp_display = f"{pokemon.current_hp}/{pokemon.max_hp}" if pokemon.max_hp > 0 else "Unknown"
                hp_pct = pokemon.hp_percentage() if pokemon.max_hp > 0 else 0
                hp_emoji = "🟢" if hp_pct > 70 else "🟡" if hp_pct > 30 else "🔴"
                
                status_display = pokemon.status if pokemon.status != "normal" else "OK"
                types_display = ", ".join(pokemon.types) if pokemon.types else "Unknown"
                
                lines.append(f"| {i} | {pokemon.name} | {pokemon.level} | {hp_display} {hp_emoji} | {status_display} | {types_display} |")
            else:
                # Dictionary data
                pokemon_dict = pokemon if isinstance(pokemon, dict) else {}
                name = pokemon_dict.get('name', f'Pokemon {i}')
                level = pokemon_dict.get('level', 'Unknown')
                lines.append(f"| {i} | {name} | {level} | - | - | - |")
        
        lines.append("")
        
        # Detailed move information
        lines.append("## Move Details")
        lines.append("")
        
        for i, pokemon in enumerate(pokemon_data, 1):
            if hasattr(pokemon, 'moves') and pokemon.moves:
                lines.append(f"### {pokemon.name}")
                lines.append("")
                for move in pokemon.moves:
                    if isinstance(move, dict):
                        move_name = move.get("name", "Unknown")
                        pp_current = move.get("pp_current", 0)
                        pp_max = move.get("pp_max", 0)
                        if pp_max > 0:
                            pp_pct = (pp_current / pp_max) * 100
                            pp_emoji = "🟢" if pp_pct > 50 else "🟡" if pp_pct > 20 else "🔴"
                            lines.append(f"- **{move_name}**: {pp_current}/{pp_max} PP {pp_emoji}")
                        else:
                            lines.append(f"- **{move_name}**")
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_text_session_report(self, session_data: Dict[str, Any]) -> str:
        """Format session summary as text"""
        lines = []
        
        lines.append("📊 " + "="*50)
        lines.append("📊 EEVEE SESSION SUMMARY")
        lines.append("📊 " + "="*50)
        
        # Session info
        lines.append(f"\nSession: {session_data.get('memory_session', 'Unknown')}")
        lines.append(f"Tasks Executed: {session_data.get('tasks_executed', 0)}")
        
        # Agent config
        if 'agent_config' in session_data:
            config = session_data['agent_config']
            lines.append(f"Model: {config.get('model', 'Unknown')}")
            lines.append(f"Window: {config.get('window_title', 'Unknown')}")
        
        return "\n".join(lines)
    
    def _format_json_report(self, data: Any) -> str:
        """Format any data as JSON"""
        return json.dumps(data, indent=2, default=str)
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        status_emojis = {
            "success": "✅",
            "completed": "✅", 
            "partial_success": "🟡",
            "failed": "❌",
            "error": "❌",
            "in_progress": "🔄",
            "pending": "⏳",
            "unknown": "❓"
        }
        return status_emojis.get(status.lower(), "❓")
    
    def _pokemon_to_dict_list(self, pokemon_data: List[Any]) -> List[Dict]:
        """Convert Pokemon objects to dictionary list"""
        dict_list = []
        for pokemon in pokemon_data:
            if hasattr(pokemon, '__dict__'):
                # Convert dataclass or object to dict
                if hasattr(pokemon, '_asdict'):
                    dict_list.append(pokemon._asdict())
                else:
                    dict_list.append(asdict(pokemon) if hasattr(pokemon, '__dataclass_fields__') else pokemon.__dict__)
            else:
                dict_list.append(pokemon)
        return dict_list

class ReportGenerator:
    """Generates comprehensive reports and exports them to files"""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory for saving reports
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "reports"
        
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.formatter = ReportFormatter()
    
    def generate_task_report(
        self,
        result: Dict[str, Any],
        save_to_file: bool = True,
        format_type: str = "text"
    ) -> Tuple[str, Optional[Path]]:
        """
        Generate and optionally save task execution report
        
        Args:
            result: Task execution result
            save_to_file: Whether to save report to file
            format_type: Output format
            
        Returns:
            Tuple of (formatted_report, file_path)
        """
        report = self.formatter.format_task_execution_report(result, format_type)
        
        file_path = None
        if save_to_file:
            file_path = self._save_report(
                report, 
                f"task_report_{self._get_safe_filename(result.get('task', 'unknown'))}",
                format_type
            )
        
        return report, file_path
    
    def generate_pokemon_report(
        self,
        pokemon_data: List[Any],
        save_to_file: bool = True,
        format_type: str = "text"
    ) -> Tuple[str, Optional[Path]]:
        """
        Generate and optionally save Pokemon party report
        
        Args:
            pokemon_data: Pokemon party data
            save_to_file: Whether to save report to file
            format_type: Output format
            
        Returns:
            Tuple of (formatted_report, file_path)
        """
        report = self.formatter.format_pokemon_party_report(pokemon_data, format_type)
        
        file_path = None
        if save_to_file:
            file_path = self._save_report(
                report,
                "pokemon_party_report",
                format_type
            )
        
        return report, file_path
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> Path:
        """
        Export data to CSV file
        
        Args:
            data: List of dictionaries to export
            filename: Output filename (without extension)
            
        Returns:
            Path to saved CSV file
        """
        if not data:
            raise ValueError("No data to export")
        
        csv_path = self.output_dir / f"{filename}.csv"
        
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return csv_path
    
    def _save_report(self, content: str, base_filename: str, format_type: str) -> Path:
        """Save report content to file"""
        extensions = {"text": "txt", "markdown": "md", "json": "json"}
        extension = extensions.get(format_type, "txt")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}.{extension}"
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return file_path
    
    def _get_safe_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_filename = "".join(c if c in safe_chars else "_" for c in text)
        return safe_filename[:30]  # Limit length