"""
PromptManager - Advanced Prompt System for Eevee
Handles prompt templating, A/B testing, and prompt optimization for Pokemon AI tasks
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class PromptManager:
    """Manages prompt templates and experimentation for Eevee AI system"""
    
    def __init__(self, prompts_dir: Path = None):
        """
        Initialize prompt manager with template directory
        
        Args:
            prompts_dir: Directory containing prompt templates
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "prompts"
        
        self.prompts_dir = prompts_dir
        self.prompts_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.prompts_dir / "base").mkdir(exist_ok=True)
        (self.prompts_dir / "playbooks").mkdir(exist_ok=True)
        
        # Load prompt templates
        self.base_prompts = self._load_base_prompts()
        self.playbooks = self._load_playbooks()
        
        # Usage tracking for debugging
        self.usage_log = []
    
    def _load_base_prompts(self) -> Dict[str, Any]:
        """Load base prompt templates"""
        base_prompts_file = self.prompts_dir / "base" / "base_prompts.yaml"
        
        if base_prompts_file.exists():
            with open(base_prompts_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default base prompts
            default_prompts = self._create_default_prompts()
            with open(base_prompts_file, 'w') as f:
                yaml.dump(default_prompts, f, default_flow_style=False)
            return default_prompts
    
    def _load_playbooks(self) -> Dict[str, str]:
        """Load playbook files for location-specific guidance"""
        playbooks = {}
        
        playbooks_dir = self.prompts_dir / "playbooks"
        for playbook_file in playbooks_dir.glob("*.md"):
            with open(playbook_file, 'r') as f:
                playbooks[playbook_file.stem] = f.read()
        
        return playbooks
    
    def _log_usage(self, prompt_type: str, template_source: str):
        """Log prompt usage for debugging"""
        self.usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "prompt_type": prompt_type,
            "template_source": template_source
        })
    
    def _create_default_prompts(self) -> Dict[str, Any]:
        """Create default prompt templates"""
        return {
            "task_analysis": {
                "name": "Task Analysis Base",
                "description": "Analyzes Pokemon game tasks and creates execution plans",
                "template": """Analyze this Pokemon game task and create a detailed execution plan:

TASK: {task}

Current Context:
{context_summary}

Memory Context:
{memory_context}

Please provide:
1. **Current Game State Analysis**: What's visible on screen
2. **Task Breakdown**: Break the task into specific steps
3. **Execution Strategy**: How to accomplish each step
4. **Navigation Requirements**: What menus/areas need to be accessed
5. **Expected Challenges**: Potential obstacles or edge cases
6. **Success Criteria**: How to know the task is complete

Be specific and actionable in your response.""",
                "variables": ["task", "context_summary", "memory_context"],
                "version": "1.0"
            },
            
            "pokemon_party_analysis": {
                "name": "Pokemon Party Analysis Base",
                "description": "Analyzes Pokemon party status, levels, moves, and condition",
                "template": """Analyze this Pokemon party screen and provide comprehensive information:

Current Task Context: {task}

Please examine the screen and provide detailed information about:

1. **Pokemon Party Overview**:
   - How many Pokemon are in the party
   - Which Pokemon is currently selected/highlighted
   - Overall party health status

2. **Individual Pokemon Details** (for each visible Pokemon):
   - Pokemon name and level
   - Current HP vs Maximum HP
   - Status conditions (poison, sleep, paralysis, etc.)
   - Type(s) if visible

3. **Moves and PP Analysis** (if move details are visible):
   - List all moves for each Pokemon
   - PP remaining for each move
   - Move types and power if shown

4. **Strategic Assessment**:
   - Which Pokemon are ready for battle
   - Which Pokemon need healing
   - Recommended actions based on current state

5. **Navigation Context**:
   - What menu/screen are we currently viewing
   - How to access more detailed information if needed

Format your response with clear sections and be specific about numbers and details.""",
                "variables": ["task"],
                "version": "1.0"
            },
            
            "location_analysis": {
                "name": "Location and Environment Analysis Base", 
                "description": "Analyzes current location, map, and environmental features",
                "template": """Analyze this Pokemon game location and environment:

Task Context: {task}

Provide detailed analysis of:

1. **Location Identification**:
   - Current area/route/town name (if visible)
   - Indoor vs outdoor environment
   - Specific building or area type

2. **Player Character**:
   - Character position on screen
   - Direction character is facing
   - Current movement state

3. **Environmental Features**:
   - Terrain types (grass, water, paths, buildings)
   - Significant landmarks or structures
   - Available exits and entrances
   - Weather or time-of-day indicators

4. **Interactive Elements**:
   - NPCs and their positions/activities
   - Items on the ground or available for interaction
   - Signs, doors, or other interactive objects
   - Battle opportunities (trainers, wild Pokemon areas)

5. **Navigation Opportunities**:
   - Immediate movement options
   - Areas that can be explored
   - Buildings or locations that can be entered

6. **Strategic Considerations**:
   - Pokemon Center or healing opportunities
   - Shop or service locations
   - Training opportunities
   - Progress-blocking obstacles

Be specific about positions, directions, and interactive elements.""",
                "variables": ["task"],
                "version": "1.0"
            },
            
            "inventory_analysis": {
                "name": "Inventory and Items Analysis Base",
                "description": "Analyzes Pokemon inventory, items, and bag contents",
                "template": """Analyze this Pokemon inventory/bag screen:

Task Context: {task}

Please examine and report on:

1. **Bag Organization**:
   - Which bag section is currently selected
   - Available bag categories (Items, Poke Balls, Key Items, etc.)
   - Navigation state within the inventory

2. **Item Inventory**:
   - List all visible items with quantities
   - Item categories and organization
   - Special or rare items present

3. **Item Functionality**:
   - Healing items and their effects
   - Battle items (X Attack, X Defense, etc.)
   - Utility items (Repel, Escape Rope, etc.)
   - Key items and their purposes

4. **Quantity Analysis**:
   - Items that are running low
   - Items that are well-stocked
   - Missing essential items

5. **Strategic Assessment**:
   - Preparedness for upcoming challenges
   - Items that should be purchased
   - Items that can be used immediately
   - Inventory management recommendations

6. **Usage Context**:
   - Items relevant to current task
   - Items that could solve immediate problems
   - Items that should be saved for later

Be thorough in listing items and their quantities.""",
                "variables": ["task"],
                "version": "1.0"
            },
            
            "battle_analysis": {
                "name": "Battle Situation Analysis Base",
                "description": "Analyzes Pokemon battles and combat situations",
                "template": """Analyze this Pokemon battle situation:

Task Context: {task}

Provide comprehensive battle analysis:

1. **Battle State**:
   - Current turn phase (selection, animation, etc.)
   - Battle type (wild Pokemon, trainer, gym leader)
   - Battle progress and turn count

2. **Your Pokemon**:
   - Active Pokemon name, level, and type(s)
   - Current HP and status condition
   - Available moves with PP remaining
   - Type advantages/disadvantages

3. **Opponent Pokemon**:
   - Opponent Pokemon name, level, and type(s)
   - Visible HP status
   - Observed moves and abilities
   - Threat assessment

4. **Strategic Analysis**:
   - Recommended next move
   - Type effectiveness considerations
   - Status effect strategies
   - Switching recommendations

5. **Battle Options**:
   - Available battle menu options
   - Items that could be used
   - Pokemon switch options
   - Escape possibility and consequences

6. **Victory Conditions**:
   - Path to winning the battle
   - Risks and backup strategies
   - Post-battle considerations

Be specific about moves, types, and strategic recommendations.""",
                "variables": ["task"],
                "version": "1.0"
            }
        }
    
    def get_prompt(
        self, 
        prompt_type: str, 
        variables: Dict[str, Any] = None,
        include_playbook: str = None,
        verbose: bool = False
    ) -> str:
        """
        Get a formatted prompt template with optional playbook integration
        
        Args:
            prompt_type: Type of prompt to retrieve
            variables: Variables to substitute in template
            include_playbook: Name of playbook to include (e.g., 'battle', 'navigation')
            verbose: Whether to log prompt usage for debugging
            
        Returns:
            Formatted prompt string
        """
        if variables is None:
            variables = {}
        
        # Get the base prompt template
        if prompt_type not in self.base_prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        template = self.base_prompts[prompt_type]["template"]
        template_source = f"base/{prompt_type}"
        
        # Add playbook context if requested
        if include_playbook and include_playbook in self.playbooks:
            playbook_content = self.playbooks[include_playbook]
            template = f"{playbook_content}\n\n{template}"
            template_source += f" + playbook/{include_playbook}"
        
        # Log usage for debugging
        if verbose:
            self._log_usage(prompt_type, template_source)
            print(f"📖 Using prompt template: {template_source}")
        
        # Format template with variables
        try:
            formatted_prompt = template.format(**variables)
            return formatted_prompt
        except KeyError as e:
            raise ValueError(f"Missing required variable for prompt {prompt_type}: {e}")
    
    def get_task_analysis_prompt(
        self, 
        task: str, 
        game_context: Dict, 
        memory_context: Dict,
        include_playbook: str = None,
        verbose: bool = False
    ) -> str:
        """Get formatted task analysis prompt"""
        variables = {
            "task": task,
            "context_summary": self._format_context_summary(game_context),
            "memory_context": self._format_memory_context(memory_context)
        }
        
        return self.get_prompt("task_analysis", variables, include_playbook, verbose)
    
    def get_pokemon_party_prompt(self, task: str, verbose: bool = False) -> str:
        """Get formatted Pokemon party analysis prompt"""
        variables = {"task": task}
        return self.get_prompt("pokemon_party_analysis", variables, verbose=verbose)
    
    def get_location_analysis_prompt(self, task: str, include_playbook: str = None, verbose: bool = False) -> str:
        """Get formatted location analysis prompt"""
        variables = {"task": task}
        return self.get_prompt("location_analysis", variables, include_playbook, verbose)
        
    def get_battle_analysis_prompt(self, task: str, verbose: bool = False) -> str:
        """Get formatted battle analysis prompt"""
        variables = {"task": task}
        return self.get_prompt("battle_analysis", variables, "battle", verbose)
    
    def add_playbook_entry(self, playbook_name: str, content: str, append: bool = True):
        """
        Add or update content in a playbook file
        
        Args:
            playbook_name: Name of the playbook (e.g., 'navigation', 'battle')
            content: Content to add
            append: Whether to append to existing content or replace it
        """
        playbook_file = self.prompts_dir / "playbooks" / f"{playbook_name}.md"
        
        if append and playbook_file.exists():
            with open(playbook_file, 'a') as f:
                f.write(f"\n\n{content}")
        else:
            with open(playbook_file, 'w') as f:
                f.write(content)
        
        # Reload playbooks
        self.playbooks = self._load_playbooks()
    
    def get_usage_summary(self) -> str:
        """
        Get a summary of prompt usage for debugging
        
        Returns:
            Formatted usage summary
        """
        if not self.usage_log:
            return "No prompt usage recorded"
        
        summary = ["\n📊 Prompt Usage Summary:"]
        for entry in self.usage_log[-10:]:  # Show last 10 usages
            time = entry["timestamp"].split("T")[1][:8]  # Extract time
            summary.append(f"  {time} - {entry['prompt_type']} from {entry['template_source']}")
        
        return "\n".join(summary)
    
    def reload_templates(self):
        """
        Reload all prompt templates and playbooks from disk
        Useful for development and testing
        """
        self.base_prompts = self._load_base_prompts()
        self.playbooks = self._load_playbooks()
        print("🔄 Reloaded all prompt templates and playbooks")
    
    
    
    def _format_context_summary(self, game_context: Dict) -> str:
        """Format game context for prompt inclusion"""
        summary = []
        
        if game_context.get("timestamp"):
            summary.append(f"Screenshot captured: {game_context['timestamp']}")
        
        if game_context.get("window_found"):
            summary.append("✅ Game window connected")
        else:
            summary.append("❌ Game window not found")
        
        return "\n".join(summary)
    
    def _format_memory_context(self, memory_context: Dict) -> str:
        """Format memory context for prompt inclusion"""
        context_parts = []
        
        if memory_context.get("similar_tasks"):
            context_parts.append(f"Similar tasks completed: {len(memory_context['similar_tasks'])}")
        
        if memory_context.get("pokemon_knowledge"):
            context_parts.append(f"Pokemon knowledge entries: {len(memory_context['pokemon_knowledge'])}")
        
        if memory_context.get("location_knowledge"):
            context_parts.append(f"Location knowledge entries: {len(memory_context['location_knowledge'])}")
        
        game_state = memory_context.get("game_state", {})
        if game_state.get("location"):
            context_parts.append(f"Last known location: {game_state['location']}")
        
        if game_state.get("pokemon_party"):
            context_parts.append(f"Pokemon party size: {len(game_state['pokemon_party'])}")
        
        return "\n".join(context_parts) if context_parts else "No relevant memory context"
    
