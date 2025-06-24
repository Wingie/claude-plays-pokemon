"""
Provider Configuration Utility for Eevee AI System
Handles environment-based provider switching and configuration management
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Centralized Task-to-Model Mapping
# Single source of truth for all AI task assignments
TASK_MODEL_MAPPING = {
    # Vision tasks (require screenshot analysis)
    "screenshot_analysis": "pixtral-12b-2409",      # Mistral's vision specialist
    "battle_decisions": "pixtral-12b-2409",         # Vision + battle strategy  
    "menu_analysis": "pixtral-12b-2409",            # Menu/UI recognition
    
    # Text reasoning tasks
    "template_selection": "mistral-large-latest",   # Template choice reasoning
    "task_execution": "mistral-large-latest",       # Multi-step task planning
    "navigation_decisions": "mistral-large-latest", # Movement strategy
    
    # Simple text tasks
    "text_only": "mistral-large-latest",            # Basic text processing
    "prompt_improvement": "mistral-large-latest",   # Prompt engineering
}

def get_model_for_task(task_type: str) -> str:
    """
    Get the assigned model for any task type, considering hybrid mode
    
    Args:
        task_type: Task type from TASK_MODEL_MAPPING keys
        
    Returns:
        Specific model name to use for this task
    """
    # Check if we're in hybrid mode
    hybrid_mode = os.getenv('HYBRID_MODE', 'false').lower() == 'true'
    llm_provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
    
    if hybrid_mode and llm_provider == 'hybrid':
        # Hybrid mode: select model based on provider assignment
        if task_type in ["screenshot_analysis", "battle_decisions", "menu_analysis"]:
            # Visual tasks use visual provider
            visual_provider = os.getenv('VISUAL_PROVIDER', 'gemini').lower()
            if visual_provider == 'gemini':
                return os.getenv('GEMINI_DEFAULT_MODEL', 'gemini-2.0-flash-exp')
            else:
                return os.getenv('MISTRAL_VISION_MODEL', 'pixtral-12b-2409')
        else:
            # Strategic tasks use strategic provider  
            strategic_provider = os.getenv('STRATEGIC_PROVIDER', 'mistral').lower()
            if strategic_provider == 'mistral':
                return os.getenv('MISTRAL_DEFAULT_MODEL', 'mistral-large-latest')
            else:
                return os.getenv('GEMINI_DEFAULT_MODEL', 'gemini-2.0-flash-exp')
    
    # Non-hybrid mode: use original mapping
    return TASK_MODEL_MAPPING.get(task_type, "mistral-large-latest")

def get_provider_for_task(task_type: str) -> str:
    """
    Get provider for task type, considering hybrid mode configuration
    
    Args:
        task_type: Task type from TASK_MODEL_MAPPING keys
        
    Returns:
        Provider name ("mistral" or "gemini")
    """
    # Check if we're in hybrid mode
    hybrid_mode = os.getenv('HYBRID_MODE', 'false').lower() == 'true'
    llm_provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
    
    if hybrid_mode and llm_provider == 'hybrid':
        # Hybrid mode: use different providers for different tasks
        if task_type in ["screenshot_analysis", "battle_decisions", "menu_analysis"]:
            return os.getenv('VISUAL_PROVIDER', 'gemini').lower()
        else:
            return os.getenv('STRATEGIC_PROVIDER', 'mistral').lower()
    
    # Non-hybrid mode: use original logic
    model = get_model_for_task(task_type)
    if "pixtral" in model or "mistral" in model:
        return "mistral"
    elif "gemini" in model:
        return "gemini"
    return "mistral"  # default

def detect_task_type(has_image: bool = False, context: str = "") -> str:
    """
    Auto-detect task type based on context
    
    Args:
        has_image: Whether this task involves image analysis
        context: Context string to help determine task type
        
    Returns:
        Task type from TASK_MODEL_MAPPING keys
    """
    if has_image:
        if "battle" in context.lower():
            return "battle_decisions"
        elif "menu" in context.lower():
            return "menu_analysis"
        else:
            return "screenshot_analysis"
    else:
        if "template" in context.lower():
            return "template_selection"
        elif "execution" in context.lower() or "task" in context.lower():
            return "task_execution"
        elif "navigation" in context.lower() or "movement" in context.lower():
            return "navigation_decisions"
        else:
            return "text_only"

def list_task_assignments() -> Dict[str, str]:
    """
    Get a copy of current task-to-model assignments
    
    Returns:
        Dictionary of task_type -> model assignments
    """
    return TASK_MODEL_MAPPING.copy()

def get_prompt_template_path(provider: str, template_type: str = "base_prompts") -> Path:
    """
    Get the path to provider-specific prompt templates
    
    Args:
        provider: Provider name ('gemini' or 'mistral')
        template_type: Type of template file ('base_prompts', 'playbooks', etc.)
        
    Returns:
        Path to the template file
    """
    base_dir = Path(__file__).parent / "prompts" / "providers" / provider.lower()
    return base_dir / f"{template_type}.yaml"

def get_provider_prompt_style(provider: str) -> Dict[str, str]:
    """
    Get prompt style preferences for each provider
    
    Args:
        provider: Provider name ('gemini' or 'mistral')
        
    Returns:
        Dictionary with style preferences
    """
    styles = {
        "gemini": {
            "format": "documentation",
            "structure": "structured_sections",
            "character_approach": "third_person_guidance",
            "best_for": "detailed_analysis_and_planning"
        },
        "mistral": {
            "format": "character_first", 
            "structure": "conversational",
            "character_approach": "first_person_roleplay",
            "best_for": "immediate_action_and_roleplay"
        }
    }
    
    return styles.get(provider.lower(), styles["gemini"])  # Default to Gemini style

class ProviderConfig:
    """Configuration manager for LLM providers and model selection"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize provider configuration
        
        Args:
            verbose: Enable verbose logging for configuration loading
        """
        self.verbose = verbose
        self._load_configuration()
        
        if self.verbose:
            self._print_configuration_summary()
    
    def _load_configuration(self):
        """Load configuration from environment variables"""
        
        # API Keys
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
        
        # Provider Selection
        self.primary_provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
        self.fallback_provider = os.getenv('FALLBACK_PROVIDER', 'mistral').lower()
        self.auto_fallback = os.getenv('AUTO_FALLBACK', 'true').lower() == 'true'
        
        # Hybrid Mode Configuration
        self.hybrid_mode = os.getenv('HYBRID_MODE', 'false').lower() == 'true'
        self.visual_provider = os.getenv('VISUAL_PROVIDER', 'gemini').lower()
        self.strategic_provider = os.getenv('STRATEGIC_PROVIDER', 'mistral').lower()
        self.template_provider = os.getenv('TEMPLATE_PROVIDER', 'mistral').lower()
        
        # Model Preferences
        self.gemini_default = os.getenv('GEMINI_DEFAULT_MODEL', 'gemini-2.0-flash-exp')
        self.mistral_default = os.getenv('MISTRAL_DEFAULT_MODEL', 'mistral-large-latest')
        self.mistral_vision = os.getenv('MISTRAL_VISION_MODEL', 'pixtral-12b-2409')
        
        # Circuit Breaker Settings
        self.circuit_breaker_reset_time = int(os.getenv('CIRCUIT_BREAKER_RESET_TIME', '300'))
        self.api_failure_threshold = int(os.getenv('API_FAILURE_THRESHOLD', '5'))
        
        # Eevee Specific
        self.template_selection_model = os.getenv('TEMPLATE_SELECTION_MODEL', 'gemini-2.0-flash-exp')
        self.gameplay_model = os.getenv('GAMEPLAY_MODEL', 'gemini-2.0-flash-exp')
        self.eevee_verbose = os.getenv('EEVEE_VERBOSE', 'false').lower() == 'true'
        self.eevee_debug = os.getenv('EEVEE_DEBUG', 'false').lower() == 'true'
        
        # Performance Tuning
        self.template_selection_max_tokens = int(os.getenv('TEMPLATE_SELECTION_MAX_TOKENS', '500'))
        self.gameplay_max_tokens = int(os.getenv('GAMEPLAY_MAX_TOKENS', '1000'))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
    
    def get_llm_manager_config(self) -> Dict[str, Any]:
        """
        Get configuration dictionary for LLMAPIManager
        
        Returns:
            Configuration dictionary for initializing LLMAPIManager
        """
        return {
            'default_provider': self.primary_provider,
            'fallback_provider': self.fallback_provider,
            'auto_fallback': self.auto_fallback,
            'gemini': {
                'api_key': self.gemini_api_key,
                'circuit_breaker_reset_time': self.circuit_breaker_reset_time,
                'api_failure_threshold': self.api_failure_threshold,
                'default_model': self.gemini_default
            },
            'mistral': {
                'api_key': self.mistral_api_key,
                'circuit_breaker_reset_time': self.circuit_breaker_reset_time,
                'api_failure_threshold': self.api_failure_threshold,
                'default_model': self.mistral_default,
                'vision_model': self.mistral_vision
            }
        }
    
    def get_eevee_config(self) -> Dict[str, Any]:
        """
        Get configuration dictionary for EeveeAgent
        
        Returns:
            Configuration dictionary for EeveeAgent initialization
        """
        return {
            'model': self.gameplay_model,
            'verbose': self.eevee_verbose,
            'debug': self.eevee_debug,
            'template_selection_model': self.template_selection_model,
            'max_tokens': self.gameplay_max_tokens
        }
    
    def get_available_providers(self) -> list:
        """
        Get list of available providers based on API keys
        
        Returns:
            List of provider names that have valid API keys
        """
        available = []
        
        if self.gemini_api_key:
            available.append('gemini')
        
        if self.mistral_api_key:
            available.append('mistral')
        
        return available
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate current configuration and return status
        
        Returns:
            Dictionary with validation results and recommendations
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'available_providers': self.get_available_providers()
        }
        
        # Check for API keys
        if not self.gemini_api_key and not self.mistral_api_key:
            validation_result['valid'] = False
            validation_result['errors'].append("No API keys found. Set GEMINI_API_KEY and/or MISTRAL_API_KEY")
        
        # Check primary provider availability
        if self.primary_provider not in validation_result['available_providers']:
            validation_result['warnings'].append(f"Primary provider '{self.primary_provider}' has no API key")
        
        # Check fallback provider availability
        if self.auto_fallback and self.fallback_provider not in validation_result['available_providers']:
            validation_result['warnings'].append(f"Fallback provider '{self.fallback_provider}' has no API key")
        
        # Check model configurations
        if self.primary_provider == 'gemini' and not self.gemini_api_key:
            validation_result['errors'].append("Primary provider is Gemini but GEMINI_API_KEY is missing")
        
        if self.primary_provider == 'mistral' and not self.mistral_api_key:
            validation_result['errors'].append("Primary provider is Mistral but MISTRAL_API_KEY is missing")
        
        return validation_result
    
    def get_prompt_manager_config(self) -> Dict[str, Any]:
        """
        Get configuration for PromptManager with provider-specific settings
        
        Returns:
            Configuration dictionary for PromptManager
        """
        return {
            'current_provider': self.primary_provider,
            'fallback_provider': self.fallback_provider,
            'prompt_style': get_provider_prompt_style(self.primary_provider),
            'template_path': get_prompt_template_path(self.primary_provider),
            'verbose': self.eevee_verbose
        }
    
    def switch_provider(self, provider: str) -> bool:
        """
        Temporarily switch primary provider (runtime only)
        
        Args:
            provider: Provider name ('gemini' or 'mistral')
            
        Returns:
            True if switch was successful, False otherwise
        """
        if provider.lower() in self.get_available_providers():
            self.primary_provider = provider.lower()
            if self.verbose:
                print(f"✅ Switched to provider: {provider}")
            return True
        else:
            if self.verbose:
                print(f"❌ Cannot switch to {provider}: API key not available")
            return False
    
    def get_model_for_task(self, task_type: str, has_vision: bool = False) -> str:
        """
        Get the best model for a specific task type
        
        Args:
            task_type: Type of task ('template_selection', 'gameplay', 'vision')
            has_vision: Whether the task requires vision capabilities
            
        Returns:
            Model name to use for the task
        """
        if task_type == 'template_selection':
            return self.template_selection_model
        elif task_type == 'gameplay':
            return self.gameplay_model
        elif task_type == 'vision' or has_vision:
            # Prefer vision-capable models
            if self.primary_provider == 'mistral':
                return self.mistral_vision
            else:
                return self.gemini_default
        else:
            # Default to gameplay model
            return self.gameplay_model
    
    def _print_configuration_summary(self):
        """Print configuration summary for debugging"""
        print("🔧 Provider Configuration Summary")
        print("=" * 50)
        print(f"Primary Provider: {self.primary_provider}")
        print(f"Fallback Provider: {self.fallback_provider}")
        print(f"Auto Fallback: {self.auto_fallback}")
        
        if self.hybrid_mode and self.primary_provider == 'hybrid':
            print(f"🔀 HYBRID MODE: Enabled")
            print(f"   Visual Provider: {self.visual_provider}")
            print(f"   Strategic Provider: {self.strategic_provider}")
            print(f"   Template Provider: {self.template_provider}")
        
        print(f"Available Providers: {self.get_available_providers()}")
        print(f"Template Selection Model: {self.template_selection_model}")
        print(f"Gameplay Model: {self.gameplay_model}")
        print("=" * 50)

def get_hybrid_config() -> dict:
    """
    Get hybrid mode configuration from environment
    
    Returns:
        Dictionary with hybrid mode settings
    """
    return {
        'enabled': os.getenv('HYBRID_MODE', 'false').lower() == 'true' and 
                  os.getenv('LLM_PROVIDER', 'gemini').lower() == 'hybrid',
        'visual_provider': os.getenv('VISUAL_PROVIDER', 'gemini').lower(),
        'strategic_provider': os.getenv('STRATEGIC_PROVIDER', 'mistral').lower(),
        'template_provider': os.getenv('TEMPLATE_PROVIDER', 'mistral').lower()
    }

def get_provider_for_hybrid_task(task_category: str) -> str:
    """
    Get provider for task category in hybrid mode
    
    Args:
        task_category: 'visual', 'strategic', or 'template'
        
    Returns:
        Provider name for the task category
    """
    hybrid_config = get_hybrid_config()
    
    if not hybrid_config['enabled']:
        return os.getenv('LLM_PROVIDER', 'gemini').lower()
    
    if task_category == 'visual':
        return hybrid_config['visual_provider']
    elif task_category == 'strategic':
        return hybrid_config['strategic_provider']
    elif task_category == 'template':
        return hybrid_config['template_provider']
    else:
        return hybrid_config['strategic_provider']  # Default to strategic

# Global configuration instance
_global_config = None

def get_provider_config(verbose: bool = False) -> ProviderConfig:
    """
    Get global provider configuration instance
    
    Args:
        verbose: Enable verbose logging
        
    Returns:
        ProviderConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ProviderConfig(verbose=verbose)
    return _global_config

