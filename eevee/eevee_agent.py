"""
EeveeAgent - Enhanced AI Pokemon Task Execution System
Core agent class that builds upon the basic EeveeAnalyzer with advanced capabilities
"""

import os
import sys
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    # Try to import SkyEmu controller first, fallback to regular controller
    try:
        from skyemu_controller import SkyEmuController, read_image_to_base64
        CONTROLLER_TYPE = "skyemu"
        print("🚀 Using SkyEmu controller")
    except ImportError:
        from pokemon_controller import PokemonController, read_image_to_base64
        CONTROLLER_TYPE = "pokemon"
        print("🔄 Using standard Pokemon controller")
    
    from gemini_api import GeminiAPI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

class EeveeAgent:
    """Enhanced Eevee AI agent for complex Pokemon task execution"""
    
    def __init__(
        self, 
        window_title: str = "mGBA - 0.10.5",
        model: str = "gemini-flash-2.0-exp",
        memory_session: str = "default",
        verbose: bool = False,
        debug: bool = False,
        enable_neo4j: bool = False
    ):
        """Initialize the enhanced Eevee agent"""
        self.window_title = window_title
        self.model = model
        self.memory_session = memory_session
        self.verbose = verbose
        self.debug = debug
        self.enable_neo4j = enable_neo4j
        
        # Initialize core components
        self._init_ai_components()
        self._init_directories()
        self._init_game_controller()
        
        # Task execution state
        self.current_task = None
        self.execution_history = []
        self.context_memory = {}
        
        if self.verbose:
            print(f"🔮 EeveeAgent initialized")
            print(f"   Model: {self.model}")
            print(f"   Memory Session: {self.memory_session}")
            print(f"   Window: {self.window_title}")
    
    def _init_ai_components(self):
        """Initialize AI components and APIs"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.gemini = GeminiAPI(api_key)
        
        # Initialize memory system when available
        try:
            from memory_system import MemorySystem
            self.memory = MemorySystem(self.memory_session, enable_neo4j=self.enable_neo4j)
        except ImportError:
            self.memory = None
            if self.debug:
                print("⚠️  MemorySystem not available, using basic memory")
        
        # Initialize prompt manager when available
        try:
            from prompt_manager import PromptManager
            self.prompt_manager = PromptManager()
        except ImportError:
            self.prompt_manager = None
            if self.debug:
                print("⚠️  PromptManager not available, using basic prompts")
        
        # Initialize task executor when available
        try:
            from task_executor import TaskExecutor
            self.task_executor = TaskExecutor(self)
        except ImportError:
            self.task_executor = None
            if self.debug:
                print("⚠️  TaskExecutor not available, using basic execution")
    
    def _init_directories(self):
        """Initialize directory structure"""
        self.eevee_dir = Path(__file__).parent
        self.analysis_dir = self.eevee_dir / "analysis"
        self.memory_dir = self.eevee_dir / "memory"
        self.reports_dir = self.eevee_dir / "reports"
        
        # Create directories if they don't exist
        for directory in [self.analysis_dir, self.memory_dir, self.reports_dir]:
            directory.mkdir(exist_ok=True)
    
    def _init_game_controller(self):
        """Initialize Pokemon game controller"""
        if CONTROLLER_TYPE == "skyemu":
            # Use SkyEmu HTTP controller
            self.controller = SkyEmuController()
            
            # Test SkyEmu connection
            if not self.controller.is_connected():
                print(f"⚠️  Warning: SkyEmu server not connected")
                print("   Make sure SkyEmu is running with HTTP server enabled")
                print("   Default connection: localhost:8080")
        else:
            # Use standard Pokemon controller
            self.controller = PokemonController(window_title=self.window_title)
            
            # Test game connection
            window = self.controller.find_window()
            if not window:
                print(f"⚠️  Warning: Pokemon game window not found")
                print(f"   Looking for: {self.window_title}")
                print("   Make sure the emulator is running with a Pokemon game loaded")
    
    def execute_task(self, task_description: str, max_steps: int = 50) -> Dict[str, Any]:
        """
        Execute a complex Pokemon task described in natural language
        
        Args:
            task_description: Natural language description of the task
            max_steps: Maximum number of execution steps
            
        Returns:
            Dict containing execution results, analysis, and metadata
        """
        start_time = time.time()
        self.current_task = task_description
        
        if self.verbose:
            print(f"🎯 Starting task execution: {task_description}")
        
        try:
            # Step 1: Analyze the task and create execution plan
            execution_plan = self._analyze_task(task_description)
            
            if self.verbose:
                print(f"📋 Execution plan created with {len(execution_plan.get('steps', []))} steps")
            
            # Step 2: Execute the plan
            if self.task_executor:
                result = self.task_executor.execute_plan(execution_plan, max_steps)
            else:
                # Fallback to basic execution
                result = self._execute_basic_task(task_description)
            
            # Step 3: Post-process and format results
            result.update({
                "task": task_description,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 4: Update memory with results
            self._update_memory(task_description, result)
            
            return result
            
        except Exception as e:
            error_result = {
                "task": task_description,
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.debug:
                import traceback
                error_result["traceback"] = traceback.format_exc()
            
            return error_result
    
    def execute_task_interruptible(self, task_description: str, max_steps: int = 50, session_state: Dict = None) -> Dict[str, Any]:
        """
        Execute a task with interruption support for interactive mode
        
        Args:
            task_description: Natural language description of the task
            max_steps: Maximum number of execution steps
            session_state: Interactive session state for pause/resume control
            
        Returns:
            Dict containing execution results, analysis, and metadata
        """
        start_time = time.time()
        self.current_task = task_description
        
        if self.verbose:
            print(f"🎯 Starting interruptible task: {task_description}")
        
        try:
            # Step 1: Analyze the task and create execution plan
            execution_plan = self._analyze_task(task_description)
            
            if self.verbose:
                print(f"📋 Execution plan created with {len(execution_plan.get('steps', []))} steps")
            
            # Step 2: Execute the plan with interruption support
            if self.task_executor:
                result = self.task_executor.execute_plan_interruptible(execution_plan, max_steps, session_state)
            else:
                # Fallback to basic interruptible execution
                result = self._execute_basic_task_interruptible(task_description, session_state)
            
            # Step 3: Post-process and format results
            result.update({
                "task": task_description,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "interrupted": session_state.get("paused", False) if session_state else False
            })
            
            # Step 4: Update memory with results
            if not session_state or not session_state.get("paused", False):
                self._update_memory(task_description, result)
            
            return result
            
        except Exception as e:
            error_result = {
                "task": task_description,
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "interrupted": session_state.get("paused", False) if session_state else False
            }
            
            if self.debug:
                import traceback
                error_result["traceback"] = traceback.format_exc()
            
            return error_result
    
    def _execute_basic_task_interruptible(self, task_description: str, session_state: Dict = None) -> Dict[str, Any]:
        """
        Basic interruptible task execution with pause/resume support
        
        Args:
            task_description: Task to execute
            session_state: Session state for pause/resume control
            
        Returns:
            Execution result with interruption awareness
        """
        steps_executed = 0
        max_steps = 10  # Default for basic execution
        results = []
        
        while steps_executed < max_steps:
            # Check for pause/interruption
            if session_state and session_state.get("paused", False):
                print("⏸️  Task execution paused.")
                break
            
            step_num = steps_executed + 1
            print(f"🔮 Eevee: Executing step {step_num}/{max_steps}...")
            
            # Capture current screen for this step
            game_context = self._capture_current_context()
            
            # Check again after potentially long screenshot operation
            if session_state and session_state.get("paused", False):
                print("⏸️  Task execution paused during step.")
                break
            
            # Create step-specific prompt
            step_prompt = self._build_basic_task_prompt(f"Step {step_num}: {task_description}")
            
            try:
                response = self.gemini.messages.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": step_prompt},
                        {
                            "role": "user",
                            "content": [{
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": game_context["screenshot_data"]
                                }
                            }]
                        }
                    ],
                    max_tokens=800
                )
                
                step_analysis = response.content[0].text if response.content else "No analysis generated"
                
                results.append({
                    "step": step_num,
                    "analysis": step_analysis,
                    "timestamp": datetime.now().isoformat(),
                    "screenshot_path": game_context.get("screenshot_path")
                })
                
                steps_executed += 1
                
                # Brief pause between steps to allow for interruption
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error in step {step_num}: {str(e)}"
                results.append({
                    "step": step_num,
                    "analysis": error_msg,
                    "timestamp": datetime.now().isoformat(),
                    "error": True
                })
                break
        
        # Determine final status
        was_paused = session_state and session_state.get("paused", False)
        status = "paused" if was_paused else ("completed" if steps_executed > 0 else "failed")
        
        # Combine all step analyses
        combined_analysis = "\n\n".join([
            f"Step {r['step']}: {r['analysis']}" for r in results if not r.get('error', False)
        ])
        
        return {
            "status": status,
            "analysis": combined_analysis,
            "steps_executed": steps_executed,
            "method": "basic_interruptible",
            "step_details": results,
            "interrupted": was_paused
        }
    
    def _analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze a task description and create an execution plan
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Execution plan with steps and strategies
        """
        # Get current game state context
        game_context = self._capture_current_context()
        
        # Get relevant memory context
        memory_context = self._get_memory_context(task_description)
        
        # Create task analysis prompt
        analysis_prompt = self._build_task_analysis_prompt(
            task_description, 
            game_context, 
            memory_context
        )
        
        try:
            response = self.gemini.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": analysis_prompt},
                    {
                        "role": "user",
                        "content": [{
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": game_context["screenshot_data"]
                            }
                        }]
                    }
                ],
                max_tokens=1500
            )
            
            analysis_text = response.content[0].text if response.content else ""
            
            # Parse the analysis into structured execution plan
            execution_plan = self._parse_execution_plan(analysis_text)
            execution_plan["raw_analysis"] = analysis_text
            
            return execution_plan
            
        except Exception as e:
            if self.debug:
                print(f"⚠️  Task analysis failed: {e}")
            
            # Return basic fallback plan
            return {
                "task": task_description,
                "strategy": "basic_analysis",
                "steps": [{"action": "analyze_screen", "description": "Analyze current game state"}],
                "complexity": "unknown",
                "estimated_steps": 1
            }
    
    def _execute_basic_task(self, task_description: str) -> Dict[str, Any]:
        """
        Basic task execution fallback when TaskExecutor is not available
        
        Args:
            task_description: Task to execute
            
        Returns:
            Basic execution result
        """
        # Capture current screen
        game_context = self._capture_current_context()
        
        # Create task-specific prompt
        task_prompt = self._build_basic_task_prompt(task_description)
        
        try:
            response = self.gemini.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": task_prompt},
                    {
                        "role": "user",
                        "content": [{
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": game_context["screenshot_data"]
                            }
                        }]
                    }
                ],
                max_tokens=1000
            )
            
            analysis = response.content[0].text if response.content else "No analysis generated"
            
            return {
                "status": "completed",
                "analysis": analysis,
                "steps_executed": 1,
                "method": "basic_analysis"
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "steps_executed": 0,
                "method": "basic_analysis"
            }
    
    def _capture_current_context(self) -> Dict[str, Any]:
        """Capture current game state and context"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if CONTROLLER_TYPE == "skyemu":
                # Use SkyEmu screenshot method
                screenshot_file = self.controller.capture_screen(f"eevee_context_{timestamp}.png")
                
                if screenshot_file:
                    # Get image data directly from SkyEmu
                    image_data = self.controller.get_screenshot_base64()
                    
                    return {
                        "timestamp": timestamp,
                        "screenshot_path": screenshot_file,
                        "screenshot_data": image_data,
                        "window_found": self.controller.is_connected(),
                        "controller_type": "skyemu"
                    }
                else:
                    raise Exception("Failed to capture SkyEmu screenshot")
            else:
                # Use standard controller screenshot method
                screenshot_file = self.controller.capture_screen(f"eevee_context_{timestamp}.jpg")
                
                # Move to analysis directory
                analysis_screenshot = self.analysis_dir / f"context_{timestamp}.jpg"
                os.rename(screenshot_file, analysis_screenshot)
                
                # Read image data
                image_data = read_image_to_base64(analysis_screenshot)
                
                return {
                    "timestamp": timestamp,
                    "screenshot_path": str(analysis_screenshot),
                    "screenshot_data": image_data,
                    "window_found": self.controller.find_window() is not None,
                    "controller_type": "pokemon"
                }
            
        except Exception as e:
            if self.debug:
                print(f"⚠️  Failed to capture context: {e}")
            
            return {
                "timestamp": timestamp,
                "screenshot_path": None,
                "screenshot_data": None,
                "window_found": False,
                "controller_type": CONTROLLER_TYPE,
                "error": str(e)
            }
    
    def _get_memory_context(self, task_description: str) -> Dict[str, Any]:
        """Get relevant memory context for the task"""
        if self.memory:
            return self.memory.get_relevant_context(task_description)
        else:
            # Basic memory fallback
            return {
                "session": self.memory_session,
                "relevant_memories": [],
                "game_state": self.context_memory.get("last_known_state", {})
            }
    
    def _update_memory(self, task_description: str, result: Dict[str, Any]):
        """Update memory with task execution results"""
        if self.memory:
            self.memory.store_task_result(task_description, result)
        else:
            # Basic memory storage
            self.context_memory[task_description] = {
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_task_analysis_prompt(self, task: str, game_context: Dict, memory_context: Dict) -> str:
        """Build prompt for task analysis and planning"""
        if self.prompt_manager:
            return self.prompt_manager.get_task_analysis_prompt(task, game_context, memory_context)
        else:
            # Basic prompt fallback
            return f"""Analyze this Pokemon game task and create an execution plan:

