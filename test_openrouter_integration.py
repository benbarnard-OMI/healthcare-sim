"""
Comprehensive OpenRouter Integration Tests
Tests the specific GLM-4.6 endpoint with the provided API key
"""

import os
import sys
import time
from llm_config import create_llm_config, test_connection, LLMBackend
from sample_data.sample_messages import get_message, list_scenarios

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "z-ai/glm-4.6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def test_openrouter_glm_connection():
    """Test connection to OpenRouter GLM-4.6 endpoint"""
    print("Testing OpenRouter GLM-4.6 connection...")
    
    try:
        config = create_llm_config(
            backend="openrouter",
            api_key=OPENROUTER_API_KEY,
            model=OPENROUTER_MODEL,
            base_url=OPENROUTER_BASE_URL
        )
        
        print(f"  Configuration: {config}")
        
        # Test connection
        start_time = time.time()
        connection_success = test_connection(config)
        connection_time = time.time() - start_time
        
        if connection_success:
            print(f"  ✅ Connection successful in {connection_time:.2f}s")
            return True, config
        else:
            print(f"  ❌ Connection failed after {connection_time:.2f}s")
            return False, None
            
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
        return False, None

def test_glm_healthcare_scenarios(config):
    """Test GLM-4.6 with healthcare scenarios"""
    print("\nTesting GLM-4.6 with healthcare scenarios...")
    
    scenarios = list_scenarios()
    results = {}
    
    for scenario in scenarios:
        print(f"\n  Testing scenario: {scenario}")
        
        try:
            # Get sample message
            message = get_message(scenario)
            print(f"    Sample message length: {len(message)} characters")
            
            # Test with OpenAI client
            from openai import OpenAI
            
            client_params = config.get_client_params()
            client = OpenAI(**client_params)
            
            # Create a healthcare-focused prompt
            prompt = f"""You are a healthcare AI assistant. Analyze this HL7 message and provide a brief summary:

{message}

Please provide:
1. Message type
2. Key patient information
3. Clinical findings
4. Recommendations

Keep response concise and professional."""

            start_time = time.time()
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            response_time = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"    ✅ Response received in {response_time:.2f}s")
                print(f"    Response length: {len(content)} characters")
                print(f"    First 200 chars: {content[:200]}...")
                
                results[scenario] = {
                    'success': True,
                    'response_time': response_time,
                    'response_length': len(content),
                    'content': content
                }
            else:
                print(f"    ❌ No response content received")
                results[scenario] = {'success': False, 'error': 'No response content'}
                
        except Exception as e:
            print(f"    ❌ Scenario {scenario} failed: {e}")
            results[scenario] = {'success': False, 'error': str(e)}
    
    return results

def test_performance_metrics(config):
    """Test performance metrics for GLM-4.6"""
    print("\nTesting performance metrics...")
    
    try:
        from openai import OpenAI
        
        client_params = config.get_client_params()
        client = OpenAI(**client_params)
        
        # Test with different message sizes
        test_messages = [
            "Hello, how are you?",
            "This is a medium length test message for performance testing.",
            "This is a longer test message that contains more content to test the performance of the GLM-4.6 model with various input sizes and complexity levels."
        ]
        
        performance_results = []
        
        for i, message in enumerate(test_messages):
            print(f"  Test {i+1}: {len(message)} characters")
            
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": message}],
                temperature=0.7,
                max_tokens=100
            )
            
            response_time = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                performance_results.append({
                    'input_length': len(message),
                    'response_time': response_time,
                    'output_length': len(content),
                    'tokens_per_second': len(content.split()) / response_time if response_time > 0 else 0
                })
                print(f"    ✅ {response_time:.2f}s, {len(content)} chars output")
            else:
                print(f"    ❌ No response received")
        
        return performance_results
        
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        return []

def test_error_handling(config):
    """Test error handling with various edge cases"""
    print("\nTesting error handling...")
    
    try:
        from openai import OpenAI
        
        client_params = config.get_client_params()
        client = OpenAI(**client_params)
        
        # Test cases
        test_cases = [
            ("Empty message", ""),
            ("Very long message", "A" * 10000),
            ("Special characters", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
            ("Unicode characters", "Hello 世界 🌍"),
            ("Medical terminology", "Patient presents with acute myocardial infarction and requires immediate intervention")
        ]
        
        error_results = []
        
        for test_name, message in test_cases:
            print(f"  Testing: {test_name}")
            
            try:
                start_time = time.time()
                
                response = client.chat.completions.create(
                    model=config.model,
                    messages=[{"role": "user", "content": message}],
                    temperature=0.7,
                    max_tokens=50
                )
                
                response_time = time.time() - start_time
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    print(f"    ✅ Handled successfully in {response_time:.2f}s")
                    error_results.append({
                        'test_name': test_name,
                        'success': True,
                        'response_time': response_time
                    })
                else:
                    print(f"    ⚠️  No response content")
                    error_results.append({
                        'test_name': test_name,
                        'success': False,
                        'error': 'No response content'
                    })
                    
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                error_results.append({
                    'test_name': test_name,
                    'success': False,
                    'error': str(e)
                })
        
        return error_results
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return []

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("="*80)
    print("COMPREHENSIVE OPENROUTER GLM-4.6 INTEGRATION TESTS")
    print("="*80)
    
    # Test 1: Connection
    connection_success, config = test_openrouter_glm_connection()
    
    if not connection_success:
        print("\n❌ Connection test failed. Cannot proceed with other tests.")
        return False
    
    # Test 2: Healthcare scenarios
    scenario_results = test_glm_healthcare_scenarios(config)
    
    # Test 3: Performance metrics
    performance_results = test_performance_metrics(config)
    
    # Test 4: Error handling
    error_results = test_error_handling(config)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    # Connection test
    print(f"✅ Connection Test: {'PASSED' if connection_success else 'FAILED'}")
    
    # Scenario tests
    scenario_success = sum(1 for r in scenario_results.values() if r.get('success', False))
    scenario_total = len(scenario_results)
    print(f"✅ Healthcare Scenarios: {scenario_success}/{scenario_total} passed")
    
    # Performance tests
    perf_success = len([r for r in performance_results if r.get('tokens_per_second', 0) > 0])
    perf_total = len(performance_results)
    print(f"✅ Performance Tests: {perf_success}/{perf_total} passed")
    
    # Error handling tests
    error_success = len([r for r in error_results if r.get('success', False)])
    error_total = len(error_results)
    print(f"✅ Error Handling: {error_success}/{error_total} passed")
    
    # Overall success
    total_tests = 1 + scenario_total + perf_total + error_total
    total_passed = (1 if connection_success else 0) + scenario_success + perf_success + error_success
    
    print(f"\n🎯 OVERALL: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests PASSED! OpenRouter GLM-4.6 integration is working perfectly!")
        return True
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)