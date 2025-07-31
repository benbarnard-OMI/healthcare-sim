# Task Extension Guide

This guide focuses specifically on extending the healthcare simulation system with new tasks that represent different steps in healthcare workflows and care pathways.

## Understanding Healthcare Tasks

Tasks in the healthcare simulation system represent specific activities, decisions, or workflows that occur during patient care. Each task has:

- **Description**: What needs to be accomplished
- **Expected Output**: The format and content of results
- **Agent Assignment**: Which healthcare professional performs the task
- **Dependencies**: What information or prior tasks are required
- **Context**: How the task fits into the overall care pathway

## Current Task Architecture

The system currently includes 5 core tasks that form a complete care pathway:

1. **Ingest HL7 Data** - Parse and validate patient information
2. **Analyze Diagnostics** - Clinical assessment and diagnosis
3. **Create Treatment Plan** - Develop therapeutic interventions
4. **Coordinate Care** - Manage care workflow and scheduling
5. **Evaluate Outcomes** - Monitor treatment effectiveness

## Step-by-Step Task Creation

### Step 1: Define Your Healthcare Workflow

Before creating a task, clearly define:

- **Clinical Purpose**: What healthcare objective does this task serve?
- **Workflow Position**: Where does this fit in the care continuum?
- **Prerequisites**: What information or prior tasks are needed?
- **Deliverables**: What specific outputs should be produced?
- **Quality Measures**: How will success be measured?

### Step 2: Create Task Configuration

Add your task to `config/tasks.yaml`:

```yaml
# Example: Emergency Triage Task
perform_emergency_triage:
  description: >
    Perform emergency department triage assessment using ESI (Emergency Severity Index) criteria:
    - Evaluate patient acuity and stability
    - Assign appropriate triage level (ESI 1-5)
    - Determine resource requirements
    - Identify immediate interventions needed
    - Communicate triage decisions to care team
    - Document triage rationale and recommendations
  expected_output: >
    An emergency triage assessment containing:
    - ESI level assignment with rationale
    - Immediate interventions required
    - Recommended care pathway and timeline
    - Resource allocation needs
    - Communication plan for care team
    - Documentation of high-risk indicators
  agent: emergency_physician
  context:
    - ingest_hl7_data

# Example: Medication Reconciliation Task
reconcile_medications:
  description: >
    Conduct comprehensive medication reconciliation for patient admission:
    - Review all current medications including prescriptions, OTC, and supplements
    - Verify dosing, frequency, and administration routes
    - Identify discrepancies between home medications and hospital orders
    - Check for drug-drug interactions and contraindications
    - Assess appropriateness for current clinical condition
    - Document changes and rationale for modifications
  expected_output: >
    A medication reconciliation report containing:
    - Complete list of verified home medications
    - Identified discrepancies and resolutions
    - Drug interaction screening results
    - Recommendations for medication modifications
    - Patient counseling points
    - Care team communication summary
  agent: clinical_pharmacist
  context:
    - ingest_hl7_data
    - analyze_diagnostics

# Example: Discharge Planning Task
plan_discharge:
  description: >
    Develop comprehensive discharge plan ensuring safe transition from hospital to home:
    - Assess patient's functional status and support systems
    - Coordinate with community resources and follow-up providers
    - Arrange necessary medical equipment and services
    - Provide patient and family education
    - Schedule appropriate follow-up appointments
    - Ensure medication availability in community
    - Address social determinants of health barriers
  expected_output: >
    A discharge plan containing:
    - Post-discharge care requirements and timeline
    - Follow-up appointment schedule
    - Community resource coordination
    - Patient education materials provided
    - Medication management plan
    - Emergency contact information and return precautions
    - Social services referrals if needed
  agent: case_manager
  context:
    - ingest_hl7_data
    - analyze_diagnostics
    - create_treatment_plan
    - coordinate_care

# Example: Quality Improvement Task
assess_care_quality:
  description: >
    Evaluate care quality using established healthcare quality metrics:
    - Review adherence to evidence-based guidelines
    - Assess patient safety indicators and near-miss events
    - Evaluate care coordination effectiveness
    - Measure patient satisfaction and experience
    - Identify opportunities for improvement
    - Benchmark against quality standards
    - Generate recommendations for care enhancement
  expected_output: >
    A quality assessment report containing:
    - Adherence scores for relevant quality measures
    - Patient safety indicator analysis
    - Care coordination effectiveness metrics
    - Areas for improvement with specific recommendations
    - Benchmarking results against standards
    - Action plan for quality enhancement
  agent: quality_improvement_specialist
  context:
    - ingest_hl7_data
    - analyze_diagnostics
    - create_treatment_plan
    - coordinate_care
    - evaluate_outcomes
```

