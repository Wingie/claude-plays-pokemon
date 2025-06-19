"""
Real-time Interruption System for Eevee
Provides Claude Code-like interruption capabilities during continuous gameplay
"""

import threading
import time
import queue
import sys
from typing import Dict, Any, Optional, Callable

class InterruptionHandler:
    """Handles real-time interruption during continuous gameplay"""
    
    def __init__(self):
        self.command_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.running = True  # Start as running, stop when quit is called
        self.paused = False
        self.input_thread = None
        self.commands = {
            'p': self._pause_command,
            'r': self._resume_command,
            'q': self._quit_command,
            's': self._status_command,
            'h': self._help_command
        }
        
    def start_monitoring(self):
        """Start the input monitoring thread"""
        if self.input_thread and self.input_thread.is_alive():
            return
            
        self.running = True
        self.input_thread = threading.Thread(target=self._monitor_input, daemon=True)
        self.input_thread.start()
        print("🎮 Real-time controls active:")
        print("   'p' = pause, 'r' = resume, 'q' = quit, 's' = status, 'h' = help")
    
    def stop_monitoring(self):
        """Stop the input monitoring thread"""
        self.running = False
        if self.input_thread:
            self.input_thread.join(timeout=1.0)
    
    def _monitor_input(self):
        """Monitor keyboard input in separate thread"""
        try:
            import termios
            import tty
            import select
            
            # Set terminal to raw mode for single character input
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            
            while self.running:
                # Check if input is available (non-blocking)
                if select.select([sys.stdin], [], [], 0.1) == ([sys.stdin], [], []):
                    char = sys.stdin.read(1).lower()
                    
                    if char in self.commands:
                        try:
                            self.commands[char]()
                        except Exception as e:
                            self.status_queue.put(f"⚠️ Command error: {e}")
                    elif char == '\x03':  # Ctrl+C
                        self.command_queue.put({"type": "interrupt", "source": "ctrl_c"})
                        break
                    elif char == '\n' or char == '\r':
                        continue  # Ignore newlines
                    else:
                        self.status_queue.put(f"❓ Unknown command: '{char}' (press 'h' for help)")
                        
        except ImportError:
            # Fallback for systems without termios (Windows)
            self._monitor_input_fallback()
        except Exception as e:
            self.status_queue.put(f"⚠️ Input monitoring error: {e}")
        finally:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except:
                pass
    
    def _monitor_input_fallback(self):
        """Fallback input monitoring for systems without termios"""
        while self.running:
            try:
                # Simple input with prompt
                char = input("Enter command (p/r/q/s/h): ").lower().strip()
                if char and char[0] in self.commands:
                    self.commands[char[0]]()
                elif char == 'quit' or char == 'exit':
                    self._quit_command()
                time.sleep(0.1)
            except (EOFError, KeyboardInterrupt):
                self.command_queue.put({"type": "interrupt", "source": "keyboard"})
                break
            except Exception as e:
                self.status_queue.put(f"⚠️ Input error: {e}")
    
    def _pause_command(self):
        """Handle pause command"""
        if not self.paused:
            self.paused = True
            self.command_queue.put({"type": "pause"})
            self.status_queue.put("⏸️ Gameplay paused")
        else:
            self.status_queue.put("⏸️ Already paused")
    
    def _resume_command(self):
        """Handle resume command"""
        if self.paused:
            self.paused = False
            self.command_queue.put({"type": "resume"})
            self.status_queue.put("▶️ Gameplay resumed")
        else:
            self.status_queue.put("▶️ Not paused")
    
    def _quit_command(self):
        """Handle quit command"""
        self.command_queue.put({"type": "quit"})
        self.status_queue.put("🛑 Quit requested")
        self.running = False
    
    def _status_command(self):
        """Handle status command"""
        status = "▶️ Running" if not self.paused else "⏸️ Paused"
        self.status_queue.put(f"📊 Status: {status}")
    
    def _help_command(self):
        """Handle help command"""
        help_text = """
🎮 Real-time Controls:
  'p' - Pause gameplay
  'r' - Resume gameplay  
  'q' - Quit gracefully
  's' - Show status
  'h' - Show this help
  Ctrl+C - Emergency stop
        """
        self.status_queue.put(help_text.strip())
    
    def get_command(self, timeout: float = 0) -> Optional[Dict[str, Any]]:
        """Get next command from queue (non-blocking by default)"""
        try:
            return self.command_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_status_message(self) -> Optional[str]:
        """Get next status message from queue (non-blocking)"""
        try:
            return self.status_queue.get_nowait()
        except queue.Empty:
            return None
    
    def is_paused(self) -> bool:
        """Check if gameplay is currently paused"""
        return self.paused
    
    def should_quit(self) -> bool:
        """Check if quit was requested"""
        return not self.running


