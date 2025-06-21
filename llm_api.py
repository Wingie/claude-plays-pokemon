"""
Unified LLM API Module for Pokemon AI System
Supports multiple providers (Gemini, Mistral) with centralized error handling and configuration
"""

import os
import time
import base64
import json
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    MISTRAL = "mistral"

class ModelCapability(Enum):
    """Model capabilities"""
    TEXT = "text"
    VISION = "vision"
    BOTH = "both"

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    text: str
    button_presses: List[str]
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    response_time: Optional[float] = None
    tokens_used: Optional[int] = None

@dataclass
class LLMRequest:
    """Standardized LLM request format"""
    prompt: str
    image_data: Optional[str] = None
    use_tools: bool = False
    max_tokens: int = 1000
    temperature: float = 0.7
    model_preference: Optional[str] = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limited_models = set()
        self.circuit_breaker_open = False
        self.api_failure_count = 0
        self.last_failure_time = 0
        self.circuit_breaker_reset_time = config.get('circuit_breaker_reset_time', 300)
        self.api_failure_threshold = config.get('api_failure_threshold', 5)
    
    @abstractmethod
    def get_available_models(self) -> Dict[str, ModelCapability]:
        """Get available models and their capabilities"""
        pass
    
    @abstractmethod
    def call_api(self, request: LLMRequest) -> LLMResponse:
        """Make API call with provider-specific implementation"""
        pass
    
    @abstractmethod
    def get_default_model(self, capability: ModelCapability) -> str:
        """Get default model for given capability"""
        pass
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should prevent API calls"""
        current_time = time.time()
        
        if self.circuit_breaker_open and (current_time - self.last_failure_time) > self.circuit_breaker_reset_time:
            self.circuit_breaker_open = False
            self.api_failure_count = 0
        
        return self.circuit_breaker_open
    
    def _record_api_success(self):
        """Record successful API call"""
        if self.api_failure_count > 0:
            self.api_failure_count = 0
    
    def _record_api_failure(self):
        """Record API failure and update circuit breaker"""
        self.api_failure_count += 1
        self.last_failure_time = time.time()
        
        if self.api_failure_count >= self.api_failure_threshold:
            self.circuit_breaker_open = True

class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize Gemini API
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.genai = genai
        
        # Model instances cache
        self._model_cache = {}
        
        # Function declaration for Pokemon controller
        self._init_function_declarations()
    
    def _init_function_declarations(self):
        """Initialize function declarations for tools"""
        try:
            from google.generativeai.types import FunctionDeclaration, Tool
            
            self.pokemon_function_declaration = FunctionDeclaration(
                name="pokemon_controller",
                description="Control Pokemon game with button presses",
                parameters={
                    "type": "object",
                    "properties": {
                        "buttons": {
                            "type": "string",
                            "description": "Single button press: up, down, left, right, a, b, start, select"
                        }
                    },
                    "required": ["buttons"]
                }
            )
            self.pokemon_tool = Tool(function_declarations=[self.pokemon_function_declaration])
        except Exception as e:
            print(f"⚠️ Function declaration failed for Gemini: {e}")
            self.pokemon_function_declaration = None
            self.pokemon_tool = None
    
    def get_available_models(self) -> Dict[str, ModelCapability]:
        """Get available Gemini models and their capabilities"""
        return {
            "gemini-2.0-flash-exp": ModelCapability.BOTH,
            "gemini-1.5-pro": ModelCapability.BOTH,
            "gemini-1.5-flash": ModelCapability.BOTH
        }
    
    def get_default_model(self, capability: ModelCapability) -> str:
        """Get default Gemini model for given capability"""
        return "gemini-2.0-flash-exp"  # Best performing model
    
    def _get_model_instance(self, model_name: str):
        """Get cached model instance"""
        if model_name not in self._model_cache:
            self._model_cache[model_name] = self.genai.GenerativeModel(model_name=model_name)
        return self._model_cache[model_name]
    
    def call_api(self, request: LLMRequest) -> LLMResponse:
        """Make Gemini API call with sophisticated error handling"""
        start_time = time.time()
        
        # Check circuit breaker
        if self._check_circuit_breaker():
            return LLMResponse(
                text="",
                button_presses=[],
                error="API circuit breaker is open",
                provider="gemini"
            )
        
        # Determine model to use
        available_models = self.get_available_models()
        
        if request.model_preference and request.model_preference in available_models:
            model_name = request.model_preference
        else:
            capability = ModelCapability.VISION if request.image_data else ModelCapability.TEXT
            model_name = self.get_default_model(capability)
        
        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                model = self._get_model_instance(model_name)
                
                # Prepare content parts
                content_parts = [request.prompt]
                
                if request.image_data:
                    content_parts.append({
                        "mime_type": "image/jpeg",
                        "data": base64.b64decode(request.image_data)
                    })
                
                # Make API call
                generation_config = {"max_output_tokens": request.max_tokens}
                
                if request.use_tools and self.pokemon_tool:
                    response = model.generate_content(
                        content_parts,
                        generation_config=generation_config,
                        tools=[self.pokemon_tool]
                    )
                else:
                    response = model.generate_content(
                        content_parts,
                        generation_config=generation_config
                    )
                
                # Process response
                result = self._process_gemini_response(response, request.use_tools)
                result.provider = "gemini"
                result.model = model_name
                result.response_time = time.time() - start_time
                
                self._record_api_success()
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle rate limiting with model switching
                if any(keyword in error_msg for keyword in ["429", "rate limit", "quota"]):
                    self.rate_limited_models.add(model_name)
                    
                    # Try to switch to different model
                    available = [m for m in available_models.keys() if m not in self.rate_limited_models]
                    if available:
                        model_name = available[0]
                        continue
                    else:
                        # All models rate limited, wait
                        retry_delay = self._parse_retry_delay(str(e), base_delay * (2 ** attempt))
                        time.sleep(retry_delay)
                        continue
                
                # Handle other retryable errors
                elif any(keyword in error_msg for keyword in ["timeout", "connection", "network"]):
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        time.sleep(retry_delay)
                        continue
                
                # Final attempt or non-retryable error
                if attempt == max_retries - 1:
                    self._record_api_failure()
                    return LLMResponse(
                        text="",
                        button_presses=[],
                        error=str(e),
                        provider="gemini",
                        model=model_name,
                        response_time=time.time() - start_time
                    )
        
        # Should never reach here
        self._record_api_failure()
        return LLMResponse(
            text="",
            button_presses=[],
            error="Max retries exceeded",
            provider="gemini"
        )
    
    def _process_gemini_response(self, response, use_tools: bool) -> LLMResponse:
        """Process Gemini API response into standardized format"""
        result = LLMResponse(text="", button_presses=[])
        
        if use_tools and response.candidates and response.candidates[0].content.parts:
            # Handle tool-enabled response
            for part in response.candidates[0].content.parts:
                if part.text:
                    result.text = part.text
                elif part.function_call and part.function_call.name == "pokemon_controller":
                    args = dict(part.function_call.args)
                    if "buttons" in args:
                        button = args["buttons"].lower().strip()
                        result.button_presses.append(button)
        else:
            # Handle text-only response
            result.text = response.text if response.text else ""
        
        # Parse buttons from text if no function calls
        if result.text and not result.button_presses:
            result.button_presses = self._parse_buttons_from_text(result.text)
        
        # Default fallback
        if not result.button_presses:
            result.button_presses = ["a"]
        
        return result
    
    def _parse_buttons_from_text(self, text: str) -> List[str]:
        """Parse button commands from text response"""
        import re
        
        button_patterns = [
            r"press (\w+)", r"button (\w+)", r"use (\w+)",
            r"go (\w+)", r"move (\w+)", r"navigate (\w+)"
        ]
        
        for pattern in button_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if match in ["up", "down", "left", "right", "a", "b", "start", "select"]:
                    return [match]
        
        return []
    
    def _parse_retry_delay(self, error_message: str, default_delay: float) -> float:
        """Parse retry delay from error message"""
        import re
        
        patterns = [
            r'retry[\s\-_]*after[\s\-_]*(\d+)[\s\-_]*seconds?',
            r'try[\s\-_]*again[\s\-_]*in[\s\-_]*(\d+)[\s\-_]*s',
            r'wait[\s\-_]*(\d+)[\s\-_]*seconds?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message.lower())
            if match:
                try:
                    return min(float(match.group(1)), 300.0)
                except (ValueError, IndexError):
                    continue
        
        # Exponential backoff with jitter
        jitter = random.uniform(0.8, 1.2)
        return min(default_delay * jitter, 60.0)

class MistralProvider(BaseLLMProvider):
    """Mistral AI API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
        
        # Initialize Mistral client (using new API)
        try:
            from mistralai import Mistral
            self.client = Mistral(api_key=self.api_key)
        except ImportError:
            raise ImportError("mistralai package required for Mistral provider. Install with: pip install mistralai")
    
    def get_available_models(self) -> Dict[str, ModelCapability]:
        """Get available Mistral models and their capabilities"""
        return {
            "pixtral-12b-2409": ModelCapability.VISION,
            "mistral-large-latest": ModelCapability.TEXT,
            "mistral-small-latest": ModelCapability.TEXT
        }
    
    def get_default_model(self, capability: ModelCapability) -> str:
        """Get default Mistral model for given capability"""
        if capability == ModelCapability.VISION:
            return "pixtral-12b-2409"
        else:
            return "mistral-large-latest"
    
    def call_api(self, request: LLMRequest) -> LLMResponse:
        """Make Mistral API call"""
        start_time = time.time()
        
        # Check circuit breaker
        if self._check_circuit_breaker():
            return LLMResponse(
                text="",
                button_presses=[],
                error="API circuit breaker is open",
                provider="mistral"
            )
        
        # Determine model
        available_models = self.get_available_models()
        
        if request.model_preference and request.model_preference in available_models:
            model_name = request.model_preference
        else:
            capability = ModelCapability.VISION if request.image_data else ModelCapability.TEXT
            model_name = self.get_default_model(capability)
        
        try:
            # Prepare messages
            if request.image_data and model_name == "pixtral-12b-2409":
                # Vision model with image
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": request.prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{request.image_data}"
                        }
                    ]
                }]
            else:
                # Text-only
                messages = [{"role": "user", "content": request.prompt}]
            
            # Make API call using new client format
            response = self.client.chat.complete(
                model=model_name,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Process response
            text = response.choices[0].message.content if response.choices else ""
            button_presses = self._parse_buttons_from_text(text)
            
            if not button_presses:
                button_presses = ["a"]  # Default fallback
            
            self._record_api_success()
            
            return LLMResponse(
                text=text,
                button_presses=button_presses,
                provider="mistral",
                model=model_name,
                response_time=time.time() - start_time,
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None
            )
            
        except Exception as e:
            self._record_api_failure()
            return LLMResponse(
                text="",
                button_presses=[],
                error=str(e),
                provider="mistral",
                model=model_name,
                response_time=time.time() - start_time
            )
    
    def _parse_buttons_from_text(self, text: str) -> List[str]:
        """Parse button commands from Mistral text response"""
        import re
        
        if not text:
            return []
        
        button_patterns = [
            r"press (\w+)", r"button (\w+)", r"use (\w+)",
            r"go (\w+)", r"move (\w+)", r"navigate (\w+)"
        ]
        
        for pattern in button_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if match in ["up", "down", "left", "right", "a", "b", "start", "select"]:
                    return [match]
        
        return []

class LLMAPIManager:
    """Main API manager that handles multiple providers and model selection"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM API Manager with configuration
        
        Args:
            config: Configuration dictionary. If None, loads from environment variables
        """
        self.config = config or self._load_config_from_env()
        self.providers = {}
        self.current_provider = None
        
        # Initialize providers
        self._init_providers()
        
        # Set default provider
        default_provider = self.config.get('default_provider', 'gemini')
        self.set_provider(default_provider)
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'default_provider': os.getenv('LLM_PROVIDER', 'gemini'),
            'gemini': {
                'api_key': os.getenv('GEMINI_API_KEY'),
                'circuit_breaker_reset_time': 300,
                'api_failure_threshold': 5
            },
            'mistral': {
                'api_key': os.getenv('MISTRAL_API_KEY'),
                'circuit_breaker_reset_time': 300,
                'api_failure_threshold': 3
            },
            'fallback_provider': os.getenv('FALLBACK_PROVIDER', 'gemini'),
            'auto_fallback': os.getenv('AUTO_FALLBACK', 'true').lower() == 'true'
        }
    
    def _init_providers(self):
        """Initialize available providers"""
        # Initialize Gemini if API key is available
        if self.config.get('gemini', {}).get('api_key'):
            try:
                self.providers['gemini'] = GeminiProvider(self.config['gemini'])
            except Exception as e:
                print(f"⚠️ Failed to initialize Gemini provider: {e}")
        
        # Initialize Mistral if API key is available
        if self.config.get('mistral', {}).get('api_key'):
            try:
                self.providers['mistral'] = MistralProvider(self.config['mistral'])
            except Exception as e:
                print(f"⚠️ Failed to initialize Mistral provider: {e}")
        
        if not self.providers:
            raise ValueError("No LLM providers could be initialized. Check your API keys.")
    
    def set_provider(self, provider_name: str) -> bool:
        """Set the current provider"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            return True
        return False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())
    
    def call(self, 
             prompt: str,
             image_data: Optional[str] = None,
             use_tools: bool = False,
             max_tokens: int = 1000,
             model_preference: Optional[str] = None,
             provider_preference: Optional[str] = None) -> LLMResponse:
        """
        Make unified LLM API call
        
        Args:
            prompt: Text prompt to send
            image_data: Base64 encoded image data (optional)
            use_tools: Whether to use function calling tools
            max_tokens: Maximum tokens for response
            model_preference: Specific model to use
            provider_preference: Specific provider to use
            
        Returns:
            LLMResponse with standardized format
        """
        # Determine provider to use
        provider_name = provider_preference or self.current_provider
        
        if provider_name not in self.providers:
            # Fallback to any available provider
            if self.providers:
                provider_name = list(self.providers.keys())[0]
            else:
                return LLMResponse(
                    text="",
                    button_presses=[],
                    error="No providers available"
                )
        
        # Create request
        request = LLMRequest(
            prompt=prompt,
            image_data=image_data,
            use_tools=use_tools,
            max_tokens=max_tokens,
            model_preference=model_preference
        )
        
        # Make API call
        provider = self.providers[provider_name]
        response = provider.call_api(request)
        
        # Handle auto-fallback if enabled and current call failed
        if (response.error and 
            self.config.get('auto_fallback', False) and 
            len(self.providers) > 1):
            
            fallback_provider = self.config.get('fallback_provider')
            if fallback_provider and fallback_provider != provider_name and fallback_provider in self.providers:
                print(f"🔄 Auto-fallback: {provider_name} → {fallback_provider}")
                fallback_request = request
                fallback_request.model_preference = None  # Use provider default
                response = self.providers[fallback_provider].call_api(fallback_request)
        
        return response
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                'circuit_breaker_open': provider.circuit_breaker_open,
                'api_failure_count': provider.api_failure_count,
                'rate_limited_models': list(provider.rate_limited_models),
                'available_models': list(provider.get_available_models().keys())
            }
        return status

# Global instance for easy access
_global_llm_manager = None

def get_llm_manager() -> LLMAPIManager:
    """Get global LLM manager instance"""
    global _global_llm_manager
    if _global_llm_manager is None:
        _global_llm_manager = LLMAPIManager()
    return _global_llm_manager

def call_llm(prompt: str, 
             image_data: Optional[str] = None,
             use_tools: bool = False,
             max_tokens: int = 1000,
             model: Optional[str] = None,
             provider: Optional[str] = None) -> LLMResponse:
    """
    Convenience function for making LLM calls
    
    Args:
        prompt: Text prompt to send
        image_data: Base64 encoded image data (optional)
        use_tools: Whether to use function calling tools
        max_tokens: Maximum tokens for response
        model: Specific model to use
        provider: Specific provider to use
        
    Returns:
        LLMResponse with standardized format
    """
    manager = get_llm_manager()
    return manager.call(
        prompt=prompt,
        image_data=image_data,
        use_tools=use_tools,
        max_tokens=max_tokens,
        model_preference=model,
        provider_preference=provider
    )

# Backwards compatibility functions
def send_gemini_request(prompt: str, model: str = "gemini-2.0-flash-exp") -> str:
    """Legacy compatibility function for gemini_api.py"""
    response = call_llm(prompt=prompt, model=model, provider="gemini")
    if response.error:
        raise Exception(f"Gemini API request failed: {response.error}")
    return response.text