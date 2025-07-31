#!/usr/bin/env python3
"""
Healthcare Simulation Extensibility Demo

This script demonstrates how to use the new extensibility features
to add custom scenarios, agents, and tasks to the healthcare simulation system.
"""

def demo_scenario_extensibility():
    """Demonstrate scenario extensibility features."""
    print("=" * 60)
    print("SCENARIO EXTENSIBILITY DEMO")
    print("=" * 60)
    
    from scenario_loader import get_scenario_loader
    import sample_data.sample_messages as sample_messages
    
    # Initialize scenario loader with fallback
    loader = get_scenario_loader()
    loader.fallback_module = sample_messages
    
    print("\n1. Available Scenarios:")
    scenarios = loader.list_scenarios()
    for scenario_id in scenarios:
        info = loader.get_scenario_info(scenario_id)
        if info:
            category = info.get('metadata', {}).get('category', info.get('category', 'general_medicine'))
            print(f"   • {scenario_id}: {info['name']} ({category})")
    
    print("\n2. Scenario Details Example (Chest Pain):")
    chest_pain_info = loader.get_scenario_info('chest_pain')
    if chest_pain_info:
        print(f"   Name: {chest_pain_info['name']}")
        print(f"   Description: {chest_pain_info['description']}")
        metadata = chest_pain_info.get('metadata', {})
        print(f"   Category: {metadata.get('category', 'general_medicine')}")
        print(f"   Age Group: {metadata.get('age_group', 'adult')}")
        print(f"   Primary Condition: {metadata.get('primary_condition', 'unknown')}")
        print(f"   Has HL7 Message: {chest_pain_info['has_hl7_message']}")
    
    print("\n3. HL7 Message Preview:")
    hl7_message = loader.get_hl7_message('chest_pain')
    if hl7_message:
        lines = hl7_message.strip().split('\n')
        for i, line in enumerate(lines[:5]):  # Show first 5 lines
            print(f"   {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
        if len(lines) > 5:
            print(f"   ... ({len(lines) - 5} more lines)")

def demo_configuration_extensibility():
    """Demonstrate configuration extensibility features."""
    print("\n" + "=" * 60)
    print("CONFIGURATION EXTENSIBILITY DEMO")
    print("=" * 60)
    
    from config_loader import get_config_loader
    
    # Initialize configuration loader
    loader = get_config_loader()
    agents, tasks = loader.load_configurations()
    
    print("\n1. Built-in vs Custom Components:")
    all_agents = loader.list_agents()
    custom_agents = loader.list_custom_agents()
    builtin_agents = [a for a in all_agents if a not in custom_agents]
    
    print(f"   Built-in Agents ({len(builtin_agents)}): {', '.join(builtin_agents)}")
    print(f"   Custom Agents ({len(custom_agents)}): {', '.join(custom_agents)}")
    
    all_tasks = loader.list_tasks()
    custom_tasks = loader.list_custom_tasks()
    builtin_tasks = [t for t in all_tasks if t not in custom_tasks]
    
    print(f"   Built-in Tasks ({len(builtin_tasks)}): {', '.join(builtin_tasks)}")
    print(f"   Custom Tasks ({len(custom_tasks)}): {', '.join(custom_tasks)}")
    
    print("\n2. Custom Agent Example (Clinical Pharmacist):")
    pharmacist_info = loader.get_agent_info('custom_pharmacist_agent')
    if pharmacist_info:
        print(f"   Role: {pharmacist_info['role']}")
        print(f"   Goal: {pharmacist_info['goal'][:100]}...")
        print(f"   Tools: {', '.join(pharmacist_info['tools'])}")
        print(f"   Can Delegate: {pharmacist_info['allow_delegation']}")
    
    print("\n3. Custom Task Example (Medication Review):")
    med_review_info = loader.get_task_info('medication_review_task')
    if med_review_info:
        print(f"   Description: {med_review_info['description'][:100]}...")
        print(f"   Assigned Agent: {med_review_info['agent']}")
        print(f"   Context Dependencies: {', '.join(med_review_info['context'])}")
        print(f"   Max Execution Time: {med_review_info['max_execution_time']} seconds")

def demo_dynamic_configuration():
    """Demonstrate dynamic configuration capabilities."""
    print("\n" + "=" * 60)
    print("DYNAMIC CONFIGURATION DEMO")
    print("=" * 60)
    
    from config_loader import get_config_loader
    
    loader = get_config_loader()
    loader.load_configurations()
    
    print("\n1. Adding a Custom Agent Dynamically:")
    
    # Define a custom respiratory therapist agent
    respiratory_therapist_config = {
        'role': 'Certified Respiratory Therapist',
        'goal': 'Optimize respiratory care and ventilator management for critically ill patients',
        'backstory': 'You are a certified respiratory therapist with expertise in pulmonary function, '
                    'mechanical ventilation, and airway management. You excel at optimizing ventilator '
                    'settings and respiratory treatments for diverse patient populations.',
        'tools': ['clinical_guidelines_tool'],
        'allow_delegation': False,
        'verbose': True,
        'max_execution_time': 300
    }
    
    try:
        loader.add_custom_agent('respiratory_therapist', respiratory_therapist_config)
        print("   ✓ Successfully added Respiratory Therapist agent")
        
        # Verify it was added
        rt_info = loader.get_agent_info('respiratory_therapist')
        if rt_info:
            print(f"   ✓ Agent confirmed: {rt_info['role']}")
        
    except Exception as e:
        print(f"   ✗ Failed to add agent: {e}")
    
    print("\n2. Adding a Custom Task Dynamically:")
    
    # Define a custom respiratory assessment task
    respiratory_assessment_config = {
        'description': 'Conduct comprehensive respiratory assessment for patient {patient_id}. '
                      'Evaluate ventilatory status, gas exchange, and optimize respiratory therapies.',
        'expected_output': 'A respiratory assessment report with ventilator recommendations, '
                          'therapy adjustments, and monitoring plan.',
        'agent': 'respiratory_therapist',
        'context': ['ingest_hl7_data', 'analyze_diagnostics'],
        'max_execution_time': 350
    }
    
    try:
        loader.add_custom_task('respiratory_assessment', respiratory_assessment_config)
        print("   ✓ Successfully added Respiratory Assessment task")
        
        # Verify it was added
        ra_info = loader.get_task_info('respiratory_assessment')
        if ra_info:
            print(f"   ✓ Task confirmed: assigned to {ra_info['agent']}")
        
    except Exception as e:
        print(f"   ✗ Failed to add task: {e}")
    
    print("\n3. Updated Configuration Summary:")
    updated_agents = loader.list_agents()
    updated_tasks = loader.list_tasks()
    print(f"   Total Agents: {len(updated_agents)} (including new respiratory_therapist)")
    print(f"   Total Tasks: {len(updated_tasks)} (including new respiratory_assessment)")

def demo_integration_potential():
    """Demonstrate integration potential with the crew system."""
    print("\n" + "=" * 60)
    print("INTEGRATION POTENTIAL DEMO")
    print("=" * 60)
    
    print("\n1. Integration with Crew System:")
    print("   The new extensibility features integrate seamlessly with the existing")
    print("   CrewAI-based healthcare simulation system:")
    print("   • Custom agents become available to the crew")
    print("   • Custom tasks can be added to workflows")
    print("   • Dynamic configuration supports runtime customization")
    print("   • All changes maintain backward compatibility")
    
    print("\n2. Example Usage in Simulation:")
    print("   # Load custom configurations")
    print("   from crew import HealthcareSimulationCrew")
    print("   crew = HealthcareSimulationCrew()")
    print("")
    print("   # Add custom respiratory therapist")
    print("   crew.add_dynamic_agent('respiratory_therapist', rt_config)")
    print("   crew.add_dynamic_task('respiratory_assessment', ra_config)")
    print("")
    print("   # Run simulation with enhanced capabilities")
    print("   result = crew.crew().kickoff(inputs={'hl7_message': patient_data})")
    
    print("\n3. Extensibility Benefits:")
    benefits = [
        "Easy addition of specialized healthcare professionals",
        "Customizable clinical workflows and protocols",
        "Rich scenario metadata for targeted simulations", 
        "YAML-based configuration for non-programmers",
        "Comprehensive validation and error handling",
        "Template-based approach for consistency",
        "Backward compatibility with existing scenarios"
    ]
    
    for i, benefit in enumerate(benefits, 1):
        print(f"   {i}. {benefit}")

def main():
    """Run the extensibility demonstration."""
    print("Healthcare Simulation Extensibility Features Demo")
    print("This demo showcases the new extensibility capabilities.")
    
    try:
        demo_scenario_extensibility()
        demo_configuration_extensibility() 
        demo_dynamic_configuration()
        demo_integration_potential()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nFor more information, see the documentation:")
        print("• docs/scenario_extension_guide.md")
        print("• docs/configuration_extension_guide.md")
        print("• docs/data_format_guide.md")
        print("\nTo get started with customization:")
        print("• Copy templates from config/custom_*_template.yaml")
        print("• Follow the examples in the documentation")
        print("• Use validate_extensibility.py to test your changes")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        print("Please ensure all dependencies are installed and the system is properly configured.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())