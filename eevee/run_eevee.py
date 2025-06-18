#!/usr/bin/env python3
"""
Eevee v1 - AI Pokemon Task Execution System
Command-line interface for executing Pokemon game tasks via natural language

Usage examples:
    python run_eevee.py "check and report all your pokemon party and their levels and moves and what PP left in each move"
    python run_eevee.py "navigate to the nearest Pokemon Center and heal all Pokemon"
    python run_eevee.py "find and catch a wild Pokemon in the current area"
    
    # With options:
    python run_eevee.py "analyze current location" --memory-session mysession --model gemini-flash-2.0-exp
    python run_eevee.py "check inventory" --output-format json --save-report
"""

import argparse
import sys
import os
import json
import time
import base64
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
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
except ImportError:
    print("⚠️  Eevee v1 components not yet available. Starting with basic implementation...")
    # Fallback to basic implementation for initial development
    from eevee_main import EeveeAnalyzer


@dataclass
class ExecutionStep:
    """Single execution step in a training session"""
    step_number: int
    timestamp: str
    screenshot_before: Optional[str]  # base64 encoded image
    screenshot_after: Optional[str]   # base64 encoded image
    ai_analysis: str
    action_taken: str
    action_reasoning: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class TrainingSession:
    """Complete training session data"""
    session_id: str
    task_description: str
    start_time: str
    end_time: Optional[str]
    total_steps: int
    max_steps: int
    final_score: Optional[int]
    task_completed: bool
    execution_trace: List[ExecutionStep]
    final_result: Dict[str, Any]
    model_used: str
    human_feedback: Optional[str] = None


