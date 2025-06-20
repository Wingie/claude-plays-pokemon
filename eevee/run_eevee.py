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
    
    def __init__(self, eevee_agent: EeveeAgent, interactive: bool = True):
        self.eevee = eevee_agent
        self.interactive = interactive
        self.session = None
        self.interactive_controller = None
        
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
        
        print(f"<� Starting continuous Pokemon gameplay")
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
                
                # Step 2: Get AI analysis and decision
                ai_result = self._get_ai_decision(game_context, turn_count)
                
                # Step 3: Execute AI's chosen action
                execution_result = self._execute_ai_action(ai_result)
                
                # Step 4: Update memory and session state
                self._update_session_state(turn_count, ai_result, execution_result)
                
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
        prompt = self._build_ai_prompt(turn_number, memory_context)
        
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
            
            return {
                "analysis": analysis_text,
                "action": button_sequence,
                "reasoning": analysis_text
            }
            
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
            nav_analysis = self._analyze_navigation_progress(turn_number, validated_actions, reasoning_text)
            
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
        
        # HIGHEST PRIORITY: Stuck navigation detection (critical for avoiding infinite loops)
        if hasattr(self, 'nav_enhancer') and self.nav_enhancer.stuck_mode:
            prompt_type = "stuck_navigation"
            playbooks = ["navigation"]
            return prompt_type, playbooks
        
        # Check for user recovery tasks
        recent_tasks = getattr(self, '_user_tasks', [])
        if any("STUCK RECOVERY" in task for task in recent_tasks):
            prompt_type = "stuck_navigation"
            playbooks = ["navigation"] 
            return prompt_type, playbooks
        
        # HIGH PRIORITY: Battle detection (most critical for Pokemon gameplay)
        if self._detect_battle_context(context_lower):
            prompt_type = "battle_analysis"
            playbooks = ["battle"]
            
            # Enhanced gym battle detection
            if any(keyword in context_lower for keyword in ["gym", "leader", "badge"]) or \
               any(keyword in user_goal for keyword in ["gym", "leader", "badge"]):
                playbooks.append("gyms")
                
        # PARTY MANAGEMENT: Pokemon party analysis
        elif self._detect_party_context(context_lower, user_goal):
            prompt_type = "pokemon_party_analysis"
            playbooks = ["battle"]  # Party management uses battle knowledge for moves/types
            
        # INVENTORY MANAGEMENT: Bag and items
        elif self._detect_inventory_context(context_lower, user_goal):
            prompt_type = "inventory_analysis" 
            playbooks = ["services"]  # Inventory management relates to shops/services
            
        # SERVICES: Pokemon Centers, shops, healing
        elif self._detect_services_context(context_lower, user_goal):
            prompt_type = "location_analysis"
            playbooks = ["services"]
            
        # NAVIGATION: Movement and exploration (default fallback)
        else:
            prompt_type = "location_analysis"
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
        battle_keywords = ["battle", "fight", "pokemon", "moves", "hp", "attack", "wild", "trainer", "fainted"]
        return any(keyword in context_lower for keyword in battle_keywords)
    
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
    
    def _build_ai_prompt(self, turn_number: int, memory_context: str) -> str:
        """Build context-aware AI prompt with playbook integration"""
        user_tasks = getattr(self, '_user_tasks', [])
        recent_task = user_tasks[-1] if user_tasks else ""
        
        # Try to get prompt manager for enhanced prompts
        prompt_manager = getattr(self.eevee, 'prompt_manager', None)
        
        if prompt_manager:
            # Use enhanced prompt system with battle playbook
            variables = {
                "task": self.session.goal,
                "context_summary": f"Turn {turn_number}/{self.session.max_turns}",
                "memory_context": memory_context,
                "recent_actions": self._get_recent_actions_summary(),
                "goal": self.session.goal,
                "stuck_problem": self._get_stuck_problem_description(),
            }
            
            try:
                # Determine appropriate prompt type and playbooks based on context
                prompt_type, playbooks = self._determine_prompt_context(memory_context)
                
                # Get context-appropriate prompt
                prompt = prompt_manager.get_prompt(
                    prompt_type, 
                    variables, 
                    include_playbook=playbooks[0] if playbooks else None,
                    verbose=True  # Always show prompt debugging
                )
                
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
                
                # Always show prompt information for debugging
                playbook_list = ", ".join(playbooks) if playbooks else "none"
                print(f"📖 Using {prompt_type} with playbooks: {playbook_list}")
                
            except Exception as e:
                if self.eevee.verbose:
                    print(f"⚠️ Prompt manager failed, using fallback: {e}")
                prompt = self._build_fallback_prompt(turn_number, memory_context, recent_task)
        else:
            prompt = self._build_fallback_prompt(turn_number, memory_context, recent_task)
        
        # Clear processed user tasks
        if hasattr(self, '_user_tasks'):
            self._user_tasks.clear()
        
        return prompt
    
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
    
    def _analyze_navigation_progress(self, turn_number: int, buttons_pressed: List[str], ai_reasoning: str) -> Dict[str, Any]:
        """
        Analyze navigation progress using screenshot comparison and loop detection
        
        Args:
            turn_number: Current turn number
            buttons_pressed: Buttons pressed this turn
            ai_reasoning: AI's reasoning for this action
            
        Returns:
            Navigation analysis with stuck detection and recovery suggestions
        """
        # Get current screenshot path (assuming it was just captured)
        screenshot_path = None
        try:
            # Get the most recent screenshot from the eevee controller
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
            gameplay = ContinuousGameplay(eevee, interactive=interactive)
            
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