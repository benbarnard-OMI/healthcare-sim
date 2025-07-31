# Agent Extension Guide

This guide focuses specifically on extending the healthcare simulation system with new agents representing different healthcare professionals and specialties.

## Understanding Healthcare Agents

Agents in the healthcare simulation system represent healthcare professionals with specific roles, expertise, and responsibilities. Each agent has:

- **Role**: Professional title and specialty area
- **Goal**: Specific objectives within the care pathway
- **Backstory**: Professional background that influences decision-making
- **Tools**: Specialized instruments and knowledge bases
- **Capabilities**: What the agent can do within the system

## Current Agent Architecture

The system currently includes 5 core agents:

1. **HL7 Data Ingestion Specialist** - Processes and validates patient data
2. **Clinical Diagnostics Analyst** - Analyzes symptoms and conditions
3. **Treatment Planning Specialist** - Develops treatment plans
4. **Patient Care Coordinator** - Manages workflow and communication
5. **Clinical Outcomes Analyst** - Monitors treatment effectiveness

## Step-by-Step Agent Creation

### Step 1: Define Your Agent's Healthcare Role

Before creating an agent, clearly define:

- **Medical Specialty**: What area of healthcare does this agent represent?
- **Scope of Practice**: What specific tasks and decisions can this agent make?
- **Expertise Level**: Primary care, specialist, subspecialist?
- **Care Setting**: Hospital, clinic, emergency department, etc.

### Step 2: Create Agent Configuration

Add your agent to `config/agents.yaml`:

```yaml
# Example: Emergency Medicine Physician
emergency_physician:
  role: >
    Emergency Medicine Physician
  goal: >
    Provide rapid assessment, stabilization, and initial management of acute medical conditions
    while determining appropriate disposition and care plans
  backstory: >
    You are an experienced emergency medicine physician with expertise in rapid clinical
    decision-making under pressure. You excel at triaging patients, performing focused
    assessments, and initiating time-sensitive interventions. Your training covers a broad
    spectrum of medical and surgical emergencies, and you're skilled at managing uncertainty
    while prioritizing patient safety. You work efficiently to stabilize patients and
    coordinate with appropriate specialists when needed.

# Example: Clinical Pharmacist
clinical_pharmacist:
  role: >
    Clinical Pharmacist
  goal: >
    Optimize medication therapy through comprehensive review, interaction screening,
    and dosing recommendations while ensuring patient safety and therapeutic efficacy
  backstory: >
    You are a clinical pharmacist with advanced training in pharmacokinetics, drug interactions,
    and medication therapy management. You specialize in reviewing complex medication regimens,
    identifying potential problems, and optimizing drug therapy for individual patients.
    Your expertise includes knowledge of drug allergies, contraindications, dose adjustments
    for organ dysfunction, and evidence-based treatment protocols. You work collaboratively
    with physicians to ensure safe and effective medication use.

# Example: Infection Control Specialist
infection_control_specialist:
  role: >
    Infection Prevention and Control Specialist
  goal: >
    Identify infection risks, implement prevention strategies, and guide antimicrobial
    stewardship to reduce healthcare-associated infections
  backstory: >
    You are an infection prevention and control specialist with deep knowledge of epidemiology,
    microbiology, and antimicrobial resistance patterns. You excel at identifying infection
    risks, investigating outbreaks, and implementing evidence-based prevention strategies.
    Your expertise includes surveillance systems, isolation precautions, sterilization
    processes, and antimicrobial stewardship. You work to protect patients and healthcare
    workers from healthcare-associated infections while promoting appropriate antimicrobial use.
```

### Step 3: Implement Agent in Code

Add the agent method to `crew.py`:

