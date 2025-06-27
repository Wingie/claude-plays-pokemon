"""
TaskExecutor - Multi-step Task Execution Engine for Eevee
Handles complex task decomposition, execution planning, and step-by-step task completion

Enhanced with Goal-Oriented Planning System:
- Hierarchical goal decomposition (Goal → Task → Action) 
- Autonomous goal discovery and navigation
- Dynamic replanning based on progress
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict

class StepStatus(Enum):
    """Status of individual execution steps"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"        # 1-2 steps, direct execution
    MODERATE = "moderate"    # 3-5 steps, some navigation
    COMPLEX = "complex"      # 6-10 steps, multiple menus
    ADVANCED = "advanced"    # 10+ steps, complex strategy

@dataclass
class Goal:
    """
    Simplified goal data structure for AI-driven planning
    
    Represents a goal that will be evaluated by AI during episode reviews:
    - Goal: High-level objective (e.g., "defeat brock")
    - AI evaluates progress and suggests new goals during reviews
    """
    id: str
    name: str
    description: str
    priority: int = 5  # 1-10 scale, 10 = highest
    
    # Hierarchy
    parent_id: Optional[str] = None
    children: List['Goal'] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    # Progress tracking
    progress_percentage: float = 0.0
    attempts: int = 0
    turns_spent: int = 0
    estimated_turns: int = 10
    
    # Context requirements for execution
    context_requirements: List[str] = field(default_factory=list)
    
    # Success/failure criteria
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    failure_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class GoalHierarchy:
    """
    Manages hierarchical goal structure for autonomous planning
    """
    root_goal: Goal
    active_goal: Optional[Goal] = None
    completed_goals: List[Goal] = field(default_factory=list)
    failed_goals: List[Goal] = field(default_factory=list)
    total_goals: int = 0
    
    def get_current_goal(self) -> Optional[Goal]:
        """Get the current goal that should be executed"""
        return self.active_goal or self.root_goal
    
    def mark_goal_completed(self, goal_id: str):
        """Mark a goal as completed and update hierarchy"""
        goal = self.find_goal_by_id(goal_id)
        if goal:
            # Goal status simplified - removed enum usage
            goal.progress_percentage = 100.0
            goal.updated_at = datetime.now().isoformat()
            self.completed_goals.append(goal)
            
            # Find next goal to activate
            self._activate_next_goal()
    
    def find_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """Find goal by ID in the hierarchy"""
        return self._search_goal_tree(self.root_goal, goal_id)
    
    def _search_goal_tree(self, goal: Goal, target_id: str) -> Optional[Goal]:
        """Recursively search goal tree for target ID"""
        if goal.id == target_id:
            return goal
        
        for child in goal.children:
            result = self._search_goal_tree(child, target_id)
            if result:
                return result
        
        return None
    
    def _activate_next_goal(self):
        """Find and activate the next goal to work on"""
        # Simple strategy: find first pending goal with highest priority
        next_goal = self._find_next_actionable_goal(self.root_goal)
        if next_goal:
            if self.active_goal:
                # Deactivate current goal (simplified)
                pass
            
            # Activate next goal (simplified)
            self.active_goal = next_goal
    
    def _find_next_actionable_goal(self, goal: Goal) -> Optional[Goal]:
        """Find next actionable goal (no unmet prerequisites)"""
        # Check if current goal is actionable
        if (True and  # Simplified goal status check 
            self._prerequisites_met(goal)):
            return goal
        
        # Check children (depth-first search for next actionable goal)
        for child in sorted(goal.children, key=lambda g: g.priority, reverse=True):
            result = self._find_next_actionable_goal(child)
            if result:
                return result
        
        return None
    
    def _prerequisites_met(self, goal: Goal) -> bool:
        """Check if goal's prerequisites are met"""
        for prereq_id in goal.prerequisites:
            prereq_goal = self.find_goal_by_id(prereq_id)
            if not prereq_goal:  # Simplified prerequisite check
                return False
        return True