class GameplayController:
    """Controls gameplay loop with interruption support"""
    
    def __init__(self, turn_delay: float = 1.5):
        self.interruption_handler = InterruptionHandler()
        self.turn_delay = turn_delay
        self.turn_count = 0
        self.max_turns = 100
        self.goal = ""
        
    def start_continuous_gameplay(
        self, 
        goal: str, 
        max_turns: int = 100,
        turn_callback: Optional[Callable] = None
    ):
        """Start continuous gameplay with interruption support"""
        self.goal = goal
        self.max_turns = max_turns
        self.turn_count = 0
        
        # Start input monitoring
        self.interruption_handler.start_monitoring()
        
        print(f"🎯 Goal: {goal}")
        print(f"📊 Max turns: {max_turns}")
        print("Press Ctrl+C to stop at any time")
        print("-" * 60)
        
        try:
            while self.turn_count < max_turns and not self.interruption_handler.should_quit():
                # Handle interruption commands
                self._handle_interruptions()
                
                # Skip turn if paused
                if self.interruption_handler.is_paused():
                    time.sleep(0.1)
                    continue
                
                self.turn_count += 1
                print(f"\n🎯 Turn {self.turn_count}/{max_turns}")
                
                # Execute turn callback if provided
                if turn_callback:
                    try:
                        should_continue = turn_callback(self.turn_count, self.goal)
                        if not should_continue:
                            break
                    except Exception as e:
                        print(f"⚠️ Turn execution error: {e}")
                        break
                
                # Wait between turns (with interruption checking)
                self._interruptible_sleep(self.turn_delay)
                
        except KeyboardInterrupt:
            print("\n🛑 Gameplay interrupted by user")
        finally:
            self.interruption_handler.stop_monitoring()
            print(f"\n🏁 Gameplay session ended after {self.turn_count} turns")
    
    def _handle_interruptions(self):
        """Handle any pending interruption commands"""
        # Process commands
        command = self.interruption_handler.get_command()
        if command:
            cmd_type = command.get("type")
            if cmd_type == "interrupt" or cmd_type == "quit":
                print(f"\n🛑 {cmd_type.capitalize()} received")
            elif cmd_type == "pause":
                print("⏸️ Paused - press 'r' to resume")
            elif cmd_type == "resume":
                print("▶️ Resuming gameplay...")
        
        # Display status messages
        status_msg = self.interruption_handler.get_status_message()
        if status_msg:
            print(f"💬 {status_msg}")
    
    def _interruptible_sleep(self, duration: float):
        """Sleep with interruption checking"""
        sleep_interval = 0.1
        elapsed = 0
        
        while elapsed < duration and not self.interruption_handler.should_quit():
            if not self.interruption_handler.is_paused():
                time.sleep(min(sleep_interval, duration - elapsed))
                elapsed += sleep_interval
            else:
                time.sleep(sleep_interval)  # Check for resume command
            
            # Handle any commands that came in during sleep
            self._handle_interruptions()
    
    def is_running(self) -> bool:
        """Check if gameplay should continue"""
        return (self.turn_count < self.max_turns and 
                not self.interruption_handler.should_quit())
    
    def get_current_turn(self) -> int:
        """Get current turn number"""
        return self.turn_count
    
    def get_goal(self) -> str:
        """Get current goal"""
        return self.goal