TASK: {task}

Current game context:
- Screenshot captured at: {game_context.get('timestamp', 'unknown')}
- Window connection: {'✅' if game_context.get('window_found') else '❌'}

Please analyze the current screen and provide:
1. **Current Game State**: What's visible on screen
2. **Task Understanding**: Break down what needs to be accomplished
3. **Execution Strategy**: Step-by-step approach to complete the task
4. **Potential Challenges**: Any obstacles or considerations
5. **Expected Outcome**: What success looks like

Be specific and actionable in your analysis."""
    
    def _build_basic_task_prompt(self, task: str) -> str:
        """Build prompt for basic task execution"""
        return f"""Execute this Pokemon game task by analyzing the current screen:

TASK: {task}

Provide a detailed analysis focused on this specific task. Look carefully at the screen and provide relevant information that addresses the task requirements.

If additional actions or navigation are needed to complete this task, describe what steps should be taken next.

Format your response with clear sections addressing the task requirements."""
    
    def _parse_execution_plan(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI analysis into structured execution plan"""
        # Basic parsing logic - can be enhanced with more sophisticated NLP
        lines = analysis_text.split('\n')
        
        plan = {
            "task": self.current_task,
            "strategy": "ai_generated",
            "steps": [],
            "complexity": "medium",
            "estimated_steps": 1
        }
        
        # Look for step-like patterns in the analysis
        current_step = 1
        for line in lines:
            line = line.strip()
            if (line.startswith(f"{current_step}.") or 
                line.startswith("Step") or
                line.startswith("-") and len(line) > 10):
                
                plan["steps"].append({
                    "step": current_step,
                    "action": "analyze_and_execute",
                    "description": line,
                    "status": "pending"
                })
                current_step += 1
        
        # If no clear steps found, create a single analysis step
        if not plan["steps"]:
            plan["steps"] = [{
                "step": 1,
                "action": "analyze_task",
                "description": "Analyze current screen and execute task",
                "status": "pending"
            }]
        
        plan["estimated_steps"] = len(plan["steps"])
        
        return plan
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "memory_session": self.memory_session,
            "tasks_executed": len(self.execution_history),
            "current_context": self.context_memory,
            "agent_config": {
                "model": self.model,
                "window_title": self.window_title,
                "verbose": self.verbose
            }
        }
    
    def clear_session(self):
        """Clear current session data"""
        self.execution_history = []
        self.context_memory = {}
        if self.memory:
            self.memory.clear_session()
        
        if self.verbose:
            print(f"🧹 Cleared session: {self.memory_session}")