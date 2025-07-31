# Configuration Extension Guide

This guide explains how to create custom agents and tasks for the Healthcare Simulation system. Learn to extend the system with specialized healthcare professionals and custom workflow tasks.

## Quick Start

### Adding a Custom Agent

1. Open `config/custom_agents_template.yaml`
2. Copy the `agent_template` section
3. Customize it for your needs:

```yaml
my_custom_pharmacist:
  role: >
    Clinical Pharmacist Specialist
  goal: >
    Review medications for safety, efficacy, and drug interactions
  backstory: >
    You are a clinical pharmacist with expertise in pharmacokinetics and drug therapy management.
    You specialize in identifying drug interactions and optimizing medication regimens.
  tools:
    - medication_interaction_tool
  allow_delegation: false
  verbose: true
  max_execution_time: 300
```

4. Test your agent:
```python
from crew import HealthcareSimulationCrew
crew = HealthcareSimulationCrew()
crew.add_dynamic_agent('my_custom_pharmacist', agent_config)
```

### Adding a Custom Task

1. Open `config/custom_tasks_template.yaml`
2. Copy the `task_template` section
3. Customize it:

```yaml
medication_review:
  description: >
    Conduct comprehensive medication review for patient {patient_id}.
    Analyze for drug interactions, dosing, and therapeutic appropriateness.
  expected_output: >
    A medication review report with interaction analysis and recommendations.
  agent: my_custom_pharmacist
  context:
    - ingest_hl7_data
    - analyze_diagnostics
  max_execution_time: 300
```

## Agent Configuration

### Core Agent Fields

Every agent must define these essential characteristics:

#### Role
The professional role and specialty:
```yaml
role: >
  Clinical Pharmacist Specialist
```

#### Goal  
Primary objective and focus area:
```yaml
goal: >
  Review medication regimens for safety, efficacy, and drug interactions
```

#### Backstory
Professional background and expertise:
```yaml
backstory: >
  You are a clinical pharmacist with expertise in pharmacokinetics and drug therapy management.
  You specialize in identifying potential drug interactions, optimizing dosing regimens, and
  ensuring medication safety across diverse patient populations.
```

### Optional Agent Configuration

#### Tools
List of available tools for the agent:
```yaml
tools:
  - clinical_guidelines_tool
  - medication_interaction_tool
  - appointment_scheduler_tool
```

#### Delegation Settings
Control whether the agent can delegate tasks:
```yaml
allow_delegation: true  # or false
```

#### Execution Parameters
Configure agent behavior:
```yaml
verbose: true                # Enable detailed output
max_execution_time: 300      # Maximum seconds for task execution
temperature: 0.7             # LLM creativity (0.0-1.0)
max_tokens: 2000            # Maximum response length
```

## Advanced Agent Examples

### Infection Control Specialist

```yaml
infection_control_specialist:
  role: >
    Healthcare-Associated Infection Control Specialist
  goal: >
    Identify infection risks, implement prevention measures, and ensure compliance with infection control protocols
  backstory: >
    You are an infection control specialist with extensive experience in healthcare epidemiology.
    You excel at risk assessment, outbreak investigation, and developing evidence-based prevention strategies.
    Your expertise includes antimicrobial stewardship, isolation protocols, and surveillance systems.
  tools:
    - clinical_guidelines_tool
  allow_delegation: false
  verbose: true
  max_execution_time: 400
  specialties:
    - healthcare_associated_infections
    - antimicrobial_stewardship
    - outbreak_investigation
    - prevention_protocols
```

### Mental Health Specialist

```yaml
mental_health_specialist:
  role: >
    Licensed Clinical Mental Health Specialist
  goal: >
    Assess psychological factors impacting patient care and provide mental health recommendations
  backstory: >
    You are a licensed mental health specialist with expertise in medical psychology and psychiatric consultation.
    You understand the complex interplay between mental and physical health, trauma-informed care principles,
    and evidence-based therapeutic interventions. You excel at screening, assessment, and care integration.
  tools:
    - clinical_guidelines_tool
  allow_delegation: false
  verbose: true
  max_execution_time: 350
  assessment_areas:
    - depression_screening
    - anxiety_disorders
    - trauma_assessment
    - substance_use_evaluation
    - cognitive_assessment
```

### Quality Assurance Analyst

