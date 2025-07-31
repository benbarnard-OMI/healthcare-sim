# Developer Guide for Healthcare Simulation System

This guide provides comprehensive instructions for extending the Healthcare Simulation System by adding new agents, tasks, and tools.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Extending Agents](#extending-agents)
3. [Extending Tasks](#extending-tasks)
4. [Extending Tools](#extending-tools)
5. [Configuration Files](#configuration-files)
6. [Best Practices](#best-practices)
7. [Testing Your Extensions](#testing-your-extensions)

## Architecture Overview

The healthcare simulation system is built using CrewAI and follows a modular architecture:

```
├── config/
│   ├── agents.yaml    # Agent definitions and configurations
│   └── tasks.yaml     # Task definitions and workflows
├── tools/
│   └── healthcare_tools.py  # Custom healthcare tools
├── crew.py           # Main crew orchestration logic
└── sample_data/      # Sample HL7 messages for testing
```

### Core Components

- **Agents**: Specialized healthcare roles (diagnosticians, coordinators, etc.)
- **Tasks**: Specific workflow steps in the care pathway simulation
- **Tools**: Reusable utilities that agents can use (clinical guidelines, scheduling, etc.)
- **Crew**: Orchestrates the entire simulation workflow

## Extending Agents

### 1. Understanding Agent Structure

Agents are defined in `config/agents.yaml` and represent healthcare professionals with specific roles. Each agent has:

- **Role**: The professional title/specialty
- **Goal**: What the agent aims to accomplish
- **Backstory**: Context that shapes the agent's behavior and decision-making

### 2. Adding a New Agent

#### Step 1: Define the Agent in `config/agents.yaml`

```yaml
# Example: Adding a Pharmacy Specialist Agent
pharmacy_specialist:
  role: >
    Clinical Pharmacy Specialist
  goal: >
    Review medication regimens for safety, efficacy, and drug interactions
  backstory: >
    You are an expert clinical pharmacist with deep knowledge of pharmacokinetics,
    drug interactions, and medication therapy management. You excel at identifying
    potential medication-related problems and optimizing drug therapy for patients.
    Your expertise helps prevent adverse drug events and improves therapeutic outcomes.
```

#### Step 2: Register the Agent in `crew.py`

Add the agent method to the `HealthcareSimulationCrew` class:

```python
@agent
def pharmacy_specialist(self) -> Agent:
    return Agent(
        config=self.agents_config['pharmacy_specialist'],
        tools=[self.healthcare_tools.medication_interaction_checker],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=False
    )
```

#### Step 3: Create Agent-Specific Tools (Optional)

If your agent needs specialized tools, add them to `tools/healthcare_tools.py`:

```python
class MedicationReviewInput(BaseModel):
    """Input schema for medication review tool."""
    patient_medications: str = Field(..., description="List of current medications")
    patient_conditions: str = Field(..., description="Patient's medical conditions")
    patient_age: int = Field(..., description="Patient age in years")

class MedicationReviewTool(BaseTool):
    name: str = "Medication Review Tool"
    description: str = "Comprehensive medication review for safety and efficacy"
    args_schema: type[BaseModel] = MedicationReviewInput

    def _run(self, patient_medications: str, patient_conditions: str, patient_age: int) -> str:
        # Implementation logic here
        return "Medication review results..."
```

### 3. Agent Configuration Options

#### Advanced Agent Configuration

```yaml
advanced_agent_example:
  role: >
    Specialized Healthcare Role
  goal: >
    Specific objective for the agent
  backstory: >
    Detailed background that influences decision-making
  # Optional: Specify allowed tools
  tools:
    - clinical_guidelines_tool
    - medication_interaction_tool
  # Optional: Set delegation permissions
  allow_delegation: true
  # Optional: Set verbosity level
  verbose: true
  # Optional: Set maximum iterations
  max_iter: 5
```

### 4. Agent Best Practices

1. **Specific Roles**: Make roles specific to healthcare specialties
2. **Clear Goals**: Define measurable objectives
3. **Rich Backstories**: Provide context that guides decision-making
4. **Appropriate Tools**: Only assign tools relevant to the agent's role
5. **Realistic Expertise**: Base agent capabilities on real healthcare professionals

## Extending Tasks

### 1. Understanding Task Structure

Tasks are defined in `config/tasks.yaml` and represent specific steps in the healthcare workflow. Each task has:

- **Description**: What the task accomplishes
- **Expected Output**: The format and content of the task result
- **Agent**: Which agent performs the task
- **Context**: Dependencies on other tasks

### 2. Adding a New Task

#### Step 1: Define the Task in `config/tasks.yaml`

```yaml
# Example: Adding a Medication Review Task
review_medications:
  description: >
    Conduct a comprehensive medication review for the patient:
    - Assess all current medications for appropriateness
    - Check for drug-drug interactions
    - Evaluate dosing based on age, weight, and kidney function
    - Identify potential medication-related problems
    - Recommend medication optimizations
  expected_output: >
    A medication review report containing:
    - List of current medications with assessment
    - Identified drug interactions and contraindications
    - Dosing recommendations and adjustments
    - Medication-related problem identification
    - Optimization recommendations with rationale
  agent: pharmacy_specialist
  context:
    - ingest_hl7_data
    - analyze_diagnostics
```

#### Step 2: Register the Task in `crew.py`

Add the task method to the `HealthcareSimulationCrew` class:

```python
@task
def review_medications(self) -> Task:
    return Task(
        config=self.tasks_config['review_medications'],
        agent=self.pharmacy_specialist(),
        output_file='medication_review.md'  # Optional: save output to file
    )
```

#### Step 3: Update the Crew Workflow

Add your task to the crew execution flow:

```python
@crew
def crew(self) -> Crew:
    """Creates the HealthcareSimulation crew"""
    return Crew(
        agents=self.agents,
        tasks=[
            self.ingest_hl7_data(),
            self.analyze_diagnostics(),
            self.review_medications(),  # Add your new task
            self.create_treatment_plan(),
            self.coordinate_care(),
            self.evaluate_outcomes()
        ],
        process=Process.hierarchical,
        manager_agent=self.care_coordinator(),
        verbose=True
    )
```

### 3. Task Dependencies and Context

#### Linear Dependencies
```yaml
task_b:
  # ... task configuration
  context:
    - task_a  # task_b depends on task_a output
```

#### Multiple Dependencies
```yaml
task_c:
  # ... task configuration
  context:
    - task_a
    - task_b  # task_c depends on both task_a and task_b
```

#### Conditional Logic in Tasks
```yaml
specialized_task:
  description: >
    Perform specialized analysis if certain conditions are met:
    - Check if patient has diabetes from previous diagnostic analysis
    - If positive, conduct detailed diabetic care assessment
    - Otherwise, perform general health maintenance review
```

### 4. Task Best Practices

1. **Clear Descriptions**: Specify exactly what the task should accomplish
2. **Structured Outputs**: Define consistent output formats
3. **Proper Dependencies**: Ensure tasks have access to required information
4. **Realistic Scope**: Keep tasks focused and achievable
5. **Error Handling**: Consider edge cases and validation

## Extending Tools

### 1. Understanding Tool Structure

Tools are reusable components that agents can use to perform specific functions. They're implemented as classes inheriting from `crewai.tools.BaseTool`.

### 2. Creating a New Tool

#### Step 1: Define Input Schema

```python
from pydantic import BaseModel, Field

class RadiologyOrderInput(BaseModel):
    """Input schema for radiology ordering tool."""
    patient_condition: str = Field(..., description="Patient's clinical condition")
    suspected_diagnosis: str = Field(..., description="Suspected diagnosis")
    urgency_level: str = Field(default="routine", description="Urgency: stat, urgent, routine")
    patient_age: int = Field(..., description="Patient age in years")
    contraindications: Optional[str] = Field(default=None, description="Known contraindications")
```

#### Step 2: Implement the Tool Class

```python
from crewai.tools import BaseTool

class RadiologyOrderTool(BaseTool):
    name: str = "Radiology Order Tool"
    description: str = "Order appropriate radiology studies based on clinical presentation"
    args_schema: type[BaseModel] = RadiologyOrderInput

    def _run(self, patient_condition: str, suspected_diagnosis: str, 
             urgency_level: str = "routine", patient_age: int = 0, 
             contraindications: Optional[str] = None) -> str:
        """
        Order appropriate radiology studies based on clinical presentation.
        
        Args:
            patient_condition: Current clinical condition
            suspected_diagnosis: Working diagnosis
            urgency_level: Priority level for the study
            patient_age: Patient's age
            contraindications: Any known contraindications
            
        Returns:
            String containing radiology order recommendations
        """
        
        # Example implementation
        recommendations = []
        
        # Clinical decision logic
        if "chest pain" in patient_condition.lower():
            if urgency_level == "stat":
                recommendations.append("STAT Chest X-ray (2 views)")
                recommendations.append("Consider STAT CT Angiography if high suspicion for PE")
            else:
                recommendations.append("Chest X-ray (PA and lateral)")
                
        if "abdominal pain" in patient_condition.lower():
            if patient_age > 50:
                recommendations.append("CT Abdomen/Pelvis with contrast")
            else:
                recommendations.append("Abdominal ultrasound initially")
                
        # Check contraindications
        if contraindications and "contrast allergy" in contraindications.lower():
            recommendations = [r.replace("with contrast", "without contrast") for r in recommendations]
            
        if not recommendations:
            recommendations.append("No specific radiology studies recommended at this time")
            
        result = f"""
        RADIOLOGY ORDER RECOMMENDATIONS:
        Clinical Indication: {patient_condition}
        Suspected Diagnosis: {suspected_diagnosis}
        Urgency Level: {urgency_level}
        
        Recommended Studies:
        {chr(10).join(f"- {rec}" for rec in recommendations)}
        
        Clinical Notes:
        - Consider patient's clinical stability before ordering
        - Ensure appropriate contrast precautions if applicable
        - Follow institutional radiology ordering guidelines
        """
        
        return result.strip()
```

#### Step 3: Register the Tool

Add your tool to the `HealthcareTools` class in `tools/healthcare_tools.py`:

```python
class HealthcareTools:
    """Collection of healthcare-specific tools for agents."""
    
    def __init__(self):
        # Existing tools
        self.clinical_guidelines = ClinicalGuidelinesTool()
        self.medication_interaction_checker = MedicationInteractionTool()
        self.appointment_scheduler = AppointmentSchedulerTool()
        
        # Add your new tool
        self.radiology_order_tool = RadiologyOrderTool()

    def get_all_tools(self) -> List[BaseTool]:
        """Return all available healthcare tools."""
        return [
            self.clinical_guidelines,
            self.medication_interaction_checker,
            self.appointment_scheduler,
            self.radiology_order_tool,  # Include your new tool
        ]
```

#### Step 4: Assign Tools to Agents

Update agent definitions to include access to your new tool:

```python
@agent
def diagnostics_agent(self) -> Agent:
    return Agent(
        config=self.agents_config['diagnostics_agent'],
        tools=[
            self.healthcare_tools.clinical_guidelines,
            self.healthcare_tools.radiology_order_tool,  # Add your tool
        ],
        llm=self.llm_config.llm,
        verbose=True
    )
```

### 3. Advanced Tool Features

#### Tool with External API Integration

```python
import httpx
from typing import Optional

class LabResultsTool(BaseTool):
    name: str = "Lab Results Lookup"
    description: str = "Retrieve lab results from external laboratory system"
    args_schema: type[BaseModel] = LabResultsInput

    def _run(self, patient_id: str, test_type: str) -> str:
        """Retrieve lab results from external system."""
        try:
            # Example external API call
            response = httpx.get(f"https://lab-api.hospital.com/results/{patient_id}/{test_type}")
            if response.status_code == 200:
                results = response.json()
                return self._format_lab_results(results)
            else:
                return f"Unable to retrieve lab results: {response.status_code}"
        except Exception as e:
            return f"Error accessing lab system: {str(e)}"
    
    def _format_lab_results(self, results: dict) -> str:
        """Format lab results for agent consumption."""
        # Implementation details...
        pass
```

#### Tool with Configuration Options

```python
class ConfigurableTool(BaseTool):
    name: str = "Configurable Healthcare Tool"
    description: str = "Tool with configurable behavior"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config = config or {}
        self.threshold = self.config.get('threshold', 0.8)
        self.strict_mode = self.config.get('strict_mode', False)
    
    def _run(self, input_data: str) -> str:
        # Use configuration in tool logic
        if self.strict_mode:
            # Stricter validation logic
            pass
        # Tool implementation...
```

### 4. Tool Best Practices

1. **Single Responsibility**: Each tool should have one clear purpose
2. **Robust Error Handling**: Handle edge cases and failures gracefully
3. **Clear Documentation**: Provide detailed descriptions and examples
4. **Type Safety**: Use proper type hints and Pydantic schemas
5. **Performance**: Consider caching for expensive operations
6. **Security**: Validate inputs and sanitize outputs

## Configuration Files

### Agent Configuration (`config/agents.yaml`)

```yaml
# Template for new agents
new_agent_name:
  role: >
    Brief description of the healthcare role
  goal: >
    Specific, measurable objective for the agent
  backstory: >
    Detailed background that provides context for decision-making.
    Include relevant experience, specialization, and approach to care.
    This shapes how the agent interprets and responds to situations.
  # Optional configurations
  tools: []  # List of specific tools for this agent
  allow_delegation: false  # Whether agent can delegate tasks
  verbose: true  # Enable detailed logging
  max_iter: 3  # Maximum iterations for task completion
```

### Task Configuration (`config/tasks.yaml`)

```yaml
# Template for new tasks
new_task_name:
  description: >
    Detailed description of what the task should accomplish.
    Include specific steps, considerations, and requirements.
    Be explicit about the expected workflow and decision points.
  expected_output: >
    Clear specification of the output format and content.
    Define the structure, required elements, and quality criteria.
    This helps ensure consistent and useful results.
  agent: responsible_agent_name
  context:
    - prerequisite_task_1
    - prerequisite_task_2
  # Optional configurations
  output_file: "task_output.md"  # Save output to file
  async_execution: false  # Execute asynchronously
  human_input: false  # Require human input
```

## Best Practices

### 1. Design Principles

- **Healthcare Accuracy**: Ensure clinical accuracy and evidence-based practices
- **Modularity**: Keep components independent and reusable
- **Scalability**: Design for easy addition of new specialties and workflows
- **Maintainability**: Use clear naming and documentation
- **Testing**: Include comprehensive tests for new components

### 2. Clinical Considerations

- **Evidence-Based**: Base agent behavior on current clinical guidelines
- **Safety First**: Prioritize patient safety in all decision-making
- **Realistic Workflows**: Mirror actual healthcare processes
- **Interdisciplinary**: Consider how different specialties interact
- **Quality Metrics**: Include measures for care quality and outcomes

### 3. Code Organization

```
your_extension/
├── agents/
│   └── new_specialty_agent.yaml
├── tasks/
│   └── new_workflow_tasks.yaml
├── tools/
│   └── specialty_tools.py
├── tests/
│   ├── test_agents.py
│   ├── test_tasks.py
│   └── test_tools.py
└── docs/
    └── specialty_guide.md
```

### 4. Documentation Standards

- **Clear Descriptions**: Use healthcare terminology appropriately
- **Examples**: Provide realistic clinical examples
- **Edge Cases**: Document handling of unusual situations
- **Integration**: Explain how components work together
- **Updates**: Keep documentation current with code changes

## Testing Your Extensions

### 1. Unit Testing

Create tests for each component:

```python
# tests/test_your_extension.py
import pytest
from your_extension.tools import YourNewTool

class TestYourNewTool:
    
    def setup_method(self):
        self.tool = YourNewTool()
    
    def test_tool_basic_functionality(self):
        result = self.tool._run(
            test_input="sample clinical data"
        )
        assert "expected output element" in result
        
    def test_tool_error_handling(self):
        with pytest.raises(ValueError):
            self.tool._run(invalid_input="")
```

### 2. Integration Testing

Test how your extensions work with the existing system:

```python
def test_agent_with_new_tool():
    crew = HealthcareSimulationCrew()
    agent = crew.your_new_agent()
    
    # Test agent has access to required tools
    assert any(isinstance(tool, YourNewTool) for tool in agent.tools)
    
def test_new_task_in_workflow():
    crew = HealthcareSimulationCrew()
    tasks = crew.crew().tasks
    
    # Verify your task is included
    task_names = [task.description for task in tasks]
    assert any("your task description" in desc for desc in task_names)
```

### 3. Clinical Validation

Validate that your extensions produce clinically appropriate results:

```python
def test_clinical_accuracy():
    # Use real clinical scenarios
    sample_patient_data = load_sample_hl7_message("diabetes_patient")
    
    crew = HealthcareSimulationCrew()
    result = crew.crew().kickoff(inputs={"hl7_message": sample_patient_data})
    
    # Validate clinical appropriateness
    assert "evidence-based treatment" in result
    assert "drug interactions checked" in result
```

### 4. Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_your_extension.py

# Run with coverage
pytest --cov=your_extension

# Run integration tests
pytest tests/test_integration.py -v
```

## Contributing Your Extensions

When contributing extensions to the main repository:

1. **Follow Standards**: Use the patterns established in existing code
2. **Include Tests**: Provide comprehensive test coverage
3. **Document Thoroughly**: Update all relevant documentation
4. **Clinical Review**: Have extensions reviewed by healthcare professionals
5. **Performance Testing**: Ensure extensions don't degrade system performance

## Getting Help

- **Issues**: Open GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Documentation**: Check existing documentation first
- **Examples**: Review existing agents, tasks, and tools for patterns
- **Community**: Engage with other developers and healthcare professionals

## Conclusion

The healthcare simulation system is designed to be extensible and adaptable to various healthcare scenarios. By following these guidelines, you can add new capabilities while maintaining system integrity and clinical accuracy.

Remember that healthcare simulation carries responsibility for accuracy and safety. Always validate your extensions against current clinical guidelines and best practices.