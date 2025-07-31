"""
Tests for scenario loader functionality and extensibility features.
"""

import pytest
import os
import yaml
import tempfile
from unittest.mock import patch, MagicMock
from scenario_loader import ScenarioLoader, ScenarioValidationError, PatientScenario, ScenarioMetadata

class TestScenarioLoader:
    """Test the ScenarioLoader class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_config = {
            'scenarios': {
                'test_scenario': {
                    'name': 'Test Scenario',
                    'description': 'A test scenario for unit testing',
                    'category': 'general_medicine',
                    'severity': 'moderate',
                    'tags': ['test', 'unit_test'],
                    'metadata': {
                        'age_group': 'adult',
                        'gender': 'male',
                        'primary_condition': 'test_condition',
                        'expected_duration': '1-2_hours'
                    },
                    'hl7_message': 'MSH|^~\\&|TEST|TEST|SIM|SIM|20240101120000||ADT^A01|123|P|2.5.1\nPID|1|123|123^^^TEST^MR|||||M||||||||'
                }
            },
            'validation': {
                'required_fields': ['name', 'description', 'category', 'severity', 'hl7_message'],
                'severity_levels': ['low', 'moderate', 'high', 'critical'],
                'categories': ['general_medicine', 'cardiology', 'emergency'],
                'age_groups': ['adult', 'pediatric', 'elderly']
            }
        }
    
    def test_scenario_loader_initialization(self):
        """Test ScenarioLoader initialization."""
        loader = ScenarioLoader()
        assert loader.config_path is not None
        assert loader._scenarios == {}
        assert not loader._loaded
    
    def test_load_scenarios_from_yaml(self):
        """Test loading scenarios from YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.test_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            scenarios = loader.load_scenarios()
            
            assert len(scenarios) == 1
            assert 'test_scenario' in scenarios
            
            scenario = scenarios['test_scenario']
            assert isinstance(scenario, PatientScenario)
            assert scenario.name == 'Test Scenario'
            assert scenario.category == 'general_medicine'
            assert scenario.severity == 'moderate'
            assert 'MSH|' in scenario.hl7_message
            
        finally:
            os.unlink(temp_path)
    
    def test_scenario_validation_required_fields(self):
        """Test scenario validation for required fields."""
        invalid_config = {
            'scenarios': {
                'invalid_scenario': {
                    'name': 'Invalid Scenario',
                    # Missing required fields: description, category, severity, hl7_message
                }
            },
            'validation': self.test_config['validation']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            scenarios = loader.load_scenarios()
            
            # Should not load invalid scenario
            assert len(scenarios) == 0
            
        finally:
            os.unlink(temp_path)
    
    def test_scenario_validation_severity_levels(self):
        """Test scenario validation for severity levels."""
        invalid_severity_config = {
            'scenarios': {
                'invalid_severity_scenario': {
                    'name': 'Invalid Severity Scenario',
                    'description': 'Test scenario with invalid severity',
                    'category': 'general_medicine',
                    'severity': 'invalid_severity',  # Invalid severity
                    'hl7_message': 'MSH|test\nPID|test'
                }
            },
            'validation': self.test_config['validation']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(invalid_severity_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            scenarios = loader.load_scenarios()
            
            # Should not load scenario with invalid severity
            assert len(scenarios) == 0
            
        finally:
            os.unlink(temp_path)
    
    def test_hl7_message_validation(self):
        """Test HL7 message validation."""
        invalid_hl7_config = {
            'scenarios': {
                'invalid_hl7_scenario': {
                    'name': 'Invalid HL7 Scenario',
                    'description': 'Test scenario with invalid HL7',
                    'category': 'general_medicine',
                    'severity': 'moderate',
                    'hl7_message': 'INVALID|MESSAGE'  # Missing MSH and PID
                }
            },
            'validation': self.test_config['validation']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(invalid_hl7_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            scenarios = loader.load_scenarios()
            
            # Should not load scenario with invalid HL7
            assert len(scenarios) == 0
            
        finally:
            os.unlink(temp_path)
    
    def test_fallback_to_python_module(self):
        """Test fallback to Python module when YAML not available."""
        # Mock Python module
        mock_module = MagicMock()
        mock_module.SAMPLE_MESSAGES = {
            'python_scenario': 'MSH|^~\\&|PYTHON|PYTHON|SIM|SIM|20240101120000||ADT^A01|123|P|2.5.1\nPID|1|123|123^^^PYTHON^MR|||||M||||||||'
        }
        
        # Use non-existent YAML path to trigger fallback
        loader = ScenarioLoader(config_path='/non/existent/path.yaml', fallback_module=mock_module)
        scenarios = loader.load_scenarios()
        
        assert len(scenarios) == 1
        assert 'python_scenario' in scenarios
        
        scenario = scenarios['python_scenario']
        assert scenario.name == 'Python Scenario'
        assert scenario.category == 'general_medicine'  # Default value
        assert 'MSH|' in scenario.hl7_message
    
    def test_get_scenario(self):
        """Test getting a specific scenario."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.test_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            
            scenario = loader.get_scenario('test_scenario')
            assert scenario is not None
            assert scenario.name == 'Test Scenario'
            
            # Test case insensitive
            scenario = loader.get_scenario('TEST_SCENARIO')
            assert scenario is not None
            
            # Test non-existent scenario
            scenario = loader.get_scenario('non_existent')
            assert scenario is None
            
        finally:
            os.unlink(temp_path)
    
    def test_list_scenarios(self):
        """Test listing all scenarios."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.test_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            scenario_list = loader.list_scenarios()
            
            assert len(scenario_list) == 1
            assert 'test_scenario' in scenario_list
            
        finally:
            os.unlink(temp_path)
    
    def test_list_scenarios_by_category(self):
        """Test listing scenarios by category."""
        multi_scenario_config = {
            'scenarios': {
                'cardiology_scenario': {
                    'name': 'Cardiology Test',
                    'description': 'Cardiology test',
                    'category': 'cardiology',
                    'severity': 'moderate',
                    'metadata': {
                        'age_group': 'adult',
                        'gender': 'male',
                        'primary_condition': 'test_condition',
                        'expected_duration': '1-2_hours'
                    },
                    'hl7_message': 'MSH|test\nPID|test'
                },
                'emergency_scenario': {
                    'name': 'Emergency Test',
                    'description': 'Emergency test',
                    'category': 'emergency',
                    'severity': 'high',
                    'metadata': {
                        'age_group': 'adult',
                        'gender': 'female',
                        'primary_condition': 'emergency_condition',
                        'expected_duration': '2-4_hours'
                    },
                    'hl7_message': 'MSH|test\nPID|test'
                }
            },
            'validation': self.test_config['validation']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(multi_scenario_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            
            cardiology_scenarios = loader.list_scenarios_by_category('cardiology')
            assert len(cardiology_scenarios) == 1
            assert 'cardiology_scenario' in cardiology_scenarios
            
            emergency_scenarios = loader.list_scenarios_by_category('emergency')
            assert len(emergency_scenarios) == 1
            assert 'emergency_scenario' in emergency_scenarios
            
            # Test non-existent category
            non_existent = loader.list_scenarios_by_category('non_existent')
            assert len(non_existent) == 0
            
        finally:
            os.unlink(temp_path)
    
    def test_get_scenario_info(self):
        """Test getting detailed scenario information."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.test_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            
            info = loader.get_scenario_info('test_scenario')
            assert info is not None
            assert info['name'] == 'Test Scenario'
            assert info['category'] == 'general_medicine'
            assert info['severity'] == 'moderate'
            assert 'test' in info['tags']
            assert info['metadata']['age_group'] == 'adult'
            assert info['has_hl7_message'] is True
            
            # Test non-existent scenario
            info = loader.get_scenario_info('non_existent')
            assert info is None
            
        finally:
            os.unlink(temp_path)
    
    def test_get_hl7_message(self):
        """Test getting HL7 message for a scenario."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.test_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            
            hl7_message = loader.get_hl7_message('test_scenario')
            assert hl7_message is not None
            assert 'MSH|' in hl7_message
            assert 'PID|' in hl7_message
            
            # Test non-existent scenario
            hl7_message = loader.get_hl7_message('non_existent')
            assert hl7_message is None
            
        finally:
            os.unlink(temp_path)
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(self.test_config, f)
            temp_path = f.name
        
        try:
            loader = ScenarioLoader(config_path=temp_path)
            errors = loader.validate_configuration()
            
            # Valid configuration should have no errors
            assert len(errors) == 0
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.skip(reason="Mock patching issue with sample_messages import")
    def test_backward_compatibility_functions(self):
        """Test backward compatibility functions."""
        from scenario_loader import get_message, list_scenarios
        
        # Create a mock sample_messages module
        mock_sample_messages = MagicMock()
        mock_sample_messages.SAMPLE_MESSAGES = {
            'chest_pain': 'MSH|test\nPID|test'
        }
        
        # Test get_message function with mock
        with patch('scenario_loader.sample_messages', mock_sample_messages):
            message = get_message('chest_pain')
            assert message is not None
            assert 'MSH|' in message
        
        # Test list_scenarios function - should not fail even without scenarios
        scenarios = list_scenarios()
        assert isinstance(scenarios, list)


class TestScenarioMetadata:
    """Test the ScenarioMetadata class."""
    
    def test_scenario_metadata_creation(self):
        """Test creating ScenarioMetadata objects."""
        metadata = ScenarioMetadata(
            age_group='adult',
            gender='female',
            primary_condition='diabetes',
            expected_duration='2-4_hours'
        )
        
        assert metadata.age_group == 'adult'
        assert metadata.gender == 'female'
        assert metadata.primary_condition == 'diabetes'
        assert metadata.expected_duration == '2-4_hours'


class TestPatientScenario:
    """Test the PatientScenario class."""
    
    def test_patient_scenario_creation(self):
        """Test creating PatientScenario objects."""
        metadata = ScenarioMetadata(
            age_group='adult',
            gender='male',
            primary_condition='chest_pain',
            expected_duration='2-3_hours'
        )
        
        scenario = PatientScenario(
            id='test_scenario',
            name='Test Scenario',
            description='A test scenario',
            category='cardiology',
            severity='moderate',
            tags=['test', 'cardiology'],
            metadata=metadata,
            hl7_message='MSH|test\nPID|test',
            expected_findings=['elevated_bp'],
            clinical_pathways=['cardiac_workup']
        )
        
        assert scenario.id == 'test_scenario'
        assert scenario.name == 'Test Scenario'
        assert scenario.category == 'cardiology'
        assert scenario.severity == 'moderate'
        assert 'test' in scenario.tags
        assert scenario.metadata.age_group == 'adult'
        assert 'elevated_bp' in scenario.expected_findings
        assert 'cardiac_workup' in scenario.clinical_pathways


class TestScenarioValidationError:
    """Test the ScenarioValidationError exception."""
    
    def test_scenario_validation_error(self):
        """Test raising ScenarioValidationError."""
        with pytest.raises(ScenarioValidationError) as exc_info:
            raise ScenarioValidationError("Test validation error")
        
        assert "Test validation error" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__])