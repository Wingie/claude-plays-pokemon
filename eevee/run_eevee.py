#!/usr/bin/env python3
"""
Eevee v1 - AI Pokemon Task Execution System
Command-line interface for executing Pokemon game tasks via natural language

Default behavior: Continuous gameplay with interactive mode
The AI continuously plays Pokemon while you can give real-time instructions

Usage examples:
    # Default: Continuous gameplay with interactive chat
    python run_eevee.py
    python run_eevee.py --goal "find and win pokemon battles"
    
    # One-shot task mode:
    python run_eevee.py --task "check my Pokemon party status"
    python run_eevee.py --task "navigate to Pokemon Center" --save-report
    
    # Interactive mode with features:
    python run_eevee.py --interactive --enable-okr
    python run_eevee.py --continue  # Resume from last session
"""

import argparse
import sys
import os
import json
import time
import base64
import threading
import queue
import signal
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, asdict, field

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    from eevee_agent import EeveeAgent
    from memory_system import MemorySystem
    from prompt_manager import PromptManager
    from task_executor import TaskExecutor
    # from utils.navigation_enhancement import NavigationEnhancer  # REMOVED - Pure AI autonomy
    from diary_generator import PokemonEpisodeDiary
    from visual_analysis import VisualAnalysis
    from evee_logger import get_comprehensive_logger
    
    # PHASE 2: Memory Integration
    from memory_integration import create_memory_enhanced_eevee
    MEMORY_INTEGRATION_AVAILABLE = True
    
except ImportError as e:
    print(f"WARNING:  Core Eevee components not available: {e}")
    print("Starting with basic implementation...")
    MEMORY_INTEGRATION_AVAILABLE = False
    # We'll implement basic functionality inline if needed

# Get debug logger at top level for clean logging
debug_logger = get_comprehensive_logger()


@dataclass
class LLMInteraction:
    """Represents a single LLM API call with complete details"""
    prompt_sent: str
    raw_response: str
    parsed_result: Dict[str, Any]
    model_used: str
    provider_used: str
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    tokens_used: Optional[Dict[str, int]] = None  # {"input": 100, "output": 50}
    processing_time_ms: Optional[float] = None

@dataclass 
class TurnData:
    """Complete data for a single gameplay turn - designed for fine-tuning dataset creation"""
    turn_number: int
    timestamp: str
    
    # Visual Analysis Stage (Pixtral)
    visual_analysis: Optional[LLMInteraction] = None
    movement_data: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None  # For fine-tuning
    
    # Strategic Decision Stage (mistral-large-latest or other)
    strategic_decision: Optional[LLMInteraction] = None
    memory_context: Optional[str] = None
    template_selected: Optional[str] = None
    template_version: Optional[str] = None
    template_selection_reasoning: Optional[str] = None
    
    # Final Action & Results
    final_button_presses: Optional[List[str]] = None
    action_result: Optional[bool] = None
    execution_time: Optional[str] = None
    
    # Fine-tuning Format
    fine_tuning_entry: Optional[Dict[str, Any]] = None  # Mistral messages format
    
    # Additional Context
    user_task: Optional[str] = None
    escalation_level: Optional[int] = None
    session_goal: Optional[str] = None
    
    # Quality Indicators
    turn_success: bool = True
    include_in_fine_tuning: bool = True
    failure_reason: Optional[str] = None
    
    def __post_init__(self):
        """Automatically create fine-tuning entry if both stages completed successfully"""
        if self.visual_analysis and self.strategic_decision and self.include_in_fine_tuning:
            self._create_fine_tuning_entry()
    
    def _create_fine_tuning_entry(self):
        """Create Mistral fine-tuning format entry from turn data"""
        if not (self.visual_analysis and self.strategic_decision and self.screenshot_base64):
            return
            
        # Create user content with text + image
        user_content = [
            {"type": "text", "text": self.visual_analysis.prompt_sent},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{self.screenshot_base64}"}}
        ]
        
        # Use strategic decision result as assistant response
        assistant_content = self.strategic_decision.parsed_result.get('reasoning', '') + " Action: " + str(self.final_button_presses)
        
        self.fine_tuning_entry = {
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                },
                {
                    "role": "assistant", 
                    "content": assistant_content
                }
            ]
        }

@dataclass
class GameplaySession:
    """Represents a continuous gameplay session with enhanced data collection"""
    session_id: str
    start_time: str
    goal: str
    turns_completed: int = 0
    max_turns: int = 100
    status: str = "running"  # running, paused, completed, error
    last_action: str = ""
    last_analysis: str = ""
    user_interactions: List[str] = None
    
    # Enhanced session data
    turns_data: List[TurnData] = None
    fine_tuning_dataset_path: Optional[str] = None
    total_llm_calls: int = 0
    successful_turns: int = 0
    
    def __post_init__(self):
        if self.user_interactions is None:
            self.user_interactions = []
        if self.turns_data is None:
            self.turns_data = []
    
    def add_turn_data(self, turn_data: TurnData):
        """Add complete turn data to session"""
        self.turns_data.append(turn_data)
        self.turns_completed = len(self.turns_data)
        if turn_data.turn_success:
            self.successful_turns += 1


