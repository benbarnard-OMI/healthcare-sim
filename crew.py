from typing import Dict, Any, Optional, List
import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, task, crew, before_kickoff
from hl7apy import parser as hl7_parser
from tools.healthcare_tools import HealthcareTools
from llm_config import LLMConfig, create_llm_config, LLMBackend
from config_loader import get_config_loader
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
        
        # Load configuration files using the enhanced loader  
        config_loader = get_config_loader()
        self._agents_config, self._tasks_config = config_loader.load_configurations()
        logger.info(f"Loaded {len(self._agents_config)} agents and {len(self._tasks_config)} tasks")

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

    def _create_crewai_llm(self):
        """Create a CrewAI LLM instance based on configuration"""
        try:
            # Create LLM instance using CrewAI's LLM class
            if self.llm_config.backend == LLMBackend.OLLAMA:
                # Use the exact format from CrewAI docs: ollama/model_name
                llm = LLM(
                    model=f"ollama/{self.llm_config.model}",
                    base_url=self.llm_config.base_url.replace('/v1', '') if self.llm_config.base_url else 'http://localhost:11434',
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens
                )
                logger.info(f"Created CrewAI LLM with Ollama: ollama/{self.llm_config.model}")
            elif self.llm_config.backend == LLMBackend.OPENROUTER:
                llm = LLM(
                    model=f"openrouter/{self.llm_config.model}",
                    base_url=self.llm_config.base_url,
                    api_key=self.llm_config.api_key,
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens
                )
                logger.info(f"Created CrewAI LLM with OpenRouter: openrouter/{self.llm_config.model}")
            elif self.llm_config.backend == LLMBackend.DEEPSEEK:
                llm = LLM(
                    model=self.llm_config.model,
                    api_key=self.llm_config.api_key,
                    base_url=self.llm_config.base_url,
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens
                )
                logger.info(f"Created CrewAI LLM with DeepSeek: {self.llm_config.model}")
            else:  # OpenAI
                llm = LLM(
                    model=self.llm_config.model,
                    api_key=self.llm_config.api_key,
                    base_url=self.llm_config.base_url,
                    temperature=self.llm_config.temperature,
                    max_tokens=self.llm_config.max_tokens
                )
                logger.info(f"Created CrewAI LLM with OpenAI: {self.llm_config.model}")
            
            return llm
            
        except Exception as e:
            logger.error(f"Failed to create CrewAI LLM instance: {str(e)}")
            raise

    def _step_callback(self, step_output):
        """Callback to monitor crew execution steps and prevent infinite loops."""
        try:
            if hasattr(step_output, 'task') and hasattr(step_output.task, 'status'):
                logger.info(f"Task {step_output.task.description[:50]}... status: {step_output.task.status}")
                
                # Check for repeated failures
                if hasattr(step_output.task, 'retry_count') and step_output.task.retry_count > 2:
                    logger.warning(f"Task {step_output.task.description[:50]}... has failed {step_output.task.retry_count} times")
                    
        except Exception as e:
            logger.warning(f"Error in step callback: {e}")

    def get_llm_config_dict(self) -> Dict[str, Any]:
        """Get LLM configuration as dictionary for CrewAI agents"""
        config = {
            'model': self.llm_config.model,
            'temperature': self.llm_config.temperature,
        }
        
        if self.llm_config.max_tokens:
            config['max_tokens'] = self.llm_config.max_tokens
            
        # For LiteLLM compatibility, prefix model with provider
        if self.llm_config.backend == LLMBackend.OLLAMA:
            config['model'] = f"ollama/{self.llm_config.model}"
            logger.info(f"Updated model name for Ollama: {config['model']}")
        elif self.llm_config.backend == LLMBackend.OPENROUTER:
            config['model'] = f"openrouter/{self.llm_config.model}"
            
        logger.info(f"Final LLM config: {config}")
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
                **agent_data['config'],
                tools=agent_data['tools']
            )
            core_agents.append(dynamic_agent)
        
        return core_agents

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks including dynamically added ones."""
        # Get core tasks by calling their methods
        core_tasks = [
            self.parse_hl7_data(),
            self.make_clinical_decisions(),
            self.generate_next_steps(),
            self.generate_hl7_messages()
        ]
        
        # Add dynamic tasks
        for task_name, task_config in self._dynamic_tasks.items():
            dynamic_task = Task(**task_config)
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
            **self._agents_config['data_ingestion_agent']
        )

    @agent
    def diagnostics_agent(self) -> Agent:
        """Creates the Clinical Diagnostics Analyst agent."""
        return Agent(
            **self._agents_config['diagnostics_agent']
            # Removed tools - real clinicians don't look up guidelines constantly
        )

    @agent
    def treatment_planner(self) -> Agent:
        """Creates the Treatment Planning Specialist agent."""
        return Agent(
            **self._agents_config['treatment_planner'],
            tools=[self.healthcare_tools.medication_interaction_tool()]  # Only keep medication interaction tool for safety
        )

    @agent
    def care_coordinator(self) -> Agent:
        """Creates the Patient Care Coordinator agent (acts as manager)."""
        config = self._agents_config['care_coordinator'].copy()
        config['allow_delegation'] = True  # Enable delegation for the manager role
        # Remove tools for manager agent - CrewAI expects managers to not have tools
        config.pop('tools', None)
        coordinator = Agent(**config)
        return coordinator

    @agent
    def outcome_evaluator(self) -> Agent:
        """Creates the Clinical Outcomes Analyst agent."""
        return Agent(
            **self._agents_config['outcome_evaluator']
        )

    @task
    def parse_hl7_data(self) -> Task:
        """Task for understanding the starting Synthea HL7 message."""
        config = {
            'description': 'Review the incoming Synthea HL7 message to understand the patient\'s current state: demographics, vital signs, lab results, and diagnoses. This is our starting point for the clinical pathway simulation.',
            'expected_output': 'Summary of patient\'s current state from the Synthea HL7 message including: patient demographics, current vital signs, lab values, active diagnoses, and any clinical concerns that need attention.',
            'agent': self.data_ingestion_agent()
        }
        return Task(**config)

    @task
    def make_clinical_decisions(self) -> Task:
        """Task for making clinical decisions based on the starting Synthea HL7 data."""
        config = {
            'description': 'Based on the patient\'s current state from the Synthea HL7 message, make clinical decisions: assess acuity level, determine disposition (admit/discharge/observe), and identify what interventions are needed.',
            'expected_output': 'Clinical decision summary including: acuity assessment (stable/unstable/critical), disposition recommendation (admit/discharge/observe), immediate interventions needed, and priority level.',
            'agent': self.diagnostics_agent()
        }
        return Task(**config)

    @task
    def generate_next_steps(self) -> Task:
        """Task for planning the next steps in the clinical pathway."""
        config = {
            'description': 'Based on the clinical decisions, plan the next steps: what specific orders need to be placed (labs, imaging, medications), what consultations to request, and what monitoring is needed.',
            'expected_output': 'Next steps plan including: specific orders to place (lab codes, imaging studies, medications with doses), consultation requests, monitoring parameters, and immediate actions for the next 24-48 hours.',
            'agent': self.treatment_planner()
        }
        return Task(**config)

    @task
    def generate_hl7_messages(self) -> Task:
        """Task for generating a complete clinical pathway with all required HL7 messages."""
        config = {
            'description': 'Generate a COMPLETE clinical pathway with ALL required HL7 messages that would be created in a real hospital system. CRITICAL HL7 FIELD MAPPING FIXES REQUIRED: 1) PID field mapping: MRN in PID-3 (not PID-2), format PID|1||123456789^^^MAIN_HOSPITAL^MR||DOE^JOHN^M, 2) DG1 coding system: use ICD-10-CM (not I10), format DG1|2||E11.9^Type 2 diabetes mellitus^ICD-10-CM, 3) ORC field mapping: timestamp in ORC-9 (not ORC-5), provider in ORC-12, 4) RXO field mapping: RXO|NDC^DRUG^NDC|dose|units (omit RXO-3 unless max dose), separate RXR and TQ1 segments, 5) WBC/platelet UCUM units: use 10*9/L^10*9/L^UCUM (not 109/L), 6) Complete all messages: finish truncated pharmacy message, add ADT^A03 discharge, MDM^T02 discharge summary with TXA and diagnoses as CWE in OBX-5, add complete pharmacy discharge message, 7) Segment termination: end each segment after last meaningful field, avoid trailing empty pipes. PREVIOUS FIXES MAINTAINED: PV1 provider in PV1-7, RAS ORC-1 use SC, correct BP LOINC codes, distinct provider IDs, result-order linkage. REQUIREMENTS: Valid NDC codes, consistent patient data, proper HL7 v2.5.1 formatting, realistic timestamps.',
            'expected_output': 'Complete clinical pathway with ALL required HL7 messages in chronological order with PROPER HL7 FIELD MAPPING AND PROPER SEGMENT TERMINATION. CRITICAL FIXES: 1) PID format: PID|1||123456789^^^MAIN_HOSPITAL^MR||DOE^JOHN^M (MRN in PID-3, not PID-2), 2) DG1 format: DG1|2||E11.9^Type 2 diabetes mellitus^ICD-10-CM (ICD-10-CM coding system), 3) ORC format: ORC|NW|ORD123|||||||20231015101500|||1234567890^SMITH^JANE^MD (timestamp in ORC-9), 4) RXO format: RXO|00093-0245-56^LISINOPRIL 20MG TAB^NDC|20|mg (dose in RXO-2, units in RXO-3), 5) WBC units: OBX|...|6690-2^Leukocytes^LN||6.8|10*9/L^10*9/L^UCUM|4.5-11.0|N (proper UCUM format), 6) Complete messages: finish truncated pharmacy message, add ADT^A03 discharge, MDM^T02 discharge summary with TXA and diagnoses as CWE in OBX-5, add complete pharmacy discharge message. Must include: 1) ADT^A01 admission with proper PID-3 MRN and DG1 ICD-10-CM coding, 2) ORM^O01 lab orders with ORC-9 timestamps, 3) ORU^R01 lab results with proper UCUM units (10*9/L), 4) ORM^O01 medication orders with correct RXO field mapping, 5) RAS^O17 medication administrations, 6) Complete ADT^A08 patient updates, 7) ADT^A03 discharge, 8) MDM^T02 discharge summary with TXA and diagnoses as CWE in OBX-5, 9) Complete pharmacy discharge message. All messages must have consistent patient data, valid codes, proper HL7 v2.5.1 structure with correct field positions, and realistic timestamps.',
            'agent': self.treatment_planner()
        }
        return Task(**config)

    @task
    def coordinate_care(self) -> Task:
        """Task for care coordination."""
        config = self._tasks_config['coordinate_care'].copy()
        # Assign the specific agent for this task
        config['agent'] = self.care_coordinator()
        return Task(**config)

    @task
    def evaluate_outcomes(self) -> Task:
        """Task for outcome evaluation."""
        config = self._tasks_config['evaluate_outcomes'].copy()
        # Assign the specific agent for this task
        config['agent'] = self.outcome_evaluator()
        return Task(**config)

    @crew
    def crew(self) -> Crew:
        """Creates the Healthcare Simulation crew focused on realistic clinical pathway simulation."""
        # Create LLM instance using CrewAI's LLM class
        llm = self._create_crewai_llm()
        
        # Use only essential tasks for realistic clinical workflow
        clinical_tasks = [
            self.parse_hl7_data(),
            self.make_clinical_decisions(),
            self.generate_next_steps(),
            self.generate_hl7_messages()
        ]
        
        # Get only the agents needed for clinical workflow
        clinical_agents = [
            self.data_ingestion_agent(),
            self.diagnostics_agent(),
            self.treatment_planner()
        ]
        
        return Crew(
            agents=clinical_agents,
            tasks=clinical_tasks,
            process=Process.sequential,  # Use sequential process for clear workflow
            verbose=True,
            llm=llm,  # Pass LLM instance to CrewAI
            max_iter=1,  # Single iteration for realistic speed
            max_execution_time=60,  # 1 minute timeout for realistic speed
            step_callback=self._step_callback  # Add callback for monitoring
        )
