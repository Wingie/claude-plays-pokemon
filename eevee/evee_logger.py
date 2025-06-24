"""
Comprehensive Logging System for Eevee Pokemon AI
Provides separate log files for different types of output and debugging
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional, TextIO
from datetime import datetime

class ComprehensiveLogger:
    """Multi-stream logger that separates different types of output"""
    
    def __init__(self, session_name: str = None, runs_dir: Path = None):
        if runs_dir is None:
            runs_dir = Path(__file__).parent / "runs"
        
        # Create session directory with consistent naming
        if session_name is None:
            session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        elif not session_name.startswith("session_"):
            # Ensure consistent session_ prefix
            session_name = f"session_{session_name}"
        
        self.session_dir = runs_dir / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log files
        self.stdout_log = self.session_dir / "stdout.log"
        self.stderr_log = self.session_dir / "stderr.log"
        self.visual_log = self.session_dir / "visual_analysis.log"
        self.hybrid_log = self.session_dir / "hybrid_mode.log"
        self.debug_log = self.session_dir / "debug.log"
        self.gemini_log = self.session_dir / "gemini_debug.log"
        
        # Open log file handles
        self.stdout_file = open(self.stdout_log, 'a', encoding='utf-8', buffering=1)
        self.stderr_file = open(self.stderr_log, 'a', encoding='utf-8', buffering=1)
        self.visual_file = open(self.visual_log, 'a', encoding='utf-8', buffering=1)
        self.hybrid_file = open(self.hybrid_log, 'a', encoding='utf-8', buffering=1)
        self.debug_file = open(self.debug_log, 'a', encoding='utf-8', buffering=1)
        self.gemini_file = open(self.gemini_log, 'a', encoding='utf-8', buffering=1)
        
        # Store original stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Initialize logs
        self._write_header()
        
    def _write_header(self):
        """Write header to all log files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"=== EEVEE LOGGING SESSION STARTED: {timestamp} ===\n"
        
        for log_file in [self.stdout_file, self.stderr_file, self.visual_file, 
                        self.hybrid_file, self.debug_file, self.gemini_file]:
            log_file.write(header)
            log_file.flush()
    
    def enable_stdout_stderr_capture(self):
        """Redirect stdout and stderr to log files while maintaining console output"""
        sys.stdout = TeeOutput(self.original_stdout, self.stdout_file)
        sys.stderr = TeeOutput(self.original_stderr, self.stderr_file)
        
        print("📋 COMPREHENSIVE LOGGING ENABLED")
        print(f"📁 Session logs: {self.session_dir}")
        print(f"📄 stdout.log: {self.stdout_log}")
        print(f"📄 stderr.log: {self.stderr_log}")
        print(f"👁️  visual_analysis.log: {self.visual_log}")
        print(f"🔀 hybrid_mode.log: {self.hybrid_log}")
        print(f"🐛 debug.log: {self.debug_log}")
        print(f"🔍 gemini_debug.log: {self.gemini_log}")
    
    def disable_stdout_stderr_capture(self):
        """Restore original stdout and stderr"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def log_visual_analysis(self, step: int, provider: str, model: str, 
                          prompt: str, response: str, screenshot_path: str = None):
        """Log visual analysis details"""
        timestamp = self._timestamp()
        
        log_entry = f"""
[{timestamp}] 👁️  VISUAL ANALYSIS STEP {step}
Provider: {provider}
Model: {model}
Screenshot: {screenshot_path or 'N/A'}
Prompt Length: {len(prompt)} chars
Response Length: {len(response)} chars
Response Preview: {response[:200]}...
--- FULL PROMPT ---
{prompt}
--- FULL RESPONSE ---
{response}
=====================================

"""
        self.visual_file.write(log_entry)
        self.visual_file.flush()
    
    def log_hybrid_routing(self, task_type: str, provider: str, model: str, 
                          decision_reason: str = ""):
        """Log hybrid mode provider routing decisions"""
        timestamp = self._timestamp()
        
        log_entry = f"""
[{timestamp}] 🔀 HYBRID MODE ROUTING
Task Type: {task_type}
Selected Provider: {provider}
Selected Model: {model}
Decision Reason: {decision_reason}
=====================================

"""
        self.hybrid_file.write(log_entry)
        self.hybrid_file.flush()
    
    def log_gemini_debug(self, call_type: str, request_data: dict, 
                        response_data: dict, error: str = None):
        """Log detailed Gemini API call information"""
        timestamp = self._timestamp()
        
        log_entry = f"""
[{timestamp}] 🔍 GEMINI API DEBUG - {call_type}
--- REQUEST ---
{self._format_dict(request_data)}
--- RESPONSE ---
{self._format_dict(response_data)}
--- ERROR ---
{error or 'None'}
=====================================

"""
        self.gemini_file.write(log_entry)
        self.gemini_file.flush()
    
    def log_debug(self, level: str, message: str, context: dict = None):
        """Log general debug information"""
        timestamp = self._timestamp()
        
        log_entry = f"[{timestamp}] {level}: {message}\n"
        if context:
            log_entry += f"Context: {self._format_dict(context)}\n"
        log_entry += "\n"
        
        self.debug_file.write(log_entry)
        self.debug_file.flush()
    
    def _timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def _format_dict(self, data: dict) -> str:
        """Format dictionary for logging"""
        if not data:
            return "None"
        
        formatted = ""
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            formatted += f"  {key}: {value}\n"
        return formatted
    
    def close(self):
        """Close all log files and restore stdout/stderr"""
        self.disable_stdout_stderr_capture()
        
        for log_file in [self.stdout_file, self.stderr_file, self.visual_file,
                        self.hybrid_file, self.debug_file, self.gemini_file]:
            try:
                log_file.close()
            except:
                pass

class TeeOutput:
    """Tee output to both console and file"""
    
    def __init__(self, console: TextIO, log_file: TextIO):
        self.console = console
        self.log_file = log_file
    
    def write(self, message: str):
        self.console.write(message)
        self.log_file.write(message)
        self.console.flush()
        self.log_file.flush()
    
    def flush(self):
        self.console.flush()
        self.log_file.flush()
    
    def __getattr__(self, name):
        return getattr(self.console, name)

# Global logger instance
_comprehensive_logger: Optional[ComprehensiveLogger] = None

def init_comprehensive_logger(session_name: str = None) -> ComprehensiveLogger:
    """Initialize global comprehensive logger"""
    global _comprehensive_logger
    _comprehensive_logger = ComprehensiveLogger(session_name)
    return _comprehensive_logger

def get_comprehensive_logger() -> Optional[ComprehensiveLogger]:
    """Get current comprehensive logger instance"""
    return _comprehensive_logger

def enable_comprehensive_logging(session_name: str = None):
    """Enable comprehensive logging with stdout/stderr capture"""
    logger = init_comprehensive_logger(session_name)
    logger.enable_stdout_stderr_capture()
    return logger

def disable_comprehensive_logging():
    """Disable comprehensive logging"""
    global _comprehensive_logger
    if _comprehensive_logger:
        _comprehensive_logger.close()
        _comprehensive_logger = None