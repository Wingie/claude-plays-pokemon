"""
TaskExecutor - Multi-step Task Execution Engine for Eevee
Handles complex task decomposition, execution planning, and step-by-step task completion
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

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
        
        # Execution configuration
        self.max_retries_per_step = 3
        self.step_timeout = 30.0  # seconds
        self.screenshot_interval = 2.0  # seconds between screenshots
        
        # Navigation and menu awareness
        self.menu_stack = []  # Track menu navigation state
        self.last_known_state = {}
        
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
        """Execute a screen analysis step"""
        # Capture current screen
        context = self.agent._capture_current_context()
        
        # Get analysis prompt based on step requirements
        analysis_prompt = self._build_step_analysis_prompt(step, context)
        
        try:
            response = self.agent.gemini.messages.create(
                model=self.agent.model,
                messages=[
                    {"role": "user", "content": analysis_prompt},
                    {
                        "role": "user",
                        "content": [{
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": context["screenshot_data"]
                            }
                        }]
                    }
                ],
                max_tokens=800
            )
            
            analysis = response.content[0].text if response.content else "No analysis generated"
            
            return {
                "status": StepStatus.COMPLETED.value,
                "analysis": analysis,
                "screenshot_path": context["screenshot_path"],
                "actions_taken": ["screen_analysis"]
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Analysis failed: {str(e)}"
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
            response = self.agent.gemini.messages.create(
                model=self.agent.model,
                messages=[
                    {"role": "user", "content": condition_prompt},
                    {
                        "role": "user",
                        "content": [{
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": context["screenshot_data"]
                            }
                        }]
                    }
                ],
                max_tokens=300
            )
            
            analysis = response.content[0].text if response.content else ""
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
        """Execute a combined analysis and action step"""
        # This is the most complex step type that combines analysis with action
        context = self.agent._capture_current_context()
        
        # Build comprehensive prompt for analysis and action
        action_prompt = self._build_action_prompt(step, context)
        
        try:
            response = self.agent.gemini.messages.create(
                model=self.agent.model,
                messages=[
                    {"role": "user", "content": action_prompt},
                    {
                        "role": "user",
                        "content": [{
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": context["screenshot_data"]
                            }
                        }]
                    }
                ],
                max_tokens=1000
            )
            
            analysis = response.content[0].text if response.content else ""
            
            # Parse any action recommendations from the analysis
            actions_taken = self._parse_and_execute_actions(analysis)
            
            return {
                "status": StepStatus.COMPLETED.value,
                "analysis": analysis,
                "actions_taken": actions_taken,
                "screenshot_path": context["screenshot_path"]
            }
            
        except Exception as e:
            return {
                "status": StepStatus.FAILED.value,
                "error": f"Analysis and action step failed: {str(e)}"
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