### Step 3: Implement Task in Code

Add the task method to `crew.py`:

```python
@task
def perform_emergency_triage(self) -> Task:
    """Emergency department triage assessment task."""
    return Task(
        config=self.tasks_config['perform_emergency_triage'],
        agent=self.emergency_physician(),
        tools=[self.healthcare_tools.emergency_triage_tool],
        output_file='emergency_triage_assessment.md'
    )

@task
def reconcile_medications(self) -> Task:
    """Medication reconciliation task."""
    return Task(
        config=self.tasks_config['reconcile_medications'],
        agent=self.clinical_pharmacist(),
        tools=[
            self.healthcare_tools.medication_interaction_checker,
            self.healthcare_tools.clinical_guidelines
        ],
        output_json=MedicationReconciliationOutput,  # Structured output
        output_file='medication_reconciliation.json'
    )

@task
def plan_discharge(self) -> Task:
    """Discharge planning task."""
    return Task(
        config=self.tasks_config['plan_discharge'],
        agent=self.case_manager(),
        tools=[
            self.healthcare_tools.appointment_scheduler,
            self.healthcare_tools.community_resources_locator
        ],
        async_execution=True,  # Can run in parallel with other tasks
        output_file='discharge_plan.md'
    )

@task
def assess_care_quality(self) -> Task:
    """Care quality assessment task."""
    return Task(
        config=self.tasks_config['assess_care_quality'],
        agent=self.quality_improvement_specialist(),
        tools=[self.healthcare_tools.quality_metrics_calculator],
        human_input=True,  # May require human review
        output_pydantic=QualityAssessmentReport  # Structured data model
    )
```

### Step 4: Define Structured Output Models (Optional)

For tasks requiring structured data, define Pydantic models:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MedicationReconciliationOutput(BaseModel):
    """Structured output for medication reconciliation."""
    reconciliation_date: datetime
    home_medications: List[dict]
    hospital_medications: List[dict]
    discrepancies: List[dict]
    interactions: List[dict]
    recommendations: List[str]
    counseling_points: List[str]

class QualityAssessmentReport(BaseModel):
    """Structured output for quality assessment."""
    assessment_date: datetime
    quality_measures: dict
    safety_indicators: dict
    improvement_opportunities: List[str]
    action_items: List[dict]
    benchmark_comparison: dict

class DischargeInstruction(BaseModel):
    """Individual discharge instruction."""
    category: str
    instruction: str
    priority: str = Field(default="routine")
    follow_up_required: bool = False

class DischargePlanOutput(BaseModel):
    """Structured discharge plan output."""
    patient_id: str
    discharge_date: datetime
    instructions: List[DischargeInstruction]
    follow_up_appointments: List[dict]
    medications: List[dict]
    equipment_needs: List[str]
    warning_signs: List[str]
```

### Step 5: Update Crew Workflow

Integrate your new tasks into the crew workflow:

```python
@crew
def crew(self) -> Crew:
    """Creates the comprehensive HealthcareSimulation crew"""
    return Crew(
        agents=self.agents,
        tasks=[
            # Core workflow
            self.ingest_hl7_data(),
            
            # Emergency-specific tasks
            self.perform_emergency_triage(),
            
            # Standard workflow continues
            self.analyze_diagnostics(),
            self.reconcile_medications(),  # New medication task
            self.create_treatment_plan(),
            self.coordinate_care(),
            self.plan_discharge(),  # New discharge task
            self.evaluate_outcomes(),
            
            # Quality improvement
            self.assess_care_quality(),  # New quality task
        ],
        process=Process.hierarchical,
        manager_agent=self.care_coordinator(),
        verbose=True
    )
