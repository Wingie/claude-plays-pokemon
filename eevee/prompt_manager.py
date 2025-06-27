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
        (self.prompts_dir / "providers").mkdir(exist_ok=True)
        (self.prompts_dir / "providers" / "gemini").mkdir(exist_ok=True)
        (self.prompts_dir / "providers" / "mistral").mkdir(exist_ok=True)
        
        # Initialize verbose flag early
        self.verbose = False
        
        # Usage tracking for debugging
        self.usage_log = []
        
        # Initialize active template and playbook
        self.active_template = None
        self.active_playbook = None
        
        # Load prompt templates
        self.base_prompts = self._load_base_prompts()
        self.playbooks = self._load_playbooks()
    
    def _load_base_prompts(self) -> Dict[str, Any]:
        """Load base prompt templates with provider-specific support"""
        # Try to load provider-specific prompts first
        provider_specific_prompts = self._load_provider_specific_prompts()
        if provider_specific_prompts:
            return provider_specific_prompts
        
        # Fallback to base prompts
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
    
    def _load_provider_specific_prompts(self) -> Dict[str, Any]:
        """Load provider-specific prompt templates based on current provider"""
        # Determine current provider from environment or centralized config
        current_provider = self._get_current_provider()
        
        if not current_provider:
            return None
            
        # Try provider-specific prompts directory
        provider_prompts_file = self.prompts_dir / "providers" / current_provider / "base_prompts.yaml"
        
        if provider_prompts_file.exists():
            try:
                with open(provider_prompts_file, 'r') as f:
                    provider_prompts = yaml.safe_load(f)
                    if self.verbose:
                        print(f"📂 Loaded {current_provider}-specific prompts from {provider_prompts_file}")
                    return provider_prompts
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Failed to load {current_provider} prompts: {e}")
                return None
        
        return None
    
    def _get_current_provider(self) -> str:
        """Determine current provider from environment or config"""
        # Always check environment variable first for runtime changes
        import os
        env_provider = os.getenv('LLM_PROVIDER', '').lower()
        if env_provider in ['gemini', 'mistral']:
            return env_provider
        
        try:
            # Fallback to provider config
            from provider_config import get_provider_config
            config = get_provider_config()
            return config.primary_provider
        except Exception:
            return None
    
    def switch_to_provider(self, provider: str, verbose: bool = False) -> bool:
        """
        Switch to provider-specific prompts and reload templates
        
        Args:
            provider: Provider name ('gemini' or 'mistral')
            verbose: Enable verbose logging
            
        Returns:
            True if switch was successful, False otherwise
        """
        if provider.lower() not in ['gemini', 'mistral']:
            if verbose:
                print(f"❌ Invalid provider: {provider}")
            return False
        
        # Create provider directory if it doesn't exist
        provider_dir = self.prompts_dir / "providers" / provider.lower()
        provider_dir.mkdir(exist_ok=True)
        
        # Temporarily set environment variable for provider detection
        import os
        old_provider = os.getenv('LLM_PROVIDER', '')
        os.environ['LLM_PROVIDER'] = provider.lower()
        
        try:
            # Reload prompts with new provider
            old_prompts = len(self.base_prompts)
            self.base_prompts = self._load_base_prompts()
            new_prompts = len(self.base_prompts)
            
            if verbose:
                print(f"✅ Switched to {provider} prompts ({new_prompts} templates loaded)")
                if old_prompts != new_prompts:
                    print(f"📊 Template count changed: {old_prompts} → {new_prompts}")
            
            return True
            
        except Exception as e:
            # Restore old provider on error
            if old_provider:
                os.environ['LLM_PROVIDER'] = old_provider
            else:
                os.environ.pop('LLM_PROVIDER', None)
            
            if verbose:
                print(f"❌ Failed to switch to {provider}: {e}")
            return False
    
    def get_current_provider_info(self) -> Dict[str, Any]:
        """
        Get information about current provider and loaded templates
        
        Returns:
            Dictionary with provider info and template details
        """
        current_provider = self._get_current_provider()
        
        # Check if provider-specific templates are loaded
        provider_specific = False
        if current_provider:
            provider_file = self.prompts_dir / "providers" / current_provider / "base_prompts.yaml"
            provider_specific = provider_file.exists()
        
        return {
            'current_provider': current_provider,
            'provider_specific_loaded': provider_specific,
            'template_count': len(self.base_prompts),
            'available_providers': ['gemini', 'mistral'],
            'template_versions': self.get_template_versions()
        }
    
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

