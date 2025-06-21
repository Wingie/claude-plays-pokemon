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
    python run_eevee.py --interactive --enable-okr --neo4j-memory
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
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict

# Add paths for importing from the main project
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))

try:
    from eevee_agent import EeveeAgent
    from memory_system import MemorySystem
    from prompt_manager import PromptManager
    from task_executor import TaskExecutor
    from utils.navigation_enhancement import NavigationEnhancer
except ImportError as e:
    print(f"⚠️  Core Eevee components not available: {e}")
    print("Starting with basic implementation...")
    # We'll implement basic functionality inline if needed


@dataclass
class GameplaySession:
    """Represents a continuous gameplay session"""
    session_id: str
    start_time: str
    goal: str
    turns_completed: int = 0
    max_turns: int = 100
    status: str = "running"  # running, paused, completed, error
    last_action: str = ""
    last_analysis: str = ""
    user_interactions: List[str] = None
    
    def __post_init__(self):
        if self.user_interactions is None:
            self.user_interactions = []


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
        print("\n=� Interactive mode active. Commands:")
        print("   /pause - Pause gameplay")
        print("   /resume - Resume gameplay") 
        print("   /status - Show current status")
        print("   /help - Show all commands")
        print("   /quit - Exit")
        print("   Or type any task for the AI...")
        
        while self.running:
            try:
                user_input = input("\n<� You: ").strip()
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
        
        # Enhanced navigation system
        self.nav_enhancer = NavigationEnhancer(history_size=20, similarity_threshold=0.95)
        
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
        
        print(f"🎮 Starting continuous Pokemon gameplay")
        print(f"📁 Session: {session_id}")
        print(f"<� Goal: {goal}")
        print(f"=� Max turns: {max_turns}")
        print(f"= Turn delay: {self.turn_delay}s")
        
        if self.interactive:
            self.interactive_controller = InteractiveController()
            self.interactive_controller.start_input_thread()
            print(f"=� Interactive mode enabled - type commands anytime")
        
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
                
                # Step 2: Get AI analysis and decision
                ai_result = self._get_ai_decision(game_context, turn_count)
                
                # Step 3: Execute AI's chosen action
                execution_result = self._execute_ai_action(ai_result)
                
                # Step 4: Update memory and session state
                self._update_session_state(turn_count, ai_result, execution_result)
                
                # Step 4.1: Update session data file for episode reviewer
                self._update_session_data_file(turn_count, ai_result, execution_result)
                
                # Step 4.5: Periodic episode review check
                if hasattr(self, 'episode_review_frequency') and self.episode_review_frequency > 0:
                    if turn_count % self.episode_review_frequency == 0:
                        print(f"\n🔍 PERIODIC EPISODE REVIEW: Analyzing last {self.episode_review_frequency} turns...")
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
        
        return self._get_session_summary()
    
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
    
    def _get_ai_decision(self, game_context: Dict[str, Any], turn_number: int) -> Dict[str, Any]:
        """Get AI analysis and action decision"""
        if not game_context.get("screenshot_data"):
            return {
                "analysis": "No game data available",
                "action": ["a"],  # Default action
                "reasoning": "Screenshot capture failed, using default action"
            }
        
        # Build context-aware prompt
        memory_context = self._get_memory_context()
        prompt_data = self._build_ai_prompt(turn_number, memory_context)
        prompt = prompt_data.get("prompt", prompt_data) if isinstance(prompt_data, dict) else prompt_data
        
        # Call Gemini API
        try:
            api_result = self.eevee._call_gemini_api(
                prompt=prompt,
                image_data=game_context["screenshot_data"],
                use_tools=True,
                max_tokens=1000
            )
            
            if api_result["error"]:
                return {
                    "analysis": f"API Error: {api_result['error']}",
                    "action": ["a"],
                    "reasoning": "API call failed, using default action"
                }
            
            # Enhanced logging with clear observation-to-action chain
            analysis_text = api_result.get("text", "No analysis provided")
            button_sequence = api_result.get("button_presses", ["a"])
            
            # DEBUG: Check what we got from API
            if self.eevee.verbose:
                print(f"🔍 DEBUG - API Response Length: {len(analysis_text)}")
                print(f"🔍 DEBUG - Has button_presses: {bool(api_result.get('button_presses'))}")
                if len(analysis_text) < 50:
                    print(f"🔍 DEBUG - Short response: '{analysis_text}'")
            
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
            
            return result
            
        except Exception as e:
            return {
                "analysis": f"Exception: {str(e)}",
                "action": ["a"],
                "reasoning": "Exception occurred, using default action"
            }
    
    def _execute_ai_action(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the AI's chosen action with button press validation"""
        actions = ai_result.get("action", ["a"])
        
        if not isinstance(actions, list):
            actions = [actions]
        
        # VALIDATION: Enforce 1-3 button maximum as requested by user
        if len(actions) > 3:
            print(f"⚠️ AI tried to press {len(actions)} buttons: {actions}")
            print(f"⚠️ Limiting to first 3 buttons for step-by-step learning")
            actions = actions[:3]
        
        # Additional validation: ensure valid button names
        valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
        validated_actions = []
        for action in actions:
            if isinstance(action, str) and action.lower() in valid_buttons:
                validated_actions.append(action.lower())
            else:
                print(f"⚠️ Invalid button '{action}' ignored")
        
        # Fallback to 'a' if no valid actions
        if not validated_actions:
            print(f"⚠️ No valid buttons found, using default 'a'")
            validated_actions = ['a']
        
        # LOOP DETECTION: Track patterns for informational purposes only
        if not hasattr(self, '_last_three_actions'):
            self._last_three_actions = []
        self._last_three_actions.append(validated_actions)
        if len(self._last_three_actions) > 3:
            self._last_three_actions.pop(0)
        
        # INFORMATION ONLY: Alert about repetitive patterns without overriding
        if hasattr(self, '_last_three_actions') and len(self._last_three_actions) >= 3:
            if all(action == validated_actions for action in self._last_three_actions[-3:]):
                print(f"ℹ️  PATTERN ALERT: Action {validated_actions} repeated 3 times - AI should consider alternatives")
        
        try:
            # Execute button sequence
            success = self.eevee.controller.press_sequence(validated_actions, delay_between=0.5)
            
            # Record this turn's action for recent context
            observation = ai_result.get("analysis", "")  # Full observation, no truncation
            result_text = "success" if success else "failed"
            turn_number = getattr(self.session, 'turns_completed', 0) + 1
            self._record_turn_action(turn_number, observation, validated_actions, result_text)
            
            # ENHANCED: Add navigation analysis after action execution
            reasoning_text = ai_result.get("reasoning", "No reasoning provided")
            # Pass the screenshot path from last game_context
            screenshot_path = self._last_game_context.get("screenshot_path") if hasattr(self, '_last_game_context') else None
            nav_analysis = self._analyze_navigation_progress(turn_number, validated_actions, reasoning_text, screenshot_path)
            
            return {
                "success": success,
                "actions_executed": validated_actions,
                "original_actions": actions,  # Keep track of what AI originally wanted
                "execution_time": datetime.now().isoformat(),
                "navigation_analysis": nav_analysis  # Include navigation insights
            }
            
        except Exception as e:
            print(f"�  Action execution failed: {e}")
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
                    print(f"�  Memory storage failed: {e}")
    
    def _update_session_data_file(self, turn_number: int, ai_result: Dict[str, Any], execution_result: Dict[str, Any]):
        """Update session data file for episode reviewer"""
        if not hasattr(self, 'session_data_file') or not hasattr(self, 'session_turns'):
            return
        
        try:
            # Create turn data in the format expected by episode reviewer
            turn_data = {
                "turn": turn_number,
                "timestamp": datetime.now().isoformat(),
                "ai_analysis": ai_result.get("analysis", ""),
                "button_presses": ai_result.get("action", []),
                "action_result": execution_result.get("success", False),
                "screenshot_path": f"screenshot_{turn_number}.png",
                "execution_time": execution_result.get("execution_time", 0.0),
                # Add template tracking information
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
                print(f"⚠️ Failed to update session data file: {e}")
    
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
        print(f"<� User task received: {task}")
        print("=� Task will influence AI decision in next turn")
        
        # Store task for AI context
        if hasattr(self, '_user_tasks'):
            self._user_tasks.append(task)
        else:
            self._user_tasks = [task]
    
    def _show_status(self):
        """Show current gameplay status"""
        print(f"\n=� Gameplay Status:")
        print(f"   Turn: {self.session.turns_completed}/{self.session.max_turns}")
        print(f"   Status: {'� Paused' if self.paused else '� Running'}")
        print(f"   Goal: {self.session.goal}")
        print(f"   Last Action: {self.session.last_action}")
        print(f"   Session ID: {self.session.session_id}")
    
    def _show_help(self):
        """Show available commands"""
        print(f"\n=� Available Commands:")
        print(f"   /pause  - Pause gameplay")
        print(f"   /resume - Resume gameplay")
        print(f"   /status - Show current status")
        print(f"   /quit   - Stop gameplay")
        print(f"   /help   - Show this help")
        print(f"\n=� Or type any Pokemon task for the AI to consider")
    
    def _get_memory_context(self) -> str:
        """Get relevant memory context for AI"""
        if not self.eevee.memory:
            return ""
        
        try:
            return self.eevee.memory.get_recent_gameplay_summary(limit=5)
        except:
            return ""
    
    def _record_turn_action(self, turn_number: int, observation: str, action: List[str], result: str):
        """Record a turn's action for recent context with progress tracking"""
        
        # Get navigation analysis if available
        nav_progress = False
        visual_similarity = 0.0
        if hasattr(self, 'nav_enhancer'):
            # Check if we have recent turn data with progress info
            if self.nav_enhancer.turn_history:
                last_turn = self.nav_enhancer.turn_history[-1]
                nav_progress = last_turn.progress_made
                visual_similarity = last_turn.visual_similarity
        
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
            
            # Enhanced summary with progress tracking
            progress_indicator = "✅" if progress else "❌" if similarity > 0.95 else "?"
            summary += f"Turn {turn_num}: {progress_indicator} Observed '{obs}' → Pressed {actions} → {result}\n"
        
        # Enhanced pattern detection with progress analysis
        if len(self.recent_turns) >= 3:
            last_actions = [turn["action"] for turn in self.recent_turns[-3:]]
            last_progress = [turn.get("progress_made", False) for turn in self.recent_turns[-3:]]
            
            if all(action == last_actions[0] for action in last_actions):
                summary += "🚨 CRITICAL: You've been repeating the same action. Try a different approach!\n"
                
            if not any(last_progress):
                summary += "⚠️ WARNING: No visual progress in last 3 turns. Consider changing strategy.\n"
        
        return summary
    
    def _determine_prompt_context(self, memory_context: str) -> tuple[str, List[str]]:
        """
        Enhanced context detection using memory, recent actions, and goal analysis
        
        Args:
            memory_context: Recent memory/gameplay context
            
        Returns:
            Tuple of (prompt_type, list_of_relevant_playbooks)
        """
        context_lower = memory_context.lower()
        user_goal = self.session.goal.lower()
        
        # HIGHEST PRIORITY: Battle detection (most critical for Pokemon gameplay)
        if self._detect_battle_context(context_lower):
            prompt_type = "battle_analysis"
            playbooks = ["battle"]
            
            # Enhanced gym battle detection
            if any(keyword in context_lower for keyword in ["gym", "leader", "badge"]) or \
               any(keyword in user_goal for keyword in ["gym", "leader", "badge"]):
                playbooks.append("gyms")
            
            return prompt_type, playbooks
        
        # HIGH PRIORITY: Stuck navigation detection (but only if NOT in battle)
        if hasattr(self, 'nav_enhancer') and self.nav_enhancer.stuck_mode:
            # Skip stuck detection if we're in a battle - battles naturally involve repeated A presses
            if not self._detect_battle_context(context_lower):
                prompt_type = "stuck_recovery"
                playbooks = ["navigation"]
                return prompt_type, playbooks
        
        # Check for user recovery tasks (but only if NOT in battle)
        recent_tasks = getattr(self, '_user_tasks', [])
        if any("STUCK RECOVERY" in task for task in recent_tasks):
            # Skip stuck recovery if we're in a battle
            if not self._detect_battle_context(context_lower):
                prompt_type = "stuck_recovery"
                playbooks = ["navigation"] 
                return prompt_type, playbooks
                
        # PARTY MANAGEMENT: Pokemon party analysis
        elif self._detect_party_context(context_lower, user_goal):
            prompt_type = "pokemon_party_analysis"
            playbooks = ["battle"]  # Party management uses battle knowledge for moves/types
            # Continue to goal-based enhancements
            
        # INVENTORY MANAGEMENT: Bag and items
        elif self._detect_inventory_context(context_lower, user_goal):
            prompt_type = "inventory_analysis" 
            playbooks = ["services"]  # Inventory management relates to shops/services
            # Continue to goal-based enhancements
            
        # SERVICES: Pokemon Centers, shops, healing
        elif self._detect_services_context(context_lower, user_goal):
            prompt_type = "exploration_strategy"
            playbooks = ["services"]
            # Continue to goal-based enhancements
            
        # NAVIGATION: Movement and exploration (default fallback)
        else:
            prompt_type = "exploration_strategy"
            playbooks = ["navigation"]
            
            # Add navigation-specific context detection
            if any(keyword in context_lower for keyword in ["route", "forest", "cave", "city", "town"]):
                # Area exploration context
                pass  # Keep navigation playbook
            
        # GOAL-BASED ENHANCEMENTS: Add playbooks based on user goal
        if "gym" in user_goal and "gyms" not in playbooks:
            playbooks.append("gyms")
        elif any(keyword in user_goal for keyword in ["heal", "center", "shop"]) and "services" not in playbooks:
            playbooks.append("services")
        elif any(keyword in user_goal for keyword in ["party", "pokemon", "level", "moves"]) and "battle" not in playbooks:
            playbooks.append("battle")
            
        return prompt_type, playbooks
    
    def _detect_battle_context(self, context_lower: str) -> bool:
        """Detect if currently in a Pokemon battle"""
        # Specific battle UI indicators
        battle_ui_keywords = [
            "wild", "trainer", "battle", "fainted", "defeated",
            "caterpie", "pidgey", "rattata", "weedle", "kakuna", "metapod",  # Common wild Pokemon
            "brock", "misty", "surge", "erika", "sabrina", "koga", "blaine", "giovanni",  # Gym leaders
        ]
        
        # Battle menu and action keywords
        battle_action_keywords = [
            "fight", "bag", "pokemon", "run",  # Main battle menu
            "growl", "tackle", "scratch", "thundershock", "water gun", "ember",  # Common moves
            "hp", "pp", "attack", "defense", "speed", "special",  # Battle stats
            "super effective", "not very effective", "critical hit",  # Battle messages
        ]
        
        # Look for any battle-related keywords
        all_battle_keywords = battle_ui_keywords + battle_action_keywords
        return any(keyword in context_lower for keyword in all_battle_keywords)
    
    def _detect_party_context(self, context_lower: str, user_goal: str) -> bool:
        """Detect Pokemon party management tasks"""
        party_keywords = ["party", "pokemon", "level", "moves", "pp", "health", "status", "healing"]
        goal_keywords = ["check", "report", "show", "analyze", "party"]
        
        return any(keyword in context_lower for keyword in party_keywords) or \
               any(keyword in user_goal.lower() for keyword in goal_keywords)
    
    def _detect_inventory_context(self, context_lower: str, user_goal: str) -> bool:
        """Detect inventory/bag management tasks"""
        inventory_keywords = ["bag", "items", "inventory", "potion", "ball", "healing", "repel"]
        goal_keywords = ["items", "bag", "inventory", "check items", "healing items"]
        
        return any(keyword in context_lower for keyword in inventory_keywords) or \
               any(keyword in user_goal.lower() for keyword in goal_keywords)
    
    def _detect_services_context(self, context_lower: str, user_goal: str) -> bool:
        """Detect Pokemon Center, shop, or service interactions"""
        service_keywords = ["pokemon center", "healing", "shop", "buy", "sell", "nurse", "mart", "pokemart"]
        goal_keywords = ["heal", "center", "shop", "buy", "nurse"]
        
        return any(keyword in context_lower for keyword in service_keywords) or \
               any(keyword in user_goal.lower() for keyword in goal_keywords)
    
    # 🧠 NEW AI-DIRECTED CONTEXT DETECTION METHODS
    
    def _determine_ai_context(self, memory_context: str, recent_actions: List[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Determine appropriate AI-directed prompt context with enhanced data
        
        Args:
            memory_context: Recent memory/gameplay context
            recent_actions: List of recent button actions
            
        Returns:
            Tuple of (context_type, context_data_dict)
        """
        context_lower = memory_context.lower()
        user_goal = self.session.goal.lower()
        recent_actions = recent_actions or []
        
        context_data = {
            "battle_context": {},
            "maze_context": {},
            "forest_context": {},
            "cave_context": {}
        }
        
        # BATTLE CONTEXT (highest priority)
        if self._detect_battle_context(context_lower):
            context_data["battle_context"] = {
                "battle_phase": self._detect_battle_phase(context_lower),
                "is_gym_battle": any(keyword in context_lower for keyword in ["gym", "leader", "badge"]),
                "recent_battle_actions": [action for action in recent_actions if action in ['a', 'up', 'down', 'left', 'right']]
            }
            return "battle", context_data
        
        # EMERGENCY CONTEXT (if stuck patterns detected)
        stuck_level = self._get_escalation_level()
        if stuck_level != "level_1":
            context_data["emergency_context"] = {
                "escalation_level": stuck_level,
                "stuck_patterns": self._analyze_stuck_patterns(recent_actions),
                "attempts_count": len([action for action in recent_actions if action == recent_actions[-1]]) if recent_actions else 0
            }
            return "emergency", context_data
        
        # MAZE/CAVE CONTEXT
        if any(keyword in context_lower for keyword in ["cave", "tunnel", "rock", "ladder", "stairs", "level"]):
            context_data["cave_context"] = {
                "is_multilevel": any(keyword in context_lower for keyword in ["stairs", "ladder", "level"]),
                "area_name": self._extract_location_name(context_lower),
                "rock_formations": "rock" in context_lower
            }
            return "maze", context_data
        
        # FOREST CONTEXT  
        elif any(keyword in context_lower for keyword in ["forest", "viridian forest", "trees", "dense"]):
            context_data["forest_context"] = {
                "forest_name": self._extract_location_name(context_lower),
                "is_dense": any(keyword in context_lower for keyword in ["dense", "thick"]),
                "has_trainers": "trainer" in context_lower
            }
            return "navigation", context_data  # Use navigation with forest context
        
        # DEFAULT NAVIGATION CONTEXT
        else:
            return "navigation", context_data
    
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
    
    def _analyze_stuck_patterns(self, recent_actions: List[str]) -> Dict[str, Any]:
        """Analyze recent actions for stuck patterns"""
        if not recent_actions:
            return {"pattern": "none", "severity": "low"}
        
        # Count consecutive identical actions
        consecutive_count = 1
        if len(recent_actions) > 1:
            for i in range(len(recent_actions) - 2, -1, -1):
                if recent_actions[i] == recent_actions[-1]:
                    consecutive_count += 1
                else:
                    break
        
        # Determine pattern severity
        if consecutive_count >= 5:
            severity = "critical"
        elif consecutive_count >= 3:
            severity = "high"
        elif consecutive_count >= 2:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "pattern": f"consecutive_{recent_actions[-1]}" if recent_actions else "none",
            "severity": severity,
            "count": consecutive_count,
            "last_action": recent_actions[-1] if recent_actions else None
        }
    
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
            print(f"⚠️  LOOP WARNING: {recent_actions}")
        
        # Show full AI reasoning
        print(f"💭 FULL AI REASONING:")
        print(f"   {analysis_text}")
        print(f"{'='*60}")
    
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
    
    def _build_ai_prompt(self, turn_number: int, memory_context: str) -> Dict[str, Any]:
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
                "stuck_problem": self._get_stuck_problem_description(),
            }
            
            try:
                # Get recent actions for context analysis
                recent_actions_list = self._get_recent_action_list()
                
                # Determine appropriate context for AI-directed prompts
                context_type, context_data = self._determine_ai_context(memory_context, recent_actions_list)
                
                # Initialize variables to avoid UnboundLocalError
                playbooks = []
                prompt_type = "fallback"
                template_used = "fallback"
                template_version = "unknown"
                
                # Try AI-directed prompt system first
                if hasattr(prompt_manager, 'get_ai_directed_prompt'):
                    prompt = prompt_manager.get_ai_directed_prompt(
                        context_type=context_type,
                        task=self.session.goal,
                        recent_actions=recent_actions_list or [],
                        available_memories=self._get_available_memory_contexts(),
                        battle_context=context_data.get('battle_context'),
                        maze_context=context_data.get('maze_context'),
                        escalation_level=self._get_escalation_level(),
                        verbose=True
                    )
                    
                    # AI-directed system is working - skip the confusing fallback logging
                    using_ai_directed = True
                    template_used = f"ai_directed_{context_type}"
                    template_version = "ai_directed"
                
                else:
                    # Fallback to original prompt system
                    prompt_type, playbooks = self._determine_prompt_context(memory_context)
                    prompt = prompt_manager.get_prompt(
                        prompt_type, 
                        variables, 
                        include_playbook=playbooks[0] if playbooks else None,
                        verbose=True
                    )
                    using_ai_directed = False
                    template_used = prompt_type
                    # Get template version if available
                    if hasattr(prompt_manager, 'base_prompts') and prompt_type in prompt_manager.base_prompts:
                        template_version = prompt_manager.base_prompts[prompt_type].get('version', 'unknown')
                
                    # Add additional playbook context if multiple playbooks are relevant
                    if len(playbooks) > 1:
                        for additional_playbook in playbooks[1:]:
                            if additional_playbook in prompt_manager.playbooks:
                                prompt += f"\n\n## Additional Knowledge from {additional_playbook.title()}:\n"
                                prompt += prompt_manager.playbooks[additional_playbook]
                
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
                if self.eevee.verbose:
                    print(f"⚠️ Prompt manager failed, using fallback: {e}")
                print(f"📖 Using fallback prompt (no template)")
                prompt = self._build_fallback_prompt(turn_number, memory_context, recent_task)
                template_used = "fallback_exception"
                template_version = "fallback"
        else:
            print(f"📖 Using fallback prompt (no prompt manager)")
            prompt = self._build_fallback_prompt(turn_number, memory_context, recent_task)
            template_used = "fallback_no_manager"
            template_version = "fallback"
        
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
    
    def _build_fallback_prompt(self, turn_number: int, memory_context: str, recent_task: str) -> str:
        """Build fallback prompt when prompt manager is unavailable"""
        # Add OKR context if enabled
        okr_context = ""
        if self.eevee.enable_okr:
            okr_context = self.eevee.get_okr_context()
            if self.eevee.verbose:
                print(f"📊 OKR Context (fallback) included: {len(okr_context)} characters")
        
        return f"""# Pokemon Fire Red AI Expert - Turn {turn_number}

**GOAL**: {self.session.goal}

**USER INSTRUCTION**: {recent_task if recent_task else "Continue autonomous gameplay"}

**RECENT MEMORY**: {memory_context}
{okr_context}
**GAMEPLAY CONTEXT**:
- Turn {turn_number} of {self.session.max_turns}
- Continuous autonomous gameplay with user guidance
- Focus on efficient progress toward goal

**ANALYSIS TASK**:
🎯 **OBSERVE**: What's visible in the current game state?
🧠 **ANALYZE**: How does this help achieve the goal? 
⚡ **ACT**: Choose the best button press(es) for progress

Analyze the screenshot and decide your next action to progress toward the goal.
Use the pokemon_controller tool with a list of button presses."""
    
    def _get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        return {
            "session_id": self.session.session_id,
            "status": self.session.status,
            "goal": self.session.goal,
            "turns_completed": self.session.turns_completed,
            "max_turns": self.session.max_turns,
            "start_time": self.session.start_time,
            "end_time": datetime.now().isoformat(),
            "user_interactions": len(self.session.user_interactions),
            "last_analysis": self.session.last_analysis,
            "last_action": self.session.last_action
        }
    
    def _run_periodic_episode_review(self, current_turn: int):
        """Run AI-powered periodic episode review and apply prompt improvements automatically"""
        try:
            print(f"🔍 PERIODIC EPISODE REVIEW (Turn {current_turn}): Analyzing last {self.episode_review_frequency} turns...")
            
            # Get recent turns for analysis
            recent_turns = self.session_turns[-self.episode_review_frequency:] if hasattr(self, 'session_turns') else []
            
            if not recent_turns:
                print("⚠️ No recent turns available for analysis")
                return
            
            # Run AI-powered analysis and template improvement
            improvement_result = self._run_ai_powered_review(recent_turns, current_turn)
            
            if improvement_result["success"]:
                changes_applied = improvement_result["changes_applied"]
                
                if changes_applied > 0:
                    print(f"\n🔧 AI-POWERED PROMPT LEARNING: Applied {changes_applied} improvements")
                    
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
                    print(f"\n✅ EXCELLENT PERFORMANCE: No prompt improvements needed")
                    print(f"   Current templates are performing optimally")
            else:
                print(f"\n❌ AI REVIEW FAILED: {improvement_result.get('message', 'Unknown error')}")
                if improvement_result.get('error'):
                    print(f"   Error details: {improvement_result['error']}")
                
        except Exception as e:
            print(f"⚠️ Periodic episode review failed: {e}")
            if hasattr(self.eevee, 'debug') and self.eevee.debug:
                import traceback
                traceback.print_exc()
                
    def _run_ai_powered_review(self, recent_turns: List[Dict], current_turn: int) -> Dict[str, Any]:
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
        
        # Detect stuck patterns in recent turns
        stuck_patterns = self._detect_stuck_patterns_in_turns(recent_turns)
        
        for i, turn in enumerate(recent_turns):
            template_used = turn.get("template_used", "unknown")
            template_version = turn.get("template_version", "unknown")
            
            # Enhanced failure detection: not just action_result, but also stuck patterns
            action_result = turn.get("action_result", False)
            is_stuck_turn = i in stuck_patterns  # This turn is part of a stuck pattern
            
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
    
    def _detect_stuck_patterns_in_turns(self, recent_turns: List[Dict]) -> List[int]:
        """Detect which turn indices are part of stuck/loop patterns"""
        stuck_turn_indices = []
        
        if len(recent_turns) < 3:
            return stuck_turn_indices
        
        # Look for consecutive identical actions (like the ['a'] repeated 3 times we saw)
        for i in range(len(recent_turns) - 2):
            current_action = recent_turns[i].get("button_presses", [])
            next_action = recent_turns[i + 1].get("button_presses", [])
            third_action = recent_turns[i + 2].get("button_presses", [])
            
            # If 3 consecutive turns have the same action, mark them as stuck
            if current_action == next_action == third_action and current_action:
                stuck_turn_indices.extend([i, i + 1, i + 2])
        
        return list(set(stuck_turn_indices))  # Remove duplicates
    
    def _identify_templates_needing_improvement(self, recent_turns: List[Dict], template_stats: Dict[str, Any]) -> List[Dict]:
        """Use AI to identify which templates need improvement based on performance patterns"""
        
        # Only consider templates that are actually used in template selection
        # Get the list of valid template names from _determine_prompt_context
        valid_templates = {
            "battle_analysis", "exploration_strategy", "stuck_recovery", 
            "pokemon_party_analysis", "inventory_analysis", "task_analysis"
        }
        
        # Filter to only templates that have poor performance and are in our valid set
        candidates = []
        for template_name, stats in template_stats.items():
            # Skip templates that aren't in our selection system or have no failures
            if template_name not in valid_templates or stats["failure_count"] == 0:
                continue
                
            # Consider templates with success rate below 70% or multiple failures
            if stats["success_rate"] < 0.7 or stats["failure_count"] >= 2:
                candidates.append({
                    "template_name": template_name,
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
                print(f"⚠️ AI analysis failed: {api_result['error']}")
                return []
            
            # Parse the AI response to extract template improvement recommendations
            analysis_text = api_result.get("text", "")
            return self._parse_template_analysis_response(analysis_text, candidates)
            
        except Exception as e:
            print(f"⚠️ Template analysis failed: {e}")
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
                ai_analysis = turn.get("ai_analysis", "No analysis")[:200] + "..."
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
                print(f"⚠️ Failed to parse template analysis section: {e}")
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
                print(f"⚠️ Template improvement failed: {api_result['error']}")
                return ""
            
            improved_content = api_result.get("text", "").strip()
            
            # Basic validation - ensure the improved template is different and substantial
            if len(improved_content) < 100:
                print(f"⚠️ Improved template too short: {len(improved_content)} chars")
                return ""
            
            if improved_content == current_template.get('template', ''):
                print(f"⚠️ Improved template identical to original")
                return ""
            
            return improved_content
            
        except Exception as e:
            print(f"⚠️ Template improvement with AI failed: {e}")
            return ""
    
    def _get_current_template_content(self, template_name: str) -> Dict[str, Any]:
        """Get current template content from the prompt manager"""
        try:
            if hasattr(self.eevee, 'prompt_manager') and self.eevee.prompt_manager:
                if hasattr(self.eevee.prompt_manager, 'base_prompts'):
                    return self.eevee.prompt_manager.base_prompts.get(template_name, {})
            return {}
        except Exception as e:
            print(f"⚠️ Failed to get template content for {template_name}: {e}")
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
                import yaml
                
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
            print(f"⚠️ Failed to save improved template {template_name}: {e}")
        
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
            print(f"⚠️ Failed to save periodic review: {e}")
    
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
            print(f"⚠️ Failed to log learning event: {e}")
    
    def _analyze_navigation_progress(self, turn_number: int, buttons_pressed: List[str], ai_reasoning: str, screenshot_path: str = None) -> Dict[str, Any]:
        """
        Analyze navigation progress using screenshot comparison and loop detection
        
        Args:
            turn_number: Current turn number
            buttons_pressed: Buttons pressed this turn
            ai_reasoning: AI's reasoning for this action
            screenshot_path: Path to the screenshot for this turn
            
        Returns:
            Navigation analysis with stuck detection and recovery suggestions
        """
        # Use provided screenshot path or capture new one
        if not screenshot_path:
            try:
                # Fallback: Get the most recent screenshot from the eevee controller
                screenshot_path = self.eevee.controller.capture_screen()
            except Exception as e:
                print(f"⚠️ Navigation analysis: Screenshot capture failed: {e}")
                return {"error": "Screenshot capture failed", "navigation_status": "unknown"}
        
        # Process with navigation enhancer
        nav_analysis = self.nav_enhancer.add_turn_data(
            turn_number=turn_number,
            screenshot_path=screenshot_path,
            buttons_pressed=buttons_pressed,
            ai_reasoning=ai_reasoning
        )
        
        # Handle navigation interventions
        if nav_analysis.get("needs_intervention"):
            self._handle_navigation_intervention(nav_analysis)
        
        # Check if we should run a critique (every 20 turns)
        if turn_number % 20 == 0:
            critique = self.nav_enhancer.generate_critique()
            nav_analysis["critique"] = critique
            
            # 🧠 NEW: AUTOMATICALLY UPDATE PROMPTS BASED ON CRITIQUE
            if hasattr(self.eevee, 'prompt_manager'):
                try:
                    # Apply critique results to prompt manager
                    prompt_changes = self.nav_enhancer.apply_critique_to_prompt_manager(
                        critique, self.eevee.prompt_manager
                    )
                    
                    # Update navigation strategy based on critique
                    strategy_update = self.nav_enhancer.update_navigation_strategy(critique)
                    
                    nav_analysis["prompt_changes"] = prompt_changes
                    nav_analysis["strategy_update"] = strategy_update
                    
                    if self.eevee.verbose:
                        print(f"\n🔧 AUTOMATIC PROMPT UPDATES (Turn {turn_number}):")
                        
                        if prompt_changes.get("template_switches"):
                            for switch in prompt_changes["template_switches"]:
                                print(f"   📝 {switch}")
                        
                        if prompt_changes.get("emergency_actions"):
                            for action in prompt_changes["emergency_actions"]:
                                print(f"   🚨 {action}")
                        
                        if prompt_changes.get("memory_updates"):
                            for update in prompt_changes["memory_updates"]:
                                print(f"   🧠 {update}")
                        
                        if strategy_update != "No navigation strategy updates needed":
                            print(f"   ⚙️ {strategy_update}")
                            
                except Exception as e:
                    if self.eevee.verbose:
                        print(f"   ⚠️ Prompt update failed: {e}")
            
            # Update OKR progress during critique analysis
            if self.eevee.enable_okr:
                progress_summary = f"20-turn checkpoint: {critique.get('overall_assessment', 'unknown assessment')}"
                problems = len(critique.get('problems_identified', []))
                progress_note = f"Progress ratio: {critique.get('progress_ratio', 0):.2f}, Issues: {problems}"
                self.eevee.update_okr_progress(progress_summary, "checkpoint", progress_note)
            
            if self.eevee.verbose:
                print(f"\n📊 NAVIGATION CRITIQUE (Turn {turn_number}):")
                print(f"   Progress ratio: {critique.get('progress_ratio', 'unknown'):.2f}")
                print(f"   Problems: {len(critique.get('problems_identified', []))}")
                print(f"   Assessment: {critique.get('overall_assessment', 'unknown')}")
                
                # Show prompt suggestions from critique
                suggestions = critique.get('suggested_prompt_changes', [])
                if suggestions:
                    print(f"   📋 Prompt suggestions: {'; '.join(suggestions)}")
        
        return nav_analysis
    
    def _handle_navigation_intervention(self, nav_analysis: Dict[str, Any]):
        """Handle navigation intervention when AI is stuck"""
        if nav_analysis.get("loop_detected"):
            consecutive_actions = nav_analysis.get("consecutive_similar_actions", 0)
            print(f"🚨 LOOP DETECTED: {consecutive_actions} consecutive identical actions")
            
            # Trigger stuck mode in the enhancer
            self.nav_enhancer.trigger_stuck_mode()
            
        if nav_analysis.get("visual_stuck"):
            print(f"🚨 VISUAL STUCK: No progress for {nav_analysis.get('consecutive_similar_screenshots', 0)} screenshots")
        
        # Display recovery suggestions
        recovery = nav_analysis.get("suggested_recovery", {})
        if recovery.get("type") == "recovery_needed":
            print(f"💡 RECOVERY SUGGESTION: {recovery.get('problem', 'Navigation issue detected')}")
            
            recommended = recovery.get("recommended_strategy")
            if recommended:
                print(f"   Recommended: {recommended.get('description', 'Try alternative approach')}")
                print(f"   Actions: {recommended.get('actions', [])}")
                
                # Add recovery strategy to user task queue for next turn
                if not hasattr(self, '_user_tasks'):
                    self._user_tasks = []
                
                recovery_task = f"STUCK RECOVERY: {recommended.get('description', 'Use alternative navigation')}"
                self._user_tasks.append(recovery_task)
        
        # Log navigation confidence
        confidence = nav_analysis.get("navigation_confidence", 0.5)
        if confidence < 0.3:
            print(f"⚠️ Low navigation confidence: {confidence:.2f}")
        elif self.eevee.verbose:
            print(f"📍 Navigation confidence: {confidence:.2f}")
    
    def _get_stuck_problem_description(self) -> str:
        """Generate description of current stuck navigation problem"""
        if not hasattr(self, 'nav_enhancer'):
            return "Navigation analysis not available"
        
        # Get recent action patterns
        recent_actions = self._get_recent_actions_summary()
        
        # Check if we have navigation analysis data
        if hasattr(self.nav_enhancer, 'recent_actions') and self.nav_enhancer.recent_actions:
            consecutive_count = self.nav_enhancer._count_consecutive_actions()
            if consecutive_count >= 3:
                last_action = list(self.nav_enhancer.recent_actions)[-1] if self.nav_enhancer.recent_actions else []
                return f"Stuck pressing {last_action} button {consecutive_count} times consecutively with no visual progress"
        
        # Check for visual stuck
        if hasattr(self.nav_enhancer, 'consecutive_similar_screenshots'):
            if self.nav_enhancer.consecutive_similar_screenshots >= 3:
                return f"No visual changes detected for {self.nav_enhancer.consecutive_similar_screenshots} consecutive turns"
        
        # Fallback description
        return f"Navigation issue detected. Recent actions: {recent_actions}"


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
  %(prog)s --interactive --enable-okr --neo4j-memory
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
    
    # AI Model Configuration
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-1.5-flash",
        choices=["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
        help="AI model to use (default: gemini-1.5-flash)"
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
    
    parser.add_argument(
        "--neo4j-memory",
        action="store_true",
        help="Use Neo4j for visual memory system"
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
    project_root = eevee_dir.parent
    
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
    print("=. " + "="*60)
    print("=. EEVEE v1 - AI Pokemon Task Execution System")
    print("=. " + "="*60)
    
    if args.task:
        print(f"=� Mode: Single Task Execution")
        print(f"<� Task: {args.task}")
    else:
        print(f"<� Mode: Continuous Gameplay with Interactive Chat")
        print(f"<� Goal: {args.goal}")
        print(f"=� Max turns: {args.max_turns}")
        interactive = not args.no_interactive
        print(f"=� Interactive: {' Enabled' if interactive else 'L Disabled'}")
    
    print(f"> Model: {args.model}")
    print(f">� Memory Session: {args.memory_session}")
    print(f"<� Window: {args.window_title}")
    print("=. " + "="*60)


def execute_single_task(eevee: EeveeAgent, task: str, args) -> Dict[str, Any]:
    """Execute a single task and return results"""
    print(f"<� Executing task: {task}")
    
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
    
    print(f"=� Session report saved: {report_file}")
    return report_file


def main():
    """Main Eevee v1 execution function"""
    try:
        # Parse arguments and setup
        args = parse_arguments()
        eevee_dir = setup_environment()
        print_startup_banner(args)
        
        # Initialize Eevee agent
        print("=� Initializing Eevee AI system...")
        
        try:
            eevee = EeveeAgent(
                window_title=args.window_title,
                model=args.model,
                memory_session=args.memory_session,
                verbose=args.verbose,
                debug=args.debug,
                enable_neo4j=args.neo4j_memory,
                enable_okr=args.enable_okr
            )
            print(" Eevee agent initialized successfully")
        except Exception as e:
            print(f"L Failed to initialize Eevee agent: {e}")
            sys.exit(1)
        
        # Clear memory if requested
        if args.clear_memory and eevee.memory:
            print(f">� Clearing memory session: {args.memory_session}")
            eevee.memory.clear_session()
        
        # Determine execution mode
        if args.task:
            # Single task execution mode
            result = execute_single_task(eevee, args.task, args)
            
            # Print results
            print(f"\n Task execution completed!")
            print(f"Status: {result['status']}")
            print(f"Analysis: {result['analysis']}")
            
            # Save report if requested
            if args.save_report:
                report_file = eevee_dir / "reports" / f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"=� Report saved: {report_file}")
            
        else:
            # Continuous gameplay mode (default)
            interactive = not args.no_interactive  # Interactive by default
            
            print(f"\n<� Starting continuous Pokemon gameplay...")
            print(f"<� Goal: {args.goal}")
            print(f"=� Interactive mode: {' Enabled' if interactive else 'L Disabled'}")
            
            if interactive:
                print(f"\n=� While playing, you can:")
                print(f"   - Type /pause to pause")
                print(f"   - Type /status to check progress")
                print(f"   - Type any task for the AI to consider")
                print(f"   - Type /help for all commands")
            
            print(f"\n{'='*60}")
            
            # Initialize continuous gameplay
            gameplay = ContinuousGameplay(eevee, interactive=interactive, episode_review_frequency=args.episode_review_frequency)
            
            # Start session
            session = gameplay.start_session(args.goal, args.max_turns)
            gameplay.turn_delay = args.turn_delay
            
            try:
                # Run the main gameplay loop
                session_summary = gameplay.run_continuous_loop()
                
                # Print final results
                print(f"\n<� Gameplay session completed!")
                print(f"=� Status: {session_summary['status']}")
                print(f"= Turns: {session_summary['turns_completed']}/{session_summary['max_turns']}")
                print(f"=� User interactions: {session_summary['user_interactions']}")
                
                # Trigger episode review if enabled and session completed sufficient turns
                if args.episode_review_frequency > 0 and session_summary['turns_completed'] >= args.episode_review_frequency:
                    try:
                        from episode_reviewer import EpisodeReviewer
                        reviewer = EpisodeReviewer(eevee_dir)
                        
                        # Find the most recent session directory
                        runs_dir = eevee_dir / "runs"
                        recent_sessions = sorted(runs_dir.glob("session_*"), key=lambda x: x.stat().st_mtime, reverse=True)
                        
                        # Filter to only directories with session_data.json
                        valid_sessions = [s for s in recent_sessions if s.is_dir() and (s / "session_data.json").exists()]
                        
                        if valid_sessions:
                            latest_session = valid_sessions[0]
                            print(f"\n🔍 EPISODE REVIEW: Analyzing {session_summary['turns_completed']}-turn session...")
                            print(f"📊 Session: {latest_session.name}")
                            
                            # Generate episode review report
                            report = reviewer.generate_episode_report(latest_session)
                            
                            # Save report to file
                            report_file = latest_session / "episode_review.md"
                            with open(report_file, 'w') as f:
                                f.write(report)
                            
                            print(f"📋 Episode review saved: {report_file}")
                            
                            # Show key findings
                            metrics = reviewer.analyze_episode(latest_session)
                            improvements = reviewer.suggest_prompt_improvements(metrics)
                            
                            print(f"\n📈 EPISODE SUMMARY:")
                            print(f"   Navigation Efficiency: {metrics.navigation_efficiency:.2f}")
                            print(f"   Battles Won: {metrics.battles_won}")
                            print(f"   Stuck Patterns: {metrics.stuck_patterns}")
                            print(f"   Major Achievements: {len(metrics.major_achievements)}")
                            
                            if improvements:
                                print(f"\n🔧 PROMPT IMPROVEMENTS SUGGESTED: {len(improvements)}")
                                for improvement in improvements[:3]:  # Show top 3
                                    print(f"   • {improvement.prompt_name} ({improvement.priority} priority)")
                                    print(f"     {improvement.reasoning}")
                                
                                # Apply template updates if enabled
                                print(f"\n📝 Applying template updates from episode review...")
                                update_result = reviewer.update_yaml_templates(latest_session, apply_changes=True)
                                if update_result["success"] and update_result["changes_applied"] > 0:
                                    # Reload templates after final review
                                    if eevee.prompt_manager:
                                        eevee.prompt_manager.reload_templates()
                                        print(f"🔄 Templates reloaded with improvements for next session")
                            else:
                                print(f"\n✅ No prompt improvements needed - excellent performance!")
                        else:
                            print(f"\n⚠️ EPISODE REVIEW: No valid session directories found")
                            print(f"   Searched in: {runs_dir}")
                            print(f"   Looking for directories matching 'session_*' with session_data.json")
                        
                    except Exception as e:
                        print(f"⚠️ Episode review failed: {e}")
                        if args.debug:
                            import traceback
                            traceback.print_exc()
                
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