class TaskExecutor:
    """Advanced task execution engine with multi-step planning and execution"""
    
    def __init__(self, eevee_agent):
        """
        Initialize task executor with reference to main Eevee agent
        
        Args:
            eevee_agent: Main EeveeAgent instance for accessing AI and controller
        """
        self.agent = eevee_agent
        self.current_execution = None
        self.step_history = []
        
        # Goal-oriented planning
        self.current_goal_hierarchy: Optional[GoalHierarchy] = None
        self.goal_templates = self._load_goal_templates()
        
        # Execution configuration
        self.max_retries_per_step = 3
        self.step_timeout = 30.0  # seconds
        self.screenshot_interval = 2.0  # seconds between screenshots
        
        # Navigation and menu awareness
        self.menu_stack = []  # Track menu navigation state
        self.last_known_state = {}
        
    def execute_task(self, task: str, max_steps: int = 20) -> Dict[str, Any]:
        """
        Execute a task from string description
        
        Args:
            task: Task description string (e.g., "test compact memory")
            max_steps: Maximum execution steps
            
        Returns:
            Execution result dictionary with success status and details
        """
        try:
            if self.agent.verbose:
                print(f"🎯 Converting task to execution plan: '{task}'")
            
            # Convert task string to execution plan using task analysis
            execution_plan = self._create_plan_from_task(task)
            
            if not execution_plan:
                return {
                    "success": False,
                    "status": "error",
                    "error": "Failed to create execution plan from task",
                    "steps_completed": 0
                }
            
            # Execute the plan using existing method
            result = self.execute_plan(execution_plan, max_steps)
            
            # Format result for caller expectations
            return {
                "success": result.get("success", False),
                "status": result.get("status", "unknown"), 
                "steps_completed": result.get("steps_completed", 0),
                "execution_time": result.get("execution_time", 0),
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "error", 
                "error": str(e),
                "steps_completed": 0
            }
    
    def _create_plan_from_task(self, task: str) -> Dict[str, Any]:
        """
        Convert task string to execution plan using goal-oriented decomposition
        
        Args:
            task: Task description string (e.g., "defeat brock", "find pewter gym")
            
        Returns:
            Structured execution plan dictionary with goal hierarchy
        """
        try:
            if self.agent.verbose:
                print(f"🧠 Decomposing goal: '{task}' into actionable hierarchy")
            
            # Create goal hierarchy from task description
            goal_hierarchy = self._decompose_task_into_goals(task)
            
            if not goal_hierarchy:
                # Fallback to simple execution plan
                return self._create_simple_execution_plan(task)
            
            # Set current goal hierarchy
            self.current_goal_hierarchy = goal_hierarchy
            
            # Convert goal hierarchy to execution plan format
            execution_plan = self._convert_goals_to_execution_plan(goal_hierarchy)
            
            if self.agent.verbose:
                current_goal = goal_hierarchy.get_current_goal()
                print(f"🎯 Active goal: {current_goal.name if current_goal else 'None'}")
                print(f"📊 Goal hierarchy created with {len(goal_hierarchy.root_goal.children)} subtasks")
            
            return execution_plan
            
        except Exception as e:
            if self.agent.verbose:
                print(f"❌ Goal decomposition failed: {e}")
            return self._create_simple_execution_plan(task)
    
    def _decompose_task_into_goals(self, task: str) -> Optional[GoalHierarchy]:
        """
        Use AI to decompose high-level task into goal hierarchy
        
        Args:
            task: High-level task description
            
        Returns:
            GoalHierarchy with decomposed goals, or None if decomposition fails
        """
        try:
            # Check for common Pokemon goal patterns first
            if self._is_pokemon_battle_goal(task):
                return self._create_battle_goal_hierarchy(task)
            elif self._is_navigation_goal(task):
                return self._create_navigation_goal_hierarchy(task)
            
            # Use AI for complex goal decomposition
            return self._ai_decompose_goal(task)
            
        except Exception as e:
            if self.agent.verbose:
                print(f"⚠️ Goal decomposition error: {e}")
            return None
    
    def _is_pokemon_battle_goal(self, task: str) -> bool:
        """Check if task is a Pokemon battle goal"""
        battle_keywords = ["defeat", "battle", "fight", "beat", "brock", "gym", "leader", "trainer"]
        return any(keyword in task.lower() for keyword in battle_keywords)
    
    def _is_navigation_goal(self, task: str) -> bool:
        """Check if task is a navigation/location goal"""
        nav_keywords = ["find", "go to", "navigate", "reach", "enter", "gym", "center", "city", "route"]
        return any(keyword in task.lower() for keyword in nav_keywords)
    
    def _create_battle_goal_hierarchy(self, task: str) -> GoalHierarchy:
        """Create goal hierarchy for Pokemon battle tasks (e.g., 'defeat brock')"""
        task_lower = task.lower()
        
        # Extract target from task
        if "brock" in task_lower:
            target = "Brock"
            location = "Pewter City Gym"
        else:
            target = "Gym Leader"
            location = "Gym"
        
        # Create root goal
        root_goal = Goal(
            id="defeat_" + target.lower().replace(" ", "_"),
            name=f"Defeat {target}",
            description=task,
            priority=10,
            estimated_turns=50,
            success_criteria={"gym_badge_obtained": True}
        )
        
        # Create subtask goals
        find_gym_goal = Goal(
            id="find_" + location.lower().replace(" ", "_"),
            name=f"Find {location}",
            description=f"Navigate to and locate {location}",
            parent_id=root_goal.id,
            priority=9,
            estimated_turns=20,
            success_criteria={"gym_entrance_found": True}
        )
        
        prepare_team_goal = Goal(
            id="prepare_team",
            name="Prepare Pokemon Team",
            description="Ensure team is ready for battle (healing, levels, type advantages)",
            parent_id=root_goal.id,
            priority=8,
            estimated_turns=15,
            prerequisites=[find_gym_goal.id],
            success_criteria={"team_health_full": True, "team_ready": True}
        )
        
        battle_goal = Goal(
            id="battle_" + target.lower().replace(" ", "_"),
            name=f"Battle {target}",
            description=f"Enter gym and battle {target} to completion",
            parent_id=root_goal.id,
            priority=10,
            estimated_turns=15,
            prerequisites=[find_gym_goal.id, prepare_team_goal.id],
            success_criteria={"battle_won": True}
        )
        
        # Build hierarchy
        root_goal.children = [find_gym_goal, prepare_team_goal, battle_goal]
        
        # Create goal hierarchy
        hierarchy = GoalHierarchy(root_goal=root_goal)
        hierarchy.total_goals = 4
        
        # Activate first goal
        # Goal status simplified - removed enum usage
        hierarchy.active_goal = find_gym_goal
        
        return hierarchy
    
    def _create_navigation_goal_hierarchy(self, task: str) -> GoalHierarchy:
        """Create goal hierarchy for navigation tasks (e.g., 'find pewter gym')"""
        task_lower = task.lower()
        
        # Extract location from task
        if "gym" in task_lower:
            if "pewter" in task_lower:
                location = "Pewter City Gym"
            else:
                location = "Gym"
        elif "center" in task_lower:
            location = "Pokemon Center"
        else:
            location = "Target Location"
        
        # Create root goal
        root_goal = Goal(
            id="navigate_to_" + location.lower().replace(" ", "_"),
            name=f"Navigate to {location}",
            description=task,
            priority=9,
            estimated_turns=25,
            success_criteria={"location_reached": True}
        )
        
        # Create subtask goals
        explore_goal = Goal(
            id="explore_area",
            name="Explore Current Area",
            description="Look around current area to understand layout and find target",
            parent_id=root_goal.id,
            priority=8,
            estimated_turns=10,
            success_criteria={"area_explored": True}
        )
        
        navigate_goal = Goal(
            id="navigate_to_target",
            name="Navigate to Target",
            description=f"Move toward {location} once location is identified",
            parent_id=root_goal.id,
            priority=9,
            estimated_turns=15,
            prerequisites=[explore_goal.id],
            success_criteria={"target_reached": True}
        )
        
        # Build hierarchy
        root_goal.children = [explore_goal, navigate_goal]
        
        # Create goal hierarchy
        hierarchy = GoalHierarchy(root_goal=root_goal)
        hierarchy.total_goals = 3
        
        # Activate first goal
        # Goal status simplified - removed enum usage
        hierarchy.active_goal = explore_goal
        
        return hierarchy
    
    def _ai_decompose_goal(self, task: str) -> Optional[GoalHierarchy]:
        """Use AI to decompose complex or unknown goal types"""
        # This is where we could use the LLM to analyze and decompose arbitrary goals
        # For now, create a simple general hierarchy
        
        root_goal = Goal(
            id="general_task",
            name=task,
            description=f"Complete general task: {task}",
            priority=8,
            estimated_turns=20,
            success_criteria={"task_completed": True}
        )
        
        # Single-goal hierarchy for general tasks
        hierarchy = GoalHierarchy(root_goal=root_goal)
        hierarchy.total_goals = 1
        hierarchy.active_goal = root_goal
        # Goal status simplified - removed enum usage
        
        return hierarchy
    
    def _convert_goals_to_execution_plan(self, goal_hierarchy: GoalHierarchy) -> Dict[str, Any]:
        """Convert goal hierarchy to execution plan format"""
        current_goal = goal_hierarchy.get_current_goal()
        
        if not current_goal:
            return self._create_simple_execution_plan("No active goal")
        
        return {
            "task": current_goal.name,
            "goal_id": current_goal.id,
            "description": current_goal.description,
            "complexity": self._estimate_complexity(current_goal),
            "estimated_steps": max(1, current_goal.estimated_turns // 10),  # Convert turns to steps
            "goal_hierarchy": asdict(goal_hierarchy.root_goal),
            "active_goal": asdict(current_goal),
            "steps": [
                {
                    "description": current_goal.description,
                    "action_type": "goal_oriented_execution",
                    "goal_context": current_goal.name,
                    "expected_outcome": "Progress toward goal completion"
                }
            ]
        }
    
    def _estimate_complexity(self, goal: Goal) -> str:
        """Estimate task complexity based on goal characteristics"""
        if goal.estimated_turns <= 5:
            return TaskComplexity.SIMPLE.value
        elif goal.estimated_turns <= 15:
            return TaskComplexity.MODERATE.value
        elif goal.estimated_turns <= 30:
            return TaskComplexity.COMPLEX.value
        else:
            return TaskComplexity.ADVANCED.value
    
    def _create_simple_execution_plan(self, task: str) -> Dict[str, Any]:
        """Create simple execution plan for basic tasks"""
        return {
            "task": task,
            "complexity": TaskComplexity.SIMPLE.value,
            "estimated_steps": 1,
            "steps": [
                {
                    "description": f"Execute task: {task}",
                    "action_type": "general",
                    "expected_outcome": "Task completion"
                }
            ]
        }
    
    def _load_goal_templates(self) -> Dict[str, Any]:
        """Load goal templates for common Pokemon scenarios"""
        # For now, return empty dict. Could load from YAML files later
        return {}
        
    def execute_plan(self, execution_plan: Dict[str, Any], max_steps: int = 50) -> Dict[str, Any]:
        """
        Execute a multi-step task plan
        
        Args:
            execution_plan: Plan created by task analysis
            max_steps: Maximum number of steps to execute
            
        Returns:
            Execution result with status, analysis, and step details
        """
        start_time = time.time()
        
        # Initialize execution context
        execution_context = {
            "plan": execution_plan,
            "start_time": start_time,
            "max_steps": max_steps,
            "steps_completed": 0,
            "current_step": 0,
            "status": "in_progress",
            "results": [],
            "errors": [],
            "screenshots": []
        }
        
        self.current_execution = execution_context
        
        try:
            if self.agent.verbose:
                print(f"🚀 Starting task execution: {execution_plan.get('task', 'Unknown')}")
                print(f"📋 Plan complexity: {execution_plan.get('complexity', 'unknown')}")
                print(f"📊 Estimated steps: {execution_plan.get('estimated_steps', 1)}")
            
            # Get the steps from the plan
            steps = execution_plan.get("steps", [])
            if not steps:
                return self._create_error_result("No execution steps found in plan")
            
            # Execute each step
            for step_index, step in enumerate(steps):
                if step_index >= max_steps:
                    break
                
                execution_context["current_step"] = step_index
                
                if self.agent.verbose:
                    print(f"\n🔄 Step {step_index + 1}/{len(steps)}: {step.get('description', 'Unknown step')}")
                
                # Execute the step
                step_result = self._execute_step(step, step_index)
                execution_context["results"].append(step_result)
                
                # Check step result
                if step_result["status"] == StepStatus.COMPLETED.value:
                    execution_context["steps_completed"] += 1
                    if self.agent.verbose:
                        print(f"✅ Step {step_index + 1} completed")
                elif step_result["status"] == StepStatus.FAILED.value:
                    execution_context["errors"].append(step_result)
                    if self.agent.verbose:
                        print(f"❌ Step {step_index + 1} failed: {step_result.get('error', 'Unknown error')}")
                    
                    # Decide whether to continue or abort
                    if not self._should_continue_after_failure(step_result, execution_context):
                        break
                
                # Small delay between steps
                time.sleep(0.5)
            
            # Finalize execution
            execution_context["status"] = self._determine_final_status(execution_context)
            execution_context["execution_time"] = time.time() - start_time
            
            return self._format_execution_result(execution_context)
            
        except Exception as e:
            return self._create_error_result(f"Task execution failed: {str(e)}")
        finally:
            self.current_execution = None
    
    def _execute_step(self, step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Execute a single step in the task plan
        
        Args:
            step: Step definition from execution plan
            step_index: Index of current step
            
        Returns:
            Step execution result
        """
        step_start_time = time.time()
        step_result = {
            "step_index": step_index,
            "step": step,
            "status": StepStatus.IN_PROGRESS.value,
            "start_time": step_start_time,
            "attempts": 0,
            "screenshots": [],
            "analysis": "",
            "actions_taken": []
        }
        
        try:
            # Determine step type and execute accordingly
            action_type = step.get("action", "analyze_and_execute")
            
            if action_type == "analyze_screen":
                result = self._execute_analysis_step(step)
            elif action_type == "navigate_menu":
                result = self._execute_navigation_step(step)
            elif action_type == "press_buttons":
                result = self._execute_button_step(step)
            elif action_type == "check_condition":
                result = self._execute_condition_step(step)
            else:
                # Default: analyze and execute
                result = self._execute_analysis_and_action_step(step)
            
            # Update step result
            step_result.update(result)
            step_result["execution_time"] = time.time() - step_start_time
            
            return step_result
            
        except Exception as e:
            step_result["status"] = StepStatus.FAILED.value
            step_result["error"] = str(e)
            step_result["execution_time"] = time.time() - step_start_time
            return step_result
    
    def _execute_analysis_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a coordinate-aware screen analysis step"""
        # Capture current screen with coordinate overlay
        context = self.agent._capture_current_context()
        
        try:
            # Use coordinate-aware prompt from prompt manager
            from prompt_manager import PromptManager
            
            prompt_manager = PromptManager()
            
            # Build variables for exploration_strategy template
            template_vars = {
                "task": step.get("description", "analyze current area"),
                "recent_actions": "[]",  # TODO: Pass real recent actions
                "visual_analysis_json": "{}",  # Empty JSON as fallback
                "current_goal_name": "analyze current area",
                "current_map_id": 0,  # Will use fallback - main flow gets real data
                "current_x": 0,       # Will use fallback - main flow gets real data
                "current_y": 0        # Will use fallback - main flow gets real data
            }
            
            # Get coordinate-aware prompt
            strategic_prompt = prompt_manager.get_prompt("exploration_strategy", template_vars)
            
            # Use centralized LLM API for strategic analysis
            from llm_api import call_llm
            
            llm_response = call_llm(
                prompt=strategic_prompt,
                image_data=context["screenshot_data"],
                max_tokens=800,
                model="mistral-large-latest"  # Use strategic model
            )
            
            if llm_response.error:
                raise Exception(f"LLM API error: {llm_response.error}")
            
            analysis = llm_response.text or "No analysis generated"
            
            return {
                "status": StepStatus.COMPLETED.value,
                "analysis": analysis,
                "screenshot_path": context["screenshot_path"],
                "actions_taken": ["coordinate_aware_analysis"]
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Coordinate analysis failed: {str(e)}"
            }
    
    def _execute_navigation_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a menu navigation step"""
        target_menu = step.get("target", "unknown")
        navigation_sequence = step.get("sequence", [])
        
        actions_taken = []
        
        try:
            # Execute navigation sequence
            for action in navigation_sequence:
                if action == "open_menu":
                    self.agent.controller.press_button('start')
                    actions_taken.append("pressed_start")
                elif action == "close_menu":
                    self.agent.controller.press_button('b')
                    actions_taken.append("pressed_b")
                elif action in ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']:
                    self.agent.controller.press_button(action)
                    actions_taken.append(f"pressed_{action}")
                
                time.sleep(0.3)  # Small delay between button presses
            
            # Verify we reached the target menu
            time.sleep(1)  # Wait for menu to stabilize
            context = self.agent._capture_current_context()
            
            return {
                "status": StepStatus.COMPLETED.value,
                "analysis": f"Navigation sequence completed for {target_menu}",
                "actions_taken": actions_taken,
                "screenshot_path": context["screenshot_path"]
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Navigation failed: {str(e)}",
                "actions_taken": actions_taken
            }
    
    def _execute_button_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a button press step"""
        buttons = step.get("buttons", [])
        
        actions_taken = []
        
        try:
            for button in buttons:
                self.agent.controller.press_button(button)
                actions_taken.append(f"pressed_{button}")
                time.sleep(0.3)
            
            return {
                "status": StepStatus.COMPLETED.value,
                "analysis": f"Button sequence completed: {buttons}",
                "actions_taken": actions_taken
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Button press failed: {str(e)}",
                "actions_taken": actions_taken
            }
    
    def _execute_condition_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a condition checking step"""
        condition = step.get("condition", "unknown")
        
        # Capture current state
        context = self.agent._capture_current_context()
        
        # Check condition using AI analysis
        condition_prompt = f"""Check if this condition is met in the Pokemon game:

CONDITION: {condition}

Look at the current screen and determine if the specified condition is satisfied.
Respond with either "CONDITION_MET" or "CONDITION_NOT_MET" followed by a brief explanation."""
        
        try:
            # Use centralized LLM API for condition checking
            from llm_api import call_llm
            
            llm_response = call_llm(
                prompt=condition_prompt,
                image_data=context["screenshot_data"],
                max_tokens=300,
                model=self.agent.current_model if hasattr(self.agent, 'current_model') else None
            )
            
            if llm_response.error:
                raise Exception(f"LLM API error: {llm_response.error}")
            
            analysis = llm_response.text or ""
            condition_met = "CONDITION_MET" in analysis.upper()
            
            return {
                "status": StepStatus.COMPLETED.value,
                "condition_met": condition_met,
                "analysis": analysis,
                "screenshot_path": context["screenshot_path"],
                "actions_taken": ["condition_check"]
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Condition check failed: {str(e)}"
            }
    
    def _execute_analysis_and_action_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simplified screenshot->strategy->action flow"""
        # SIMPLIFIED FLOW: Screenshot -> Strategy -> Action
        context = self.agent._capture_current_context()
        
        try:
            # Use coordinate-aware exploration_strategy prompt directly
            from prompt_manager import PromptManager
            
            prompt_manager = PromptManager()
            
            # Build variables for exploration_strategy template
            current_goal = "explore"
            if hasattr(self, 'goal_hierarchy') and self.goal_hierarchy:
                current_goal = self.goal_hierarchy.get_current_goal().name
            
            template_vars = {
                "task": step.get("description", current_goal),
                "recent_actions": "[]",
                "visual_analysis_json": "{}",
                "current_goal_name": current_goal,
                "current_map_id": 0,  # Will use fallback - main flow gets real data
                "current_x": 0,       # Will use fallback - main flow gets real data  
                "current_y": 0        # Will use fallback - main flow gets real data
            }
            
            # Get strategic prompt that outputs JSON with either button_presses or target_coordinates
            strategic_prompt = prompt_manager.get_prompt("exploration_strategy", template_vars)
            
            # Use strategic model (Mistral) for decision making
            from llm_api import call_llm
            
            llm_response = call_llm(
                prompt=strategic_prompt,
                image_data=context["screenshot_data"],
                max_tokens=800,
                model="mistral-large-latest"
            )
            
            if llm_response.error:
                raise Exception(f"Strategic LLM API error: {llm_response.error}")
            
            # Parse JSON response and execute actions
            response_text = llm_response.text or ""
            actions_taken = self._parse_and_execute_strategic_response(response_text)
            
            return {
                "status": StepStatus.COMPLETED.value,
                "analysis": response_text,
                "actions_taken": actions_taken,
                "screenshot_path": context["screenshot_path"],
                "execution_method": "simplified_strategic_flow"
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Strategic flow failed: {str(e)}"
            }
    
    def _build_step_analysis_prompt(self, step: Dict[str, Any], context: Dict) -> str:
        """Build prompt for step analysis"""
        return f"""Analyze the current Pokemon game screen for this specific step:

STEP: {step.get('description', 'Unknown step')}
ACTION TYPE: {step.get('action', 'analyze_and_execute')}

Provide detailed analysis of what's currently visible on screen and how it relates to completing this step.

If this step requires specific actions, describe what should be done next."""
    
    def _build_action_prompt(self, step: Dict[str, Any], context: Dict) -> str:
        """Build prompt for analysis and action step"""
        return f"""Analyze this Pokemon game screen and recommend actions for this step:

STEP OBJECTIVE: {step.get('description', 'Unknown objective')}

Current Context:
- Step in larger task: {self.current_execution.get('plan', {}).get('task', 'Unknown task')}
- Step number: {self.current_execution.get('current_step', 0) + 1}

Please:
1. Analyze what's currently visible on screen
2. Determine what actions are needed to complete this step
3. Recommend specific button presses or navigation steps
4. Identify any potential issues or obstacles

If immediate action is needed, include specific button recommendations like:
- "Press START to open menu"
- "Press UP to select Pokemon"
- "Press A to confirm"

Be specific and actionable in your recommendations."""
    
    def _parse_and_execute_actions(self, analysis: str) -> List[str]:
        """Parse action recommendations from AI analysis and execute them"""
        actions_taken = []
        
        # Look for common action patterns in the analysis
        analysis_lower = analysis.lower()
        
        # Basic action parsing - can be enhanced with more sophisticated NLP
        if "press start" in analysis_lower or "open menu" in analysis_lower:
            self.agent.controller.press_button('start')
            actions_taken.append("pressed_start")
            time.sleep(0.5)
        
        if "press a" in analysis_lower and "confirm" in analysis_lower:
            self.agent.controller.press_button('a')
            actions_taken.append("pressed_a")
            time.sleep(0.5)
        
        if "press b" in analysis_lower and ("back" in analysis_lower or "cancel" in analysis_lower):
            self.agent.controller.press_button('b')
            actions_taken.append("pressed_b")
            time.sleep(0.5)
        
        # Directional movements
        for direction in ['up', 'down', 'left', 'right']:
            if f"press {direction}" in analysis_lower:
                self.agent.controller.press_button(direction)
                actions_taken.append(f"pressed_{direction}")
                time.sleep(0.3)
        
        return actions_taken
    
    def _parse_and_execute_strategic_response(self, response_text: str) -> List[str]:
        """Parse strategic JSON response and execute actions"""
        actions_taken = []
        
        try:
            # Try to parse JSON response
            import json
            import re
            
            # Extract JSON from response text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            json_str = json_match.group(0)
            response_data = json.loads(json_str)
            
            # Handle button_presses (manual movement)
            if "button_presses" in response_data:
                buttons = response_data["button_presses"]
                if isinstance(buttons, list):
                    for button in buttons:
                        if button in ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']:
                            self.agent.controller.press_button(button)
                            actions_taken.append(f"pressed_{button}")
                            time.sleep(0.3)
            
            # Handle target_coordinates (coordinate navigation)
            elif "target_coordinates" in response_data:
                coords = response_data["target_coordinates"]
                print("** RECEIVED REQUEST TO PATHFIND! ***",coords)
                if isinstance(coords, dict) and "x" in coords and "y" in coords:
                    # Execute coordinate navigation
                    success = self.agent.navigate_to_coordinates(coords["x"], coords["y"])
                    if success:
                        actions_taken.append(f"navigated_to_{coords['x']}_{coords['y']}")
                    else:
                        actions_taken.append("navigation_failed")
                        print("#### pathfinder script fails but triggered to {coords} #####")
            
            else:
                # No valid action found, fallback to text parsing
                actions_taken = self._parse_and_execute_actions(response_text)
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback to text-based action parsing
            actions_taken = self._parse_and_execute_actions(response_text)
        
        return actions_taken
    
    def _should_continue_after_failure(self, step_result: Dict, execution_context: Dict) -> bool:
        """Determine if execution should continue after a step failure"""
        # Simple logic - can be enhanced with more sophisticated error recovery
        
        # Always stop if we've had too many consecutive failures
        recent_failures = sum(1 for result in execution_context["results"][-3:] 
                            if result.get("status") == StepStatus.FAILED.value)
        
        if recent_failures >= 2:
            return False
        
        # Continue for non-critical steps
        step = step_result.get("step", {})
        if step.get("critical", True):  # Default to critical
            return False
        
        return True
    
    def _determine_final_status(self, execution_context: Dict) -> str:
        """Determine final execution status"""
        results = execution_context["results"]
        
        if not results:
            return "failed"
        
        completed_steps = sum(1 for r in results if r.get("status") == StepStatus.COMPLETED.value)
        failed_steps = sum(1 for r in results if r.get("status") == StepStatus.FAILED.value)
        
        # Success if majority of steps completed
        if completed_steps > failed_steps and completed_steps > 0:
            return "success"
        elif completed_steps > 0:
            return "partial_success"
        else:
            return "failed"
    
    def _format_execution_result(self, execution_context: Dict) -> Dict[str, Any]:
        """Format execution context into final result"""
        plan = execution_context["plan"]
        results = execution_context["results"]
        
        # Combine all analysis from steps
        combined_analysis = []
        for i, result in enumerate(results):
            if result.get("analysis"):
                combined_analysis.append(f"Step {i+1}: {result['analysis']}")
        
        return {
            "status": execution_context["status"],
            "task": plan.get("task", "Unknown task"),
            "steps_executed": execution_context["steps_completed"],
            "total_steps": len(plan.get("steps", [])),
            "execution_time": execution_context.get("execution_time", 0),
            "analysis": "\n\n".join(combined_analysis),
            "step_details": results,
            "method": "multi_step_execution"
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result dictionary"""
        return {
            "status": "error",
            "error": error_message,
            "steps_executed": 0,
            "execution_time": 0,
            "method": "task_executor"
        }
    
    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        if self.current_execution:
            return {
                "is_executing": True,
                "current_step": self.current_execution["current_step"],
                "steps_completed": self.current_execution["steps_completed"],
                "status": self.current_execution["status"],
                "elapsed_time": time.time() - self.current_execution["start_time"]
            }
        else:
            return {"is_executing": False}
    
    def abort_execution(self) -> bool:
        """Abort current execution"""
        if self.current_execution:
            self.current_execution["status"] = "aborted"
            return True
        return False