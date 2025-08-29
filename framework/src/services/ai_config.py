"""
AI Configuration Module for GPT-5 Integration
Provides centralized configuration, validation, and optimization for AI services.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AIOperationType(Enum):
    """Types of AI operations with different configuration requirements."""
    BROWSER_AUTOMATION = "browser_automation"
    CONTENT_GENERATION = "content_generation"
    PROFILE_ANALYSIS = "profile_analysis"
    SESSION_MANAGEMENT = "session_management"
    ERROR_RECOVERY = "error_recovery"
    DEBUG_ANALYSIS = "debug_analysis"


@dataclass
class GPT5Config:
    """GPT-5 specific configuration parameters."""
    model: str = "gpt-5"
    temperature: float = 0.3
    max_tokens: int = 1000
    timeout: int = 60
    retry_attempts: int = 3
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    top_p: float = 1.0
    response_format: Optional[Dict[str, str]] = None


class AIConfigManager:
    """Centralized AI configuration and validation manager."""
    
    def __init__(self):
        self.api_key = None
        self.model_configs = {}
        self._initialize_configs()
        self._validate_environment()
    
    def _initialize_configs(self):
        """Initialize optimized configurations for different AI operations."""
        
        # Browser Automation: Fast, precise responses
        self.model_configs[AIOperationType.BROWSER_AUTOMATION] = GPT5Config(
            model="gpt-5",
            temperature=0.1,
            max_tokens=500,
            timeout=45,
            retry_attempts=2,
            response_format={"type": "json_object"}
        )
        
        # Content Generation: Creative but controlled
        self.model_configs[AIOperationType.CONTENT_GENERATION] = GPT5Config(
            model="gpt-5",
            temperature=0.3,
            max_tokens=800,
            timeout=60,
            retry_attempts=3,
            presence_penalty=0.1
        )
        
        # Profile Analysis: Analytical and detailed
        self.model_configs[AIOperationType.PROFILE_ANALYSIS] = GPT5Config(
            model="gpt-5",
            temperature=0.2,
            max_tokens=1200,
            timeout=75,
            retry_attempts=3,
            response_format={"type": "json_object"}
        )
        
        # Session Management: Quick decisions
        self.model_configs[AIOperationType.SESSION_MANAGEMENT] = GPT5Config(
            model="gpt-5",
            temperature=0.1,
            max_tokens=300,
            timeout=30,
            retry_attempts=2
        )
        
        # Error Recovery: Conservative and reliable
        self.model_configs[AIOperationType.ERROR_RECOVERY] = GPT5Config(
            model="gpt-5",
            temperature=0.1,
            max_tokens=400,
            timeout=45,
            retry_attempts=3,
            response_format={"type": "json_object"}
        )
        
        # Debug Analysis: Detailed investigation
        self.model_configs[AIOperationType.DEBUG_ANALYSIS] = GPT5Config(
            model="gpt-5",
            temperature=0.2,
            max_tokens=1500,
            timeout=90,
            retry_attempts=2
        )
    
    def _validate_environment(self):
        """Validate environment variables and API key configuration."""
        
        # Check for OpenAI API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            raise ValueError("OpenAI API key is required for AI operations")
        
        # Validate API key format
        if not self.api_key.startswith(('sk-', 'sk-proj-')):
            logger.warning("OpenAI API key format appears invalid")
        
        # Log configuration status
        logger.info("AI Configuration Manager initialized successfully")
        logger.info(f"Using model: {self.get_config(AIOperationType.BROWSER_AUTOMATION).model}")
        logger.info(f"API key configured: {'***' + self.api_key[-8:] if len(self.api_key) > 8 else '***'}")
    
    def get_config(self, operation_type: AIOperationType) -> GPT5Config:
        """Get optimized configuration for specific AI operation type."""
        return self.model_configs.get(operation_type, self.model_configs[AIOperationType.BROWSER_AUTOMATION])
    
    def get_openai_params(self, operation_type: AIOperationType, **overrides) -> Dict[str, Any]:
        """Get OpenAI API parameters for specific operation type."""
        config = self.get_config(operation_type)
        
        params = {
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "presence_penalty": config.presence_penalty,
            "frequency_penalty": config.frequency_penalty,
            "top_p": config.top_p,
            "timeout": config.timeout
        }
        
        # Add response format if specified
        if config.response_format:
            params["response_format"] = config.response_format
        
        # Apply any overrides
        params.update(overrides)
        
        return params
    
    def get_retry_config(self, operation_type: AIOperationType) -> Dict[str, Any]:
        """Get retry configuration for specific operation type."""
        config = self.get_config(operation_type)
        return {
            "max_retries": config.retry_attempts,
            "exponential_base": 2,
            "jitter": True,
            "max_delay": 60
        }
    
    def validate_api_key_for_stagehand(self) -> Dict[str, str]:
        """Get validated headers for Stagehand server communication."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        return {
            'x-model-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get GPT-5 model capabilities and limitations."""
        return {
            "context_window": 128000,  # GPT-5 context window
            "max_output_tokens": 4096,
            "supports_json_mode": True,
            "supports_function_calling": True,
            "supports_vision": True,
            "rate_limits": {
                "requests_per_minute": 500,
                "tokens_per_minute": 150000
            }
        }
    
    def log_usage_stats(self, operation_type: AIOperationType, tokens_used: int, duration: float):
        """Log AI operation usage statistics."""
        logger.info(f"AI Operation: {operation_type.value} | Tokens: {tokens_used} | Duration: {duration:.2f}s")


