"""
EeveeAgent - Enhanced AI Pokemon Task Execution System
Core agent class that builds upon the basic EeveeAnalyzer with advanced capabilities
"""

import os
import sys
import time
import json
import base64
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
    
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool
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
        model: str = "gemini-1.5-flash",
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
        
        # Circuit breaker state for API resilience
        self.api_failure_count = 0
        self.api_failure_threshold = 5
        self.circuit_breaker_reset_time = 300  # 5 minutes
        self.last_failure_time = 0
        self.circuit_breaker_open = False
        
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
        
        # Initialize native Gemini API
        genai.configure(api_key=api_key)
        self.gemini = genai.GenerativeModel(model_name=self.model)
        
        # Define Pokemon controller tool using Google's format
        self.pokemon_function_declaration = FunctionDeclaration(
            name="pokemon_controller",
            description="Control the Pokémon game using a list of button presses.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "button_presses": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right", "a", "b", "start", "select"]
                        },
                        "description": "A list of button presses for the GameBoy."
                    }
                },
                "required": ["button_presses"]
            }
        )
        self.pokemon_tool = Tool(function_declarations=[self.pokemon_function_declaration])
        
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
    
    def _call_gemini_api(self, prompt: str, image_data: str = None, use_tools: bool = False, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Unified Gemini API calling method with smart timeout and rate limiting
        
        Args:
            prompt: Text prompt to send
            image_data: Base64 encoded image data (optional)
            use_tools: Whether to include Pokemon controller tools
            max_tokens: Maximum tokens for response
            
        Returns:
            Dict with 'text', 'button_presses', and 'error' keys
        """
        # Check circuit breaker status
        if self._check_circuit_breaker():
            return {
                "text": "",
                "button_presses": [],
                "error": "API circuit breaker is open - too many recent failures"
            }
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Prepare prompt parts
                prompt_parts = [prompt]
                
                # Add image if provided
                if image_data:
                    prompt_parts.append({
                        "mime_type": "image/jpeg",
                        "data": base64.b64decode(image_data)
                    })
                
                # Call Gemini API with timeout handling
                if use_tools:
                    response = self.gemini.generate_content(
                        prompt_parts,
                        generation_config={"max_output_tokens": max_tokens},
                        tools=[self.pokemon_tool]
                    )
                else:
                    response = self.gemini.generate_content(
                        prompt_parts,
                        generation_config={"max_output_tokens": max_tokens}
                    )
                
                # Process response
                result = {
                    "text": "",
                    "button_presses": [],
                    "error": None
                }
                
                if use_tools and response.candidates and response.candidates[0].content.parts:
                    # Handle tool-enabled response
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            result["text"] = part.text
                        elif part.function_call and part.function_call.name == "pokemon_controller":
                            # Extract button presses
                            for item, button_list in part.function_call.args.items():
                                for button in button_list:
                                    result["button_presses"].append(button.lower())
                else:
                    # Handle text-only response
                    result["text"] = response.text if response.text else ""
                
                # Record successful API call
                self._record_api_success()
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle 429 rate limit errors with smart backoff
                if "429" in error_msg or "rate limit" in error_msg or "quota" in error_msg:
                    retry_delay = self._parse_retry_delay(str(e), base_delay * (2 ** attempt))
                    if self.verbose:
                        print(f"⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay:.1f}s...")
                    time.sleep(retry_delay)
                    continue
                
                # Handle timeout and connection errors  
                elif any(keyword in error_msg for keyword in ["timeout", "connection", "network", "temporarily unavailable"]):
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        if self.verbose:
                            print(f"⚠️ Connection error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay:.1f}s...")
                        time.sleep(retry_delay)
                        continue
                
                # For other errors or final attempt, return error result
                if self.verbose and attempt == max_retries - 1:
                    print(f"❌ API call failed after {max_retries} attempts: {e}")
                
                # Record API failure for circuit breaker
                self._record_api_failure()
                
                return {
                    "text": "",
                    "button_presses": [],
                    "error": str(e)
                }
        
        # This should never be reached, but included for completeness
        self._record_api_failure()
        return {
            "text": "",
            "button_presses": [],
            "error": "Max retries exceeded"
        }
    
    def _parse_retry_delay(self, error_message: str, default_delay: float) -> float:
        """
        Parse retry delay from 429 error response headers
        
        Args:
            error_message: The error message string
            default_delay: Default delay if no specific delay found
            
        Returns:
            Delay in seconds to wait before retry
        """
        import re
        
        # Look for retry-after patterns in error message
        # Common patterns: "retry after 60 seconds", "try again in 30s", etc.
        patterns = [
            r'retry[\s\-_]*after[\s\-_]*(\d+)[\s\-_]*seconds?',
            r'try[\s\-_]*again[\s\-_]*in[\s\-_]*(\d+)[\s\-_]*s',
            r'wait[\s\-_]*(\d+)[\s\-_]*seconds?',
            r'(\d+)[\s\-_]*seconds?[\s\-_]*retry'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message.lower())
            if match:
                try:
                    parsed_delay = float(match.group(1))
                    # Cap delay at reasonable maximum (5 minutes)
                    return min(parsed_delay, 300.0)
                except (ValueError, IndexError):
                    continue
        
        # If no specific delay found, use exponential backoff with jitter
        import random
        jitter = random.uniform(0.8, 1.2)
        return min(default_delay * jitter, 60.0)  # Cap at 1 minute
    
    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker should prevent API calls
        
        Returns:
            True if circuit breaker is open (should prevent calls)
        """
        current_time = time.time()
        
        # Reset circuit breaker if enough time has passed
        if self.circuit_breaker_open and (current_time - self.last_failure_time) > self.circuit_breaker_reset_time:
            self.circuit_breaker_open = False
            self.api_failure_count = 0
            if self.verbose:
                print("🔄 Circuit breaker reset - API calls resumed")
        
        return self.circuit_breaker_open
    
    def _record_api_success(self):
        """Record successful API call and reset failure count"""
        if self.api_failure_count > 0:
            self.api_failure_count = 0
            if self.verbose:
                print("✅ API success - failure count reset")
    
    def _record_api_failure(self):
        """Record API failure and update circuit breaker state"""
        self.api_failure_count += 1
        self.last_failure_time = time.time()
        
        if self.api_failure_count >= self.api_failure_threshold and not self.circuit_breaker_open:
            self.circuit_breaker_open = True
            if self.verbose:
                print(f"🔴 Circuit breaker opened after {self.api_failure_count} failures")
                print(f"   API calls suspended for {self.circuit_breaker_reset_time//60} minutes")
    
    def _init_directories(self):
        """Initialize directory structure"""
        self.eevee_dir = Path(__file__).parent
        self.analysis_dir = self.eevee_dir / "analysis"
        self.memory_dir = self.eevee_dir / "memory"
        self.reports_dir = self.eevee_dir / "reports"
        self.runs_dir = self.eevee_dir / "runs"
        
        # Create directories if they don't exist
        for directory in [self.analysis_dir, self.memory_dir, self.reports_dir, self.runs_dir]:
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
                # Use unified API method
                api_result = self._call_gemini_api(
                    prompt=step_prompt,
                    image_data=game_context["screenshot_data"],
                    use_tools=False,
                    max_tokens=800
                )
                
                if api_result["error"]:
                    step_analysis = f"Error: {api_result['error']}"
                else:
                    step_analysis = api_result["text"] or "No analysis generated"
                
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
            # Use unified API method
            api_result = self._call_gemini_api(
                prompt=analysis_prompt,
                image_data=game_context["screenshot_data"],
                use_tools=False,
                max_tokens=1500
            )
            
            if api_result["error"]:
                raise Exception(api_result["error"])
            
            analysis_text = api_result["text"] or ""
            
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
            # Use unified API method
            api_result = self._call_gemini_api(
                prompt=task_prompt,
                image_data=game_context["screenshot_data"],
                use_tools=False,
                max_tokens=1000
            )
            
            if api_result["error"]:
                return {
                    "status": "failed",
                    "error": api_result["error"],
                    "steps_executed": 0,
                    "method": "basic_analysis"
                }
            
            analysis = api_result["text"] or "No analysis generated"
            
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
    
    def start_continuous_gameplay(self, goal: str, max_turns: int = 100, turn_delay: float = 1.0, session_state: Dict = None) -> Dict[str, Any]:
        """
        Start continuous autonomous Pokemon gameplay loop
        
        Args:
            goal: The game goal to pursue (e.g. "find and win pokemon battles")
            max_turns: Maximum number of turns to execute
            turn_delay: Delay between turns in seconds
            session_state: Interactive session state for pause/resume control
            
        Returns:
            Dict containing gameplay session results
        """
        if self.verbose:
            print(f"🎮 Starting continuous gameplay with goal: {goal}")
            print(f"📊 Max turns: {max_turns}, Turn delay: {turn_delay}s")
        
        # Initialize game loop state
        running = True
        turn = 0
        gameplay_history = []
        
        # Create run directory for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.runs_dir / f"{timestamp}_continuous"
        run_dir.mkdir(exist_ok=True)
        
        # Initialize progress tracking
        progress_file = run_dir / "progress_summary.md"
        
        try:
            while running and turn < max_turns:
                # Check for pause/resume controls if in interactive mode
                if session_state:
                    if session_state.get("paused", False):
                        time.sleep(0.5)  # Check pause state every 500ms
                        continue
                    if not session_state.get("running", True):
                        print("🛑 Stopping continuous gameplay - session ended")
                        break
                
                turn_start_time = time.time()
                print(f"\n🎯 Turn {turn + 1}/{max_turns}")
                
                # Step 1: Capture current game state
                game_context = self._capture_current_context()
                if not game_context.get("screenshot_data"):
                    print("⚠️ Failed to capture screenshot, skipping turn")
                    time.sleep(turn_delay)
                    continue
                
                # Step 2: Get memory summary for context
                memory_summary = ""
                if self.memory:
                    try:
                        memory_context = self.memory.generate_summary()
                        memory_summary = memory_context.get("summary", "")
                    except Exception as e:
                        if self.debug:
                            print(f"⚠️ Memory summary failed: {e}")
                        memory_summary = "No memory context available"
                
                # Step 3: Enhanced prompt with battle memory and expert knowledge
                battle_memory = ""
                if self.memory:
                    try:
                        battle_memory = self.memory.generate_battle_summary()
                    except Exception as e:
                        if self.debug:
                            print(f"⚠️ Battle memory failed: {e}")
                
                ai_prompt = f"""# Pokemon Battle Expert Agent - Continuous Gameplay

**CURRENT GOAL:** {goal}

**RECENT MEMORY CONTEXT:**
{memory_summary}

**BATTLE EXPERIENCE:**
{battle_memory}

**CRITICAL BATTLE NAVIGATION RULES:**

🎯 **MOVE SELECTION PROCESS:**
1. **When you see battle menu** ("FIGHT", "BAG", "POKEMON", "RUN"):
   - Press **["a"]** to select "FIGHT" (usually first option)

2. **When you see move options** (like "GROWL", "THUNDERSHOCK", "TAIL WHIP"):
   - **DO NOT just press A repeatedly**
   - **READ each move name carefully** 
   - **Use DOWN arrow** to navigate to desired move
   - **Then press A** to select it

**Move Navigation Examples:**
- Want move #1 (top): ["a"]
- Want move #2 (second): ["down", "a"] 
- Want THUNDERSHOCK in position 2: ["down", "a"]
- Want move #3 in 2x2 grid: ["right", "a"]

**Type Effectiveness Quick Reference:**
- **THUNDERSHOCK** (Electric) → Super effective vs Flying/Water (like Pidgey, Magikarp)
- **TACKLE/SCRATCH** (Normal) → Reliable neutral damage vs most Pokemon
- **Status moves** (Growl, Tail Whip) → Don't deal damage, avoid in wild battles

**ANALYSIS TASK:**
1. **OBSERVE:** What screen elements are visible? Are there move names displayed?
2. **ANALYZE:** Is this a battle? What Pokemon are involved? What moves are available?
3. **STRATEGIZE:** What's the best action to progress toward your goal?
4. **ACT:** Provide specific button sequence for your chosen action

What do you observe in the current screen? What action will you take next to progress toward your goal?"""
                
                # Step 4: Get AI analysis and action decision using unified API
                try:
                    api_result = self._call_gemini_api(
                        prompt=ai_prompt,
                        image_data=game_context["screenshot_data"], 
                        use_tools=True,
                        max_tokens=1000
                    )
                    
                    if api_result["error"]:
                        print(f"❌ API Error: {api_result['error']}")
                        continue
                    
                    ai_analysis = api_result["text"]
                    button_presses = api_result["button_presses"]
                    
                    if ai_analysis:
                        print(f"🤖 AI: {ai_analysis}")
                    
                    # Step 6: Execute button presses if provided
                    action_result = "No action taken"
                    if button_presses:
                        print(f"🎮 Executing buttons: {button_presses}")
                        if CONTROLLER_TYPE == "skyemu":
                            action_result = self.controller.press_sequence(button_presses, delay_between=2)
                        else:
                            # Execute buttons one by one for standard controller
                            for button in button_presses:
                                success = self.controller.press_button(button)
                                if not success:
                                    action_result = f"Failed to press {button}"
                                    break
                            else:
                                action_result = f"Successfully pressed: {', '.join(button_presses)}"
                        
                        print(f"🎯 Result: {action_result}")
                    else:
                        print("ℹ️ No button presses requested by AI")
                    
                    # Step 7: Detect and store battle outcomes for learning
                    battle_context = self._extract_battle_context(ai_analysis, button_presses)
                    
                    turn_data = {
                        "turn": turn + 1,
                        "timestamp": datetime.now().isoformat(),
                        "goal": goal,
                        "ai_analysis": ai_analysis,
                        "button_presses": button_presses,
                        "action_result": action_result,
                        "screenshot_path": game_context.get("screenshot_path"),
                        "execution_time": time.time() - turn_start_time,
                        "battle_context": battle_context
                    }
                    
                    gameplay_history.append(turn_data)
                    
                    # Store in persistent memory with battle learning
                    if self.memory:
                        try:
                            self.memory.store_gameplay_turn(turn_data)
                            
                            # Store battle-specific learning if this was a battle action
                            if battle_context.get("is_battle_action"):
                                self._store_battle_learning(battle_context, ai_analysis, button_presses)
                                
                        except Exception as e:
                            if self.debug:
                                print(f"⚠️ Failed to store turn in memory: {e}")
                    
                    # Step 8: Update progress file every 5 turns
                    if turn % 5 == 0:
                        self._update_progress_file(progress_file, goal, gameplay_history[-5:])
                    
                except Exception as e:
                    print(f"❌ Error during turn {turn + 1}: {str(e)}")
                    if self.debug:
                        import traceback
                        traceback.print_exc()
                
                # Increment turn and apply delay
                turn += 1
                
                if turn < max_turns:
                    print(f"⏱️ Waiting {turn_delay}s before next turn...")
                    time.sleep(turn_delay)
        
        except KeyboardInterrupt:
            print("\n🛑 Continuous gameplay interrupted by user")
            running = False
        except Exception as e:
            print(f"\n❌ Unexpected error in gameplay loop: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            running = False
        
        finally:
            # Create final progress summary
            self._update_progress_file(progress_file, goal, gameplay_history)
            
            # Save complete session data
            session_file = run_dir / "session_data.json"
            with open(session_file, 'w') as f:
                json.dump({
                    "goal": goal,
                    "total_turns": turn,
                    "max_turns": max_turns,
                    "session_duration": sum(h.get("execution_time", 0) for h in gameplay_history),
                    "gameplay_history": gameplay_history,
                    "final_status": "completed" if turn >= max_turns else "interrupted"
                }, f, indent=2)
            
            print(f"\n✅ Continuous gameplay session completed after {turn} turns")
            print(f"📁 Session data saved to: {run_dir}")
            
            return {
                "status": "completed" if turn >= max_turns else "interrupted",
                "total_turns": turn,
                "max_turns": max_turns,
                "goal": goal,
                "run_directory": str(run_dir),
                "gameplay_history": gameplay_history
            }
    
    def _update_progress_file(self, progress_file: Path, goal: str, recent_turns: List[Dict]):
        """Update the progress summary file with recent gameplay"""
        try:
            if not recent_turns:
                return
            
            # Format recent turns for AI analysis
            turns_text = ""
            for turn_data in recent_turns:
                turns_text += f"Turn {turn_data['turn']}: {turn_data['ai_analysis']}\n"
                if turn_data['button_presses']:
                    turns_text += f"Actions: {', '.join(turn_data['button_presses'])}\n"
                turns_text += f"Result: {turn_data['action_result']}\n\n"
            
            # Ask AI to create progress summary
            prompt = f"""Create a concise progress report for our Pokemon gameplay session.

Current Goal: {goal}

Recent Gameplay Activity:
{turns_text}

Please provide:
1. Current status and achievements
2. Progress toward the goal
3. Key challenges encountered
4. Next steps and strategy

Keep it concise but informative."""

            # Use unified API method (no image needed for progress summary)
            api_result = self._call_gemini_api(
                prompt=prompt,
                image_data=None,
                use_tools=False,
                max_tokens=800
            )
            
            if api_result["error"]:
                summary = f"Error generating summary: {api_result['error']}"
            else:
                summary = api_result["text"] or "No summary generated"
            
            # Write to progress file
            with open(progress_file, 'w') as f:
                f.write(f"# Pokemon Gameplay Progress Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Goal:** {goal}\n\n")
                f.write(f"**Total Turns:** {len(recent_turns)}\n\n")
                f.write(summary)
            
            if self.verbose:
                print(f"📝 Updated progress file: {progress_file}")
                
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to update progress file: {e}")
    
    def _extract_battle_context(self, ai_analysis: str, button_presses: List[str]) -> Dict[str, Any]:
        """Extract battle context from AI analysis for learning"""
        context = {
            "is_battle_action": False,
            "opponent": None,
            "moves_mentioned": [],
            "move_used": None,
            "battle_outcome": None
        }
        
        if not ai_analysis:
            return context
        
        analysis_lower = ai_analysis.lower()
        
        # Detect if this is a battle-related action
        battle_keywords = ["battle", "fight", "thundershock", "tackle", "scratch", "growl", "tail whip", "caterpie", "pidgey", "vs", "hp"]
        if any(keyword in analysis_lower for keyword in battle_keywords):
            context["is_battle_action"] = True
        
        # Extract opponent Pokemon if mentioned
        pokemon_names = ["caterpie", "pidgey", "rattata", "weedle", "pikachu", "metapod", "kakuna"]
        for pokemon in pokemon_names:
            if pokemon in analysis_lower:
                context["opponent"] = pokemon.title()
                break
        
        # Extract moves mentioned in analysis
        move_names = ["thundershock", "tackle", "scratch", "growl", "tail whip", "ember", "vine whip"]
        for move in move_names:
            if move in analysis_lower:
                context["moves_mentioned"].append(move.title())
        
        # Determine which move was likely used based on button sequence and analysis
        if button_presses and context["is_battle_action"]:
            if button_presses == ["a"]:
                # First move (top-left) was selected
                if "thundershock" in analysis_lower:
                    context["move_used"] = "Thundershock"
                elif "tackle" in analysis_lower:
                    context["move_used"] = "Tackle"
                else:
                    context["move_used"] = "First move"
            elif button_presses == ["down", "a"]:
                # Second move was selected
                if "thundershock" in analysis_lower:
                    context["move_used"] = "Thundershock"
                else:
                    context["move_used"] = "Second move"
        
        # Detect battle outcomes
        outcome_keywords = {
            "victory": ["won", "defeated", "fainted", "victory", "gained exp"],
            "ongoing": ["battle", "attack", "use", "hp"],
            "lost": ["lost", "my pokemon fainted", "returned to pokeball"]
        }
        
        for outcome, keywords in outcome_keywords.items():
            if any(keyword in analysis_lower for keyword in keywords):
                context["battle_outcome"] = outcome
                break
        
        return context
    
    def _store_battle_learning(self, battle_context: Dict[str, Any], ai_analysis: str, button_presses: List[str]):
        """Store battle learning in memory for future reference"""
        if not self.memory or not battle_context.get("is_battle_action"):
            return
        
        try:
            # Store move effectiveness if we have enough context
            if battle_context.get("move_used") and battle_context.get("opponent"):
                move = battle_context["move_used"]
                opponent = battle_context["opponent"]
                outcome = battle_context.get("battle_outcome", "ongoing")
                
                effectiveness_note = f"Used {move} vs {opponent}. Buttons: {button_presses}. Outcome: {outcome}"
                
                # Determine effectiveness based on context
                effectiveness = "unknown"
                if "super effective" in ai_analysis.lower():
                    effectiveness = "super_effective"
                elif "not very effective" in ai_analysis.lower():
                    effectiveness = "not_very_effective" 
                elif outcome == "victory":
                    effectiveness = "effective"
                
                self.memory.store_move_effectiveness(
                    move_name=move,
                    move_type="unknown",  # Could be enhanced to detect type
                    target_type=opponent,
                    effectiveness=effectiveness,
                    button_sequence=button_presses
                )
            
            # Store general battle strategy learning
            if battle_context.get("battle_outcome") == "victory":
                strategy_note = f"Successful battle strategy: {ai_analysis[:100]}... Buttons used: {button_presses}"
                self.memory.store_learned_knowledge(
                    knowledge_type="battle_strategy",
                    subject="successful_battle",
                    content=strategy_note,
                    confidence_score=0.8
                )
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ Failed to store battle learning: {e}")