class TrainingDataCollector:
    """Manages training data collection for VLLM fine-tuning"""
    
    def __init__(self, project_root: Path, session_id: Optional[str] = None):
        self.project_root = project_root
        self.runs_dir = project_root / "runs"
        self.runs_dir.mkdir(exist_ok=True)
        
        # Generate session ID if not provided
        if session_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_id = f"{timestamp}_{session_id}"
        else:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.session_dir = None
        self.current_session = None
        self.execution_trace = []
    
    def start_training_session(self, task_description: str, max_steps: int, model: str) -> str:
        """Start a new training data collection session"""
        
        # Create session directory with descriptive name
        safe_task = "".join(c for c in task_description[:30] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        session_dir_name = f"{self.session_id}_{safe_task}"
        
        self.session_dir = self.runs_dir / session_dir_name
        self.session_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.session_dir / "screenshots").mkdir(exist_ok=True)
        (self.session_dir / "memory_snapshots").mkdir(exist_ok=True)
        (self.session_dir / "analysis").mkdir(exist_ok=True)
        
        # Initialize session data
        self.current_session = TrainingSession(
            session_id=self.session_id,
            task_description=task_description,
            start_time=datetime.now().isoformat(),
            end_time=None,
            total_steps=0,
            max_steps=max_steps,
            final_score=None,
            task_completed=False,
            execution_trace=[],
            final_result={},
            model_used=model
        )
        
        print(f"🎬 Started training session: {session_dir_name}")
        print(f"📁 Session directory: {self.session_dir}")
        
        return str(self.session_dir)
    
    def end_training_session(self, final_result: Dict[str, Any], task_completed: bool) -> None:
        """End the training session and save all data"""
        
        if not self.current_session:
            raise RuntimeError("No active training session to end.")
        
        self.current_session.end_time = datetime.now().isoformat()
        self.current_session.final_result = final_result
        self.current_session.task_completed = task_completed
        
        # Save session metadata
        self._save_session_metadata()
        
        # Save execution trace
        self._save_execution_trace()
        
        # Get human feedback score
        self._collect_human_feedback()
        
        # Generate VLLM training data
        self._generate_vllm_training_data()
        
        print(f"🏁 Training session completed: {self.session_dir}")
    
    def _save_session_metadata(self) -> None:
        """Save session metadata to JSON file"""
        metadata_file = self.session_dir / "session_metadata.json"
        
        metadata = {
            "session_id": self.current_session.session_id,
            "task_description": self.current_session.task_description,
            "start_time": self.current_session.start_time,
            "end_time": self.current_session.end_time,
            "total_steps": self.current_session.total_steps,
            "max_steps": self.current_session.max_steps,
            "final_score": self.current_session.final_score,
            "task_completed": self.current_session.task_completed,
            "model_used": self.current_session.model_used,
            "human_feedback": self.current_session.human_feedback
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _save_execution_trace(self) -> None:
        """Save complete execution trace to JSON file"""
        trace_file = self.session_dir / "execution_trace.json"
        
        trace_data = {
            "session_metadata": {
                "session_id": self.current_session.session_id,
                "task_description": self.current_session.task_description,
                "total_steps": self.current_session.total_steps
            },
            "execution_trace": [asdict(step) for step in self.current_session.execution_trace],
            "final_result": self.current_session.final_result
        }
        
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f, indent=2)
    
    def _collect_human_feedback(self) -> None:
        """Collect human feedback and scoring"""
        print("\n" + "="*60)
        print("🎯 TRAINING SESSION EVALUATION")
        print("="*60)
        print(f"Task: {self.current_session.task_description}")
        print(f"Steps Used: {self.current_session.total_steps}/{self.current_session.max_steps}")
        print(f"Task Completed: {'✅ Yes' if self.current_session.task_completed else '❌ No'}")
        print(f"Final Result: {self.current_session.final_result.get('analysis', 'N/A')}")
        
        # Show key screenshots if available
        screenshots_dir = self.session_dir / "screenshots"
        if screenshots_dir.exists() and list(screenshots_dir.glob("*.png")):
            print(f"📸 Screenshots saved in: {screenshots_dir}")
        
        print("\n📊 SCORING GUIDELINES:")
        print("9-10: Perfect execution (optimal path, clear results)")
        print("7-8:  Good execution (minor inefficiencies)")
        print("5-6:  Acceptable execution (basic objectives met)")
        print("3-4:  Poor execution (significant errors)")
        print("1-2:  Failed execution (task not completed)")
        
        # Get human score with fallback for non-interactive environments
        try:
            # Check if we're in an interactive environment
            import sys
            if not sys.stdin.isatty():
                # Non-interactive environment - use auto-scoring
                auto_score = 7 if self.current_session.task_completed else 4
                print(f"\n🤖 Auto-scored (non-interactive): {auto_score}/10")
                self.current_session.final_score = auto_score
                self.current_session.human_feedback = "Auto-generated score (non-interactive environment)"
            else:
                # Interactive environment - ask for human input
                while True:
                    try:
                        score_input = input("\n🎯 Rate task completion (1-10): ").strip()
                        if not score_input:
                            print("Please enter a score between 1 and 10")
                            continue
                            
                        score = int(score_input)
                        if 1 <= score <= 10:
                            self.current_session.final_score = score
                            break
                        else:
                            print("Please enter a score between 1 and 10")
                    except ValueError:
                        print("Please enter a valid number")
                
                # Get optional feedback
                try:
                    feedback = input("💬 Additional feedback (optional, press Enter to skip): ").strip()
                    if feedback:
                        self.current_session.human_feedback = feedback
                except (EOFError, KeyboardInterrupt):
                    pass
                
                print(f"✅ Session scored: {self.current_session.final_score}/10")
        
        except (EOFError, KeyboardInterrupt):
            # Handle input errors gracefully
            auto_score = 7 if self.current_session.task_completed else 4
            print(f"\n🤖 Auto-scored (input error): {auto_score}/10")
            self.current_session.final_score = auto_score
            self.current_session.human_feedback = "Auto-generated score (input unavailable)"
        
        # Update metadata file with score
        self._save_session_metadata()
    
    def _generate_vllm_training_data(self) -> None:
        """Generate VLLM-compatible training data"""
        training_data = []
        
        # Try to use execution_trace first, fallback to final_result.step_details
        execution_steps = self.current_session.execution_trace
        
        if not execution_steps and hasattr(self.current_session, 'final_result') and 'step_details' in self.current_session.final_result:
            # Fallback: use step_details from final_result
            step_details = self.current_session.final_result['step_details']
            for i, step_detail in enumerate(step_details):
                # Extract action from actions_taken array or use default
                action_taken = step_detail.get('actions_taken', ['analyze_screen'])[0] if step_detail.get('actions_taken') else 'analyze_screen'
                
                # Create instruction-response pair for each step
                instruction_data = {
                    "instruction": self.current_session.task_description,
                    "input": {
                        "game_state": {
                            "screenshot_base64": step_detail.get('screenshot_path', f'step_{i+1}_screenshot.png'),
                            "step_number": i + 1,
                            "total_steps": self.current_session.max_steps,
                            "previous_analysis": step_details[i-1].get('analysis') if i > 0 else None
                        },
                        "task_context": {
                            "goal": self.current_session.task_description,
                            "progress": f"Step {i+1} of {self.current_session.max_steps}"
                        }
                    },
                    "output": {
                        "action": action_taken,
                        "reasoning": step_detail['step'].get('description', 'Execute step'),
                        "analysis": step_detail.get('analysis', 'No analysis available')
                    },
                    "metadata": {
                        "session_id": self.current_session.session_id,
                        "timestamp": datetime.now().isoformat(),
                        "model_used": self.current_session.model_used,
                        "success": step_detail.get('status') == 'completed',
                        "human_score": self.current_session.final_score,
                        "task_completed": self.current_session.task_completed
                    }
                }
                
                training_data.append(instruction_data)
        else:
            # Original execution_trace format
            for i, step in enumerate(execution_steps):
                instruction_data = {
                    "instruction": self.current_session.task_description,
                    "input": {
                        "game_state": {
                            "screenshot_base64": step.screenshot_before,
                            "step_number": step.step_number,
                            "total_steps": self.current_session.max_steps,
                            "previous_analysis": execution_steps[i-1].ai_analysis if i > 0 else None
                        },
                        "task_context": {
                            "goal": self.current_session.task_description,
                            "progress": f"Step {step.step_number} of {self.current_session.max_steps}"
                        }
                    },
                    "output": {
                        "action": step.action_taken,
                        "reasoning": step.action_reasoning,
                        "analysis": step.ai_analysis
                    },
                    "metadata": {
                        "session_id": self.current_session.session_id,
                        "timestamp": step.timestamp,
                        "model_used": self.current_session.model_used,
                        "success": step.success,
                        "human_score": self.current_session.final_score,
                        "task_completed": self.current_session.task_completed
                    }
                }
                
                training_data.append(instruction_data)
        
        # Save as JSONL format for VLLM
        training_file = self.session_dir / "training_data.jsonl"
        with open(training_file, 'w') as f:
            for example in training_data:
                f.write(json.dumps(example) + '\n')
        
        print(f"🤖 Generated {len(training_data)} training examples: {training_file}")


