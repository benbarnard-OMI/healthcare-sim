"""
Integration tests for LLM backend functionality
Tests the complete workflow without requiring CrewAI installation
"""

import os
import tempfile
from llm_config import create_llm_config, get_available_backends, test_connection
from sample_data.sample_messages import get_message, list_scenarios

def test_end_to_end_configuration():
    """Test complete configuration workflow"""
    print("Testing end-to-end configuration...")
    
    # Test each backend configuration
    for backend in get_available_backends():
        print(f"\nTesting {backend} backend:")
        
        try:
            if backend == "openai":
                config = create_llm_config(
                    backend=backend, 
                    api_key="test-key",
                    model="gpt-4"
                )
            elif backend == "ollama":
                config = create_llm_config(
                    backend=backend,
                    model="llama2"
                )
            else:  # openrouter
                config = create_llm_config(
                    backend=backend,
                    api_key="test-key", 
                    model="openai/gpt-4"
                )
            
            print(f"  ✅ Configuration created: {config}")
            
            # Test OpenAI-compatible config generation
            openai_config = config.to_openai_config()
            assert "model" in openai_config
            assert "temperature" in openai_config
            print(f"  ✅ OpenAI config: {openai_config}")
            
            # Test client parameters
            client_params = config.get_client_params()
            if backend != "ollama" or config.api_key:
                assert "api_key" in client_params
            assert "base_url" in client_params
            print(f"  ✅ Client params: {client_params}")
            
        except Exception as e:
            print(f"  ❌ {backend} configuration failed: {e}")
            return False
    
    print("\n✅ All backend configurations successful!")
    return True

def test_scenario_integration():
    """Test integration with sample scenarios"""
    print("\nTesting scenario integration...")
    
    scenarios = list_scenarios()
    print(f"Available scenarios: {scenarios}")
    
    for scenario in scenarios[:2]:  # Test first 2 scenarios
        try:
            message = get_message(scenario)
            assert len(message) > 0
            print(f"  ✅ {scenario}: {len(message)} characters")
        except Exception as e:
            print(f"  ❌ {scenario} failed: {e}")
            return False
    
    print("✅ Scenario integration successful!")
    return True

def test_environment_variable_support():
    """Test environment variable configuration"""
    print("\nTesting environment variable support...")
    
    # Save original environment
    original_env = {}
    test_vars = ['LLM_BACKEND', 'OLLAMA_MODEL', 'LLM_TEMPERATURE']
    for var in test_vars:
        original_env[var] = os.environ.get(var)
    
    try:
        # Set test environment variables
        os.environ['LLM_BACKEND'] = 'ollama'
        os.environ['OLLAMA_MODEL'] = 'llama2:13b'
        os.environ['LLM_TEMPERATURE'] = '0.5'
        
        # Create config from environment
        config = create_llm_config()
        
        assert config.backend.value == 'ollama'
        assert config.model == 'llama2:13b'
        assert config.temperature == 0.5
        
        print(f"  ✅ Environment config: {config}")
        
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
    
    print("✅ Environment variable support successful!")
    return True

def test_file_operations():
    """Test file operations for CLI usage"""
    print("\nTesting file operations...")
    
    try:
        # Test with temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hl7', delete=False) as f:
            sample_message = get_message('diabetes')
            f.write(sample_message)
            temp_file = f.name
        
        # Simulate reading file (like simulate.py does)
        with open(temp_file, 'r') as f:
            loaded_message = f.read()
        
        assert loaded_message == sample_message
        print(f"  ✅ File I/O successful: {len(loaded_message)} characters")
        
        # Cleanup
        os.unlink(temp_file)
        
    except Exception as e:
        print(f"  ❌ File operations failed: {e}")
        return False
    
    print("✅ File operations successful!")
    return True

def test_error_handling():
    """Test error handling and validation"""
    print("\nTesting error handling...")
    
    try:
        # Test invalid backend
        try:
            create_llm_config(backend="invalid_backend")
            print("  ❌ Should have failed with invalid backend")
            return False
        except ValueError:
            print("  ✅ Invalid backend properly rejected")
        
        # Test missing API key for OpenAI
        try:
            create_llm_config(backend="openai", api_key=None)
            print("  ❌ Should have failed without OpenAI API key")
            return False
        except ValueError:
            print("  ✅ Missing OpenAI API key properly rejected")
        
        # Test missing API key for Openrouter
        try:
            create_llm_config(backend="openrouter", api_key=None)
            print("  ❌ Should have failed without Openrouter API key")
            return False
        except ValueError:
            print("  ✅ Missing Openrouter API key properly rejected")
        
        # Test Ollama without API key (should work)
        config = create_llm_config(backend="ollama", api_key=None)
        print(f"  ✅ Ollama without API key works: {config}")
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False
    
    print("✅ Error handling successful!")
    return True

def run_all_tests():
    """Run all integration tests"""
    print("="*60)
    print("HEALTHCARE SIMULATION - LLM BACKEND INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        test_end_to_end_configuration,
        test_scenario_integration,
        test_environment_variable_support,
        test_file_operations,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"\n❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"\n❌ {test.__name__} CRASHED: {e}")
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("🎉 All integration tests PASSED!")
        return True
    else:
        print("⚠️  Some integration tests FAILED!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)