from typing import Dict, Any, Optional
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew, before_kickoff
from hl7apy import parser as hl7_parser
from tools.healthcare_tools import HealthcareTools
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define a constant for unknown patient ID
UNKNOWN_PATIENT_ID = "UNKNOWN_PATIENT_ID"
logger = logging.getLogger(__name__)

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
        """
        Validates the incoming HL7 message, extracts essential patient information,
        and prepares the data for the simulation kickoff.
        This method attempts to parse the HL7 message using hl7apy and falls back
        to basic string parsing for patient ID if the primary parsing fails.
        Validation issues encountered during parsing are stored in self.validation_issues.
        """
        if not inputs.get('hl7_message'):
            raise ValueError("HL7 message is required to start simulation")
        
        # Primary attempt to parse the HL7 message using the hl7apy library.
        # This allows for structured extraction of various HL7 segments and fields.
        try:
            parsed_message = hl7_parser.parse_message(
                inputs['hl7_message'], 
                validation_level=2  # Standard validation level
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
            self.validation_issues.append({
                'error_type': type(e).__name__,
                'message': str(e),
                'details': 'Primary HL7 parsing failed'
            })

            # Fallback mechanism: If primary parsing fails, attempt to extract at least the patient ID.
            # This is crucial for allowing the simulation to proceed with a minimal identifier,
            # even if the full message structure is problematic.
            if 'patient_id' not in inputs:
                try:
                    # Simple string parsing as a last resort to find PID segment and extract ID.
                    lines = inputs['hl7_message'].strip().split('\n')
                    pid_found_in_fallback = False
                    for line in lines:
                        if line.startswith('PID'):
                            fields = line.split('|')
                            # PID-3 (Patient Identifier List) is a common field for patient IDs.
                            # We target the first component (PID-3.1) if available.
                            if len(fields) > 3 and fields[3]: # Check if PID-3 exists and is not empty
                                pid_parts = fields[3].split('^') # ID is often the first component
                                if pid_parts and pid_parts[0]: # Check if the first component exists and is not empty
                                    inputs['patient_id'] = pid_parts[0]
                                    pid_found_in_fallback = True
                                    break
                    if not pid_found_in_fallback:
                        # This case handles if PID line was not found or ID was not extracted in fallback.
                        raise ValueError("PID line not found or Patient ID not extracted in fallback string parsing.")

                except Exception as fallback_exception:
                    # If fallback parsing also fails, log the issue and assign a generic unknown ID.
                    self.validation_issues.append({
                        'error_type': 'FallbackParsingError',
                        'message': 'Failed to extract patient ID via fallback string parsing mechanism.',
                        'details': str(fallback_exception)
                    })
                    # UNKNOWN_PATIENT_ID is used when no identifier can be extracted,
                    # allowing the system to acknowledge the processing attempt but flag missing data.
                    inputs['patient_id'] = UNKNOWN_PATIENT_ID

            # Final check: Ensure patient_id is set, even if all attempts failed.
            if 'patient_id' not in inputs or not inputs['patient_id']:
                inputs['patient_id'] = UNKNOWN_PATIENT_ID # Assign unknown if still not set.
                # Log that patient_id was ultimately not found and set to UNKNOWN.
                # This condition might be met if the initial 'try' failed very early,
                # and the fallback was either not triggered or also failed to set the patient_id.
                already_logged_unknown_final_check = any(
                    issue.get('error_type') == 'PatientIDNotFoundError' and
                    "Initial parsing and fallback mechanism failed" in issue.get('details', '')
                    for issue in self.validation_issues
                )
                if not already_logged_unknown_final_check: # Avoid duplicate generic messages
                     self.validation_issues.append({
                        'error_type': 'PatientIDNotFoundError', # Standardized error type
                        'message': 'Patient ID could not be determined after all parsing attempts and was set to UNKNOWN_PATIENT_ID.',
                        'details': 'Initial HL7 parsing failed, and fallback mechanism also failed to yield a patient ID.'
                    })

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