```

## Task Specialization Patterns

### Pattern 1: Conditional Task Execution

```yaml
# Task that only executes under certain conditions
perform_cardiac_catheterization:
  description: >
    Perform cardiac catheterization if indicated by clinical assessment:
    - Review indication criteria (chest pain with positive stress test, STEMI, etc.)
    - If not indicated, document rationale for conservative management
    - If indicated, plan procedure timing and preparation
    - Coordinate with interventional cardiology team
    - Arrange pre-procedure testing and patient preparation
  expected_output: >
    Either:
    - Cardiac catheterization plan with procedure details and timeline, OR
    - Documentation of why procedure is not indicated with alternative plan
  agent: cardiologist
  context:
    - analyze_diagnostics
    - create_treatment_plan
```

### Pattern 2: Parallel Task Execution

```python
# Tasks that can run simultaneously
@crew
def parallel_assessment_crew(self) -> Crew:
    return Crew(
        agents=[
            self.internist(),
            self.clinical_pharmacist(),
            self.case_manager(),
        ],
        tasks=[
            self.assess_medical_conditions(),    # Can run in parallel
            self.reconcile_medications(),        # Can run in parallel  
            self.assess_social_needs(),         # Can run in parallel
        ],
        process=Process.sequential,  # Will auto-parallelize independent tasks
        verbose=True
    )
```

### Pattern 3: Iterative Task Refinement

```yaml
monitor_treatment_response:
  description: >
    Monitor patient response to treatment with iterative assessment:
    - Evaluate clinical indicators every 4-6 hours
    - Compare current status to baseline and treatment goals
    - Identify signs of improvement or deterioration
    - Adjust treatment plan based on response
    - Continue monitoring until stable or treatment goals met
    - Document response patterns and modifications made
  expected_output: >
    Treatment monitoring report with:
    - Timeline of clinical changes
    - Response to interventions
    - Treatment modifications made
    - Current clinical status
    - Recommendations for continued care
  agent: attending_physician
  context:
    - create_treatment_plan
  # This task may repeat multiple times
  max_iterations: 5
  iteration_criteria: "Continue until patient stable or treatment goals achieved"
```

### Pattern 4: Human-in-the-Loop Tasks

```python
@task
def complex_ethical_decision(self) -> Task:
    """Task requiring human input for ethical decisions."""
    return Task(
        config=self.tasks_config['complex_ethical_decision'],
        agent=self.ethics_consultant(),
        human_input=True,  # Requires human review
        async_execution=False,  # Must complete before proceeding
        context=[self.analyze_diagnostics(), self.assess_prognosis()]
    )