```python
@agent
def emergency_physician(self) -> Agent:
    """Emergency Medicine Physician agent for acute care scenarios."""
    return Agent(
        config=self.agents_config['emergency_physician'],
        tools=[
            self.healthcare_tools.clinical_guidelines,
            self.healthcare_tools.medication_interaction_checker,
            # Add emergency-specific tools as needed
        ],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=True,  # Can delegate to specialists
        max_iter=3,
        step_callback=self._agent_step_callback  # Optional: for monitoring
    )

@agent
def clinical_pharmacist(self) -> Agent:
    """Clinical Pharmacist agent for medication optimization."""
    return Agent(
        config=self.agents_config['clinical_pharmacist'],
        tools=[
            self.healthcare_tools.medication_interaction_checker,
            self.healthcare_tools.clinical_guidelines,
            # Add pharmacy-specific tools
        ],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=False,  # Typically provides recommendations
        max_iter=2
    )

@agent
def infection_control_specialist(self) -> Agent:
    """Infection Prevention and Control Specialist."""
    return Agent(
        config=self.agents_config['infection_control_specialist'],
        tools=[
            self.healthcare_tools.clinical_guidelines,
            # Add infection control specific tools
        ],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2
    )
```

### Step 4: Create Specialized Tools (If Needed)

If your agent requires specialized tools, add them to `tools/healthcare_tools.py`:

```python
class EmergencyTriageInput(BaseModel):
    """Input schema for emergency triage tool."""
    chief_complaint: str = Field(..., description="Patient's primary complaint")
    vital_signs: str = Field(..., description="Current vital signs")
    pain_scale: Optional[int] = Field(default=None, description="Pain scale 0-10")
    acuity_indicators: Optional[str] = Field(default=None, description="High acuity indicators")

class EmergencyTriageTool(BaseTool):
    name: str = "Emergency Triage Tool"
    description: str = "Perform emergency department triage using ESI criteria"
    args_schema: type[BaseModel] = EmergencyTriageInput

    def _run(self, chief_complaint: str, vital_signs: str, 
             pain_scale: Optional[int] = None, acuity_indicators: Optional[str] = None) -> str:
        """Perform emergency triage assessment."""
        
        # ESI (Emergency Severity Index) logic
        esi_level = 3  # Default to level 3
        
        # Level 1: Immediate life-threatening conditions
        critical_keywords = ['cardiac arrest', 'respiratory failure', 'shock', 'severe trauma']
        if any(keyword in chief_complaint.lower() for keyword in critical_keywords):
            esi_level = 1
            
        # Level 2: High risk situations or severe pain/distress
        elif acuity_indicators or (pain_scale and pain_scale >= 8):
            esi_level = 2
            
        # Level 4-5: Lower acuity based on resource needs
        elif 'minor' in chief_complaint.lower() or (pain_scale and pain_scale <= 3):
            esi_level = 4
            
        result = f"""
        EMERGENCY TRIAGE ASSESSMENT:
        Chief Complaint: {chief_complaint}
        Vital Signs: {vital_signs}
        Pain Scale: {pain_scale if pain_scale else 'Not assessed'}
        
        ESI LEVEL: {esi_level}
        
        Recommendations:
        {self._get_esi_recommendations(esi_level)}
        
        Next Steps:
        {self._get_next_steps(esi_level, chief_complaint)}
        """
        
        return result.strip()
    
    def _get_esi_recommendations(self, esi_level: int) -> str:
        recommendations = {
            1: "- Immediate physician evaluation\n- Continuous monitoring\n- Prepare for resuscitation",
            2: "- Physician evaluation within 10 minutes\n- Consider immediate interventions\n- Frequent reassessment",
            3: "- Physician evaluation within 30 minutes\n- Standard monitoring\n- Reassess if condition changes",
            4: "- Physician evaluation within 60 minutes\n- Basic monitoring\n- Patient education on return precautions",
            5: "- Physician evaluation within 120 minutes\n- Minimal monitoring required\n- Consider fast track if appropriate"
        }
        return recommendations.get(esi_level, "Standard assessment")
    
    def _get_next_steps(self, esi_level: int, chief_complaint: str) -> str:
        if esi_level <= 2:
            return "- Immediate room assignment\n- Notify attending physician\n- Prepare for potential procedures"
        elif esi_level == 3:
            return "- Room assignment when available\n- Order routine labs/imaging if indicated\n- Pain management as appropriate"
        else:
            return "- Waiting room appropriate\n- Routine triage protocols\n- Discharge planning if stable"
```

### Step 5: Agent Specialization Patterns

