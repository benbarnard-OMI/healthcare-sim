"""
Scenario Loader Module

This module provides functionality to load patient scenarios from both YAML configuration
files and Python modules, with validation and error handling. It also integrates with
Synthea-generated scenarios for realistic synthetic patient data.
"""

import yaml
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Import Synthea integration (optional)
try:
    from synthea_scenario_loader import SyntheaScenarioLoader
    SYNTHEA_AVAILABLE = True
except ImportError:
    SYNTHEA_AVAILABLE = False
    logger.warning("Synthea integration not available. Install synthea_scenario_loader for realistic patient data.")

@dataclass
class ScenarioMetadata:
    """Metadata about a patient scenario."""
    age_group: str
    gender: str
    primary_condition: str
    expected_duration: str

@dataclass
class PatientScenario:
    """A patient scenario with all associated data."""
    id: str
    name: str
    description: str
    category: str
    severity: str
    tags: List[str]
    metadata: ScenarioMetadata
    hl7_message: str
    expected_findings: Optional[List[str]] = None
    clinical_pathways: Optional[List[str]] = None

class ScenarioValidationError(Exception):
    """Raised when scenario validation fails."""
    pass

class ScenarioLoader:
    """
    Loads and validates patient scenarios from YAML configuration files
    and provides backward compatibility with Python-based scenarios.
    Also integrates with Synthea for realistic synthetic patient data.
    """
    
    def __init__(self, config_path: str = None, fallback_module = None, enable_synthea: bool = True):
        """
        Initialize the scenario loader.
        
        Args:
            config_path: Path to the YAML scenarios configuration file
            fallback_module: Python module containing SAMPLE_MESSAGES (for backward compatibility)
            enable_synthea: Whether to enable Synthea integration for realistic patient data
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'config', 'scenarios.yaml')
        self.fallback_module = fallback_module
        self.enable_synthea = enable_synthea and SYNTHEA_AVAILABLE
        self._scenarios: Dict[str, PatientScenario] = {}
        self._validation_config: Dict[str, Any] = {}
        self._loaded = False
        
        # Initialize Synthea loader if available
        self._synthea_loader = None
        if self.enable_synthea:
            try:
                self._synthea_loader = SyntheaScenarioLoader()
                logger.info("Synthea integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Synthea loader: {e}")
                self.enable_synthea = False
    
    def load_scenarios(self) -> Dict[str, PatientScenario]:
        """
        Load scenarios from YAML configuration with fallback to Python module.
        Also loads Synthea-generated scenarios if available.
        
        Returns:
            Dictionary of scenario_id -> PatientScenario objects
        """
        if self._loaded:
            return self._scenarios
        
        # Try to load from YAML first
        try:
            if os.path.exists(self.config_path):
                self._load_from_yaml()
                logger.info(f"Loaded {len(self._scenarios)} scenarios from YAML config")
            else:
                logger.warning(f"YAML config file not found at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load scenarios from YAML: {str(e)}")
        
        # Load Synthea scenarios if available
        if self.enable_synthea and self._synthea_loader:
            try:
                self._load_synthea_scenarios()
                logger.info(f"Loaded Synthea scenarios, total: {len(self._scenarios)} scenarios")
            except Exception as e:
                logger.error(f"Failed to load Synthea scenarios: {str(e)}")
        
        # Fallback to Python module if no YAML scenarios loaded or for backward compatibility
        if not self._scenarios and self.fallback_module:
            self._load_from_python_module()
            logger.info(f"Loaded {len(self._scenarios)} scenarios from Python module (fallback)")
        
        # If both YAML and Python scenarios exist, merge them (YAML takes precedence)
        elif self.fallback_module:
            python_scenarios = self._extract_python_scenarios()
            for scenario_id, scenario in python_scenarios.items():
                if scenario_id not in self._scenarios:
                    self._scenarios[scenario_id] = scenario
            logger.info(f"Merged Python scenarios, total: {len(self._scenarios)} scenarios")
        
        self._loaded = True
        return self._scenarios
    
    def _load_from_yaml(self) -> None:
        """Load scenarios from YAML configuration file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'scenarios' not in config:
            raise ScenarioValidationError("YAML config must contain 'scenarios' section")
        
        # Store validation configuration
        self._validation_config = config.get('validation', {})
        
        # Load and validate each scenario
        for scenario_id, scenario_data in config['scenarios'].items():
            try:
                scenario = self._create_scenario_from_yaml(scenario_id, scenario_data)
                self._validate_scenario(scenario)
                self._scenarios[scenario_id] = scenario
            except Exception as e:
                logger.error(f"Failed to load scenario '{scenario_id}': {str(e)}")
                continue
    
    def _create_scenario_from_yaml(self, scenario_id: str, data: Dict[str, Any]) -> PatientScenario:
        """Create a PatientScenario object from YAML data."""
        # Create metadata object
        metadata_data = data.get('metadata', {})
        metadata = ScenarioMetadata(
            age_group=metadata_data.get('age_group', 'unknown'),
            gender=metadata_data.get('gender', 'unknown'),
            primary_condition=metadata_data.get('primary_condition', 'unknown'),
            expected_duration=metadata_data.get('expected_duration', 'unknown')
        )
        
        # Create scenario object
        scenario = PatientScenario(
            id=scenario_id,
            name=data.get('name', scenario_id),
            description=data.get('description', ''),
            category=data.get('category', 'general_medicine'),
            severity=data.get('severity', 'moderate'),
            tags=data.get('tags', []),
            metadata=metadata,
            hl7_message=data.get('hl7_message', '').strip(),
            expected_findings=data.get('expected_findings'),
            clinical_pathways=data.get('clinical_pathways')
        )
        
        return scenario
    
    def _load_from_python_module(self) -> None:
        """Load scenarios from Python module (backward compatibility)."""
        python_scenarios = self._extract_python_scenarios()
        self._scenarios.update(python_scenarios)
    
    def _extract_python_scenarios(self) -> Dict[str, PatientScenario]:
        """Extract scenarios from Python module format."""
        scenarios = {}
        
        if not hasattr(self.fallback_module, 'SAMPLE_MESSAGES'):
            logger.warning("Python module does not have SAMPLE_MESSAGES attribute")
            return scenarios
        
        sample_messages = self.fallback_module.SAMPLE_MESSAGES
        
        for scenario_id, hl7_message in sample_messages.items():
            try:
                # Create a basic scenario from Python data
                scenario = PatientScenario(
                    id=scenario_id,
                    name=self._format_scenario_name(scenario_id),
                    description=f"Legacy scenario: {scenario_id}",
                    category="general_medicine",
                    severity="moderate",
                    tags=[scenario_id],
                    metadata=ScenarioMetadata(
                        age_group="adult",
                        gender="unknown",
                        primary_condition=scenario_id,
                        expected_duration="unknown"
                    ),
                    hl7_message=hl7_message.strip()
                )
                scenarios[scenario_id] = scenario
            except Exception as e:
                logger.error(f"Failed to convert Python scenario '{scenario_id}': {str(e)}")
                continue
        
        return scenarios
    
    def _load_synthea_scenarios(self) -> None:
        """Load Synthea-generated scenarios."""
        if not self._synthea_loader:
            return
        
        # Get all Synthea scenarios
        synthea_scenarios = self._synthea_loader.scenarios
        
        for scenario_id, synthea_scenario in synthea_scenarios.items():
            try:
                # Convert Synthea scenario to PatientScenario
                scenario = self._create_scenario_from_synthea(scenario_id, synthea_scenario)
                self._scenarios[scenario_id] = scenario
            except Exception as e:
                logger.error(f"Failed to convert Synthea scenario '{scenario_id}': {str(e)}")
                continue
    
    def _create_scenario_from_synthea(self, scenario_id: str, synthea_scenario: Dict[str, Any]) -> PatientScenario:
        """Create a PatientScenario object from Synthea scenario data."""
        metadata_data = synthea_scenario.get('metadata', {})
        metadata = ScenarioMetadata(
            age_group=metadata_data.get('age_group', 'unknown'),
            gender=metadata_data.get('gender', 'unknown'),
            primary_condition=metadata_data.get('primary_condition', 'unknown'),
            expected_duration=metadata_data.get('expected_duration', 'unknown')
        )
        
        # Create scenario object
        scenario = PatientScenario(
            id=scenario_id,
            name=synthea_scenario.get('name', scenario_id),
            description=synthea_scenario.get('description', ''),
            category=synthea_scenario.get('category', 'general_medicine'),
            severity=synthea_scenario.get('severity', 'moderate'),
            tags=synthea_scenario.get('tags', []),
            metadata=metadata,
            hl7_message=synthea_scenario.get('hl7_message', '').strip(),
            expected_findings=synthea_scenario.get('expected_findings'),
            clinical_pathways=synthea_scenario.get('clinical_pathways')
        )
        
        return scenario
    
    def _format_scenario_name(self, scenario_id: str) -> str:
        """Convert scenario_id to a readable name."""
        return scenario_id.replace('_', ' ').title()
    
    def _validate_scenario(self, scenario: PatientScenario) -> None:
        """Validate a scenario against the configuration schema."""
        # Check required fields
        required_fields = self._validation_config.get('required_fields', [])
        for field in required_fields:
            if field == 'name' and not scenario.name:
                raise ScenarioValidationError(f"Scenario {scenario.id}: name is required")
            elif field == 'description' and not scenario.description:
                raise ScenarioValidationError(f"Scenario {scenario.id}: description is required")
            elif field == 'category' and not scenario.category:
                raise ScenarioValidationError(f"Scenario {scenario.id}: category is required")
            elif field == 'severity' and not scenario.severity:
                raise ScenarioValidationError(f"Scenario {scenario.id}: severity is required")
            elif field == 'hl7_message' and not scenario.hl7_message:
                raise ScenarioValidationError(f"Scenario {scenario.id}: hl7_message is required")
        
        # Validate severity level
        valid_severities = self._validation_config.get('severity_levels', [])
        if valid_severities and scenario.severity not in valid_severities:
            raise ScenarioValidationError(
                f"Scenario {scenario.id}: invalid severity '{scenario.severity}'. "
                f"Valid options: {valid_severities}"
            )
        
        # Validate category
        valid_categories = self._validation_config.get('categories', [])
        if valid_categories and scenario.category not in valid_categories:
            raise ScenarioValidationError(
                f"Scenario {scenario.id}: invalid category '{scenario.category}'. "
                f"Valid options: {valid_categories}"
            )
        
        # Validate age group
        valid_age_groups = self._validation_config.get('age_groups', [])
        if valid_age_groups and scenario.metadata.age_group not in valid_age_groups:
            raise ScenarioValidationError(
                f"Scenario {scenario.id}: invalid age_group '{scenario.metadata.age_group}'. "
                f"Valid options: {valid_age_groups}"
            )
        
        # Basic HL7 message validation
        self._validate_hl7_message(scenario)
    
    def _validate_hl7_message(self, scenario: PatientScenario) -> None:
        """Basic validation of HL7 message structure."""
        message = scenario.hl7_message
        if not message:
            return
        
        lines = message.strip().split('\n')
        if not lines:
            raise ScenarioValidationError(f"Scenario {scenario.id}: empty HL7 message")
        
        # Check for required segments
        has_msh = any(line.startswith('MSH|') for line in lines)
        has_pid = any(line.startswith('PID|') for line in lines)
        
        if not has_msh:
            raise ScenarioValidationError(f"Scenario {scenario.id}: HL7 message missing MSH segment")
        if not has_pid:
            raise ScenarioValidationError(f"Scenario {scenario.id}: HL7 message missing PID segment")
    
    def get_scenario(self, scenario_id: str) -> Optional[PatientScenario]:
        """
        Get a specific scenario by ID.
        
        Args:
            scenario_id: The scenario identifier
            
        Returns:
            PatientScenario object or None if not found
        """
        scenarios = self.load_scenarios()
        return scenarios.get(scenario_id.lower())
    
    def list_scenarios(self) -> List[str]:
        """
        List all available scenario IDs.
        
        Returns:
            List of scenario identifiers
        """
        scenarios = self.load_scenarios()
        return list(scenarios.keys())
    
    def list_scenarios_by_category(self, category: str) -> List[str]:
        """
        List scenarios filtered by category.
        
        Args:
            category: The category to filter by
            
        Returns:
            List of scenario identifiers in the category
        """
        scenarios = self.load_scenarios()
        return [
            scenario_id for scenario_id, scenario in scenarios.items()
            if scenario.category == category
        ]
    
    def list_scenarios_by_severity(self, severity: str) -> List[str]:
        """
        List scenarios filtered by severity.
        
        Args:
            severity: The severity level to filter by
            
        Returns:
            List of scenario identifiers with the severity level
        """
        scenarios = self.load_scenarios()
        return [
            scenario_id for scenario_id, scenario in scenarios.items()
            if scenario.severity == severity
        ]
    
    def get_scenario_info(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a scenario.
        
        Args:
            scenario_id: The scenario identifier
            
        Returns:
            Dictionary with scenario information or None if not found
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None
        
        return {
            'id': scenario.id,
            'name': scenario.name,
            'description': scenario.description,
            'category': scenario.category,
            'severity': scenario.severity,
            'tags': scenario.tags,
            'metadata': {
                'age_group': scenario.metadata.age_group,
                'gender': scenario.metadata.gender,
                'primary_condition': scenario.metadata.primary_condition,
                'expected_duration': scenario.metadata.expected_duration
            },
            'expected_findings': scenario.expected_findings or [],
            'clinical_pathways': scenario.clinical_pathways or [],
            'has_hl7_message': bool(scenario.hl7_message)
        }
    
    def get_hl7_message(self, scenario_id: str) -> Optional[str]:
        """
        Get the HL7 message for a scenario.
        
        Args:
            scenario_id: The scenario identifier
            
        Returns:
            HL7 message string or None if not found
        """
        scenario = self.get_scenario(scenario_id)
        return scenario.hl7_message if scenario else None
    
    def validate_configuration(self) -> List[str]:
        """
        Validate all loaded scenarios and return a list of validation errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        try:
            scenarios = self.load_scenarios()
            for scenario_id, scenario in scenarios.items():
                try:
                    self._validate_scenario(scenario)
                except ScenarioValidationError as e:
                    errors.append(str(e))
        except Exception as e:
            errors.append(f"Failed to load scenarios for validation: {str(e)}")
        
        return errors
    
    def generate_synthea_scenarios(self, 
                                  num_patients: int = 20,
                                  age_min: int = 0,
                                  age_max: int = 100,
                                  state: str = "Massachusetts",
                                  city: str = "Boston",
                                  seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate new Synthea scenarios and integrate them into the simulation.
        
        Args:
            num_patients: Number of patients to generate
            age_min: Minimum age for generated patients
            age_max: Maximum age for generated patients
            state: US state for patient demographics
            city: City for patient demographics
            seed: Random seed for reproducible results
            
        Returns:
            Dictionary containing generation results and scenario metadata
        """
        if not self.enable_synthea or not self._synthea_loader:
            raise RuntimeError("Synthea integration not available")
        
        # Generate scenarios using Synthea loader
        result = self._synthea_loader.generate_synthea_scenarios(
            num_patients=num_patients,
            age_min=age_min,
            age_max=age_max,
            state=state,
            city=city,
            seed=seed
        )
        
        # Refresh our scenarios to include the new ones
        self._loaded = False
        self.load_scenarios()
        
        return result
    
    def get_synthea_scenarios(self) -> List[str]:
        """Get all Synthea-generated scenarios."""
        if not self.enable_synthea or not self._synthea_loader:
            return []
        
        return self._synthea_loader.get_synthea_scenarios()
    
    def export_synthea_scenario(self, scenario_id: str, output_file: str):
        """Export a Synthea scenario to a file."""
        if not self.enable_synthea or not self._synthea_loader:
            raise RuntimeError("Synthea integration not available")
        
        self._synthea_loader.export_scenario(scenario_id, output_file)
    
    def export_all_synthea_scenarios(self, output_dir: str):
        """Export all Synthea scenarios to individual files."""
        if not self.enable_synthea or not self._synthea_loader:
            raise RuntimeError("Synthea integration not available")
        
        self._synthea_loader.export_all_synthea_scenarios(output_dir)


# Global scenario loader instance (initialized lazily)
_scenario_loader = None

def get_scenario_loader(config_path: str = None, fallback_module = None) -> ScenarioLoader:
    """
    Get the global scenario loader instance.
    
    Args:
        config_path: Path to scenarios configuration file (optional)
        fallback_module: Python module for backward compatibility (optional)
        
    Returns:
        ScenarioLoader instance
    """
    global _scenario_loader
    if _scenario_loader is None:
        _scenario_loader = ScenarioLoader(config_path, fallback_module)
    return _scenario_loader

# Convenience functions for backward compatibility
def get_message(scenario_name: str) -> Optional[str]:
    """Get HL7 message for a scenario (backward compatibility)."""
    loader = get_scenario_loader()
    try:
        # Import the fallback module for backward compatibility
        from sample_data import sample_messages
        loader.fallback_module = sample_messages
    except ImportError:
        pass
    
    return loader.get_hl7_message(scenario_name.lower())

def list_scenarios() -> List[str]:
    """List all available scenarios (backward compatibility)."""
    loader = get_scenario_loader()
    try:
        # Import the fallback module for backward compatibility
        from sample_data import sample_messages
        loader.fallback_module = sample_messages
    except ImportError:
        pass
    
    return loader.list_scenarios()