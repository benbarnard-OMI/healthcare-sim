"""
Optimized GLM-4.6 Integration Tests
Uses the best parameters discovered for GLM-4.6
"""

import os
import time
from llm_config import create_llm_config
from sample_data.sample_messages import get_message, list_scenarios

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "z-ai/glm-4.6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def test_optimized_glm_connection():
    """Test connection with optimized parameters"""
    print("Testing optimized GLM-4.6 connection...")
    
    try:
        config = create_llm_config(
            backend="openrouter",
            api_key=OPENROUTER_API_KEY,
            model=OPENROUTER_MODEL,
            base_url=OPENROUTER_BASE_URL,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        print(f"  Configuration: {config}")
        
        # Test connection
        start_time = time.time()
        from openai import OpenAI
        
        client_params = config.get_client_params()
        client = OpenAI(**client_params)
        
        # Test with a simple message
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            temperature=0.7,
            max_tokens=100,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        connection_time = time.time() - start_time
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"  ✅ Connection successful in {connection_time:.2f}s")
            print(f"  Response: '{content[:100]}{'...' if len(content) > 100 else ''}'")
            return True, config
        else:
            print(f"  ❌ Connection failed - no response content")
            return False, None
            
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
        return False, None

def test_healthcare_scenarios_optimized(config):
    """Test healthcare scenarios with optimized parameters"""
    print("\nTesting healthcare scenarios with optimized GLM-4.6...")
    
    scenarios = list_scenarios()
    results = {}
    
    for scenario in scenarios:
        print(f"\n  Testing scenario: {scenario}")
        
        try:
            # Get sample message
            message = get_message(scenario)
            print(f"    Sample message length: {len(message)} characters")
            
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
                max_tokens=500,
                frequency_penalty=0.0,
                presence_penalty=0.0
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

def test_performance_optimized(config):
    """Test performance with optimized parameters"""
    print("\nTesting performance with optimized parameters...")
    
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
                max_tokens=100,
                frequency_penalty=0.0,
                presence_penalty=0.0
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
                print(f"    Content: '{content[:50]}{'...' if len(content) > 50 else ''}'")
            else:
                print(f"    ❌ No response received")
        
        return performance_results
        
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        return []

def test_crew_integration(config):
    """Test CrewAI integration with optimized GLM-4.6"""
    print("\nTesting CrewAI integration...")
    
    try:
        # Test if we can create a simple agent with the configuration
        from crewai import Agent, Task, Crew
        from crewai.llm import LLM
        
        # Create LLM instance with our configuration
        llm = LLM(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Create a simple agent
        agent = Agent(
            role='Healthcare Assistant',
            goal='Analyze healthcare data and provide insights',
            backstory='You are an AI assistant specialized in healthcare data analysis.',
            llm=llm,
            verbose=True
        )
        
        # Create a simple task
        task = Task(
            description='Analyze this HL7 message: MSH|^~\\&|HIS|HOSPITAL|LIS|LAB|20240101120000||ORU^R01|12345|P|2.5',
            expected_output='A brief analysis of the HL7 message structure and content',
            agent=agent
        )
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        print("  ✅ CrewAI components created successfully")
        
        # Test execution (this might take a while)
        print("  Testing crew execution...")
        start_time = time.time()
        
        result = crew.kickoff()
        
        execution_time = time.time() - start_time
        
        print(f"  ✅ Crew execution completed in {execution_time:.2f}s")
        print(f"  Result: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
        
        return True, execution_time
        
    except Exception as e:
        print(f"  ❌ CrewAI integration failed: {e}")
        return False, None

def run_optimized_tests():
    """Run all optimized tests"""
    print("="*80)
    print("OPTIMIZED GLM-4.6 INTEGRATION TESTS")
    print("="*80)
    
    # Test 1: Connection
    connection_success, config = test_optimized_glm_connection()
    
    if not connection_success:
        print("\n❌ Connection test failed. Cannot proceed with other tests.")
        return False
    
    # Test 2: Healthcare scenarios
    scenario_results = test_healthcare_scenarios_optimized(config)
    
    # Test 3: Performance metrics
    performance_results = test_performance_optimized(config)
    
    # Test 4: CrewAI integration
    crew_success, crew_time = test_crew_integration(config)
    
    # Summary
    print("\n" + "="*80)
    print("OPTIMIZED TEST SUMMARY")
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
    
    # CrewAI integration
    print(f"✅ CrewAI Integration: {'PASSED' if crew_success else 'FAILED'}")
    if crew_success:
        print(f"   Execution time: {crew_time:.2f}s")
    
    # Overall success
    total_tests = 1 + scenario_total + perf_total + 1
    total_passed = (1 if connection_success else 0) + scenario_success + perf_success + (1 if crew_success else 0)
    
    print(f"\n🎯 OVERALL: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All optimized tests PASSED! GLM-4.6 integration is working perfectly!")
        return True
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_optimized_tests()
    exit(0 if success else 1)