# Global instance
ai_config = AIConfigManager()


class StagehandClient:
    """Enhanced Stagehand client with comprehensive API key validation."""
    
    def __init__(self, server_url: str = "http://localhost:8081"):
        self.server_url = server_url
        self.ai_config = ai_config
        self._validate_initialization()
    
    def _validate_initialization(self):
        """Validate all required configurations for Stagehand operations."""
        
        # Validate OpenAI API key
        if not self.ai_config.api_key:
            raise ValueError("OpenAI API key not configured - cannot initialize Stagehand client")
        
        # Validate Browserbase credentials with enhanced error handling and fallback loading
        bb_api_key = os.getenv('BROWSERBASE_API_KEY')
        bb_project_id = os.getenv('BROWSERBASE_PROJECT_ID')
        
        # If environment variables are missing, try to reload from .env file
        if not bb_api_key or not bb_project_id:
            logger.warning("Browserbase environment variables missing, attempting to reload .env file")
            
            # Try to find and reload .env file
            from dotenv import load_dotenv
            possible_env_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(os.getcwd()), '.env'),
                os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), '.env'),
                '/home/chorizo/projects/linkedin-research-suite/.env'  # Absolute fallback
            ]
            
            for env_path in possible_env_paths:
                if os.path.exists(env_path):
                    logger.info(f"Found .env file at: {env_path}")
                    load_dotenv(env_path, override=True)
                    bb_api_key = os.getenv('BROWSERBASE_API_KEY')
                    bb_project_id = os.getenv('BROWSERBASE_PROJECT_ID')
                    if bb_api_key and bb_project_id:
                        logger.info("Successfully reloaded Browserbase credentials from .env file")
                        break
                    else:
                        logger.warning(f"Loaded .env from {env_path} but variables still missing")
        
        # Enhanced debugging for missing environment variables
        if not bb_api_key:
            logger.error("BROWSERBASE_API_KEY environment variable is missing")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Available env vars starting with BROWSERBASE: {[k for k in os.environ.keys() if k.startswith('BROWSERBASE')]}")
            raise ValueError("BROWSERBASE_API_KEY environment variable is required")
        if not bb_project_id:
            logger.error("BROWSERBASE_PROJECT_ID environment variable is missing")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Available env vars starting with BROWSERBASE: {[k for k in os.environ.keys() if k.startswith('BROWSERBASE')]}")
            raise ValueError("BROWSERBASE_PROJECT_ID environment variable is required")
        
        # Store credentials for reuse to avoid repeated os.getenv calls
        self._bb_api_key = bb_api_key
        self._bb_project_id = bb_project_id
        
        # Log successful validation
        logger.info("StagehandClient initialized with validated credentials")
        logger.info(f"Server URL: {self.server_url}")
        logger.info(f"OpenAI API key: {'***' + self.ai_config.api_key[-8:]}")
        logger.info(f"Browserbase project: {bb_project_id}")
    
    def get_session_headers(self) -> Dict[str, str]:
        """Get properly formatted headers for session creation."""
        # Use stored credentials that were validated during initialization
        bb_api_key = self._bb_api_key
        bb_project_id = self._bb_project_id
        
        # Debug logging
        logger.info(f"StagehandClient headers - API key: {'***' + bb_api_key[-8:] if bb_api_key else 'None'}")
        logger.info(f"StagehandClient headers - Project ID: {bb_project_id}")
        
        headers = {
            'x-bb-api-key': bb_api_key,
            'x-bb-project-id': bb_project_id,
            'x-model-api-key': self.ai_config.api_key,
            'Content-Type': 'application/json'
        }
        
        # Log final headers (sanitized)
        sanitized_headers = {k: ('***' + v[-8:] if k.endswith('api-key') and v else v) for k, v in headers.items()}
        logger.info(f"Final headers for Stagehand: {sanitized_headers}")
        
        return headers
    
    def get_session_config(self, operation_type: AIOperationType = AIOperationType.BROWSER_AUTOMATION) -> Dict[str, Any]:
        """Get session configuration optimized for specific operation type."""
        config = self.ai_config.get_config(operation_type)
        
        return {
            'env': 'BROWSERBASE',
            'headless': True,
            'debugDom': False,
            'modelName': config.model,
            'timeout': config.timeout * 1000,  # Convert to milliseconds
            'retryAttempts': config.retry_attempts
        }


def get_ai_config() -> AIConfigManager:
    """Get the global AI configuration manager instance."""
    return ai_config


def get_stagehand_client() -> StagehandClient:
    """Get a validated Stagehand client instance."""
    return StagehandClient()
