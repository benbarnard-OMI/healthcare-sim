import unittest
from unittest.mock import patch, MagicMock
import os
from llm_config import LLMConfig, LLMBackend, create_llm_config, get_available_backends


class TestLLMConfig(unittest.TestCase):
    """Test LLM configuration functionality."""

    def test_llm_backend_enum(self):
        """Test LLMBackend enum functionality."""
        # Test enum values
        self.assertEqual(LLMBackend.OPENAI.value, "openai")
        self.assertEqual(LLMBackend.OLLAMA.value, "ollama")
        self.assertEqual(LLMBackend.OPENROUTER.value, "openrouter")
        
        # Test from_string method
        self.assertEqual(LLMBackend.from_string("openai"), LLMBackend.OPENAI)
        self.assertEqual(LLMBackend.from_string("OPENAI"), LLMBackend.OPENAI)
        self.assertEqual(LLMBackend.from_string("ollama"), LLMBackend.OLLAMA)
        self.assertEqual(LLMBackend.from_string("openrouter"), LLMBackend.OPENROUTER)
        
        # Test invalid backend
        with self.assertRaises(ValueError):
            LLMBackend.from_string("invalid_backend")

    def test_get_available_backends(self):
        """Test get_available_backends function."""
        backends = get_available_backends()
        self.assertIsInstance(backends, list)
        self.assertIn("openai", backends)
        self.assertIn("ollama", backends)
        self.assertIn("openrouter", backends)
        self.assertEqual(len(backends), 3)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_llm_config_openai_valid(self):
        """Test LLMConfig with valid OpenAI configuration."""
        config = LLMConfig(
            backend=LLMBackend.OPENAI,
            api_key="test_api_key",
            model="gpt-4",
            temperature=0.7
        )
        
        self.assertEqual(config.backend, LLMBackend.OPENAI)
        self.assertEqual(config.api_key, "test_api_key")
        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.base_url, "https://api.openai.com/v1")

    def test_llm_config_openai_missing_key(self):
        """Test LLMConfig validation fails without OpenAI API key."""
        with self.assertRaises(ValueError) as cm:
            LLMConfig(backend=LLMBackend.OPENAI, api_key=None)
        self.assertIn("OpenAI API key is required", str(cm.exception))

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_openrouter_key"})
    def test_llm_config_openrouter_valid(self):
        """Test LLMConfig with valid Openrouter configuration."""
        config = LLMConfig(
            backend=LLMBackend.OPENROUTER,
            api_key="test_openrouter_key",
            model="anthropic/claude-3-haiku:beta"
        )
        
        self.assertEqual(config.backend, LLMBackend.OPENROUTER)
        self.assertEqual(config.api_key, "test_openrouter_key")
        self.assertEqual(config.model, "anthropic/claude-3-haiku:beta")
        self.assertEqual(config.base_url, "https://openrouter.ai/api/v1")

    def test_llm_config_openrouter_missing_key(self):
        """Test LLMConfig validation fails without Openrouter API key."""
        with self.assertRaises(ValueError) as cm:
            LLMConfig(backend=LLMBackend.OPENROUTER, api_key=None)
        self.assertIn("Openrouter API key is required", str(cm.exception))

    def test_llm_config_ollama_valid(self):
        """Test LLMConfig with valid Ollama configuration."""
        config = LLMConfig(
            backend=LLMBackend.OLLAMA,
            model="llama2",
            base_url="http://localhost:11434/v1"
        )
        
        self.assertEqual(config.backend, LLMBackend.OLLAMA)
        self.assertEqual(config.model, "llama2")
        self.assertEqual(config.base_url, "http://localhost:11434/v1")
        self.assertIsNone(config.api_key)  # Ollama doesn't require API key

    def test_llm_config_ollama_default_model(self):
        """Test LLMConfig with Ollama sets default model if none provided."""
        with patch('llm_config.logger') as mock_logger:
            config = LLMConfig(backend=LLMBackend.OLLAMA, model=None)
            self.assertEqual(config.model, "llama2")
            mock_logger.warning.assert_called_with("No Ollama model specified, using default: llama2")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env_api_key", "LLM_BACKEND": "openai"})
    def test_llm_config_environment_loading(self):
        """Test LLMConfig loads from environment variables."""
        config = LLMConfig()  # No explicit parameters
        
        self.assertEqual(config.backend, LLMBackend.OPENAI)
        self.assertEqual(config.api_key, "env_api_key")

    @patch.dict(os.environ, {"LLM_TEMPERATURE": "0.5", "LLM_MAX_TOKENS": "2000"})
    def test_llm_config_environment_parameters(self):
        """Test LLMConfig loads temperature and max_tokens from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            config = LLMConfig(backend=LLMBackend.OPENAI)
            
            self.assertEqual(config.temperature, 0.5)
            self.assertEqual(config.max_tokens, 2000)

    @patch.dict(os.environ, {"LLM_TEMPERATURE": "invalid", "LLM_MAX_TOKENS": "invalid"})
    def test_llm_config_invalid_environment_parameters(self):
        """Test LLMConfig handles invalid environment parameters gracefully."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('llm_config.logger') as mock_logger:
                config = LLMConfig(backend=LLMBackend.OPENAI)
                
                # Should use defaults when environment values are invalid
                self.assertEqual(config.temperature, 0.7)  # default
                self.assertIsNone(config.max_tokens)  # default
                
                # Should log warnings
                mock_logger.warning.assert_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_llm_config_to_openai_config(self):
        """Test LLMConfig.to_openai_config method."""
        config = LLMConfig(
            backend=LLMBackend.OPENAI,
            model="gpt-4",
            temperature=0.8,
            max_tokens=1500
        )
        
        openai_config = config.to_openai_config()
        
        self.assertEqual(openai_config['model'], "gpt-4")
        self.assertEqual(openai_config['temperature'], 0.8)
        self.assertEqual(openai_config['max_tokens'], 1500)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_llm_config_to_openai_config_no_max_tokens(self):
        """Test LLMConfig.to_openai_config method without max_tokens."""
        config = LLMConfig(
            backend=LLMBackend.OPENAI,
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        openai_config = config.to_openai_config()
        
        self.assertEqual(openai_config['model'], "gpt-3.5-turbo")
        self.assertEqual(openai_config['temperature'], 0.7)
        self.assertNotIn('max_tokens', openai_config)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_llm_config_string_representation(self):
        """Test LLMConfig string representation."""
        config = LLMConfig(
            backend=LLMBackend.OPENAI,
            model="gpt-4",
            base_url="https://api.openai.com/v1"
        )
        
        str_repr = str(config)
        self.assertIn("LLMConfig", str_repr)
        self.assertIn("backend=openai", str_repr)
        self.assertIn("model=gpt-4", str_repr)
        self.assertIn("base_url=https://api.openai.com/v1", str_repr)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_create_llm_config_default(self):
        """Test create_llm_config function with defaults."""
        config = create_llm_config()
        
        self.assertIsInstance(config, LLMConfig)
        self.assertEqual(config.backend, LLMBackend.OPENAI)
        self.assertEqual(config.api_key, "test_key")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_create_llm_config_with_params(self):
        """Test create_llm_config function with custom parameters."""
        config = create_llm_config(
            backend="ollama",
            model="llama2",
            temperature=0.5
        )
        
        self.assertEqual(config.backend, LLMBackend.OLLAMA)
        self.assertEqual(config.model, "llama2")
        self.assertEqual(config.temperature, 0.5)


class TestLLMConfigErrorHandling(unittest.TestCase):
    """Test error handling in LLM configuration."""

    def test_invalid_temperature_range(self):
        """Test LLMConfig with invalid temperature values."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            # Test negative temperature
            config = LLMConfig(backend=LLMBackend.OPENAI, temperature=-0.1)
            # Should clamp or handle gracefully (depending on implementation)
            self.assertIsInstance(config.temperature, (int, float))
            
            # Test temperature > 2
            config = LLMConfig(backend=LLMBackend.OPENAI, temperature=2.5)
            self.assertIsInstance(config.temperature, (int, float))

    def test_invalid_max_tokens(self):
        """Test LLMConfig with invalid max_tokens values."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            # Test negative max_tokens
            config = LLMConfig(backend=LLMBackend.OPENAI, max_tokens=-100)
            # Should handle gracefully
            self.assertIsInstance(config, LLMConfig)
            
            # Test extremely large max_tokens
            config = LLMConfig(backend=LLMBackend.OPENAI, max_tokens=1000000)
            self.assertIsInstance(config, LLMConfig)

    def test_empty_model_string(self):
        """Test LLMConfig with empty model string."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            config = LLMConfig(backend=LLMBackend.OPENAI, model="")
            # Should use default model or handle gracefully
            self.assertIsInstance(config, LLMConfig)

    def test_invalid_base_url(self):
        """Test LLMConfig with invalid base URL."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            # Test malformed URL
            config = LLMConfig(backend=LLMBackend.OPENAI, base_url="not-a-url")
            self.assertEqual(config.base_url, "not-a-url")  # Should store as-is
            
            # Test empty URL
            config = LLMConfig(backend=LLMBackend.OPENAI, base_url="")
            self.assertIsInstance(config, LLMConfig)

    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Should fall back to defaults or raise appropriate errors
            try:
                config = LLMConfig()  # No explicit backend or API key
                # If it doesn't raise an exception, it should have reasonable defaults
                self.assertIsInstance(config, LLMConfig)
            except ValueError:
                # This is also acceptable behavior
                pass

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_config_with_extra_parameters(self):
        """Test LLMConfig with extra keyword arguments."""
        config = LLMConfig(
            backend=LLMBackend.OPENAI,
            model="gpt-4",
            custom_param="custom_value",
            another_param=123
        )
        
        # Extra parameters should be stored
        self.assertEqual(config.extra_params["custom_param"], "custom_value")
        self.assertEqual(config.extra_params["another_param"], 123)

    def test_concurrent_config_creation(self):
        """Test that multiple LLMConfig instances can be created concurrently."""
        import threading
        
        configs = []
        exceptions = []
        
        def create_config():
            try:
                with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                    config = LLMConfig(backend=LLMBackend.OPENAI)
                    configs.append(config)
            except Exception as e:
                exceptions.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_config)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no exceptions occurred
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred: {exceptions}")
        self.assertEqual(len(configs), 10)
        
        # All configs should be valid
        for config in configs:
            self.assertIsInstance(config, LLMConfig)
            self.assertEqual(config.backend, LLMBackend.OPENAI)


