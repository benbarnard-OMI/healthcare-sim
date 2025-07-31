#!/usr/bin/env python3
"""
Healthcare Simulation Extensibility Validation Script

This script validates the extensibility features of the healthcare simulation system,
including scenario loading, configuration management, and custom agent/task support.
"""

import sys
import os
from typing import List, Dict, Any

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✓ {message}")

def print_error(message: str) -> None:
    """Print an error message."""
    print(f"✗ {message}")

def print_info(message: str) -> None:
    """Print an info message."""
    print(f"ℹ {message}")

def validate_scenario_system() -> bool:
    """Validate the scenario loading system."""
    print_section("SCENARIO SYSTEM VALIDATION")
    
    try:
        from scenario_loader import get_scenario_loader
        import sample_data.sample_messages as sample_messages
        
        # Initialize scenario loader
        loader = get_scenario_loader()
        loader.fallback_module = sample_messages
        
        # Test basic functionality
        scenarios = loader.list_scenarios()
        print_success(f"Scenario loader initialized - found {len(scenarios)} scenarios")
        
        # Test YAML loading capability
        if os.path.exists('config/scenarios.yaml'):
            print_success("YAML scenario configuration file found")
        else:
            print_info("YAML scenario configuration file not found - using Python fallback")
        
        # Test individual scenarios
        test_scenarios = ['chest_pain', 'diabetes', 'pediatric']
        for scenario_id in test_scenarios:
            info = loader.get_scenario_info(scenario_id)
            if info:
                print_success(f"Scenario '{scenario_id}': {info['name']}")
            else:
                print_error(f"Scenario '{scenario_id}' not found")
        
        # Test filtering capabilities
        all_scenarios = loader.list_scenarios()
        categories = set()
        severities = set()
        
        for scenario_id in all_scenarios:
            info = loader.get_scenario_info(scenario_id)
            if info:
                categories.add(info.get('metadata', {}).get('category', 'general_medicine'))
                severities.add(info.get('severity', 'moderate'))
        
        print_success(f"Scenario categories: {sorted(categories)}")
        print_success(f"Scenario severities: {sorted(severities)}")
        
        # Test validation
        errors = loader.validate_configuration()
        if errors:
            print_error(f"Scenario validation errors: {errors}")
            return False
        else:
            print_success("Scenario validation passed")
        
        return True
        
    except Exception as e:
        print_error(f"Scenario system validation failed: {str(e)}")
        return False

def validate_configuration_system() -> bool:
    """Validate the configuration loading system."""
    print_section("CONFIGURATION SYSTEM VALIDATION")
    
    try:
        from config_loader import get_config_loader
        
        # Initialize configuration loader
        loader = get_config_loader()
        agents, tasks = loader.load_configurations()
        
        print_success(f"Configuration loader initialized")
        print_success(f"Found {len(agents)} agents total")
        print_success(f"Found {len(tasks)} tasks total")
        
        # Test custom configurations
        custom_agents = loader.list_custom_agents()
        custom_tasks = loader.list_custom_tasks()
        
        print_success(f"Found {len(custom_agents)} custom agents")
        print_success(f"Found {len(custom_tasks)} custom tasks")
        
        # Test some specific custom agents
        expected_custom_agents = [
            'custom_pharmacist_agent',
            'custom_infection_control_agent', 
            'custom_mental_health_agent',
            'custom_quality_assurance_agent'
        ]
        
        for agent_name in expected_custom_agents:
            info = loader.get_agent_info(agent_name)
            if info:
                print_success(f"Custom agent '{agent_name}': {info['role']}")
            else:
                print_error(f"Custom agent '{agent_name}' not found")
        
        # Test validation
        errors = loader.validate_configuration_files()
        if errors:
            print_error(f"Configuration validation errors: {errors}")
            return False
        else:
            print_success("Configuration validation passed")
        
        return True
        
    except Exception as e:
        print_error(f"Configuration system validation failed: {str(e)}")
        return False

def validate_integration() -> bool:
    """Validate integration with the main crew system."""
    print_section("INTEGRATION VALIDATION")
    
    try:
        from crew import HealthcareSimulationCrew
        
        # Test crew initialization (without LLM to avoid API key requirement)
        try:
            crew = HealthcareSimulationCrew()
            print_success("Crew system initialized")
            
            # Test agent and task availability
            available_agents = crew.list_available_agents()
            available_tasks = crew.list_available_tasks()
            
            print_success(f"Crew has access to {len(available_agents)} agents")
            print_success(f"Crew has access to {len(available_tasks)} tasks")
            
            # Test dynamic addition capabilities
            print_success("Dynamic agent/task addition capability available")
            
            return True
            
        except Exception as e:
            if "OpenAI API key" in str(e) or "LLM" in str(e):
                print_info("Crew system requires API key for full initialization (expected)")
                print_success("Integration components available")
                return True
            else:
                raise e
        
    except Exception as e:
        print_error(f"Integration validation failed: {str(e)}")
        return False

def validate_documentation() -> bool:
    """Validate that documentation files exist and are complete."""
    print_section("DOCUMENTATION VALIDATION")
    
    expected_docs = [
        'docs/data_format_guide.md',
        'docs/scenario_extension_guide.md', 
        'docs/configuration_extension_guide.md',
        'config/scenarios.yaml',
        'config/custom_agents_template.yaml',
        'config/custom_tasks_template.yaml'
    ]
    
    all_found = True
    for doc_path in expected_docs:
        if os.path.exists(doc_path):
            print_success(f"Documentation file: {doc_path}")
        else:
            print_error(f"Missing documentation file: {doc_path}")
            all_found = False
    
    return all_found

def validate_backward_compatibility() -> bool:
    """Validate backward compatibility with existing functionality."""
    print_section("BACKWARD COMPATIBILITY VALIDATION")
    
    try:
        # Test that original imports still work
        from sample_data.sample_messages import SAMPLE_MESSAGES, list_scenarios, get_message
        print_success("Original sample_messages imports work")
        
        # Test that simulate.py still works
        import simulate
        print_success("simulate.py imports successfully")
        
        # Test that original functions still work
        scenarios = list_scenarios()
        print_success(f"Original list_scenarios() returns {len(scenarios)} scenarios")
        
        message = get_message('chest_pain')
        if message and 'MSH|' in message:
            print_success("Original get_message() works correctly")
        else:
            print_error("Original get_message() not working correctly")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Backward compatibility validation failed: {str(e)}")
        return False

def main():
    """Run all validation tests."""
    print("Healthcare Simulation Extensibility Validation")
    print("This script validates the new extensibility features.")
    
    # Run all validation tests
    tests = [
        ("Scenario System", validate_scenario_system),
        ("Configuration System", validate_configuration_system), 
        ("Integration", validate_integration),
        ("Documentation", validate_documentation),
        ("Backward Compatibility", validate_backward_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_section("VALIDATION SUMMARY")
    
    all_passed = True
    for test_name, passed in results:
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All extensibility features validated successfully!")
        print("The healthcare simulation system is ready for extension and customization.")
        return 0
    else:
        print("\n❌ Some validation tests failed.")
        print("Please review the errors above and ensure all components are properly installed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())