#### Pattern 1: Specialist Consultant Agent
```python
@agent
def cardiologist(self) -> Agent:
    """Cardiology consultant for cardiac conditions."""
    return Agent(
        config=self.agents_config['cardiologist'],
        tools=[
            self.healthcare_tools.clinical_guidelines,
            self.healthcare_tools.cardiac_risk_calculator,  # Specialized tool
        ],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=False,  # Provides expert recommendations
        max_iter=3
    )
```

#### Pattern 2: Procedure-Focused Agent
```python
@agent
def interventional_radiologist(self) -> Agent:
    """Interventional radiologist for procedure planning."""
    return Agent(
        config=self.agents_config['interventional_radiologist'],
        tools=[
            self.healthcare_tools.imaging_protocols,
            self.healthcare_tools.procedure_scheduler,
        ],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=True,  # May need other specialists
        max_iter=2
    )
```

#### Pattern 3: Care Coordination Agent
```python
@agent
def case_manager(self) -> Agent:
    """Case manager for care coordination and discharge planning."""
    return Agent(
        config=self.agents_config['case_manager'],
        tools=[
            self.healthcare_tools.insurance_verification,
            self.healthcare_tools.discharge_planner,
            self.healthcare_tools.community_resources,
        ],
        llm=self.llm_config.llm,
        verbose=True,
        allow_delegation=True,  # Coordinates with multiple services
        max_iter=4
    )
```

## Agent Interaction Patterns

### Hierarchical Relationships
```python
# Manager-subordinate relationship
@crew
def emergency_crew(self) -> Crew:
    return Crew(
        agents=[
            self.emergency_physician(),  # Manager
            self.emergency_nurse(),
            self.emergency_tech(),
        ],
        process=Process.hierarchical,
        manager_agent=self.emergency_physician(),
        verbose=True
    )
```

### Collaborative Relationships
```python
# Peer-to-peer collaboration
@crew
def multidisciplinary_crew(self) -> Crew:
    return Crew(
        agents=[
            self.attending_physician(),
            self.clinical_pharmacist(),
            self.case_manager(),
            self.infection_control_specialist(),
        ],
        process=Process.sequential,  # Or Process.collaborative
        verbose=True
    )
```

## Advanced Agent Features

### Custom Agent Behaviors

```python
class SpecializedHealthcareAgent(Agent):
    """Custom agent class with healthcare-specific behaviors."""
    
    def __init__(self, specialty: str, certification_level: str, **kwargs):
        super().__init__(**kwargs)
        self.specialty = specialty
        self.certification_level = certification_level
        self.consultation_requests = []
    
    def request_consultation(self, specialty: str, question: str):
        """Request consultation from another specialist."""
        self.consultation_requests.append({
            'specialty': specialty,
            'question': question,
            'timestamp': datetime.now()
        })
    
    def provide_consultation(self, question: str, patient_data: dict) -> str:
        """Provide specialist consultation response."""
        # Specialized consultation logic based on agent's specialty
        return f"Consultation response from {self.specialty}: ..."
```

### Dynamic Agent Assignment

```python
def assign_agents_by_condition(self, patient_condition: str) -> List[Agent]:
    """Dynamically assign agents based on patient condition."""
    agents = [self.data_ingestion_agent()]  # Always needed
    
    if "cardiac" in patient_condition.lower():
        agents.extend([
            self.cardiologist(),
            self.cardiac_nurse()
        ])
    elif "infection" in patient_condition.lower():
        agents.extend([
            self.infectious_disease_specialist(),
            self.infection_control_specialist()
        ])
    elif "surgical" in patient_condition.lower():
        agents.extend([
            self.surgeon(),
            self.anesthesiologist(),
            self.or_nurse()
        ])
    
    agents.append(self.care_coordinator())  # Always include
    return agents
```

## Agent Testing and Validation

### Unit Testing Agents

