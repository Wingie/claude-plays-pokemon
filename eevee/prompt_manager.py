"""
PromptManager - Advanced Prompt System for Eevee
Handles prompt templating, A/B testing, and prompt optimization for Pokemon AI tasks
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import statistics

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
        (self.prompts_dir / "experimental").mkdir(exist_ok=True)
        (self.prompts_dir / "base").mkdir(exist_ok=True)
        
        # Load prompt templates
        self.base_prompts = self._load_base_prompts()
        self.experimental_prompts = self._load_experimental_prompts()
        
        # Performance tracking
        self.performance_log = self.prompts_dir / "performance_log.json"
        self.prompt_metrics = self._load_performance_metrics()
        
        # Current experiment settings
        self.active_experiments = {}
    
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
    
    def _load_experimental_prompts(self) -> Dict[str, Any]:
        """Load experimental prompt variants"""
        experimental_prompts = {}
        
        experimental_dir = self.prompts_dir / "experimental"
        for prompt_file in experimental_dir.glob("*.yaml"):
            with open(prompt_file, 'r') as f:
                experimental_prompts[prompt_file.stem] = yaml.safe_load(f)
        
        return experimental_prompts
    
    def _load_performance_metrics(self) -> Dict[str, List[Dict]]:
        """Load prompt performance metrics"""
        if self.performance_log.exists():
            with open(self.performance_log, 'r') as f:
                return json.load(f)
        else:
            return {}
    
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
        experiment_name: str = None
    ) -> str:
        """
        Get a formatted prompt template
        
        Args:
            prompt_type: Type of prompt to retrieve
            variables: Variables to substitute in template
            experiment_name: Name of experimental variant to use
            
        Returns:
            Formatted prompt string
        """
        if variables is None:
            variables = {}
        
        # Get the prompt template
        if experiment_name and experiment_name in self.experimental_prompts:
            # Use experimental variant
            template_data = self.experimental_prompts[experiment_name].get(prompt_type)
            if template_data:
                template = template_data["template"]
                self._log_prompt_usage(prompt_type, experiment_name, "experimental")
            else:
                # Fallback to base prompt
                template = self.base_prompts[prompt_type]["template"]
                self._log_prompt_usage(prompt_type, "base", "fallback")
        else:
            # Use base prompt
            if prompt_type not in self.base_prompts:
                raise ValueError(f"Unknown prompt type: {prompt_type}")
            
            template = self.base_prompts[prompt_type]["template"]
            self._log_prompt_usage(prompt_type, "base", "standard")
        
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
        experiment_name: str = None
    ) -> str:
        """Get formatted task analysis prompt"""
        variables = {
            "task": task,
            "context_summary": self._format_context_summary(game_context),
            "memory_context": self._format_memory_context(memory_context)
        }
        
        return self.get_prompt("task_analysis", variables, experiment_name)
    
    def get_pokemon_party_prompt(self, task: str, experiment_name: str = None) -> str:
        """Get formatted Pokemon party analysis prompt"""
        variables = {"task": task}
        return self.get_prompt("pokemon_party_analysis", variables, experiment_name)
    
    def get_location_analysis_prompt(self, task: str, experiment_name: str = None) -> str:
        """Get formatted location analysis prompt"""
        variables = {"task": task}
        return self.get_prompt("location_analysis", variables, experiment_name)
    
    def create_experimental_prompt(
        self,
        experiment_name: str,
        base_prompt_type: str,
        modifications: Dict[str, Any],
        description: str = ""
    ) -> str:
        """
        Create an experimental prompt variant
        
        Args:
            experiment_name: Name for the experiment
            base_prompt_type: Base prompt to modify
            modifications: Changes to make to the base prompt
            description: Description of the experiment
            
        Returns:
            Path to created experimental prompt file
        """
        if base_prompt_type not in self.base_prompts:
            raise ValueError(f"Base prompt type not found: {base_prompt_type}")
        
        # Start with base prompt
        base_prompt = self.base_prompts[base_prompt_type].copy()
        
        # Apply modifications
        experimental_prompt = base_prompt.copy()
        experimental_prompt.update(modifications)
        experimental_prompt["experiment_name"] = experiment_name
        experimental_prompt["base_prompt"] = base_prompt_type
        experimental_prompt["description"] = description
        experimental_prompt["created_at"] = datetime.now().isoformat()
        
        # Save experimental prompt
        experiment_file = self.prompts_dir / "experimental" / f"{experiment_name}.yaml"
        experiment_data = {base_prompt_type: experimental_prompt}
        
        with open(experiment_file, 'w') as f:
            yaml.dump(experiment_data, f, default_flow_style=False)
        
        # Reload experimental prompts
        self.experimental_prompts = self._load_experimental_prompts()
        
        return str(experiment_file)
    
    def start_ab_test(
        self,
        experiment_name: str,
        prompt_type: str,
        variant_a: str = "base",
        variant_b: str = None,
        traffic_split: float = 0.5
    ):
        """
        Start an A/B test between prompt variants
        
        Args:
            experiment_name: Name of the A/B test
            prompt_type: Type of prompt to test
            variant_a: First variant (default: base prompt)
            variant_b: Second variant (experimental prompt name)
            traffic_split: Percentage of traffic for variant A (0.0-1.0)
        """
        import random
        
        self.active_experiments[experiment_name] = {
            "prompt_type": prompt_type,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "traffic_split": traffic_split,
            "started_at": datetime.now().isoformat(),
            "total_requests": 0,
            "variant_a_requests": 0,
            "variant_b_requests": 0
        }
        
        print(f"🧪 Started A/B test: {experiment_name}")
        print(f"   Testing: {variant_a} vs {variant_b}")
        print(f"   Traffic split: {traffic_split*100:.1f}% / {(1-traffic_split)*100:.1f}%")
    
    def get_ab_test_variant(self, experiment_name: str) -> Tuple[str, str]:
        """
        Get variant for A/B test
        
        Args:
            experiment_name: Name of active A/B test
            
        Returns:
            Tuple of (variant_name, variant_type)
        """
        import random
        
        if experiment_name not in self.active_experiments:
            return "base", "standard"
        
        experiment = self.active_experiments[experiment_name]
        experiment["total_requests"] += 1
        
        # Determine which variant to use
        if random.random() < experiment["traffic_split"]:
            experiment["variant_a_requests"] += 1
            return experiment["variant_a"], "variant_a"
        else:
            experiment["variant_b_requests"] += 1
            return experiment["variant_b"], "variant_b"
    
    def log_prompt_performance(
        self,
        prompt_type: str,
        variant_name: str,
        task_description: str,
        success: bool,
        execution_time: float,
        quality_score: float = None,
        metadata: Dict = None
    ):
        """
        Log performance metrics for a prompt
        
        Args:
            prompt_type: Type of prompt used
            variant_name: Name of prompt variant
            task_description: Description of task executed
            success: Whether task was successful
            execution_time: Time taken to execute task
            quality_score: Quality score for the result (0.0-1.0)
            metadata: Additional metadata
        """
        if prompt_type not in self.prompt_metrics:
            self.prompt_metrics[prompt_type] = []
        
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "variant_name": variant_name,
            "task_description": task_description,
            "success": success,
            "execution_time": execution_time,
            "quality_score": quality_score,
            "metadata": metadata or {}
        }
        
        self.prompt_metrics[prompt_type].append(performance_entry)
        
        # Save metrics to file
        with open(self.performance_log, 'w') as f:
            json.dump(self.prompt_metrics, f, indent=2)
    
    def get_performance_report(self, prompt_type: str = None) -> Dict[str, Any]:
        """
        Get performance report for prompts
        
        Args:
            prompt_type: Specific prompt type to report on (None for all)
            
        Returns:
            Performance report dictionary
        """
        if prompt_type:
            metrics = {prompt_type: self.prompt_metrics.get(prompt_type, [])}
        else:
            metrics = self.prompt_metrics
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "prompt_performance": {}
        }
        
        for ptype, entries in metrics.items():
            if not entries:
                continue
            
            # Calculate statistics
            successes = [e for e in entries if e["success"]]
            execution_times = [e["execution_time"] for e in entries if e["execution_time"]]
            quality_scores = [e["quality_score"] for e in entries if e["quality_score"] is not None]
            
            # Group by variant
            variants = {}
            for entry in entries:
                variant = entry["variant_name"]
                if variant not in variants:
                    variants[variant] = {"total": 0, "successful": 0, "avg_time": 0, "avg_quality": 0}
                
                variants[variant]["total"] += 1
                if entry["success"]:
                    variants[variant]["successful"] += 1
                if entry["execution_time"]:
                    variants[variant]["avg_time"] += entry["execution_time"]
                if entry["quality_score"]:
                    variants[variant]["avg_quality"] += entry["quality_score"]
            
            # Finalize averages
            for variant_stats in variants.values():
                if variant_stats["total"] > 0:
                    variant_stats["success_rate"] = variant_stats["successful"] / variant_stats["total"]
                    variant_stats["avg_time"] = variant_stats["avg_time"] / variant_stats["total"]
                    variant_stats["avg_quality"] = variant_stats["avg_quality"] / variant_stats["total"]
            
            report["prompt_performance"][ptype] = {
                "total_uses": len(entries),
                "success_rate": len(successes) / len(entries) if entries else 0,
                "avg_execution_time": statistics.mean(execution_times) if execution_times else 0,
                "avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                "variants": variants
            }
        
        return report
    
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
    
    def _log_prompt_usage(self, prompt_type: str, variant_name: str, usage_type: str):
        """Log prompt usage for analytics"""
        # This could be expanded to track detailed usage patterns
        pass