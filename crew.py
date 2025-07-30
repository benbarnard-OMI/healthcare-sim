from typing import Dict, Any, Optional, List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew, before_kickoff
from hl7apy import parser as hl7_parser
from tools.healthcare_tools import HealthcareTools
from llm_config import LLMConfig, create_llm_config
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

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.patient_data = {}
        self.validation_issues = []
        
        # Initialize LLM configuration
        self.llm_config = llm_config or create_llm_config()
        logger.info(f"Initialized with LLM backend: {self.llm_config}")
        
        # Initialize healthcare tools
        self.healthcare_tools = HealthcareTools()
        
        # Storage for dynamically added agents and tasks
        self._dynamic_agents = {}
        self._dynamic_tasks = {}
        
        # Load configuration files
        import yaml
        with open(self.agents_config, 'r') as f:
            self._agents_config = yaml.safe_load(f)
        with open(self.tasks_config, 'r') as f:
            self._tasks_config = yaml.safe_load(f)

    def _extract_observations(self, parsed_message) -> List[Dict[str, Any]]:
        """Extract observation/lab results from OBX segments."""
        observations = []
        if hasattr(parsed_message, 'OBX'):
            obx_segments = parsed_message.OBX if isinstance(parsed_message.OBX, list) else [parsed_message.OBX]
            for obx in obx_segments:
                try:
                    obs_data = {
                        'set_id': str(obx.set_id_obx.value) if hasattr(obx, 'set_id_obx') and obx.set_id_obx.value else '',
                        'value_type': str(obx.value_type.value) if hasattr(obx, 'value_type') and obx.value_type.value else '',
                        'observation_identifier': str(obx.observation_identifier.identifier.value) if hasattr(obx, 'observation_identifier') else '',
                        'observation_description': str(obx.observation_identifier.text.value) if hasattr(obx, 'observation_identifier') and hasattr(obx.observation_identifier, 'text') else '',
                        'observation_value': str(obx.observation_value.value) if hasattr(obx, 'observation_value') and obx.observation_value.value else '',
                        'units': str(obx.units.identifier.value) if hasattr(obx, 'units') and hasattr(obx.units, 'identifier') else '',
                        'reference_range': str(obx.references_range.value) if hasattr(obx, 'references_range') and obx.references_range.value else '',
                        'abnormal_flags': str(obx.abnormal_flags.value) if hasattr(obx, 'abnormal_flags') and obx.abnormal_flags.value else '',
                        'observation_result_status': str(obx.observation_result_status.value) if hasattr(obx, 'observation_result_status') and obx.observation_result_status.value else ''
                    }
                    observations.append(obs_data)
                except Exception as e:
                    self.validation_issues.append({
                        'error_type': 'OBXParsingError',
                        'message': f'Failed to parse OBX segment: {str(e)}',
                        'details': f'OBX segment data extraction failed for set_id {getattr(obx, "set_id_obx", "unknown")}'
                    })
        return observations

    def _extract_visit_info(self, parsed_message) -> Dict[str, Any]:
        """Extract patient visit information from PV1 segment."""
        visit_info = {}
        if hasattr(parsed_message, 'PV1'):
            pv1 = parsed_message.PV1
            try:
                visit_info = {
                    'set_id': str(pv1.set_id_pv1.value) if hasattr(pv1, 'set_id_pv1') and pv1.set_id_pv1.value else '',
                    'patient_class': str(pv1.patient_class.value) if hasattr(pv1, 'patient_class') and pv1.patient_class.value else '',
                    'assigned_patient_location': str(pv1.assigned_patient_location.point_of_care.value) if hasattr(pv1, 'assigned_patient_location') and hasattr(pv1.assigned_patient_location, 'point_of_care') else '',
                    'room': str(pv1.assigned_patient_location.room.value) if hasattr(pv1, 'assigned_patient_location') and hasattr(pv1.assigned_patient_location, 'room') else '',
                    'bed': str(pv1.assigned_patient_location.bed.value) if hasattr(pv1, 'assigned_patient_location') and hasattr(pv1.assigned_patient_location, 'bed') else '',
                    'attending_doctor': str(pv1.attending_doctor.id_number.value) if hasattr(pv1, 'attending_doctor') and hasattr(pv1.attending_doctor, 'id_number') else '',
                    'attending_doctor_name': f"{pv1.attending_doctor.family_name.value}^{pv1.attending_doctor.given_name.value}" if hasattr(pv1, 'attending_doctor') and hasattr(pv1.attending_doctor, 'family_name') else '',
                    'hospital_service': str(pv1.hospital_service.value) if hasattr(pv1, 'hospital_service') and pv1.hospital_service.value else '',
                    'admission_type': str(pv1.admission_type.value) if hasattr(pv1, 'admission_type') and pv1.admission_type.value else '',
                    'admit_date_time': str(pv1.admit_date_time.time) if hasattr(pv1, 'admit_date_time') and pv1.admit_date_time.time else ''
                }
            except Exception as e:
                self.validation_issues.append({
                    'error_type': 'PV1ParsingError',
                    'message': f'Failed to parse PV1 segment: {str(e)}',
                    'details': 'PV1 segment data extraction failed'
                })
        return visit_info

    def _extract_procedures(self, parsed_message) -> List[Dict[str, Any]]:
        """Extract procedure information from PR1 segments."""
        procedures = []
        if hasattr(parsed_message, 'PR1'):
            pr1_segments = parsed_message.PR1 if isinstance(parsed_message.PR1, list) else [parsed_message.PR1]
            for pr1 in pr1_segments:
                try:
                    proc_data = {
                        'set_id': str(pr1.set_id_pr1.value) if hasattr(pr1, 'set_id_pr1') and pr1.set_id_pr1.value else '',
                        'procedure_coding_method': str(pr1.procedure_coding_method.value) if hasattr(pr1, 'procedure_coding_method') and pr1.procedure_coding_method.value else '',
                        'procedure_code': str(pr1.procedure_code.identifier.value) if hasattr(pr1, 'procedure_code') and hasattr(pr1.procedure_code, 'identifier') else '',
                        'procedure_description': str(pr1.procedure_description.value) if hasattr(pr1, 'procedure_description') and pr1.procedure_description.value else '',
                        'procedure_date_time': str(pr1.procedure_date_time.time) if hasattr(pr1, 'procedure_date_time') and pr1.procedure_date_time.time else '',
                        'procedure_functional_type': str(pr1.procedure_functional_type.value) if hasattr(pr1, 'procedure_functional_type') and pr1.procedure_functional_type.value else '',
                        'surgeon_id': str(pr1.surgeon.id_number.value) if hasattr(pr1, 'surgeon') and hasattr(pr1.surgeon, 'id_number') else '',
                        'surgeon_name': f"{pr1.surgeon.family_name.value}^{pr1.surgeon.given_name.value}" if hasattr(pr1, 'surgeon') and hasattr(pr1.surgeon, 'family_name') else ''
                    }
                    procedures.append(proc_data)
                except Exception as e:
                    self.validation_issues.append({
                        'error_type': 'PR1ParsingError',
                        'message': f'Failed to parse PR1 segment: {str(e)}',
                        'details': f'PR1 segment data extraction failed for set_id {getattr(pr1, "set_id_pr1", "unknown")}'
                    })
        return procedures

    def _validate_segment_data(self, segment_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate extracted segment data and return validation issues."""
        validation_issues = []
        
        if segment_type == 'PID':
            # Validate patient demographics
            if not data.get('id'):
                validation_issues.append({
                    'error_type': 'ValidationError',
                    'message': 'Patient ID is missing',
                    'details': 'PID segment must contain a valid patient identifier'
                })
            if not data.get('name') or data.get('name') == '^':
                validation_issues.append({
                    'error_type': 'ValidationWarning',
                    'message': 'Patient name is missing or incomplete',
                    'details': 'PID segment should contain patient name information'
                })
            if not data.get('dob'):
                validation_issues.append({
                    'error_type': 'ValidationWarning',
                    'message': 'Patient date of birth is missing',
                    'details': 'PID segment should contain date of birth for clinical context'
                })
        
        elif segment_type == 'OBX':
            # Validate observations
            for obs in data if isinstance(data, list) else [data]:
                if not obs.get('observation_identifier'):
                    validation_issues.append({
                        'error_type': 'ValidationWarning',
                        'message': 'Observation identifier is missing',
                        'details': f'OBX segment set_id {obs.get("set_id", "unknown")} lacks proper identifier'
                    })
                if not obs.get('observation_value'):
                    validation_issues.append({
                        'error_type': 'ValidationWarning',
                        'message': 'Observation value is missing',
                        'details': f'OBX segment set_id {obs.get("set_id", "unknown")} lacks observation value'
                    })
        
        return validation_issues

    def _fallback_parse_segments(self, hl7_message: str) -> Dict[str, Any]:
        """Fallback parsing using string operations when hl7apy fails."""
        fallback_data = {
            'patient_info': {},
            'diagnoses': [],
            'observations': [],
            'visit_info': {},
            'procedures': []
        }
        
        lines = hl7_message.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            fields = line.split('|')
            segment_type = fields[0]
            
            try:
                if segment_type == 'PID' and len(fields) > 3:
                    # Extract basic patient info
                    patient_id = fields[3].split('^')[0] if fields[3] else ''
                    name_parts = fields[5].split('^') if len(fields) > 5 and fields[5] else []
                    name = f"{name_parts[0]}^{name_parts[1]}" if len(name_parts) >= 2 else fields[5]
                    
                    fallback_data['patient_info'] = {
                        'id': patient_id,
                        'name': name,
                        'dob': fields[7] if len(fields) > 7 else '',
                        'gender': fields[8] if len(fields) > 8 else '',
                        'address': fields[11] if len(fields) > 11 else 'Unknown'
                    }
                
                elif segment_type == 'DG1' and len(fields) > 4:
                    # Extract diagnosis info
                    fallback_data['diagnoses'].append({
                        'code': fields[3] if fields[3] else '',
                        'coding_system': fields[2] if fields[2] else '',
                        'description': fields[4] if fields[4] else '',
                        'date': fields[5] if len(fields) > 5 else ''
                    })
                
                elif segment_type == 'OBX' and len(fields) > 5:
                    # Extract observation info
                    identifier_parts = fields[3].split('^') if fields[3] else []
                    fallback_data['observations'].append({
                        'set_id': fields[1] if fields[1] else '',
                        'value_type': fields[2] if fields[2] else '',
                        'observation_identifier': identifier_parts[0] if identifier_parts else '',
                        'observation_description': identifier_parts[1] if len(identifier_parts) > 1 else '',
                        'observation_value': fields[5] if fields[5] else '',
                        'units': fields[6] if len(fields) > 6 else '',
                        'reference_range': fields[7] if len(fields) > 7 else '',
                        'abnormal_flags': fields[8] if len(fields) > 8 else '',
                        'observation_result_status': fields[11] if len(fields) > 11 else ''
                    })
                
                elif segment_type == 'PV1' and len(fields) > 3:
                    # Extract visit info
                    location_parts = fields[3].split('^') if fields[3] else []
                    doctor_parts = fields[7].split('^') if len(fields) > 7 and fields[7] else []
                    
                    fallback_data['visit_info'] = {
                        'set_id': fields[1] if fields[1] else '',
                        'patient_class': fields[2] if fields[2] else '',
                        'assigned_patient_location': location_parts[0] if location_parts else '',
                        'room': location_parts[1] if len(location_parts) > 1 else '',
                        'bed': location_parts[2] if len(location_parts) > 2 else '',
                        'attending_doctor': doctor_parts[0] if doctor_parts else '',
                        'attending_doctor_name': f"{doctor_parts[1]}^{doctor_parts[2]}" if len(doctor_parts) > 2 else '',
                        'hospital_service': fields[10] if len(fields) > 10 else '',
                        'admission_type': fields[18] if len(fields) > 18 else '',
                        'admit_date_time': fields[44] if len(fields) > 44 else ''
                    }
                
                elif segment_type == 'PR1' and len(fields) > 4:
                    # Extract procedure info
                    code_parts = fields[3].split('^') if fields[3] else []
                    surgeon_parts = fields[11].split('^') if len(fields) > 11 and fields[11] else []
                    
                    fallback_data['procedures'].append({
                        'set_id': fields[1] if fields[1] else '',
                        'procedure_coding_method': fields[2] if fields[2] else '',
                        'procedure_code': code_parts[0] if code_parts else '',
                        'procedure_description': code_parts[1] if len(code_parts) > 1 else '',
                        'procedure_date_time': fields[5] if len(fields) > 5 else '',
                        'procedure_functional_type': fields[6] if len(fields) > 6 else '',
                        'surgeon_id': surgeon_parts[0] if surgeon_parts else '',
                        'surgeon_name': f"{surgeon_parts[1]}^{surgeon_parts[2]}" if len(surgeon_parts) > 2 else ''
                    })
                    
            except Exception as e:
                self.validation_issues.append({
                    'error_type': 'FallbackParsingError',
                    'message': f'Failed to parse {segment_type} segment in fallback mode: {str(e)}',
                    'details': f'Fallback parsing error for segment: {line[:50]}...'
                })
        
        return fallback_data

    @before_kickoff
    def prepare_simulation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced HL7 message validation and parsing with support for additional segments.
        Extracts patient information, diagnoses, observations, visit info, and procedures.
        Provides comprehensive error handling and validation with fallback mechanisms.
        """
        if not inputs.get('hl7_message'):
            raise ValueError("HL7 message is required to start simulation")
        
        # Reset validation issues for this parsing session
        self.validation_issues = []
        
        # Primary attempt to parse the HL7 message using the hl7apy library
        try:
            parsed_message = hl7_parser.parse_message(
                inputs['hl7_message'], 
                validation_level=2  # Standard validation level
            )
            
            # Extract patient demographics from PID segment
            pid = parsed_message.PID
            patient_id = str(pid.patient_identifier_list.id_number)
            
            # Extract comprehensive patient information
            patient_info = {
                'id': patient_id,
                'name': f"{pid.patient_name.family_name}^{pid.patient_name.given_name}",
                'dob': str(pid.date_time_of_birth.time),
                'gender': str(pid.administrative_sex.value),
                'address': str(pid.patient_address.street_address) if hasattr(pid, 'patient_address') and hasattr(pid.patient_address, 'street_address') else "Unknown",
                'phone': str(pid.phone_number_home.value) if hasattr(pid, 'phone_number_home') and pid.phone_number_home.value else '',
                'ssn': str(pid.ssn_number_patient.value) if hasattr(pid, 'ssn_number_patient') and pid.ssn_number_patient.value else ''
            }
            
            # Validate patient information
            pid_validation_issues = self._validate_segment_data('PID', patient_info)
            self.validation_issues.extend(pid_validation_issues)
            
            # Extract diagnostic information from DG1 segments
            diagnoses = []
            if hasattr(parsed_message, 'DG1'):
                dg1_segments = parsed_message.DG1 if isinstance(parsed_message.DG1, list) else [parsed_message.DG1]
                for dg1 in dg1_segments:
                    try:
                        diagnosis = {
                            'set_id': str(dg1.set_id_dg1.value) if hasattr(dg1, 'set_id_dg1') and dg1.set_id_dg1.value else '',
                            'code': str(dg1.diagnosis_code.identifier.value) if hasattr(dg1, 'diagnosis_code') and hasattr(dg1.diagnosis_code, 'identifier') else '',
                            'coding_system': str(dg1.diagnosis_coding_method.value) if hasattr(dg1, 'diagnosis_coding_method') and dg1.diagnosis_coding_method.value else '',
                            'description': str(dg1.diagnosis_description.value) if hasattr(dg1, 'diagnosis_description') and dg1.diagnosis_description.value else '',
                            'date': str(dg1.diagnosis_date_time.time) if hasattr(dg1, 'diagnosis_date_time') and dg1.diagnosis_date_time.time else '',
                            'type': str(dg1.diagnosis_type.value) if hasattr(dg1, 'diagnosis_type') and dg1.diagnosis_type.value else ''
                        }
                        diagnoses.append(diagnosis)
                    except Exception as e:
                        self.validation_issues.append({
                            'error_type': 'DG1ParsingError',
                            'message': f'Failed to parse DG1 segment: {str(e)}',
                            'details': f'DG1 segment data extraction failed for set_id {getattr(dg1, "set_id_dg1", "unknown")}'
                        })
            
            # Extract observations from OBX segments
            observations = self._extract_observations(parsed_message)
            obx_validation_issues = self._validate_segment_data('OBX', observations)
            self.validation_issues.extend(obx_validation_issues)
            
            # Extract visit information from PV1 segment
            visit_info = self._extract_visit_info(parsed_message)
            
            # Extract procedures from PR1 segments
            procedures = self._extract_procedures(parsed_message)
            
            # Store the structured data
            inputs['patient_id'] = patient_id
            inputs['patient_info'] = patient_info
            inputs['diagnoses'] = diagnoses
            inputs['observations'] = observations
            inputs['visit_info'] = visit_info
            inputs['procedures'] = procedures
            inputs['full_message'] = parsed_message.to_er7()
            
            # Save for later use
            self.patient_data = {
                'patient_info': patient_info,
                'diagnoses': diagnoses,
                'observations': observations,
                'visit_info': visit_info,
                'procedures': procedures,
                'message': parsed_message
            }
            
        except Exception as e:
            self.validation_issues.append({
                'error_type': type(e).__name__,
                'message': str(e),
                'details': 'Primary HL7 parsing failed, attempting fallback parsing'
            })

            # Enhanced fallback mechanism with comprehensive segment parsing
            try:
                fallback_data = self._fallback_parse_segments(inputs['hl7_message'])
                
                # Use fallback data
                inputs['patient_id'] = fallback_data['patient_info'].get('id', UNKNOWN_PATIENT_ID)
                inputs['patient_info'] = fallback_data['patient_info'] if fallback_data['patient_info'] else {'id': UNKNOWN_PATIENT_ID}
                inputs['diagnoses'] = fallback_data['diagnoses']
                inputs['observations'] = fallback_data['observations']
                inputs['visit_info'] = fallback_data['visit_info']
                inputs['procedures'] = fallback_data['procedures']
                
                if not inputs['patient_id'] or inputs['patient_id'] == UNKNOWN_PATIENT_ID:
                    self.validation_issues.append({
                        'error_type': 'PatientIDNotFoundError',
                        'message': 'Patient ID could not be determined from HL7 message',
                        'details': 'Both primary and fallback parsing failed to extract patient identifier'
                    })
                
            except Exception as fallback_exception:
                self.validation_issues.append({
                    'error_type': 'FallbackParsingError',
                    'message': 'Complete parsing failure - both primary and fallback methods failed',
                    'details': str(fallback_exception)
                })
                
                # Last resort - set minimal data
                inputs['patient_id'] = UNKNOWN_PATIENT_ID
                inputs['patient_info'] = {'id': UNKNOWN_PATIENT_ID}
                inputs['diagnoses'] = []
                inputs['observations'] = []
                inputs['visit_info'] = {}
                inputs['procedures'] = []

        # Always include validation results
        inputs['validation_errors'] = self.validation_issues
        inputs['parsing_success'] = len([issue for issue in self.validation_issues if issue['error_type'] in ['Exception', 'FallbackParsingError']]) == 0
        inputs['validation_warnings'] = len([issue for issue in self.validation_issues if 'Warning' in issue['error_type']])
        inputs['validation_errors_count'] = len([issue for issue in self.validation_issues if 'Error' in issue['error_type']])
            
        return inputs

    def _create_llm_instance(self):
        """Create an LLM instance based on configuration"""
        try:
            from openai import OpenAI
            
            # Get client parameters for the LLM backend
            client_params = self.llm_config.get_client_params()
            client = OpenAI(**client_params)
            
            # For CrewAI, we need to set the OpenAI client
            import os
            if self.llm_config.api_key:
                os.environ["OPENAI_API_KEY"] = self.llm_config.api_key
            if self.llm_config.base_url:
                os.environ["OPENAI_BASE_URL"] = self.llm_config.base_url
            if self.llm_config.model:
                os.environ["OPENAI_MODEL_NAME"] = self.llm_config.model
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create LLM instance: {str(e)}")
            raise

    def get_llm_config_dict(self) -> Dict[str, Any]:
        """Get LLM configuration as dictionary for CrewAI agents"""
        config = {
            'model': self.llm_config.model,
            'temperature': self.llm_config.temperature,
        }
        
        if self.llm_config.max_tokens:
            config['max_tokens'] = self.llm_config.max_tokens
            
        return config

    def add_dynamic_agent(self, agent_name: str, agent_config: Dict[str, Any], tools: Optional[List] = None) -> None:
        """
        Add a new agent dynamically to the simulation crew.
        
        Args:
            agent_name: Unique name for the agent
            agent_config: Configuration dictionary with role, goal, backstory
            tools: Optional list of tools for the agent
        """
        if agent_name in self._dynamic_agents:
            logger.warning(f"Agent '{agent_name}' already exists, replacing...")
        
        # Validate required fields
        required_fields = ['role', 'goal', 'backstory']
        missing_fields = [field for field in required_fields if field not in agent_config]
        if missing_fields:
            raise ValueError(f"Agent config missing required fields: {missing_fields}")
        
        self._dynamic_agents[agent_name] = {
            'config': agent_config,
            'tools': tools or []
        }
        logger.info(f"Added dynamic agent: {agent_name}")

    def add_dynamic_task(self, task_name: str, task_config: Dict[str, Any]) -> None:
        """
        Add a new task dynamically to the simulation crew.
        
        Args:
            task_name: Unique name for the task
            task_config: Configuration dictionary with description, expected_output, agent
        """
        if task_name in self._dynamic_tasks:
            logger.warning(f"Task '{task_name}' already exists, replacing...")
        
        # Validate required fields
        required_fields = ['description', 'expected_output', 'agent']
        missing_fields = [field for field in required_fields if field not in task_config]
        if missing_fields:
            raise ValueError(f"Task config missing required fields: {missing_fields}")
        
        # Validate that the assigned agent exists
        agent_name = task_config['agent']
        if (agent_name not in self._agents_config and 
            agent_name not in self._dynamic_agents):
            raise ValueError(f"Task '{task_name}' assigned to non-existent agent: {agent_name}")
        
        self._dynamic_tasks[task_name] = task_config
        logger.info(f"Added dynamic task: {task_name}")

    def get_all_agents(self) -> List[Agent]:
        """Get all agents including dynamically added ones."""
        # Get core agents by calling their methods
        core_agents = [
            self.data_ingestion_agent(),
            self.diagnostics_agent(),
            self.treatment_planner(),
            self.care_coordinator(),
            self.outcome_evaluator()
        ]
        
        # Add dynamic agents
        for agent_name, agent_data in self._dynamic_agents.items():
            dynamic_agent = Agent(
                config=agent_data['config'],
                tools=agent_data['tools'],
                verbose=True
            )
            core_agents.append(dynamic_agent)
        
        return core_agents

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks including dynamically added ones."""
        # Get core tasks by calling their methods
        core_tasks = [
            self.ingest_hl7_data(),
            self.analyze_diagnostics(),
            self.create_treatment_plan(),
            self.coordinate_care(),
            self.evaluate_outcomes()
        ]
        
        # Add dynamic tasks
        for task_name, task_config in self._dynamic_tasks.items():
            dynamic_task = Task(config=task_config)
            core_tasks.append(dynamic_task)
        
        return core_tasks

    def list_available_agents(self) -> List[str]:
        """List all available agent types (core + dynamic)."""
        core_agents = list(self._agents_config.keys())
        dynamic_agents = list(self._dynamic_agents.keys())
        return core_agents + dynamic_agents

    def list_available_tasks(self) -> List[str]:
        """List all available task types (core + dynamic)."""
        core_tasks = list(self._tasks_config.keys())
        dynamic_tasks = list(self._dynamic_tasks.keys())
        return core_tasks + dynamic_tasks

    @agent
    def data_ingestion_agent(self) -> Agent:
        """Creates the HL7 Data Ingestion Specialist agent."""
        return Agent(
            config=self._agents_config['data_ingestion_agent'],
            verbose=True
        )

    @agent
    def diagnostics_agent(self) -> Agent:
        """Creates the Clinical Diagnostics Analyst agent."""
        return Agent(
            config=self._agents_config['diagnostics_agent'],
            verbose=True,
            tools=[self.healthcare_tools.clinical_guidelines_tool()]
        )

    @agent
    def treatment_planner(self) -> Agent:
        """Creates the Treatment Planning Specialist agent."""
        return Agent(
            config=self._agents_config['treatment_planner'],
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
            config=self._agents_config['care_coordinator'],
            verbose=True,
            allow_delegation=True,  # Enable delegation for the manager role
            tools=[self.healthcare_tools.appointment_scheduler_tool()]
        )
        return coordinator

    @agent
    def outcome_evaluator(self) -> Agent:
        """Creates the Clinical Outcomes Analyst agent."""
        return Agent(
            config=self._agents_config['outcome_evaluator'],
            verbose=True
        )

    @task
    def ingest_hl7_data(self) -> Task:
        """Task for parsing and validating HL7 data."""
        return Task(
            config=self._tasks_config['ingest_hl7_data']
        )

    @task
    def analyze_diagnostics(self) -> Task:
        """Task for diagnostic analysis."""
        return Task(
            config=self._tasks_config['analyze_diagnostics']
        )

    @task 
    def create_treatment_plan(self) -> Task:
        """Task for treatment planning."""
        return Task(
            config=self._tasks_config['create_treatment_plan']
        )

    @task
    def coordinate_care(self) -> Task:
        """Task for care coordination."""
        return Task(
            config=self._tasks_config['coordinate_care']
        )

    @task
    def evaluate_outcomes(self) -> Task:
        """Task for outcome evaluation."""
        return Task(
            config=self._tasks_config['evaluate_outcomes']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Healthcare Simulation crew with core and dynamic agents/tasks."""
        # Initialize LLM configuration for CrewAI
        self._create_llm_instance()
        
        # Get all agents and tasks (core + dynamic)
        all_agents = self.get_all_agents()
        all_tasks = self.get_all_tasks()
        
        return Crew(
            agents=all_agents,
            tasks=all_tasks,
            process=Process.hierarchical,  # Use hierarchical process with care coordinator as manager
            manager_agent=self.care_coordinator(),
            verbose=True
        )
