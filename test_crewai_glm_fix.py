"""
Fixed CrewAI integration with GLM-4.6
Uses the correct model name format for CrewAI/LiteLLM
"""

import os
import time
from llm_config import create_llm_config

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "z-ai/glm-4.6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def test_crewai_glm_fix():
    """Test CrewAI integration with fixed GLM-4.6 configuration"""
    print("Testing CrewAI integration with GLM-4.6...")
    
    try:
        from crewai import Agent, Task, Crew
        from crewai.llm import LLM
        
        # Create LLM instance with correct model name format for CrewAI
        # CrewAI/LiteLLM expects the model name to include the provider
        llm = LLM(
            model="openrouter/z-ai/glm-4.6",  # Add 'openrouter/' prefix
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
            max_tokens=500,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        print("  ✅ LLM instance created successfully")
        
        # Create a simple agent
        agent = Agent(
            role='Healthcare Assistant',
            goal='Analyze healthcare data and provide insights',
            backstory='You are an AI assistant specialized in healthcare data analysis.',
            llm=llm,
            verbose=True
        )
        
        print("  ✅ Agent created successfully")
        
        # Create a simple task
        task = Task(
            description='Analyze this HL7 message: MSH|^~\\&|HIS|HOSPITAL|LIS|LAB|20240101120000||ORU^R01|12345|P|2.5',
            expected_output='A brief analysis of the HL7 message structure and content',
            agent=agent
        )
        
        print("  ✅ Task created successfully")
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        print("  ✅ Crew created successfully")
        
        # Test execution
        print("  Testing crew execution...")
        start_time = time.time()
        
        result = crew.kickoff()
        
        execution_time = time.time() - start_time
        
        print(f"  ✅ Crew execution completed in {execution_time:.2f}s")
        print(f"  Result: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}")
        
        return True, execution_time, str(result)
        
    except Exception as e:
        print(f"  ❌ CrewAI integration failed: {e}")
        return False, None, str(e)

def test_alternative_crewai_approaches():
    """Test alternative approaches for CrewAI integration"""
    print("\nTesting alternative CrewAI approaches...")
    
    approaches = [
        {
            "name": "Direct OpenAI client approach",
            "model": "z-ai/glm-4.6",
            "base_url": OPENROUTER_BASE_URL
        },
        {
            "name": "LiteLLM direct approach",
            "model": "openrouter/z-ai/glm-4.6",
            "base_url": OPENROUTER_BASE_URL
        },
        {
            "name": "Custom LLM class approach",
            "model": "z-ai/glm-4.6",
            "base_url": OPENROUTER_BASE_URL
        }
    ]
    
    results = []
    
    for approach in approaches:
        print(f"\n  Testing: {approach['name']}")
        
        try:
            from crewai import Agent, Task, Crew
            from crewai.llm import LLM
            
            # Try different configurations
            if approach["name"] == "Custom LLM class approach":
                # Create a custom LLM class that handles the OpenRouter API directly
                from openai import OpenAI
                
                class CustomOpenRouterLLM:
                    def __init__(self, model, api_key, base_url, **kwargs):
                        self.model = model
                        self.client = OpenAI(api_key=api_key, base_url=base_url)
                        self.kwargs = kwargs
                    
                    def call(self, messages, **kwargs):
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            **{**self.kwargs, **kwargs}
                        )
                        return response.choices[0].message.content
                
                llm = CustomOpenRouterLLM(
                    model=approach["model"],
                    api_key=OPENROUTER_API_KEY,
                    base_url=approach["base_url"],
                    temperature=0.7,
                    max_tokens=500,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
                
                # Create agent with custom LLM
                agent = Agent(
                    role='Healthcare Assistant',
                    goal='Analyze healthcare data',
                    backstory='AI assistant for healthcare analysis',
                    llm=llm,
                    verbose=True
                )
                
                # Test direct call
                test_messages = [{"role": "user", "content": "Hello, how are you?"}]
                result = llm.call(test_messages)
                print(f"    ✅ Custom LLM working: {result[:100]}...")
                results.append({"approach": approach["name"], "success": True, "result": result})
                
            else:
                # Standard LLM approach
                llm = LLM(
                    model=approach["model"],
                    api_key=OPENROUTER_API_KEY,
                    base_url=approach["base_url"],
                    temperature=0.7,
                    max_tokens=500
                )
                
                agent = Agent(
                    role='Healthcare Assistant',
                    goal='Analyze healthcare data',
                    backstory='AI assistant for healthcare analysis',
                    llm=llm,
                    verbose=True
                )
                
                task = Task(
                    description='Say hello and introduce yourself',
                    expected_output='A brief greeting and introduction',
                    agent=agent
                )
                
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                
                start_time = time.time()
                result = crew.kickoff()
                execution_time = time.time() - start_time
                
                print(f"    ✅ {approach['name']} working: {execution_time:.2f}s")
                results.append({
                    "approach": approach["name"], 
                    "success": True, 
                    "execution_time": execution_time,
                    "result": str(result)
                })
                
        except Exception as e:
            print(f"    ❌ {approach['name']} failed: {e}")
            results.append({"approach": approach["name"], "success": False, "error": str(e)})
    
    return results

def run_crewai_tests():
    """Run all CrewAI tests"""
    print("="*80)
    print("CREWAI GLM-4.6 INTEGRATION TESTS")
    print("="*80)
    
    # Test 1: Fixed CrewAI integration
    success, execution_time, result = test_crewai_glm_fix()
    
    # Test 2: Alternative approaches
    alternative_results = test_alternative_crewai_approaches()
    
    # Summary
    print("\n" + "="*80)
    print("CREWAI TEST SUMMARY")
    print("="*80)
    
    print(f"✅ Fixed CrewAI Integration: {'PASSED' if success else 'FAILED'}")
    if success:
        print(f"   Execution time: {execution_time:.2f}s")
    
    print(f"\nAlternative Approaches:")
    for result in alternative_results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"  {status} {result['approach']}")
        if result["success"] and "execution_time" in result:
            print(f"    Execution time: {result['execution_time']:.2f}s")
        elif not result["success"]:
            print(f"    Error: {result['error']}")
    
    # Overall success
    total_approaches = 1 + len(alternative_results)
    successful_approaches = (1 if success else 0) + sum(1 for r in alternative_results if r["success"])
    
    print(f"\n🎯 OVERALL: {successful_approaches}/{total_approaches} approaches working")
    
    if successful_approaches > 0:
        print("🎉 At least one CrewAI integration approach is working!")
        return True
    else:
        print("⚠️  All CrewAI integration approaches failed.")
        return False

if __name__ == "__main__":
    success = run_crewai_tests()
    exit(0 if success else 1)