def parse_arguments():
    """Parse command line arguments for Eevee v1"""
    parser = argparse.ArgumentParser(
        description="Eevee v1 - AI Pokemon Task Execution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "check my pokemon party levels and moves"
  %(prog)s "navigate to Pokemon Center" --memory-session gym-run
  %(prog)s "analyze current battle situation" --model gemini-flash-2.0-exp
  %(prog)s "find items in current area" --output-format json
        """
    )
    
    # Main task argument
    parser.add_argument(
        "task",
        type=str,
        nargs="?",  # Make optional for interactive mode
        help="Natural language description of the Pokemon task to execute (optional in interactive mode)"
    )
    
    # AI Model Configuration
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-flash-2.0-exp",
        choices=["gemini-flash-2.0-exp", "gemini-1.5-flash", "gemini-1.5-pro"],
        help="AI model to use for task execution (default: gemini-flash-2.0-exp)"
    )
    
    # Memory and Session Management
    parser.add_argument(
        "--memory-session",
        type=str,
        default="default",
        help="Memory session name for context persistence (default: 'default')"
    )
    
    parser.add_argument(
        "--clear-memory",
        action="store_true",
        help="Clear memory session before starting task"
    )
    
    # Output and Reporting
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for task results (default: text)"
    )
    
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save detailed report to file in eevee/reports/"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output showing step-by-step execution"
    )
    
    # Emulator Configuration
    parser.add_argument(
        "--window-title",
        type=str,
        default="mGBA - 0.10.5",
        help="Emulator window title to connect to (default: 'mGBA - 0.10.5')"
    )
    
    # Experimental Features
    parser.add_argument(
        "--prompt-experiment",
        type=str,
        help="Name of prompt experiment to use (for A/B testing)"
    )
    
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum number of execution steps for complex tasks (default: 50)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze task and show execution plan without actually performing actions"
    )
    
    # Debug and Development
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with extra logging"
    )
    
    # Interactive Mode
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive chat mode - guide Eevee while it plays"
    )
    
    parser.add_argument(
        "--enable-okr",
        action="store_true",
        help="Enable OKR.md progress tracking"
    )
    
    parser.add_argument(
        "--neo4j-memory",
        action="store_true",
        help="Use Neo4j for visual memory system instead of SQLite"
    )
    
    # Training Data Collection (Eevee v2)
    parser.add_argument(
        "--save-training-data",
        action="store_true",
        help="Enable training data collection mode for VLLM fine-tuning"
    )
    
    parser.add_argument(
        "--steps",
        type=int,
        help="Limit execution to maximum number of steps (overrides --max-steps when training)"
    )
    
    parser.add_argument(
        "--training-session",
        type=str,
        help="Custom identifier for training session (auto-generated if not provided)"
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
        eevee_dir / "prompts",
        eevee_dir / "prompts" / "experimental",
        eevee_dir / "utils",
        eevee_dir / "analysis",  # For screenshots and analysis files
        project_root / "runs"    # Training data collection
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
    
    return eevee_dir

def print_header(args):
    """Print Eevee v1 startup header"""
    print("🔮 " + "="*60)
    if args.save_training_data:
        print("🔮 EEVEE v2 - Training Data Collection Mode")
    else:
        print("🔮 EEVEE v1 - AI Pokemon Task Execution System")
    print("🔮 " + "="*60)
    print(f"📋 Task: {args.task}")
    print(f"🤖 Model: {args.model}")
    print(f"🧠 Memory Session: {args.memory_session}")
    print(f"🎮 Emulator: {args.window_title}")
    if args.save_training_data:
        max_steps = args.steps if args.steps else args.max_steps
        print(f"🎬 Training Mode: Enabled (max {max_steps} steps)")
        if args.training_session:
            print(f"📝 Session ID: {args.training_session}")
    if args.dry_run:
        print("🔍 Mode: DRY RUN (analysis only)")
    print("🔮 " + "="*60)

def format_output(result: Dict[str, Any], format_type: str) -> str:
    """Format task execution result according to specified format"""
    if format_type == "json":
        return json.dumps(result, indent=2)
    elif format_type == "markdown":
        return format_markdown_report(result)
    else:  # text format
        return format_text_report(result)

def format_text_report(result: Dict[str, Any]) -> str:
    """Format result as human-readable text"""
    report = []
    report.append("📊 EEVEE TASK EXECUTION REPORT")
    report.append("=" * 40)
    
    if "task" in result:
        report.append(f"📋 Task: {result['task']}")
    
    if "status" in result:
        status_emoji = "✅" if result["status"] == "success" else "❌"
        report.append(f"{status_emoji} Status: {result['status']}")
    
    if "analysis" in result:
        report.append(f"\n📝 Analysis:\n{result['analysis']}")
    
    if "steps_executed" in result:
        report.append(f"\n🔄 Steps Executed: {result['steps_executed']}")
    
    if "execution_time" in result:
        report.append(f"⏱️  Execution Time: {result['execution_time']:.2f}s")
    
    return "\n".join(report)

def format_markdown_report(result: Dict[str, Any]) -> str:
    """Format result as markdown report"""
    report = []
    report.append("# 🔮 Eevee Task Execution Report")
    report.append("")
    
    if "task" in result:
        report.append(f"**Task:** {result['task']}")
        report.append("")
    
    if "status" in result:
        status_emoji = "✅" if result["status"] == "success" else "❌"
        report.append(f"**Status:** {status_emoji} {result['status']}")
        report.append("")
    
    if "analysis" in result:
        report.append("## 📝 Analysis")
        report.append("")
        report.append(result['analysis'])
        report.append("")
    
    if "steps_executed" in result:
        report.append(f"**Steps Executed:** {result['steps_executed']}")
        report.append("")
    
    if "execution_time" in result:
        report.append(f"**Execution Time:** {result['execution_time']:.2f}s")
        report.append("")
    
    return "\n".join(report)

def save_report(result: Dict[str, Any], eevee_dir: Path, format_type: str):
    """Save execution report to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_task = "".join(c for c in result.get("task", "unknown")[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
    
    extension = {"text": "txt", "json": "json", "markdown": "md"}[format_type]
    filename = f"eevee_report_{safe_task}_{timestamp}.{extension}"
    
    report_file = eevee_dir / "reports" / filename
    
    formatted_output = format_output(result, format_type)
    
    with open(report_file, 'w') as f:
        f.write(formatted_output)
    
    print(f"💾 Report saved to: {report_file}")
    return report_file


def interactive_mode(eevee, args):
    """Interactive chat mode for real-time Pokemon guidance"""
    print("🔮 " + "="*60)
    print("🔮 EEVEE INTERACTIVE MODE - Pokemon AI Assistant")
    print("🔮 " + "="*60)
    
    # Load session continuity
    previous_state = get_session_state()
    user_goal = get_user_goal()
    
    print(f"🎯 Current Goal: {user_goal}")
    
    if previous_state.get("last_session"):
        print(f"📅 Resuming from last session: {previous_state['last_session']}")
        if previous_state.get("current_location"):
            print(f"📍 Last known location: {previous_state['current_location']}")
        if previous_state.get("locations_discovered"):
            locations = ", ".join(previous_state["locations_discovered"][-3:])  # Show last 3
            print(f"🗺️  Known locations: {locations}")
    
    print("💬 Type your tasks or use /commands for control")
    print("📋 Available commands: /pause, /resume, /status, /memory, /help, /quit")
    print("🎮 Game state updates will appear in real-time")
    print("🔮 " + "="*60)
    
    # Initialize interactive session state
    session_state = {
        "paused": False,
        "current_task": None,
        "task_thread": None,
        "command_queue": queue.Queue(),
        "response_queue": queue.Queue(),
        "running": True,
        "user_goal": user_goal,
        "session_data": previous_state,
        "active_runs": 0,
        "max_runs": 5
    }
    
    # Initialize OKR tracking if enabled
    if args.enable_okr:
        update_okr_file("Interactive session started", "session_start")
    
    try:
        while session_state["running"]:
            try:
                user_input = input("\n🎯 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    handle_interactive_command(user_input, session_state, eevee, args)
                else:
                    # Handle task execution
                    handle_interactive_task(user_input, session_state, eevee, args)
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting interactive mode...")
                session_state["running"] = False
                break
            except EOFError:
                print("\n👋 Input stream closed, exiting...")
                session_state["running"] = False
                break
    
    finally:
        # Cleanup
        if session_state["task_thread"] and session_state["task_thread"].is_alive():
            print("🛑 Stopping current task...")
            session_state["paused"] = True
            session_state["task_thread"].join(timeout=2)
        
        if args.enable_okr:
            update_okr_file("Interactive session ended", "session_end")
        
        print("✅ Interactive session ended")


def handle_interactive_command(command, session_state, eevee, args):
    """Handle interactive commands like /pause, /resume, etc."""
    cmd = command.lower().strip()
    
    if cmd == "/help":
        print("\n📋 INTERACTIVE COMMANDS:")
        print("  /pause          - Pause current task execution")
        print("  /resume         - Resume paused task")
        print("  /status         - Show current game state and task status")
        print("  /memory         - Show recent memory and context")
        print("  /okr            - Show current objectives and key results")
        print("  /clear          - Clear current task and reset")
        print("  /reset-memory   - Clear navigation memory for fresh test")
        print("  /show-route     - Display known routes from memory")
        print("  /location-stats - Show location recognition confidence")
        print("  /goal           - Show current USER_GOAL and suggest task")
        print("  /help           - Show this help message")
        print("  /quit           - Exit interactive mode")
        print("\n💡 Or just type a natural language task to execute it!")
    
    elif cmd == "/pause":
        if session_state["current_task"]:
            session_state["paused"] = True
            print("⏸️  Task paused. Type /resume to continue or give new instructions.")
        else:
            print("ℹ️  No active task to pause.")
    
    elif cmd == "/resume":
        if session_state["current_task"] and session_state["paused"]:
            session_state["paused"] = False
            print("▶️  Resuming task execution...")
        else:
            print("ℹ️  No paused task to resume.")
    
    elif cmd == "/status":
        show_interactive_status(session_state, eevee, args)
    
    elif cmd == "/memory":
        show_memory_status(eevee, args)
    
    elif cmd == "/okr":
        if args.enable_okr:
            show_okr_status()
        else:
            print("ℹ️  OKR tracking not enabled. Use --enable-okr to track progress.")
    
    elif cmd == "/clear":
        if session_state["task_thread"] and session_state["task_thread"].is_alive():
            session_state["paused"] = True
            print("🛑 Stopping current task...")
        session_state["current_task"] = None
        session_state["task_thread"] = None
        session_state["paused"] = False
        print("🧹 Cleared current task. Ready for new instructions.")
    
    elif cmd == "/reset-memory":
        reset_navigation_memory(eevee, args)
    
    elif cmd == "/show-route":
        show_known_routes(eevee, args)
    
    elif cmd == "/location-stats":
        show_location_stats(eevee, args)
    
    elif cmd == "/goal":
        show_goal_and_suggestions(session_state, args)
    
    elif cmd == "/quit":
        # Save session state before quitting
        save_current_session_state(session_state, eevee)
        session_state["running"] = False
        print("👋 Goodbye! Exiting interactive mode...")
    
    else:
        print(f"❓ Unknown command: {command}. Type /help for available commands.")


def handle_interactive_task(task, session_state, eevee, args):
    """Handle new task execution in interactive mode"""
    
    # If there's a current task, check if we should interrupt it
    if session_state["current_task"] and not session_state["paused"]:
        print(f"🔄 Current task: '{session_state['current_task']}' is running.")
        interrupt = input("   Do you want to interrupt it? (y/N): ").strip().lower()
        if interrupt not in ['y', 'yes']:
            print("   Continuing with current task. Use /pause to pause first.")
            return
        else:
            session_state["paused"] = True
            print("   🛑 Interrupting current task...")
    
    # Start new task
    session_state["current_task"] = task
    session_state["paused"] = False
    
    print(f"🎯 Eevee: Starting task - '{task}'")
    
    # Start task in separate thread for interruptibility
    session_state["task_thread"] = threading.Thread(
        target=execute_interactive_task,
        args=(task, session_state, eevee, args),
        daemon=True
    )
    session_state["task_thread"].start()
    
    # Update OKR if enabled
    if args.enable_okr:
        update_okr_file(f"Started task: {task}", "task_start")


def execute_interactive_task(task, session_state, eevee, args):
    """Execute task in separate thread with pause/resume support"""
    try:
        print(f"🔮 Eevee: Analyzing task and current game state...")
        
        # Check for pause before starting
        if session_state["paused"]:
            print("⏸️  Task paused before execution.")
            return
        
        # Execute the task with interruption support
        max_steps = args.steps if args.steps else args.max_steps
        
        # This is a simplified version - would need to enhance EeveeAgent for proper interruption
        if hasattr(eevee, 'execute_task_interruptible'):
            result = eevee.execute_task_interruptible(task, max_steps, session_state)
        else:
            # Fallback to regular execution
            result = eevee.execute_task(task, max_steps=max_steps)
        
        if not session_state["paused"]:
            print(f"✅ Eevee: Task completed!")
            if result.get("analysis"):
                print(f"📝 Result: {result['analysis'][:200]}...")
            
            # Update OKR if enabled
            if args.enable_okr:
                success = result.get("status") in ["success", "completed"]
                update_okr_file(f"Completed: {task}", "task_complete", success)
        
        session_state["current_task"] = None
        session_state["task_thread"] = None
        
    except Exception as e:
        print(f"❌ Error during task execution: {e}")
        session_state["current_task"] = None
        session_state["task_thread"] = None


def show_interactive_status(session_state, eevee, args):
    """Show current status in interactive mode"""
    print("\n📊 EEVEE STATUS REPORT")
    print("=" * 30)
    
    if session_state["current_task"]:
        status = "⏸️ PAUSED" if session_state["paused"] else "🔄 RUNNING"
        print(f"Current Task: {session_state['current_task']}")
        print(f"Status: {status}")
    else:
        print("Current Task: None - Ready for instructions")
    
    print(f"Memory Session: {getattr(eevee, 'memory_session', 'default')}")
    print(f"Model: {getattr(eevee, 'model', 'unknown')}")
    
    # Try to get current game context
    try:
        if hasattr(eevee, '_capture_current_context'):
            context = eevee._capture_current_context()
            print(f"Game Window: {'✅ Connected' if context.get('window_found') else '❌ Not Found'}")
            if context.get('timestamp'):
                print(f"Last Screenshot: {context['timestamp']}")
    except Exception as e:
        print(f"Game Connection: ⚠️ Error checking - {e}")
    
    print("=" * 30)


def show_memory_status(eevee, args):
    """Show memory system status and recent context"""
    print("\n🧠 MEMORY SYSTEM STATUS")
    print("=" * 30)
    
    try:
        if hasattr(eevee, 'memory') and eevee.memory:
            # Get memory stats
            if hasattr(eevee.memory, 'get_memory_stats'):
                stats = eevee.memory.get_memory_stats()
                print(f"Memory Session: {stats.get('session', 'unknown')}")
                print(f"Task History: {stats.get('task_history_count', 0)} entries")
                print(f"Game States: {stats.get('game_states_count', 0)} entries")
                print(f"Knowledge Base: {stats.get('learned_knowledge_count', 0)} entries")
            
            # Show recent context
            if hasattr(eevee.memory, 'get_relevant_context'):
                context = eevee.memory.get_relevant_context("recent activity")
                if context.get('similar_tasks'):
                    print("\n📚 Recent Tasks:")
                    for task in context['similar_tasks'][:3]:
                        status = "✅" if task.get('success') else "❌"
                        print(f"  {status} {task['description'][:50]}...")
        else:
            print("Memory system not available or not initialized")
    
    except Exception as e:
        print(f"Error accessing memory: {e}")
    
    print("=" * 30)


def get_user_goal():
    """Get user goal from environment variable"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        user_goal = os.getenv("USER_GOAL", "Complete Pokemon League Challenge")
        return user_goal.strip()
    except Exception as e:
        print(f"⚠️ Could not load USER_GOAL: {e}")
        return "Complete Pokemon League Challenge"


def get_session_state():
    """Get the last session state for continuity"""
    try:
        project_root = Path(__file__).parent.parent
        state_file = project_root / "session_state.json"
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load session state: {e}")
    
    return {
        "last_session": None,
        "current_objective": None,
        "progress": {},
        "memory_session": "default",
        "locations_discovered": [],
        "current_location": None
    }


def save_session_state(state):
    """Save current session state for continuity"""
    try:
        project_root = Path(__file__).parent.parent
        state_file = project_root / "session_state.json"
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save session state: {e}")


def update_okr_file(event, event_type, success=None):
    """Update OKR.md file with progress tracking"""
    try:
        project_root = Path(__file__).parent.parent
        okr_file = project_root / "OKR.md"
        
        # Create or read existing OKR file
        if okr_file.exists():
            with open(okr_file, 'r') as f:
                content = f.read()
        else:
            content = create_initial_okr_content()
        
        # Update content based on event type
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if event_type == "session_start":
            user_goal = get_user_goal()
            new_entry = f"\n## Session {datetime.now().strftime('%Y-%m-%d %H:%M')}\n- 🎬 Interactive session started\n- 🎯 Current Goal: {user_goal}\n"
        elif event_type == "task_start":
            new_entry = f"- 🎯 [{timestamp}] Started: {event}\n"
        elif event_type == "task_complete":
            emoji = "✅" if success else "❌"
            new_entry = f"- {emoji} [{timestamp}] {event}\n"
        elif event_type == "location_discovered":
            new_entry = f"- 📍 [{timestamp}] Location discovered: {event}\n"
        elif event_type == "navigation_success":
            new_entry = f"- 🗺️ [{timestamp}] Navigation success: {event}\n"
        elif event_type == "session_end":
            new_entry = f"- 🏁 [{timestamp}] Interactive session ended\n\n"
        else:
            new_entry = f"- 📝 [{timestamp}] {event}\n"
        
        # Append to file
        with open(okr_file, 'w') as f:
            f.write(content + new_entry)
    
    except Exception as e:
        print(f"⚠️ Could not update OKR.md: {e}")


def create_initial_okr_content():
    """Create initial OKR.md content structure"""
    user_goal = get_user_goal()
    
    return f"""# Pokemon Fire Red - Objectives & Key Results

## Current Objectives
### Primary Goal: {user_goal}
- **KR1**: Navigation & Exploration - Current Score: 0/10
- **KR2**: Memory & Learning - Current Score: 0/10  
- **KR3**: Task Completion Efficiency - Current Score: 5/10
- **KR4**: Strategic Decision Making - Current Score: 5/10

### Secondary Goals:
- **Location Discovery**: Find and remember key locations
- **Route Optimization**: Learn efficient navigation paths
- **Visual Recognition**: Recognize landmarks and game states
- **Knowledge Retention**: Remember successful strategies

## Progress Log
*This file auto-updates during interactive sessions*

Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Current Goal: {user_goal}
"""


def reset_navigation_memory(eevee, args):
    """Reset navigation memory for fresh testing"""
    try:
        if hasattr(eevee, 'memory') and eevee.memory:
            print("🧹 Clearing navigation memory...")
            eevee.memory.clear_navigation_memory()
            print("✅ Navigation memory reset. Ready for fresh navigation test.")
            
            # Update OKR if enabled
            if args.enable_okr:
                update_okr_file("Navigation memory reset for fresh test", "memory_reset")
        else:
            print("⚠️ Memory system not available.")
    except Exception as e:
        print(f"❌ Error resetting memory: {e}")


def show_known_routes(eevee, args):
    """Display known routes from memory"""
    try:
        if hasattr(eevee, 'memory') and eevee.memory:
            print("\n🗺️ KNOWN ROUTES & LOCATIONS")
            print("=" * 30)
            
            # Get all known routes
            routes = eevee.memory.get_all_known_routes()
            if routes:
                print("🛤️ Known navigation routes:")
                for i, route in enumerate(routes[:5], 1):
                    if route.get("from_location") and route.get("to_location"):
                        print(f"  {i}. {route['from_location']} → {route['to_location']}")
                        if route.get("steps_taken"):
                            print(f"     Steps: {route['steps_taken']}, Success count: {route.get('success_count', 1)}")
                    else:
                        print(f"  {i}. {route['route_id']}: {route['description'][:60]}...")
            else:
                print("🛤️ No navigation routes learned yet.")
            
            # Get location history
            if hasattr(eevee.memory, 'get_location_history'):
                locations = eevee.memory.get_location_history(limit=10)
                if locations:
                    print("\n📍 Recently visited locations:")
                    for i, loc in enumerate(locations[:5]):
                        print(f"  {i+1}. {loc['location']} (visited: {loc['visited_at'][:16]})")
            
            # Show visual memory stats if available
            if hasattr(eevee.memory, 'neo4j_memory') and eevee.memory.neo4j_memory:
                stats = eevee.memory.get_memory_stats().get('neo4j_visual_memory', {})
                if stats.get('connected'):
                    print(f"\n🔗 Visual memories: {stats.get('session_screenshots', 0)}")
            
            print("=" * 30)
        else:
            print("⚠️ Memory system not available.")
    except Exception as e:
        print(f"❌ Error showing routes: {e}")


def show_location_stats(eevee, args):
    """Show location recognition confidence for current area"""
    try:
        print("\n📊 LOCATION RECOGNITION STATS")
        print("=" * 35)
        
        # Get current context
        if hasattr(eevee, '_capture_current_context'):
            context = eevee._capture_current_context()
            
            print(f"🕒 Last screenshot: {context.get('timestamp', 'unknown')}")
            print(f"🔗 Game connection: {'✅' if context.get('window_found') else '❌'}")
            
            # Show visual memory stats if available
            if hasattr(eevee, 'memory') and eevee.memory and hasattr(eevee.memory, 'neo4j_memory'):
                if eevee.memory.neo4j_memory:
                    stats = eevee.memory.neo4j_memory.get_memory_stats()
                    print(f"📸 Visual memories: {stats.get('session_screenshots', 0)}")
                    print(f"🔍 Similarity threshold: {stats.get('similarity_threshold', 0.85)}")
            
            print("=" * 35)
        else:
            print("❌ Cannot capture current context.")
    except Exception as e:
        print(f"❌ Error getting location stats: {e}")


def show_goal_and_suggestions(session_state, args):
    """Show current USER_GOAL and suggest relevant tasks"""
    try:
        user_goal = session_state.get("user_goal", get_user_goal())
        
        print(f"\n🎯 CURRENT GOAL: {user_goal}")
        print("=" * 50)
        
        # Parse goal and suggest tasks
        goal_lower = user_goal.lower()
        
        suggestions = []
        if "viridian forest" in goal_lower:
            suggestions = [
                "Navigate to Viridian Forest from Pokemon Center",
                "Explore Viridian Forest and map the area", 
                "Battle trainers in Viridian Forest",
                "Find and catch Pokemon in Viridian Forest",
                "Return to Pokemon Center from Viridian Forest"
            ]
        elif "gym" in goal_lower or "badge" in goal_lower:
            suggestions = [
                "Navigate to the nearest gym",
                "Challenge the gym leader",
                "Train Pokemon before gym battle"
            ]
        else:
            suggestions = [
                "Explore current area and identify location",
                "Navigate to Pokemon Center for healing",
                "Check Pokemon party status and health",
                "Explore nearby areas for trainers or items"
            ]
        
        print("💡 Suggested tasks based on your goal:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        print(f"\n📝 Just type any of these tasks or describe what you want Claude to do!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error showing goal: {e}")


def save_current_session_state(session_state, eevee):
    """Save current session state for continuity"""
    try:
        # Get current context if possible
        current_location = "unknown"
        if hasattr(eevee, '_capture_current_context'):
            context = eevee._capture_current_context()
            # Would extract location from context analysis here
        
        state = {
            "last_session": datetime.now().isoformat(),
            "current_objective": session_state.get("user_goal"),
            "progress": {
                "tasks_completed": 0,  # Would track from session
                "locations_found": 0
            },
            "memory_session": getattr(eevee, 'memory_session', 'default'),
            "locations_discovered": session_state.get("session_data", {}).get("locations_discovered", []),
            "current_location": current_location
        }
        
        save_session_state(state)
        print("💾 Session state saved for next time.")
        
    except Exception as e:
        print(f"⚠️ Could not save session state: {e}")


def show_okr_status():
    """Display current OKR status"""
    try:
        project_root = Path(__file__).parent.parent
        okr_file = project_root / "OKR.md"
        
        if okr_file.exists():
            with open(okr_file, 'r') as f:
                content = f.read()
            
            print("\n📈 OBJECTIVES & KEY RESULTS")
            print("=" * 40)
            
            # Extract and show just the objectives section
            lines = content.split('\n')
            in_objectives = False
            for line in lines:
                if line.startswith('## Current Objectives'):
                    in_objectives = True
                    continue
                elif line.startswith('## Progress Log'):
                    break
                elif in_objectives and line.strip():
                    print(line)
            
            print("=" * 40)
            print(f"📄 Full report: {okr_file}")
        else:
            print("ℹ️ No OKR.md file found. Use --enable-okr to start tracking.")
    
    except Exception as e:
        print(f"❌ Error reading OKR.md: {e}")

def main():
    """Main Eevee v1 execution function"""
    try:
        # Parse arguments and setup
        args = parse_arguments()
        eevee_dir = setup_environment()
        
        # Print startup header
        print_header(args)
        
        # Initialize Eevee system (fallback to basic version for now)
        start_time = time.time()
        
        try:
            # Try to use enhanced Eevee v1 components when available
            eevee = EeveeAgent(
                window_title=args.window_title,
                model=args.model,
                memory_session=args.memory_session,
                verbose=args.verbose,
                debug=args.debug,
                enable_neo4j=args.neo4j_memory
            )
            print("🚀 Enhanced Eevee v1 system initialized")
        except NameError:
            # Fallback to basic implementation
            eevee = EeveeAnalyzer(window_title=args.window_title)
            print("🔄 Using basic Eevee implementation (v1 components loading...)")
        
        # Clear memory if requested
        if args.clear_memory:
            print(f"🧹 Clearing memory session: {args.memory_session}")
            # TODO: Implement memory clearing when MemorySystem is available
        
        # Initialize training data collector if needed
        training_collector = None
        if args.save_training_data:
            project_root = eevee_dir.parent
            training_collector = TrainingDataCollector(
                project_root=project_root,
                session_id=args.training_session
            )
            
            # Determine max steps (--steps overrides --max-steps for training)
            max_steps = args.steps if args.steps else args.max_steps
            training_collector.start_training_session(
                task_description=args.task,
                max_steps=max_steps,
                model=args.model
            )
        
        # Check if interactive mode is requested
        if args.interactive:
            # Interactive mode - enter chat interface
            interactive_mode(eevee, args)
            return
        
        # Validate that a task is provided for non-interactive mode
        if not args.task:
            print("❌ Error: Task is required in non-interactive mode.")
            print("💡 Use --interactive for chat mode or provide a task description.")
            print("Example: python run_eevee.py 'check my Pokemon party'")
            sys.exit(1)
        
        # Execute the task
        print(f"\n🎯 Executing task: {args.task}")
        
        if args.dry_run:
            # Dry run: analyze and plan without execution
            result = {
                "task": args.task,
                "status": "dry_run_completed",
                "analysis": f"DRY RUN: Would analyze and execute the task '{args.task}' using {args.model}",
                "steps_executed": 0,
                "execution_time": time.time() - start_time
            }
            print("🔍 Dry run completed - no actual actions performed")
        else:
            # Enhanced execution with optional training data collection
            if hasattr(eevee, 'execute_task'):
                # Use enhanced EeveeAgent
                max_steps = args.steps if args.steps else args.max_steps
                result = eevee.execute_task(args.task, max_steps=max_steps)
            elif hasattr(eevee, 'perform_custom_task'):
                # Fallback to basic implementation
                analysis = eevee.perform_custom_task(args.task)
                result = {
                    "task": args.task,
                    "status": "completed" if analysis else "failed",
                    "analysis": analysis or "Task execution failed",
                    "steps_executed": 1,
                    "execution_time": time.time() - start_time
                }
                
                # Create mock training data for basic implementation
                if training_collector:
                    # For basic implementation, create a single step entry
                    training_collector.current_session.total_steps = 1
                    step = ExecutionStep(
                        step_number=1,
                        timestamp=datetime.now().isoformat(),
                        screenshot_before=None,
                        screenshot_after=None,
                        ai_analysis=result.get("analysis", "Basic task execution"),
                        action_taken="perform_custom_task",
                        action_reasoning="Using basic Eevee implementation",
                        success=result.get("status") == "completed"
                    )
                    training_collector.current_session.execution_trace.append(step)
        
        # Finalize training data collection if enabled
        if training_collector and not args.dry_run:
            task_completed = result.get("status") in ["success", "completed"]
            
            # Update session with proper step count
            if training_collector.current_session:
                training_collector.current_session.total_steps = result.get("steps_executed", 0)
                training_collector.current_session.final_result = result
            
            training_collector.end_training_session(
                final_result=result,
                task_completed=task_completed
            )
        
        # Format and display output
        formatted_output = format_output(result, args.output_format)
        print(f"\n{formatted_output}")
        
        # Save report if requested
        if args.save_report:
            save_report(result, eevee_dir, args.output_format)
        
        # Exit with appropriate code
        exit_code = 0 if result.get("status") in ["success", "completed", "dry_run_completed"] else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n👋 Eevee interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.debug if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()