def create_llm_manager_with_env_config():
    """
    Create LLMAPIManager with environment-based configuration
    
    Returns:
        Configured LLMAPIManager instance
    """
    try:
        from llm_api import LLMAPIManager
        config = get_provider_config()
        return LLMAPIManager(config.get_llm_manager_config())
    except ImportError as e:
        print(f"❌ Cannot import LLMAPIManager: {e}")
        return None

def setup_eevee_with_env_config():
    """
    Get EeveeAgent configuration from environment variables
    
    Returns:
        Configuration dictionary for EeveeAgent
    """
    config = get_provider_config()
    return config.get_eevee_config()

# Command-line utility functions
def print_current_config():
    """Print current configuration to console"""
    config = get_provider_config(verbose=True)
    validation = config.validate_configuration()
    
    print("\n🔍 Configuration Validation:")
    print(f"Valid: {'✅' if validation['valid'] else '❌'}")
    
    if validation['errors']:
        print("\n❌ Errors:")
        for error in validation['errors']:
            print(f"  • {error}")
    
    if validation['warnings']:
        print("\n⚠️ Warnings:")
        for warning in validation['warnings']:
            print(f"  • {warning}")

def set_provider_env_var(provider: str):
    """Set LLM_PROVIDER environment variable"""
    os.environ['LLM_PROVIDER'] = provider
    print(f"✅ Set LLM_PROVIDER to {provider}")
    print("💡 This change is temporary. Update .env file for permanent change.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Eevee Provider Configuration Utility")
    parser.add_argument('--show-config', action='store_true', help='Show current configuration')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--set-provider', choices=['gemini', 'mistral'], help='Set primary provider')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.show_config or not any(vars(args).values()):
        print_current_config()
    
    if args.validate:
        config = get_provider_config(verbose=args.verbose)
        validation = config.validate_configuration()
        
        if validation['valid']:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has errors")
            sys.exit(1)
    
    if args.set_provider:
        set_provider_env_var(args.set_provider)