```yaml
quality_assurance_analyst:
  role: >
    Healthcare Quality Assurance and Performance Improvement Analyst
  goal: >
    Monitor care quality indicators, ensure adherence to best practices, and identify improvement opportunities
  backstory: >
    You are a quality assurance specialist focused on healthcare performance metrics and continuous improvement.
    You excel at analyzing care patterns, measuring outcomes against benchmarks, and developing process improvements
    to enhance patient safety and care quality. Your expertise includes statistical analysis and performance measurement.
  tools: []
  allow_delegation: false
  verbose: true
  max_execution_time: 300
  quality_domains:
    - patient_safety_indicators
    - clinical_effectiveness
    - care_coordination
    - patient_experience
    - efficiency_metrics
```

### Specialized Nurse Practitioner

```yaml
acute_care_nurse_practitioner:
  role: >
    Acute Care Nurse Practitioner
  goal: >
    Provide advanced nursing assessment, diagnosis, and management of acute and critical care patients
  backstory: >
    You are an acute care nurse practitioner with advanced clinical training in critical care medicine.
    You excel at rapid assessment, clinical decision-making, and patient stabilization in acute care settings.
    Your expertise includes advanced pathophysiology, pharmacology, and evidence-based acute care protocols.
  tools:
    - clinical_guidelines_tool
    - medication_interaction_tool
  allow_delegation: true
  verbose: true
  max_execution_time: 350
  clinical_areas:
    - acute_assessment
    - critical_care_management
    - patient_stabilization
    - family_communication
    - care_transitions
```

## Task Configuration

### Core Task Fields

Every task requires these essential elements:

#### Description
Detailed task instructions with specific requirements:
```yaml
description: >
  Conduct comprehensive medication review for patient {patient_id}.
  Analyze current medications for:
  - Drug-drug interactions
  - Drug-disease contraindications
  - Dosing appropriateness
  - Therapeutic duplication
  - Missing indicated medications
```

#### Expected Output
Specific deliverable format and content:
```yaml
expected_output: >
  A medication review report containing:
  - Current medication list with assessment
  - Identified interactions with severity ratings
  - Dosing recommendations and adjustments
  - Patient education points
  - Monitoring parameters
```

#### Agent Assignment
The responsible agent for this task:
```yaml
agent: my_custom_pharmacist
```

### Task Dependencies

#### Context Dependencies
Tasks that must complete before this task:
```yaml
context:
  - ingest_hl7_data
  - analyze_diagnostics
  - create_treatment_plan
```

#### Tool Dependencies
Specific tools needed for this task:
```yaml
tools:
  - medication_interaction_tool
  - clinical_guidelines_tool
```

## Advanced Task Examples

### Comprehensive Medication Review

```yaml
comprehensive_medication_review:
  description: >
    Perform a detailed medication therapy management review for patient {patient_id}.
    Evaluate:
    - Current medication list accuracy and completeness
    - Drug-drug, drug-disease, and drug-food interactions
    - Dosing appropriateness for age, weight, and renal/hepatic function
    - Therapeutic duplication and contraindications
    - Medication adherence barriers and solutions
    - Cost-effectiveness and therapeutic alternatives
    - Monitoring parameters and follow-up requirements
  expected_output: >
    A comprehensive medication therapy management report including:
    - Reconciled medication list with assessment of each drug
    - Interaction analysis with clinical significance ratings
    - Dosing recommendations with rationale
    - Therapeutic alternatives when appropriate
    - Patient education materials and counseling points
    - Monitoring plan with specific parameters and timing
    - Follow-up recommendations and safety measures
  agent: clinical_pharmacist_specialist
  context:
    - ingest_hl7_data
    - analyze_diagnostics
  tools:
    - medication_interaction_tool
  max_execution_time: 600
  priority: high
  requires_validation: true
```

### Infection Control Assessment

```yaml
infection_control_risk_assessment:
  description: >
    Conduct thorough infection control risk assessment for patient {patient_id}.
    Assess:
    - Current infection status and microbiology results
    - Risk factors for healthcare-associated infections
    - Appropriate isolation precautions and PPE requirements
    - Antimicrobial therapy appropriateness and stewardship
    - Environmental controls and cleaning protocols
    - Contact tracing and surveillance requirements
    - Staff education and compliance monitoring needs
  expected_output: >
    An infection control assessment report with:
    - Risk stratification and current infection status
    - Evidence-based isolation precaution recommendations
    - Antimicrobial stewardship recommendations with rationale
    - Environmental control measures and protocols
    - Surveillance and monitoring requirements
    - Staff and visitor guidance with education materials
    - Quality indicators and compliance metrics
  agent: infection_control_specialist
  context:
    - ingest_hl7_data
    - analyze_diagnostics
  tools:
    - clinical_guidelines_tool
  max_execution_time: 450
  priority: high
  output_format: structured_report
```

