from typing import Dict, Any, Optional
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew, before_kickoff
from hl7apy import parser as hl7_parser
from tools.healthcare_tools import HealthcareTools
import json

@CrewBase
class HealthcareSimulationCrew:
    """Synthetic Care Pathway Simulator using CrewAI"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.patient_data = {}
        self.validation_issues = []
        
        # Initialize healthcare tools
        self.healthcare_tools = HealthcareTools()

    @before_kickoff
    def prepare_simulation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs and prepare patient data before simulation."""
        if not inputs.get('hl7_message'):
            raise ValueError("HL7 message is required to start simulation")
        
        # Parse and validate the HL7 message using hl7apy
        try:
            parsed_message = hl7_parser.parse_message(
                inputs['hl7_message'], 
                validation_level=2  # Increase validation level
            )
            
            # Extract patient demographics from PID segment
            pid = parsed_message.PID
            patient_id = str(pid.patient_identifier_list.id_number)
            
            # Extract more patient information when available
            patient_info = {
                'id': patient_id,
                'name': f"{pid.patient_name.family_name}^{pid.patient_name.given_name}",
                'dob': str(pid.date_time_of_birth.time),
                'gender': str(pid.administrative_sex.value),
                'address': str(pid.patient_address.street_address) if hasattr(pid, 'patient_address') else "Unknown"
            }
            
            # Extract diagnostic information
            diagnoses = []
            if hasattr(parsed_message, 'DG1'):
                for dg1 in parsed_message.DG1:
                    diagnoses.append({
                        'code': str(dg1.diagnosis_code.identifier),
                        'coding_system': str(dg1.diagnosis_coding_method.value),
                        'description': str(dg1.diagnosis_description.value),
                        'date': str(dg1.diagnosis_date_time.time)
                    })
            
            # Store the structured data
            inputs['patient_id'] = patient_id
            inputs['patient_info'] = patient_info
            inputs['diagnoses'] = diagnoses
            inputs['full_message'] = parsed_message.to_er7()
            
            # Save for later use
            self.patient_data = {
                'patient_info': patient_info,
                'diagnoses': diagnoses,
                'message': parsed_message
            }
            
        except Exception as e:
            self.validation_issues.append(str(e))
            # Don't fail immediately, try to extract what we can
            if 'patient_id' not in inputs:
                # Try to extract patient ID using fallback method
                try:
                    # Simple string parsing as last resort
                    lines = inputs['hl7_message'].strip().split('\n')
                    for line in lines:
                        if line.startswith('PID'):
                            fields = line.split('|')
                            if len(fields) > 3:
                                pid_parts = fields[3].split('^')
                                if pid_parts:
                                    inputs['patient_id'] = pid_parts[0]
                                    break
                except:
                    # If all parsing fails, use a placeholder
                    inputs['patient_id'] = "UNKNOWN"
                    
            inputs['validation_errors'] = self.validation_issues
            
        return inputs

    @agent
    def data_ingestion_agent(self) -> Agent:
        """Creates the HL7 Data Ingestion Specialist agent."""
        return Agent(
            config=self.agents_config['data_ingestion_agent'],
            verbose=True
        )

    @agent
    def diagnostics_agent(self) -> Agent:
        """Creates the Clinical Diagnostics Analyst agent."""
        return Agent(
            config=self.agents_config['diagnostics_agent'],
            verbose=True,
            tools=[self.healthcare_tools.clinical_guidelines_tool()]
        )

    @agent
    def treatment_planner(self) -> Agent:
        """Creates the Treatment Planning Specialist agent."""
        return Agent(
            config=self.agents_config['treatment_planner'],
            verbose=True,
            tools=[
                self.healthcare_tools.clinical_guidelines_tool(),
                self.healthcare_tools.medication_interaction_tool()
            ]
        )

    @agent
    def care_coordinator(self) -> Agent:
        """Creates the Patient Care Coordinator agent (acts as manager)."""
        coordinator = Agent(
            config=self.agents_config['care_coordinator'],
            verbose=True,
            allow_delegation=True,  # Enable delegation for the manager role
            tools=[self.healthcare_tools.appointment_scheduler_tool()]
        )
        return coordinator

    @agent
    def outcome_evaluator(self) -> Agent:
        """Creates the Clinical Outcomes Analyst agent."""
        return Agent(
            config=self.agents_config['outcome_evaluator'],
            verbose=True
        )

    @task
    def ingest_hl7_data(self) -> Task:
        """Task for parsing and validating HL7 data."""
        return Task(
            config=self.tasks_config['ingest_hl7_data']
        )

    @task
    def analyze_diagnostics(self) -> Task:
        """Task for diagnostic analysis."""
        return Task(
            config=self.tasks_config['analyze_diagnostics']
        )

    @task 
    def create_treatment_plan(self) -> Task:
        """Task for treatment planning."""
        return Task(
            config=self.tasks_config['create_treatment_plan']
        )

    @task
    def coordinate_care(self) -> Task:
        """Task for care coordination."""
        return Task(
            config=self.tasks_config['coordinate_care']
        )

    @task
    def evaluate_outcomes(self) -> Task:
        """Task for outcome evaluation."""
        return Task(
            config=self.tasks_config['evaluate_outcomes']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Healthcare Simulation crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,  # Use hierarchical process with care coordinator as manager
            manager_agent=self.care_coordinator(),
            verbose=True
        )