class InteractiveController:
    """Handles real-time user input during continuous gameplay"""
    
    def __init__(self):
        self.input_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.running = True
        self.paused = False
        
    def start_input_thread(self):
        """Start background thread for user input"""
        self.input_thread = threading.Thread(target=self._input_handler, daemon=True)
        self.input_thread.start()
        
    def _input_handler(self):
        """Background thread that handles user input"""
        print("\n- Interactive mode active. Commands:")
        print("   /pause - Pause gameplay")
        print("   /resume - Resume gameplay") 
        print("   /status - Show current status")
        print("   /help - Show all commands")
        print("   /quit - Exit")
        print("   Or type any task for the AI...")
        
        while self.running:
            try:
                user_input = input("\n- You: ").strip()
                if user_input:
                    self.input_queue.put(user_input)
            except (EOFError, KeyboardInterrupt):
                self.input_queue.put("/quit")
                break
    
    def get_user_input(self) -> Optional[str]:
        """Get user input if available"""
        try:
            return self.input_queue.get_nowait()
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop the interactive controller"""
        self.running = False


class ContinuousGameplay:
    """Manages continuous Pokemon gameplay with AI"""
    
    def __init__(self, eevee_agent: EeveeAgent, interactive: bool = True, episode_review_frequency: int = 100):
        self.eevee = eevee_agent
        self.interactive = interactive
        self.session = None
        self.interactive_controller = None
        self.episode_review_frequency = episode_review_frequency
        
        # Gameplay state
        self.paused = False
        self.running = False
        self.turn_delay = 2.0  # Seconds between turns
        
        # Visual analysis system for movement validation (8x8 grid, every turn)
        try:
            self.visual_analyzer = VisualAnalysis(grid_size=8, save_logs=True)
            self.use_visual_analysis = True
            import os
            provider = os.getenv('LLM_PROVIDER', 'mistral').lower()
            vision_model = 'gemini-2.0-flash-exp' if provider == 'hybrid' else 'pixtral-12b-2409'
            print(f"✅ Visual analysis system initialized ({vision_model} + mistral-large-latest)")
        except Exception as e:
            print(f"WARNING: Visual analysis unavailable: {e}")
            self.visual_analyzer = None
            self.use_visual_analysis = False
        
        # Track recent actions for context (last 5 turns)
        self.recent_turns = []
        self.max_recent_turns = 5
        
        # Set up interrupt handler
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n�  Stopping gameplay...")
        self.running = False
        if self.interactive_controller:
            self.interactive_controller.stop()
    
    def start_session(self, goal: str, max_turns: int = 100) -> GameplaySession:
        """Start a new continuous gameplay session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.session = GameplaySession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            goal=goal,
            max_turns=max_turns
        )
        
        # Create session directory and initialize session data file for episode reviewer
        self.session_dir = self.eevee.runs_dir / f"session_{session_id}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Initialize session data file
        self.session_data_file = self.session_dir / "session_data.json"
        self.session_turns = []  # Track turns for episode reviewer
        
        initial_session_data = {
            "session_id": session_id,
            "goal": goal,
            "start_time": self.session.start_time,
            "turns": []
        }
        
        with open(self.session_data_file, 'w') as f:
            json.dump(initial_session_data, f, indent=2)
        
        # Create Neo4j session for persistent memory
        try:
            from neo4j_singleton import Neo4jSingleton
            neo4j = Neo4jSingleton()
            writer = neo4j.get_writer()
            
            if writer and writer.driver:
                session_data = {
                    "session_id": session_id,
                    "start_time": self.session.start_time,
                    "goal": goal,
                    "max_turns": max_turns,
                    "status": "active"
                }
                success = writer.create_session(session_data)
                if success:
                    print(f"✅ Neo4j session created: {session_id}")
                else:
                    print(f"⚠️ Neo4j session creation failed")
            else:
                print(f"⚠️ Neo4j writer not available")
        except Exception as e:
            print(f"⚠️ Neo4j session creation error: {e}")
        
        print(f"🎮 Starting continuous Pokemon gameplay")
        print(f"📁 Session: {session_id}")
        print(f"- Goal: {goal}")
        print(f"- Max turns: {max_turns}")
        print(f"= Turn delay: {self.turn_delay}s")
        
        if self.interactive:
            self.interactive_controller = InteractiveController()
            self.interactive_controller.start_input_thread()
            print(f"- Interactive mode enabled - type commands anytime")
        
        print("=" * 60)
        
        return self.session
    
    def run_continuous_loop(self) -> Dict[str, Any]:
        """Main continuous gameplay loop"""
        if not self.session:
            raise RuntimeError("No session started. Call start_session() first.")
        
        self.running = True
        turn_count = 0
        
        # Core game loop: screenshot � AI analysis � action � memory � repeat
        while self.running and turn_count < self.session.max_turns:
            turn_count += 1
            
            try:
                # Handle user input if in interactive mode
                if self.interactive and self.interactive_controller:
                    self._handle_user_input()
                
                # Skip turn if paused
                if self.paused:
                    time.sleep(0.5)
                    continue
                
                print(f"\n= Turn {turn_count}/{self.session.max_turns}")
                
                # Step 1: Capture current game state
                game_context = self._capture_game_context()
                # Store for navigation analysis
                self._last_game_context = game_context
                
                # Step 2: Get AI analysis and decision (returns both AI result and movement data)
                ai_result, movement_data = self._get_ai_decision(game_context, turn_count)
                
                # Step 3: Execute AI's chosen action (with movement validation)
                execution_result = self._execute_ai_action(ai_result, movement_data)
                
                # Step 4: Update memory and session state
                self._update_session_state(turn_count, ai_result, execution_result)
                
                # Step 4.0: Store complete turn data in Neo4j for persistent memory
                self._store_complete_turn_data(turn_count, game_context, ai_result, execution_result, movement_data)
                
                # Step 4.1: Update legacy session data for episode reviewer (first)
                self._update_session_data_file(turn_count, ai_result, execution_result)
                
                # Step 4.2: Comprehensive turn data logging (overrides with enhanced data)
                self._log_complete_turn_data(turn_count, game_context, ai_result, execution_result, movement_data)
                
                # Step 4.5: Emergency/Periodic episode review check
                if hasattr(self, 'episode_review_frequency') and self.episode_review_frequency > 0:
                    # EMERGENCY: Check for catastrophic performance needing immediate intervention
                    emergency_review_needed = self._check_emergency_review_needed(turn_count)
                    
                    if emergency_review_needed or turn_count % self.episode_review_frequency == 0:
                        if emergency_review_needed:
                            print(f"\n🚨 EMERGENCY REVIEW TRIGGERED: Catastrophic performance detected at turn {turn_count}")
                        else:
                            print(f"\n📊 PERIODIC REVIEW: Analyzing last {self.episode_review_frequency} turns...")
                        self._run_periodic_episode_review(turn_count)
                
                # Step 5: Wait before next turn
                time.sleep(self.turn_delay)
                
            except Exception as e:
                print(f"L Error in turn {turn_count}: {e}")
                if self.eevee.debug:
                    import traceback
                    traceback.print_exc()
                
                # Continue with next turn
                time.sleep(self.turn_delay)
        
        # Session ended
        self.session.status = "completed" if self.running else "stopped"
        self.session.turns_completed = turn_count
        
        # Generate final fine-tuning dataset
        self._export_fine_tuning_dataset()
        
        return self._get_session_summary()
    
    def _export_fine_tuning_dataset(self):
        """Export session data as JSONL file for Mistral fine-tuning"""
        try:
            if not self.session or not hasattr(self.session, 'turns_data'):
                print("WARNING: No turn data available for export")
                return
            
            # Create runs directory for this session
            runs_dir = Path("runs") / f"session_{self.session.session_id}"
            runs_dir.mkdir(parents=True, exist_ok=True)
            
            # Export JSONL for fine-tuning
            jsonl_path = runs_dir / "fine_tuning_dataset.jsonl"
            quality_turns = [turn for turn in self.session.turns_data if turn.include_in_fine_tuning and turn.fine_tuning_entry]
            
            with open(jsonl_path, 'w') as f:
                for turn in quality_turns:
                    f.write(json.dumps(turn.fine_tuning_entry) + "\n")
            
            print(f"📊 Fine-tuning dataset exported: {len(quality_turns)} turns → {jsonl_path}")
            
            # Export metadata
            metadata = {
                "session_id": self.session.session_id,
                "total_turns": len(self.session.turns_data),
                "quality_turns": len(quality_turns),
                "success_rate": len([t for t in self.session.turns_data if t.turn_success]) / len(self.session.turns_data) if self.session.turns_data else 0,
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(runs_dir / "dataset_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"WARNING: Failed to export fine-tuning dataset: {e}")
    
    def _capture_game_context(self) -> Dict[str, Any]:
        """Capture current game state via screenshot"""
        try:
            # Use SkyEmu controller for screenshot
            screenshot_path = self.eevee.controller.capture_screen()
            
            # Read screenshot as base64 for AI
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "screenshot_path": screenshot_path,
                "screenshot_data": image_data,
                "timestamp": datetime.now().isoformat(),
                "window_found": True
            }
            
        except Exception as e:
            print(f"�  Failed to capture screenshot: {e}")
            return {
                "screenshot_path": None,
                "screenshot_data": None,
                "timestamp": datetime.now().isoformat(),
                "window_found": False,
                "error": str(e)
            }
    
    def _get_ai_decision(self, game_context: Dict[str, Any], turn_number: int) -> tuple:
        """Get AI analysis and action decision with two-stage visual analysis system
        
        Returns:
            tuple: (ai_result_dict, movement_data_dict)
        """
        if not game_context.get("screenshot_data"):
            return {
                "analysis": "No game data available",
                "action": ["b"],  # Default action (safer for menu exit)
                "reasoning": "Screenshot capture failed, using default action"
            }, None
        
        # STAGE 1: Visual Analysis - Movement validation and object detection
        movement_data = None
        if self.use_visual_analysis and self.visual_analyzer:
            try:
                # Get session name for logging
                session_name = getattr(self.session, 'session_id', None)
                
                # Analyze current scene for movement validation
                movement_data = self.visual_analyzer.analyze_current_scene(
                    screenshot_base64=game_context.get("screenshot_data"),
                    verbose=self.eevee.verbose,
                    session_name=session_name
                )
                
                # ENHANCED: Store visual analysis metadata for comprehensive logging
                if movement_data and '_meta' in movement_data:
                    meta = movement_data['_meta']
                    self._last_visual_prompt = meta.get('prompt_sent', '')
                    self._last_visual_response = meta.get('raw_response', '')
                    self._last_visual_processing_time = meta.get('processing_time_ms')
                
                    
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                print(f"WARNING: Visual analysis failed: {e}")
                print(f"💀 CRITICAL: Cannot proceed without visual analysis - terminating script")
                # Clear metadata on failure
                self._last_visual_prompt = ''
                self._last_visual_response = f'Error: {e}'
                self._last_visual_processing_time = None
                # Re-raise the exception to crash the script as required
                raise RuntimeError(f"Visual analysis failure is fatal - cannot proceed without visual data: {e}") from e
        
        # STAGE 2: Strategic Decision (mistral-large-latest) - Build context-aware prompt
        memory_context = self._get_memory_context()
        prompt_data = self._build_ai_prompt(
            turn_number, 
            memory_context, 
            game_context.get("screenshot_data"), 
            movement_data  # Pass movement validation data to prompt builder
        )
        prompt = prompt_data.get("prompt", prompt_data) if isinstance(prompt_data, dict) else prompt_data
        
        # STAGE 2: Strategic Decision (mistral-large-latest) - No image needed, uses movement validation data
        try:
            # Import centralized LLM API
            from llm_api import call_llm
            import time
            
            # Store data for comprehensive logging
            self._last_strategic_prompt = prompt
            strategic_start_time = time.time()
            
            # Use mistral-large-latest for strategic decision making (text-only)
            llm_response = call_llm(
                prompt=prompt,
                image_data=None,  # No image needed - movement validation provides visual analysis
                model="mistral-large-latest",
                provider="mistral",
                max_tokens=1000
            )
            
            # Store additional metadata for logging
            self._last_strategic_response = llm_response.text if hasattr(llm_response, 'text') else str(llm_response)
            self._last_strategic_model = "mistral-large-latest"
            self._last_strategic_provider = "mistral"
            self._last_strategic_processing_time = (time.time() - strategic_start_time) * 1000
            
            # Convert to expected format
            api_result = {
                "error": llm_response.error,
                "text": llm_response.text if hasattr(llm_response, 'text') else str(llm_response),
                "button_presses": None  # Will be extracted from text
            }
            
            # Extract button presses from JSON response (simplified)
            if api_result["text"] and not api_result["error"]:
                import re
                import json
                
                # Parse standardized JSON response
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', api_result["text"], re.DOTALL)
                if json_match:
                    try:
                        json_data = json.loads(json_match.group(1))
                        if "button_presses" in json_data:
                            api_result["button_presses"] = json_data["button_presses"]
                        else:
                            from evee_logger import get_comprehensive_logger
                            debug_logger = get_comprehensive_logger()
                            if debug_logger:
                                debug_logger.log_debug('WARNING', 'No button_presses in JSON response')
                            else:
                                print("WARNING: No button_presses in JSON response")
                            api_result["button_presses"] = ["b"]  # Simple fallback
                    except json.JSONDecodeError as e:
                        from evee_logger import get_comprehensive_logger
                        debug_logger = get_comprehensive_logger()
                        if debug_logger:
                            debug_logger.log_debug('ERROR', f'JSON parsing failed: {e}')
                        else:
                            print(f"WARNING: JSON parsing failed: {e}")
                        api_result["button_presses"] = ["b"]  # Simple fallback
                else:
                    print("WARNING: No JSON format found in response : {0}",api_result["text"])
                    api_result["button_presses"] = ["b"]  # Simple fallback
            
            if api_result["error"]:
                return {
                    "analysis": f"API Error: {api_result['error']}",
                    "action": ["b"],
                    "reasoning": "API call failed, using default action"
                }, movement_data
            
            # Enhanced logging with clear observation-to-action chain
            analysis_text = api_result.get("text", "No analysis provided")
            button_sequence = api_result.get("button_presses", ["a"])
            
            # Always show enhanced analysis logging for better debugging
            self._log_enhanced_analysis(turn_number, analysis_text, button_sequence)
            
            # Add template metadata if available
            result = {
                "analysis": analysis_text,
                "action": button_sequence,
                "reasoning": analysis_text
            }
            
            # Include template metadata if we got it from prompt building
            if isinstance(prompt_data, dict) and "template_used" in prompt_data:
                result["template_used"] = prompt_data["template_used"]
                result["template_version"] = prompt_data.get("template_version", "unknown")
            
            # Clean console output for strategic decisions (if enabled)
            self._log_strategic_decision_clean_output(result)
            
            return result, movement_data
            
        except Exception as e:
            return {
                "analysis": f"Exception: {str(e)}",
                "action": ["b"],
                "reasoning": "Exception occurred, using default action"
            }, movement_data
    
    # Movement validation is now handled in the AI prompt stage
    
    def _execute_ai_action(self, ai_result: Dict[str, Any], movement_data: Dict = None) -> Dict[str, Any]:
        """Execute the AI's chosen action (movement already validated by two-stage system)"""
        actions = ai_result.get("action", ["b"])
        
        if not isinstance(actions, list):
            actions = [actions]
        
        # VALIDATION: Enforce 1-3 button maximum as requested by user
        if len(actions) > 3:
            from evee_logger import get_comprehensive_logger
            debug_logger = get_comprehensive_logger()
            if debug_logger:
                debug_logger.log_debug('WARNING', f'AI tried to press {len(actions)} buttons: {actions}')
                debug_logger.log_debug('WARNING', 'Limiting to first 3 buttons for step-by-step learning')
            else:
                print(f"WARNING: AI tried to press {len(actions)} buttons: {actions}")
                print(f"WARNING: Limiting to first 3 buttons for step-by-step learning")
            actions = actions[:3]
        
        # Additional validation: ensure valid button names
        valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
        validated_actions = []
        for action in actions:
            if isinstance(action, str) and action.lower() in valid_buttons:
                validated_actions.append(action.lower())
            else:
                print(f"WARNING: Invalid button '{action}' ignored")
        
        # Fallback to 'b' if no valid actions (safer default for exiting menus)
        if not validated_actions:
            print(f"WARNING: No valid buttons found, using default 'b' (exit menus)")
            validated_actions = ['b']
        
        # Note: Movement validation is handled in the AI prompt stage, not here
        
        # Note: Loop breaking system removed per user request - AI decisions are now fully respected
        
        try:
            # Execute button sequence
            success = self.eevee.controller.press_sequence(validated_actions, delay_between=0.5)
            
            # Record this turn's action for recent context
            observation = ai_result.get("analysis", "")  # Full observation, no truncation
            result_text = "success" if success else "failed"
            turn_number = getattr(self.session, 'turns_completed', 0) + 1
            self._record_turn_action(turn_number, observation, validated_actions, result_text)
            
            return {
                "success": success,
                "actions_executed": validated_actions,
                "original_actions": actions,  # Keep track of what AI originally wanted
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            from evee_logger import get_comprehensive_logger
            debug_logger = get_comprehensive_logger()
            if debug_logger:
                debug_logger.log_debug('ERROR', f'Action execution failed: {e}')
            else:
                print(f"WARNING:  Action execution failed: {e}")
            return {
                "success": False,
                "actions_executed": [],
                "original_actions": actions,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
    
    def _update_session_state(self, turn_number: int, ai_result: Dict[str, Any], execution_result: Dict[str, Any]):
        """Update session state and memory"""
        self.session.turns_completed = turn_number
        self.session.last_analysis = ai_result.get("analysis", "")
        self.session.last_action = str(ai_result.get("action", []))
        
        # Store in memory if available
        if self.eevee.memory:
            try:
                self.eevee.memory.store_gameplay_turn(
                    turn_number=turn_number,
                    analysis=ai_result.get("analysis", ""),
                    actions=ai_result.get("action", []),
                    success=execution_result.get("success", False),
                    reasoning=ai_result.get("reasoning", "")
                )
            except Exception as e:
                if self.eevee.debug:
                    from evee_logger import get_comprehensive_logger
                    debug_logger = get_comprehensive_logger()
                    if debug_logger:
                        debug_logger.log_debug('ERROR', f'Memory storage failed: {e}')
                    else:
                        print(f"WARNING:  Memory storage failed: {e}")
    
    def _store_complete_turn_data(self, turn_number: int, game_context: Dict[str, Any], 
                                 ai_result: Dict[str, Any], execution_result: Dict[str, Any], 
                                 movement_data: Dict[str, Any] = None):
        """Store complete turn data in Neo4j with all context"""
        try:
            from neo4j_singleton import Neo4jSingleton
            neo4j = Neo4jSingleton()
            writer = neo4j.get_writer()
            
            if not writer or not writer.driver:
                if self.eevee.verbose:
                    print("⚠️ Neo4j writer not available for turn storage")
                return
            
            # Prepare complete turn data
            turn_data = {
                "turn_id": f"{self.session.session_id}_turn_{turn_number}",
                "session_id": self.session.session_id,
                "timestamp": datetime.now().isoformat(),
                "gemini_text": ai_result.get("analysis", ""),
                "button_presses": ai_result.get("action", []),
                "screenshot_path": game_context.get("screenshot_path"),
                "screenshot_base64": game_context.get("screenshot_data"),  # Store base64
                "location": "unknown",  # Visual context contains location info
                "success": execution_result.get("success", False),
                "visual_context": movement_data,  # Contains all visual analysis
                "battle_context": None,  # All context is in visual_context
                "memory_context": getattr(self, '_last_memory_context', None)
            }
            
            success = writer.store_game_turn(turn_data)
            
            if self.eevee.verbose:
                status = "✅ stored" if success else "⚠️ failed to store"
                print(f"Neo4j turn {turn_number}: {status}")
                
        except Exception as e:
            if self.eevee.verbose:
                print(f"⚠️ Neo4j turn storage error: {e}")
    
    def _parse_ai_analysis_json(self, ai_analysis: str) -> Dict[str, Any]:
        """Parse JSON from ai_analysis string into structured data"""
        try:
            import re
            import json
            
            # Extract JSON from markdown code block
            json_match = re.search(r'```json\s*({.*?})\s*```', ai_analysis, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                return {
                    "parsed_json": json_data,
                    "raw_text": ai_analysis,
                    "parsing_success": True
                }
            else:
                return {
                    "parsed_json": None,
                    "raw_text": ai_analysis,
                    "parsing_success": False,
                    "error": "No JSON block found"
                }
        except json.JSONDecodeError as e:
            return {
                "parsed_json": None,
                "raw_text": ai_analysis,
                "parsing_success": False,
                "error": f"JSON parsing failed: {e}"
            }
        except Exception as e:
            return {
                "parsed_json": None,
                "raw_text": ai_analysis,
                "parsing_success": False,
                "error": f"Unexpected error: {e}"
            }
    
    def _update_session_data_file(self, turn_number: int, ai_result: Dict[str, Any], execution_result: Dict[str, Any]):
        """Update legacy session data file for episode reviewer (backward compatibility)"""
        if not hasattr(self, 'session_data_file') or not hasattr(self, 'session_turns'):
            return
        
        try:
            # Parse AI analysis JSON
            ai_analysis_raw = ai_result.get("analysis", "")
            ai_analysis_parsed = self._parse_ai_analysis_json(ai_analysis_raw)
            
            # Create turn data in the format expected by episode reviewer (enhanced legacy format)
            turn_data = {
                "turn": turn_number,
                "timestamp": datetime.now().isoformat(),
                "ai_analysis": ai_analysis_parsed,  # ENHANCED: Structured JSON instead of string
                "button_presses": ai_result.get("action", []),
                "action_result": execution_result.get("success", False),
                "screenshot_path": f"screenshot_{turn_number}.png",
                "execution_time": execution_result.get("execution_time", 0.0),
                "template_used": ai_result.get("template_used", "unknown"),
                "template_version": ai_result.get("template_version", "unknown")
            }
            
            # Add to session turns list
            self.session_turns.append(turn_data)
            
            # Update the session data file
            session_data = {
                "session_id": self.session.session_id,
                "goal": self.session.goal,
                "start_time": self.session.start_time,
                "turns": self.session_turns
            }
            
            with open(self.session_data_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
        except Exception as e:
            if self.eevee.debug:
                print(f"WARNING: Failed to update session data file: {e}")
    
    def _log_complete_turn_data(self, turn_number: int, game_context: Dict[str, Any], 
                               ai_result: Dict[str, Any], execution_result: Dict[str, Any], 
                               movement_data: Dict = None):
        """Log complete turn data for fine-tuning dataset creation"""
        try:
            # Create comprehensive turn data structure
            turn_data = TurnData(
                turn_number=turn_number,
                timestamp=datetime.now().isoformat(),
                
                # Visual Analysis Stage (if available)
                visual_analysis=self._extract_visual_analysis_data(movement_data) if movement_data else None,
                movement_data=movement_data,
                screenshot_path=game_context.get("screenshot_path"),
                screenshot_base64=game_context.get("screenshot_data"),  # For fine-tuning
                
                # Strategic Decision Stage 
                strategic_decision=self._extract_strategic_decision_data(ai_result),
                memory_context=self._get_memory_context(),
                template_selected=ai_result.get("template_used", "unknown"),
                template_version=ai_result.get("template_version", "unknown"),
                template_selection_reasoning=getattr(self, '_last_template_reasoning', None),
                
                # Final Action & Results
                final_button_presses=ai_result.get("action", []),
                action_result=execution_result.get("success", False),
                execution_time=execution_result.get("execution_time"),
                
                # Additional Context
                user_task=getattr(self, '_user_tasks', [])[-1] if hasattr(self, '_user_tasks') and self._user_tasks else None,
                escalation_level=self._get_escalation_level(),
                session_goal=self.session.goal,
                
                # Quality Assessment
                turn_success=self._assess_turn_success(ai_result, execution_result),
                include_in_fine_tuning=self._should_include_in_fine_tuning(ai_result, execution_result, movement_data)
            )
            
            # Add to session
            if not hasattr(self.session, 'turns_data'):
                self.session.turns_data = []
            
            self.session.add_turn_data(turn_data)
            
            # Save enhanced session data to file
            self._save_enhanced_session_data()
            
            if self.eevee.verbose:
                print(f"📊 Turn {turn_number} logged: {len(turn_data.__dict__)} data fields, fine-tuning: {'✅' if turn_data.include_in_fine_tuning else '❌'}")
                
        except Exception as e:
            print(f"WARNING: Failed to log complete turn data: {e}")
            if self.eevee.debug:
                import traceback
                traceback.print_exc()
    
    def _extract_visual_analysis_data(self, movement_data: Dict) -> LLMInteraction:
        """Extract visual analysis data from movement_data for structured logging"""
        if not movement_data or not hasattr(self, '_last_visual_prompt'):
            return None
            
        return LLMInteraction(
            prompt_sent=getattr(self, '_last_visual_prompt', ''),
            raw_response=getattr(self, '_last_visual_response', ''),
            parsed_result=movement_data,
            model_used="pixtral-12b-2409",
            provider_used="mistral",
            timestamp=datetime.now().isoformat(),
            success=bool(movement_data.get('valid_sequences', {}).get('1_move')),
            processing_time_ms=getattr(self, '_last_visual_processing_time', None)
        )
    
    def _extract_strategic_decision_data(self, ai_result: Dict[str, Any]) -> LLMInteraction:
        """Extract strategic decision data for structured logging"""
        return LLMInteraction(
            prompt_sent=getattr(self, '_last_strategic_prompt', ''),
            raw_response=getattr(self, '_last_strategic_response', ai_result.get('analysis', '')),
            parsed_result=ai_result,
            model_used=getattr(self, '_last_strategic_model', 'mistral-large-latest'),
            provider_used=getattr(self, '_last_strategic_provider', 'mistral'),
            timestamp=datetime.now().isoformat(),
            success=bool(ai_result.get('action')),
            processing_time_ms=getattr(self, '_last_strategic_processing_time', None)
        )
    
    def _assess_turn_success(self, ai_result: Dict[str, Any], execution_result: Dict[str, Any]) -> bool:
        """Assess if turn was successful for quality filtering"""
        # Basic success criteria
        has_analysis = bool(ai_result.get('analysis', '').strip())
        has_action = bool(ai_result.get('action'))
        action_executed = execution_result.get('success', False)
        
        return has_analysis and has_action and action_executed
    
    def _should_include_in_fine_tuning(self, ai_result: Dict[str, Any], 
                                     execution_result: Dict[str, Any], 
                                     movement_data: Dict = None) -> bool:
        """Determine if turn should be included in fine-tuning dataset"""
        # Must be successful turn
        if not self._assess_turn_success(ai_result, execution_result):
            return False
        
        # Must have meaningful analysis (not just error messages)
        analysis = ai_result.get('analysis', '')
        if any(error_keyword in analysis.lower() for error_keyword in ['error', 'failed', 'exception', 'no game data']):
            return False
        
        # Must have valid button presses
        actions = ai_result.get('action', [])
        if not actions or not isinstance(actions, list):
            return False
        
        # Visual analysis quality check (if available)
        if movement_data:
            # Check for new visual context analyzer format
            valid_moves = movement_data.get('valid_movements', [])
            # Fallback to old format if needed
            if not valid_moves:
                valid_moves = movement_data.get('valid_sequences', {}).get('1_move', [])
            if not valid_moves:
                return False  # Skip turns with no valid movements detected
        
        return True
    
    def _save_enhanced_session_data(self):
        """Save enhanced session data with all turn details"""
        try:
            if not hasattr(self, 'session_data_file'):
                return
                
            # Create comprehensive session data
            enhanced_session_data = {
                "session_metadata": {
                    "session_id": self.session.session_id,
                    "goal": self.session.goal,
                    "start_time": self.session.start_time,
                    "status": self.session.status,
                    "total_turns": len(self.session.turns_data) if hasattr(self.session, 'turns_data') else 0,
                    "successful_turns": self.session.successful_turns if hasattr(self.session, 'successful_turns') else 0,
                    "fine_tuning_eligible": len([t for t in self.session.turns_data if t.include_in_fine_tuning]) if hasattr(self.session, 'turns_data') else 0
                },
                
                # Legacy format for backward compatibility
                "session_id": self.session.session_id,
                "goal": self.session.goal,
                "start_time": self.session.start_time,
                "turns": self.session_turns if hasattr(self, 'session_turns') else [],
                
                # Enhanced turn data
                "enhanced_turns": [asdict(turn) for turn in self.session.turns_data] if hasattr(self.session, 'turns_data') else []
            }
            
            # Write enhanced session data
            with open(self.session_data_file, 'w') as f:
                json.dump(enhanced_session_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"WARNING: Failed to save enhanced session data: {e}")
    
    def _handle_user_input(self):
        """Handle real-time user input during gameplay"""
        user_input = self.interactive_controller.get_user_input()
        
        if user_input:
            self.session.user_interactions.append(user_input)
            
            if user_input.startswith("/"):
                self._handle_command(user_input)
            else:
                self._handle_user_task(user_input)
    
    def _handle_command(self, command: str):
        """Handle interactive commands"""
        cmd = command.lower().strip()
        
        if cmd == "/pause":
            self.paused = True
            print("�  Gameplay paused. Type /resume to continue.")
            
        elif cmd == "/resume":
            self.paused = False
            print("�  Gameplay resumed.")
            
        elif cmd == "/status":
            self._show_status()
            
        elif cmd == "/quit":
            print("=K Stopping gameplay...")
            self.running = False
            
        elif cmd == "/help":
            self._show_help()
            
        else:
            print(f"S Unknown command: {command}")
    
    def _handle_user_task(self, task: str):
        """Handle user task during gameplay"""
        print(f"- User task received: {task}")
        print("- Task will influence AI decision in next turn")
        
        # Store task for AI context
        if hasattr(self, '_user_tasks'):
            self._user_tasks.append(task)
        else:
            self._user_tasks = [task]
    
    def _show_status(self):
        """Show current gameplay status"""
        print(f"\n- Gameplay Status:")
        print(f"   Turn: {self.session.turns_completed}/{self.session.max_turns}")
        print(f"   Status: {'� Paused' if self.paused else '� Running'}")
        print(f"   Goal: {self.session.goal}")
        print(f"   Last Action: {self.session.last_action}")
        print(f"   Session ID: {self.session.session_id}")
    
    def _show_help(self):
        """Show available commands"""
        print(f"\n- Available Commands:")
        print(f"   /pause  - Pause gameplay")
        print(f"   /resume - Resume gameplay")
        print(f"   /status - Show current status")
        print(f"   /quit   - Stop gameplay")
        print(f"   /help   - Show this help")
        print(f"\n- Or type any Pokemon task for the AI to consider")
    
    def _get_memory_context(self) -> str:
        """Get memory context combining SQLite + Neo4j last 4 turns"""
        context_parts = []
        
        # Get general memory context (existing SQLite)
        if self.eevee.memory:
            try:
                general_context = self.eevee.memory.get_recent_gameplay_summary(limit=5)
                if general_context:
                    context_parts.append(general_context)
            except:
                pass
        
        # Get last 4 turns from Neo4j for compact memory context
        try:
            from neo4j_compact_reader import Neo4jCompactReader
            reader = Neo4jCompactReader()
            
            if reader.test_connection():
                # Get recent turns for this session
                recent_turns = reader.get_recent_turns(4)
                if recent_turns:
                    compact_memory = reader.format_turns_to_compact_json(recent_turns)
                    memory_json = json.dumps(compact_memory, separators=(',', ':'))
                    context_parts.append(f"**RECENT MEMORY** (last 4 turns):\n{memory_json}")
                    
                    # Store for turn storage
                    self._last_memory_context = memory_json
                    
                    if self.eevee.verbose:
                        token_count = len(memory_json.split())
                        print(f"📝 Neo4j memory context: {token_count} tokens")
            
            reader.close()
            
        except Exception as e:
            if self.eevee.verbose:
                print(f"⚠️ Neo4j memory retrieval failed: {e}")
        
        # Add spatial memory to prevent repetitive actions (fallback)
        spatial_memory = self._build_spatial_memory()
        if spatial_memory:
            context_parts.append(spatial_memory)
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def _build_spatial_memory(self) -> str:
        """Build spatial memory to prevent repetitive actions"""
        if not hasattr(self, 'recent_turns') or not self.recent_turns:
            return ""
        
        memory_parts = []
        recent_turns = self.recent_turns[-5:]  # Analyze last 5 turns
        
        # Track item collection attempts
        item_attempts = []
        repeated_movements = []
        
        for turn in recent_turns:
            observation = turn.get("observation", "").lower()
            actions = turn.get("action", [])
            
            # Detect item collection attempts
            if any(keyword in observation for keyword in ["pokeball", "poke ball", "item", "pick up"]):
                item_attempts.append({
                    "turn": turn.get("turn"),
                    "action": actions,
                    "observation_snippet": observation[:100] + "..." if len(observation) > 100 else observation
                })
            
            # Detect repeated directional movements
            if actions and len(actions) == 1 and actions[0] in ["up", "down", "left", "right"]:
                repeated_movements.append(actions[0])
        
        # Build warnings about repeated item attempts
        if len(item_attempts) >= 2:
            memory_parts.append("🚨 SPATIAL MEMORY - ITEM COLLECTION:")
            memory_parts.append(f"   • You've attempted to collect items {len(item_attempts)} times recently")
            memory_parts.append("   • If the item is still visible, try a different approach or move to explore other areas")
            memory_parts.append("   • Avoid repeating the same movement toward items that may already be collected")
        
        # Build warnings about movement loops
        if len(repeated_movements) >= 3:
            from collections import Counter
            movement_counts = Counter(repeated_movements[-4:])  # Last 4 movements
            most_common = movement_counts.most_common(1)[0]
            if most_common[1] >= 3:
                memory_parts.append("🚨 SPATIAL MEMORY - MOVEMENT LOOP:")
                memory_parts.append(f"   • You've pressed '{most_common[0]}' {most_common[1]} times recently")
                memory_parts.append("   • Try a different direction or consider using 'A' to interact")
        
        return "\n".join(memory_parts) if memory_parts else ""
    
    
    def _record_turn_action(self, turn_number: int, observation: str, action: List[str], result: str):
        """Record a turn's action for recent context with progress tracking and Neo4j storage"""
        
        nav_progress = True  # Assume progress unless AI determines otherwise
        visual_similarity = 0.0
        
        turn_record = {
            "turn": turn_number,
            "observation": observation,  # Full observation, no truncation
            "action": action,
            "result": result,  # Full result, no truncation  
            "progress_made": nav_progress,  # Enhanced: Track if visual progress was made
            "visual_similarity": visual_similarity,  # Enhanced: Track visual similarity
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to recent turns, keep only last N turns
        self.recent_turns.append(turn_record)
        if len(self.recent_turns) > self.max_recent_turns:
            self.recent_turns.pop(0)
        
    
    def _extract_location_from_observation(self, observation: str) -> str:
        """Extract location information from observation text"""
        # Simple location extraction - can be enhanced
        observation_lower = observation.lower()
        
        # Common Pokemon locations
        locations = [
            "route", "forest", "cave", "city", "town", "center", "gym", 
            "viridian", "pewter", "cerulean", "vermillion", "lavender", 
            "celadon", "fuchsia", "saffron", "cinnabar", "pallet"
        ]
        
        for location in locations:
            if location in observation_lower:
                return location.title()
        
        return "unknown"
    
    def _get_recent_actions_summary(self) -> str:
        """Build a summary of recent actions for AI context"""
        if not self.recent_turns:
            return "No previous actions in this session."
        
        summary = "**RECENT ACTIONS** (last few turns):\n"
        
        for turn_record in self.recent_turns[-3:]:  # Show last 3 turns max
            turn_num = turn_record["turn"]
            obs = turn_record["observation"]
            actions = turn_record["action"]
            result = turn_record["result"]
            progress = turn_record.get("progress_made", "unknown")
            similarity = turn_record.get("visual_similarity", 0.0)
            
            # Simple summary without hardcoded progress heuristics
            summary += f"Turn {turn_num}: Observed '{obs}' → Pressed {actions} → {result}\n"
        
        # Simple pattern detection - let AI make its own conclusions
        if len(self.recent_turns) >= 3:
            last_actions = [turn["action"] for turn in self.recent_turns[-3:]]
            
            if all(action == last_actions[0] for action in last_actions):
                summary += "Note: Same action repeated 3 times.\n"
        
        return summary
    

    # 🧠 NEW AI-DIRECTED CONTEXT DETECTION METHODS
    
    def _determine_ai_context(self, memory_context: str, recent_actions: List[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        UPDATED: Let AI choose the appropriate context based on provided data
        No more hardcoded detection - provide rich context and let AI decide
        
        Args:
            memory_context: Recent memory/gameplay context
            recent_actions: List of recent button actions
            
        Returns:
            Tuple of (context_type, context_data_dict)
        """
        user_goal = self.session.goal.lower()
        recent_actions = recent_actions or []
        
        # Provide rich context data for AI to analyze
        context_data = {
            "memory_context": memory_context,
            "user_goal": user_goal,
            "recent_actions": recent_actions,
            "escalation_level": self._get_escalation_level(),
            "session_turn": getattr(self.session, 'turns_completed', 0)
        }
        
        # EMERGENCY CONTEXT (only for severe stuck patterns)
        stuck_level = self._get_escalation_level()
        if stuck_level in ["level_3", "level_4", "level_5"]:  # Only severe stuck patterns
            context_data["emergency_context"] = {
                "escalation_level": stuck_level,
                "recent_actions": recent_actions[-5:] if recent_actions else [],  # Simple recent actions instead of stuck analysis
                "attempts_count": len([action for action in recent_actions if action == recent_actions[-1]]) if recent_actions else 0
            }
            return "emergency", context_data
        
        # DEFAULT: Return context data and let AI choose template dynamically
        # The prompt_manager will use memory_context to select appropriate template
        return "auto_select", context_data  # AI will analyze context and choose template
    
    def _detect_battle_phase(self, context_lower: str) -> str:
        """Detect current battle phase for context"""
        if any(keyword in context_lower for keyword in ["appeared", "wild", "trainer", "battle text"]):
            return "intro"
        elif any(keyword in context_lower for keyword in ["fight", "bag", "pokemon", "run"]):
            return "menu"
        elif any(keyword in context_lower for keyword in ["move", "attack", "thundershock", "tackle"]):
            return "moves"
        elif any(keyword in context_lower for keyword in ["animation", "damage", "hp"]):
            return "animation"
        else:
            return "unknown"
    
    def _get_escalation_level(self) -> str:
        """Determine current escalation level based on stuck patterns"""
        if not hasattr(self, 'nav_enhancer'):
            return "level_1"
        
        if hasattr(self.nav_enhancer, 'stuck_counter'):
            stuck_count = getattr(self.nav_enhancer, 'stuck_counter', 0)
            if stuck_count >= 10:
                return "level_3"  # Nuclear options
            elif stuck_count >= 6:
                return "level_2"  # Aggressive recovery
            else:
                return "level_1"  # Gentle recovery
        
        return "level_1"
    
    def _get_available_memory_contexts(self) -> List[str]:
        """Get list of available memory contexts for AI to choose from"""
        contexts = ["navigation", "battle", "gym", "forest", "cave", "services"]
        
        # Add context based on current goal
        user_goal = self.session.goal.lower()
        if "gym" in user_goal:
            contexts.append("gym_strategies")
        if "forest" in user_goal:
            contexts.append("forest_navigation")
        if "battle" in user_goal:
            contexts.append("battle_tactics")
        
        return contexts
    
    # Note: _analyze_stuck_patterns function removed to allow natural AI learning
    
    def _extract_location_name(self, context_lower: str) -> str:
        """Extract location name from context"""
        # Common Pokemon location patterns
        locations = [
            "viridian forest", "viridian city", "pallet town", "pewter city",
            "cerulean city", "vermillion city", "lavender town", "celadon city",
            "fuchsia city", "saffron city", "cinnabar island", "indigo plateau",
            "rock tunnel", "victory road", "pokemon tower", "silph co"
        ]
        
        for location in locations:
            if location in context_lower:
                return location.title()
        
        # Fallback to generic extraction
        import re
        match = re.search(r'(route \d+|forest|city|town|cave|tunnel)', context_lower)
        return match.group(1).title() if match else "Unknown Location"
    
    def _get_recent_action_list(self) -> List[str]:
        """Get list of recent button actions for context analysis"""
        if not hasattr(self, 'recent_turns') or not self.recent_turns:
            return []
        
        # Extract button actions from recent turns
        recent_actions = []
        for turn in self.recent_turns[-10:]:  # Last 10 turns
            if isinstance(turn, dict) and 'action' in turn:
                action = turn['action']
                if isinstance(action, list):
                    recent_actions.extend(action)
                else:
                    recent_actions.append(action)
        
        return recent_actions
    
    def _analyze_recent_actions_for_context(self) -> Dict[str, Any]:
        """Analyze recent actions to determine likely game context"""
        if not self.recent_turns:
            return {"repeated_a_presses": 0, "recent_sequences": [], "movement_pattern": "none"}
        
        recent_actions = [turn["action"] for turn in self.recent_turns[-5:]]  # Last 5 turns
        
        # Count 'a' button presses (common in battles and menus)
        a_presses = sum(1 for action_list in recent_actions for action in action_list if action == 'a')
        
        # Detect movement patterns
        movement_buttons = ['up', 'down', 'left', 'right']
        movement_count = sum(1 for action_list in recent_actions for action in action_list if action in movement_buttons)
        
        # Recent action sequences for pattern detection
        sequences = [turn["action"] for turn in self.recent_turns[-3:]]
        
        return {
            "repeated_a_presses": a_presses,
            "movement_count": movement_count,
            "recent_sequences": sequences,
            "total_recent_actions": len(recent_actions)
        }
    
    def _log_enhanced_analysis(self, turn_number: int, analysis_text: str, button_sequence: List[str]):
        """Enhanced logging with loop detection and full reasoning"""
        print(f"\n🎮 TURN {turn_number}: Pressed {button_sequence}")
        
        # Check for immediate loop patterns
        recent_actions = self._get_recent_actions_summary()
        if "consecutive" in recent_actions.lower():
            print(f"WARNING:  LOOP WARNING: {recent_actions}")
        
    def _log_strategic_decision_clean_output(self, result: Dict[str, Any]) -> None:
        """Output clean JSON for strategic decisions to console"""
        # Only output clean JSON if we have clean_output mode enabled
        # For now, we'll check if the comprehensive logger is available
        from evee_logger import get_comprehensive_logger
        
        # Extract the core strategic decision data for clean output
        strategic_output = {}
        
        if 'action' in result:
            strategic_output['button_presses'] = result['action']
        
        if 'reasoning' in result:
            strategic_output['reasoning'] = result['reasoning']
        
        if 'analysis' in result and result['analysis'] != result.get('reasoning', ''):
            strategic_output['analysis'] = result['analysis']
        
        # Try to extract JSON structure if it exists in the reasoning/analysis
        try:
            import json
            import re
            
            # Look for JSON in the response
            text = result.get('reasoning', '') or result.get('analysis', '')
            
            # Try to find JSON block
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group())
                    # If we found valid JSON, use it as the strategic output
                    strategic_output.update(parsed_json)
                except json.JSONDecodeError:
                    pass  # Use the fallback structure above
        except Exception:
            pass  # Use the fallback structure above
        
        # Add default fields if they're missing
        if 'confidence' not in strategic_output:
            strategic_output['confidence'] = 'medium'
        
        if 'context_detected' not in strategic_output:
            strategic_output['context_detected'] = 'navigation'
        
        # Use logger for clean console output
        logger = get_comprehensive_logger()
        if logger:
            logger.log_strategic_decision_console(strategic_output)
        else:
            # Fallback if no logger available
            import json
            print("=== STRATEGIC DECISION ===")
            print(json.dumps(strategic_output, indent=2, ensure_ascii=False))
            print()
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """Extract a section from AI response based on keywords"""
        import re
        
        for keyword in keywords:
            # Look for patterns like "🎯 OBSERVATION:", "**OBSERVATION**:", etc.
            patterns = [
                rf"{re.escape(keyword)}[:\s]+(.*?)(?=🎯|🧠|⚡|$)",
                rf"\*\*{re.escape(keyword)}\*\*[:\s]+(.*?)(?=\*\*|$)",
                rf"{re.escape(keyword)}[:\s]+(.*?)(?=\n\n|$)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
        
        return ""
    
    def _build_ai_prompt(self, turn_number: int, memory_context: str, image_data: str = None, movement_data: Dict = None) -> Dict[str, Any]:
        """Build context-aware AI prompt with playbook integration
        
        Returns:
            Dict with 'prompt' key and metadata about template selection
        """
        user_tasks = getattr(self, '_user_tasks', [])
        recent_task = user_tasks[-1] if user_tasks else ""
        
        # Try to get prompt manager for enhanced prompts
        prompt_manager = getattr(self.eevee, 'prompt_manager', None)
        
        if prompt_manager:
            # 🧠 NEW: Use AI-directed prompt system that can self-manage
            variables = {
                "task": self.session.goal,
                "context_summary": f"Turn {turn_number}/{self.session.max_turns}",
                "memory_context": memory_context,
                "recent_actions": self._get_recent_actions_summary(),
                "goal": self.session.goal,
                # "stuck_problem": removed - Pure AI autonomy preferred
            }
            
            try:
                # OPTIMIZATION: Use visual context analyzer's template recommendation directly
                # This eliminates the redundant AI selection call and saves LLM tokens
                if movement_data and 'recommended_template' in movement_data:
                    # SIMPLIFIED: Use Gemini's template recommendation directly - no complex mapping!
                    prompt_type = movement_data['recommended_template']
                    
                    # Simple playbook selection based on template
                    playbook = "battle" if prompt_type == "battle_analysis" else "navigation"
                    
                    if self.eevee.verbose:
                        print(f"✅ DIRECT TEMPLATE SELECTION: {prompt_type}")
                        print(f"   Scene: {movement_data.get('scene_type', 'unknown')}")
                        print(f"   Confidence: {movement_data.get('confidence', 'unknown')}")
                        print(f"   Playbook: {playbook}")
                    
                    # Add visual context variables
                    variables.update({
                        "scene_type": movement_data.get("scene_type", "unknown"),
                        "spatial_context": movement_data.get("spatial_context", ""),
                        "character_position": movement_data.get("character_position", ""),
                        "visual_description": movement_data.get("visual_description", ""),
                        "valid_movements": movement_data.get("valid_movements", []),
                        "confidence": movement_data.get("confidence", "unknown")
                    })
                    
                    # Add battle-specific variables if using battle template
                    if prompt_type == "battle_analysis":
                        variables.update({
                            "battle_phase": movement_data.get("battle_phase", "unknown"),
                            "our_pokemon": movement_data.get("our_pokemon", "unknown"),
                            "enemy_pokemon": movement_data.get("enemy_pokemon", "unknown"),
                            "move_options": movement_data.get("move_options", []),
                            "cursor_on": movement_data.get("cursor_on", "unknown"),
                            "valid_buttons": movement_data.get("valid_buttons", [])
                        })
                    
                    # Generate prompt - simple and direct
                    prompt = prompt_manager.get_prompt(
                        prompt_type, 
                        variables, 
                        include_playbook=playbook,
                        verbose=True
                    )
                    
                    template_used = prompt_type
                    template_version = prompt_manager.base_prompts[prompt_type].get('version', 'direct_selection')
                    playbooks = [playbook]
                    using_ai_directed = False
                
                else:
                    # SIMPLIFIED FALLBACK: Just use exploration_strategy when visual analysis unavailable
                    if self.eevee.verbose:
                        print(f"⚠️ No visual recommendation available, using default template")
                    
                    prompt_type = "exploration_strategy"
                    playbook = "navigation"
                    
                    # Add fallback values
                    variables.update({
                        "scene_type": "navigation",
                        "spatial_context": "Visual analysis unavailable",
                        "character_position": "unknown", 
                        "visual_description": "No visual analysis data",
                        "valid_movements": ["up", "down", "left", "right"],
                        "confidence": "low"
                    })
                    
                    prompt = prompt_manager.get_prompt(
                        prompt_type, 
                        variables, 
                        include_playbook=playbook,
                        verbose=True
                    )
                    
                    template_used = prompt_type
                    template_version = prompt_manager.base_prompts[prompt_type].get('version', 'fallback')
                    playbooks = [playbook]
                
                # Add OKR context if enabled
                okr_context = ""
                if self.eevee.enable_okr:
                    okr_context = self.eevee.get_okr_context()
                    if self.eevee.verbose:
                        print(f"📊 OKR Context included: {len(okr_context)} characters")
                
                # Add continuous gameplay context
                prompt += f"""

**CONTINUOUS GAMEPLAY CONTEXT**:
- Turn {turn_number} of {self.session.max_turns}
- Goal: {self.session.goal}
- User instruction: {recent_task if recent_task else "Continue autonomous gameplay"}
- Memory: {memory_context}
{okr_context}
**ENHANCED ANALYSIS REQUIREMENTS**:
🎯 **OBSERVATION**: Describe exactly what you see on screen
🧠 **ANALYSIS**: Explain your reasoning process for the next action
⚡ **ACTION**: Choose button sequence with strategic justification

Use the pokemon_controller tool with your chosen button sequence."""
                
                # Only show fallback logging when not using AI-directed prompts
                if not using_ai_directed:
                    playbook_list = ", ".join(playbooks) if playbooks else "none"
                    print(f"📖 Using template: {prompt_type} with playbooks: {playbook_list}")
                    
                    # Show template version if available
                    if hasattr(prompt_manager, 'base_prompts') and prompt_type in prompt_manager.base_prompts:
                        version = prompt_manager.base_prompts[prompt_type].get('version', 'unknown')
                        print(f"   📌 Template version: {version}")
                
            except Exception as e:
                # INIT: FIX: No fallback! Fix the actual issue and retry with safe defaults
                if self.eevee.verbose:
                    print(f"WARNING: Prompt manager failed: {e}")
                    print(f"🔄 Retrying with safe template selection...")
                
                # Use safe default template instead of fallback
                try:
                    prompt = prompt_manager.get_prompt(
                        "exploration_strategy", 
                        variables, 
                        include_playbook="navigation",
                        verbose=True
                    )
                    template_used = "exploration_strategy"
                    template_version = prompt_manager.base_prompts["exploration_strategy"].get('version', 'safe_default')
                    using_ai_directed = False
                    
                    if self.eevee.verbose:
                        print(f"✅ Using safe default JSON template: exploration_strategy")
                        
                except Exception as e2:
                    # If even safe defaults fail, there's a fundamental issue
                    raise Exception(f"Prompt manager completely broken: {e2}. Original error: {e}")
        else:
            # 🚨 CRITICAL: This should never happen - prompt_manager is always initialized in EeveeAgent
            raise Exception("EeveeAgent.prompt_manager is None - this indicates a critical initialization failure")
        
        # Clear processed user tasks
        if hasattr(self, '_user_tasks'):
            self._user_tasks.clear()
        
        # Return prompt with metadata about template selection
        return {
            "prompt": prompt,
            "template_used": template_used,
            "template_version": template_version,
            "playbooks_used": playbooks if 'playbooks' in locals() else []
        }
    
    # All responses must be JSON format for consistent parsing
    
    def _get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary and generate Pokemon episode diary"""
        end_time = datetime.now().isoformat()
        
        # Generate Pokemon episode diary
        diary_path = None
        try:
            print("\n🎬 Generating Pokemon episode diary...")
            
            # Create diary generator
            diary_gen = PokemonEpisodeDiary()
            
            # Determine day number
            day_number = diary_gen.get_next_day_number(str(self.eevee.runs_dir))
            
            # Load session data from file for complete diary generation
            session_data = {}
            if hasattr(self, 'session_data_file') and self.session_data_file.exists():
                with open(self.session_data_file, 'r') as f:
                    session_data = json.load(f)
            
            # Generate and save diary
            if session_data.get("turns"):
                diary_path = diary_gen.save_episode_diary(
                    session_data, 
                    str(self.eevee.runs_dir),
                    day_number
                )
                print(f"📖 Pokemon episode diary saved: {diary_path}")
                print(f"🎬 Episode #{day_number}: {session_data.get('goal', 'Pokemon Adventure')} completed!")
            else:
                print("WARNING:  No turn data available for diary generation")
                
        except Exception as e:
            print(f"WARNING:  Failed to generate Pokemon episode diary: {e}")
            if hasattr(self.eevee, 'debug') and self.eevee.debug:
                import traceback
                traceback.print_exc()
        
        summary = {
            "session_id": self.session.session_id,
            "status": self.session.status,
            "goal": self.session.goal,
            "turns_completed": self.session.turns_completed,
            "max_turns": self.session.max_turns,
            "start_time": self.session.start_time,
            "end_time": end_time,
            "user_interactions": len(self.session.user_interactions),
            "last_analysis": self.session.last_analysis,
            "last_action": self.session.last_action,
            "diary_path": diary_path
        }
        
        # Update Neo4j session status and cleanup
        try:
            from neo4j_singleton import Neo4jSingleton
            neo4j = Neo4jSingleton()
            writer = neo4j.get_writer()
            
            if writer and writer.driver:
                update_success = writer.update_session(self.session.session_id, {
                    "status": "completed",
                    "turns_completed": self.session.turns_completed,
                    "end_time": end_time
                })
                if update_success:
                    print(f"✅ Neo4j session updated: {self.session.session_id}")
                else:
                    print(f"⚠️ Neo4j session update failed")
                
                # Close Neo4j connection
                neo4j.close()
                print(f"✅ Neo4j connection closed")
            else:
                print(f"⚠️ Neo4j writer not available for cleanup")
        except Exception as e:
            print(f"⚠️ Neo4j session cleanup error: {e}")
        
        return summary
    
    def _run_periodic_episode_review(self, current_turn: int):
        """Run AI-powered periodic episode review and apply prompt improvements automatically"""
        try:
            print(f"📊 PERIODIC REVIEW (Turn {current_turn}): Analyzing last {self.episode_review_frequency} turns...")
            
            # Get recent turns for analysis
            recent_turns = self.session_turns[-self.episode_review_frequency:] if hasattr(self, 'session_turns') else []
            
            if not recent_turns:
                print("WARNING: No recent turns available for analysis")
                return
            
            # Run AI-powered analysis and template improvement
            improvement_result = self._run_ai_powered_review(recent_turns)
            
            # NEW: Goal-oriented planning analysis
            goal_planning_result = self._run_goal_oriented_planning_review(recent_turns, current_turn)
            
            if improvement_result["success"]:
                changes_applied = improvement_result["changes_applied"]
                
                if changes_applied > 0:
                    print(f"\nINIT: AI-POWERED PROMPT LEARNING: Applied {changes_applied} improvements")
                    
                    for change in improvement_result.get("changes", []):
                        print(f"   📝 {change['template']} v{change['old_version']} → v{change['new_version']}")
                        print(f"      Reason: {change['reasoning']}")
                    
                    # CRITICAL: Reload prompt templates to use the updates immediately
                    if hasattr(self.eevee, 'prompt_manager') and self.eevee.prompt_manager:
                        self.eevee.prompt_manager.reload_templates()
                        print(f"   🔄 RELOADED PROMPT TEMPLATES - AI will now use improved versions")
                    
                    # Save detailed periodic review
                    self._save_periodic_review(current_turn, improvement_result, recent_turns)
                        
                else:
                    # Use AI-powered performance analysis instead of primitive metrics
                    ai_performance_result = self._ai_evaluate_performance(recent_turns, current_turn)
                    
                    if ai_performance_result["success"]:
                        performance_score = ai_performance_result["performance_score"] 
                        issues = ai_performance_result["issues"]
                        
                        if performance_score >= 0.7 and not issues:
                            print(f"\n✅ AI PERFORMANCE ANALYSIS: Excellent gameplay detected")
                            print(f"   AI Performance Score: {performance_score:.2f}")
                            print(f"   Assessment: {ai_performance_result.get('assessment', 'No major issues detected')}")
                        else:
                            print(f"\n📊 AI ANALYSIS: Issues identified but no template improvements generated")
                            print(f"   AI Performance Score: {performance_score:.2f}")
                            if issues:
                                print(f"   Issues Detected: {', '.join(issues)}")
                            print(f"   Assessment: {ai_performance_result.get('assessment', 'Complex patterns require further observation')}")
                    else:
                        # Fallback to enhanced statistical analysis if AI analysis fails
                        enhanced_metrics = self._get_enhanced_performance_metrics(recent_turns)
                        
                        print(f"\n📊 PERFORMANCE REVIEW: AI analysis unavailable, using metrics")
                        print(f"   Navigation efficiency: {enhanced_metrics['navigation_efficiency']:.2f}")
                        print(f"   Complex stuck patterns: {enhanced_metrics['stuck_patterns']}")
                        print(f"   Oscillation patterns: {enhanced_metrics['oscillations']}")
                        print(f"   Directional bias: {enhanced_metrics['directional_bias']:.2f}")
            else:
                print(f"\n❌ AI REVIEW FAILED: {improvement_result.get('message', 'Unknown error')}")
                if improvement_result.get('error'):
                    print(f"   Error details: {improvement_result['error']}")
                
        except Exception as e:
            print(f"WARNING: Periodic episode review failed: {e}")
            if hasattr(self.eevee, 'debug') and self.eevee.debug:
                import traceback
                traceback.print_exc()
    
    def _get_quick_performance_metrics(self, recent_turns: List[Dict]) -> Dict[str, float]:
        """Get quick performance metrics without full episode review analysis"""
        if not recent_turns:
            return {'navigation_efficiency': 0.0, 'stuck_patterns': 0}
        
        # Count stuck patterns (consecutive identical actions)
        stuck_patterns = 0
        prev_action = None
        consecutive_count = 0
        
        for turn in recent_turns:
            current_action = str(turn.get('button_presses', []))
            if current_action == prev_action and current_action != "[]":
                consecutive_count += 1
                if consecutive_count >= 3:
                    stuck_patterns += 1
            else:
                consecutive_count = 0
            prev_action = current_action
        
        # Calculate navigation efficiency
        unique_actions = len(set(str(turn.get('button_presses', [])) for turn in recent_turns))
        total_actions = len(recent_turns)
        action_diversity = unique_actions / max(1, total_actions)
        stuck_penalty = max(0, 1 - (stuck_patterns / 20))  # Normalize for smaller sample
        navigation_efficiency = (action_diversity + stuck_penalty) / 2
        
        return {
            'navigation_efficiency': navigation_efficiency,
            'stuck_patterns': stuck_patterns
        }
    
    def _ai_evaluate_performance(self, recent_turns: List[Dict], current_turn: int) -> Dict[str, Any]:
        """Use Gemini 2.0 Flash Thinking to analyze Pokemon gameplay performance"""
        try:
            # Use enhanced stuck detection for analysis context
            # Build AI performance analysis prompt (without stuck detection interference)
            analysis_prompt = self._build_ai_performance_analysis_prompt(recent_turns, [], current_turn)
            
            # Call Gemini for intelligent performance analysis
            api_result = self.eevee._call_gemini_api(
                prompt=analysis_prompt,
                image_data=None,  # Text-only analysis for now
                use_tools=False,
                max_tokens=1500
            )
            
            if api_result["error"]:
                return {
                    "success": False,
                    "error": f"Gemini API failed: {api_result['error']}"
                }
            
            # Parse Gemini's response for performance assessment
            analysis_text = api_result.get("text", "")
            return self._parse_ai_performance_response(analysis_text, [])
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI performance evaluation failed: {e}"
            }
    
    def _build_ai_performance_analysis_prompt(self, recent_turns: List[Dict], stuck_indices: List[int], current_turn: int) -> str:
        """Build comprehensive prompt for AI performance analysis"""
        
        # Extract key gameplay patterns
        button_summary = []
        analysis_summary = []
        
        for i, turn in enumerate(recent_turns[-10:]):  # Last 10 turns for context
            turn_num = current_turn - len(recent_turns) + i + 1
            buttons = turn.get("button_presses", [])
            analysis = turn.get("ai_analysis", "")[:100]  # First 100 chars
            
            stuck_marker = " [STUCK]" if i in stuck_indices else ""
            button_summary.append(f"Turn {turn_num}: {buttons}{stuck_marker}")
            
            if analysis:
                analysis_summary.append(f"Turn {turn_num}: {analysis}...")
        
        # Count pattern types detected by enhanced system
        pattern_summary = {
            "exact_repetitions": len(self._detect_exact_repetition_patterns(recent_turns)),
            "oscillations": len(self._detect_oscillation_patterns(recent_turns)),
            "multibutton_reps": len(self._detect_multibutton_repetitions(recent_turns)),
            "directional_bias": len(self._detect_directional_bias_patterns(recent_turns))
        }
        
        return f"""POKEMON GAMEPLAY PERFORMANCE ANALYSIS

You are analyzing a Pokemon AI gameplay session to determine performance quality and identify potential issues.

GAMEPLAY DATA (Last {len(recent_turns)} turns):
{chr(10).join(button_summary)}

AI REASONING SAMPLES:
{chr(10).join(analysis_summary[:5])}  

DETECTED PATTERNS:
- Exact repetitions: {pattern_summary['exact_repetitions']} stuck turns
- Oscillations (A→B→A→B): {pattern_summary['oscillations']} stuck turns  
- Multi-button repetitions: {pattern_summary['multibutton_reps']} stuck turns
- Directional bias: {pattern_summary['directional_bias']} stuck turns
- Total stuck patterns: {len(stuck_indices)} turns

ANALYSIS REQUIREMENTS:

1. **POKEMON-SPECIFIC ASSESSMENT**:
   - Corner traps: AI hitting invisible collision boundaries repeatedly
   - Trainer fixation: Obsessing over unreachable trainers
   - Oscillation patterns: up→right→up→right cycles indicating spatial confusion  
   - Progress evaluation: Is the AI making meaningful spatial progress?

2. **TEMPLATE EFFECTIVENESS**:
   - Are the AI's decisions logical for Pokemon gameplay?
   - Does the AI understand Pokemon collision mechanics?
   - Is the AI getting stuck in complex patterns the templates don't handle?

3. **PERFORMANCE SCORING** (0.0 = terrible, 1.0 = excellent):
   - 0.8-1.0: Efficient navigation, minimal stuck patterns, good progress
   - 0.5-0.7: Some issues but generally functional
   - 0.0-0.4: Severely stuck, no meaningful progress

REQUIRED OUTPUT FORMAT:
PERFORMANCE_SCORE: [0.0-1.0]
ISSUES: [comma-separated list of specific problems, or "none"]
ASSESSMENT: [2-3 sentence summary of gameplay quality]
RECOMMENDATIONS: [specific suggestions for improvement]

Focus on Pokemon-specific gameplay understanding. A score of 0.75 means "good performance with minor issues".
"""
    
    def _parse_ai_performance_response(self, analysis_text: str, stuck_indices: List[int]) -> Dict[str, Any]:
        """Parse Gemini's performance analysis response"""
        try:
            # Extract performance score
            performance_score = 0.0
            if "PERFORMANCE_SCORE:" in analysis_text:
                score_line = analysis_text.split("PERFORMANCE_SCORE:")[1].split("\n")[0].strip()
                try:
                    performance_score = float(score_line.replace("[", "").replace("]", ""))
                    performance_score = max(0.0, min(1.0, performance_score))  # Clamp to 0-1
                except ValueError:
                    performance_score = 0.3  # Conservative default
            
            # Extract issues
            issues = []
            if "ISSUES:" in analysis_text:
                issues_line = analysis_text.split("ISSUES:")[1].split("\n")[0].strip()
                if issues_line.lower() not in ["none", "[]", "[none]"]:
                    issues = [issue.strip() for issue in issues_line.replace("[", "").replace("]", "").split(",")]
            
            # Extract assessment
            assessment = ""
            if "ASSESSMENT:" in analysis_text:
                assessment_line = analysis_text.split("ASSESSMENT:")[1].split("RECOMMENDATIONS:")[0].strip()
                assessment = assessment_line
            
            # Extract recommendations
            recommendations = ""
            if "RECOMMENDATIONS:" in analysis_text:
                recommendations = analysis_text.split("RECOMMENDATIONS:")[1].strip()
            
            return {
                "success": True,
                "performance_score": performance_score,
                "issues": issues,
                "assessment": assessment,
                "recommendations": recommendations,
                "stuck_patterns_detected": len(stuck_indices),
                "analysis_text": analysis_text
            }
            
        except Exception as e:
            # Fallback: if parsing fails, assume poor performance due to complexity
            return {
                "success": True,
                "performance_score": 0.2,  # Conservative - if we can't parse, likely problems
                "issues": ["analysis_parsing_failed", "complex_patterns_detected"],
                "assessment": f"Performance analysis parsing failed. Detected {len(stuck_indices)} stuck patterns.",
                "recommendations": "Improve template handling for complex stuck patterns.",
                "stuck_patterns_detected": len(stuck_indices),
                "parse_error": str(e)
            }
    
    def _get_enhanced_performance_metrics(self, recent_turns: List[Dict]) -> Dict[str, Any]:
        """Enhanced statistical analysis using comprehensive stuck detection (fallback for AI failure)"""
        if not recent_turns:
            return {
                'navigation_efficiency': 0.0, 
                'stuck_patterns': 0,
                'oscillations': 0,
                'directional_bias': 0.0
            }
        
        # Use the new comprehensive stuck detection
        # Performance analysis without stuck detection interference - let AI learn naturally
        exact_reps = 0
        oscillations = 0
        multibutton_reps = 0
        directional_bias_turns = 0
        
        # Calculate navigation efficiency without stuck detection
        total_turns = len(recent_turns)
        stuck_ratio = 0.0  # No artificial stuck detection
        
        # Diversity of actions (all turns considered equally)
        non_stuck_turns = recent_turns  # All turns treated equally
        if non_stuck_turns:
            unique_actions = len(set(str(turn.get('button_presses', [])) for turn in non_stuck_turns))
            action_diversity = unique_actions / len(non_stuck_turns)
        else:
            action_diversity = 0.0
        
        # Enhanced efficiency calculation
        navigation_efficiency = (1 - stuck_ratio) * 0.7 + action_diversity * 0.3
        
        # Directional bias calculation
        direction_counts = {"up": 0, "down": 0, "left": 0, "right": 0}
        total_directions = 0
        
        for turn in recent_turns:
            for button in turn.get("button_presses", []):
                if button in direction_counts:
                    direction_counts[button] += 1
                    total_directions += 1
        
        max_direction_ratio = max(direction_counts.values()) / max(1, total_directions)
        
        return {
            'navigation_efficiency': navigation_efficiency,
            'stuck_patterns': 0,  # Fixed: No stuck detection in this system
            'oscillations': oscillations,
            'directional_bias': max_direction_ratio,
            'pattern_breakdown': {
                'exact_repetitions': exact_reps,
                'oscillations': oscillations,
                'multibutton_repetitions': multibutton_reps,
                'directional_bias_turns': directional_bias_turns
            }
        }
                
    def _run_ai_powered_review(self, recent_turns: List[Dict]) -> Dict[str, Any]:
        """Use AI to analyze recent turns and identify templates that need improvement"""
        try:
            # Step 1: Analyze which templates were used and their performance
            template_usage = self._analyze_template_usage(recent_turns)
            
            # Step 2: Ask Gemini to identify which templates need improvement
            templates_to_improve = self._identify_templates_needing_improvement(recent_turns, template_usage)
            
            if not templates_to_improve:
                return {
                    "success": True,
                    "changes_applied": 0,
                    "message": "No templates identified for improvement"
                }
            
            # Step 3: Improve each identified template using AI
            changes_applied = []
            for template_info in templates_to_improve:
                template_name = template_info["template_name"]
                failure_examples = template_info["failure_examples"]
                improvement_reasoning = template_info["reasoning"]
                
                # Get current template content
                current_template = self._get_current_template_content(template_name)
                if not current_template:
                    continue
                
                # Use AI to improve the template
                improved_template = self._improve_template_with_ai(
                    template_name, current_template, failure_examples, improvement_reasoning
                )
                
                if improved_template and improved_template != current_template["template"]:
                    # Save the improved template
                    change_result = self._save_improved_template(template_name, improved_template, improvement_reasoning)
                    if change_result:
                        changes_applied.append(change_result)
            
            return {
                "success": True,
                "changes_applied": len(changes_applied),
                "changes": changes_applied,
                "message": f"Applied {len(changes_applied)} template improvements"
            }
            
        except Exception as e:
            return {
                "success": False,
                "changes_applied": 0,
                "error": str(e),
                "message": "AI-powered review failed"
            }
    
    def _analyze_template_usage(self, recent_turns: List[Dict]) -> Dict[str, Any]:
        """Analyze which templates were used and their success/failure patterns"""
        template_stats = {}
        
        # Analyze turns without stuck detection - let AI learn naturally
        
        for i, turn in enumerate(recent_turns):
            template_used = turn.get("template_used", "unknown")
            template_version = turn.get("template_version", "unknown")
            
            # Natural failure detection based on actual results only
            action_result = turn.get("action_result", False)
            is_stuck_turn = False  # No artificial stuck detection
            
            # A turn is considered a "failure" if:
            # 1. The action didn't succeed, OR
            # 2. It's part of a stuck/loop pattern (repeated actions with no progress)
            is_failure = not action_result or is_stuck_turn
            
            if template_used not in template_stats:
                template_stats[template_used] = {
                    "usage_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "version": template_version,
                    "failure_turns": [],
                    "success_turns": [],
                    "stuck_turns": 0
                }
            
            template_stats[template_used]["usage_count"] += 1
            
            if is_failure:
                template_stats[template_used]["failure_count"] += 1
                template_stats[template_used]["failure_turns"].append(turn)
                if is_stuck_turn:
                    template_stats[template_used]["stuck_turns"] += 1
            else:
                template_stats[template_used]["success_count"] += 1
                template_stats[template_used]["success_turns"].append(turn)
        
        # Calculate success rates
        for template_name, stats in template_stats.items():
            if stats["usage_count"] > 0:
                stats["success_rate"] = stats["success_count"] / stats["usage_count"]
            else:
                stats["success_rate"] = 0.0
        
        return template_stats
    
    # Note: Stuck pattern detection functions removed to allow natural AI learning
    # The AI will learn collision and navigation patterns through experience
    # rather than code-based intervention that interferes with learning
    
    def _identify_templates_needing_improvement(self, recent_turns: List[Dict], template_stats: Dict[str, Any]) -> List[Dict]:
        """Use AI to identify which templates need improvement based on performance patterns"""
        
        # FIXED: Consider templates that are actually used by AI-directed system
        # The AI-directed system generates template names like "ai_directed_navigation"
        valid_templates = {
            "ai_directed_navigation", "ai_directed_battle", "ai_directed_maze", "ai_directed_emergency",
            # Legacy templates (fallback system)
            "battle_analysis", "exploration_strategy", "stuck_recovery", 
            "pokemon_party_analysis", "inventory_analysis", "task_analysis"
        }
        
        # Template mapping: AI-directed templates → base templates for improvement
        ai_template_mapping = {
            "ai_directed_navigation": "exploration_strategy",
            "ai_directed_battle": "battle_analysis", 
            "ai_directed_maze": "exploration_strategy",
            "ai_directed_emergency": "stuck_recovery"
        }
        
        # Filter to only templates that have poor performance and are in our valid set
        candidates = []
        for template_name, stats in template_stats.items():
            # Skip templates that aren't in our selection system or have no failures
            if template_name not in valid_templates or stats["failure_count"] == 0:
                continue
                
            # Enhanced criteria: More sensitive to stuck patterns and complex failures
            # Since we now detect oscillations, directional bias, and multi-button repetitions,
            # we should lower thresholds to catch subtler performance issues
            stuck_turns = stats.get("stuck_turns", 0)
            stuck_ratio = stuck_turns / max(1, stats["usage_count"])
            
            # Trigger improvements for:
            # 1. Success rate below 80% (raised from 70% to be more sensitive)
            # 2. Any failures detected (lowered from 2 to 1)  
            # 3. High stuck pattern ratio (>30% of turns)
            if stats["success_rate"] < 0.8 or stats["failure_count"] >= 1 or stuck_ratio > 0.3:
                # Map AI-directed template to its base template for improvement
                base_template = ai_template_mapping.get(template_name, template_name)
                
                candidates.append({
                    "template_name": template_name,
                    "base_template": base_template,  # Template to actually improve
                    "stats": stats,
                    "failure_turns": stats["failure_turns"][:3]  # Last 3 failures
                })
        
        if not candidates:
            return []
        
        # Format the analysis data for Gemini
        analysis_prompt = self._build_template_analysis_prompt(candidates, recent_turns)
        
        try:
            # Call Gemini to analyze the failures and identify improvements needed
            api_result = self.eevee._call_gemini_api(
                prompt=analysis_prompt,
                image_data=None,  # Text-only analysis
                use_tools=False,
                max_tokens=2000
            )
            
            if api_result["error"]:
                print(f"WARNING: AI analysis failed: {api_result['error']}")
                return []
            
            # Parse the AI response to extract template improvement recommendations
            analysis_text = api_result.get("text", "")
            return self._parse_template_analysis_response(analysis_text, candidates)
            
        except Exception as e:
            print(f"WARNING: Template analysis failed: {e}")
            return []
    
    def _build_template_analysis_prompt(self, candidates: List[Dict], recent_turns: List[Dict]) -> str:
        """Build prompt for AI to analyze template performance and identify improvements"""
        
        prompt = """# Pokemon AI Template Performance Analysis

You are analyzing Pokemon gameplay templates that have shown poor performance. Your job is to identify which templates need improvement and why.

## Recent Gameplay Context
Goal: Find and win Pokemon battles
Turns analyzed: {}

## Template Performance Issues

""".format(len(recent_turns))
        
        for candidate in candidates:
            template_name = candidate["template_name"]
            stats = candidate["stats"]
            failure_turns = candidate["failure_turns"]
            
            prompt += f"""### Template: {template_name}
- Success rate: {stats['success_rate']:.2f} ({stats['success_count']}/{stats['usage_count']})
- Version: {stats['version']}
- Recent failures: {stats['failure_count']}

**Failure Examples:**
"""
            
            for i, turn in enumerate(failure_turns[:2], 1):  # Show 2 failure examples
                ai_analysis = turn.get("ai_analysis", "No analysis")
                button_presses = turn.get("button_presses", [])
                prompt += f"""
Failure {i}:
- AI Analysis: {ai_analysis}
- AI Decision: {button_presses}
- Result: Failed/No progress
"""
        
        prompt += """

## Your Analysis Task

For each template above, determine:
1. Is this template causing actual failures that hurt Pokemon gameplay?
2. What specific reasoning patterns or instructions are leading to poor decisions?
3. Should this template be improved? 

**Response Format:**
For each template that needs improvement, provide:

TEMPLATE: [template_name]
NEEDS_IMPROVEMENT: [yes/no]
REASONING: [specific failure pattern analysis]
PRIORITY: [high/medium/low]

Focus on templates that are actively causing Pokemon game failures, not just low success rates.
"""
        
        return prompt
    
    def _parse_template_analysis_response(self, analysis_text: str, candidates: List[Dict]) -> List[Dict]:
        """Parse AI response to extract templates that need improvement"""
        improvements_needed = []
        
        # Split response into sections by TEMPLATE:
        sections = analysis_text.split("TEMPLATE:")
        
        for section in sections[1:]:  # Skip first empty section
            try:
                lines = section.strip().split('\n')
                if not lines:
                    continue
                
                # Extract template name (first line)
                template_name = lines[0].strip()
                
                # Look for NEEDS_IMPROVEMENT field
                needs_improvement = False
                reasoning = ""
                priority = "medium"
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("NEEDS_IMPROVEMENT:"):
                        needs_improvement = "yes" in line.lower()
                    elif line.startswith("REASONING:"):
                        reasoning = line.replace("REASONING:", "").strip()
                    elif line.startswith("PRIORITY:"):
                        priority = line.replace("PRIORITY:", "").strip().lower()
                
                # Only include templates that need improvement
                if needs_improvement and template_name and reasoning:
                    # Find the failure examples for this template
                    failure_examples = []
                    for candidate in candidates:
                        if candidate["template_name"] == template_name:
                            failure_examples = candidate["failure_turns"]
                            break
                    
                    improvements_needed.append({
                        "template_name": template_name,
                        "reasoning": reasoning,
                        "priority": priority,
                        "failure_examples": failure_examples
                    })
                    
            except Exception as e:
                print(f"WARNING: Failed to parse template analysis section: {e}")
                continue
        
        return improvements_needed
    
    def _improve_template_with_ai(self, template_name: str, current_template: Dict, failure_examples: List[Dict], improvement_reasoning: str) -> str:
        """Use Gemini 2.0 Flash to improve a template based on failure analysis"""
        
        # Build the template improvement prompt
        improvement_prompt = f"""# Pokemon AI Template Improvement Task

You are a prompt engineering expert tasked with improving a Pokemon AI template that has shown poor performance.

## Current Template Information
**Template Name:** {template_name}
**Current Version:** {current_template.get('version', 'unknown')}
**Template Purpose:** {current_template.get('description', 'Pokemon gameplay guidance')}

## Current Template Content:
```
{current_template.get('template', '')}
```

## Performance Issues Identified:
{improvement_reasoning}

## Specific Failure Examples:
"""
        
        # Add failure examples with details
        for i, failure in enumerate(failure_examples[:2], 1):
            ai_analysis = failure.get("ai_analysis", "No analysis")
            button_presses = failure.get("button_presses", [])
            improvement_prompt += f"""
**Failure {i}:**
- AI Reasoning: {ai_analysis[:300]}...
- AI Action: {button_presses}
- Result: Failed to make progress

"""
        
        improvement_prompt += f"""
## Your Task
Generate an improved version of this template that:
1. Fixes the specific reasoning patterns causing failures
2. Maintains the same structure and variables: {current_template.get('variables', [])}
3. Provides clearer, more actionable guidance for Pokemon gameplay
4. Addresses the performance issues identified above

## Requirements:
- Keep the same template format and variable placeholders
- Focus on practical Pokemon game mechanics 
- Make instructions more specific and actionable
- Ensure the template guides better decision-making

## Output Format:
Return ONLY the improved template content, ready to replace the current template.
"""
        
        try:
            # Call Gemini 2.0 Flash for template improvement
            api_result = self.eevee._call_gemini_api(
                prompt=improvement_prompt,
                image_data=None,
                use_tools=False,
                max_tokens=3000,
                model="gemini-2.0-flash"  # Use the more powerful model
            )
            
            if api_result["error"]:
                print(f"WARNING: Template improvement failed: {api_result['error']}")
                return ""
            
            improved_content = api_result.get("text", "").strip()
            
            # Basic validation - ensure the improved template is different and substantial
            if len(improved_content) < 100:
                print(f"WARNING: Improved template too short: {len(improved_content)} chars")
                return ""
            
            if improved_content == current_template.get('template', ''):
                print(f"WARNING: Improved template identical to original")
                return ""
            
            return improved_content
            
        except Exception as e:
            print(f"WARNING: Template improvement with AI failed: {e}")
            return ""
    
    def _get_current_template_content(self, template_name: str) -> Dict[str, Any]:
        """Get current template content from the prompt manager"""
        try:
            if hasattr(self.eevee, 'prompt_manager') and self.eevee.prompt_manager:
                if hasattr(self.eevee.prompt_manager, 'base_prompts'):
                    return self.eevee.prompt_manager.base_prompts.get(template_name, {})
            return {}
        except Exception as e:
            print(f"WARNING: Failed to get template content for {template_name}: {e}")
            return {}
    
    def _save_improved_template(self, template_name: str, improved_content: str, reasoning: str) -> Dict[str, Any]:
        """Save improved template to YAML file"""
        try:
            # Get current template info
            current_template = self._get_current_template_content(template_name)
            if not current_template:
                return None
            
            old_version = current_template.get('version', '1.0')
            new_version = self._increment_template_version(old_version)
            
            # Update the template
            current_template['template'] = improved_content
            current_template['version'] = new_version
            
            # Save to YAML file
            prompts_file = Path(__file__).parent / "prompts" / "base" / "base_prompts.yaml"
            if prompts_file.exists():
                # Load current YAML
                with open(prompts_file, 'r') as f:
                    all_templates = yaml.safe_load(f) or {}
                
                # Update the specific template
                all_templates[template_name] = current_template
                
                # Save back to file
                with open(prompts_file, 'w') as f:
                    yaml.dump(all_templates, f, default_flow_style=False, indent=2, sort_keys=False)
                
                print(f"📝 Saved {template_name} v{old_version} → v{new_version} to {prompts_file}")
                
                return {
                    "template": template_name,
                    "old_version": old_version,
                    "new_version": new_version,
                    "reasoning": reasoning
                }
            
        except Exception as e:
            print(f"WARNING: Failed to save improved template {template_name}: {e}")
        
        return None
    
    def _increment_template_version(self, version: str) -> str:
        """Increment template version (e.g., '1.0' -> '1.1')"""
        try:
            parts = version.split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                return f"{major}.{minor + 1}"
            else:
                return f"{version}.1"
        except:
            return f"{version}.updated"
    
    def _save_periodic_review(self, current_turn: int, improvement_result: Dict, recent_turns: List[Dict]):
        """Save detailed periodic review report"""
        try:
            if hasattr(self, 'session_dir'):
                review_file = self.session_dir / f"periodic_review_turn_{current_turn}.md"
                
                # Create detailed review report
                report = f"""# Periodic Review - Turn {current_turn}

## Analysis Summary
- Templates analyzed: {len(improvement_result.get('changes', []))}
- Changes applied: {improvement_result['changes_applied']}
- Recent turns reviewed: {len(recent_turns)}

## Template Changes

"""
                
                for change in improvement_result.get('changes', []):
                    report += f"""### {change['template']} v{change['old_version']} → v{change['new_version']}

**Reasoning:** {change['reasoning']}

---

"""
                
                report += f"""
## Recent Gameplay Data

"""
                
                # Include summary of recent turns
                for turn in recent_turns[-3:]:  # Last 3 turns
                    turn_num = turn.get('turn', '?')
                    template = turn.get('template_used', 'unknown')
                    success = turn.get('action_result', False)
                    analysis = turn.get('ai_analysis', '')[:100] + "..."
                    
                    report += f"""**Turn {turn_num}** (Template: {template}, Result: {'✅' if success else '❌'})
{analysis}

"""
                
                with open(review_file, 'w') as f:
                    f.write(report)
                
                print(f"   📋 Detailed review saved: {review_file}")
                
        except Exception as e:
            print(f"WARNING: Failed to save periodic review: {e}")
    
    def _check_emergency_review_needed(self, current_turn: int) -> bool:
        """Check if emergency review needed due to catastrophic performance"""
        # Only check every 6 turns to avoid excessive overhead
        if current_turn % 6 != 0:
            return False
        
        # Load session data from file
        try:
            if hasattr(self, 'session_data_file') and self.session_data_file.exists():
                with open(self.session_data_file, 'r') as f:
                    session_data = json.load(f)
            else:
                return False
        except Exception:
            return False
        
        # Need at least 12 turns to detect patterns
        if len(session_data["turns"]) < 12:
            return False
        
        # No artificial stuck detection - let AI learn naturally
        return False  # Disable emergency reviews based on stuck patterns
    
    def _log_learning_event(self, turn_number: int, update_result: Dict[str, Any]):
        """Log automatic learning events to runs directory"""
        try:
            if not hasattr(self, '_learning_log_file'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._learning_log_file = self.eevee.runs_dir / f"learning_events_{timestamp}.log"
            
            with open(self._learning_log_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"TURN {turn_number} - AUTOMATIC LEARNING EVENT\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Changes Applied: {update_result['changes_applied']}\n")
                
                if update_result['changes_applied'] > 0:
                    f.write(f"Template Updates:\n")
                    for change in update_result.get('changes', []):
                        f.write(f"  - {change['template']} {change['version']}: {change['reasoning']}\n")
                    
                    f.write(f"Git Committed: {update_result.get('git_committed', False)}\n")
                
                metrics = update_result['metrics']
                f.write(f"Performance Metrics:\n")
                f.write(f"  - Navigation Efficiency: {metrics['navigation_efficiency']:.2f}\n")
                f.write(f"  - Battle Win Rate: {metrics['battle_win_rate']:.2f}\n")
                f.write(f"  - Stuck Patterns: {metrics['stuck_patterns']}\n")
                f.write(f"{'='*60}\n")
        
        except Exception as e:
            print(f"WARNING: Failed to log learning event: {e}")
    

    def _run_goal_oriented_planning_review(self, recent_turns: List[Dict], current_turn: int) -> Dict[str, Any]:
        """
        Analyze recent turns and update goal hierarchy for autonomous planning
        
        Enhanced with comprehensive contextual analysis for strategic prompt injection:
        1. Analyze progress toward current goal
        2. Generate movement pattern analysis
        3. Create strategic context for decision-making
        4. Store results for injection into strategic prompts
        5. Update okr.json with current active goal
        """
        try:
            print(f"🎯 GOAL-ORIENTED PLANNING: Analyzing progress toward '{self.session.goal}'")
            
            # Import TaskExecutor for goal decomposition
            from task_executor import TaskExecutor, Goal, GoalHierarchy
            
            # Create or get TaskExecutor
            if not hasattr(self.eevee, 'task_executor'):
                self.eevee.task_executor = TaskExecutor(self.eevee)
            
            task_executor = self.eevee.task_executor
            
            # NEW: Generate comprehensive strategic context analysis
            strategic_context = self._generate_strategic_context_analysis(recent_turns, current_turn)
            
            # Analyze recent turns for goal progress using AI
            progress_analysis = self._analyze_goal_progress_with_ai(recent_turns, self.session.goal)
            
            if not progress_analysis["success"]:
                print(f"⚠️ Goal progress analysis failed: {progress_analysis.get('error', 'Unknown error')}")
                # Still store strategic context even if goal analysis fails
                self._store_last_periodic_review(strategic_context, current_turn)
                return {"success": False, "error": "Goal progress analysis failed", "strategic_context": strategic_context}
            
            # Enhance progress analysis with strategic context
            enhanced_analysis = {**progress_analysis, **strategic_context}
            
            # Determine if goal hierarchy needs updating
            needs_replanning = progress_analysis.get("needs_replanning", False)
            current_goal_status = progress_analysis.get("goal_status", "in_progress")
            
            print(f"📊 Enhanced Analysis (Turn {current_turn}):")
            print(f"   Current Status: {current_goal_status}")
            print(f"   Progress Score: {progress_analysis.get('progress_score', 0)}/10")
            print(f"   Movement Pattern: {strategic_context.get('movement_pattern_summary', 'Unknown')}")
            print(f"   Strategic Insight: {strategic_context.get('key_insight', 'None')}")
            print(f"   Needs Replanning: {needs_replanning}")
            
            # Update or create goal hierarchy
            if needs_replanning or not task_executor.current_goal_hierarchy:
                print(f"🔄 Updating goal hierarchy for: '{self.session.goal}'")
                
                # Use TaskExecutor to decompose goal
                execution_plan = task_executor._create_plan_from_task(self.session.goal)
                
                if execution_plan and task_executor.current_goal_hierarchy:
                    goal_hierarchy = task_executor.current_goal_hierarchy
                    
                    # Update goal progress based on analysis
                    self._update_goal_progress(goal_hierarchy, progress_analysis)
                    
                    # Generate okr.json for AI context
                    okr_result = self._generate_okr_json(goal_hierarchy, progress_analysis)
                    
                    if okr_result["success"]:
                        print(f"✅ Goal hierarchy updated - Active: {okr_result['active_goal_name']}")
                        print(f"   Next Actions: {okr_result['next_actions']}")
                        
                        # Store enhanced context for strategic prompt injection
                        final_result = {
                            "success": True,
                            "goal_hierarchy_updated": True,
                            "active_goal": okr_result['active_goal_name'],
                            "okr_file_path": okr_result['okr_file_path'],
                            "strategic_context": strategic_context,
                            "enhanced_analysis": enhanced_analysis
                        }
                        self._store_last_periodic_review(enhanced_analysis, current_turn)
                        return final_result
                    else:
                        print(f"❌ Failed to generate okr.json: {okr_result.get('error')}")
                        self._store_last_periodic_review(enhanced_analysis, current_turn)
                else:
                    print(f"❌ Failed to create goal hierarchy from task: '{self.session.goal}'")
                    self._store_last_periodic_review(enhanced_analysis, current_turn)
            else:
                print(f"✅ Goal hierarchy is current - continuing with existing plan")
                self._store_last_periodic_review(enhanced_analysis, current_turn)
            
            return {
                "success": True,
                "goal_hierarchy_updated": False,
                "progress_analysis": progress_analysis,
                "strategic_context": strategic_context,
                "enhanced_analysis": enhanced_analysis
            }
            
        except Exception as e:
            print(f"❌ Goal-oriented planning review failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_strategic_context_analysis(self, recent_turns: List[Dict], current_turn: int) -> Dict[str, Any]:
        """
        Generate comprehensive strategic context analysis for prompt injection
        
        Analyzes movement patterns, performance metrics, and strategic insights
        to provide rich context for strategic decision-making prompts.
        """
        try:
            analysis_timestamp = datetime.now().isoformat()
            turns_analyzed = len(recent_turns)
            
            # Analyze movement patterns
            movement_analysis = self._analyze_movement_patterns(recent_turns)
            
            # Generate performance metrics
            performance_metrics = self._get_enhanced_performance_metrics(recent_turns)
            
            # Create strategic insights
            strategic_insights = self._generate_strategic_insights(recent_turns, movement_analysis, performance_metrics)
            
            return {
                "analysis_timestamp": analysis_timestamp,
                "turns_analyzed": turns_analyzed,
                "current_turn": current_turn,
                "movement_pattern_summary": movement_analysis.get("summary", "Unknown pattern"),
                "movement_patterns": movement_analysis,
                "performance_score": performance_metrics.get("navigation_efficiency", 0.0),
                "performance_metrics": performance_metrics,
                "key_insight": strategic_insights.get("primary_insight", "No clear patterns detected"),
                "strategic_recommendations": strategic_insights.get("recommendations", []),
                "behavioral_analysis": strategic_insights.get("behavioral_analysis", "Standard exploration behavior"),
                "adaptation_needed": strategic_insights.get("adaptation_needed", False)
            }
            
        except Exception as e:
            print(f"WARNING: Strategic context analysis failed: {e}")
            return {
                "analysis_timestamp": datetime.now().isoformat(),
                "turns_analyzed": len(recent_turns),
                "current_turn": current_turn,
                "movement_pattern_summary": "Analysis failed",
                "key_insight": "Unable to generate strategic context",
                "strategic_recommendations": ["continue_current_strategy"],
                "performance_score": 0.5,
                "error": str(e)
            }
    
    def _analyze_movement_patterns(self, recent_turns: List[Dict]) -> Dict[str, Any]:
        """Analyze movement patterns from recent turns"""
        try:
            if not recent_turns:
                return {"summary": "No turns to analyze", "pattern_type": "unknown"}
            
            # Extract button presses
            actions = []
            for turn in recent_turns:
                button_presses = turn.get('button_presses', [])
                if button_presses:
                    actions.extend(button_presses)
            
            if not actions:
                return {"summary": "No actions recorded", "pattern_type": "idle"}
            
            # Count action frequencies
            action_counts = {}
            for action in actions:
                action_counts[action] = action_counts.get(action, 0) + 1
            
            # Detect patterns
            total_actions = len(actions)
            most_common_action = max(action_counts.items(), key=lambda x: x[1])
            most_common_percentage = (most_common_action[1] / total_actions) * 100
            
            # Detect repetitive sequences
            consecutive_same = 0
            max_consecutive = 0
            prev_action = None
            
            for action in actions:
                if action == prev_action:
                    consecutive_same += 1
                    max_consecutive = max(max_consecutive, consecutive_same)
                else:
                    consecutive_same = 1
                prev_action = action
            
            # Determine pattern type
            if max_consecutive >= 4:
                pattern_type = "stuck_loop"
                summary = f"Repeating '{most_common_action[0]}' {max_consecutive} times consecutively"
            elif most_common_percentage > 70:
                pattern_type = "heavily_biased"
                summary = f"Heavy bias toward '{most_common_action[0]}' ({most_common_percentage:.1f}%)"
            elif len(set(actions)) == 1:
                pattern_type = "single_action"
                summary = f"Only using '{most_common_action[0]}'"
            elif len(set(actions)) >= 4:
                pattern_type = "diverse_exploration"
                summary = f"Diverse movement using {len(set(actions))} different actions"
            else:
                pattern_type = "limited_exploration"
                summary = f"Using {len(set(actions))} different actions"
            
            return {
                "summary": summary,
                "pattern_type": pattern_type,
                "action_counts": action_counts,
                "most_common_action": most_common_action[0],
                "most_common_percentage": most_common_percentage,
                "max_consecutive_same": max_consecutive,
                "action_diversity": len(set(actions)),
                "total_actions": total_actions
            }
            
        except Exception as e:
            return {"summary": f"Pattern analysis failed: {e}", "pattern_type": "error"}
    
    def _generate_strategic_insights(self, recent_turns: List[Dict], movement_analysis: Dict, performance_metrics: Dict) -> Dict[str, Any]:
        """Generate strategic insights and recommendations"""
        try:
            insights = []
            recommendations = []
            adaptation_needed = False
            
            # Analyze based on movement patterns
            pattern_type = movement_analysis.get("pattern_type", "unknown")
            max_consecutive = movement_analysis.get("max_consecutive_same", 0)
            action_diversity = movement_analysis.get("action_diversity", 0)
            
            if pattern_type == "stuck_loop":
                insights.append(f"AI is stuck in a loop, repeating same action {max_consecutive} times")
                recommendations.extend(["try_perpendicular_direction", "use_interaction_button", "backtrack_and_retry"])
                adaptation_needed = True
            elif pattern_type == "heavily_biased":
                insights.append("AI showing strong directional bias, may be missing alternative paths")
                recommendations.extend(["try_opposite_direction", "explore_perpendicular_paths"])
                adaptation_needed = True
            elif pattern_type == "single_action":
                insights.append("AI using only one action type, very limited exploration")
                recommendations.extend(["diversify_movement", "try_all_directions"])
                adaptation_needed = True
            elif action_diversity >= 4:
                insights.append("AI showing good exploration diversity")
                recommendations.append("continue_systematic_exploration")
            
            # Analyze performance metrics
            nav_efficiency = performance_metrics.get("navigation_efficiency", 0.0)
            if nav_efficiency < 0.3:
                insights.append("Low navigation efficiency, possible navigation issues")
                recommendations.append("reassess_navigation_strategy")
                adaptation_needed = True
            elif nav_efficiency > 0.7:
                insights.append("Good navigation efficiency, making progress")
                recommendations.append("maintain_current_approach")
            
            # Check for oscillation patterns
            oscillations = performance_metrics.get("oscillations", 0)
            if oscillations > 2:
                insights.append(f"Detected {oscillations} oscillation patterns, AI may be indecisive")
                recommendations.append("commit_to_direction")
                adaptation_needed = True
            
            # Generate primary insight
            if insights:
                primary_insight = insights[0]
            else:
                primary_insight = "Standard exploration behavior, no major issues detected"
            
            # Generate behavioral analysis
            behavioral_analysis = f"Movement pattern: {pattern_type}, Efficiency: {nav_efficiency:.2f}, Diversity: {action_diversity} actions"
            
            return {
                "primary_insight": primary_insight,
                "all_insights": insights,
                "recommendations": recommendations[:3],  # Limit to top 3
                "behavioral_analysis": behavioral_analysis,
                "adaptation_needed": adaptation_needed,
                "analysis_confidence": "high" if len(recent_turns) >= 5 else "low"
            }
            
        except Exception as e:
            return {
                "primary_insight": f"Strategic analysis failed: {e}",
                "recommendations": ["continue_current_strategy"],
                "behavioral_analysis": "Analysis error",
                "adaptation_needed": False
            }
    
    def _store_last_periodic_review(self, enhanced_analysis: Dict[str, Any], current_turn: int) -> None:
        """Store the last periodic review result for strategic prompt injection"""
        try:
            # Store in eevee agent for easy access during strategic decisions
            if not hasattr(self.eevee, 'last_periodic_review'):
                self.eevee.last_periodic_review = {}
            
            self.eevee.last_periodic_review = {
                "timestamp": datetime.now().isoformat(),
                "turn": current_turn,
                "analysis": enhanced_analysis,
                "summary": {
                    "movement_pattern": enhanced_analysis.get("movement_pattern_summary", "Unknown"),
                    "key_insight": enhanced_analysis.get("key_insight", "No insights"),
                    "performance_score": enhanced_analysis.get("performance_score", 0.0),
                    "recommendations": enhanced_analysis.get("strategic_recommendations", [])[:2],  # Top 2
                    "goal_progress": enhanced_analysis.get("progress_description", "Unknown progress")
                }
            }
            
            if self.eevee.verbose:
                print(f"📊 Stored periodic review for strategic context injection (Turn {current_turn})")
                
        except Exception as e:
            print(f"WARNING: Failed to store periodic review: {e}")
    
    def _analyze_goal_progress_with_ai(self, recent_turns: List[Dict], session_goal: str) -> Dict[str, Any]:
        """Use AI to analyze progress toward current session goal"""
        try:
            # Build analysis prompt
            turns_summary = []
            for i, turn in enumerate(recent_turns[-5:], 1):  # Last 5 turns
                ai_analysis = turn.get('ai_analysis', {})
                if isinstance(ai_analysis, dict):
                    reasoning = ai_analysis.get('reasoning', 'Unknown')
                    observations = ai_analysis.get('observations', 'Unknown')
                else:
                    reasoning = str(ai_analysis)[:100] + "..."
                    observations = "Legacy format"
                
                turns_summary.append(f"Turn {i}: {reasoning} | Obs: {observations}")
            
            analysis_prompt = f"""
**POKEMON GOAL PROGRESS ANALYSIS**

**Session Goal**: {session_goal}

**Recent Activity** (last {len(recent_turns)} turns):
{chr(10).join(turns_summary)}

**ANALYSIS REQUIRED**:
Please analyze if the AI is making progress toward the goal "{session_goal}".

**RESPONSE FORMAT** (JSON only):
{{
  "goal_status": "in_progress|completed|failed|blocked",
  "progress_score": 7,
  "progress_description": "AI is exploring Pewter City and looking for gym building",
  "needs_replanning": false,
  "issues_detected": ["stuck_in_loop", "wrong_direction"],
  "next_recommended_actions": ["continue_exploration", "try_different_direction"],
  "estimated_turns_to_completion": 15
}}

**KEY CONSIDERATIONS**:
- Is the AI making visual progress toward the goal?
- Are there signs of being stuck or repeating actions?
- Has the goal been achieved or become impossible?
- Should the goal be broken down into smaller subtasks?

Respond with valid JSON only.
"""
            
            # Call AI for analysis
            from llm_api import call_llm
            
            llm_response = call_llm(
                prompt=analysis_prompt,
                provider="mistral",  # Use Mistral for strategic analysis
                max_tokens=500
            )
            
            if llm_response.error:
                return {"success": False, "error": f"LLM error: {llm_response.error}"}
            
            # Parse JSON response
            response_text = llm_response.text.strip()
            
            # Extract JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    analysis_result = json.loads(json_str)
                    
                    # Validate required fields
                    required_fields = ["goal_status", "progress_score", "needs_replanning"]
                    if all(field in analysis_result for field in required_fields):
                        return {
                            "success": True,
                            **analysis_result
                        }
                    else:
                        return {"success": False, "error": "Missing required fields in AI response"}
                else:
                    return {"success": False, "error": "No JSON found in AI response"}
                    
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"JSON parsing failed: {e}"}
            
        except Exception as e:
            return {"success": False, "error": f"Goal progress analysis error: {e}"}
    
    def _update_goal_progress(self, goal_hierarchy, progress_analysis):
        """Update goal hierarchy based on progress analysis"""
        try:
            current_goal = goal_hierarchy.get_current_goal()
            if current_goal:
                # Update progress percentage
                progress_score = progress_analysis.get("progress_score", 0)
                current_goal.progress_percentage = min(100.0, progress_score * 10)  # Convert 0-10 to 0-100
                
                # Update status if needed
                goal_status = progress_analysis.get("goal_status", "in_progress")
                from task_executor import GoalStatus
                
                if goal_status == "completed":
                    current_goal.status = GoalStatus.COMPLETED
                elif goal_status == "failed":
                    current_goal.status = GoalStatus.FAILED
                elif goal_status == "blocked":
                    current_goal.status = GoalStatus.BLOCKED
                else:
                    current_goal.status = GoalStatus.IN_PROGRESS
                
                # Update timestamp
                current_goal.updated_at = datetime.now().isoformat()
                
        except Exception as e:
            print(f"⚠️ Failed to update goal progress: {e}")
    
    def _generate_okr_json(self, goal_hierarchy, progress_analysis) -> Dict[str, Any]:
        """Generate okr.json file with current goal state for AI context"""
        try:
            current_goal = goal_hierarchy.get_current_goal()
            
            if not current_goal:
                return {"success": False, "error": "No active goal found"}
            
            # Create okr.json data structure
            okr_data = {
                "meta": {
                    "updated_at": datetime.now().isoformat(),
                    "session_id": self.session.session_id,
                    "source": "goal_oriented_planning_system"
                },
                "session_goal": self.session.goal,
                "current_goal": {
                    "id": current_goal.id,
                    "name": current_goal.name,
                    "description": current_goal.description,
                    "status": current_goal.status.value,
                    "priority": current_goal.priority,
                    "progress_percentage": current_goal.progress_percentage,
                    "estimated_turns": current_goal.estimated_turns,
                    "attempts": current_goal.attempts,
                    "turns_spent": current_goal.turns_spent
                },
                "goal_hierarchy": {
                    "root_goal": {
                        "id": goal_hierarchy.root_goal.id,
                        "name": goal_hierarchy.root_goal.name,
                        "description": goal_hierarchy.root_goal.description,
                        "children": [child.id for child in goal_hierarchy.root_goal.children]
                    },
                    "total_goals": goal_hierarchy.total_goals,
                    "completed_goals": len(goal_hierarchy.completed_goals),
                    "failed_goals": len(goal_hierarchy.failed_goals)
                },
                "progress_analysis": {
                    "progress_score": progress_analysis.get("progress_score", 0),
                    "progress_description": progress_analysis.get("progress_description", ""),
                    "issues_detected": progress_analysis.get("issues_detected", []),
                    "next_recommended_actions": progress_analysis.get("next_recommended_actions", []),
                    "estimated_turns_to_completion": progress_analysis.get("estimated_turns_to_completion", 10)
                }
            }
            
            # Save okr.json file 
            okr_file_path = Path("okr.json")  # Save in current directory
            with open(okr_file_path, 'w') as f:
                json.dump(okr_data, f, indent=2)
            
            return {
                "success": True,
                "okr_file_path": str(okr_file_path),
                "active_goal_name": current_goal.name,
                "next_actions": progress_analysis.get("next_recommended_actions", [])
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to generate okr.json: {e}"}


def parse_arguments():
    """Parse command line arguments for Eevee v1"""
    parser = argparse.ArgumentParser(
        description="Eevee v1 - AI Pokemon Task Execution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Continuous gameplay with interactive mode
  %(prog)s
  %(prog)s --goal "find and win pokemon battles"
  %(prog)s --goal "navigate to gym and challenge leader" --max-turns 50
  
  # One-shot task mode:
  %(prog)s --task "check my Pokemon party levels and moves"
  %(prog)s --task "navigate to Pokemon Center" --save-report
  
  # With options:
  %(prog)s --interactive --enable-okr
  %(prog)s --continue --verbose
        """
    )
    
    # Task vs continuous mode
    parser.add_argument(
        "--task",
        type=str,
        help="Execute single task and exit (overrides default continuous mode)"
    )
    
    parser.add_argument(
        "--goal",
        type=str,
        default="Explore Pokemon world and win battles",
        help="Goal for continuous gameplay (default: 'Explore Pokemon world and win battles')"
    )
    
    # Gameplay configuration
    parser.add_argument(
        "--max-turns",
        type=int,
        default=100,
        help="Maximum number of gameplay turns (default: 100)"
    )
    
    parser.add_argument(
        "--turn-delay",
        type=float,
        default=2.0,
        help="Seconds between gameplay turns (default: 2.0)"
    )
    
    # Interactive mode (enabled by default for continuous)
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive mode (continuous only)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true", 
        help="Force interactive mode (default for continuous gameplay)"
    )
    
    # AI Model Configuration (uses environment configuration by default)
    from provider_config import get_provider_config
    config = get_provider_config()
    
    parser.add_argument(
        "--model",
        type=str,
        default=config.gameplay_model,
        help=f"AI model to use (default from .env: {config.gameplay_model})"
    )
    
    # Memory and Session Management
    parser.add_argument(
        "--memory-session",
        type=str,
        default="default",
        help="Memory session name (default: 'default')"
    )
    
    parser.add_argument(
        "--clear-memory",
        action="store_true",
        help="Clear memory session before starting"
    )
    
    parser.add_argument(
        "--continue",
        action="store_true",
        dest="continue_session",
        help="Resume from last session"
    )
    
    # Output and Reporting
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save detailed report to file"
    )
    
    parser.add_argument(
        "--episode-review-frequency",
        type=int,
        default=100,
        help="Generate episode review every N turns (default: 100, 0 to disable)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with extra logging"
    )
    
    # Advanced Features
    parser.add_argument(
        "--enable-okr",
        action="store_true",
        default=True,
        help="Enable OKR.md progress tracking (default: True)"
    )
    
    
    # Emulator Configuration
    parser.add_argument(
        "--window-title",
        type=str,
        default="SkyEmu",
        help="Emulator window title (default: 'SkyEmu')"
    )
    
    return parser.parse_args()


def setup_environment():
    """Setup Eevee v1 directory structure and environment"""
    eevee_dir = Path(__file__).parent
    
    # Create required directories
    directories = [
        eevee_dir / "memory",
        eevee_dir / "reports", 
        eevee_dir / "runs",
        eevee_dir / "prompts",
        eevee_dir / "utils"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
    
    return eevee_dir


def print_startup_banner(args):
    """Print Eevee v1 startup banner"""
    print("=" + "="*61)
    print("= EEVEE v1 - AI Pokemon Task Execution System")
    print("=" + "="*61)
    
    if args.task:
        print(f"- Mode: Single Task Execution")
        print(f"- Task: {args.task}")
    else:
        print(f"- Mode: Continuous Gameplay with Interactive Chat")
        print(f"- Goal: {args.goal}")
        print(f"- Max turns: {args.max_turns}")
        interactive = not args.no_interactive
        print(f"- Interactive: {' Enabled' if interactive else ' Disabled'}")
    
    print(f"> Model: {args.model}")
    print(f"- Memory Session: {args.memory_session}")
    print(f"- Window: {args.window_title}")
    print("=" + "="*61)


def execute_single_task(eevee: EeveeAgent, task: str) -> Dict[str, Any]:
    """Execute a single task and return results"""
    print(f"- Executing task: {task}")
    
    try:
        # Use task executor if available
        if hasattr(eevee, 'task_executor') and eevee.task_executor:
            result = eevee.task_executor.execute_task(task, max_steps=20)
        else:
            # Fallback to basic execution
            result = execute_basic_task(eevee, task)
        
        return {
            "task": task,
            "status": "completed" if result.get("success") else "failed",
            "analysis": result.get("analysis", "Task execution completed"),
            "steps_executed": result.get("steps", 1),
            "execution_time": result.get("execution_time", 0)
        }
        
    except Exception as e:
        print(f"L Task execution failed: {e}")
        return {
            "task": task,
            "status": "failed",
            "error": str(e),
            "steps_executed": 0,
            "execution_time": 0
        }


def execute_basic_task(eevee: EeveeAgent, task: str) -> Dict[str, Any]:
    """Basic task execution fallback"""
    start_time = time.time()
    
    # Capture current game state
    try:
        screenshot_path = eevee.controller.capture_screen()
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return {"success": False, "error": f"Screenshot capture failed: {e}"}
    
    # Build task prompt
    prompt = f"""# Pokemon Task Execution Expert

**TASK**: {task}

**INSTRUCTIONS**:
1. Analyze the current Pokemon game screenshot
2. Determine what actions are needed to complete: {task}
3. Provide step-by-step analysis
4. Use pokemon_controller tool if actions are needed

Analyze the current game state and explain how to complete this task."""
    
    # Call AI
    try:
        api_result = eevee._call_gemini_api(
            prompt=prompt,
            image_data=image_data,
            use_tools=True,
            max_tokens=1500
        )
        
        if api_result["error"]:
            return {"success": False, "error": api_result["error"]}
        
        # Execute any button presses
        if api_result.get("button_presses"):
            eevee.controller.press_sequence(api_result["button_presses"], delay_between=1.0)
        
        return {
            "success": True,
            "analysis": api_result.get("text", "Task completed"),
            "actions": api_result.get("button_presses", []),
            "execution_time": time.time() - start_time
        }
        
    except Exception as e:
        return {"success": False, "error": f"AI execution failed: {e}"}


def save_session_report(session_summary: Dict[str, Any], eevee_dir: Path):
    """Save session report to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = eevee_dir / "reports" / f"session_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(session_summary, f, indent=2)
    
    print(f"- Session report saved: {report_file}")
    return report_file


def main():
    """Main Eevee v1 execution function"""
    try:
        # Parse arguments and setup
        args = parse_arguments()
        eevee_dir = setup_environment()
        print_startup_banner(args)
        
        # Initialize Eevee agent
        print("- Initializing Eevee AI system...")
        
        try:
            eevee = EeveeAgent(
                window_title=args.window_title,
                model=args.model,
                memory_session=args.memory_session,
                verbose=args.verbose,
                debug=args.debug,
                enable_neo4j=True,  # Neo4j is now mandatory
                enable_okr=args.enable_okr
            )
            print(" Eevee agent initialized successfully")
            
            # PHASE 2: Enhance with memory system (now mandatory)
            if MEMORY_INTEGRATION_AVAILABLE:
                print("🧠 PHASE 2: Enhancing Eevee with mandatory memory integration...")
                try:
                    success = create_memory_enhanced_eevee(eevee, args.memory_session)
                    if success:
                        print("✅ Memory-enhanced Eevee activated!")
                    else:
                        print("❌ CRITICAL: Memory enhancement failed - Neo4j is required")
                        sys.exit(1)
                except Exception as e:
                    print(f"❌ CRITICAL: Memory integration error: {e} - Neo4j is required")
                    sys.exit(1)
            else:
                print("❌ CRITICAL: Memory integration not available - check neo4j_compact_reader import")
                sys.exit(1)
                    
        except Exception as e:
            print(f"L Failed to initialize Eevee agent: {e}")
            sys.exit(1)
        
        # Clear memory if requested
        if args.clear_memory and eevee.memory:
            print(f"- Clearing memory session: {args.memory_session}")
            eevee.memory.clear_session()
        
        # Determine execution mode
        if args.task:
            # Single task execution mode
            result = execute_single_task(eevee, args.task)
            
            # Print results
            print(f"\n Task execution completed!")
            print(f"Status: {result['status']}")
            print(f"Analysis: {result['analysis']}")
            
            # Save report if requested
            if args.save_report:
                report_file = eevee_dir / "reports" / f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"- Report saved: {report_file}")
            
        else:
            # Continuous gameplay mode (default)
            interactive = not args.no_interactive  # Interactive by default
            
            print(f"\n- Starting continuous Pokemon gameplay...")
            print(f"- Goal: {args.goal}")
            print(f"- Interactive mode: {' Enabled' if interactive else ' Disabled'}")
            
            if interactive:
                print(f"\n- While playing, you can:")
                print(f"   - Type /pause to pause")
                print(f"   - Type /status to check progress")
                print(f"   - Type any task for the AI to consider")
                print(f"   - Type /help for all commands")
            
            print(f"\n{'='*60}")
            
            # Initialize continuous gameplay
            gameplay = ContinuousGameplay(eevee, interactive=interactive, episode_review_frequency=args.episode_review_frequency)
            
            # Start session
            gameplay.start_session(args.goal, args.max_turns)
            gameplay.turn_delay = args.turn_delay
            
            try:
                # Run the main gameplay loop
                session_summary = gameplay.run_continuous_loop()
                
                # Print final results
                print(f"\n- Gameplay session completed!")
                print(f"- Status: {session_summary['status']}")
                print(f"= Turns: {session_summary['turns_completed']}/{session_summary['max_turns']}")
                print(f"- User interactions: {session_summary['user_interactions']}")
                
                # OLD EPISODE REVIEWER SYSTEM - DISABLED (replaced by AI-powered periodic review)
                # The new AI-powered review system runs during gameplay every N turns
                # This old system conflicts with the new one and has been replaced
                
                # if args.episode_review_frequency > 0 and session_summary['turns_completed'] >= args.episode_review_frequency:
                #     try:
                #         from episode_reviewer import EpisodeReviewer
                #         reviewer = EpisodeReviewer(eevee_dir)
                #         [... old episode review code disabled ...]
                #     except Exception as e:
                #         print(f"WARNING: Episode review failed: {e}")
                
                print(f"\n✅ AI-powered learning system handled prompt improvements during gameplay")
                
                # Save session report
                if args.save_report:
                    save_session_report(session_summary, eevee_dir)
                
            except KeyboardInterrupt:
                print(f"\n�  Gameplay interrupted by user")
                session_summary = gameplay._get_session_summary()
                session_summary["status"] = "interrupted"
                
                if args.save_report:
                    save_session_report(session_summary, eevee_dir)
        
        print(f"\n=K Eevee session ended. Goodbye!")
        
    except Exception as e:
        print(f"L Unexpected error: {e}")
        if args.debug if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()