```python
import pytest
from unittest.mock import Mock, patch

class TestEmergencyPhysician:
    
    def setup_method(self):
        self.crew = HealthcareSimulationCrew()
        self.agent = self.crew.emergency_physician()
    
    def test_agent_configuration(self):
        """Test agent has correct configuration."""
        assert "Emergency Medicine Physician" in self.agent.role
        assert "rapid assessment" in self.agent.goal.lower()
        assert len(self.agent.tools) > 0
    
    def test_agent_tool_access(self):
        """Test agent has access to required tools."""
        tool_names = [tool.name for tool in self.agent.tools]
        assert "Clinical Guidelines Search" in tool_names
        
    @patch('crew.HealthcareSimulationCrew._execute_task')
    def test_agent_task_execution(self, mock_execute):
        """Test agent can execute tasks."""
        mock_execute.return_value = "Test result"
        
        # Create a simple task for testing
        task = Task(
            description="Assess emergency patient",
            agent=self.agent,
            expected_output="Assessment report"
        )
        
        result = task.execute()
        assert "Test result" in result
```

### Integration Testing

```python
def test_agent_collaboration():
    """Test how agents work together."""
    crew = HealthcareSimulationCrew()
    
    # Create a multi-agent scenario
    emergency_crew = Crew(
        agents=[
            crew.emergency_physician(),
            crew.clinical_pharmacist(),
        ],
        tasks=[
            crew.emergency_assessment(),
            crew.medication_review(),
        ],
        process=Process.sequential
    )
    
    # Test with sample patient data
    result = emergency_crew.kickoff(inputs={
        "patient_data": "Sample emergency patient data"
    })
    
    assert "assessment" in result.lower()
    assert "medication" in result.lower()
```

## Clinical Validation

### Evidence-Based Agent Behavior

Ensure your agents follow current clinical guidelines:

```python
def validate_clinical_accuracy(agent_output: str, condition: str) -> bool:
    """Validate agent output against clinical guidelines."""
    
    # Load relevant guidelines
    guidelines = load_clinical_guidelines(condition)
    
    # Check for evidence-based recommendations
    for guideline in guidelines:
        if guideline['recommendation'] not in agent_output:
            return False
    
    # Check for contraindicated recommendations
    contraindications = get_contraindications(condition)
    for contraindication in contraindications:
        if contraindication in agent_output:
            return False
    
    return True
```

### Professional Standards Compliance

```python
def check_scope_of_practice(agent: Agent, task_description: str) -> bool:
    """Ensure agent tasks align with professional scope of practice."""
    
    scope_definitions = {
        'nurse': ['assessment', 'monitoring', 'patient education', 'medication administration'],
        'physician': ['diagnosis', 'treatment planning', 'procedures', 'prescribing'],
        'pharmacist': ['medication review', 'drug interactions', 'dosing'],
        'therapist': ['rehabilitation', 'functional assessment', 'therapy planning']
    }
    
    agent_type = determine_agent_type(agent.role)
    allowed_activities = scope_definitions.get(agent_type, [])
    
    return any(activity in task_description.lower() for activity in allowed_activities)
```

## Best Practices for Agent Extension

### 1. Clinical Accuracy
- Base agent behaviors on current clinical guidelines
- Consult with healthcare professionals during development
- Include evidence-based decision-making patterns
- Regular updates to reflect changing standards of care

### 2. Professional Realism
- Respect scope of practice boundaries
- Include realistic time constraints and workflow pressures
- Model actual professional communication patterns
- Consider legal and ethical constraints

### 3. System Integration
- Ensure new agents work well with existing agents
- Maintain consistent communication protocols
- Plan for scalability and future extensions
- Document agent capabilities and limitations

### 4. Quality Assurance
- Include comprehensive testing scenarios
- Validate against real clinical cases
- Monitor agent performance over time
- Provide mechanisms for continuous improvement

## Common Pitfalls to Avoid

1. **Overly Broad Roles**: Keep agent responsibilities focused and realistic
2. **Unrealistic Expertise**: Don't make agents omniscient within their specialty  
3. **Poor Tool Selection**: Only provide tools relevant to the agent's role
4. **Inadequate Testing**: Test agents with diverse clinical scenarios
5. **Ignoring Constraints**: Consider real-world limitations and scope of practice

## Conclusion

Creating effective healthcare agents requires balancing technical implementation with clinical realism. Focus on authentic professional roles, evidence-based practices, and realistic workflow patterns. Always validate your agents against current healthcare standards and seek input from healthcare professionals when possible.