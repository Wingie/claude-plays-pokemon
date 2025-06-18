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
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

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
        help="Natural language description of the Pokemon task to execute"
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
    
    return parser.parse_args()

def setup_environment():
    """Setup Eevee v1 directory structure and environment"""
    eevee_dir = Path(__file__).parent
    
    # Create required directories
    directories = [
        eevee_dir / "memory",
        eevee_dir / "reports", 
        eevee_dir / "prompts",
        eevee_dir / "prompts" / "experimental",
        eevee_dir / "utils",
        eevee_dir / "analysis"  # For screenshots and analysis files
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
    
    return eevee_dir

def print_header(args):
    """Print Eevee v1 startup header"""
    print("🔮 " + "="*60)
    print("🔮 EEVEE v1 - AI Pokemon Task Execution System")
    print("🔮 " + "="*60)
    print(f"📋 Task: {args.task}")
    print(f"🤖 Model: {args.model}")
    print(f"🧠 Memory Session: {args.memory_session}")
    print(f"🎮 Emulator: {args.window_title}")
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
                debug=args.debug
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
            # For now, use the custom task functionality from basic implementation
            if hasattr(eevee, 'perform_custom_task'):
                analysis = eevee.perform_custom_task(args.task)
                result = {
                    "task": args.task,
                    "status": "completed" if analysis else "failed",
                    "analysis": analysis or "Task execution failed",
                    "steps_executed": 1,
                    "execution_time": time.time() - start_time
                }
            else:
                # Enhanced execution when EeveeAgent is available
                result = eevee.execute_task(args.task, max_steps=args.max_steps)
        
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