### Mental Health Integration Assessment

```yaml
mental_health_integration_assessment:
  description: >
    Evaluate mental health factors and integration opportunities for patient {patient_id}.
    Consider:
    - Psychological impact of current medical condition
    - Mental health history and current symptoms
    - Social determinants affecting mental health
    - Coping mechanisms and support systems
    - Risk factors for depression, anxiety, or trauma responses
    - Integration points with medical treatment plan
    - Barriers to mental health care access
  expected_output: >
    A mental health integration assessment including:
    - Psychological risk and protective factor analysis
    - Evidence-based screening results and clinical impressions
    - Recommendations for mental health interventions
    - Integration strategies with medical treatment plan
    - Referral recommendations with specific provider types
    - Patient and family support resource recommendations
    - Follow-up and monitoring plan for mental health aspects
  agent: mental_health_specialist
  context:
    - ingest_hl7_data
    - analyze_diagnostics
    - create_treatment_plan
  tools:
    - clinical_guidelines_tool
  max_execution_time: 400
  priority: medium
  requires_specialized_training: true
```

### Discharge Planning and Care Transitions

```yaml
comprehensive_discharge_planning:
  description: >
    Develop detailed discharge planning and care transition strategy for patient {patient_id}.
    Address:
    - Medical stability criteria and discharge readiness assessment
    - Home environment assessment and safety considerations
    - Medication reconciliation and patient education requirements
    - Follow-up appointment coordination and scheduling
    - Durable medical equipment and home health service needs
    - Patient and caregiver education and competency assessment
    - Communication with receiving providers and care teams
    - Risk mitigation and contingency planning
  expected_output: >
    A comprehensive discharge plan including:
    - Discharge readiness checklist with criteria and timeline
    - Home care services coordination with contact information
    - Complete medication reconciliation with patient education materials
    - Structured follow-up appointment schedule with priorities
    - Equipment and service authorization with delivery coordination
    - Patient and caregiver education documentation and competency assessment
    - Provider communication plan with care transition summary
    - Emergency contacts and warning signs with action plans
  agent: care_coordinator
  context:
    - ingest_hl7_data
    - analyze_diagnostics
    - create_treatment_plan
    - coordinate_care
  tools:
    - appointment_scheduler_tool
  max_execution_time: 500
  priority: high
  requires_coordination: true
```

## Configuration Validation

### Validation Rules

The system validates configurations against these rules:

#### Agent Validation
- **Required fields**: role, goal, backstory
- **Optional fields**: tools, allow_delegation, verbose, max_execution_time
- **Tool validation**: Must reference available tools
- **Type validation**: Proper data types and formats

#### Task Validation  
- **Required fields**: description, expected_output, agent
- **Agent validation**: Must reference existing agent
- **Context validation**: Dependencies must exist
- **Execution validation**: Reasonable time limits and parameters

### Custom Validation

Add custom validation rules:

```yaml
# In custom_agents_template.yaml
validation:
  required_fields:
    - role
    - goal
    - backstory
  
  custom_rules:
    max_execution_time:
      min: 60
      max: 3600
    temperature:
      min: 0.0
      max: 1.0
  
  specialty_requirements:
    clinical_pharmacist:
      required_tools: [medication_interaction_tool]
    infection_control:
      required_tools: [clinical_guidelines_tool]
```

## Dynamic Configuration Loading

### Runtime Agent Creation

```python
from config_loader import get_config_loader

# Get configuration loader
config_loader = get_config_loader()

# Define custom agent
custom_agent_config = {
    'role': 'Respiratory Therapist',
    'goal': 'Optimize respiratory care and ventilator management',
    'backstory': 'You are a certified respiratory therapist with expertise in pulmonary function and ventilator management.',
    'tools': ['clinical_guidelines_tool'],
    'allow_delegation': False,
    'verbose': True,
    'max_execution_time': 300
}

# Add agent dynamically
try:
    config_loader.add_custom_agent('respiratory_therapist', custom_agent_config)
    print("Custom agent added successfully")
except Exception as e:
    print(f"Error adding agent: {e}")
```

