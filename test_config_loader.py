"""
Tests for configuration loader functionality and custom agent/task management.
"""

import pytest
import os
import yaml
import tempfile
from unittest.mock import patch, MagicMock
from config_loader import ConfigurationLoader, ConfigurationValidationError

class TestConfigurationLoader:
    """Test the ConfigurationLoader class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_agents_config = {
            'test_agent': {
                'role': 'Test Healthcare Professional',
                'goal': 'Provide test healthcare services',
                'backstory': 'You are a test healthcare professional for unit testing.',
                'tools': ['clinical_guidelines_tool'],
                'allow_delegation': False,
                'verbose': True,
                'max_execution_time': 300
            }
        }
        
        self.test_tasks_config = {
            'test_task': {
                'description': 'Perform a test healthcare task for patient {patient_id}.',
                'expected_output': 'A test report with healthcare recommendations.',
                'agent': 'test_agent',
                'context': ['ingest_hl7_data'],
                'max_execution_time': 300
            }
        }
        
        self.custom_agents_template = {
            'custom_test_agent': {
                'role': 'Custom Test Agent',
                'goal': 'Test custom agent functionality',
                'backstory': 'Custom test agent for validation testing.',
                'tools': ['medication_interaction_tool']
            },
            'validation': {
                'required_fields': ['role', 'goal', 'backstory'],
                'available_tools': ['clinical_guidelines_tool', 'medication_interaction_tool', 'appointment_scheduler_tool'],
                'defaults': {
                    'allow_delegation': False,
                    'verbose': True,
                    'max_execution_time': 300
                }
            }
        }
        
        self.custom_tasks_template = {
            'custom_test_task': {
                'description': 'Custom test task for patient {patient_id}.',
                'expected_output': 'Custom test task output.',
                'agent': 'custom_test_agent'
            },
            'validation': {
                'required_fields': ['description', 'expected_output', 'agent'],
                'context_dependencies': ['ingest_hl7_data', 'analyze_diagnostics'],
                'defaults': {
                    'max_execution_time': 300,
                    'human_input': False
                }
            }
        }
    
    def create_temp_config_dir(self):
        """Create a temporary configuration directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create agents.yaml
        agents_file = os.path.join(temp_dir, 'agents.yaml')
        with open(agents_file, 'w') as f:
            yaml.safe_dump(self.test_agents_config, f)
        
        # Create tasks.yaml
        tasks_file = os.path.join(temp_dir, 'tasks.yaml')
        with open(tasks_file, 'w') as f:
            yaml.safe_dump(self.test_tasks_config, f)
        
        # Create custom_agents_template.yaml
        custom_agents_file = os.path.join(temp_dir, 'custom_agents_template.yaml')
        with open(custom_agents_file, 'w') as f:
            yaml.safe_dump(self.custom_agents_template, f)
        
        # Create custom_tasks_template.yaml
        custom_tasks_file = os.path.join(temp_dir, 'custom_tasks_template.yaml')
        with open(custom_tasks_file, 'w') as f:
            yaml.safe_dump(self.custom_tasks_template, f)
        
        return temp_dir
    
    def test_configuration_loader_initialization(self):
        """Test ConfigurationLoader initialization."""
        loader = ConfigurationLoader()
        assert loader.config_dir is not None
        assert loader._agents_config == {}
        assert loader._tasks_config == {}
        assert not loader._loaded
    
    def test_load_builtin_configurations(self):
        """Test loading built-in agent and task configurations."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            agents_config, tasks_config = loader.load_configurations()
            
            # Check agents
            assert len(agents_config) >= 1
            assert 'test_agent' in agents_config
            assert agents_config['test_agent']['role'] == 'Test Healthcare Professional'
            
            # Check tasks
            assert len(tasks_config) >= 1
            assert 'test_task' in tasks_config
            assert tasks_config['test_task']['agent'] == 'test_agent'
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_load_custom_configurations(self):
        """Test loading custom configurations from templates."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            agents_config, tasks_config = loader.load_configurations()
            
            # Check custom agents loaded
            assert 'custom_test_agent' in agents_config
            assert agents_config['custom_test_agent']['role'] == 'Custom Test Agent'
            
            # Check custom tasks loaded
            assert 'custom_test_task' in tasks_config
            assert tasks_config['custom_test_task']['agent'] == 'custom_test_agent'
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_agent_validation_required_fields(self):
        """Test agent validation for required fields."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            
            # Test invalid agent config (missing required fields)
            invalid_agent_config = {
                'role': 'Test Role',
                # Missing 'goal' and 'backstory'
            }
            
            with pytest.raises(ConfigurationValidationError) as exc_info:
                loader.add_custom_agent('invalid_agent', invalid_agent_config)
            
            assert "missing required field" in str(exc_info.value)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_task_validation_required_fields(self):
        """Test task validation for required fields."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            loader.load_configurations()  # Load agents first
            
            # Test invalid task config (missing required fields)
            invalid_task_config = {
                'description': 'Test task description',
                # Missing 'expected_output' and 'agent'
            }
            
            with pytest.raises(ConfigurationValidationError) as exc_info:
                loader.add_custom_task('invalid_task', invalid_task_config)
            
            assert "missing required field" in str(exc_info.value)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_task_validation_agent_exists(self):
        """Test task validation for agent existence."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            loader.load_configurations()
            
            # Test task with non-existent agent
            invalid_task_config = {
                'description': 'Test task description',
                'expected_output': 'Test output',
                'agent': 'non_existent_agent'
            }
            
            with pytest.raises(ConfigurationValidationError) as exc_info:
                loader.add_custom_task('invalid_task', invalid_task_config)
            
            assert "non-existent agent" in str(exc_info.value)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_add_custom_agent_success(self):
        """Test successfully adding a custom agent."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            loader.load_configurations()
            
            custom_agent_config = {
                'role': 'Custom Pharmacist',
                'goal': 'Review medications',
                'backstory': 'You are a clinical pharmacist.',
                'tools': ['medication_interaction_tool']
            }
            
            # Should succeed without raising an exception
            loader.add_custom_agent('custom_pharmacist', custom_agent_config)
            
            # Verify agent was added
            agent_config = loader.get_agent_config('custom_pharmacist')
            assert agent_config is not None
            assert agent_config['role'] == 'Custom Pharmacist'
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_add_custom_task_success(self):
        """Test successfully adding a custom task."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            loader.load_configurations()
            
            # First add a custom agent
            custom_agent_config = {
                'role': 'Custom Pharmacist',
                'goal': 'Review medications',
                'backstory': 'You are a clinical pharmacist.'
            }
            loader.add_custom_agent('custom_pharmacist', custom_agent_config)
            
            # Then add a custom task
            custom_task_config = {
                'description': 'Review medications for patient {patient_id}.',
                'expected_output': 'Medication review report.',
                'agent': 'custom_pharmacist'
            }
            
            # Should succeed without raising an exception
            loader.add_custom_task('medication_review', custom_task_config)
            
            # Verify task was added
            task_config = loader.get_task_config('medication_review')
            assert task_config is not None
            assert task_config['agent'] == 'custom_pharmacist'
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_get_agent_config(self):
        """Test getting agent configuration."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            
            # Test existing agent
            config = loader.get_agent_config('test_agent')
            assert config is not None
            assert config['role'] == 'Test Healthcare Professional'
            
            # Test non-existent agent
            config = loader.get_agent_config('non_existent_agent')
            assert config is None
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_get_task_config(self):
        """Test getting task configuration."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            
            # Test existing task
            config = loader.get_task_config('test_task')
            assert config is not None
            assert config['agent'] == 'test_agent'
            
            # Test non-existent task
            config = loader.get_task_config('non_existent_task')
            assert config is None
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_list_agents(self):
        """Test listing all agents."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            agents = loader.list_agents()
            
            assert 'test_agent' in agents
            assert 'custom_test_agent' in agents
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_list_tasks(self):
        """Test listing all tasks."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            tasks = loader.list_tasks()
            
            assert 'test_task' in tasks
            assert 'custom_test_task' in tasks
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_list_custom_agents(self):
        """Test listing custom agents only."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            custom_agents = loader.list_custom_agents()
            
            assert 'custom_test_agent' in custom_agents
            assert 'test_agent' not in custom_agents  # Built-in agent
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_list_custom_tasks(self):
        """Test listing custom tasks only."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            custom_tasks = loader.list_custom_tasks()
            
            assert 'custom_test_task' in custom_tasks
            assert 'test_task' not in custom_tasks  # Built-in task
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_get_agent_info(self):
        """Test getting detailed agent information."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            
            info = loader.get_agent_info('test_agent')
            assert info is not None
            assert info['name'] == 'test_agent'
            assert info['role'] == 'Test Healthcare Professional'
            assert info['goal'] == 'Provide test healthcare services'
            assert 'clinical_guidelines_tool' in info['tools']
            assert info['allow_delegation'] is False
            assert info['is_custom'] is False
            
            # Test custom agent
            info = loader.get_agent_info('custom_test_agent')
            assert info is not None
            assert info['is_custom'] is True
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_get_task_info(self):
        """Test getting detailed task information."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            
            info = loader.get_task_info('test_task')
            assert info is not None
            assert info['name'] == 'test_task'
            assert info['agent'] == 'test_agent'
            assert 'patient {patient_id}' in info['description']
            assert info['max_execution_time'] == 300
            assert info['is_custom'] is False
            
            # Test custom task
            info = loader.get_task_info('custom_test_task')
            assert info is not None
            assert info['is_custom'] is True
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_validation_defaults_applied(self):
        """Test that validation defaults are applied to configurations."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            loader.load_configurations()
            
            # Check that defaults were applied to custom agent
            agent_config = loader.get_agent_config('custom_test_agent')
            assert agent_config['allow_delegation'] is False  # Default value
            assert agent_config['verbose'] is True  # Default value
            assert agent_config['max_execution_time'] == 300  # Default value
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_validate_configuration_files(self):
        """Test configuration file validation."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            errors = loader.validate_configuration_files()
            
            # Valid configurations should have no errors
            assert len(errors) == 0
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_save_custom_configurations(self):
        """Test saving custom configurations to files."""
        temp_dir = self.create_temp_config_dir()
        
        try:
            loader = ConfigurationLoader(config_dir=temp_dir)
            loader.load_configurations()
            
            # Add custom configurations
            custom_agent_config = {
                'role': 'Test Save Agent',
                'goal': 'Test saving functionality',
                'backstory': 'Test agent for save testing.'
            }
            loader.add_custom_agent('save_test_agent', custom_agent_config)
            
            custom_task_config = {
                'description': 'Test save task',
                'expected_output': 'Test save output',
                'agent': 'save_test_agent'
            }
            loader.add_custom_task('save_test_task', custom_task_config)
            
            # Save configurations
            loader.save_custom_configurations()
            
            # Verify files were created
            custom_agents_file = os.path.join(temp_dir, 'custom_agents.yaml')
            custom_tasks_file = os.path.join(temp_dir, 'custom_tasks.yaml')
            
            assert os.path.exists(custom_agents_file)
            assert os.path.exists(custom_tasks_file)
            
            # Verify content
            with open(custom_agents_file, 'r') as f:
                saved_agents = yaml.safe_load(f)
                assert 'save_test_agent' in saved_agents
            
            with open(custom_tasks_file, 'r') as f:
                saved_tasks = yaml.safe_load(f)
                assert 'save_test_task' in saved_tasks
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_global_config_loader_function(self):
        """Test the global get_config_loader function."""
        from config_loader import get_config_loader
        
        loader1 = get_config_loader()
        loader2 = get_config_loader()
        
        # Should return the same instance
        assert loader1 is loader2


class TestConfigurationValidationError:
    """Test the ConfigurationValidationError exception."""
    
    def test_configuration_validation_error(self):
        """Test raising ConfigurationValidationError."""
        with pytest.raises(ConfigurationValidationError) as exc_info:
            raise ConfigurationValidationError("Test configuration error")
        
        assert "Test configuration error" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__])