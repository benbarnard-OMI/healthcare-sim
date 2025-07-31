"""
Test utilities for healthcare simulation tests.
"""
import os
from unittest.mock import patch
from llm_config import LLMConfig, LLMBackend


def create_mock_llm_config():
    """Create a mock LLM configuration for testing."""
    return LLMConfig(
        backend=LLMBackend.OPENAI,
        api_key="test_api_key",
        model="gpt-3.5-turbo",
        temperature=0.7
    )


def mock_env_with_api_key():
    """Context manager to mock environment with API key."""
    return patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})


def mock_env_no_api_key():
    """Context manager to mock environment without API key."""
    return patch.dict(os.environ, {}, clear=True)