### Runtime Task Creation

```python
# Define custom task
custom_task_config = {
    'description': 'Assess respiratory status and optimize ventilator settings for patient {patient_id}.',
    'expected_output': 'Respiratory assessment with ventilator recommendations and monitoring plan.',
    'agent': 'respiratory_therapist',
    'context': ['ingest_hl7_data', 'analyze_diagnostics'],
    'max_execution_time': 300
}

# Add task dynamically
try:
    config_loader.add_custom_task('respiratory_assessment', custom_task_config)
    print("Custom task added successfully")
except Exception as e:
    print(f"Error adding task: {e}")
```

### Integration with Crew

```python
from crew import HealthcareSimulationCrew

# Create crew with custom configurations
crew = HealthcareSimulationCrew()

# Add custom agent and task
crew.add_dynamic_agent('respiratory_therapist', custom_agent_config)
crew.add_dynamic_task('respiratory_assessment', custom_task_config)

# Run simulation with custom components
result = crew.crew().kickoff(inputs={'hl7_message': hl7_message})
```

## Best Practices

### Agent Design Principles

1. **Single Responsibility**: Each agent should have a clear, focused role
2. **Clinical Accuracy**: Ensure agents reflect real healthcare professional capabilities
3. **Appropriate Tools**: Assign tools that match the agent's clinical role
4. **Realistic Constraints**: Set reasonable execution times and capabilities

### Task Design Principles

1. **Clear Objectives**: Define specific, measurable task outcomes
2. **Appropriate Dependencies**: Ensure logical task sequencing
3. **Comprehensive Output**: Specify detailed expected deliverables
4. **Error Handling**: Consider edge cases and error scenarios

### Configuration Management

1. **Version Control**: Track configuration changes with git
2. **Testing**: Validate configurations before deployment
3. **Documentation**: Document custom agents and tasks thoroughly
4. **Backup**: Maintain backups of working configurations

## Testing and Validation

### Configuration Testing

```python
# Test configuration loading
from config_loader import get_config_loader

loader = get_config_loader()
errors = loader.validate_configuration_files()

if errors:
    print("Configuration errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("All configurations are valid")
```

### Agent Testing

```python
# Test custom agent functionality
from crew import HealthcareSimulationCrew

crew = HealthcareSimulationCrew()

# List available agents
agents = crew.list_available_agents()
print("Available agents:", agents)

# Get agent information
agent_info = loader.get_agent_info('my_custom_agent')
print("Agent info:", agent_info)
```

### Simulation Testing

```bash
# Test with custom configuration
python simulate.py --scenario diabetes --verbose

# Test specific custom components
python test_custom_configs.py --agent my_custom_agent --task my_custom_task
```

## Troubleshooting

### Common Configuration Issues

1. **YAML Syntax Errors**: Check indentation and special characters
2. **Missing Required Fields**: Ensure all required fields are present
3. **Invalid Tool References**: Verify tool names match available tools
4. **Circular Dependencies**: Check task context dependencies
5. **Agent Not Found**: Ensure agent exists before assigning to tasks

### Debug Techniques

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check configuration loading
from config_loader import get_config_loader
loader = get_config_loader()

# Debug agent loading
print("Built-in agents:", loader.list_agents())
print("Custom agents:", loader.list_custom_agents())

# Debug task loading  
print("Built-in tasks:", loader.list_tasks())
print("Custom tasks:", loader.list_custom_tasks())
```

## Migration Guide

### Migrating from Legacy Configurations

If you have existing custom agents or tasks, migrate them to the new format:

1. **Extract existing configurations** from Python code
2. **Convert to YAML format** using the templates
3. **Validate new configurations** using the validation tools
4. **Test functionality** with the new system
5. **Update references** in your code

### Backward Compatibility

The system maintains backward compatibility with:
- Existing YAML configurations
- Python-based scenarios  
- Legacy agent and task definitions
- Current simulation workflows

## Resources

- [CrewAI Documentation](https://github.com/joaomdmoura/crewAI)
- [YAML Specification](https://yaml.org/spec/1.2/spec.html)
- [Healthcare Agent Examples](config/custom_agents_template.yaml)
- [Healthcare Task Examples](config/custom_tasks_template.yaml)
- [System Architecture Documentation](docs/DEVELOPER_GUIDE.md)

For additional help or questions, please refer to the project documentation or contact the development team.