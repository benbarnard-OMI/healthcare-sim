"""
Debug script for GLM-4.6 response issues
Investigates why the model is returning very short or empty responses
"""

import os
import time
from llm_config import create_llm_config
from openai import OpenAI

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "z-ai/glm-4.6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def debug_glm_responses():
    """Debug GLM-4.6 response issues"""
    print("="*60)
    print("DEBUGGING GLM-4.6 RESPONSE ISSUES")
    print("="*60)
    
    # Create configuration
    config = create_llm_config(
        backend="openrouter",
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_MODEL,
        base_url=OPENROUTER_BASE_URL
    )
    
    print(f"Configuration: {config}")
    
    # Initialize client
    client_params = config.get_client_params()
    client = OpenAI(**client_params)
    
    # Test cases with different parameters
    test_cases = [
        {
            "name": "Simple greeting",
            "message": "Hello, how are you?",
            "params": {"temperature": 0.7, "max_tokens": 100}
        },
        {
            "name": "Simple greeting with high temperature",
            "message": "Hello, how are you?",
            "params": {"temperature": 1.0, "max_tokens": 100}
        },
        {
            "name": "Simple greeting with low temperature",
            "message": "Hello, how are you?",
            "params": {"temperature": 0.1, "max_tokens": 100}
        },
        {
            "name": "Simple greeting with more tokens",
            "message": "Hello, how are you?",
            "params": {"temperature": 0.7, "max_tokens": 500}
        },
        {
            "name": "Medical question",
            "message": "What are the symptoms of diabetes?",
            "params": {"temperature": 0.7, "max_tokens": 200}
        },
        {
            "name": "Code generation",
            "message": "Write a Python function to calculate fibonacci numbers",
            "params": {"temperature": 0.7, "max_tokens": 300}
        },
        {
            "name": "Chinese question",
            "message": "你好，请介绍一下人工智能",
            "params": {"temperature": 0.7, "max_tokens": 200}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Message: {test_case['message']}")
        print(f"Params: {test_case['params']}")
        
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": test_case['message']}],
                **test_case['params']
            )
            
            response_time = time.time() - start_time
            
            print(f"Response time: {response_time:.2f}s")
            
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content
                finish_reason = choice.finish_reason
                
                print(f"Finish reason: {finish_reason}")
                print(f"Content length: {len(content)} characters")
                print(f"Content: '{content}'")
                
                # Check if content is empty or very short
                if len(content.strip()) == 0:
                    print("⚠️  WARNING: Empty response!")
                elif len(content.strip()) < 10:
                    print("⚠️  WARNING: Very short response!")
                else:
                    print("✅ Response looks good")
            else:
                print("❌ No choices in response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

def test_different_models():
    """Test different models to compare behavior"""
    print("\n" + "="*60)
    print("TESTING DIFFERENT MODELS")
    print("="*60)
    
    models_to_test = [
        "z-ai/glm-4.6",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemini-pro"
    ]
    
    config = create_llm_config(
        backend="openrouter",
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL
    )
    
    client_params = config.get_client_params()
    client = OpenAI(**client_params)
    
    test_message = "Hello, how are you? Please respond with at least 20 words."
    
    for model in models_to_test:
        print(f"\n--- Testing model: {model} ---")
        
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": test_message}],
                temperature=0.7,
                max_tokens=100
            )
            
            response_time = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"Response time: {response_time:.2f}s")
                print(f"Content length: {len(content)} characters")
                print(f"Content: '{content[:100]}{'...' if len(content) > 100 else ''}'")
            else:
                print("❌ No response content")
                
        except Exception as e:
            print(f"❌ Error with {model}: {e}")

def test_glm_specific_parameters():
    """Test GLM-4.6 with specific parameters that might work better"""
    print("\n" + "="*60)
    print("TESTING GLM-4.6 SPECIFIC PARAMETERS")
    print("="*60)
    
    config = create_llm_config(
        backend="openrouter",
        api_key=OPENROUTER_API_KEY,
        model=OPENROUTER_MODEL,
        base_url=OPENROUTER_BASE_URL
    )
    
    client_params = config.get_client_params()
    client = OpenAI(**client_params)
    
    # Test with different parameter combinations
    parameter_tests = [
        {"temperature": 0.7, "max_tokens": 100, "top_p": 1.0},
        {"temperature": 0.7, "max_tokens": 100, "top_p": 0.9},
        {"temperature": 0.7, "max_tokens": 100, "frequency_penalty": 0.0},
        {"temperature": 0.7, "max_tokens": 100, "presence_penalty": 0.0},
        {"temperature": 0.7, "max_tokens": 100, "stop": None},
        {"temperature": 0.7, "max_tokens": 100, "stream": False},
    ]
    
    test_message = "Please explain what artificial intelligence is in 2-3 sentences."
    
    for i, params in enumerate(parameter_tests, 1):
        print(f"\n--- Parameter Test {i} ---")
        print(f"Params: {params}")
        
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": test_message}],
                **params
            )
            
            response_time = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"Response time: {response_time:.2f}s")
                print(f"Content length: {len(content)} characters")
                print(f"Content: '{content}'")
            else:
                print("❌ No response content")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_glm_responses()
    test_different_models()
    test_glm_specific_parameters()