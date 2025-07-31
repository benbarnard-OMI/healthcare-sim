"""
Configuration Loader Module

This module provides functionality to load and validate agent and task configurations
from YAML files, including support for custom configurations and templates.
"""

import yaml
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from copy import deepcopy

# Setup logging
logger = logging.getLogger(__name__)

class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

class ConfigurationLoader:
    """
    Loads and validates agent and task configurations from YAML files.
    Supports both built-in configurations and custom user-defined configurations.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'config')
        self._agents_config: Dict[str, Any] = {}
        self._tasks_config: Dict[str, Any] = {}
        self._custom_agents: Dict[str, Any] = {}
        self._custom_tasks: Dict[str, Any] = {}
        self._validation_rules: Dict[str, Any] = {}
        self._loaded = False
    
    def load_configurations(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load all agent and task configurations.
        
        Returns:
            Tuple of (agents_config, tasks_config)
        """
        if self._loaded:
            return self._agents_config, self._tasks_config
        
        # Load built-in configurations
        self._load_builtin_agents()
        self._load_builtin_tasks()
        
        # Load custom configurations
        self._load_custom_agents()
        self._load_custom_tasks()
        
        # Validate all configurations
        self._validate_all_configurations()
        
        self._loaded = True
        return self._agents_config, self._tasks_config
    
    def _load_builtin_agents(self) -> None:
        """Load built-in agent configurations."""
        agents_file = os.path.join(self.config_dir, 'agents.yaml')
        if os.path.exists(agents_file):
            with open(agents_file, 'r', encoding='utf-8') as f:
                self._agents_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded {len(self._agents_config)} built-in agents")
        else:
            logger.warning(f"Built-in agents file not found: {agents_file}")
    
    def _load_builtin_tasks(self) -> None:
        """Load built-in task configurations."""
        tasks_file = os.path.join(self.config_dir, 'tasks.yaml')
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                self._tasks_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded {len(self._tasks_config)} built-in tasks")
        else:
            logger.warning(f"Built-in tasks file not found: {tasks_file}")
    
    def _load_custom_agents(self) -> None:
        """Load custom agent configurations."""
        # Load from custom agents template file
        template_file = os.path.join(self.config_dir, 'custom_agents_template.yaml')
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f) or {}
            
            # Extract custom agents (exclude templates and validation)
            for key, value in template_data.items():
                if key.startswith('custom_') and isinstance(value, dict):
                    self._custom_agents[key] = value
            
            # Store validation rules
            if 'validation' in template_data:
                self._validation_rules['agents'] = template_data['validation']
        
        # Load from custom agents file if exists
        custom_file = os.path.join(self.config_dir, 'custom_agents.yaml')
        if os.path.exists(custom_file):
            with open(custom_file, 'r', encoding='utf-8') as f:
                custom_data = yaml.safe_load(f) or {}
            self._custom_agents.update(custom_data)
        
        # Merge custom agents into main config
        self._agents_config.update(self._custom_agents)
        
        if self._custom_agents:
            logger.info(f"Loaded {len(self._custom_agents)} custom agents")
    
    def _load_custom_tasks(self) -> None:
        """Load custom task configurations."""
        # Load from custom tasks template file
        template_file = os.path.join(self.config_dir, 'custom_tasks_template.yaml')
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f) or {}
            
            # Extract custom tasks (exclude templates and validation)
            for key, value in template_data.items():
                if not key.startswith(('task_template', 'validation', 'execution_patterns')) and isinstance(value, dict):
                    # Only include tasks that have required fields
                    if 'description' in value and 'expected_output' in value and 'agent' in value:
                        self._custom_tasks[key] = value
            
            # Store validation rules
            if 'validation' in template_data:
                self._validation_rules['tasks'] = template_data['validation']
        
        # Load from custom tasks file if exists
        custom_file = os.path.join(self.config_dir, 'custom_tasks.yaml')
        if os.path.exists(custom_file):
            with open(custom_file, 'r', encoding='utf-8') as f:
                custom_data = yaml.safe_load(f) or {}
            self._custom_tasks.update(custom_data)
        
        # Merge custom tasks into main config
        self._tasks_config.update(self._custom_tasks)
        
        if self._custom_tasks:
            logger.info(f"Loaded {len(self._custom_tasks)} custom tasks")
    
    def _validate_all_configurations(self) -> None:
        """Validate all loaded configurations."""
        # Validate agents
        for agent_name, agent_config in self._agents_config.items():
            try:
                self._validate_agent_config(agent_name, agent_config)
            except ConfigurationValidationError as e:
                logger.error(f"Agent validation failed: {e}")
        
        # Validate tasks
        for task_name, task_config in self._tasks_config.items():
            try:
                self._validate_task_config(task_name, task_config)
            except ConfigurationValidationError as e:
                logger.error(f"Task validation failed: {e}")
    
    def _validate_agent_config(self, agent_name: str, config: Dict[str, Any]) -> None:
        """Validate an agent configuration."""
        validation_rules = self._validation_rules.get('agents', {})
        
        # Check required fields
        required_fields = validation_rules.get('required_fields', ['role', 'goal', 'backstory'])
        for field in required_fields:
            if field not in config or not config[field]:
                raise ConfigurationValidationError(
                    f"Agent '{agent_name}': missing required field '{field}'"
                )
        
        # Validate tools
        if 'tools' in config:
            available_tools = validation_rules.get('available_tools', [])
            if available_tools:
                for tool in config['tools']:
                    if tool not in available_tools:
                        logger.warning(
                            f"Agent '{agent_name}': unknown tool '{tool}'. "
                            f"Available tools: {available_tools}"
                        )
        
        # Apply defaults
        defaults = validation_rules.get('defaults', {})
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
    
    def _validate_task_config(self, task_name: str, config: Dict[str, Any]) -> None:
        """Validate a task configuration."""
        validation_rules = self._validation_rules.get('tasks', {})
        
        # Check required fields
        required_fields = validation_rules.get('required_fields', ['description', 'expected_output', 'agent'])
        for field in required_fields:
            if field not in config or not config[field]:
                raise ConfigurationValidationError(
                    f"Task '{task_name}': missing required field '{field}'"
                )
        
        # Validate agent exists
        agent_name = config['agent']
        if agent_name not in self._agents_config:
            raise ConfigurationValidationError(
                f"Task '{task_name}': references non-existent agent '{agent_name}'"
            )
        
        # Validate context dependencies
        if 'context' in config:
            available_contexts = validation_rules.get('context_dependencies', [])
            for context_task in config['context']:
                if available_contexts and context_task not in available_contexts:
                    # Check if it's a custom task
                    if context_task not in self._tasks_config:
                        logger.warning(
                            f"Task '{task_name}': unknown context dependency '{context_task}'"
                        )
        
        # Apply defaults
        defaults = validation_rules.get('defaults', {})
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
    
    def add_custom_agent(self, agent_name: str, agent_config: Dict[str, Any]) -> None:
        """
        Add a custom agent configuration dynamically.
        
        Args:
            agent_name: Name of the agent
            agent_config: Configuration dictionary
        """
        try:
            # Validate the configuration
            config_copy = deepcopy(agent_config)
            self._validate_agent_config(agent_name, config_copy)
            
            # Add to configurations
            self._agents_config[agent_name] = config_copy
            self._custom_agents[agent_name] = config_copy
            
            logger.info(f"Added custom agent: {agent_name}")
        except ConfigurationValidationError as e:
            logger.error(f"Failed to add custom agent '{agent_name}': {e}")
            raise
    
    def add_custom_task(self, task_name: str, task_config: Dict[str, Any]) -> None:
        """
        Add a custom task configuration dynamically.
        
        Args:
            task_name: Name of the task
            task_config: Configuration dictionary
        """
        try:
            # Validate the configuration
            config_copy = deepcopy(task_config)
            self._validate_task_config(task_name, config_copy)
            
            # Add to configurations
            self._tasks_config[task_name] = config_copy
            self._custom_tasks[task_name] = config_copy
            
            logger.info(f"Added custom task: {task_name}")
        except ConfigurationValidationError as e:
            logger.error(f"Failed to add custom task '{task_name}': {e}")
            raise
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent."""
        self.load_configurations()
        return deepcopy(self._agents_config.get(agent_name))
    
    def get_task_config(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific task."""
        self.load_configurations()
        return deepcopy(self._tasks_config.get(task_name))
    
    def list_agents(self) -> List[str]:
        """List all available agent names."""
        self.load_configurations()
        return list(self._agents_config.keys())
    
    def list_tasks(self) -> List[str]:
        """List all available task names."""
        self.load_configurations()
        return list(self._tasks_config.keys())
    
    def list_custom_agents(self) -> List[str]:
        """List custom agent names."""
        self.load_configurations()
        return list(self._custom_agents.keys())
    
    def list_custom_tasks(self) -> List[str]:
        """List custom task names."""
        self.load_configurations()
        return list(self._custom_tasks.keys())
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent."""
        config = self.get_agent_config(agent_name)
        if not config:
            return None
        
        return {
            'name': agent_name,
            'role': config.get('role', ''),
            'goal': config.get('goal', ''),
            'backstory': config.get('backstory', ''),
            'tools': config.get('tools', []),
            'allow_delegation': config.get('allow_delegation', False),
            'verbose': config.get('verbose', True),
            'is_custom': agent_name in self._custom_agents
        }
    
    def get_task_info(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a task."""
        config = self.get_task_config(task_name)
        if not config:
            return None
        
        return {
            'name': task_name,
            'description': config.get('description', ''),
            'expected_output': config.get('expected_output', ''),
            'agent': config.get('agent', ''),
            'context': config.get('context', []),
            'tools': config.get('tools', []),
            'max_execution_time': config.get('max_execution_time', 300),
            'is_custom': task_name in self._custom_tasks
        }
    
    def save_custom_configurations(self) -> None:
        """Save custom configurations to files."""
        # Save custom agents
        if self._custom_agents:
            custom_agents_file = os.path.join(self.config_dir, 'custom_agents.yaml')
            with open(custom_agents_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._custom_agents, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved {len(self._custom_agents)} custom agents to {custom_agents_file}")
        
        # Save custom tasks
        if self._custom_tasks:
            custom_tasks_file = os.path.join(self.config_dir, 'custom_tasks.yaml')
            with open(custom_tasks_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._custom_tasks, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved {len(self._custom_tasks)} custom tasks to {custom_tasks_file}")
    
    def validate_configuration_files(self) -> List[str]:
        """
        Validate all configuration files and return a list of errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        try:
            self.load_configurations()
        except Exception as e:
            errors.append(f"Failed to load configurations: {str(e)}")
        
        return errors


# Global configuration loader instance
_config_loader = None

def get_config_loader(config_dir: str = None) -> ConfigurationLoader:
    """
    Get the global configuration loader instance.
    
    Args:
        config_dir: Directory containing configuration files
        
    Returns:
        ConfigurationLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigurationLoader(config_dir)
    return _config_loader