Please examine and report on:

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
            
            "exploration_strategy": {
                "name": "Pokemon Area Exploration Strategy",
                "description": "Systematic exploration of Pokemon game areas to find all trainers and paths",
                "template": """🎮 **POKEMON AREA EXPLORATION** 🎮
    
**🎯 CORE POKEMON PRINCIPLE**: 
- **Trainers battle you AUTOMATICALLY** when they see you (line of sight)
- **Your goal**: Explore every part of this area systematically
- **Wild Pokemon**: Will also encounter you automatically in tall grass
- **Navigation**: Move through area to discover all content

Task Context: {task}

**📍 EXPLORATION ANALYSIS**:

🎯 **OBSERVE** (What area are you in?):
- What type of area: Route, Forest, Cave, City, Building?
- Where is your character currently positioned?
- What paths/directions are available from here?
- Are there any trainers visible on screen?
- Any unexplored paths or areas visible?

🧠 **EXPLORATION STRATEGY** (Systematic area clearing):
- **PRIMARY GOAL**: Visit every walkable tile in this area
- **Trainer Battles**: Will happen automatically when you get close enough
- **Wild Pokemon**: Will appear in grass areas automatically  
- **Area Completion**: When you've explored all possible paths
- **Next Step**: Pick an unexplored direction and move there

⚡ **NEXT MOVEMENT** (1-2 buttons max):
- Choose ONE unexplored direction: up, down, left, or right
- If all nearby areas explored, backtrack and try different branch
- If you see a trainer, move toward them (battle will start automatically)
- If path blocked, try alternative route
- **NEVER** spam same direction repeatedly

**🗺️ DEPTH-FIRST EXPLORATION RULES**:
1. **Pick a direction** and follow it until you can't go further
2. **When blocked**, backtrack and try the next available path  
3. **Trainers will battle you** automatically - don't try to initiate
4. **Area complete** when no more unexplored paths remain
5. **Then find exit** to next area or return to previous area

Use pokemon_controller with 1 directional button.""",
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
        self._log_usage(prompt_type, template_source)
        if verbose:
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
    
    def get_exploration_strategy_prompt(self, task: str, include_playbook: str = None, verbose: bool = False) -> str:
        """Get formatted exploration strategy prompt"""
        variables = {"task": task}
        return self.get_prompt("exploration_strategy", variables, include_playbook, verbose)
        
    def get_battle_analysis_prompt(self, task: str, recent_actions: str = "", verbose: bool = False) -> str:
        """Get formatted battle analysis prompt"""
        variables = {"task": task, "recent_actions": recent_actions}
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
    
    def reload_templates(self):
        """Reload all templates and playbooks from disk"""
        print("🔄 RELOADING PROMPT TEMPLATES...")
        old_versions = self.get_template_versions()
        
        # Reload base prompts and playbooks
        self.base_prompts = self._load_base_prompts()
        self.playbooks = self._load_playbooks()
        
        new_versions = self.get_template_versions()
        
        # Show what changed
        changes = []
        for template, old_version in old_versions.items():
            if template in new_versions and new_versions[template] != old_version:
                changes.append(f"{template} {old_version} → {new_versions[template]}")
        
        if changes:
            print(f"✅ TEMPLATE UPDATES LOADED: {', '.join(changes)}")
        else:
            print("ℹ️ No template version changes detected")
            
        print("🔄 RELOADED PROMPT TEMPLATES - AI will now use improved versions")
    
    def get_template_versions(self) -> Dict[str, str]:
        """Get current versions of all templates"""
        versions = {}
        for template_name, template_data in self.base_prompts.items():
            if isinstance(template_data, dict):
                versions[template_name] = template_data.get('version', '1.0')
        return versions
    
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
    
    def get_template_versions(self) -> Dict[str, str]:
        """
        Get current versions of all loaded templates
        
        Returns:
            Dictionary mapping template names to their versions
        """
        versions = {}
        for template_name, template_data in self.base_prompts.items():
            versions[template_name] = template_data.get("version", "unknown")
        return versions
    
    def set_active_template(self, template_name: str) -> bool:
        """
        Set the active prompt template by name.
        
        Args:
            template_name: Name of the template to activate (must exist in base_prompts)
            
        Returns:
            bool: True if template was found and activated, False otherwise
        """
        if template_name in self.base_prompts:
            self.active_template = template_name
            if self.verbose:
                print(f"✓ Activated prompt template: {template_name}")
            return True
        else:
            if self.verbose:
                print(f"✗ Template not found: {template_name}")
            return False
            
    def set_active_playbook(self, playbook_name: str) -> bool:
        """
        Set the active playbook by name.
        
        Args:
            playbook_name: Name of the playbook to activate (must exist in playbooks)
            
        Returns:
            bool: True if playbook was found and activated, False otherwise
        """
        if playbook_name in self.playbooks:
            self.active_playbook = playbook_name
            if self.verbose:
                print(f"✓ Activated playbook: {playbook_name}")
            return True
        else:
            if self.verbose:
                print(f"✗ Playbook not found: {playbook_name}")
            return False
    
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
    
    # AI-DIRECTED PROMPT CONTROL METHODS
    
    def process_ai_commands(self, ai_response: str, memory_system=None) -> Dict[str, Any]:
        """
        Process AI prompt control commands from AI response
        
        Args:
            ai_response: The AI's response text containing potential commands
            memory_system: Optional memory system to execute memory commands
            
        Returns:
            Dict containing processed commands and their results
        """
        commands_processed = {
            "memory_commands": [],
            "prompt_commands": [],
            "emergency_commands": [],
            "context_changes": []
        }
        
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Memory control commands
            if line.startswith('LOAD_MEMORIES:'):
                context = line.split(':', 1)[1].strip()
                if memory_system:
                    memories = self._load_memories_by_context(context, memory_system)
                    commands_processed["memory_commands"].append({
                        "action": "load",
                        "context": context,
                        "result": memories
                    })
            
            elif line.startswith('SAVE_MEMORY:'):
                # Extract memory content and tag
                parts = line.split('TAG:', 1)
                if len(parts) == 2:
                    content = parts[0].replace('SAVE_MEMORY:', '').strip()
                    tag = parts[1].strip()
                    if memory_system:
                        result = self._save_memory_with_tag(content, tag, memory_system)
                        commands_processed["memory_commands"].append({
                            "action": "save",
                            "content": content,
                            "tag": tag,
                            "result": result
                        })
            
            # Prompt control commands
            elif line.startswith('REQUEST_PROMPT:'):
                prompt_name = line.split(':', 1)[1].strip()
                result = self._switch_to_prompt(prompt_name)
                commands_processed["prompt_commands"].append({
                    "action": "request",
                    "prompt": prompt_name,
                    "result": result
                })
            
            elif line.startswith('CONTEXT_PROMPT:'):
                context = line.split(':', 1)[1].strip()
                result = self._select_context_prompt(context)
                commands_processed["prompt_commands"].append({
                    "action": "context_switch",
                    "context": context,
                    "result": result
                })
            
            elif line.startswith('ESCALATE_PROMPT'):
                level = "level_1"
                if ':' in line:
                    level = line.split(':', 1)[1].strip()
                result = self._escalate_prompt(level)
                commands_processed["prompt_commands"].append({
                    "action": "escalate",
                    "level": level,
                    "result": result
                })
            
            # Emergency commands
            elif 'EMERGENCY_MODE' in line:
                result = self._activate_emergency_mode()
                commands_processed["emergency_commands"].append({
                    "action": "emergency_mode",
                    "result": result
                })
            
            elif 'RESET_CONTEXT' in line:
                result = self._reset_context()
                commands_processed["emergency_commands"].append({
                    "action": "reset_context",
                    "result": result
                })
        
        return commands_processed
    
    def _load_memories_by_context(self, context: str, memory_system) -> List[Dict]:
        """Load memories matching the specified context"""
        try:
            # This would interface with the actual memory system
            if hasattr(memory_system, 'search_memories_by_tag'):
                return memory_system.search_memories_by_tag(context)
            elif hasattr(memory_system, 'get_memories'):
                all_memories = memory_system.get_memories()
                # Filter by context/tag
                filtered = [m for m in all_memories if context.lower() in str(m).lower()]
                return filtered[:10]  # Limit to 10 most relevant
            else:
                return []
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Memory loading failed: {e}")
            return []
    
    def _save_memory_with_tag(self, content: str, tag: str, memory_system) -> bool:
        """Save memory with specified tag"""
        try:
            if hasattr(memory_system, 'save_memory_with_tag'):
                return memory_system.save_memory_with_tag(content, tag)
            elif hasattr(memory_system, 'add_memory'):
                # Fallback for simpler memory systems
                tagged_content = f"[{tag}] {content}"
                return memory_system.add_memory(tagged_content)
            else:
                return False
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Memory saving failed: {e}")
            return False
    
    def _switch_to_prompt(self, prompt_name: str) -> bool:
        """Switch to a specific prompt template"""
        # Map AI prompt names to actual template names
        prompt_mapping = {
            "battle_expert": "ai_battle_with_context_loading",
            "maze_navigation": "ai_maze_with_solution_memory", 
            "exploration_strategy": "ai_navigation_with_memory_control",
            "emergency_recovery": "ai_emergency_recovery"
        }
        
        actual_prompt = prompt_mapping.get(prompt_name, prompt_name)
        
        if actual_prompt in self.base_prompts:
            self.active_template = actual_prompt
            if self.verbose:
                print(f"🔄 AI requested prompt switch to: {prompt_name} ({actual_prompt})")
            return True
        else:
            if self.verbose:
                print(f"❌ AI requested unknown prompt: {prompt_name}")
            return False
    
    def _select_context_prompt(self, context: str) -> bool:
        """Select appropriate prompt based on context"""
        context_mapping = {
            "forest": "ai_navigation_with_memory_control",
            "cave": "ai_maze_with_solution_memory",
            "battle": "ai_battle_with_context_loading",
            "maze": "ai_maze_with_solution_memory",
        }
        
        prompt_name = context_mapping.get(context.lower())
        if prompt_name:
            self.active_template = prompt_name
            if self.verbose:
                print(f"🎯 AI selected context prompt: {context} → {prompt_name}")
            return True
        return False
    
    
    
    def _reset_context(self) -> bool:
        """Reset context to default navigation"""
        self.active_template = "ai_navigation_with_memory_control"
        if self.verbose:
            print("🔄 AI reset context to default navigation")
        return True
    
    
    def get_ai_directed_prompt(
        self, 
        context_type: str = "navigation",
        task: str = "",
        recent_actions: List[str] = None,
        available_memories: List[str] = None,
        battle_context: Dict = None,
        maze_context: Dict = None,
        escalation_level: str = "level_1",
        memory_context: str = "",
        image_data: str = None,
        movement_data: Dict = None,
        verbose: bool = False
    ) -> str:
        """
        Get AI-directed prompt with full context and memory control
        
        Args:
            context_type: Type of context (navigation, battle, maze, emergency)
            task: Current task description
            recent_actions: List of recent button actions
            available_memories: List of available memory contexts
            battle_context: Battle-specific context information
            maze_context: Maze-specific context information  
            escalation_level: Emergency escalation level
            memory_context: Current memory context string
            image_data: Base64 encoded screenshot for visual template selection
            movement_data: Movement validation data from visual analysis (Pixtral)
            verbose: Enable verbose logging
            
        Returns:
            Formatted AI-directed prompt
        """
        
        # SIMPLIFIED: Direct template usage with variables and optional playbook
        variables = variables or {}
        
        # Check if template exists
        if prompt_type not in self.base_prompts:
            if verbose:
                print(f"⚠️ Template '{prompt_type}' not found, using exploration_strategy")
            prompt_type = "exploration_strategy"
        
        # Get the template
        template = self.base_prompts[prompt_type]["template"]
        
        # Add playbook content if specified
        if include_playbook and include_playbook in self.playbooks:
            playbook_content = self.playbooks[include_playbook]
            template = f"{playbook_content}\n\n{template}"
            if verbose:
                print(f"✅ Direct Prompt: {prompt_type} + playbook/{include_playbook}")
        else:
            if verbose:
                print(f"✅ Direct Prompt: {prompt_type} (no playbook)")
        
        # Format template with variables
        try:
            formatted_prompt = template.format(**variables)
            return formatted_prompt
        except KeyError as e:
            if verbose:
                print(f"⚠️ Template formatting error: {e}")
            # Simple fallback
            return f"Error formatting template {prompt_type}: {e}"
    
    # AI selection utility methods removed - now using direct visual template recommendations
