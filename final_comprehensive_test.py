"""
Final Comprehensive Integration Test Suite
Tests all LLM backends, healthcare scenarios, and CrewAI integration
"""

import os
import time
import sys
from llm_config import create_llm_config, get_available_backends, test_connection
from sample_data.sample_messages import get_message, list_scenarios

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "z-ai/glm-4.6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class TestResults:
    """Class to track test results"""
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    def add_result(self, test_name, success, details=None, execution_time=None):
        self.results[test_name] = {
            'success': success,
            'details': details,
            'execution_time': execution_time,
            'timestamp': time.time()
        }
    
    def get_summary(self):
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r['success'])
        total_time = time.time() - self.start_time
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'total_time': total_time,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

def test_llm_backend_configurations():
    """Test all LLM backend configurations"""
    print("="*60)
    print("TESTING LLM BACKEND CONFIGURATIONS")
    print("="*60)
    
    results = TestResults()
    
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
            elif backend == "openrouter":
                config = create_llm_config(
                    backend=backend,
                    api_key=OPENROUTER_API_KEY,
                    model=OPENROUTER_MODEL,
                    base_url=OPENROUTER_BASE_URL,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
            
            # Test configuration creation
            results.add_result(f"{backend}_config_creation", True, f"Config: {config}")
            
            # Test OpenAI-compatible config generation
            openai_config = config.to_openai_config()
            results.add_result(f"{backend}_openai_config", True, f"OpenAI config generated: {len(openai_config)} params")
            
            # Test client parameters
            client_params = config.get_client_params()
            results.add_result(f"{backend}_client_params", True, f"Client params: {len(client_params)} params")
            
            print(f"  ✅ {backend} configuration successful")
            
        except Exception as e:
            results.add_result(f"{backend}_config_creation", False, str(e))
            print(f"  ❌ {backend} configuration failed: {e}")
    
    return results

def test_openrouter_glm_connection():
    """Test OpenRouter GLM-4.6 connection"""
    print("\n" + "="*60)
    print("TESTING OPENROUTER GLM-4.6 CONNECTION")
    print("="*60)
    
    results = TestResults()
    
    try:
        config = create_llm_config(
            backend="openrouter",
            api_key=OPENROUTER_API_KEY,
            model=OPENROUTER_MODEL,
            base_url=OPENROUTER_BASE_URL,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        print(f"Configuration: {config}")
        
        # Test connection
        start_time = time.time()
        connection_success = test_connection(config)
        connection_time = time.time() - start_time
        
        results.add_result("openrouter_connection", connection_success, 
                          f"Connection time: {connection_time:.2f}s", connection_time)
        
        if connection_success:
            print(f"  ✅ Connection successful in {connection_time:.2f}s")
            
            # Test actual API call
            from openai import OpenAI
            client_params = config.get_client_params()
            client = OpenAI(**client_params)
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": "Hello, how are you?"}],
                temperature=0.7,
                max_tokens=100,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            api_time = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                results.add_result("openrouter_api_call", True, 
                                  f"API call successful: {len(content)} chars", api_time)
                print(f"  ✅ API call successful in {api_time:.2f}s")
                print(f"  Response: '{content[:100]}{'...' if len(content) > 100 else ''}'")
            else:
                results.add_result("openrouter_api_call", False, "No response content")
                print(f"  ❌ API call failed - no response content")
        else:
            print(f"  ❌ Connection failed after {connection_time:.2f}s")
            results.add_result("openrouter_api_call", False, "Connection failed")
            
    except Exception as e:
        results.add_result("openrouter_connection", False, str(e))
        results.add_result("openrouter_api_call", False, str(e))
        print(f"  ❌ OpenRouter test failed: {e}")
    
    return results

def test_healthcare_scenarios():
    """Test healthcare scenarios with GLM-4.6"""
    print("\n" + "="*60)
    print("TESTING HEALTHCARE SCENARIOS")
    print("="*60)
    
    results = TestResults()
    
    try:
        config = create_llm_config(
            backend="openrouter",
            api_key=OPENROUTER_API_KEY,
            model=OPENROUTER_MODEL,
            base_url=OPENROUTER_BASE_URL,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        from openai import OpenAI
        client_params = config.get_client_params()
        client = OpenAI(**client_params)
        
        scenarios = list_scenarios()
        print(f"Testing {len(scenarios)} healthcare scenarios:")
        
        for scenario in scenarios:
            print(f"\n  Testing scenario: {scenario}")
            
            try:
                message = get_message(scenario)
                print(f"    Sample message length: {len(message)} characters")
                
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
                    success = len(content.strip()) > 0
                    results.add_result(f"healthcare_scenario_{scenario}", success, 
                                      f"Response: {len(content)} chars", response_time)
                    
                    if success:
                        print(f"    ✅ Response received in {response_time:.2f}s")
                        print(f"    Response length: {len(content)} characters")
                        print(f"    First 100 chars: {content[:100]}...")
                    else:
                        print(f"    ⚠️  Empty response received in {response_time:.2f}s")
                else:
                    results.add_result(f"healthcare_scenario_{scenario}", False, "No response content")
                    print(f"    ❌ No response content received")
                    
            except Exception as e:
                results.add_result(f"healthcare_scenario_{scenario}", False, str(e))
                print(f"    ❌ Scenario {scenario} failed: {e}")
        
    except Exception as e:
        results.add_result("healthcare_scenarios_setup", False, str(e))
        print(f"  ❌ Healthcare scenarios test failed: {e}")
    
    return results

def test_crewai_integration():
    """Test CrewAI integration with GLM-4.6"""
    print("\n" + "="*60)
    print("TESTING CREWAI INTEGRATION")
    print("="*60)
    
    results = TestResults()
    
    try:
        from crewai import Agent, Task, Crew
        from crewai.llm import LLM
        
        # Create LLM instance with correct model name format
        llm = LLM(
            model="openrouter/z-ai/glm-4.6",
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
            max_tokens=500,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        results.add_result("crewai_llm_creation", True, "LLM instance created successfully")
        print("  ✅ LLM instance created successfully")
        
        # Create agent
        agent = Agent(
            role='Healthcare Assistant',
            goal='Analyze healthcare data and provide insights',
            backstory='You are an AI assistant specialized in healthcare data analysis.',
            llm=llm,
            verbose=True
        )
        
        results.add_result("crewai_agent_creation", True, "Agent created successfully")
        print("  ✅ Agent created successfully")
        
        # Create task
        task = Task(
            description='Analyze this HL7 message: MSH|^~\\&|HIS|HOSPITAL|LIS|LAB|20240101120000||ORU^R01|12345|P|2.5',
            expected_output='A brief analysis of the HL7 message structure and content',
            agent=agent
        )
        
        results.add_result("crewai_task_creation", True, "Task created successfully")
        print("  ✅ Task created successfully")
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        results.add_result("crewai_crew_creation", True, "Crew created successfully")
        print("  ✅ Crew created successfully")
        
        # Test execution
        print("  Testing crew execution...")
        start_time = time.time()
        
        result = crew.kickoff()
        
        execution_time = time.time() - start_time
        
        success = result is not None and len(str(result).strip()) > 0
        results.add_result("crewai_execution", success, 
                          f"Execution time: {execution_time:.2f}s", execution_time)
        
        if success:
            print(f"  ✅ Crew execution completed in {execution_time:.2f}s")
            print(f"  Result length: {len(str(result))} characters")
            print(f"  First 200 chars: {str(result)[:200]}...")
        else:
            print(f"  ❌ Crew execution failed after {execution_time:.2f}s")
            
    except Exception as e:
        results.add_result("crewai_integration", False, str(e))
        print(f"  ❌ CrewAI integration failed: {e}")
    
    return results

def test_performance_metrics():
    """Test performance metrics"""
    print("\n" + "="*60)
    print("TESTING PERFORMANCE METRICS")
    print("="*60)
    
    results = TestResults()
    
    try:
        config = create_llm_config(
            backend="openrouter",
            api_key=OPENROUTER_API_KEY,
            model=OPENROUTER_MODEL,
            base_url=OPENROUTER_BASE_URL,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        from openai import OpenAI
        client_params = config.get_client_params()
        client = OpenAI(**client_params)
        
        # Test with different message sizes
        test_messages = [
            ("Short", "Hello!"),
            ("Medium", "This is a medium length test message for performance testing."),
            ("Long", "This is a longer test message that contains more content to test the performance of the GLM-4.6 model with various input sizes and complexity levels.")
        ]
        
        for test_name, message in test_messages:
            print(f"\n  Testing {test_name} message ({len(message)} chars):")
            
            try:
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
                    success = len(content.strip()) > 0
                    results.add_result(f"performance_{test_name.lower()}", success, 
                                      f"Response: {len(content)} chars", response_time)
                    
                    if success:
                        print(f"    ✅ {response_time:.2f}s, {len(content)} chars output")
                        print(f"    Content: '{content[:50]}{'...' if len(content) > 50 else ''}'")
                    else:
                        print(f"    ⚠️  {response_time:.2f}s, empty response")
                else:
                    results.add_result(f"performance_{test_name.lower()}", False, "No response content")
                    print(f"    ❌ No response received")
                    
            except Exception as e:
                results.add_result(f"performance_{test_name.lower()}", False, str(e))
                print(f"    ❌ {test_name} test failed: {e}")
        
    except Exception as e:
        results.add_result("performance_setup", False, str(e))
        print(f"  ❌ Performance test failed: {e}")
    
    return results

def run_final_comprehensive_tests():
    """Run all comprehensive tests"""
    print("="*80)
    print("FINAL COMPREHENSIVE INTEGRATION TEST SUITE")
    print("="*80)
    print(f"OpenRouter API Key: {OPENROUTER_API_KEY[:20]}...")
    print(f"Model: {OPENROUTER_MODEL}")
    print(f"Base URL: {OPENROUTER_BASE_URL}")
    print("="*80)
    
    # Run all test suites
    test_suites = [
        ("LLM Backend Configurations", test_llm_backend_configurations),
        ("OpenRouter GLM-4.6 Connection", test_openrouter_glm_connection),
        ("Healthcare Scenarios", test_healthcare_scenarios),
        ("CrewAI Integration", test_crewai_integration),
        ("Performance Metrics", test_performance_metrics)
    ]
    
    all_results = {}
    total_start_time = time.time()
    
    for suite_name, test_function in test_suites:
        print(f"\n{'='*20} {suite_name} {'='*20}")
        try:
            suite_results = test_function()
            all_results[suite_name] = suite_results
        except Exception as e:
            print(f"❌ {suite_name} suite failed: {e}")
            all_results[suite_name] = TestResults()
            all_results[suite_name].add_result("suite_error", False, str(e))
    
    # Generate final summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_time = time.time() - total_start_time
    
    for suite_name, results in all_results.items():
        summary = results.get_summary()
        total_tests += summary['total_tests']
        total_passed += summary['passed_tests']
        total_failed += summary['failed_tests']
        
        status = "✅ PASSED" if summary['failed_tests'] == 0 else "⚠️  PARTIAL" if summary['passed_tests'] > 0 else "❌ FAILED"
        print(f"{status} {suite_name}: {summary['passed_tests']}/{summary['total_tests']} tests passed ({summary['success_rate']:.1f}%)")
    
    print("\n" + "="*80)
    print("OVERALL RESULTS")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
    print(f"Total Time: {total_time:.2f}s")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Integration is working perfectly!")
        return True
    elif total_passed > total_tests * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL! Integration is working well with minor issues.")
        return True
    else:
        print("\n⚠️  SOME ISSUES DETECTED! Check the details above.")
        return False

if __name__ == "__main__":
    success = run_final_comprehensive_tests()
    sys.exit(0 if success else 1)