```

## Advanced Task Features

### Custom Task Validation

```python
class HealthcareTask(Task):
    """Custom task class with healthcare-specific validation."""
    
    def __init__(self, clinical_guidelines: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.clinical_guidelines = clinical_guidelines or {}
    
    def validate_output(self, output: str) -> bool:
        """Validate task output against clinical guidelines."""
        # Check for required elements
        required_elements = self.clinical_guidelines.get('required_elements', [])
        for element in required_elements:
            if element not in output.lower():
                return False
        
        # Check for contraindicated recommendations
        contraindications = self.clinical_guidelines.get('contraindications', [])
        for contraindication in contraindications:
            if contraindication in output.lower():
                return False
        
        return True
    
    def execute(self, context: str = None) -> str:
        """Execute task with validation."""
        output = super().execute(context)
        
        if not self.validate_output(output):
            # Request revision or escalate
            output = self.request_revision(output)
        
        return output
```

### Dynamic Task Creation

```python
def create_specialty_consultation_task(self, specialty: str, question: str) -> Task:
    """Dynamically create consultation tasks."""
    
    task_config = {
        'description': f"""
            Provide {specialty} consultation for the following question:
            {question}
            
            Include:
            - Specialist assessment of the clinical situation
            - Evidence-based recommendations
            - Suggested diagnostic workup if needed
            - Treatment recommendations within scope of specialty
            - Communication with referring team
        """,
        'expected_output': f"""
            {specialty} consultation note containing:
            - Clinical assessment from specialist perspective
            - Recommended diagnostic studies
            - Treatment recommendations
            - Follow-up plan
            - Communication with referring physician
        """,
        'agent': f'{specialty.lower()}_specialist'
    }
    
    return Task(
        description=task_config['description'],
        expected_output=task_config['expected_output'],
        agent=self.get_agent_by_specialty(specialty),
        tools=self.get_specialty_tools(specialty)
    )
```

### Task Monitoring and Metrics

```python
class TaskMetrics:
    """Track task performance and quality metrics."""
    
    def __init__(self):
        self.task_durations = {}
        self.quality_scores = {}
        self.error_rates = {}
    
    def record_task_completion(self, task_name: str, duration: float, 
                             quality_score: float, errors: int):
        """Record task completion metrics."""
        if task_name not in self.task_durations:
            self.task_durations[task_name] = []
            self.quality_scores[task_name] = []
            self.error_rates[task_name] = []
        
        self.task_durations[task_name].append(duration)
        self.quality_scores[task_name].append(quality_score)
        self.error_rates[task_name].append(errors)
    
    def get_task_performance_summary(self, task_name: str) -> dict:
        """Get performance summary for a task."""
        if task_name not in self.task_durations:
            return {}
        
        return {
            'avg_duration': sum(self.task_durations[task_name]) / len(self.task_durations[task_name]),
            'avg_quality': sum(self.quality_scores[task_name]) / len(self.quality_scores[task_name]),
            'avg_errors': sum(self.error_rates[task_name]) / len(self.error_rates[task_name]),
            'total_executions': len(self.task_durations[task_name])
        }
```

## Task Dependencies and Context Management

### Complex Dependency Patterns

```yaml
# Task with multiple conditional dependencies
create_surgical_plan:
  description: >
    Create comprehensive surgical plan based on assessment results:
    - If surgery indicated by diagnostics, proceed with surgical planning
    - Include pre-operative assessment and optimization
    - Plan surgical approach and technique
    - Coordinate with anesthesiology and nursing teams
    - Schedule surgery and arrange resources
    - Plan post-operative care pathway
    - If surgery not indicated, document rationale and alternative plan
  expected_output: >
    Surgical plan or alternative management plan with rationale
  agent: surgeon
  context:
    - analyze_diagnostics
    - assess_surgical_candidacy  # Custom conditional task
    - optimize_medical_conditions  # May be required first
  conditional_execution:
    condition: "surgery_indicated == true"
    alternative_agent: "medical_specialist"
```

### Context Transformation

```python
def transform_context_for_task(self, raw_context: dict, task_name: str) -> dict:
    """Transform context data for specific task requirements."""
    
    transformations = {
        'medication_reconciliation': self._extract_medication_data,
        'discharge_planning': self._extract_discharge_relevant_data,
        'quality_assessment': self._extract_quality_metrics_data
    }
    
    transformer = transformations.get(task_name, lambda x: x)
    return transformer(raw_context)

def _extract_medication_data(self, context: dict) -> dict:
    """Extract medication-relevant data from context."""
    return {
        'current_medications': context.get('medications', []),
        'allergies': context.get('allergies', []),
        'diagnoses': context.get('diagnoses', []),
        'lab_results': context.get('labs', {}),
        'patient_age': context.get('demographics', {}).get('age'),
        'kidney_function': context.get('labs', {}).get('creatinine')
    }
```

## Task Testing and Validation

### Unit Testing Tasks

```python
import pytest
from unittest.mock import Mock, patch

class TestMedicationReconciliation:
    
    def setup_method(self):
        self.crew = HealthcareSimulationCrew()
        self.task = self.crew.reconcile_medications()
    
    def test_task_configuration(self):
        """Test task has correct configuration."""
        assert "medication reconciliation" in self.task.description.lower()
        assert isinstance(self.task.agent, Agent)
        assert len(self.task.tools) > 0
    
    def test_task_context_requirements(self):
        """Test task has required context dependencies."""
        expected_context = ['ingest_hl7_data', 'analyze_diagnostics']
        for ctx in expected_context:
            assert ctx in [t.description for t in self.task.context]
    
    @patch('crew.HealthcareSimulationCrew.clinical_pharmacist')
    def test_task_execution(self, mock_agent):
        """Test task execution with mock agent."""
        mock_agent.return_value.execute_task.return_value = "Mock reconciliation result"
        
        context = {
            'patient_medications': ['Metformin 1000mg BID', 'Lisinopril 10mg daily'],
            'diagnoses': ['Type 2 Diabetes', 'Hypertension']
        }
        
        result = self.task.execute(context=context)
        assert "reconciliation" in result.lower()
```

### Integration Testing Task Workflows

```python
def test_complete_workflow():
    """Test complete task workflow execution."""
    crew = HealthcareSimulationCrew()
    
    # Define complete workflow
    workflow_tasks = [
        crew.ingest_hl7_data(),
        crew.perform_emergency_triage(),
        crew.analyze_diagnostics(),
        crew.reconcile_medications(),
        crew.create_treatment_plan(),
        crew.coordinate_care(),
        crew.evaluate_outcomes()
    ]
    
    test_crew = Crew(
        agents=crew.agents,
        tasks=workflow_tasks,
        process=Process.sequential
    )
    
    # Execute with test data
    result = test_crew.kickoff(inputs={
        "hl7_message": load_test_hl7_message("emergency_patient")
    })
    
    # Validate workflow completion
    assert all(task_name in result for task_name in [
        'triage', 'diagnosis', 'medication', 'treatment', 'coordination'
    ])
```

### Clinical Validation

```python
def validate_task_clinical_accuracy(task_name: str, output: str, 
                                  condition: str) -> dict:
    """Validate task output for clinical accuracy."""
    
    validation_results = {
        'evidence_based': False,
        'guidelines_compliant': False,
        'safety_appropriate': True,
        'completeness_score': 0.0,
        'recommendations': []
    }
    
    # Load clinical guidelines for condition
    guidelines = load_clinical_guidelines(condition)
    
    # Check evidence-based recommendations
    evidence_keywords = guidelines.get('evidence_keywords', [])
    validation_results['evidence_based'] = any(
        keyword in output.lower() for keyword in evidence_keywords
    )
    
    # Check guideline compliance
    required_elements = guidelines.get('required_elements', [])
    present_elements = sum(1 for element in required_elements 
                          if element in output.lower())
    validation_results['completeness_score'] = present_elements / len(required_elements)
    
    # Check for safety issues
    safety_contraindications = guidelines.get('contraindications', [])
    for contraindication in safety_contraindications:
        if contraindication in output.lower():
            validation_results['safety_appropriate'] = False
            validation_results['recommendations'].append(
                f"Remove contraindicated recommendation: {contraindication}"
            )
    
    return validation_results
```

## Best Practices for Task Extension

### 1. Clinical Workflow Alignment
- Map tasks to actual healthcare workflows
- Consider timing and sequencing constraints
- Include realistic decision points and branching
- Account for emergency vs. routine pathways

### 2. Clear Task Boundaries
- Define specific, measurable objectives
- Avoid overly broad or complex tasks
- Ensure tasks align with agent capabilities
- Plan for task interdependencies

### 3. Quality and Safety
- Include quality checkpoints and validation
- Build in safety checks and contraindication screening
- Plan for error handling and escalation
- Consider patient safety in all task designs

### 4. Flexibility and Adaptability
- Design tasks to handle various clinical scenarios
- Include conditional logic for different pathways
- Plan for iterative refinement based on outcomes
- Enable dynamic task modification when needed

## Common Pitfalls to Avoid

1. **Overly Complex Tasks**: Keep tasks focused and manageable
2. **Missing Dependencies**: Ensure all required context is available
3. **Unrealistic Timing**: Consider actual healthcare workflow constraints
4. **Poor Output Definition**: Specify clear, measurable outputs
5. **Inadequate Error Handling**: Plan for exceptions and edge cases

## Conclusion

Effective healthcare task design requires understanding both clinical workflows and technical implementation. Focus on realistic healthcare processes, clear dependencies, and measurable outcomes. Always validate tasks against current clinical practices and consider patient safety implications.