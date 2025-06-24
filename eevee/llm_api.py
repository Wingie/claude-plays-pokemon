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

# Import debug logger at top level for clean logging
try:
    from evee_logger import get_comprehensive_logger
    debug_logger = get_comprehensive_logger()
except ImportError:
    debug_logger = None

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
        
        # Configure safety settings for gaming content (most permissive for Pokemon gameplay)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
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
            if debug_logger:
                debug_logger.log_debug('ERROR', f'Function declaration failed for Gemini: {e}')
            else:
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
        return "gemini-2.0-flash-exp"  # Test experimental model for safety differences
    
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
                        tools=[self.pokemon_tool],
                        safety_settings=self.safety_settings
                    )
                else:
                    response = model.generate_content(
                        content_parts,
                        generation_config=generation_config,
                        safety_settings=self.safety_settings
                    )
                

                result = self._process_gemini_response(response, request.use_tools)
                result.provider = "gemini"
                result.model = model_name
                result.response_time = time.time() - start_time
                
                # Log warning if response is empty
                if not result.text:
                    try:
                        from evee_logger import get_comprehensive_logger
                        debug_logger = get_comprehensive_logger()
                        if debug_logger:
                            debug_logger.log_debug('WARNING', f'Gemini returned empty response for model {model_name}')
                        else:
                            print(f"⚠️ Gemini returned empty response for model {model_name}")
                    except ImportError:
                        print(f"⚠️ Gemini returned empty response for model {model_name}")
                    if hasattr(response, 'prompt_feedback'):
                        if debug_logger:
                            debug_logger.log_debug('INFO', f'Prompt feedback: {response.prompt_feedback}')
                        else:
                            print(f"   Prompt feedback: {response.prompt_feedback}")
                    if hasattr(response, 'candidates') and not response.candidates:
                        if debug_logger:
                            debug_logger.log_debug('INFO', 'No candidates in response')
                        else:
                            print(f"   No candidates in response")
                
                self._record_api_success()
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Log detailed error information for each retry attempt
                from evee_logger import get_comprehensive_logger
                logger = get_comprehensive_logger()
                
                error_data = {
                    'attempt': f"{attempt + 1}/{max_retries}",
                    'model': model_name,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'full_exception': repr(e)
                }
                
                if hasattr(e, 'details'):
                    error_data['error_details'] = str(e.details)
                if hasattr(e, 'reason'):
                    error_data['error_reason'] = str(e.reason)
                
                if logger:
                    logger.log_gemini_debug(
                        call_type=f"RETRY_ATTEMPT_{attempt + 1}",
                        request_data={'model': model_name, 'prompt_length': len(request.prompt)},
                        response_data={},
                        error=f"{type(e).__name__}: {str(e)}"
                    )
                
                # Log to debug system - fail fast, no excessive error handling
                if debug_logger:
                    debug_logger.log_debug('ERROR', f'GEMINI API ERROR - Attempt {attempt + 1}/{max_retries}')
                    debug_logger.log_debug('ERROR', f'Model: {model_name}, Error: {type(e).__name__}: {str(e)}')
                    if hasattr(e, 'details'):
                        debug_logger.log_debug('ERROR', f'Error Details: {e.details}')
                    if hasattr(e, 'reason'):
                        debug_logger.log_debug('ERROR', f'Error Reason: {e.reason}')
                
                # Handle rate limiting with model switching
                if any(keyword in error_msg for keyword in ["429", "rate limit", "quota"]):
                    if debug_logger:
                        debug_logger.log_debug('WARNING', f'RATE LIMIT DETECTED - Adding {model_name} to rate limited models')
                    self.rate_limited_models.add(model_name)
                    
                    # Try to switch to different model
                    available = [m for m in available_models.keys() if m not in self.rate_limited_models]
                    if available:
                        if debug_logger:
                            debug_logger.log_debug('INFO', f'SWITCHING MODEL: {model_name} → {available[0]}')
                        model_name = available[0]
                        continue
                    else:
                        # All models rate limited, wait
                        retry_delay = self._parse_retry_delay(str(e), base_delay * (2 ** attempt))
                        if debug_logger:
                            debug_logger.log_debug('WARNING', f'ALL MODELS RATE LIMITED - Waiting {retry_delay}s before retry')
                        time.sleep(retry_delay)
                        continue
                
                # Handle other retryable errors
                elif any(keyword in error_msg for keyword in ["timeout", "connection", "network"]):
                    if debug_logger:
                        debug_logger.log_debug('WARNING', 'NETWORK/TIMEOUT ERROR - Retryable')
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)
                        if debug_logger:
                            debug_logger.log_debug('INFO', f'Waiting {retry_delay}s before retry {attempt + 2}')
                        time.sleep(retry_delay)
                        continue
                
                # Non-retryable errors or authentication issues
                else:
                    if debug_logger:
                        debug_logger.log_debug('ERROR', f'NON-RETRYABLE ERROR - Error type: {type(e).__name__}')
                        debug_logger.log_debug('ERROR', 'Likely cause: API key, model availability, or authentication issue')
                
                # Final attempt or non-retryable error
                if attempt == max_retries - 1:
                    if debug_logger:
                        debug_logger.log_debug('ERROR', 'FINAL ATTEMPT FAILED - Recording API failure and returning error response')
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
        if debug_logger:
            debug_logger.log_debug('ERROR', 'UNEXPECTED: Reached end of retry loop without returning - This should not happen')
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
                        # Provide meaningful text when function calling succeeds
                        if not result.text:
                            result.text = f"Pressing {button.upper()} button for Pokemon game control"
        else:
            # Handle text-only response
            # Try different ways to extract text from Gemini response
            try:
                if hasattr(response, 'text') and response.text:
                    result.text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # Try to extract text from candidates even if safety-blocked
                    candidate = response.candidates[0]
                    
                    # Check if content exists despite safety blocking
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    result.text = part.text
                                    break
                    
                    # If no content but candidate exists, check for finish_reason and safety ratings
                    if not result.text and hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        print(f"⚠️ Gemini response blocked with finish_reason: {finish_reason}")
                        
                        # Extract safety ratings for detailed blocking information
                        if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                            print(f"   🛡️ SAFETY RATINGS:")
                            for rating in candidate.safety_ratings:
                                category = getattr(rating, 'category', 'UNKNOWN')
                                probability = getattr(rating, 'probability', 'UNKNOWN')
                                blocked = getattr(rating, 'blocked', False)
                                print(f"     {category}: {probability} (blocked: {blocked})")
                        
                        # Check for prompt feedback (input blocking)
                        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                            feedback = response.prompt_feedback
                            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                                print(f"   🚫 PROMPT BLOCKED: {feedback.block_reason}")
                            if hasattr(feedback, 'safety_ratings') and feedback.safety_ratings:
                                print(f"   📝 PROMPT SAFETY RATINGS:")
                                for rating in feedback.safety_ratings:
                                    category = getattr(rating, 'category', 'UNKNOWN')
                                    probability = getattr(rating, 'probability', 'UNKNOWN')
                                    print(f"     {category}: {probability}")
                        
                        # Try to get any partial content that might exist
                        if hasattr(candidate, 'content') and candidate.content:
                            print(f"   Content object exists: {type(candidate.content)}")
                            if hasattr(candidate.content, 'parts'):
                                print(f"   Parts exist: {len(candidate.content.parts) if candidate.content.parts else 0}")
            except Exception as text_extraction_error:
                print(f"⚠️ Error extracting text from Gemini response: {text_extraction_error}")
            
            # If still no text, set empty string
            if not result.text:
                result.text = ""
        
        # Parse buttons from text if no function calls
        if result.text and not result.button_presses:
            result.button_presses = self._parse_buttons_from_text(result.text)
        
        # Default fallback
        if not result.button_presses:
            result.button_presses = ["b"]
        
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
        
        # Initialize function calling for Mistral (JSON schema format)
        self.pokemon_function_schema = {
            "type": "function",
            "function": {
                "name": "pokemon_controller",
                "description": "Control Pokemon game with button presses",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "buttons": {
                            "type": "string",
                            "description": "Single button press: up, down, left, right, a, b, start, select"
                        }
                    },
                    "required": ["buttons"]
                }
            }
        }
    
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
            
            # Make API call using new client format with optional function calling
            if request.use_tools:
                response = self.client.chat.complete(
                    model=model_name,
                    messages=messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    tools=[self.pokemon_function_schema]
                )
            else:
                response = self.client.chat.complete(
                    model=model_name,
                    messages=messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            
            # Process response
            result = self._process_mistral_response(response, request.use_tools)
            result.provider = "mistral"
            result.model = model_name
            result.response_time = time.time() - start_time
            
            if hasattr(response, 'usage') and response.usage:
                result.tokens_used = response.usage.total_tokens
            
            self._record_api_success()
            return result
            
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
    
    def _process_mistral_response(self, response, use_tools: bool) -> LLMResponse:
        """Process Mistral API response into standardized format"""
        result = LLMResponse(text="", button_presses=[])
        
        if response.choices and response.choices[0].message:
            message = response.choices[0].message
            
            # Handle function calling response
            if use_tools and hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if (hasattr(tool_call, 'function') and 
                        tool_call.function.name == "pokemon_controller"):
                        try:
                            import json
                            args = json.loads(tool_call.function.arguments)
                            if "buttons" in args:
                                button = args["buttons"].lower().strip()
                                result.button_presses.append(button)
                                # Provide meaningful text when function calling succeeds
                                if not result.text:
                                    result.text = f"Pressing {button.upper()} button for Pokemon game control"
                        except (json.JSONDecodeError, KeyError):
                            pass
            
            # Get text content
            if hasattr(message, 'content') and message.content:
                result.text = message.content
        
        # Parse buttons from text if no function calls
        if result.text and not result.button_presses:
            result.button_presses = self._parse_buttons_from_text(result.text)
        
        # Default fallback
        if not result.button_presses:
            result.button_presses = ["b"]
        
        return result
    
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
        llm_provider = os.getenv('LLM_PROVIDER', 'gemini')
        
        # Handle hybrid mode: use strategic provider as default
        if llm_provider == 'hybrid':
            default_provider = os.getenv('STRATEGIC_PROVIDER', 'mistral')
        else:
            default_provider = llm_provider
            
        return {
            'default_provider': default_provider,
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
            # Fallback provider options removed per user request
            'hybrid_mode': llm_provider == 'hybrid'
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
        
        # Fallback provider functionality removed per user request
        # System will fail fast instead of falling back to different providers
        
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