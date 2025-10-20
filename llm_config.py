"""
LLM Configuration Management for Healthcare Simulation

This module provides configuration and initialization for different LLM backends:
- OpenAI: Default OpenAI API
- Ollama: Local Ollama instance
- Openrouter: Openrouter API gateway

Supports environment variables and programmatic configuration.
"""

import os
from typing import Dict, Any, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LLMBackend(Enum):
    """Supported LLM backends"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    
    @classmethod
    def from_string(cls, backend: str) -> 'LLMBackend':
        """Convert string to LLMBackend enum"""
        backend = backend.lower().strip()
        for item in cls:
            if item.value == backend:
                return item
        raise ValueError(f"Unsupported backend: {backend}. Supported: {[b.value for b in cls]}")

class LLMConfig:
    """Configuration class for LLM backends"""
    
    def __init__(
        self,
        backend: Union[LLMBackend, str] = LLMBackend.OPENAI,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize LLM configuration
        
        Args:
            backend: LLM backend to use
            api_key: API key for the service
            base_url: Base URL for API endpoints
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional backend-specific parameters
        """
        if isinstance(backend, str):
            backend = LLMBackend.from_string(backend)
        
        self.backend = backend
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs
        
        # Auto-detect configuration from environment if not provided
        self._load_from_environment()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        
        # Backend selection
        if not hasattr(self, 'backend') or self.backend is None:
            backend_env = os.getenv('LLM_BACKEND', 'openai')
            self.backend = LLMBackend.from_string(backend_env)
        
        # API keys - try specific then generic
        if not self.api_key:
            if self.backend == LLMBackend.OPENAI:
                self.api_key = os.getenv('OPENAI_API_KEY')
            elif self.backend == LLMBackend.OPENROUTER:
                self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
            elif self.backend == LLMBackend.OLLAMA:
                # Ollama typically doesn't need API key for local instances
                self.api_key = os.getenv('OLLAMA_API_KEY')
            elif self.backend == LLMBackend.DEEPSEEK:
                self.api_key = os.getenv('DEEPSEEK_API_KEY')
        
        # Base URLs
        if not self.base_url:
            if self.backend == LLMBackend.OPENAI:
                self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
            elif self.backend == LLMBackend.OPENROUTER:
                self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
            elif self.backend == LLMBackend.OLLAMA:
                self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
            elif self.backend == LLMBackend.DEEPSEEK:
                self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        # Model names
        if not self.model:
            if self.backend == LLMBackend.OPENAI:
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
            elif self.backend == LLMBackend.OPENROUTER:
                self.model = os.getenv('OPENROUTER_MODEL', 'z-ai/glm-4.6')
            elif self.backend == LLMBackend.OLLAMA:
                self.model = os.getenv('OLLAMA_MODEL', 'hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M')
            elif self.backend == LLMBackend.DEEPSEEK:
                self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        # Temperature
        temp_env = os.getenv('LLM_TEMPERATURE')
        if temp_env and self.temperature == 0.7:  # Only override if using default
            try:
                self.temperature = float(temp_env)
            except ValueError:
                logger.warning(f"Invalid temperature value in environment: {temp_env}")
        
        # Max tokens
        max_tokens_env = os.getenv('LLM_MAX_TOKENS')
        if max_tokens_env and not self.max_tokens:
            try:
                self.max_tokens = int(max_tokens_env)
            except ValueError:
                logger.warning(f"Invalid max_tokens value in environment: {max_tokens_env}")
    
    def _validate_config(self):
        """Validate the configuration"""
        if self.backend == LLMBackend.OPENAI:
            if not self.api_key:
                raise ValueError("OpenAI API key is required")
        
        elif self.backend == LLMBackend.OPENROUTER:
            if not self.api_key:
                raise ValueError("Openrouter API key is required")
        
        elif self.backend == LLMBackend.OLLAMA:
            # Ollama validation - check if model name is reasonable
            if not self.model:
                logger.warning("No Ollama model specified, using default: hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M")
                self.model = "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M"
            # Ollama typically doesn't require API key for local/remote servers
            if not self.api_key:
                self.api_key = "ollama"  # Placeholder for Ollama compatibility
        
        elif self.backend == LLMBackend.DEEPSEEK:
            if not self.api_key:
                raise ValueError("DeepSeek API key is required")
            if not self.model:
                logger.warning("No DeepSeek model specified, using default: deepseek-chat")
                self.model = "deepseek-chat"
    
    def to_openai_config(self) -> Dict[str, Any]:
        """
        Convert configuration to OpenAI-compatible format
        This works for OpenAI, Openrouter, and Ollama (with OpenAI-compatible API)
        """
        config = {
            'model': self.model,
            'temperature': self.temperature,
        }
        
        if self.max_tokens:
            config['max_tokens'] = self.max_tokens
        
        # Add base URL and API key for client initialization
        if self.base_url:
            config['base_url'] = self.base_url
        
        if self.api_key:
            config['api_key'] = self.api_key
        
        # Add extra parameters
        config.update(self.extra_params)
        
        return config
    
    def get_client_params(self) -> Dict[str, Any]:
        """Get parameters for initializing the OpenAI client"""
        params = {}
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        if self.base_url:
            params['base_url'] = self.base_url
        
        return params
    
    def __str__(self) -> str:
        return f"LLMConfig(backend={self.backend.value}, model={self.model}, base_url={self.base_url})"

def create_llm_config(
    backend: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMConfig:
    """
    Factory function to create LLM configuration
    
    Args:
        backend: Backend name ('openai', 'ollama', 'openrouter')
        api_key: API key for the service
        model: Model name to use
        **kwargs: Additional configuration parameters
    
    Returns:
        LLMConfig: Configured LLM configuration object
    """
    
    # Use environment variable if backend not specified
    if not backend:
        backend = os.getenv('LLM_BACKEND', 'openai')
    
    return LLMConfig(
        backend=backend,
        api_key=api_key,
        model=model,
        **kwargs
    )

def get_available_backends() -> list[str]:
    """Get list of available backend names"""
    return [backend.value for backend in LLMBackend]

def test_connection(config: LLMConfig) -> bool:
    """
    Test connection to the configured LLM backend
    
    Args:
        config: LLM configuration to test
    
    Returns:
        bool: True if connection successful
    """
    try:
        # Import OpenAI client here to avoid dependency issues
        from openai import OpenAI
        
        client_params = config.get_client_params()
        client = OpenAI(**client_params)
        
        # Try a simple completion to test the connection
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed for {config.backend.value}: {str(e)}")
        return False

# Default configurations for each backend
DEFAULT_CONFIGS = {
    LLMBackend.OPENAI: {
        'model': 'gpt-4',
        'temperature': 0.7,
        'max_tokens': 2000
    },
    LLMBackend.OLLAMA: {
        'model': 'hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M',
        'temperature': 0.7,
        'max_tokens': 2000,
        'base_url': 'http://localhost:11434/v1'
    },
    LLMBackend.OPENROUTER: {
        'model': 'z-ai/glm-4.6',
        'temperature': 0.7,
        'max_tokens': 2000,
        'base_url': 'https://openrouter.ai/api/v1',
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    },
    LLMBackend.DEEPSEEK: {
        'model': 'deepseek-chat',
        'temperature': 0.7,
        'max_tokens': 2000,
        'base_url': 'https://api.deepseek.com'
    }
}

def get_default_config(backend: Union[LLMBackend, str]) -> Dict[str, Any]:
    """Get default configuration for a backend"""
    if isinstance(backend, str):
        backend = LLMBackend.from_string(backend)
    
    return DEFAULT_CONFIGS.get(backend, {})