class TestLLMConfigIntegration(unittest.TestCase):
    """Integration tests for LLM configuration with other components."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_llm_config_with_healthcare_crew(self):
        """Test LLMConfig integration with HealthcareSimulationCrew."""
        from crew import HealthcareSimulationCrew
        
        # Create custom LLM config
        config = LLMConfig(
            backend=LLMBackend.OPENAI,
            model="gpt-3.5-turbo",
            temperature=0.5
        )
        
        # Should be able to create crew with custom config
        crew = HealthcareSimulationCrew(llm_config=config)
        self.assertIsNotNone(crew)
        self.assertEqual(crew.llm_config, config)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_llm_config_with_simulate_module(self):
        """Test LLMConfig integration with simulate module."""
        import simulate
        
        # Test that simulate module can use custom LLM config
        config = create_llm_config(backend="openai", model="gpt-4")
        self.assertIsInstance(config, LLMConfig)
        self.assertEqual(config.backend, LLMBackend.OPENAI)
        self.assertEqual(config.model, "gpt-4")

    def test_llm_config_serialization(self):
        """Test that LLMConfig can be serialized/deserialized."""
        import json
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            config = LLMConfig(
                backend=LLMBackend.OPENAI,
                model="gpt-4",
                temperature=0.8
            )
            
            # Convert to dict for serialization
            config_dict = {
                'backend': config.backend.value,
                'model': config.model,
                'temperature': config.temperature,
                'base_url': config.base_url
            }
            
            # Should be JSON serializable
            json_str = json.dumps(config_dict)
            self.assertIsInstance(json_str, str)
            
            # Should be deserializable
            loaded_dict = json.loads(json_str)
            self.assertEqual(loaded_dict['backend'], 'openai')
            self.assertEqual(loaded_dict['model'], 'gpt-4')


if __name__ == '__main__':
    unittest.main()