"""
Tests for LLM configuration and backend support
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from llm_config import (
    LLMConfig, 
    LLMBackend, 
    create_llm_config, 
    get_available_backends,
    get_default_config,
    test_connection
)

class TestLLMConfig:
    """Test LLM configuration functionality"""
    
    def test_llm_backend_enum(self):
        """Test LLMBackend enum functionality"""
        assert LLMBackend.OPENAI.value == "openai"
        assert LLMBackend.OLLAMA.value == "ollama"
        assert LLMBackend.OPENROUTER.value == "openrouter"
        
        # Test from_string method
        assert LLMBackend.from_string("openai") == LLMBackend.OPENAI
        assert LLMBackend.from_string("OLLAMA") == LLMBackend.OLLAMA
        assert LLMBackend.from_string(" openrouter ") == LLMBackend.OPENROUTER
        
        with pytest.raises(ValueError):
            LLMBackend.from_string("invalid_backend")
    
    def test_llm_config_initialization(self):
        """Test LLMConfig initialization"""
        config = LLMConfig(
            backend="openai",
            api_key="test-key",
            model="gpt-4",
            temperature=0.8
        )
        
        assert config.backend == LLMBackend.OPENAI
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.temperature == 0.8
    
    def test_llm_config_environment_loading(self):
        """Test environment variable loading"""
        with patch.dict(os.environ, {
            'LLM_BACKEND': 'ollama',
            'OLLAMA_MODEL': 'llama2',
            'LLM_TEMPERATURE': '0.5'
        }):
            config = LLMConfig()
            assert config.backend == LLMBackend.OLLAMA
            assert config.model == "llama2"
            assert config.temperature == 0.5
    
    def test_openai_config_conversion(self):
        """Test conversion to OpenAI-compatible format"""
        config = LLMConfig(
            backend="openai",
            api_key="test-key",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
        openai_config = config.to_openai_config()
        
        assert openai_config['model'] == "gpt-4"
        assert openai_config['temperature'] == 0.7
        assert openai_config['max_tokens'] == 1000
        assert openai_config['api_key'] == "test-key"
    
    def test_client_params(self):
        """Test client parameter extraction"""
        config = LLMConfig(
            backend="ollama",
            base_url="http://localhost:11434/v1",
            api_key="test-key"
        )
        
        params = config.get_client_params()
        
        assert params['base_url'] == "http://localhost:11434/v1"
        assert params['api_key'] == "test-key"
    
    def test_validation(self):
        """Test configuration validation"""
        # OpenAI should require API key
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            LLMConfig(backend="openai", api_key=None)
        
        # Openrouter should require API key
        with pytest.raises(ValueError, match="Openrouter API key is required"):
            LLMConfig(backend="openrouter", api_key=None)
        
        # Ollama should work without API key
        config = LLMConfig(backend="ollama", api_key=None)
        assert config.backend == LLMBackend.OLLAMA

class TestLLMConfigFactory:
    """Test factory functions"""
    
    def test_create_llm_config(self):
        """Test LLM config factory function"""
        config = create_llm_config(
            backend="openai",
            api_key="test-key",
            model="gpt-3.5-turbo"
        )
        
        assert config.backend == LLMBackend.OPENAI
        assert config.api_key == "test-key"
        assert config.model == "gpt-3.5-turbo"
    
    def test_get_available_backends(self):
        """Test available backends listing"""
        backends = get_available_backends()
        
        assert "openai" in backends
        assert "ollama" in backends
        assert "openrouter" in backends
        assert len(backends) == 3
    
    def test_get_default_config(self):
        """Test default configuration retrieval"""
        openai_config = get_default_config("openai")
        assert openai_config['model'] == 'gpt-4'
        
        ollama_config = get_default_config(LLMBackend.OLLAMA)
        assert ollama_config['model'] == 'llama2'
        assert ollama_config['base_url'] == 'http://localhost:11434/v1'

class TestConnectionTesting:
    """Test connection testing functionality"""
    
    @patch('llm_config.OpenAI')
    def test_connection_success(self, mock_openai):
        """Test successful connection test"""
        # Mock successful OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock()
        
        config = LLMConfig(
            backend="openai",
            api_key="test-key",
            model="gpt-4"
        )
        
        result = test_connection(config)
        assert result is True
        
        # Verify client was created with correct parameters
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
    
    @patch('llm_config.OpenAI')
    def test_connection_failure(self, mock_openai):
        """Test failed connection test"""
        # Mock failed OpenAI client
        mock_openai.side_effect = Exception("Connection failed")
        
        config = LLMConfig(
            backend="openai",
            api_key="test-key",
            model="gpt-4"
        )
        
        result = test_connection(config)
        assert result is False

# Integration test (requires actual backends to be available)
class TestIntegration:
    """Integration tests for LLM backends"""
    
    def test_config_string_representation(self):
        """Test string representation of config"""
        config = LLMConfig(
            backend="ollama",
            model="llama2",
            base_url="http://localhost:11434/v1"
        )
        
        config_str = str(config)
        assert "ollama" in config_str
        assert "llama2" in config_str
        assert "localhost:11434" in config_str

if __name__ == "__main__":
    pytest.main([__file__])